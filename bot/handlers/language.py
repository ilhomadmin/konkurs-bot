"""
Til o'zgartirish handler (profil menyudan)
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery

from bot.db.models import get_user, update_language
from bot.keyboards.main_menu import language_select_kb
from bot.utils.texts import t

router = Router()


@router.callback_query(F.data == "profile:lang")
async def change_language_prompt(callback: CallbackQuery) -> None:
    """Til o'zgartirish ekranini ko'rsatish"""
    try:
        user = await get_user(callback.from_user.id)
        lang = user.get("language", "uz") if user else "uz"
        await callback.message.edit_text(
            t("choose_language", lang),
            reply_markup=language_select_kb()
        )
        await callback.answer()
    except Exception:
        await callback.answer(t("error_general"), show_alert=True)


@router.callback_query(F.data.startswith("lang:"))
async def change_language(callback: CallbackQuery) -> None:
    """Yangi tilni saqlash (profil menyudan kelganda)"""
    try:
        lang = callback.data.split(":")[1]
        if lang not in ("uz", "ru"):
            lang = "uz"

        user = await get_user(callback.from_user.id)
        # Agar onboarding ko'rsatilmagan bo'lsa — bu /start dagi til tanlash
        if user and not user.get("onboarding_shown"):
            return  # start.py handler hal qiladi

        await update_language(callback.from_user.id, lang)
        await callback.answer(t("language_set", lang), show_alert=False)

        from bot.keyboards.main_menu import profile_menu_kb
        from bot.utils.texts import t as _t
        await callback.message.edit_text(
            _t("profile_menu", lang),
            reply_markup=profile_menu_kb(lang)
        )
    except Exception:
        await callback.answer(t("error_general"), show_alert=True)
