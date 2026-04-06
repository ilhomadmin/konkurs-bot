"""
Scheduler vazifalari — APScheduler bilan
YANGI STRUKTURA: duration_tier yo'q
"""
import logging
from datetime import datetime
from typing import TYPE_CHECKING

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from bot.config import TIMEZONE
from bot.db.models import update_remaining_days

if TYPE_CHECKING:
    from aiogram import Bot

logger = logging.getLogger(__name__)

_prev_stock: dict[int, int] = {}


# ==================== VAZIFALAR ====================

async def task_update_account_days() -> None:
    try:
        updated = await update_remaining_days()
        logger.info(f"Akkaunt kunlari yangilandi: {updated} ta.")
    except Exception as e:
        logger.exception(f"update_remaining_days xato: {e}")


async def task_check_payment_timeout(bot: "Bot") -> None:
    try:
        from bot.db.models import get_orders_by_status, release_reserved, update_order_status
        from bot.utils.texts import t
        from datetime import timedelta

        try:
            from bot.utils.settings import get_setting_int
            timeout = await get_setting_int("payment_timeout_minutes", 30)
        except Exception:
            timeout = 30

        orders = await get_orders_by_status("pending_payment", limit=100)
        now = datetime.now()

        for order in orders:
            created = order.get("created_at", "")
            if not created:
                continue
            try:
                created_dt = datetime.fromisoformat(str(created))
            except (ValueError, TypeError):
                continue

            if (now - created_dt).total_seconds() < timeout * 60:
                continue

            order_id = order["id"]
            user_telegram_id = order.get("telegram_id")

            await release_reserved(order_id)
            await update_order_status(order_id, "cancelled")

            if user_telegram_id:
                progress_msg_id = order.get("progress_message_id")
                if progress_msg_id:
                    try:
                        await bot.edit_message_text(
                            chat_id=user_telegram_id,
                            message_id=progress_msg_id,
                            text=t("progress_cancelled", "uz")
                        )
                    except Exception:
                        pass
                try:
                    from bot.db.models import get_user
                    user = await get_user(user_telegram_id)
                    lang = user.get("language", "uz") if user else "uz"
                    await bot.send_message(
                        chat_id=user_telegram_id,
                        text=t("order_cancelled_timeout", lang, order_id=order_id)
                    )
                except Exception:
                    pass

            logger.info(f"Buyurtma #{order_id} timeout bilan bekor qilindi.")

    except Exception as e:
        logger.exception(f"check_payment_timeout xato: {e}")


async def task_check_stock_levels(bot: "Bot") -> None:
    try:
        from bot.utils.texts import t
        from bot.db.database import get_db
        from bot.db.models import get_user, get_product_by_id

        try:
            from bot.utils.settings import get_setting_int
            threshold = await get_setting_int("stock_alert_threshold", 3)
        except Exception:
            threshold = 3

        # 1. Kam qolgan stoklar
        async with get_db() as db:
            cursor = await db.execute("""
                SELECT a.product_id, COUNT(*) as cnt, p.name_uz
                FROM accounts a
                JOIN products p ON p.id = a.product_id
                WHERE a.status = 'available'
                GROUP BY a.product_id
                HAVING cnt <= ? AND cnt > 0
            """, (threshold,))
            low_items = [dict(r) for r in await cursor.fetchall()]

        if low_items:
            from bot.db.models import get_all_admins
            admins = await get_all_admins()
            admin_ids = [a["telegram_id"] for a in admins if a.get("role") in ("manager", "boss")]

            item_lines = [f"• {item['name_uz']}: {item['cnt']} ta" for item in low_items]
            msg = t("low_stock_admin", "uz", items="\n".join(item_lines))

            for admin_id in admin_ids:
                try:
                    await bot.send_message(chat_id=admin_id, text=msg, parse_mode="HTML")
                except Exception:
                    pass

        # 2. Stok tiklangan mahsulotlar
        global _prev_stock
        async with get_db() as db:
            cursor = await db.execute("""
                SELECT a.product_id, COUNT(*) as cnt
                FROM accounts a WHERE a.status = 'available'
                GROUP BY a.product_id
            """)
            rows = [dict(r) for r in await cursor.fetchall()]
            current_stock = {r["product_id"]: r["cnt"] for r in rows}

        for pid, cnt in current_stock.items():
            prev_cnt = _prev_stock.get(pid, 0)
            if prev_cnt == 0 and cnt > 0:
                from bot.db.models import get_stock_notifications, mark_notified
                notify_users = await get_stock_notifications(pid)
                prod = await get_product_by_id(pid)
                if not prod:
                    continue

                for nu in notify_users:
                    user_tid = nu.get("telegram_id") or nu.get("user_id")
                    if not user_tid:
                        continue
                    user = await get_user(user_tid)
                    lang = user.get("language", "uz") if user else "uz"
                    name = prod.get(f"name_{lang}", prod.get("name_uz", "?"))

                    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                    kb = InlineKeyboardMarkup(inline_keyboard=[[
                        InlineKeyboardButton(
                            text=t("btn_buy_now", lang),
                            callback_data=f"addcart:{pid}"
                        )
                    ]])
                    try:
                        await bot.send_message(
                            chat_id=user_tid,
                            text=t("stock_restored_notify", lang, name=name, price=prod.get("price", 0)),
                            reply_markup=kb, parse_mode="HTML"
                        )
                    except Exception:
                        pass

                    await mark_notified(user_tid, pid)

        _prev_stock = current_stock

    except Exception as e:
        logger.exception(f"check_stock_levels xato: {e}")


