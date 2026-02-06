# Quick Setup Guide 🚀

## What Changed?

Your Instagram bot has been completely rewritten to **eliminate all API costs**!

### Before
- Used RapidAPI's Star API
- Limited to 100 queries/month
- Cost: $10-50/month
- Anonymous access

### After
- Uses `instagrapi` (free Python library)
- Unlimited queries (with rate limits)
- Cost: $0 (FREE!)
- Requires Instagram login (visible in story views)

---

## 🔴 IMPORTANT: Privacy Warning

**When you use a logged-in Instagram account:**
- ✅ **Posts**: The owner won't be notified when you fetch their posts
- ❌ **Stories**: Your account **WILL appear** in their story viewers list

**Recommendation**: Create a new "burner" Instagram account specifically for this bot.

---

## 📝 Setup Steps

### 1. Create a Throwaway Instagram Account

1. Go to Instagram.com or use the app
2. Create a new account with:
   - Fake name (e.g., "Tech Updates Bot")
   - New email (use Gmail with +tag: `youremail+instabot@gmail.com`)
   - Random password (save it!)
3. Complete the profile:
   - Add a profile picture (generic image)
   - Make it a private account
   - Don't follow anyone initially
4. **Don't enable 2FA** (two-factor authentication)

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

Or if you don't have pip:
```bash
pip3 install instagrapi python-telegram-bot
```

### 3. Configure Your Bot

Edit `bot.py` and update these lines:

```python
# Method 1: Direct in file (line 12-13)
INSTAGRAM_USERNAME = "your_throwaway_account"
INSTAGRAM_PASSWORD = "your_password"
```

Or use environment variables (more secure):

```bash
export INSTAGRAM_USERNAME="your_throwaway_account"
export INSTAGRAM_PASSWORD="your_password"
```

### 4. Verify Target Accounts

Your current target accounts (already configured):
```python
TARGET_IDS = [
    "9158581810", "8540571400", "56893406476", "52778386307", 
    "45521544431", "8916182875", "15181547765", "2859988906", "67619369047"
]
```

If you want to add more accounts, find their User ID:
- Use: https://instafollowers.co/find-instagram-user-id
- Or run: `python3 -c "from instagrapi import Client; cl = Client(); cl.login('user', 'pass'); print(cl.user_id_from_username('target_username'))"`

### 5. Run the Bot

```bash
python3 bot.py
```

**First run will:**
1. Login to Instagram with your credentials
2. Save session to `instagram_session.json`
3. Start monitoring all 9 accounts
4. Send new stories/posts to your Telegram

---

## 🎯 Expected Behavior

### First Run
```
🚀 Bot Started (FREE - No API Cost!)...
👤 Target Account Count: 9
--------------------------------------------------
🔐 Logging in to Instagram...
✅ Successfully logged in!
✅ Session saved

==================================================
🔄 Loop #1 - 2026-02-06 08:30:00
==================================================

🔍 Checking 9158581810 stories...
   Found 2 story/stories
   📸 Story (Photo)...
   📹 Story (Video)...
   
🔍 Checking 9158581810 posts...
   Found 2 post(s)
   ✨ New Post: 9158581810
...

✅ Loop completed! Waiting 12 hours until next check...
   Next check at: 2026-02-06 20:30:00
```

### Subsequent Runs
```
✅ Session loaded from file
✅ Logged in using saved session
```
(No need to login again!)

---

## ⚠️ Common Issues & Solutions

### Issue: "Challenge Required"
**Problem**: Instagram wants to verify your account

**Solution**:
1. Log in to the bot account from a browser or Instagram app
2. Complete any verification (email/SMS code)
3. Try running the bot again
4. If it persists, wait 24 hours and use a different IP/device

### Issue: "Please Wait Few Minutes"
**Problem**: You hit rate limits (too many requests)

**Solution**:
- The bot automatically waits 5 minutes
- Reduce the number of monitored accounts
- Increase the check interval (default: 12 hours)

### Issue: "Session Expired"
**Problem**: Saved session is no longer valid

**Solution**:
```bash
rm instagram_session.json
python3 bot.py  # Will re-login
```

### Issue: Account Gets Banned
**Problem**: Instagram detected bot activity

**Solution**:
1. Wait 24-48 hours
2. Create a new throwaway account
3. Use a VPN or different IP
4. Reduce monitoring frequency

---

## 🔒 Security Tips

1. ✅ **Never commit credentials** to git
2. ✅ **Use environment variables** for sensitive data
3. ✅ **Don't use your personal Instagram account**
4. ✅ **Keep `instagram_session.json` secure** (it's in .gitignore)
5. ✅ **Log in manually** to the bot account occasionally to keep it active

---

## 📊 Cost Comparison

| Time Period | Old Cost (RapidAPI) | New Cost (Instagrapi) |
|-------------|---------------------|------------------------|
| 1 month     | $10-50              | $0                     |
| 6 months    | $60-300             | $0                     |
| 1 year      | $120-600            | $0                     |

**Savings**: $120-600 per year! 💰

---

## 🎛️ Advanced Configuration

### Change Check Interval

Default: 12 hours (43200 seconds)

To check every 6 hours:
```python
await asyncio.sleep(21600)  # Line 238 in bot.py
```

To check every 24 hours:
```python
await asyncio.sleep(86400)
```

### Check More Posts

Default: 2 most recent posts

To check 5 posts:
```python
posts = get_user_posts(cl, user_id, amount=5)  # Line 223
```

### Run in Background (24/7)

**Linux/Mac:**
```bash
nohup python3 bot.py > bot.log 2>&1 &
```

**Check if running:**
```bash
ps aux | grep bot.py
```

**Stop bot:**
```bash
pkill -f bot.py
```

**View logs:**
```bash
tail -f bot.log
```

---

## 🆘 Need Help?

1. **Check logs**: Look for error messages in the terminal output
2. **Read README.md**: Full documentation with troubleshooting
3. **Common fixes**:
   - Delete `instagram_session.json` and restart
   - Use a fresh Instagram account
   - Wait 24 hours if rate limited
   - Try a different IP/VPN

---

## ✅ Verification Checklist

Before running, make sure:

- [ ] Created a throwaway Instagram account
- [ ] Installed dependencies (`pip install -r requirements.txt`)
- [ ] Set `INSTAGRAM_USERNAME` and `INSTAGRAM_PASSWORD`
- [ ] Telegram bot token is correct
- [ ] Target account IDs are correct
- [ ] Internet connection is stable

---

## 🎉 You're All Set!

Run the bot and enjoy unlimited free Instagram monitoring!

```bash
python3 bot.py
```

**Questions about privacy?**
- Yes, your account will appear in story views
- No, post owners won't be notified of post views
- Use a throwaway account to maintain privacy

**Enjoy your FREE bot! 🚀**
