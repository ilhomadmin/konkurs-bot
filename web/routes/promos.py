"""
Promo kodlar boshqaruvi
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
async def promos_list(request: Request):
    redirect = require_auth(request)
    if redirect:
        return redirect

    admin = get_current_admin(request)
    try:
        async with get_db() as db:
            cursor = await db.execute("""
                SELECT * FROM promo_codes
                ORDER BY created_at DESC
            """)
            promos = [dict(r) for r in await cursor.fetchall()]

        return templates.TemplateResponse(request, "promos.html", {
            "admin": admin,
            "promos": promos,
        })
    except Exception:
        logger.exception("Promo kodlar ro'yxatini yuklashda xato")
        return templates.TemplateResponse(request, "promos.html", {
            "admin": admin,
            "promos": [],
            "error": "Xato yuz berdi",
        })


@router.post("/add")
async def promos_add(
    request: Request,
    code: str = Form(...),
    discount_percent: int = Form(...),
    max_uses: int = Form(-1),
    valid_from: str = Form(""),
    valid_until: str = Form(""),
):
    redirect = require_auth(request)
    if redirect:
        return redirect

    try:
        async with get_db() as db:
            await db.execute("""
                INSERT INTO promo_codes (code, discount_percent, max_uses, valid_from, valid_until)
                VALUES (?, ?, ?, ?, ?)
            """, (
                code.strip().upper(),
                discount_percent,
                max_uses,
                valid_from or None,
                valid_until or None,
            ))
            await db.commit()
        return RedirectResponse("/promos?success=1", status_code=302)
    except Exception:
        logger.exception("Promo kod qo'shishda xato")
        return RedirectResponse("/promos?error=1", status_code=302)


@router.post("/{promo_id}/toggle")
async def promos_toggle(request: Request, promo_id: int):
    redirect = require_auth(request)
    if redirect:
        return redirect

    try:
        async with get_db() as db:
            await db.execute(
                "UPDATE promo_codes SET is_active = CASE WHEN is_active = 1 THEN 0 ELSE 1 END WHERE id = ?",
                (promo_id,)
            )
            await db.commit()
        return RedirectResponse("/promos?success=toggled", status_code=302)
    except Exception:
        logger.exception("Promo kod holatini o'zgartirishda xato")
        return RedirectResponse("/promos?error=1", status_code=302)
