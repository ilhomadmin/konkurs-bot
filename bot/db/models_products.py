"""
Reviews, Favorites, Stock Notifications, Bundles, Admin Roles,
VIP, Finance, Auto Renewals, Cross-sell, Settings, Dashboard
"""
import json
import time
from typing import Optional

from bot.db.database import get_db
from bot.db.models_users import _get_user_id, get_user


# ==================== REVIEWS ====================

async def create_review(user_telegram_id: int, product_id: int,
                        order_item_id: int, rating: int,
                        comment: Optional[str] = None) -> int:
    async with get_db() as db:
        cursor_u = await db.execute("SELECT id FROM users WHERE telegram_id = ?", (user_telegram_id,))
        u_row = await cursor_u.fetchone()
        if not u_row:
            raise ValueError("User topilmadi")
        cursor = await db.execute("""
            INSERT OR IGNORE INTO reviews (user_id, product_id, order_item_id, rating, comment)
            VALUES (?, ?, ?, ?, ?)
        """, (u_row["id"], product_id, order_item_id, rating, comment))
        await db.commit()
        return cursor.lastrowid


async def get_product_rating(product_id: int) -> dict:
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT AVG(rating) as avg_rating, COUNT(*) as review_count
            FROM reviews
            WHERE product_id = ? AND is_visible = 1
        """, (product_id,))
        row = await cursor.fetchone()
        return {
            "avg": round(row["avg_rating"], 1) if row["avg_rating"] else 0.0,
            "count": row["review_count"]
        }


async def get_product_reviews(product_id: int, limit: int = 5) -> list[dict]:
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT r.*, u.full_name, u.username
            FROM reviews r
            JOIN users u ON u.id = r.user_id
            WHERE r.product_id = ? AND r.is_visible = 1
            ORDER BY r.created_at DESC LIMIT ?
        """, (product_id, limit))
        return [dict(r) for r in await cursor.fetchall()]


async def get_pending_reviews_to_request() -> list[dict]:
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT oi.id as order_item_id, oi.product_id,
                   u.telegram_id as user_telegram_id, u.language as user_lang,
                   p.name_uz, p.name_ru
            FROM order_items oi
            JOIN orders o ON o.id = oi.order_id
            JOIN users u ON u.id = o.user_id
            JOIN products p ON p.id = oi.product_id
            WHERE oi.status = 'delivered'
              AND date(oi.delivered_at) = date('now', '-3 days')
              AND oi.id NOT IN (SELECT order_item_id FROM reviews)
        """)
        return [dict(r) for r in await cursor.fetchall()]


async def set_review_visible(review_id: int, visible: int) -> None:
    async with get_db() as db:
        await db.execute("UPDATE reviews SET is_visible = ? WHERE id = ?", (visible, review_id))
        await db.commit()


async def get_all_reviews_for_admin(limit: int = 20, only_low: bool = False) -> list[dict]:
    async with get_db() as db:
        if only_low:
            cursor = await db.execute("""
                SELECT r.*, u.full_name, u.username, p.name_uz, p.name_ru
                FROM reviews r JOIN users u ON u.id = r.user_id
                JOIN products p ON p.id = r.product_id
                WHERE r.rating <= 2 AND r.is_visible = 1
                ORDER BY r.created_at DESC LIMIT ?
            """, (limit,))
        else:
            cursor = await db.execute("""
                SELECT r.*, u.full_name, u.username, p.name_uz, p.name_ru
                FROM reviews r JOIN users u ON u.id = r.user_id
                JOIN products p ON p.id = r.product_id
                ORDER BY r.created_at DESC LIMIT ?
            """, (limit,))
        return [dict(r) for r in await cursor.fetchall()]


# ==================== FAVORITES ====================

async def add_favorite(user_telegram_id: int, product_id: int) -> None:
    db_user_id = await _get_user_id(user_telegram_id)
    if not db_user_id:
        return
    async with get_db() as db:
        await db.execute(
            "INSERT OR IGNORE INTO favorites (user_id, product_id) VALUES (?, ?)",
            (db_user_id, product_id)
        )
        await db.commit()


async def remove_favorite(user_telegram_id: int, product_id: int) -> None:
    db_user_id = await _get_user_id(user_telegram_id)
    if not db_user_id:
        return
    async with get_db() as db:
        await db.execute(
            "DELETE FROM favorites WHERE user_id = ? AND product_id = ?",
            (db_user_id, product_id)
        )
        await db.commit()


async def is_favorite(user_telegram_id: int, product_id: int) -> bool:
    db_user_id = await _get_user_id(user_telegram_id)
    if not db_user_id:
        return False
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id FROM favorites WHERE user_id = ? AND product_id = ?",
            (db_user_id, product_id)
        )
        return (await cursor.fetchone()) is not None


async def get_user_favorites(user_id: int) -> list[dict]:
    """user_id = ichki DB id"""
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT f.product_id, p.name_uz as name,
                   (SELECT COUNT(*) FROM accounts a
                    WHERE a.product_id = f.product_id AND a.status = 'available') as stock
            FROM favorites f
            JOIN products p ON p.id = f.product_id
            WHERE f.user_id = ?
            ORDER BY f.created_at DESC
        """, (user_id,))
        return [dict(r) for r in await cursor.fetchall()]


