import os
import re
import time
import requests
import pandas as pd
from datetime import datetime, date, timedelta, timezone
from bs4 import BeautifulSoup

# ==============================================================================
# 🔑 KREDENSIAL & KONFIGURASI SUPABASE & JEZPRO
# ==============================================================================
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://fanzsmghhbefhhaicrok.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZhbnpzbWdoaGJlZmhoYWljcm9rIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODgxNTQzNDgsImV4cCI6MjEwMzczMDM0OH0.brCSOO9nHAUK8CxDWPperpJ--_NA_nwy5cO9OqGv3I0")

JEZPRO_EMAIL = os.environ.get("JEZPRO_EMAIL", "fajarbintang786@jez.co.id")
JEZPRO_PASSWORD = os.environ.get("JEZPRO_PASSWORD", "131199")

WIB = timezone(timedelta(hours=7))

# Mapping ID Cabang Resmi Jezpro (Sesuai Orchestrator Anda)
BRANCH_MAP = {
    "JEZ SURABAYA": 3,
    "JEZ SEMARANG": 53,
    "JEZ SIDOARJO": 8,
    "JEZ KEDIRI": 5,
    "JEZ MALANG": 2,
    "JEZ JEMBER": 40,
    "HUB JAKARTA": 55,
    "ONLINE HUB SURABAYA": 30,
    "ONLINE HUB MALANG": 20,
}

HEADERS_SB = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates"
}

PATTERN_MISS_LOC = re.compile(r"mis+[\s\-_]*loc", re.IGNORECASE)


# ==============================================================================
# HELPER PEMBERSIH & PARSER
# ==============================================================================
def strip_html(val):
    if not val:
        return ""
    s = str(val)
    if "<" in s:
        s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"\s+", " ", s).strip()


def parse_datetime(dt_str):
    if not dt_str:
        return datetime.now(WIB).strftime("%Y-%m-%d %H:%M:%S")
    clean = strip_html(dt_str).strip()
    for fmt in ("%d-%m-%Y %H:%M:%S", "%d/%m/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(clean[:19], fmt).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            pass
    try:
        return pd.to_datetime(clean, dayfirst=True).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return datetime.now(WIB).strftime("%Y-%m-%d %H:%M:%S")


# ==============================================================================
# AUTENTIKASI KE JEZPRO
# ==============================================================================
def create_jezpro_session():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
    })
    print(f"🔐 [{datetime.now(WIB).strftime('%H:%M:%S')}] Login ke Jezpro ({JEZPRO_EMAIL})...")
    res = session.get("https://jezpro.id/", timeout=20)
    soup = BeautifulSoup(res.text, "html.parser")
    token_tag = soup.find("input", {"name": "_token"})
    if not token_tag:
        raise Exception("Gagal mendapatkan CSRF Token Jezpro!")

    login_res = session.post(
        "https://jezpro.id/user_login",
        data={
            "_token": token_tag["value"],
            "u_email": JEZPRO_EMAIL,
            "password": JEZPRO_PASSWORD,
        },
        timeout=20,
    )

    # Inisialisasi route setup lokasi stok agar session cookie aktif
    session.get("https://jezpro.id/setup_lokasi_stok_v2", timeout=15)
    print("✅ Berhasil login Jezpro!\n")
    return session


def relogin_jezpro(session):
    try:
        print(f"🔄 [{datetime.now(WIB).strftime('%H:%M:%S')}] Sesi kedaluwarsa, relogin...")
        res = session.get("https://jezpro.id/", timeout=20)
        soup = BeautifulSoup(res.text, "html.parser")
        token_tag = soup.find("input", {"name": "_token"})
        if not token_tag:
            return False

        session.post(
            "https://jezpro.id/user_login",
            data={
                "_token": token_tag["value"],
                "u_email": JEZPRO_EMAIL,
                "password": JEZPRO_PASSWORD,
            },
            timeout=20,
        )
        session.get("https://jezpro.id/setup_lokasi_stok_v2", timeout=15)
        return True
    except Exception as e:
        print(f"❌ Gagal relogin: {e}")
        return False


