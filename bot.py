import asyncio
import os
import json
import time
from pathlib import Path
from instagrapi import Client
from instagrapi.exceptions import (
    LoginRequired,
    PleaseWaitFewMinutes,
    ChallengeRequired,
    FeedbackRequired,
    ClientError,
)
from telegram import Bot

# =============================================================================
# CONFIGURATION
# =============================================================================

# Instagram credentials — set via environment variables or edit directly.
# Using a dedicated/fake account is recommended.
IG_USERNAME = os.environ.get("IG_USERNAME", "YOUR_FAKE_ACCOUNT_USERNAME")
IG_PASSWORD = os.environ.get("IG_PASSWORD", "YOUR_FAKE_ACCOUNT_PASSWORD")

# Telegram settings
TELEGRAM_TOKEN = os.environ.get(
    "TELEGRAM_TOKEN", "8502372148:AAGqwcMrkXMasZEhABLmHaE2HKLxOYeRjIY"
)
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "7075582251")

# Target Instagram user IDs to monitor
TARGET_IDS = [
    "9158581810",
    "8540571400",
    "56893406476",
    "52778386307",
    "45521544431",
    "8916182875",
    "15181547765",
    "2859988906",
    "67619369047",
]

# File paths
HISTORY_FILE = "gecmis_final.txt"
SESSION_FILE = "ig_session.json"

# Timing (seconds)
DELAY_BETWEEN_REQUESTS = 4  # delay between each API call to avoid rate limits
DELAY_BETWEEN_ACCOUNTS = 8  # delay between processing different accounts
CYCLE_INTERVAL = 43200  # 12 hours between full cycles
RATE_LIMIT_WAIT = 300  # 5 minutes wait on rate limit

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def load_history():
    """Load previously sent media IDs from disk."""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return set(line.strip() for line in f if line.strip())
    return set()


def save_to_history(media_id):
    """Append a media ID to the history file."""
    with open(HISTORY_FILE, "a") as f:
        f.write(f"{media_id}\n")


SENT_IDS = load_history()

# =============================================================================
# INSTAGRAM CLIENT — Session Management
# =============================================================================


def create_ig_client():
    """
    Create and authenticate an Instagram client with session persistence.
    Saves the session to disk so subsequent runs don't need a fresh login.
    """
    cl = Client()

    # Realistic device/user-agent settings to reduce detection risk
    cl.delay_range = [2, 5]

    # Try to restore an existing session first
    if os.path.exists(SESSION_FILE):
        try:
            cl.load_settings(SESSION_FILE)
            cl.login(IG_USERNAME, IG_PASSWORD)
            # Validate the session with a lightweight call
            cl.get_timeline_feed()
            print("✅ Mevcut oturum başarıyla yüklendi.")
            return cl
        except LoginRequired:
            print("⚠️ Oturum süresi dolmuş, yeniden giriş yapılıyor...")
        except ChallengeRequired:
            print("⚠️ Instagram doğrulama istiyor — yeni giriş deneniyor...")
        except Exception as e:
            print(f"⚠️ Oturum yüklenemedi ({e}), yeniden giriş yapılıyor...")

    # Fresh login
    try:
        cl.login(IG_USERNAME, IG_PASSWORD)
        cl.dump_settings(SESSION_FILE)
        print("✅ Yeni giriş başarılı, oturum kaydedildi.")
        return cl
    except ChallengeRequired:
        print(
            "❌ Instagram doğrulama istiyor! Lütfen hesaba tarayıcıdan giriş yapıp "
            "doğrulamayı tamamlayın, sonra botu tekrar çalıştırın."
        )
        return None
    except Exception as e:
        print(f"❌ Giriş başarısız: {e}")
        return None


def relogin(cl):
    """Attempt to re-authenticate when the session becomes invalid."""
    try:
        cl.login(IG_USERNAME, IG_PASSWORD)
        cl.dump_settings(SESSION_FILE)
        print("✅ Yeniden giriş başarılı.")
        return cl
    except Exception as e:
        print(f"❌ Yeniden giriş başarısız: {e}")
        return create_ig_client()


# =============================================================================
# MEDIA URL EXTRACTION
# =============================================================================


def get_best_media_url(media):
    """
    Extract the best quality video and/or image URL from an instagrapi
    media/story/resource object.
    Returns (video_url, image_url).
    """
    video_url = None
    image_url = None

    if hasattr(media, "video_url") and media.video_url:
        video_url = str(media.video_url)

    if hasattr(media, "thumbnail_url") and media.thumbnail_url:
        image_url = str(media.thumbnail_url)

    return video_url, image_url


# =============================================================================
# TELEGRAM BOT
# =============================================================================

try:
    bot = Bot(token=TELEGRAM_TOKEN)
except Exception as e:
    print(f"❌ Telegram Bot token hatası: {e}")
    exit(1)


