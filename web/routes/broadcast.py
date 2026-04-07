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
    message_text: str = Form(...),
    language_filter: str = Form(""),
    parse_mode: str = Form("HTML"),
):
    redirect = require_auth(request)
    if redirect:
        return redirect

    try:
        async with get_db() as db:
            if language_filter:
                cursor = await db.execute(
                    "SELECT telegram_id FROM users WHERE language = ?",
                    (language_filter,)
                )
            else:
                cursor = await db.execute("SELECT telegram_id FROM users")
            users = await cursor.fetchall()

        sent = 0
        failed = 0

        async with httpx.AsyncClient(timeout=30) as client:
            for user in users:
                try:
                    resp = await client.post(
                        f"{TELEGRAM_API}/sendMessage",
                        json={
                            "chat_id": user["telegram_id"],
                            "text": message_text,
                            "parse_mode": parse_mode,
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
