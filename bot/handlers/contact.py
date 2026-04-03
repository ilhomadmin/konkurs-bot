from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.db.models import get_user_by_telegram_id, get_all_operators
from bot.utils.texts import t

router = Router()


class ContactFSM(StatesGroup):
    enter_question = State()


class OperatorReplyFSM(StatesGroup):
    enter_reply = State()


@router.callback_query(F.data == "contact_page")
async def contact_page(call: CallbackQuery, state: FSMContext):
    user = await get_user_by_telegram_id(call.from_user.id)
    lang = user.get("language", "uz") if user else "uz"

    await call.message.edit_text(t("contact_enter_question", lang))
    await state.set_state(ContactFSM.enter_question)
    await call.answer()


@router.message(ContactFSM.enter_question)
async def contact_send_question(message: Message, state: FSMContext, bot):
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.get("language", "uz") if user else "uz"
    await state.clear()

    username = f"@{message.from_user.username}" if message.from_user.username else f"ID:{message.from_user.id}"
    text = t("contact_new_message", "uz",
             user=username,
             user_id=message.from_user.id,
             lang=lang,
             question=message.text)

    operators = await get_all_operators()
    for op in operators:
        try:
            kb = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(
                    text=t("btn_reply", "uz"),
                    callback_data=f"op_reply:{message.from_user.id}"
                )
            ]])
            await bot.send_message(op["telegram_id"], text, reply_markup=kb, parse_mode="HTML")
        except Exception:
            pass

    await message.answer(t("contact_sent", lang))


@router.callback_query(F.data.startswith("op_reply:"))
async def op_reply_start(call: CallbackQuery, state: FSMContext):
    user_id = int(call.data.split(":")[1])
    await state.update_data(target_user_id=user_id)
    await call.message.answer(t("contact_reply_prompt", "uz"))
    await state.set_state(OperatorReplyFSM.enter_reply)
    await call.answer()


@router.message(OperatorReplyFSM.enter_reply)
async def op_send_reply(message: Message, state: FSMContext, bot):
    data = await state.get_data()
    target_id = data["target_user_id"]
    await state.clear()

    # Get target user lang
    target_user = await get_user_by_telegram_id(target_id)
    lang = target_user.get("language", "uz") if target_user else "uz"

    reply_text = t("contact_operator_reply", lang, reply=message.text)
    try:
        await bot.send_message(target_id, reply_text, parse_mode="HTML")
    except Exception:
        pass

    await message.answer(t("contact_reply_sent", "uz"))
