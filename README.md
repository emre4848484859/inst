# Instagram Story & Post Downloader Bot

A Telegram bot that monitors Instagram accounts and automatically forwards new **stories** and **posts** to a Telegram chat — **without any paid API**.

## How It Works

Instead of relying on the RapidAPI "Star API" (which has a 100 queries/month limit), this bot uses **[instagrapi](https://github.com/subzeroid/instagrapi)** to communicate with Instagram's private mobile API directly. This means:

- **No API key or paid subscription required**
- **No query limits** (just respect Instagram's natural rate limits)
- You only need a dedicated Instagram account to authenticate

## Will the Queried Accounts See My Fake Account?

| Action | Visible to Account Owner? | Explanation |
|--------|--------------------------|-------------|
| **Fetching Posts** | **No** | Instagram does not track or show who views regular posts. |
| **Fetching Stories** | **No*** | `instagrapi` fetches story data without calling the `media/seen/` endpoint, so your account should **not** appear in the story viewers list. |

\* **Important caveat**: Instagram's server-side behavior can change. While the bot does not explicitly mark stories as "seen", there is a small theoretical risk that Instagram could track fetches in the future. For maximum safety:
- Use a completely separate fake account (not your personal account)
- Don't follow the target accounts from the fake account (public accounts don't require following)
- Keep query frequency low (the 12-hour cycle is very safe)

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure credentials

Set your Instagram credentials as environment variables:

```bash
export IG_USERNAME="your_fake_instagram_username"
export IG_PASSWORD="your_fake_instagram_password"
```

Optionally, you can also override the Telegram settings:

```bash
export TELEGRAM_TOKEN="your_telegram_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"
```

Or edit the default values directly in `bot.py`.

### 3. Run the bot

```bash
python bot.py
```

## Configuration

All configuration is at the top of `bot.py`:

| Variable | Description | Default |
|----------|-------------|---------|
| `IG_USERNAME` | Instagram account username | env var `IG_USERNAME` |
| `IG_PASSWORD` | Instagram account password | env var `IG_PASSWORD` |
| `TELEGRAM_TOKEN` | Telegram Bot API token | hardcoded |
| `TELEGRAM_CHAT_ID` | Telegram chat to send media to | hardcoded |
| `TARGET_IDS` | List of Instagram user IDs to monitor | 9 accounts |
| `DELAY_BETWEEN_REQUESTS` | Seconds between API calls | 4 |
| `DELAY_BETWEEN_ACCOUNTS` | Seconds between accounts | 8 |
| `CYCLE_INTERVAL` | Seconds between full cycles | 43200 (12h) |

## Session Persistence

The bot saves the Instagram session to `ig_session.json` after the first successful login. On subsequent runs it restores the session automatically, avoiding repeated logins (which reduces the chance of Instagram flagging the account).

## Tips for Avoiding Detection

1. **Use a real-looking fake account** — add a profile picture, bio, and a few posts.
2. **Don't follow too many accounts** — the bot doesn't need to follow public accounts.
3. **Keep delays reasonable** — the default delays (4s between requests, 8s between accounts) are conservative and safe.
4. **12-hour cycle is very low traffic** — 18 requests every 12 hours is well within safe limits.
5. **If Instagram challenges the account** — log in via a browser, complete the verification, then restart the bot.

## Files

| File | Purpose |
|------|---------|
| `bot.py` | Main bot script |
| `requirements.txt` | Python dependencies |
| `gecmis_final.txt` | History of sent media IDs (auto-created) |
| `ig_session.json` | Saved Instagram session (auto-created) |
