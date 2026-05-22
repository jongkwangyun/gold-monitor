# Gold Monitor

Gold Monitor는 금(XAU/USD)과 은(XAG/USD) 시세를 조회해 Telegram으로 전송하는 Python 기반 모니터입니다. 프로젝트 폴더명은 `gold-monitor`이고, Python 패키지명은 하이픈을 사용할 수 없어 내부적으로 `gold_monitor`를 사용합니다.

## 구조

```text
D:\1work
├── common
├── bitcoin-monitor
└── gold-monitor
    └── gold_monitor
```

## Provider 우선순위

실시간 가격:

1. Convertz `/api/metals`
2. Twelve Data `/quote`
3. Yahoo direct chart endpoint

과거 일봉 데이터:

1. Twelve Data `/time_series`
2. Yahoo direct chart endpoint

기본 모델은 spot과 futures를 분리합니다.

- spot: `XAU/USD`, `XAG/USD`
- futures fallback: `GC=F`, `SI=F`

Convertz는 실시간 가격만 제공하므로 historical provider가 모두 실패하면 리포트는 `realtime_only`로 유지되고 MA20/50/200은 `N/A`가 됩니다. Twelve Data 또는 Yahoo historical이 성공하면 MA20/50/200을 계산합니다.

## 데이터 품질 표시

리포트에는 다음 항목이 포함됩니다.

- `Source`: 실시간 가격 provider
- `Historical`: 일봉 provider
- `DataQuality`: `realtime+historical`, `realtime+partial_historical`, `realtime_only`
- `Stale`: 오래된 캐시 사용 여부
- `MA available`: MA20/50/200 계산 가능 여부
- `Asset kind`: `spot` 또는 `futures`

## Twelve Data

Twelve Data는 `TWELVEDATA_API_KEY`가 있으면 우선 historical source로 사용됩니다.

```env
TWELVEDATA_API_KEY=your_api_key
TWELVEDATA_OUTPUTSIZE=260
TWELVEDATA_RETRY_COUNT=3
```

무료 플랜은 분당/일일 API credit 제한이 있으므로 historical daily 데이터는 `.cache`에 저장하고 하루 1회만 새로 조회합니다. API 실패 시 기존 캐시가 있으면 stale cache를 사용해 MA 계산을 유지합니다.

공식 문서 기준으로 Twelve Data의 `/time_series`는 `interval=1day`, `outputsize`를 지원하고, `/quote`는 최신 quote 조회용입니다. 무료 Basic 플랜은 제한된 API credits와 일일 제한이 있습니다.

## Yahoo Direct 제한

Yahoo는 공식 안정 API가 아니며 429/404가 발생할 수 있습니다. 이 프로젝트에서는 `yfinance` 라이브러리를 사용하지 않고 직접 `requests`로 호출합니다.

- Gold futures: `https://query1.finance.yahoo.com/v8/finance/chart/GC=F`
- Silver futures: `https://query1.finance.yahoo.com/v8/finance/chart/SI=F`

Yahoo direct는 spot이 아니라 futures fallback이므로 리포트에 `Asset kind: futures`로 표시됩니다.

## Telegram 방 설정

Bot API만으로 새 Telegram 방을 자동 생성할 수는 없습니다.

1. Telegram에서 새 그룹 또는 채널을 생성합니다.
2. BotFather로 만든 bot을 초대하고 메시지 전송 권한을 줍니다.
3. 해당 방의 chat id를 확인해 `.env`의 `GOLD_TELEGRAM_CHAT_ID`에 넣습니다.
4. BTC와 분리하려면 기존 BTC 방의 chat id가 아니라 새 방의 chat id를 사용합니다.

## 설치

```powershell
cd D:\1work
python -m venv gold-monitor\.venv
.\gold-monitor\.venv\Scripts\Activate.ps1
pip install -r gold-monitor\requirements.txt
```

## 설정

```powershell
Copy-Item gold-monitor\.env.example gold-monitor\.env
```

`.env` 예시:

```env
GOLD_TELEGRAM_BOT_TOKEN=123456:bot-token
GOLD_TELEGRAM_CHAT_ID=-1001234567890
GOLD_ALLOWED_CHAT_IDS=-1001234567890

GOLD_SPOT_SYMBOL=XAU/USD
SILVER_SPOT_SYMBOL=XAG/USD
GOLD_YAHOO_SYMBOL=GC=F
SILVER_YAHOO_SYMBOL=SI=F

GOLD_REPORT_HOURS=8,20
GOLD_POLL_INTERVAL_SECONDS=300
TWELVEDATA_API_KEY=
```

## 실행

한 번 실행하고 현재 시간이 08시 또는 20시이면 전송:

```powershell
cd D:\1work\gold-monitor
python -m gold_monitor.monitor --once
```

스케줄과 무관하게 테스트 리포트 전송:

```powershell
cd D:\1work\gold-monitor
python -m gold_monitor.monitor --once --force-report
```

polling loop 실행:

```powershell
cd D:\1work\gold-monitor
python -m gold_monitor.monitor
```

Telegram 명령 bot 실행:

```powershell
cd D:\1work\gold-monitor
python -m gold_monitor.bot
```

## 조건 알림 확장

`gold-monitor/gold_monitor/conditions.py`의 `load_conditions()`에서 조건을 추가합니다.

```python
def load_conditions() -> List[Condition]:
    return [DailyMoveCondition(threshold_pct=2.0)]
```
