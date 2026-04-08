"""
Users, Categories, Products, Accounts CRUD
"""
import secrets
from datetime import date, timedelta
from typing import Optional

from bot.db.database import get_db


# ==================== HELPER ====================

async def _get_user_id(telegram_id: int) -> Optional[int]:
    async with get_db() as db:
        cursor = await db.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
        row = await cursor.fetchone()
        return row["id"] if row else None


# ==================== USERS ====================

async def create_user(telegram_id: int, username: Optional[str] = None,
                      full_name: Optional[str] = None, language: str = "uz") -> dict:
    referral_code = secrets.token_urlsafe(6)
    async with get_db() as db:
        await db.execute("""
            INSERT OR IGNORE INTO users (telegram_id, username, full_name, language, referral_code)
            VALUES (?, ?, ?, ?, ?)
        """, (telegram_id, username, full_name, language, referral_code))
        await db.commit()
    return await get_user(telegram_id)


async def get_user(telegram_id: int) -> Optional[dict]:
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


get_user_by_telegram_id = get_user


async def update_language(telegram_id: int, language: str) -> None:
    async with get_db() as db:
        await db.execute("UPDATE users SET language = ? WHERE telegram_id = ?", (language, telegram_id))
        await db.commit()


async def set_onboarding_shown(telegram_id: int) -> None:
    async with get_db() as db:
        await db.execute("UPDATE users SET onboarding_shown = 1 WHERE telegram_id = ?", (telegram_id,))
        await db.commit()


async def update_user_phone(telegram_id: int, phone: str) -> None:
    async with get_db() as db:
        await db.execute("UPDATE users SET phone = ? WHERE telegram_id = ?", (phone, telegram_id))
        await db.commit()


async def increment_user_purchases(telegram_id: int, amount: int) -> None:
    async with get_db() as db:
        await db.execute("""
            UPDATE users SET total_purchases = total_purchases + 1,
                             total_spent = total_spent + ?
            WHERE telegram_id = ?
        """, (amount, telegram_id))
        await db.commit()


async def toggle_auto_renewal(telegram_id: int) -> bool:
    async with get_db() as db:
        cursor = await db.execute("SELECT auto_renewal_enabled FROM users WHERE telegram_id = ?", (telegram_id,))
        row = await cursor.fetchone()
        new_val = 0 if row and row["auto_renewal_enabled"] else 1
        await db.execute("UPDATE users SET auto_renewal_enabled = ? WHERE telegram_id = ?", (new_val, telegram_id))
        await db.commit()
        return bool(new_val)


async def get_users_count() -> int:
    async with get_db() as db:
        cursor = await db.execute("SELECT COUNT(*) as cnt FROM users")
        row = await cursor.fetchone()
        return row["cnt"] if row else 0


async def get_all_users(limit: int = 50, offset: int = 0) -> list[dict]:
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?", (limit, offset))
        return [dict(r) for r in await cursor.fetchall()]


async def get_user_by_referral_code(code: str) -> Optional[dict]:
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM users WHERE referral_code = ?", (code,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def set_user_referred_by(telegram_id: int, referrer_tid: int) -> None:
    async with get_db() as db:
        await db.execute("UPDATE users SET referred_by = ? WHERE telegram_id = ?", (referrer_tid, telegram_id))
        await db.execute("UPDATE users SET referral_count = referral_count + 1 WHERE telegram_id = ?", (referrer_tid,))
        await db.commit()


async def get_user_total_spent(telegram_id: int) -> int:
    user = await get_user(telegram_id)
    return user.get("total_spent", 0) if user else 0


async def get_all_user_telegram_ids() -> list[int]:
    async with get_db() as db:
        cursor = await db.execute("SELECT telegram_id FROM users")
        rows = await cursor.fetchall()
        return [r["telegram_id"] for r in rows]


async def get_user_count() -> int:
    return await get_users_count()


# ==================== CATEGORIES ====================

