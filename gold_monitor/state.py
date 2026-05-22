import json
from datetime import datetime
from pathlib import Path
from typing import Dict
from zoneinfo import ZoneInfo

from .config import REPORT_HOURS, REPORT_STATE_PATH, TIMEZONE


def load_state(path: Path = REPORT_STATE_PATH) -> Dict[str, str]:
    if not path.is_file():
        return {"last_report": ""}
    try:
        with path.open(encoding="utf-8") as fp:
            data = json.load(fp)
        return data if isinstance(data, dict) else {"last_report": ""}
    except (json.JSONDecodeError, OSError):
        return {"last_report": ""}


def save_state(data: Dict[str, str], path: Path = REPORT_STATE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=2)


def should_send_regular_report(now: datetime | None = None, path: Path = REPORT_STATE_PATH) -> bool:
    current = now or datetime.now(ZoneInfo(TIMEZONE))
    if current.hour not in REPORT_HOURS:
        return False

    report_id = current.strftime("%Y-%m-%d-%H")
    state = load_state(path)
    if state.get("last_report") == report_id:
        return False

    state["last_report"] = report_id
    save_state(state, path)
    return True

