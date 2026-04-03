import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.db.models import get_all_user_telegram_ids, get_user_count
from bot.utils.texts import t

router = Router()


class BroadcastFSM(StatesGroup):
    enter_message = State()
    confirm = State()


@router.callback_query(F.data == "adm_broadcast")
async def broadcast_start(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(t("broadcast_enter_text", "uz"))
    await state.set_state(BroadcastFSM.enter_message)
    await call.answer()


@router.message(BroadcastFSM.enter_message, F.text | F.photo)
async def broadcast_preview(message: Message, state: FSMContext):
    count = await get_user_count()

    if message.photo:
        file_id = message.photo[-1].file_id
        caption = message.caption or ""
        await state.update_data(type="photo", file_id=file_id, text=caption)
    else:
        await state.update_data(type="text", text=message.text)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_confirm_broadcast", "uz"), callback_data="broadcast_confirm")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="adm_main")],
    ])

    preview_text = t("broadcast_confirm", "uz", count=count)
    await message.answer(preview_text, reply_markup=kb, parse_mode="HTML")
    await state.set_state(BroadcastFSM.confirm)


@router.callback_query(F.data == "broadcast_confirm")
async def broadcast_send(call: CallbackQuery, state: FSMContext, bot):
    data = await state.get_data()
    await state.clear()

    user_ids = await get_all_user_telegram_ids()
    total = len(user_ids)
    success = 0
    failed = 0

    status_msg = await call.message.edit_text(
        t("broadcast_sending", "uz", sent=0, total=total)
    )

    for i, uid in enumerate(user_ids, 1):
        try:
            if data.get("type") == "photo":
                await bot.send_photo(uid, data["file_id"], caption=data.get("text", ""),
                                     parse_mode="HTML")
            else:
                await bot.send_message(uid, data["text"], parse_mode="HTML")
            success += 1
        except Exception:
            failed += 1

        if i % 10 == 0:
            try:
                await status_msg.edit_text(
                    t("broadcast_sending", "uz", sent=i, total=total)
                )
            except Exception:
                pass

        await asyncio.sleep(0.05)  # ~20 msgs/sec

    result = t("broadcast_done", "uz", success=success, failed=failed)
    try:
        await status_msg.edit_text(result)
    except Exception:
        await call.message.answer(result)

    await call.answer()
