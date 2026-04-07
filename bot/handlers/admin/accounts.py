"""
Admin: Akkaunt qo'shish (bitta va bulk)
YANGI STRUKTURA: tier tekshiruv yo'q, product ga to'g'ridan-to'g'ri bog'lanadi
"""
import logging
from datetime import date
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

from bot.db.models import (
    create_account, bulk_create_accounts,
    get_product_stock, get_product_by_id,
)
from bot.keyboards.admin_kb import accounts_menu_kb, product_actions_kb
from bot.keyboards.common import back_kb
from bot.utils.texts import t

logger = logging.getLogger(__name__)
router = Router()


# ==================== FSM STATES ====================

class AddAccountFSM(StatesGroup):
    login = State()
    password = State()
    expiry = State()
    supplier = State()
    additional = State()


class BulkAccountFSM(StatesGroup):
    lines = State()


# ==================== HELPER ====================

async def get_lang_and_role(user_id: int) -> tuple[str, str | None]:
    from bot.db.models import get_user
    from bot.handlers.admin.menu import get_admin_role
    user = await get_user(user_id)
    lang = user.get("language", "uz") if user else "uz"
    role = await get_admin_role(user_id)
    return lang, role


# ==================== AKKAUNTLAR MENYUSI ====================

@router.callback_query(F.data.startswith("adm:acc:list:"))
async def accounts_list(callback: CallbackQuery) -> None:
    try:
        lang, role = await get_lang_and_role(callback.from_user.id)
        if not role:
            await callback.answer(t("access_denied", lang), show_alert=True)
            return

        prod_id = int(callback.data.split(":")[3])
        prod = await get_product_by_id(prod_id)
        stock = await get_product_stock(prod_id)

        prod_name = prod[f"name_{lang}"] if prod else f"#{prod_id}"
        text = f"📊 <b>{prod_name}</b>\n\n📦 Mavjud: {stock} ta"
        await callback.message.edit_text(
            text,
            reply_markup=accounts_menu_kb(prod_id, lang),
            parse_mode="HTML"
        )
        await callback.answer()
    except Exception as e:
        logger.exception(f"accounts_list error: {e}")
        await callback.answer(t("error_general"), show_alert=True)


# ==================== BITTA AKKAUNT QO'SHISH ====================

@router.callback_query(F.data.startswith("adm:acc:add:"))
async def add_account_start(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        lang, role = await get_lang_and_role(callback.from_user.id)
        if not role:
            await callback.answer(t("access_denied", lang), show_alert=True)
            return

        prod_id = int(callback.data.split(":")[3])
        await state.update_data(lang=lang, product_id=prod_id)
        await state.set_state(AddAccountFSM.login)
        await callback.message.edit_text(t("ask_account_login", lang))
        await callback.answer()
    except Exception as e:
        logger.exception(f"add_account_start error: {e}")
        await callback.answer(t("error_general"), show_alert=True)


@router.message(AddAccountFSM.login)
async def account_login(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uz")
    await state.update_data(login=message.text.strip())
    await state.set_state(AddAccountFSM.password)
    await message.answer(t("ask_account_password", lang))


@router.message(AddAccountFSM.password)
async def account_password(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uz")
    await state.update_data(password=message.text.strip())
    await state.set_state(AddAccountFSM.expiry)
    await message.answer(t("ask_account_expiry", lang))


@router.message(AddAccountFSM.expiry)
async def account_expiry(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uz")
    expiry_str = message.text.strip()

    try:
        date.fromisoformat(expiry_str)
    except ValueError:
        await message.answer(t("invalid_date_format", lang))
        return

    await state.update_data(expiry=expiry_str)
    await state.set_state(AddAccountFSM.supplier)
    await message.answer(t("ask_account_supplier", lang))


@router.message(AddAccountFSM.supplier)
async def account_supplier(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uz")
    supplier = None if message.text.strip() == "/skip" else message.text.strip()
    await state.update_data(supplier=supplier)
    await state.set_state(AddAccountFSM.additional)
    await message.answer(t("ask_account_additional", lang))


@router.message(AddAccountFSM.additional)
async def account_additional(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uz")
    additional = None if message.text.strip() == "/skip" else message.text.strip()

    try:
        result = await create_account(
            product_id=data["product_id"],
            login=data["login"],
            password=data["password"],
            expiry_date=data["expiry"],
            supplier=data.get("supplier"),
            additional_data=additional
        )

        text = t("account_created_simple", lang, days=result["remaining_days"])

        await state.clear()
        await message.answer(
            text,
            reply_markup=back_kb(f"adm:acc:list:{data['product_id']}", lang)
        )
    except Exception as e:
        logger.exception(f"account_additional error: {e}")
        await state.clear()
        await message.answer(f"{t('error_general', lang)}\n{e}")


# ==================== BULK AKKAUNTLAR ====================

@router.callback_query(F.data.startswith("adm:acc:bulk:"))
async def bulk_accounts_start(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        lang, role = await get_lang_and_role(callback.from_user.id)
        if not role:
            await callback.answer(t("access_denied", lang), show_alert=True)
            return

        prod_id = int(callback.data.split(":")[3])
        await state.update_data(lang=lang, product_id=prod_id)
        await state.set_state(BulkAccountFSM.lines)
        await callback.message.edit_text(t("ask_bulk_accounts", lang))
        await callback.answer()
    except Exception as e:
        logger.exception(f"bulk_accounts_start error: {e}")
        await callback.answer(t("error_general"), show_alert=True)


@router.message(BulkAccountFSM.lines)
async def bulk_accounts_process(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uz")
    prod_id = data["product_id"]

    lines = message.text.strip().splitlines()

    try:
        result = await bulk_create_accounts(prod_id, lines)
        added = result["added"]
        errors = result["errors"]

        errors_count = len(errors)
        text = t("bulk_result", lang, added=added, errors=errors_count)

        if errors:
            errors_text = "\n".join(errors[:5])
            if len(errors) > 5:
                errors_text += f"\n... (+{len(errors) - 5})"
            text += f"\n\n❌ Xatolar:\n{errors_text}"

        await state.clear()
        await message.answer(
            text,
            reply_markup=back_kb(f"adm:acc:list:{prod_id}", lang)
        )
    except Exception as e:
        logger.exception(f"bulk_accounts_process error: {e}")
        await state.clear()
        await message.answer(f"{t('error_general', lang)}\n{e}")
