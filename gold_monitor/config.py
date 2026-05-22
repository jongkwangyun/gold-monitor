from pathlib import Path

from common.config import ensure_dir, env_csv_ints, env_int, env_str, load_env

PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent

load_env(PROJECT_ROOT)

TIMEZONE = env_str("GOLD_TIMEZONE", "Asia/Seoul")
POLL_INTERVAL_SECONDS = env_int("GOLD_POLL_INTERVAL_SECONDS", 300)
REPORT_HOURS = env_csv_ints("GOLD_REPORT_HOURS", [8, 20])

GOLD_SPOT_SYMBOL = env_str("GOLD_SPOT_SYMBOL", "XAU/USD")
SILVER_SPOT_SYMBOL = env_str("SILVER_SPOT_SYMBOL", "XAG/USD")
GOLD_YAHOO_SYMBOL = env_str("GOLD_YAHOO_SYMBOL", "GC=F")
SILVER_YAHOO_SYMBOL = env_str("SILVER_YAHOO_SYMBOL", "SI=F")

DATA_DIR = ensure_dir(Path(env_str("GOLD_DATA_DIR") or str(PROJECT_ROOT / "data")).resolve())
LOG_DIR = ensure_dir(Path(env_str("GOLD_LOG_DIR") or str(PROJECT_ROOT / "logs")).resolve())
CACHE_DIR = ensure_dir(Path(env_str("GOLD_CACHE_DIR") or str(PROJECT_ROOT / ".cache")).resolve())
REPORT_STATE_PATH = Path(env_str("GOLD_REPORT_STATE") or str(DATA_DIR / "report_state.json")).resolve()

TELEGRAM_BOT_TOKEN = env_str("GOLD_TELEGRAM_BOT_TOKEN") or env_str("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = env_str("GOLD_TELEGRAM_CHAT_ID") or env_str("TELEGRAM_CHAT_ID")
ALLOWED_CHAT_IDS = env_str("GOLD_ALLOWED_CHAT_IDS") or env_str("ALLOWED_CHAT_IDS")

TWELVEDATA_API_KEY = env_str("TWELVEDATA_API_KEY")
HISTORICAL_DAYS = env_int("GOLD_HISTORICAL_DAYS", 520)
TWELVEDATA_OUTPUTSIZE = env_int("TWELVEDATA_OUTPUTSIZE", HISTORICAL_DAYS)
TWELVEDATA_RETRY_COUNT = env_int("TWELVEDATA_RETRY_COUNT", 3)
