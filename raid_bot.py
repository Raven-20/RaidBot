import asyncio
import os
import sys
import logging
import re
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
    MessageHandler,
    filters,
    ContextTypes,
)

import tweepy
import random

# --- Enhanced logging setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("raid_bot")

# --- Load environment variables ---
load_dotenv()

# Configuration
TOKEN = os.getenv("TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID", "0"))

TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
TWITTER_USER_ID = os.getenv("TWITTER_USER_ID")

# Performance settings
POLLING_INTERVAL = 30           # safer for rate limits
RATE_LIMIT_DELAY = 60
ERROR_DELAY = 30

# --- Twitter API client ---
twitter_client = tweepy.Client(bearer_token=TWITTER_BEARER_TOKEN)

# Keep track of last tweet seen
last_tweet_id = None


# --- Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Received /start command from user: {update.effective_user.username}")

    welcome_msg = """
🎯 **Welcome to X Raid Bot!**

Ready to amplify your X presence? This bot automatically shares your latest tweets for maximum engagement!

**Commands:**
• `/raid` - Share your latest tweet
• `/debugid` - Get chat ID info

Or simply send me a tweet link to raid any tweet!

🚀 **Auto-raid is active** - New tweets shared instantly!
    """
    await update.message.reply_text(welcome_msg, parse_mode='Markdown')


async def raid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Manual raid requested by user: {update.effective_user.username}")

    status_msg = await update.message.reply_text("🔍 Fetching your latest tweet...")

    tweet_url = await get_latest_tweet_url()
    if tweet_url:
        await send_raid_message(context.bot, tweet_url)
        await status_msg.edit_text("✅ **Raid launched successfully!** 🚀", parse_mode='Markdown')
        logger.info(f"✅ Manual raid completed for: {tweet_url}")
    else:
        await status_msg.edit_text("❌ Could not fetch the latest tweet. Please try again.")
        logger.warning("❌ Manual raid failed - no tweet found")


async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "engaged":
        if query.from_user:
            username = query.from_user.username or query.from_user.first_name
            responses = [
                f"🤩 @{username} has dunked it! 💥",
                f"🔥 @{username} crushed that engagement! 🎯",
                f"⚡ @{username} brought the energy! 🚀",
                f"💫 @{username} made it shine! ✨",
                f"🏆 @{username} dominated! 🎖️"
            ]
            response = random.choice(responses)
            await query.message.reply_text(response)
            logger.info(f"🎉 User {username} engaged with tweet")
        else:
            await query.message.reply_text("🎉 Someone engaged with the tweet! Keep it going! 🚀")


async def debugid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    user_id = update.effective_user.id
    username = update.effective_user.username

    debug_info = f"""
🔧 **Debug Information**

**Chat ID:** `{chat_id}`
**Chat Type:** `{chat_type}`
**User ID:** `{user_id}`
**Username:** `{username or 'N/A'}`
**Bot Status:** `Active`
**Polling:** `Every {POLLING_INTERVAL} seconds`
    """
    await update.message.reply_text(debug_info, parse_mode='Markdown')
    logger.info(f"Debug info requested by {username} in chat {chat_id}")


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
            tweet_url = f"https://twitter.com/i/web/status/{tweet_id}"
            logger.info(f"Fetched latest tweet: {tweet_url}")
            return tweet_url
        else:
            logger.info("No tweets found in API response.")
            return None

    except tweepy.TooManyRequests:
        logger.warning("⚠️ Rate limit hit while fetching tweets.")
        await asyncio.sleep(RATE_LIMIT_DELAY)
        return None
    except Exception as e:
        logger.error(f"❌ Error fetching tweets: {e}")
        return None


