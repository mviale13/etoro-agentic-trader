# eToro Agentic Trader v2

Python 3.12 starter with paper trading, crypto support, deterministic risk controls,
manual approval, audit logging, a kill switch, and guarded eToro Demo/Real connectors.

## Install on macOS

Keep the project outside iCloud Drive:

```bash
mkdir -p ~/Projects
cd ~/Projects
unzip ~/Downloads/etoro-agentic-trader-v2.zip
cd etoro-agentic-trader-v2
cp .env.example .env
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m pytest
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs`.

Real execution requires all three settings:

```env
TRADING_MODE=real
LIVE_TRADING_ENABLED=true
LIVE_CONFIRMATION=I_ACCEPT_REAL_MONEY_RISK
```

The AI layer may propose trades, but only the deterministic risk engine can authorize them.
Validate eToro order payloads in the official API playground before enabling Demo or Real mode.
