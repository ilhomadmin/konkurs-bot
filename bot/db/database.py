"""
Ma'lumotlar bazasiga ulanish va barcha jadvallarni yaratish
YANGI STRUKTURA: Kategoriya (ixtiyoriy) → Obuna turi (products) → Akkauntlar
"""
import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import aiosqlite

from bot.config import DB_PATH

logger = logging.getLogger(__name__)


@asynccontextmanager
async def get_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys = ON")
        await db.execute("PRAGMA journal_mode = WAL")
        yield db


async def init_db() -> None:
    """Barcha jadvallarni yaratadi (agar mavjud bo'lmasa)"""
    os.makedirs(os.path.dirname(DB_PATH) if os.path.dirname(DB_PATH) else ".", exist_ok=True)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        await db.execute("PRAGMA journal_mode = WAL")

        # ==================== FOYDALANUVCHILAR ====================
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

        # ==================== TURKUMLAR (ixtiyoriy guruhlash) ====================
        await db.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name_uz TEXT NOT NULL,
                name_ru TEXT NOT NULL,
                description_uz TEXT,
                description_ru TEXT,
                instruction_video_file_id TEXT,
                video_keyword TEXT UNIQUE,
                is_active INTEGER DEFAULT 1,
                sort_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ==================== OBUNA TURLARI (asosiy mahsulot) ====================
        # Har bir obuna turi o'zida nom + narx + muddat saqlanadi
        # "ChatGPT Plus 1 oylik" = bitta obuna turi, narxi 25000
        # "ChatGPT Plus 1 yillik" = boshqa obuna turi, narxi 200000
        await db.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER,
                name_uz TEXT NOT NULL,
                name_ru TEXT NOT NULL,
                description_uz TEXT,
                description_ru TEXT,
                duration_text_uz TEXT,
                duration_text_ru TEXT,
                price INTEGER NOT NULL DEFAULT 0,
                cost_price INTEGER NOT NULL DEFAULT 0,
                instruction_video_file_id TEXT,
                video_keyword TEXT UNIQUE,
                has_warranty INTEGER DEFAULT 0,
                warranty_days INTEGER DEFAULT 0,
                purchase_count INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                sort_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
            )
        """)

        # product_prices jadvali qoladi (eski data uchun backward compat)
        # lekin yangi kodda ishlatilmaydi
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
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
            )
        """)

        # ==================== AKKAUNTLAR ====================
        # login, password, expiry_date — nullable (flexible fields)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                login TEXT,
                password TEXT,
                additional_data TEXT,
                supplier TEXT,
                expiry_date DATE,
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
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
            )
        """)

        # ==================== SAVAT ====================
        await db.execute("""
            CREATE TABLE IF NOT EXISTS cart_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER DEFAULT 1,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reminder_sent_2h INTEGER DEFAULT 0,
                reminder_sent_24h INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
            )
        """)

        # ==================== BUYURTMALAR ====================
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

        # ==================== BUYURTMA ELEMENTLARI ====================
        await db.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                account_id INTEGER,
                quantity INTEGER NOT NULL,
                unit_price INTEGER NOT NULL,
                cost_price INTEGER NOT NULL DEFAULT 0,
                status TEXT DEFAULT 'pending',
                delivered_at TIMESTAMP,
                expiry_date DATE,
                expiry_notified_3d INTEGER DEFAULT 0,
                expiry_notified_1d INTEGER DEFAULT 0,
                expiry_notified_0d INTEGER DEFAULT 0,
                FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(id),
                FOREIGN KEY (account_id) REFERENCES accounts(id)
            )
        """)

        # ==================== ALMASHTIRISH SO'ROVLARI ====================
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

        # ==================== PROMO KODLAR ====================
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

        # ==================== FLASH SALE ====================
        await db.execute("""
            CREATE TABLE IF NOT EXISTS flash_sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                discount_percent INTEGER NOT NULL,
                starts_at TIMESTAMP NOT NULL,
                ends_at TIMESTAMP NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
            )
        """)

        # ==================== SEVIMLILAR ====================
        await db.execute("""
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, product_id),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
            )
        """)

        # ==================== SHARHLAR ====================
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

        # ==================== STOK BILDIRISHNOMALAR ====================
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

        # ==================== XARAJATLAR ====================
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

        # ==================== KUNLIK MOLIYA KESHI ====================
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

        # ==================== TO'PLAMLAR ====================
        await db.execute("""
            CREATE TABLE IF NOT EXISTS bundles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name_uz TEXT NOT NULL,
                name_ru TEXT NOT NULL,
                description_uz TEXT,
                description_ru TEXT,
                discount_percent INTEGER NOT NULL DEFAULT 0,
                price INTEGER NOT NULL DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS bundle_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bundle_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER DEFAULT 1,
                FOREIGN KEY (bundle_id) REFERENCES bundles(id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
            )
        """)

        # ==================== ADMIN ROLLAR ====================
        await db.execute("""
            CREATE TABLE IF NOT EXISTS admin_roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                full_name TEXT,
                role TEXT NOT NULL DEFAULT 'operator',
                password_hash TEXT,
                permissions TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ==================== AVTOMATIK UZAYTIRISH ====================
        await db.execute("""
            CREATE TABLE IF NOT EXISTS auto_renewals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                order_item_id INTEGER NOT NULL,
                status TEXT DEFAULT 'active',
                next_renewal_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (product_id) REFERENCES products(id),
                FOREIGN KEY (order_item_id) REFERENCES order_items(id)
            )
        """)

        # ==================== VIP DARAJALAR ====================
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

        await db.execute("""
            INSERT OR IGNORE INTO vip_levels (level, min_purchases, discount_percent, display_name_uz, display_name_ru, badge_emoji)
            VALUES
                ('standard', 0, 0, 'Oddiy', 'Обычный', '👤'),
                ('silver', 3, 3, '🥈 Silver', '🥈 Серебряный', '🥈'),
                ('gold', 10, 7, '🥇 Gold', '🥇 Золотой', '🥇'),
                ('platinum', 20, 12, '💎 Platinum', '💎 Платиновый', '💎')
        """)

        # ==================== CROSS-SELL LOG ====================
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

        # ==================== SOZLAMALAR ====================
        await db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                description_uz TEXT,
                description_ru TEXT,
                category TEXT NOT NULL,
                value_type TEXT DEFAULT 'text',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Default sozlamalar
        defaults = [
            # To'lov
            ('payment_methods', '[{"id": "click", "name": "Click", "card": "8600 XXXX XXXX XXXX", "active": true}, {"id": "payme", "name": "Payme", "card": "8600 XXXX XXXX XXXX", "active": true}]', "To'lov usullari", 'Способы оплаты', 'payment', 'json'),
            ('payment_timeout_minutes', '30', "To'lov kutish (daqiqa)", 'Таймаут оплаты (мин)', 'payment', 'number'),
            ('payment_group_id', '', "To'lov cheklari guruhi ID", 'ID группы чеков', 'payment', 'text'),
            ('payment_instruction_uz', "To'lov qilib chekni yuboring", "To'lov yo'riqnomasi uz", 'Инструкция оплаты uz', 'payment', 'textarea'),
            ('payment_instruction_ru', 'Оплатите и отправьте чек', "To'lov yo'riqnomasi ru", 'Инструкция оплаты ru', 'payment', 'textarea'),
            # Marketing
            ('vip_enabled', 'true', 'VIP tizimi', 'VIP система', 'marketing', 'boolean'),
            ('referral_enabled', 'true', 'Referal tizimi', 'Реферальная система', 'marketing', 'boolean'),
            ('referral_discount_percent', '10', 'Referal chegirma %', 'Реферальная скидка %', 'marketing', 'number'),
            ('referral_bonus_days', '30', 'Referal promo muddati (kun)', 'Срок реферального промо (дни)', 'marketing', 'number'),
            ('renewal_discount_percent', '20', 'Uzaytirish chegirma %', 'Скидка на продление %', 'marketing', 'number'),
            ('abandoned_cart_discount_percent', '5', 'Savatga chegirma %', 'Скидка на брошенную корзину %', 'marketing', 'number'),
            ('cross_sell_enabled', 'true', 'Cross-sell tavsiya', 'Cross-sell рекомендации', 'marketing', 'boolean'),
            ('auto_delivery_enabled', 'true', 'Avtomatik yetkazish', 'Автодоставка', 'marketing', 'boolean'),
            # Vaqtlar
            ('smart_timing_start', '10', 'Xabar boshi (soat)', 'Начало отправки (час)', 'timing', 'number'),
            ('smart_timing_end', '21', 'Xabar oxiri (soat)', 'Конец отправки (час)', 'timing', 'number'),
            ('abandoned_cart_first_hours', '2', '1-eslatma (soat)', '1-е напоминание (часы)', 'timing', 'number'),
            ('abandoned_cart_second_hours', '24', '2-eslatma (soat)', '2-е напоминание (часы)', 'timing', 'number'),
            ('expiry_reminder_days', '3,1,0', 'Muddat eslatma kunlari', 'Дни напоминания об истечении', 'timing', 'text'),
            ('review_ask_days', '3', "Sharh so'rash (kun keyin)", 'Запрос отзыва (через дней)', 'timing', 'number'),
            ('cross_sell_delay_days', '1', 'Tavsiya (kun keyin)', 'Рекомендация (через дней)', 'timing', 'number'),
            # Stok
            ('stock_alert_enabled', 'true', 'Stok ogohlantirish', 'Уведомление о стоке', 'inventory', 'boolean'),
            ('stock_alert_threshold', '3', 'Stok chegarasi', 'Порог стока', 'inventory', 'number'),
            # Kontent
            ('faq_items', '[{"q_uz": "Qanday to\'lash mumkin?", "q_ru": "Как оплатить?", "a_uz": "Click yoki Payme orqali", "a_ru": "Через Click или Payme", "active": true}]', 'FAQ', 'FAQ', 'content', 'json'),
            ('onboarding_enabled', 'true', 'Onboarding', 'Онбоардинг', 'content', 'boolean'),
            ('onboarding_messages', '[{"uz": "IDROK.AI ga xush kelibsiz!", "ru": "Добро пожаловать в IDROK.AI!"}, {"uz": "Tanlang, savatga soling, to\'lang!", "ru": "Выберите, добавьте в корзину, оплатите!"}, {"uz": "Barcha obunalarga kafolat!", "ru": "Гарантия на все подписки!"}]', 'Onboarding xabarlari', 'Сообщения онбоардинга', 'content', 'json'),
            ('welcome_message_uz', 'Assalomu alaykum! Obuna tanlang:', 'Salomlashish uz', 'Приветствие uz', 'content', 'textarea'),
            ('welcome_message_ru', 'Здравствуйте! Выберите подписку:', 'Salomlashish ru', 'Приветствие ru', 'content', 'textarea'),
            ('order_confirmed_message_uz', "Buyurtmangiz tasdiqlandi! Akkaunt ma'lumotlari:", 'Tasdiqlash xabari uz', 'Сообщение подтверждения uz', 'content', 'textarea'),
            ('order_confirmed_message_ru', 'Ваш заказ подтвержден! Данные аккаунта:', 'Tasdiqlash xabari ru', 'Сообщение подтверждения ru', 'content', 'textarea'),
            ('error_message_uz', "Xato yuz berdi. Iltimos, qayta urinib ko'ring.", 'Xato xabari uz', 'Сообщение об ошибке uz', 'content', 'textarea'),
            ('error_message_ru', 'Произошла ошибка. Попробуйте еще раз.', 'Xato xabari ru', 'Сообщение об ошибке ru', 'content', 'textarea'),
            ('bot_description_uz', 'Premium obunalar arzon narxda!', 'Bot tavsifi uz', 'Описание бота uz', 'content', 'textarea'),
            ('bot_description_ru', 'Премиум подписки по низким ценам!', 'Bot tavsifi ru', 'Описание бота ru', 'content', 'textarea'),
            # Menyu matnlari
            ('menu_products_uz', '📦 Obunalar', 'Menyu: obunalar uz', 'Меню: подписки uz', 'menu', 'text'),
            ('menu_products_ru', '📦 Подписки', 'Menyu: obunalar ru', 'Меню: подписки ru', 'menu', 'text'),
            ('menu_cart_uz', '🛒 Savat', 'Menyu: savat uz', 'Меню: корзина uz', 'menu', 'text'),
            ('menu_cart_ru', '🛒 Корзина', 'Menyu: savat ru', 'Меню: корзина ru', 'menu', 'text'),
            ('menu_orders_uz', '📋 Buyurtmalarim', 'Menyu: buyurtmalar uz', 'Меню: заказы uz', 'menu', 'text'),
            ('menu_orders_ru', '📋 Мои заказы', 'Menyu: buyurtmalar ru', 'Меню: заказы ru', 'menu', 'text'),
            ('menu_bundles_uz', '🎁 To\'plamlar', 'Menyu: to\'plamlar uz', 'Меню: пакеты uz', 'menu', 'text'),
            ('menu_bundles_ru', '🎁 Пакеты', 'Menyu: to\'plamlar ru', 'Меню: пакеты ru', 'menu', 'text'),
            ('menu_profile_uz', '👤 Profil', 'Menyu: profil uz', 'Меню: профиль uz', 'menu', 'text'),
            ('menu_profile_ru', '👤 Профиль', 'Menyu: profil ru', 'Меню: профиль ru', 'menu', 'text'),
            ('menu_help_uz', 'ℹ️ Yordam', 'Menyu: yordam uz', 'Меню: помощь uz', 'menu', 'text'),
            ('menu_help_ru', 'ℹ️ Помощь', 'Menyu: yordam ru', 'Меню: помощь ru', 'menu', 'text'),
            # Umumiy
            ('bot_maintenance_mode', 'false', 'Texnik tanaffus', 'Тех. перерыв', 'general', 'boolean'),
            ('maintenance_message_uz', 'Bot texnik ishlar sababli vaqtinchalik ishlamayapti.', 'Tanaffus xabari uz', 'Сообщение перерыва uz', 'general', 'textarea'),
            ('maintenance_message_ru', 'Бот временно не работает.', 'Tanaffus xabari ru', 'Сообщение перерыва ru', 'general', 'textarea'),
            ('min_order_amount', '0', "Min buyurtma (so'm)", 'Мин. заказ (сум)', 'general', 'number'),
            ('max_cart_items', '20', 'Max savat soni', 'Макс. товаров в корзине', 'general', 'number'),
            ('currency_rate_usd', '12500', 'Dollar kurs', 'Курс доллара', 'general', 'number'),
            ('ask_phone_on_register', 'false', "Ro'yxatda telefon", 'Телефон при регистрации', 'general', 'boolean'),
            ('bot_language_mode', 'uz_ru', 'Til rejimi (uz / uz_ru)', 'Режим языка', 'general', 'text'),
        ]

        for d in defaults:
            try:
                await db.execute(
                    """INSERT OR IGNORE INTO settings (key, value, description_uz, description_ru, category, value_type)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    d
                )
            except Exception as e:
                logger.warning(f"Setting insert error: {e}")

        # ==================== MIGRATION ====================
        # Eski jadvallar uchun yangi ustunlar
        migrations = [
            ("products", "price", "INTEGER NOT NULL DEFAULT 0"),
            ("products", "cost_price", "INTEGER NOT NULL DEFAULT 0"),
            ("products", "duration_text_uz", "TEXT"),
            ("products", "duration_text_ru", "TEXT"),
            ("products", "video_keyword", "TEXT"),
            # FIX 1: yangi product ustunlar
            ("products", "duration_days", "INTEGER DEFAULT 30"),
            ("products", "video_url", "TEXT"),
            ("products", "image_url", "TEXT"),
            ("categories", "video_keyword", "TEXT"),
            ("admin_roles", "password_hash", "TEXT"),
            ("admin_roles", "permissions", "TEXT"),
            ("order_items", "expiry_notified_3d", "INTEGER DEFAULT 0"),
            ("order_items", "expiry_notified_1d", "INTEGER DEFAULT 0"),
            ("order_items", "expiry_notified_0d", "INTEGER DEFAULT 0"),
            ("cart_items", "reminder_sent_2h", "INTEGER DEFAULT 0"),
            ("cart_items", "reminder_sent_24h", "INTEGER DEFAULT 0"),
        ]

        for table, col, coltype in migrations:
            try:
                await db.execute(f"ALTER TABLE {table} ADD COLUMN {col} {coltype}")
            except Exception:
                pass  # Allaqachon mavjud

        # FIX 7: accounts jadvalida expiry_date / login / password NOT NULL bo'lsa qayta yaratish
        try:
            cursor = await db.execute("PRAGMA table_info(accounts)")
            cols = await cursor.fetchall()
            needs_recreation = any(
                col[1] in ("expiry_date", "login", "password") and col[3] == 1
                for col in cols
            )
            if needs_recreation:
                logger.info("accounts jadvalini nullable ustunlar bilan qayta yaratish...")
                await db.execute("PRAGMA foreign_keys = OFF")
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS accounts_v2 (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        product_id INTEGER NOT NULL,
                        login TEXT,
                        password TEXT,
                        additional_data TEXT,
                        supplier TEXT,
                        expiry_date DATE,
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
                        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
                    )
                """)
                await db.execute("""
                    INSERT OR IGNORE INTO accounts_v2
                    SELECT id, product_id, login, password, additional_data, supplier,
                           expiry_date, remaining_days, duration_tier, status,
                           reserved_for_order_id, reserved_at, sold_to_user_id, sold_at,
                           sold_via, direct_sale_token, created_at
                    FROM accounts
                """)
                await db.execute("DROP TABLE accounts")
                await db.execute("ALTER TABLE accounts_v2 RENAME TO accounts")
                await db.execute("PRAGMA foreign_keys = ON")
                logger.info("accounts jadval migratsiyasi muvaffaqiyatli.")
        except Exception as e:
            logger.warning(f"accounts migration error: {e}")

        await db.commit()
        logger.info("DB init completed.")
