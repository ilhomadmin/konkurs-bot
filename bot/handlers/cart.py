"""
Savat handlerlari — ko'rish, son o'zgartirish, promo kod, buyurtma berish
"""
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.db.models import (
    get_user, cart_get, cart_update_qty, cart_remove_item, cart_clear,
    get_promo_by_code, get_vip_level,
)
from bot.utils.texts import t
from bot.utils.duration import tier_display_name

router = Router()


# ==================== FSM ====================

class PromoFSM(StatesGroup):
    code = State()


# ==================== KLAVIATURA ====================

def cart_kb(items: list[dict], lang: str, promo_applied: bool = False) -> InlineKeyboardMarkup:
    """Savat klaviaturasi — har element uchun -/+ va o'chirish"""
    buttons = []
    for item in items:
        tier_name = tier_display_name(item["duration_tier"], lang)
        name = item[f"name_{lang}"]
        # -/+ / o'chirish qatori
        buttons.append([
            InlineKeyboardButton(
                text="➖",
                callback_data=f"cart:dec:{item['product_id']}:{item['duration_tier']}"
            ),
            InlineKeyboardButton(
                text=f"{name} ({tier_name}) x{item['quantity']}",
                callback_data="noop"
            ),
            InlineKeyboardButton(
                text="➕",
                callback_data=f"cart:inc:{item['product_id']}:{item['duration_tier']}"
            ),
            InlineKeyboardButton(
                text="🗑",
                callback_data=f"cart:del:{item['id']}"
            ),
        ])

    # Pastki tugmalar
    bottom = []
    if not promo_applied:
        bottom.append(InlineKeyboardButton(text=t("btn_promo", lang), callback_data="cart:promo"))
    bottom.append(InlineKeyboardButton(text=t("btn_clear_cart", lang), callback_data="cart:clear"))
    buttons.append(bottom)

    buttons.append([
        InlineKeyboardButton(text=t("btn_checkout", lang), callback_data="cart:checkout"),
        InlineKeyboardButton(text=t("btn_back", lang), callback_data="cat:back"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ==================== SAVAT MATNINI HISOBLASH ====================

async def build_cart_text(
    user_id: int,
    items: list[dict],
    lang: str,
    promo: dict | None = None
) -> tuple[str, int, int, int]:
    """
    Savat matnini va summalarni hisoblaydi.
    Returns: (text, total, discount_amount, final_amount)
    """
    user = await get_user(user_id)
    if not user:
        return t("cart_empty", lang), 0, 0, 0

    lines = [t("cart_title", lang)]

    # VIP daraja
    vip_level = user.get("vip_level", "standard")
    vip_info = await get_vip_level(vip_level)
    vip_pct = vip_info["discount_percent"] if vip_info else 0
    vip_name = vip_info[f"display_name_{lang}"] if vip_info else "Oddiy"

    if vip_pct > 0:
        lines.append(t("cart_vip_line", lang, vip_name=vip_name, pct=vip_pct))

    # Elementlar
    total = 0
    for i, item in enumerate(items, 1):
        name = item[f"name_{lang}"]
        tier_name = tier_display_name(item["duration_tier"], lang)
        price = item["price"] * item["quantity"]
        total += price
        lines.append(t("cart_item_line", lang,
                       num=i, name=name, tier=tier_name,
                       qty=item["quantity"], price=price))

    lines.append("")
    lines.append(t("cart_total", lang, total=total))

    # Chegirma hisoblash: max(vip, promo)
    promo_pct = promo["discount_percent"] if promo else 0
    final_pct = max(vip_pct, promo_pct)
    discount_amount = int(total * final_pct / 100)
    final_amount = total - discount_amount

    if final_pct > 0:
        if promo_pct >= vip_pct and promo:
            label = f"🏷 Promo ({promo['code']})"
            icon = "🏷"
        else:
            label = vip_name
            icon = "💎"
        lines.append(t("cart_discount_line", lang,
                       icon=icon, label=label, pct=final_pct, amount=discount_amount))

    lines.append(t("cart_final", lang, final=final_amount))

    return "\n".join(lines), total, discount_amount, final_amount


# ==================== HANDLERLAR ====================

async def show_cart(
    message: Message,
    user_id: int,
    promo: dict | None = None,
    edit: bool = False
) -> None:
    """Savatni ko'rsatish (message yoki edit sifatida)"""
    user = await get_user(user_id)
    lang = user.get("language", "uz") if user else "uz"

    items = await cart_get(user_id)
    if not items:
        text = t("cart_empty", lang)
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text=t("btn_go_catalog", lang), callback_data="cat:back")
        ]])
        if edit:
            await message.edit_text(text, reply_markup=kb)
        else:
            await message.answer(text, reply_markup=kb)
        return

    text, total, discount, final = await build_cart_text(user_id, items, lang, promo)

    kb = cart_kb(items, lang, promo_applied=promo is not None)
    if edit:
        await message.edit_text(text, reply_markup=kb)
    else:
        await message.answer(text, reply_markup=kb)


@router.message(F.text.in_(["🛒 Savat", "🛒 Корзина"]))
async def cart_handler(message: Message) -> None:
    """Savat tugmasi bosilganda"""
    try:
        await show_cart(message, message.from_user.id)
    except Exception:
        await message.answer(t("error_general"))


