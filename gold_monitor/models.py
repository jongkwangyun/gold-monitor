from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional


class AssetKind(str, Enum):
    SPOT = "spot"
    FUTURES = "futures"


@dataclass(frozen=True)
class MetalInstrument:
    key: str
    name: str
    metal_code: str
    spot_symbol: str
    yahoo_symbol: str


@dataclass(frozen=True)
class LatestPrice:
    price: float
    currency: str
    source: str
    asset_kind: AssetKind
    symbol: str
    market_time: Optional[datetime]


@dataclass(frozen=True)
class HistoricalSeries:
    closes: List[float]
    source: str
    asset_kind: AssetKind
    symbol: str
    stale: bool
    last_date: Optional[str]


@dataclass(frozen=True)
class MetalQuote:
    symbol: str
    name: str
    price: float
    currency: str
    previous_close: Optional[float]
    change_abs: Optional[float]
    change_pct: Optional[float]
    market_time: Optional[datetime]
    closes: List[float]
    ma20: Optional[float]
    ma50: Optional[float]
    ma200: Optional[float]
    realtime_source: str
    historical_source: str
    data_quality: str
    stale: bool
    ma_available: bool
    asset_kind: AssetKind
    historical_symbol: str
