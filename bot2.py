import sqlite3
import random
import string
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Bot configuration
TOKEN = "7003492468:AAGFKDDs9nKv3C9XqY3xWHWO9eddoqmvp3A"
CHANNEL_ID = -1002740723606
DB_FILE = "referral_bot.db"
ADMIN_USERNAME = "heleromana"

# Initialize the database schema
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("PRAGMA foreign_keys = ON")
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        referral_code TEXT UNIQUE,
        invited_count INTEGER DEFAULT 0,
        phone_number TEXT
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS referrals (
        invited_user_id INTEGER PRIMARY KEY,
        referrer_id INTEGER,
        joined_channel INTEGER DEFAULT 0,
        FOREIGN KEY (referrer_id) REFERENCES users(user_id)
    )
    """)
    conn.commit()
    conn.close()

# Generate or fetch a user's referral code
def generate_referral_code():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

def get_or_create_user(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT referral_code FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    if row:
        code = row[0]
    else:
        code = generate_referral_code()
        c.execute("INSERT INTO users (user_id, referral_code) VALUES (?, ?)", (user_id, code))
        conn.commit()
    conn.close()
    return code

# /start handler: prompt subscription
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    get_or_create_user(user_id)
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Obuna bo‘lish", url="https://t.me/buxgalteriyada_daromad")],
        [InlineKeyboardButton("✅ Obuna bo‘ldim", callback_data="joined")]
    ])
    await update.message.reply_text(
        "🎁 Bepul buxgalteriya kursi yutish imkoniyati!\n\n"
        "Ishtirok uchun kanalga obuna bo‘ling va 'Obuna bo‘ldim' tugmasini bosing 👇",
        reply_markup=keyboard
    )

# Callback when 'Obuna bo‘ldim' pressed: request contact
async def joined(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton("📱 Telefon raqamini yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await update.callback_query.message.reply_text(
        "✅ Obuna bo‘lganingiz uchun rahmat!\n\n"
        "1-shartni bajardingiz 🎉 Endi telefon raqamingizni yuboring:",
        reply_markup=keyboard
    )

# Handle contact: save phone, notify referrer, show share + stats
async def save_contact_and_notify(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id, phone):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE users SET phone_number = ? WHERE user_id = ?", (phone, user_id))
    conn.commit()
    # Notify referrer if exists
    c.execute("SELECT referrer_id FROM referrals WHERE invited_user_id = ?", (user_id,))
    row = c.fetchone()
    if row and row[0]:
        referrer = row[0]
        c.execute("UPDATE users SET invited_count = invited_count + 1 WHERE user_id = ?", (referrer,))
        conn.commit()
        c.execute("SELECT invited_count FROM users WHERE user_id = ?", (referrer,))
        count = c.fetchone()[0]
        try:
            await context.bot.send_message(
                chat_id=referrer,
                text=("🎉 @{0} sizning havolangiz orqali konkursda ishtirok etdi!\n"
                      "📈 Siz orqali qo‘shilganlar soni: {1} ta").format(
                          update.effective_user.username or update.effective_user.first_name,
                          count
                      )
            )
        except:
            pass
    conn.close()

async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    phone = update.message.contact.phone_number
    # Save and notify
    await save_contact_and_notify(update, context, user_id, phone)
    # Remove contact keyboard
    await update.message.reply_text(
        "📞 Raqamingiz qabul qilindi.",
        reply_markup=ReplyKeyboardRemove()
    )
    # Show next stage buttons
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 Do‘stlarni taklif qilish", callback_data="share_link")],
        [InlineKeyboardButton("📊 Statistika", callback_data="stats")]
    ])
    await update.message.reply_text(
        "Endi asosiy 3-shart:\n\n"
        "👇 Quyidagi havolani do‘stlaringizga tarqating. Qancha ko‘p odam qo‘shilsa, yutish imkoniyatingiz shuncha yuqori!",
        reply_markup=keyboard
    )

# Share link handler
async def share_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT referral_code FROM users WHERE user_id = ?", (user_id,))
    code = c.fetchone()[0]
    conn.close()
    caption = (
        "📢 <b>Farg‘onaliklar uchun maxsus imkoniyat!</b>\n\n"
        "💸 Buxgalteriya sohasini o‘rganib, oylab 5–10 million so‘m daromad qilishni xohlaysizmi?\n\n"
        "🎯 Unda aynan siz uchun imkoniyat — <b>BUXGALTERIYA KURSINI BEPUL YUTIB OLING!</b>\n\n"
        "✅ Ishtirok qilish juda oson:\n"
        "1. Pastdagi havolangizni do‘stlaringizga yuboring 📩\n"
        "2. Ular kanalga qo‘shilsin 📢\n"
        "3. Siz esa g‘oliblikka bir qadam yaqinlashasiz 🏆\n\n"
        "⏳ G‘olib 27-iyul kuni e’lon qilinadi. Shoshiling — imkoniyatni qo‘ldan boy bermang!\n\n"
        "👇 Havola: https://t.me/ossonkonkursbot?start={}".format(code)
    )
    try:
        with open("poster.jpg", "rb") as photo:
            await context.bot.send_photo(
                chat_id=user_id,
                photo=photo,
                caption=caption,
                parse_mode="HTML"
            )
    except:
        await context.bot.send_message(chat_id=user_id, text=caption, parse_mode="HTML")
    await update.callback_query.message.reply_text(
        "👆 Ushbu xabarni tanishlaringizga yuboring!"
    )

# Statistics handler
async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "SELECT invited_user_id, joined_channel FROM referrals WHERE referrer_id = ?",
        (user_id,)
    )
    rows = c.fetchall()
    conn.close()

    msg = "📊 Siz orqali hozirgacha {} ta do‘ston taklif qilindi.\n\n".format(len(rows))
    for invited_id, joined in rows:
        status = "✅ Kanalga qo‘shilgan" if joined else "❌ Kanalga hali qo‘shilmagan"
        try:
            user = await context.bot.get_chat(invited_id)
            name = "@{}".format(user.username) if user.username else user.first_name
        except:
            name = str(invited_id)
        mention = "<a href='tg://user?id={}'>{}</a>".format(invited_id, name)
        msg += "{} — {}\n".format(mention, status)
    await update.callback_query.message.reply_text(msg, parse_mode="HTML")

# Admin broadcast
admin_mass_content = {}
async def handle_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower().strip()
    if text == ADMIN_USERNAME and update.effective_user.username == ADMIN_USERNAME:
        await update.message.reply_text("Rassilka uchun xabar yuboring (matn, rasm, video yoki ovoz).")
        admin_mass_content[update.effective_user.id] = None
    elif update.effective_user.id in admin_mass_content and admin_mass_content[update.effective_user.id] is None:
        admin_mass_content[update.effective_user.id] = update.message
        await update.message.reply_text("Rassilka tayyor! Barchaga yuborish uchun /sendall buyrug‘ini yozing.")

async def send_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.username != ADMIN_USERNAME:
        return
    msg = admin_mass_content.get(update.effective_user.id)
    if not msg:
        await update.message.reply_text("Rassilka matni topilmadi.")
        return
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    users = [r[0] for r in c.fetchall()]
    conn.close()
    for uid in users:
        try:
            await msg.copy(chat_id=uid)
        except:
            pass
    await update.message.reply_text("✅ Rassilka yuborildi!")

# Main entry point
def main():
    init_db()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(joined, pattern="joined"))
    app.add_handler(MessageHandler(filters.CONTACT, contact_handler))
    app.add_handler(CallbackQueryHandler(share_link, pattern="share_link"))
    app.add_handler(CallbackQueryHandler(show_stats, pattern="stats"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin))
    app.add_handler(CommandHandler("sendall", send_all))
    app.run_polling()

if __name__ == "__main__":
    main()
