import asyncio
import os
from itertools import islice

import instaloader
from instaloader.exceptions import (
    BadCredentialsException,
    ConnectionException,
    LoginRequiredException,
    PrivateProfileNotFollowedException,
    ProfileNotExistsException,
    TwoFactorAuthRequiredException,
    TooManyRequestsException,
)
from telegram import Bot

# Telegram config (prefer environment variables)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8502372148:AAGqwcMrkXMasZEhABLmHaE2HKLxOYeRjIY")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "7075582251")

# Instagram login config
IG_USERNAME = os.getenv("IG_USERNAME")
IG_PASSWORD = os.getenv("IG_PASSWORD")
IG_SESSION_FILE = os.getenv("IG_SESSION_FILE", "ig_session")

DOWNLOAD_DIR = os.getenv("IG_DOWNLOAD_DIR", "downloads")

HISTORY_FILE = "gecmis_final.txt"

# Targets can be numeric IDs or usernames.
TARGETS = [
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


def get_int_env(name, default):
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        print(f"Invalid {name}='{raw}', using {default}.")
        return default


POST_LIMIT = get_int_env("IG_POST_LIMIT", 2)
CHECK_INTERVAL_SECONDS = get_int_env("CHECK_INTERVAL_SECONDS", 43200)
DOWNLOAD_TIMEOUT_SECONDS = get_int_env("IG_DOWNLOAD_TIMEOUT", 30)
RATE_LIMIT_SLEEP_SECONDS = get_int_env("IG_RATE_LIMIT_SLEEP", 900)


def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as handle:
            return set(line.strip() for line in handle if line.strip())
    return set()


def save_to_history(media_id):
    with open(HISTORY_FILE, "a") as handle:
        handle.write(f"{media_id}\n")


SENT_IDS = load_history()


try:
    bot = Bot(token=TELEGRAM_TOKEN)
except Exception as exc:
    print(f"Telegram bot token error: {exc}")
    raise SystemExit(1)


def init_instaloader():
    return instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        save_metadata=False,
        compress_json=False,
        max_connection_attempts=3,
        quiet=True,
    )


def ensure_login(loader):
    if not IG_USERNAME:
        print("Missing IG_USERNAME. Set it in the environment.")
        return False

    if os.path.exists(IG_SESSION_FILE):
        try:
            loader.load_session_from_file(IG_USERNAME, IG_SESSION_FILE)
            return True
        except Exception as exc:
            print(f"Session load failed, retrying login: {exc}")

    if not IG_PASSWORD:
        print("Missing IG_PASSWORD and no session file available.")
        return False

    try:
        loader.login(IG_USERNAME, IG_PASSWORD)
        loader.save_session_to_file(IG_SESSION_FILE)
        return True
    except TwoFactorAuthRequiredException:
        print("Two-factor auth required. Create a session file with instaloader.")
    except BadCredentialsException:
        print("Bad Instagram credentials.")
    except ConnectionException as exc:
        print(f"Instagram connection error: {exc}")
    return False


def resolve_profile(loader, target):
    try:
        target_str = str(target)
        if target_str.isdigit():
            return instaloader.Profile.from_id(loader.context, int(target_str))
        return instaloader.Profile.from_username(loader.context, target_str)
    except ProfileNotExistsException:
        print(f"Profile not found: {target}")
    except (ConnectionException, LoginRequiredException) as exc:
        print(f"Profile lookup failed for {target}: {exc}")
    return None


def guess_extension(url, is_video):
    default = ".mp4" if is_video else ".jpg"
    if not url:
        return default
    path = url.split("?", 1)[0]
    _, ext = os.path.splitext(path)
    ext = ext.lower()
    if ext in {".jpg", ".jpeg", ".png", ".mp4"}:
        return ext
    return default


