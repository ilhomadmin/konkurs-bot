"""
Muddat (kun) → tier mapping va ko'rsatish nomlarini hisoblash
"""

# Tier chegaralari
TIER_RANGES = [
    ("15_days",   1,   15),
    ("1_month",  16,   45),
    ("3_months", 46,  105),
    ("6_months", 106, 195),
    ("12_months", 196, 99999),
]

# Tier ko'rsatish nomlari
TIER_DISPLAY = {
    "15_days":   {"uz": "15 kun",  "ru": "15 дней"},
    "1_month":   {"uz": "1 oy",    "ru": "1 месяц"},
    "3_months":  {"uz": "3 oy",    "ru": "3 месяца"},
    "6_months":  {"uz": "6 oy",    "ru": "6 месяцев"},
    "12_months": {"uz": "12 oy",   "ru": "12 месяцев"},
}

# Tier min/max kunlar (product_prices uchun)
TIER_MIN_MAX = {
    "15_days":   (1,   15),
    "1_month":   (16,  45),
    "3_months":  (46,  105),
    "6_months":  (106, 195),
    "12_months": (196, 99999),
}


def days_to_tier(remaining_days: int) -> str:
    """
    Qolgan kunlar soniga qarab tier stringini qaytaradi.
    Masalan: 20 → '1_month', 100 → '3_months'
    """
    for tier, min_d, max_d in TIER_RANGES:
        if min_d <= remaining_days <= max_d:
            return tier
    # 0 va undan kam bo'lsa — eng kichik tier qaytariladi
    return "15_days"


def tier_display_name(tier: str, lang: str = "uz") -> str:
    """
    Tier string bo'yicha foydalanuvchiga ko'rinadigan nom qaytaradi.
    Masalan: tier_display_name('1_month', 'uz') → '1 oy'
    """
    lang = lang if lang in ("uz", "ru") else "uz"
    return TIER_DISPLAY.get(tier, {}).get(lang, tier)


def all_tiers() -> list[str]:
    """Barcha tier stringlarini tartib bilan qaytaradi"""
    return [t[0] for t in TIER_RANGES]