async def add_to_favorites(user_id: int, product_id: int) -> None:
    """user_id = ichki DB id"""
    async with get_db() as db:
        await db.execute(
            "INSERT OR IGNORE INTO favorites (user_id, product_id) VALUES (?, ?)",
            (user_id, product_id)
        )
        await db.commit()


async def remove_from_favorites(user_id: int, product_id: int) -> None:
    """user_id = ichki DB id"""
    async with get_db() as db:
        await db.execute(
            "DELETE FROM favorites WHERE user_id = ? AND product_id = ?",
            (user_id, product_id)
        )
        await db.commit()


async def is_in_favorites(user_id: int, product_id: int) -> bool:
    """user_id = ichki DB id"""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT 1 FROM favorites WHERE user_id = ? AND product_id = ?",
            (user_id, product_id)
        )
        return bool(await cursor.fetchone())


# ==================== STOCK NOTIFICATIONS ====================

async def add_stock_notification(user_telegram_id: int, product_id: int) -> None:
    db_user_id = await _get_user_id(user_telegram_id)
    if not db_user_id:
        return
    async with get_db() as db:
        await db.execute(
            "INSERT OR IGNORE INTO stock_notifications (user_id, product_id) VALUES (?, ?)",
            (db_user_id, product_id)
        )
        await db.commit()


async def add_stock_notify(user_id: int, product_id: int) -> None:
    """user_id = ichki DB id"""
    async with get_db() as db:
        cursor = await db.execute("SELECT telegram_id FROM users WHERE id = ?", (user_id,))
        row = await cursor.fetchone()
        if row:
            await add_stock_notification(row["telegram_id"], product_id)


async def get_stock_notification_users(product_id: int) -> list[int]:
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT u.telegram_id FROM stock_notifications sn
            JOIN users u ON u.id = sn.user_id
            WHERE sn.product_id = ? AND sn.notified = 0
        """, (product_id,))
        return [r["telegram_id"] for r in await cursor.fetchall()]


get_stock_notifications = get_stock_notification_users


async def mark_stock_notified(product_id: int) -> None:
    async with get_db() as db:
        await db.execute(
            "UPDATE stock_notifications SET notified = 1 WHERE product_id = ?",
            (product_id,)
        )
        await db.commit()


mark_notified = mark_stock_notified


async def get_low_stock_products(threshold: int = 3) -> list[dict]:
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT a.product_id, COUNT(*) as cnt,
                   p.name_uz, p.name_ru
            FROM accounts a
            JOIN products p ON p.id = a.product_id
            WHERE a.status = 'available'
            GROUP BY a.product_id
            HAVING cnt <= ?
        """, (threshold,))
        return [dict(r) for r in await cursor.fetchall()]


# ==================== ADMIN ROLES ====================

async def create_admin_role(telegram_id: int, role: str = "operator",
                            username: Optional[str] = None,
                            full_name: Optional[str] = None) -> int:
    async with get_db() as db:
        cursor = await db.execute("""
            INSERT OR REPLACE INTO admin_roles (telegram_id, role, username, full_name)
            VALUES (?, ?, ?, ?)
        """, (telegram_id, role, username, full_name))
        await db.commit()
        return cursor.lastrowid


