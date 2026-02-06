import requests
import asyncio
import os
import random
from telegram import Bot

# --- 🔐 ANAHTAR HAVUZU (EN ÖNEMLİ KISIM) ---
# Guerrilla Mail ile aldığın keyleri tırnak içinde, virgülle ayırarak yapıştır.
API_KEYS = [
    "0c01188cb4msh74b0acfcc245125p11b555jsn24b92abc748f", # Senin mevcut keyin
    "KEY_2_BURAYA_YAPISTIR",
    "KEY_3_BURAYA_YAPISTIR",
    "KEY_4_BURAYA_YAPISTIR",
    "KEY_5_BURAYA_YAPISTIR",
    "KEY_6_BURAYA_YAPISTIR",
    "KEY_7_BURAYA_YAPISTIR",
    "KEY_8_BURAYA_YAPISTIR",
    "KEY_9_BURAYA_YAPISTIR",
    "KEY_10_BURAYA_YAPISTIR"
]

# Ayarlar
RAPID_API_HOST = "starapi1.p.rapidapi.com"
TELEGRAM_TOKEN = "8502372148:AAGqwcMrkXMasZEhABLmHaE2HKLxOYeRjIY"
CHAT_ID = "7075582251"

# Hedef ID Listesi (Senin verdiğin ID'ler)
TARGET_IDS = [
    "9158581810", "8540571400", "56893406476", "52778386307", 
    "45521544431", "8916182875", "15181547765", "2859988906", "67619369047"
]

HISTORY_FILE = "gecmis_final.txt"

# --- YARDIMCI FONKSİYONLAR ---

def get_random_header():
    """Havuzdan çalışan rastgele bir key seçer."""
    # Placeholder (BURAYA...) olanları filtrele
    valid_keys = [k for k in API_KEYS if "BURAYA" not in k and len(k) > 10]
    
    if not valid_keys:
        print("❌ HATA: Listede hiç geçerli API Key yok! Lütfen bot.py dosyasını düzenle.")
        return None

    selected_key = random.choice(valid_keys)
    return {
        "x-rapidapi-key": selected_key,
        "x-rapidapi-host": RAPID_API_HOST,
        "Content-Type": "application/json"
    }

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return set(line.strip() for line in f)
    return set()

def save_to_history(media_id):
    with open(HISTORY_FILE, "a") as f:
        f.write(f"{media_id}\n")

SENT_IDS = load_history()

try:
    bot = Bot(token=TELEGRAM_TOKEN)
except Exception as e:
    print(f"Bot token hatası: {e}")
    exit()

# --- İSTEK FONKSİYONLARI ---

def get_stories(user_id):
    url = f"https://{RAPID_API_HOST}/instagram/user/get_stories"
    payload = {"ids": [user_id]}
    header = get_random_header()
    if not header: return None

    try:
        response = requests.post(url, json=payload, headers=header, timeout=30)
        if response.status_code == 429:
            print("⚠️ Bir anahtarın kotası doldu, diğer turda başkası seçilecek.")
        return response.json()
    except:
        return None

def get_posts(user_id):
    url = f"https://{RAPID_API_HOST}/instagram/user/get_media"
    payload = {"id": user_id, "count": 2}
    header = get_random_header()
    if not header: return None

    try:
        response = requests.post(url, json=payload, headers=header, timeout=30)
        return response.json()
    except:
        return None

def extract_media_url(item):
    video_url = None
    image_url = None
    
    if 'video_versions' in item:
        video_url = item['video_versions'][0]['url']
    elif item.get('video_url'):
        video_url = item['video_url']

    if not video_url:
        if 'image_versions2' in item:
            candidates = item['image_versions2'].get('candidates', [])
            if candidates: image_url = candidates[0]['url']
        elif 'display_url' in item:
            image_url = item['display_url']
            
    return video_url, image_url

async def process_and_send_post(post_item, user_label):
    post_id = str(post_item.get('pk') or post_item.get('id'))
    
    if post_id in SENT_IDS: return

    print(f"   ✨ Yeni Post: {user_label}")

    if 'carousel_media' in post_item and post_item['carousel_media']:
        album = post_item['carousel_media']
        total_slides = len(album)
        
        for i, slide in enumerate(album, 1):
            vid, img = extract_media_url(slide)
            caption = f"📮 Post (ID: {user_label}) - {i}/{total_slides}"
            try:
                if vid: await bot.send_video(chat_id=CHAT_ID, video=vid, caption=caption)
                elif img: await bot.send_photo(chat_id=CHAT_ID, photo=img, caption=caption)
                await asyncio.sleep(1) 
            except: pass
    else:
        vid, img = extract_media_url(post_item)
        caption = f"📮 Post (ID: {user_label})"
        try:
            if vid: await bot.send_video(chat_id=CHAT_ID, video=vid, caption=caption)
            elif img: await bot.send_photo(chat_id=CHAT_ID, photo=img, caption=caption)
        except: pass

    SENT_IDS.add(post_id)
    save_to_history(post_id)

async def send_story_media(media_item, caption):
    media_id = str(media_item.get('pk') or media_item.get('id'))
    if media_id in SENT_IDS: return

    vid, img = extract_media_url(media_item)
    try:
        if vid:
            print(f"   📹 Story (Video)...")
            await bot.send_video(chat_id=CHAT_ID, video=vid, caption=caption)
        elif img:
            print(f"   📸 Story (Foto)...")
            await bot.send_photo(chat_id=CHAT_ID, photo=img, caption=caption)
        SENT_IDS.add(media_id)
        save_to_history(media_id)
        await asyncio.sleep(2)
    except: pass

async def main():
    print("🚀 Bot Başlatıldı (API HAVUZ MODU)...")
    
    active_keys = [k for k in API_KEYS if 'BURAYA' not in k]
    print(f"🔑 Aktif Key Sayısı: {len(active_keys)}")
    
    if len(active_keys) < 2:
        print("⚠️ UYARI: Çok az key var! Lütfen Guerrilla Mail ile alıp listeyi doldur.")

    print(f"👤 Hedef ID Sayısı: {len(TARGET_IDS)}")
    print("-" * 30)
    
    while True:
        for user_id in TARGET_IDS:
            user_label = str(user_id) 

            # Story
            print(f"🔍 {user_label} story...")
            s_data = get_stories(user_id)
            if s_data:
                try:
                    reels = s_data.get('response', {}).get('body', {}).get('reels', {})
                    items = reels.get(str(user_id), {}).get('items', [])
                    for item in items: await send_story_media(item, f"🔔 Story (ID: {user_label})")
                except: pass

            await asyncio.sleep(1)

            # Post
            print(f"🔍 {user_label} post...")
            p_data = get_posts(user_id)
            if p_data:
                try:
                    items = p_data.get('response', {}).get('body', {}).get('items', [])
                    for item in items: await process_and_send_post(item, user_label)
                except: pass
            
            await asyncio.sleep(2)

        # ✅ SÜRE: 12 SAAT (43200 Saniye)
        print("✅ Tur bitti. 12 SAAT mola...")
        await asyncio.sleep(43200)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
  
