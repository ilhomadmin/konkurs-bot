from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command

from bot.db.models import (
    get_all_promo_codes, create_promo_code,
    activate_promo_code, deactivate_promo_code
)
from bot.utils.texts import t

router = Router()


class PromoCreateFSM(StatesGroup):
    enter_code = State()
    enter_discount = State()
    enter_limit = State()
    enter_expiry = State()


@router.callback_query(F.data == "adm_promos")
async def admin_promos(call: CallbackQuery):
    promos = await get_all_promo_codes()
    items = ""
    for p in promos:
        status = "✅" if p["is_active"] else "❌"
        limit_str = str(p["usage_limit"]) if p["usage_limit"] else "∞"
        items += f"• <code>{p['code']}</code> — {p['discount']}% | {p['used_count']}/{limit_str} | {status}\n"

    text = t("promo_list", "uz", items=items or "Hozircha yo'q.")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_create_promo", "uz"), callback_data="adm_promo_create")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="adm_main")],
    ])
    await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data == "adm_promo_create")
async def promo_create_start(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(t("promo_create_code", "uz"))
    await state.set_state(PromoCreateFSM.enter_code)
    await call.answer()


@router.message(PromoCreateFSM.enter_code)
async def promo_code(message: Message, state: FSMContext):
    code = message.text.strip().upper()
    await state.update_data(code=code)
    await message.answer(t("promo_create_discount", "uz"))
    await state.set_state(PromoCreateFSM.enter_discount)


@router.message(PromoCreateFSM.enter_discount)
async def promo_discount(message: Message, state: FSMContext):
    try:
        discount = int(message.text)
        if not 1 <= discount <= 100:
            raise ValueError
    except ValueError:
        await message.answer("❌ 1-100 orasida kiriting:")
        return
    await state.update_data(discount=discount)
    await message.answer(t("promo_create_limit", "uz"))
    await state.set_state(PromoCreateFSM.enter_limit)


@router.message(PromoCreateFSM.enter_limit)
async def promo_limit(message: Message, state: FSMContext):
    try:
        limit = int(message.text)
    except ValueError:
        await message.answer("❌ Raqam kiriting:")
        return
    await state.update_data(limit=limit if limit > 0 else None)
    await message.answer(t("promo_create_expiry", "uz"))
    await state.set_state(PromoCreateFSM.enter_expiry)


@router.message(PromoCreateFSM.enter_expiry)
async def promo_expiry(message: Message, state: FSMContext):
    data = await state.get_data()
    expiry = None

    if message.text.strip() != "/skip":
        expiry = message.text.strip()

    await create_promo_code(
        code=data["code"],
        discount=data["discount"],
        usage_limit=data.get("limit"),
        expires_at=expiry
    )
    await state.clear()
    await message.answer(t("promo_created", "uz", code=data["code"]))
