from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.db.models import create_bundle, add_bundle_item, get_all_bundles, get_all_products_flat
from bot.utils.texts import t

router = Router()


class BundleCreateFSM(StatesGroup):
    enter_name = State()
    enter_desc = State()
    enter_price = State()


@router.callback_query(F.data == "adm_bundles")
async def admin_bundles(call: CallbackQuery):
    bundles = await get_all_bundles()
    text = "📦 <b>To'plamlar</b>\n\n"
    if bundles:
        for b in bundles:
            text += f"• {b['name']} — {b['price']:,} so'm\n"
    else:
        text += "Hozircha yo'q."

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Yangi to'plam", callback_data="adm_bundle_create")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="adm_main")],
    ])
    await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data == "adm_bundle_create")
async def bundle_create_start(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(t("bundle_create_name", "uz"))
    await state.set_state(BundleCreateFSM.enter_name)
    await call.answer()


@router.message(BundleCreateFSM.enter_name)
async def bundle_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(t("bundle_create_desc", "uz"))
    await state.set_state(BundleCreateFSM.enter_desc)


@router.message(BundleCreateFSM.enter_desc)
async def bundle_desc(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer(t("bundle_create_price", "uz"))
    await state.set_state(BundleCreateFSM.enter_price)


@router.message(BundleCreateFSM.enter_price)
async def bundle_price(message: Message, state: FSMContext):
    try:
        price = int(message.text.replace(" ", "").replace(",", ""))
    except ValueError:
        await message.answer("❌ Noto'g'ri format. Raqam kiriting:")
        return

    data = await state.get_data()
    bundle = await create_bundle(data["name"], data.get("description", ""), price)
    await state.clear()

    # Now let admin add items
    products = await get_all_products_flat()
    buttons = []
    for p in products[:20]:  # Max 20
        buttons.append([InlineKeyboardButton(
            text=f"{p['name']} ({p['tier']})",
            callback_data=f"adm_bundle_additem:{bundle['id']}:{p['product_id']}:{p['tier']}"
        )])
    buttons.append([InlineKeyboardButton(
        text="✅ Tugallash",
        callback_data="adm_bundles"
    )])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await message.answer(
        t("bundle_created", "uz", name=data["name"]) + "\n\nMahsulotlarni qo'shing:",
        reply_markup=kb
    )


@router.callback_query(F.data.startswith("adm_bundle_additem:"))
async def bundle_add_item(call: CallbackQuery):
    parts = call.data.split(":")
    bundle_id = int(parts[1])
    product_id = int(parts[2])
    tier = parts[3]

    await add_bundle_item(bundle_id, product_id, tier)
    await call.answer("✅ Qo'shildi!")
