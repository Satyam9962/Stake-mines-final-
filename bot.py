import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters, ConversationHandler
from utils import generate_prediction_image
import os
import io
from pathlib import Path
from datetime import datetime, timedelta
import json

BOT_TOKEN = os.environ.get("BOT_TOKEN")
PASSKEY_BASIC = "AjdJe62BHkaie"
PASSKEY_KING = "Sushru73TyaMisGHn"
CHOOSE_PLAN, ASK_PASSKEY, ASK_SEED = range(3)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

user_data_file = "user_data.json"

def load_user_data():
    if Path(user_data_file).exists():
        with open(user_data_file, "r") as f:
            return json.load(f)
    return {}

def save_user_data(data):
    with open(user_data_file, "w") as f:
        json.dump(data, f)

user_data = load_user_data()

def get_expiry_date(plan):
    days = 15 if plan == "basic" else 31
    return (datetime.utcnow() + timedelta(days=days)).strftime("%Y-%m-%d")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("🪙 Mines Basic (₹499)", callback_data="basic")],
        [InlineKeyboardButton("👑 Mines King (₹999)", callback_data="king")]
    ]
    await update.message.reply_text(
        f"Namaste {user.first_name} 👋\n\n"
        "🤖 Swagat hai aapka *Stake Mines Predictor Bot* mein!\n\n"
        "🔔 *Recommendation:* Aapke liye *Mines King* lena behtar rahega.\n"
        "Is plan mein *Basic* se zyada features hai aur *win chance 499%* tak hai.\n\n"
        "👇 Plan choose kare:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return CHOOSE_PLAN

async def choose_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    plan = query.data
    context.user_data["plan"] = plan
    qr_file = "qr_basic.png" if plan == "basic" else "qr_king.png"
    with open(qr_file, "rb") as photo:
        await query.message.reply_photo(
            photo=photo,
            caption=f"🧾 *{plan.capitalize()} Plan Price:* ₹{'499' if plan == 'basic' else '999'}\n"
                    "✅ Kripya payment kare aur screenshot bheje verification ke liye.",
            parse_mode="Markdown"
        )
    return ASK_PASSKEY

async def check_passkey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()
    plan = context.user_data.get("plan")
    correct = PASSKEY_BASIC if plan == "basic" else PASSKEY_KING
    user_id = str(update.effective_user.id)
    if user_input == correct:
        expiry = get_expiry_date(plan)
        user_data[user_id] = {"plan": plan, "expiry": expiry}
        save_user_data(user_data)
        await update.message.reply_text(
            f"✅ Payment verified!\nPlan activated till *{expiry}*.\n"
            "Ab apna client seed bheje (3 mines k saath khelein).",
            parse_mode="Markdown"
        )
        return ASK_SEED
    else:
        await update.message.reply_text(
            "❌ Galat passkey. Agar aapne payment kar diya hai to admin se sampark kare: @Stake_Mines_God"
        )
        return ASK_PASSKEY

async def receive_seed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    seed = update.message.text.strip()
    image = generate_prediction_image(seed)
    bio = io.BytesIO()
    bio.name = 'prediction.png'
    image.save(bio, 'PNG')
    bio.seek(0)
    keyboard = [[InlineKeyboardButton("➡️ Next Signal", callback_data="next_signal")]]
    await update.message.reply_photo(
        photo=bio,
        caption="🟩 Yeh rahe 5 safe tiles!\nType or tap 'Next Signal' for a new prediction.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ASK_SEED

async def next_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("📝 Naya client seed bheje:")
    return ASK_SEED

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSE_PLAN: [CallbackQueryHandler(choose_plan)],
            ASK_PASSKEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_passkey)],
            ASK_SEED: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_seed),
                       CallbackQueryHandler(next_signal, pattern="next_signal")]
        },
        fallbacks=[]
    )
    app.add_handler(conv_handler)
    logger.info("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
