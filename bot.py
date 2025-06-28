import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters, ConversationHandler
)
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

def is_plan_expired(user_id):
    today = datetime.utcnow().date()
    if user_id in user_data:
        expiry = datetime.strptime(user_data[user_id]['expiry'], "%Y-%m-%d").date()
        return today > expiry
    return True

def get_remaining_signals(user_id):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    if user_id in user_data:
        plan = user_data[user_id]['plan']
        limit = 20 if plan == "basic" else 45
        usage = user_data[user_id].get("usage", {})
        used_today = usage.get(today, 0)
        return limit - used_today
    return 0

def increment_usage(user_id):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    usage = user_data[user_id].setdefault("usage", {})
    usage[today] = usage.get(today, 0) + 1
    save_user_data(user_data)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    context.user_data.clear()
    keyboard = [
        [InlineKeyboardButton("🪙 Mines Basic (₹499)", callback_data="basic")],
        [InlineKeyboardButton("👑 Mines King (₹999)", callback_data="king")]
    ]
    await update.message.reply_text(
        f"Namaste {user.first_name} 👋\n\n"
        "🤖 Swagat hai aapka *Stake Mines Predictor Bot* mein!\n\n"
        "🕗 Bot Timing: *8 AM se 8 PM* tak\n"
        "🔔 Recommendation: *Mines King* plan behtar hai zyada accuracy ke liye.\n\n"
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
            caption=f"🧾 *{plan.capitalize()} Plan Price:* ₹{'499' if plan == 'basic' else '999'}\n\n"
                    "✅ *Payment kare*\n"
                    "📸 *Screenshot bheje*\n\n"
                    "🔐 *Passkey ke liye admin se contact kare:* @Stake_Mines_God",
            parse_mode="Markdown"
        )
    return ASK_PASSKEY

async def handle_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ Payment successful received!\n"
        "🔐 Passkey ke liye admin se contact kare: @Stake_Mines_God"
    )
    return ASK_PASSKEY

async def check_passkey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()
    plan = context.user_data.get("plan")
    correct = PASSKEY_BASIC if plan == "basic" else PASSKEY_KING
    user_id = str(update.effective_user.id)
    if user_input == correct:
        expiry = get_expiry_date(plan)
        user_data[user_id] = {"plan": plan, "expiry": expiry, "usage": {}}
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
    user_id = str(update.effective_user.id)
    if is_plan_expired(user_id):
        await update.message.reply_text("❌ Aapka plan expire ho chuka hai. Dobara plan kharide.")
        return ConversationHandler.END

    remaining = get_remaining_signals(user_id)
    if remaining <= 0:
        await update.message.reply_text("⛔ Aapki daily signals count khtm hogyi hai. Dubara prapt krne ke liye kal wapas aaye.")
        return ASK_SEED

    seed = update.message.text.strip()
    image = generate_prediction_image(seed)
    bio = io.BytesIO()
    bio.name = 'prediction.png'
    image_path = generate_prediction_image(seed)
img = Image.open(image_path)
bio = io.BytesIO()
img.save(bio, 'PNG')
bio.seek(0)
keyboard = [[InlineKeyboardButton("➡️ Next Signal", callback_data="next_signal")]]
await update.message.reply_photo(
    photo=bio,
    caption="🟩 Yeh rahe 5 safe tiles!\nType or tap 'Next Signal' for a new prediction.",
    reply_markup=InlineKeyboardMarkup(keyboard)
)

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
            ASK_PASSKEY: [
                MessageHandler(filters.PHOTO, handle_screenshot),
                MessageHandler(filters.TEXT & ~filters.COMMAND, check_passkey)
            ],
            ASK_SEED: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_seed),
                CallbackQueryHandler(next_signal, pattern="next_signal")
            ]
        },
        fallbacks=[],
        allow_reentry=True
    )
    app.add_handler(conv_handler)
    logger.info("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
