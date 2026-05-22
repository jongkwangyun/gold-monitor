import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from zoneinfo import ZoneInfo

from .config import CACHE_DIR, TIMEZONE


def _cache_path(name: str) -> Path:
    safe = "".join(ch if ch.isalnum() else "_" for ch in name)
    return CACHE_DIR / f"{safe}.json"


def load_daily_cache(name: str) -> Optional[Dict[str, Any]]:
    path = _cache_path(name)
    if not path.is_file():
        return None
    try:
        with path.open(encoding="utf-8") as fp:
            data = json.load(fp)
        return data if isinstance(data, dict) else None
    except (json.JSONDecodeError, OSError):
        return None


def save_daily_cache(name: str, data: Dict[str, Any]) -> None:
    path = _cache_path(name)
    payload = dict(data)
    payload["cache_date"] = datetime.now(ZoneInfo(TIMEZONE)).strftime("%Y-%m-%d")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=2)


def is_fresh_daily_cache(data: Dict[str, Any]) -> bool:
    today = datetime.now(ZoneInfo(TIMEZONE)).strftime("%Y-%m-%d")
    return data.get("cache_date") == today
