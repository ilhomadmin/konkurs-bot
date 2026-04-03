"""
Umumiy klaviaturalar
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

from bot.utils.texts import t


def back_kb(callback_data: str = "back", lang: str = "uz") -> InlineKeyboardMarkup:
    """Faqat 'Ortga' tugmasidan iborat klaviatura"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("btn_back", lang), callback_data=callback_data)]
        ]
    )


def yes_no_kb(yes_data: str, no_data: str = "adm:cancel", lang: str = "uz") -> InlineKeyboardMarkup:
    """Ha/Yo'q tanlash"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t("btn_warranty_yes", lang), callback_data=yes_data),
                InlineKeyboardButton(text=t("btn_warranty_no", lang), callback_data=no_data),
            ]
        ]
    )