async def _get_product_name(product_id: int, lang: str) -> str:
    from bot.db.models import get_product_by_id
    prod = await get_product_by_id(product_id)
    if not prod:
        return f"#{product_id}"
    return prod.get(f"name_{lang}", prod.get("name_uz", "?"))


async def task_check_expiring_subscriptions(bot: "Bot") -> None:
    try:
        from bot.utils.texts import t
        from bot.db.database import get_db
        from bot.db.models import get_user
        from datetime import date, timedelta

        today = date.today()
        checks = [
            (3, "expiry_notified_3d", "expiry_3days"),
            (1, "expiry_notified_1d", "expiry_1day"),
            (0, "expiry_notified_0d", "expiry_today"),
        ]

        for days_left, notified_col, text_key in checks:
            target_date = (today + timedelta(days=days_left)).isoformat()
            async with get_db() as db:
                cursor = await db.execute(f"""
                    SELECT oi.id, oi.expiry_date, oi.product_id,
                           o.user_id, u.telegram_id, u.language,
                           p.name_uz, p.name_ru
                    FROM order_items oi
                    JOIN orders o ON o.id = oi.order_id
                    JOIN users u ON u.id = o.user_id
                    JOIN products p ON p.id = oi.product_id
                    WHERE oi.expiry_date = ? AND oi.status = 'delivered'
                          AND oi.{notified_col} = 0
                """, (target_date,))
                items = [dict(r) for r in await cursor.fetchall()]

            for item in items:
                lang = item.get("language", "uz")
                name = item.get(f"name_{lang}", item.get("name_uz", "?"))
                try:
                    await bot.send_message(
                        chat_id=item["telegram_id"],
                        text=t(text_key, lang, product=name, expiry=item["expiry_date"]),
                        parse_mode="HTML"
                    )
                except Exception:
                    pass

                async with get_db() as db:
                    await db.execute(
                        f"UPDATE order_items SET {notified_col} = 1 WHERE id = ?",
                        (item["id"],)
                    )
                    await db.commit()

    except Exception as e:
        logger.exception(f"check_expiring_subscriptions xato: {e}")


async def task_check_auto_renewals(bot: "Bot") -> None:
    try:
        from bot.utils.texts import t
        from bot.db.models import (
            get_due_auto_renewals, sell_account, get_product_by_id,
            update_auto_renewal_status, get_user,
        )
        from datetime import date, timedelta

        renewals = await get_due_auto_renewals()
        for renewal in renewals:
            user_tid = renewal.get("telegram_id") or renewal.get("user_telegram_id")
            if not user_tid:
                continue
            user = await get_user(user_tid)
            lang = user.get("language", "uz") if user else "uz"
            prod = await get_product_by_id(renewal["product_id"])
            product_name = prod.get(f"name_{lang}", "?") if prod else "?"

            account = await sell_account(renewal["product_id"], 0, user_tid)
            if account:
                try:
                    await bot.send_message(
                        chat_id=user_tid,
                        text=t("auto_renewal_executed", lang,
                               product=product_name,
                               login=account["login"],
                               password=account["password"],
                               expiry=account.get("expiry_date", "—")),
                        parse_mode="HTML"
                    )
                except Exception:
                    pass
                # Update next renewal date (30 days default)
                next_date = (date.today() + timedelta(days=30)).isoformat()
                await update_auto_renewal_status(renewal["id"], "active", next_date)
            else:
                try:
                    await bot.send_message(
                        chat_id=user_tid,
                        text=t("auto_renewal_failed", lang, product=product_name),
                        parse_mode="HTML"
                    )
                except Exception:
                    pass
                await update_auto_renewal_status(renewal["id"], "failed")

    except Exception as e:
        logger.exception(f"check_auto_renewals xato: {e}")


