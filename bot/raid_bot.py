import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Environment variables
TOKEN = os.getenv("TOKEN")
TWEET_URL = os.getenv("TWEET_URL")
CHANNEL_ID = os.getenv("CHANNEL_ID")         # e.g., "@channelusername"
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID", "0"))      # e.g., -1001234567890

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! Use /raid to share your tweet.")

# /raid command
async def raid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🏀 Dunked that tweet!", url=TWEET_URL)],
        [InlineKeyboardButton("💫 Swished! Slam dunk!🔥", callback_data="engaged")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    photo_path = os.path.join("bot", "raid_banner.png")

    # 1. Send to the user who issued the command
    with open(photo_path, "rb") as photo:
        await update.message.reply_photo(
            photo=photo,
            caption="💥Post & Prosper - Time to go viral",
            reply_markup=reply_markup
        )

    # 2. List of additional targets
    target_chat_ids = [CHANNEL_ID, GROUP_CHAT_ID]

    for chat_id in target_chat_ids:
        try:
            with open(photo_path, "rb") as photo:
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=photo,
                    caption="💥Post & Prosper - Time to go viral",
                    reply_markup=reply_markup
                )
            print(f"✅ Sent raid message to {chat_id}")
        except Exception as e:
            print(f"❌ Error sending to {chat_id}: {e}")


# Button click handler
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "engaged":
        username = query.from_user.username or query.from_user.first_name
        await query.message.reply_text(f"🤩 @{username} has dunked it! 💥")


# Fetch telegram Group chat ID
async def debugid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        f"This chat ID is: `{chat_id}`",
        parse_mode='Markdown'
    )

# Run the bot
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("raid", raid))
    app.add_handler(CallbackQueryHandler(button_click)) 
    app.add_handler(CommandHandler("debugid", debugid)) #send "/debugid" to the group chat to get the Group chat ID

    print("Bot is running...")
    app.run_polling()
