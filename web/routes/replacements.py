"""
Almashtirish so'rovlari boshqaruvi
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
async def replacements_list(request: Request):
    redirect = require_auth(request)
    if redirect:
        return redirect

    admin = get_current_admin(request)
    status_filter = request.query_params.get("status", "pending")

    try:
        async with get_db() as db:
            conditions = []
            params = []
            if status_filter:
                conditions.append("r.status = ?")
                params.append(status_filter)

            where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

            cursor = await db.execute(f"""
                SELECT r.*,
                       u.full_name, u.username, u.telegram_id,
                       p.name_uz AS product_name,
                       a.login AS old_login, a.password AS old_password
                FROM replacements r
                JOIN users u ON u.id = r.user_id
                JOIN order_items oi ON oi.id = r.order_item_id
                JOIN products p ON p.id = oi.product_id
                LEFT JOIN accounts a ON a.id = oi.account_id
                {where}
                ORDER BY r.created_at DESC
                LIMIT 100
            """, params)
            replacements = [dict(r) for r in await cursor.fetchall()]

        return templates.TemplateResponse(request, "replacements.html", {
            "admin": admin,
            "replacements": replacements,
            "filter_status": status_filter,
        })
    except Exception:
        logger.exception("Almashtirish so'rovlarini yuklashda xato")
        return templates.TemplateResponse(request, "replacements.html", {
            "admin": admin,
            "replacements": [],
            "filter_status": status_filter,
            "error": "Xato yuz berdi",
        })


@router.post("/{replacement_id}/approve")
async def replacement_approve(request: Request, replacement_id: int):
    redirect = require_auth(request)
    if redirect:
        return redirect

    try:
        async with get_db() as db:
            # Almashtirish so'rovini topish
            cursor = await db.execute("""
                SELECT r.*, oi.product_id, oi.account_id AS old_account_id
                FROM replacements r
                JOIN order_items oi ON oi.id = r.order_item_id
                WHERE r.id = ?
            """, (replacement_id,))
            repl = await cursor.fetchone()
            if not repl:
                return RedirectResponse("/replacements?error=not_found", status_code=302)
            repl = dict(repl)

            # Yangi akkaunt topish
            cursor2 = await db.execute("""
                SELECT id, expiry_date FROM accounts
                WHERE product_id = ? AND status = 'available'
                  AND id != ?
                ORDER BY expiry_date ASC
                LIMIT 1
            """, (repl["product_id"], repl["old_account_id"] or 0))
            new_acc = await cursor2.fetchone()

            if not new_acc:
                return RedirectResponse(f"/replacements?error=no_stock&id={replacement_id}", status_code=302)

            new_acc = dict(new_acc)

            # Eski akkauntni qaytarish (available -> qaytarilgan emas, lekin statusni o'zgartirish)
            if repl["old_account_id"]:
                await db.execute(
                    "UPDATE accounts SET status = 'replaced' WHERE id = ?",
                    (repl["old_account_id"],)
                )

            # Yangi akkauntni sotilgan deb belgilash
            await db.execute("""
                UPDATE accounts
                SET status = 'sold', sold_at = CURRENT_TIMESTAMP,
                    sold_to_user_id = ?
                WHERE id = ?
            """, (repl["user_id"], new_acc["id"]))

            # Order item yangilash
            await db.execute("""
                UPDATE order_items
                SET account_id = ?, expiry_date = ?, delivered_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (new_acc["id"], new_acc["expiry_date"], repl["order_item_id"]))

            # Almashtirish so'rovini yopish
            await db.execute("""
                UPDATE replacements
                SET status = 'approved', resolved_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (replacement_id,))

            await db.commit()

        return RedirectResponse("/replacements?success=approved", status_code=302)
    except Exception:
        logger.exception("Almashtirish so'rovini tasdiqlashda xato")
        return RedirectResponse("/replacements?error=1", status_code=302)


@router.post("/{replacement_id}/reject")
async def replacement_reject(
    request: Request,
    replacement_id: int,
    admin_note: str = Form(""),
):
    redirect = require_auth(request)
    if redirect:
        return redirect

    try:
        async with get_db() as db:
            cursor = await db.execute("SELECT id FROM replacements WHERE id = ?", (replacement_id,))
            if not await cursor.fetchone():
                return RedirectResponse("/replacements?error=not_found", status_code=302)

            await db.execute("""
                UPDATE replacements
                SET status = 'rejected',
                    admin_note = ?,
                    resolved_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (admin_note or None, replacement_id))
            await db.commit()

        return RedirectResponse("/replacements?success=rejected", status_code=302)
    except Exception:
        logger.exception("Almashtirish so'rovini rad etishda xato")
        return RedirectResponse("/replacements?error=1", status_code=302)
