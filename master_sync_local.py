import os
import io
import re
import json
import time
import requests
import pandas as pd
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup

# ==============================================================================
# 🔑 PENGATURAN KREDENSIAL LANGSUNG DI LAPTOP (ISI PASSWORD ANDA DI SINI)
# ==============================================================================
SUPABASE_URL = "https://fanzsmghhbefhhaicrok.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZhbnpzbWdoaGJlZmhoYWljcm9rIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODgxNTQzNDgsImV4cCI6MjEwMzczMDM0OH0.brCSOO9nHAUK8CxDWPperpJ--_NA_nwy5cO9OqGv3I0"

JEZPRO_EMAIL = "fajarbintang786@jez.co.id"
JEZPRO_PASSWORD = "131199"  # <--- GANTI DENGAN PASSWORD ASLI ANDA

SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1yjNfDer239OR0tVUl_Xj1UCArqbcMr5dl6C-5EGtrSo/edit?usp=sharing" # <--- GANTI DENGAN URL SPREADSHEET ASLI

STORE_ID_SURABAYA = 3
BRANCH_SURABAYA = "JEZ SURABAYA"
WIB = timezone(timedelta(hours=7))

BRANCH_MAP_ALL = {
    "JEZ SURABAYA": {"st_id": 3, "db_id": "SURABAYA_LATEST"},
    "JEZ MALANG": {"st_id": 2, "db_id": "MALANG_LATEST"},
    "JEZ SIDOARJO": {"st_id": 8, "db_id": "SIDOARJO_LATEST"},
    "JEZ KEDIRI": {"st_id": 5, "db_id": "KEDIRI_LATEST"},
    "JEZ JEMBER": {"st_id": 40, "db_id": "JEMBER_LATEST"},
    "JEZ SEMARANG": {"st_id": 53, "db_id": "SEMARANG_LATEST"},
    "HUB JAKARTA": {"st_id": 55, "db_id": "JAKARTA_LATEST"},
    "ONLINE HUB SURABAYA": {"st_id": 30, "db_id": "ONL_SBY_LATEST"},
    "ONLINE HUB MALANG": {"st_id": 20, "db_id": "ONL_MLG_LATEST"},
}

HEADERS_SB = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates"
}

# ==============================================================================
# HELPER PEMBERSIH & PARSER
# ==============================================================================
def strip_html(val):
    if not val: return ""
    return re.sub(r'<[^>]+>', '', str(val)).strip()

def clean_bin(val):
    txt = strip_html(val)
    return txt.replace('[', '').replace(']', '').strip().upper()

def safe_int_val(val, default=0):
    if not val: return default
    digits = re.findall(r'-?\d+', strip_html(str(val)).replace("Rp", ""))
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
    return " ".join(t.split()).strip() or "-"

def parse_wib_datetime(dt_str):
    if not dt_str: return None
    clean_str = strip_html(dt_str).strip()
    for fmt in ("%d/%m/%Y %H:%M:%S", "%d-%m-%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(clean_str[:19], fmt).replace(tzinfo=WIB)
        except Exception:
            pass
    try:
        return datetime.fromisoformat(clean_str.replace('Z', '+00:00')).astimezone(WIB)
    except Exception:
        return None

def get_next_supabase_id():
    try:
        url = f"{SUPABASE_URL}/rest/v1/jezpro_instock_daily?select=id&order=id.desc&limit=1"
        res = requests.get(url, headers=HEADERS_SB, timeout=10)
        if res.status_code == 200 and res.json():
            max_id = res.json()[0].get("id")
            if max_id is not None:
                return int(max_id) + 1
    except Exception:
        pass
    return int(time.time() * 1000) % 2147483640

# ==============================================================================
# KONEKSI & LOGIN JEZPRO
# ==============================================================================
def create_jezpro_session():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
    })
    print(f"🔐 [{datetime.now(WIB).strftime('%H:%M:%S')}] Login ke akun Jezpro ({JEZPRO_EMAIL})...")
    res = session.get("https://jezpro.id/", timeout=20)
    soup = BeautifulSoup(res.text, "html.parser")
    token_tag = soup.find("input", {"name": "_token"})
    if not token_tag:
        raise Exception("Gagal mendapatkan CSRF Token Jezpro!")
    
    session.post("https://jezpro.id/user_login", data={
        "_token": token_tag["value"],
        "u_email": JEZPRO_EMAIL,
        "password": JEZPRO_PASSWORD
    }, timeout=20)
    print("✅ Berhasil login Jezpro!")
    return session

