"""
Admin Direct Sale — akkauntlarni bevosita link orqali sotish
YANGI STRUKTURA: tier yo'q, narx product da
"""
import secrets
import logging
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.filters import CommandStart
from aiogram.filters.command import CommandObject

from bot.db.models import (
    get_user, get_all_categories, get_products_by_category, get_product_by_id,
    get_product_stock, sell_account, generate_direct_sale_token,
    get_account_by_direct_sale_token,
    create_order, add_order_item, increment_purchase_count,
    increment_user_purchases, update_order_status,
)
from bot.utils.texts import t

logger = logging.getLogger(__name__)
router = Router()

DS_PREFIX = "DS_"


async def get_lang_and_role(user_id: int) -> tuple[str, str | None]:
    from bot.handlers.admin.menu import get_admin_role
    user = await get_user(user_id)
    lang = user.get("language", "uz") if user else "uz"
    role = await get_admin_role(user_id)
    return lang, role


# ==================== ADMIN: SOTUV MENYUSI ====================

@router.callback_query(F.data == "adm:ds")
async def ds_start(callback: CallbackQuery) -> None:
    try:
        lang, role = await get_lang_and_role(callback.from_user.id)
        if not role:
            await callback.answer(t("access_denied", lang), show_alert=True)
            return

        categories = await get_all_categories(only_active=True)
        buttons = []
        for cat in categories:
            buttons.append([InlineKeyboardButton(
                text=cat.get(f"name_{lang}", cat.get("name_uz", "?")),
                callback_data=f"adm:ds:cat:{cat['id']}"
            )])
        buttons.append([InlineKeyboardButton(text=t("btn_back", lang), callback_data="adm:back")])

        await callback.message.edit_text(
            t("btn_ds_select_cat", lang),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )
        await callback.answer()
    except Exception as e:
        logger.exception(f"ds_start error: {e}")
        await callback.answer(t("error_general"), show_alert=True)


@router.callback_query(F.data.startswith("adm:ds:cat:"))
async def ds_category(callback: CallbackQuery) -> None:
    try:
        cat_id = int(callback.data.split(":")[3])
        lang, role = await get_lang_and_role(callback.from_user.id)
        if not role:
            await callback.answer(t("access_denied", lang), show_alert=True)
            return

        products = await get_products_by_category(cat_id, only_active=True)
        buttons = []
        for prod in products:
            stock = await get_product_stock(prod["id"])
            name = prod.get(f"name_{lang}", prod.get("name_uz", "?"))
            buttons.append([InlineKeyboardButton(
                text=f"{name} — {prod['price']:,} ({stock} ta)",
                callback_data=f"adm:ds:prod:{prod['id']}"
            )])
        buttons.append([InlineKeyboardButton(text=t("btn_back", lang), callback_data="adm:ds")])

        await callback.message.edit_text(
            t("select_product", lang),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )
        await callback.answer()
    except Exception as e:
        logger.exception(f"ds_category error: {e}")
        await callback.answer(t("error_general"), show_alert=True)


@router.callback_query(F.data.startswith("adm:ds:prod:"))
async def ds_product(callback: CallbackQuery, bot: Bot) -> None:
    try:
        product_id = int(callback.data.split(":")[3])
        lang, role = await get_lang_and_role(callback.from_user.id)
        if not role:
            await callback.answer(t("access_denied", lang), show_alert=True)
            return

        await _show_ds_account(callback, bot, product_id, lang)
    except Exception as e:
        logger.exception(f"ds_product error: {e}")
        await callback.answer(t("error_general"), show_alert=True)


