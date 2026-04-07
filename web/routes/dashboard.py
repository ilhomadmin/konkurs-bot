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
            # Bugungi daromad
            cursor = await db.execute("""
                SELECT
                    COALESCE(SUM(o.total_amount - o.discount_amount), 0) AS today_revenue,
                    COUNT(o.id) AS today_orders
                FROM orders o
                WHERE DATE(o.created_at) = DATE('now', 'localtime')
                  AND o.status IN ('confirmed', 'delivered')
            """)
            today_row = dict(await cursor.fetchone())

            # Bugungi foyda (daromad - xarajat narxi)
            cursor = await db.execute("""
                SELECT COALESCE(SUM(oi.unit_price * oi.quantity - oi.cost_price * oi.quantity), 0) AS today_profit
                FROM order_items oi
                JOIN orders o ON o.id = oi.order_id
                WHERE DATE(o.created_at) = DATE('now', 'localtime')
                  AND o.status IN ('confirmed', 'delivered')
            """)
            profit_row = dict(await cursor.fetchone())

            # Faol akkauntlar (sotilgan, muddati o'tmagan)
            cursor = await db.execute("""
                SELECT COUNT(*) AS active_accounts
                FROM accounts
                WHERE status = 'sold'
                  AND expiry_date >= DATE('now', 'localtime')
            """)
            active_row = dict(await cursor.fetchone())

            # So'nggi 5 ta buyurtma
            cursor = await db.execute("""
                SELECT o.id, o.total_amount, o.discount_amount, o.status,
                       o.created_at, u.full_name, u.username, u.telegram_id
                FROM orders o
                JOIN users u ON u.id = o.user_id
                ORDER BY o.created_at DESC
                LIMIT 5
            """)
            last_orders = [dict(r) for r in await cursor.fetchall()]

            # Kam qolgan akkauntlar (5 dan kam)
            cursor = await db.execute("""
                SELECT p.id, p.name_uz, COUNT(a.id) AS stock_count
                FROM products p
                LEFT JOIN accounts a ON a.product_id = p.id AND a.status = 'available'
                WHERE p.is_active = 1
                GROUP BY p.id
                HAVING stock_count < 5
                ORDER BY stock_count ASC
            """)
            low_stock = [dict(r) for r in await cursor.fetchall()]

            # Kutayotgan almashtirish so'rovlari
            cursor = await db.execute("""
                SELECT COUNT(*) AS pending_replacements
                FROM replacements
                WHERE status = 'pending'
            """)
            repl_row = dict(await cursor.fetchone())

            # Kutayotgan buyurtmalar
            cursor = await db.execute("""
                SELECT COUNT(*) AS pending_orders
                FROM orders
                WHERE status = 'pending_payment'
            """)
            pending_orders_row = dict(await cursor.fetchone())

        stats = {
            "today_revenue": today_row["today_revenue"],
            "today_profit": profit_row["today_profit"],
            "today_orders": today_row["today_orders"],
            "active_accounts": active_row["active_accounts"],
            "pending_replacements": repl_row["pending_replacements"],
            "pending_orders": pending_orders_row["pending_orders"],
        }

        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "admin": admin,
            "stats": stats,
            "last_orders": last_orders,
            "low_stock": low_stock,
        })

    except Exception:
        logger.exception("Dashboard yuklashda xato")
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "admin": admin,
            "stats": {},
            "last_orders": [],
            "low_stock": [],
            "error": "Ma'lumotlarni yuklashda xato yuz berdi",
        })
