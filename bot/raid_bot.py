import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

TOKEN = "8074739090:AAG4wZmOYdeL3sgwzZOJ6l24ltDvEbHGWpw"
TWEET_URL = "https://x.com/XodeNet/status/1937438171220038035"
CHANNEL_ID = "@syzchannell"  

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! Use /raid to share your tweet.")

# /raid command
async def raid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🚀 Smashed that tweet!", url=TWEET_URL)],
        [InlineKeyboardButton("🔥 Tweet Smashed!", callback_data="engaged")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send to private chat (user)
    with open("raid_banner.png", "rb") as photo:
        await update.message.reply_photo(
            photo=photo,
            caption="🔥 New tweet is out!\nSmash it on X 👇",
            reply_markup=reply_markup
        )

    # Send to channel
    try:
        with open("raid_banner.png", "rb") as channel_photo:
            await context.bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=channel_photo,
                caption="🔥 New tweet is out!\nSmash it on X 👇",
                reply_markup=reply_markup
            )
    except Exception as e:
        print(f"Error posting to channel: {e}")

# Handle "🔥 Tweet Smashed!" button clicks
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "engaged":
        username = query.from_user.username or query.from_user.first_name
        await query.message.reply_text(f"✅ @{username} has smashed it! 💥")

# Run the bot
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("raid", raid))
    app.add_handler(CallbackQueryHandler(button_click))

    print("Bot is running...")
    app.run_polling()
