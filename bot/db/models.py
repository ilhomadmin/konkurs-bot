"""
CRUD operatsiyalar — barcha jadvallar uchun
"""
import secrets
from datetime import date
from typing import Optional
import aiosqlite

from bot.db.database import get_db
from bot.utils.duration import days_to_tier


# ==================== USERS ====================

async def create_user(
    telegram_id: int,
    username: Optional[str],
    full_name: Optional[str],
    language: str = "uz"
) -> dict:
    """Yangi foydalanuvchi yaratadi yoki mavjudini qaytaradi"""
    referral_code = secrets.token_urlsafe(6)
    async with get_db() as db:
        await db.execute("""
            INSERT OR IGNORE INTO users (telegram_id, username, full_name, language, referral_code)
            VALUES (?, ?, ?, ?, ?)
        """, (telegram_id, username, full_name, language, referral_code))
        await db.commit()
        return await get_user(telegram_id)


async def get_user(telegram_id: int) -> Optional[dict]:
    """Foydalanuvchini telegram_id bo'yicha topadi"""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def update_language(telegram_id: int, language: str) -> None:
    """Foydalanuvchi tilini yangilaydi"""
    async with get_db() as db:
        await db.execute(
            "UPDATE users SET language = ? WHERE telegram_id = ?",
            (language, telegram_id)
        )
        await db.commit()


async def set_onboarding_shown(telegram_id: int) -> None:
    """Onboarding ko'rsatilganini belgilaydi"""
    async with get_db() as db:
        await db.execute(
            "UPDATE users SET onboarding_shown = 1 WHERE telegram_id = ?",
            (telegram_id,)
        )
        await db.commit()


# ==================== CATEGORIES ====================

