"""
Moliya boshqaruvi — daromad, xarajat, foyda statistikasi
"""
import logging
import os
from datetime import date, timedelta

from fastapi import APIRouter, Form, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from bot.db.database import get_db
from web.auth import get_current_admin, require_auth

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")
)


@router.get("/")
async def finance_dashboard(request: Request):
    redirect = require_auth(request)
    if redirect:
        return redirect

    admin = get_current_admin(request)
    period = request.query_params.get("period", "30")  # kunlar soni

    try:
        days = int(period)
    except ValueError:
        days = 30

    try:
        async with get_db() as db:
            # Jami daromad (tanlangan davr)
            cursor = await db.execute("""
                SELECT
                    COALESCE(SUM(total_amount - discount_amount), 0) AS total_revenue,
                    COUNT(id) AS total_orders
                FROM orders
                WHERE status IN ('confirmed', 'delivered')
                  AND DATE(created_at) >= DATE('now', ?)
            """, (f"-{days} days",))
            rev_row = dict(await cursor.fetchone())

            # Jami foyda
            cursor = await db.execute("""
                SELECT COALESCE(SUM(oi.unit_price * oi.quantity - oi.cost_price * oi.quantity), 0) AS gross_profit
                FROM order_items oi
                JOIN orders o ON o.id = oi.order_id
                WHERE o.status IN ('confirmed', 'delivered')
                  AND DATE(o.created_at) >= DATE('now', ?)
            """, (f"-{days} days",))
            profit_row = dict(await cursor.fetchone())

            # Jami xarajatlar
            cursor = await db.execute("""
                SELECT COALESCE(SUM(amount), 0) AS total_expenses
                FROM expenses
                WHERE DATE(date) >= DATE('now', ?)
            """, (f"-{days} days",))
            exp_row = dict(await cursor.fetchone())

            # So'nggi xarajatlar
            cursor = await db.execute("""
                SELECT * FROM expenses
                ORDER BY date DESC, created_at DESC
                LIMIT 50
            """)
            expenses = [dict(r) for r in await cursor.fetchall()]

            # Mahsulot bo'yicha statistika
            cursor = await db.execute("""
                SELECT p.name_uz AS product_name,
                       COUNT(oi.id) AS sold_count,
                       SUM(oi.unit_price * oi.quantity) AS revenue,
                       SUM((oi.unit_price - oi.cost_price) * oi.quantity) AS profit
                FROM order_items oi
                JOIN products p ON p.id = oi.product_id
                JOIN orders o ON o.id = oi.order_id
                WHERE o.status IN ('confirmed', 'delivered')
                  AND DATE(o.created_at) >= DATE('now', ?)
                GROUP BY p.id
                ORDER BY revenue DESC
                LIMIT 10
            """, (f"-{days} days",))
            product_stats = [dict(r) for r in await cursor.fetchall()]

        net_profit = profit_row["gross_profit"] - exp_row["total_expenses"]

        stats = {
            "total_revenue": rev_row["total_revenue"],
            "total_orders": rev_row["total_orders"],
            "gross_profit": profit_row["gross_profit"],
            "total_expenses": exp_row["total_expenses"],
            "net_profit": net_profit,
            "period_days": days,
        }

        return templates.TemplateResponse(request, "finance.html", {
            "admin": admin,
            "stats": stats,
            "expenses": expenses,
            "product_stats": product_stats,
            "period": str(days),
        })
    except Exception:
        logger.exception("Moliya dashboardini yuklashda xato")
        return templates.TemplateResponse("finance.html", {
            "request": request,
            "admin": admin,
            "stats": {},
            "expenses": [],
            "product_stats": [],
            "period": str(days),
            "error": "Xato yuz berdi",
        })


@router.post("/expense")
async def finance_add_expense(
    request: Request,
    expense_date: str = Form(...),
    category: str = Form(...),
    description: str = Form(""),
    amount: int = Form(...),
):
    redirect = require_auth(request)
    if redirect:
        return redirect

    admin = get_current_admin(request)
    admin_tid = admin.get("tid") if admin else None

    try:
        async with get_db() as db:
            await db.execute("""
                INSERT INTO expenses (date, category, description, amount, created_by)
                VALUES (?, ?, ?, ?, ?)
            """, (expense_date, category, description or None, amount, admin_tid))
            await db.commit()
        return RedirectResponse("/finance?success=expense_added", status_code=302)
    except Exception:
        logger.exception("Xarajat qo'shishda xato")
        return RedirectResponse("/finance?error=1", status_code=302)


@router.get("/api/chart")
async def finance_chart_data(request: Request):
    redirect = require_auth(request)
    if redirect:
        return redirect

    period = request.query_params.get("period", "30")
    try:
        days = int(period)
    except ValueError:
        days = 30

    try:
        async with get_db() as db:
            # Kunlik daromad ma'lumotlari
            cursor = await db.execute("""
                SELECT DATE(o.created_at) AS day,
                       COALESCE(SUM(o.total_amount - o.discount_amount), 0) AS revenue,
                       COALESCE(SUM(oi.unit_price * oi.quantity - oi.cost_price * oi.quantity), 0) AS profit
                FROM orders o
                LEFT JOIN order_items oi ON oi.order_id = o.id
                WHERE o.status IN ('confirmed', 'delivered')
                  AND DATE(o.created_at) >= DATE('now', ?)
                GROUP BY DATE(o.created_at)
                ORDER BY day ASC
            """, (f"-{days} days",))
            rows = [dict(r) for r in await cursor.fetchall()]

            # Kunlik xarajatlar
            cursor2 = await db.execute("""
                SELECT date AS day, COALESCE(SUM(amount), 0) AS expenses
                FROM expenses
                WHERE DATE(date) >= DATE('now', ?)
                GROUP BY date
                ORDER BY day ASC
            """, (f"-{days} days",))
            exp_rows = {r["day"]: r["expenses"] for r in await cursor2.fetchall()}

        # Barcha kunlarni to'ldirish
        today = date.today()
        all_days = [(today - timedelta(days=i)).isoformat() for i in range(days - 1, -1, -1)]
        revenue_map = {r["day"]: r["revenue"] for r in rows}
        profit_map = {r["day"]: r["profit"] for r in rows}

        chart_data = {
            "labels": all_days,
            "revenue": [revenue_map.get(d, 0) for d in all_days],
            "profit": [profit_map.get(d, 0) for d in all_days],
            "expenses": [exp_rows.get(d, 0) for d in all_days],
        }

        return JSONResponse(chart_data)
    except Exception:
        logger.exception("Chart ma'lumotlarini yuklashda xato")
        return JSONResponse({"error": "Xato yuz berdi"}, status_code=500)
