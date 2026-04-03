"""
Admin: Kategoriya va mahsulot boshqarish handlerlar
FSMContext bilan step-by-step jarayon
"""
from datetime import date
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

from bot.db.models import (
    create_category, get_all_categories, get_category_by_id,
    update_category, delete_category,
    create_product, get_products_by_category, get_product_by_id,
    update_product, delete_product,
    create_product_price, get_prices_by_product,
)
from bot.keyboards.admin_kb import (
    categories_list_kb, category_actions_kb, confirm_delete_kb,
    products_list_kb, product_actions_kb, prices_list_kb, tier_select_kb,
)
from bot.keyboards.common import back_kb
from bot.utils.texts import t
from bot.utils.duration import TIER_DISPLAY, TIER_MIN_MAX

router = Router()


# ==================== FSM STATES ====================

class AddCategoryFSM(StatesGroup):
    name_uz = State()
    name_ru = State()
    desc_uz = State()
    desc_ru = State()
    video = State()


class AddProductFSM(StatesGroup):
    name_uz = State()
    name_ru = State()
    desc_uz = State()
    desc_ru = State()
    warranty = State()
    warranty_days = State()
    video = State()


class AddPriceFSM(StatesGroup):
    tier = State()
    price = State()
    cost_price = State()


# ==================== HELPER ====================

async def get_lang_and_role(user_id: int) -> tuple[str, str | None]:
    """Foydalanuvchi tili va rolini qaytaradi"""
    from bot.db.models import get_user
    from bot.handlers.admin.menu import get_admin_role
    user = await get_user(user_id)
    lang = user.get("language", "uz") if user else "uz"
    role = await get_admin_role(user_id)
    return lang, role


# ==================== KATEGORIYALAR ====================

@router.callback_query(F.data == "adm:cat:list")
async def categories_list(callback: CallbackQuery) -> None:
    """Kategoriyalar ro'yxatini ko'rsatish"""
    try:
        lang, role = await get_lang_and_role(callback.from_user.id)
        if not role or role not in ("manager", "boss"):
            await callback.answer(t("access_denied", lang), show_alert=True)
            return

        categories = await get_all_categories()
        if categories:
            text = t("categories_list", lang)
        else:
            text = t("no_categories", lang)

        await callback.message.edit_text(
            text,
            reply_markup=categories_list_kb(categories, lang)
        )
        await callback.answer()
    except Exception:
        await callback.answer(t("error_general"), show_alert=True)


@router.callback_query(F.data == "adm:cat:add")
async def add_category_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Kategoriya qo'shish jarayonini boshlash"""
    try:
        lang, role = await get_lang_and_role(callback.from_user.id)
        if not role or role not in ("manager", "boss"):
            await callback.answer(t("access_denied", lang), show_alert=True)
            return

        await state.update_data(lang=lang)
        await state.set_state(AddCategoryFSM.name_uz)
        await callback.message.edit_text(t("ask_category_name_uz", lang))
        await callback.answer()
    except Exception:
        await callback.answer(t("error_general"), show_alert=True)


