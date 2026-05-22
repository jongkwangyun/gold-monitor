import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from common.logging import setup_logging

from .config import ALLOWED_CHAT_IDS, LOG_DIR, TELEGRAM_BOT_TOKEN
from .monitor import symbol_map
from .price_client import fetch_metal_quotes
from .report import format_regular_report

LOG = logging.getLogger(__name__)


def allowed_chat(update: Update) -> bool:
    if not ALLOWED_CHAT_IDS:
        return True
    chat_id = update.effective_chat.id if update.effective_chat else None
    if chat_id is None:
        return False
    allowed = {int(item.strip()) for item in ALLOWED_CHAT_IDS.split(",") if item.strip().isdigit()}
    return chat_id in allowed


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not allowed_chat(update):
        return
    await update.message.reply_html("<b>Gold Monitor</b>\n/gold - XAU/USD and XAG/USD snapshot")


async def cmd_gold(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not allowed_chat(update):
        await update.message.reply_text("This chat is not allowed.")
        return
    await update.message.reply_chat_action(action="typing")
    try:
        quotes = fetch_metal_quotes(symbol_map())
        await update.message.reply_html(format_regular_report(quotes.values()))
    except Exception as exc:
        LOG.exception("gold command failed")
        await update.message.reply_text(f"Lookup failed: {exc}")


def main() -> None:
    setup_logging("gold_bot", LOG_DIR)
    if not TELEGRAM_BOT_TOKEN:
        raise SystemExit("GOLD_TELEGRAM_BOT_TOKEN is required.")

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("gold", cmd_gold))

    LOG.info("Starting Telegram polling.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()

