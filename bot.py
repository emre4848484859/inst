import asyncio
import os
import json
from datetime import datetime
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ChallengeRequired, PleaseWaitFewMinutes
from telegram import Bot
import time

# --- 🔐 INSTAGRAM CREDENTIALS ---
# Create a fake/throwaway Instagram account for this
INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME", "YOUR_INSTAGRAM_USERNAME")
INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD", "YOUR_INSTAGRAM_PASSWORD")

# --- 📱 TELEGRAM SETTINGS ---
TELEGRAM_TOKEN = "8502372148:AAGqwcMrkXMasZEhABLmHaE2HKLxOYeRjIY"
CHAT_ID = "7075582251"

# --- 🎯 TARGET ACCOUNTS ---
# You can use either usernames or user IDs
TARGET_USERNAMES = [
    # Add Instagram usernames here, e.g., "username1", "username2"
]

TARGET_IDS = [
    "9158581810", "8540571400", "56893406476", "52778386307", 
    "45521544431", "8916182875", "15181547765", "2859988906", "67619369047"
]

# --- 💾 FILES ---
HISTORY_FILE = "gecmis_final.txt"
SESSION_FILE = "instagram_session.json"

# --- 🔧 HELPER FUNCTIONS ---

def load_history():
    """Load previously sent media IDs"""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return set(line.strip() for line in f)
    return set()

def save_to_history(media_id):
    """Save media ID to history"""
    with open(HISTORY_FILE, "a") as f:
        f.write(f"{media_id}\n")

def load_session(cl):
    """Load Instagram session from file"""
    if os.path.exists(SESSION_FILE):
        try:
            cl.load_settings(SESSION_FILE)
            print("✅ Session loaded from file")
            return True
        except Exception as e:
            print(f"⚠️ Could not load session: {e}")
    return False

def save_session(cl):
    """Save Instagram session to file"""
    try:
        cl.dump_settings(SESSION_FILE)
        print("✅ Session saved")
    except Exception as e:
        print(f"⚠️ Could not save session: {e}")

def instagram_login():
    """Login to Instagram with session management"""
    cl = Client()
    cl.delay_range = [2, 5]  # Random delay between requests
    
    # Try to load existing session
    if load_session(cl):
        try:
            cl.get_timeline_feed()  # Test if session is valid
            print("✅ Logged in using saved session")
            return cl
        except LoginRequired:
            print("⚠️ Session expired, logging in again...")
    
    # Login with credentials
    try:
        print("🔐 Logging in to Instagram...")
        cl.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
        save_session(cl)
        print("✅ Successfully logged in!")
        return cl
    except ChallengeRequired as e:
        print("❌ Challenge required! Instagram wants verification.")
        print("   Solution: Log in to your account manually from a browser/app first.")
        raise e
    except PleaseWaitFewMinutes:
        print("❌ Rate limited! Please wait a few minutes.")
        raise
    except Exception as e:
        print(f"❌ Login failed: {e}")
        raise e

SENT_IDS = load_history()

try:
    bot = Bot(token=TELEGRAM_TOKEN)
except Exception as e:
    print(f"❌ Telegram bot token error: {e}")
    exit()

# --- 📸 INSTAGRAM API FUNCTIONS ---

def get_user_stories(cl, user_id):
    """Fetch user stories using instagrapi"""
    try:
        stories = cl.user_stories(int(user_id))
        return stories if stories else []
    except Exception as e:
        print(f"   ⚠️ Error fetching stories: {e}")
        return []

def get_user_posts(cl, user_id, amount=2):
    """Fetch recent user posts using instagrapi"""
    try:
        medias = cl.user_medias(int(user_id), amount=amount)
        return medias if medias else []
    except Exception as e:
        print(f"   ⚠️ Error fetching posts: {e}")
        return []

def download_media(cl, media_obj):
    """Download media and return file path"""
    try:
        if media_obj.media_type == 1:  # Photo
            path = cl.photo_download(media_obj.pk, folder="temp")
            return path, "photo"
        elif media_obj.media_type == 2 and media_obj.product_type == "feed":  # Video
            path = cl.video_download(media_obj.pk, folder="temp")
            return path, "video"
        elif media_obj.media_type == 2 and media_obj.product_type == "story":  # Story video
            path = cl.video_download(media_obj.pk, folder="temp")
            return path, "video"
        elif media_obj.media_type == 8:  # Carousel/Album
            return None, "carousel"
        else:
            return None, "unknown"
    except Exception as e:
        print(f"   ⚠️ Error downloading media: {e}")
        return None, None