async def send_raid_message(bot, tweet_url):
    button_texts = [
        ("🏀 Dunked that tweet!", "💫 Swished! Slam dunk!🔥"),
        ("🎯 Hit the target!", "⚡ Bullseye! On fire!🔥"),
        ("🚀 Launched it!", "💥 Boom! Explosive!🔥"),
        ("🔥 Ignited!", "✨ Lit! Amazing!🔥"),
        ("💎 Polished!", "🌟 Sparkled! Brilliant!🔥")
    ]

    engage_text, engaged_text = random.choice(button_texts)

    keyboard = [
        [InlineKeyboardButton(engage_text, url=tweet_url)],
        [InlineKeyboardButton(engaged_text, callback_data="engaged")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    captions = [
        "💥 Post & Prosper - Time to go viral! 🚀",
        "🎯 Fresh content alert - Let's make it trend! 🔥",
        "⚡ New post dropped - Raid time! 💫",
        "🚀 Launch sequence initiated - Engage! 🎖️",
        "🔥 Hot content incoming - All hands on deck! 💥"
    ]

    caption = random.choice(captions)

    photo_path = os.path.join("bot", "raidBot.png")
    target_chat_ids = [c for c in [CHANNEL_ID, GROUP_CHAT_ID] if c and c != 0]

    success_count = 0

    for chat_id in target_chat_ids:
        try:
            if os.path.exists(photo_path):
                with open(photo_path, "rb") as photo:
                    await bot.send_photo(
                        chat_id=chat_id,
                        photo=photo,
                        caption=caption,
                        reply_markup=reply_markup
                    )
            else:
                await bot.send_message(
                    chat_id=chat_id,
                    text=f"{caption}\n\n{tweet_url}",
                    reply_markup=reply_markup
                )

            success_count += 1
            logger.info(f"✅ Raid message sent to {chat_id}")

        except Exception as e:
            logger.error(f"❌ Error sending raid message to {chat_id}: {e}")

    logger.info(f"📊 Raid completed: {success_count}/{len(target_chat_ids)} targets reached")


async def tweet_watcher(app):
    global last_tweet_id

    logger.info("🔍 Tweet watcher started...")

    known_tweet_ids = set()
    consecutive_errors = 0
    max_consecutive_errors = 5

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
                new_tweet_detected = False

                for tweet in tweets:
                    tweet_id = tweet.id
                    tweet_url = f"https://twitter.com/i/web/status/{tweet_id}"

                    if tweet_id not in known_tweet_ids:
                        known_tweet_ids.add(tweet_id)
                        logger.info(f"🆕 New tweet detected: {tweet_url}")

                        # Only raid if this isn't the initial startup
                        if last_tweet_id is not None:
                            await send_raid_message(app.bot, tweet_url)
                            logger.info("🎯 Auto-raid completed successfully")

                        new_tweet_detected = True

                # On first run, initialize last_tweet_id
                if last_tweet_id is None and tweets:
                    last_tweet_id = tweets[0].id
                    logger.info(f"🔧 Initialized watcher with latest tweet: {tweet_url}")

                if not new_tweet_detected:
                    logger.debug("No new tweets found in latest poll.")

            else:
                logger.debug("No tweets returned from API.")

            consecutive_errors = 0

        except tweepy.TooManyRequests:
            logger.warning(f"⚠️ Rate limit hit. Waiting {RATE_LIMIT_DELAY} seconds...")
            await asyncio.sleep(RATE_LIMIT_DELAY)
            continue
        except Exception as e:
            consecutive_errors += 1
            logger.error(f"❌ Error in tweet watcher (#{consecutive_errors}): {e}")

            if consecutive_errors >= max_consecutive_errors:
                logger.critical(f"🚨 Too many consecutive errors. Extending delay...")
                await asyncio.sleep(ERROR_DELAY * 3)
                consecutive_errors = 0
            else:
                await asyncio.sleep(ERROR_DELAY)
            continue

        await asyncio.sleep(POLLING_INTERVAL)


async def on_startup(app):
    logger.info("🚀 Bot startup initiated...")

    logger.info(f"TOKEN: {'SET' if TOKEN else 'MISSING'}")
    logger.info(f"TWITTER_BEARER_TOKEN: {'SET' if TWITTER_BEARER_TOKEN else 'MISSING'}")
    logger.info(f"TWITTER_USER_ID: {TWITTER_USER_ID}")
    logger.info(f"CHANNEL_ID: {CHANNEL_ID}")
    logger.info(f"GROUP_CHAT_ID: {GROUP_CHAT_ID}")

    if not TOKEN:
        logger.error("❌ TOKEN missing in environment variables")
        sys.exit(1)
    if not TWITTER_BEARER_TOKEN:
        logger.error("❌ TWITTER_BEARER_TOKEN missing in environment variables")
        sys.exit(1)
    if not TWITTER_USER_ID:
        logger.error("❌ TWITTER_USER_ID missing in environment variables")
        sys.exit(1)

    asyncio.create_task(tweet_watcher(app))

    logger.info("✅ All systems operational!")
    logger.info(f"📡 Polling interval: {POLLING_INTERVAL} seconds")
    logger.info(f"🎯 Monitoring user ID: {TWITTER_USER_ID}")


async def user_tweet_raid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.effective_message.text
    user = update.effective_user
    chat_id = update.effective_chat.id

    tweet_url_match = re.search(
        r"(https?://)?(www\.)?(twitter\.com|x\.com)/\S+/status/\d+",
        message_text
    )

    if tweet_url_match:
        tweet_url = tweet_url_match.group(0)
        logger.info(f"📨 User @{user.username} submitted link for raid: {tweet_url}")

        await update.message.reply_text(
            f"🚀 Launching raid for tweet:\n{tweet_url}"
        )

        await send_raid_message(context.bot, tweet_url)

        logger.info(f"✅ Raid triggered via message by @{user.username}")
    else:
        logger.debug(f"⚠️ Message in chat {chat_id} did not match a tweet URL.")
        await update.message.reply_text(
            "❌ I couldn’t detect a valid tweet link. Please send a full tweet URL from Twitter or X."
        )


def main():
    logger.info("🎯 Initializing X Raid Bot...")

    try:
        app = ApplicationBuilder().token(TOKEN).post_init(on_startup).build()

        # Handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("raid", raid))
        app.add_handler(CommandHandler("debugid", debugid))
        app.add_handler(CallbackQueryHandler(button_click))
        app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            user_tweet_raid
        ))

        logger.info("✅ Bot initialized successfully!")

        # Ensure only ONE instance is running!
        app.run_polling()

    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error in main application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
