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


# ==================== CART ITEMS ====================

async def cart_get(user_id: int) -> list[dict]:
    """Foydalanuvchi savatini qaytaradi (product ma'lumotlari bilan). user_id = telegram_id"""
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT ci.*, p.name_uz, p.name_ru, pp.price, pp.cost_price
            FROM cart_items ci
            JOIN users u ON u.id = ci.user_id
            JOIN products p ON p.id = ci.product_id
            JOIN product_prices pp ON pp.product_id = ci.product_id
                AND pp.duration_tier = ci.duration_tier AND pp.is_active = 1
            WHERE u.telegram_id = ?
            ORDER BY ci.added_at
        """, (user_id,))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def cart_add(user_id: int, product_id: int, duration_tier: str, quantity: int = 1) -> None:
    """Savatga mahsulot qo'shadi yoki miqdorini oshiradi"""
    async with get_db() as db:
        # Avval users.id ni topish
        cursor = await db.execute("SELECT id FROM users WHERE telegram_id = ?", (user_id,))
        row = await cursor.fetchone()
        if not row:
            return
        db_user_id = row["id"]

        existing = await db.execute(
            "SELECT id, quantity FROM cart_items WHERE user_id = ? AND product_id = ? AND duration_tier = ?",
            (db_user_id, product_id, duration_tier)
        )
        ex_row = await existing.fetchone()
        if ex_row:
            await db.execute(
                "UPDATE cart_items SET quantity = ? WHERE id = ?",
                (ex_row["quantity"] + quantity, ex_row["id"])
            )
        else:
            await db.execute(
                "INSERT INTO cart_items (user_id, product_id, duration_tier, quantity) VALUES (?, ?, ?, ?)",
                (db_user_id, product_id, duration_tier, quantity)
            )
        await db.commit()


async def cart_update_qty(user_id: int, product_id: int, duration_tier: str, quantity: int) -> None:
    """Savat elementining miqdorini yangilaydi (0 bo'lsa o'chiradi)"""
    async with get_db() as db:
        cursor = await db.execute("SELECT id FROM users WHERE telegram_id = ?", (user_id,))
        row = await cursor.fetchone()
        if not row:
            return
        db_user_id = row["id"]

        if quantity <= 0:
            await db.execute(
                "DELETE FROM cart_items WHERE user_id = ? AND product_id = ? AND duration_tier = ?",
                (db_user_id, product_id, duration_tier)
            )
        else:
            await db.execute(
                "UPDATE cart_items SET quantity = ? WHERE user_id = ? AND product_id = ? AND duration_tier = ?",
                (quantity, db_user_id, product_id, duration_tier)
            )
        await db.commit()


async def cart_remove_item(cart_item_id: int) -> None:
    """Savat elementini ID bo'yicha o'chiradi"""
    async with get_db() as db:
        await db.execute("DELETE FROM cart_items WHERE id = ?", (cart_item_id,))
        await db.commit()


async def cart_clear(user_id: int) -> None:
    """Foydalanuvchi savatini tozalaydi"""
    async with get_db() as db:
        cursor = await db.execute("SELECT id FROM users WHERE telegram_id = ?", (user_id,))
        row = await cursor.fetchone()
        if not row:
            return
        await db.execute("DELETE FROM cart_items WHERE user_id = ?", (row["id"],))
        await db.commit()


async def cart_item_in_cart(user_id: int, product_id: int, duration_tier: str) -> Optional[dict]:
    """Savatda bu mahsulot/tier borligini tekshiradi"""
    async with get_db() as db:
        cursor = await db.execute("SELECT id FROM users WHERE telegram_id = ?", (user_id,))
        row = await cursor.fetchone()
        if not row:
            return None
        db_user_id = row["id"]
        cursor2 = await db.execute(
            "SELECT * FROM cart_items WHERE user_id = ? AND product_id = ? AND duration_tier = ?",
            (db_user_id, product_id, duration_tier)
        )
        r = await cursor2.fetchone()
        return dict(r) if r else None


# ==================== PROMO CODES ====================

async def get_promo_by_code(code: str) -> Optional[dict]:
    """Promo kodni topadi"""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM promo_codes WHERE code = ? AND is_active = 1",
            (code.upper().strip(),)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def increment_promo_usage(promo_id: int) -> None:
    """Promo kod foydalanish sonini oshiradi"""
    async with get_db() as db:
        await db.execute(
            "UPDATE promo_codes SET used_count = used_count + 1 WHERE id = ?",
            (promo_id,)
        )
        await db.commit()


