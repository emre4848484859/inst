import asyncio
import os
import random
import time
from dataclasses import dataclass

from instagrapi import Client
from instagrapi.exceptions import ChallengeRequired, LoginRequired, TwoFactorRequired
from telegram import Bot


DEFAULT_TARGET_IDS = [
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


@dataclass(frozen=True)
class Config:
    telegram_token: str
    telegram_chat_id: str
    ig_username: str
    ig_password: str
    ig_session_file: str
    history_file: str
    poll_interval_seconds: int
    per_account_delay_seconds: float
    jitter_seconds: float
    target_ids: list[str]


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def load_config() -> Config:
    """
    Required env vars:
    - TELEGRAM_TOKEN
    - TELEGRAM_CHAT_ID
    - IG_USERNAME
    - IG_PASSWORD
    Optional:
    - IG_SESSION_FILE (default: ig_session.json)
    - HISTORY_FILE (default: gecmis_final.txt)
    - TARGET_IDS (comma-separated numeric IDs)
    - POLL_INTERVAL_SECONDS (default: 900)
    - PER_ACCOUNT_DELAY_SECONDS (default: 2)
    - JITTER_SECONDS (default: 1)
    """
    telegram_token = _env("TELEGRAM_TOKEN")
    telegram_chat_id = _env("TELEGRAM_CHAT_ID")
    ig_username = _env("IG_USERNAME")
    ig_password = _env("IG_PASSWORD")

    missing = []
    if not telegram_token:
        missing.append("TELEGRAM_TOKEN")
    if not telegram_chat_id:
        missing.append("TELEGRAM_CHAT_ID")
    if not ig_username:
        missing.append("IG_USERNAME")
    if not ig_password:
        missing.append("IG_PASSWORD")
    if missing:
        raise RuntimeError(f"Missing env vars: {', '.join(missing)}")

    ig_session_file = _env("IG_SESSION_FILE", "ig_session.json")
    history_file = _env("HISTORY_FILE", "gecmis_final.txt")

    poll_interval_seconds = int(_env("POLL_INTERVAL_SECONDS", "900"))
    per_account_delay_seconds = float(_env("PER_ACCOUNT_DELAY_SECONDS", "2"))
    jitter_seconds = float(_env("JITTER_SECONDS", "1"))

    target_ids_raw = _env("TARGET_IDS", "")
    if target_ids_raw:
        target_ids = [x.strip() for x in target_ids_raw.split(",") if x.strip()]
    else:
        target_ids = DEFAULT_TARGET_IDS[:]

    return Config(
        telegram_token=telegram_token,
        telegram_chat_id=telegram_chat_id,
        ig_username=ig_username,
        ig_password=ig_password,
        ig_session_file=ig_session_file,
        history_file=history_file,
        poll_interval_seconds=poll_interval_seconds,
        per_account_delay_seconds=per_account_delay_seconds,
        jitter_seconds=jitter_seconds,
        target_ids=target_ids,
    )


def load_history(path: str) -> set[str]:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return {line.strip() for line in f if line.strip()}
    return set()


def save_to_history(path: str, media_id: str) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"{media_id}\n")


def build_ig_client(username: str, password: str, session_file: str) -> Client:
    """
    Login and cache session/settings.
    Notes:
    - Instagram may request Challenge/2FA; this needs manual completion in-app.
    - Session file is persisted so subsequent runs reduce login frequency.
    """
    cl = Client()
    if session_file and os.path.exists(session_file):
        try:
            cl.load_settings(session_file)
        except Exception:
            pass
    try:
        cl.login(username, password)
        if session_file:
            cl.dump_settings(session_file)
    except TwoFactorRequired as e:
        raise RuntimeError(
            "Instagram 2FA istiyor. Önce hesabı Instagram uygulamasında doğrula "
            "veya istersen 2FA kod akışını koda ekleyebilirim."
        ) from e
    except ChallengeRequired as e:
        raise RuntimeError(
            "Instagram 'challenge' (şüpheli giriş) istiyor. Instagram uygulamasından girip "
            "challenge'ı tamamla, sonra tekrar çalıştır."
        ) from e
    except LoginRequired as e:
        raise RuntimeError(
            "Instagram login başarısız. Kullanıcı adı/şifre doğru mu? Challenge/2FA olabilir."
        ) from e
    return cl


def extract_media_url(item):
    """
    Extract URLs from instagrapi Media/Story/Resource models.
    Telegram will download from these URLs.
    """
    video_url = getattr(item, "video_url", None) or None
    image_url = getattr(item, "thumbnail_url", None) or getattr(item, "url", None) or None
    return video_url, image_url


