"""
Dashboard — bosh sahifa statistikasi
"""
import logging
import os

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from bot.db.database import get_db
from web.auth import get_current_admin, require_auth

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")
)


@router.get("/")
async def dashboard(request: Request):
    redirect = require_auth(request)
    if redirect:
        return redirect

    admin = get_current_admin(request)

    try:
        async with get_db() as db:
            # Bugungi daromad va buyurtmalar
            cursor = await db.execute("""
                SELECT
                    COALESCE(SUM(o.total_amount - o.discount_amount), 0) AS today_revenue,
                    COUNT(o.id) AS today_orders
                FROM orders o
                WHERE DATE(o.created_at) = DATE('now', 'localtime')
                  AND o.status IN ('confirmed', 'delivered', 'auto_delivered')
            """)
            today_row = dict(await cursor.fetchone())

            # Bugungi foyda
            cursor = await db.execute("""
                SELECT COALESCE(SUM((oi.unit_price - oi.cost_price) * oi.quantity), 0) AS today_profit
                FROM order_items oi
                JOIN orders o ON o.id = oi.order_id
                WHERE DATE(o.created_at) = DATE('now', 'localtime')
                  AND o.status IN ('confirmed', 'delivered', 'auto_delivered')
            """)
            profit_row = dict(await cursor.fetchone())

            # Mavjud akkauntlar soni
            cursor = await db.execute(
                "SELECT COUNT(*) AS available_accounts FROM accounts WHERE status = 'available'")
            active_row = dict(await cursor.fetchone())

            # Oxirgi 7 ta buyurtma
            cursor = await db.execute("""
                SELECT o.id, o.total_amount, o.discount_amount, o.status,
                       o.created_at, u.full_name, u.username, u.telegram_id
                FROM orders o
                JOIN users u ON u.id = o.user_id
                ORDER BY o.created_at DESC
                LIMIT 7
            """)
            recent_orders = [dict(r) for r in await cursor.fetchall()]

            # Kam qolgan akkauntlar (5 dan kam)
            cursor = await db.execute("""
                SELECT p.id, p.name_uz, COUNT(a.id) AS cnt
                FROM products p
                LEFT JOIN accounts a ON a.product_id = p.id AND a.status = 'available'
                WHERE p.is_active = 1
                GROUP BY p.id
                HAVING cnt < 5
                ORDER BY cnt ASC
                LIMIT 10
            """)
            low_stock = [dict(r) for r in await cursor.fetchall()]

            # Kutayotgan almashtirish va buyurtmalar
            cursor = await db.execute(
                "SELECT COUNT(*) AS cnt FROM replacements WHERE status = 'pending'")
            pending_replacements = (await cursor.fetchone())["cnt"]

            cursor = await db.execute(
                "SELECT COUNT(*) AS cnt FROM orders WHERE status = 'pending_payment'")
            pending_orders = (await cursor.fetchone())["cnt"]

            # Oxirgi 7 kunlik grafik ma'lumotlari
            cursor = await db.execute("""
                SELECT date(o.created_at, 'localtime') AS day,
                       COALESCE(SUM(o.total_amount - o.discount_amount), 0) AS revenue
                FROM orders o
                WHERE o.status IN ('confirmed', 'delivered', 'auto_delivered')
                  AND date(o.created_at) >= date('now', '-6 days')
                GROUP BY day ORDER BY day
            """)
            daily_rows = [dict(r) for r in await cursor.fetchall()]

            # 7 ta label (so'nggi 7 kun)
            from datetime import date, timedelta
            today = date.today()
            days_map = {(today - timedelta(days=i)).isoformat(): 0 for i in range(6, -1, -1)}
            for row in daily_rows:
                if row["day"] in days_map:
                    days_map[row["day"]] = row["revenue"]

            chart_data = {
                "labels": [d[5:] for d in days_map.keys()],  # MM-DD format
                "revenue": list(days_map.values()),
                "expenses": [0] * 7,  # expenses hisob-kitobi alohida
            }

        stats = {
            "today_revenue": today_row["today_revenue"],
            "today_profit": profit_row["today_profit"],
            "today_orders": today_row["today_orders"],
            "available_accounts": active_row["available_accounts"],
            "pending_replacements": pending_replacements,
            "pending_orders": pending_orders,
            "low_stock": low_stock,
        }

        return templates.TemplateResponse(request, "dashboard.html", {
            "admin": admin,
            "stats": stats,
            "recent_orders": recent_orders,
            "low_stock": low_stock,
            "chart_data": chart_data,
        })

    except Exception:
        logger.exception("Dashboard yuklashda xato")
        empty_chart = {"labels": [], "revenue": [], "expenses": []}
        return templates.TemplateResponse(request, "dashboard.html", {
            "admin": admin,
            "stats": {
                "today_revenue": 0, "today_profit": 0, "today_orders": 0,
                "available_accounts": 0, "pending_replacements": 0,
                "pending_orders": 0, "low_stock": [],
            },
            "recent_orders": [],
            "low_stock": [],
            "chart_data": empty_chart,
            "error": "Ma'lumotlarni yuklashda xato yuz berdi",
        })
