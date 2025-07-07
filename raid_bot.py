import asyncio
import os
import logging
from dotenv import load_dotenv

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

import tweepy

# --- Setup logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Load .env ---
load_dotenv()

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")       # e.g. "@channelusername"
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID", "0"))

TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
TWITTER_USER_ID = os.getenv("TWITTER_USER_ID")

# --- Twitter API client ---
twitter_client = tweepy.Client(bearer_token=TWITTER_BEARER_TOKEN)

# Keep track of last tweet seen
last_tweet_id = None


# --- Telegram Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Received /start command")
    await update.message.reply_text("Hello! Use /raid to share your tweet.")


async def raid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tweet_url = await get_latest_tweet_url()
    if tweet_url:
        await send_raid_message(context.bot, tweet_url)
    else:
        await update.message.reply_text("Could not fetch the latest tweet.")


async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "engaged":
        if query.from_user:
            username = query.from_user.username or query.from_user.first_name
            await query.message.reply_text(f"🤩 @{username} has dunked it! 💥")
        else:
            await query.message.reply_text("Someone engaged with the tweet!")


async def debugid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        f"This chat ID is: `{chat_id}`",
        parse_mode='Markdown'
    )


# --- Twitter fetching logic ---

async def get_latest_tweet_url():
    try:
        response = twitter_client.get_users_tweets(
            id=TWITTER_USER_ID,
            max_results=5,
            tweet_fields=["id", "text", "created_at"],
            exclude=['replies']
        )
        tweets = response.data or []
        if tweets:
            latest_tweet = tweets[0]
            tweet_id = latest_tweet.id
            return f"https://twitter.com/i/web/status/{tweet_id}"
        else:
            logger.info("No tweets found.")
            return None
    except Exception as e:
        logger.error(f"Error fetching tweets: {e}")
        return None


# --- Raid message sending logic ---

async def send_raid_message(bot, tweet_url):
    keyboard = [
        [InlineKeyboardButton("🏀 Dunked that tweet!", url=tweet_url)],
        [InlineKeyboardButton("💫 Swished! Slam dunk!🔥", callback_data="engaged")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    photo_path = os.path.join("bot", "raidBot.png")
    target_chat_ids = [c for c in [CHANNEL_ID, GROUP_CHAT_ID] if c and c != 0]

    for chat_id in target_chat_ids:
        try:
            with open(photo_path, "rb") as photo:
                await bot.send_photo(
                    chat_id=chat_id,
                    photo=photo,
                    caption="💥Post & Prosper - Time to go viral",
                    reply_markup=reply_markup
                )
            logger.info(f"✅ Sent raid message to {chat_id}")
        except Exception as e:
            logger.error(f"❌ Error sending to {chat_id}: {e}")


# --- Background polling task ---

async def tweet_watcher(app):
    global last_tweet_id

    while True:
        try:
            response = twitter_client.get_users_tweets(
                id=TWITTER_USER_ID,
                max_results=5,
                tweet_fields=["id", "text", "created_at"],
                exclude=['replies']
            )
            tweets = response.data or []

            if tweets:
                latest_tweet = tweets[0]
                tweet_id = latest_tweet.id
                tweet_url = f"https://twitter.com/i/web/status/{tweet_id}"

                if tweet_id != last_tweet_id:
                    logger.info(f"New tweet detected: {tweet_url}")
                    last_tweet_id = tweet_id
                    await send_raid_message(app.bot, tweet_url)
                else:
                    logger.info("No new tweet.")
            else:
                logger.info("No tweets returned.")

        except tweepy.TooManyRequests:
            logger.warning("Rate limit hit! Waiting 2 minutes before retrying...")
            await asyncio.sleep(2 * 60)

        except Exception as e:
            logger.error(f"Unexpected error during tweet watcher: {e}")
            await asyncio.sleep(1 * 60)

        await asyncio.sleep(60)


# --- Startup hook ---

async def on_startup(app):
    logger.info("🚀 Bot is starting up and tweet watcher is launching.")
    asyncio.create_task(tweet_watcher(app))


# --- Main entrypoint ---

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("raid", raid))
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(CommandHandler("debugid", debugid))

    app.post_init = on_startup

    logger.info("✅ Bot is running. Waiting for commands...")
    await app.run_polling()

import sys

if __name__ == '__main__':
    if sys.platform.startswith("win"):
        import nest_asyncio
        nest_asyncio.apply()

    asyncio.run(main())


