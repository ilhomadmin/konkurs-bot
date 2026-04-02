"""
Barcha UI matnlar — O'zbekcha va Ruscha
"""

TEXTS: dict[str, dict[str, str]] = {
    # Til tanlash
    "choose_language": {
        "uz": "🌐 Tilni tanlang:",
        "ru": "🌐 Выберите язык:"
    },
    "language_set": {
        "uz": "✅ Til o'zgartirildi: O'zbekcha",
        "ru": "✅ Язык изменён: Русский"
    },

    # Asosiy menyu
    "main_menu": {
        "uz": "📋 Asosiy menyu",
        "ru": "📋 Главное меню"
    },

    # Onboarding
    "onboarding_1": {
        "uz": "1️⃣ IDROK.AI ga xush kelibsiz! 🎉\n\nBiz premium software akkauntlarini 5-10 barobar arzon narxda taklif qilamiz.",
        "ru": "1️⃣ Добро пожаловать в IDROK.AI! 🎉\n\nМы предлагаем premium software аккаунты в 5-10 раз дешевле рыночной цены."
    },
    "onboarding_2": {
        "uz": "2️⃣ Qanday sotib olasiz?\n\n📦 Tanlang → 🛒 Savatga → 📸 To'lang → ✅ Akkaunt keladi!",
        "ru": "2️⃣ Как купить?\n\n📦 Выберите → 🛒 В корзину → 📸 Оплатите → ✅ Аккаунт готов!"
    },
    "onboarding_3": {
        "uz": "3️⃣ 🛡 Barcha mahsulotlarga kafolat!\n\nAkkaunt ishlamasa — bepul almashtiramiz.",
        "ru": "3️⃣ 🛡 Гарантия на все товары!\n\nЕсли аккаунт не работает — заменим бесплатно."
    },
    "onboarding_done_btn": {
        "uz": "📦 Mahsulotlarni ko'rish",
        "ru": "📦 Посмотреть товары"
    },

    # Asosiy tugmalar (ReplyKeyboard)
    "btn_catalog": {
        "uz": "📦 Obunalar",
        "ru": "📦 Подписки"
    },
    "btn_cart": {
        "uz": "🛒 Savat",
        "ru": "🛒 Корзина"
    },
    "btn_orders": {
        "uz": "📋 Buyurtmalarim",
        "ru": "📋 Мои заказы"
    },
    "btn_bundles": {
        "uz": "🎁 To'plamlar",
        "ru": "🎁 Комплекты"
    },
    "btn_profile": {
        "uz": "👤 Profil",
        "ru": "👤 Профиль"
    },
    "btn_help": {
        "uz": "ℹ️ Yordam",
        "ru": "ℹ️ Помощь"
    },

    # Profil submenu
    "profile_menu": {
        "uz": "👤 Profilingiz:",
        "ru": "👤 Ваш профиль:"
    },
    "btn_vip": {
        "uz": "💎 VIP daraja",
        "ru": "💎 VIP уровень"
    },
    "btn_favorites": {
        "uz": "⭐ Sevimlilar",
        "ru": "⭐ Избранное"
    },
    "btn_referral": {
        "uz": "🎁 Referal dasturi",
        "ru": "🎁 Реферальная программа"
    },
    "btn_auto_renewal": {
        "uz": "🔄 Avtouzaytirish",
        "ru": "🔄 Автопродление"
    },
    "btn_change_lang": {
        "uz": "🌐 Tilni o'zgartirish",
        "ru": "🌐 Изменить язык"
    },
    "btn_back": {
        "uz": "⬅️ Ortga",
        "ru": "⬅️ Назад"
    },

    # Yordam submenu
    "help_menu": {
        "uz": "ℹ️ Yordam bo'limi:",
        "ru": "ℹ️ Раздел помощи:"
    },
    "btn_faq": {
        "uz": "❓ Ko'p beriladigan savollar",
        "ru": "❓ Часто задаваемые вопросы"
    },
    "btn_operator": {
        "uz": "📞 Operator bilan bog'lanish",
        "ru": "📞 Связаться с оператором"
    },
    "btn_replacement": {
        "uz": "🔄 Akkaunt almashtirish",
        "ru": "🔄 Замена аккаунта"
    },

    # Admin menyu
    "admin_menu": {
        "uz": "🔧 Admin panel",
        "ru": "🔧 Панель администратора"
    },
    "btn_admin_products": {
        "uz": "📦 Mahsulotlar",
        "ru": "📦 Товары"
    },
    "btn_admin_orders": {
        "uz": "📋 Buyurtmalar",
        "ru": "📋 Заказы"
    },
    "btn_admin_stats": {
        "uz": "📊 Statistika",
        "ru": "📊 Статистика"
    },
    "btn_admin_broadcast": {
        "uz": "📢 Xabar yuborish",
        "ru": "📢 Рассылка"
    },
    "btn_admin_finance": {
        "uz": "💰 Moliya",
        "ru": "💰 Финансы"
    },
    "btn_admin_roles": {
        "uz": "👥 Adminlar",
        "ru": "👥 Администраторы"
    },
    "btn_admin_promo": {
        "uz": "🎟 Promo kodlar",
        "ru": "🎟 Промо коды"
    },
    "btn_admin_flash": {
        "uz": "⚡ Flash Sale",
        "ru": "⚡ Flash Sale"
    },

    # Mahsulot boshqarish
    "products_menu": {
        "uz": "📦 Mahsulotlar boshqaruvi:",
        "ru": "📦 Управление товарами:"
    },
    "btn_categories": {
        "uz": "🗂 Kategoriyalar",
        "ru": "🗂 Категории"
    },
    "categories_list": {
        "uz": "🗂 Kategoriyalar ro'yxati:",
        "ru": "🗂 Список категорий:"
    },
    "no_categories": {
        "uz": "Hozircha kategoriyalar yo'q.",
        "ru": "Категорий пока нет."
    },
    "btn_add_category": {
        "uz": "➕ Yangi kategoriya",
        "ru": "➕ Новая категория"
    },
    "ask_category_name_uz": {
        "uz": "📝 Kategoriya nomini o'zbekcha kiriting:",
        "ru": "📝 Введите название категории на узбекском:"
    },
    "ask_category_name_ru": {
        "uz": "📝 Kategoriya nomini ruscha kiriting:",
        "ru": "📝 Введите название категории на русском:"
    },
    "ask_category_desc_uz": {
        "uz": "📝 Tavsifni o'zbekcha kiriting (yoki /skip):",
        "ru": "📝 Введите описание на узбекском (или /skip):"
    },
    "ask_category_desc_ru": {
        "uz": "📝 Tavsifni ruscha kiriting (yoki /skip):",
        "ru": "📝 Введите описание на русском (или /skip):"
    },
    "ask_category_video": {
        "uz": "🎬 Video yuboring (ixtiyoriy, yoki /skip):",
        "ru": "🎬 Отправьте видео (необязательно, или /skip):"
    },
    "category_created": {
        "uz": "✅ Kategoriya muvaffaqiyatli yaratildi!",
        "ru": "✅ Категория успешно создана!"
    },
    "category_deleted": {
        "uz": "✅ Kategoriya o'chirildi.",
        "ru": "✅ Категория удалена."
    },
    "btn_edit": {
        "uz": "✏️ Tahrirlash",
        "ru": "✏️ Редактировать"
    },
    "btn_delete": {
        "uz": "🗑 O'chirish",
        "ru": "🗑 Удалить"
    },
    "btn_toggle_active": {
        "uz": "🔄 Faol/Nofaol",
        "ru": "🔄 Активный/Неактивный"
    },
    "confirm_delete": {
        "uz": "❓ Rostdan o'chirishni xohlaysizmi?",
        "ru": "❓ Вы действительно хотите удалить?"
    },
    "btn_confirm": {
        "uz": "✅ Ha, o'chirish",
        "ru": "✅ Да, удалить"
    },
    "btn_cancel": {
        "uz": "❌ Bekor qilish",
        "ru": "❌ Отмена"
    },
    "action_cancelled": {
        "uz": "❌ Amal bekor qilindi.",
        "ru": "❌ Действие отменено."
    },

    # Mahsulot qo'shish
    "btn_add_product": {
        "uz": "➕ Yangi mahsulot",
        "ru": "➕ Новый товар"
    },
    "products_list": {
        "uz": "📦 Mahsulotlar:",
        "ru": "📦 Товары:"
    },
    "no_products": {
        "uz": "Bu kategoriyada mahsulotlar yo'q.",
        "ru": "В этой категории нет товаров."
    },
    "ask_product_name_uz": {
        "uz": "📝 Mahsulot nomini o'zbekcha kiriting:",
        "ru": "📝 Введите название товара на узбекском:"
    },
    "ask_product_name_ru": {
        "uz": "📝 Mahsulot nomini ruscha kiriting:",
        "ru": "📝 Введите название товара на русском:"
    },
    "ask_product_desc_uz": {
        "uz": "📝 Tavsifni o'zbekcha kiriting (yoki /skip):",
        "ru": "📝 Введите описание на узбекском (или /skip):"
    },
    "ask_product_desc_ru": {
        "uz": "📝 Tavsifni ruscha kiriting (yoki /skip):",
        "ru": "📝 Введите описание на русском (или /skip):"
    },
    "ask_product_warranty": {
        "uz": "🛡 Kafolat bormi?\n✅ Ha / ❌ Yo'q",
        "ru": "🛡 Есть гарантия?\n✅ Да / ❌ Нет"
    },
    "btn_warranty_yes": {
        "uz": "✅ Ha",
        "ru": "✅ Да"
    },
    "btn_warranty_no": {
        "uz": "❌ Yo'q",
        "ru": "❌ Нет"
    },
    "ask_warranty_days": {
        "uz": "📅 Kafolat necha kun davom etadi? (raqam kiriting):",
        "ru": "📅 Сколько дней длится гарантия? (введите число):"
    },
    "ask_product_video": {
        "uz": "🎬 Mahsulot videosi (ixtiyoriy, yoki /skip):",
        "ru": "🎬 Видео товара (необязательно, или /skip):"
    },
    "product_created": {
        "uz": "✅ Mahsulot yaratildi! Endi narx tierlarini qo'shing.",
        "ru": "✅ Товар создан! Теперь добавьте ценовые тиры."
    },
    "product_deleted": {
        "uz": "✅ Mahsulot o'chirildi.",
        "ru": "✅ Товар удалён."
    },

    # Narx tier qo'shish
    "prices_menu": {
        "uz": "💰 Narx tierlari:",
        "ru": "💰 Ценовые тиры:"
    },
    "btn_add_price": {
        "uz": "➕ Narx qo'shish",
        "ru": "➕ Добавить цену"
    },
    "ask_tier_select": {
        "uz": "⏱ Davomiylik tierini tanlang:",
        "ru": "⏱ Выберите тир длительности:"
    },
    "ask_price": {
        "uz": "💵 Sotish narxini kiriting (so'm):",
        "ru": "💵 Введите цену продажи (сум):"
    },
    "ask_cost_price": {
        "uz": "💴 Tannarxini kiriting (so'm, foyda uchun):",
        "ru": "💴 Введите себестоимость (сум, для прибыли):"
    },
    "price_created": {
        "uz": "✅ Narx tier qo'shildi!",
        "ru": "✅ Ценовой тир добавлен!"
    },
    "no_prices": {
        "uz": "Hozircha narxlar yo'q.",
        "ru": "Цен пока нет."
    },

    # Akkaunt qo'shish
    "accounts_menu": {
        "uz": "📊 Akkauntlar:",
        "ru": "📊 Аккаунты:"
    },
    "btn_add_account": {
        "uz": "➕ Akkaunt qo'shish",
        "ru": "➕ Добавить аккаунт"
    },
    "btn_bulk_accounts": {
        "uz": "📥 Bulk qo'shish",
        "ru": "📥 Массовое добавление"
    },
    "ask_account_login": {
        "uz": "👤 Login kiriting:",
        "ru": "👤 Введите логин:"
    },
    "ask_account_password": {
        "uz": "🔑 Parol kiriting:",
        "ru": "🔑 Введите пароль:"
    },
    "ask_account_expiry": {
        "uz": "📅 Muddat tugash sanasini kiriting (YYYY-MM-DD):",
        "ru": "📅 Введите дату истечения (YYYY-MM-DD):"
    },
    "ask_account_supplier": {
        "uz": "🏪 Yetkazib beruvchi nomini kiriting (yoki /skip):",
        "ru": "🏪 Введите название поставщика (или /skip):"
    },
    "ask_account_additional": {
        "uz": "📎 Qo'shimcha ma'lumot kiriting (yoki /skip):",
        "ru": "📎 Введите дополнительные данные (или /skip):"
    },
    "account_created": {
        "uz": "✅ Akkaunt qo'shildi!\n📅 Qolgan: {days} kun\n📊 Tier: {tier}",
        "ru": "✅ Аккаунт добавлен!\n📅 Осталось: {days} дней\n📊 Тир: {tier}"
    },
    "no_price_for_tier_warning": {
        "uz": "⚠️ Bu tier uchun narx belgilanmagan! Iltimos, avval narx qo'shing.",
        "ru": "⚠️ Для этого тира цена не установлена! Пожалуйста, сначала добавьте цену."
    },
    "ask_bulk_accounts": {
        "uz": "📥 Akkauntlarni kiriting (har qator bitta):\nFormat: login:parol:YYYY-MM-DD\nYoki: login:parol:YYYY-MM-DD:supplier_nomi",
        "ru": "📥 Введите аккаунты (каждый с новой строки):\nФормат: логин:пароль:YYYY-MM-DD\nИли: логин:пароль:YYYY-MM-DD:поставщик"
    },
    "bulk_result": {
        "uz": "📊 Natija:\n✅ Qo'shildi: {added}\n❌ Xatolar: {errors}",
        "ru": "📊 Результат:\n✅ Добавлено: {added}\n❌ Ошибки: {errors}"
    },
    "invalid_date_format": {
        "uz": "❌ Noto'g'ri sana formati! YYYY-MM-DD ko'rinishida kiriting.",
        "ru": "❌ Неверный формат даты! Введите в формате YYYY-MM-DD."
    },
    "invalid_number": {
        "uz": "❌ Raqam kiriting!",
        "ru": "❌ Введите число!"
    },

    # Admin rollar
    "roles_menu": {
        "uz": "👥 Adminlar ro'yxati:",
        "ru": "👥 Список администраторов:"
    },
    "btn_add_admin": {
        "uz": "➕ Admin qo'shish",
        "ru": "➕ Добавить администратора"
    },
    "ask_admin_id": {
        "uz": "👤 Admin Telegram ID sini kiriting:",
        "ru": "👤 Введите Telegram ID администратора:"
    },
    "ask_admin_role": {
        "uz": "🔑 Rol tanlang:",
        "ru": "🔑 Выберите роль:"
    },
    "admin_created": {
        "uz": "✅ Admin qo'shildi!",
        "ru": "✅ Администратор добавлен!"
    },
    "admin_deleted": {
        "uz": "✅ Admin o'chirildi.",
        "ru": "✅ Администратор удалён."
    },
    "no_admins": {
        "uz": "Hozircha adminlar yo'q.",
        "ru": "Администраторов пока нет."
    },

    # Xatolar
    "error_general": {
        "uz": "❌ Xato yuz berdi. Iltimos, qayta urinib ko'ring.",
        "ru": "❌ Произошла ошибка. Пожалуйста, попробуйте снова."
    },
    "access_denied": {
        "uz": "🚫 Sizda bu amalni bajarish huquqi yo'q.",
        "ru": "🚫 У вас нет прав для выполнения этого действия."
    },
    "not_found": {
        "uz": "❌ Ma'lumot topilmadi.",
        "ru": "❌ Данные не найдены."
    },
}


def t(key: str, lang: str = "uz", **kwargs) -> str:
    """
    Matnni tilga qarab qaytaradi.
    kwargs bilan format qo'llanilishi mumkin.
    """
    lang = lang if lang in ("uz", "ru") else "uz"
    text_dict = TEXTS.get(key, {})
    text = text_dict.get(lang, text_dict.get("uz", key))
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            pass
    return text
