"""
To'lov handlerlari:
- Mijoz chek yuboradi
- Bot guruhga forward qiladi
- Admin guruhda tasdiqlaydi → akkauntlar yetkaziladi
YANGI STRUKTURA: duration_tier yo'q
"""
import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.config import PAYMENT_GROUP_ID
from bot.db.models import (
    get_user, get_order_by_id, get_order_items,
    update_order_status, confirm_reserved,
    release_reserved, increment_purchase_count,
    increment_user_purchases, check_and_upgrade_vip,
    get_admin_by_telegram_id,
)
from bot.utils.texts import t

logger = logging.getLogger(__name__)
router = Router()

PROGRESS_MAP = {
    "pending_payment": "progress_pending",
    "payment_sent":    "progress_sent",
    "confirmed":       "progress_confirmed",
    "partial":         "progress_partial",
    "cancelled":       "progress_cancelled",
}


async def edit_progress_bar(bot: Bot, user_telegram_id: int, order: dict, new_status: str) -> None:
    """Progress bar xabarini yangilaydi"""
    try:
        msg_id = order.get("progress_message_id")
        if not msg_id:
            return
        user = await get_user(user_telegram_id)
        lang = user.get("language", "uz") if user else "uz"
        text_key = PROGRESS_MAP.get(new_status, "progress_pending")
        await bot.edit_message_text(
            chat_id=user_telegram_id,
            message_id=msg_id,
            text=t(text_key, lang)
        )
    except Exception as e:
        logger.warning(f"Progress bar yangilashda xato: {e}")


def build_account_delivery_text(items: list[dict], lang: str) -> str:
    """Akkaunt yetkazish matni"""
    lines = []
    num = 1
    for item in items:
        if item.get("status") != "delivered":
            continue
        name = item.get(f"name_{lang}", item.get("name_uz", "?"))
        login = item.get("login") or "—"
        password = item.get("password") or "—"
        expiry = item.get("expiry_date") or "—"
        lines.append(t("account_delivery_line", lang,
                       num=num, name=name,
                       login=login, password=password, expiry=expiry))
        num += 1
    return "\n\n".join(lines)


# ==================== CHEK YUBORISH ====================

@router.message(F.photo)
async def payment_screenshot(message: Message, bot: Bot) -> None:
    """Mijoz rasm yuboradi — bu to'lov cheki bo'lishi mumkin."""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            return
        lang = user.get("language", "uz")

        # Aktiv buyurtmani topish
        from bot.db.models import get_user_orders
        orders = await get_user_orders(message.from_user.id, limit=1)
        order = None
        for o in orders:
            if o["status"] in ("pending_payment", "payment_sent"):
                order = o
                break

        if not order:
            return

        file_id = message.photo[-1].file_id
        order_id = order["id"]

        # Buyurtma elementlarini olish
        items = await get_order_items(order_id)
        items_text = ""
        for item in items:
            name = item.get(f"name_{lang}", item.get("name_uz", "?"))
            items_text += f"• {name} x{item['quantity']}\n"

        full_name = user.get("full_name") or "—"
        username = user.get("username") or "—"

        # Guruhga xabar + chek
        group_text = t("group_payment_notify", "uz",
                       order_id=order_id,
                       full_name=full_name,
                       username=username,
                       amount=order["total_amount"],
                       items_text=items_text.strip())

        group_kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("btn_confirm_payment", "uz"),
                    callback_data=f"pay:ok:{order_id}"
                ),
                InlineKeyboardButton(
                    text=t("btn_partial_confirm", "uz"),
                    callback_data=f"pay:partial:{order_id}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text=t("btn_reject_payment", "uz"),
                    callback_data=f"pay:reject:{order_id}"
                )
            ]
        ])

        await bot.send_photo(
            chat_id=PAYMENT_GROUP_ID,
            photo=file_id,
            caption=group_text,
            reply_markup=group_kb,
            parse_mode="HTML"
        )

        await update_order_status(
            order_id, "payment_sent",
            payment_screenshot_file_id=file_id
        )

        await edit_progress_bar(bot, message.from_user.id, order, "payment_sent")
        await message.answer(t("payment_received", lang))

    except Exception as e:
        logger.exception(f"payment_screenshot error: {e}")


# ==================== ADMIN: TO'LOV TASDIQLASH ====================