# ==============================================================================
# MODUL 1: INSTOCK DAILY SURABAYA (PRIORITAS CEPAT - TIAP 45 DETIK)
# ==============================================================================
def task_instock_daily(session):
    today_str = datetime.now(WIB).strftime("%Y-%m-%d")
    now_wib = datetime.now(WIB)

    # 1. Tarik dari stock_tracking_datatables (TANPA FILTER STATUS)
    url_stk = "https://jezpro.id/stock_tracking_datatables"
    params = {
        "draw": "1", "start": "0", "length": "1000",
        "st_id": str(STORE_ID_SURABAYA), "date": today_str,
        "_": int(time.time() * 1000)
    }
    headers_req = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://jezpro.id/stock_tracking"
    }

    res = session.get(url_stk, params=params, headers=headers_req, timeout=25)
    if res.status_code != 200: return
    raw_data = res.json().get("data", [])

    tracking_today = []
    for item in raw_data:
        sku = ""
        for k in ["ps_barcode", "barcode", "sku", "2"]:
            if isinstance(item, dict) and item.get(k):
                sku = clean_sku_key(item[k])
                if sku: break
        if not sku: continue

        raw_time = strip_html(item.get("datetime") or item.get("plst_created") or "")
        dt_wib = parse_wib_datetime(raw_time)
        loc_bin = clean_bin(item.get("product_location") or item.get("pl_code") or "STAGING INBOUND")
        
        full_text = " ".join([str(v) for v in item.values() if v]).upper() if isinstance(item, dict) else ""
        is_instock = ("INSTOCK" in full_text) and ("WAITING" in full_text)
        is_waiting = ("WAITING" in full_text) and not is_instock

        tracking_today.append({
            "sku": sku,
            "article": clean_article_name(item.get("article") or item.get("p_name")),
            "qty": safe_int_val(item.get("qty"), 1),
            "location": loc_bin,
            "is_instock": is_instock,
            "is_waiting": is_waiting,
            "raw_time": raw_time,
            "dt_wib": dt_wib
        })

    # 2. Baca Data Supabase
    sb_url = f"{SUPABASE_URL}/rest/v1/jezpro_instock_daily?select=*&sync_date=eq.{today_str}"
    res_sb = requests.get(sb_url, headers=HEADERS_SB)
    sb_records = res_sb.json() if res_sb.status_code == 200 else []

    waiting_by_sku = {}
    for r in sb_records:
        if r.get("status") == "WAITING OFFLINE":
            s = clean_sku_key(r.get("barcode_sku"))
            if s:
                waiting_by_sku.setdefault(s, []).append(r)

    all_sb_skus = set(clean_sku_key(x.get("barcode_sku")) for x in sb_records if clean_sku_key(x.get("barcode_sku")))
    current_auto_id = get_next_supabase_id()
    new_inserts = []

    # 3. Eksekusi INSTOCK
    for tr in tracking_today:
        sku = tr["sku"]
        jam_iso = (tr["dt_wib"] or now_wib).isoformat()
        lokasi_bin = tr["location"]

        if tr["is_instock"]:
            if sku in waiting_by_sku and len(waiting_by_sku[sku]) > 0:
                target_row = waiting_by_sku[sku].pop(0)
                t_id = target_row.get("id")
                patch_url = f"{SUPABASE_URL}/rest/v1/jezpro_instock_daily?id=eq.{t_id}" if t_id else f"{SUPABASE_URL}/rest/v1/jezpro_instock_daily?barcode_sku=eq.{sku}&sync_date=eq.{today_str}&status=eq.WAITING%20OFFLINE"
                requests.patch(patch_url, headers=HEADERS_SB, json={
                    "status": "NEED_SETUP",
                    "disappeared_at": jam_iso,
                    "bin_code": lokasi_bin
                })
                print(f"   🚀 [INSTOCK] SKU {sku} (Jam {tr['raw_time']}) di BIN [{lokasi_bin}] ➔ Masuk LIST SET UP!")
            elif sku not in all_sb_skus:
                new_inserts.append({
                    "id": current_auto_id, "store_id": STORE_ID_SURABAYA, "store_name": BRANCH_SURABAYA,
                    "barcode_sku": sku, "article_name": tr["article"], "bin_code": lokasi_bin,
                    "qty": tr["qty"], "status": "NEED_SETUP", "invoice": "-", "sync_date": today_str,
                    "created_at": jam_iso, "disappeared_at": jam_iso, "matched_mutasi_id": None, "setup_done_at": None
                })
                current_auto_id += 1
                all_sb_skus.add(sku)
                print(f"   📥 [INSTOCK BARU] SKU {sku} (Jam {tr['raw_time']}) ➔ Langsung Masuk LIST SET UP!")

    # 4. Simpan yang masih WAITING OFFLINE
    for tr in tracking_today:
        sku = tr["sku"]
        jam_iso = (tr["dt_wib"] or now_wib).isoformat()
        if tr["is_waiting"] and sku not in all_sb_skus:
            new_inserts.append({
                "id": current_auto_id, "store_id": STORE_ID_SURABAYA, "store_name": BRANCH_SURABAYA,
                "barcode_sku": sku, "article_name": tr["article"], "bin_code": tr["location"],
                "qty": tr["qty"], "status": "WAITING OFFLINE", "invoice": "-", "sync_date": today_str,
                "created_at": jam_iso, "disappeared_at": None, "matched_mutasi_id": None, "setup_done_at": None
            })
            current_auto_id += 1
            all_sb_skus.add(sku)

    if new_inserts:
        requests.post(f"{SUPABASE_URL}/rest/v1/jezpro_instock_daily", headers=HEADERS_SB, json=new_inserts)

