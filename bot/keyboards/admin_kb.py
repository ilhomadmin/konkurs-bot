"""
Admin panel klaviaturalari
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.utils.texts import t
from bot.utils.duration import all_tiers, tier_display_name


def admin_main_menu_kb(lang: str = "uz", role: str = "operator") -> InlineKeyboardMarkup:
    """Admin asosiy menyu — rolga qarab tugmalar"""
    buttons = []

    # Operator va yuqori rollar uchun
    if role in ("operator", "manager", "boss"):
        buttons.append([InlineKeyboardButton(text=t("btn_admin_orders", lang), callback_data="adm:orders")])

    # Manager va yuqori rollar uchun
    if role in ("manager", "boss"):
        buttons.append([InlineKeyboardButton(text=t("btn_admin_products", lang), callback_data="adm:products")])
        buttons.append([InlineKeyboardButton(text=t("btn_admin_promo", lang), callback_data="adm:promo")])
        buttons.append([InlineKeyboardButton(text=t("btn_admin_flash", lang), callback_data="adm:flash")])
        buttons.append([InlineKeyboardButton(text=t("btn_admin_stats", lang), callback_data="adm:stats")])
        buttons.append([InlineKeyboardButton(text=t("btn_admin_finance", lang), callback_data="adm:finance")])
        buttons.append([InlineKeyboardButton(text=t("btn_admin_broadcast", lang), callback_data="adm:broadcast")])

    # Faqat boss uchun
    if role == "boss":
        buttons.append([InlineKeyboardButton(text=t("btn_admin_roles", lang), callback_data="adm:roles")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def products_menu_kb(lang: str = "uz") -> InlineKeyboardMarkup:
    """Mahsulotlar boshqarish menyusi"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("btn_categories", lang), callback_data="adm:cat:list")],
            [InlineKeyboardButton(text=t("btn_back", lang), callback_data="adm:back")],
        ]
    )


def categories_list_kb(categories: list[dict], lang: str = "uz") -> InlineKeyboardMarkup:
    """Kategoriyalar ro'yxati klaviaturasi"""
    buttons = []
    for cat in categories:
        name = cat[f"name_{lang}"]
        status = "" if cat["is_active"] else " 🔴"
        buttons.append([
            InlineKeyboardButton(
                text=f"{name}{status}",
                callback_data=f"adm:cat:{cat['id']}"
            )
        ])
    buttons.append([InlineKeyboardButton(text=t("btn_add_category", lang), callback_data="adm:cat:add")])
    buttons.append([InlineKeyboardButton(text=t("btn_back", lang), callback_data="adm:products")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def category_actions_kb(category_id: int, lang: str = "uz") -> InlineKeyboardMarkup:
    """Kategoriya amallari (tahrirlash, o'chirish)"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📦 Mahsulotlar" if lang == "uz" else "📦 Товары",
                                  callback_data=f"adm:prod:list:{category_id}")],
            [InlineKeyboardButton(text=t("btn_toggle_active", lang),
                                  callback_data=f"adm:cat:toggle:{category_id}")],
            [InlineKeyboardButton(text=t("btn_delete", lang),
                                  callback_data=f"adm:cat:del:{category_id}")],
            [InlineKeyboardButton(text=t("btn_back", lang), callback_data="adm:cat:list")],
        ]
    )


def confirm_delete_kb(confirm_data: str, lang: str = "uz") -> InlineKeyboardMarkup:
    """Tasdiqlash/bekor qilish klaviaturasi"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t("btn_confirm", lang), callback_data=confirm_data),
                InlineKeyboardButton(text=t("btn_cancel", lang), callback_data="adm:cancel"),
            ]
        ]
    )


