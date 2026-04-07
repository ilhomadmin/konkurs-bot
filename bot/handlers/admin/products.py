"""
Admin: Kategoriya va obuna turi (mahsulot) boshqarish handlerlar
YANGI STRUKTURA: Narx to'g'ridan-to'g'ri product da, tier yo'q
"""
import logging
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.db.models import (
    create_category, get_all_categories, get_category_by_id,
    update_category, delete_category,
    create_product, get_products_by_category, get_product_by_id,
    update_product, delete_product, get_product_stock,
)
from bot.keyboards.admin_kb import (
    categories_list_kb, category_actions_kb, confirm_delete_kb,
    products_list_kb, product_actions_kb,
)
from bot.keyboards.common import back_kb
from bot.utils.texts import t

logger = logging.getLogger(__name__)
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
    duration_text_uz = State()
    duration_text_ru = State()
    price = State()
    cost_price = State()
    desc_uz = State()
    desc_ru = State()
    warranty = State()
    warranty_days = State()
    video = State()


# ==================== HELPER ====================

async def get_lang_and_role(user_id: int) -> tuple[str, str | None]:
    from bot.db.models import get_user
    from bot.handlers.admin.menu import get_admin_role
    user = await get_user(user_id)
    lang = user.get("language", "uz") if user else "uz"
    role = await get_admin_role(user_id)
    return lang, role


# ==================== KATEGORIYALAR ====================

@router.callback_query(F.data == "adm:cat:list")
async def categories_list_handler(callback: CallbackQuery) -> None:
    try:
        lang, role = await get_lang_and_role(callback.from_user.id)
        if not role or role not in ("manager", "boss"):
            await callback.answer(t("access_denied", lang), show_alert=True)
            return

        categories = await get_all_categories()
        text = t("categories_list", lang) if categories else t("no_categories", lang)
        await callback.message.edit_text(text, reply_markup=categories_list_kb(categories, lang))
        await callback.answer()
    except Exception as e:
        logger.exception(f"categories_list error: {e}")
        await callback.answer(t("error_general"), show_alert=True)


