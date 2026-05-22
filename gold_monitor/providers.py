from datetime import datetime, timezone
import logging
import time
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo

from common.http_session import get_session

from .cache import is_fresh_daily_cache, load_daily_cache, save_daily_cache
from .config import TIMEZONE, TWELVEDATA_API_KEY, TWELVEDATA_OUTPUTSIZE, TWELVEDATA_RETRY_COUNT
from .models import AssetKind, HistoricalSeries, LatestPrice, MetalInstrument

LOG = logging.getLogger(__name__)
_SESSION = get_session()

REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125 Safari/537.36"
    ),
    "Accept": "application/json,text/plain,*/*",
}


def _request_json(url: str, *, params: Optional[Dict[str, object]] = None) -> Dict[str, object]:
    last_exc: Optional[Exception] = None
    for attempt in range(1, TWELVEDATA_RETRY_COUNT + 1):
        try:
            response = _SESSION.get(url, params=params, headers=REQUEST_HEADERS, timeout=20)
            if response.status_code == 429 and attempt < TWELVEDATA_RETRY_COUNT:
                wait = 2 ** attempt
                LOG.warning("Rate limited by %s, retrying in %ss", url, wait)
                time.sleep(wait)
                continue
            response.raise_for_status()
            payload = response.json()
            if isinstance(payload, dict):
                return payload
            raise RuntimeError("Response was not a JSON object")
        except Exception as exc:
            last_exc = exc
            if attempt < TWELVEDATA_RETRY_COUNT:
                wait = 2 ** attempt
                LOG.warning("Request failed (%d/%d), retrying in %ss: %s", attempt, TWELVEDATA_RETRY_COUNT, wait, exc)
                time.sleep(wait)
    raise RuntimeError(f"Request failed after {TWELVEDATA_RETRY_COUNT} attempts: {last_exc}")


def _parse_iso_time(raw: object) -> Optional[datetime]:
    if not isinstance(raw, str) or not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(ZoneInfo(TIMEZONE))
    except ValueError:
        return None


class ConvertzProvider:
    source = "Convertz"

    def fetch_latest_many(self, instruments: Dict[str, MetalInstrument]) -> Dict[str, LatestPrice]:
        payload = _request_json("https://convertz.app/api/metals")
        prices = payload.get("prices")
        if not isinstance(prices, dict):
            raise RuntimeError("Convertz prices field is missing")

        timestamp = _parse_iso_time(payload.get("timestamp") or payload.get("updated_at"))
        if timestamp is None:
            timestamp = datetime.now(timezone.utc).astimezone(ZoneInfo(TIMEZONE))

        result: Dict[str, LatestPrice] = {}
        for key, instrument in instruments.items():
            metal_prices = prices.get(instrument.metal_code) or {}
            price = metal_prices.get("USD") if isinstance(metal_prices, dict) else None
            if price is None:
                raise RuntimeError(f"Convertz price missing for {instrument.metal_code}")
            result[key] = LatestPrice(
                price=float(price),
                currency="USD",
                source=self.source,
                asset_kind=AssetKind.SPOT,
                symbol=instrument.spot_symbol,
                market_time=timestamp,
            )
        return result


