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
    """Mengubah format tanggal Jezpro (DD/MM/YYYY HH:MM:SS atau ISO) ke datetime WIB"""
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
    """Mengambil ID tertinggi agar tidak pernah null value pada kolom id"""
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
    """
    Menarik data dari https://jezpro.id/stock_tracking_datatables
    Filter: st_id = 3 (Surabaya), date = hari ini, status = WAITING OFFLINE
    """
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
    """Menarik riwayat mutasi untuk mencocokkan mutasi ke GL1-INSTOCK"""
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
# SINKRONISASI SUPABASE (COMPARE STOCK TRACKING DENGAN VALIDASI JAM KETAT)
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

    # 1. BERSIHKAN DATA SEBELUM HARI INI
    try:
        cleanup_url = f"{SUPABASE_URL}/rest/v1/jezpro_instock_daily?sync_date=lt.{today_date}"
        requests.delete(cleanup_url, headers=headers)
    except Exception as e:
        print(f"⚠️ Gagal membersihkan data lama: {e}")

    # 2. AMBIL DATA HARI INI DARI SUPABASE
    sb_url = f"{SUPABASE_URL}/rest/v1/jezpro_instock_daily?select=*&sync_date=eq.{today_date}"
    res_sb = requests.get(sb_url, headers=headers)
    sb_records = res_sb.json() if res_sb.status_code == 200 else []

    # Kelompokkan data Supabase berdasarkan status
    waiting_in_sb = [x for x in sb_records if x.get("status") == "WAITING OFFLINE" and clean_sku_key(x.get("barcode_sku"))]
    need_setup_in_sb = [x for x in sb_records if x.get("status") == "NEED_SETUP" and clean_sku_key(x.get("barcode_sku"))]
    done_setup_in_sb = [x for x in sb_records if x.get("status") == "DONE_SETUP" and clean_sku_key(x.get("barcode_sku"))]

    used_mutasi_ids = set(str(d.get("matched_mutasi_id")) for d in done_setup_in_sb if d.get("matched_mutasi_id"))

    # 3. TARIK DATA DARI STOCK TRACKING JEZPRO HARI INI
    tracking_today = fetch_stock_tracking_today(session)

    # Pisahkan antara yang masih WAITING dengan yang sudah berubah jadi INSTOCK
    instock_movements = []
    waiting_movements = []

    for tr in tracking_today:
        if tr["status"] == "INSTOCK" or "INSTOCK" in tr["status"]:
            instock_movements.append(tr)
        else:
            waiting_movements.append(tr)

    # Urutkan secara kronologis (waktu paling awal duluan)
    instock_movements = sorted(instock_movements, key=lambda x: x["dt_wib"] or now_wib)
    waiting_movements = sorted(waiting_movements, key=lambda x: x["dt_wib"] or now_wib)

    # ID generator agar tidak terjadi error NOT NULL pada kolom id
    current_auto_id = get_next_supabase_id(headers)
    new_inserts = []

    # Kunci pelacak kuantitas yang sudah tercatat di Supabase
    sb_sku_qty_map = {}
    for r in sb_records:
        s = clean_sku_key(r.get("barcode_sku"))
        if s:
            sb_sku_qty_map[s] = sb_sku_qty_map.get(s, 0) + safe_int_val(r.get("qty"), 1)

    # ==========================================================================
    # LANGKAH 4: PROSES BARANG YANG MASIH WAITING OFFLINE KE SUPABASE
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
                "disappeared_at": None,
                "matched_mutasi_id": None,
                "setup_done_at": None
            })
            current_auto_id += 1
        else:
            temp_allocated[s] -= wm["qty"]

    # ==========================================================================
    # LANGKAH 5: DETEKSI PERUBAHAN STATUS MENJADI "INSTOCK"
    # DENGAN VALIDASI WAKTU KETAT (Jam Instock >= Jam Waiting)
    # ==========================================================================
    # Kelompokkan WAITING yang ada di Supabase per SKU secara FIFO
    waiting_by_sku = {}
    for r in waiting_in_sb:
        s = clean_sku_key(r.get("barcode_sku"))
        if s not in waiting_by_sku:
            waiting_by_sku[s] = []
        waiting_by_sku[s].append(r)

    used_instock_keys = set()

    # A. Cek barang di Supabase yang statusnya berubah dari WAITING -> INSTOCK
    for instk in instock_movements:
        sku = instk["sku"]
        dt_instock = instk["dt_wib"] or now_wib
        loc_instock = instk["location"]
        event_key = f"{sku}_{instk['raw_time']}_{loc_instock}"

        if event_key in used_instock_keys:
            continue

        if sku in waiting_by_sku and waiting_by_sku[sku]:
            # Ambil data waiting tertua
            target_wait = waiting_by_sku[sku][0]
            dt_wait = parse_wib_datetime(target_wait.get("created_at")) or now_wib

            # 🛑 VALIDASI JAM KETAT: Jam Instock WAJIB >= Jam Waiting (Toleransi mundur maks 30 detik)
            time_diff_sec = (dt_instock - dt_wait).total_seconds()
            if time_diff_sec >= -30:
                # MATCH! Barang ini telah di-instock, ubah status ke NEED_SETUP & isi disappeared_at
                used_instock_keys.add(event_key)
                waiting_by_sku[sku].pop(0)

                iso_instock = dt_instock.isoformat()
                patch_url = f"{SUPABASE_URL}/rest/v1/jezpro_instock_daily?id=eq.{target_wait['id']}"
                patch_payload = {
                    "status": "NEED_SETUP",
                    "disappeared_at": iso_instock,      # ✅ TERISI DENGAN JAM TRANSAKSI INSTOCK
                    "bin_code": loc_instock             # ✅ DIUPDATE KE LOKASI RAK BARU (cth: GL2-A-LOG-F4-2)
                }
                res_patch = requests.patch(patch_url, headers=headers, json=patch_payload)

                if res_patch.status_code in [200, 204]:
                    target_wait["status"] = "NEED_SETUP"
                    target_wait["disappeared_at"] = iso_instock
                    target_wait["bin_code"] = loc_instock
                    need_setup_in_sb.append(target_wait)
                    print(f"   🚀 STATUS BERUBAH ➔ INSTOCK! SKU {sku} (Jam {instk['raw_time']}) di BIN [{loc_instock}] masuk ke LIST SET UP (NEED_SETUP)!")
                else:
                    print(f"   ❌ Gagal update ke NEED_SETUP: {res_patch.text}")

    # B. Jika ada barang di Stock Tracking yang statusnya SUDAH "INSTOCK" (asal WAITING)
    # tapi belum pernah tercatat sama sekali di Supabase hari ini -> Langsung masukkan ke NEED_SETUP
    for instk in instock_movements:
        sku = instk["sku"]
        event_key = f"{sku}_{instk['raw_time']}_{instk['location']}"
        if event_key in used_instock_keys:
            continue

        # Cek apakah SKU ini sudah tercover di Supabase
        if sb_sku_qty_map.get(sku, 0) <= 0:
            used_instock_keys.add(event_key)
            dt_instk = instk["dt_wib"] or now_wib
            iso_instk = dt_instk.isoformat()

            new_inserts.append({
                "id": current_auto_id,
                "store_id": STORE_ID,
                "store_name": BRANCH_NAME,
                "barcode_sku": sku,
                "article_name": instk["article"],
                "bin_code": instk["location"],
                "qty": instk["qty"],
                "status": "NEED_SETUP",                 # ✅ Langsung siap di-setup
                "invoice": instk["invoice"],
                "sync_date": today_date,
                "created_at": iso_instk,
                "disappeared_at": iso_instk,            # ✅ Jam instock terisi
                "matched_mutasi_id": None,
                "setup_done_at": None
            })
            current_auto_id += 1
            print(f"   📥 Barang langsung INSTOCK terdeteksi: SKU {sku} (Jam {instk['raw_time']}) ➔ Masuk LIST SET UP!")

    # Kirim insert jika ada data baru
    if new_inserts:
        res_ins = requests.post(f"{SUPABASE_URL}/rest/v1/jezpro_instock_daily", headers=headers, json=new_inserts)
        if res_ins.status_code in [200, 201]:
            print(f"   📥 Berhasil simpan {len(new_inserts)} record baru ke Supabase.")
            # Tambahkan ke need_setup_in_sb agar bisa dicocokkan ke mutasi jika ada
            for ins in new_inserts:
                if ins["status"] == "NEED_SETUP":
                    need_setup_in_sb.append(ins)
        else:
            print(f"   ❌ Gagal insert: {res_ins.text}")

    # ==========================================================================
    # LANGKAH 6: VERIFIKASI SELESAI MUTASI KE GL1-INSTOCK (DONE_SETUP)
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
                # Bin asal cocok dengan lokasi instock barang
                bin_awal_match = (m["bin_awal"] == t_bin_awal or t_bin_awal in m["bin_awal"] or m["bin_awal"] in ["STAGING INBOUND", "WAITING OFFLINE"])
                # Bin tujuan adalah GL1-INSTOCK
                bin_tujuan_match = ("GL1-INSTOCK" in m["bin_tujuan"] or "INSTOCK" in m["bin_tujuan"])
                qty_match = (m["qty_mts"] >= t_qty)

                # Validasi jam: Mutasi ke GL1-INSTOCK harus sesudah jam INSTOCK
                time_valid = True
                if t_disappeared_dt and m["dt_wib"]:
                    time_diff = (m["dt_wib"] - t_disappeared_dt).total_seconds()
                    if time_diff < -120:  # Toleransi 2 menit
                        time_valid = False

                if sku_match and bin_awal_match and bin_tujuan_match and qty_match and time_valid:
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
