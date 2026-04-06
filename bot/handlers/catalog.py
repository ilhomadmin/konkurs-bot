"""
Katalog handlerlari — turkumlar, obuna turlari, savatga qo'shish
YANGI STRUKTURA: Turkum (ixtiyoriy) → Obuna turi → Savatga
"""
import logging
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.db.models import (
    get_all_categories, get_category_by_id,
    get_products_by_category, get_all_products, get_product_by_id,
    get_product_stock, get_product_avg_rating,
    is_in_favorites, add_to_favorites, remove_from_favorites,
    add_stock_notification, cart_get, cart_add, get_user,
)
from bot.utils.texts import t

logger = logging.getLogger(__name__)
router = Router()
PAGE_SIZE = 5


class QtyInputFSM(StatesGroup):
    qty = State()


# ==================== KLAVIATURALAR ====================

def categories_kb(categories: list[dict], lang: str) -> InlineKeyboardMarkup:
    buttons = []
    for cat in categories:
        buttons.append([InlineKeyboardButton(
            text=cat[f"name_{lang}"],
            callback_data=f"cat:{cat['id']}"
        )])
    # "Hammasi" tugmasi
    buttons.append([InlineKeyboardButton(
        text="📋 Hammasi" if lang == "uz" else "📋 Все",
        callback_data="cat:all"
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def products_kb(
    products: list[dict],
    cat_id: int | str,
    lang: str,
    page: int,
    total: int,
    cart_product_ids: set
) -> InlineKeyboardMarkup:
    buttons = []
    total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE or 1

    for prod in products:
        name = prod[f"name_{lang}"]
        stock = prod.get("stock", 0)
        badge = "🛒 " if prod["id"] in cart_product_ids else ""
        fire = f" 🔥{prod['purchase_count']}" if prod.get("purchase_count", 0) > 0 else ""
        stock_txt = f" ({stock})" if stock > 0 else " ❌"
        price_txt = f" {prod['price']:,}" if prod.get("price") else ""
        buttons.append([InlineKeyboardButton(
            text=f"{badge}{name}{price_txt}{stock_txt}{fire}",
            callback_data=f"prod:{prod['id']}:{cat_id}"
        )])

    # Pagination
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="⬅️",
                                             callback_data=f"catpage:{cat_id}:{page - 1}"))
    nav_row.append(InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="noop"))
    if (page + 1) * PAGE_SIZE < total:
        nav_row.append(InlineKeyboardButton(text="➡️",
                                             callback_data=f"catpage:{cat_id}:{page + 1}"))
    if len(nav_row) > 1:
        buttons.append(nav_row)

    buttons.append([InlineKeyboardButton(text=t("btn_back", lang), callback_data="cat:back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def product_detail_kb(
    product_id: int,
    stock: int,
    is_fav: bool,
    lang: str,
    cat_id: int | str
) -> InlineKeyboardMarkup:
    buttons = []

    if stock > 0:
        buttons.append([InlineKeyboardButton(
            text="🛒 Savatga qo'shish" if lang == "uz" else "🛒 Добавить в корзину",
            callback_data=f"addcart:{product_id}"
        )])
    else:
        buttons.append([InlineKeyboardButton(
            text="🔔 Xabar berish" if lang == "uz" else "🔔 Уведомить",
            callback_data=f"notify:{product_id}"
        )])

    fav_text = "💔 Sevimlilardan" if is_fav else "❤️ Sevimlilarga"
    if lang == "ru":
        fav_text = "💔 Из избранного" if is_fav else "❤️ В избранное"
    buttons.append([InlineKeyboardButton(
        text=fav_text,
        callback_data=f"fav:toggle:{product_id}:{cat_id}"
    )])

    buttons.append([InlineKeyboardButton(
        text=t("btn_back", lang),
        callback_data=f"catpage:{cat_id}:0"
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def quantity_kb(product_id: int, available: int, lang: str) -> InlineKeyboardMarkup:
    qtys = [1, 2, 3, 5]
    buttons = []
    row = []
    for q in qtys:
        if q <= available:
            row.append(InlineKeyboardButton(
                text=str(q),
                callback_data=f"qty:{product_id}:{q}"
            ))
    if row:
        buttons.append(row)

    if available > 5:
        buttons.append([InlineKeyboardButton(
            text="✏️ Boshqa son..." if lang == "uz" else "✏️ Другое кол-во...",
            callback_data=f"qty:{product_id}:custom"
        )])

    buttons.append([InlineKeyboardButton(
        text=t("btn_back", lang),
        callback_data=f"prod:{product_id}:back"
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ==================== HANDLERLAR ====================

@router.message(F.text.in_(["📦 Obunalar", "📦 Подписки"]))
async def catalog_start(message: Message) -> None:
    try:
        user = await get_user(message.from_user.id)
        lang = user.get("language", "uz") if user else "uz"

        categories = await get_all_categories(only_active=True)
        if not categories:
            # Turkumsiz — to'g'ri mahsulotlar
            prods = await get_all_products(only_active=True)
            if not prods:
                await message.answer(t("no_products", lang))
                return
            cart_items = await cart_get(message.from_user.id)
            cart_pids = {ci["product_id"] for ci in cart_items}
            await message.answer(
                t("select_product", lang),
                reply_markup=products_kb(prods[:PAGE_SIZE], "all", lang, 0, len(prods), cart_pids)
            )
            return

        await message.answer(
            t("select_category", lang),
            reply_markup=categories_kb(categories, lang)
        )
    except Exception as e:
        logger.exception(f"catalog_start error: {e}")
        await message.answer(t("error_general"))


@router.callback_query(F.data == "catalog_main")
async def catalog_main_cb(callback: CallbackQuery) -> None:
    try:
        user = await get_user(callback.from_user.id)
        lang = user.get("language", "uz") if user else "uz"
        categories = await get_all_categories(only_active=True)
        if categories:
            await callback.message.edit_text(
                t("select_category", lang),
                reply_markup=categories_kb(categories, lang)
            )
        else:
            prods = await get_all_products(only_active=True)
            cart_items = await cart_get(callback.from_user.id)
            cart_pids = {ci["product_id"] for ci in cart_items}
            await callback.message.edit_text(
                t("select_product", lang),
                reply_markup=products_kb(prods[:PAGE_SIZE], "all", lang, 0, len(prods), cart_pids)
            )
        await callback.answer()
    except Exception as e:
        logger.exception(f"catalog_main error: {e}")
        await callback.answer()


@router.callback_query(F.data == "cat:back")
async def catalog_back(callback: CallbackQuery) -> None:
    await catalog_main_cb(callback)


@router.callback_query(F.data.startswith("cat:"))
async def category_products(callback: CallbackQuery) -> None:
    try:
        cat_key = callback.data.split(":")[1]
        user = await get_user(callback.from_user.id)
        lang = user.get("language", "uz") if user else "uz"
        await _show_products_page(callback, lang, cat_key, page=0)
    except Exception as e:
        logger.exception(f"category_products error: {e}")
        await callback.answer(t("error_general"), show_alert=True)


@router.callback_query(F.data.startswith("catpage:"))
async def category_page(callback: CallbackQuery) -> None:
    try:
        parts = callback.data.split(":")
        cat_key = parts[1]
        page = int(parts[2])
        user = await get_user(callback.from_user.id)
        lang = user.get("language", "uz") if user else "uz"
        await _show_products_page(callback, lang, cat_key, page)
    except Exception as e:
        logger.exception(f"category_page error: {e}")
        await callback.answer(t("error_general"), show_alert=True)


async def _show_products_page(callback: CallbackQuery, lang: str, cat_key: str, page: int) -> None:
    if cat_key == "all":
        all_products = await get_all_products(only_active=True)
        title = "📦 " + ("Barcha obunalar" if lang == "uz" else "Все подписки")
    else:
        cat_id = int(cat_key)
        cat = await get_category_by_id(cat_id)
        all_products = await get_products_by_category(cat_id, only_active=True)
        title = f"📦 <b>{cat[f'name_{lang}'] if cat else ''}</b>"

    if not all_products:
        await callback.message.edit_text(
            t("no_products_in_cat", lang),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text=t("btn_back", lang), callback_data="cat:back")
            ]])
        )
        await callback.answer()
        return

    start = page * PAGE_SIZE
    page_products = all_products[start: start + PAGE_SIZE]

    cart_items = await cart_get(callback.from_user.id)
    cart_pids = {ci["product_id"] for ci in cart_items}

    text = f"{title}\n{t('select_product', lang)}"
    await callback.message.edit_text(
        text,
        reply_markup=products_kb(page_products, cat_key, lang, page, len(all_products), cart_pids),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("prod:"))
async def product_detail(callback: CallbackQuery) -> None:
    try:
        parts = callback.data.split(":")
        product_id = int(parts[1])
        cat_id = parts[2] if len(parts) > 2 and parts[2] != "back" else "all"

        user = await get_user(callback.from_user.id)
        lang = user.get("language", "uz") if user else "uz"

        prod = await get_product_by_id(product_id)
        if not prod:
            await callback.answer(t("not_found", lang), show_alert=True)
            return

        if cat_id == "all" and prod.get("category_id"):
            cat_id = str(prod["category_id"])

        stock = await get_product_stock(product_id)
        rating = await get_product_avg_rating(product_id)
        fav = await is_in_favorites(user["id"], product_id) if user else False

        # Product card
        name = prod[f"name_{lang}"]
        desc = prod.get(f"description_{lang}") or ""
        dur = prod.get(f"duration_text_{lang}") or ""

        lines = [f"📦 <b>{name}</b>"]
        if dur:
            lines.append(f"📅 {dur}")
        lines.append(f"💰 <b>{prod['price']:,} so'm</b>")
        if stock > 0:
            lines.append(f"📊 {'Mavjud' if lang == 'uz' else 'В наличии'}: <b>{stock}</b> ta")
        else:
            lines.append(f"❌ {'Hozircha yo\\'q' if lang == 'uz' else 'Нет в наличии'}")

        if prod.get("purchase_count", 0) > 0:
            lines.append(f"🔥 {prod['purchase_count']} {'marta sotilgan' if lang == 'uz' else 'раз продано'}")
        if prod.get("has_warranty") and prod.get("warranty_days", 0) > 0:
            lines.append(f"🛡 {prod['warranty_days']} {'kunlik kafolat' if lang == 'uz' else 'дней гарантии'}")
        if rating and rating > 0:
            lines.append(f"⭐ {rating:.1f}")
        if desc:
            lines.append(f"\n{desc}")

        text = "\n".join(lines)
        await callback.message.edit_text(
            text,
            reply_markup=product_detail_kb(product_id, stock, fav, lang, cat_id),
            parse_mode="HTML"
        )
        await callback.answer()
    except Exception as e:
        logger.exception(f"product_detail error: {e}")
        await callback.answer(t("error_general"), show_alert=True)


@router.callback_query(F.data.startswith("addcart:"))
async def add_to_cart_start(callback: CallbackQuery) -> None:
    """Son tanlash sahifasi"""
    try:
        product_id = int(callback.data.split(":")[1])
        user = await get_user(callback.from_user.id)
        lang = user.get("language", "uz") if user else "uz"

        stock = await get_product_stock(product_id)
        if stock == 0:
            await callback.answer(t("sold_out", lang), show_alert=True)
            return

        prod = await get_product_by_id(product_id)
        name = prod[f"name_{lang}"] if prod else ""

        text = f"📦 <b>{name}</b>\n{t('select_quantity', lang, available=stock)}"
        await callback.message.edit_text(
            text,
            reply_markup=quantity_kb(product_id, stock, lang),
            parse_mode="HTML"
        )
        await callback.answer()
    except Exception as e:
        logger.exception(f"add_to_cart_start error: {e}")
        await callback.answer(t("error_general"), show_alert=True)


@router.callback_query(F.data.startswith("qty:"))
async def quantity_selected(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        parts = callback.data.split(":")
        product_id = int(parts[1])
        qty_str = parts[2]

        user = await get_user(callback.from_user.id)
        lang = user.get("language", "uz") if user else "uz"

        stock = await get_product_stock(product_id)

        if qty_str == "custom":
            await state.update_data(product_id=product_id, available=stock, lang=lang)
            await state.set_state(QtyInputFSM.qty)
            await callback.message.edit_text(
                t("enter_quantity", lang, max=min(stock, 99))
            )
            await callback.answer()
            return

        qty = int(qty_str)
        if qty > stock:
            await callback.answer(t("qty_exceeds_stock", lang, available=stock), show_alert=True)
            return

        await _add_to_cart(callback, lang, product_id, qty)
    except Exception as e:
        logger.exception(f"quantity_selected error: {e}")
        await callback.answer(t("error_general"), show_alert=True)


@router.message(QtyInputFSM.qty)
async def custom_qty_input(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uz")
    available = data.get("available", 1)
    product_id = data["product_id"]

    try:
        qty = int(message.text.strip())
    except ValueError:
        await message.answer(t("qty_invalid", lang, max=min(available, 99)))
        return

    if qty < 1 or qty > available:
        await message.answer(t("qty_invalid", lang, max=min(available, 99)))
        return

    await state.clear()

    prod = await get_product_by_id(product_id)
    if not prod:
        await message.answer(t("not_found", lang))
        return

    name = prod.get(f"name_{lang}", prod.get("name_uz", ""))
    cat_id = prod.get("category_id") or "all"

    await cart_add(message.from_user.id, product_id, qty)

    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=t("btn_view_cart", lang), callback_data="go:cart"),
        InlineKeyboardButton(text=t("btn_continue", lang), callback_data=f"catpage:{cat_id}:0"),
    ]])
    await message.answer(
        t("added_to_cart_simple", lang, name=name, qty=qty),
        reply_markup=kb
    )


async def _add_to_cart(callback: CallbackQuery, lang: str, product_id: int, qty: int) -> None:
    prod = await get_product_by_id(product_id)
    if not prod:
        await callback.answer(t("not_found", lang), show_alert=True)
        return

    name = prod.get(f"name_{lang}", prod.get("name_uz", ""))
    cat_id = prod.get("category_id") or "all"

    await cart_add(callback.from_user.id, product_id, qty)

    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=t("btn_view_cart", lang), callback_data="go:cart"),
        InlineKeyboardButton(text=t("btn_continue", lang), callback_data=f"catpage:{cat_id}:0"),
    ]])
    await callback.message.edit_text(
        t("added_to_cart_simple", lang, name=name, qty=qty),
        reply_markup=kb
    )
    await callback.answer()


