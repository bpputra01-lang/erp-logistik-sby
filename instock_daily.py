import os
import json
import requests
import re
import time
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup

# ==============================================================================
# KONFIGURASI & KREDENSIAL
# ==============================================================================
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
JEZPRO_EMAIL = os.environ.get("JEZPRO_EMAIL")
JEZPRO_PASS  = os.environ.get("JEZPRO_PASSWORD")

BRANCH_NAME = "JEZ SURABAYA"
STORE_ID = 3
POLL_INTERVAL_SECONDS = 15

# Zona Waktu WIB (UTC+7) Murni Bawaan Python - ANTI ERROR 'No module named pytz'
WIB = timezone(timedelta(hours=7))

# ==============================================================================
# HELPER PEMBERSIH & PARSER WAKTU
# ==============================================================================
def strip_html(val):
    if not val: return ""
    return re.sub(r'<[^>]+>', '', str(val)).strip()

def safe_int_val(val, default=0):
    if not val: return default
    digits = re.findall(r'-?\d+', strip_html(val))
    return int(digits[0]) if digits else default

def parse_wib_datetime(dt_str):
    """Mengubah format tanggal Jezpro / Supabase ke objek datetime WIB tanpa pytz"""
    if not dt_str: return None
    clean_str = strip_html(dt_str).strip()
    formats = [
        "%d-%m-%Y %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S"
    ]
    for fmt in formats:
        try:
            naive = datetime.strptime(clean_str[:19], fmt)
            return naive.replace(tzinfo=WIB)
        except Exception:
            pass
    try:
        # Fallback format ISO dari Supabase (misal ada 'Z' atau '+00:00')
        dt = datetime.fromisoformat(clean_str.replace('Z', '+00:00'))
        return dt.astimezone(WIB)
    except Exception:
        return None

# ==============================================================================
# AUTENTIKASI KE JEZPRO
# ==============================================================================
def create_jezpro_session():
    if not JEZPRO_EMAIL or not JEZPRO_PASS:
        raise ValueError("Environment JEZPRO_EMAIL dan JEZPRO_PASSWORD belum diset!")

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })
    print("🔐 [1/3] Login ke Jezpro...")
    res = session.get("https://jezpro.id/")
    soup = BeautifulSoup(res.text, "html.parser")
    token_input = soup.find("input", {"name": "_token"})
    if not token_input:
        raise Exception("Gagal mendapatkan CSRF Token Jezpro!")

    payload = {
        "_token": token_input.get("value"),
        "u_email": JEZPRO_EMAIL,
        "password": JEZPRO_PASS
    }
    session.post("https://jezpro.id/user_login", data=payload)
    print("✅ Berhasil login Jezpro!")
    return session

# ==============================================================================
# FETCH DATA HELPER & MUTASI
# ==============================================================================
def fetch_helper_jezpro(session):
    """Menarik antrean WAITING OFFLINE dari Helper App Jezpro"""
    url = "https://jezpro.id/scan_product_in_datatables"
    params = {
        "draw": "1",
        "start": "0",
        "length": "500",
        "st_id": str(STORE_ID),
        "waiting": "WAITING OFFLINE",
        "_": int(time.time() * 1000)
    }
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://jezpro.id/helper_backup"
    }

    try:
        res = session.get(url, params=params, headers=headers, timeout=15)
        if res.status_code == 200:
            data = res.json().get("data", [])
            clean_list = []
            for item in data:
                raw_bin = strip_html(item.get("product_location") or "[WAITING OFFLINE]").upper()
                clean_bin = raw_bin.replace('[', '').replace(']', '').strip()
                clean_list.append({
                    "barcode_sku": strip_html(item.get("barcode") or item.get("ps_barcode") or "-").upper(),
                    "article_name": strip_html(item.get("article") or "-"),
                    "bin_code": clean_bin if clean_bin else "STAGING INBOUND",
                    "qty": safe_int_val(item.get("qty"), 1),
                    "invoice": strip_html(item.get("invoice") or "-")
                })
            return clean_list
    except Exception as e:
        print(f"⚠️ Gagal fetch helper: {e}")
    return []

