"""
Flash sale va to'g'ridan-to'g'ri sotish boshqaruvi
"""
import logging
import os

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

BOT_USERNAME = "aaarzonbot"


@router.get("/")
async def flash_sales_list(request: Request):
    redirect = require_auth(request)
    if redirect:
        return redirect

    admin = get_current_admin(request)
    try:
        async with get_db() as db:
            cursor = await db.execute("""
                SELECT fs.*, p.name_uz AS product_name
                FROM flash_sales fs
                JOIN products p ON p.id = fs.product_id
                ORDER BY fs.created_at DESC
            """)
            flash_sales = [dict(r) for r in await cursor.fetchall()]

            cursor2 = await db.execute("""
                SELECT p.id, p.name_uz, p.name_ru, p.price, p.duration_days,
                       COUNT(CASE WHEN a.status='available' THEN 1 END) AS stock
                FROM products p
                LEFT JOIN accounts a ON a.product_id = p.id
                WHERE p.is_active = 1
                GROUP BY p.id
                ORDER BY p.sort_order, p.name_uz
            """)
            products = [dict(r) for r in await cursor2.fetchall()]

        return templates.TemplateResponse(request, "flash_sales.html", {
            "admin": admin,
            "flash_sales": flash_sales,
            "products": products,
            "bot_username": BOT_USERNAME,
        })
    except Exception:
        logger.exception("Flash sale sahifasini yuklashda xato")
        return templates.TemplateResponse(request, "flash_sales.html", {
            "admin": admin,
            "flash_sales": [],
            "products": [],
            "bot_username": BOT_USERNAME,
            "error": "Xato yuz berdi",
        })


@router.post("/add")
async def flash_sales_add(
    request: Request,
    product_id: int = Form(...),
    discount_percent: int = Form(...),
    ends_at: str = Form(...),
):
    redirect = require_auth(request)
    if redirect:
        return redirect

    try:
        async with get_db() as db:
            await db.execute("""
                INSERT INTO flash_sales (product_id, discount_percent, starts_at, ends_at)
                VALUES (?, ?, datetime('now'), ?)
            """, (product_id, discount_percent, ends_at))
            await db.commit()
        return RedirectResponse("/flash-sales?success=Aksiya+yaratildi", status_code=302)
    except Exception:
        logger.exception("Flash sale qo'shishda xato")
        return RedirectResponse("/flash-sales?error=Xato+yuz+berdi", status_code=302)


@router.post("/direct-sell")
async def flash_sales_direct_sell(
    request: Request,
    product_id: int = Form(...),
    buyer_name: str = Form(""),
    buyer_phone: str = Form(""),
):
    """Bitta akkauntni to'g'ridan-to'g'ri sotilgan deb belgilash."""
    redirect = require_auth(request)
    if redirect:
        return JSONResponse({"ok": False, "error": "Tizimga kiring"}, status_code=401)

    try:
        async with get_db() as db:
            cursor = await db.execute("""
                SELECT id FROM accounts
                WHERE product_id = ? AND status = 'available'
                ORDER BY created_at ASC
                LIMIT 1
            """, (product_id,))
            row = await cursor.fetchone()
            if not row:
                return JSONResponse({"ok": False, "error": "Mavjud akkaunt yo'q"}, status_code=400)

            account_id = row["id"]
            note = f"Direct: {buyer_name.strip() or '—'} / {buyer_phone.strip() or '—'}"
            await db.execute("""
                UPDATE accounts
                SET status = 'sold', sold_at = datetime('now'), sold_via = 'direct_web'
                WHERE id = ?
            """, (account_id,))
            await db.commit()

        return JSONResponse({"ok": True, "account_id": account_id})
    except Exception:
        logger.exception("Direct sell xato")
        return JSONResponse({"ok": False, "error": "Server xatosi"}, status_code=500)


@router.post("/{sale_id}/toggle")
async def flash_sales_toggle(request: Request, sale_id: int):
    redirect = require_auth(request)
    if redirect:
        return redirect

    try:
        async with get_db() as db:
            await db.execute(
                "UPDATE flash_sales SET is_active=CASE WHEN is_active=1 THEN 0 ELSE 1 END WHERE id=?",
                (sale_id,)
            )
            await db.commit()
        return RedirectResponse("/flash-sales?success=Holat+o%27zgartirildi", status_code=302)
    except Exception:
        logger.exception("Flash sale toggle xato")
        return RedirectResponse("/flash-sales?error=Xato", status_code=302)


@router.post("/{sale_id}/delete")
async def flash_sales_delete(request: Request, sale_id: int):
    redirect = require_auth(request)
    if redirect:
        return redirect

    try:
        async with get_db() as db:
            await db.execute("DELETE FROM flash_sales WHERE id=?", (sale_id,))
            await db.commit()
        return RedirectResponse("/flash-sales?success=O%27chirildi", status_code=302)
    except Exception:
        logger.exception("Flash sale o'chirish xato")
        return RedirectResponse("/flash-sales?error=Xato", status_code=302)