@router.message(AddCategoryFSM.name_uz)
async def category_name_uz(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uz")
    await state.update_data(name_uz=message.text.strip())
    await state.set_state(AddCategoryFSM.name_ru)
    await message.answer(t("ask_category_name_ru", lang))


@router.message(AddCategoryFSM.name_ru)
async def category_name_ru(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uz")
    await state.update_data(name_ru=message.text.strip())
    await state.set_state(AddCategoryFSM.desc_uz)
    await message.answer(t("ask_category_desc_uz", lang))


@router.message(AddCategoryFSM.desc_uz)
async def category_desc_uz(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uz")
    desc = None if message.text.strip() == "/skip" else message.text.strip()
    await state.update_data(desc_uz=desc)
    await state.set_state(AddCategoryFSM.desc_ru)
    await message.answer(t("ask_category_desc_ru", lang))


@router.message(AddCategoryFSM.desc_ru)
async def category_desc_ru(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uz")
    desc = None if message.text.strip() == "/skip" else message.text.strip()
    await state.update_data(desc_ru=desc)
    await state.set_state(AddCategoryFSM.video)
    await message.answer(t("ask_category_video", lang))


@router.message(AddCategoryFSM.video)
async def category_video(message: Message, state: FSMContext) -> None:
    """Video yoki /skip — kategoriyani DB ga saqlash"""
    data = await state.get_data()
    lang = data.get("lang", "uz")

    video_file_id = None
    if message.video:
        video_file_id = message.video.file_id
    elif message.text and message.text.strip() != "/skip":
        # Matn video ID sifatida qabul qilinadi (test uchun)
        video_file_id = message.text.strip()

    try:
        cat_id = await create_category(
            name_uz=data["name_uz"],
            name_ru=data["name_ru"],
            description_uz=data.get("desc_uz"),
            description_ru=data.get("desc_ru"),
            instruction_video_file_id=video_file_id
        )
        await state.clear()
        await message.answer(
            t("category_created", lang),
            reply_markup=back_kb("adm:cat:list", lang)
        )
    except Exception as e:
        await state.clear()
        await message.answer(f"{t('error_general', lang)}\n{e}")


@router.callback_query(F.data.startswith("adm:cat:") & ~F.data.in_({"adm:cat:list", "adm:cat:add"}))
async def category_detail(callback: CallbackQuery) -> None:
    """Kategoriya tafsilotlari"""
    try:
        parts = callback.data.split(":")
        lang, role = await get_lang_and_role(callback.from_user.id)

        if not role or role not in ("manager", "boss"):
            await callback.answer(t("access_denied", lang), show_alert=True)
            return

        # adm:cat:toggle:ID yoki adm:cat:del:ID yoki adm:cat:ID
        if parts[2] == "toggle" and len(parts) >= 4:
            cat_id = int(parts[3])
            cat = await get_category_by_id(cat_id)
            if cat:
                new_active = 0 if cat["is_active"] else 1
                await update_category(cat_id, is_active=new_active)
                cat = await get_category_by_id(cat_id)
            await callback.message.edit_text(
                f"{cat['name_' + lang]}\n{'✅ Faol' if cat['is_active'] else '🔴 Nofaol'}",
                reply_markup=category_actions_kb(cat_id, lang)
            )

        elif parts[2] == "del" and len(parts) >= 4:
            cat_id = int(parts[3])
            await callback.message.edit_text(
                t("confirm_delete", lang),
                reply_markup=confirm_delete_kb(f"adm:cat:delok:{cat_id}", lang)
            )

        elif parts[2] == "delok" and len(parts) >= 4:
            cat_id = int(parts[3])
            await delete_category(cat_id)
            await callback.message.edit_text(
                t("category_deleted", lang),
                reply_markup=back_kb("adm:cat:list", lang)
            )

        else:
            # adm:cat:ID — kategoriya tafsiloti
            cat_id = int(parts[2])
            cat = await get_category_by_id(cat_id)
            if not cat:
                await callback.answer(t("not_found", lang), show_alert=True)
                return
            status = "✅ Faol" if cat["is_active"] else "🔴 Nofaol"
            text = (
                f"🗂 <b>{cat['name_' + lang]}</b>\n"
                f"{cat.get('description_' + lang) or ''}\n"
                f"Holat: {status}"
            )
            await callback.message.edit_text(
                text,
                reply_markup=category_actions_kb(cat_id, lang),
                parse_mode="HTML"
            )

        await callback.answer()
    except Exception as e:
        await callback.answer(t("error_general"), show_alert=True)


# ==================== MAHSULOTLAR ====================

@router.callback_query(F.data.startswith("adm:prod:list:"))
async def products_list(callback: CallbackQuery) -> None:
    """Kategoriya mahsulotlari ro'yxati"""
    try:
        lang, role = await get_lang_and_role(callback.from_user.id)
        if not role or role not in ("manager", "boss"):
            await callback.answer(t("access_denied", lang), show_alert=True)
            return

        cat_id = int(callback.data.split(":")[3])
        cat = await get_category_by_id(cat_id)
        products = await get_products_by_category(cat_id)

        if products:
            text = f"📦 <b>{cat['name_' + lang] if cat else ''}</b>\n{t('products_list', lang)}"
        else:
            text = f"📦 <b>{cat['name_' + lang] if cat else ''}</b>\n{t('no_products', lang)}"

        await callback.message.edit_text(
            text,
            reply_markup=products_list_kb(products, cat_id, lang),
            parse_mode="HTML"
        )
        await callback.answer()
    except Exception:
        await callback.answer(t("error_general"), show_alert=True)


@router.callback_query(F.data.startswith("adm:prod:add:"))
async def add_product_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Mahsulot qo'shish jarayonini boshlash"""
    try:
        lang, role = await get_lang_and_role(callback.from_user.id)
        if not role or role not in ("manager", "boss"):
            await callback.answer(t("access_denied", lang), show_alert=True)
            return

        cat_id = int(callback.data.split(":")[3])
        await state.update_data(lang=lang, category_id=cat_id)
        await state.set_state(AddProductFSM.name_uz)
        await callback.message.edit_text(t("ask_product_name_uz", lang))
        await callback.answer()
    except Exception:
        await callback.answer(t("error_general"), show_alert=True)


@router.message(AddProductFSM.name_uz)
async def product_name_uz(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uz")
    await state.update_data(name_uz=message.text.strip())
    await state.set_state(AddProductFSM.name_ru)
    await message.answer(t("ask_product_name_ru", lang))


@router.message(AddProductFSM.name_ru)
async def product_name_ru(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uz")
    await state.update_data(name_ru=message.text.strip())
    await state.set_state(AddProductFSM.desc_uz)
    await message.answer(t("ask_product_desc_uz", lang))


@router.message(AddProductFSM.desc_uz)
async def product_desc_uz(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uz")
    desc = None if message.text.strip() == "/skip" else message.text.strip()
    await state.update_data(desc_uz=desc)
    await state.set_state(AddProductFSM.desc_ru)
    await message.answer(t("ask_product_desc_ru", lang))


@router.message(AddProductFSM.desc_ru)
async def product_desc_ru(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uz")
    desc = None if message.text.strip() == "/skip" else message.text.strip()
    await state.update_data(desc_ru=desc)
    await state.set_state(AddProductFSM.warranty)

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=t("btn_warranty_yes", lang), callback_data="prod:warranty:yes"),
            InlineKeyboardButton(text=t("btn_warranty_no", lang), callback_data="prod:warranty:no"),
        ]
    ])
    await message.answer(t("ask_product_warranty", lang), reply_markup=kb)


@router.callback_query(F.data.startswith("prod:warranty:"), AddProductFSM.warranty)
async def product_warranty(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uz")
    has_warranty = callback.data.endswith("yes")
    await state.update_data(has_warranty=has_warranty)

    if has_warranty:
        await state.set_state(AddProductFSM.warranty_days)
        await callback.message.edit_text(t("ask_warranty_days", lang))
    else:
        await state.update_data(warranty_days=0)
        await state.set_state(AddProductFSM.video)
        await callback.message.edit_text(t("ask_product_video", lang))
    await callback.answer()


@router.message(AddProductFSM.warranty_days)
async def product_warranty_days(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uz")
    try:
        days = int(message.text.strip())
    except ValueError:
        await message.answer(t("invalid_number", lang))
        return
    await state.update_data(warranty_days=days)
    await state.set_state(AddProductFSM.video)
    await message.answer(t("ask_product_video", lang))


@router.message(AddProductFSM.video)
async def product_video(message: Message, state: FSMContext) -> None:
    """Video yoki /skip — mahsulotni DB ga saqlash"""
    data = await state.get_data()
    lang = data.get("lang", "uz")

    video_file_id = None
    if message.video:
        video_file_id = message.video.file_id
    elif message.text and message.text.strip() != "/skip":
        video_file_id = message.text.strip()

    try:
        prod_id = await create_product(
            category_id=data["category_id"],
            name_uz=data["name_uz"],
            name_ru=data["name_ru"],
            description_uz=data.get("desc_uz"),
            description_ru=data.get("desc_ru"),
            instruction_video_file_id=video_file_id,
            has_warranty=data.get("has_warranty", False),
            warranty_days=data.get("warranty_days", 0)
        )
        await state.clear()
        await message.answer(
            t("product_created", lang),
            reply_markup=prices_list_kb([], prod_id, lang)
        )
    except Exception as e:
        await state.clear()
        await message.answer(f"{t('error_general', lang)}\n{e}")


@router.callback_query(F.data.startswith("adm:prod:"))
async def product_detail(callback: CallbackQuery) -> None:
    """Mahsulot tafsilotlari va amallari"""
    try:
        parts = callback.data.split(":")
        lang, role = await get_lang_and_role(callback.from_user.id)

        if not role or role not in ("manager", "boss"):
            await callback.answer(t("access_denied", lang), show_alert=True)
            return

        action = parts[2] if len(parts) > 2 else ""

        if action == "toggle" and len(parts) >= 4:
            prod_id = int(parts[3])
            prod = await get_product_by_id(prod_id)
            if prod:
                await update_product(prod_id, is_active=0 if prod["is_active"] else 1)
                prod = await get_product_by_id(prod_id)
            await callback.message.edit_text(
                f"{prod['name_' + lang]}\n{'✅ Faol' if prod['is_active'] else '🔴 Nofaol'}",
                reply_markup=product_actions_kb(prod_id, lang)
            )

        elif action == "del" and len(parts) >= 4:
            prod_id = int(parts[3])
            await callback.message.edit_text(
                t("confirm_delete", lang),
                reply_markup=confirm_delete_kb(f"adm:prod:delok:{prod_id}", lang)
            )

        elif action == "delok" and len(parts) >= 4:
            prod_id = int(parts[3])
            await delete_product(prod_id)
            await callback.message.edit_text(
                t("product_deleted", lang),
                reply_markup=back_kb("adm:cat:list", lang)
            )

        elif action == "back" and len(parts) >= 4:
            # Kategoriyaga qaytish
            prod_id = int(parts[3])
            prod = await get_product_by_id(prod_id)
            if prod:
                cat_id = prod["category_id"]
                products = await get_products_by_category(cat_id)
                await callback.message.edit_text(
                    t("products_list", lang),
                    reply_markup=products_list_kb(products, cat_id, lang)
                )

        else:
            # adm:prod:ID — mahsulot tafsiloti
            try:
                prod_id = int(action)
            except ValueError:
                await callback.answer()
                return

            prod = await get_product_by_id(prod_id)
            if not prod:
                await callback.answer(t("not_found", lang), show_alert=True)
                return

            warranty = ""
            if prod["has_warranty"]:
                warranty = f"\n🛡 Kafolat: {prod['warranty_days']} kun" if lang == "uz" else f"\n🛡 Гарантия: {prod['warranty_days']} дней"

            status = "✅ Faol" if prod["is_active"] else "🔴 Nofaol"
            text = (
                f"📦 <b>{prod['name_' + lang]}</b>\n"
                f"{prod.get('description_' + lang) or ''}"
                f"{warranty}\n"
                f"Holat: {status}"
            )
            await callback.message.edit_text(
                text,
                reply_markup=product_actions_kb(prod_id, lang),
                parse_mode="HTML"
            )

        await callback.answer()
    except Exception as e:
        await callback.answer(t("error_general"), show_alert=True)


# ==================== NARX TIERLARI ====================

@router.callback_query(F.data.startswith("adm:price:list:"))
async def prices_list(callback: CallbackQuery) -> None:
    """Narx tierlari ro'yxati"""
    try:
        lang, role = await get_lang_and_role(callback.from_user.id)
        if not role or role not in ("manager", "boss"):
            await callback.answer(t("access_denied", lang), show_alert=True)
            return

        prod_id = int(callback.data.split(":")[3])
        prices = await get_prices_by_product(prod_id)
        prod = await get_product_by_id(prod_id)

        text = f"💰 <b>{prod['name_' + lang] if prod else ''}</b>\n{t('prices_menu', lang)}"
        if not prices:
            text += f"\n{t('no_prices', lang)}"

        await callback.message.edit_text(
            text,
            reply_markup=prices_list_kb(prices, prod_id, lang),
            parse_mode="HTML"
        )
        await callback.answer()
    except Exception:
        await callback.answer(t("error_general"), show_alert=True)


@router.callback_query(F.data.startswith("adm:price:add:"))
async def add_price_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Narx tier qo'shish jarayonini boshlash"""
    try:
        lang, role = await get_lang_and_role(callback.from_user.id)
        if not role or role not in ("manager", "boss"):
            await callback.answer(t("access_denied", lang), show_alert=True)
            return

        prod_id = int(callback.data.split(":")[3])
        await state.update_data(lang=lang, product_id=prod_id)
        await state.set_state(AddPriceFSM.tier)
        await callback.message.edit_text(
            t("ask_tier_select", lang),
            reply_markup=tier_select_kb(lang, prod_id)
        )
        await callback.answer()
    except Exception:
        await callback.answer(t("error_general"), show_alert=True)


@router.callback_query(F.data.startswith("adm:tier:"), AddPriceFSM.tier)
async def price_tier_selected(callback: CallbackQuery, state: FSMContext) -> None:
    """Tier tanlanganda"""
    data = await state.get_data()
    lang = data.get("lang", "uz")
    # adm:tier:TIER:PROD_ID
    parts = callback.data.split(":")
    tier = parts[2]
    await state.update_data(selected_tier=tier)
    await state.set_state(AddPriceFSM.price)
    await callback.message.edit_text(t("ask_price", lang))
    await callback.answer()


@router.message(AddPriceFSM.price)
async def price_amount(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uz")
    try:
        price = int(message.text.strip().replace(" ", "").replace(",", ""))
    except ValueError:
        await message.answer(t("invalid_number", lang))
        return
    await state.update_data(price=price)
    await state.set_state(AddPriceFSM.cost_price)
    await message.answer(t("ask_cost_price", lang))


@router.message(AddPriceFSM.cost_price)
async def price_cost(message: Message, state: FSMContext) -> None:
    """Tannarx kiritilgandan keyin — DB ga saqlash"""
    data = await state.get_data()
    lang = data.get("lang", "uz")
    try:
        cost_price = int(message.text.strip().replace(" ", "").replace(",", ""))
    except ValueError:
        await message.answer(t("invalid_number", lang))
        return

    tier = data["selected_tier"]
    prod_id = data["product_id"]
    min_days, max_days = TIER_MIN_MAX[tier]
    display_uz = TIER_DISPLAY[tier]["uz"]
    display_ru = TIER_DISPLAY[tier]["ru"]

    try:
        await create_product_price(
            product_id=prod_id,
            duration_tier=tier,
            display_name_uz=display_uz,
            display_name_ru=display_ru,
            min_days=min_days,
            max_days=max_days,
            price=data["price"],
            cost_price=cost_price
        )
        await state.clear()
        prices = await get_prices_by_product(prod_id)
        await message.answer(
            t("price_created", lang),
            reply_markup=prices_list_kb(prices, prod_id, lang)
        )
    except Exception as e:
        await state.clear()
        await message.answer(f"{t('error_general', lang)}\n{e}")
