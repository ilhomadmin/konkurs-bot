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

CATEGORY_LABELS = {
    "payment": "To'lov sozlamalari",
    "marketing": "Marketing",
    "timing": "Vaqt sozlamalari",
    "inventory": "Stok boshqaruvi",
    "content": "Bot kontenti",
    "menu": "Menyu matnlari",
    "general": "Umumiy sozlamalar",
}


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

        # Kategoriya bo'yicha guruhlash
        grouped: dict = defaultdict(list)
        for s in all_settings:
            grouped[s["category"]].append(s)

        return templates.TemplateResponse(request, "settings.html", {
            "admin": admin,
            "grouped_settings": dict(grouped),
            "category_labels": CATEGORY_LABELS,
        })
    except Exception:
        logger.exception("Sozlamalarni yuklashda xato")
        return templates.TemplateResponse(request, "settings.html", {
            "admin": admin,
            "grouped_settings": {},
            "category_labels": CATEGORY_LABELS,
            "error": "Xato yuz berdi",
        })


@router.post("/update")
async def settings_update(
    request: Request,
    key: str = Form(...),
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
        return RedirectResponse("/settings?success=1", status_code=302)
    except Exception:
        logger.exception("Sozlama yangilashda xato")
        return RedirectResponse("/settings?error=1", status_code=302)


@router.post("/update-many")
async def settings_update_many(request: Request):
    """Bir vaqtda ko'p sozlamalarni yangilash (forma submit)"""
    redirect = require_auth(request)
    if redirect:
        return redirect

    try:
        form_data = await request.form()
        async with get_db() as db:
            for key, value in form_data.items():
                if key.startswith("_"):
                    continue
                await db.execute("""
                    UPDATE settings
                    SET value = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE key = ?
                """, (str(value).strip(), key.strip()))
            await db.commit()
        return RedirectResponse("/settings?success=1", status_code=302)
    except Exception:
        logger.exception("Ko'p sozlamalarni yangilashda xato")
        return RedirectResponse("/settings?error=1", status_code=302)
