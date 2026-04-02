"""
Scheduler vazifalari — APScheduler bilan
"""
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from bot.config import TIMEZONE
from bot.db.models import update_remaining_days

logger = logging.getLogger(__name__)


async def task_update_account_days() -> None:
    """
    Har kuni 06:00 (TIMEZONE) da ishlaydigan vazifa.
    Barcha available akkauntlar uchun remaining_days va tier yangilaydi.
    Muddati o'tganlarni expired qiladi.
    """
    try:
        updated = await update_remaining_days()
        logger.info(f"Akkaunt kunlari yangilandi: {updated} ta akkaunt.")
    except Exception as e:
        logger.error(f"Akkaunt kunlarini yangilashda xato: {e}")


def setup_scheduler() -> AsyncIOScheduler:
    """Schedulerni sozlaydi va qaytaradi"""
    scheduler = AsyncIOScheduler(timezone=TIMEZONE)

    # Har kuni 06:00 da akkaunt kunlarini yangilash
    scheduler.add_job(
        task_update_account_days,
        trigger=CronTrigger(hour=6, minute=0, timezone=TIMEZONE),
        id="update_account_days",
        name="Akkaunt kunlarini yangilash",
        replace_existing=True,
        misfire_grace_time=3600  # 1 soat ichida ishlamasa ham qayta uradi
    )

    return scheduler
