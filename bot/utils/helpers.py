"""
Yordamchi funksiyalar
"""
from typing import Optional


def format_account_stats(stats: dict, lang: str = "uz") -> str:
    """Akkaunt statistikasini chiroyli formatda ko'rsatadi"""
    total = sum(stats.get(s, 0) for s in ("available", "reserved", "sold", "expired", "blocked"))
    available = stats.get("available", 0)
    reserved = stats.get("reserved", 0)
    sold = stats.get("sold", 0)
    expired = stats.get("expired", 0)

    by_tier = stats.get("by_tier", {})
    tier_parts = " | ".join(
        f"{tier.replace('_', '')}:{cnt}" for tier, cnt in by_tier.items()
    )

    if lang == "ru":
        lines = [
            f"Всего: {total} | ✅ Доступно: {available} | 🔒 Забронировано: {reserved}",
            f"✅ Продано: {sold} | ⛔ Истекло: {expired}",
        ]
        if tier_parts:
            lines.append(f"По тирам: {tier_parts}")
    else:
        lines = [
            f"Jami: {total} | ✅ Mavjud: {available} | 🔒 Band: {reserved}",
            f"✅ Sotilgan: {sold} | ⛔ Expired: {expired}",
        ]
        if tier_parts:
            lines.append(f"Tier bo'yicha: {tier_parts}")

    return "\n".join(lines)


def safe_int(value: str) -> Optional[int]:
    """Satrni butun songa aylantiradi, xato bo'lsa None qaytaradi"""
    try:
        return int(value.strip())
    except (ValueError, AttributeError):
        return None
