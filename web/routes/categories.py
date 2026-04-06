"""
Kategoriyalar (turkumlar) CRUD
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
async def categories_list(request: Request):
    redirect = require_auth(request)
    if redirect:
        return redirect

    admin = get_current_admin(request)
    try:
        async with get_db() as db:
            cursor = await db.execute("""
                SELECT c.*,
                       COUNT(p.id) AS product_count
                FROM categories c
                LEFT JOIN products p ON p.category_id = c.id
                GROUP BY c.id
                ORDER BY c.sort_order, c.id
            """)
            categories = [dict(r) for r in await cursor.fetchall()]

        return templates.TemplateResponse("categories/list.html", {
            "request": request,
            "admin": admin,
            "categories": categories,
        })
    except Exception:
        logger.exception("Kategoriyalar ro'yxatini yuklashda xato")
        return templates.TemplateResponse("categories/list.html", {
            "request": request,
            "admin": admin,
            "categories": [],
            "error": "Xato yuz berdi",
        })


@router.post("/add")
async def categories_add(
    request: Request,
    name_uz: str = Form(...),
    name_ru: str = Form(...),
    description_uz: str = Form(""),
    description_ru: str = Form(""),
    video_keyword: str = Form(""),
    sort_order: int = Form(0),
):
    redirect = require_auth(request)
    if redirect:
        return redirect

    try:
        async with get_db() as db:
            await db.execute("""
                INSERT INTO categories (name_uz, name_ru, description_uz, description_ru, video_keyword, sort_order)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                name_uz, name_ru,
                description_uz or None, description_ru or None,
                video_keyword or None, sort_order,
            ))
            await db.commit()
        return RedirectResponse("/categories?success=1", status_code=302)
    except Exception:
        logger.exception("Kategoriya qo'shishda xato")
        return RedirectResponse("/categories?error=1", status_code=302)


@router.get("/{category_id}")
async def categories_edit_form(request: Request, category_id: int):
    redirect = require_auth(request)
    if redirect:
        return redirect

    admin = get_current_admin(request)
    try:
        async with get_db() as db:
            cursor = await db.execute("SELECT * FROM categories WHERE id = ?", (category_id,))
            row = await cursor.fetchone()
            if not row:
                return RedirectResponse("/categories?error=not_found", status_code=302)
            category = dict(row)

        return templates.TemplateResponse("categories/form.html", {
            "request": request,
            "admin": admin,
            "category": category,
        })
    except Exception:
        logger.exception("Kategoriya formasini yuklashda xato")
        return RedirectResponse("/categories", status_code=302)


@router.post("/{category_id}")
async def categories_edit_submit(
    request: Request,
    category_id: int,
    name_uz: str = Form(...),
    name_ru: str = Form(...),
    description_uz: str = Form(""),
    description_ru: str = Form(""),
    video_keyword: str = Form(""),
    sort_order: int = Form(0),
    is_active: str = Form("1"),
):
    redirect = require_auth(request)
    if redirect:
        return redirect

    try:
        async with get_db() as db:
            await db.execute("""
                UPDATE categories
                SET name_uz = ?, name_ru = ?, description_uz = ?, description_ru = ?,
                    video_keyword = ?, sort_order = ?, is_active = ?
                WHERE id = ?
            """, (
                name_uz, name_ru,
                description_uz or None, description_ru or None,
                video_keyword or None, sort_order,
                1 if is_active == "1" else 0,
                category_id,
            ))
            await db.commit()
        return RedirectResponse(f"/categories/{category_id}?success=1", status_code=302)
    except Exception:
        logger.exception("Kategoriya yangilashda xato")
        return RedirectResponse(f"/categories/{category_id}?error=1", status_code=302)


@router.post("/{category_id}/delete")
async def categories_delete(request: Request, category_id: int):
    redirect = require_auth(request)
    if redirect:
        return redirect

    try:
        async with get_db() as db:
            await db.execute("DELETE FROM categories WHERE id = ?", (category_id,))
            await db.commit()
        return RedirectResponse("/categories?success=deleted", status_code=302)
    except Exception:
        logger.exception("Kategoriya o'chirishda xato")
        return RedirectResponse("/categories?error=1", status_code=302)