def products_list_kb(products: list[dict], category_id: int, lang: str = "uz") -> InlineKeyboardMarkup:
    """Mahsulotlar ro'yxati klaviaturasi"""
    buttons = []
    for prod in products:
        name = prod[f"name_{lang}"]
        status = "" if prod["is_active"] else " 🔴"
        buttons.append([
            InlineKeyboardButton(
                text=f"{name}{status}",
                callback_data=f"adm:prod:{prod['id']}"
            )
        ])
    buttons.append([
        InlineKeyboardButton(
            text=t("btn_add_product", lang),
            callback_data=f"adm:prod:add:{category_id}"
        )
    ])
    buttons.append([InlineKeyboardButton(text=t("btn_back", lang),
                                          callback_data=f"adm:cat:{category_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def product_actions_kb(product_id: int, lang: str = "uz") -> InlineKeyboardMarkup:
    """Mahsulot amallari klaviaturasi"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💰 Narxlar" if lang == "uz" else "💰 Цены",
                                  callback_data=f"adm:price:list:{product_id}")],
            [InlineKeyboardButton(text="📊 Akkauntlar" if lang == "uz" else "📊 Аккаунты",
                                  callback_data=f"adm:acc:list:{product_id}")],
            [InlineKeyboardButton(text=t("btn_toggle_active", lang),
                                  callback_data=f"adm:prod:toggle:{product_id}")],
            [InlineKeyboardButton(text=t("btn_delete", lang),
                                  callback_data=f"adm:prod:del:{product_id}")],
            [InlineKeyboardButton(text=t("btn_back", lang),
                                  callback_data=f"adm:prod:back:{product_id}")],
        ]
    )


def prices_list_kb(prices: list[dict], product_id: int, lang: str = "uz") -> InlineKeyboardMarkup:
    """Narx tierlari ro'yxati"""
    buttons = []
    for price in prices:
        name = price[f"display_name_{lang}"]
        buttons.append([
            InlineKeyboardButton(
                text=f"{name} — {price['price']:,} so'm",
                callback_data=f"adm:price:{price['id']}"
            )
        ])
    buttons.append([
        InlineKeyboardButton(text=t("btn_add_price", lang),
                             callback_data=f"adm:price:add:{product_id}")
    ])
    buttons.append([InlineKeyboardButton(text=t("btn_back", lang),
                                          callback_data=f"adm:prod:{product_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def tier_select_kb(lang: str = "uz", product_id: int = 0) -> InlineKeyboardMarkup:
    """Tier tanlash klaviaturasi (narx qo'shishda)"""
    buttons = []
    from bot.utils.duration import TIER_DISPLAY
    for tier in all_tiers():
        display = TIER_DISPLAY[tier][lang]
        buttons.append([
            InlineKeyboardButton(
                text=display,
                callback_data=f"adm:tier:{tier}:{product_id}"
            )
        ])
    buttons.append([InlineKeyboardButton(text=t("btn_back", lang),
                                          callback_data=f"adm:prod:{product_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def accounts_menu_kb(product_id: int, lang: str = "uz") -> InlineKeyboardMarkup:
    """Akkauntlar boshqarish menyusi"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("btn_add_account", lang),
                                  callback_data=f"adm:acc:add:{product_id}")],
            [InlineKeyboardButton(text=t("btn_bulk_accounts", lang),
                                  callback_data=f"adm:acc:bulk:{product_id}")],
            [InlineKeyboardButton(text=t("btn_back", lang),
                                  callback_data=f"adm:prod:{product_id}")],
        ]
    )


def roles_list_kb(admins: list[dict], lang: str = "uz") -> InlineKeyboardMarkup:
    """Adminlar ro'yxati klaviaturasi"""
    buttons = []
    role_labels = {"operator": "🔧", "manager": "📊", "boss": "👑"}
    for admin in admins:
        label = role_labels.get(admin["role"], "")
        name = admin.get("full_name") or admin.get("username") or str(admin["telegram_id"])
        status = "" if admin["is_active"] else " 🔴"
        buttons.append([
            InlineKeyboardButton(
                text=f"{label} {name} ({admin['role']}){status}",
                callback_data=f"adm:role:{admin['telegram_id']}"
            )
        ])
    buttons.append([InlineKeyboardButton(text=t("btn_add_admin", lang), callback_data="adm:role:add")])
    buttons.append([InlineKeyboardButton(text=t("btn_back", lang), callback_data="adm:back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def role_select_kb(target_id: int, lang: str = "uz") -> InlineKeyboardMarkup:
    """Rol tanlash klaviaturasi"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔧 Operator", callback_data=f"adm:role:set:{target_id}:operator")],
            [InlineKeyboardButton(text="📊 Manager", callback_data=f"adm:role:set:{target_id}:manager")],
            [InlineKeyboardButton(text="👑 Boss", callback_data=f"adm:role:set:{target_id}:boss")],
            [InlineKeyboardButton(text=t("btn_delete", lang), callback_data=f"adm:role:del:{target_id}")],
            [InlineKeyboardButton(text=t("btn_back", lang), callback_data="adm:roles")],
        ]
    )