async def create_category(name_uz: str, name_ru: str, description_uz: str = None,
                          description_ru: str = None, video_keyword: str = None,
                          sort_order: int = 0, instruction_video_file_id: str = None) -> int:
    async with get_db() as db:
        cursor = await db.execute("""
            INSERT INTO categories (name_uz, name_ru, description_uz, description_ru,
                                    video_keyword, sort_order, instruction_video_file_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name_uz, name_ru, description_uz, description_ru, video_keyword, sort_order, instruction_video_file_id))
        await db.commit()
        return cursor.lastrowid


async def get_all_categories(only_active: bool = False) -> list[dict]:
    async with get_db() as db:
        q = "SELECT * FROM categories"
        if only_active:
            q += " WHERE is_active = 1"
        q += " ORDER BY sort_order, id"
        cursor = await db.execute(q)
        return [dict(r) for r in await cursor.fetchall()]


async def get_category_by_id(category_id: int) -> Optional[dict]:
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM categories WHERE id = ?", (category_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def update_category(category_id: int, **kwargs) -> None:
    allowed = {"name_uz", "name_ru", "description_uz", "description_ru",
               "instruction_video_file_id", "video_keyword", "is_active", "sort_order"}
    fields = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [category_id]
    async with get_db() as db:
        await db.execute(f"UPDATE categories SET {set_clause} WHERE id = ?", values)
        await db.commit()


async def delete_category(category_id: int) -> None:
    async with get_db() as db:
        await db.execute("DELETE FROM categories WHERE id = ?", (category_id,))
        await db.commit()


async def get_category_by_video_keyword(keyword: str) -> Optional[dict]:
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM categories WHERE video_keyword = ?", (keyword,))
        row = await cursor.fetchone()
        return dict(row) if row else None


# ==================== PRODUCTS ====================

async def create_product(name_uz: str, name_ru: str, price: int, cost_price: int = 0,
                         category_id: int = None, description_uz: str = None, description_ru: str = None,
                         duration_text_uz: str = None, duration_text_ru: str = None,
                         video_keyword: str = None, has_warranty: bool = False,
                         warranty_days: int = 0, sort_order: int = 0,
                         instruction_video_file_id: str = None) -> int:
    async with get_db() as db:
        cursor = await db.execute("""
            INSERT INTO products (category_id, name_uz, name_ru, description_uz, description_ru,
                                  duration_text_uz, duration_text_ru, price, cost_price,
                                  video_keyword, has_warranty, warranty_days, sort_order,
                                  instruction_video_file_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (category_id, name_uz, name_ru, description_uz, description_ru,
              duration_text_uz, duration_text_ru, price, cost_price,
              video_keyword, int(has_warranty), warranty_days, sort_order,
              instruction_video_file_id))
        await db.commit()
        return cursor.lastrowid


async def get_all_products(only_active: bool = False) -> list[dict]:
    async with get_db() as db:
        q = """SELECT p.*,
               (SELECT COUNT(*) FROM accounts a WHERE a.product_id = p.id AND a.status = 'available') AS stock
               FROM products p"""
        if only_active:
            q += " WHERE p.is_active = 1"
        q += " ORDER BY p.sort_order, p.id"
        cursor = await db.execute(q)
        return [dict(r) for r in await cursor.fetchall()]


async def get_products_by_category(category_id: int, only_active: bool = False) -> list[dict]:
    async with get_db() as db:
        q = """SELECT p.*,
               (SELECT COUNT(*) FROM accounts a WHERE a.product_id = p.id AND a.status = 'available') AS stock
               FROM products p WHERE p.category_id = ?"""
        if only_active:
            q += " AND p.is_active = 1"
        q += " ORDER BY p.sort_order, p.id"
        cursor = await db.execute(q, (category_id,))
        return [dict(r) for r in await cursor.fetchall()]


async def get_product_by_id(product_id: int) -> Optional[dict]:
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def update_product(product_id: int, **kwargs) -> None:
    allowed = {"category_id", "name_uz", "name_ru", "description_uz", "description_ru",
               "duration_text_uz", "duration_text_ru", "price", "cost_price",
               "instruction_video_file_id", "video_keyword", "has_warranty",
               "warranty_days", "is_active", "sort_order"}
    fields = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [product_id]
    async with get_db() as db:
        await db.execute(f"UPDATE products SET {set_clause} WHERE id = ?", values)
        await db.commit()


async def delete_product(product_id: int) -> None:
    async with get_db() as db:
        await db.execute("DELETE FROM products WHERE id = ?", (product_id,))
        await db.commit()


async def get_product_stock(product_id: int) -> int:
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT COUNT(*) as cnt FROM accounts WHERE product_id = ? AND status = 'available'",
            (product_id,))
        row = await cursor.fetchone()
        return row["cnt"] if row else 0


