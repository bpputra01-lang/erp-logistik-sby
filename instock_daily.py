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

# Zona Waktu WIB (UTC+7)
WIB = timezone(timedelta(hours=7))

# ==============================================================================
# HELPER PEMBERSIH & PARSER WAKTU
# ==============================================================================
def strip_html(val):
    if not val: return ""
    return re.sub(r'<[^>]+>', '', str(val)).strip()

def clean_bin(val):
    txt = strip_html(val)
    return txt.replace('[', '').replace(']', '').strip().upper()

def safe_int_val(val, default=0):
    if not val: return default
    digits = re.findall(r'-?\d+', strip_html(val))
    return int(digits[0]) if digits else default

def clean_sku_key(sku):
    if not sku: return ""
    s = str(sku).strip().upper()
    if s.endswith('.0'): s = s[:-2]
    return s if s not in ["-", "NAN", "NONE", "NULL", ""] else ""

def clean_article_name(raw_text):
    if not raw_text: return "-"
    t = strip_html(raw_text)
    t = re.sub(r'\b(WAITING OFFLINE|WAITING|REFUND|JEZ SURABAYA|Jml\s*:\s*\d+)\b', '', t, flags=re.IGNORECASE)
    t = " ".join(t.split()).strip()
    return t if t else "-"

def parse_wib_datetime(dt_str):
    if not dt_str: return None
    clean_str = strip_html(dt_str).strip()
    formats = [
        "%d/%m/%Y %H:%M:%S",
        "%d-%m-%Y %H:%M:%S",
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
        dt = datetime.fromisoformat(clean_str.replace('Z', '+00:00'))
        return dt.astimezone(WIB)
    except Exception:
        return None

def get_next_supabase_id(headers):
    """Mengambil ID tertinggi agar tidak terjadi null value pada kolom id"""
    try:
        url = f"{SUPABASE_URL}/rest/v1/jezpro_instock_daily?select=id&order=id.desc&limit=1"
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200 and res.json():
            max_id = res.json()[0].get("id")
            if max_id is not None:
                return int(max_id) + 1
    except Exception as e:
        print(f"⚠️ Gagal fetch max_id: {e}")
    return int(time.time() * 1000) % 2147483640

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
    res = session.get("https://jezpro.id/", timeout=15)
    soup = BeautifulSoup(res.text, "html.parser")
    token_input = soup.find("input", {"name": "_token"})
    if not token_input:
        raise Exception("Gagal mendapatkan CSRF Token Jezpro!")

    payload = {
        "_token": token_input.get("value"),
        "u_email": JEZPRO_EMAIL,
        "password": JEZPRO_PASS
    }
    session.post("https://jezpro.id/user_login", data=payload, timeout=15)
    print("✅ Berhasil login Jezpro!")
    return session

# ==============================================================================
# FETCH DATA: STOCK TRACKING & MUTASI
# ==============================================================================
def fetch_stock_tracking_today(session):
    today_str = datetime.now(WIB).strftime("%Y-%m-%d")
    url = "https://jezpro.id/stock_tracking_datatables"
    params = {
        "draw": "1",
        "start": "0",
        "length": "1000",
        "st_id": str(STORE_ID),
        "date": today_str,
        "status": "WAITING OFFLINE",
        "_": int(time.time() * 1000)
    }
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://jezpro.id/stock_tracking"
    }

    def get_cell(row, key, index):
        if isinstance(row, dict):
            if key in row and row[key] is not None: return row[key]
            if str(index) in row and row[str(index)] is not None: return row[str(index)]
        elif isinstance(row, list) and len(row) > index:
            return row[index]
        return ""

    try:
        res = session.get(url, params=params, headers=headers, timeout=25)
        if res.status_code == 200:
            raw_data = res.json().get("data", [])
            tracking_list = []
            for item in raw_data:
                sku = clean_sku_key(get_cell(item, "ps_barcode", 2))
                if not sku:
                    continue

                raw_time = strip_html(get_cell(item, "datetime", 1))
                dt_wib = parse_wib_datetime(raw_time)
                loc_bin = clean_bin(get_cell(item, "product_location", 7))
                status_val = strip_html(get_cell(item, "status", 8)).upper()
                source_val = strip_html(get_cell(item, "instock_source", 9)).upper()

                tracking_list.append({
                    "sku": sku,
                    "article": clean_article_name(get_cell(item, "article", 3)),
                    "invoice": strip_html(get_cell(item, "invoice", 4)),
                    "qty": safe_int_val(get_cell(item, "qty", 6), 1),
                    "location": loc_bin if loc_bin else "STAGING INBOUND",
                    "status": status_val,             # "INSTOCK" atau "WAITING OFFLINE"
                    "instock_source": source_val,     # "WAITING"
                    "raw_time": raw_time,             # "06/11/2026 20:04:41"
                    "dt_wib": dt_wib
                })
            return tracking_list
    except Exception as e:
        print(f"⚠️ Gagal fetch stock_tracking: {e}")
    return []

