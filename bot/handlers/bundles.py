from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.db.models import (
    get_user_by_telegram_id, get_all_bundles,
    get_bundle_by_id, get_bundle_items, cart_add
)
from bot.utils.texts import t

router = Router()


@router.callback_query(F.data == "bundles_page")
async def bundles_page(call: CallbackQuery):
    user = await get_user_by_telegram_id(call.from_user.id)
    lang = user.get("language", "uz") if user else "uz"

    bundles = await get_all_bundles()
    if not bundles:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="catalog_main")]
        ])
        await call.message.edit_text(t("bundle_empty", lang), reply_markup=kb, parse_mode="HTML")
        await call.answer()
        return

    buttons = []
    for b in bundles:
        buttons.append([InlineKeyboardButton(
            text=f"📦 {b['name']} — {b['price']:,} so'm",
            callback_data=f"bundle_detail:{b['id']}"
        )])
    buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="catalog_main")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await call.message.edit_text(t("bundles_page", lang), reply_markup=kb, parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data.startswith("bundle_detail:"))
async def bundle_detail(call: CallbackQuery):
    bundle_id = int(call.data.split(":")[1])
    user = await get_user_by_telegram_id(call.from_user.id)
    lang = user.get("language", "uz") if user else "uz"

    bundle = await get_bundle_by_id(bundle_id)
    if not bundle:
        await call.answer("Topilmadi", show_alert=True)
        return

    items = await get_bundle_items(bundle_id)
    items_text = "\n".join(f"• {it['product_name']} ({it['tier']})" for it in items)

    # Calculate original price
    original = sum(it.get("price", 0) for it in items)
    saving = original - bundle["price"]

    text = t("bundle_detail", lang,
             name=bundle["name"],
             description=bundle.get("description", ""),
             items=items_text,
             original=original,
             price=bundle["price"],
             saving=saving)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_buy_bundle", lang), callback_data=f"bundle_buy:{bundle_id}")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="bundles_page")],
    ])
    await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data.startswith("bundle_buy:"))
async def bundle_buy(call: CallbackQuery):
    bundle_id = int(call.data.split(":")[1])
    user = await get_user_by_telegram_id(call.from_user.id)
    lang = user.get("language", "uz") if user else "uz"

    items = await get_bundle_items(bundle_id)
    for item in items:
        await cart_add(user["id"], item["product_id"], item["tier"], 1)

    await call.answer(t("bundle_added_to_cart", lang), show_alert=True)