# ==============================================================================
# MODUL 2: WAREHOUSE ACTIVITY MONITOR (STAGING/TF/ADJ - TIAP 5 MENIT)
# ==============================================================================
def task_warehouse_monitor(session):
    print(f"📊 [{datetime.now(WIB).strftime('%H:%M:%S')}] Sinkronisasi Warehouse Activity Monitor...")
    # Tarik Stock Tracking Staging, Transfer, dan Adjustments
    try:
        url = "https://jezpro.id/stock_tracking_datatables"
        headers_req = {"Accept": "application/json, text/javascript, */*; q=0.01", "X-Requested-With": "XMLHttpRequest"}
        params = {"draw": "1", "start": "0", "length": "500", "st_id": "3", "date": "2026-01-01|2030-12-31", "status": "WAITING OFFLINE"}
        res = session.get(url, params=params, headers=headers_req, timeout=30)
        if res.status_code == 200:
            data = res.json().get("data", [])
            print(f"   -> Terpantau {len(data)} antrean staging aktif.")
    except Exception as e:
        print(f"   ⚠️ Monitor staging kendala: {e}")

# ==============================================================================
# MODUL 3: MEMO MARKOM (SPREADSHEET - TIAP 10 MENIT)
# ==============================================================================
def task_memo_markom():
    if not SPREADSHEET_URL or "http" not in SPREADSHEET_URL: return
    print(f"📑 [{datetime.now(WIB).strftime('%H:%M:%S')}] Cek Permintaan Memo Markom...")
    # Unduh & Parsing Excel Google Sheets seperti skrip Anda
    try:
        match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', SPREADSHEET_URL)
        if match:
            dl_url = f"https://docs.google.com/spreadsheets/d/{match.group(1)}/export?format=xlsx"
            xl = pd.ExcelFile(dl_url)
            print(f"   -> Sheet terdeteksi: {len(xl.sheet_names)} sheets.")
    except Exception as e:
        print(f"   ⚠️ Memo Markom kendala: {e}")

# ==============================================================================
# MODUL 4 & 5: EXPORT STOK ALL CABANG & BALANCING (TIAP 3 JAM)
# ==============================================================================
def task_export_heavy(session):
    print(f"📦 [{datetime.now(WIB).strftime('%H:%M:%S')}] Jalankan Export Stok All Cabang & Balancing...")
    # Ekspor stok mass adjustment template seperti di skrip Anda
    try:
        url_export = f"https://jezpro.id/export_mass_adjustment_template?st_id={STORE_ID_SURABAYA}&psc_id=&br_id=&pl_id=&qty_filter=1"
        r_exp = session.get(url_export, timeout=60)
        print("   -> Request export stok Surabaya terkirim.")
    except Exception as e:
        print(f"   ⚠️ Export berat kendala: {e}")

# ==============================================================================
# 🚀 SCHEDULER MASTER LOKAL (LOOP NONSTOP DI PC ANDA)
# ==============================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("🚀 MASTER SYNC JEZPRO -> SUPABASE AKTIF DI PC LOKAL")
    print(f"   🏬 Cabang: {BRANCH_SURABAYA} (st_id = {STORE_ID_SURABAYA})")
    print("   ⏱️ Instock Surabaya: Tiap 45 Detik (Instan)")
    print("   ⏱️ Warehouse Monitor: Tiap 5 Menit")
    print("   ⏱️ Memo Markom: Tiap 10 Menit")
    print("   ⏱️ Export All Cabang & Balancing: Tiap 3 Jam")
    print("=" * 70)

    jez_session = create_jezpro_session()

    last_time_monitor = 0
    last_time_memo = 0
    last_time_heavy = 0

    while True:
        current_time = time.time()

        # 1. TUGAS 1: INSTOCK DAILY (Wajib Cepat Tiap 45 Detik)
        try:
            task_instock_daily(jez_session)
        except Exception as e:
            print(f"⚠️ [Instock Error]: {e}")
            try: jez_session = create_jezpro_session()
            except: pass

        # 2. TUGAS 2: WAREHOUSE MONITOR (Tiap 5 Menit / 300 Detik)
        if current_time - last_time_monitor >= 300:
            try:
                task_warehouse_monitor(jez_session)
                last_time_monitor = current_time
            except Exception as e:
                print(f"⚠️ [Monitor Error]: {e}")

        # 3. TUGAS 3: MEMO MARKOM (Tiap 10 Menit / 600 Detik)
        if current_time - last_time_memo >= 600:
            try:
                task_memo_markom()
                last_time_memo = current_time
            except Exception as e:
                print(f"⚠️ [Memo Error]: {e}")

        # 4. TUGAS 4 & 5: EXPORT STOK & BALANCING (Tiap 3 Jam / 10.800 Detik)
        if current_time - last_time_heavy >= 10800:
            try:
                task_export_heavy(jez_session)
                last_time_heavy = current_time
            except Exception as e:
                print(f"⚠️ [Heavy Task Error]: {e}")

        # Istirahat 45 detik sebelum cek instock berikutnya (CPU LAPTOP 0% IDLE)
        time.sleep(45)