async def task_check_abandoned_carts(bot: "Bot") -> None:
    try:
        now_hour = datetime.now().hour
        if not (10 <= now_hour <= 21):
            return

        from bot.utils.texts import t
        from bot.db.database import get_db
        from datetime import timedelta

        now = datetime.now()

        # 2 soatlik eslatma
        cutoff_2h = (now - timedelta(hours=2)).isoformat()
        async with get_db() as db:
            cursor = await db.execute("""
                SELECT u.telegram_id, u.language, COUNT(*) as item_count, ci.id as cart_item_id
                FROM cart_items ci
                JOIN users u ON u.id = ci.user_id
                WHERE ci.added_at <= ? AND ci.reminder_sent_2h = 0
                GROUP BY u.id
            """, (cutoff_2h,))
            users_2h = [dict(r) for r in await cursor.fetchall()]

        for u in users_2h:
            try:
                await bot.send_message(
                    chat_id=u["telegram_id"],
                    text=t("abandoned_cart_reminder", u.get("language", "uz"), count=u["item_count"]),
                    parse_mode="HTML"
                )
            except Exception:
                pass
            async with get_db() as db:
                await db.execute("""
                    UPDATE cart_items SET reminder_sent_2h = 1
                    WHERE user_id = (SELECT id FROM users WHERE telegram_id = ?)
                """, (u["telegram_id"],))
                await db.commit()

    except Exception as e:
        logger.exception(f"check_abandoned_carts xato: {e}")


async def task_request_reviews(bot: "Bot") -> None:
    try:
        from bot.utils.texts import t
        from bot.db.database import get_db
        from bot.db.models import get_user
        from datetime import timedelta

        cutoff = (datetime.now() - timedelta(days=3)).isoformat()

        async with get_db() as db:
            cursor = await db.execute("""
                SELECT oi.id as order_item_id, oi.product_id,
                       o.user_id, u.telegram_id, u.language,
                       p.name_uz, p.name_ru
                FROM order_items oi
                JOIN orders o ON o.id = oi.order_id
                JOIN users u ON u.id = o.user_id
                JOIN products p ON p.id = oi.product_id
                WHERE oi.status = 'delivered' AND oi.delivered_at <= ?
                AND NOT EXISTS (
                    SELECT 1 FROM reviews r WHERE r.order_item_id = oi.id
                )
                LIMIT 50
            """, (cutoff,))
            items = [dict(r) for r in await cursor.fetchall()]

        for item in items:
            lang = item.get("language", "uz")
            name = item.get(f"name_{lang}", item.get("name_uz", "?"))
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=f"{'⭐' * i}", callback_data=f"rev:{item['order_item_id']}:{i}")
                 for i in range(1, 6)]
            ])
            try:
                await bot.send_message(
                    chat_id=item["telegram_id"],
                    text=t("review_request", lang, product=name),
                    reply_markup=kb, parse_mode="HTML"
                )
            except Exception:
                pass

    except Exception as e:
        logger.exception(f"request_reviews xato: {e}")


