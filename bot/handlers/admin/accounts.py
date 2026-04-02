"""
Admin: Akkaunt qo'shish (bitta va bulk)
"""
from datetime import date
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

from bot.db.models import (
    create_account, bulk_create_accounts,
    get_available_count, get_product_by_id,
    get_prices_by_product,
)
from bot.keyboards.admin_kb import accounts_menu_kb, product_actions_kb
from bot.keyboards.common import back_kb
from bot.utils.texts import t
from bot.utils.duration import days_to_tier, tier_display_name
from bot.utils.helpers import format_account_stats

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


async def check_tier_price(product_id: int, tier: str) -> bool:
    """Mahsulot uchun berilgan tier narxi mavjudligini tekshiradi"""
    prices = await get_prices_by_product(product_id)
    return any(p["duration_tier"] == tier for p in prices)


# ==================== AKKAUNTLAR MENYUSI ====================

@router.callback_query(F.data.startswith("adm:acc:list:"))
async def accounts_list(callback: CallbackQuery) -> None:
    """Akkauntlar ro'yxati va statistika"""
    try:
        lang, role = await get_lang_and_role(callback.from_user.id)
        if not role:
            await callback.answer(t("access_denied", lang), show_alert=True)
            return

        prod_id = int(callback.data.split(":")[3])
        prod = await get_product_by_id(prod_id)
        stats = await get_available_count(prod_id)

        prod_name = prod[f"name_{lang}"] if prod else f"#{prod_id}"
        stats_text = format_account_stats(stats, lang)

        text = f"📊 <b>{prod_name}</b>\n\n{stats_text}"
        await callback.message.edit_text(
            text,
            reply_markup=accounts_menu_kb(prod_id, lang),
            parse_mode="HTML"
        )
        await callback.answer()
    except Exception:
        await callback.answer(t("error_general"), show_alert=True)


# ==================== BITTA AKKAUNT QO'SHISH ====================

@router.callback_query(F.data.startswith("adm:acc:add:"))
async def add_account_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Bitta akkaunt qo'shish jarayonini boshlash"""
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
    except Exception:
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

    # Sanani tekshirish
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
    """Qo'shimcha ma'lumot — akkauntni DB ga saqlash"""
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

        tier_name = tier_display_name(result["duration_tier"], lang) if result["duration_tier"] else "—"
        text = t("account_created", lang, days=result["remaining_days"], tier=tier_name)

        # Tier narxi yo'q bo'lsa ogohlantirish
        if result["duration_tier"]:
            has_price = await check_tier_price(data["product_id"], result["duration_tier"])
            if not has_price:
                text += f"\n\n{t('no_price_for_tier_warning', lang)}"

        await state.clear()
        await message.answer(
            text,
            reply_markup=back_kb(f"adm:acc:list:{data['product_id']}", lang)
        )
    except Exception as e:
        await state.clear()
        await message.answer(f"{t('error_general', lang)}\n{e}")


# ==================== BULK AKKAUNTLAR ====================

@router.callback_query(F.data.startswith("adm:acc:bulk:"))
async def bulk_accounts_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Bulk akkaunt qo'shish jarayonini boshlash"""
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
    except Exception:
        await callback.answer(t("error_general"), show_alert=True)


@router.message(BulkAccountFSM.lines)
async def bulk_accounts_process(message: Message, state: FSMContext) -> None:
    """Bulk akkauntlarni parse qilib DB ga saqlash"""
    data = await state.get_data()
    lang = data.get("lang", "uz")
    prod_id = data["product_id"]

    lines = message.text.strip().splitlines()

    try:
        result = await bulk_create_accounts(prod_id, lines)
        added = result["added"]
        errors = result["errors"]
        tier_stats = result["tier_stats"]

        # Tier bo'yicha natija
        tier_info = ""
        for tier, cnt in tier_stats.items():
            tier_info += f"\n  {tier_display_name(tier, lang)}: {cnt}"

        errors_count = len(errors)
        text = t("bulk_result", lang, added=added, errors=errors_count)

        if tier_info:
            if lang == "uz":
                text += f"\n📊 Tier bo'yicha:{tier_info}"
            else:
                text += f"\n📊 По тирам:{tier_info}"

        if errors:
            errors_text = "\n".join(errors[:5])
            if len(errors) > 5:
                errors_text += f"\n... (+{len(errors) - 5})"
            text += f"\n\n❌ Xatolar:\n{errors_text}"

        # Tier narxlari yo'q bo'lganlari uchun ogohlantirish
        for tier in tier_stats:
            has_price = await check_tier_price(prod_id, tier)
            if not has_price:
                text += f"\n\n⚠️ {tier_display_name(tier, lang)}: {t('no_price_for_tier_warning', lang)}"

        await state.clear()
        await message.answer(
            text,
            reply_markup=back_kb(f"adm:acc:list:{prod_id}", lang)
        )
    except Exception as e:
        await state.clear()
        await message.answer(f"{t('error_general', lang)}\n{e}")
