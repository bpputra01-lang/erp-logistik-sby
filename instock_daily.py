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
# HELPER PEMBERSIH & PARSER
# ==============================================================================
def strip_html(val):
    if not val: return ""
    return re.sub(r'<[^>]+>', '', str(val)).strip()

def safe_int_val(val, default=0):
    if not val: return default
    digits = re.findall(r'-?\d+', strip_html(val))
    return int(digits[0]) if digits else default

def clean_sku_key(sku):
    """Normalisasi SKU agar seragam (tanpa .0, spasi, atau karakter aneh)"""
    if not sku: return ""
    s = str(sku).strip().upper()
    if s.endswith('.0'): s = s[:-2]
    return s if s not in ["-", "NAN", "NONE", "NULL", ""] else ""

def clean_article_name(raw_text):
    """Membersihkan artikel agar tidak ada kata WAITING OFFLINE / enter di dalamnya"""
    if not raw_text: return "-"
    t = strip_html(raw_text)
    t = re.sub(r'\b(WAITING OFFLINE|WAITING|REFUND|JEZ SURABAYA|Jml\s*:\s*\d+)\b', '', t, flags=re.IGNORECASE)
    t = " ".join(t.split()).strip()
    return t if t else "-"

def parse_wib_datetime(dt_str):
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
        dt = datetime.fromisoformat(clean_str.replace('Z', '+00:00'))
        return dt.astimezone(WIB)
    except Exception:
        return None

def extract_barcode_from_item(item):
    """Deteksi barcode cerdas dari berbagai kemungkinan key DataTables Jezpro"""
    # 1. Cek key umum
    for k in ["barcode", "ps_barcode", "p_barcode", "product_barcode", "pro_barcode", "sku", "item_code", "code"]:
        val = clean_sku_key(item.get(k))
        if val:
            return val

    # 2. Cek key bertipe angka / index kolom DataTables
    for k, v in item.items():
        if str(k).isdigit() or any(sub in str(k).lower() for sub in ["bar", "sku", "code"]):
            val = clean_sku_key(strip_html(v))
            if val and len(val) >= 4 and not any(ign in val for ign in ["WAITING", "OFFLINE", "HTML", "SPAN"]):
                return val

    # 3. Cari pola angka barcode di dalam teks artikel / deskripsi
    raw_article = str(item.get("article") or "")
    match_digits = re.search(r'\b\d{6,14}\b', raw_article)
    if match_digits:
        return match_digits.group(0)

    return ""