def fetch_bin_history_today(session):
    """Menarik riwayat mutasi hari ini dari setup_lokasi_stok_v2"""
    today_str = datetime.now(WIB).strftime("%Y-%m-%d")
    url = "https://jezpro.id/bin_history_datatables"
    params = {
        "draw": "1",
        "start": "0",
        "length": "500",
        "st_id": str(STORE_ID),
        "date": today_str,
        "_": int(time.time() * 1000)
    }
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://jezpro.id/setup_lokasi_stok_v2"
    }

    try:
        res = session.get(url, params=params, headers=headers, timeout=15)
        if res.status_code == 200:
            raw_data = res.json().get("data", [])
            history_list = []
            for item in raw_data:
                mutasi_id = strip_html(item.get("pmt_id") or item.get("DT_RowIndex") or "")
                raw_time = strip_html(item.get("pm_created_at") or "")
                dt_mutasi = parse_wib_datetime(raw_time)

                history_list.append({
                    "mutasi_id": str(mutasi_id),
                    "sku": strip_html(item.get("ps_barcode") or "").upper(),
                    "bin_awal": strip_html(item.get("start_bin") or "").upper(),
                    "bin_tujuan": strip_html(item.get("end_bin") or "").upper(),
                    "qty_mts": safe_int_val(item.get("pmt_qty"), 0),
                    "notes": strip_html(item.get("notes") or "").upper(),
                    "dt_wib": dt_mutasi,
                    "raw_time": raw_time
                })
            return history_list
    except Exception as e:
        print(f"⚠️ Gagal fetch bin_history: {e}")
    return []

# ==============================================================================
# SINKRONISASI SUPABASE (DENGAN TIME VALIDATION & LEDGER LOCK)
# ==============================================================================
def sync_cycle(session):
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Environment SUPABASE_URL dan SUPABASE_KEY wajib diset!")

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    now_wib = datetime.now(WIB)
    today_date = now_wib.strftime("%Y-%m-%d")

    # Ambil data hari ini dari Supabase
    sb_url = f"{SUPABASE_URL}/rest/v1/jezpro_instock_daily?select=*&sync_date=eq.{today_date}"
    res_sb = requests.get(sb_url, headers=headers)
    sb_records = res_sb.json() if res_sb.status_code == 200 else []

    waiting_in_sb = [x for x in sb_records if x.get("status") == "WAITING OFFLINE"]
    need_setup_in_sb = [x for x in sb_records if x.get("status") == "NEED_SETUP"]
    done_setup_in_sb = [x for x in sb_records if x.get("status") == "DONE_SETUP"]

    # Kunci mutasi_id yang sudah pernah terpakai
    used_mutasi_ids = set()
    for d in done_setup_in_sb:
        m_id = d.get("matched_mutasi_id")
        if m_id:
            used_mutasi_ids.add(str(m_id))

    sb_waiting_map = {f"{it['barcode_sku']}_{it.get('invoice','')}": it for it in waiting_in_sb}

    # --- LANGKAH 1: CEK HELPER BACKUP ---
    jez_helper = fetch_helper_jezpro(session)
    current_helper_keys = set()
    new_inserts = []

    for it in jez_helper:
        k = f"{it['barcode_sku']}_{it['invoice']}"
        current_helper_keys.add(k)
        if k not in sb_waiting_map:
            new_inserts.append({
                "barcode_sku": it["barcode_sku"],
                "article_name": it["article_name"],
                "bin_code": it["bin_code"],
                "qty": it["qty"],
                "status": "WAITING OFFLINE",
                "invoice": it["invoice"],
                "sync_date": today_date,
                "created_at": now_wib.isoformat()
            })

    if new_inserts:
        requests.post(f"{SUPABASE_URL}/rest/v1/jezpro_instock_daily", headers=headers, json=new_inserts)
        print(f"   📥 {len(new_inserts)} barang baru masuk antrean WAITING OFFLINE.")

    # Deteksi barang yang hilang dari Helper -> Pindah ke NEED_SETUP
    for k, sb_item in sb_waiting_map.items():
        if k not in current_helper_keys:
            disappeared_timestamp = now_wib.isoformat()
            patch_url = f"{SUPABASE_URL}/rest/v1/jezpro_instock_daily?id=eq.{sb_item['id']}"
            requests.patch(patch_url, headers=headers, json={
                "status": "NEED_SETUP",
                "disappeared_at": disappeared_timestamp
            })
            print(f"   ⚠️ BARANG HILANG ({now_wib.strftime('%H:%M:%S')}): {sb_item['barcode_sku']} ➔ Siap Setup di Shiny!")

    # --- LANGKAH 2: CEK MUTASI SUDAH DIEKSEKUSI (TIME & MUTASI-ID MATCHING) ---
    if need_setup_in_sb:
        mutasi_today = fetch_bin_history_today(session)
        # Urutkan mutasi dari yang paling awal ke paling baru
        mutasi_today = sorted(mutasi_today, key=lambda x: x["dt_wib"] or now_wib)

        for target in need_setup_in_sb:
            t_sku = target["barcode_sku"]
            t_bin_awal = target["bin_code"]
            t_qty = safe_int_val(target["qty"], 1)
            t_disappeared_dt = parse_wib_datetime(target.get("disappeared_at"))

            matched_mutasi = None

            for m in mutasi_today:
                m_id = m["mutasi_id"]
                if m_id in used_mutasi_ids:
                    continue

                sku_match = (m["sku"] == t_sku)
                bin_awal_match = (m["bin_awal"] == t_bin_awal or t_bin_awal in m["bin_awal"] or m["bin_awal"] in ["STAGING INBOUND", "WAITING OFFLINE"])
                bin_tujuan_match = ("GL1-INSTOCK" in m["bin_tujuan"] or "INSTOCK" in m["bin_tujuan"])
                qty_match = (m["qty_mts"] >= t_qty)

                # Validasi: Waktu mutasi harus >= Waktu barang hilang (toleransi mundur 60 detik)
                time_valid = True
                if t_disappeared_dt and m["dt_wib"]:
                    time_diff = (m["dt_wib"] - t_disappeared_dt).total_seconds()
                    if time_diff < -60:
                        time_valid = False

                if sku_match and bin_awal_match and bin_tujuan_match and qty_match and time_valid:
                    matched_mutasi = m
                    break

            if matched_mutasi:
                used_mutasi_ids.add(matched_mutasi["mutasi_id"])

                patch_url = f"{SUPABASE_URL}/rest/v1/jezpro_instock_daily?id=eq.{target['id']}"
                requests.patch(patch_url, headers=headers, json={
                    "status": "DONE_SETUP",
                    "matched_mutasi_id": matched_mutasi["mutasi_id"],
                    "setup_done_at": matched_mutasi["raw_time"]
                })
                print(f"   🎉 MATCH VALID! SKU: {t_sku} (Hilang: {target.get('disappeared_at')[11:19]} ➔ Mutasi: {matched_mutasi['raw_time']}) ➔ DIGESER KE DONE SETUP!")

