import sqlite3
import random
import string
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    InputFile
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, CallbackQueryHandler, ContextTypes
)

TOKEN = "7003492468:AAGFKDDs9nKv3C9XqY3xWHWO9eddoqmvp3A"
CHANNEL_ID = -1002740723606
DB_FILE = "referral_bot.db"
ADMIN_USERNAME = "heleromana"

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
    try:
        c.execute("ALTER TABLE users ADD COLUMN phone_number TEXT")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()

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
        try:
            c.execute("ALTER TABLE users ADD COLUMN phone_number TEXT")
        except sqlite3.OperationalError:
            pass

    conn.commit()
    conn.close()
    return code

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    get_or_create_user(user_id)

    keyboard = [
        [InlineKeyboardButton("📢 Obuna bo‘lish", url="https://t.me/buxgalteriyada_daromad")],
        [InlineKeyboardButton("✅ Obuna bo‘ldim", callback_data="joined")]
    ]
    await update.message.reply_text(
        """🎁 Bepul buxgalteriya kursi yutish imkoniyati!

Ishtirok uchun kanalga obuna bo‘ling va 'Obuna bo‘ldim' tugmasini bosing 👇""",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def joined(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE referrals SET joined_channel = 1 WHERE invited_user_id = ?", (user_id,))
    try:
        c.execute("ALTER TABLE users ADD COLUMN phone_number TEXT")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()

    # Add a button to request phone number
    keyboard = [[KeyboardButton("📞 Telefon raqamni yuborish", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.callback_query.message.reply_text(
        """✅ Obuna bo‘lganingiz uchun rahmat!

1-shartni bajardingiz 🎉 Endi telefon raqamingizni yuboring:""",
        reply_markup=reply_markup
    )

async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    phone_number = update.message.contact.phone_number

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE users SET phone_number = ? WHERE user_id = ?", (phone_number, user_id))
    try:
        c.execute("ALTER TABLE users ADD COLUMN phone_number TEXT")
    except sqlite3.OperationalError:
        pass

    conn.commit()

    # Notify referrer if exists
    c.execute("SELECT referrer_id FROM referrals WHERE invited_user_id = ?", (user_id,))
    ref_row = c.fetchone()
    if ref_row and ref_row[0]:
        referrer_id = ref_row[0]
        c.execute("UPDATE users SET invited_count = invited_count + 1 WHERE user_id = ?", (referrer_id,))
        conn.commit()

        c.execute("SELECT invited_count FROM users WHERE user_id = ?", (referrer_id,))
        count_row = c.fetchone()
        invited_total = count_row[0] if count_row else 1

        try:
            await context.bot.send_message(
                chat_id=referrer_id,
                text=f"🎉 @{update.effective_user.username or update.effective_user.first_name} sizning havolangiz orqali konkursda ishtirok etdi!\n"
                     f"📈 Siz orqali qo‘shilganlar soni: {invited_total} ta"
            )
        except:
            pass

    conn.close()

    await update.message.reply_text(
        """📞 Raqamingiz qabul qilindi. Endi esa asosiy 3-shart:

👇 Quyidagi havolani do‘stlaringizga tarqating. Qancha ko‘p odam qo‘shilsa, yutish imkoniyatingiz shuncha yuqori!""",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("👥 Do‘stlarni taklif qilish", callback_data="share_link")],
            [InlineKeyboardButton("📊 Statistika", callback_data="stats")]
        ]),
        reply_markup=ReplyKeyboardRemove()  # Remove the keyboard after phone number is submitted
    )

async def share_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT referral_code FROM users WHERE user_id = ?", (user_id,))
    code = c.fetchone()[0]
    conn.close()

    caption = f"""
📢 <b>Farg‘onaliklar uchun maxsus imkoniyat!</b>

💸 Buxgalteriya sohasini o‘rganib, oylab 5–10 million so‘m daromad qilishni xohlaysizmi?

🎯 Unda aynan siz uchun imkoniyat — <b>BUXGALTERIYA KURSINI BEPUL YUTIB OLING!</b>

✅ Ishtirok qilish juda oson:
1. Pastdagi havolangizni do‘stlaringizga yuboring 📩
2. Ular kanalga qo‘shilsin 📢
3. Siz esa g‘oliblikka bir qadam yaqinlashasiz 🏆

⏳ G‘olib 27-iyul kuni e’lon qilinadi. Shoshiling — imkoniyatni qo‘ldan boy bermang!

👇 Havola: https://t.me/ossonkonkursbot?start={code}
"""

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

    await update.callback_query.message.reply_text("👆 Ushbu xabarni tanishlaringizga yuboring!")

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        SELECT u.user_id, u.invited_count, r.invited_user_id, r.joined_channel
        FROM users u
        LEFT JOIN referrals r ON u.user_id = r.referrer_id
        WHERE u.user_id = ?
    """, (user_id,))
    rows = c.fetchall()
    conn.close()

    invited_users = {}
    for row in rows:
        invited_id = row[2]
        joined_channel = row[3]
        if invited_id:
            invited_users[invited_id] = joined_channel

    msg = f"📊 Siz orqali hozirgacha {len(invited_users)} kishi konkursda ishtirok etgan.\n\n"
    for uid, joined in invited_users.items():
        status = "✅ Kanalga qo‘shilgan" if joined else "❌ Hali kanalga qo‘shilmagan"
        mention = f"<a href='tg://user?id={uid}'>User {uid}</a>"
        msg += f"{mention} — {status}\n"

    await update.callback_query.message.reply_text(
        msg,
        parse_mode="HTML"
    )

admin_mass_msg = {}

async def handle_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.strip().lower() == "heleromana" and update.effective_user.username == ADMIN_USERNAME:
        await update.message.reply_text("Rassilka uchun xabarni yuboring (video, rasm, ovozli yoki matn).")
        admin_mass_msg[update.effective_user.id] = "waiting"

    elif admin_mass_msg.get(update.effective_user.id) == "waiting":
        context.user_data["mass_content"] = update.message
        admin_mass_msg[update.effective_user.id] = "confirming"
        await update.message.reply_text("Rassilkaga tayyorlandi. Yuborish uchun /sendall buyrug‘ini yozing.")

async def send_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.username != ADMIN_USERNAME:
        return
    msg = context.user_data.get("mass_content")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    users = c.fetchall()
    conn.close()

    for u in users:
        try:
            await msg.copy(chat_id=u[0])
        except:
            continue
    await update.message.reply_text("✅ Rassilka yuborildi.")

def main():
    init_db()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("sendall", send_all))
    app.add_handler(CallbackQueryHandler(joined, pattern="joined"))
    app.add_handler(CallbackQueryHandler(share_link, pattern="share_link"))
    app.add_handler(CallbackQueryHandler(show_stats, pattern="stats"))
    app.add_handler(MessageHandler(filters.CONTACT, contact_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin))
    app.run_polling()

if __name__ == "__main__":
    main()