# Instagram downloader bot (no paid API)

This bot logs in to Instagram with Instaloader and forwards new stories and
posts to a Telegram chat.

## Setup
1. Install dependencies:
   pip install -r requirements.txt

2. Configure environment variables:
   export TELEGRAM_TOKEN="your-telegram-bot-token"
   export TELEGRAM_CHAT_ID="your-telegram-chat-id"
   export IG_USERNAME="your-instagram-username"
   export IG_PASSWORD="your-instagram-password"

   Optional:
   export IG_SESSION_FILE="ig_session"
   export IG_DOWNLOAD_DIR="downloads"
   export IG_POST_LIMIT="2"
   export CHECK_INTERVAL_SECONDS="43200"
   export IG_DOWNLOAD_TIMEOUT="30"
   export IG_RATE_LIMIT_SLEEP="900"

3. Update TARGETS in bot.py to IDs or usernames.

4. Run:
   python bot.py

## Notes
- Stories require that the logged-in account can view them. For private
  accounts you must be approved.
- If you have 2FA enabled, create a session file once with:
  instaloader -l your_instagram_username
  Then set IG_SESSION_FILE to the saved session file.