# ==============================================================================
# EKSEKUSI PROGRAM REAL-TIME LOOPING
# ==============================================================================
if __name__ == "__main__":
    # Baca durasi kerja dari environment variable GitHub Actions
    # Default: loop 28 menit (1680 detik) dengan jeda 15 detik sekali cek
    max_duration = int(os.environ.get("WORKER_DURATION_SECONDS", "1680"))
    poll_interval = int(os.environ.get("POLL_INTERVAL_SECONDS", "15"))

    print("=" * 65)
    print(f"🚀 WORKER REAL-TIME AKTIF: Cek Jezpro setiap {poll_interval} detik")
    print(f"⏱️ Durasi sesi runner: {max_duration // 60} menit")
    print("=" * 65)

    jez_session = create_jezpro_session()
    start_time = time.time()
    cycle_count = 1

    while (time.time() - start_time) < max_duration:
        try:
            print(f"\n🔄 [Cycle #{cycle_count}] Pengecekan data Jezpro: {datetime.now(WIB).strftime('%H:%M:%S')} WIB")
            sync_cycle(jez_session)
            cycle_count += 1
        except Exception as e:
            print(f"❌ Terjadi kesalahan pada cycle #{cycle_count}: {e}")
            # Jika session login expired, coba login ulang
            time.sleep(3)
            try:
                jez_session = create_jezpro_session()
            except Exception:
                pass

        time.sleep(poll_interval)

    print("\n🏁 Sesi runner 28 menit selesai. Akan dilanjutkan oleh jadwal berikutnya.")
