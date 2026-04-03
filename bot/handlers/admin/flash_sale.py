from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.db.models import (
    create_flash_sale, get_active_flash_sale,
    get_all_products_flat, get_all_user_telegram_ids
)
from bot.utils.texts import t
import asyncio

router = Router()


class FlashSaleFSM(StatesGroup):
    select_product = State()
    enter_discount = State()
    enter_duration = State()


@router.callback_query(F.data == "adm_flash_sale")
async def admin_flash_sale(call: CallbackQuery, state: FSMContext):
    active = await get_active_flash_sale()
    if active:
        remaining = active["ends_at"]
        text = f"⚡ Faol Flash Sale: <b>{active['product_name']}</b>\n{active['discount']}% chegirma\n⏳ {remaining} gacha"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="adm_main")]
        ])
        await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        await call.answer()
        return

    products = await get_all_products_flat()
    buttons = []
    for p in products[:20]:
        buttons.append([InlineKeyboardButton(
            text=f"{p['name']} ({p['tier']})",
            callback_data=f"fs_prod:{p['product_id']}:{p['tier']}"
        )])
    buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="adm_main")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await call.message.edit_text(t("flash_sale_create_product", "uz"), reply_markup=kb)
    await state.set_state(FlashSaleFSM.select_product)
    await call.answer()


@router.callback_query(F.data.startswith("fs_prod:"), FlashSaleFSM.select_product)
async def fs_product_selected(call: CallbackQuery, state: FSMContext):
    parts = call.data.split(":")
    product_id = int(parts[1])
    tier = parts[2]
    await state.update_data(product_id=product_id, tier=tier)
    await call.message.edit_text(t("flash_sale_create_discount", "uz"))
    await state.set_state(FlashSaleFSM.enter_discount)
    await call.answer()


@router.message(FlashSaleFSM.enter_discount)
async def fs_discount(message: Message, state: FSMContext):
    try:
        discount = int(message.text)
        if not 1 <= discount <= 100:
            raise ValueError
    except ValueError:
        await message.answer("❌ 1-100 orasida kiriting:")
        return
    await state.update_data(discount=discount)
    await message.answer(t("flash_sale_create_duration", "uz"))
    await state.set_state(FlashSaleFSM.enter_duration)


@router.message(FlashSaleFSM.enter_duration)
async def fs_duration(message: Message, state: FSMContext, bot):
    try:
        hours = int(message.text)
        if hours < 1:
            raise ValueError
    except ValueError:
        await message.answer("❌ Musbat raqam kiriting:")
        return

    data = await state.get_data()
    ends_at = (datetime.now() + timedelta(hours=hours)).isoformat(timespec="minutes")

    flash = await create_flash_sale(
        product_id=data["product_id"],
        tier=data["tier"],
        discount=data["discount"],
        ends_at=ends_at
    )
    await state.clear()
    await message.answer(t("flash_sale_created", "uz", discount=data["discount"], hours=hours))

    # Broadcast flash sale
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Xarid qilish", callback_data=f"prod:{data['product_id']}")]
    ])
    product_name = flash.get("product_name", "Mahsulot")
    notif = t("flash_sale_active", "uz",
              product=product_name,
              discount=data["discount"],
              time_left=ends_at)

    user_ids = await get_all_user_telegram_ids()
    for uid in user_ids:
        try:
            await bot.send_message(uid, notif, reply_markup=kb, parse_mode="HTML")
        except Exception:
            pass
        await asyncio.sleep(0.05)
