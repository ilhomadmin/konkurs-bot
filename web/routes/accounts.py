"""
Akkauntlar boshqaruvi
"""
import csv
import io
import json
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


def _parse_fields_json(acc: dict) -> dict:
    """fields_json ni parse qilib, login/password fallback bilan birlashtiradi."""
    raw = acc.get("fields_json")
    if raw:
        try:
            acc["fields"] = json.loads(raw)
        except Exception:
            acc["fields"] = {}
    else:
        # Eski akkauntlar uchun login/password/additional_data dan fields yaratish
        f = {}
        if acc.get("login"):
            f["Login"] = acc["login"]
        if acc.get("password"):
            f["Parol"] = acc["password"]
        if acc.get("additional_data"):
            f["Qo'shimcha"] = acc["additional_data"]
        acc["fields"] = f
    return acc


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
                SELECT a.*, p.name_uz AS product_name,
                       p.account_fields AS product_account_fields
                FROM accounts a
                LEFT JOIN products p ON p.id = a.product_id
                {where}
                ORDER BY a.created_at DESC
                LIMIT 200
            """, params)
            accounts = [_parse_fields_json(dict(r)) for r in await cursor.fetchall()]

            cursor2 = await db.execute(
                "SELECT id, name_uz, account_fields FROM products ORDER BY name_uz"
            )
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
    fields_json_str: str = Form("{}"),
    supplier: str = Form(""),
    next: str = Form(""),
):
    """Flexible fields — fields_json_str JSON object sifatida keladi."""
    redirect = require_auth(request)
    if redirect:
        return redirect

    try:
        fields_data = json.loads(fields_json_str) if fields_json_str.strip() else {}
        if not isinstance(fields_data, dict):
            fields_data = {}
    except Exception:
        fields_data = {}

    if not fields_data:
        dest = next.strip() or "/accounts"
        sep = "&" if "?" in dest else "?"
        return RedirectResponse(f"{dest}{sep}error=Kamida+bitta+maydon+to%27ldirilishi+kerak", status_code=302)

    try:
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT duration_days FROM products WHERE id = ?", (product_id,)
            )
            row = await cursor.fetchone()
            duration_days = row["duration_days"] if row and row["duration_days"] else 30

        # Backward compat: extract login/password from fields
        login_val = fields_data.get("Login") or fields_data.get("login") or None
        password_val = fields_data.get("Parol") or fields_data.get("password") or None
        additional = fields_data.get("Invite Link") or fields_data.get("additional_data") or None

        from datetime import date, timedelta
        today = date.today()
        if duration_days and duration_days > 0:
            expiry_str = (today + timedelta(days=duration_days)).isoformat()
            remaining = duration_days
        else:
            expiry_str = None
            remaining = 9999

        async with get_db() as db:
            await db.execute("""
                INSERT INTO accounts
                    (product_id, login, password, additional_data, expiry_date,
                     remaining_days, supplier, status, fields_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'available', ?)
            """, (
                product_id, login_val, password_val, additional,
                expiry_str, remaining,
                supplier.strip() or None,
                json.dumps(fields_data, ensure_ascii=False),
            ))
            await db.commit()

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
    lines_text: str = Form(...),
    supplier: str = Form(""),
    next: str = Form(""),
):
    redirect = require_auth(request)
    if redirect:
        return redirect

    try:
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT duration_days, account_fields FROM products WHERE id = ?", (product_id,)
            )
            row = await cursor.fetchone()
            duration_days = row["duration_days"] if row and row["duration_days"] else 30
            try:
                field_names = json.loads(row["account_fields"] or '["Login","Parol"]')
                if not isinstance(field_names, list):
                    field_names = ["Login", "Parol"]
            except Exception:
                field_names = ["Login", "Parol"]

        from datetime import date, timedelta
        today = date.today()
        if duration_days and duration_days > 0:
            expiry_str = (today + timedelta(days=duration_days)).isoformat()
            remaining = duration_days
        else:
            expiry_str = None
            remaining = 9999

        lines = [l for l in lines_text.splitlines() if l.strip()]
        added = 0
        errors_list = []

        async with get_db() as db:
            for i, line in enumerate(lines, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    parts = [p.strip() for p in line.split("|")]
                    fields_data = {}
                    for idx, fname in enumerate(field_names):
                        fields_data[fname] = parts[idx] if idx < len(parts) else ""
                    # Remove empty values
                    fields_data = {k: v for k, v in fields_data.items() if v}

                    login_val = fields_data.get("Login") or fields_data.get("login") or None
                    password_val = fields_data.get("Parol") or fields_data.get("password") or None
                    additional = None
                    for k, v in fields_data.items():
                        if k not in ("Login", "login", "Parol", "password"):
                            additional = v
                            break

                    await db.execute("""
                        INSERT INTO accounts
                            (product_id, login, password, additional_data, expiry_date,
                             remaining_days, supplier, status, fields_json)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 'available', ?)
                    """, (
                        product_id, login_val, password_val, additional,
                        expiry_str, remaining,
                        supplier.strip() or None,
                        json.dumps(fields_data, ensure_ascii=False),
                    ))
                    added += 1
                except Exception as e:
                    errors_list.append(f"Qator {i}: {e}")

            await db.commit()

        dest = next.strip() or "/accounts"
        sep = "&" if "?" in dest else "?"
        msg = f"added={added}"
        if errors_list:
            msg += f"&xerrors={len(errors_list)}"
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
                LEFT JOIN products p ON p.id = a.product_id
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
