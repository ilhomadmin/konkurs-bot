"""
Admin profil va parol o'zgartirish
"""
import logging
import os

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from bot.db.database import get_db
from web.auth import get_current_admin, hash_password, require_auth, verify_password

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")
)


@router.get("/")
async def profile_page(request: Request):
    redirect = require_auth(request)
    if redirect:
        return redirect

    admin = get_current_admin(request)
    try:
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT * FROM admin_roles WHERE telegram_id = ?",
                (admin["tid"],)
            )
            row = await cursor.fetchone()
            admin_info = dict(row) if row else {}

        success = request.query_params.get("success", "")
        error = request.query_params.get("error", "")

        return templates.TemplateResponse(request, "profile.html", {
            "admin": admin,
            "admin_info": admin_info,
            "success": success,
            "error": error,
        })
    except Exception:
        logger.exception("Profil sahifasini yuklashda xato")
        return templates.TemplateResponse(request, "profile.html", {
            "admin": admin,
            "admin_info": {},
            "error": "Profil ma'lumotlarini yuklashda xato",
        })


@router.post("/change-password")
async def profile_change_password(
    request: Request,
    old_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
):
    redirect = require_auth(request)
    if redirect:
        return redirect

    admin = get_current_admin(request)

    if new_password != confirm_password:
        return RedirectResponse("/profile?error=Yangi+parollar+mos+emas", status_code=302)

    if len(new_password) < 4:
        return RedirectResponse("/profile?error=Parol+kamida+4+ta+belgi+bo%27lishi+kerak", status_code=302)

    try:
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT password_hash FROM admin_roles WHERE telegram_id = ?",
                (admin["tid"],)
            )
            row = await cursor.fetchone()
            if not row or not row["password_hash"]:
                return RedirectResponse("/profile?error=Joriy+parol+topilmadi", status_code=302)

            if not verify_password(old_password, row["password_hash"]):
                return RedirectResponse("/profile?error=Eski+parol+noto%27g%27ri", status_code=302)

            new_hash = hash_password(new_password)
            await db.execute(
                "UPDATE admin_roles SET password_hash = ? WHERE telegram_id = ?",
                (new_hash, admin["tid"])
            )
            await db.commit()

        return RedirectResponse("/profile?success=Parol+muvaffaqiyatli+o%27zgartirildi", status_code=302)
    except Exception:
        logger.exception("Parol o'zgartirishda xato")
        return RedirectResponse("/profile?error=Xato+yuz+berdi", status_code=302)
