"""
Settings — DB dagi sozlamalarni cache bilan o'qish/yozish
"""
import json
import logging
import time
from typing import Any, Optional

logger = logging.getLogger(__name__)

# In-memory cache
_cache: dict[str, str] = {}
_cache_time: float = 0
_CACHE_TTL = 300  # 5 daqiqa


async def _load_cache() -> None:
    global _cache, _cache_time
    now = time.time()
    if _cache and (now - _cache_time) < _CACHE_TTL:
        return
    try:
        from bot.db.database import get_db
        async with get_db() as db:
            cursor = await db.execute("SELECT key, value FROM settings")
            rows = await cursor.fetchall()
            _cache = {row["key"]: row["value"] for row in rows}
            _cache_time = now
    except Exception as e:
        logger.error(f"Settings cache load error: {e}")


def invalidate_cache() -> None:
    global _cache_time
    _cache_time = 0


async def get_setting(key: str, default: str = "") -> str:
    await _load_cache()
    return _cache.get(key, default)


async def get_setting_int(key: str, default: int = 0) -> int:
    val = await get_setting(key, str(default))
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


async def get_setting_bool(key: str, default: bool = False) -> bool:
    val = await get_setting(key, str(default).lower())
    return val.lower() in ("true", "1", "yes")


async def get_setting_json(key: str, default: Any = None) -> Any:
    val = await get_setting(key, "")
    if not val:
        return default if default is not None else []
    try:
        return json.loads(val)
    except (json.JSONDecodeError, TypeError):
        return default if default is not None else []


async def set_setting(key: str, value: str) -> None:
    try:
        from bot.db.database import get_db
        async with get_db() as db:
            await db.execute(
                "UPDATE settings SET value = ?, updated_at = CURRENT_TIMESTAMP WHERE key = ?",
                (value, key)
            )
            if db.total_changes == 0:
                await db.execute(
                    "INSERT INTO settings (key, value, category, value_type) VALUES (?, ?, 'custom', 'text')",
                    (key, value)
                )
            await db.commit()
        _cache[key] = value
    except Exception as e:
        logger.exception(f"set_setting error: {e}")


async def get_settings_by_category(category: str) -> list[dict]:
    from bot.db.database import get_db
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM settings WHERE category = ? ORDER BY id", (category,)
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_all_settings() -> list[dict]:
    from bot.db.database import get_db
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM settings ORDER BY category, id")
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
