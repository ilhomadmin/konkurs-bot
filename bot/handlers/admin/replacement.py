from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.db.models import (
    get_replacement_by_id, update_replacement_status,
    get_order_item_by_id, get_available_account,
    sell_account, get_user_by_id
)
from bot.utils.texts import t

router = Router()


class AdminReplacementFSM(StatesGroup):
    reject_reason = State()


@router.callback_query(F.data.startswith("adm_repl_ok:"))
async def admin_approve_replacement(call: CallbackQuery, bot):
    repl_id = int(call.data.split(":")[1])
    replacement = await get_replacement_by_id(repl_id)
    if not replacement:
        await call.answer("Topilmadi", show_alert=True)
        return

    order_item = await get_order_item_by_id(replacement["order_item_id"])
    if not order_item:
        await call.answer("Buyurtma topilmadi", show_alert=True)
        return

    account = await get_available_account(order_item["product_id"], order_item["tier"])
    if not account:
        await call.answer("Stokda hisob yo'q!", show_alert=True)
        return

    user_info = await get_user_by_id(replacement["user_id"])
    if user_info:
        await sell_account(account["id"], user_info["telegram_id"], sold_via="replacement")
    await update_replacement_status(repl_id, "approved", new_account_id=account["id"])

    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.answer(f"✅ Almashtirish tasdiqlandi. Hisob: {account['login']}")

    # Notify user
    user = await get_user_by_id(replacement["user_id"])
    if user:
        from datetime import date, timedelta
        from bot.utils.duration import tier_to_days
        days = tier_to_days(order_item["tier"])
        expiry = (date.today() + timedelta(days=days)).isoformat()
        msg = t("replacement_approved", user.get("language", "uz"),
                login=account["login"],
                password=account["password"],
                expiry=expiry)
        try:
            await bot.send_message(user["telegram_id"], msg, parse_mode="HTML")
        except Exception:
            pass

    await call.answer("✅ Tasdiqlandi")


@router.callback_query(F.data.startswith("adm_repl_rej:"))
async def admin_reject_replacement_start(call: CallbackQuery, state: FSMContext):
    repl_id = int(call.data.split(":")[1])
    await state.update_data(repl_id=repl_id)
    await call.message.answer("Rad etish sababini yozing:")
    await state.set_state(AdminReplacementFSM.reject_reason)
    await call.answer()


@router.message(AdminReplacementFSM.reject_reason)
async def admin_reject_reason(message: Message, state: FSMContext, bot):
    data = await state.get_data()
    repl_id = data["repl_id"]
    reason = message.text
    await state.clear()

    replacement = await get_replacement_by_id(repl_id)
    if replacement:
        await update_replacement_status(repl_id, "rejected")
        user = await get_user_by_id(replacement["user_id"])
        if user:
            msg = t("replacement_rejected", user.get("language", "uz"), reason=reason)
            try:
                await bot.send_message(user["telegram_id"], msg, parse_mode="HTML")
            except Exception:
                pass

    await message.answer("❌ Rad etildi va foydalanuvchiga xabar yuborildi.")
