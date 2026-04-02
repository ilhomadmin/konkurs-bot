"""
Katalog handlerlari — kategoriyalar, mahsulotlar, tier tanlash, savatga qo'shish
"""
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.db.models import (
    get_all_categories, get_category_by_id,
    get_products_by_category, get_product_by_id,
    get_prices_by_product, get_available_count,
    get_product_rating, is_favorite, add_favorite, remove_favorite,
    add_stock_notification, cart_item_in_cart, cart_add, get_user,
)
from bot.utils.texts import t
from bot.utils.duration import tier_display_name

router = Router()

PAGE_SIZE = 5  # Mahsulotlar sahifasida nechta ko'rsatiladi


# ==================== FSM ====================

class QtyInputFSM(StatesGroup):
    """Foydalanuvchi o'zi son kiritganda"""
    qty = State()


# ==================== KLAVIATURALAR ====================

def categories_kb(categories: list[dict], lang: str) -> InlineKeyboardMarkup:
    """Kategoriyalar ro'yxati klaviaturasi"""
    buttons = []
    for cat in categories:
        buttons.append([InlineKeyboardButton(
            text=cat[f"name_{lang}"],
            callback_data=f"cat:{cat['id']}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def products_kb(
    products: list[dict],
    cat_id: int,
    lang: str,
    page: int,
    total: int,
    cart_product_ids: set
) -> InlineKeyboardMarkup:
    """Mahsulotlar ro'yxati klaviaturasi (pagination bilan)"""
    buttons = []
    total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE or 1

    for prod in products:
        name = prod[f"name_{lang}"]
        badge = "🛒 " if prod["id"] in cart_product_ids else ""
        fire = f" 🔥{prod['purchase_count']}" if prod["purchase_count"] > 0 else ""
        buttons.append([InlineKeyboardButton(
            text=f"{badge}{name}{fire}",
            callback_data=f"prod:{prod['id']}:{cat_id}"
        )])

    # Pagination
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text=t("btn_prev_page", lang),
                                             callback_data=f"catpage:{cat_id}:{page - 1}"))
    nav_row.append(InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="noop"))
    if (page + 1) * PAGE_SIZE < total:
        nav_row.append(InlineKeyboardButton(text=t("btn_next_page", lang),
                                             callback_data=f"catpage:{cat_id}:{page + 1}"))
    if nav_row:
        buttons.append(nav_row)

    buttons.append([InlineKeyboardButton(text=t("btn_back", lang), callback_data="cat:back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def product_detail_kb(
    product_id: int,
    prices: list[dict],
    stock_by_tier: dict,
    is_fav: bool,
    lang: str,
    cat_id: int
) -> InlineKeyboardMarkup:
    """Mahsulot sahifasi klaviaturasi — tier tugmalari"""
    buttons = []

    for price in prices:
        tier = price["duration_tier"]
        tier_name = price[f"display_name_{lang}"]
        count = stock_by_tier.get(tier, 0)
        if count > 0:
            btn_text = f"{tier_name} — {price['price']:,} ({count} ta)"
            buttons.append([InlineKeyboardButton(
                text=btn_text,
                callback_data=f"tier:{product_id}:{tier}"
            )])
        else:
            buttons.append([InlineKeyboardButton(
                text=f"{tier_name} — {t('sold_out', lang)}",
                callback_data=f"notify:{product_id}:{tier}"
            )])

    # Sevimlilar tugmasi
    fav_text = t("btn_remove_favorite", lang) if is_fav else t("btn_add_favorite", lang)
    buttons.append([InlineKeyboardButton(
        text=fav_text,
        callback_data=f"fav:toggle:{product_id}:{cat_id}"
    )])

    buttons.append([InlineKeyboardButton(
        text=t("btn_back", lang),
        callback_data=f"catpage:{cat_id}:0"
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def quantity_kb(product_id: int, tier: str, available: int, lang: str) -> InlineKeyboardMarkup:
    """Son tanlash klaviaturasi"""
    qtys = [1, 2, 3, 5]
    buttons = []
    row = []
    for q in qtys:
        if q <= available:
            row.append(InlineKeyboardButton(
                text=str(q),
                callback_data=f"qty:{product_id}:{tier}:{q}"
            ))
    if row:
        buttons.append(row)

    # Boshqa son
    if available > 5:
        buttons.append([InlineKeyboardButton(
            text="✏️ Boshqa son..." if lang == "uz" else "✏️ Другое количество...",
            callback_data=f"qty:{product_id}:{tier}:custom"
        )])

    buttons.append([InlineKeyboardButton(
        text=t("btn_back", lang),
        callback_data=f"prod:{product_id}:back"
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def added_to_cart_kb(product_id: int, cat_id: int, lang: str) -> InlineKeyboardMarkup:
    """Savatga qo'shilgandan keyin tugmalar"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=t("btn_view_cart", lang), callback_data="go:cart"),
            InlineKeyboardButton(text=t("btn_continue", lang), callback_data=f"catpage:{cat_id}:0"),
        ]
    ])


# ==================== HANDLERLAR ====================

@router.message(F.text.in_(["📦 Obunalar", "📦 Подписки"]))
async def catalog_start(message: Message) -> None:
    """Asosiy katalog — kategoriyalar ro'yxati"""
    try:
        user = await get_user(message.from_user.id)
        lang = user.get("language", "uz") if user else "uz"

        categories = await get_all_categories(only_active=True)
        if not categories:
            await message.answer(t("no_categories", lang))
            return

        await message.answer(
            t("select_category", lang),
            reply_markup=categories_kb(categories, lang)
        )
    except Exception:
        await message.answer(t("error_general"))


@router.callback_query(F.data == "cat:back")
async def catalog_back(callback: CallbackQuery) -> None:
    """Kategoriyalar ro'yxatiga qaytish"""
    try:
        user = await get_user(callback.from_user.id)
        lang = user.get("language", "uz") if user else "uz"
        categories = await get_all_categories(only_active=True)
        await callback.message.edit_text(
            t("select_category", lang),
            reply_markup=categories_kb(categories, lang)
        )
        await callback.answer()
    except Exception:
        await callback.answer(t("error_general"), show_alert=True)


@router.callback_query(F.data.startswith("cat:"))
async def category_products(callback: CallbackQuery) -> None:
    """Kategoriya ichidagi mahsulotlar"""
    try:
        cat_id = int(callback.data.split(":")[1])
        user = await get_user(callback.from_user.id)
        lang = user.get("language", "uz") if user else "uz"

        await _show_products_page(callback, lang, cat_id, page=0)
    except Exception:
        await callback.answer(t("error_general"), show_alert=True)


@router.callback_query(F.data.startswith("catpage:"))
async def category_page(callback: CallbackQuery) -> None:
    """Mahsulotlar sahifasi (pagination)"""
    try:
        _, cat_id_str, page_str = callback.data.split(":")
        cat_id = int(cat_id_str)
        page = int(page_str)
        user = await get_user(callback.from_user.id)
        lang = user.get("language", "uz") if user else "uz"

        await _show_products_page(callback, lang, cat_id, page)
    except Exception:
        await callback.answer(t("error_general"), show_alert=True)


async def _show_products_page(callback: CallbackQuery, lang: str, cat_id: int, page: int) -> None:
    """Mahsulotlar sahifasini ko'rsatish (ichki funksiya)"""
    cat = await get_category_by_id(cat_id)
    all_products = await get_products_by_category(cat_id, only_active=True)

    if not all_products:
        await callback.message.edit_text(
            t("no_products_in_cat", lang),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text=t("btn_back", lang), callback_data="cat:back")
            ]])
        )
        await callback.answer()
        return

    # Pagination
    start = page * PAGE_SIZE
    page_products = all_products[start: start + PAGE_SIZE]

    # Savatdagi mahsulotlar IDlarini olish
    from bot.db.models import cart_get
    cart_items = await cart_get(callback.from_user.id)
    cart_product_ids = {item["product_id"] for item in cart_items}

    cat_name = cat[f"name_{lang}"] if cat else ""
    text = f"📦 <b>{cat_name}</b>\n{t('select_product', lang)}"

    await callback.message.edit_text(
        text,
        reply_markup=products_kb(page_products, cat_id, lang, page, len(all_products), cart_product_ids),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("prod:"))
async def product_detail(callback: CallbackQuery) -> None:
    """Mahsulot karta ko'rsatish"""
    try:
        parts = callback.data.split(":")
        product_id = int(parts[1])
        cat_id = int(parts[2]) if len(parts) > 2 and parts[2] != "back" else 0

        user = await get_user(callback.from_user.id)
        lang = user.get("language", "uz") if user else "uz"

        prod = await get_product_by_id(product_id)
        if not prod:
            await callback.answer(t("not_found", lang), show_alert=True)
            return

        if not cat_id:
            cat_id = prod["category_id"]

        # Narxlar va mavjud sonlar
        prices = await get_prices_by_product(product_id)
        stats = await get_available_count(product_id)
        stock_by_tier = stats.get("by_tier", {})

        # Reyting
        rating = await get_product_rating(product_id)

        # Sevimlilar
        fav = await is_favorite(callback.from_user.id, product_id)

        # Savatda bormi
        from bot.db.models import cart_get
        cart_items = await cart_get(callback.from_user.id)
        cart_tiers = {(ci["product_id"], ci["duration_tier"]): ci["quantity"] for ci in cart_items}

        # Mahsulot karta matni
        name = prod[f"name_{lang}"]
        desc = prod.get(f"description_{lang}") or ""

        lines = [f"📦 <b>{name}</b>"]
        if prod["purchase_count"] > 0:
            lines.append(f"🔥 {prod['purchase_count']} marta sotilgan" if lang == "uz"
                         else f"🔥 Продано {prod['purchase_count']} раз")
        if prod["has_warranty"] and prod["warranty_days"] > 0:
            if lang == "uz":
                lines.append(f"🛡 {prod['warranty_days']} kunlik kafolat — ishlamasa almashtiramiz!")
            else:
                lines.append(f"🛡 Гарантия {prod['warranty_days']} дней — заменим если не работает!")
        if rating["count"] > 0:
            lines.append(f"⭐ Reyting: {rating['avg']} ({rating['count']} ta sharh)" if lang == "uz"
                         else f"⭐ Рейтинг: {rating['avg']} ({rating['count']} отзывов)")
        if desc:
            lines.append(f"\n{desc}")

        # Narxlar
        if lang == "uz":
            lines.append("\n💰 Narxlar:")
        else:
            lines.append("\n💰 Цены:")

        for price in prices:
            tier = price["duration_tier"]
            tier_name = price[f"display_name_{lang}"]
            count = stock_by_tier.get(tier, 0)
            qty_in_cart = cart_tiers.get((product_id, tier), 0)

            if count > 0:
                line = f"  ✅ {tier_name} — {price['price']:,} so'm ({count} ta)"
                if qty_in_cart:
                    line += f" | 🛒 {qty_in_cart} ta"
            else:
                line = f"  ❌ {tier_name} — {t('sold_out', lang)}"
            lines.append(line)

        text = "\n".join(lines)

        await callback.message.edit_text(
            text,
            reply_markup=product_detail_kb(product_id, prices, stock_by_tier, fav, lang, cat_id),
            parse_mode="HTML"
        )
        await callback.answer()
    except Exception:
        await callback.answer(t("error_general"), show_alert=True)


@router.callback_query(F.data.startswith("fav:toggle:"))
async def toggle_favorite(callback: CallbackQuery) -> None:
    """Sevimlilarga qo'shish/olib tashlash"""
    try:
        parts = callback.data.split(":")
        product_id = int(parts[2])
        cat_id = int(parts[3]) if len(parts) > 3 else 0

        user = await get_user(callback.from_user.id)
        lang = user.get("language", "uz") if user else "uz"

        fav = await is_favorite(callback.from_user.id, product_id)
        if fav:
            await remove_favorite(callback.from_user.id, product_id)
            await callback.answer(t("removed_from_favorites", lang))
        else:
            await add_favorite(callback.from_user.id, product_id)
            await callback.answer(t("added_to_favorites", lang))

        # Mahsulot kartani yangilash
        # Callback data ni prod:{product_id}:{cat_id} ko'rinishida chaqiramiz
        from aiogram.types import CallbackQuery as CQ
        fake_cb_data = f"prod:{product_id}:{cat_id}"
        callback.data = fake_cb_data
        await product_detail(callback)
    except Exception:
        await callback.answer(t("error_general"), show_alert=True)


@router.callback_query(F.data.startswith("notify:"))
async def stock_notify(callback: CallbackQuery) -> None:
    """Stok bildirishnomaga yozilish"""
    try:
        parts = callback.data.split(":")
        product_id = int(parts[1])
        user = await get_user(callback.from_user.id)
        lang = user.get("language", "uz") if user else "uz"

        await add_stock_notification(callback.from_user.id, product_id)
        await callback.answer(t("stock_notify_set", lang), show_alert=True)
    except Exception:
        await callback.answer(t("error_general"), show_alert=True)


@router.callback_query(F.data.startswith("tier:"))
async def tier_selected(callback: CallbackQuery) -> None:
    """Tier tanlanganda — son tanlash"""
    try:
        _, product_id_str, tier = callback.data.split(":")
        product_id = int(product_id_str)

        user = await get_user(callback.from_user.id)
        lang = user.get("language", "uz") if user else "uz"

        stats = await get_available_count(product_id, tier)
        available = stats.get("available", 0)

        if available == 0:
            await callback.answer(t("sold_out", lang), show_alert=True)
            return

        prod = await get_product_by_id(product_id)
        name = prod[f"name_{lang}"] if prod else ""
        tier_name = tier_display_name(tier, lang)

        text = f"📦 <b>{name}</b> — {tier_name}\n{t('select_quantity', lang, available=available)}"

        await callback.message.edit_text(
            text,
            reply_markup=quantity_kb(product_id, tier, available, lang),
            parse_mode="HTML"
        )
        await callback.answer()
    except Exception:
        await callback.answer(t("error_general"), show_alert=True)


@router.callback_query(F.data.startswith("qty:"))
async def quantity_selected(callback: CallbackQuery, state: FSMContext) -> None:
    """Son tanlanganda savatga qo'shish yoki custom son so'rash"""
    try:
        parts = callback.data.split(":")
        product_id = int(parts[1])
        tier = parts[2]
        qty_str = parts[3]

        user = await get_user(callback.from_user.id)
        lang = user.get("language", "uz") if user else "uz"

        # Mavjud sonni tekshirish
        stats = await get_available_count(product_id, tier)
        available = stats.get("available", 0)

        if qty_str == "custom":
            # Custom son kiritish
            await state.update_data(product_id=product_id, tier=tier, available=available, lang=lang)
            await state.set_state(QtyInputFSM.qty)
            await callback.message.edit_text(
                t("enter_quantity", lang, max=min(available, 99))
            )
            await callback.answer()
            return

        qty = int(qty_str)
        if qty > available:
            await callback.answer(t("qty_exceeds_stock", lang, available=available), show_alert=True)
            return

        await _add_to_cart(callback, lang, product_id, tier, qty, available)
    except Exception:
        await callback.answer(t("error_general"), show_alert=True)


@router.message(QtyInputFSM.qty)
async def custom_qty_input(message: Message, state: FSMContext) -> None:
    """Foydalanuvchi o'zi son kiritganda"""
    data = await state.get_data()
    lang = data.get("lang", "uz")
    available = data.get("available", 1)
    product_id = data["product_id"]
    tier = data["tier"]

    try:
        qty = int(message.text.strip())
    except ValueError:
        await message.answer(t("qty_invalid", lang, max=min(available, 99)))
        return

    if qty < 1 or qty > available:
        await message.answer(t("qty_invalid", lang, max=min(available, 99)))
        return

    await state.clear()

    # Savatga qo'shish
    prod = await get_product_by_id(product_id)
    if not prod:
        await message.answer(t("not_found", lang))
        return

    lang_key = f"name_{lang}"
    name = prod.get(lang_key, prod.get("name_uz", ""))
    tier_name = tier_display_name(tier, lang)
    cat_id = prod.get("category_id", 0)

    await cart_add(message.from_user.id, product_id, tier, qty)

    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=t("btn_view_cart", lang), callback_data="go:cart"),
        InlineKeyboardButton(text=t("btn_continue", lang), callback_data=f"catpage:{cat_id}:0"),
    ]])
    await message.answer(
        t("added_to_cart", lang, name=name, tier=tier_name, qty=qty),
        reply_markup=kb
    )


