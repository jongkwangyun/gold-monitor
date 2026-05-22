from html import escape
from typing import Iterable, Optional

from .price_client import MetalQuote


def _fmt_price(value: Optional[float], currency: str = "USD") -> str:
    if value is None:
        return "N/A"
    prefix = "$" if currency.upper() == "USD" else f"{currency} "
    return f"{prefix}{value:,.2f}"


def _fmt_pct(value: Optional[float]) -> str:
    if value is None:
        return "N/A"
    return f"{value:+.2f}%"


def _fmt_ma_line(label: str, price: float, ma_value: Optional[float], currency: str) -> str:
    if ma_value is None:
        return f"- {label}: N/A"
    pos = "above" if price > ma_value else "below"
    pct = ((price / ma_value) - 1.0) * 100.0
    return f"- {label}: {_fmt_price(ma_value, currency)} / current is <b>{pos}</b> ({pct:+.2f}%)"


def format_quote_html(quote: MetalQuote) -> str:
    lines = [
        f"<b>{escape(quote.name)}</b>",
        f"Price: <b>{_fmt_price(quote.price, quote.currency)}</b>",
        f"Source: <b>{escape(quote.realtime_source)}</b> ({escape(quote.symbol)})",
        f"Historical: <b>{escape(quote.historical_source)}</b> ({escape(quote.historical_symbol)})",
        f"DataQuality: <b>{escape(quote.data_quality)}</b>",
        f"Stale: <b>{'yes' if quote.stale else 'no'}</b>",
        f"MA available: <b>{'yes' if quote.ma_available else 'no'}</b>",
        f"Asset kind: <b>{escape(str(quote.asset_kind.value))}</b>",
        f"1D: <b>{_fmt_pct(quote.change_pct)}</b>",
    ]
    if quote.previous_close is not None:
        lines.append(f"Previous close: {_fmt_price(quote.previous_close, quote.currency)}")
    if quote.market_time is not None:
        lines.append(f"Market time: {escape(quote.market_time.strftime('%Y-%m-%d %H:%M:%S %Z'))}")
    lines.extend(
        [
            _fmt_ma_line("MA20", quote.price, quote.ma20, quote.currency),
            _fmt_ma_line("MA50", quote.price, quote.ma50, quote.currency),
            _fmt_ma_line("MA200", quote.price, quote.ma200, quote.currency),
        ]
    )
    return "\n".join(lines)


def format_regular_report(quotes: Iterable[MetalQuote]) -> str:
    body = "\n\n".join(format_quote_html(quote) for quote in quotes)
    return f"<b>Gold/Silver Regular Report</b>\n\n{body}"


def format_condition_alert(messages: Iterable[str], quotes: Iterable[MetalQuote]) -> str:
    alert_lines = "\n".join(f"- {escape(message)}" for message in messages)
    return f"<b>Gold/Silver Alert</b>\n{alert_lines}\n\n{format_regular_report(quotes)}"