@router.callback_query(F.data == "adm:cat:add")
async def add_category_start(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        lang, role = await get_lang_and_role(callback.from_user.id)
        if not role or role not in ("manager", "boss"):
            await callback.answer(t("access_denied", lang), show_alert=True)
            return
        await state.update_data(lang=lang)
        await state.set_state(AddCategoryFSM.name_uz)
        await callback.message.edit_text(t("ask_category_name_uz", lang))
        await callback.answer()
    except Exception as e:
        logger.exception(f"add_category_start error: {e}")
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
    data = await state.get_data()
    lang = data.get("lang", "uz")
    video_file_id = None
    if message.video:
        video_file_id = message.video.file_id
    elif message.text and message.text.strip() != "/skip":
        video_file_id = message.text.strip()

    try:
        await create_category(
            name_uz=data["name_uz"],
            name_ru=data["name_ru"],
            description_uz=data.get("desc_uz"),
            description_ru=data.get("desc_ru"),
        )
        await state.clear()
        await message.answer(
            t("category_created", lang),
            reply_markup=back_kb("adm:cat:list", lang)
        )
    except Exception as e:
        logger.exception(f"category_video error: {e}")
        await state.clear()
        await message.answer(f"{t('error_general', lang)}\n{e}")


@router.callback_query(F.data.startswith("adm:cat:") & ~F.data.in_({"adm:cat:list", "adm:cat:add"}))
async def category_detail(callback: CallbackQuery) -> None:
    try:
        parts = callback.data.split(":")
        lang, role = await get_lang_and_role(callback.from_user.id)
        if not role or role not in ("manager", "boss"):
            await callback.answer(t("access_denied", lang), show_alert=True)
            return

        if parts[2] == "toggle" and len(parts) >= 4:
            cat_id = int(parts[3])
            cat = await get_category_by_id(cat_id)
            if cat:
                await update_category(cat_id, is_active=0 if cat["is_active"] else 1)
                cat = await get_category_by_id(cat_id)
            await callback.message.edit_text(
                f"{cat['name_uz']}\n{'✅ Faol' if cat['is_active'] else '🔴 Nofaol'}",
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
            cat_id = int(parts[2])
            cat = await get_category_by_id(cat_id)
            if not cat:
                await callback.answer(t("not_found", lang), show_alert=True)
                return
            status = "✅ Faol" if cat["is_active"] else "🔴 Nofaol"
            text = (
                f"🗂 <b>{cat['name_uz']}</b> / {cat['name_ru']}\n"
                f"{cat.get('description_uz') or ''}\n"
                f"Holat: {status}"
            )
            await callback.message.edit_text(
                text, reply_markup=category_actions_kb(cat_id, lang), parse_mode="HTML"
            )
        await callback.answer()
    except Exception as e:
        logger.exception(f"category_detail error: {e}")
        await callback.answer(t("error_general"), show_alert=True)


# ==================== OBUNA TURLARI (MAHSULOTLAR) ====================

@router.callback_query(F.data.startswith("adm:prod:list:"))
async def products_list_handler(callback: CallbackQuery) -> None:
    try:
        lang, role = await get_lang_and_role(callback.from_user.id)
        if not role or role not in ("manager", "boss"):
            await callback.answer(t("access_denied", lang), show_alert=True)
            return

        cat_id = int(callback.data.split(":")[3])
        cat = await get_category_by_id(cat_id)
        products = await get_products_by_category(cat_id)

        cat_name = cat[f'name_{lang}'] if cat else ''
        text = f"📦 <b>{cat_name}</b>\n"
        text += t('products_list', lang) if products else t('no_products', lang)

        await callback.message.edit_text(
            text, reply_markup=products_list_kb(products, cat_id, lang), parse_mode="HTML"
        )
        await callback.answer()
    except Exception as e:
        logger.exception(f"products_list error: {e}")
        await callback.answer(t("error_general"), show_alert=True)


@router.callback_query(F.data.startswith("adm:prod:add:"))
async def add_product_start(callback: CallbackQuery, state: FSMContext) -> None:
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
    except Exception as e:
        logger.exception(f"add_product_start error: {e}")
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
    await state.set_state(AddProductFSM.duration_text_uz)
    await message.answer(t("ask_duration_text_uz", lang))


@router.message(AddProductFSM.duration_text_uz)
async def product_duration_uz(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uz")
    text = None if message.text.strip() == "/skip" else message.text.strip()
    await state.update_data(duration_text_uz=text)
    await state.set_state(AddProductFSM.duration_text_ru)
    await message.answer(t("ask_duration_text_ru", lang))


@router.message(AddProductFSM.duration_text_ru)
async def product_duration_ru(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uz")
    text = None if message.text.strip() == "/skip" else message.text.strip()
    await state.update_data(duration_text_ru=text)
    await state.set_state(AddProductFSM.price)
    await message.answer(t("ask_price", lang))


@router.message(AddProductFSM.price)
async def product_price(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uz")
    try:
        price = int(message.text.strip().replace(" ", "").replace(",", ""))
    except ValueError:
        await message.answer(t("invalid_number", lang))
        return
    await state.update_data(price=price)
    await state.set_state(AddProductFSM.cost_price)
    await message.answer(t("ask_cost_price", lang))


@router.message(AddProductFSM.cost_price)
async def product_cost_price(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uz")
    try:
        cost_price = int(message.text.strip().replace(" ", "").replace(",", ""))
    except ValueError:
        await message.answer(t("invalid_number", lang))
        return
    await state.update_data(cost_price=cost_price)
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
    data = await state.get_data()
    lang = data.get("lang", "uz")

    video_file_id = None
    if message.video:
        video_file_id = message.video.file_id
    elif message.text and message.text.strip() != "/skip":
        video_file_id = message.text.strip()

    try:
        prod_id = await create_product(
            name_uz=data["name_uz"],
            name_ru=data["name_ru"],
            price=data["price"],
            cost_price=data.get("cost_price", 0),
            category_id=data.get("category_id"),
            description_uz=data.get("desc_uz"),
            description_ru=data.get("desc_ru"),
            duration_text_uz=data.get("duration_text_uz"),
            duration_text_ru=data.get("duration_text_ru"),
            has_warranty=data.get("has_warranty", False),
            warranty_days=data.get("warranty_days", 0),
        )
        await state.clear()

        stock = await get_product_stock(prod_id)
        text = t("product_created", lang) + f"\n💰 {data['price']:,} so'm | 📦 Stok: {stock}"
        await message.answer(
            text,
            reply_markup=back_kb(f"adm:prod:list:{data.get('category_id', 0)}", lang)
        )
    except Exception as e:
        logger.exception(f"product_video error: {e}")
        await state.clear()
        await message.answer(f"{t('error_general', lang)}\n{e}")


@router.callback_query(F.data.startswith("adm:prod:"))
async def product_detail(callback: CallbackQuery) -> None:
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
                f"{prod['name_uz']}\n{'✅ Faol' if prod['is_active'] else '🔴 Nofaol'}",
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
            prod_id = int(parts[3])
            prod = await get_product_by_id(prod_id)
            if prod:
                cat_id = prod.get("category_id", 0)
                products = await get_products_by_category(cat_id) if cat_id else []
                await callback.message.edit_text(
                    t("products_list", lang),
                    reply_markup=products_list_kb(products, cat_id, lang)
                )

        else:
            try:
                prod_id = int(action)
            except ValueError:
                await callback.answer()
                return

            prod = await get_product_by_id(prod_id)
            if not prod:
                await callback.answer(t("not_found", lang), show_alert=True)
                return

            stock = await get_product_stock(prod_id)
            warranty = ""
            if prod["has_warranty"]:
                warranty = f"\n🛡 Kafolat: {prod['warranty_days']} kun"

            duration = ""
            if prod.get("duration_text_uz"):
                duration = f"\n⏱ {prod['duration_text_uz']}"

            status = "✅ Faol" if prod["is_active"] else "🔴 Nofaol"
            text = (
                f"📦 <b>{prod['name_uz']}</b> / {prod['name_ru']}\n"
                f"{prod.get('description_uz') or ''}"
                f"{duration}{warranty}\n"
                f"💰 Narx: {prod['price']:,} so'm | Tannarx: {prod.get('cost_price', 0):,}\n"
                f"📦 Stok: {stock}\n"
                f"Holat: {status}"
            )
            await callback.message.edit_text(
                text, reply_markup=product_actions_kb(prod_id, lang), parse_mode="HTML"
            )

        await callback.answer()
    except Exception as e:
        logger.exception(f"product_detail error: {e}")
        await callback.answer(t("error_general"), show_alert=True)
