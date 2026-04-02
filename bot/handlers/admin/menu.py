"""
Admin asosiy menyu handler
"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from bot.config import ADMIN_IDS
from bot.db.models import get_admin_by_telegram_id, get_user
from bot.keyboards.admin_kb import admin_main_menu_kb, products_menu_kb
from bot.utils.texts import t

router = Router()


async def get_admin_role(telegram_id: int) -> str | None:
    """Admin rolini aniqlash"""
    if telegram_id == ADMIN_IDS[0]:
        return "boss"
    admin = await get_admin_by_telegram_id(telegram_id)
    return admin["role"] if admin else None


@router.message(Command("admin"))
async def admin_panel(message: Message) -> None:
    """Admin panelni ochish"""
    try:
        role = await get_admin_role(message.from_user.id)
        if not role:
            user = await get_user(message.from_user.id)
            lang = user.get("language", "uz") if user else "uz"
            await message.answer(t("access_denied", lang))
            return

        user = await get_user(message.from_user.id)
        lang = user.get("language", "uz") if user else "uz"
        await message.answer(
            t("admin_menu", lang),
            reply_markup=admin_main_menu_kb(lang, role)
        )
    except Exception:
        await message.answer(t("error_general"))


@router.callback_query(F.data == "adm:products")
async def admin_products_menu(callback: CallbackQuery) -> None:
    """Mahsulotlar boshqarish menyusi"""
    try:
        role = await get_admin_role(callback.from_user.id)
        if not role or role not in ("manager", "boss"):
            await callback.answer(t("access_denied"), show_alert=True)
            return

        user = await get_user(callback.from_user.id)
        lang = user.get("language", "uz") if user else "uz"
        await callback.message.edit_text(
            t("products_menu", lang),
            reply_markup=products_menu_kb(lang)
        )
        await callback.answer()
    except Exception:
        await callback.answer(t("error_general"), show_alert=True)


@router.callback_query(F.data == "adm:back")
async def admin_back(callback: CallbackQuery) -> None:
    """Admin menyuga qaytish"""
    try:
        role = await get_admin_role(callback.from_user.id)
        if not role:
            await callback.answer(t("access_denied"), show_alert=True)
            return

        user = await get_user(callback.from_user.id)
        lang = user.get("language", "uz") if user else "uz"
        await callback.message.edit_text(
            t("admin_menu", lang),
            reply_markup=admin_main_menu_kb(lang, role)
        )
        await callback.answer()
    except Exception:
        await callback.answer(t("error_general"), show_alert=True)


@router.callback_query(F.data == "adm:cancel")
async def admin_cancel(callback: CallbackQuery) -> None:
    """Amalni bekor qilish"""
    try:
        user = await get_user(callback.from_user.id)
        lang = user.get("language", "uz") if user else "uz"
        await callback.message.edit_text(t("action_cancelled", lang))
        await callback.answer()
    except Exception:
        await callback.answer(t("error_general"), show_alert=True)
