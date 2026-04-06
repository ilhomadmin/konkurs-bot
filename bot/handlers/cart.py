"""
Savat handlerlari — ko'rish, son o'zgartirish, promo kod, buyurtma berish
YANGI STRUKTURA: duration_tier yo'q, mahsulot = obuna turi
"""
import logging
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.db.models import (
    get_user, cart_get, cart_update_qty, cart_remove_item, cart_clear,
    get_promo_by_code, get_product_stock,
)
from bot.utils.texts import t

logger = logging.getLogger(__name__)
router = Router()


class PromoFSM(StatesGroup):
    code = State()


def cart_kb(items: list[dict], lang: str, promo_applied: bool = False) -> InlineKeyboardMarkup:
    buttons = []
    for item in items:
        name = item.get(f"name_{lang}", item.get("name_uz", "?"))
        buttons.append([
            InlineKeyboardButton(text="➖", callback_data=f"cart:dec:{item['product_id']}"),
            InlineKeyboardButton(text=f"{name} x{item['quantity']}", callback_data="noop"),
            InlineKeyboardButton(text="➕", callback_data=f"cart:inc:{item['product_id']}"),
            InlineKeyboardButton(text="🗑", callback_data=f"cart:del:{item['product_id']}"),
        ])

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


async def build_cart_text(
    user_id: int,
    items: list[dict],
    lang: str,
    promo: dict | None = None
) -> tuple[str, int, int, int]:
    user = await get_user(user_id)
    if not user:
        return t("cart_empty", lang), 0, 0, 0

    lines = [t("cart_title", lang)]

    # VIP
    vip_level = user.get("vip_level", "standard")
    vip_pct = 0
    vip_name = "Oddiy"
    try:
        from bot.db.models import get_vip_levels
        vip_levels = await get_vip_levels()
        for vl in vip_levels:
            if vl["level"] == vip_level:
                vip_pct = vl["discount_percent"]
                vip_name = vl[f"display_name_{lang}"]
                break
    except Exception:
        pass

    if vip_pct > 0:
        lines.append(t("cart_vip_line", lang, vip_name=vip_name, pct=vip_pct))

    total = 0
    for i, item in enumerate(items, 1):
        name = item.get(f"name_{lang}", item.get("name_uz", "?"))
        price = item.get("price", 0) * item["quantity"]
        total += price
        lines.append(f"  {i}. {name} x{item['quantity']} = {price:,} so'm")

    lines.append("")
    lines.append(t("cart_total", lang, total=total))

    promo_pct = promo["discount_percent"] if promo else 0
    final_pct = max(vip_pct, promo_pct)
    discount_amount = int(total * final_pct / 100)
    final_amount = total - discount_amount

    if final_pct > 0:
        if promo_pct >= vip_pct and promo:
            label = f"🏷 Promo ({promo['code']})"
        else:
            label = f"💎 {vip_name}"
        lines.append(f"  {label}: -{final_pct}% = -{discount_amount:,} so'm")

    lines.append(t("cart_final", lang, final=final_amount))

    return "\n".join(lines), total, discount_amount, final_amount


async def show_cart(
    message: Message,
    user_id: int,
    promo: dict | None = None,
    edit: bool = False
) -> None:
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
    try:
        await show_cart(message, message.from_user.id)
    except Exception as e:
        logger.exception(f"cart_handler error: {e}")
        await message.answer(t("error_general"))


@router.callback_query(F.data.startswith("cart:inc:"))
async def cart_increase(callback: CallbackQuery) -> None:
    try:
        product_id = int(callback.data.split(":")[2])
        user = await get_user(callback.from_user.id)
        lang = user.get("language", "uz") if user else "uz"

        stock = await get_product_stock(product_id)
        items = await cart_get(callback.from_user.id)
        current_qty = 0
        for it in items:
            if it["product_id"] == product_id:
                current_qty = it["quantity"]
                break

        if current_qty >= stock:
            await callback.answer(t("qty_exceeds_stock", lang, available=stock), show_alert=True)
            return

        await cart_update_qty(callback.from_user.id, product_id, 1)
        await show_cart(callback.message, callback.from_user.id, edit=True)
        await callback.answer()
    except Exception as e:
        logger.exception(f"cart_increase error: {e}")
        await callback.answer(t("error_general"), show_alert=True)


@router.callback_query(F.data.startswith("cart:dec:"))
async def cart_decrease(callback: CallbackQuery) -> None:
    try:
        product_id = int(callback.data.split(":")[2])
        await cart_update_qty(callback.from_user.id, product_id, -1)
        await show_cart(callback.message, callback.from_user.id, edit=True)
        await callback.answer()
    except Exception as e:
        logger.exception(f"cart_decrease error: {e}")
        await callback.answer(t("error_general"), show_alert=True)


@router.callback_query(F.data.startswith("cart:del:"))
async def cart_delete_item(callback: CallbackQuery) -> None:
    try:
        product_id = int(callback.data.split(":")[2])
        await cart_remove_item(callback.from_user.id, product_id)
        await show_cart(callback.message, callback.from_user.id, edit=True)
        await callback.answer()
    except Exception as e:
        logger.exception(f"cart_delete error: {e}")
        await callback.answer(t("error_general"), show_alert=True)


@router.callback_query(F.data == "cart:clear")
async def cart_clear_handler(callback: CallbackQuery) -> None:
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
    except Exception as e:
        logger.exception(f"cart_clear error: {e}")
        await callback.answer(t("error_general"), show_alert=True)


@router.callback_query(F.data == "cart:promo")
async def promo_start(callback: CallbackQuery, state: FSMContext) -> None:
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
    except Exception as e:
        logger.exception(f"promo_start error: {e}")
        await callback.answer(t("error_general"), show_alert=True)


@router.callback_query(F.data == "cart:promo_cancel", PromoFSM.code)
async def promo_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await show_cart(callback.message, callback.from_user.id, edit=True)
    await callback.answer()


@router.message(PromoFSM.code)
async def promo_entered(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uz")
    code = message.text.strip()
    await state.clear()

    try:
        from datetime import datetime
        promo = await get_promo_by_code(code)

        valid = False
        if promo and promo.get("is_active"):
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
            await message.answer(t("promo_valid", lang, discount=promo["discount_percent"]))
            await show_cart(message, message.from_user.id, promo=promo)
        else:
            await message.answer(t("promo_invalid", lang))
            await show_cart(message, message.from_user.id)
    except Exception as e:
        logger.exception(f"promo_entered error: {e}")
        await message.answer(t("error_general"))


@router.callback_query(F.data == "cart:checkout")
async def checkout(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        user = await get_user(callback.from_user.id)
        lang = user.get("language", "uz") if user else "uz"

        items = await cart_get(callback.from_user.id)
        if not items:
            await callback.answer(t("cart_empty", lang), show_alert=True)
            return

        await state.update_data(checkout_lang=lang)
        await callback.answer()

        from bot.handlers.order import create_order_handler
        await create_order_handler(callback.message, callback.from_user.id, lang, state)
    except Exception as e:
        logger.exception(f"checkout error: {e}")
        await callback.answer(t("error_general"), show_alert=True)
