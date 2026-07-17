import logging
import os
from io import BytesIO

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

from fetcher import fetch_html

logger = logging.getLogger(__name__)

# Conversation state
WAITING_FOR_URL = 1

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [[KeyboardButton("📥 FECH HTML")]],
    resize_keyboard=True,
    one_time_keyboard=False,
)


# ── /start ────────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 *HTML Fetcher Bot*\n\n"
        "নিচের বাটনে ক্লিক করো, তারপর যে URL থেকে HTML নামাতে চাও সেটা পাঠাও।\n\n"
        "Bot টি anti-bot challenge (AES cookie challenge) অটোমেটিক সলভ করে real HTML ফাইল দিবে।",
        parse_mode="Markdown",
        reply_markup=MAIN_KEYBOARD,
    )


# ── Button: FECH HTML ─────────────────────────────────────────────────────────

async def fech_html_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "🔗 URL টা পাঠাও (যেমন: https://example.com/page.html)\n\n"
        "বাতিল করতে /cancel লেখো।",
        reply_markup=ReplyKeyboardRemove(),
    )
    return WAITING_FOR_URL


# ── URL received ──────────────────────────────────────────────────────────────

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    url = update.message.text.strip()

    # Basic URL validation
    if not url.startswith(("http://", "https://")):
        await update.message.reply_text(
            "❌ Valid URL দাও। `http://` বা `https://` দিয়ে শুরু হতে হবে।\n\n"
            "আবার চেষ্টা করো অথবা /cancel লেখো।",
            parse_mode="Markdown",
        )
        return WAITING_FOR_URL

    status_msg = await update.message.reply_text(f"⏳ Fetching করছি...\n`{url}`", parse_mode="Markdown")

    try:
        html_content, filename = fetch_html(url)

        file_bytes = BytesIO(html_content.encode("utf-8"))
        file_bytes.name = filename

        await status_msg.delete()
        await update.message.reply_document(
            document=file_bytes,
            filename=filename,
            caption=(
                f"✅ *সফল!*\n"
                f"📄 File: `{filename}`\n"
                f"📦 Size: {len(html_content):,} bytes"
            ),
            parse_mode="Markdown",
            reply_markup=MAIN_KEYBOARD,
        )

    except ValueError as e:
        await status_msg.delete()
        await update.message.reply_text(
            f"{e}",
            reply_markup=MAIN_KEYBOARD,
        )
    except Exception as e:
        logger.exception("Fetch error for %s", url)
        await status_msg.delete()
        await update.message.reply_text(
            f"❌ *Error:* `{e}`\n\nURL চেক করো এবং আবার চেষ্টা করো।",
            parse_mode="Markdown",
            reply_markup=MAIN_KEYBOARD,
        )

    return ConversationHandler.END


# ── /cancel ───────────────────────────────────────────────────────────────────

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "❎ বাতিল করা হয়েছে।",
        reply_markup=MAIN_KEYBOARD,
    )
    return ConversationHandler.END


# ── Unknown text (outside conversation) ───────────────────────────────────────

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👇 নিচের বাটন ব্যবহার করো।",
        reply_markup=MAIN_KEYBOARD,
    )


# ── Build and return the Application ─────────────────────────────────────────

def build_app() -> Application:
    token = os.environ["BOT_TOKEN"]
    app = Application.builder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^📥 FECH HTML$"), fech_html_button)
        ],
        states={
            WAITING_FOR_URL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown))

    return app
