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
              "{payment_info}\n\n"
              "📸 Chekni shu yerga yuboring\n"
              "⏳ 30 daqiqa vaqtingiz bor!",
        "ru": "✅ Заказ #{order_id} создан!\n"
              "⬜⬜⬜⬜ Ожидание оплаты\n\n"
              "💰 {amount:,} сум\n"
              "{payment_info}\n\n"
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
        "uz": "• {name} x{qty}\n  Login: <code>{login}</code>\n  Parol: <code>{password}</code>\n  Muddat: {expiry}",
        "ru": "• {name} x{qty}\n  Логин: <code>{login}</code>\n  Пароль: <code>{password}</code>\n  До: {expiry}"
    },
    "order_item_pending": {
        "uz": "• {name} x{qty} — kutilmoqda",
        "ru": "• {name} x{qty} — ожидается"
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
        "uz": "🛒 Sotish: <b>{name}</b>\n"
              "📊 Mavjud: {available} ta\n"
              "🔢 Birinchi: #{acc_id} ({days} kun)\n\n"
              "👤 Login: <code>{login}</code>\n"
              "🔑 Parol: <code>{password}</code>\n"
              "📅 Muddat: {expiry}\n\n"
              "🔗 Link: {link}",
        "ru": "🛒 Продажа: <b>{name}</b>\n"
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
        "uz": "• {name} — faqat <b>{cnt}</b> ta!",
        "ru": "• {name} — всего <b>{cnt}</b> шт!"
    },
    "stock_restored_notify": {
        "uz": "🔔 <b>{name}</b> yana sotuvda!\n💰 {price:,} so'm\n\nTez oling — tez tugaydi! 🔥",
        "ru": "🔔 <b>{name}</b> снова в наличии!\n💰 {price:,} сум\n\nБерите скорей — быстро разбирают! 🔥"
    },
    "btn_buy_now": {
        "uz": "🛒 Xarid qilish",
        "ru": "🛒 Купить"
    },
    # ==================== ALMASHTIRISH (REPLACEMENT) ====================
    "replacement_menu": {
        "uz": "🔄 <b>Almashtirish</b>\n\nGarantiya muddatida ishlamay qolgan hisobni almashtirish uchun so'rov yuboring.",
        "ru": "🔄 <b>Замена</b>\n\nОтправьте заявку на замену неработающего аккаунта в гарантийный период."
    },
    "replacement_select_item": {
        "uz": "Qaysi buyurtmani almashtirmoqchisiz?",
        "ru": "Какой заказ хотите заменить?"
    },
    "replacement_no_items": {
        "uz": "❌ Almashtirish mumkin bo'lgan buyurtma yo'q.",
        "ru": "❌ Нет заказов, доступных для замены."
    },
    "replacement_select_reason": {
        "uz": "Sabab tanlang:",
        "ru": "Выберите причину:"
    },
    "replacement_reason_not_work": {
        "uz": "❌ Ishlamayapti",
        "ru": "❌ Не работает"
    },
    "replacement_reason_wrong": {
        "uz": "⚠️ Noto'g'ri hisob",
        "ru": "⚠️ Неверный аккаунт"
    },
    "replacement_reason_expired": {
        "uz": "⏰ Muddatidan oldin tugadi",
        "ru": "⏰ Истёк раньше срока"
    },
    "replacement_reason_other": {
        "uz": "💬 Boshqa",
        "ru": "💬 Другое"
    },
    "replacement_enter_description": {
        "uz": "Muammoni batafsil yozing:",
        "ru": "Опишите проблему подробнее:"
    },
    "replacement_send_screenshot": {
        "uz": "📸 Skrinshotni yuboring (ixtiyoriy):\n/skip — o'tkazib yuborish",
        "ru": "📸 Отправьте скриншот (необязательно):\n/skip — пропустить"
    },
    "replacement_sent": {
        "uz": "✅ So'rovingiz qabul qilindi! Operator tez orada ko'rib chiqadi.",
        "ru": "✅ Ваша заявка принята! Оператор рассмотрит в ближайшее время."
    },
    "replacement_new_request": {
        "uz": "🔄 <b>Yangi almashtirish so'rovi</b>\n\nFoydalanuvchi: {user}\nBuyurtma: #{order_id}\nMahsulot: {product}\nSabab: {reason}\nIzoh: {description}",
        "ru": "🔄 <b>Новая заявка на замену</b>\n\nПользователь: {user}\nЗаказ: #{order_id}\nТовар: {product}\nПричина: {reason}\nОписание: {description}"
    },
    "replacement_approved": {
        "uz": "✅ Almashtirishingiz tasdiqlandi!\n\n🔑 Login: <code>{login}</code>\n🔒 Parol: <code>{password}</code>\n📅 Muddati: {expiry}",
        "ru": "✅ Ваша замена одобрена!\n\n🔑 Логин: <code>{login}</code>\n🔒 Пароль: <code>{password}</code>\n📅 Срок: {expiry}"
    },
    "replacement_rejected": {
        "uz": "❌ Almashtirishingiz rad etildi.\n\nSabab: {reason}",
        "ru": "❌ Ваша замена отклонена.\n\nПричина: {reason}"
    },
    "btn_approve_replacement": {
        "uz": "✅ Tasdiqlash",
        "ru": "✅ Одобрить"
    },
    "btn_reject_replacement": {
        "uz": "❌ Rad etish",
        "ru": "❌ Отклонить"
    },

    # ==================== VIP ====================
    "vip_page": {
        "uz": "👑 <b>VIP Dastur</b>\n\nDarajangiz: <b>{level}</b>\nJami xarid: <b>{total:,} so'm</b>\nChegaracha: <b>{next:,} so'm</b>\n\n{bar}\n\n<b>Joriy chegirma: {discount}%</b>",
        "ru": "👑 <b>VIP Программа</b>\n\nВаш уровень: <b>{level}</b>\nВсего покупок: <b>{total:,} сум</b>\nДо следующего: <b>{next:,} сум</b>\n\n{bar}\n\n<b>Текущая скидка: {discount}%</b>"
    },
    "vip_levels": {
        "uz": "📊 <b>VIP Darajalar:</b>\n\n🥉 Bronze — 500,000 so'mdan | 3% chegirma\n🥈 Silver — 2,000,000 so'mdan | 5% chegirma\n🥇 Gold — 5,000,000 so'mdan | 8% chegirma\n💎 Platinum — 10,000,000 so'mdan | 12% chegirma",
        "ru": "📊 <b>VIP Уровни:</b>\n\n🥉 Bronze — от 500,000 сум | скидка 3%\n🥈 Silver — от 2,000,000 сум | скидка 5%\n🥇 Gold — от 5,000,000 сум | скидка 8%\n💎 Platinum — от 10,000,000 сум | скидка 12%"
    },
    "vip_none": {
        "uz": "Oddiy foydalanuvchi",
        "ru": "Обычный пользователь"
    },
    "btn_vip_levels": {
        "uz": "📊 Barcha darajalar",
        "ru": "📊 Все уровни"
    },

    # ==================== SEVIMLIlar (FAVORITES) ====================
    "favorites_page": {
        "uz": "❤️ <b>Sevimlilar</b>\n\nSaqlab qo'ygan mahsulotlaringiz:",
        "ru": "❤️ <b>Избранное</b>\n\nВаши сохранённые товары:"
    },
    "favorites_empty": {
        "uz": "❤️ Sevimlilar bo'sh.\n\nMahsulot kartasidagi ❤️ tugmasini bosib qo'shing.",
        "ru": "❤️ Избранное пусто.\n\nНажмите ❤️ на карточке товара, чтобы добавить."
    },
    "favorites_added": {
        "uz": "❤️ Sevimlilarga qo'shildi!",
        "ru": "❤️ Добавлено в избранное!"
    },
    "favorites_removed": {
        "uz": "🗑 Sevimlilardan o'chirildi.",
        "ru": "🗑 Удалено из избранного."
    },
    "btn_favorites": {
        "uz": "❤️ Sevimlilar",
        "ru": "❤️ Избранное"
    },
    "btn_fav_add_cart": {
        "uz": "🛒 Savatga",
        "ru": "🛒 В корзину"
    },
    "btn_fav_notify": {
        "uz": "🔔 Xabar",
        "ru": "🔔 Уведомить"
    },
    "btn_remove_fav": {
        "uz": "🗑 O'chirish",
        "ru": "🗑 Удалить"
    },

    # ==================== SHARHLAR (REVIEWS) ====================
    "review_request": {
        "uz": "⭐ <b>{product}</b> mahsulotini baholang!\n\nSifat haqida fikringiz muhim.",
        "ru": "⭐ Оцените товар <b>{product}</b>!\n\nВаше мнение о качестве важно."
    },
    "review_comment_prompt": {
        "uz": "✍️ Izoh yozing (ixtiyoriy):\n/skip — o'tkazib yuborish",
        "ru": "✍️ Напишите комментарий (необязательно):\n/skip — пропустить"
    },
    "review_thanks": {
        "uz": "✅ Rahmat! Sharhingiz qabul qilindi.",
        "ru": "✅ Спасибо! Ваш отзыв принят."
    },
    "review_already_done": {
        "uz": "Siz allaqachon baho bergansiz.",
        "ru": "Вы уже оставили оценку."
    },
    "btn_review_skip": {
        "uz": "➡️ O'tkazib yuborish",
        "ru": "➡️ Пропустить"
    },

    # ==================== REFERRAL ====================
    "referral_page": {
        "uz": "🤝 <b>Do'stlarni taklif qil</b>\n\nSizning havolangiz:\n<code>{link}</code>\n\nTaklif qilinganlar: <b>{count}</b>\n\nDo'stingiz birinchi xarid qilganda <b>{bonus}</b> so'mlik promo-kod olasiz!",
        "ru": "🤝 <b>Пригласи друзей</b>\n\nВаша ссылка:\n<code>{link}</code>\n\nПриглашено: <b>{count}</b>\n\nПри первой покупке друга получите промокод на <b>{bonus}</b> сум!"
    },
    "referral_welcome": {
        "uz": "🎁 Siz do'stingiz tavsiyasi bilan keldingiz! Birinchi xariddan keyin bonus olasiz.",
        "ru": "🎁 Вы пришли по реферальной ссылке! После первой покупки получите бонус."
    },
    "referral_bonus_given": {
        "uz": "🎁 Do'stingiz xarid qildi! Promo-kod: <code>{code}</code> — {discount}% chegirma",
        "ru": "🎁 Ваш друг совершил покупку! Промокод: <code>{code}</code> — скидка {discount}%"
    },
    "btn_copy_referral": {
        "uz": "📋 Havola nusxalash",
        "ru": "📋 Скопировать ссылку"
    },
    "btn_referral": {
        "uz": "🤝 Referral",
        "ru": "🤝 Реферал"
    },

    # ==================== AUTO-RENEWAL ====================
    "auto_renewal_page": {
        "uz": "🔄 <b>Avtomatik yangilash</b>\n\nFaol yangilanishlar: <b>{count}</b>\n\nMuddati tugashidan 1 kun oldin avtomatik yangilanadi.",
        "ru": "🔄 <b>Автообновление</b>\n\nАктивных обновлений: <b>{count}</b>\n\nАвтоматически продлевается за 1 день до истечения."
    },
    "auto_renewal_enabled": {
        "uz": "✅ Avtomatik yangilash yoqildi.",
        "ru": "✅ Автообновление включено."
    },
    "auto_renewal_disabled": {
        "uz": "❌ Avtomatik yangilash o'chirildi.",
        "ru": "❌ Автообновление отключено."
    },
    "auto_renewal_executed": {
        "uz": "🔄 <b>{product}</b> avtomatik yangilandi!\n\n🔑 Login: <code>{login}</code>\n🔒 Parol: <code>{password}</code>\n📅 Yangi muddati: {expiry}",
        "ru": "🔄 <b>{product}</b> автоматически продлён!\n\n🔑 Логин: <code>{login}</code>\n🔒 Пароль: <code>{password}</code>\n📅 Новый срок: {expiry}"
    },
    "auto_renewal_failed": {
        "uz": "❌ <b>{product}</b> avtomatik yangilanmadi — stok tugagan.",
        "ru": "❌ <b>{product}</b> не удалось автоматически продлить — нет в наличии."
    },
    "btn_enable_renewal": {
        "uz": "🔄 Yoqish",
        "ru": "🔄 Включить"
    },
    "btn_disable_renewal": {
        "uz": "⏹ O'chirish",
        "ru": "⏹ Отключить"
    },
    "btn_auto_renewals": {
        "uz": "🔄 Avtomatik yangilash",
        "ru": "🔄 Автообновление"
    },

    # ==================== MOLIYA (FINANCE) ====================
    "finance_report": {
        "uz": "💰 <b>Moliyaviy hisobot</b> — {period}\n\n📈 Daromad: <b>{revenue:,} so'm</b>\n📉 Xarajat: <b>{expense:,} so'm</b>\n💵 Foyda: <b>{profit:,} so'm</b>\n📦 Buyurtmalar: <b>{orders}</b>\n🧾 O'rtacha chek: <b>{avg:,} so'm</b>",
        "ru": "💰 <b>Финансовый отчёт</b> — {period}\n\n📈 Доход: <b>{revenue:,} сум</b>\n📉 Расход: <b>{expense:,} сум</b>\n💵 Прибыль: <b>{profit:,} сум</b>\n📦 Заказов: <b>{orders}</b>\n🧾 Средний чек: <b>{avg:,} сум</b>"
    },
    "btn_finance": {
        "uz": "💰 Moliya",
        "ru": "💰 Финансы"
    },
    "btn_finance_today": {
        "uz": "📅 Bugun",
        "ru": "📅 Сегодня"
    },
    "btn_finance_week": {
        "uz": "📆 Hafta",
        "ru": "📆 Неделя"
    },
    "btn_finance_month": {
        "uz": "🗓 Oy",
        "ru": "🗓 Месяц"
    },
    "btn_add_expense": {
        "uz": "➕ Xarajat qo'shish",
        "ru": "➕ Добавить расход"
    },
    "expense_enter_amount": {
        "uz": "💸 Xarajat summasini kiriting (so'mda):",
        "ru": "💸 Введите сумму расхода (в сумах):"
    },
    "expense_enter_description": {
        "uz": "📝 Xarajat tavsifini kiriting:",
        "ru": "📝 Введите описание расхода:"
    },
    "expense_added": {
        "uz": "✅ Xarajat qo'shildi: {amount:,} so'm — {desc}",
        "ru": "✅ Расход добавлен: {amount:,} сум — {desc}"
    },

    # ==================== PROMO KODI ====================
    "promo_enter": {
        "uz": "🎟 Promo-kodni kiriting:",
        "ru": "🎟 Введите промокод:"
    },
    "promo_valid": {
        "uz": "✅ Promo-kod qo'llandi: <b>{discount}% chegirma</b>",
        "ru": "✅ Промокод применён: <b>скидка {discount}%</b>"
    },
    "promo_invalid": {
        "uz": "❌ Promo-kod noto'g'ri yoki muddati tugagan.",
        "ru": "❌ Промокод неверный или истёк."
    },
    "promo_list": {
        "uz": "🎟 <b>Promo-kodlar</b>\n\n{items}",
        "ru": "🎟 <b>Промокоды</b>\n\n{items}"
    },
    "promo_item": {
        "uz": "• <code>{code}</code> — {discount}% | {used}/{limit} | {status}",
        "ru": "• <code>{code}</code> — {discount}% | {used}/{limit} | {status}"
    },
    "promo_create_code": {
        "uz": "Promo-kod nomini kiriting:",
        "ru": "Введите название промокода:"
    },
    "promo_create_discount": {
        "uz": "Chegirma foizini kiriting (1-100):",
        "ru": "Введите процент скидки (1-100):"
    },
    "promo_create_limit": {
        "uz": "Foydalanish limitini kiriting (0 = cheksiz):",
        "ru": "Введите лимит использований (0 = без лимита):"
    },
    "promo_create_expiry": {
        "uz": "Muddatini kiriting (YYYY-MM-DD) yoki /skip:",
        "ru": "Введите срок действия (YYYY-MM-DD) или /skip:"
    },
    "promo_created": {
        "uz": "✅ Promo-kod yaratildi: <code>{code}</code>",
        "ru": "✅ Промокод создан: <code>{code}</code>"
    },
    "btn_create_promo": {
        "uz": "➕ Yangi promo-kod",
        "ru": "➕ Новый промокод"
    },
    "btn_promo_list": {
        "uz": "📋 Promo-kodlar",
        "ru": "📋 Промокоды"
    },

    # ==================== FLASH SALE ====================
    "flash_sale_active": {
        "uz": "⚡ <b>FLASH SALE!</b>\n\n{product} — <b>{discount}%</b> chegirma!\n⏳ {time_left} gacha",
        "ru": "⚡ <b>FLASH SALE!</b>\n\n{product} — скидка <b>{discount}%</b>!\n⏳ До {time_left}"
    },
    "flash_sale_ended": {
        "uz": "Flash sale tugadi.",
        "ru": "Flash sale завершён."
    },
    "flash_sale_create_product": {
        "uz": "Flash sale uchun mahsulotni tanlang:",
        "ru": "Выберите товар для flash sale:"
    },
    "flash_sale_create_discount": {
        "uz": "Chegirma foizini kiriting:",
        "ru": "Введите процент скидки:"
    },
    "flash_sale_create_duration": {
        "uz": "Davomiyligini soatlarda kiriting:",
        "ru": "Введите длительность в часах:"
    },
    "flash_sale_created": {
        "uz": "✅ Flash sale boshlandi! {discount}% chegirma {hours} soat davomida.",
        "ru": "✅ Flash sale запущен! Скидка {discount}% на {hours} часов."
    },
    "btn_create_flash_sale": {
        "uz": "⚡ Flash Sale",
        "ru": "⚡ Flash Sale"
    },

    # ==================== BUNDLE ====================
    "bundles_page": {
        "uz": "📦 <b>To'plamlar</b>\n\nMaxsus narxdagi mahsulotlar to'plami:",
        "ru": "📦 <b>Наборы</b>\n\nКомплекты товаров по специальной цене:"
    },
    "bundle_detail": {
        "uz": "📦 <b>{name}</b>\n\n{description}\n\nTarkib: {items}\n\n💰 Umumiy narx: <s>{original:,}</s> <b>{price:,} so'm</b>\n📉 Tejash: {saving:,} so'm",
        "ru": "📦 <b>{name}</b>\n\n{description}\n\nСостав: {items}\n\n💰 Итоговая цена: <s>{original:,}</s> <b>{price:,} сум</b>\n📉 Экономия: {saving:,} сум"
    },
    "bundle_empty": {
        "uz": "📦 Hozircha to'plamlar yo'q.",
        "ru": "📦 Наборов пока нет."
    },
    "bundle_added_to_cart": {
        "uz": "✅ To'plam savatga qo'shildi!",
        "ru": "✅ Набор добавлен в корзину!"
    },
    "btn_buy_bundle": {
        "uz": "🛒 Savatga qo'shish",
        "ru": "🛒 Добавить в корзину"
    },
    "btn_bundles": {
        "uz": "📦 To'plamlar",
        "ru": "📦 Наборы"
    },
    "bundle_create_name": {
        "uz": "To'plam nomini kiriting:",
        "ru": "Введите название набора:"
    },
    "bundle_create_desc": {
        "uz": "Tavsifini kiriting:",
        "ru": "Введите описание:"
    },
    "bundle_create_price": {
        "uz": "To'plam narxini kiriting (so'mda):",
        "ru": "Введите цену набора (в сумах):"
    },
    "bundle_created": {
        "uz": "✅ To'plam yaratildi: {name}",
        "ru": "✅ Набор создан: {name}"
    },

    # ==================== BROADCAST ====================
    "broadcast_enter_text": {
        "uz": "📢 Xabar matnini kiriting:\n(Rasmli xabar uchun rasm + matn yuboring)",
        "ru": "📢 Введите текст сообщения:\n(Для сообщения с фото отправьте фото + текст)"
    },
    "broadcast_confirm": {
        "uz": "📢 <b>Xabarni yuborishni tasdiqlang</b>\n\nFoydalanuvchilar soni: <b>{count}</b>\n\nPreview:",
        "ru": "📢 <b>Подтвердите отправку</b>\n\nПользователей: <b>{count}</b>\n\nПревью:"
    },
    "broadcast_sending": {
        "uz": "📤 Yuborilmoqda... {sent}/{total}",
        "ru": "📤 Отправляется... {sent}/{total}"
    },
    "broadcast_done": {
        "uz": "✅ Xabar yuborildi!\n✅ Muvaffaqiyat: {success}\n❌ Xato: {failed}",
        "ru": "✅ Рассылка завершена!\n✅ Успешно: {success}\n❌ Ошибок: {failed}"
    },
    "btn_broadcast": {
        "uz": "📢 Xabar yuborish",
        "ru": "📢 Рассылка"
    },
    "btn_confirm_broadcast": {
        "uz": "✅ Yuborish",
        "ru": "✅ Отправить"
    },

    # ==================== KONTAKT / OPERATOR ====================
    "contact_page": {
        "uz": "💬 <b>Operator bilan bog'lanish</b>\n\nSavolingizni yozing, operator javob beradi.",
        "ru": "💬 <b>Связь с оператором</b>\n\nНапишите ваш вопрос, оператор ответит."
    },
    "contact_enter_question": {
        "uz": "✍️ Savolingizni yozing:",
        "ru": "✍️ Напишите ваш вопрос:"
    },
    "contact_sent": {
        "uz": "✅ Savolingiz yuborildi! Operator tez orada javob beradi.",
        "ru": "✅ Ваш вопрос отправлен! Оператор ответит в ближайшее время."
    },
    "contact_new_message": {
        "uz": "💬 <b>Yangi savol</b>\n\nFoydalanuvchi: {user} (ID: {user_id})\nTil: {lang}\n\nSavol:\n{question}",
        "ru": "💬 <b>Новый вопрос</b>\n\nПользователь: {user} (ID: {user_id})\nЯзык: {lang}\n\nВопрос:\n{question}"
    },
    "contact_reply_prompt": {
        "uz": "Javob yozing:",
        "ru": "Напишите ответ:"
    },
    "contact_reply_sent": {
        "uz": "✅ Javob yuborildi.",
        "ru": "✅ Ответ отправлен."
    },
    "contact_operator_reply": {
        "uz": "💬 <b>Operator javobi:</b>\n\n{reply}",
        "ru": "💬 <b>Ответ оператора:</b>\n\n{reply}"
    },
    "btn_contact": {
        "uz": "💬 Operator",
        "ru": "💬 Оператор"
    },
    "btn_reply": {
        "uz": "↩️ Javob berish",
        "ru": "↩️ Ответить"
    },

    # ==================== MUDDATI ESLATMASI ====================
    "expiry_3days": {
        "uz": "⏰ <b>{product}</b> hisobingizning muddati 3 kunda tugaydi!\n📅 {expiry}\n\nYangilash uchun /start",
        "ru": "⏰ Срок аккаунта <b>{product}</b> истекает через 3 дня!\n📅 {expiry}\n\nДля продления /start"
    },
    "expiry_1day": {
        "uz": "🚨 <b>{product}</b> hisobingizning muddati ERTAGA tugaydi!\n📅 {expiry}",
        "ru": "🚨 Срок аккаунта <b>{product}</b> истекает ЗАВТРА!\n📅 {expiry}"
    },
    "expiry_today": {
        "uz": "🔴 <b>{product}</b> hisobingizning muddati BUGUN tugaydi!",
        "ru": "🔴 Срок аккаунта <b>{product}</b> истекает СЕГОДНЯ!"
    },

    # ==================== CROSS-SELL ====================
    "cross_sell": {
        "uz": "💡 <b>{product}</b> sotib olganlar buni ham yoqtirishdi:\n\n{recommendations}",
        "ru": "💡 Покупатели <b>{product}</b> также интересовались:\n\n{recommendations}"
    },
    "cross_sell_item": {
        "uz": "• {name} — {price:,} so'm",
        "ru": "• {name} — {price:,} сум"
    },

    # ==================== TARK ETILGAN SAVAT ====================
    "abandoned_cart_reminder": {
        "uz": "🛒 Savatchangizda {count} ta mahsulot qoldi!\n\nXaridni yakunlash uchun /start",
        "ru": "🛒 В вашей корзине осталось {count} товаров!\n\nЗавершите покупку /start"
    },

    # ==================== YANGI STRUKTURA UCHUN QO'SHIMCHALAR ====================
    "account_created_simple": {
        "uz": "✅ Akkaunt qo'shildi! Muddati: {days} kun",
        "ru": "✅ Аккаунт добавлен! Срок: {days} дней"
    },
    "ask_duration_text_uz": {
        "uz": "⏱ Muddat matnini kiriting (uz):\n\nMasalan: '1 oylik', '1 yillik'\n/skip — bo'sh qoldirish",
        "ru": "⏱ Введите текст срока (uz):\n\nНапример: '1 oylik', '1 yillik'\n/skip — пропустить"
    },
    "ask_duration_text_ru": {
        "uz": "⏱ Muddat matnini kiriting (ru):\n\nMasalan: '1 месяц', '1 год'\n/skip — bo'sh qoldirish",
        "ru": "⏱ Введите текст срока (ru):\n\nНапример: '1 месяц', '1 год'\n/skip — пропустить"
    },
    "added_to_cart_simple": {
        "uz": "✅ {name} savatga qo'shildi!",
        "ru": "✅ {name} добавлен в корзину!"
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