async def _add_to_cart(
    callback: CallbackQuery,
    lang: str,
    product_id: int,
    tier: str,
    qty: int,
    available: int
) -> None:
    """Savatga qo'shib xabar ko'rsatish"""
    prod = await get_product_by_id(product_id)
    if not prod:
        await callback.answer(t("not_found", lang), show_alert=True)
        return

    lang_key = f"name_{lang}"
    name = prod.get(lang_key, prod.get("name_uz", ""))
    tier_name = tier_display_name(tier, lang)
    cat_id = prod.get("category_id", 0)

    await cart_add(callback.from_user.id, product_id, tier, qty)

    await callback.message.edit_text(
        t("added_to_cart", lang, name=name, tier=tier_name, qty=qty),
        reply_markup=added_to_cart_kb(product_id, cat_id, lang)
    )
    await callback.answer()


@router.callback_query(F.data == "go:cart")
async def go_to_cart(callback: CallbackQuery) -> None:
    """Savatga o'tish"""
    from bot.handlers.cart import show_cart
    await show_cart(callback.message, callback.from_user.id)
    await callback.answer()


@router.callback_query(F.data == "noop")
async def noop(callback: CallbackQuery) -> None:
    """Bo'sh tugma (pagination sahifa raqami)"""
    await callback.answer()