# ==============================================================================
# SINKRONISASI MISS LOCATION 2 BULAN TERAKHIR (PER CABANG)
# ==============================================================================
def run_sync_miss_location(days_back: int = 60, batch_upload_size: int = 500):
    session = create_jezpro_session()
    today = date.today()
    date_list = [
        (today - timedelta(days=i)).strftime("%Y-%m-%d")
        for i in range(days_back)
    ]

    print("=" * 80)
    print(f"🚀 SCRAPING MISS LOCATION TIAP CABANG ({date_list[-1]} s/d {date_list[0]})")
    print(f"   -> Jumlah Cabang : {len(BRANCH_MAP)} Cabang")
    print("   -> Filter Note   : Mengandung variasi MISS LOCATION")
    print("   -> Filter BIN    : Mengecualikan BIN Tujuan KARANTINA")
    print("=" * 80 + "\n")

    url_history = "https://jezpro.id/bin_history_datatables"
    headers_req = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://jezpro.id/setup_lokasi_stok_v2"
    }

    all_matched_records = []

    # Looping per Cabang (Agar st_id selalu valid dan server tidak 500)
    for b_idx, (branch_name, st_id) in enumerate(BRANCH_MAP.items(), start=1):
        print(f"🏢 [{b_idx}/{len(BRANCH_MAP)}] Memeriksa Cabang: {branch_name} (ID: {st_id})...")
        branch_found = 0

        for target_date in date_list:
            # Parameter ringkas persis seperti baris 348 di orchestrator Anda
            params = {
                "draw": "1",
                "start": "0",
                "length": "1000",
                "st_id": str(st_id),  # 🌟 st_id terisi ID angka valid!
                "date": target_date,
                "_": int(time.time() * 1000)
            }

            try:
                resp = session.get(url_history, headers=headers_req, params=params, timeout=25)
                
                # Relogin jika session habis
                if resp.status_code in [401, 419] or "login" in resp.url:
                    if relogin_jezpro(session):
                        resp = session.get(url_history, headers=headers_req, params=params, timeout=25)

                if resp.status_code != 200:
                    # Tampilkan cuplikan respon server jika masih error
                    err_preview = resp.text[:120].replace("\n", " ")
                    print(f"   ⚠️ {branch_name} Tgl {target_date}: Status {resp.status_code} ({err_preview})")
                    continue

                raw_json = resp.json().get("data", [])

                for item in raw_json:
                    note_text = strip_html(item.get("notes") or "")
                    end_bin = strip_html(item.get("end_bin") or "").upper()

                    # SYARAT: Catatan Miss Location & BIN Tujuan bukan Karantina
                    if PATTERN_MISS_LOC.search(note_text) and ("KARANTINA" not in end_bin):
                        clean_dt = parse_datetime(item.get("pm_created_at"))
                        try:
                            q_val = int(item.get("pmt_qty", 1))
                        except Exception:
                            q_val = 1

                        pmt_id_raw = item.get("pmt_id") or item.get("id")
                        try:
                            pmt_id_val = int(pmt_id_raw) if pmt_id_raw else None
                        except Exception:
                            pmt_id_val = None

                        all_matched_records.append({
                            "pmt_id": pmt_id_val,
                            "tanggal": clean_dt,
                            "cabang": branch_name,
                            "user_name": strip_html(item.get("u_name", "-")),
                            "sku": strip_html(item.get("ps_barcode", "-")).split(".")[0].upper(),
                            "artikel": strip_html(item.get("article", "-")),
                            "bin_awal": strip_html(item.get("start_bin", "-")).upper(),
                            "qty_mutasi": q_val,
                            "bin_tujuan": end_bin,
                            "catatan": note_text,
                        })
                        branch_found += 1

                time.sleep(0.04)  # Jeda aman

            except Exception as e:
                print(f"   ❌ Error {branch_name} pada {target_date}: {e}")
                continue

        print(f"   ✅ Selesai {branch_name}: Ditemukan {branch_found} baris Miss Location.\n")

    total_scraped = len(all_matched_records)
    print(f"🎯 TOTAL KESELURUHAN MISS LOCATION: {total_scraped:,} baris.\n")

    if total_scraped == 0:
        print("ℹ️ Tidak ada data yang memenuhi kriteria untuk disimpan.")
        return

    # ==========================================================================
    # UPLOAD LANGSUNG KE SUPABASE VIA REST API (UPSERT ANTI-DUPLIKASI)
    # ==========================================================================
    print("📤 Mengunggah data ke tabel Supabase 'jezpro_miss_location_logs'...")
    inserted_count = 0
    upsert_url = f"{SUPABASE_URL}/rest/v1/jezpro_miss_location_logs?on_conflict=tanggal,sku,bin_awal,bin_tujuan,qty_mutasi"

    for i in range(0, total_scraped, batch_upload_size):
        chunk = all_matched_records[i : i + batch_upload_size]
        try:
            res_up = requests.post(upsert_url, headers=HEADERS_SB, json=chunk, timeout=60)
            if res_up.status_code in [200, 201, 204]:
                inserted_count += len(chunk)
                print(f"   ➔ Berhasil upload batch {i + 1} s/d {min(i + batch_upload_size, total_scraped)}...")
            else:
                print(f"   ⚠️ Respons Supabase ({res_up.status_code}): {res_up.text}")
        except Exception as e_up:
            print(f"   ⚠️ Kendala upload batch {i}: {e_up}")

    print(f"\n🎉 SELESAI! {inserted_count:,} baris data Miss Location berhasil tersimpan di Supabase!")


if __name__ == "__main__":
    run_sync_miss_location(days_back=60)