class TwelveDataProvider:
    source = "TwelveData"

    def _require_key(self) -> str:
        if not TWELVEDATA_API_KEY:
            raise RuntimeError("TWELVEDATA_API_KEY is not configured")
        return TWELVEDATA_API_KEY

    def fetch_latest(self, instrument: MetalInstrument) -> LatestPrice:
        payload = _request_json(
            "https://api.twelvedata.com/quote",
            params={"symbol": instrument.spot_symbol, "apikey": self._require_key()},
        )
        if payload.get("status") == "error":
            raise RuntimeError(str(payload.get("message") or payload))

        price = payload.get("close") or payload.get("price")
        if price is None:
            raise RuntimeError(f"Twelve Data latest price missing for {instrument.spot_symbol}")

        timestamp = _parse_iso_time(payload.get("datetime") or payload.get("timestamp"))
        return LatestPrice(
            price=float(price),
            currency=str(payload.get("currency") or "USD"),
            source=self.source,
            asset_kind=AssetKind.SPOT,
            symbol=instrument.spot_symbol,
            market_time=timestamp,
        )

    def fetch_historical(self, instrument: MetalInstrument) -> HistoricalSeries:
        cache_name = f"twelvedata_{instrument.spot_symbol}_1day"
        cached = load_daily_cache(cache_name)
        if cached and is_fresh_daily_cache(cached):
            closes = [float(value) for value in cached.get("closes", [])]
            if closes:
                return HistoricalSeries(
                    closes=closes,
                    dates=[str(value) for value in cached.get("dates", [])],
                    source=f"{self.source}Cache",
                    asset_kind=AssetKind.SPOT,
                    symbol=instrument.spot_symbol,
                    stale=False,
                    last_date=cached.get("last_date"),
                )

        try:
            payload = _request_json(
                "https://api.twelvedata.com/time_series",
                params={
                    "symbol": instrument.spot_symbol,
                    "interval": "1day",
                    "outputsize": TWELVEDATA_OUTPUTSIZE,
                    "apikey": self._require_key(),
                },
            )
            if payload.get("status") == "error":
                raise RuntimeError(str(payload.get("message") or payload))

            values = payload.get("values")
            if not isinstance(values, list):
                raise RuntimeError(f"Twelve Data values missing for {instrument.spot_symbol}")

            rows = list(reversed(values))
            closes: List[float] = []
            dates: List[str] = []
            last_date = None
            for row in rows:
                if not isinstance(row, dict) or row.get("close") is None:
                    continue
                closes.append(float(row["close"]))
                dates.append(str(row.get("datetime") or ""))
                last_date = str(row.get("datetime") or last_date)
            if not closes:
                raise RuntimeError(f"Twelve Data close prices missing for {instrument.spot_symbol}")

            save_daily_cache(cache_name, {"closes": closes, "dates": dates, "last_date": last_date})
            return HistoricalSeries(
                closes=closes,
                dates=dates,
                source=self.source,
                asset_kind=AssetKind.SPOT,
                symbol=instrument.spot_symbol,
                stale=False,
                last_date=last_date,
            )
        except Exception:
            if cached:
                closes = [float(value) for value in cached.get("closes", [])]
                if closes:
                    LOG.warning("Using stale Twelve Data cache for %s", instrument.spot_symbol)
                    return HistoricalSeries(
                        closes=closes,
                        dates=[str(value) for value in cached.get("dates", [])],
                        source=f"{self.source}Cache",
                        asset_kind=AssetKind.SPOT,
                        symbol=instrument.spot_symbol,
                        stale=True,
                        last_date=cached.get("last_date"),
                    )
            raise


class YahooDirectProvider:
    source = "YahooDirect"

    def _fetch_chart(self, symbol: str, range_: str = "260d") -> Dict[str, object]:
        return _request_json(
            f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
            params={"range": range_, "interval": "1d", "includePrePost": "false"},
        )

    def fetch_latest(self, instrument: MetalInstrument) -> LatestPrice:
        payload = self._fetch_chart(instrument.yahoo_symbol, range_="5d")
        result = (payload.get("chart", {}).get("result") or [None])[0]
        if not isinstance(result, dict):
            raise RuntimeError(f"Yahoo chart data missing for {instrument.yahoo_symbol}")
        meta = result.get("meta") or {}
        if not isinstance(meta, dict):
            raise RuntimeError(f"Yahoo meta missing for {instrument.yahoo_symbol}")
        price = meta.get("regularMarketPrice")
        if price is None:
            quote = ((result.get("indicators") or {}).get("quote") or [{}])[0]
            closes = quote.get("close") if isinstance(quote, dict) else []
            price = next((value for value in reversed(closes) if value is not None), None)
        if price is None:
            raise RuntimeError(f"Yahoo latest price missing for {instrument.yahoo_symbol}")

        market_time = None
        raw_time = meta.get("regularMarketTime")
        if raw_time:
            market_time = datetime.fromtimestamp(int(raw_time), ZoneInfo(TIMEZONE))

        return LatestPrice(
            price=float(price),
            currency=str(meta.get("currency") or "USD"),
            source=self.source,
            asset_kind=AssetKind.FUTURES,
            symbol=instrument.yahoo_symbol,
            market_time=market_time,
        )

    def fetch_historical(self, instrument: MetalInstrument) -> HistoricalSeries:
        payload = self._fetch_chart(instrument.yahoo_symbol)
        result = (payload.get("chart", {}).get("result") or [None])[0]
        if not isinstance(result, dict):
            raise RuntimeError(f"Yahoo chart data missing for {instrument.yahoo_symbol}")

        quote = ((result.get("indicators") or {}).get("quote") or [{}])[0]
        closes = [float(value) for value in quote.get("close", []) if value is not None] if isinstance(quote, dict) else []
        if not closes:
            raise RuntimeError(f"Yahoo close prices missing for {instrument.yahoo_symbol}")

        timestamps = result.get("timestamp") or []
        dates = [
            datetime.fromtimestamp(int(value), ZoneInfo(TIMEZONE)).strftime("%Y-%m-%d")
            for value in timestamps[-len(closes):]
        ]
        last_date = None
        if timestamps:
            last_date = datetime.fromtimestamp(int(timestamps[-1]), ZoneInfo(TIMEZONE)).strftime("%Y-%m-%d")

        return HistoricalSeries(
            closes=closes,
            dates=dates,
            source=self.source,
            asset_kind=AssetKind.FUTURES,
            symbol=instrument.yahoo_symbol,
            stale=False,
            last_date=last_date,
        )
