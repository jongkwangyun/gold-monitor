import io
from typing import List

from .models import MetalQuote


def _last(values: List[float], count: int) -> List[float]:
    return values[-count:] if len(values) > count else values


def render_quote_chart_png(quote: MetalQuote, days: int = 520) -> bytes:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    closes = _last(list(quote.closes), days)
    dates = _last(list(quote.dates), len(closes))
    x_values = list(range(len(closes)))

    fig, ax = plt.subplots(figsize=(10, 4.8), dpi=140)
    ax.plot(x_values, closes, linewidth=1.6, color="#1f77b4", label="Close")
    ax.set_title(f"{quote.name} - 2Y Daily Close")
    ax.set_ylabel(quote.currency)
    ax.grid(True, alpha=0.25)
    ax.legend(loc="upper left")

    if dates and len(dates) == len(closes):
        step = max(len(dates) // 6, 1)
        ticks = list(range(0, len(dates), step))
        ax.set_xticks(ticks)
        ax.set_xticklabels([dates[index] for index in ticks], rotation=30, ha="right")

    fig.tight_layout()
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png")
    plt.close(fig)
    return buffer.getvalue()
