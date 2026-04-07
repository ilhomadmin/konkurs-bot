"""
Foydalanuvchi sharhlari boshqaruvi
"""
import logging
import os

from fastapi import APIRouter, Request
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
async def reviews_list(request: Request):
    redirect = require_auth(request)
    if redirect:
        return redirect

    admin = get_current_admin(request)
    product_filter = request.query_params.get("product_id", "")
    visible_filter = request.query_params.get("visible", "")

    try:
        async with get_db() as db:
            conditions = []
            params = []
            if product_filter:
                conditions.append("r.product_id = ?")
                params.append(int(product_filter))
            if visible_filter != "":
                conditions.append("r.is_visible = ?")
                params.append(1 if visible_filter == "1" else 0)

            where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

            cursor = await db.execute(f"""
                SELECT r.*,
                       u.full_name, u.username, u.telegram_id,
                       p.name_uz AS product_name
                FROM reviews r
                JOIN users u ON u.id = r.user_id
                JOIN products p ON p.id = r.product_id
                {where}
                ORDER BY r.created_at DESC
                LIMIT 200
            """, params)
            reviews = [dict(r) for r in await cursor.fetchall()]

            cursor2 = await db.execute("SELECT id, name_uz FROM products ORDER BY name_uz")
            products = [dict(r) for r in await cursor2.fetchall()]

        return templates.TemplateResponse(request, "reviews.html", {
            "admin": admin,
            "reviews": reviews,
            "products": products,
            "filter_product_id": product_filter,
            "filter_visible": visible_filter,
        })
    except Exception:
        logger.exception("Sharhlar ro'yxatini yuklashda xato")
        return templates.TemplateResponse(request, "reviews.html", {
            "admin": admin,
            "reviews": [],
            "products": [],
            "filter_product_id": "",
            "filter_visible": "",
            "error": "Xato yuz berdi",
        })


@router.post("/{review_id}/toggle")
async def reviews_toggle(request: Request, review_id: int):
    redirect = require_auth(request)
    if redirect:
        return redirect

    try:
        async with get_db() as db:
            await db.execute(
                "UPDATE reviews SET is_visible = CASE WHEN is_visible = 1 THEN 0 ELSE 1 END WHERE id = ?",
                (review_id,)
            )
            await db.commit()
        return RedirectResponse("/reviews?success=toggled", status_code=302)
    except Exception:
        logger.exception("Sharh holatini o'zgartirishda xato")
        return RedirectResponse("/reviews?error=1", status_code=302)


@router.post("/{review_id}/delete")
async def reviews_delete(request: Request, review_id: int):
    redirect = require_auth(request)
    if redirect:
        return redirect

    try:
        async with get_db() as db:
            await db.execute("DELETE FROM reviews WHERE id = ?", (review_id,))
            await db.commit()
        return RedirectResponse("/reviews?success=deleted", status_code=302)
    except Exception:
        logger.exception("Sharh o'chirishda xato")
        return RedirectResponse("/reviews?error=1", status_code=302)