async def process_and_send_post(post, user_label):
    """Process a single post and send it to Telegram."""
    post_id = str(post.pk)

    if post_id in SENT_IDS:
        return

    print(f"   ✨ Yeni Post: {user_label}")

    # Handle carousel / album posts
    if post.resources and len(post.resources) > 0:
        total_slides = len(post.resources)
        for i, resource in enumerate(post.resources, 1):
            vid, img = get_best_media_url(resource)
            caption = f"📮 Post (ID: {user_label}) - {i}/{total_slides}"
            try:
                if vid:
                    await bot.send_video(
                        chat_id=CHAT_ID, video=vid, caption=caption
                    )
                elif img:
                    await bot.send_photo(
                        chat_id=CHAT_ID, photo=img, caption=caption
                    )
                await asyncio.sleep(1)
            except Exception as e:
                print(f"   ❌ Gönderim hatası: {e}")
    else:
        vid, img = get_best_media_url(post)
        caption = f"📮 Post (ID: {user_label})"
        try:
            if vid:
                await bot.send_video(
                    chat_id=CHAT_ID, video=vid, caption=caption
                )
            elif img:
                await bot.send_photo(
                    chat_id=CHAT_ID, photo=img, caption=caption
                )
        except Exception as e:
            print(f"   ❌ Gönderim hatası: {e}")

    SENT_IDS.add(post_id)
    save_to_history(post_id)


async def send_story_media(story, user_label):
    """Send a single story item to Telegram."""
    story_id = str(story.pk)
    if story_id in SENT_IDS:
        return

    vid, img = get_best_media_url(story)
    caption = f"🔔 Story (ID: {user_label})"

    try:
        if vid:
            print(f"   📹 Story (Video)...")
            await bot.send_video(
                chat_id=CHAT_ID, video=vid, caption=caption
            )
        elif img:
            print(f"   📸 Story (Fotoğraf)...")
            await bot.send_photo(
                chat_id=CHAT_ID, photo=img, caption=caption
            )
        SENT_IDS.add(story_id)
        save_to_history(story_id)
        await asyncio.sleep(2)
    except Exception as e:
        print(f"   ❌ Gönderim hatası: {e}")


# =============================================================================
# MAIN LOOP
# =============================================================================


async def main():
    print("=" * 50)
    print("🚀 Bot Başlatıldı (ÜCRETSİZ MOD — API Key Gereksiz)")
    print("=" * 50)
    print(f"👤 Hedef hesap sayısı: {len(TARGET_IDS)}")
    print(f"⏱️  Döngü aralığı: {CYCLE_INTERVAL // 3600} saat")
    print("-" * 50)

    if IG_USERNAME == "YOUR_FAKE_ACCOUNT_USERNAME":
        print(
            "❌ HATA: Instagram kullanıcı adı ayarlanmamış!\n"
            "   Ortam değişkenlerini ayarlayın:\n"
            "   export IG_USERNAME='kullanici_adi'\n"
            "   export IG_PASSWORD='sifre'"
        )
        return

    cl = create_ig_client()
    if not cl:
        print("❌ Instagram girişi yapılamadı, bot durduruluyor.")
        return

    while True:
        for user_id in TARGET_IDS:
            user_label = str(user_id)
            int_user_id = int(user_id)

            # ── Stories ──────────────────────────────────────
            print(f"🔍 [{user_label}] Story kontrol ediliyor...")
            try:
                stories = cl.user_stories(int_user_id)
                for story in stories:
                    await send_story_media(story, user_label)
            except LoginRequired:
                print("⚠️ Oturum süresi doldu, yeniden giriş yapılıyor...")
                cl = relogin(cl)
                if not cl:
                    print("❌ Yeniden giriş başarısız, döngü atlanıyor.")
                    break
            except PleaseWaitFewMinutes:
                print(
                    f"⚠️ Hız sınırı! {RATE_LIMIT_WAIT // 60} dakika bekleniyor..."
                )
                await asyncio.sleep(RATE_LIMIT_WAIT)
            except FeedbackRequired as e:
                print(f"⚠️ Instagram uyarısı: {e}")
                await asyncio.sleep(RATE_LIMIT_WAIT)
            except ClientError as e:
                print(f"   ❌ Story hatası: {e}")
            except Exception as e:
                print(f"   ❌ Story hatası: {e}")

            await asyncio.sleep(DELAY_BETWEEN_REQUESTS)

            # ── Posts ────────────────────────────────────────
            print(f"🔍 [{user_label}] Post kontrol ediliyor...")
            try:
                posts = cl.user_medias(int_user_id, amount=2)
                for post in posts:
                    await process_and_send_post(post, user_label)
            except LoginRequired:
                print("⚠️ Oturum süresi doldu, yeniden giriş yapılıyor...")
                cl = relogin(cl)
                if not cl:
                    print("❌ Yeniden giriş başarısız, döngü atlanıyor.")
                    break
            except PleaseWaitFewMinutes:
                print(
                    f"⚠️ Hız sınırı! {RATE_LIMIT_WAIT // 60} dakika bekleniyor..."
                )
                await asyncio.sleep(RATE_LIMIT_WAIT)
            except FeedbackRequired as e:
                print(f"⚠️ Instagram uyarısı: {e}")
                await asyncio.sleep(RATE_LIMIT_WAIT)
            except ClientError as e:
                print(f"   ❌ Post hatası: {e}")
            except Exception as e:
                print(f"   ❌ Post hatası: {e}")

            await asyncio.sleep(DELAY_BETWEEN_ACCOUNTS)

        print(f"\n✅ Tur bitti. {CYCLE_INTERVAL // 3600} saat mola...")
        await asyncio.sleep(CYCLE_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())
