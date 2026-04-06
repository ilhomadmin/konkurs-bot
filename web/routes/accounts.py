"""
Akkauntlar boshqaruvi
"""
import csv
import io
import logging
import os
from datetime import date

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from bot.db.database import get_db
from bot.db.models import create_account, bulk_create_accounts
from bot.utils.duration import days_to_tier
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

        return templates.TemplateResponse("accounts/list.html", {
            "request": request,
            "admin": admin,
            "accounts": accounts,
            "products": products,
            "filter_product_id": product_id,
            "filter_status": status_filter,
        })
    except Exception:
        logger.exception("Akkauntlar ro'yxatini yuklashda xato")
        return templates.TemplateResponse("accounts/list.html", {
            "request": request,
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
    login: str = Form(...),
    password: str = Form(...),
    expiry_date: str = Form(...),
    supplier: str = Form(""),
):
    redirect = require_auth(request)
    if redirect:
        return redirect

    try:
        await create_account(
            product_id=product_id,
            login=login.strip(),
            password=password.strip(),
            expiry_date=expiry_date,
            supplier=supplier.strip() or None,
        )
        return RedirectResponse("/accounts?success=1", status_code=302)
    except Exception:
        logger.exception("Akkaunt qo'shishda xato")
        return RedirectResponse("/accounts?error=1", status_code=302)


@router.post("/bulk")
async def accounts_bulk_add(
    request: Request,
    product_id: int = Form(...),
    lines_text: str = Form(...),
):
    redirect = require_auth(request)
    if redirect:
        return redirect

    try:
        lines = [l for l in lines_text.splitlines() if l.strip()]
        result = await bulk_create_accounts(product_id=product_id, lines=lines)
        added = result.get("added", 0)
        errors = result.get("errors", [])
        error_str = "; ".join(errors[:5]) if errors else ""
        msg = f"added={added}"
        if error_str:
            msg += f"&errors={len(errors)}"
        return RedirectResponse(f"/accounts?success=bulk&{msg}", status_code=302)
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
