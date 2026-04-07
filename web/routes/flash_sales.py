"""
Flash sale (vaqtinchalik chegirma) boshqaruvi
"""
import logging
import os

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from bot.db.database import get_db
from web.auth import get_current_admin, require_auth

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")
)


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

            cursor2 = await db.execute(
                "SELECT id, name_uz FROM products WHERE is_active = 1 ORDER BY name_uz"
            )
            products = [dict(r) for r in await cursor2.fetchall()]

        return templates.TemplateResponse(request, "flash_sales.html", {
            "admin": admin,
            "flash_sales": flash_sales,
            "products": products,
        })
    except Exception:
        logger.exception("Flash sale ro'yxatini yuklashda xato")
        return templates.TemplateResponse(request, "flash_sales.html", {
            "admin": admin,
            "flash_sales": [],
            "products": [],
            "error": "Xato yuz berdi",
        })


@router.post("/add")
async def flash_sales_add(
    request: Request,
    product_id: int = Form(...),
    discount_percent: int = Form(...),
    starts_at: str = Form(...),
    ends_at: str = Form(...),
):
    redirect = require_auth(request)
    if redirect:
        return redirect

    try:
        async with get_db() as db:
            await db.execute("""
                INSERT INTO flash_sales (product_id, discount_percent, starts_at, ends_at)
                VALUES (?, ?, ?, ?)
            """, (product_id, discount_percent, starts_at, ends_at))
            await db.commit()
        return RedirectResponse("/flash-sales?success=1", status_code=302)
    except Exception:
        logger.exception("Flash sale qo'shishda xato")
        return RedirectResponse("/flash-sales?error=1", status_code=302)


@router.post("/{sale_id}/toggle")
async def flash_sales_toggle(request: Request, sale_id: int):
    redirect = require_auth(request)
    if redirect:
        return redirect

    try:
        async with get_db() as db:
            await db.execute(
                "UPDATE flash_sales SET is_active = CASE WHEN is_active = 1 THEN 0 ELSE 1 END WHERE id = ?",
                (sale_id,)
            )
            await db.commit()
        return RedirectResponse("/flash-sales?success=toggled", status_code=302)
    except Exception:
        logger.exception("Flash sale holatini o'zgartirishda xato")
        return RedirectResponse("/flash-sales?error=1", status_code=302)


@router.post("/{sale_id}/delete")
async def flash_sales_delete(request: Request, sale_id: int):
    redirect = require_auth(request)
    if redirect:
        return redirect

    try:
        async with get_db() as db:
            await db.execute("DELETE FROM flash_sales WHERE id = ?", (sale_id,))
            await db.commit()
        return RedirectResponse("/flash-sales?success=deleted", status_code=302)
    except Exception:
        logger.exception("Flash sale o'chirishda xato")
        return RedirectResponse("/flash-sales?error=1", status_code=302)