async def get_admin_by_telegram_id(telegram_id: int) -> Optional[dict]:
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM admin_roles WHERE telegram_id = ? AND is_active = 1",
            (telegram_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_all_admins() -> list[dict]:
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM admin_roles ORDER BY created_at")
        return [dict(r) for r in await cursor.fetchall()]


async def update_admin_role(telegram_id: int, role: str) -> None:
    async with get_db() as db:
        await db.execute(
            "UPDATE admin_roles SET role = ? WHERE telegram_id = ?",
            (role, telegram_id)
        )
        await db.commit()


async def delete_admin_role(telegram_id: int) -> None:
    async with get_db() as db:
        await db.execute(
            "UPDATE admin_roles SET is_active = 0 WHERE telegram_id = ?",
            (telegram_id,)
        )
        await db.commit()


async def update_admin_password(telegram_id: int, password_hash: str) -> None:
    async with get_db() as db:
        await db.execute(
            "UPDATE admin_roles SET password_hash = ? WHERE telegram_id = ?",
            (password_hash, telegram_id)
        )
        await db.commit()


async def get_all_operators() -> list[dict]:
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT ar.telegram_id, ar.username, ar.role, u.language
            FROM admin_roles ar
            LEFT JOIN users u ON u.telegram_id = ar.telegram_id
            WHERE ar.role IN ('operator', 'manager', 'boss') AND ar.is_active = 1
        """)
        return [dict(r) for r in await cursor.fetchall()]


async def get_all_managers_and_bosses() -> list[int]:
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT telegram_id FROM admin_roles WHERE role IN ('manager','boss') AND is_active = 1"
        )
        return [r["telegram_id"] for r in await cursor.fetchall()]


# ==================== VIP LEVELS ====================

async def get_vip_level(level: str) -> Optional[dict]:
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM vip_levels WHERE level = ?", (level,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_all_vip_levels() -> list[dict]:
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM vip_levels ORDER BY min_purchases")
        return [dict(r) for r in await cursor.fetchall()]


get_vip_levels = get_all_vip_levels


async def check_and_upgrade_vip(telegram_id: int) -> str:
    user = await get_user(telegram_id)
    if not user:
        return "standard"
    total = user.get("total_purchases", 0)
    levels = await get_all_vip_levels()
    new_level = "standard"
    for lv in sorted(levels, key=lambda x: x["min_purchases"], reverse=True):
        if total >= lv["min_purchases"]:
            new_level = lv["level"]
            break
    async with get_db() as db:
        await db.execute(
            "UPDATE users SET vip_level = ? WHERE telegram_id = ?",
            (new_level, telegram_id)
        )
        await db.commit()
    return new_level


update_user_vip = check_and_upgrade_vip


# ==================== AUTO RENEWALS ====================

async def create_auto_renewal(user_telegram_id: int, product_id: int,
                              order_item_id: int, next_renewal_date: str) -> int:
    db_user_id = await _get_user_id(user_telegram_id)
    if not db_user_id:
        raise ValueError("User topilmadi")
    async with get_db() as db:
        cursor = await db.execute("""
            INSERT OR REPLACE INTO auto_renewals
                (user_id, product_id, order_item_id, status, next_renewal_date)
            VALUES (?, ?, ?, 'active', ?)
        """, (db_user_id, product_id, order_item_id, next_renewal_date))
        await db.commit()
        return cursor.lastrowid


async def get_user_auto_renewals(telegram_id: int) -> list[dict]:
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT ar.*, p.name_uz, p.name_ru
            FROM auto_renewals ar
            JOIN users u ON u.id = ar.user_id
            JOIN products p ON p.id = ar.product_id
            WHERE u.telegram_id = ? AND ar.status = 'active'
        """, (telegram_id,))
        return [dict(r) for r in await cursor.fetchall()]


async def get_user_auto_renewals_by_id(user_id: int) -> list[dict]:
    """user_id = ichki DB id"""
    async with get_db() as db:
        cursor = await db.execute("SELECT telegram_id FROM users WHERE id = ?", (user_id,))
        row = await cursor.fetchone()
        if not row:
            return []
        return await get_user_auto_renewals(row["telegram_id"])


async def update_auto_renewal(renewal_id: int, **kwargs) -> None:
    allowed = {"status", "next_renewal_date"}
    fields = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [renewal_id]
    async with get_db() as db:
        await db.execute(f"UPDATE auto_renewals SET {set_clause} WHERE id = ?", values)
        await db.commit()


