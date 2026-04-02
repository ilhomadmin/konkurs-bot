"""
IDROK.AI Bot — Entry Point
"""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import BOT_TOKEN
from bot.db.database import init_db
from bot.db.models import create_admin_role, get_admin_by_telegram_id
from bot.config import ADMIN_IDS

# Handler routerlarni import qilish
from bot.handlers.start import router as start_router
from bot.handlers.language import router as language_router
from bot.handlers.catalog import router as catalog_router
from bot.handlers.admin.menu import router as admin_menu_router
from bot.handlers.admin.products import router as admin_products_router
from bot.handlers.admin.accounts import router as admin_accounts_router
from bot.handlers.admin.roles import router as admin_roles_router

# Schedulerni import qilish
from bot.scheduler.tasks import setup_scheduler

# Logging sozlash
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot) -> None:
    """Bot ishga tushganda bajariladigan amallar"""
    # DB ni yaratish
    await init_db()
    logger.info("Ma'lumotlar bazasi tayyor.")

    # Birinchi ADMIN_ID ni boss sifatida ro'yxatdan o'tkazish
    boss_id = ADMIN_IDS[0]
    existing = await get_admin_by_telegram_id(boss_id)
    if not existing:
        await create_admin_role(boss_id, role="boss")
        logger.info(f"Boss admin yaratildi: {boss_id}")

    logger.info("Bot ishga tushdi! ✅")


async def main() -> None:
    """Asosiy funksiya"""
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp = Dispatcher(storage=MemoryStorage())

    # Routerlarni qo'shish (tartib muhim — spesifik handlerlar avval)
    dp.include_router(start_router)
    dp.include_router(language_router)
    dp.include_router(catalog_router)
    dp.include_router(admin_menu_router)
    dp.include_router(admin_products_router)
    dp.include_router(admin_accounts_router)
    dp.include_router(admin_roles_router)

    # Schedulerni ishga tushirish
    scheduler = setup_scheduler()
    scheduler.start()
    logger.info("Scheduler ishga tushdi.")

    # Bot ishga tushganda
    dp.startup.register(on_startup)

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        scheduler.shutdown()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
