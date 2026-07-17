import logging
import os
import threading

from flask import Flask
from bot import build_app

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ── Flask (health endpoint for Cron-job.org keep-alive) ──────────────────────
flask_app = Flask(__name__)

@flask_app.route("/health")
def health():
    return "OK", 200

@flask_app.route("/")
def index():
    return "HTML Fetcher Bot is running ✅", 200


# ── Bot polling thread ────────────────────────────────────────────────────────
def run_bot():
    logger.info("Starting Telegram bot polling...")
    tg_app = build_app()
    tg_app.run_polling(drop_pending_updates=True)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Start bot in background thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()

    # Start Flask (keeps Render web service alive)
    port = int(os.environ.get("PORT", 10000))
    logger.info("Starting Flask on port %d", port)
    flask_app.run(host="0.0.0.0", port=port)
