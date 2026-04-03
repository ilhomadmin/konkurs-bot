from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.db.models import (
    get_user_by_telegram_id, get_user_by_referral_code,
    set_referred_by, get_referral_count
)
from bot.utils.texts import t
import os

router = Router()


@router.message(CommandStart(deep_link=True))
async def referral_deep_link(message: Message):
    """Handle REF_ deep links"""
    arg = message.text.split()[-1] if len(message.text.split()) > 1 else ""
    if not arg.startswith("REF_"):
        return  # Let other deep link handlers handle it

    ref_code = arg[4:]  # Remove REF_ prefix
    referrer = await get_user_by_referral_code(ref_code)

    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.get("language", "uz") if user else "uz"

    if referrer and user and referrer["id"] != user["id"] and not user.get("referred_by"):
        await set_referred_by(user["id"], referrer["id"])
        await message.answer(t("referral_welcome", lang))

    # Continue with normal start flow
    from bot.handlers.start import send_main_menu
    await send_main_menu(message, user)


@router.callback_query(F.data == "referral_page")
async def referral_page(call: CallbackQuery):
    user = await get_user_by_telegram_id(call.from_user.id)
    if not user:
        await call.answer()
        return
    lang = user.get("language", "uz")

    bot_username = os.getenv("BOT_USERNAME", "mybot")
    ref_code = user.get("referral_code", "")
    link = f"https://t.me/{bot_username}?start=REF_{ref_code}"
    count = await get_referral_count(user["id"])

    bonus = 50_000  # UZS bonus promo

    text = t("referral_page", lang, link=link, count=count, bonus=bonus)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="profile_page")]
    ])
    await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await call.answer()