# ==================== VIP LEVELS ====================

async def get_vip_level(level: str) -> Optional[dict]:
    """VIP daraja ma'lumotini qaytaradi"""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM vip_levels WHERE level = ?", (level,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_all_vip_levels() -> list[dict]:
    """Barcha VIP darajalarni qaytaradi"""
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM vip_levels ORDER BY min_purchases")
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def update_user_vip(telegram_id: int) -> str:
    """
    Foydalanuvchi xarid soniga qarab VIP darajasini yangilaydi.
    Yangi darajani qaytaradi.
    """
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


# ==================== ORDERS ====================

async def create_order(
    user_telegram_id: int,
    total_amount: int,
    discount_amount: int = 0,
    promo_code_id: Optional[int] = None
) -> int:
    """Yangi buyurtma yaratadi, order_id qaytaradi"""
    async with get_db() as db:
        cursor_u = await db.execute("SELECT id FROM users WHERE telegram_id = ?", (user_telegram_id,))
        u_row = await cursor_u.fetchone()
        if not u_row:
            raise ValueError("Foydalanuvchi topilmadi")
        db_user_id = u_row["id"]

        cursor = await db.execute("""
            INSERT INTO orders (user_id, total_amount, discount_amount, promo_code_id, status)
            VALUES (?, ?, ?, ?, 'pending_payment')
        """, (db_user_id, total_amount, discount_amount, promo_code_id))
        await db.commit()
        return cursor.lastrowid


async def get_order(order_id: int) -> Optional[dict]:
    """Buyurtmani ID bo'yicha topadi (user telegram_id bilan)"""
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


async def get_user_orders(telegram_id: int, limit: int = 20, offset: int = 0) -> list[dict]:
    """Foydalanuvchi buyurtmalarini qaytaradi"""
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT o.* FROM orders o
            JOIN users u ON u.id = o.user_id
            WHERE u.telegram_id = ?
            ORDER BY o.created_at DESC
            LIMIT ? OFFSET ?
        """, (telegram_id, limit, offset))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_user_active_order(telegram_id: int) -> Optional[dict]:
    """Foydalanuvchining joriy aktiv buyurtmasini topadi"""
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
    """Buyurtma statusini yangilaydi"""
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
    """Progress bar message_id ni saqlaydi"""
    async with get_db() as db:
        await db.execute(
            "UPDATE orders SET progress_message_id = ? WHERE id = ?",
            (message_id, order_id)
        )
        await db.commit()


async def count_user_orders(telegram_id: int) -> int:
    """Foydalanuvchi buyurtmalari sonini qaytaradi"""
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT COUNT(*) as cnt FROM orders o
            JOIN users u ON u.id = o.user_id
            WHERE u.telegram_id = ?
        """, (telegram_id,))
        row = await cursor.fetchone()
        return row["cnt"] if row else 0


# ==================== ORDER ITEMS ====================

async def create_order_item(
    order_id: int,
    product_id: int,
    quantity: int,
    duration_tier: str,
    unit_price: int,
    cost_price: int = 0
) -> int:
    """Buyurtma elementi yaratadi"""
    async with get_db() as db:
        cursor = await db.execute("""
            INSERT INTO order_items
                (order_id, product_id, quantity, duration_tier, unit_price, cost_price, status)
            VALUES (?, ?, ?, ?, ?, ?, 'pending')
        """, (order_id, product_id, quantity, duration_tier, unit_price, cost_price))
        await db.commit()
        return cursor.lastrowid


async def get_order_items(order_id: int) -> list[dict]:
    """Buyurtma elementlarini qaytaradi (akkaunt + mahsulot ma'lumotlari bilan)"""
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT oi.*, p.name_uz, p.name_ru,
                   p.instruction_video_file_id as product_video,
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
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def update_order_item(item_id: int, **kwargs) -> None:
    """Buyurtma elementini yangilaydi"""
    allowed = {"account_id", "status", "delivered_at", "expiry_date"}
    fields = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [item_id]
    async with get_db() as db:
        await db.execute(
            f"UPDATE order_items SET {set_clause} WHERE id = ?", values
        )
        await db.commit()


# ==================== ACCOUNTS: REZERV + SOTISH ====================

