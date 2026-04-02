"""
/start handler — til tanlash, onboarding va asosiy menyu
"""
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from bot.db.models import create_user, get_user, update_language, set_onboarding_shown
from bot.keyboards.main_menu import (
    language_select_kb, onboarding_done_kb, main_menu_kb,
    profile_menu_kb, help_menu_kb
)
from bot.utils.texts import t

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    """
    /start buyrug'i:
    - Yangi foydalanuvchi → til tanlash
    - Mavjud foydalanuvchi (onboarding_shown=1) → asosiy menyu
    - Mavjud foydalanuvchi (onboarding_shown=0) → til tanlash
    """
    try:
        tg_user = message.from_user
        user = await get_user(tg_user.id)

        if user and user.get("onboarding_shown"):
            # Qayta /start — to'g'ridan-to'g'ri asosiy menyu
            lang = user.get("language", "uz")
            await message.answer(
                t("main_menu", lang),
                reply_markup=main_menu_kb(lang)
            )
        else:
            # Yangi yoki onboarding ko'rmagan foydalanuvchi
            if not user:
                await create_user(
                    telegram_id=tg_user.id,
                    username=tg_user.username,
                    full_name=tg_user.full_name,
                    language="uz"
                )
            await message.answer(
                t("choose_language"),
                reply_markup=language_select_kb()
            )
    except Exception as e:
        await message.answer(t("error_general"))


@router.callback_query(F.data.startswith("lang:"))
async def language_chosen(callback: CallbackQuery) -> None:
    """Foydalanuvchi tilni tanlaganda — onboarding boshlash"""
    try:
        lang = callback.data.split(":")[1]
        if lang not in ("uz", "ru"):
            lang = "uz"

        await update_language(callback.from_user.id, lang)
        await callback.message.delete()

        # Onboarding: 3 xabar ketma-ket
        await callback.message.answer(t("onboarding_1", lang))
        await callback.message.answer(t("onboarding_2", lang))
        await callback.message.answer(
            t("onboarding_3", lang),
            reply_markup=onboarding_done_kb(lang)
        )
        await callback.answer()
    except Exception:
        await callback.answer(t("error_general"), show_alert=True)


@router.callback_query(F.data == "onboarding:done")
async def onboarding_done(callback: CallbackQuery) -> None:
    """Onboarding tugagach — asosiy menyuni ko'rsatish"""
    try:
        user = await get_user(callback.from_user.id)
        lang = user.get("language", "uz") if user else "uz"

        await set_onboarding_shown(callback.from_user.id)
        await callback.message.delete()
        await callback.message.answer(
            t("main_menu", lang),
            reply_markup=main_menu_kb(lang)
        )
        await callback.answer()
    except Exception:
        await callback.answer(t("error_general"), show_alert=True)


@router.message(F.text.in_(["👤 Profil", "👤 Профиль"]))
async def profile_menu(message: Message, lang: str = "uz") -> None:
    """Profil submenu"""
    try:
        user = await get_user(message.from_user.id)
        if user:
            lang = user.get("language", "uz")
        await message.answer(
            t("profile_menu", lang),
            reply_markup=profile_menu_kb(lang)
        )
    except Exception:
        await message.answer(t("error_general"))


@router.message(F.text.in_(["ℹ️ Yordam", "ℹ️ Помощь"]))
async def help_menu(message: Message, lang: str = "uz") -> None:
    """Yordam submenu"""
    try:
        user = await get_user(message.from_user.id)
        if user:
            lang = user.get("language", "uz")
        await message.answer(
            t("help_menu", lang),
            reply_markup=help_menu_kb(lang)
        )
    except Exception:
        await message.answer(t("error_general"))


@router.callback_query(F.data == "profile:back")
async def profile_back(callback: CallbackQuery) -> None:
    """Profildan asosiy menyuga qaytish"""
    try:
        user = await get_user(callback.from_user.id)
        lang = user.get("language", "uz") if user else "uz"
        await callback.message.delete()
        await callback.message.answer(t("main_menu", lang), reply_markup=main_menu_kb(lang))
        await callback.answer()
    except Exception:
        await callback.answer(t("error_general"), show_alert=True)


@router.callback_query(F.data == "help:back")
async def help_back(callback: CallbackQuery) -> None:
    """Yordamdan asosiy menyuga qaytish"""
    try:
        user = await get_user(callback.from_user.id)
        lang = user.get("language", "uz") if user else "uz"
        await callback.message.delete()
        await callback.message.answer(t("main_menu", lang), reply_markup=main_menu_kb(lang))
        await callback.answer()
    except Exception:
        await callback.answer(t("error_general"), show_alert=True)
