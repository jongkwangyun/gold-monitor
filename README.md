# Gold Monitor

Gold Monitor? ?(XAU/USD)? ?(XAG/USD) ??? ??? Telegram?? ???? Python ???????. ? ????? workspace monorepo? `common` ???? editable install? ?????.

## ??

```text
gold-monitor/
 gold_monitor/
    __init__.py
    bot.py
    monitor.py
    ...
 requirements.txt
 README.md
```

## ??

```powershell
Set-Location C:\1work\gold-monitor
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

`requirements.txt`?? ?? ??? ??? ?????.

```powershell
pip install -e ../common
```

## ??

`.env` ??? Telegram? provider ??? ?????.

```env
GOLD_TELEGRAM_BOT_TOKEN=your_bot_token
GOLD_TELEGRAM_CHAT_ID=your_chat_id
GOLD_ALLOWED_CHAT_IDS=your_chat_id
GOLD_REPORT_HOURS=8,20
GOLD_POLL_INTERVAL_SECONDS=300
TWELVEDATA_API_KEY=
```

## ??

?? ??? ??:

```powershell
Set-Location C:\1work\gold-monitor
python -m gold_monitor.monitor
```

?? ??:

```powershell
python -m gold_monitor.monitor --once
python -m gold_monitor.monitor --once --force-report
```

Run the Telegram command bot:

```powershell
python -m gold_monitor.bot
```

## Import rules

Use the editable-installed `common` package with absolute imports.

```python
from common.logging import setup_logging
from common.telegram import send_telegram_html
```

Do not rely on `sys.path` changes or manual `PYTHONPATH` settings.
