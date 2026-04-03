"""
To'lov handlerlari:
- Mijoz chek yuboradi
- Bot guruhga forward qiladi
- Admin guruhda tasdiqlaydi → akkauntlar yetkaziladi
"""
import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.config import PAYMENT_GROUP_ID
from bot.db.models import (
    get_user, get_user_active_order, get_order, get_order_items,
    update_order_status, sell_account, update_order_item,
    increment_purchase_count, update_user_stats, update_user_vip,
    get_admin_by_telegram_id,
)
from bot.utils.texts import t
from bot.utils.duration import tier_display_name

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
        name = item[f"name_{lang}"]
        tier_name = tier_display_name(item["duration_tier"], lang)
        login = item.get("login") or "—"
        password = item.get("password") or "—"
        expiry = item.get("account_expiry") or item.get("expiry_date") or "—"
        lines.append(t("account_delivery_line", lang,
                       num=num, name=f"{name} ({tier_name})",
                       login=login, password=password, expiry=expiry))
        num += 1
    return "\n\n".join(lines)


# ==================== CHEK YUBORISH ====================

@router.message(F.photo)
async def payment_screenshot(message: Message, bot: Bot) -> None:
    """
    Mijoz rasm yuboradi — bu to'lov cheki bo'lishi mumkin.
    Foydalanuvchida aktiv buyurtma bo'lsa, guruhga yuboriladi.
    """
    try:
        user = await get_user(message.from_user.id)
        if not user:
            return
        lang = user.get("language", "uz")

        order = await get_user_active_order(message.from_user.id)
        if not order:
            # Aktiv buyurtma yo'q — odatiy foydalanuvchi, ignore
            return

        file_id = message.photo[-1].file_id  # Eng yuqori sifatli rasm
        order_id = order["id"]

        # Buyurtma elementlarini olish
        items = await get_order_items(order_id)
        items_text = ""
        for item in items:
            name = item[f"name_{lang}"]
            tier_name = tier_display_name(item["duration_tier"], lang)
            items_text += f"• {name} ({tier_name}) x{item['quantity']}\n"

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

        # Chekni guruhga yuborish
        await bot.send_photo(
            chat_id=PAYMENT_GROUP_ID,
            photo=file_id,
            caption=group_text,
            reply_markup=group_kb,
            parse_mode="HTML"
        )

        # Buyurtma statusini yangilash
        await update_order_status(
            order_id, "payment_sent",
            payment_screenshot_file_id=file_id
        )

        # Progress bar yangilash
        await edit_progress_bar(bot, message.from_user.id, order, "payment_sent")

        # Mijozga tasdiqlash
        await message.answer(t("payment_received", lang))

    except Exception as e:
        logger.error(f"Chek qabul qilishda xato: {e}")


# ==================== ADMIN: TO'LOV TASDIQLASH ====================