async def get_product_by_video_keyword(keyword: str) -> Optional[dict]:
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM products WHERE video_keyword = ?", (keyword,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def increment_purchase_count(product_id: int) -> None:
    async with get_db() as db:
        await db.execute("UPDATE products SET purchase_count = purchase_count + 1 WHERE id = ?", (product_id,))
        await db.commit()


async def get_all_products_flat() -> list[dict]:
    """Barcha mahsulotlar — admin UI uchun"""
    return await get_all_products()


# ==================== ACCOUNTS ====================

async def create_account(
    product_id: int,
    duration_days: int = 30,
    login: str = None,
    password: str = None,
    additional_data: str = None,
    supplier: str = None,
) -> dict:
    """FIX 2: expiry_date avtomatik hisoblanadi duration_days dan."""
    today = date.today()
    if duration_days and duration_days > 0:
        expiry = today + timedelta(days=duration_days)
        expiry_str = expiry.isoformat()
        remaining = duration_days
        status = "available"
    else:
        expiry_str = None
        remaining = 9999
        status = "available"

    async with get_db() as db:
        cursor = await db.execute("""
            INSERT INTO accounts (product_id, login, password, expiry_date, remaining_days,
                                  supplier, additional_data, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (product_id, login or None, password or None, expiry_str, remaining,
              supplier or None, additional_data or None, status))
        await db.commit()
        return {"id": cursor.lastrowid, "remaining_days": remaining, "status": status}


async def bulk_create_accounts(product_id: int, lines: list[str],
                                duration_days: int = 30) -> dict:
    """FIX 3: pipe format — login|parol. Bitta qiymat = invite link.
       FIX 2: expiry_date duration_days dan avtomatik."""
    added = 0
    errors = []
    today = date.today()

    if duration_days and duration_days > 0:
        expiry_str = (today + timedelta(days=duration_days)).isoformat()
        remaining = duration_days
    else:
        expiry_str = None
        remaining = 9999

    async with get_db() as db:
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            login_val = None
            pwd_val = None
            invite_val = None
            if "|" in line:
                parts = line.split("|", 2)
                login_val = parts[0].strip() or None
                pwd_val = parts[1].strip() if len(parts) > 1 else None
                pwd_val = pwd_val or None
                invite_val = parts[2].strip() if len(parts) > 2 else None
                invite_val = invite_val or None
            else:
                # Pipe yo'q — invite link deb qabul qilinadi
                invite_val = line.strip()
            try:
                await db.execute("""
                    INSERT INTO accounts (product_id, login, password, additional_data,
                                          expiry_date, remaining_days, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (product_id, login_val, pwd_val, invite_val,
                      expiry_str, remaining, "available"))
                added += 1
            except Exception as e:
                errors.append(f"Qator {i}: DB xato — {e}")
        await db.commit()
    return {"added": added, "errors": errors}


async def get_accounts_by_product(product_id: int, status: str = "available") -> list[dict]:
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM accounts WHERE product_id = ? AND status = ? ORDER BY expiry_date ASC",
            (product_id, status))
        return [dict(r) for r in await cursor.fetchall()]


