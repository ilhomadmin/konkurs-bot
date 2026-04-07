"""
Cart, Orders, Order Items, Replacements, Promo Codes, Flash Sales,
Abandoned Cart, Expiry Notifications, Pending Orders
"""
from typing import Optional

from bot.db.database import get_db
from bot.db.models_users import _get_user_id


# ==================== CART ====================

async def cart_get(telegram_id: int) -> list[dict]:
    """Foydalanuvchi savatini qaytaradi (product ma'lumotlari bilan)."""
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT ci.*, p.name_uz, p.name_ru, p.price, p.cost_price
            FROM cart_items ci
            JOIN users u ON u.id = ci.user_id
            JOIN products p ON p.id = ci.product_id
            WHERE u.telegram_id = ?
            ORDER BY ci.added_at
        """, (telegram_id,))
        return [dict(r) for r in await cursor.fetchall()]


async def cart_add(telegram_id: int, product_id: int, quantity: int = 1) -> None:
    """Savatga mahsulot qo'shadi yoki miqdorini oshiradi."""
    db_user_id = await _get_user_id(telegram_id)
    if not db_user_id:
        return
    async with get_db() as db:
        existing = await db.execute(
            "SELECT id, quantity FROM cart_items WHERE user_id = ? AND product_id = ?",
            (db_user_id, product_id)
        )
        ex_row = await existing.fetchone()
        if ex_row:
            await db.execute(
                "UPDATE cart_items SET quantity = ? WHERE id = ?",
                (ex_row["quantity"] + quantity, ex_row["id"])
            )
        else:
            await db.execute(
                "INSERT INTO cart_items (user_id, product_id, quantity) VALUES (?, ?, ?)",
                (db_user_id, product_id, quantity)
            )
        await db.commit()


async def cart_update_qty(telegram_id: int, product_id: int, quantity: int) -> None:
    """Savat elementining miqdorini yangilaydi (0 bo'lsa o'chiradi)."""
    db_user_id = await _get_user_id(telegram_id)
    if not db_user_id:
        return
    async with get_db() as db:
        if quantity <= 0:
            await db.execute(
                "DELETE FROM cart_items WHERE user_id = ? AND product_id = ?",
                (db_user_id, product_id)
            )
        else:
            await db.execute(
                "UPDATE cart_items SET quantity = ? WHERE user_id = ? AND product_id = ?",
                (quantity, db_user_id, product_id)
            )
        await db.commit()


async def cart_remove_item(cart_item_id: int) -> None:
    async with get_db() as db:
        await db.execute("DELETE FROM cart_items WHERE id = ?", (cart_item_id,))
        await db.commit()


async def cart_clear(telegram_id: int) -> None:
    db_user_id = await _get_user_id(telegram_id)
    if not db_user_id:
        return
    async with get_db() as db:
        await db.execute("DELETE FROM cart_items WHERE user_id = ?", (db_user_id,))
        await db.commit()


async def cart_count(telegram_id: int) -> int:
    db_user_id = await _get_user_id(telegram_id)
    if not db_user_id:
        return 0
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT COALESCE(SUM(quantity), 0) as cnt FROM cart_items WHERE user_id = ?",
            (db_user_id,))
        row = await cursor.fetchone()
        return row["cnt"] if row else 0


async def cart_item_in_cart(telegram_id: int, product_id: int) -> Optional[dict]:
    db_user_id = await _get_user_id(telegram_id)
    if not db_user_id:
        return None
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM cart_items WHERE user_id = ? AND product_id = ?",
            (db_user_id, product_id)
        )
        r = await cursor.fetchone()
        return dict(r) if r else None


# ==================== ORDERS ====================

async def create_order(user_telegram_id: int, total_amount: int,
                       discount_amount: int = 0, promo_code_id: Optional[int] = None) -> int:
    async with get_db() as db:
        cursor_u = await db.execute("SELECT id FROM users WHERE telegram_id = ?", (user_telegram_id,))
        u_row = await cursor_u.fetchone()
        if not u_row:
            raise ValueError("Foydalanuvchi topilmadi")
        cursor = await db.execute("""
            INSERT INTO orders (user_id, total_amount, discount_amount, promo_code_id, status)
            VALUES (?, ?, ?, ?, 'pending_payment')
        """, (u_row["id"], total_amount, discount_amount, promo_code_id))
        await db.commit()
        return cursor.lastrowid