async def _show_ds_account(
    callback: CallbackQuery,
    bot: Bot,
    product_id: int,
    lang: str
) -> None:
    from bot.db.database import get_db

    # Birinchi available akkauntni topish
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT * FROM accounts
            WHERE product_id = ? AND status = 'available'
            ORDER BY expiry_date ASC
            LIMIT 1
        """, (product_id,))
        row = await cursor.fetchone()

    if not row:
        await callback.answer(t("ds_no_accounts", lang), show_alert=True)
        return

    acc = dict(row)

    # Token generatsiya
    token = await generate_direct_sale_token(acc["id"])

    me = await bot.get_me()
    bot_username = me.username
    link = f"https://t.me/{bot_username}?start={DS_PREFIX}{token}"

    stock = await get_product_stock(product_id)
    prod = await get_product_by_id(product_id)
    name = prod.get(f"name_{lang}", "—") if prod else "—"

    text = t("ds_account_info", lang,
             name=name,
             available=stock,
             acc_id=acc["id"],
             days=acc.get("remaining_days", 0),
             login=acc["login"],
             password=acc["password"],
             expiry=acc["expiry_date"],
             link=link)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=t("btn_ds_sold", lang),
                                 callback_data=f"adm:ds:sell:{acc['id']}:{product_id}"),
            InlineKeyboardButton(text=t("btn_ds_next", lang),
                                 callback_data=f"adm:ds:next:{product_id}"),
        ],
        [InlineKeyboardButton(text=t("btn_back", lang),
                              callback_data=f"adm:ds:cat:{prod.get('category_id', 0) if prod else 0}")],
    ])

    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("adm:ds:sell:"))
async def ds_manual_sell(callback: CallbackQuery, bot: Bot) -> None:
    try:
        parts = callback.data.split(":")
        acc_id = int(parts[3])
        product_id = int(parts[4])

        lang, role = await get_lang_and_role(callback.from_user.id)
        if not role:
            await callback.answer(t("access_denied", lang), show_alert=True)
            return

        from bot.db.database import get_db
        async with get_db() as db:
            await db.execute("""
                UPDATE accounts
                SET status = 'sold', sold_at = CURRENT_TIMESTAMP,
                    sold_via = 'direct_sale_manual'
                WHERE id = ? AND status = 'available'
            """, (acc_id,))
            await db.commit()

        await increment_purchase_count(product_id)
        await callback.answer(t("ds_sold_success", lang))

        await _show_ds_account(callback, bot, product_id, lang)
    except Exception as e:
        logger.exception(f"ds_manual_sell error: {e}")
        await callback.answer(t("error_general"), show_alert=True)


@router.callback_query(F.data.startswith("adm:ds:next:"))
async def ds_next_account(callback: CallbackQuery, bot: Bot) -> None:
    try:
        product_id = int(callback.data.split(":")[3])
        lang, role = await get_lang_and_role(callback.from_user.id)
        if not role:
            await callback.answer(t("access_denied", lang), show_alert=True)
            return
        await _show_ds_account(callback, bot, product_id, lang)
    except Exception as e:
        logger.exception(f"ds_next_account error: {e}")
        await callback.answer(t("error_general"), show_alert=True)


# ==================== MIJOZ: /start=DS_TOKEN ====================

@router.message(CommandStart(deep_link=True, deep_link_encoded=False))
async def direct_sale_start(message: Message, command: CommandObject, bot: Bot) -> None:
    try:
        arg = command.args or ""
        if not arg.startswith(DS_PREFIX):
            return

        token = arg[len(DS_PREFIX):]

        tg_user = message.from_user
        from bot.db.models import create_user
        user = await create_user(tg_user.id, tg_user.username, tg_user.full_name)
        lang = user.get("language", "uz") if user else "uz"

        acc = await get_account_by_direct_sale_token(token)
        if not acc or acc.get("status") != "available":
            await message.answer(t("ds_link_expired", lang))
            return

        # Akkauntni sotish
        prod = await get_product_by_id(acc["product_id"])
        unit_price = prod.get("price", 0) if prod else 0
        cost_price = prod.get("cost_price", 0) if prod else 0

        # Sell the account
        from bot.db.database import get_db
        async with get_db() as db:
            await db.execute("""
                UPDATE accounts SET status = 'sold', sold_to_user_id = ?,
                       sold_at = CURRENT_TIMESTAMP, sold_via = 'direct_sale'
                WHERE id = ? AND status = 'available'
            """, (tg_user.id, acc["id"]))
            await db.commit()

        # Order yaratish
        order_id = await create_order(
            user_telegram_id=tg_user.id,
            total_amount=unit_price,
            discount_amount=0
        )
        await update_order_status(order_id, "auto_delivered")
        await add_order_item(
            order_id=order_id,
            product_id=acc["product_id"],
            quantity=1,
            unit_price=unit_price,
            cost_price=cost_price
        )

        await increment_purchase_count(acc["product_id"])
        await increment_user_purchases(tg_user.id, unit_price)

        name = prod.get(f"name_{lang}", "?") if prod else "?"
        text = t("ds_account_delivered", lang,
                 name=name,
                 login=acc["login"],
                 password=acc["password"],
                 expiry=acc["expiry_date"])
        await message.answer(text, parse_mode="HTML")

        # Video instruksiya
        if prod:
            video_id = prod.get("instruction_video_file_id")
            if video_id:
                try:
                    await bot.send_video(
                        chat_id=tg_user.id,
                        video=video_id,
                        caption="📹 Foydalanish instruksiyasi" if lang == "uz" else "📹 Инструкция"
                    )
                except Exception:
                    pass

    except Exception as e:
        logger.exception(f"direct_sale_start error: {e}")
        await message.answer(t("error_general"))
