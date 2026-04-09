"""
To'lov API — Payme va Click webhook handlerlari
PHASE 5: Payment API Infrastructure
"""
import base64
import hashlib
import json
import logging
import time
from typing import Optional

from fastapi import APIRouter, Form, Header, Request
from fastapi.responses import JSONResponse

from bot.db.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


# ==================== HELPERS ====================

async def _get_setting(key: str, default: str = "") -> str:
    try:
        from bot.utils.settings import get_setting
        return await get_setting(key, default)
    except Exception:
        return default


async def _get_order(order_id: int) -> Optional[dict]:
    try:
        async with get_db() as db:
            cursor = await db.execute("""
                SELECT o.*, u.telegram_id as user_telegram_id, u.language as user_lang
                FROM orders o
                JOIN users u ON u.id = o.user_id
                WHERE o.id = ?
            """, (order_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None
    except Exception:
        return None


async def _confirm_order(order_id: int, payment_method: str) -> bool:
    """Buyurtmani tasdiqlash — confirm_reserved va status yangilash."""
    try:
        order = await _get_order(order_id)
        if not order:
            return False

        from bot.db.models import (
            confirm_reserved, increment_purchase_count,
            increment_user_purchases, check_and_upgrade_vip,
            get_order_items, update_order_status
        )

        user_telegram_id = order["user_telegram_id"]
        await confirm_reserved(order_id, user_telegram_id)

        items = await get_order_items(order_id)
        for item in items:
            await increment_purchase_count(item["product_id"])

        await increment_user_purchases(user_telegram_id, order["total_amount"])
        await check_and_upgrade_vip(user_telegram_id)

        async with get_db() as db:
            await db.execute("""
                UPDATE orders SET status = 'confirmed', payment_method = ?,
                    payment_verified_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (payment_method, order_id))
            await db.commit()

        # Foydalanuvchiga xabar yuborish
        try:
            from bot.handlers.payment import build_account_delivery_text
            from bot.utils.texts import t
            from bot.main import bot as bot_instance

            fresh_items = await get_order_items(order_id)
            lang = order.get("user_lang", "uz")
            accounts_text = build_account_delivery_text(fresh_items, lang)
            delivery_msg = t("order_delivered", lang,
                             order_id=order_id, accounts_text=accounts_text)
            await bot_instance.send_message(
                chat_id=user_telegram_id,
                text=f"✅ To'lov qabul qilindi!\n\n{delivery_msg}",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.warning(f"Bot delivery message error: {e}")

        return True
    except Exception as e:
        logger.exception(f"_confirm_order error: {e}")
        return False


# ==================== PAYME ====================

@router.post("/payme")
async def payme_webhook(request: Request):
    """
    Payme Merchant API — JSON-RPC webhook.
    Docs: https://developer.payme.uz/documentation/merchant-api
    """
    # Authentication check
    merchant_id = await _get_setting("payme_merchant_id")
    secret_key = await _get_setting("payme_secret_key")

    auth_header = request.headers.get("Authorization", "")
    if secret_key:
        try:
            encoded = base64.b64decode(auth_header.replace("Basic ", "")).decode()
            _, given_key = encoded.split(":", 1)
            if given_key != secret_key:
                return JSONResponse({"error": {"code": -32504, "message": {"uz": "Token noto'g'ri", "ru": "Неверный токен"}}})
        except Exception:
            return JSONResponse({"error": {"code": -32504, "message": {"uz": "Token xato", "ru": "Ошибка токена"}}})

    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": {"code": -32700, "message": "Parse error"}})

    method = body.get("method", "")
    params = body.get("params", {})
    req_id = body.get("id")

    def ok(result: dict):
        return JSONResponse({"result": result, "id": req_id})

    def err(code: int, msg: str):
        return JSONResponse({"error": {"code": code, "message": {"uz": msg, "ru": msg}}, "id": req_id})

    # Parse order_id from account
    account = params.get("account", {})
    order_id = None
    try:
        order_id = int(account.get("order_id") or account.get("id") or 0)
    except Exception:
        pass

    if method == "CheckPerformTransaction":
        if not order_id:
            return err(-31050, "Buyurtma ID noto'g'ri")
        order = await _get_order(order_id)
        if not order:
            return err(-31050, "Buyurtma topilmadi")
        amount = params.get("amount", 0)
        expected = order["total_amount"] * 100  # tiyin
        if amount != expected:
            return err(-31001, "Summa mos emas")
        return ok({"allow": True})

    elif method == "CreateTransaction":
        if not order_id:
            return err(-31050, "Buyurtma ID noto'g'ri")
        order = await _get_order(order_id)
        if not order:
            return err(-31050, "Buyurtma topilmadi")
        if order["status"] not in ("pending_payment",):
            return err(-31008, "Buyurtma holati noto'g'ri")
        t_id = params.get("id")
        create_time = params.get("time", int(time.time() * 1000))
        try:
            async with get_db() as db:
                await db.execute("""
                    UPDATE orders SET payment_method = 'payme', updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (order_id,))
                await db.commit()
        except Exception:
            pass
        return ok({
            "create_time": create_time,
            "transaction": str(order_id),
            "state": 1
        })

    elif method == "PerformTransaction":
        t_id = params.get("id")
        # Extract order_id from transaction id stored earlier
        if not order_id:
            try:
                order_id = int(params.get("id", 0))
            except Exception:
                return err(-31003, "Tranzaksiya topilmadi")
        order = await _get_order(order_id)
        if not order:
            return err(-31003, "Tranzaksiya topilmadi")
        perform_time = int(time.time() * 1000)
        if order["status"] not in ("pending_payment", "payment_sent"):
            if order["status"] == "confirmed":
                return ok({"transaction": str(order_id), "perform_time": perform_time, "state": 2})
            return err(-31008, "Buyurtma holati noto'g'ri")
        await _confirm_order(order_id, "payme")
        return ok({"transaction": str(order_id), "perform_time": perform_time, "state": 2})

    elif method == "CancelTransaction":
        if not order_id:
            return err(-31003, "Tranzaksiya topilmadi")
        order = await _get_order(order_id)
        if not order:
            return err(-31003, "Tranzaksiya topilmadi")
        cancel_time = int(time.time() * 1000)
        reason = params.get("reason", 1)
        if order["status"] not in ("confirmed",):
            try:
                from bot.db.models import release_reserved, update_order_status
                await release_reserved(order_id)
                await update_order_status(order_id, "cancelled")
            except Exception:
                pass
        return ok({"transaction": str(order_id), "cancel_time": cancel_time, "state": -1})

    elif method == "CheckTransaction":
        if not order_id:
            return err(-31003, "Tranzaksiya topilmadi")
        order = await _get_order(order_id)
        if not order:
            return err(-31003, "Tranzaksiya topilmadi")
        state = 2 if order["status"] == "confirmed" else 1
        return ok({"create_time": 0, "perform_time": 0, "cancel_time": 0,
                   "transaction": str(order_id), "state": state, "reason": None})

    elif method == "GetStatement":
        return ok({"transactions": []})

    return err(-32601, "Metod topilmadi")


# ==================== CLICK ====================

def _click_sign(params: dict, secret_key: str) -> str:
    """Click imzo yaratish."""
    sign_str = (
        f"{params.get('click_trans_id', '')}"
        f"{params.get('service_id', '')}"
        f"{secret_key}"
        f"{params.get('merchant_trans_id', '')}"
        f"{params.get('amount', '')}"
        f"{params.get('action', '')}"
        f"{params.get('sign_time', '')}"
    )
    return hashlib.md5(sign_str.encode()).hexdigest()


@router.post("/click/prepare")
async def click_prepare(
    click_trans_id: str = Form(...),
    service_id: str = Form(...),
    click_paydoc_id: str = Form(...),
    merchant_trans_id: str = Form(...),
    amount: str = Form(...),
    action: str = Form(...),
    error: str = Form("0"),
    error_note: str = Form(""),
    sign_time: str = Form(...),
    sign_string: str = Form(...),
):
    """Click Prepare endpoint."""
    secret_key = await _get_setting("click_secret_key")

    # Verify signature
    if secret_key:
        expected = _click_sign({
            "click_trans_id": click_trans_id,
            "service_id": service_id,
            "secret_key": secret_key,
            "merchant_trans_id": merchant_trans_id,
            "amount": amount,
            "action": action,
            "sign_time": sign_time,
        }, secret_key)
        if sign_string != expected:
            return JSONResponse({
                "click_trans_id": click_trans_id, "merchant_trans_id": merchant_trans_id,
                "error": -1, "error_note": "Imzo noto'g'ri"
            })

    try:
        order_id = int(merchant_trans_id)
    except Exception:
        return JSONResponse({"click_trans_id": click_trans_id, "merchant_trans_id": merchant_trans_id,
                             "error": -6, "error_note": "Buyurtma ID noto'g'ri"})

    order = await _get_order(order_id)
    if not order:
        return JSONResponse({"click_trans_id": click_trans_id, "merchant_trans_id": merchant_trans_id,
                             "error": -5, "error_note": "Buyurtma topilmadi"})

    try:
        expected_amount = float(order["total_amount"])
        given_amount = float(amount)
        if abs(expected_amount - given_amount) > 1:
            return JSONResponse({"click_trans_id": click_trans_id, "merchant_trans_id": merchant_trans_id,
                                 "error": -2, "error_note": "Summa mos emas"})
    except Exception:
        pass

    try:
        async with get_db() as db:
            await db.execute("UPDATE orders SET payment_method = 'click' WHERE id = ?", (order_id,))
            await db.commit()
    except Exception:
        pass

    return JSONResponse({
        "click_trans_id": click_trans_id,
        "merchant_trans_id": merchant_trans_id,
        "merchant_prepare_id": order_id,
        "error": 0,
        "error_note": "Success"
    })


@router.post("/click/complete")
async def click_complete(
    click_trans_id: str = Form(...),
    service_id: str = Form(...),
    click_paydoc_id: str = Form(...),
    merchant_trans_id: str = Form(...),
    merchant_prepare_id: str = Form(...),
    amount: str = Form(...),
    action: str = Form(...),
    error: str = Form("0"),
    error_note: str = Form(""),
    sign_time: str = Form(...),
    sign_string: str = Form(...),
):
    """Click Complete endpoint."""
    secret_key = await _get_setting("click_secret_key")

    if secret_key:
        expected = _click_sign({
            "click_trans_id": click_trans_id,
            "service_id": service_id,
            "secret_key": secret_key,
            "merchant_trans_id": merchant_trans_id,
            "amount": amount,
            "action": action,
            "sign_time": sign_time,
        }, secret_key)
        if sign_string != expected:
            return JSONResponse({
                "click_trans_id": click_trans_id, "merchant_trans_id": merchant_trans_id,
                "error": -1, "error_note": "Imzo noto'g'ri"
            })

    if int(error) < 0:
        # To'lov muvaffaqiyatsiz
        try:
            order_id = int(merchant_trans_id)
            from bot.db.models import release_reserved, update_order_status
            await release_reserved(order_id)
            await update_order_status(order_id, "cancelled")
        except Exception:
            pass
        return JSONResponse({
            "click_trans_id": click_trans_id, "merchant_trans_id": merchant_trans_id,
            "error": 0, "error_note": "Cancelled"
        })

    try:
        order_id = int(merchant_trans_id)
    except Exception:
        return JSONResponse({"click_trans_id": click_trans_id, "merchant_trans_id": merchant_trans_id,
                             "error": -6, "error_note": "ID noto'g'ri"})

    order = await _get_order(order_id)
    if not order:
        return JSONResponse({"click_trans_id": click_trans_id, "merchant_trans_id": merchant_trans_id,
                             "error": -5, "error_note": "Buyurtma topilmadi"})

    if order["status"] == "confirmed":
        return JSONResponse({"click_trans_id": click_trans_id, "merchant_trans_id": merchant_trans_id,
                             "error": 0, "error_note": "Already confirmed"})

    await _confirm_order(order_id, "click")

    return JSONResponse({
        "click_trans_id": click_trans_id,
        "merchant_trans_id": merchant_trans_id,
        "merchant_confirm_id": order_id,
        "error": 0,
        "error_note": "Success"
    })
