import os
import re
import time
import requests
import threading
from datetime import datetime
from bs4 import BeautifulSoup

# Untuk pemutar audio & Text-to-Speech
from gtts import gTTS
import pygame

# ==============================================================================
# 🔑 KREDENSIAL & KONFIGURASI JEZPRO
# ==============================================================================
JEZPRO_EMAIL = os.environ.get("JEZPRO_EMAIL", "fajarbintang786@jez.co.id")
JEZPRO_PASSWORD = os.environ.get("JEZPRO_PASSWORD", "131199")
STORE_ID_SURABAYA = 3  # Sesuaikan dengan store id tempatmu (3 = Surabaya)

AUDIO_FILE = "mas_ambilin_dong.mp3"
CHECK_INTERVAL_SECONDS = 3  # Rekomendasi 1.5 - 2 detik agar tidak diblokir Cloudflare

# ==============================================================================
# 🔊 GENERATOR & PEMUTAR SUARA
# ==============================================================================
def init_audio():
    # Buat file audio jika belum ada
    if not os.path.exists(AUDIO_FILE):
        print("🎙️ Sedang membuat voice over wanita: 'Mas ambilin dong'...")
        tts = gTTS(text="Mas, ambilin dong!", lang="id", slow=False)
        tts.save(AUDIO_FILE)
        print("✅ File audio berhasil dibuat!")

    # Inisialisasi mixer pygame
    pygame.mixer.init()

def play_alert_sound():
    try:
        def _play():
            pygame.mixer.music.load(AUDIO_FILE)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)

        # Mainkan di thread terpisah agar proses scraping tidak terhenti sesaat
        threading.Thread(target=_play, daemon=True).start()
    except Exception as e:
        print(f"⚠️ Gagal memutar suara: {e}")

# ==============================================================================
# 🔐 LOGIN KE JEZPRO
# ==============================================================================
def create_jezpro_session():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
    })
    print(f"🔐 [{datetime.now().strftime('%H:%M:%S')}] Login ke Jezpro...")
    res = session.get("https://jezpro.id/", timeout=20)
    soup = BeautifulSoup(res.text, "html.parser")
    token_tag = soup.find("input", {"name": "_token"})
    if not token_tag:
        raise Exception("Gagal mendapatkan CSRF Token Jezpro!")

    res_post = session.post("https://jezpro.id/user_login", data={
        "_token": token_tag["value"],
        "u_email": JEZPRO_EMAIL,
        "password": JEZPRO_PASSWORD
    }, timeout=20)

    # Kunjungi helper_backup untuk registrasi cookie session
    session.get("https://jezpro.id/helper_backup", timeout=15)
    print("✅ Berhasil login Jezpro!")
    return session

# ==============================================================================
# 🚀 LOOP PEMANTAUAN REAL-TIME
# ==============================================================================
from supabase import create_client

# Masukkan URL & Key Supabase proyek Anda langsung di sini:
SUPABASE_URL = "https://fanzsmghhbefhhaicrok.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZhbnpzbWdoaGJlZmhoYWljcm9rIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODgxNTQzNDgsImV4cCI6MjEwMzczMDM0OH0.brCSOO9nHAUK8CxDWPperpJ--_NA_nwy5cO9OqGv3I0"

# Buat fungsi get_supabase agar baris 90 tidak error lagi
_client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_supabase():
    return _client

def start_monitoring():
    init_audio()
    session = create_jezpro_session()
    supabase = get_supabase() # Hubungkan ke Supabase

    url_target = "https://jezpro.id/product_out_datatables"
    headers_req = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://jezpro.id/helper_backup"
    }

    seen_request_keys = set()
    is_initial_load = True

    print("\n" + "=" * 65)
    print(f"🎧 MONITOR PERMINTAAN FL AKTIF (Tersambung ke Supabase & Web)")
    print("📢 Menunggu permintaan barang masuk dari Frontline...")
    print("=" * 65 + "\n")

    while True:
        try:
            params = {
                "draw": str(int(time.time())),
                "columns[0][data]": "article",
                "columns[0][name]": "article",
                "columns[0][searchable]": "true",
                "columns[0][orderable]": "false",
                "order[0][column]": "0",
                "order[0][dir]": "desc",
                "start": "0",
                "length": "25",
                "search": "",
                "st_id": str(STORE_ID_SURABAYA),
                "_": int(time.time() * 1000)
            }

            resp = session.get(url_target, params=params, headers=headers_req, timeout=10)

            if resp.status_code in [401, 419] or "login" in resp.url:
                print("⚠️ Sesi login habis, mencoba login ulang...")
                session = create_jezpro_session()
                continue

            if resp.status_code == 200:
                raw_json = resp.json()
                data_list = raw_json.get("data", [])

                for item in data_list:
                    req_id = item.get("id") or item.get("plst_id") or item.get("DT_RowIndex")
                    art_name = item.get("article") or item.get("p_name") or "-"
                    waktu = item.get("datetime") or item.get("created_at") or "-"
                    pic = item.get("user_name") or item.get("u_name") or "Tim FL"
                    bin_lokasi = item.get("product_location") or item.get("pl_code") or "-"
                    qty_val = int(item.get("qty", 1) or 1)

                    unique_key = f"{req_id}_{art_name}_{waktu}"

                    if is_initial_load:
                        seen_request_keys.add(unique_key)
                        continue

                    # JIKA ADA PERMINTAAN BARU
                    if unique_key not in seen_request_keys:
                        seen_request_keys.add(unique_key)

                        now_str = datetime.now().strftime("%H:%M:%S")
                        print(f"\n🚨 [{now_str}] PERMINTAAN BARU: {art_name} ({pic}) -> Kirim ke Supabase!")
                        
                        # 1. Kirim ke database Supabase agar web di laptop lain tahu
                        try:
                            supabase.table("jezpro_fl_requests").insert({
                                "req_id": str(req_id),
                                "article_name": str(art_name),
                                "pic": str(pic),
                                "bin": str(bin_lokasi),
                                "qty": qty_val,
                                "created_at": datetime.now().isoformat()
                            }).execute()
                        except Exception as err_db:
                            print(f"⚠️ Gagal simpan ke Supabase: {err_db}")

                        # 2. Bunyikan suara di speaker laptop ini
                        play_alert_sound()

                is_initial_load = False

        except requests.exceptions.RequestException as e:
            print(f"⚠️ Masalah koneksi: {e}")
        except Exception as e:
            print(f"❌ Error: {e}")

        time.sleep(CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    start_monitoring()