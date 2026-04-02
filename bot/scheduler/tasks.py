"""
Scheduler vazifalari — APScheduler bilan
"""
import logging
from datetime import datetime
from typing import TYPE_CHECKING

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from bot.config import TIMEZONE
from bot.db.models import (
    update_remaining_days, get_expired_pending_orders,
    release_reserved_accounts, update_order_status,
    get_low_stock_products, get_all_managers_and_bosses,
    get_stock_notification_users, mark_stock_notified,
    get_prices_by_product,
)

if TYPE_CHECKING:
    from aiogram import Bot

logger = logging.getLogger(__name__)

# Stok bildirishnoma uchun oldingi holat (xotira)
_prev_stock: dict[str, int] = {}


# ==================== VAZIFALAR ====================

async def task_update_account_days() -> None:
    """
    Har kuni 06:00 da ishlaydigan vazifa.
    Barcha available akkauntlar uchun remaining_days va tier yangilaydi.
    Muddati o'tganlarni expired qiladi.
    """
    try:
        updated = await update_remaining_days()
        logger.info(f"Akkaunt kunlari yangilandi: {updated} ta.")
    except Exception as e:
        logger.error(f"update_remaining_days xato: {e}")


async def task_check_payment_timeout(bot: "Bot") -> None:
    """
    Har 5 daqiqada tekshirish.
    To'lov muddati 30 daqiqadan o'tgan buyurtmalarni bekor qiladi.
    """
    try:
        expired_orders = await get_expired_pending_orders(timeout_minutes=30)

        for order in expired_orders:
            order_id = order["id"]
            user_telegram_id = order["user_telegram_id"]
            lang = order.get("user_lang", "uz")

            # Akkauntlarni ozod qilish
            await release_reserved_accounts(order_id)
            await update_order_status(order_id, "cancelled")

            # Progress bar yangilash
            progress_msg_id = order.get("progress_message_id")
            if progress_msg_id:
                try:
                    from bot.utils.texts import t
                    await bot.edit_message_text(
                        chat_id=user_telegram_id,
                        message_id=progress_msg_id,
                        text=t("progress_cancelled", lang)
                    )
                except Exception:
                    pass

            # Mijozga xabar
            try:
                from bot.utils.texts import t
                await bot.send_message(
                    chat_id=user_telegram_id,
                    text=t("order_cancelled_timeout", lang, order_id=order_id)
                )
            except Exception:
                pass

            logger.info(f"Buyurtma #{order_id} timeout bilan bekor qilindi.")

    except Exception as e:
        logger.error(f"check_payment_timeout xato: {e}")


async def task_check_stock_levels(bot: "Bot") -> None:
    """
    Har kuni 09:00 da tekshirish (smart timing: 10:00-21:00).
    Kam qolgan stoklar uchun adminlarga ogohlantirish yuboradi.
    Stok tiklangan mahsulotlar uchun kutayotgan mijozlarga xabar yuboradi.
    """
    try:
        from bot.utils.texts import t
        from bot.utils.duration import tier_display_name

        # Smart timing tekshirish (UTC+5)
        now_hour = datetime.now().hour
        # Scheduler TIMEZONE bilan ishlaydi, qo'shimcha tekshirish shart emas

        # 1. Kam qolgan stoklar (3 va kam)
        low_items = await get_low_stock_products(threshold=3)
        if low_items:
            admin_ids = await get_all_managers_and_bosses()

            item_lines = []
            for item in low_items:
                tier_name = tier_display_name(item["duration_tier"], "uz")
                item_lines.append(
                    t("low_stock_item", "uz",
                      name=item["name_uz"],
                      tier=tier_name,
                      cnt=item["cnt"])
                )

            if item_lines:
                msg = t("low_stock_admin", "uz", items="\n".join(item_lines))
                for admin_id in admin_ids:
                    try:
                        await bot.send_message(
                            chat_id=admin_id,
                            text=msg,
                            parse_mode="HTML"
                        )
                    except Exception:
                        pass

        # 2. Stok tiklangan mahsulotlar uchun mijozlarga xabar
        global _prev_stock
        from bot.db.database import get_db
        async with get_db() as db:
            cursor = await db.execute("""
                SELECT a.product_id, a.duration_tier, COUNT(*) as cnt,
                       p.name_uz, p.name_ru
                FROM accounts a
                JOIN products p ON p.id = a.product_id
                WHERE a.status = 'available'
                GROUP BY a.product_id, a.duration_tier
            """)
            rows = await cursor.fetchall()
            current_stock = {f"{r['product_id']}:{r['duration_tier']}": r["cnt"] for r in rows}

        for key, cnt in current_stock.items():
            prev_cnt = _prev_stock.get(key, 0)
            if prev_cnt == 0 and cnt > 0:
                # Stok tiklandi — bildirishnoma yuborish
                product_id, tier = key.split(":", 1)
                product_id = int(product_id)

                notify_users = await get_stock_notification_users(product_id)
                if notify_users:
                    prices = await get_prices_by_product(product_id)
                    price_info = next((p for p in prices if p["duration_tier"] == tier), None)
                    price_val = price_info["price"] if price_info else 0

                    for user_tid in notify_users:
                        from bot.db.models import get_user
                        user = await get_user(user_tid)
                        lang = user.get("language", "uz") if user else "uz"
                        name = (await _get_product_name(product_id, lang))
                        tier_name = tier_display_name(tier, lang)

                        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                        kb = InlineKeyboardMarkup(inline_keyboard=[[
                            InlineKeyboardButton(
                                text=t("btn_buy_now", lang),
                                callback_data=f"tier:{product_id}:{tier}"
                            )
                        ]])
                        try:
                            await bot.send_message(
                                chat_id=user_tid,
                                text=t("stock_restored_notify", lang,
                                       name=name, tier=tier_name, price=price_val),
                                reply_markup=kb,
                                parse_mode="HTML"
                            )
                        except Exception:
                            pass

                    await mark_stock_notified(product_id)

        _prev_stock = current_stock

    except Exception as e:
        logger.error(f"check_stock_levels xato: {e}")


async def _get_product_name(product_id: int, lang: str) -> str:
    """Mahsulot nomini qaytaradi"""
    from bot.db.models import get_product_by_id
    prod = await get_product_by_id(product_id)
    if not prod:
        return f"#{product_id}"
    return prod[f"name_{lang}"]


# ==================== SCHEDULER SOZLASH ====================

def setup_scheduler(bot: "Bot") -> AsyncIOScheduler:
    """Schedulerni sozlaydi va qaytaradi"""
    scheduler = AsyncIOScheduler(timezone=TIMEZONE)

    # Har kuni 06:00 da akkaunt kunlarini yangilash
    scheduler.add_job(
        task_update_account_days,
        trigger=CronTrigger(hour=6, minute=0, timezone=TIMEZONE),
        id="update_account_days",
        name="Akkaunt kunlarini yangilash",
        replace_existing=True,
        misfire_grace_time=3600
    )

    # Har 5 daqiqada payment timeout tekshirish
    scheduler.add_job(
        task_check_payment_timeout,
        trigger=IntervalTrigger(minutes=5),
        id="check_payment_timeout",
        name="To'lov timeout tekshirish",
        replace_existing=True,
        kwargs={"bot": bot}
    )

    # Har kuni 09:00 da stok tekshirish (smart timing)
    scheduler.add_job(
        task_check_stock_levels,
        trigger=CronTrigger(hour=9, minute=0, timezone=TIMEZONE),
        id="check_stock_levels",
        name="Stok tekshirish va ogohlantirish",
        replace_existing=True,
        kwargs={"bot": bot}
    )

    return scheduler