async def get_order_by_id(order_id: int) -> Optional[dict]:
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT o.*, u.telegram_id as user_telegram_id, u.language as user_lang,
                   u.username as user_username, u.full_name as user_full_name
            FROM orders o
            JOIN users u ON u.id = o.user_id
            WHERE o.id = ?
        """, (order_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


get_order = get_order_by_id


async def get_user_orders(telegram_id: int, limit: int = 20, offset: int = 0) -> list[dict]:
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT o.* FROM orders o
            JOIN users u ON u.id = o.user_id
            WHERE u.telegram_id = ?
            ORDER BY o.created_at DESC
            LIMIT ? OFFSET ?
        """, (telegram_id, limit, offset))
        return [dict(r) for r in await cursor.fetchall()]


async def get_user_active_order(telegram_id: int) -> Optional[dict]:
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT o.* FROM orders o
            JOIN users u ON u.id = o.user_id
            WHERE u.telegram_id = ? AND o.status IN ('pending_payment', 'payment_sent')
            ORDER BY o.created_at DESC LIMIT 1
        """, (telegram_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def update_order_status(order_id: int, status: str, **extra) -> None:
    allowed_extra = {"payment_screenshot_file_id", "payment_verified_by",
                     "payment_verified_at", "progress_message_id", "note"}
    fields = {"status": status, "updated_at": "CURRENT_TIMESTAMP"}
    fields.update({k: v for k, v in extra.items() if k in allowed_extra})

    set_parts = []
    values = []
    for k, v in fields.items():
        if v == "CURRENT_TIMESTAMP":
            set_parts.append(f"{k} = CURRENT_TIMESTAMP")
        else:
            set_parts.append(f"{k} = ?")
            values.append(v)
    values.append(order_id)

    async with get_db() as db:
        await db.execute(
            f"UPDATE orders SET {', '.join(set_parts)} WHERE id = ?", values
        )
        await db.commit()


async def set_order_progress_message(order_id: int, message_id: int) -> None:
    async with get_db() as db:
        await db.execute(
            "UPDATE orders SET progress_message_id = ? WHERE id = ?",
            (message_id, order_id)
        )
        await db.commit()


async def count_user_orders(telegram_id: int) -> int:
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT COUNT(*) as cnt FROM orders o
            JOIN users u ON u.id = o.user_id
            WHERE u.telegram_id = ?
        """, (telegram_id,))
        row = await cursor.fetchone()
        return row["cnt"] if row else 0


async def has_any_order(telegram_id: int) -> bool:
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT COUNT(*) as cnt FROM orders o
            JOIN users u ON u.id = o.user_id
            WHERE u.telegram_id = ? AND o.status IN ('confirmed','auto_delivered','partial')
        """, (telegram_id,))
        row = await cursor.fetchone()
        return (row["cnt"] or 0) > 0


async def get_orders_by_status(status: str, limit: int = 50) -> list[dict]:
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT o.*, u.telegram_id as user_telegram_id, u.language as user_lang
            FROM orders o
            JOIN users u ON u.id = o.user_id
            WHERE o.status = ?
            ORDER BY o.created_at DESC LIMIT ?
        """, (status, limit))
        return [dict(r) for r in await cursor.fetchall()]


async def get_pending_orders_count() -> int:
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT COUNT(*) as cnt FROM orders WHERE status IN ('pending_payment','payment_sent')")
        row = await cursor.fetchone()
        return row["cnt"] if row else 0


async def get_recent_orders(limit: int = 20) -> list[dict]:
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT o.*, u.telegram_id as user_telegram_id,
                   u.username as user_username, u.full_name as user_full_name
            FROM orders o
            JOIN users u ON u.id = o.user_id
            ORDER BY o.created_at DESC LIMIT ?
        """, (limit,))
        return [dict(r) for r in await cursor.fetchall()]


async def get_expired_pending_orders(timeout_minutes: int = 30) -> list[dict]:
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT o.*, u.telegram_id as user_telegram_id, u.language as user_lang
            FROM orders o
            JOIN users u ON u.id = o.user_id
            WHERE o.status IN ('pending_payment', 'payment_sent')
              AND datetime(o.created_at, '+' || ? || ' minutes') < datetime('now')
        """, (timeout_minutes,))
        return [dict(r) for r in await cursor.fetchall()]


