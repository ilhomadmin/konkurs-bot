"""
Mening buyurtmalarim — tarixi, pagination, tafsilot
YANGI STRUKTURA: duration_tier yo'q
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.db.models import (
    get_user, get_user_orders, get_order_by_id, get_order_items,
)
from bot.utils.texts import t

logger = logging.getLogger(__name__)
router = Router()

PAGE_SIZE = 5

STATUS_KEYS = {
    "pending_payment": "order_status_pending",
    "payment_sent":    "order_status_sent",
    "confirmed":       "order_status_confirmed",
    "auto_delivered":  "order_status_confirmed",
    "partial":         "order_status_partial",
    "cancelled":       "order_status_cancelled",
}


def orders_list_kb(orders: list[dict], lang: str, page: int, total: int) -> InlineKeyboardMarkup:
    buttons = []
    total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE or 1

    for order in orders:
        status_key = STATUS_KEYS.get(order["status"], "order_status_pending")
        status_text = t(status_key, lang)
        date_str = str(order["created_at"])[:10]
        buttons.append([InlineKeyboardButton(
            text=f"#{order['id']} — {date_str} | {status_text} | {order['total_amount']:,}",
            callback_data=f"ord:{order['id']}:{page}"
        )])

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(
            text=t("btn_prev_page", lang),
            callback_data=f"ordpage:{page - 1}"
        ))
    nav_row.append(InlineKeyboardButton(
        text=f"{page + 1}/{total_pages}",
        callback_data="noop"
    ))
    if (page + 1) * PAGE_SIZE < total:
        nav_row.append(InlineKeyboardButton(
            text=t("btn_next_page", lang),
            callback_data=f"ordpage:{page + 1}"
        ))
    if nav_row:
        buttons.append(nav_row)

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def order_detail_kb(order_id: int, items: list[dict], lang: str, back_page: int) -> InlineKeyboardMarkup:
    buttons = []

    has_video = any(i.get("instruction_video_file_id") for i in items)
    if has_video:
        buttons.append([InlineKeyboardButton(
            text=t("btn_instruction_video", lang),
            callback_data=f"ordvid:{order_id}"
        )])

    buttons.append([InlineKeyboardButton(
        text=t("btn_back", lang),
        callback_data=f"ordpage:{back_page}"
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(F.text.in_(["📋 Buyurtmalarim", "📋 Мои заказы"]))
async def my_orders(message: Message) -> None:
    try:
        user = await get_user(message.from_user.id)
        lang = user.get("language", "uz") if user else "uz"

        orders = await get_user_orders(message.from_user.id, limit=100)
        total = len(orders)
        if total == 0:
            await message.answer(t("no_orders", lang))
            return

        page_orders = orders[:PAGE_SIZE]
        await message.answer(
            t("my_orders_title", lang),
            reply_markup=orders_list_kb(page_orders, lang, 0, total)
        )
    except Exception as e:
        logger.exception(f"my_orders error: {e}")
        await message.answer(t("error_general"))


@router.callback_query(F.data.startswith("ordpage:"))
async def orders_page(callback: CallbackQuery) -> None:
    try:
        page = int(callback.data.split(":")[1])
        user = await get_user(callback.from_user.id)
        lang = user.get("language", "uz") if user else "uz"

        orders = await get_user_orders(callback.from_user.id, limit=100)
        total = len(orders)
        start = page * PAGE_SIZE
        page_orders = orders[start:start + PAGE_SIZE]

        await callback.message.edit_text(
            t("my_orders_title", lang),
            reply_markup=orders_list_kb(page_orders, lang, page, total)
        )
        await callback.answer()
    except Exception as e:
        logger.exception(f"orders_page error: {e}")
        await callback.answer(t("error_general"), show_alert=True)


@router.callback_query(F.data.startswith("ord:"))
async def order_detail(callback: CallbackQuery) -> None:
    try:
        parts = callback.data.split(":")
        order_id = int(parts[1])
        back_page = int(parts[2]) if len(parts) > 2 else 0

        user = await get_user(callback.from_user.id)
        lang = user.get("language", "uz") if user else "uz"

        order = await get_order_by_id(order_id)
        if not order:
            await callback.answer(t("not_found", lang), show_alert=True)
            return

        # Foydalanuvchi o'z buyurtmasimi tekshirish
        if order.get("telegram_id") != callback.from_user.id:
            await callback.answer(t("access_denied", lang), show_alert=True)
            return

        items = await get_order_items(order_id)

        status_key = STATUS_KEYS.get(order["status"], "order_status_pending")
        status_text = t(status_key, lang)

        item_lines = []
        for item in items:
            name = item.get(f"name_{lang}", item.get("name_uz", "?"))

            if item.get("status") == "delivered" and item.get("login"):
                item_lines.append(t("order_item_detail", lang,
                                    name=name,
                                    qty=item["quantity"],
                                    login=item.get("login", "—"),
                                    password=item.get("password", "—"),
                                    expiry=item.get("expiry_date") or "—"))
            else:
                item_lines.append(t("order_item_pending", lang,
                                    name=name,
                                    qty=item["quantity"]))

        items_text = "\n".join(item_lines)
        date_str = str(order["created_at"])[:16]

        text = t("order_detail", lang,
                 order_id=order_id,
                 date=date_str,
                 status=status_text,
                 amount=order["total_amount"],
                 items=items_text)

        await callback.message.edit_text(
            text,
            reply_markup=order_detail_kb(order_id, items, lang, back_page),
            parse_mode="HTML"
        )
        await callback.answer()
    except Exception as e:
        logger.exception(f"order_detail error: {e}")
        await callback.answer(t("error_general"), show_alert=True)


@router.callback_query(F.data.startswith("ordvid:"))
async def order_instruction_video(callback: CallbackQuery) -> None:
    try:
        order_id = int(callback.data.split(":")[1])
        user = await get_user(callback.from_user.id)
        lang = user.get("language", "uz") if user else "uz"

        items = await get_order_items(order_id)
        for item in items:
            video_id = item.get("instruction_video_file_id")
            if video_id:
                await callback.message.answer_video(
                    video=video_id,
                    caption=t("btn_instruction_video", lang)
                )
                break

        await callback.answer()
    except Exception as e:
        logger.exception(f"order_instruction_video error: {e}")
        await callback.answer(t("error_general"), show_alert=True)
