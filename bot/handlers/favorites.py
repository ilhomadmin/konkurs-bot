from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.db.models import (
    get_user_by_telegram_id, get_user_favorites,
    add_to_favorites, remove_from_favorites,
    is_in_favorites, add_stock_notify
)
from bot.utils.texts import t

router = Router()


@router.callback_query(F.data == "favorites_page")
async def favorites_page(call: CallbackQuery):
    user = await get_user_by_telegram_id(call.from_user.id)
    if not user:
        await call.answer()
        return
    lang = user.get("language", "uz")

    favs = await get_user_favorites(user["id"])
    if not favs:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📦 Katalog", callback_data="catalog_main")],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="profile_page")],
        ])
        await call.message.edit_text(t("favorites_empty", lang), reply_markup=kb, parse_mode="HTML")
        await call.answer()
        return

    buttons = []
    for fav in favs:
        name = fav["name"]
        stock = fav.get("stock", 0)
        stock_icon = "✅" if stock > 0 else "❌"
        buttons.append([InlineKeyboardButton(
            text=f"{stock_icon} {name}",
            callback_data=f"fav_detail:{fav['product_id']}"
        )])

    buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="profile_page")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await call.message.edit_text(t("favorites_page", lang), reply_markup=kb, parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data.startswith("fav_detail:"))
async def fav_detail(call: CallbackQuery):
    product_id = int(call.data.split(":")[1])
    user = await get_user_by_telegram_id(call.from_user.id)
    lang = user.get("language", "uz") if user else "uz"

    buttons = [
        [InlineKeyboardButton(text=t("btn_fav_add_cart", lang), callback_data=f"prod:{product_id}")],
        [InlineKeyboardButton(text=t("btn_fav_notify", lang), callback_data=f"stock_notify:{product_id}")],
        [InlineKeyboardButton(text=t("btn_remove_fav", lang), callback_data=f"fav_remove:{product_id}")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="favorites_page")],
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await call.message.edit_reply_markup(reply_markup=kb)
    await call.answer()


@router.callback_query(F.data.startswith("fav_remove:"))
async def fav_remove(call: CallbackQuery):
    product_id = int(call.data.split(":")[1])
    user = await get_user_by_telegram_id(call.from_user.id)
    lang = user.get("language", "uz") if user else "uz"

    await remove_from_favorites(user["id"], product_id)
    await call.answer(t("favorites_removed", lang), show_alert=False)

    # Refresh favorites page
    await favorites_page(call)


@router.callback_query(F.data.startswith("fav_toggle:"))
async def fav_toggle(call: CallbackQuery):
    product_id = int(call.data.split(":")[1])
    user = await get_user_by_telegram_id(call.from_user.id)
    lang = user.get("language", "uz") if user else "uz"

    already = await is_in_favorites(user["id"], product_id)
    if already:
        await remove_from_favorites(user["id"], product_id)
        await call.answer(t("favorites_removed", lang))
    else:
        await add_to_favorites(user["id"], product_id)
        await call.answer(t("favorites_added", lang))


@router.callback_query(F.data.startswith("stock_notify:"))
async def stock_notify_toggle(call: CallbackQuery):
    product_id = int(call.data.split(":")[1])
    user = await get_user_by_telegram_id(call.from_user.id)
    lang = user.get("language", "uz") if user else "uz"

    await add_stock_notify(user["id"], product_id)
    await call.answer("🔔 Stok to'ldirilganda xabar olasiz!", show_alert=True)
