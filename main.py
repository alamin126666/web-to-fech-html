import asyncio
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


def run_flask():
    port = int(os.environ.get("PORT", 10000))
    logger.info("Starting Flask on port %d", port)
    flask_app.run(host="0.0.0.0", port=port, use_reloader=False)


# ── Bot async entry (low-level API — avoids run_polling signal issues) ────────
async def run_bot_async():
    tg_app = build_app()
    async with tg_app:
        await tg_app.start()
        logger.info("Telegram bot started, polling...")
        await tg_app.updater.start_polling(drop_pending_updates=True)
        # Block forever until process is killed
        await asyncio.Event().wait()
        await tg_app.updater.stop()
        await tg_app.stop()


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Flask in background daemon thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Bot runs via asyncio.run() — creates its own event loop cleanly
    asyncio.run(run_bot_async())