async def process_and_send_post(
    bot: Bot,
    cfg: Config,
    sent_ids: set[str],
    post_item,
    user_label: str,
):
    post_id = str(getattr(post_item, "pk", None) or getattr(post_item, "id", None))
    if post_id in sent_ids:
        return

    print(f"   ✨ Yeni Post: {user_label} ({post_id})")

    resources = getattr(post_item, "resources", None) or []
    if resources:
        total_slides = len(resources)
        for i, slide in enumerate(resources, 1):
            vid, img = extract_media_url(slide)
            caption = f"📮 Post (ID: {user_label}) - {i}/{total_slides}"
            try:
                if vid:
                    await bot.send_video(chat_id=cfg.telegram_chat_id, video=vid, caption=caption)
                elif img:
                    await bot.send_photo(chat_id=cfg.telegram_chat_id, photo=img, caption=caption)
                await asyncio.sleep(1)
            except Exception:
                pass
    else:
        vid, img = extract_media_url(post_item)
        caption = f"📮 Post (ID: {user_label})"
        try:
            if vid:
                await bot.send_video(chat_id=cfg.telegram_chat_id, video=vid, caption=caption)
            elif img:
                await bot.send_photo(chat_id=cfg.telegram_chat_id, photo=img, caption=caption)
        except Exception:
            pass

    sent_ids.add(post_id)
    save_to_history(cfg.history_file, post_id)


async def send_story_media(
    bot: Bot,
    cfg: Config,
    sent_ids: set[str],
    media_item,
    caption: str,
):
    media_id = str(getattr(media_item, "pk", None) or getattr(media_item, "id", None))
    if media_id in sent_ids:
        return

    vid, img = extract_media_url(media_item)
    try:
        if vid:
            print("   📹 Story (Video)...")
            await bot.send_video(chat_id=cfg.telegram_chat_id, video=vid, caption=caption)
        elif img:
            print("   📸 Story (Foto)...")
            await bot.send_photo(chat_id=cfg.telegram_chat_id, photo=img, caption=caption)
        sent_ids.add(media_id)
        save_to_history(cfg.history_file, media_id)
        await asyncio.sleep(2)
    except Exception:
        pass


async def main():
    cfg = load_config()
    sent_ids = load_history(cfg.history_file)

    bot = Bot(token=cfg.telegram_token)

    print("🚀 Bot Başlatıldı (ÜCRETSİZ IG SESSION MODU)")
    print(f"👤 Hedef ID Sayısı: {len(cfg.target_ids)}")
    print(
        f"⏱️ Poll: {cfg.poll_interval_seconds}s | "
        f"Account delay: {cfg.per_account_delay_seconds}s | Jitter: {cfg.jitter_seconds}s"
    )
    print("🔐 Instagram login başlıyor...")

    cl = await asyncio.to_thread(build_ig_client, cfg.ig_username, cfg.ig_password, cfg.ig_session_file)
    print("✅ Instagram login OK.")
    print("-" * 30)

    # Basit backoff: hata olursa bekleme süresini arttır, sonra toparla.
    backoff = 0.0

    while True:
        loop_started = time.time()
        any_error = False

        for user_id in cfg.target_ids:
            user_label = str(user_id)
            uid = int(user_id)

            print(f"🔍 {user_label} story...")
            try:
                stories = await asyncio.to_thread(cl.user_stories, uid)
                for story in stories:
                    await send_story_media(bot, cfg, sent_ids, story, f"🔔 Story (ID: {user_label})")
            except Exception as e:
                any_error = True
                print(f"⚠️ Story hata ({user_label}): {e}")

            await asyncio.sleep(cfg.per_account_delay_seconds + random.random() * cfg.jitter_seconds)

            print(f"🔍 {user_label} post...")
            try:
                medias = await asyncio.to_thread(cl.user_medias, uid, 2)
                for media in medias:
                    await process_and_send_post(bot, cfg, sent_ids, media, user_label)
            except Exception as e:
                any_error = True
                print(f"⚠️ Post hata ({user_label}): {e}")

            await asyncio.sleep(cfg.per_account_delay_seconds + random.random() * cfg.jitter_seconds)

        elapsed = int(time.time() - loop_started)
        print(f"✅ Tur bitti. Süre: {elapsed}s")

        if any_error:
            backoff = min(max(5.0, backoff * 2 if backoff else 5.0), 600.0)
        else:
            backoff = max(0.0, backoff / 2)

        sleep_for = max(0, cfg.poll_interval_seconds + backoff)
        print(f"🕒 Mola: {sleep_for:.0f}s (backoff={backoff:.0f}s)")
        await asyncio.sleep(sleep_for)


if __name__ == "__main__":
    asyncio.run(main())

