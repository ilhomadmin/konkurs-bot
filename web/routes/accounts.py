"""
Akkauntlar boshqaruvi
"""
import csv
import io
import logging
import os
from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from bot.db.database import get_db
from bot.db.models import create_account, bulk_create_accounts
from web.auth import get_current_admin, require_auth

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")
)


@router.get("/")
async def accounts_list(request: Request):
    redirect = require_auth(request)
    if redirect:
        return redirect

    admin = get_current_admin(request)
    product_id = request.query_params.get("product_id", "")
    status_filter = request.query_params.get("status", "")

    try:
        async with get_db() as db:
            conditions = []
            params = []
            if product_id:
                conditions.append("a.product_id = ?")
                params.append(int(product_id))
            if status_filter:
                conditions.append("a.status = ?")
                params.append(status_filter)

            where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

            cursor = await db.execute(f"""
                SELECT a.*, p.name_uz AS product_name
                FROM accounts a
                JOIN products p ON p.id = a.product_id
                {where}
                ORDER BY a.created_at DESC
                LIMIT 200
            """, params)
            accounts = [dict(r) for r in await cursor.fetchall()]

            cursor2 = await db.execute("SELECT id, name_uz FROM products ORDER BY name_uz")
            products = [dict(r) for r in await cursor2.fetchall()]

        return templates.TemplateResponse(request, "accounts.html", {
            "admin": admin,
            "accounts": accounts,
            "products": products,
            "filter_product_id": product_id,
            "filter_status": status_filter,
        })
    except Exception:
        logger.exception("Akkauntlar ro'yxatini yuklashda xato")
        return templates.TemplateResponse(request, "accounts.html", {
            "admin": admin,
            "accounts": [],
            "products": [],
            "filter_product_id": "",
            "filter_status": "",
            "error": "Xato yuz berdi",
        })


@router.post("/add")
async def accounts_add(
    request: Request,
    product_id: int = Form(...),
    login: str = Form(""),
    password: str = Form(""),
    invite_link: str = Form(""),
    supplier: str = Form(""),
    next: str = Form(""),
):
    """FIX 2+3: expiry avtomatik, login/password/invite_link ixtiyoriy."""
    redirect = require_auth(request)
    if redirect:
        return redirect

    login = login.strip() or None
    password = password.strip() or None
    invite_link = invite_link.strip() or None

    if not login and not password and not invite_link:
        dest = next.strip() or "/accounts"
        sep = "&" if "?" in dest else "?"
        return RedirectResponse(f"{dest}{sep}error=Kamida+bitta+maydon+to%27ldirilishi+kerak", status_code=302)

    try:
        # duration_days mahsulotdan olinadi
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT duration_days FROM products WHERE id = ?", (product_id,)
            )
            row = await cursor.fetchone()
            duration_days = row["duration_days"] if row and row["duration_days"] else 30

        await create_account(
            product_id=product_id,
            duration_days=duration_days,
            login=login,
            password=password,
            additional_data=invite_link,
            supplier=supplier.strip() or None,
        )
        dest = next.strip() or "/accounts"
        sep = "&" if "?" in dest else "?"
        return RedirectResponse(f"{dest}{sep}success=Akkaunt+qo%27shildi", status_code=302)
    except Exception:
        logger.exception("Akkaunt qo'shishda xato")
        return RedirectResponse("/accounts?error=Xato+yuz+berdi", status_code=302)


@router.post("/bulk")
async def accounts_bulk_add(
    request: Request,
    product_id: int = Form(...),
    accounts: str = Form(...),
    supplier: str = Form(""),
    next: str = Form(""),
):
    redirect = require_auth(request)
    if redirect:
        return redirect

    try:
        # duration_days mahsulotdan olinadi
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT duration_days FROM products WHERE id = ?", (product_id,)
            )
            row = await cursor.fetchone()
            duration_days = row["duration_days"] if row and row["duration_days"] else 30

        lines = [l for l in accounts.splitlines() if l.strip()]
        result = await bulk_create_accounts(
            product_id=product_id, lines=lines, duration_days=duration_days
        )
        added = result.get("added", 0)
        errors = result.get("errors", [])
        dest = next.strip() or "/accounts"
        sep = "&" if "?" in dest else "?"
        msg = f"added={added}"
        if errors:
            msg += f"&xerrors={len(errors)}"
        return RedirectResponse(f"{dest}{sep}success=bulk&{msg}", status_code=302)
    except Exception:
        logger.exception("Bulk akkaunt qo'shishda xato")
        return RedirectResponse("/accounts?error=bulk", status_code=302)


@router.get("/export")
async def accounts_export(request: Request):
    redirect = require_auth(request)
    if redirect:
        return redirect

    product_id = request.query_params.get("product_id", "")
    status_filter = request.query_params.get("status", "")

    try:
        async with get_db() as db:
            conditions = []
            params = []
            if product_id:
                conditions.append("a.product_id = ?")
                params.append(int(product_id))
            if status_filter:
                conditions.append("a.status = ?")
                params.append(status_filter)

            where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

            cursor = await db.execute(f"""
                SELECT a.id, p.name_uz AS product_name, a.login, a.password,
                       a.expiry_date, a.remaining_days, a.status, a.supplier, a.created_at
                FROM accounts a
                JOIN products p ON p.id = a.product_id
                {where}
                ORDER BY a.created_at DESC
            """, params)
            rows = await cursor.fetchall()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Mahsulot", "Login", "Parol", "Tugash sanasi", "Qolgan kunlar", "Status", "Yetkazuvchi", "Qo'shilgan"])
        for row in rows:
            writer.writerow([
                row["id"], row["product_name"], row["login"], row["password"],
                row["expiry_date"], row["remaining_days"], row["status"],
                row["supplier"] or "", row["created_at"],
            ])

        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=accounts.csv"},
        )
    except Exception:
        logger.exception("Akkauntlar eksportida xato")
        return RedirectResponse("/accounts?error=export", status_code=302)


@router.post("/{account_id}/delete")
async def accounts_delete(
    request: Request,
    account_id: int,
    next: str = Form(""),
):
    redirect = require_auth(request)
    if redirect:
        return redirect

    try:
        async with get_db() as db:
            await db.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
            await db.commit()
        dest = next.strip() or "/accounts"
        sep = "&" if "?" in dest else "?"
        return RedirectResponse(f"{dest}{sep}success=O%27chirildi", status_code=302)
    except Exception:
        logger.exception("Akkaunt o'chirishda xato: %s", account_id)
        return RedirectResponse("/accounts?error=Xato", status_code=302)
