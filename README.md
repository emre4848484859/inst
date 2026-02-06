# Instagram Story & Post Downloader Bot (FREE VERSION) 🤖📱

A Telegram bot that monitors Instagram accounts and automatically downloads and sends new stories and posts to your Telegram chat. **Now using FREE Instagram API - no paid services required!**

## 🆓 What Changed?

**Before:** Used RapidAPI Star API (limited to 100 queries/month, expensive)  
**Now:** Uses `instagrapi` - a free Python library that directly interfaces with Instagram's private API

### ⚠️ Privacy Considerations

When using a logged-in Instagram account to fetch content:

- **Stories**: The account owner **WILL see** your account in their story viewers list
- **Posts**: Viewing posts won't notify them, but programmatic access may be logged
- **Recommendation**: Use a separate "burner" Instagram account with minimal activity

## 🚀 Features

- ✅ **Monitors 9+ Instagram accounts** for new content
- ✅ **Downloads stories** automatically (before they expire)
- ✅ **Downloads posts** (photos, videos, carousels)
- ✅ **Sends to Telegram** instantly
- ✅ **Session persistence** (no repeated logins)
- ✅ **Duplicate prevention** (tracks sent media)
- ✅ **Rate limit handling** (auto-retry on limits)
- ✅ **100% FREE** - no API costs!

## 📋 Requirements

- Python 3.7+
- Instagram account (create a fake/throwaway account)
- Telegram bot token

## 🛠️ Installation

### 1. Clone the repository

```bash
git clone <your-repo>
cd <your-repo>
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create an Instagram account

Create a new Instagram account specifically for this bot:
- Use a temporary email (like Gmail with +tag)
- Make it a private account
- Don't follow anyone or post anything
- Complete the profile minimally (add a photo to look more legitimate)

### 4. Configure the bot

Edit `bot.py` and set your credentials:

```python
INSTAGRAM_USERNAME = "your_throwaway_account"
INSTAGRAM_PASSWORD = "your_password"
```

Or use environment variables:

```bash
export INSTAGRAM_USERNAME="your_throwaway_account"
export INSTAGRAM_PASSWORD="your_password"
```

### 5. Add target accounts

In `bot.py`, update the `TARGET_IDS` list with Instagram user IDs:

```python
TARGET_IDS = [
    "9158581810",
    "8540571400",
    # ... add more IDs
]
```

**How to find Instagram User IDs:**
- Use online tools like `instafollowers.co/find-instagram-user-id`
- Or use Python: `python -c "from instagrapi import Client; cl = Client(); cl.login('user', 'pass'); print(cl.user_id_from_username('target_username'))"`

## 🏃 Running the Bot

### Run directly

```bash
python bot.py
```

### Run in background (Linux/Mac)

```bash
nohup python bot.py > bot.log 2>&1 &
```

### Run with systemd (Linux)

Create `/etc/systemd/system/instagram-bot.service`:

```ini
[Unit]
Description=Instagram Story Downloader Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/bot
Environment="INSTAGRAM_USERNAME=your_username"
Environment="INSTAGRAM_PASSWORD=your_password"
ExecStart=/usr/bin/python3 /path/to/bot/bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable instagram-bot
sudo systemctl start instagram-bot
```

## 📁 Files Generated

- `gecmis_final.txt` - History of sent media IDs (prevents duplicates)
- `instagram_session.json` - Saved Instagram session (avoid re-login)
- `temp/` - Temporary folder for downloaded media (auto-cleaned)

## ⚙️ Configuration

### Check Interval

Default: 12 hours (43200 seconds)

To change, edit this line in `bot.py`:
```python
await asyncio.sleep(43200)  # Change to your desired seconds
```

### Number of posts to check

Default: 2 most recent posts

To change:
```python
posts = get_user_posts(cl, user_id, amount=5)  # Check 5 posts instead
```

## 🔒 Security Best Practices

1. **Never share your credentials** in code commits
2. **Use environment variables** for sensitive data
3. **Use a throwaway Instagram account**, not your personal account
4. **Don't use 2FA** on the bot account (or handle it programmatically)
5. **Keep session file secure** (`instagram_session.json`)

## ⚠️ Instagram Limitations

Instagram has rate limits to prevent abuse:

- **~200 requests per hour** per account
- **Aggressive scraping** may trigger temporary blocks
- **Use delays** between requests (built-in: 2-5 seconds)
- If you get challenges, log in manually from a browser first

## 🐛 Troubleshooting

### "Challenge Required" Error

Instagram wants to verify your account:
1. Log in to the bot account from a browser/app
2. Complete any verification challenges
3. Try running the bot again

### "Please Wait Few Minutes" Error

You've hit rate limits:
- The bot will automatically wait 5 minutes
- Reduce check frequency or number of accounts
- Spread out requests more

### Session Expired

Delete `instagram_session.json` and restart the bot to re-login.

### Media Download Fails

Some media types may not be supported. Check the error message and update the `download_media()` function if needed.

## 📊 Monitoring

Watch logs in real-time:
```bash
tail -f bot.log
```

Check if bot is running:
```bash
ps aux | grep bot.py
```

## 🆚 Comparison: Old vs New

| Feature | Old (RapidAPI) | New (Instagrapi) |
|---------|---------------|------------------|
| **Cost** | $10-50/month | FREE |
| **Query Limit** | 100-500/month | ~200/hour |
| **Privacy** | Anonymous | Visible to stories |
| **Reliability** | High | Medium (may need occasional re-login) |
| **Setup** | Easy (just API key) | Medium (need Instagram account) |

## 📝 License

MIT License - Use at your own risk. This bot uses Instagram's private API, which may violate their Terms of Service. Use responsibly.

## ⚖️ Disclaimer

This bot is for educational purposes. Automated access to Instagram may violate their Terms of Service. Use at your own risk. The developers are not responsible for any account bans or legal issues.

## 🤝 Contributing

Feel free to open issues or submit pull requests!

## 💡 Tips

- Start with a small number of accounts (2-3) to test
- Monitor for the first few hours to ensure it works
- Keep your bot account active (log in manually sometimes)
- If banned, wait 24 hours and try with a new account
- Use a VPS/cloud server for 24/7 operation

---

**Made with ❤️ by the community**
