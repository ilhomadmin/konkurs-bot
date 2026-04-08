"""
Bot sozlamalari boshqaruvi
"""
import logging
import os
from collections import defaultdict

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
async def settings_list(request: Request):
    redirect = require_auth(request)
    if redirect:
        return redirect

    admin = get_current_admin(request)
    try:
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT * FROM settings ORDER BY category, id"
            )
            all_settings = [dict(r) for r in await cursor.fetchall()]

        grouped: dict = defaultdict(list)
        for s in all_settings:
            grouped[s["category"]].append(s)

        categories = list(grouped.keys())

        return templates.TemplateResponse(request, "settings.html", {
            "admin": admin,
            "categories": categories,
            "settings": all_settings,
        })
    except Exception:
        logger.exception("Sozlamalarni yuklashda xato")
        return templates.TemplateResponse(request, "settings.html", {
            "admin": admin,
            "categories": [],
            "settings": [],
            "error": "Sozlamalarni yuklashda xato yuz berdi",
        })


@router.post("/clear-cache")
async def settings_clear_cache(request: Request):
    redirect = require_auth(request)
    if redirect:
        return redirect

    try:
        from bot.db.models_products import invalidate_settings_cache
        invalidate_settings_cache()
    except Exception:
        logger.exception("Kesh tozalashda xato")
    return RedirectResponse("/settings?success=Kesh+muvaffaqiyatli+tozalandi", status_code=302)


@router.post("/{key}")
async def settings_update_by_key(
    request: Request,
    key: str,
    value: str = Form(...),
):
    redirect = require_auth(request)
    if redirect:
        return redirect

    try:
        async with get_db() as db:
            await db.execute("""
                UPDATE settings
                SET value = ?, updated_at = CURRENT_TIMESTAMP
                WHERE key = ?
            """, (value.strip(), key.strip()))
            await db.commit()
        return RedirectResponse("/settings?success=Saqlandi", status_code=302)
    except Exception:
        logger.exception("Sozlama yangilashda xato: %s", key)
        return RedirectResponse("/settings?error=Xato+yuz+berdi", status_code=302)
