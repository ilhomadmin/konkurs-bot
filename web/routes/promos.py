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
    discount_type: str = Form("percent"),
    discount_value: int = Form(0),
    max_uses: str = Form(""),
    expires_at: str = Form(""),
    min_order_amount: int = Form(0),
):
    redirect = require_auth(request)
    if redirect:
        return redirect

    try:
        max_uses_val = int(max_uses) if max_uses.strip() else -1
        discount_percent = discount_value if discount_type == "percent" else 0
        async with get_db() as db:
            await db.execute("""
                INSERT INTO promo_codes (code, discount_percent, max_uses, valid_until)
                VALUES (?, ?, ?, ?)
            """, (
                code.strip().upper(),
                discount_percent,
                max_uses_val,
                expires_at.strip() or None,
            ))
            await db.commit()
        return RedirectResponse("/promos?success=Promo+kod+qo%27shildi", status_code=302)
    except Exception:
        logger.exception("Promo kod qo'shishda xato")
        return RedirectResponse("/promos?error=Xato+yuz+berdi", status_code=302)


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