async def task_send_cross_sell(bot: "Bot") -> None:
    try:
        from bot.utils.texts import t
        from bot.db.database import get_db
        from bot.db.models import get_user, log_cross_sell
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        from datetime import timedelta

        cutoff = (datetime.now() - timedelta(days=1)).isoformat()

        async with get_db() as db:
            # Users who bought something recently
            cursor = await db.execute("""
                SELECT DISTINCT u.telegram_id, u.language, u.id as user_id
                FROM orders o
                JOIN users u ON u.id = o.user_id
                WHERE o.status = 'confirmed' AND o.updated_at >= ?
                LIMIT 50
            """, (cutoff,))
            buyers = [dict(r) for r in await cursor.fetchall()]

        for buyer in buyers:
            lang = buyer.get("language", "uz")
            async with get_db() as db:
                cursor = await db.execute("""
                    SELECT p.id, p.name_uz, p.name_ru, p.price
                    FROM products p
                    WHERE p.is_active = 1
                    AND p.id NOT IN (
                        SELECT oi.product_id FROM order_items oi
                        JOIN orders o ON o.id = oi.order_id
                        WHERE o.user_id = ?
                    )
                    AND p.id NOT IN (
                        SELECT product_id FROM cross_sell_log WHERE user_id = ?
                    )
                    ORDER BY p.purchase_count DESC
                    LIMIT 3
                """, (buyer["user_id"], buyer["user_id"]))
                recs = [dict(r) for r in await cursor.fetchall()]

            if not recs:
                continue

            buttons = []
            for r in recs:
                name = r.get(f"name_{lang}", r.get("name_uz", "?"))
                buttons.append([InlineKeyboardButton(
                    text=f"{name} — {r['price']:,} so'm",
                    callback_data=f"addcart:{r['id']}"
                )])

            kb = InlineKeyboardMarkup(inline_keyboard=buttons)
            try:
                await bot.send_message(
                    chat_id=buyer["telegram_id"],
                    text=t("cross_sell", lang),
                    reply_markup=kb, parse_mode="HTML"
                )
                for r in recs:
                    await log_cross_sell(buyer["telegram_id"], r["id"])
            except Exception:
                pass

    except Exception as e:
        logger.exception(f"send_cross_sell xato: {e}")


async def task_deactivate_flash_sales() -> None:
    try:
        from bot.db.database import get_db
        now = datetime.now().isoformat()
        async with get_db() as db:
            await db.execute(
                "UPDATE flash_sales SET is_active = 0 WHERE ends_at <= ? AND is_active = 1",
                (now,)
            )
            await db.commit()
    except Exception as e:
        logger.exception(f"deactivate_flash_sales xato: {e}")


async def task_update_finance_cache() -> None:
    try:
        from bot.db.models import update_daily_finance_cache
        from datetime import date
        await update_daily_finance_cache(date.today().isoformat())
    except Exception as e:
        logger.exception(f"update_finance_cache xato: {e}")


# ==================== SCHEDULER SOZLASH ====================

def setup_scheduler(bot: "Bot") -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=TIMEZONE)

    scheduler.add_job(
        task_update_account_days,
        trigger=CronTrigger(hour=6, minute=0, timezone=TIMEZONE),
        id="update_account_days", replace_existing=True, misfire_grace_time=3600
    )

    scheduler.add_job(
        task_check_payment_timeout,
        trigger=IntervalTrigger(minutes=5),
        id="check_payment_timeout", replace_existing=True,
        kwargs={"bot": bot}
    )

    scheduler.add_job(
        task_check_stock_levels,
        trigger=CronTrigger(hour=9, minute=0, timezone=TIMEZONE),
        id="check_stock_levels", replace_existing=True,
        kwargs={"bot": bot}
    )

    scheduler.add_job(
        task_check_expiring_subscriptions,
        trigger=CronTrigger(hour=10, minute=0, timezone=TIMEZONE),
        id="check_expiring", replace_existing=True,
        kwargs={"bot": bot}
    )

    scheduler.add_job(
        task_check_auto_renewals,
        trigger=CronTrigger(hour=10, minute=5, timezone=TIMEZONE),
        id="check_auto_renewals", replace_existing=True,
        kwargs={"bot": bot}
    )

    scheduler.add_job(
        task_check_abandoned_carts,
        trigger=IntervalTrigger(hours=1),
        id="check_abandoned_carts", replace_existing=True,
        kwargs={"bot": bot}
    )

    scheduler.add_job(
        task_request_reviews,
        trigger=CronTrigger(hour=12, minute=0, timezone=TIMEZONE),
        id="request_reviews", replace_existing=True,
        kwargs={"bot": bot}
    )

    scheduler.add_job(
        task_send_cross_sell,
        trigger=CronTrigger(hour=14, minute=0, timezone=TIMEZONE),
        id="send_cross_sell", replace_existing=True,
        kwargs={"bot": bot}
    )

    scheduler.add_job(
        task_deactivate_flash_sales,
        trigger=IntervalTrigger(minutes=5),
        id="deactivate_flash_sales", replace_existing=True,
    )

    scheduler.add_job(
        task_update_finance_cache,
        trigger=CronTrigger(hour=23, minute=59, timezone=TIMEZONE),
        id="update_finance_cache", replace_existing=True,
    )

    return scheduler
