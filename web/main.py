"""
IDROK.AI Web Admin Panel — FastAPI + Jinja2 + Tailwind
"""
import logging
import os
import sys

# Bot modulini import qilish uchun
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from bot.db.database import init_db
from web.auth import (
    get_current_admin, require_auth, require_role,
    hash_password, verify_password, create_token,
)
from web.routes import dashboard, products, categories, accounts, orders, replacements
from web.routes import finance, promos, flash_sales, bundles, reviews
from web.routes import broadcast, admins, settings as settings_routes, direct_sale

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="IDROK.AI Admin", docs_url=None, redoc_url=None)

# Static va template
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


# ==================== STARTUP ====================
@app.on_event("startup")
async def startup():
    await init_db()
    logger.info("Web admin panel ishga tushdi.")


# ==================== AUTH ====================
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    admin = get_current_admin(request)
    if admin:
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@app.post("/login")
async def login_submit(request: Request, username: str = Form(...), password: str = Form(...)):
    from bot.db.database import get_db
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM admin_roles WHERE (username = ? OR telegram_id = ?) AND is_active = 1",
            (username, username)
        )
        admin = await cursor.fetchone()

    if not admin:
        return templates.TemplateResponse("login.html", {
            "request": request, "error": "Foydalanuvchi topilmadi"
        })

    admin = dict(admin)
    if not admin.get("password_hash"):
        return templates.TemplateResponse("login.html", {
            "request": request, "error": "Parol o'rnatilmagan. Bot orqali /admin dan parol o'rnating."
        })

    if not verify_password(password, admin["password_hash"]):
        return templates.TemplateResponse("login.html", {
            "request": request, "error": "Noto'g'ri parol"
        })

    token = create_token(admin["telegram_id"], admin["role"])
    response = RedirectResponse("/", status_code=302)
    response.set_cookie("admin_token", token, max_age=86400 * 7, httponly=True)
    return response


@app.get("/logout")
async def logout():
    response = RedirectResponse("/login", status_code=302)
    response.delete_cookie("admin_token")
    return response


# ==================== ROUTES ====================
app.include_router(dashboard.router)
app.include_router(products.router, prefix="/products")
app.include_router(categories.router, prefix="/categories")
app.include_router(accounts.router, prefix="/accounts")
app.include_router(orders.router, prefix="/orders")
app.include_router(replacements.router, prefix="/replacements")
app.include_router(finance.router, prefix="/finance")
app.include_router(promos.router, prefix="/promos")
app.include_router(flash_sales.router, prefix="/flash-sales")
app.include_router(bundles.router, prefix="/bundles")
app.include_router(reviews.router, prefix="/reviews")
app.include_router(broadcast.router, prefix="/broadcast")
app.include_router(admins.router, prefix="/admins")
app.include_router(settings_routes.router, prefix="/settings")
app.include_router(direct_sale.router, prefix="/direct-sale")