async def create_category(
    name_uz: str,
    name_ru: str,
    description_uz: Optional[str] = None,
    description_ru: Optional[str] = None,
    instruction_video_file_id: Optional[str] = None,
    sort_order: int = 0
) -> int:
    """Yangi kategoriya yaratadi, ID qaytaradi"""
    async with get_db() as db:
        cursor = await db.execute("""
            INSERT INTO categories (name_uz, name_ru, description_uz, description_ru, instruction_video_file_id, sort_order)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name_uz, name_ru, description_uz, description_ru, instruction_video_file_id, sort_order))
        await db.commit()
        return cursor.lastrowid


async def get_all_categories(only_active: bool = False) -> list[dict]:
    """Barcha kategoriyalarni qaytaradi"""
    async with get_db() as db:
        if only_active:
            cursor = await db.execute(
                "SELECT * FROM categories WHERE is_active = 1 ORDER BY sort_order, id"
            )
        else:
            cursor = await db.execute(
                "SELECT * FROM categories ORDER BY sort_order, id"
            )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_category_by_id(category_id: int) -> Optional[dict]:
    """Kategoriyani ID bo'yicha topadi"""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM categories WHERE id = ?", (category_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def update_category(category_id: int, **kwargs) -> None:
    """Kategoriya ma'lumotlarini yangilaydi"""
    allowed = {"name_uz", "name_ru", "description_uz", "description_ru",
               "instruction_video_file_id", "is_active", "sort_order"}
    fields = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [category_id]
    async with get_db() as db:
        await db.execute(
            f"UPDATE categories SET {set_clause} WHERE id = ?", values
        )
        await db.commit()


async def delete_category(category_id: int) -> None:
    """Kategoriyani o'chiradi"""
    async with get_db() as db:
        await db.execute("DELETE FROM categories WHERE id = ?", (category_id,))
        await db.commit()


# ==================== PRODUCTS ====================

async def create_product(
    category_id: int,
    name_uz: str,
    name_ru: str,
    description_uz: Optional[str] = None,
    description_ru: Optional[str] = None,
    instruction_video_file_id: Optional[str] = None,
    has_warranty: bool = False,
    warranty_days: int = 0,
    sort_order: int = 0
) -> int:
    """Yangi mahsulot yaratadi, ID qaytaradi"""
    async with get_db() as db:
        cursor = await db.execute("""
            INSERT INTO products
                (category_id, name_uz, name_ru, description_uz, description_ru,
                 instruction_video_file_id, has_warranty, warranty_days, sort_order)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (category_id, name_uz, name_ru, description_uz, description_ru,
              instruction_video_file_id, int(has_warranty), warranty_days, sort_order))
        await db.commit()
        return cursor.lastrowid


async def get_all_products(only_active: bool = False) -> list[dict]:
    """Barcha mahsulotlarni qaytaradi"""
    async with get_db() as db:
        if only_active:
            cursor = await db.execute(
                "SELECT * FROM products WHERE is_active = 1 ORDER BY sort_order, id"
            )
        else:
            cursor = await db.execute(
                "SELECT * FROM products ORDER BY sort_order, id"
            )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_products_by_category(category_id: int, only_active: bool = False) -> list[dict]:
    """Kategoriya bo'yicha mahsulotlarni qaytaradi"""
    async with get_db() as db:
        if only_active:
            cursor = await db.execute(
                "SELECT * FROM products WHERE category_id = ? AND is_active = 1 ORDER BY sort_order, id",
                (category_id,)
            )
        else:
            cursor = await db.execute(
                "SELECT * FROM products WHERE category_id = ? ORDER BY sort_order, id",
                (category_id,)
            )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_product_by_id(product_id: int) -> Optional[dict]:
    """Mahsulotni ID bo'yicha topadi"""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM products WHERE id = ?", (product_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def update_product(product_id: int, **kwargs) -> None:
    """Mahsulot ma'lumotlarini yangilaydi"""
    allowed = {"category_id", "name_uz", "name_ru", "description_uz", "description_ru",
               "instruction_video_file_id", "has_warranty", "warranty_days",
               "is_active", "sort_order"}
    fields = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [product_id]
    async with get_db() as db:
        await db.execute(
            f"UPDATE products SET {set_clause} WHERE id = ?", values
        )
        await db.commit()


async def delete_product(product_id: int) -> None:
    """Mahsulotni o'chiradi"""
    async with get_db() as db:
        await db.execute("DELETE FROM products WHERE id = ?", (product_id,))
        await db.commit()


# ==================== PRODUCT PRICES ====================

async def create_product_price(
    product_id: int,
    duration_tier: str,
    display_name_uz: str,
    display_name_ru: str,
    min_days: int,
    max_days: int,
    price: int,
    cost_price: int = 0
) -> int:
    """Mahsulot uchun narx tier yaratadi"""
    async with get_db() as db:
        cursor = await db.execute("""
            INSERT INTO product_prices
                (product_id, duration_tier, display_name_uz, display_name_ru,
                 min_days, max_days, price, cost_price)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (product_id, duration_tier, display_name_uz, display_name_ru,
              min_days, max_days, price, cost_price))
        await db.commit()
        return cursor.lastrowid


async def get_prices_by_product(product_id: int) -> list[dict]:
    """Mahsulotga tegishli barcha narx tierlarini qaytaradi"""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM product_prices WHERE product_id = ? AND is_active = 1",
            (product_id,)
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def update_product_price(price_id: int, **kwargs) -> None:
    """Narx tier ma'lumotlarini yangilaydi"""
    allowed = {"duration_tier", "display_name_uz", "display_name_ru",
               "min_days", "max_days", "price", "cost_price", "is_active"}
    fields = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [price_id]
    async with get_db() as db:
        await db.execute(
            f"UPDATE product_prices SET {set_clause} WHERE id = ?", values
        )
        await db.commit()


async def delete_product_price(price_id: int) -> None:
    """Narx tierni o'chiradi"""
    async with get_db() as db:
        await db.execute("DELETE FROM product_prices WHERE id = ?", (price_id,))
        await db.commit()


# ==================== ACCOUNTS ====================

async def create_account(
    product_id: int,
    login: str,
    password: str,
    expiry_date: str,
    supplier: Optional[str] = None,
    additional_data: Optional[str] = None
) -> dict:
    """
    Bitta akkaunt qo'shadi.
    expiry_date: 'YYYY-MM-DD' formatida
    Avtomatik remaining_days va duration_tier hisoblanadi.
    """
    today = date.today()
    exp = date.fromisoformat(expiry_date)
    remaining = (exp - today).days
    tier = days_to_tier(remaining) if remaining > 0 else None
    status = "available" if remaining > 0 else "expired"

    async with get_db() as db:
        cursor = await db.execute("""
            INSERT INTO accounts
                (product_id, login, password, expiry_date, remaining_days,
                 duration_tier, supplier, additional_data, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (product_id, login, password, expiry_date, remaining,
              tier, supplier, additional_data, status))
        await db.commit()
        return {
            "id": cursor.lastrowid,
            "remaining_days": remaining,
            "duration_tier": tier,
            "status": status
        }


async def bulk_create_accounts(
    product_id: int,
    lines: list[str]
) -> dict:
    """
    Bir nechta akkauntlarni qo'shadi.
    Format: login:parol:YYYY-MM-DD  yoki  login:parol:YYYY-MM-DD:supplier
    Qaytaradi: {added: int, errors: list, tier_stats: dict}
    """
    added = 0
    errors = []
    tier_stats: dict[str, int] = {}

    today = date.today()

    async with get_db() as db:
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            parts = line.split(":")
            if len(parts) < 3:
                errors.append(f"Qator {i}: noto'g'ri format — '{line}'")
                continue

            login = parts[0].strip()
            password = parts[1].strip()
            expiry_str = parts[2].strip()
            supplier = parts[3].strip() if len(parts) > 3 else None

            try:
                exp = date.fromisoformat(expiry_str)
            except ValueError:
                errors.append(f"Qator {i}: noto'g'ri sana — '{expiry_str}'")
                continue

            remaining = (exp - today).days
            tier = days_to_tier(remaining) if remaining > 0 else None
            status = "available" if remaining > 0 else "expired"

            try:
                await db.execute("""
                    INSERT INTO accounts
                        (product_id, login, password, expiry_date, remaining_days,
                         duration_tier, supplier, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (product_id, login, password, expiry_str, remaining,
                      tier, supplier, status))
                added += 1
                if tier:
                    tier_stats[tier] = tier_stats.get(tier, 0) + 1
            except Exception as e:
                errors.append(f"Qator {i}: DB xato — {e}")

        await db.commit()

    return {"added": added, "errors": errors, "tier_stats": tier_stats}


async def get_accounts_by_product_and_tier(
    product_id: int,
    duration_tier: str,
    status: str = "available"
) -> list[dict]:
    """Mahsulot va tier bo'yicha akkauntlarni qaytaradi"""
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT * FROM accounts
            WHERE product_id = ? AND duration_tier = ? AND status = ?
            ORDER BY expiry_date ASC
        """, (product_id, duration_tier, status))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_available_count(product_id: int, duration_tier: Optional[str] = None) -> dict:
    """
    Mahsulot uchun mavjud akkauntlar sonini qaytaradi.
    Agar tier berilmasa, barcha tierlar bo'yicha hisoblanadi.
    """
    async with get_db() as db:
        if duration_tier:
            cursor = await db.execute("""
                SELECT status, COUNT(*) as cnt
                FROM accounts
                WHERE product_id = ? AND duration_tier = ?
                GROUP BY status
            """, (product_id, duration_tier))
        else:
            cursor = await db.execute("""
                SELECT status, COUNT(*) as cnt
                FROM accounts
                WHERE product_id = ?
                GROUP BY status
            """, (product_id,))

        rows = await cursor.fetchall()
        result = {r["status"]: r["cnt"] for r in rows}

        # Tier bo'yicha mavjud sonlar
        cursor2 = await db.execute("""
            SELECT duration_tier, COUNT(*) as cnt
            FROM accounts
            WHERE product_id = ? AND status = 'available'
            GROUP BY duration_tier
        """, (product_id,))
        tier_rows = await cursor2.fetchall()
        result["by_tier"] = {r["duration_tier"]: r["cnt"] for r in tier_rows}

        return result


async def update_remaining_days() -> int:
    """
    Barcha available akkauntlar uchun remaining_days va tier yangilaydi.
    Muddati o'tganlarni expired qiladi.
    Yangilangan akkauntlar sonini qaytaradi.
    """
    today = date.today()
    updated = 0

    async with get_db() as db:
        cursor = await db.execute("""
            SELECT id, expiry_date FROM accounts
            WHERE status = 'available'
        """)
        rows = await cursor.fetchall()

        for row in rows:
            exp = date.fromisoformat(row["expiry_date"])
            remaining = (exp - today).days

            if remaining <= 0:
                await db.execute(
                    "UPDATE accounts SET remaining_days = 0, status = 'expired', duration_tier = NULL WHERE id = ?",
                    (row["id"],)
                )
            else:
                tier = days_to_tier(remaining)
                await db.execute(
                    "UPDATE accounts SET remaining_days = ?, duration_tier = ? WHERE id = ?",
                    (remaining, tier, row["id"])
                )
            updated += 1

        await db.commit()

    return updated


# ==================== ADMIN ROLES ====================

async def create_admin_role(
    telegram_id: int,
    role: str = "operator",
    username: Optional[str] = None,
    full_name: Optional[str] = None
) -> int:
    """Yangi admin qo'shadi"""
    async with get_db() as db:
        cursor = await db.execute("""
            INSERT OR REPLACE INTO admin_roles (telegram_id, role, username, full_name)
            VALUES (?, ?, ?, ?)
        """, (telegram_id, role, username, full_name))
        await db.commit()
        return cursor.lastrowid


async def get_admin_by_telegram_id(telegram_id: int) -> Optional[dict]:
    """Adminni telegram_id bo'yicha topadi"""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM admin_roles WHERE telegram_id = ? AND is_active = 1",
            (telegram_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_all_admins() -> list[dict]:
    """Barcha adminlarni qaytaradi"""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM admin_roles ORDER BY created_at"
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def update_admin_role(telegram_id: int, role: str) -> None:
    """Admin rolini yangilaydi"""
    async with get_db() as db:
        await db.execute(
            "UPDATE admin_roles SET role = ? WHERE telegram_id = ?",
            (role, telegram_id)
        )
        await db.commit()


async def delete_admin_role(telegram_id: int) -> None:
    """Adminni o'chiradi (deactivate qiladi)"""
    async with get_db() as db:
        await db.execute(
            "UPDATE admin_roles SET is_active = 0 WHERE telegram_id = ?",
            (telegram_id,)
        )
        await db.commit()
