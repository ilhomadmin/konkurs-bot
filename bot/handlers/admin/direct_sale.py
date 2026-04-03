"""
Admin Direct Sale — akkauntlarni bevosita link orqali sotish
"""
import secrets
import logging
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.filters import CommandStart
from aiogram.filters.command import CommandObject

from bot.db.models import (
    get_user, get_all_categories, get_products_by_category, get_product_by_id,
    get_prices_by_product, get_available_count, get_next_available_account,
    set_direct_sale_token, get_direct_sale_account, sell_account,
    create_order, create_order_item, increment_purchase_count,
    update_user_stats, update_order_status,
)
from bot.utils.texts import t
from bot.utils.duration import tier_display_name

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
    """Direct sale — kategoriya tanlash"""
    try:
        lang, role = await get_lang_and_role(callback.from_user.id)
        if not role:
            await callback.answer(t("access_denied", lang), show_alert=True)
            return

        categories = await get_all_categories(only_active=True)
        buttons = []
        for cat in categories:
            buttons.append([InlineKeyboardButton(
                text=cat[f"name_{lang}"],
                callback_data=f"adm:ds:cat:{cat['id']}"
            )])
        buttons.append([InlineKeyboardButton(text=t("btn_back", lang), callback_data="adm:back")])

        await callback.message.edit_text(
            t("btn_ds_select_cat", lang),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )
        await callback.answer()
    except Exception:
        await callback.answer(t("error_general"), show_alert=True)


@router.callback_query(F.data.startswith("adm:ds:cat:"))
async def ds_category(callback: CallbackQuery) -> None:
    """Direct sale — mahsulot tanlash"""
    try:
        cat_id = int(callback.data.split(":")[3])
        lang, role = await get_lang_and_role(callback.from_user.id)
        if not role:
            await callback.answer(t("access_denied", lang), show_alert=True)
            return

        products = await get_products_by_category(cat_id, only_active=True)
        buttons = []
        for prod in products:
            stats = await get_available_count(prod["id"])
            available = stats.get("available", 0)
            name = prod[f"name_{lang}"]
            buttons.append([InlineKeyboardButton(
                text=f"{name} ({available} ta)" if lang == "uz" else f"{name} ({available} шт)",
                callback_data=f"adm:ds:prod:{prod['id']}"
            )])
        buttons.append([InlineKeyboardButton(text=t("btn_back", lang), callback_data="adm:ds")])

        await callback.message.edit_text(
            t("select_product", lang),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )
        await callback.answer()
    except Exception:
        await callback.answer(t("error_general"), show_alert=True)


@router.callback_query(F.data.startswith("adm:ds:prod:"))
async def ds_product(callback: CallbackQuery) -> None:
    """Direct sale — tier tanlash"""
    try:
        product_id = int(callback.data.split(":")[3])
        lang, role = await get_lang_and_role(callback.from_user.id)
        if not role:
            await callback.answer(t("access_denied", lang), show_alert=True)
            return

        prices = await get_prices_by_product(product_id)
        prod = await get_product_by_id(product_id)
        cat_id = prod["category_id"] if prod else 0

        buttons = []
        for price in prices:
            tier = price["duration_tier"]
            tier_name = price[f"display_name_{lang}"]
            stats = await get_available_count(product_id, tier)
            available = stats.get("available", 0)
            if available > 0:
                buttons.append([InlineKeyboardButton(
                    text=f"{tier_name} — {price['price']:,} ({available} ta)",
                    callback_data=f"adm:ds:tier:{product_id}:{tier}"
                )])

        if not buttons:
            await callback.answer(t("ds_no_accounts", lang), show_alert=True)
            return

        buttons.append([InlineKeyboardButton(
            text=t("btn_back", lang),
            callback_data=f"adm:ds:cat:{cat_id}"
        )])

        await callback.message.edit_text(
            t("ask_tier_select", lang),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )
        await callback.answer()
    except Exception:
        await callback.answer(t("error_general"), show_alert=True)


@router.callback_query(F.data.startswith("adm:ds:tier:"))
async def ds_show_account(callback: CallbackQuery, bot: Bot) -> None:
    """Direct sale — akkaunt ko'rsatish va link generatsiya"""
    try:
        parts = callback.data.split(":")
        product_id = int(parts[3])
        tier = parts[4]

        lang, role = await get_lang_and_role(callback.from_user.id)
        if not role:
            await callback.answer(t("access_denied", lang), show_alert=True)
            return

        await _show_ds_account(callback, bot, product_id, tier, lang)
    except Exception:
        await callback.answer(t("error_general"), show_alert=True)