# ==================== ORDER ITEMS ====================

async def add_order_item(order_id: int, product_id: int, quantity: int,
                         unit_price: int, cost_price: int = 0) -> int:
    async with get_db() as db:
        cursor = await db.execute("""
            INSERT INTO order_items (order_id, product_id, quantity, unit_price, cost_price, status)
            VALUES (?, ?, ?, ?, ?, 'pending')
        """, (order_id, product_id, quantity, unit_price, cost_price))
        await db.commit()
        return cursor.lastrowid


async def get_order_items(order_id: int) -> list[dict]:
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT oi.*, p.name_uz, p.name_ru,
                   p.instruction_video_file_id,
                   p.category_id,
                   a.login, a.password, a.expiry_date as account_expiry,
                   a.additional_data,
                   c.instruction_video_file_id as category_video
            FROM order_items oi
            JOIN products p ON p.id = oi.product_id
            LEFT JOIN accounts a ON a.id = oi.account_id
            LEFT JOIN categories c ON c.id = p.category_id
            WHERE oi.order_id = ?
            ORDER BY oi.id
        """, (order_id,))
        return [dict(r) for r in await cursor.fetchall()]


async def get_order_item_by_id(order_item_id: int) -> Optional[dict]:
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT oi.*, p.name_uz as product_name, p.id as product_id
            FROM order_items oi
            JOIN products p ON p.id = oi.product_id
            WHERE oi.id = ?
        """, (order_item_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def update_order_item(item_id: int, **kwargs) -> None:
    allowed = {"account_id", "status", "delivered_at", "expiry_date"}
    fields = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [item_id]
    async with get_db() as db:
        await db.execute(f"UPDATE order_items SET {set_clause} WHERE id = ?", values)
        await db.commit()


# ==================== EXPIRY NOTIFICATIONS ====================

async def get_expiring_order_items(days_left: int, notified_field: str) -> list[dict]:
    allowed = {"expiry_notified_3d", "expiry_notified_1d", "expiry_notified_0d"}
    if notified_field not in allowed:
        return []
    async with get_db() as db:
        cursor = await db.execute(f"""
            SELECT oi.id, oi.product_id, oi.expiry_date,
                   u.telegram_id as user_telegram_id, u.language as user_lang,
                   p.name_uz, p.name_ru
            FROM order_items oi
            JOIN orders o ON o.id = oi.order_id
            JOIN users u ON u.id = o.user_id
            JOIN products p ON p.id = oi.product_id
            WHERE oi.status = 'delivered'
              AND oi.expiry_date IS NOT NULL
              AND date(oi.expiry_date) = date('now', '+{days_left} days')
              AND oi.{notified_field} = 0
        """)
        return [dict(r) for r in await cursor.fetchall()]


async def mark_expiry_notified(order_item_id: int, notified_field: str) -> None:
    allowed = {"expiry_notified_3d", "expiry_notified_1d", "expiry_notified_0d"}
    if notified_field not in allowed:
        return
    async with get_db() as db:
        await db.execute(
            f"UPDATE order_items SET {notified_field} = 1 WHERE id = ?",
            (order_item_id,)
        )
        await db.commit()


# ==================== REPLACEMENTS ====================

async def create_replacement(order_item_id: int, user_telegram_id: int, reason: str,
                             description: Optional[str] = None,
                             screenshot_file_id: Optional[str] = None) -> int:
    async with get_db() as db:
        cursor_u = await db.execute("SELECT id FROM users WHERE telegram_id = ?", (user_telegram_id,))
        u_row = await cursor_u.fetchone()
        if not u_row:
            raise ValueError("Foydalanuvchi topilmadi")
        cursor = await db.execute("""
            INSERT INTO replacements (order_item_id, user_id, reason, description, screenshot_file_id)
            VALUES (?, ?, ?, ?, ?)
        """, (order_item_id, u_row["id"], reason, description, screenshot_file_id))
        await db.commit()
        return cursor.lastrowid


async def get_replacement_by_id(replacement_id: int) -> Optional[dict]:
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT r.*, u.telegram_id as user_telegram_id, u.language as user_lang,
                   u.username as user_username, u.full_name as user_full_name,
                   oi.product_id, oi.delivered_at,
                   p.name_uz, p.name_ru, p.warranty_days
            FROM replacements r
            JOIN users u ON u.id = r.user_id
            JOIN order_items oi ON oi.id = r.order_item_id
            JOIN products p ON p.id = oi.product_id
            WHERE r.id = ?
        """, (replacement_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_pending_replacements() -> list[dict]:
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT r.*, u.telegram_id as user_telegram_id,
                   u.username as user_username, u.full_name as user_full_name,
                   p.name_uz, p.name_ru
            FROM replacements r
            JOIN users u ON u.id = r.user_id
            JOIN order_items oi ON oi.id = r.order_item_id
            JOIN products p ON p.id = oi.product_id
            WHERE r.status = 'pending'
            ORDER BY r.created_at DESC
        """)
        return [dict(r) for r in await cursor.fetchall()]


