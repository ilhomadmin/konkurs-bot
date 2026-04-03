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

    # Har kuni 10:00 da muddati tugayotgan obunalar
    scheduler.add_job(
        task_check_expiring_subscriptions,
        trigger=CronTrigger(hour=10, minute=0, timezone=TIMEZONE),
        id="check_expiring",
        name="Muddati tugayotgan obunalar",
        replace_existing=True,
        kwargs={"bot": bot}
    )

    # Har kuni 10:05 da avtomatik yangilash
    scheduler.add_job(
        task_check_auto_renewals,
        trigger=CronTrigger(hour=10, minute=5, timezone=TIMEZONE),
        id="check_auto_renewals",
        name="Avtomatik yangilash",
        replace_existing=True,
        kwargs={"bot": bot}
    )

    # Har soatda tark etilgan savatlar
    scheduler.add_job(
        task_check_abandoned_carts,
        trigger=IntervalTrigger(hours=1),
        id="check_abandoned_carts",
        name="Tark etilgan savatlar",
        replace_existing=True,
        kwargs={"bot": bot}
    )

    # Har kuni 12:00 da baho so'rash
    scheduler.add_job(
        task_request_reviews,
        trigger=CronTrigger(hour=12, minute=0, timezone=TIMEZONE),
        id="request_reviews",
        name="Baho so'rash",
        replace_existing=True,
        kwargs={"bot": bot}
    )

    # Har kuni 14:00 da cross-sell
    scheduler.add_job(
        task_send_cross_sell,
        trigger=CronTrigger(hour=14, minute=0, timezone=TIMEZONE),
        id="send_cross_sell",
        name="Cross-sell tavsiyalar",
        replace_existing=True,
        kwargs={"bot": bot}
    )

    # Har 5 daqiqada flash sale muddatini tekshirish
    scheduler.add_job(
        task_deactivate_flash_sales,
        trigger=IntervalTrigger(minutes=5),
        id="deactivate_flash_sales",
        name="Flash sale tekshirish",
        replace_existing=True,
    )

    # Har kuni 23:59 da moliyaviy kesh yangilash
    scheduler.add_job(
        task_update_finance_cache,
        trigger=CronTrigger(hour=23, minute=59, timezone=TIMEZONE),
        id="update_finance_cache",
        name="Moliyaviy kesh yangilash",
        replace_existing=True,
    )

    return scheduler


async def task_check_expiring_subscriptions(bot: "Bot") -> None:
    """Har kuni 10:00 da muddati tugayotgan obunalarni tekshiradi."""
    try:
        from bot.utils.texts import t
        from bot.db.models import get_expiring_order_items, mark_expiry_notified

        for days, key in [(3, "expiry_3days"), (1, "expiry_1day"), (0, "expiry_today")]:
            items = await get_expiring_order_items(days_left=days, notified_field=notified_field)
            for item in items:
                user_tid = item["user_telegram_id"]
                lang = item.get("user_lang", item.get("lang", "uz"))
                try:
                    await bot.send_message(
                        chat_id=user_tid,
                        text=t(key, lang, product=item["product_name"], expiry=item["expires_at"]),
                        parse_mode="HTML"
                    )
                    await mark_expiry_notified(item["id"], notified_field)
                except Exception:
                    pass
    except Exception as e:
        logger.error(f"check_expiring_subscriptions xato: {e}")


async def task_check_auto_renewals(bot: "Bot") -> None:
    """Har kuni 10:00 da avtomatik yangilashlarni bajaradi."""
    try:
        from bot.utils.texts import t
        from bot.db.models import (
            get_due_auto_renewals, get_available_account,
            sell_account, deactivate_auto_renewal
        )
        from datetime import date, timedelta

        from datetime import date, timedelta
        tomorrow_str = (date.today() + timedelta(days=1)).isoformat()
        renewals = await get_due_auto_renewals(tomorrow_str)
        for renewal in renewals:
            lang = renewal.get("user_lang", "uz")
            product_name = renewal.get("name_uz") if lang == "uz" else renewal.get("name_ru", renewal.get("name_uz","?"))
            account = await get_available_account(renewal["product_id"], renewal["duration_tier"])
            if account:
                await sell_account(account["id"], renewal["user_telegram_id"], sold_via="auto_renewal")
                tier_days = {"15_days": 15, "1_month": 30, "3_months": 90,
                        "6_months": 180, "12_months": 365}.get(renewal["duration_tier"], 30)
                expiry = (date.today() + timedelta(days=tier_days)).isoformat()
                try:
                    await bot.send_message(
                        chat_id=renewal["user_telegram_id"],
                        text=t("auto_renewal_executed", lang,
                               product=product_name,
                               login=account["login"],
                               password=account["password"],
                               expiry=expiry),
                        parse_mode="HTML"
                    )
                except Exception:
                    pass
            else:
                try:
                    await bot.send_message(
                        chat_id=renewal["user_telegram_id"],
                        text=t("auto_renewal_failed", lang, product=product_name),
                        parse_mode="HTML"
                    )
                    await deactivate_auto_renewal(renewal["id"])
                except Exception:
                    pass
    except Exception as e:
        logger.error(f"check_auto_renewals xato: {e}")