@router.callback_query(F.data.startswith("fav:toggle:"))
async def toggle_favorite(callback: CallbackQuery) -> None:
    try:
        parts = callback.data.split(":")
        product_id = int(parts[2])
        cat_id = parts[3] if len(parts) > 3 else "all"

        user = await get_user(callback.from_user.id)
        lang = user.get("language", "uz") if user else "uz"

        fav = await is_in_favorites(user["id"], product_id)
        if fav:
            await remove_from_favorites(user["id"], product_id)
            await callback.answer(t("favorites_removed", lang))
        else:
            await add_to_favorites(user["id"], product_id)
            await callback.answer(t("favorites_added", lang))

        callback.data = f"prod:{product_id}:{cat_id}"
        await product_detail(callback)
    except Exception as e:
        logger.exception(f"toggle_favorite error: {e}")
        await callback.answer(t("error_general"), show_alert=True)


@router.callback_query(F.data.startswith("notify:"))
async def stock_notify(callback: CallbackQuery) -> None:
    try:
        product_id = int(callback.data.split(":")[1])
        user = await get_user(callback.from_user.id)
        lang = user.get("language", "uz") if user else "uz"
        await add_stock_notification(callback.from_user.id, product_id)
        await callback.answer(t("stock_notify_set", lang), show_alert=True)
    except Exception as e:
        logger.exception(f"stock_notify error: {e}")
        await callback.answer(t("error_general"), show_alert=True)


@router.callback_query(F.data == "go:cart")
async def go_to_cart(callback: CallbackQuery) -> None:
    from bot.handlers.cart import show_cart
    await show_cart(callback.message, callback.from_user.id)
    await callback.answer()


@router.callback_query(F.data == "noop")
async def noop(callback: CallbackQuery) -> None:
    await callback.answer()