async def get_due_auto_renewals(tomorrow: str) -> list[dict]:
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT ar.*, u.telegram_id as user_telegram_id, u.language as user_lang,
                   p.name_uz, p.name_ru
            FROM auto_renewals ar
            JOIN users u ON u.id = ar.user_id
            JOIN products p ON p.id = ar.product_id
            WHERE ar.status = 'active' AND ar.next_renewal_date = ?
        """, (tomorrow,))
        return [dict(r) for r in await cursor.fetchall()]


async def delete_auto_renewal(renewal_id: int) -> None:
    async with get_db() as db:
        await db.execute("DELETE FROM auto_renewals WHERE id = ?", (renewal_id,))
        await db.commit()


deactivate_auto_renewal = delete_auto_renewal


# ==================== BUNDLES ====================

async def create_bundle(name_uz: str, name_ru: str,
                        description_uz: Optional[str] = None,
                        description_ru: Optional[str] = None,
                        discount_percent: int = 0, price: int = 0) -> int:
    async with get_db() as db:
        cursor = await db.execute("""
            INSERT INTO bundles (name_uz, name_ru, description_uz, description_ru, discount_percent, price)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name_uz, name_ru, description_uz, description_ru, discount_percent, price))
        await db.commit()
        return cursor.lastrowid


async def add_bundle_item(bundle_id: int, product_id: int, quantity: int = 1) -> None:
    async with get_db() as db:
        await db.execute("""
            INSERT INTO bundle_items (bundle_id, product_id, quantity)
            VALUES (?, ?, ?)
        """, (bundle_id, product_id, quantity))
        await db.commit()


async def get_active_bundles() -> list[dict]:
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM bundles WHERE is_active = 1 ORDER BY id")
        return [dict(r) for r in await cursor.fetchall()]


get_all_bundles = get_active_bundles


async def get_bundle_by_id(bundle_id: int) -> Optional[dict]:
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM bundles WHERE id = ?", (bundle_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_bundle_items(bundle_id: int) -> list[dict]:
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT bi.*, p.name_uz, p.name_ru, p.price
            FROM bundle_items bi
            JOIN products p ON p.id = bi.product_id
            WHERE bi.bundle_id = ?
        """, (bundle_id,))
        return [dict(r) for r in await cursor.fetchall()]


async def get_all_bundles_admin() -> list[dict]:
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM bundles ORDER BY id")
        return [dict(r) for r in await cursor.fetchall()]


async def update_bundle(bundle_id: int, **kwargs) -> None:
    allowed = {"name_uz", "name_ru", "description_uz", "description_ru",
               "discount_percent", "price", "is_active"}
    fields = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [bundle_id]
    async with get_db() as db:
        await db.execute(f"UPDATE bundles SET {set_clause} WHERE id = ?", values)
        await db.commit()


# ==================== FINANCE ====================

async def get_finance_report(date_from: str, date_to: str) -> dict:
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT
                SUM(oi.unit_price * oi.quantity) as revenue,
                SUM(oi.cost_price * oi.quantity) as cost,
                COUNT(DISTINCT oi.order_id) as order_count,
                SUM(CASE WHEN o.status='auto_delivered' THEN 1 ELSE 0 END) as direct_count
            FROM order_items oi
            JOIN orders o ON o.id = oi.order_id
            WHERE oi.status IN ('delivered','replaced')
              AND date(oi.delivered_at) BETWEEN ? AND ?
        """, (date_from, date_to))
        row = await cursor.fetchone()
        revenue = row["revenue"] or 0
        cost = row["cost"] or 0
        order_count = row["order_count"] or 0
        direct_count = row["direct_count"] or 0

        cursor2 = await db.execute("""
            SELECT SUM(amount) as total_expenses, category,
                   GROUP_CONCAT(description || ': ' || amount) as details
            FROM expenses
            WHERE date BETWEEN ? AND ?
            GROUP BY category
        """, (date_from, date_to))
        expense_rows = await cursor2.fetchall()
        total_expenses = sum(r["total_expenses"] or 0 for r in expense_rows)
        expense_details = [dict(r) for r in expense_rows]

        gross_profit = revenue - cost
        net_profit = gross_profit - total_expenses
        avg_check = revenue // order_count if order_count else 0
        margin = round(gross_profit * 100 / revenue, 1) if revenue else 0

        return {
            "revenue": revenue,
            "cost": cost,
            "order_count": order_count,
            "direct_count": direct_count,
            "total_expenses": total_expenses,
            "expense_details": expense_details,
            "gross_profit": gross_profit,
            "net_profit": net_profit,
            "avg_check": avg_check,
            "margin": margin,
        }


