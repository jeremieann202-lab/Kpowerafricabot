import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import sqlite3

# ==========================
# CONFIGURATION
# ==========================
TOKEN = "8756174682:AAGp6wePhV1C-n3sPCuSk35l89chqEQEcHA"
ADMIN_ID = 1919559774
POINTS_PER_CLICK = 50
MIN_WITHDRAW_POINTS = 1000
POINTS_TO_CFA = 500  # taux de conversion 500 points = 25 F

# ==========================
# LOGGING
# ==========================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ==========================
# DATABASE
# ==========================
conn = sqlite3.connect('kpowerafrica.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY,
    points INTEGER DEFAULT 0
)
''')
conn.commit()

# ==========================
# UTILS
# ==========================
def get_user_points(user_id):
    cursor.execute("SELECT points FROM users WHERE id=?", (user_id,))
    res = cursor.fetchone()
    if res:
        return res[0]
    else:
        cursor.execute("INSERT INTO users(id, points) VALUES(?, ?)", (user_id, 0))
        conn.commit()
        return 0

def add_points(user_id, points):
    current = get_user_points(user_id)
    cursor.execute("UPDATE users SET points=? WHERE id=?", (current + points, user_id))
    conn.commit()

# ==========================
# HANDLERS
# ==========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("⛏ Mining", callback_data='mining')],
        [InlineKeyboardButton("💰 Plus d'argent", callback_data='more_money')],
        [InlineKeyboardButton("👥 Parrainer un ami", callback_data='referral')],
        [InlineKeyboardButton("👤 Profil", callback_data='profile')],
        [InlineKeyboardButton("🔄 Échange KCU", callback_data='exchange')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Bienvenue sur Kpower Africa !\nSélectionnez un menu :", reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data == 'mining':
        keyboard = [
            [InlineKeyboardButton("Clique", callback_data='click')],
            [InlineKeyboardButton("Menu principal", callback_data='menu')]
        ]
        await query.edit_message_text("Mining actif ! Cliquez pour gagner des points :", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == 'click':
        add_points(user_id, POINTS_PER_CLICK)
        points = get_user_points(user_id)
        keyboard = [
            [InlineKeyboardButton("Clique", callback_data='click')],
            [InlineKeyboardButton("Menu principal", callback_data='menu')]
        ]
        await query.edit_message_text(f"Vous avez {points} points !", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == 'menu':
        await start(update, context)

    elif data == 'more_money':
        await query.edit_message_text("Pour gagner plus d'argent, abonnez-vous aux canaux Telegram et envoyez la capture à l'admin !")

    elif data == 'referral':
        await query.edit_message_text("Parrainez un ami et gagnez 500 points ! Lien généré automatiquement pour chaque utilisateur.")

    elif data == 'profile':
        points = get_user_points(user_id)
        await query.edit_message_text(f"Votre ID : {user_id}\nVos points : {points}")

    elif data == 'exchange':
        points = get_user_points(user_id)
        if points < MIN_WITHDRAW_POINTS:
            await query.edit_message_text(f"Vous devez avoir au moins {MIN_WITHDRAW_POINTS} points pour retirer.")
        else:
            cfa = (points // POINTS_TO_CFA) * 25
            await query.edit_message_text(f"Vous pouvez échanger vos points contre {cfa} F CFA.")

# ==========================
# APPLICATION
# ==========================
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    print("Bot démarré...")
    app.run_polling()