async def get_account_by_id(account_id: int) -> Optional[dict]:
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM accounts WHERE id = ?", (account_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def sell_account(product_id: int, order_id: int, user_telegram_id: int) -> Optional[dict]:
    """Pick oldest available account for product, mark sold. Returns account dict or None."""
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT * FROM accounts
            WHERE product_id = ? AND status = 'available'
            ORDER BY expiry_date ASC LIMIT 1
        """, (product_id,))
        row = await cursor.fetchone()
        if not row:
            return None
        acc = dict(row)
        await db.execute("""
            UPDATE accounts SET status = 'sold', sold_to_user_id = ?,
                   sold_at = CURRENT_TIMESTAMP, sold_via = 'bot_order'
            WHERE id = ?
        """, (user_telegram_id, acc["id"]))
        await db.commit()
        return acc


async def reserve_accounts(product_id: int, quantity: int, order_id: int) -> list[dict]:
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT * FROM accounts
            WHERE product_id = ? AND status = 'available'
            ORDER BY expiry_date ASC LIMIT ?
        """, (product_id, quantity))
        rows = await cursor.fetchall()
        reserved = []
        for row in rows:
            acc = dict(row)
            await db.execute("""
                UPDATE accounts SET status = 'reserved', reserved_for_order_id = ?,
                       reserved_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (order_id, acc["id"]))
            reserved.append(acc)
        await db.commit()
        return reserved


async def release_reserved(order_id: int) -> None:
    async with get_db() as db:
        await db.execute("""
            UPDATE accounts SET status = 'available', reserved_for_order_id = NULL, reserved_at = NULL
            WHERE reserved_for_order_id = ? AND status = 'reserved'
        """, (order_id,))
        await db.commit()


async def confirm_reserved(order_id: int, user_telegram_id: int) -> list[dict]:
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT * FROM accounts WHERE reserved_for_order_id = ? AND status = 'reserved'
        """, (order_id,))
        rows = await cursor.fetchall()
        result = []
        for row in rows:
            acc = dict(row)
            await db.execute("""
                UPDATE accounts SET status = 'sold', sold_to_user_id = ?,
                       sold_at = CURRENT_TIMESTAMP, sold_via = 'bot_order'
                WHERE id = ?
            """, (user_telegram_id, acc["id"]))
            # Update order_items
            await db.execute("""
                UPDATE order_items SET account_id = ?, status = 'delivered',
                       delivered_at = CURRENT_TIMESTAMP, expiry_date = ?
                WHERE order_id = ? AND product_id = ? AND account_id IS NULL
                LIMIT 1
            """, (acc["id"], acc["expiry_date"], order_id, acc["product_id"]))
            result.append(acc)
        await db.commit()
        return result


async def update_remaining_days() -> int:
    today = date.today()
    updated = 0
    async with get_db() as db:
        cursor = await db.execute("SELECT id, expiry_date FROM accounts WHERE status = 'available'")
        rows = await cursor.fetchall()
        for row in rows:
            if not row["expiry_date"]:
                continue
            exp = date.fromisoformat(row["expiry_date"])
            remaining = (exp - today).days
            if remaining <= 0:
                await db.execute(
                    "UPDATE accounts SET remaining_days = 0, status = 'expired' WHERE id = ?",
                    (row["id"],))
            else:
                await db.execute(
                    "UPDATE accounts SET remaining_days = ? WHERE id = ?",
                    (remaining, row["id"]))
            updated += 1
        await db.commit()
    return updated


async def generate_direct_sale_token(account_id: int) -> str:
    token = secrets.token_urlsafe(8)
    async with get_db() as db:
        await db.execute("UPDATE accounts SET direct_sale_token = ? WHERE id = ?", (token, account_id))
        await db.commit()
    return token


async def get_account_by_direct_sale_token(token: str) -> Optional[dict]:
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM accounts WHERE direct_sale_token = ?", (token,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_all_accounts(product_id: int = None, status: str = None,
                           limit: int = 50, offset: int = 0) -> list[dict]:
    async with get_db() as db:
        q = "SELECT a.*, p.name_uz, p.name_ru FROM accounts a JOIN products p ON p.id = a.product_id WHERE 1=1"
        params = []
        if product_id:
            q += " AND a.product_id = ?"
            params.append(product_id)
        if status:
            q += " AND a.status = ?"
            params.append(status)
        q += " ORDER BY a.created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        cursor = await db.execute(q, params)
        return [dict(r) for r in await cursor.fetchall()]


async def update_account(account_id: int, **kwargs) -> None:
    allowed = {"login", "password", "additional_data", "supplier", "expiry_date",
               "status", "sold_to_user_id", "sold_via"}
    fields = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [account_id]
    async with get_db() as db:
        await db.execute(f"UPDATE accounts SET {set_clause} WHERE id = ?", values)
        await db.commit()
