"""
FAQ — Ko'p beriladigan savollar
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.db.models import get_user
from bot.utils.texts import t

router = Router()

FAQ_ITEMS = [
    ("faq_q1", "faq_a1", "1"),
    ("faq_q2", "faq_a2", "2"),
    ("faq_q3", "faq_a3", "3"),
    ("faq_q4", "faq_a4", "4"),
    ("faq_q5", "faq_a5", "5"),
    ("faq_q6", "faq_a6", "6"),
]


def faq_list_kb(lang: str) -> InlineKeyboardMarkup:
    """FAQ ro'yxati klaviaturasi"""
    buttons = []
    for q_key, _, faq_id in FAQ_ITEMS:
        buttons.append([InlineKeyboardButton(
            text=t(q_key, lang),
            callback_data=f"faq:{faq_id}"
        )])
    buttons.append([InlineKeyboardButton(
        text=t("btn_back", lang),
        callback_data="help:back"
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def faq_answer_kb(lang: str) -> InlineKeyboardMarkup:
    """Javob pastidagi tugmalar"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=t("btn_go_catalog", lang), callback_data="cat:back"),
            InlineKeyboardButton(text=t("faq_back", lang), callback_data="faq:list"),
        ]
    ])


@router.callback_query(F.data == "help:faq")
async def faq_list(callback: CallbackQuery) -> None:
    """FAQ ro'yxatini ko'rsatish"""
    try:
        user = await get_user(callback.from_user.id)
        lang = user.get("language", "uz") if user else "uz"

        await callback.message.edit_text(
            t("faq_title", lang),
            reply_markup=faq_list_kb(lang)
        )
        await callback.answer()
    except Exception:
        await callback.answer(t("error_general"), show_alert=True)


@router.callback_query(F.data == "faq:list")
async def faq_back(callback: CallbackQuery) -> None:
    """FAQ ro'yxatiga qaytish"""
    try:
        user = await get_user(callback.from_user.id)
        lang = user.get("language", "uz") if user else "uz"

        await callback.message.edit_text(
            t("faq_title", lang),
            reply_markup=faq_list_kb(lang)
        )
        await callback.answer()
    except Exception:
        await callback.answer(t("error_general"), show_alert=True)


@router.callback_query(F.data.startswith("faq:"))
async def faq_answer(callback: CallbackQuery) -> None:
    """FAQ javobi"""
    try:
        faq_id = callback.data.split(":")[1]
        if faq_id == "list":
            return  # faq:list yuqorida handle qilinadi

        user = await get_user(callback.from_user.id)
        lang = user.get("language", "uz") if user else "uz"

        # FAQ elementini topish
        item = next((x for x in FAQ_ITEMS if x[2] == faq_id), None)
        if not item:
            await callback.answer(t("not_found", lang), show_alert=True)
            return

        q_key, a_key, _ = item
        text = f"{t(q_key, lang)}\n\n{t(a_key, lang)}"

        await callback.message.edit_text(
            text,
            reply_markup=faq_answer_kb(lang),
            parse_mode="HTML"
        )
        await callback.answer()
    except Exception:
        await callback.answer(t("error_general"), show_alert=True)


@router.callback_query(F.data == "help:operator")
async def help_operator(callback: CallbackQuery) -> None:
    """Operator bilan bog'lanish"""
    try:
        user = await get_user(callback.from_user.id)
        lang = user.get("language", "uz") if user else "uz"

        text = ("📞 Operator bilan bog'lanish:\n\n"
                "Telegram: @support_username\n"
                "Ish vaqti: 09:00 — 22:00 (UTC+5)") if lang == "uz" else (
                "📞 Связь с оператором:\n\n"
                "Telegram: @support_username\n"
                "Рабочее время: 09:00 — 22:00 (UTC+5)")

        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text=t("btn_back", lang), callback_data="help:back")
            ]])
        )
        await callback.answer()
    except Exception:
        await callback.answer(t("error_general"), show_alert=True)


@router.callback_query(F.data == "help:replace")
async def help_replace(callback: CallbackQuery) -> None:
    """Akkaunt almashtirish yo'riqnomasi"""
    try:
        user = await get_user(callback.from_user.id)
        lang = user.get("language", "uz") if user else "uz"

        text = t("faq_a4", lang)
        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text=t("btn_orders", lang), callback_data="go:orders"),
                InlineKeyboardButton(text=t("btn_back", lang), callback_data="help:back"),
            ]]),
            parse_mode="HTML"
        )
        await callback.answer()
    except Exception:
        await callback.answer(t("error_general"), show_alert=True)
