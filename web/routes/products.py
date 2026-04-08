"""
Mahsulotlar CRUD — 2-daraja: Mahsulotlar → Akkauntlar
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
async def products_list(request: Request):
    redirect = require_auth(request)
    if redirect:
        return redirect

    admin = get_current_admin(request)
    try:
        async with get_db() as db:
            cursor = await db.execute("""
                SELECT p.*,
                       COUNT(CASE WHEN a.status = 'available' THEN 1 END) AS stock_available,
                       COUNT(CASE WHEN a.status = 'sold' THEN 1 END) AS stock_sold,
                       COUNT(a.id) AS stock_total
                FROM products p
                LEFT JOIN accounts a ON a.product_id = p.id
                GROUP BY p.id
                ORDER BY p.sort_order, p.id
            """)
            products = [dict(r) for r in await cursor.fetchall()]

        return templates.TemplateResponse(request, "products.html", {
            "admin": admin,
            "products": products,
        })
    except Exception:
        logger.exception("Mahsulotlar ro'yxatini yuklashda xato")
        return templates.TemplateResponse(request, "products.html", {
            "admin": admin,
            "products": [],
            "error": "Xato yuz berdi",
        })


@router.get("/add")
async def products_add_form(request: Request):
    redirect = require_auth(request)
    if redirect:
        return redirect

    admin = get_current_admin(request)
    return templates.TemplateResponse(request, "product_form.html", {
        "admin": admin,
        "product": None,
    })


@router.post("/add")
async def products_add_submit(
    request: Request,
    name_uz: str = Form(...),
    name_ru: str = Form(""),
    price: int = Form(0),
    cost_price: int = Form(0),
    description_uz: str = Form(""),
    description_ru: str = Form(""),
    has_warranty: str = Form("0"),
    warranty_days: int = Form(0),
    video_keyword: str = Form(""),
    is_active: str = Form("1"),
):
    redirect = require_auth(request)
    if redirect:
        return redirect

    try:
        async with get_db() as db:
            await db.execute("""
                INSERT INTO products
                    (name_uz, name_ru, price, cost_price,
                     description_uz, description_ru,
                     has_warranty, warranty_days, video_keyword, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                name_uz.strip(), name_ru.strip() or None,
                price, cost_price,
                description_uz.strip() or None, description_ru.strip() or None,
                1 if has_warranty in ("1", "on") else 0, warranty_days,
                video_keyword.strip() or None,
                1 if is_active in ("1", "on") else 0,
            ))
            await db.commit()

        return RedirectResponse("/products?success=Mahsulot+qo%27shildi", status_code=302)
    except Exception:
        logger.exception("Mahsulot qo'shishda xato")
        return templates.TemplateResponse(request, "product_form.html", {
            "admin": get_current_admin(request),
            "product": None,
            "error": "Mahsulot qo'shishda xato yuz berdi",
        })


@router.get("/edit/{product_id}")
async def products_edit_form(request: Request, product_id: int):
    redirect = require_auth(request)
    if redirect:
        return redirect

    admin = get_current_admin(request)
    try:
        async with get_db() as db:
            cursor = await db.execute("SELECT * FROM products WHERE id = ?", (product_id,))
            row = await cursor.fetchone()
            if not row:
                return RedirectResponse("/products?error=Mahsulot+topilmadi", status_code=302)
            product = dict(row)

        return templates.TemplateResponse(request, "product_form.html", {
            "admin": admin,
            "product": product,
        })
    except Exception:
        logger.exception("Mahsulot tahrirlash formasini yuklashda xato")
        return RedirectResponse("/products", status_code=302)


@router.post("/edit/{product_id}")
async def products_edit_submit(
    request: Request,
    product_id: int,
    name_uz: str = Form(...),
    name_ru: str = Form(""),
    price: int = Form(0),
    cost_price: int = Form(0),
    description_uz: str = Form(""),
    description_ru: str = Form(""),
    has_warranty: str = Form("0"),
    warranty_days: int = Form(0),
    video_keyword: str = Form(""),
    is_active: str = Form("1"),
):
    redirect = require_auth(request)
    if redirect:
        return redirect

    try:
        async with get_db() as db:
            await db.execute("""
                UPDATE products
                SET name_uz = ?, name_ru = ?, price = ?, cost_price = ?,
                    description_uz = ?, description_ru = ?,
                    has_warranty = ?, warranty_days = ?,
                    video_keyword = ?, is_active = ?
                WHERE id = ?
            """, (
                name_uz.strip(), name_ru.strip() or None,
                price, cost_price,
                description_uz.strip() or None, description_ru.strip() or None,
                1 if has_warranty in ("1", "on") else 0, warranty_days,
                video_keyword.strip() or None,
                1 if is_active in ("1", "on") else 0,
                product_id,
            ))
            await db.commit()

        return RedirectResponse(f"/products/{product_id}?success=Saqlandi", status_code=302)
    except Exception:
        logger.exception("Mahsulot yangilashda xato")
        return RedirectResponse(f"/products/edit/{product_id}?error=Xato+yuz+berdi", status_code=302)


@router.get("/{product_id}")
async def products_detail(request: Request, product_id: int):
    redirect = require_auth(request)
    if redirect:
        return redirect

    admin = get_current_admin(request)
    try:
        async with get_db() as db:
            cursor = await db.execute("SELECT * FROM products WHERE id = ?", (product_id,))
            row = await cursor.fetchone()
            if not row:
                return RedirectResponse("/products?error=Mahsulot+topilmadi", status_code=302)
            product = dict(row)

            cursor2 = await db.execute("""
                SELECT a.*,
                    CASE
                        WHEN a.expiry_date IS NOT NULL
                        THEN CAST((julianday(a.expiry_date) - julianday('now')) AS INTEGER)
                        ELSE NULL
                    END AS days_left
                FROM accounts a
                WHERE a.product_id = ?
                ORDER BY a.status, a.created_at DESC
            """, (product_id,))
            accounts = [dict(r) for r in await cursor2.fetchall()]

            # Stats
            available = sum(1 for a in accounts if a["status"] == "available")
            sold = sum(1 for a in accounts if a["status"] == "sold")

        return templates.TemplateResponse(request, "product_detail.html", {
            "admin": admin,
            "product": product,
            "accounts": accounts,
            "stats": {
                "available": available,
                "sold": sold,
                "total": len(accounts),
            },
        })
    except Exception:
        logger.exception("Mahsulot detail sahifasini yuklashda xato")
        return RedirectResponse("/products", status_code=302)


@router.post("/{product_id}/toggle")
async def products_toggle(request: Request, product_id: int):
    redirect = require_auth(request)
    if redirect:
        return redirect

    try:
        async with get_db() as db:
            await db.execute(
                "UPDATE products SET is_active = CASE WHEN is_active = 1 THEN 0 ELSE 1 END WHERE id = ?",
                (product_id,)
            )
            await db.commit()
        return RedirectResponse("/products?success=Holat+o%27zgartirildi", status_code=302)
    except Exception:
        logger.exception("Mahsulot holatini o'zgartirishda xato")
        return RedirectResponse("/products?error=Xato", status_code=302)


@router.post("/{product_id}/delete")
async def products_delete(request: Request, product_id: int):
    redirect = require_auth(request)
    if redirect:
        return redirect

    try:
        async with get_db() as db:
            await db.execute("DELETE FROM products WHERE id = ?", (product_id,))
            await db.commit()
        return RedirectResponse("/products?success=O%27chirildi", status_code=302)
    except Exception:
        logger.exception("Mahsulot o'chirishda xato")
        return RedirectResponse("/products?error=Xato", status_code=302)
