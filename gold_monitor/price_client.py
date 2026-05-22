import logging
from typing import Dict, List, Optional

from .models import AssetKind, HistoricalSeries, LatestPrice, MetalInstrument, MetalQuote
from .providers import ConvertzProvider, TwelveDataProvider, YahooDirectProvider

LOG = logging.getLogger(__name__)


def _moving_average(values: List[float], window: int) -> Optional[float]:
    if len(values) < window:
        return None
    return sum(values[-window:]) / window


def _build_quote(
    instrument: MetalInstrument,
    latest: LatestPrice,
    historical: Optional[HistoricalSeries],
) -> MetalQuote:
    closes = historical.closes if historical else []
    previous_close = closes[-1] if closes else None
    change_abs = latest.price - previous_close if previous_close else None
    change_pct = ((latest.price / previous_close) - 1.0) * 100.0 if previous_close else None

    ma20 = _moving_average(closes, 20)
    ma50 = _moving_average(closes, 50)
    ma200 = _moving_average(closes, 200)
    ma_available = ma20 is not None and ma50 is not None and ma200 is not None

    if historical and ma_available:
        quality = "realtime+historical"
    elif historical:
        quality = "realtime+partial_historical"
    else:
        quality = "realtime_only"

    return MetalQuote(
        symbol=latest.symbol,
        name=instrument.name,
        price=latest.price,
        currency=latest.currency,
        previous_close=previous_close,
        change_abs=change_abs,
        change_pct=change_pct,
        market_time=latest.market_time,
        closes=closes or [latest.price],
        ma20=ma20,
        ma50=ma50,
        ma200=ma200,
        realtime_source=latest.source,
        historical_source=historical.source if historical else "N/A",
        data_quality=quality,
        stale=historical.stale if historical else False,
        ma_available=ma_available,
        asset_kind=historical.asset_kind if historical else latest.asset_kind,
        historical_symbol=historical.symbol if historical else "N/A",
    )


def _fetch_latest_prices(instruments: Dict[str, MetalInstrument]) -> Dict[str, LatestPrice]:
    convertz = ConvertzProvider()
    twelve = TwelveDataProvider()
    yahoo = YahooDirectProvider()

    try:
        return convertz.fetch_latest_many(instruments)
    except Exception as exc:
        LOG.warning("Convertz latest prices failed, falling back per symbol: %s", exc)

    latest: Dict[str, LatestPrice] = {}
    for key, instrument in instruments.items():
        try:
            latest[key] = twelve.fetch_latest(instrument)
            continue
        except Exception as exc:
            LOG.warning("Twelve Data latest failed for %s: %s", instrument.spot_symbol, exc)
        try:
            latest[key] = yahoo.fetch_latest(instrument)
        except Exception as exc:
            LOG.warning("Yahoo latest failed for %s: %s", instrument.yahoo_symbol, exc)
    return latest


def _fetch_historical(instrument: MetalInstrument) -> Optional[HistoricalSeries]:
    twelve = TwelveDataProvider()
    yahoo = YahooDirectProvider()

    try:
        return twelve.fetch_historical(instrument)
    except Exception as exc:
        LOG.warning("Twelve Data historical failed for %s: %s", instrument.spot_symbol, exc)

    try:
        return yahoo.fetch_historical(instrument)
    except Exception as exc:
        LOG.warning("Yahoo historical failed for %s: %s", instrument.yahoo_symbol, exc)
        return None


def fetch_quote(instrument: MetalInstrument) -> MetalQuote:
    latest_map = _fetch_latest_prices({instrument.key: instrument})
    latest = latest_map.get(instrument.key)
    if latest is None:
        raise RuntimeError(f"All latest price providers failed for {instrument.name}")
    historical = _fetch_historical(instrument)
    return _build_quote(instrument, latest, historical)


def fetch_metal_quotes(instruments: Dict[str, MetalInstrument]) -> Dict[str, MetalQuote]:
    latest = _fetch_latest_prices(instruments)
    quotes: Dict[str, MetalQuote] = {}
    for key, instrument in instruments.items():
        latest_price = latest.get(key)
        if latest_price is None:
            LOG.error("Skipping %s because all latest providers failed.", instrument.name)
            continue
        historical = _fetch_historical(instrument)
        quotes[key] = _build_quote(instrument, latest_price, historical)
    if not quotes:
        raise RuntimeError("All metal quote providers failed")
    return quotes


__all__ = ["AssetKind", "MetalInstrument", "MetalQuote", "fetch_quote", "fetch_metal_quotes"]
