"""
To'plamlar (bundles) boshqaruvi
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
async def bundles_list(request: Request):
    redirect = require_auth(request)
    if redirect:
        return redirect

    admin = get_current_admin(request)
    try:
        async with get_db() as db:
            cursor = await db.execute("""
                SELECT b.*, COUNT(bi.id) AS item_count
                FROM bundles b
                LEFT JOIN bundle_items bi ON bi.bundle_id = b.id
                GROUP BY b.id
                ORDER BY b.created_at DESC
            """)
            bundles = [dict(r) for r in await cursor.fetchall()]

            cursor2 = await db.execute(
                "SELECT id, name_uz FROM products WHERE is_active = 1 ORDER BY name_uz"
            )
            products = [dict(r) for r in await cursor2.fetchall()]

        return templates.TemplateResponse(request, "bundles.html", {
            "admin": admin,
            "bundles": bundles,
            "products": products,
        })
    except Exception:
        logger.exception("To'plamlar ro'yxatini yuklashda xato")
        return templates.TemplateResponse(request, "bundles.html", {
            "admin": admin,
            "bundles": [],
            "products": [],
            "error": "Xato yuz berdi",
        })


@router.post("/add")
async def bundles_add(
    request: Request,
    name_uz: str = Form(...),
    name_ru: str = Form(...),
    description_uz: str = Form(""),
    description_ru: str = Form(""),
    discount_percent: int = Form(0),
    price: int = Form(0),
):
    redirect = require_auth(request)
    if redirect:
        return redirect

    try:
        async with get_db() as db:
            await db.execute("""
                INSERT INTO bundles (name_uz, name_ru, description_uz, description_ru, discount_percent, price)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                name_uz, name_ru,
                description_uz or None, description_ru or None,
                discount_percent, price,
            ))
            await db.commit()
        return RedirectResponse("/bundles?success=1", status_code=302)
    except Exception:
        logger.exception("To'plam qo'shishda xato")
        return RedirectResponse("/bundles?error=1", status_code=302)


@router.post("/{bundle_id}/add-item")
async def bundles_add_item(
    request: Request,
    bundle_id: int,
    product_id: int = Form(...),
    quantity: int = Form(1),
):
    redirect = require_auth(request)
    if redirect:
        return redirect

    try:
        async with get_db() as db:
            # To'plam mavjudligini tekshirish
            cursor = await db.execute("SELECT id FROM bundles WHERE id = ?", (bundle_id,))
            if not await cursor.fetchone():
                return RedirectResponse("/bundles?error=not_found", status_code=302)

            await db.execute("""
                INSERT INTO bundle_items (bundle_id, product_id, quantity)
                VALUES (?, ?, ?)
            """, (bundle_id, product_id, max(1, quantity)))
            await db.commit()
        return RedirectResponse(f"/bundles?success=item_added&bundle={bundle_id}", status_code=302)
    except Exception:
        logger.exception("To'plamga element qo'shishda xato")
        return RedirectResponse(f"/bundles?error=1", status_code=302)


@router.post("/{bundle_id}/toggle")
async def bundles_toggle(request: Request, bundle_id: int):
    redirect = require_auth(request)
    if redirect:
        return redirect

    try:
        async with get_db() as db:
            await db.execute(
                "UPDATE bundles SET is_active = CASE WHEN is_active = 1 THEN 0 ELSE 1 END WHERE id = ?",
                (bundle_id,)
            )
            await db.commit()
        return RedirectResponse("/bundles?success=toggled", status_code=302)
    except Exception:
        logger.exception("To'plam holatini o'zgartirishda xato")
        return RedirectResponse("/bundles?error=1", status_code=302)


@router.post("/{bundle_id}/delete")
async def bundles_delete(request: Request, bundle_id: int):
    redirect = require_auth(request)
    if redirect:
        return redirect

    try:
        async with get_db() as db:
            await db.execute("DELETE FROM bundles WHERE id = ?", (bundle_id,))
            await db.commit()
        return RedirectResponse("/bundles?success=deleted", status_code=302)
    except Exception:
        logger.exception("To'plam o'chirishda xato")
        return RedirectResponse("/bundles?error=1", status_code=302)