async def update_replacement_status(replacement_id: int, status: str,
                                    admin_note: Optional[str] = None) -> None:
    async with get_db() as db:
        await db.execute("""
            UPDATE replacements
            SET status = ?, admin_note = ?, resolved_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (status, admin_note, replacement_id))
        await db.commit()


async def get_user_replaceable_items(telegram_id: int) -> list[dict]:
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT oi.*, p.name_uz, p.name_ru, p.warranty_days,
                   o.id as order_id
            FROM order_items oi
            JOIN orders o ON o.id = oi.order_id
            JOIN users u ON u.id = o.user_id
            JOIN products p ON p.id = oi.product_id
            WHERE u.telegram_id = ?
              AND oi.status = 'delivered'
              AND p.has_warranty = 1
              AND p.warranty_days > 0
              AND date(oi.delivered_at, '+' || p.warranty_days || ' days') >= date('now')
            ORDER BY oi.delivered_at DESC
        """, (telegram_id,))
        return [dict(r) for r in await cursor.fetchall()]


async def get_all_replacements(limit: int = 50) -> list[dict]:
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT r.*, u.telegram_id as user_telegram_id,
                   u.username as user_username, u.full_name as user_full_name,
                   p.name_uz, p.name_ru
            FROM replacements r
            JOIN users u ON u.id = r.user_id
            JOIN order_items oi ON oi.id = r.order_item_id
            JOIN products p ON p.id = oi.product_id
            ORDER BY r.created_at DESC LIMIT ?
        """, (limit,))
        return [dict(r) for r in await cursor.fetchall()]


# ==================== PROMO CODES ====================

async def create_promo_code(code: str, discount_percent: int, max_uses: int = -1,
                            valid_from: Optional[str] = None,
                            valid_until: Optional[str] = None) -> int:
    async with get_db() as db:
        cursor = await db.execute("""
            INSERT INTO promo_codes (code, discount_percent, max_uses, valid_from, valid_until)
            VALUES (?, ?, ?, ?, ?)
        """, (code.upper().strip(), discount_percent, max_uses, valid_from, valid_until))
        await db.commit()
        return cursor.lastrowid


create_promo = create_promo_code


async def get_promo_by_code(code: str) -> Optional[dict]:
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM promo_codes WHERE code = ? AND is_active = 1",
            (code.upper().strip(),)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_all_promo_codes() -> list[dict]:
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM promo_codes ORDER BY created_at DESC")
        return [dict(r) for r in await cursor.fetchall()]


get_all_promos = get_all_promo_codes


async def increment_promo_usage(promo_id: int) -> None:
    async with get_db() as db:
        await db.execute(
            "UPDATE promo_codes SET used_count = used_count + 1 WHERE id = ?",
            (promo_id,)
        )
        await db.commit()


async def update_promo_code(promo_id: int, **kwargs) -> None:
    allowed = {"is_active", "max_uses", "valid_until", "discount_percent"}
    fields = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [promo_id]
    async with get_db() as db:
        await db.execute(f"UPDATE promo_codes SET {set_clause} WHERE id = ?", values)
        await db.commit()


async def activate_promo_code(promo_id: int) -> None:
    async with get_db() as db:
        await db.execute("UPDATE promo_codes SET is_active = 1 WHERE id = ?", (promo_id,))
        await db.commit()


async def deactivate_promo_code(promo_id: int) -> None:
    async with get_db() as db:
        await db.execute("UPDATE promo_codes SET is_active = 0 WHERE id = ?", (promo_id,))
        await db.commit()


async def get_promo_stats(promo_id: int) -> dict:
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT COUNT(*) as order_count, SUM(total_amount) as total_revenue
            FROM orders WHERE promo_code_id = ? AND status IN ('confirmed','auto_delivered','partial')
        """, (promo_id,))
        row = await cursor.fetchone()
        return dict(row) if row else {"order_count": 0, "total_revenue": 0}


