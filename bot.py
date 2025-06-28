import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters
)
from utils import generate_safe_tiles, generate_prediction_image, load_user_data, save_user_data

# --- Constants ---
ASK_PLAN, ASK_PAYMENT, ASK_PASSKEY, ASK_SEED = range(4)
ADMIN_USERNAME = "@Stake_Mines_God"

# --- Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- Start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"👋 Namaste {user.first_name}!\n\n"
        "Aapka swagat hai *Stake Mines Prediction Bot* me!\n\n"
        "⏰ Timing: 8 AM - 8 PM\n"
        "🔐 Prediction sirf 3 mines ke liye kaam karta hai.\n\n"
        "💎 Recommended Plan: *Mines King (₹999)*\n"
        "👇 Apna plan chune:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Mines Basic (₹499)", callback_data="basic")],
            [InlineKeyboardButton("Mines King (₹999)", callback_data="king")]
        ])
    )
    return ASK_PLAN


# --- Plan Selection ---
async def select_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    plan = query.data
    context.user_data["selected_plan"] = plan

    qr_image = "qr_basic.png" if plan == "basic" else "qr_king.png"
    await query.message.reply_photo(
        photo=open(qr_image, "rb"),
        caption="✅ Kripya QR code scan karke payment kare.\n"
                "💬 Payment hone ke baad screenshot bheje."
    )
    return ASK_PAYMENT


# --- Screenshot Handler ---
async def receive_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ Screenshot prapt. Kripya admin se sampark kare passkey ke liye: "
        f"{ADMIN_USERNAME}\n\nPasskey milne ke baad yahan bheje."
    )
    return ASK_PASSKEY


# --- Passkey Verification ---
async def receive_passkey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_data = load_user_data()
    plan = context.user_data.get("selected_plan")

    valid_keys = {
        "basic": "AjdJe62BHkaie",
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
        await update.message.reply_text("❌ Galat passkey. Agar aapne payment kar diya hai to admin se sampark kare.")
        return ASK_PASSKEY


# --- Client Seed Receiver ---
async def receive_seed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_data = load_user_data()

    if user_id not in user_data:
        await update.message.reply_text("❌ Aapka plan active nahi hai. Kripya /start dabaye.")
        return ConversationHandler.END

    # Plan expiry check
    today = datetime.now().date()
    expiry_date = datetime.strptime(user_data[user_id]["expiry_date"], "%Y-%m-%d").date()
    if today > expiry_date:
        await update.message.reply_text("❌ Aapka plan samapt ho gaya hai. Kripya naye plan ke liye /start dabaye.")
        return ConversationHandler.END

    # Daily reset
    if str(today) != user_data[user_id]["last_used"]:
        user_data[user_id]["used_today"] = 0
        user_data[user_id]["last_used"] = str(today)

    # Signal limit check
    if user_data[user_id]["used_today"] >= user_data[user_id]["daily_limit"]:
        await update.message.reply_text("⚠️ Aapki daily signals count khtm hogyi hai. Dubara prapt krne ke liye kal wapas aaye.")
        return ConversationHandler.END

    # Generate prediction
    seed = update.message.text.strip()
    safe_tiles = generate_safe_tiles(seed)
    image = generate_prediction_image(seed, safe_tiles)

    image_path = f"prediction_{user_id}.png"
    image.save(image_path)

    await update.message.reply_photo(
        photo=open(image_path, "rb"),
        caption="✅ Prediction tayar hai! Safe tiles dikhaye gaye hain."
    )

    user_data[user_id]["used_today"] += 1
    save_user_data(user_data)

    await update.message.reply_text("➡️ Agla signal prapt karne ke liye 'Next Signal' bheje.")
    return ASK_SEED


# --- Main Function ---
if __name__ == "__main__":
    import os
    TOKEN = os.getenv("BOT_TOKEN")  # Render pe BOT_TOKEN env me set hoga

    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_PLAN: [CallbackQueryHandler(select_plan)],
            ASK_PAYMENT: [MessageHandler(filters.PHOTO, receive_screenshot)],
            ASK_PASSKEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_passkey)],
            ASK_SEED: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_seed)],
        },
        fallbacks=[],
    )

    app.add_handler(conv_handler)

    print("🤖 Bot started...")
    app.run_polling()
