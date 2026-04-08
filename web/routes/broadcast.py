"""
Xabar tarqatish (broadcast) — barcha foydalanuvchilarga yoki filtr bo'yicha
"""
import logging
import os

import httpx
from fastapi import APIRouter, Form, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from bot.config import BOT_TOKEN
from bot.db.database import get_db
from web.auth import get_current_admin, require_auth

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")
)

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"


@router.get("/")
async def broadcast_form(request: Request):
    redirect = require_auth(request)
    if redirect:
        return redirect

    admin = get_current_admin(request)
    try:
        async with get_db() as db:
            cursor = await db.execute("SELECT COUNT(*) AS cnt FROM users")
            row = await cursor.fetchone()
            user_count = row["cnt"] if row else 0

        return templates.TemplateResponse(request, "broadcast.html", {
            "admin": admin,
            "user_count": user_count,
        })
    except Exception:
        logger.exception("Broadcast formasini yuklashda xato")
        return templates.TemplateResponse(request, "broadcast.html", {
            "admin": admin,
            "user_count": 0,
            "error": "Xato yuz berdi",
        })


@router.post("/send")
async def broadcast_send(
    request: Request,
    message_uz: str = Form(...),
    message_ru: str = Form(""),
    target: str = Form("all"),
):
    redirect = require_auth(request)
    if redirect:
        return redirect

    try:
        async with get_db() as db:
            if target == "vip_only":
                cursor = await db.execute(
                    "SELECT telegram_id, language FROM users WHERE vip_level != 'standard'"
                )
            elif target == "active_30d":
                cursor = await db.execute("""
                    SELECT DISTINCT u.telegram_id, u.language FROM users u
                    JOIN orders o ON o.user_id = u.id
                    WHERE o.created_at >= datetime('now', '-30 days')
                """)
            else:
                cursor = await db.execute("SELECT telegram_id, language FROM users")
            users = await cursor.fetchall()

        sent = 0
        failed = 0

        async with httpx.AsyncClient(timeout=30) as client:
            for user in users:
                lang = user["language"] if user["language"] in ("uz", "ru") else "uz"
                text = message_ru if (lang == "ru" and message_ru) else message_uz
                if not text:
                    continue
                try:
                    resp = await client.post(
                        f"{TELEGRAM_API}/sendMessage",
                        json={
                            "chat_id": user["telegram_id"],
                            "text": text,
                            "parse_mode": "HTML",
                        },
                    )
                    if resp.status_code == 200 and resp.json().get("ok"):
                        sent += 1
                    else:
                        failed += 1
                except Exception:
                    failed += 1

        return RedirectResponse(
            f"/broadcast?success=1&sent={sent}&failed={failed}",
            status_code=302,
        )
    except Exception:
        logger.exception("Broadcast yuborishda xato")
        return RedirectResponse("/broadcast?error=1", status_code=302)