async def process_and_send_post(cl, media_obj, user_label):
    """Process and send Instagram post to Telegram"""
    post_id = str(media_obj.pk)
    
    if post_id in SENT_IDS:
        return

    print(f"   ✨ New Post: {user_label}")

    try:
        # Handle carousel/album posts
        if media_obj.media_type == 8:
            resources = media_obj.resources
            total = len(resources)
            
            for i, resource in enumerate(resources, 1):
                caption = f"📮 Post (ID: {user_label}) - {i}/{total}"
                try:
                    if resource.media_type == 1:  # Photo
                        path = cl.photo_download(resource.pk, folder="temp")
                        with open(path, 'rb') as photo:
                            await bot.send_photo(chat_id=CHAT_ID, photo=photo, caption=caption)
                        os.remove(path)
                    elif resource.media_type == 2:  # Video
                        path = cl.video_download(resource.pk, folder="temp")
                        with open(path, 'rb') as video:
                            await bot.send_video(chat_id=CHAT_ID, video=video, caption=caption)
                        os.remove(path)
                    await asyncio.sleep(1)
                except Exception as e:
                    print(f"   ⚠️ Error sending carousel item: {e}")
        else:
            # Single photo or video
            caption = f"📮 Post (ID: {user_label})\n{media_obj.caption_text[:100] if media_obj.caption_text else ''}"
            path, media_type = download_media(cl, media_obj)
            
            if path and media_type == "photo":
                with open(path, 'rb') as photo:
                    await bot.send_photo(chat_id=CHAT_ID, photo=photo, caption=caption)
                os.remove(path)
            elif path and media_type == "video":
                with open(path, 'rb') as video:
                    await bot.send_video(chat_id=CHAT_ID, video=video, caption=caption)
                os.remove(path)

        SENT_IDS.add(post_id)
        save_to_history(post_id)
    except Exception as e:
        print(f"   ❌ Error processing post: {e}")

async def send_story_media(cl, story_obj, user_label):
    """Send Instagram story to Telegram"""
    media_id = str(story_obj.pk)
    
    if media_id in SENT_IDS:
        return

    try:
        caption = f"🔔 Story (ID: {user_label})"
        path, media_type = download_media(cl, story_obj)
        
        if path and media_type == "photo":
            print(f"   📸 Story (Photo)...")
            with open(path, 'rb') as photo:
                await bot.send_photo(chat_id=CHAT_ID, photo=photo, caption=caption)
            os.remove(path)
        elif path and media_type == "video":
            print(f"   📹 Story (Video)...")
            with open(path, 'rb') as video:
                await bot.send_video(chat_id=CHAT_ID, video=video, caption=caption)
            os.remove(path)
        
        SENT_IDS.add(media_id)
        save_to_history(media_id)
        await asyncio.sleep(2)
    except Exception as e:
        print(f"   ❌ Error sending story: {e}")

async def main():
    """Main bot loop"""
    print("🚀 Bot Started (FREE - No API Cost!)...")
    print(f"👤 Target Account Count: {len(TARGET_IDS)}")
    print("-" * 50)
    
    # Check credentials
    if INSTAGRAM_USERNAME == "YOUR_INSTAGRAM_USERNAME":
        print("❌ ERROR: Please set your Instagram credentials!")
        print("   Set environment variables or edit the file:")
        print("   INSTAGRAM_USERNAME=your_username")
        print("   INSTAGRAM_PASSWORD=your_password")
        return
    
    # Create temp directory for downloads
    os.makedirs("temp", exist_ok=True)
    
    # Login to Instagram
    try:
        cl = instagram_login()
    except Exception as e:
        print(f"❌ Cannot continue without Instagram login: {e}")
        return
    
    loop_count = 0
    
    while True:
        loop_count += 1
        print(f"\n{'='*50}")
        print(f"🔄 Loop #{loop_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*50}")
        
        for user_id in TARGET_IDS:
            user_label = str(user_id)
            
            try:
                # Fetch and send stories
                print(f"\n🔍 Checking {user_label} stories...")
                stories = get_user_stories(cl, user_id)
                
                if stories:
                    print(f"   Found {len(stories)} story/stories")
                    for story in stories:
                        await send_story_media(cl, story, user_label)
                else:
                    print(f"   No stories found")
                
                await asyncio.sleep(2)
                
                # Fetch and send posts
                print(f"🔍 Checking {user_label} posts...")
                posts = get_user_posts(cl, user_id, amount=2)
                
                if posts:
                    print(f"   Found {len(posts)} post(s)")
                    for post in posts:
                        await process_and_send_post(cl, post, user_label)
                else:
                    print(f"   No posts found")
                
                await asyncio.sleep(3)
                
            except PleaseWaitFewMinutes:
                print(f"⚠️ Rate limited! Waiting 5 minutes...")
                await asyncio.sleep(300)
            except Exception as e:
                print(f"⚠️ Error processing user {user_label}: {e}")
                continue
        
        # Wait 12 hours before next check
        print(f"\n✅ Loop completed! Waiting 12 hours until next check...")
        print(f"   Next check at: {datetime.fromtimestamp(time.time() + 43200).strftime('%Y-%m-%d %H:%M:%S')}")
        await asyncio.sleep(43200)  # 12 hours

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
  