@router.callback_query(F.data.startswith("pay:ok:"))
async def confirm_payment(callback: CallbackQuery, bot: Bot) -> None:
    """Admin to'lovni tasdiqlaydi — barcha akkauntlar yetkaziladi"""
    try:
        order_id = int(callback.data.split(":")[2])

        from bot.config import ADMIN_IDS
        is_admin = (callback.from_user.id in ADMIN_IDS or
                    await get_admin_by_telegram_id(callback.from_user.id) is not None)
        if not is_admin:
            await callback.answer(t("access_denied"), show_alert=True)
            return

        order = await get_order_by_id(order_id)
        if not order:
            await callback.answer(t("not_found"), show_alert=True)
            return

        user_telegram_id = order["user_telegram_id"]
        user = await get_user(user_telegram_id)
        lang = user.get("language", "uz") if user else "uz"

        # Band qilingan akkauntlarni sotish
        sold_accounts = await confirm_reserved(order_id, user_telegram_id)

        # Har bir element uchun purchase_count oshirish
        items = await get_order_items(order_id)
        for item in items:
            await increment_purchase_count(item["product_id"])

        # User statistikasini yangilash
        total_qty = sum(i["quantity"] for i in items)
        await increment_user_purchases(user_telegram_id, order["total_amount"])
        await check_and_upgrade_vip(user_telegram_id)

        # Buyurtma statusini yangilash
        await update_order_status(
            order_id, "confirmed",
            payment_verified_by=callback.from_user.id
        )

        # Yangilangan itemlarni qayta o'qish (login/password bilan)
        fresh_items = await get_order_items(order_id)
        accounts_text = build_account_delivery_text(fresh_items, lang)

        # Mijozga akkauntlar yuborish
        delivery_msg = t("order_delivered", lang,
                          order_id=order_id,
                          accounts_text=accounts_text)

        await bot.send_message(
            chat_id=user_telegram_id,
            text=delivery_msg,
            parse_mode="HTML"
        )

        # Video instruksiya yuborish (birinchi mahsulotdan)
        if fresh_items:
            video_id = fresh_items[0].get("instruction_video_file_id")
            if video_id:
                try:
                    await bot.send_video(
                        chat_id=user_telegram_id,
                        video=video_id,
                        caption="📹 Foydalanish bo'yicha instruksiya" if lang == "uz"
                                else "📹 Инструкция по использованию"
                    )
                except Exception:
                    pass

        # Progress bar yangilash
        await edit_progress_bar(bot, user_telegram_id, order, "confirmed")

        # Admin guruhda xabarni yangilash
        await callback.message.edit_caption(
            caption=(callback.message.caption or "") + f"\n\n✅ Tasdiqlandi — @{callback.from_user.username or callback.from_user.id}",
            reply_markup=None
        )
        await callback.answer("✅ Tasdiqlandi")

    except Exception as e:
        logger.exception(f"confirm_payment error: {e}")
        await callback.answer(t("error_general"), show_alert=True)


@router.callback_query(F.data.startswith("pay:reject:"))
async def reject_payment(callback: CallbackQuery, bot: Bot) -> None:
    """Admin to'lovni rad etadi"""
    try:
        order_id = int(callback.data.split(":")[2])

        from bot.config import ADMIN_IDS
        is_admin = (callback.from_user.id in ADMIN_IDS or
                    await get_admin_by_telegram_id(callback.from_user.id) is not None)
        if not is_admin:
            await callback.answer(t("access_denied"), show_alert=True)
            return

        order = await get_order_by_id(order_id)
        if not order:
            await callback.answer(t("not_found"), show_alert=True)
            return

        user_telegram_id = order["user_telegram_id"]
        user = await get_user(user_telegram_id)
        lang = user.get("language", "uz") if user else "uz"

        await release_reserved(order_id)
        await update_order_status(order_id, "cancelled")

        await edit_progress_bar(bot, user_telegram_id, order, "cancelled")

        await bot.send_message(
            chat_id=user_telegram_id,
            text=f"❌ Buyurtma #{order_id} rad etildi. Savol bo'lsa operatorga murojaat qiling." if lang == "uz"
            else f"❌ Заказ #{order_id} отклонён. По вопросам обратитесь к оператору."
        )

        await callback.message.edit_caption(
            caption=(callback.message.caption or "") + f"\n\n❌ Rad etildi — @{callback.from_user.username or callback.from_user.id}",
            reply_markup=None
        )
        await callback.answer("❌ Rad etildi")

    except Exception as e:
        logger.exception(f"reject_payment error: {e}")
        await callback.answer(t("error_general"), show_alert=True)