async def get_daily_finance_data(days: int = 30) -> list[dict]:
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT
                date(oi.delivered_at) as day,
                SUM(oi.unit_price * oi.quantity) as revenue,
                SUM(oi.cost_price * oi.quantity) as cost
            FROM order_items oi
            WHERE oi.status IN ('delivered','replaced')
              AND date(oi.delivered_at) >= date('now', ? || ' days')
            GROUP BY day
            ORDER BY day
        """, (f"-{days}",))
        return [dict(r) for r in await cursor.fetchall()]


async def add_expense(date_str: str, category: str, amount: int,
                      description: Optional[str] = None,
                      created_by: Optional[int] = None) -> int:
    async with get_db() as db:
        cursor = await db.execute("""
            INSERT INTO expenses (date, category, description, amount, created_by)
            VALUES (?, ?, ?, ?, ?)
        """, (date_str, category, description, amount, created_by))
        await db.commit()
        return cursor.lastrowid


async def update_finance_cache_today() -> None:
    from datetime import date as dt
    today = str(dt.today())
    report = await get_finance_report(today, today)
    async with get_db() as db:
        await db.execute("""
            INSERT OR REPLACE INTO daily_finance_cache
                (date, total_revenue, total_cost, total_expenses, total_orders,
                 gross_profit, net_profit, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (today, report["revenue"], report["cost"], report["total_expenses"],
              report["order_count"], report["gross_profit"], report["net_profit"]))
        await db.commit()


update_daily_finance_cache = update_finance_cache_today


async def get_all_expenses(limit: int = 50) -> list[dict]:
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM expenses ORDER BY date DESC, id DESC LIMIT ?", (limit,))
        return [dict(r) for r in await cursor.fetchall()]


# ==================== CROSS-SELL ====================

async def get_cross_sell_recommendations(product_id: int, user_telegram_id: int) -> list[dict]:
    db_user_id = await _get_user_id(user_telegram_id)
    if not db_user_id:
        return []
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT oi2.product_id, COUNT(*) as cnt, p.name_uz, p.name_ru
            FROM order_items oi1
            JOIN order_items oi2 ON oi1.order_id = oi2.order_id
            JOIN products p ON p.id = oi2.product_id
            WHERE oi1.product_id = ?
              AND oi2.product_id != ?
              AND p.is_active = 1
              AND oi2.product_id NOT IN (
                  SELECT oi3.product_id FROM order_items oi3
                  JOIN orders o3 ON o3.id = oi3.order_id
                  WHERE o3.user_id = ?
              )
              AND oi2.product_id NOT IN (
                  SELECT product_id FROM cross_sell_log WHERE user_id = ?
              )
            GROUP BY oi2.product_id
            ORDER BY cnt DESC LIMIT 2
        """, (product_id, product_id, db_user_id, db_user_id))
        return [dict(r) for r in await cursor.fetchall()]


async def log_cross_sell(user_telegram_id: int, product_id: int) -> None:
    db_user_id = await _get_user_id(user_telegram_id)
    if not db_user_id:
        return
    async with get_db() as db:
        await db.execute(
            "INSERT OR IGNORE INTO cross_sell_log (user_id, product_id) VALUES (?, ?)",
            (db_user_id, product_id)
        )
        await db.commit()


async def log_cross_sell_by_id(user_id: int, product_ids: list) -> None:
    """user_id = ichki DB id"""
    async with get_db() as db:
        for pid in product_ids:
            await db.execute(
                "INSERT OR IGNORE INTO cross_sell_log (user_id, product_id) VALUES (?, ?)",
                (user_id, pid)
            )
        await db.commit()


async def get_cross_sell_targets() -> list[dict]:
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT DISTINCT u.id, u.telegram_id, u.language,
                   p.name_uz as last_product, p.id as last_product_id
            FROM users u
            JOIN orders o ON o.user_id = u.id
            JOIN order_items oi ON oi.order_id = o.id
            JOIN products p ON p.id = oi.product_id
            WHERE o.status IN ('confirmed','auto_delivered')
              AND o.created_at >= datetime('now', '-7 days')
              AND u.id NOT IN (
                  SELECT DISTINCT user_id FROM cross_sell_log
                  WHERE sent_at >= datetime('now', '-3 days')
              )
            LIMIT 100
        """)
        rows = await cursor.fetchall()
        targets = []
        for row in rows:
            recs = await get_cross_sell_recommendations(row["last_product_id"], row["telegram_id"])
            if recs:
                t = dict(row)
                t["recommendations"] = recs
                targets.append(t)
        return targets


