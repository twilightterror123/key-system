# 🔐 Key System

Discord-managed license/key system with:

- `1d` keys (24 hours after activation)
- lifetime keys
- one-time activation
- installation/device binding
- key revocation
- server-side hashed keys
- SQLite persistence
- FastAPI API + Discord bot

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set the values in `.env`, then run:

```bash
uvicorn server.main:app --host 0.0.0.0 --port 8000
python -m bot.bot
```

Never commit your `.env` or Discord token.