# ==================== QISMAN TASDIQLASH ====================

@router.callback_query(F.data.startswith("pay:partial:"))
async def partial_confirm_start(callback: CallbackQuery, bot: Bot) -> None:
    """Qisman tasdiqlash — har bir element uchun alohida tugmalar"""
    try:
        order_id = int(callback.data.split(":")[2])

        from bot.config import ADMIN_IDS
        is_admin = (callback.from_user.id in ADMIN_IDS or
                    await get_admin_by_telegram_id(callback.from_user.id) is not None)
        if not is_admin:
            await callback.answer(t("access_denied"), show_alert=True)
            return

        items = await get_order_items(order_id)
        buttons = []
        for item in items:
            name = item.get("name_uz", "?")
            buttons.append([
                InlineKeyboardButton(
                    text=f"✅ {name} x{item['quantity']}",
                    callback_data=f"pay:pok:{order_id}:{item['id']}"
                ),
                InlineKeyboardButton(
                    text="❌",
                    callback_data=f"pay:pno:{order_id}:{item['id']}"
                ),
            ])
        buttons.append([InlineKeyboardButton(
            text="✅ Hammasi tayyor",
            callback_data=f"pay:ok:{order_id}"
        )])

        await callback.message.edit_caption(
            caption=t("order_partial_text", "uz", order_id=order_id),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )
        await callback.answer()
    except Exception as e:
        logger.exception(f"partial_confirm_start error: {e}")
        await callback.answer(t("error_general"), show_alert=True)


@router.callback_query(F.data.startswith("pay:pok:"))
async def partial_item_ok(callback: CallbackQuery, bot: Bot) -> None:
    """Bitta elementni tasdiqlash"""
    try:
        parts = callback.data.split(":")
        order_id = int(parts[2])
        item_id = int(parts[3])

        order = await get_order_by_id(order_id)
        if not order:
            await callback.answer(t("not_found"), show_alert=True)
            return

        user_telegram_id = order["user_telegram_id"]
        user = await get_user(user_telegram_id)
        lang = user.get("language", "uz") if user else "uz"

        items = await get_order_items(order_id)
        target_item = next((i for i in items if i["id"] == item_id), None)
        if not target_item:
            await callback.answer(t("not_found"), show_alert=True)
            return

        # Bu element uchun band qilingan akkauntlarni sotish
        from bot.db.models import sell_account
        from bot.db.database import get_db
        async with get_db() as db:
            cursor = await db.execute("""
                SELECT id FROM accounts
                WHERE reserved_for_order_id = ? AND product_id = ? AND status = 'reserved'
                LIMIT ?
            """, (order_id, target_item["product_id"], target_item["quantity"]))
            acc_rows = await cursor.fetchall()

            for acc_row in acc_rows:
                await sell_account(target_item["product_id"], order_id, user_telegram_id)

        await increment_purchase_count(target_item["product_id"])

        # Status yangilash
        all_items = await get_order_items(order_id)
        delivered = sum(1 for i in all_items if i["status"] == "delivered")
        pending = sum(1 for i in all_items if i["status"] == "pending")

        new_status = "confirmed" if pending == 0 else "partial"
        await update_order_status(order_id, new_status,
                                  payment_verified_by=callback.from_user.id)

        await edit_progress_bar(bot, user_telegram_id, order, new_status)

        fresh_items = await get_order_items(order_id)
        delivered_items = [i for i in fresh_items if i["status"] == "delivered"]
        accounts_text = build_account_delivery_text(delivered_items, lang)

        await bot.send_message(
            chat_id=user_telegram_id,
            text=t("partial_delivered_notify", lang,
                   order_id=order_id,
                   delivered=delivered,
                   pending=pending,
                   accounts_text=accounts_text),
            parse_mode="HTML"
        )

        await callback.answer(f"✅ {delivered} ta yetkazildi")
    except Exception as e:
        logger.exception(f"partial_item_ok error: {e}")
        await callback.answer(t("error_general"), show_alert=True)
