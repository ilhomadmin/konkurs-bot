from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command

from bot.db.models import (
    get_user_by_telegram_id, get_user_replaceable_items,
    create_replacement, get_all_operators
)
from bot.utils.texts import t

router = Router()


class ReplacementFSM(StatesGroup):
    select_item = State()
    select_reason = State()
    enter_description = State()
    send_screenshot = State()


REASONS = {
    "not_work": {"uz": "❌ Ishlamayapti", "ru": "❌ Не работает"},
    "wrong": {"uz": "⚠️ Noto'g'ri hisob", "ru": "⚠️ Неверный аккаунт"},
    "expired": {"uz": "⏰ Muddatidan oldin tugadi", "ru": "⏰ Истёк раньше срока"},
    "other": {"uz": "💬 Boshqa", "ru": "💬 Другое"},
}


@router.callback_query(F.data == "replacement_start")
async def replacement_start(call: CallbackQuery, state: FSMContext):
    user = await get_user_by_telegram_id(call.from_user.id)
    if not user:
        await call.answer()
        return
    lang = user.get("language", "uz")

    items = await get_user_replaceable_items(user["id"])
    if not items:
        await call.answer(t("replacement_no_items", lang), show_alert=True)
        return

    buttons = []
    for item in items:
        label = f"#{item['order_id']} — {item['product_name']} ({item['tier']})"
        buttons.append([InlineKeyboardButton(
            text=label,
            callback_data=f"repl_item:{item['order_item_id']}"
        )])
    buttons.append([InlineKeyboardButton(text="❌", callback_data="close")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await call.message.edit_text(t("replacement_select_item", lang), reply_markup=kb)
    await state.set_state(ReplacementFSM.select_item)
    await call.answer()


@router.callback_query(F.data.startswith("repl_item:"))
async def replacement_item_selected(call: CallbackQuery, state: FSMContext):
    order_item_id = int(call.data.split(":")[1])
    user = await get_user_by_telegram_id(call.from_user.id)
    lang = user.get("language", "uz")

    await state.update_data(order_item_id=order_item_id)

    buttons = []
    for key, names in REASONS.items():
        buttons.append([InlineKeyboardButton(
            text=names[lang],
            callback_data=f"repl_reason:{key}"
        )])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await call.message.edit_text(t("replacement_select_reason", lang), reply_markup=kb)
    await state.set_state(ReplacementFSM.select_reason)
    await call.answer()


@router.callback_query(F.data.startswith("repl_reason:"))
async def replacement_reason_selected(call: CallbackQuery, state: FSMContext):
    reason_key = call.data.split(":")[1]
    user = await get_user_by_telegram_id(call.from_user.id)
    lang = user.get("language", "uz")

    reason_text = REASONS.get(reason_key, {}).get(lang, reason_key)
    await state.update_data(reason=reason_text)

    await call.message.edit_text(t("replacement_enter_description", lang))
    await state.set_state(ReplacementFSM.enter_description)
    await call.answer()


@router.message(ReplacementFSM.enter_description)
async def replacement_description(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.get("language", "uz")

    await state.update_data(description=message.text)
    await message.answer(t("replacement_send_screenshot", lang))
    await state.set_state(ReplacementFSM.send_screenshot)


@router.message(ReplacementFSM.send_screenshot, F.photo)
async def replacement_screenshot(message: Message, state: FSMContext, bot):
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.get("language", "uz")
    data = await state.get_data()

    screenshot_file_id = message.photo[-1].file_id
    replacement = await create_replacement(
        user_id=user["id"],
        order_item_id=data["order_item_id"],
        reason=data["reason"],
        description=data["description"],
        screenshot_file_id=screenshot_file_id
    )
    await state.clear()

    await message.answer(t("replacement_sent", lang))

    # Notify operators
    await _notify_operators(bot, user, data, replacement, screenshot_file_id)


@router.message(ReplacementFSM.send_screenshot, Command("skip"))
async def replacement_skip_screenshot(message: Message, state: FSMContext, bot):
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.get("language", "uz")
    data = await state.get_data()

    replacement = await create_replacement(
        user_id=user["id"],
        order_item_id=data["order_item_id"],
        reason=data["reason"],
        description=data["description"],
        screenshot_file_id=None
    )
    await state.clear()

    await message.answer(t("replacement_sent", lang))
    await _notify_operators(bot, user, data, replacement, None)


async def _notify_operators(bot, user, data, replacement, screenshot_file_id):
    operators = await get_all_operators()
    username = f"@{user['username']}" if user.get("username") else f"ID:{user['telegram_id']}"

    text = t("replacement_new_request", "uz",
             user=username,
             order_id=replacement["order_item_id"],
             product=replacement.get("product_name", "?"),
             reason=data["reason"],
             description=data["description"])

    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"adm_repl_ok:{replacement['id']}"),
        InlineKeyboardButton(text="❌ Rad etish", callback_data=f"adm_repl_rej:{replacement['id']}"),
    ]])

    for op in operators:
        try:
            if screenshot_file_id:
                await bot.send_photo(op["telegram_id"], screenshot_file_id, caption=text,
                                     reply_markup=kb, parse_mode="HTML")
            else:
                await bot.send_message(op["telegram_id"], text, reply_markup=kb, parse_mode="HTML")
        except Exception:
            pass
