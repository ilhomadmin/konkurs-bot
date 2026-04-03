"""
Ma'lumotlar bazasiga ulanish va barcha jadvallarni yaratish
"""
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import aiosqlite
from bot.config import DB_PATH


@asynccontextmanager
async def get_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    """
    Asinxron DB ulanishini context manager sifatida qaytaradi.
    Ishlatish: async with get_db() as db: ...
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys = ON")
        yield db


async def init_db() -> None:
    """Barcha jadvallarni yaratadi (agar mavjud bo'lmasa)"""
    # DB papkasini yaratish
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")

        # Foydalanuvchilar jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                full_name TEXT,
                phone TEXT,
                language TEXT DEFAULT 'uz',
                referral_code TEXT UNIQUE,
                referred_by INTEGER,
                referral_count INTEGER DEFAULT 0,
                vip_level TEXT DEFAULT 'standard',
                total_purchases INTEGER DEFAULT 0,
                total_spent INTEGER DEFAULT 0,
                auto_renewal_enabled INTEGER DEFAULT 0,
                onboarding_shown INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Kategoriyalar jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name_uz TEXT NOT NULL,
                name_ru TEXT NOT NULL,
                description_uz TEXT,
                description_ru TEXT,
                instruction_video_file_id TEXT,
                is_active INTEGER DEFAULT 1,
                sort_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Mahsulotlar jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                name_uz TEXT NOT NULL,
                name_ru TEXT NOT NULL,
                description_uz TEXT,
                description_ru TEXT,
                instruction_video_file_id TEXT,
                has_warranty INTEGER DEFAULT 0,
                warranty_days INTEGER DEFAULT 0,
                purchase_count INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                sort_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
        """)

        # Mahsulot narx tierlari
        await db.execute("""
            CREATE TABLE IF NOT EXISTS product_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                duration_tier TEXT NOT NULL,
                display_name_uz TEXT NOT NULL,
                display_name_ru TEXT NOT NULL,
                min_days INTEGER NOT NULL,
                max_days INTEGER NOT NULL,
                price INTEGER NOT NULL,
                cost_price INTEGER NOT NULL DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)

        # Akkauntlar jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                login TEXT NOT NULL,
                password TEXT NOT NULL,
                additional_data TEXT,
                supplier TEXT,
                expiry_date DATE NOT NULL,
                remaining_days INTEGER,
                duration_tier TEXT,
                status TEXT DEFAULT 'available',
                reserved_for_order_id INTEGER,
                reserved_at TIMESTAMP,
                sold_to_user_id INTEGER,
                sold_at TIMESTAMP,
                sold_via TEXT,
                direct_sale_token TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)

        # Savat elementlari
        await db.execute("""
            CREATE TABLE IF NOT EXISTS cart_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                duration_tier TEXT NOT NULL,
                quantity INTEGER DEFAULT 1,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)

        # Buyurtmalar jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                status TEXT DEFAULT 'pending_payment',
                total_amount INTEGER NOT NULL,
                discount_amount INTEGER DEFAULT 0,
                promo_code_id INTEGER,
                referral_discount INTEGER DEFAULT 0,
                note TEXT,
                payment_screenshot_file_id TEXT,
                payment_verified_by INTEGER,
                payment_verified_at TIMESTAMP,
                progress_message_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Buyurtma elementlari
        await db.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                account_id INTEGER,
                quantity INTEGER NOT NULL,
                duration_tier TEXT NOT NULL,
                unit_price INTEGER NOT NULL,
                cost_price INTEGER NOT NULL DEFAULT 0,
                status TEXT DEFAULT 'pending',
                delivered_at TIMESTAMP,
                expiry_date DATE,
                FOREIGN KEY (order_id) REFERENCES orders(id),
                FOREIGN KEY (product_id) REFERENCES products(id),
                FOREIGN KEY (account_id) REFERENCES accounts(id)
            )
        """)

        # Almashtirish so'rovlari
        await db.execute("""
            CREATE TABLE IF NOT EXISTS replacements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_item_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                reason TEXT NOT NULL,
                description TEXT,
                screenshot_file_id TEXT,
                status TEXT DEFAULT 'pending',
                admin_note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP,
                FOREIGN KEY (order_item_id) REFERENCES order_items(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Promo kodlar
        await db.execute("""
            CREATE TABLE IF NOT EXISTS promo_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                discount_percent INTEGER NOT NULL,
                max_uses INTEGER DEFAULT -1,
                used_count INTEGER DEFAULT 0,
                valid_from TIMESTAMP,
                valid_until TIMESTAMP,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Flash sale
        await db.execute("""
            CREATE TABLE IF NOT EXISTS flash_sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                discount_percent INTEGER NOT NULL,
                starts_at TIMESTAMP NOT NULL,
                ends_at TIMESTAMP NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)

        # Sevimlilar
        await db.execute("""
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, product_id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)

        # Baholar/sharhlar
        await db.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                order_item_id INTEGER NOT NULL,
                rating INTEGER NOT NULL,
                comment TEXT,
                is_visible INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)

        # Stok bildirishnomalar
        await db.execute("""
            CREATE TABLE IF NOT EXISTS stock_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                notified INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, product_id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)

        # Xarajatlar
        await db.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                amount INTEGER NOT NULL,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Kunlik moliya keshi
        await db.execute("""
            CREATE TABLE IF NOT EXISTS daily_finance_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE UNIQUE NOT NULL,
                total_revenue INTEGER DEFAULT 0,
                total_cost INTEGER DEFAULT 0,
                total_expenses INTEGER DEFAULT 0,
                total_orders INTEGER DEFAULT 0,
                gross_profit INTEGER DEFAULT 0,
                net_profit INTEGER DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # To'plamlar (bundles)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS bundles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name_uz TEXT NOT NULL,
                name_ru TEXT NOT NULL,
                description_uz TEXT,
                description_ru TEXT,
                discount_percent INTEGER NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # To'plam elementlari
        await db.execute("""
            CREATE TABLE IF NOT EXISTS bundle_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bundle_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                duration_tier TEXT NOT NULL,
                quantity INTEGER DEFAULT 1,
                FOREIGN KEY (bundle_id) REFERENCES bundles(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)

        # Admin rollar
        await db.execute("""
            CREATE TABLE IF NOT EXISTS admin_roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                full_name TEXT,
                role TEXT NOT NULL DEFAULT 'operator',
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Avtomatik uzaytirish
        await db.execute("""
            CREATE TABLE IF NOT EXISTS auto_renewals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                duration_tier TEXT NOT NULL,
                order_item_id INTEGER NOT NULL,
                status TEXT DEFAULT 'active',
                next_renewal_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (product_id) REFERENCES products(id),
                FOREIGN KEY (order_item_id) REFERENCES order_items(id)
            )
        """)

        # VIP darajalar
        await db.execute("""
            CREATE TABLE IF NOT EXISTS vip_levels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT UNIQUE NOT NULL,
                min_purchases INTEGER NOT NULL,
                discount_percent INTEGER NOT NULL,
                display_name_uz TEXT NOT NULL,
                display_name_ru TEXT NOT NULL,
                badge_emoji TEXT NOT NULL
            )
        """)

        # VIP darajalarini boshlang'ich ma'lumotlar bilan to'ldirish
        await db.execute("""
            INSERT OR IGNORE INTO vip_levels (level, min_purchases, discount_percent, display_name_uz, display_name_ru, badge_emoji)
            VALUES
                ('standard', 0, 0, 'Oddiy', 'Обычный', '👤'),
                ('silver', 3, 3, '🥈 Silver', '🥈 Серебряный', '🥈'),
                ('gold', 10, 7, '🥇 Gold', '🥇 Золотой', '🥇'),
                ('platinum', 20, 12, '💎 Platinum', '💎 Платиновый', '💎')
        """)

        # Cross-sell log
        await db.execute("""
            CREATE TABLE IF NOT EXISTS cross_sell_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, product_id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)

        # Mavjud order_items jadvaliga yangi fieldlar qo'shish (migration)
        for col, default in [
            ("expiry_notified_3d", "0"),
            ("expiry_notified_1d", "0"),
            ("expiry_notified_0d", "0"),
        ]:
            try:
                await db.execute(
                    f"ALTER TABLE order_items ADD COLUMN {col} INTEGER DEFAULT {default}"
                )
            except Exception:
                pass  # Allaqachon mavjud

        # Mavjud cart_items jadvaliga yangi fieldlar
        for col, default in [
            ("reminder_sent_2h", "0"),
            ("reminder_sent_24h", "0"),
        ]:
            try:
                await db.execute(
                    f"ALTER TABLE cart_items ADD COLUMN {col} INTEGER DEFAULT {default}"
                )
            except Exception:
                pass

        await db.commit()
