"""
Bot konfiguratsiyasi — .env fayldan o'qiladi
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Asosiy token
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

# Admin IDlar (vergul bilan ajratilgan, list sifatida)
_admin_ids_raw = os.getenv("ADMIN_IDS", "")
ADMIN_IDS: list[int] = [int(x.strip()) for x in _admin_ids_raw.split(",") if x.strip().isdigit()]

# To'lov skrinshotlari yuboriladigan guruh ID
PAYMENT_GROUP_ID: int = int(os.getenv("PAYMENT_GROUP_ID", "0"))

# SQLite DB manzili
DB_PATH: str = os.getenv("DB_PATH", "data/bot.db")

# Vaqt zonasi (scheduler uchun)
TIMEZONE: str = os.getenv("TIMEZONE", "Asia/Tashkent")

# Web admin panel
WEB_SECRET_KEY: str = os.getenv("WEB_SECRET_KEY", "change-this-secret-key-in-production")
WEB_PORT: int = int(os.getenv("WEB_PORT", "8000"))

# Validatsiya
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN .env faylda ko'rsatilmagan!")

if not ADMIN_IDS:
    raise ValueError("ADMIN_IDS .env faylda ko'rsatilmagan!")