@router.callback_query(F.data.startswith("pay:ok:"))
async def confirm_payment(callback: CallbackQuery, bot: Bot) -> None:
    """Admin to'lovni tasdiqlaydi — barcha akkauntlar yetkaziladi"""
    try:
        order_id = int(callback.data.split(":")[2])

        # Admin tekshirish
        from bot.config import ADMIN_IDS
        is_admin = (callback.from_user.id in ADMIN_IDS or
                    await get_admin_by_telegram_id(callback.from_user.id) is not None)
        if not is_admin:
            await callback.answer(t("access_denied"), show_alert=True)
            return

        order = await get_order(order_id)
        if not order:
            await callback.answer(t("not_found"), show_alert=True)
            return

        user_telegram_id = order["user_telegram_id"]
        user = await get_user(user_telegram_id)
        lang = user.get("language", "uz") if user else "uz"

        # Barcha band qilingan akkauntlarni sotish
        items = await get_order_items(order_id)
        from bot.db.models import get_reserved_accounts_for_order
        reserved_accs = await get_reserved_accounts_for_order(order_id)

        # Akkauntlarni product_id + tier bo'yicha guruhlaymiz
        acc_map: dict[tuple, list] = {}
        for acc in reserved_accs:
            key = (acc["product_id"], acc["duration_tier"])
            acc_map.setdefault(key, []).append(acc)

        delivered_items = []
        for item in items:
            key = (item["product_id"], item["duration_tier"])
            accs_for_item = acc_map.get(key, [])[:item["quantity"]]

            for acc in accs_for_item:
                # Akkauntni sotilgan deb belgilash
                await sell_account(acc["id"], user_telegram_id, "bot_order")
                # order_item ni yangilash
                await update_order_item(
                    item["id"],
                    account_id=acc["id"],
                    status="delivered",
                    delivered_at="CURRENT_TIMESTAMP",
                    expiry_date=acc["expiry_date"]
                )
                await increment_purchase_count(item["product_id"], item["quantity"])

            delivered_items.append(item)

        # User statistikasini yangilash
        total_qty = sum(i["quantity"] for i in items)
        await update_user_stats(user_telegram_id, order["total_amount"], total_qty)
        await update_user_vip(user_telegram_id)

        # Buyurtma statusini yangilash
        await update_order_status(
            order_id, "confirmed",
            payment_verified_by=callback.from_user.id
        )

        # Yangilangan itemlarni qayta o'qish (login/password bilan)
        fresh_items = await get_order_items(order_id)
        for fi in fresh_items:
            fi["status"] = "delivered"  # Hammasi delivered

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
            video_id = (fresh_items[0].get("product_video") or
                        fresh_items[0].get("category_video"))
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
            caption=(callback.message.caption or "") + f"\n\n✅ {t('payment_confirmed_admin', 'uz')} — @{callback.from_user.username or callback.from_user.id}",
            reply_markup=None
        )
        await callback.answer(t("payment_confirmed_admin", "uz"))

    except Exception as e:
        logger.error(f"To'lov tasdiqlashda xato: {e}")
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

        order = await get_order(order_id)
        if not order:
            await callback.answer(t("not_found"), show_alert=True)
            return

        user_telegram_id = order["user_telegram_id"]
        user = await get_user(user_telegram_id)
        lang = user.get("language", "uz") if user else "uz"

        # Akkauntlarni ozod qilish
        from bot.db.models import release_reserved_accounts
        await release_reserved_accounts(order_id)
        await update_order_status(order_id, "cancelled")

        # Progress bar yangilash
        await edit_progress_bar(bot, user_telegram_id, order, "cancelled")

        # Mijozga xabar
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
        logger.error(f"To'lovni rad etishda xato: {e}")
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
            name = item.get("name_uz", "")
            tier_name = tier_display_name(item["duration_tier"], "uz")
            buttons.append([
                InlineKeyboardButton(
                    text=f"✅ {name} ({tier_name}) x{item['quantity']}",
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
        logger.error(f"Qisman tasdiqlashda xato: {e}")
        await callback.answer(t("error_general"), show_alert=True)


@router.callback_query(F.data.startswith("pay:pok:"))
async def partial_item_ok(callback: CallbackQuery, bot: Bot) -> None:
    """Bitta elementni tasdiqlash"""
    try:
        parts = callback.data.split(":")
        order_id = int(parts[2])
        item_id = int(parts[3])

        order = await get_order(order_id)
        if not order:
            await callback.answer(t("not_found"), show_alert=True)
            return

        user_telegram_id = order["user_telegram_id"]
        user = await get_user(user_telegram_id)
        lang = user.get("language", "uz") if user else "uz"

        # Bu elementni deliver qilish
        items = await get_order_items(order_id)
        target_item = next((i for i in items if i["id"] == item_id), None)
        if not target_item:
            await callback.answer(t("not_found"), show_alert=True)
            return

        from bot.db.models import get_reserved_accounts_for_order
        reserved_accs = await get_reserved_accounts_for_order(order_id)
        accs_for_item = [a for a in reserved_accs
                         if a["product_id"] == target_item["product_id"]
                         and a.get("duration_tier") == target_item["duration_tier"]]

        for acc in accs_for_item[:target_item["quantity"]]:
            await sell_account(acc["id"], user_telegram_id, "bot_order")
            await update_order_item(item_id,
                                    account_id=acc["id"],
                                    status="delivered",
                                    delivered_at="CURRENT_TIMESTAMP",
                                    expiry_date=acc["expiry_date"])
            await increment_purchase_count(target_item["product_id"])

        # Status yangilash
        all_items = await get_order_items(order_id)
        delivered = sum(1 for i in all_items if i["status"] == "delivered")
        pending = sum(1 for i in all_items if i["status"] == "pending")

        new_status = "confirmed" if pending == 0 else "partial"
        await update_order_status(order_id, new_status,
                                  payment_verified_by=callback.from_user.id)

        # Progress bar
        await edit_progress_bar(bot, user_telegram_id, order, new_status)

        # Mijozga tayyor bo'lgan akkauntlarni yuborish
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
        logger.error(f"Qisman tasdiqlashda xato: {e}")
        await callback.answer(t("error_general"), show_alert=True)
