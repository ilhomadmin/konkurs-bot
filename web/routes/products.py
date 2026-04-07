"""
Mahsulotlar (obuna turlari) CRUD
"""
import logging
import os
from typing import Optional

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
                       c.name_uz AS category_name,
                       COUNT(CASE WHEN a.status = 'available' THEN 1 END) AS stock_available,
                       COUNT(CASE WHEN a.status = 'sold' THEN 1 END) AS stock_sold
                FROM products p
                LEFT JOIN categories c ON c.id = p.category_id
                LEFT JOIN accounts a ON a.product_id = p.id
                GROUP BY p.id
                ORDER BY p.sort_order, p.id
            """)
            products = [dict(r) for r in await cursor.fetchall()]

            cursor2 = await db.execute("SELECT * FROM categories WHERE is_active = 1 ORDER BY sort_order, id")
            categories = [dict(r) for r in await cursor2.fetchall()]

        return templates.TemplateResponse(request, "products.html", {
            "admin": admin,
            "products": products,
            "categories": categories,
        })
    except Exception:
        logger.exception("Mahsulotlar ro'yxatini yuklashda xato")
        return templates.TemplateResponse(request, "products.html", {
            "admin": admin,
            "products": [],
            "categories": [],
            "error": "Xato yuz berdi",
        })


@router.get("/add")
async def products_add_form(request: Request):
    redirect = require_auth(request)
    if redirect:
        return redirect

    admin = get_current_admin(request)
    try:
        async with get_db() as db:
            cursor = await db.execute("SELECT * FROM categories WHERE is_active = 1 ORDER BY sort_order, id")
            categories = [dict(r) for r in await cursor.fetchall()]

        return templates.TemplateResponse(request, "product_form.html", {
            "admin": admin,
            "categories": categories,
            "product": None,
        })
    except Exception:
        logger.exception("Mahsulot formasini yuklashda xato")
        return RedirectResponse("/products", status_code=302)


@router.post("/add")
async def products_add_submit(
    request: Request,
    name_uz: str = Form(...),
    name_ru: str = Form(...),
    duration_text_uz: str = Form(""),
    duration_text_ru: str = Form(""),
    price: int = Form(0),
    cost_price: int = Form(0),
    has_warranty: str = Form("0"),
    warranty_days: int = Form(0),
    description_uz: str = Form(""),
    description_ru: str = Form(""),
    video_keyword: str = Form(""),
    category_id: str = Form(""),
    sort_order: int = Form(0),
):
    redirect = require_auth(request)
    if redirect:
        return redirect

    try:
        cat_id = int(category_id) if category_id.strip() else None
        async with get_db() as db:
            await db.execute("""
                INSERT INTO products
                    (category_id, name_uz, name_ru, duration_text_uz, duration_text_ru,
                     price, cost_price, has_warranty, warranty_days,
                     description_uz, description_ru, video_keyword, sort_order)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cat_id, name_uz, name_ru, duration_text_uz, duration_text_ru,
                price, cost_price, 1 if has_warranty == "1" else 0, warranty_days,
                description_uz or None, description_ru or None,
                video_keyword or None, sort_order,
            ))
            await db.commit()

        return RedirectResponse("/products?success=1", status_code=302)
    except Exception:
        logger.exception("Mahsulot qo'shishda xato")
        return RedirectResponse("/products/add?error=1", status_code=302)


@router.get("/{product_id}")
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
                return RedirectResponse("/products?error=not_found", status_code=302)
            product = dict(row)

            cursor2 = await db.execute("SELECT * FROM categories ORDER BY sort_order, id")
            categories = [dict(r) for r in await cursor2.fetchall()]

        return templates.TemplateResponse(request, "product_form.html", {
            "admin": admin,
            "product": product,
            "categories": categories,
        })
    except Exception:
        logger.exception("Mahsulot tahrirlash formasini yuklashda xato")
        return RedirectResponse("/products", status_code=302)


@router.post("/{product_id}")
async def products_edit_submit(
    request: Request,
    product_id: int,
    name_uz: str = Form(...),
    name_ru: str = Form(...),
    duration_text_uz: str = Form(""),
    duration_text_ru: str = Form(""),
    price: int = Form(0),
    cost_price: int = Form(0),
    has_warranty: str = Form("0"),
    warranty_days: int = Form(0),
    description_uz: str = Form(""),
    description_ru: str = Form(""),
    video_keyword: str = Form(""),
    category_id: str = Form(""),
    sort_order: int = Form(0),
):
    redirect = require_auth(request)
    if redirect:
        return redirect

    try:
        cat_id = int(category_id) if category_id.strip() else None
        async with get_db() as db:
            await db.execute("""
                UPDATE products
                SET category_id = ?, name_uz = ?, name_ru = ?,
                    duration_text_uz = ?, duration_text_ru = ?,
                    price = ?, cost_price = ?,
                    has_warranty = ?, warranty_days = ?,
                    description_uz = ?, description_ru = ?,
                    video_keyword = ?, sort_order = ?
                WHERE id = ?
            """, (
                cat_id, name_uz, name_ru, duration_text_uz, duration_text_ru,
                price, cost_price, 1 if has_warranty == "1" else 0, warranty_days,
                description_uz or None, description_ru or None,
                video_keyword or None, sort_order, product_id,
            ))
            await db.commit()

        return RedirectResponse(f"/products/{product_id}?success=1", status_code=302)
    except Exception:
        logger.exception("Mahsulot yangilashda xato")
        return RedirectResponse(f"/products/{product_id}?error=1", status_code=302)


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
        return RedirectResponse("/products?success=toggled", status_code=302)
    except Exception:
        logger.exception("Mahsulot holatini o'zgartirishda xato")
        return RedirectResponse("/products?error=1", status_code=302)


@router.post("/{product_id}/delete")
async def products_delete(request: Request, product_id: int):
    redirect = require_auth(request)
    if redirect:
        return redirect

    try:
        async with get_db() as db:
            await db.execute("DELETE FROM products WHERE id = ?", (product_id,))
            await db.commit()
        return RedirectResponse("/products?success=deleted", status_code=302)
    except Exception:
        logger.exception("Mahsulot o'chirishda xato")
        return RedirectResponse("/products?error=1", status_code=302)
