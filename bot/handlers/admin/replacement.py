"""
Admin: Almashtirish so'rovlari boshqarish
YANGI STRUKTURA: tier yo'q
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.db.models import (
    get_replacement_by_id, update_replacement_status,
    sell_account, get_user,
)
from bot.utils.texts import t

logger = logging.getLogger(__name__)
router = Router()


class AdminReplacementFSM(StatesGroup):
    reject_reason = State()


@router.callback_query(F.data.startswith("adm_repl_ok:"))
async def admin_approve_replacement(call: CallbackQuery, bot):
    try:
        repl_id = int(call.data.split(":")[1])
        replacement = await get_replacement_by_id(repl_id)
        if not replacement:
            await call.answer("Topilmadi", show_alert=True)
            return

        # order_item dan product_id olish
        from bot.db.database import get_db
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT * FROM order_items WHERE id = ?",
                (replacement["order_item_id"],)
            )
            order_item = await cursor.fetchone()

        if not order_item:
            await call.answer("Buyurtma topilmadi", show_alert=True)
            return

        order_item = dict(order_item)

        # User topish
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT u.telegram_id FROM users u JOIN orders o ON o.user_id = u.id WHERE o.id = (SELECT order_id FROM order_items WHERE id = ?)",
                (replacement["order_item_id"],)
            )
            user_row = await cursor.fetchone()

        user_tid = dict(user_row)["telegram_id"] if user_row else None

        # Yangi akkaunt topish va sotish
        account = await sell_account(order_item["product_id"], 0, user_tid or 0)
        if not account:
            await call.answer("Stokda hisob yo'q!", show_alert=True)
            return

        await update_replacement_status(repl_id, "approved", admin_note=f"new_account_id={account['id']}")

        await call.message.edit_reply_markup(reply_markup=None)
        await call.message.answer(f"✅ Almashtirish tasdiqlandi. Hisob: {account['login']}")

        # Foydalanuvchiga xabar
        if user_tid:
            user = await get_user(user_tid)
            lang = user.get("language", "uz") if user else "uz"
            msg = t("replacement_approved", lang,
                    login=account["login"],
                    password=account["password"],
                    expiry=account.get("expiry_date", "—"))
            try:
                await bot.send_message(user_tid, msg, parse_mode="HTML")
            except Exception:
                pass

        await call.answer("✅ Tasdiqlandi")
    except Exception as e:
        logger.exception(f"admin_approve_replacement error: {e}")
        await call.answer(t("error_general"), show_alert=True)


@router.callback_query(F.data.startswith("adm_repl_rej:"))
async def admin_reject_replacement_start(call: CallbackQuery, state: FSMContext):
    repl_id = int(call.data.split(":")[1])
    await state.update_data(repl_id=repl_id)
    await call.message.answer("Rad etish sababini yozing:")
    await state.set_state(AdminReplacementFSM.reject_reason)
    await call.answer()


@router.message(AdminReplacementFSM.reject_reason)
async def admin_reject_reason(message: Message, state: FSMContext, bot):
    try:
        data = await state.get_data()
        repl_id = data["repl_id"]
        reason = message.text
        await state.clear()

        replacement = await get_replacement_by_id(repl_id)
        if replacement:
            await update_replacement_status(repl_id, "rejected", admin_note=reason)

            from bot.db.database import get_db
            async with get_db() as db:
                cursor = await db.execute(
                    "SELECT u.telegram_id, u.language FROM users u WHERE u.id = ?",
                    (replacement["user_id"],)
                )
                user_row = await cursor.fetchone()

            if user_row:
                user = dict(user_row)
                lang = user.get("language", "uz")
                msg = t("replacement_rejected", lang, reason=reason)
                try:
                    await bot.send_message(user["telegram_id"], msg, parse_mode="HTML")
                except Exception:
                    pass

        await message.answer("❌ Rad etildi va foydalanuvchiga xabar yuborildi.")
    except Exception as e:
        logger.exception(f"admin_reject_reason error: {e}")
        await message.answer(t("error_general"))