async def task_check_abandoned_carts(bot: "Bot") -> None:
    """Har soatda tark etilgan savatlarni tekshiradi (10:00-21:00)."""
    try:
        now_hour = datetime.now().hour
        if not (10 <= now_hour <= 21):
            return

        from bot.utils.texts import t
        from bot.db.models import get_abandoned_cart_users, mark_cart_reminder_sent

        users = await get_abandoned_cart_users(hours=2, sent_field="reminder_sent_2h")
        for user in users:
            try:
                await bot.send_message(
                    chat_id=user["telegram_id"],
                    text=t("abandoned_cart_reminder", user.get("language", "uz"),
                           count=user["item_count"]),
                    parse_mode="HTML"
                )
                await mark_cart_reminder_sent(user["id"], "reminder_sent_2h")
            except Exception:
                pass
    except Exception as e:
        logger.error(f"check_abandoned_carts xato: {e}")


async def task_request_reviews(bot: "Bot") -> None:
    """Har kuni 12:00 da yetkazilgan buyurtmalar uchun baho so'rashi."""
    try:
        from bot.utils.texts import t
        from bot.db.models import get_pending_reviews_to_request
        from bot.handlers.review import make_review_keyboard

        items = await get_pending_reviews_to_request()
        for item in items:
            lang = item.get("user_lang", item.get("lang", "uz"))
            kb = make_review_keyboard(item["order_item_id"], lang)
            try:
                await bot.send_message(
                    chat_id=item["user_telegram_id"],
                    text=t("review_request", lang, product=item["product_name"]),
                    reply_markup=kb,
                    parse_mode="HTML"
                )
            except Exception:
                pass
    except Exception as e:
        logger.error(f"request_reviews xato: {e}")


async def task_send_cross_sell(bot: "Bot") -> None:
    """Har kuni 14:00 da cross-sell tavsiyalar yuboradi."""
    try:
        from bot.utils.texts import t
        from bot.db.models import get_cross_sell_targets, log_cross_sell
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

        targets = await get_cross_sell_targets()
        for target in targets:
            recs = target.get("recommendations", [])
            if not recs:
                continue
            lang = target.get("lang", "uz")
            items_text = "\n".join(
                t("cross_sell_item", lang, name=r["name"], price=r["price"])
                for r in recs[:3]
            )
            buttons = [
                [InlineKeyboardButton(text=r["name"], callback_data=f"prod:{r['product_id']}")]
                for r in recs[:3]
            ]
            kb = InlineKeyboardMarkup(inline_keyboard=buttons)
            try:
                await bot.send_message(
                    chat_id=target["telegram_id"],
                    text=t("cross_sell", lang,
                           product=target["last_product"],
                           recommendations=items_text),
                    reply_markup=kb,
                    parse_mode="HTML"
                )
                await log_cross_sell(target["id"], [r["product_id"] for r in recs[:3]])
            except Exception:
                pass
    except Exception as e:
        logger.error(f"send_cross_sell xato: {e}")


async def task_deactivate_flash_sales() -> None:
    """Har 5 daqiqada flash sale muddatini tekshiradi."""
    try:
        from bot.db.models import deactivate_expired_flash_sales
        await deactivate_expired_flash_sales()
    except Exception as e:
        logger.error(f"deactivate_flash_sales xato: {e}")


async def task_update_finance_cache() -> None:
    """Har kuni 23:59 da moliyaviy keshni yangilaydi."""
    try:
        from bot.db.models import update_finance_cache_today
        await update_finance_cache_today()
    except Exception as e:
        logger.error(f"update_finance_cache xato: {e}")