def download_media(loader, url, file_prefix, is_video):
    if not url:
        print("Missing media URL; skipping.")
        return None

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    extension = guess_extension(url, is_video)
    file_path = os.path.join(DOWNLOAD_DIR, f"{file_prefix}{extension}")

    try:
        response = loader.context.session.get(
            url, stream=True, timeout=DOWNLOAD_TIMEOUT_SECONDS
        )
        response.raise_for_status()
        with open(file_path, "wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)
        return file_path
    except Exception as exc:
        print(f"Download failed: {exc}")
        return None


async def send_media_file(file_path, caption, is_video):
    if not file_path:
        return

    try:
        with open(file_path, "rb") as handle:
            if is_video:
                await bot.send_video(chat_id=CHAT_ID, video=handle, caption=caption)
            else:
                await bot.send_photo(chat_id=CHAT_ID, photo=handle, caption=caption)
    except Exception as exc:
        print(f"Telegram send failed: {exc}")
    finally:
        try:
            os.remove(file_path)
        except FileNotFoundError:
            pass


async def process_and_send_post(loader, post, user_label):
    post_id = str(post.mediaid)
    if post_id in SENT_IDS:
        return

    if post.typename == "GraphSidecar":
        nodes = list(post.get_sidecar_nodes())
        total_slides = len(nodes)
        for index, node in enumerate(nodes, 1):
            is_video = node.is_video
            url = node.video_url if is_video else node.display_url
            file_path = download_media(loader, url, f"{post_id}_{index}", is_video)
            caption = f"Post ({user_label}) - {index}/{total_slides}"
            await send_media_file(file_path, caption, is_video)
            await asyncio.sleep(1)
    else:
        is_video = post.is_video
        url = post.video_url if is_video else post.url
        file_path = download_media(loader, url, post_id, is_video)
        caption = f"Post ({user_label})"
        await send_media_file(file_path, caption, is_video)

    SENT_IDS.add(post_id)
    save_to_history(post_id)


async def send_story_media(loader, media_item, caption):
    media_id = str(getattr(media_item, "mediaid", None) or getattr(media_item, "id", ""))
    if not media_id:
        return
    if media_id in SENT_IDS:
        return

    is_video = media_item.is_video
    url = media_item.video_url if is_video else media_item.url
    file_path = download_media(loader, url, media_id, is_video)
    if not file_path:
        return

    await send_media_file(file_path, caption, is_video)
    SENT_IDS.add(media_id)
    save_to_history(media_id)
    await asyncio.sleep(2)


async def main():
    print("Bot started (instaloader mode).")
    print(f"Targets configured: {len(TARGETS)}")

    loader = init_instaloader()
    if not ensure_login(loader):
        return

    profiles = []
    for target in TARGETS:
        profile = resolve_profile(loader, target)
        if profile:
            profiles.append(profile)

    if not profiles:
        print("No valid targets found. Check TARGETS.")
        return

    while True:
        for profile in profiles:
            user_label = f"{profile.username} ({profile.userid})"

            print(f"Checking stories for {user_label}...")
            try:
                for story in loader.get_stories(userids=[profile.userid]):
                    for item in story.get_items():
                        await send_story_media(loader, item, f"Story ({user_label})")
            except PrivateProfileNotFollowedException:
                print(f"Stories unavailable (not following): {user_label}")
            except TooManyRequestsException:
                print("Rate limited by Instagram. Sleeping longer.")
                await asyncio.sleep(RATE_LIMIT_SLEEP_SECONDS)
            except Exception as exc:
                print(f"Story error for {user_label}: {exc}")

            await asyncio.sleep(1)

            print(f"Checking posts for {user_label}...")
            try:
                for post in islice(profile.get_posts(), POST_LIMIT):
                    await process_and_send_post(loader, post, user_label)
            except PrivateProfileNotFollowedException:
                print(f"Posts unavailable (not following): {user_label}")
            except TooManyRequestsException:
                print("Rate limited by Instagram. Sleeping longer.")
                await asyncio.sleep(RATE_LIMIT_SLEEP_SECONDS)
            except Exception as exc:
                print(f"Post error for {user_label}: {exc}")

            await asyncio.sleep(2)

        print(f"Cycle complete. Sleeping {CHECK_INTERVAL_SECONDS} seconds.")
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    asyncio.run(main())
