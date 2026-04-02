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

    # ==================== KATALOG ====================
    "no_categories": {
        "uz": "Hozircha kategoriyalar yo'q.",
        "ru": "Категорий пока нет."
    },
    "select_category": {
        "uz": "📦 Kategoriyani tanlang:",
        "ru": "📦 Выберите категорию:"
    },
    "select_product": {
        "uz": "📦 Mahsulotni tanlang:",
        "ru": "📦 Выберите товар:"
    },
    "no_products_in_cat": {
        "uz": "Bu kategoriyada mahsulotlar yo'q.",
        "ru": "В этой категории нет товаров."
    },
    "btn_add_to_cart": {
        "uz": "🛒 Savatga",
        "ru": "🛒 В корзину"
    },
    "btn_add_favorite": {
        "uz": "⭐ Sevimlilarga",
        "ru": "⭐ В избранное"
    },
    "btn_remove_favorite": {
        "uz": "💔 Sevimlilardan",
        "ru": "💔 Из избранного"
    },
    "btn_notify_stock": {
        "uz": "🔔 Kelganda xabar",
        "ru": "🔔 Уведомить о наличии"
    },
    "stock_notify_set": {
        "uz": "✅ Mahsulot paydo bo'lganda xabar beramiz!",
        "ru": "✅ Уведомим когда товар появится!"
    },
    "added_to_favorites": {
        "uz": "⭐ Sevimlilarga qo'shildi!",
        "ru": "⭐ Добавлено в избранное!"
    },
    "removed_from_favorites": {
        "uz": "💔 Sevimlilardan olib tashlandi.",
        "ru": "💔 Удалено из избранного."
    },
    "sold_out": {
        "uz": "Tugagan",
        "ru": "Нет в наличии"
    },
    "select_quantity": {
        "uz": "🔢 Nechta xarid qilasiz?\nMavjud: {available} ta",
        "ru": "🔢 Сколько купить?\nДоступно: {available} шт"
    },
    "enter_quantity": {
        "uz": "✏️ Miqdorni kiriting (1-{max}):",
        "ru": "✏️ Введите количество (1-{max}):"
    },
    "qty_exceeds_stock": {
        "uz": "❌ Faqat {available} ta mavjud!",
        "ru": "❌ Доступно только {available} шт!"
    },
    "qty_invalid": {
        "uz": "❌ Noto'g'ri son! 1 dan {max} gacha kiriting.",
        "ru": "❌ Неверное число! Введите от 1 до {max}."
    },
    "added_to_cart": {
        "uz": "✅ {name} ({tier}) x{qty} savatga qo'shildi!",
        "ru": "✅ {name} ({tier}) x{qty} добавлено в корзину!"
    },
    "btn_view_cart": {
        "uz": "🛒 Savatni ko'rish",
        "ru": "🛒 Посмотреть корзину"
    },
    "btn_continue": {
        "uz": "🛍 Davom ettirish",
        "ru": "🛍 Продолжить покупки"
    },
    "in_cart_badge": {
        "uz": "🛒 Savatda: {qty} dona ({tier})",
        "ru": "🛒 В корзине: {qty} шт ({tier})"
    },

    # ==================== SAVAT ====================
    "cart_title": {
        "uz": "🛒 Sizning savatingiz:",
        "ru": "🛒 Ваша корзина:"
    },
    "cart_empty": {
        "uz": "🛒 Savat bo'sh.\n\n📦 Mahsulotlarni ko'rish uchun tugmani bosing.",
        "ru": "🛒 Корзина пуста.\n\n📦 Нажмите кнопку для просмотра товаров."
    },
    "cart_vip_line": {
        "uz": "💎 VIP: {vip_name} ({pct}% chegirma)",
        "ru": "💎 VIP: {vip_name} ({pct}% скидка)"
    },
    "cart_item_line": {
        "uz": "{num}. {name} ({tier}) x{qty} — {price:,} so'm",
        "ru": "{num}. {name} ({tier}) x{qty} — {price:,} сум"
    },
    "cart_total": {
        "uz": "💰 Jami: {total:,} so'm",
        "ru": "💰 Итого: {total:,} сум"
    },
    "cart_discount_line": {
        "uz": "{icon} {label}: -{pct}% (-{amount:,} so'm)",
        "ru": "{icon} {label}: -{pct}% (-{amount:,} сум)"
    },
    "cart_final": {
        "uz": "💰 To'lov: {final:,} so'm",
        "ru": "💰 К оплате: {final:,} сум"
    },
    "btn_promo": {
        "uz": "🏷 Promo-kod",
        "ru": "🏷 Промо-код"
    },
    "btn_clear_cart": {
        "uz": "🗑 Tozalash",
        "ru": "🗑 Очистить"
    },
    "btn_checkout": {
        "uz": "✅ Buyurtma berish",
        "ru": "✅ Оформить заказ"
    },
    "ask_promo_code": {
        "uz": "🏷 Promo kodingizni kiriting:",
        "ru": "🏷 Введите промо-код:"
    },
    "promo_valid": {
        "uz": "✅ Promo kod qo'llanildi! -{pct}% chegirma",
        "ru": "✅ Промо-код применён! -{pct}% скидка"
    },
    "promo_invalid": {
        "uz": "❌ Promo kod yaroqsiz yoki muddati o'tgan.",
        "ru": "❌ Промо-код недействителен или истёк."
    },
    "cart_cleared": {
        "uz": "🗑 Savat tozalandi.",
        "ru": "🗑 Корзина очищена."
    },

    # ==================== BUYURTMA ====================
    "order_creating": {
        "uz": "⏳ Buyurtma yaratilmoqda...",
        "ru": "⏳ Создание заказа..."
    },
    "order_insufficient_stock": {
        "uz": "❌ Yetarli akkaunt yo'q!\n{details}\n\nIltimos, miqdorni kamaytiring yoki keyinroq urinib ko'ring.",
        "ru": "❌ Недостаточно аккаунтов!\n{details}\n\nПожалуйста, уменьшите количество или попробуйте позже."
    },
    "order_created_progress": {
        "uz": "✅ Buyurtma #{order_id} yaratildi!\n"
              "⬜⬜⬜⬜ To'lov kutilmoqda\n\n"
              "💰 {amount:,} so'm\n"
              "💳 Click: {click}\n"
              "💳 Payme: {payme}\n\n"
              "📸 Chekni shu yerga yuboring\n"
              "⏳ 30 daqiqa vaqtingiz bor!",
        "ru": "✅ Заказ #{order_id} создан!\n"
              "⬜⬜⬜⬜ Ожидание оплаты\n\n"
              "💰 {amount:,} сум\n"
              "💳 Click: {click}\n"
              "💳 Payme: {payme}\n\n"
              "📸 Отправьте чек сюда\n"
              "⏳ У вас 30 минут!"
    },
    "progress_pending": {
        "uz": "⬜⬜⬜⬜ To'lov kutilmoqda",
        "ru": "⬜⬜⬜⬜ Ожидание оплаты"
    },
    "progress_sent": {
        "uz": "🟩⬜⬜⬜ Chek yuborildi",
        "ru": "🟩⬜⬜⬜ Чек отправлен"
    },
    "progress_confirmed": {
        "uz": "🟩🟩🟩🟩 Tayyor!",
        "ru": "🟩🟩🟩🟩 Готово!"
    },
    "progress_partial": {
        "uz": "🟩🟩🟨⬜ Qisman tayyor",
        "ru": "🟩🟩🟨⬜ Частично готово"
    },
    "progress_cancelled": {
        "uz": "❌ Bekor qilindi",
        "ru": "❌ Отменён"
    },
    "payment_received": {
        "uz": "📸 Chekingiz qabul qilindi! Admin tezda tekshiradi.",
        "ru": "📸 Ваш чек принят! Администратор скоро проверит."
    },
    "order_delivered": {
        "uz": "✅ To'lov tasdiqlandi! Buyurtma #{order_id}\n🟩🟩🟩🟩 Tayyor!\n\n{accounts_text}",
        "ru": "✅ Оплата подтверждена! Заказ #{order_id}\n🟩🟩🟩🟩 Готово!\n\n{accounts_text}"
    },
    "account_delivery_line": {
        "uz": "{num}. <b>{name}</b>\n👤 Login: <code>{login}</code>\n🔑 Parol: <code>{password}</code>\n📅 Muddat: {expiry}",
        "ru": "{num}. <b>{name}</b>\n👤 Логин: <code>{login}</code>\n🔑 Пароль: <code>{password}</code>\n📅 До: {expiry}"
    },
    "order_cancelled_timeout": {
        "uz": "⏳ Buyurtma #{order_id} bekor qilindi (to'lov vaqti o'tdi).",
        "ru": "⏳ Заказ #{order_id} отменён (истекло время оплаты)."
    },
    "no_active_order": {
        "uz": "❌ Aktiv buyurtmangiz topilmadi. Avval mahsulot tanlang.",
        "ru": "❌ Активный заказ не найден. Сначала выберите товар."
    },
    "send_payment_screenshot": {
        "uz": "📸 To'lov chekini (screenshot) yuboring:",
        "ru": "📸 Отправьте скриншот чека оплаты:"
    },

    # ==================== ADMIN: GURUH XABARI ====================
    "group_payment_notify": {
        "uz": "💳 <b>To'lov cheki</b> — Buyurtma #{order_id}\n"
              "👤 {full_name} (@{username})\n"
              "💰 {amount:,} so'm\n\n"
              "{items_text}",
        "ru": "💳 <b>Чек оплаты</b> — Заказ #{order_id}\n"
              "👤 {full_name} (@{username})\n"
              "💰 {amount:,} сум\n\n"
              "{items_text}"
    },
    "btn_confirm_payment": {
        "uz": "✅ To'lovni tasdiqlash",
        "ru": "✅ Подтвердить оплату"
    },
    "btn_partial_confirm": {
        "uz": "🔶 Qisman tasdiqlash",
        "ru": "🔶 Частичное подтверждение"
    },
    "btn_reject_payment": {
        "uz": "❌ Rad etish",
        "ru": "❌ Отклонить"
    },
    "payment_confirmed_admin": {
        "uz": "✅ To'lov tasdiqlandi! Akkauntlar yuborildi.",
        "ru": "✅ Оплата подтверждена! Аккаунты отправлены."
    },
    "order_partial_text": {
        "uz": "🔶 Buyurtma #{order_id} — Qisman tasdiqlash\nHar bir element uchun tasdiqlang:",
        "ru": "🔶 Заказ #{order_id} — Частичное подтверждение\nПодтвердите каждый элемент:"
    },
    "partial_delivered_notify": {
        "uz": "📦 Buyurtma #{order_id}: {delivered} ta tayyor, {pending} ta kutilmoqda.\n🟩🟩🟨⬜\n\n{accounts_text}",
        "ru": "📦 Заказ #{order_id}: {delivered} готово, {pending} ожидается.\n🟩🟩🟨⬜\n\n{accounts_text}"
    },

    # ==================== MENING BUYURTMALARIM ====================
    "my_orders_title": {
        "uz": "📋 Buyurtmalarim:",
        "ru": "📋 Мои заказы:"
    },
    "no_orders": {
        "uz": "📋 Hozircha buyurtmalaringiz yo'q.",
        "ru": "📋 У вас пока нет заказов."
    },
    "order_status_pending": {
        "uz": "⬜ To'lov kutilmoqda",
        "ru": "⬜ Ожидание оплаты"
    },
    "order_status_sent": {
        "uz": "🟩 Chek yuborildi",
        "ru": "🟩 Чек отправлен"
    },
    "order_status_confirmed": {
        "uz": "✅ Yetkazildi",
        "ru": "✅ Доставлено"
    },
    "order_status_partial": {
        "uz": "🟡 Qisman yetkazildi",
        "ru": "🟡 Частично доставлено"
    },
    "order_status_cancelled": {
        "uz": "❌ Bekor qilindi",
        "ru": "❌ Отменён"
    },
    "order_detail": {
        "uz": "📋 Buyurtma #{order_id}\n"
              "Sana: {date}\n"
              "Status: {status}\n"
              "Summa: {amount:,} so'm\n\n"
              "{items}",
        "ru": "📋 Заказ #{order_id}\n"
              "Дата: {date}\n"
              "Статус: {status}\n"
              "Сумма: {amount:,} сум\n\n"
              "{items}"
    },
    "order_item_detail": {
        "uz": "• {name} ({tier}) x{qty}\n  Login: <code>{login}</code>\n  Parol: <code>{password}</code>\n  Muddat: {expiry}",
        "ru": "• {name} ({tier}) x{qty}\n  Логин: <code>{login}</code>\n  Пароль: <code>{password}</code>\n  До: {expiry}"
    },
    "order_item_pending": {
        "uz": "• {name} ({tier}) x{qty} — kutilmoqda",
        "ru": "• {name} ({tier}) x{qty} — ожидается"
    },
    "btn_instruction_video": {
        "uz": "📹 Instruksiya",
        "ru": "📹 Инструкция"
    },
    "btn_prev_page": {
        "uz": "◀️",
        "ru": "◀️"
    },
    "btn_next_page": {
        "uz": "▶️",
        "ru": "▶️"
    },

    # ==================== DIRECT SALE ====================
    "ds_title": {
        "uz": "🛒 Direct Sale:",
        "ru": "🛒 Прямая продажа:"
    },
    "ds_account_info": {
        "uz": "🛒 Sotish: <b>{name}</b> ({tier})\n"
              "📊 Mavjud: {available} ta\n"
              "🔢 Birinchi: #{acc_id} ({days} kun)\n\n"
              "👤 Login: <code>{login}</code>\n"
              "🔑 Parol: <code>{password}</code>\n"
              "📅 Muddat: {expiry}\n\n"
              "🔗 Link: {link}",
        "ru": "🛒 Продажа: <b>{name}</b> ({tier})\n"
              "📊 Доступно: {available} шт\n"
              "🔢 Первый: #{acc_id} ({days} дней)\n\n"
              "👤 Логин: <code>{login}</code>\n"
              "🔑 Пароль: <code>{password}</code>\n"
              "📅 До: {expiry}\n\n"
              "🔗 Ссылка: {link}"
    },
    "btn_ds_copy": {
        "uz": "📋 Nusxalash",
        "ru": "📋 Скопировать"
    },
    "btn_ds_sold": {
        "uz": "✅ Sotildi",
        "ru": "✅ Продано"
    },
    "btn_ds_next": {
        "uz": "⏭ Keyingisi",
        "ru": "⏭ Следующий"
    },
    "ds_sold_success": {
        "uz": "✅ Akkaunt sotildi!",
        "ru": "✅ Аккаунт продан!"
    },
    "ds_no_accounts": {
        "uz": "❌ Bu mahsulot/tier uchun mavjud akkaunt yo'q.",
        "ru": "❌ Нет доступных аккаунтов для этого товара/тира."
    },
    "ds_link_expired": {
        "uz": "❌ Bu link eskirgan yoki akkaunt sotilgan.",
        "ru": "❌ Эта ссылка устарела или аккаунт уже продан."
    },
    "ds_account_delivered": {
        "uz": "📦 <b>{name}</b>\n"
              "👤 Login: <code>{login}</code>\n"
              "🔑 Parol: <code>{password}</code>\n"
              "📅 Muddat: {expiry}",
        "ru": "📦 <b>{name}</b>\n"
              "👤 Логин: <code>{login}</code>\n"
              "🔑 Пароль: <code>{password}</code>\n"
              "📅 До: {expiry}"
    },
    "btn_ds_select_cat": {
        "uz": "🛒 Sotuv — kategoriya tanlang:",
        "ru": "🛒 Продажа — выберите категорию:"
    },

    # ==================== FAQ ====================
    "faq_title": {
        "uz": "❓ Ko'p beriladigan savollar:",
        "ru": "❓ Часто задаваемые вопросы:"
    },
    "faq_q1": {
        "uz": "💳 Qanday to'lash mumkin?",
        "ru": "💳 Как оплатить?"
    },
    "faq_a1": {
        "uz": "💳 <b>To'lov usullari:</b>\n\n"
              "• Click orqali: 8600 xxxx xxxx xxxx\n"
              "• Payme orqali: 8600 xxxx xxxx xxxx\n\n"
              "To'lovdan so'ng chekni botga yuboring — admin tasdiqlaydi!",
        "ru": "💳 <b>Способы оплаты:</b>\n\n"
              "• Через Click: 8600 xxxx xxxx xxxx\n"
              "• Через Payme: 8600 xxxx xxxx xxxx\n\n"
              "После оплаты отправьте чек боту — администратор подтвердит!"
    },
    "faq_q2": {
        "uz": "⏰ Qancha vaqtda yetkaziladi?",
        "ru": "⏰ Как быстро доставляют?"
    },
    "faq_a2": {
        "uz": "⏰ <b>Yetkazish vaqti:</b>\n\n"
              "To'lov tasdiqlangandan keyin <b>5 daqiqa ichida</b> avtomatik yuboriladi!\n\n"
              "Ish vaqtida (09:00-22:00) tezroq bo'ladi.",
        "ru": "⏰ <b>Время доставки:</b>\n\n"
              "После подтверждения оплаты — <b>в течение 5 минут</b> автоматически!\n\n"
              "В рабочее время (09:00-22:00) быстрее."
    },
    "faq_q3": {
        "uz": "🛡 Kafolat qanday ishlaydi?",
        "ru": "🛡 Как работает гарантия?"
    },
    "faq_a3": {
        "uz": "🛡 <b>Kafolat:</b>\n\n"
              "Agar akkaunt ishlamasa yoki ban yesa — <b>bepul almashtiramiz!</b>\n\n"
              "Kafolat muddati mahsulot sahifasida ko'rsatilgan.",
        "ru": "🛡 <b>Гарантия:</b>\n\n"
              "Если аккаунт не работает или забанен — <b>заменим бесплатно!</b>\n\n"
              "Срок гарантии указан на странице товара."
    },
    "faq_q4": {
        "uz": "🔄 Akkaunt ishlamasa nima qilaman?",
        "ru": "🔄 Что делать если аккаунт не работает?"
    },
    "faq_a4": {
        "uz": "🔄 <b>Akkaunt ishlamasa:</b>\n\n"
              "1. «📋 Buyurtmalarim» → buyurtmani tanlang\n"
              "2. «🔄 Almashtirish» tugmasini bosing\n"
              "3. Muammoni tasvirlab yozing\n\n"
              "Admin kafolat muddatida bepul almashtiradi!",
        "ru": "🔄 <b>Если аккаунт не работает:</b>\n\n"
              "1. «📋 Мои заказы» → выберите заказ\n"
              "2. Нажмите «🔄 Замена»\n"
              "3. Опишите проблему\n\n"
              "Admin заменит бесплатно в течение гарантийного срока!"
    },
    "faq_q5": {
        "uz": "💰 Nega bunchalik arzon?",
        "ru": "💰 Почему так дёшево?"
    },
    "faq_a5": {
        "uz": "💰 <b>Nega arzon?</b>\n\n"
              "Biz akkauntlarni ulgurji sotib olamiz va foydani minimal qilib mijozlarga uzatamiz.\n\n"
              "Sifat va kafolat — birinchi o'rinda! 🛡",
        "ru": "💰 <b>Почему дёшево?</b>\n\n"
              "Мы закупаем аккаунты оптом и передаём выгоду клиентам с минимальной наценкой.\n\n"
              "Качество и гарантия — на первом месте! 🛡"
    },
    "faq_q6": {
        "uz": "📦 Qaysi mahsulotlar bor?",
        "ru": "📦 Какие товары есть?"
    },
    "faq_a6": {
        "uz": "📦 <b>Bizning mahsulotlar:</b>\n\n"
              "Canva Pro, Spotify, YouTube Premium, Netflix, ChatGPT Plus va boshqalar.\n\n"
              "«📦 Obunalar» bo'limidan to'liq ro'yxatni ko'ring!",
        "ru": "📦 <b>Наши товары:</b>\n\n"
              "Canva Pro, Spotify, YouTube Premium, Netflix, ChatGPT Plus и другие.\n\n"
              "Полный список — в разделе «📦 Подписки»!"
    },
    "faq_back": {
        "uz": "⬅️ FAQ ga qaytish",
        "ru": "⬅️ К вопросам"
    },
    "btn_go_catalog": {
        "uz": "📦 Mahsulotlar",
        "ru": "📦 Товары"
    },

    # ==================== STOK OGOHLANTIRISHLARI ====================
    "low_stock_admin": {
        "uz": "⚠️ <b>STOK OGOHLANTIRISH:</b>\n\n{items}",
        "ru": "⚠️ <b>УВЕДОМЛЕНИЕ О ЗАПАСАХ:</b>\n\n{items}"
    },
    "low_stock_item": {
        "uz": "• {name} ({tier}) — faqat <b>{cnt}</b> ta!",
        "ru": "• {name} ({tier}) — всего <b>{cnt}</b> шт!"
    },
    "stock_restored_notify": {
        "uz": "🔔 <b>{name}</b> ({tier}) yana sotuvda!\n💰 {price:,} so'm\n\nTez oling — tez tugaydi! 🔥",
        "ru": "🔔 <b>{name}</b> ({tier}) снова в наличии!\n💰 {price:,} сум\n\nБерите скорей — быстро разбирают! 🔥"
    },
    "btn_buy_now": {
        "uz": "🛒 Xarid qilish",
        "ru": "🛒 Купить"
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