def get_next_supabase_id(headers):
    """Mengambil ID tertinggi agar tidak melanggar not-null constraint pada kolom id"""
    try:
        url = f"{SUPABASE_URL}/rest/v1/jezpro_instock_daily?select=id&order=id.desc&limit=1"
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200 and res.json():
            max_id = res.json()[0].get("id")
            if max_id is not None:
                return int(max_id) + 1
    except Exception as e:
        print(f"⚠️ Gagal fetch max_id: {e}")
    # Fallback ID unik berbasis epoch millisecond dalam batas int4 positif
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
# FETCH DATA HELPER & MUTASI
# ==============================================================================
def fetch_helper_jezpro(session):
    url = "https://jezpro.id/scan_product_in_datatables"
    params = {
        "draw": "1",
        "start": "0",
        "length": "1000",
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
        res = session.get(url, params=params, headers=headers, timeout=20)
        if res.status_code == 200:
            data = res.json().get("data", [])
            clean_list = []
            for item in data:
                raw_bin = strip_html(item.get("product_location") or "[WAITING OFFLINE]").upper()
                clean_bin = raw_bin.replace('[', '').replace(']', '').strip()
                
                sku = extract_barcode_from_item(item)
                article = clean_article_name(item.get("article"))
                
                # Hanya simpan jika SKU valid
                if sku:
                    clean_list.append({
                        "barcode_sku": sku,
                        "article_name": article,
                        "bin_code": clean_bin if clean_bin else "STAGING INBOUND",
                        "qty": safe_int_val(item.get("qty"), 1),
                        "invoice": strip_html(item.get("invoice") or "")
                    })
            return clean_list
    except Exception as e:
        print(f"⚠️ Gagal fetch helper: {e}")
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
# SINKRONISASI SUPABASE (DENGAN GENERASI ID OTOMATIS)
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

    # Kelompokkan data Supabase berdasarkan status (abaikan baris jika barcode kosong)
    waiting_in_sb = [x for x in sb_records if x.get("status") == "WAITING OFFLINE" and clean_sku_key(x.get("barcode_sku"))]
    need_setup_in_sb = [x for x in sb_records if x.get("status") == "NEED_SETUP" and clean_sku_key(x.get("barcode_sku"))]
    done_setup_in_sb = [x for x in sb_records if x.get("status") == "DONE_SETUP" and clean_sku_key(x.get("barcode_sku"))]

    used_mutasi_ids = set(str(d.get("matched_mutasi_id")) for d in done_setup_in_sb if d.get("matched_mutasi_id"))

    # 3. TARIK DATA DARI HELPER JEZPRO SAAT INI
    jez_helper = fetch_helper_jezpro(session)

    # Hitung jumlah item per SKU yang masih ada di Jezpro Helper saat ini
    jez_sku_counts = {}
    for it in jez_helper:
        s = it["barcode_sku"]
        jez_sku_counts[s] = jez_sku_counts.get(s, 0) + it.get("qty", 1)

    # Hitung jumlah item per SKU yang sudah tercatat di Supabase hari ini
    sb_sku_total_active = {}
    for r in sb_records:
        s = clean_sku_key(r.get("barcode_sku"))
        if s:
            sb_sku_total_active[s] = sb_sku_total_active.get(s, 0) + safe_int_val(r.get("qty"), 1)

    # 4. INSERT BARANG BARU (DENGAN ID TIDAK BOLEH NULL)
    new_inserts = []
    temp_allocated = dict(sb_sku_total_active)
    
    # Ambil start ID berikutnya agar tidak melanggar not-null constraint
    current_auto_id = get_next_supabase_id(headers)

    for it in jez_helper:
        s = it["barcode_sku"]
        current_in_sb = temp_allocated.get(s, 0)

        # Jika item di helper belum tercatat di database, insert!
        if current_in_sb <= 0:
            new_inserts.append({
                "id": current_auto_id,                 # ✅ ID DIJAMIN ADA & TIDAK NULL
                "store_id": STORE_ID,                   # ✅ Terisi otomatis
                "store_name": BRANCH_NAME,               # ✅ Terisi otomatis
                "barcode_sku": s,
                "article_name": it["article_name"],
                "bin_code": it["bin_code"],
                "qty": it["qty"],
                "status": "WAITING OFFLINE",
                "invoice": it.get("invoice", ""),
                "sync_date": today_date,
                "created_at": now_wib.isoformat(),
                "disappeared_at": None,
                "matched_mutasi_id": None,
                "setup_done_at": None
            })
            current_auto_id += 1
        else:
            temp_allocated[s] -= it.get("qty", 1)

    if new_inserts:
        res_ins = requests.post(f"{SUPABASE_URL}/rest/v1/jezpro_instock_daily", headers=headers, json=new_inserts)
        if res_ins.status_code in [200, 201]:
            print(f"   📥 Berhasil insert {len(new_inserts)} barang baru ke antrean WAITING OFFLINE.")
        else:
            print(f"   ❌ Gagal insert data baru: {res_ins.text}")

    # ==========================================================================
    # 5. DETEKSI BARANG HILANG (UPDATE STATUS KE NEED_SETUP & ISI DISAPPEARED_AT)
    # ==========================================================================
    waiting_by_sku = {}
    for r in waiting_in_sb:
        s = clean_sku_key(r.get("barcode_sku"))
        if s:
            if s not in waiting_by_sku:
                waiting_by_sku[s] = []
            waiting_by_sku[s].append(r)

    now_iso = now_wib.isoformat()
    disappeared_count = 0

    for sku, records_list in waiting_by_sku.items():
        remain_in_helper = jez_sku_counts.get(sku, 0)
        total_waiting_sb = sum(safe_int_val(r.get("qty"), 1) for r in records_list)

        # Selisih = Barang yang sudah di-scan masuk / hilang dari Helper
        diff_disappeared = total_waiting_sb - remain_in_helper

        if diff_disappeared > 0:
            for r in records_list:
                if diff_disappeared <= 0:
                    break

                patch_url = f"{SUPABASE_URL}/rest/v1/jezpro_instock_daily?id=eq.{r['id']}"
                patch_payload = {
                    "status": "NEED_SETUP",
                    "disappeared_at": now_iso           # ✅ DISAPPEARED_AT TERISI WAKTU SCAN
                }
                res_patch = requests.patch(patch_url, headers=headers, json=patch_payload)

                if res_patch.status_code in [200, 204]:
                    disappeared_count += 1
                    diff_disappeared -= safe_int_val(r.get("qty"), 1)
                    r["status"] = "NEED_SETUP"
                    r["disappeared_at"] = now_iso
                    need_setup_in_sb.append(r)
                    print(f"   ⚠️ HILANG DARI HELPER ({now_wib.strftime('%H:%M:%S')}): SKU {sku} ➔ Status: NEED_SETUP (disappeared_at terisi)!")
                else:
                    print(f"   ❌ Gagal update ke NEED_SETUP: {res_patch.text}")

    # ==========================================================================
    # 6. COCOKKAN DENGAN RIWAYAT MUTASI (UPDATE STATUS KE DONE_SETUP)
    # ==========================================================================
    if need_setup_in_sb:
        mutasi_today = fetch_bin_history_today(session)
        mutasi_today = sorted(mutasi_today, key=lambda x: x["dt_wib"] or now_wib)

        for target in need_setup_in_sb:
            t_sku = clean_sku_key(target.get("barcode_sku"))
            t_bin_awal = str(target.get("bin_code", "")).strip().upper()
            t_qty = safe_int_val(target.get("qty"), 1)
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
                    print(f"   🎉 MUTASI MATCH! SKU {t_sku} ➔ Selesai Setup ke GL1-INSTOCK ({matched_mutasi['raw_time']})!")

# ==============================================================================
# EKSEKUSI PROGRAM
# ==============================================================================
if __name__ == "__main__":
    print("=" * 65)
    print("🚀 MENJALANKAN SYNC INSTOCK DAILY")
    print("=" * 65)

    try:
        jez_session = create_jezpro_session()
        sync_cycle(jez_session)
        print("🏁 Siklus Sinkronisasi Selesai!")
    except Exception as e:
        print(f"❌ Error saat sinkronisasi: {e}")
        exit(1)
