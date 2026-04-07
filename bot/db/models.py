"""
Hub fayl — barcha model funksiyalarini bir joydan import qilish uchun.

Ishlatish:
    from bot.db.models import get_user, create_order, get_finance_report
"""

# ==================== USERS, CATEGORIES, PRODUCTS, ACCOUNTS ====================
from bot.db.models_users import (
    # helpers
    _get_user_id,
    # users
    create_user,
    get_user,
    get_user_by_telegram_id,
    update_language,
    set_onboarding_shown,
    update_user_phone,
    increment_user_purchases,
    toggle_auto_renewal,
    get_users_count,
    get_all_users,
    get_user_by_referral_code,
    set_user_referred_by,
    get_user_total_spent,
    get_all_user_telegram_ids,
    get_user_count,
    # categories
    create_category,
    get_all_categories,
    get_category_by_id,
    update_category,
    delete_category,
    get_category_by_video_keyword,
    # products
    create_product,
    get_all_products,
    get_products_by_category,
    get_product_by_id,
    update_product,
    delete_product,
    get_product_stock,
    get_product_by_video_keyword,
    increment_purchase_count,
    get_all_products_flat,
    # accounts
    create_account,
    bulk_create_accounts,
    get_accounts_by_product,
    get_account_by_id,
    sell_account,
    reserve_accounts,
    release_reserved,
    confirm_reserved,
    update_remaining_days,
    generate_direct_sale_token,
    get_account_by_direct_sale_token,
    get_all_accounts,
    update_account,
)

# ==================== CART, ORDERS, REPLACEMENTS, PROMO, FLASH ====================
from bot.db.models_orders import (
    # cart
    cart_get,
    cart_add,
    cart_update_qty,
    cart_remove_item,
    cart_clear,
    cart_count,
    cart_item_in_cart,
    # orders
    create_order,
    get_order_by_id,
    get_order,
    get_user_orders,
    get_user_active_order,
    update_order_status,
    set_order_progress_message,
    count_user_orders,
    has_any_order,
    get_orders_by_status,
    get_pending_orders_count,
    get_recent_orders,
    get_expired_pending_orders,
    # order items
    add_order_item,
    get_order_items,
    get_order_item_by_id,
    update_order_item,
    # expiry
    get_expiring_order_items,
    mark_expiry_notified,
    # replacements
    create_replacement,
    get_replacement_by_id,
    get_pending_replacements,
    update_replacement_status,
    get_user_replaceable_items,
    get_all_replacements,
    # promo
    create_promo_code,
    create_promo,
    get_promo_by_code,
    get_all_promo_codes,
    get_all_promos,
    increment_promo_usage,
    update_promo_code,
    activate_promo_code,
    deactivate_promo_code,
    get_promo_stats,
    # flash sales
    create_flash_sale,
    get_active_flash_sale,
    get_active_flash_sales,
    get_all_flash_sales,
    deactivate_expired_flash_sales,
    update_flash_sale,
    # abandoned cart
    get_abandoned_cart_users,
    mark_cart_reminder_sent,
)

# ==================== REVIEWS, FAVORITES, BUNDLES, ADMIN, VIP, FINANCE, ETC ====================
from bot.db.models_products import (
    # reviews
    create_review,
    get_product_rating,
    get_product_reviews,
    get_pending_reviews_to_request,
    set_review_visible,
    get_all_reviews_for_admin,
    # favorites
    add_favorite,
    remove_favorite,
    is_favorite,
    get_user_favorites,
    add_to_favorites,
    remove_from_favorites,
    is_in_favorites,
    # stock notifications
    add_stock_notification,
    add_stock_notify,
    get_stock_notification_users,
    get_stock_notifications,
    mark_stock_notified,
    mark_notified,
    get_low_stock_products,
    # admin roles
    create_admin_role,
    get_admin_by_telegram_id,
    get_all_admins,
    update_admin_role,
    delete_admin_role,
    update_admin_password,
    get_all_operators,
    get_all_managers_and_bosses,
    # vip
    get_vip_level,
    get_all_vip_levels,
    get_vip_levels,
    check_and_upgrade_vip,
    update_user_vip,
    # auto renewals
    create_auto_renewal,
    get_user_auto_renewals,
    get_user_auto_renewals_by_id,
    update_auto_renewal,
    get_due_auto_renewals,
    delete_auto_renewal,
    deactivate_auto_renewal,
    # bundles
    create_bundle,
    add_bundle_item,
    get_active_bundles,
    get_all_bundles,
    get_bundle_by_id,
    get_bundle_items,
    get_all_bundles_admin,
    update_bundle,
    # finance
    get_finance_report,
    get_daily_finance_data,
    add_expense,
    update_finance_cache_today,
    update_daily_finance_cache,
    get_all_expenses,
    # cross-sell
    get_cross_sell_recommendations,
    log_cross_sell,
    log_cross_sell_by_id,
    get_cross_sell_targets,
    # settings
    get_setting,
    get_setting_json,
    set_setting,
    get_all_settings,
    get_settings_by_category,
    invalidate_settings_cache,
    # dashboard
    get_dashboard_stats,
    # misc
    get_user_by_id,
    get_referral_count,
)

