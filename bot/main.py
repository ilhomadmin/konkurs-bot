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

# Handlerlar
from bot.handlers.admin.direct_sale import router as direct_sale_router  # DS /start avval
from bot.handlers.start import router as start_router
from bot.handlers.language import router as language_router
from bot.handlers.catalog import router as catalog_router
from bot.handlers.cart import router as cart_router
from bot.handlers.order import router as order_router
from bot.handlers.payment import router as payment_router
from bot.handlers.my_orders import router as my_orders_router
from bot.handlers.faq import router as faq_router
from bot.handlers.admin.menu import router as admin_menu_router
from bot.handlers.admin.products import router as admin_products_router
from bot.handlers.admin.accounts import router as admin_accounts_router
from bot.handlers.admin.roles import router as admin_roles_router
from bot.handlers.admin.orders import router as admin_orders_router

# Scheduler
from bot.scheduler.tasks import setup_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot) -> None:
    """Bot ishga tushganda bajariladigan amallar"""
    await init_db()
    logger.info("Ma'lumotlar bazasi tayyor.")

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

    # Routerlar tartib muhim:
    # 1. Direct sale deep link — /start DS_xxx (avval tekshiriladi)
    dp.include_router(direct_sale_router)
    # 2. Oddiy /start
    dp.include_router(start_router)
    dp.include_router(language_router)
    # 3. Katalog, savat, buyurtma
    dp.include_router(catalog_router)
    dp.include_router(cart_router)
    dp.include_router(order_router)
    dp.include_router(payment_router)
    dp.include_router(my_orders_router)
    dp.include_router(faq_router)
    # 4. Admin handlerlar
    dp.include_router(admin_menu_router)
    dp.include_router(admin_products_router)
    dp.include_router(admin_accounts_router)
    dp.include_router(admin_roles_router)
    dp.include_router(admin_orders_router)

    # Scheduler (bot instance bilan)
    scheduler = setup_scheduler(bot)
    scheduler.start()
    logger.info("Scheduler ishga tushdi.")

    dp.startup.register(on_startup)

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        scheduler.shutdown()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
