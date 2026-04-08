"""
To'g'ridan-to'g'ri sotuv (direct sale) — havola orqali akkaunt sotish
"""
import logging
import os
import secrets

from fastapi import APIRouter, Form, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from bot.db.database import get_db
from web.auth import get_current_admin, require_auth

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")
)


@router.get("/")
async def direct_sale_form(request: Request):
    redirect = require_auth(request)
    if redirect:
        return redirect

    admin = get_current_admin(request)
    product_id = request.query_params.get("product_id", "")
    raw_token = request.query_params.get("success_token", "")
    success_token = raw_token if raw_token else None

    try:
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT id, name_uz FROM products WHERE is_active = 1 ORDER BY name_uz"
            )
            products = [dict(r) for r in await cursor.fetchall()]

            available_account = None
            if product_id:
                cursor2 = await db.execute("""
                    SELECT a.*, p.name_uz AS product_name
                    FROM accounts a
                    LEFT JOIN products p ON p.id = a.product_id
                    WHERE a.product_id = ? AND a.status = 'available'
                    ORDER BY a.expiry_date ASC
                    LIMIT 1
                """, (int(product_id),))
                row = await cursor2.fetchone()
                available_account = dict(row) if row else None

            # Joriy to'g'ridan-to'g'ri savdo havolalar
            cursor3 = await db.execute("""
                SELECT a.*, p.name_uz AS product_name
                FROM accounts a
                LEFT JOIN products p ON p.id = a.product_id
                WHERE a.direct_sale_token IS NOT NULL AND a.status = 'available'
                ORDER BY a.created_at DESC
                LIMIT 50
            """)
            accounts_list = [dict(r) for r in await cursor3.fetchall()]

        return templates.TemplateResponse(request, "direct_sale.html", {
            "admin": admin,
            "products": products,
            "available_account": available_account,
            "accounts_list": accounts_list,
            "selected_product_id": product_id,
            "success_token": success_token,
        })
    except Exception:
        logger.exception("To'g'ridan-to'g'ri sotuv formasini yuklashda xato")
        return templates.TemplateResponse(request, "direct_sale.html", {
            "admin": admin,
            "products": [],
            "available_account": None,
            "accounts_list": [],
            "selected_product_id": "",
            "success_token": None,
            "error": "Xato yuz berdi",
        })


@router.post("/generate")
async def direct_sale_generate(
    request: Request,
    product_id: int = Form(...),
    account_id: int = Form(0),
):
    redirect = require_auth(request)
    if redirect:
        return redirect

    try:
        async with get_db() as db:
            # Akkaunt topish
            if account_id:
                cursor = await db.execute(
                    "SELECT id FROM accounts WHERE id = ? AND product_id = ? AND status = 'available'",
                    (account_id, product_id)
                )
            else:
                cursor = await db.execute("""
                    SELECT id FROM accounts
                    WHERE product_id = ? AND status = 'available'
                    ORDER BY expiry_date ASC
                    LIMIT 1
                """, (product_id,))

            row = await cursor.fetchone()
            if not row:
                return RedirectResponse(
                    f"/direct-sale?product_id={product_id}&error=no_stock",
                    status_code=302,
                )

            acc_id = row["id"]
            token = secrets.token_urlsafe(16)

            await db.execute(
                "UPDATE accounts SET direct_sale_token = ? WHERE id = ?",
                (token, acc_id)
            )
            await db.commit()

        return RedirectResponse(
            f"/direct-sale?success_token=DS_{token}&product_id={product_id}",
            status_code=302,
        )
    except Exception:
        logger.exception("To'g'ridan-to'g'ri sotuv havolasi yaratishda xato")
        return RedirectResponse("/direct-sale?error=1", status_code=302)


@router.post("/sell")
async def direct_sale_sell(
    request: Request,
    account_id: int = Form(...),
    buyer_telegram_id: str = Form(""),
):
    redirect = require_auth(request)
    if redirect:
        return redirect

    try:
        buyer_tid = int(buyer_telegram_id.strip()) if buyer_telegram_id.strip() else None

        async with get_db() as db:
            cursor = await db.execute(
                "SELECT id, status FROM accounts WHERE id = ?", (account_id,)
            )
            row = await cursor.fetchone()
            if not row:
                return RedirectResponse("/direct-sale?error=not_found", status_code=302)

            # Foydalanuvchi topish (agar telegram_id berilgan bo'lsa)
            user_db_id = None
            if buyer_tid:
                cursor2 = await db.execute(
                    "SELECT id FROM users WHERE telegram_id = ?", (buyer_tid,)
                )
                user_row = await cursor2.fetchone()
                if user_row:
                    user_db_id = user_row["id"]

            await db.execute("""
                UPDATE accounts
                SET status = 'sold',
                    sold_to_user_id = ?,
                    sold_at = CURRENT_TIMESTAMP,
                    sold_via = 'direct',
                    direct_sale_token = NULL
                WHERE id = ?
            """, (user_db_id, account_id))
            await db.commit()

        return RedirectResponse("/direct-sale?success=sold", status_code=302)
    except Exception:
        logger.exception("To'g'ridan-to'g'ri sotuvda xato")
        return RedirectResponse("/direct-sale?error=1", status_code=302)


@router.post("/revoke")
async def direct_sale_revoke(
    request: Request,
    account_id: int = Form(...),
):
    """Havola tokenini bekor qilish"""
    redirect = require_auth(request)
    if redirect:
        return redirect

    try:
        async with get_db() as db:
            await db.execute(
                "UPDATE accounts SET direct_sale_token = NULL WHERE id = ?",
                (account_id,)
            )
            await db.commit()
        return RedirectResponse("/direct-sale?success=revoked", status_code=302)
    except Exception:
        logger.exception("Havola bekor qilishda xato")
        return RedirectResponse("/direct-sale?error=1", status_code=302)
