# Instagram Story + New Post Downloader (Telegram Bot)

This repo runs a simple polling bot that:
- Logs into Instagram with **your own account session**
- Checks a list of target Instagram **user IDs**
- Sends **new stories** and **new posts** to a Telegram chat
- Keeps a local history file so it won’t resend the same media

## Notes (important)

- This is **not** an official Instagram API. It uses `instagrapi` (reverse-engineered endpoints). It can break if Instagram changes things, and Instagram may trigger **challenge / 2FA / rate limits**.
- Make sure your use complies with Instagram’s Terms and applicable laws, and only monitor accounts you have permission to monitor.

## Setup

Create a virtual environment and install deps:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Set required environment variables:

```bash
export TELEGRAM_TOKEN="...your telegram bot token..."
export TELEGRAM_CHAT_ID="...target chat id..."
export IG_USERNAME="...instagram username..."
export IG_PASSWORD="...instagram password..."
```

Optional configuration:

```bash
# Comma-separated numeric Instagram IDs
export TARGET_IDS="9158581810,8540571400"

# Session/settings cache file (reduces repeated logins)
export IG_SESSION_FILE="ig_session.json"

# History file to avoid resending the same media
export HISTORY_FILE="gecmis_final.txt"

# Polling
export POLL_INTERVAL_SECONDS="900"        # default 15 minutes
export PER_ACCOUNT_DELAY_SECONDS="2"      # default 2 seconds
export JITTER_SECONDS="1"                 # default 1 second
```

Run:

```bash
python3 bot.py
```

## Troubleshooting

- **Challenge / suspicious login**: log into the account in the Instagram app, complete the challenge, then rerun.
- **2FA**: you may need to complete 2FA in-app (or extend the script to accept a code).
- **Rate limits**: increase `POLL_INTERVAL_SECONDS` and delays.