# ==================== BACKWARD-COMPATIBLE ALIASES ====================
# Eski kodda ishlatiladigan funksiya nomlari
update_user_stats = increment_user_purchases
set_referred_by = set_user_referred_by
release_reserved_accounts = release_reserved
create_order_item = add_order_item
get_replacement = get_replacement_by_id
update_replacement = update_replacement_status

__all__ = [
    # users
    "create_user", "get_user", "get_user_by_telegram_id", "update_language",
    "set_onboarding_shown", "update_user_phone", "increment_user_purchases",
    "toggle_auto_renewal", "get_users_count", "get_all_users",
    "get_user_by_referral_code", "set_user_referred_by", "get_user_total_spent",
    "get_all_user_telegram_ids", "get_user_count", "update_user_stats",
    "set_referred_by", "get_user_by_id", "get_referral_count",
    # categories
    "create_category", "get_all_categories", "get_category_by_id",
    "update_category", "delete_category", "get_category_by_video_keyword",
    # products
    "create_product", "get_all_products", "get_products_by_category",
    "get_product_by_id", "update_product", "delete_product",
    "get_product_stock", "get_product_by_video_keyword",
    "increment_purchase_count", "get_all_products_flat",
    # accounts
    "create_account", "bulk_create_accounts", "get_accounts_by_product",
    "get_account_by_id", "sell_account", "reserve_accounts",
    "release_reserved", "release_reserved_accounts", "confirm_reserved",
    "update_remaining_days", "generate_direct_sale_token",
    "get_account_by_direct_sale_token", "get_all_accounts", "update_account",
    # cart
    "cart_get", "cart_add", "cart_update_qty", "cart_remove_item",
    "cart_clear", "cart_count", "cart_item_in_cart",
    # orders
    "create_order", "get_order_by_id", "get_order", "get_user_orders",
    "get_user_active_order", "update_order_status", "set_order_progress_message",
    "count_user_orders", "has_any_order", "get_orders_by_status",
    "get_pending_orders_count", "get_recent_orders", "get_expired_pending_orders",
    # order items
    "add_order_item", "create_order_item", "get_order_items",
    "get_order_item_by_id", "update_order_item",
    # expiry
    "get_expiring_order_items", "mark_expiry_notified",
    # replacements
    "create_replacement", "get_replacement_by_id", "get_replacement",
    "get_pending_replacements", "update_replacement_status", "update_replacement",
    "get_user_replaceable_items", "get_all_replacements",
    # promo
    "create_promo_code", "create_promo", "get_promo_by_code",
    "get_all_promo_codes", "get_all_promos", "increment_promo_usage",
    "update_promo_code", "activate_promo_code", "deactivate_promo_code",
    "get_promo_stats",
    # flash sales
    "create_flash_sale", "get_active_flash_sale", "get_active_flash_sales",
    "get_all_flash_sales", "deactivate_expired_flash_sales", "update_flash_sale",
    # abandoned cart
    "get_abandoned_cart_users", "mark_cart_reminder_sent",
    # reviews
    "create_review", "get_product_rating", "get_product_reviews",
    "get_pending_reviews_to_request", "set_review_visible",
    "get_all_reviews_for_admin",
    # favorites
    "add_favorite", "remove_favorite", "is_favorite", "get_user_favorites",
    "add_to_favorites", "remove_from_favorites", "is_in_favorites",
    # stock notifications
    "add_stock_notification", "add_stock_notify", "get_stock_notification_users",
    "get_stock_notifications", "mark_stock_notified", "mark_notified",
    "get_low_stock_products",
    # admin roles
    "create_admin_role", "get_admin_by_telegram_id", "get_all_admins",
    "update_admin_role", "delete_admin_role", "update_admin_password",
    "get_all_operators", "get_all_managers_and_bosses",
    # vip
    "get_vip_level", "get_all_vip_levels", "get_vip_levels",
    "check_and_upgrade_vip", "update_user_vip",
    # auto renewals
    "create_auto_renewal", "get_user_auto_renewals",
    "get_user_auto_renewals_by_id", "update_auto_renewal",
    "get_due_auto_renewals", "delete_auto_renewal", "deactivate_auto_renewal",
    # bundles
    "create_bundle", "add_bundle_item", "get_active_bundles", "get_all_bundles",
    "get_bundle_by_id", "get_bundle_items", "get_all_bundles_admin", "update_bundle",
    # finance
    "get_finance_report", "get_daily_finance_data", "add_expense",
    "update_finance_cache_today", "update_daily_finance_cache", "get_all_expenses",
    # cross-sell
    "get_cross_sell_recommendations", "log_cross_sell", "log_cross_sell_by_id",
    "get_cross_sell_targets",
    # settings
    "get_setting", "get_setting_json", "set_setting", "get_all_settings",
    "get_settings_by_category", "invalidate_settings_cache",
    # dashboard
    "get_dashboard_stats",
]
