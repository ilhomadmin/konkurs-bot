"""
Admin: Rol boshqarish
"""
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

from bot.config import ADMIN_IDS
from bot.db.models import (
    get_all_admins, get_admin_by_telegram_id,
    create_admin_role, update_admin_role, delete_admin_role
)
from bot.keyboards.admin_kb import roles_list_kb, role_select_kb
from bot.keyboards.common import back_kb
from bot.utils.texts import t

router = Router()


class AddAdminFSM(StatesGroup):
    telegram_id = State()
    role = State()


# ==================== HELPER ====================

async def get_lang_and_role(user_id: int) -> tuple[str, str | None]:
    from bot.db.models import get_user
    from bot.handlers.admin.menu import get_admin_role
    user = await get_user(user_id)
    lang = user.get("language", "uz") if user else "uz"
    role = await get_admin_role(user_id)
    return lang, role


# ==================== ADMINLAR RO'YXATI ====================

@router.callback_query(F.data == "adm:roles")
async def roles_list(callback: CallbackQuery) -> None:
    """Adminlar ro'yxati (faqat boss)"""
    try:
        lang, role = await get_lang_and_role(callback.from_user.id)
        if role != "boss":
            await callback.answer(t("access_denied", lang), show_alert=True)
            return

        admins = await get_all_admins()
        text = t("roles_menu", lang)
        if not admins:
            text += f"\n{t('no_admins', lang)}"

        await callback.message.edit_text(
            text,
            reply_markup=roles_list_kb(admins, lang)
        )
        await callback.answer()
    except Exception:
        await callback.answer(t("error_general"), show_alert=True)


@router.callback_query(F.data == "adm:role:add")
async def add_admin_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Admin qo'shish jarayonini boshlash"""
    try:
        lang, role = await get_lang_and_role(callback.from_user.id)
        if role != "boss":
            await callback.answer(t("access_denied", lang), show_alert=True)
            return

        await state.update_data(lang=lang)
        await state.set_state(AddAdminFSM.telegram_id)
        await callback.message.edit_text(t("ask_admin_id", lang))
        await callback.answer()
    except Exception:
        await callback.answer(t("error_general"), show_alert=True)


@router.message(AddAdminFSM.telegram_id)
async def admin_telegram_id(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uz")

    try:
        target_id = int(message.text.strip())
    except ValueError:
        await message.answer(t("invalid_number", lang))
        return

    await state.update_data(target_id=target_id)
    await state.set_state(AddAdminFSM.role)

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔧 Operator", callback_data=f"adm:newrole:operator")],
        [InlineKeyboardButton(text="📊 Manager", callback_data=f"adm:newrole:manager")],
        [InlineKeyboardButton(text="👑 Boss", callback_data=f"adm:newrole:boss")],
    ])
    await message.answer(t("ask_admin_role", lang), reply_markup=kb)


@router.callback_query(F.data.startswith("adm:newrole:"), AddAdminFSM.role)
async def admin_role_selected(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uz")
    role_selected = callback.data.split(":")[2]
    target_id = data["target_id"]

    try:
        await create_admin_role(target_id, role=role_selected)
        await state.clear()
        await callback.message.edit_text(
            t("admin_created", lang),
            reply_markup=back_kb("adm:roles", lang)
        )
    except Exception as e:
        await state.clear()
        await callback.message.edit_text(f"{t('error_general', lang)}\n{e}")
    await callback.answer()


@router.callback_query(F.data.startswith("adm:role:"))
async def admin_role_actions(callback: CallbackQuery) -> None:
    """Admin amallari (set/del va detail)"""
    try:
        parts = callback.data.split(":")
        lang, caller_role = await get_lang_and_role(callback.from_user.id)

        if caller_role != "boss":
            await callback.answer(t("access_denied", lang), show_alert=True)
            return

        # adm:role:set:TARGET_ID:ROLE
        if parts[2] == "set" and len(parts) >= 5:
            target_id = int(parts[3])
            new_role = parts[4]

            # ADMIN_IDS[0] rolini o'zgartirish mumkin emas
            if target_id == ADMIN_IDS[0]:
                await callback.answer("Boss rolini o'zgartirish mumkin emas!", show_alert=True)
                return

            await update_admin_role(target_id, new_role)
            admins = await get_all_admins()
            await callback.message.edit_text(
                t("roles_menu", lang),
                reply_markup=roles_list_kb(admins, lang)
            )

        # adm:role:del:TARGET_ID
        elif parts[2] == "del" and len(parts) >= 4:
            target_id = int(parts[3])
            if target_id == ADMIN_IDS[0]:
                await callback.answer("Asosiy boss ni o'chirish mumkin emas!", show_alert=True)
                return
            await delete_admin_role(target_id)
            admins = await get_all_admins()
            await callback.message.edit_text(
                t("admin_deleted", lang),
                reply_markup=roles_list_kb(admins, lang)
            )

        # adm:role:TELEGRAM_ID — tafsilot
        else:
            try:
                target_id = int(parts[2])
            except ValueError:
                await callback.answer()
                return

            admin = await get_admin_by_telegram_id(target_id)
            if not admin:
                await callback.answer(t("not_found", lang), show_alert=True)
                return

            name = admin.get("full_name") or admin.get("username") or str(target_id)
            role_label = {"operator": "🔧 Operator", "manager": "📊 Manager", "boss": "👑 Boss"}.get(
                admin["role"], admin["role"]
            )
            text = f"👤 <b>{name}</b>\nID: {target_id}\nRol: {role_label}"

            await callback.message.edit_text(
                text,
                reply_markup=role_select_kb(target_id, lang),
                parse_mode="HTML"
            )

        await callback.answer()
    except Exception:
        await callback.answer(t("error_general"), show_alert=True)
