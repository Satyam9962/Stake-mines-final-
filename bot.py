import logging, os, json, io
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
    filters, ContextTypes, ConversationHandler
)
from utils import generate_safe_tiles, generate_prediction_image
from datetime import datetime, timedelta
# --- Constants ---
ASK_PLAN, ASK_SCREENSHOT, ASK_PASSKEY, ASK_SEED = range(4)
ADMIN_USERNAME = "@Stake_Mines_God"

# File to store user plans and usage
USER_DATA_FILE = "user_data.json"
if not os.path.exists(USER_DATA_FILE):
    with open(USER_DATA_FILE, "w") as f:
        json.dump({}, f)

# --- Load/Save User Data ---
def load_user_data():
    with open(USER_DATA_FILE, "r") as f:
        return json.load(f)

def save_user_data(data):
    with open(USER_DATA_FILE, "w") as f:
        json.dump(data, f)

# --- Start Command ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_data = load_user_data()

    # Always reset if user restarts
    user_data[str(user.id)] = {}
    save_user_data(user_data)

    buttons = [
        [InlineKeyboardButton("💎 Mines Basic – ₹499", callback_data="basic")],
        [InlineKeyboardButton("👑 Mines King – ₹999", callback_data="king")]
    ]
    await update.message.reply_text(
        f"🙏 *{user.first_name}* ji, aapka swagat hai hamare Stake Mines Prediction Bot me!\n\n"
        "🕒 Timing: 8 AM se 8 PM tak\n\n"
        "⚡ Recommended Plan: *Mines King* for best predictions.\n\n"
        "👇 Apna plan chune:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return ASK_PLAN

# --- Plan Selected ---
async def ask_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    plan = query.data

    context.user_data["selected_plan"] = plan
    price = "₹499" if plan == "basic" else "₹999"
    qr_image = "qr_basic.png" if plan == "basic" else "qr_king.png"

    with open(qr_image, "rb") as f:
        await query.message.reply_photo(
            photo=f,
            caption=f"💸 *{price} ka payment* kare aur screenshot bheje.\n\n"
                    "✅ Payment hone ke baad passkey prapt karne ke liye admin se sampark kare: "
                    f"{ADMIN_USERNAME}",
            parse_mode="Markdown"
        )
    return ASK_SCREENSHOT

# --- Handle Screenshot Upload ---
async def receive_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ Screenshot prapt. Kripya admin se sampark kare passkey ke liye: "
        f"{ADMIN_USERNAME}\n\nPasskey milne ke baad yahan bheje."
    )
    return ASK_PASSKEY

# --- Handle Passkey ---
async def receive_passkey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_data = load_user_data()
    plan = context.user_data.get("selected_plan")

    valid_keys = {
        "basic": "AjdJe62BHkaie",   # Replace with your actual passkey
        "king": "Sushru73TyaMisGHn"
    }

    if update.message.text.strip() == valid_keys.get(plan):
        days = 15 if plan == "basic" else 31
        limit = 20 if plan == "basic" else 45
        user_data[user_id] = {
            "plan": plan,
            "start_date": str(datetime.now().date()),
            "expiry_date": str(datetime.now().date() + timedelta(days=days)),
            "daily_limit": limit,
            "used_today": 0,
            "last_used": str(datetime.now().date())
        }
        save_user_data(user_data)

        await update.message.reply_text(
            "✅ Passkey sahi hai!\n\nAb apna *client seed* bheje (3 mines ke sath khelein).",
            parse_mode="Markdown"
        )
        return ASK_SEED
    else:
        await update.message.reply_text(
            "❌ Galat passkey. Agar aapne payment kar diya hai to admin se sampark kare: "
            f"{ADMIN_USERNAME}"
        )
        return ASK_PASSKEY

# --- Handle Client Seed & Generate Prediction ---

async def receive_seed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_data = load_user_data()

    if user_id not in user_data:
        await update.message.reply_text("❌ Aapka plan active nahi hai. Kripya /start dabaye.")
        return ConversationHandler.END

    # Check expiry
    expiry_date = datetime.strptime(user_data[user_id]["expiry_date"], "%Y-%m-%d").date()
    today = datetime.now().date()
    if today > expiry_date:
        await update.message.reply_text("❌ Aapka plan samapt ho gaya hai. Kripya naye plan ke liye /start dabaye.")
        return ConversationHandler.END

    # Reset daily count if new day
    if str(today) != user_data[user_id]["last_used"]:
        user_data[user_id]["used_today"] = 0
        user_data[user_id]["last_used"] = str(today)

    # Daily limit check
    if user_data[user_id]["used_today"] >= user_data[user_id]["daily_limit"]:
        await update.message.reply_text("⚠️ Aapki daily signals count khtm hogyi hai. Dubara prapt krne ke liye kal wapas aaye.")
        return ConversationHandler.END

    seed = update.message.text.strip()
    safe_tiles = generate_safe_tiles(seed)
    image = generate_prediction_image(seed, safe_tiles)

    file_path = f"prediction_{user_id}.png"
    image.save(file_path)

    await update.message.reply_photo(
        photo=open(file_path, "rb"),
        caption="✅ Prediction tayar hai! Safe tiles dikhaye gaye hain."
    )

    user_data[user_id]["used_today"] += 1
    save_user_data(user_data)

    await update.message.reply_text("➡️ Agla signal prapt karne ke liye 'Next Signal' bheje.")
    return ASK_SEED
# --- Handle Next Signal Button ---
async def next_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("🔁 Apna agla *client seed* bheje:", parse_mode="Markdown")
    return ASK_SEED

# --- Main ---
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    BOT_TOKEN = os.environ.get("BOT_TOKEN")  # Replace with your bot token or use export

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_PLAN: [CallbackQueryHandler(ask_screenshot)],
            ASK_SCREENSHOT: [MessageHandler(filters.PHOTO, receive_screenshot)],
            ASK_PASSKEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_passkey)],
            ASK_SEED: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_seed)],
                CallbackQueryHandler(next_signal, pattern="^next_signal$")
            ]
        },
        fallbacks=[]
    )

    app.add_handler(conv)
    app.run_polling()
