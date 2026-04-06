"""
Admin: Buyurtmalar boshqarish
YANGI STRUKTURA: duration_tier yo'q
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.db.models import get_user, get_order_by_id, get_order_items
from bot.utils.texts import t

logger = logging.getLogger(__name__)
router = Router()

STATUS_EMOJI = {
    "pending_payment": "⬜",
    "payment_sent":    "🟩",
    "confirmed":       "✅",
    "partial":         "🟡",
    "cancelled":       "❌",
    "auto_delivered":  "✅",
}


async def get_lang_and_role(user_id: int) -> tuple[str, str | None]:
    from bot.handlers.admin.menu import get_admin_role
    user = await get_user(user_id)
    lang = user.get("language", "uz") if user else "uz"
    role = await get_admin_role(user_id)
    return lang, role


@router.callback_query(F.data == "adm:orders")
async def admin_orders_menu(callback: CallbackQuery) -> None:
    try:
        lang, role = await get_lang_and_role(callback.from_user.id)
        if not role:
            await callback.answer(t("access_denied", lang), show_alert=True)
            return

        from bot.db.database import get_db
        async with get_db() as db:
            cursor = await db.execute("""
                SELECT o.id, o.status, o.total_amount, o.created_at,
                       u.telegram_id as user_tid, u.full_name, u.username
                FROM orders o
                JOIN users u ON u.id = o.user_id
                WHERE o.status IN ('pending_payment', 'payment_sent', 'partial')
                ORDER BY o.created_at DESC
                LIMIT 20
            """)
            orders = [dict(r) for r in await cursor.fetchall()]

        if not orders:
            await callback.message.edit_text(
                "📋 Kutilayotgan buyurtmalar yo'q." if lang == "uz" else "📋 Нет ожидающих заказов.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(text=t("btn_back", lang), callback_data="adm:back")
                ]])
            )
            await callback.answer()
            return

        buttons = []
        for order in orders:
            status_emoji = STATUS_EMOJI.get(order["status"], "⬜")
            name = order.get("full_name") or order.get("username") or str(order["user_tid"])
            buttons.append([InlineKeyboardButton(
                text=f"{status_emoji} #{order['id']} — {name} — {order['total_amount']:,}",
                callback_data=f"adm:ord:{order['id']}"
            )])
        buttons.append([InlineKeyboardButton(text=t("btn_back", lang), callback_data="adm:back")])

        await callback.message.edit_text(
            "📋 Buyurtmalar:" if lang == "uz" else "📋 Заказы:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )
        await callback.answer()
    except Exception as e:
        logger.exception(f"admin_orders_menu error: {e}")
        await callback.answer(t("error_general"), show_alert=True)


@router.callback_query(F.data.startswith("adm:ord:"))
async def admin_order_detail(callback: CallbackQuery) -> None:
    try:
        order_id = int(callback.data.split(":")[2])
        lang, role = await get_lang_and_role(callback.from_user.id)

        if not role:
            await callback.answer(t("access_denied", lang), show_alert=True)
            return

        order = await get_order_by_id(order_id)
        if not order:
            await callback.answer(t("not_found", lang), show_alert=True)
            return

        items = await get_order_items(order_id)

        status_emoji = STATUS_EMOJI.get(order["status"], "⬜")
        items_text = ""
        for item in items:
            name = item.get(f"name_{lang}", item.get("name_uz", "?"))
            status = "✅" if item.get("status") == "delivered" else "⬜"
            items_text += f"{status} {name} x{item['quantity']}\n"

        full_name = order.get("full_name") or "—"
        username = order.get("username") or "—"
        date_str = str(order["created_at"])[:16]

        text = (
            f"📋 <b>Buyurtma #{order_id}</b>\n"
            f"👤 {full_name} (@{username})\n"
            f"📅 {date_str}\n"
            f"Status: {status_emoji} {order['status']}\n"
            f"💰 {order['total_amount']:,} so'm\n\n"
            f"{items_text}"
        )

        buttons = [
            [
                InlineKeyboardButton(text=t("btn_confirm_payment", lang),
                                     callback_data=f"pay:ok:{order_id}"),
                InlineKeyboardButton(text=t("btn_partial_confirm", lang),
                                     callback_data=f"pay:partial:{order_id}"),
            ],
            [InlineKeyboardButton(text=t("btn_reject_payment", lang),
                                  callback_data=f"pay:reject:{order_id}")],
            [InlineKeyboardButton(text=t("btn_back", lang), callback_data="adm:orders")],
        ]

        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
            parse_mode="HTML"
        )
        await callback.answer()
    except Exception as e:
        logger.exception(f"admin_order_detail error: {e}")
        await callback.answer(t("error_general"), show_alert=True)