@router.callback_query(F.data.startswith("cart:inc:"))
async def cart_increase(callback: CallbackQuery) -> None:
    """Miqdorni oshirish"""
    try:
        _, _, product_id_str, tier = callback.data.split(":")
        product_id = int(product_id_str)
        user = await get_user(callback.from_user.id)
        lang = user.get("language", "uz") if user else "uz"

        # Joriy miqdorni topish
        from bot.db.models import cart_item_in_cart
        item = await cart_item_in_cart(callback.from_user.id, product_id, tier)
        if not item:
            await callback.answer()
            return

        # Mavjudlikni tekshirish
        from bot.db.models import get_available_count
        stats = await get_available_count(product_id, tier)
        available = stats.get("available", 0)

        new_qty = item["quantity"] + 1
        if new_qty > available + item["quantity"]:
            await callback.answer(t("qty_exceeds_stock", lang, available=available), show_alert=True)
            return

        await cart_update_qty(callback.from_user.id, product_id, tier, new_qty)
        await show_cart(callback.message, callback.from_user.id, edit=True)
        await callback.answer()
    except Exception:
        await callback.answer(t("error_general"), show_alert=True)


@router.callback_query(F.data.startswith("cart:dec:"))
async def cart_decrease(callback: CallbackQuery) -> None:
    """Miqdorni kamaytirish"""
    try:
        _, _, product_id_str, tier = callback.data.split(":")
        product_id = int(product_id_str)

        from bot.db.models import cart_item_in_cart
        item = await cart_item_in_cart(callback.from_user.id, product_id, tier)
        if not item:
            await callback.answer()
            return

        new_qty = item["quantity"] - 1
        await cart_update_qty(callback.from_user.id, product_id, tier, new_qty)
        await show_cart(callback.message, callback.from_user.id, edit=True)
        await callback.answer()
    except Exception:
        await callback.answer(t("error_general"), show_alert=True)


@router.callback_query(F.data.startswith("cart:del:"))
async def cart_delete_item(callback: CallbackQuery) -> None:
    """Elementni savatdan o'chirish"""
    try:
        item_id = int(callback.data.split(":")[2])
        await cart_remove_item(item_id)
        await show_cart(callback.message, callback.from_user.id, edit=True)
        await callback.answer()
    except Exception:
        await callback.answer(t("error_general"), show_alert=True)


@router.callback_query(F.data == "cart:clear")
async def cart_clear_handler(callback: CallbackQuery) -> None:
    """Savatni tozalash"""
    try:
        user = await get_user(callback.from_user.id)
        lang = user.get("language", "uz") if user else "uz"
        await cart_clear(callback.from_user.id)
        await callback.message.edit_text(
            t("cart_cleared", lang),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text=t("btn_go_catalog", lang), callback_data="cat:back")
            ]])
        )
        await callback.answer()
    except Exception:
        await callback.answer(t("error_general"), show_alert=True)


@router.callback_query(F.data == "cart:promo")
async def promo_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Promo kod kiritish"""
    try:
        user = await get_user(callback.from_user.id)
        lang = user.get("language", "uz") if user else "uz"
        await state.set_state(PromoFSM.code)
        await state.update_data(lang=lang)
        await callback.message.edit_text(
            t("ask_promo_code", lang),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text=t("btn_cancel", lang), callback_data="cart:promo_cancel")
            ]])
        )
        await callback.answer()
    except Exception:
        await callback.answer(t("error_general"), show_alert=True)


@router.callback_query(F.data == "cart:promo_cancel", PromoFSM.code)
async def promo_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    """Promo kod kiritishni bekor qilish"""
    await state.clear()
    await show_cart(callback.message, callback.from_user.id, edit=True)
    await callback.answer()


@router.message(PromoFSM.code)
async def promo_entered(message: Message, state: FSMContext) -> None:
    """Promo kod tekshirish"""
    data = await state.get_data()
    lang = data.get("lang", "uz")
    code = message.text.strip()
    await state.clear()

    try:
        from datetime import datetime
        promo = await get_promo_by_code(code)

        valid = False
        if promo:
            # Sana va limit tekshirish
            now = datetime.now()
            valid_from = promo.get("valid_from")
            valid_until = promo.get("valid_until")
            max_uses = promo.get("max_uses", -1)
            used_count = promo.get("used_count", 0)

            if valid_from and datetime.fromisoformat(str(valid_from)) > now:
                valid = False
            elif valid_until and datetime.fromisoformat(str(valid_until)) < now:
                valid = False
            elif max_uses != -1 and used_count >= max_uses:
                valid = False
            else:
                valid = True

        if valid:
            await message.answer(t("promo_valid", lang, pct=promo["discount_percent"]))
            await show_cart(message, message.from_user.id, promo=promo)
        else:
            await message.answer(t("promo_invalid", lang))
            await show_cart(message, message.from_user.id)
    except Exception:
        await message.answer(t("error_general"))


@router.callback_query(F.data == "cart:checkout")
async def checkout(callback: CallbackQuery, state: FSMContext) -> None:
    """Buyurtma berish — order.py ga yo'naltirish"""
    try:
        user = await get_user(callback.from_user.id)
        lang = user.get("language", "uz") if user else "uz"

        items = await cart_get(callback.from_user.id)
        if not items:
            await callback.answer(t("cart_empty", lang), show_alert=True)
            return

        # FSM ga savat ma'lumotlarini saqlash va order yaratish
        await state.update_data(checkout_lang=lang)
        await callback.answer()

        # Order handlerga yo'naltirish
        from bot.handlers.order import create_order_handler
        await create_order_handler(callback.message, callback.from_user.id, lang, state)
    except Exception:
        await callback.answer(t("error_general"), show_alert=True)
