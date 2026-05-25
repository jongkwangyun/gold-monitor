# Gold Monitor

Gold Monitor는 금(XAU/USD)과 은(XAG/USD) 시세를 조회해 Telegram으로 전송하는 Python 프로젝트입니다. 이 프로젝트는 같은 workspace의 `common` 패키지를 editable install로 사용합니다.

## 구조

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

## 설치

가상환경은 PC마다 새로 만들어야 합니다. 다른 PC나 다른 경로에서 만든 `.venv`를 복사해서 사용하면 `pip.exe`가 이전 Python 경로를 참조해 실행 오류가 발생할 수 있습니다.

```powershell
Set-Location C:\1work\gold-monitor
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

`requirements.txt`에는 `common` editable install이 포함되어 있습니다.

```text
-e ../common
```

## 기존 `.venv` 오류 해결

아래처럼 이전 PC의 경로를 참조하는 오류가 나오면 `.venv`를 삭제하고 다시 생성합니다.

```text
Fatal error in launcher: Unable to create process using ...
```

```powershell
Set-Location C:\1work\gold-monitor
deactivate
Remove-Item -Recurse -Force .venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 설정

`.env` 파일에 Telegram과 provider 설정을 입력합니다.

```env
GOLD_TELEGRAM_BOT_TOKEN=your_bot_token
GOLD_TELEGRAM_CHAT_ID=your_chat_id
GOLD_ALLOWED_CHAT_IDS=your_chat_id
GOLD_REPORT_HOURS=8,20
GOLD_POLL_INTERVAL_SECONDS=300
TWELVEDATA_API_KEY=
```

## 실행

모니터 실행:

```powershell
Set-Location C:\1work\gold-monitor
python -m gold_monitor.monitor
```

단발 실행:

```powershell
python -m gold_monitor.monitor --once
python -m gold_monitor.monitor --once --force-report
```

Telegram 명령 bot 실행:

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
