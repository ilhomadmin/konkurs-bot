"""
Admin foydalanuvchilar boshqaruvi
"""
import logging
import os

from fastapi import APIRouter, Form, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from bot.db.database import get_db
from web.auth import get_current_admin, hash_password, require_auth, require_role

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")
)

ROLES = ["superadmin", "admin", "operator", "finance"]


@router.get("/")
async def admins_list(request: Request):
    redirect = require_role(request, ["superadmin", "admin"])
    if redirect:
        return redirect

    admin = get_current_admin(request)
    try:
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT * FROM admin_roles ORDER BY created_at"
            )
            admins = [dict(r) for r in await cursor.fetchall()]

        return templates.TemplateResponse(request, "admins.html", {
            "admin": admin,
            "admins": admins,
            "roles": ROLES,
        })
    except Exception:
        logger.exception("Adminlar ro'yxatini yuklashda xato")
        return templates.TemplateResponse(request, "admins.html", {
            "admin": admin,
            "admins": [],
            "roles": ROLES,
            "error": "Xato yuz berdi",
        })


@router.post("/find-by-username")
async def admins_find_by_username(
    request: Request,
    username: str = Form(...),
):
    """Username bo'yicha users jadvalidan qidirish."""
    redirect = require_role(request, ["superadmin"])
    if redirect:
        return JSONResponse({"found": False, "message": "Ruxsat yo'q"}, status_code=403)

    username = username.strip().lstrip("@")
    if not username:
        return JSONResponse({"found": False, "message": "Username bo'sh"})

    try:
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT telegram_id, username, full_name FROM users WHERE username = ? COLLATE NOCASE LIMIT 1",
                (username,)
            )
            row = await cursor.fetchone()

        if row:
            return JSONResponse({
                "found": True,
                "telegram_id": row["telegram_id"],
                "username": row["username"] or "",
                "full_name": row["full_name"] or "",
            })
        else:
            return JSONResponse({
                "found": False,
                "message": "Bu foydalanuvchi botdan foydalanmagan"
            })
    except Exception:
        logger.exception("Username qidiruvda xato")
        return JSONResponse({"found": False, "message": "Xato yuz berdi"})


@router.post("/add")
async def admins_add(
    request: Request,
    telegram_id: str = Form(...),
    username: str = Form(""),
    full_name: str = Form(""),
    role: str = Form("operator"),
    password: str = Form(""),
):
    redirect = require_role(request, ["superadmin"])
    if redirect:
        return redirect

    try:
        tid = int(telegram_id.strip())
        password_hash = hash_password(password) if password.strip() else None
        role = role if role in ROLES else "operator"

        async with get_db() as db:
            await db.execute("""
                INSERT OR REPLACE INTO admin_roles
                    (telegram_id, username, full_name, role, password_hash, is_active)
                VALUES (?, ?, ?, ?, ?, 1)
            """, (
                tid,
                username.strip() or None,
                full_name.strip() or None,
                role,
                password_hash,
            ))
            await db.commit()
        return RedirectResponse("/admins?success=1", status_code=302)
    except ValueError:
        return RedirectResponse("/admins?error=invalid_id", status_code=302)
    except Exception:
        logger.exception("Admin qo'shishda xato")
        return RedirectResponse("/admins?error=1", status_code=302)


@router.post("/{admin_id}/update")
async def admins_update(
    request: Request,
    admin_id: int,
    role: str = Form(...),
    is_active: str = Form("1"),
    permissions: str = Form(""),
):
    redirect = require_role(request, ["superadmin"])
    if redirect:
        return redirect

    try:
        role = role if role in ROLES else "operator"
        async with get_db() as db:
            await db.execute("""
                UPDATE admin_roles
                SET role = ?, is_active = ?, permissions = ?
                WHERE id = ?
            """, (
                role,
                1 if is_active == "1" else 0,
                permissions.strip() or None,
                admin_id,
            ))
            await db.commit()
        return RedirectResponse("/admins?success=updated", status_code=302)
    except Exception:
        logger.exception("Admin yangilashda xato")
        return RedirectResponse("/admins?error=1", status_code=302)


@router.post("/{admin_id}/password")
async def admins_change_password(
    request: Request,
    admin_id: int,
    password: str = Form(...),
):
    redirect = require_role(request, ["superadmin", "admin"])
    if redirect:
        return redirect

    try:
        if not password.strip():
            return RedirectResponse("/admins?error=Parol+bo%27sh", status_code=302)

        password_hash = hash_password(password.strip())
        async with get_db() as db:
            await db.execute(
                "UPDATE admin_roles SET password_hash = ? WHERE telegram_id = ?",
                (password_hash, admin_id)
            )
            await db.commit()
        return RedirectResponse("/admins?success=Parol+o%27zgartirildi", status_code=302)
    except Exception:
        logger.exception("Admin paroli o'zgartirishda xato")
        return RedirectResponse("/admins?error=Xato", status_code=302)


@router.post("/{admin_id}/role")
async def admins_change_role(
    request: Request,
    admin_id: int,
    role: str = Form(...),
):
    redirect = require_role(request, ["superadmin", "admin"])
    if redirect:
        return redirect

    try:
        role = role if role in ROLES else "operator"
        async with get_db() as db:
            await db.execute(
                "UPDATE admin_roles SET role = ? WHERE telegram_id = ?",
                (role, admin_id)
            )
            await db.commit()
        return RedirectResponse("/admins?success=Rol+o%27zgartirildi", status_code=302)
    except Exception:
        logger.exception("Admin roli o'zgartirishda xato")
        return RedirectResponse("/admins?error=Xato", status_code=302)


@router.post("/{admin_id}/toggle")
async def admins_toggle(request: Request, admin_id: int):
    redirect = require_role(request, ["superadmin", "admin"])
    if redirect:
        return redirect

    try:
        async with get_db() as db:
            await db.execute(
                "UPDATE admin_roles SET is_active = CASE WHEN is_active = 1 THEN 0 ELSE 1 END WHERE telegram_id = ?",
                (admin_id,)
            )
            await db.commit()
        return RedirectResponse("/admins?success=Holat+o%27zgartirildi", status_code=302)
    except Exception:
        logger.exception("Admin toggle xato")
        return RedirectResponse("/admins?error=Xato", status_code=302)


@router.post("/{admin_id}/delete")
async def admins_delete(request: Request, admin_id: int):
    redirect = require_role(request, ["superadmin"])
    if redirect:
        return redirect

    try:
        async with get_db() as db:
            await db.execute("DELETE FROM admin_roles WHERE telegram_id = ?", (admin_id,))
            await db.commit()
        return RedirectResponse("/admins?success=O%27chirildi", status_code=302)
    except Exception:
        logger.exception("Admin o'chirishda xato")
        return RedirectResponse("/admins?error=Xato", status_code=302)


@router.post("/{admin_id}/deactivate")
async def admins_deactivate(request: Request, admin_id: int):
    redirect = require_role(request, ["superadmin"])
    if redirect:
        return redirect

    try:
        async with get_db() as db:
            await db.execute(
                "UPDATE admin_roles SET is_active = 0 WHERE id = ?",
                (admin_id,)
            )
            await db.commit()
        return RedirectResponse("/admins?success=deactivated", status_code=302)
    except Exception:
        logger.exception("Admin deaktivatsiyasida xato")
        return RedirectResponse("/admins?error=1", status_code=302)
