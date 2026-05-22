from typing import Iterable, List

from .price_client import MetalQuote


class Condition:
    name = "base"

    def evaluate(self, quotes: Iterable[MetalQuote]) -> List[str]:
        return []


class DailyMoveCondition(Condition):
    name = "daily_move"

    def __init__(self, threshold_pct: float) -> None:
        self.threshold_pct = threshold_pct

    def evaluate(self, quotes: Iterable[MetalQuote]) -> List[str]:
        alerts: List[str] = []
        for quote in quotes:
            if quote.change_pct is None:
                continue
            if abs(quote.change_pct) >= self.threshold_pct:
                alerts.append(
                    f"{quote.name} daily move {quote.change_pct:+.2f}% "
                    f"(threshold {self.threshold_pct:.2f}%)"
                )
        return alerts


def load_conditions() -> List[Condition]:
    # Add future conditions here, such as MA cross or volatility alerts.
    return []

