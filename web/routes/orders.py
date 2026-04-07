"""
Buyurtmalar boshqaruvi
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
async def orders_list(request: Request):
    redirect = require_auth(request)
    if redirect:
        return redirect

    admin = get_current_admin(request)
    status_filter = request.query_params.get("status", "")
    date_filter = request.query_params.get("date", "")

    try:
        async with get_db() as db:
            conditions = []
            params = []
            if status_filter:
                conditions.append("o.status = ?")
                params.append(status_filter)
            if date_filter:
                conditions.append("DATE(o.created_at) = ?")
                params.append(date_filter)

            where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

            cursor = await db.execute(f"""
                SELECT o.*, u.full_name, u.username, u.telegram_id,
                       COUNT(oi.id) AS item_count
                FROM orders o
                JOIN users u ON u.id = o.user_id
                LEFT JOIN order_items oi ON oi.order_id = o.id
                {where}
                GROUP BY o.id
                ORDER BY o.created_at DESC
                LIMIT 200
            """, params)
            orders = [dict(r) for r in await cursor.fetchall()]

        return templates.TemplateResponse(request, "orders.html", {
            "admin": admin,
            "orders": orders,
            "filter_status": status_filter,
            "filter_date": date_filter,
        })
    except Exception:
        logger.exception("Buyurtmalar ro'yxatini yuklashda xato")
        return templates.TemplateResponse(request, "orders.html", {
            "admin": admin,
            "orders": [],
            "filter_status": "",
            "filter_date": "",
            "error": "Xato yuz berdi",
        })


@router.get("/{order_id}")
async def order_detail(request: Request, order_id: int):
    redirect = require_auth(request)
    if redirect:
        return redirect

    admin = get_current_admin(request)
    try:
        async with get_db() as db:
            cursor = await db.execute("""
                SELECT o.*, u.full_name, u.username, u.telegram_id, u.phone
                FROM orders o
                JOIN users u ON u.id = o.user_id
                WHERE o.id = ?
            """, (order_id,))
            row = await cursor.fetchone()
            if not row:
                return RedirectResponse("/orders?error=not_found", status_code=302)
            order = dict(row)

            cursor2 = await db.execute("""
                SELECT oi.*, p.name_uz AS product_name,
                       a.login AS account_login, a.password AS account_password,
                       a.expiry_date AS account_expiry
                FROM order_items oi
                JOIN products p ON p.id = oi.product_id
                LEFT JOIN accounts a ON a.id = oi.account_id
                WHERE oi.order_id = ?
            """, (order_id,))
            items = [dict(r) for r in await cursor2.fetchall()]

        return templates.TemplateResponse(request, "order_detail.html", {
            "admin": admin,
            "order": order,
            "items": items,
        })
    except Exception:
        logger.exception("Buyurtma tafsilotlarini yuklashda xato")
        return RedirectResponse("/orders", status_code=302)


@router.post("/{order_id}/confirm")
async def order_confirm(request: Request, order_id: int):
    redirect = require_auth(request)
    if redirect:
        return redirect

    admin = get_current_admin(request)
    admin_tid = admin.get("tid") if admin else None

    try:
        async with get_db() as db:
            # Buyurtma mavjudligini tekshirish
            cursor = await db.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
            order = await cursor.fetchone()
            if not order:
                return RedirectResponse("/orders?error=not_found", status_code=302)

            # Har bir order item uchun akkaunt topish va berish
            cursor2 = await db.execute("""
                SELECT oi.* FROM order_items oi
                WHERE oi.order_id = ? AND oi.status = 'pending'
            """, (order_id,))
            items = await cursor2.fetchall()

            for item in items:
                # Mavjud akkaunt topish
                cursor3 = await db.execute("""
                    SELECT id FROM accounts
                    WHERE product_id = ? AND status = 'available'
                    ORDER BY expiry_date ASC
                    LIMIT 1
                """, (item["product_id"],))
                acc_row = await cursor3.fetchone()

                if acc_row:
                    acc_id = acc_row["id"]
                    # Akkauntni sotilgan deb belgilash
                    await db.execute("""
                        UPDATE accounts
                        SET status = 'sold', sold_to_user_id = ?, sold_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (order["user_id"], acc_id))

                    # Order item yangilash
                    cursor4 = await db.execute(
                        "SELECT expiry_date FROM accounts WHERE id = ?", (acc_id,)
                    )
                    acc_info = await cursor4.fetchone()
                    await db.execute("""
                        UPDATE order_items
                        SET account_id = ?, status = 'delivered',
                            delivered_at = CURRENT_TIMESTAMP,
                            expiry_date = ?
                        WHERE id = ?
                    """, (acc_id, acc_info["expiry_date"] if acc_info else None, item["id"]))
                else:
                    # Akkaunt yo'q — no_stock
                    await db.execute(
                        "UPDATE order_items SET status = 'no_stock' WHERE id = ?",
                        (item["id"],)
                    )

            # Buyurtma statusini yangilash
            await db.execute("""
                UPDATE orders
                SET status = 'confirmed',
                    payment_verified_by = ?,
                    payment_verified_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (admin_tid, order_id))
            await db.commit()

        return RedirectResponse(f"/orders/{order_id}?success=confirmed", status_code=302)
    except Exception:
        logger.exception("Buyurtmani tasdiqlashda xato")
        return RedirectResponse(f"/orders/{order_id}?error=1", status_code=302)


@router.post("/{order_id}/reject")
async def order_reject(
    request: Request,
    order_id: int,
    reason: str = Form(""),
):
    redirect = require_auth(request)
    if redirect:
        return redirect

    try:
        async with get_db() as db:
            cursor = await db.execute("SELECT id FROM orders WHERE id = ?", (order_id,))
            if not await cursor.fetchone():
                return RedirectResponse("/orders?error=not_found", status_code=302)

            await db.execute("""
                UPDATE orders
                SET status = 'rejected',
                    note = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (reason or None, order_id))
            await db.commit()

        return RedirectResponse(f"/orders/{order_id}?success=rejected", status_code=302)
    except Exception:
        logger.exception("Buyurtmani rad etishda xato")
        return RedirectResponse(f"/orders/{order_id}?error=1", status_code=302)