async def _show_ds_account(
    callback: CallbackQuery,
    bot: Bot,
    product_id: int,
    tier: str,
    lang: str
) -> None:
    """Birinchi available akkauntni ko'rsatib token generatsiya qiladi"""
    acc = await get_next_available_account(product_id, tier)
    if not acc:
        await callback.answer(t("ds_no_accounts", lang), show_alert=True)
        return

    # Token generatsiya va saqlash
    token = secrets.token_urlsafe(6)
    await set_direct_sale_token(acc["id"], token)

    # Bot username ni olish
    me = await bot.get_me()
    bot_username = me.username
    link = f"https://t.me/{bot_username}?start={DS_PREFIX}{token}"

    # Mavjud sonni olish
    stats = await get_available_count(product_id, tier)
    available = stats.get("available", 0)

    prod = await get_product_by_id(product_id)
    name = prod[f"name_{lang}"] if prod else "—"
    tier_name = tier_display_name(tier, lang)

    text = t("ds_account_info", lang,
             name=name, tier=tier_name,
             available=available,
             acc_id=acc["id"],
             days=acc.get("remaining_days", 0),
             login=acc["login"],
             password=acc["password"],
             expiry=acc["expiry_date"],
             link=link)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=t("btn_ds_sold", lang),
                                 callback_data=f"adm:ds:sell:{acc['id']}:{product_id}:{tier}"),
            InlineKeyboardButton(text=t("btn_ds_next", lang),
                                 callback_data=f"adm:ds:next:{product_id}:{tier}"),
        ],
        [InlineKeyboardButton(text=t("btn_back", lang),
                              callback_data=f"adm:ds:prod:{product_id}")],
    ])

    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("adm:ds:sell:"))
async def ds_manual_sell(callback: CallbackQuery, bot: Bot) -> None:
    """Admin qo'lda akkauntni sotildi deb belgilaydi"""
    try:
        parts = callback.data.split(":")
        acc_id = int(parts[3])
        product_id = int(parts[4])
        tier = parts[5]

        lang, role = await get_lang_and_role(callback.from_user.id)
        if not role:
            await callback.answer(t("access_denied", lang), show_alert=True)
            return

        # Akkauntni sotilgan deb belgilash (user_id = None, manual sale)
        from bot.db.database import get_db
        async with get_db() as db:
            await db.execute("""
                UPDATE accounts
                SET status = 'sold',
                    sold_at = CURRENT_TIMESTAMP,
                    sold_via = 'direct_sale_manual'
                WHERE id = ? AND status = 'available'
            """, (acc_id,))
            await db.commit()

        await increment_purchase_count(product_id)
        await callback.answer(t("ds_sold_success", lang))

        # Keyingi akkauntni ko'rsatish
        await _show_ds_account(callback, bot, product_id, tier, lang)
    except Exception:
        await callback.answer(t("error_general"), show_alert=True)


@router.callback_query(F.data.startswith("adm:ds:next:"))
async def ds_next_account(callback: CallbackQuery, bot: Bot) -> None:
    """Keyingi akkauntni ko'rsatish"""
    try:
        parts = callback.data.split(":")
        product_id = int(parts[3])
        tier = parts[4]

        lang, role = await get_lang_and_role(callback.from_user.id)
        if not role:
            await callback.answer(t("access_denied", lang), show_alert=True)
            return

        await _show_ds_account(callback, bot, product_id, tier, lang)
    except Exception:
        await callback.answer(t("error_general"), show_alert=True)


# ==================== MIJOZ: /start=DS_TOKEN ====================

@router.message(CommandStart(deep_link=True, deep_link_encoded=False))
async def direct_sale_start(message: Message, command: CommandObject, bot: Bot) -> None:
    """
    /start DS_xxxxx — direct sale link orqali kelgan mijoz.
    Token bo'yicha akkauntni topib, yetkazadi.
    """
    try:
        arg = command.args or ""
        if not arg.startswith(DS_PREFIX):
            return  # Oddiy /start — start.py handle qiladi

        token = arg[len(DS_PREFIX):]

        # Foydalanuvchini yaratish yoki topish
        tg_user = message.from_user
        from bot.db.models import create_user
        user = await create_user(tg_user.id, tg_user.username, tg_user.full_name)
        lang = user.get("language", "uz") if user else "uz"

        # Akkauntni topish
        acc = await get_direct_sale_account(token)
        if not acc:
            await message.answer(t("ds_link_expired", lang))
            return

        # Akkauntni sotish
        await sell_account(acc["id"], tg_user.id, "direct_sale")

        # Order va order_item yaratish (auto_delivered)
        prices = await get_prices_by_product(acc["product_id"])
        tier = acc.get("duration_tier")
        price_info = next((p for p in prices if p["duration_tier"] == tier), None)
        unit_price = price_info["price"] if price_info else 0
        cost_price = price_info["cost_price"] if price_info else 0

        order_id = await create_order(
            user_telegram_id=tg_user.id,
            total_amount=unit_price,
            discount_amount=0
        )
        await update_order_status(order_id, "auto_delivered")
        item_id = await create_order_item(
            order_id=order_id,
            product_id=acc["product_id"],
            quantity=1,
            duration_tier=tier or "",
            unit_price=unit_price,
            cost_price=cost_price
        )
        from bot.db.models import update_order_item
        await update_order_item(item_id,
                                account_id=acc["id"],
                                status="delivered",
                                expiry_date=acc["expiry_date"])

        await increment_purchase_count(acc["product_id"])
        await update_user_stats(tg_user.id, unit_price, 1)

        # Akkaunt ma'lumotlarini yuborish
        name = acc[f"name_{lang}"]
        text = t("ds_account_delivered", lang,
                 name=name,
                 login=acc["login"],
                 password=acc["password"],
                 expiry=acc["expiry_date"])
        await message.answer(text, parse_mode="HTML")

        # Instruksiya video
        video_id = acc.get("product_video") or acc.get("category_video")
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
        logger.error(f"Direct sale start xato: {e}")
        await message.answer(t("error_general"))
