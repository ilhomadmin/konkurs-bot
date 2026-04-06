"""
Web auth — JWT token bilan login
"""
import hashlib
import hmac
import json
import logging
import time
from typing import Optional

from starlette.requests import Request
from starlette.responses import RedirectResponse

logger = logging.getLogger(__name__)

try:
    from bot.config import WEB_SECRET_KEY
    SECRET_KEY = WEB_SECRET_KEY
except ImportError:
    SECRET_KEY = "idrok-ai-web-secret-change-this"
TOKEN_TTL = 86400 * 7  # 7 kun


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash


def create_token(telegram_id: int, role: str) -> str:
    payload = {
        "tid": telegram_id,
        "role": role,
        "exp": int(time.time()) + TOKEN_TTL,
    }
    data = json.dumps(payload).encode()
    sig = hmac.new(SECRET_KEY.encode(), data, hashlib.sha256).hexdigest()
    import base64
    return base64.urlsafe_b64encode(data).decode() + "." + sig


def decode_token(token: str) -> Optional[dict]:
    try:
        import base64
        parts = token.split(".", 1)
        if len(parts) != 2:
            return None
        data = base64.urlsafe_b64decode(parts[0])
        sig = hmac.new(SECRET_KEY.encode(), data, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, parts[1]):
            return None
        payload = json.loads(data)
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None


def get_current_admin(request: Request) -> Optional[dict]:
    token = request.cookies.get("admin_token")
    if not token:
        return None
    return decode_token(token)


def require_auth(request: Request) -> Optional[RedirectResponse]:
    admin = get_current_admin(request)
    if not admin:
        return RedirectResponse("/login", status_code=302)
    return None


def require_role(request: Request, roles: list[str]) -> Optional[RedirectResponse]:
    admin = get_current_admin(request)
    if not admin:
        return RedirectResponse("/login", status_code=302)
    if admin.get("role") not in roles:
        return RedirectResponse("/", status_code=302)
    return None