async def reserve_accounts_for_order(
    order_id: int,
    product_id: int,
    duration_tier: str,
    quantity: int
) -> list[dict]:
    """
    Buyurtma uchun eng kam remaining_days bo'lgan akkauntlarni band qiladi.
    Yetarli bo'lmasa bo'sh list qaytaradi.
    """
    async with get_db() as db:
        # Mavjud akkauntlarni tekshirish
        cursor = await db.execute("""
            SELECT id, login, password, expiry_date, remaining_days FROM accounts
            WHERE product_id = ? AND duration_tier = ? AND status = 'available'
            ORDER BY remaining_days ASC
            LIMIT ?
        """, (product_id, duration_tier, quantity))
        rows = await cursor.fetchall()

        if len(rows) < quantity:
            return []

        reserved = []
        for row in rows:
            await db.execute("""
                UPDATE accounts
                SET status = 'reserved',
                    reserved_for_order_id = ?,
                    reserved_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (order_id, row["id"]))
            reserved.append(dict(row))

        await db.commit()
        return reserved


async def release_reserved_accounts(order_id: int) -> None:
    """Band qilingan akkauntlarni ozod qiladi (timeout yoki bekor qilish)"""
    async with get_db() as db:
        await db.execute("""
            UPDATE accounts
            SET status = 'available',
                reserved_for_order_id = NULL,
                reserved_at = NULL
            WHERE reserved_for_order_id = ? AND status = 'reserved'
        """, (order_id,))
        await db.commit()


async def sell_account(
    account_id: int,
    user_telegram_id: int,
    sold_via: str = "bot_order"
) -> None:
    """Akkauntni sotilgan deb belgilaydi"""
    async with get_db() as db:
        await db.execute("""
            UPDATE accounts
            SET status = 'sold',
                sold_to_user_id = ?,
                sold_at = CURRENT_TIMESTAMP,
                sold_via = ?
            WHERE id = ?
        """, (user_telegram_id, sold_via, account_id))
        await db.commit()


async def get_reserved_accounts_for_order(order_id: int) -> list[dict]:
    """Buyurtma uchun band qilingan akkauntlarni qaytaradi"""
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT a.*, p.name_uz, p.name_ru,
                   p.instruction_video_file_id as product_video,
                   p.category_id
            FROM accounts a
            JOIN products p ON p.id = a.product_id
            WHERE a.reserved_for_order_id = ? AND a.status = 'reserved'
            ORDER BY a.remaining_days ASC
        """, (order_id,))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_direct_sale_account(token: str) -> Optional[dict]:
    """Direct sale token bo'yicha akkauntni topadi"""
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT a.*, p.name_uz, p.name_ru,
                   p.instruction_video_file_id as product_video,
                   p.category_id,
                   c.instruction_video_file_id as category_video
            FROM accounts a
            JOIN products p ON p.id = a.product_id
            LEFT JOIN categories c ON c.id = p.category_id
            WHERE a.direct_sale_token = ? AND a.status = 'available'
        """, (token,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_next_available_account(product_id: int, duration_tier: str) -> Optional[dict]:
    """Shu product+tier dagi birinchi available akkauntni qaytaradi"""
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT * FROM accounts
            WHERE product_id = ? AND duration_tier = ? AND status = 'available'
            ORDER BY remaining_days ASC
            LIMIT 1
        """, (product_id, duration_tier))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def set_direct_sale_token(account_id: int, token: str) -> None:
    """Akkauntga direct sale token o'rnatadi"""
    async with get_db() as db:
        await db.execute(
            "UPDATE accounts SET direct_sale_token = ? WHERE id = ?",
            (token, account_id)
        )
        await db.commit()


# ==================== PRODUCTS: PURCHASE COUNT ====================

async def increment_purchase_count(product_id: int, qty: int = 1) -> None:
    """Mahsulot xarid sonini oshiradi"""
    async with get_db() as db:
        await db.execute(
            "UPDATE products SET purchase_count = purchase_count + ? WHERE id = ?",
            (qty, product_id)
        )
        await db.commit()


async def update_user_stats(telegram_id: int, amount: int, qty: int = 1) -> None:
    """Foydalanuvchi umumiy xarid/summasini yangilaydi"""
    async with get_db() as db:
        await db.execute("""
            UPDATE users
            SET total_purchases = total_purchases + ?,
                total_spent = total_spent + ?
            WHERE telegram_id = ?
        """, (qty, amount, telegram_id))
        await db.commit()


# ==================== REVIEWS ====================

