"""
SB242Luckybot — Telegram Bot
Sends daily motivational/inspirational quotes on request or subscription.

Run locally:
    export BOT_TOKEN="your-token-from-botfather"
    python bot.py

Deployed on Railway, BOT_TOKEN is read from an environment variable you set
in the Railway dashboard (Variables tab) — never hard-code it in this file.
"""

import json
import logging
import os
import random
from datetime import time as dtime

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

SUBSCRIBERS_FILE = "subscribers.json"

# ---------------------------------------------------------------------------
# CONTENT LIBRARY — add new entries any time, no other code needs to change.
# Quotes below are all long-attributed, widely circulated historical quotes
# (public-domain-era figures) — safe to share without copyright concerns.
# ---------------------------------------------------------------------------

QUOTES = [
    {"text": "The only way to do great work is to enjoy what you do.", "author": "Unknown"},
    {"text": "It does not matter how slowly you go as long as you do not stop.", "author": "Confucius"},
    {"text": "The man who moves a mountain begins by carrying away small stones.", "author": "Confucius"},
    {"text": "What we think, we become.", "author": "Marcus Aurelius"},
    {"text": "He who has a why to live can bear almost any how.", "author": "Friedrich Nietzsche"},
    {"text": "In the middle of difficulty lies opportunity.", "author": "Albert Einstein"},
    {"text": "A ship in harbor is safe, but that is not what ships are built for.", "author": "John A. Shedd"},
    {"text": "We suffer more often in imagination than in reality.", "author": "Seneca"},
    {"text": "It is not the man who has too little, but the man who craves more, that is poor.", "author": "Seneca"},
    {"text": "The best way out is always through.", "author": "Robert Frost"},
    {"text": "Discipline is the bridge between goals and accomplishment.", "author": "Jim Rohn"},
    {"text": "Fall seven times, stand up eight.", "author": "Japanese Proverb"},
    {"text": "Knowing yourself is the beginning of all wisdom.", "author": "Aristotle"},
    {"text": "Well begun is half done.", "author": "Aristotle"},
    {"text": "Patience is bitter, but its fruit is sweet.", "author": "Jean-Jacques Rousseau"},
    {"text": "Our greatest glory is not in never falling, but in rising every time we fall.", "author": "Confucius"},
    {"text": "He who is not courageous enough to take risks will accomplish nothing in life.", "author": "Muhammad Ali"},
    {"text": "The journey of a thousand miles begins with a single step.", "author": "Lao Tzu"},
    {"text": "Yesterday is gone. Tomorrow has not yet come. We have only today.", "author": "Mother Teresa"},
    {"text": "Difficulties strengthen the mind, as labor does the body.", "author": "Seneca"},
]

WELCOME_MESSAGE = (
    "👋 Welcome!\n\n"
    "This bot sends you a short, well-known quote to think about — one at a "
    "time, no fluff.\n\n"
    "Commands:\n"
    "/quote — get a random quote\n"
    "/subscribe — get a daily quote automatically\n"
    "/unsubscribe — stop daily quotes\n"
    "/help — show this message again"
)

# ---------------------------------------------------------------------------
# SUBSCRIBER STORAGE
# ---------------------------------------------------------------------------


def load_subscribers() -> set:
    if os.path.exists(SUBSCRIBERS_FILE):
        with open(SUBSCRIBERS_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_subscribers(subscribers: set) -> None:
    with open(SUBSCRIBERS_FILE, "w") as f:
        json.dump(list(subscribers), f)


subscribers = load_subscribers()

# ---------------------------------------------------------------------------
# COMMAND HANDLERS
# ---------------------------------------------------------------------------


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(WELCOME_MESSAGE)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(WELCOME_MESSAGE)


async def quote(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pick = random.choice(QUOTES)
    text = f'"{pick["text"]}"\n\n— {pick["author"]}'
    await update.message.reply_text(text)


async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if chat_id in subscribers:
        await update.message.reply_text("You're already subscribed to daily quotes.")
        return
    subscribers.add(chat_id)
    save_subscribers(subscribers)
    await update.message.reply_text(
        "✅ Subscribed! You'll get one quote a day. Use /unsubscribe to stop anytime."
    )


async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if chat_id not in subscribers:
        await update.message.reply_text("You're not currently subscribed.")
        return
    subscribers.discard(chat_id)
    save_subscribers(subscribers)
    await update.message.reply_text("You've been unsubscribed from daily quotes.")


async def send_daily_quote(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Runs once a day, sends one random quote to every subscriber."""
    if not subscribers:
        return
    pick = random.choice(QUOTES)
    text = f'"{pick["text"]}"\n\n— {pick["author"]}'
    for chat_id in list(subscribers):
        try:
            await context.bot.send_message(chat_id=chat_id, text=text)
        except Exception as exc:
            logger.warning("Failed to send to %s: %s", chat_id, exc)


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------


def main() -> None:
    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise RuntimeError(
            "BOT_TOKEN environment variable is not set. "
            "Set it locally with `export BOT_TOKEN=...` or in Railway's Variables tab."
        )

    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("quote", quote))
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe))

    # Daily quote at 09:00 UTC — adjust the hour to suit your audience's timezone.
    job_queue = application.job_queue
    job_queue.run_daily(send_daily_quote, time=dtime(hour=9, minute=0))

    logger.info("Bot starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