def fetch_bin_history_today(session):
    today_str = datetime.now(WIB).strftime("%Y-%m-%d")
    url = "https://jezpro.id/bin_history_datatables"
    params = {
        "draw": "1",
        "start": "0",
        "length": "1000",
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
        res = session.get(url, params=params, headers=headers, timeout=20)
        if res.status_code == 200:
            raw_data = res.json().get("data", [])
            history_list = []
            for item in raw_data:
                mutasi_id = strip_html(item.get("pmt_id") or item.get("DT_RowIndex") or "")
                raw_time = strip_html(item.get("pm_created_at") or "")
                dt_mutasi = parse_wib_datetime(raw_time)
                sku = clean_sku_key(item.get("ps_barcode") or item.get("barcode"))

                if sku:
                    history_list.append({
                        "mutasi_id": str(mutasi_id),
                        "sku": sku,
                        "bin_awal": clean_bin(item.get("start_bin")),
                        "bin_tujuan": clean_bin(item.get("end_bin")),
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
# SINKRONISASI SUPABASE (LANGSUNG ISI DISAPPEARED_AT DENGAN JAM INSTOCK)
# ==============================================================================
def sync_cycle(session):
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Environment SUPABASE_URL dan SUPABASE_KEY wajib diset!")

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    now_wib = datetime.now(WIB)
    today_date = now_wib.strftime("%Y-%m-%d")

    # 1. BERSIHKAN DATA KEMARIN
    try:
        cleanup_url = f"{SUPABASE_URL}/rest/v1/jezpro_instock_daily?sync_date=lt.{today_date}"
        requests.delete(cleanup_url, headers=headers)
    except Exception as e:
        print(f"⚠️ Gagal membersihkan data lama: {e}")

    # 2. AMBIL DATA HARI INI DARI SUPABASE
    sb_url = f"{SUPABASE_URL}/rest/v1/jezpro_instock_daily?select=*&sync_date=eq.{today_date}"
    res_sb = requests.get(sb_url, headers=headers)
    sb_records = res_sb.json() if res_sb.status_code == 200 else []

    waiting_in_sb = [x for x in sb_records if x.get("status") == "WAITING OFFLINE" and clean_sku_key(x.get("barcode_sku"))]
    need_setup_in_sb = [x for x in sb_records if x.get("status") == "NEED_SETUP" and clean_sku_key(x.get("barcode_sku"))]
    done_setup_in_sb = [x for x in sb_records if x.get("status") == "DONE_SETUP" and clean_sku_key(x.get("barcode_sku"))]

    used_mutasi_ids = set(str(d.get("matched_mutasi_id")) for d in done_setup_in_sb if d.get("matched_mutasi_id"))

    # 3. TARIK DATA STOCK TRACKING JEZPRO
    tracking_today = fetch_stock_tracking_today(session)

    instock_movements = []
    waiting_movements = []

    for tr in tracking_today:
        # Jika statusnya INSTOCK dan asalnya WAITING -> ini yang sudah di-scan masuk!
        if "INSTOCK" in tr["status"] and ("WAITING" in tr["instock_source"] or "WAITING" in tr["status"]):
            instock_movements.append(tr)
        elif "WAITING" in tr["status"] or "WAITING" in tr["instock_source"]:
            waiting_movements.append(tr)

    current_auto_id = get_next_supabase_id(headers)
    new_inserts = []

    # Map jumlah SKU di Supabase
    sb_sku_qty_map = {}
    for r in sb_records:
        s = clean_sku_key(r.get("barcode_sku"))
        if s:
            sb_sku_qty_map[s] = sb_sku_qty_map.get(s, 0) + safe_int_val(r.get("qty"), 1)

    # ==========================================================================
    # LANGKAH 4: PROSES BARANG YANG SUDAH MENJADI "INSTOCK" (MASUK KE NEED_SETUP)
    # ==========================================================================
    # Kelompokkan baris WAITING di Supabase per SKU
    waiting_by_sku = {}
    for r in waiting_in_sb:
        s = clean_sku_key(r.get("barcode_sku"))
        if s not in waiting_by_sku:
            waiting_by_sku[s] = []
        waiting_by_sku[s].append(r)

    processed_instock_keys = set()

    for instk in instock_movements:
        sku = instk["sku"]
        jam_instock_iso = (instk["dt_wib"] or now_wib).isoformat()
        lokasi_rak = instk["location"]
        event_key = f"{sku}_{instk['raw_time']}_{lokasi_rak}"

        if event_key in processed_instock_keys:
            continue
        processed_instock_keys.add(event_key)

        # KASUS A: Barangnya sebelumnya sudah tercatat sebagai WAITING di Supabase
        # -> Langsung update statusnya ke NEED_SETUP dan isi disappeared_at dengan jam INSTOCK!
        if sku in waiting_by_sku and waiting_by_sku[sku]:
            target_row = waiting_by_sku[sku].pop(0)
            patch_url = f"{SUPABASE_URL}/rest/v1/jezpro_instock_daily?id=eq.{target_row['id']}"
            patch_payload = {
                "status": "NEED_SETUP",
                "disappeared_at": jam_instock_iso,   # ✅ TERISI DENGAN JAM TANGGAL INSTOCK!
                "bin_code": lokasi_rak               # ✅ TERISI DENGAN LOKASI RAK AKTUAL!
            }
            res_patch = requests.patch(patch_url, headers=headers, json=patch_payload)
            if res_patch.status_code in [200, 204]:
                target_row["status"] = "NEED_SETUP"
                target_row["disappeared_at"] = jam_instock_iso
                target_row["bin_code"] = lokasi_rak
                need_setup_in_sb.append(target_row)
                print(f"   🚀 STATUS BERUBAH ➔ INSTOCK! SKU {sku} (Jam {instk['raw_time']}) di BIN [{lokasi_rak}] -> Masuk LIST SET UP (disappeared_at terisi)!")
            else:
                print(f"   ❌ Gagal update: {res_patch.text}")

        # KASUS B: Barangnya langsung terdeteksi INSTOCK di Jezpro dan belum ada di Supabase
        # -> Langsung insert sebagai NEED_SETUP lengkap dengan disappeared_at!
        elif sb_sku_qty_map.get(sku, 0) <= 0:
            new_inserts.append({
                "id": current_auto_id,
                "store_id": STORE_ID,
                "store_name": BRANCH_NAME,
                "barcode_sku": sku,
                "article_name": instk["article"],
                "bin_code": lokasi_rak,
                "qty": instk["qty"],
                "status": "NEED_SETUP",              # ✅ Langsung siap setup
                "invoice": instk["invoice"],
                "sync_date": today_date,
                "created_at": jam_instock_iso,
                "disappeared_at": jam_instock_iso,   # ✅ Terisi jam instock!
                "matched_mutasi_id": None,
                "setup_done_at": None
            })
            current_auto_id += 1
            print(f"   📥 Barang langsung INSTOCK terdeteksi: SKU {sku} (Jam {instk['raw_time']}) -> Masuk LIST SET UP!")

    # ==========================================================================
    # LANGKAH 5: BARANG YANG MASIH BERSTATUS "WAITING" (BELUM INSTOCK)
    # ==========================================================================
    temp_allocated = dict(sb_sku_qty_map)
    for wm in waiting_movements:
        s = wm["sku"]
        if temp_allocated.get(s, 0) <= 0:
            new_inserts.append({
                "id": current_auto_id,
                "store_id": STORE_ID,
                "store_name": BRANCH_NAME,
                "barcode_sku": s,
                "article_name": wm["article"],
                "bin_code": wm["location"],
                "qty": wm["qty"],
                "status": "WAITING OFFLINE",
                "invoice": wm["invoice"],
                "sync_date": today_date,
                "created_at": (wm["dt_wib"] or now_wib).isoformat(),
                "disappeared_at": None,              # Masih waiting, belum instock
                "matched_mutasi_id": None,
                "setup_done_at": None
            })
            current_auto_id += 1
        else:
            temp_allocated[s] -= wm["qty"]

    if new_inserts:
        res_ins = requests.post(f"{SUPABASE_URL}/rest/v1/jezpro_instock_daily", headers=headers, json=new_inserts)
        if res_ins.status_code in [200, 201]:
            print(f"   📥 Berhasil simpan {len(new_inserts)} record baru ke Supabase.")
            for ins in new_inserts:
                if ins["status"] == "NEED_SETUP":
                    need_setup_in_sb.append(ins)
        else:
            print(f"   ❌ Gagal insert: {res_ins.text}")

    # ==========================================================================
    # LANGKAH 6: VERIFIKASI MUTASI KE GL1-INSTOCK (DONE_SETUP)
    # ==========================================================================
    if need_setup_in_sb:
        mutasi_today = fetch_bin_history_today(session)
        mutasi_today = sorted(mutasi_today, key=lambda x: x["dt_wib"] or now_wib)

        for target in need_setup_in_sb:
            t_sku = clean_sku_key(target.get("barcode_sku"))
            t_bin_awal = clean_bin(target.get("bin_code"))
            t_qty = safe_int_val(target.get("qty"), 1)
            t_disappeared_dt = parse_wib_datetime(target.get("disappeared_at"))

            matched_mutasi = None

            for m in mutasi_today:
                m_id = m["mutasi_id"]
                if m_id in used_mutasi_ids:
                    continue

                sku_match = (m["sku"] == t_sku)
                bin_tujuan_match = ("GL1-INSTOCK" in m["bin_tujuan"] or "INSTOCK" in m["bin_tujuan"])
                qty_match = (m["qty_mts"] >= t_qty)

                if sku_match and bin_tujuan_match and qty_match:
                    matched_mutasi = m
                    break

            if matched_mutasi:
                used_mutasi_ids.add(matched_mutasi["mutasi_id"])
                patch_url = f"{SUPABASE_URL}/rest/v1/jezpro_instock_daily?id=eq.{target['id']}"
                res_done = requests.patch(patch_url, headers=headers, json={
                    "status": "DONE_SETUP",
                    "matched_mutasi_id": matched_mutasi["mutasi_id"],
                    "setup_done_at": matched_mutasi["raw_time"]
                })
                if res_done.status_code in [200, 204]:
                    print(f"   🎉 SELESAI MUTASI! SKU {t_sku} ➔ Selesai Setup ke GL1-INSTOCK ({matched_mutasi['raw_time']})!")

# ==============================================================================
# EKSEKUSI PROGRAM
# ==============================================================================
if __name__ == "__main__":
    print("=" * 65)
    print("🚀 MENJALANKAN SYNC INSTOCK DAILY (STOCK TRACKING BASED)")
    print("=" * 65)

    try:
        jez_session = create_jezpro_session()
        sync_cycle(jez_session)
        print("🏁 Siklus Sinkronisasi Selesai!")
    except Exception as e:
        print(f"❌ Error saat sinkronisasi: {e}")
        exit(1)