async def get_product_rating(product_id: int) -> dict:
    """Mahsulot o'rtacha reytingi va sharhlar sonini qaytaradi"""
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


# ==================== FAVORITES ====================

async def add_favorite(user_telegram_id: int, product_id: int) -> None:
    """Sevimlilarga qo'shadi"""
    async with get_db() as db:
        cursor = await db.execute("SELECT id FROM users WHERE telegram_id = ?", (user_telegram_id,))
        row = await cursor.fetchone()
        if not row:
            return
        await db.execute(
            "INSERT OR IGNORE INTO favorites (user_id, product_id) VALUES (?, ?)",
            (row["id"], product_id)
        )
        await db.commit()


async def remove_favorite(user_telegram_id: int, product_id: int) -> None:
    """Sevimlilardan o'chiradi"""
    async with get_db() as db:
        cursor = await db.execute("SELECT id FROM users WHERE telegram_id = ?", (user_telegram_id,))
        row = await cursor.fetchone()
        if not row:
            return
        await db.execute(
            "DELETE FROM favorites WHERE user_id = ? AND product_id = ?",
            (row["id"], product_id)
        )
        await db.commit()


async def is_favorite(user_telegram_id: int, product_id: int) -> bool:
    """Mahsulot sevimlilar ro'yxatida borligini tekshiradi"""
    async with get_db() as db:
        cursor = await db.execute("SELECT id FROM users WHERE telegram_id = ?", (user_telegram_id,))
        row = await cursor.fetchone()
        if not row:
            return False
        cursor2 = await db.execute(
            "SELECT id FROM favorites WHERE user_id = ? AND product_id = ?",
            (row["id"], product_id)
        )
        return (await cursor2.fetchone()) is not None


# ==================== STOCK NOTIFICATIONS ====================

async def add_stock_notification(user_telegram_id: int, product_id: int) -> None:
    """Stok bildirishnoma qo'shadi"""
    async with get_db() as db:
        cursor = await db.execute("SELECT id FROM users WHERE telegram_id = ?", (user_telegram_id,))
        row = await cursor.fetchone()
        if not row:
            return
        await db.execute(
            "INSERT OR IGNORE INTO stock_notifications (user_id, product_id) VALUES (?, ?)",
            (row["id"], product_id)
        )
        await db.commit()


async def get_stock_notification_users(product_id: int) -> list[int]:
    """Shu mahsulotga bildirishnoma so'ragan foydalanuvchilar telegram_id larini qaytaradi"""
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT u.telegram_id FROM stock_notifications sn
            JOIN users u ON u.id = sn.user_id
            WHERE sn.product_id = ? AND sn.notified = 0
        """, (product_id,))
        rows = await cursor.fetchall()
        return [r["telegram_id"] for r in rows]


async def mark_stock_notified(product_id: int) -> None:
    """Shu mahsulot bildirishnomalarini yuborilgan deb belgilaydi"""
    async with get_db() as db:
        await db.execute(
            "UPDATE stock_notifications SET notified = 1 WHERE product_id = ?",
            (product_id,)
        )
        await db.commit()


async def get_low_stock_products(threshold: int = 3) -> list[dict]:
    """Kamligi past mahsulot+tierlarni qaytaradi"""
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT a.product_id, a.duration_tier, COUNT(*) as cnt,
                   p.name_uz, p.name_ru
            FROM accounts a
            JOIN products p ON p.id = a.product_id
            WHERE a.status = 'available'
            GROUP BY a.product_id, a.duration_tier
            HAVING cnt <= ?
        """, (threshold,))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_all_managers_and_bosses() -> list[int]:
    """Manager va boss telegram_id larini qaytaradi"""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT telegram_id FROM admin_roles WHERE role IN ('manager','boss') AND is_active = 1"
        )
        rows = await cursor.fetchall()
        return [r["telegram_id"] for r in rows]


# ==================== PENDING ORDERS: TIMEOUT ====================

async def get_expired_pending_orders(timeout_minutes: int = 30) -> list[dict]:
    """To'lov muddati o'tgan buyurtmalarni qaytaradi"""
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT o.*, u.telegram_id as user_telegram_id, u.language as user_lang
            FROM orders o
            JOIN users u ON u.id = o.user_id
            WHERE o.status IN ('pending_payment', 'payment_sent')
              AND datetime(o.created_at, '+' || ? || ' minutes') < datetime('now')
        """, (timeout_minutes,))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
