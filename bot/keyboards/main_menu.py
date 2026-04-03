"""
Asosiy menyu klaviaturalari
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from bot.utils.texts import t


def main_menu_kb(lang: str = "uz") -> ReplyKeyboardMarkup:
    """Asosiy menyu — ReplyKeyboard, 3 qator"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=t("btn_catalog", lang)),
                KeyboardButton(text=t("btn_cart", lang)),
            ],
            [
                KeyboardButton(text=t("btn_orders", lang)),
                KeyboardButton(text=t("btn_bundles", lang)),
            ],
            [
                KeyboardButton(text=t("btn_profile", lang)),
                KeyboardButton(text=t("btn_help", lang)),
            ],
        ],
        resize_keyboard=True,
        is_persistent=True
    )


def profile_menu_kb(lang: str = "uz") -> InlineKeyboardMarkup:
    """Profil submenu — InlineKeyboard"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("btn_vip", lang), callback_data="profile:vip")],
            [InlineKeyboardButton(text=t("btn_favorites", lang), callback_data="profile:fav")],
            [InlineKeyboardButton(text=t("btn_referral", lang), callback_data="profile:ref")],
            [InlineKeyboardButton(text=t("btn_auto_renewal", lang), callback_data="profile:auto")],
            [InlineKeyboardButton(text=t("btn_change_lang", lang), callback_data="profile:lang")],
            [InlineKeyboardButton(text=t("btn_back", lang), callback_data="profile:back")],
        ]
    )


def help_menu_kb(lang: str = "uz") -> InlineKeyboardMarkup:
    """Yordam submenu — InlineKeyboard"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("btn_faq", lang), callback_data="help:faq")],
            [InlineKeyboardButton(text=t("btn_operator", lang), callback_data="help:operator")],
            [InlineKeyboardButton(text=t("btn_replacement", lang), callback_data="help:replace")],
            [InlineKeyboardButton(text=t("btn_back", lang), callback_data="help:back")],
        ]
    )


def language_select_kb() -> InlineKeyboardMarkup:
    """Til tanlash klaviaturasi"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang:uz"),
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
            ]
        ]
    )


def onboarding_done_kb(lang: str = "uz") -> InlineKeyboardMarkup:
    """Onboarding oxirgi tugmasi"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("onboarding_done_btn", lang), callback_data="onboarding:done")]
        ]
    )