# ==================== FLASH SALES ====================

async def create_flash_sale(product_id: int, discount_percent: int,
                            starts_at: str, ends_at: str) -> int:
    async with get_db() as db:
        cursor = await db.execute("""
            INSERT INTO flash_sales (product_id, discount_percent, starts_at, ends_at, is_active)
            VALUES (?, ?, ?, ?, 1)
        """, (product_id, discount_percent, starts_at, ends_at))
        await db.commit()
        return cursor.lastrowid


async def get_active_flash_sale(product_id: int) -> Optional[dict]:
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT * FROM flash_sales
            WHERE product_id = ? AND is_active = 1
              AND datetime('now') BETWEEN datetime(starts_at) AND datetime(ends_at)
        """, (product_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_active_flash_sales() -> list[dict]:
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT fs.*, p.name_uz, p.name_ru FROM flash_sales fs
            JOIN products p ON p.id = fs.product_id
            WHERE fs.is_active = 1
              AND datetime('now') BETWEEN datetime(fs.starts_at) AND datetime(fs.ends_at)
            ORDER BY fs.ends_at ASC
        """)
        return [dict(r) for r in await cursor.fetchall()]


async def get_all_flash_sales() -> list[dict]:
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT fs.*, p.name_uz, p.name_ru FROM flash_sales fs
            JOIN products p ON p.id = fs.product_id
            ORDER BY fs.created_at DESC LIMIT 20
        """)
        return [dict(r) for r in await cursor.fetchall()]


async def deactivate_expired_flash_sales() -> int:
    async with get_db() as db:
        cursor = await db.execute("""
            UPDATE flash_sales SET is_active = 0
            WHERE is_active = 1 AND datetime(ends_at) < datetime('now')
        """)
        await db.commit()
        return cursor.rowcount


async def update_flash_sale(sale_id: int, **kwargs) -> None:
    allowed = {"is_active", "discount_percent", "starts_at", "ends_at"}
    fields = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [sale_id]
    async with get_db() as db:
        await db.execute(f"UPDATE flash_sales SET {set_clause} WHERE id = ?", values)
        await db.commit()


# ==================== ABANDONED CART ====================

async def get_abandoned_cart_users(hours: int, sent_field: str) -> list[dict]:
    allowed = {"reminder_sent_2h", "reminder_sent_24h"}
    if sent_field not in allowed:
        return []
    async with get_db() as db:
        cursor = await db.execute(f"""
            SELECT DISTINCT u.telegram_id as user_telegram_id, u.language as user_lang,
                   u.id as db_user_id
            FROM cart_items ci
            JOIN users u ON u.id = ci.user_id
            WHERE datetime(ci.added_at, '+{hours} hours') < datetime('now')
              AND ci.{sent_field} = 0
              AND NOT EXISTS (
                  SELECT 1 FROM orders o
                  WHERE o.user_id = u.id
                    AND o.status IN ('pending_payment','payment_sent')
              )
        """)
        return [dict(r) for r in await cursor.fetchall()]


async def mark_cart_reminder_sent(db_user_id: int, sent_field: str) -> None:
    allowed = {"reminder_sent_2h", "reminder_sent_24h"}
    if sent_field not in allowed:
        return
    async with get_db() as db:
        await db.execute(
            f"UPDATE cart_items SET {sent_field} = 1 WHERE user_id = ?",
            (db_user_id,)
        )
        await db.commit()
