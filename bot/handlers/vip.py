from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.db.models import get_user_by_telegram_id, get_user_total_spent
from bot.utils.texts import t

router = Router()

VIP_LEVELS = [
    {"name": "🥉 Bronze", "min": 500_000, "discount": 3},
    {"name": "🥈 Silver", "min": 2_000_000, "discount": 5},
    {"name": "🥇 Gold", "min": 5_000_000, "discount": 8},
    {"name": "💎 Platinum", "min": 10_000_000, "discount": 12},
]


def get_vip_info(total: int):
    level_name = None
    discount = 0
    next_threshold = VIP_LEVELS[0]["min"]

    for lvl in VIP_LEVELS:
        if total >= lvl["min"]:
            level_name = lvl["name"]
            discount = lvl["discount"]
        else:
            next_threshold = lvl["min"]
            break
    else:
        next_threshold = None

    if next_threshold is None:
        remaining = 0
        bar_pct = 100
    else:
        remaining = max(0, next_threshold - total)
        prev = 0
        for lvl in VIP_LEVELS:
            if total < lvl["min"]:
                span = lvl["min"] - prev
                prog = total - prev
                bar_pct = min(100, int(prog * 100 / span)) if span > 0 else 0
                break
            prev = lvl["min"]
        else:
            bar_pct = 100

    filled = bar_pct // 10
    bar = "🟩" * filled + "⬜" * (10 - filled) + f" {bar_pct}%"
    return level_name, discount, remaining, bar


@router.callback_query(F.data == "vip_page")
async def vip_page(call: CallbackQuery):
    user = await get_user_by_telegram_id(call.from_user.id)
    if not user:
        await call.answer()
        return
    lang = user.get("language", "uz")
    total = await get_user_total_spent(user["id"])

    level_name, discount, remaining, bar = get_vip_info(total)
    if level_name is None:
        level_name = t("vip_none", lang)

    text = t("vip_page", lang,
             level=level_name,
             total=total,
             next=remaining,
             bar=bar,
             discount=discount)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_vip_levels", lang), callback_data="vip_levels")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="profile_page")],
    ])
    await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data == "vip_levels")
async def vip_levels(call: CallbackQuery):
    user = await get_user_by_telegram_id(call.from_user.id)
    lang = user.get("language", "uz") if user else "uz"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="vip_page")]
    ])
    await call.message.edit_text(t("vip_levels", lang), reply_markup=kb, parse_mode="HTML")
    await call.answer()