# ==================== SETTINGS ====================

_settings_cache: dict = {}
_settings_cache_time: float = 0.0
_SETTINGS_TTL = 300  # 5 daqiqa


async def get_setting(key: str, default: str = "") -> str:
    global _settings_cache, _settings_cache_time
    now = time.time()
    if now - _settings_cache_time > _SETTINGS_TTL or not _settings_cache:
        await _refresh_settings_cache()
    return _settings_cache.get(key, default)


async def get_setting_json(key: str, default=None):
    val = await get_setting(key, "")
    if not val:
        return default
    try:
        return json.loads(val)
    except (json.JSONDecodeError, TypeError):
        return default


async def set_setting(key: str, value: str) -> None:
    global _settings_cache, _settings_cache_time
    async with get_db() as db:
        await db.execute(
            "UPDATE settings SET value = ?, updated_at = CURRENT_TIMESTAMP WHERE key = ?",
            (value, key)
        )
        await db.commit()
    _settings_cache[key] = value


async def get_all_settings() -> list[dict]:
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM settings ORDER BY category, id")
        return [dict(r) for r in await cursor.fetchall()]


async def get_settings_by_category(category: str) -> list[dict]:
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM settings WHERE category = ? ORDER BY id", (category,))
        return [dict(r) for r in await cursor.fetchall()]


async def _refresh_settings_cache() -> None:
    global _settings_cache, _settings_cache_time
    async with get_db() as db:
        cursor = await db.execute("SELECT key, value FROM settings")
        rows = await cursor.fetchall()
        _settings_cache = {r["key"]: r["value"] for r in rows}
        _settings_cache_time = time.time()


def invalidate_settings_cache() -> None:
    global _settings_cache_time
    _settings_cache_time = 0.0


# ==================== DASHBOARD ====================

async def get_dashboard_stats() -> dict:
    async with get_db() as db:
        # Users
        c = await db.execute("SELECT COUNT(*) as cnt FROM users")
        users_count = (await c.fetchone())["cnt"]

        # Today users
        c = await db.execute(
            "SELECT COUNT(*) as cnt FROM users WHERE date(created_at) = date('now')")
        today_users = (await c.fetchone())["cnt"]

        # Orders today
        c = await db.execute(
            "SELECT COUNT(*) as cnt FROM orders WHERE date(created_at) = date('now')")
        today_orders = (await c.fetchone())["cnt"]

        # Revenue today
        c = await db.execute("""
            SELECT COALESCE(SUM(oi.unit_price * oi.quantity), 0) as rev
            FROM order_items oi
            JOIN orders o ON o.id = oi.order_id
            WHERE oi.status IN ('delivered','replaced')
              AND date(oi.delivered_at) = date('now')
        """)
        today_revenue = (await c.fetchone())["rev"]

        # Pending orders
        c = await db.execute(
            "SELECT COUNT(*) as cnt FROM orders WHERE status IN ('pending_payment','payment_sent')")
        pending_orders = (await c.fetchone())["cnt"]

        # Pending replacements
        c = await db.execute(
            "SELECT COUNT(*) as cnt FROM replacements WHERE status = 'pending'")
        pending_replacements = (await c.fetchone())["cnt"]

        # Total accounts available
        c = await db.execute(
            "SELECT COUNT(*) as cnt FROM accounts WHERE status = 'available'")
        available_accounts = (await c.fetchone())["cnt"]

        # Total products
        c = await db.execute("SELECT COUNT(*) as cnt FROM products WHERE is_active = 1")
        products_count = (await c.fetchone())["cnt"]

        return {
            "users_count": users_count,
            "today_users": today_users,
            "today_orders": today_orders,
            "today_revenue": today_revenue,
            "pending_orders": pending_orders,
            "pending_replacements": pending_replacements,
            "available_accounts": available_accounts,
            "products_count": products_count,
        }


# ==================== MISC HELPERS ====================

async def get_user_by_id(user_id: int) -> Optional[dict]:
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_referral_count(user_id: int) -> int:
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT COUNT(*) as cnt FROM users WHERE referred_by = ?", (user_id,))
        row = await cursor.fetchone()
        return row["cnt"] if row else 0
