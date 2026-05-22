import argparse
import logging
import time
from typing import Dict

from common.logging import setup_logging
from common.telegram import send_telegram_html, send_telegram_photo

from .chart import render_quote_chart_png
from .conditions import load_conditions
from .config import (
    GOLD_SPOT_SYMBOL,
    GOLD_YAHOO_SYMBOL,
    LOG_DIR,
    POLL_INTERVAL_SECONDS,
    SILVER_SPOT_SYMBOL,
    SILVER_YAHOO_SYMBOL,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
)
from .models import MetalInstrument
from .price_client import fetch_metal_quotes
from .report import format_condition_alert, format_regular_report
from .state import should_send_regular_report

LOG = logging.getLogger(__name__)


def symbol_map() -> Dict[str, MetalInstrument]:
    return {
        "gold": MetalInstrument(
            key="gold",
            name="Gold",
            metal_code="XAU",
            spot_symbol=GOLD_SPOT_SYMBOL,
            yahoo_symbol=GOLD_YAHOO_SYMBOL,
        ),
        "silver": MetalInstrument(
            key="silver",
            name="Silver",
            metal_code="XAG",
            spot_symbol=SILVER_SPOT_SYMBOL,
            yahoo_symbol=SILVER_YAHOO_SYMBOL,
        ),
    }


def run_once(force_report: bool = False) -> None:
    quotes = fetch_metal_quotes(symbol_map())
    quote_list = list(quotes.values())

    condition_messages = []
    for condition in load_conditions():
        condition_messages.extend(condition.evaluate(quote_list))

    if condition_messages:
        LOG.info("Sending condition alert.")
        send_telegram_html(
            format_condition_alert(condition_messages, quote_list),
            token=TELEGRAM_BOT_TOKEN,
            chat_id=TELEGRAM_CHAT_ID,
        )

    if force_report or should_send_regular_report():
        LOG.info("Sending regular report.")
        send_telegram_html(
            format_regular_report(quote_list),
            token=TELEGRAM_BOT_TOKEN,
            chat_id=TELEGRAM_CHAT_ID,
        )
        send_charts(quote_list)
    else:
        LOG.info("No scheduled report due.")


def send_charts(quotes) -> None:
    for quote in quotes:
        if len(quote.closes) < 2:
            LOG.info("Skipping chart for %s because historical data is unavailable.", quote.name)
            continue
        try:
            chart_png = render_quote_chart_png(quote)
            send_telegram_photo(
                chart_png,
                caption=f"<b>{quote.name} 2Y Chart</b>\nSource: {quote.historical_source} ({quote.historical_symbol})",
                token=TELEGRAM_BOT_TOKEN,
                chat_id=TELEGRAM_CHAT_ID,
            )
        except Exception:
            LOG.exception("Failed to send chart for %s", quote.name)


def main() -> int:
    parser = argparse.ArgumentParser(description="Gold/Silver monitor")
    parser.add_argument("--once", action="store_true", help="Run one check and exit.")
    parser.add_argument("--force-report", action="store_true", help="Send report regardless of schedule.")
    args = parser.parse_args()

    setup_logging("gold_monitor", LOG_DIR)

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        LOG.error("GOLD_TELEGRAM_BOT_TOKEN/GOLD_TELEGRAM_CHAT_ID must be configured.")
        return 1

    if args.once:
        run_once(force_report=args.force_report)
        return 0

    LOG.info("Starting polling loop. interval=%ss", POLL_INTERVAL_SECONDS)
    first_run = True
    while True:
        try:
            run_once(force_report=args.force_report and first_run)
        except Exception:
            LOG.exception("Monitor loop failed.")
        first_run = False
        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    raise SystemExit(main())
