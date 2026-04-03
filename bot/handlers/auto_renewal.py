from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.db.models import (
    get_user_by_telegram_id, get_user_auto_renewals_by_id,
    delete_auto_renewal
)
from bot.utils.texts import t

router = Router()


@router.callback_query(F.data == "auto_renewals_page")
async def auto_renewals_page(call: CallbackQuery):
    user = await get_user_by_telegram_id(call.from_user.id)
    if not user:
        await call.answer()
        return
    lang = user.get("language", "uz")

    renewals = await get_user_auto_renewals_by_id(user["id"])
    count = len(renewals)

    text = t("auto_renewal_page", lang, count=count)
    buttons = []
    for r in renewals:
        buttons.append([InlineKeyboardButton(
            text=f"⏹ {r['product_name']} ({r['tier']})",
            callback_data=f"renewal_disable:{r['id']}"
        )])
    buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="profile_page")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data.startswith("renewal_enable:"))
async def renewal_enable(call: CallbackQuery):
    await call.answer("Buyurtma sahifasidan yoqing", show_alert=True)


@router.callback_query(F.data.startswith("renewal_disable:"))
async def renewal_disable(call: CallbackQuery):
    renewal_id = int(call.data.split(":")[1])
    user = await get_user_by_telegram_id(call.from_user.id)
    lang = user.get("language", "uz") if user else "uz"

    await delete_auto_renewal(renewal_id)
    await call.answer(t("auto_renewal_disabled", lang), show_alert=True)
    await auto_renewals_page(call)
