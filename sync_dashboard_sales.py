import os
import re
import json
import time
import calendar
import requests
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup

# ==============================================================================
# 🔑 KREDENSIAL & KONFIGURASI PUSAT
# ==============================================================================
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://fanzsmghhbefhhaicrok.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZhbnpzbWdoaGJlZmhoYWljcm9rIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODgxNTQzNDgsImV4cCI6MjEwMzczMDM0OH0.brCSOO9nHAUK8CxDWPperpJ--_NA_nwy5cO9OqGv3I0")

JEZPRO_EMAIL = os.environ.get("JEZPRO_EMAIL", "fajarbintang786@jez.co.id")
JEZPRO_PASSWORD = os.environ.get("JEZPRO_PASSWORD", "131199")

WIB = timezone(timedelta(hours=7))

HEADERS_SB = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates"
}

ALL_KNOWN_STORES = [
    "JEZ SURABAYA",
    "ONLINE HUB SURABAYA",
    "ONLINE SURABAYA",
    "JEZ MALANG",
    "ONLINE HUB MALANG",
    "JEZ KEDIRI",
    "JEZ JEMBER",
    "JEZ SIDOARJO",
    "JEZ SEMARANG",
    "HUB JAKARTA",
]

# ==============================================================================
# HELPER & VALIDATOR
# ==============================================================================
def strip_html(val):
    if not val: return ""
    return re.sub(r'<[^>]+>', '', str(val)).strip()

def safe_int(val, default=0):
    try:
        if val is None: return default
        if isinstance(val, (int, float)): return int(round(val))
        s = strip_html(str(val)).replace("Rp", "").replace(".", "").replace(",", ".").strip()
        return int(round(float(s)))
    except Exception:
        digits = re.findall(r'-?\d+', str(val))
        return int(digits[0]) if digits else default

def extract_valid_date(val):
    if not val: return None
    s = strip_html(str(val)).strip()
    m1 = re.search(r'\b(20\d{2}[-/]\d{1,2}[-/]\d{1,2})\b', s)
    if m1:
        try:
            return datetime.strptime(m1.group(1).replace('/', '-'), "%Y-%m-%d").strftime("%Y-%m-%d")
        except Exception: pass

    m2 = re.search(r'\b(\d{1,2}[-/]\d{1,2}[-/]20\d{2})\b', s)
    if m2:
        for fmt in ("%d-%m-%Y", "%d/%m/%Y"):
            try:
                return datetime.strptime(m2.group(1), fmt).strftime("%Y-%m-%d")
            except Exception: pass
    return None

# ==============================================================================
# LOGIN JEZPRO
# ==============================================================================
def create_jezpro_session():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://jezpro.id/dashboards"
    })
    print(f"🔐 [{datetime.now(WIB).strftime('%H:%M:%S')}] Login ke Jezpro ({JEZPRO_EMAIL})...")
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
    
    session.get("https://jezpro.id/dashboards", timeout=20)
    print("✅ Berhasil login ke Jezpro!")
    return session

def get_store_list_from_page(session):
    try:
        res = session.get("https://jezpro.id/dashboards", timeout=20)
        soup = BeautifulSoup(res.text, "html.parser")
        stores = []
        select_tag = soup.find("select", {"id": re.compile(r'store', re.I)}) or soup.find("select", {"name": re.compile(r'store', re.I)})
        if select_tag:
            for opt in select_tag.find_all("option"):
                txt = opt.get_text().strip()
                if txt and txt.upper() not in ["PILIH", "ALL", "SEMUA", "SELECT STORE"]:
                    stores.append(txt)
        if stores:
            return list(dict.fromkeys(stores))
    except Exception:
        pass
    return ALL_KNOWN_STORES

# ==============================================================================
# FETCH SINGLE STORE & PARSER
# ==============================================================================
def fetch_metrics_single_store(session, start_date: str, end_date: str, store_name: str, channel="ALL"):
    url = "https://jezpro.id/dashboards/metrics"
    params = [
        ("start_date", start_date),
        ("end_date", end_date),
        ("channel", channel),
        ("metric_key", "net_sales"),
        ("stores[]", store_name)
    ]

    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://jezpro.id/dashboards"
    }

    try:
        res = session.get(url, params=params, headers=headers, timeout=25)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        print(f"      ⚠️ Gagal fetch {store_name}: {e}")
    return None

def parse_single_store_data(raw_json, store_name: str, channel="ALL"):
    records = []
    now_iso = datetime.now(WIB).isoformat()
    if not raw_json or not isinstance(raw_json, dict):
        return records

    detail_table = raw_json.get("detail_table")
    if isinstance(detail_table, dict):
        detail_table = detail_table.get("data") or detail_table.get("rows") or []

    # 1. Parsing dari Detail Table
    if isinstance(detail_table, list) and len(detail_table) > 0:
        for row in detail_table:
            if not isinstance(row, dict): continue
            
            date_val = None
            for d_k in ["DATE", "date", "tgl", "tanggal"]:
                if d_k in row:
                    date_val = extract_valid_date(row[d_k])
                    if date_val: break
            if not date_val: continue

            # Karena hanya request 1 cabang, sales diambil dari kolom nama cabang atau kolom net_sales_total
            sales_val = 0
            if store_name in row:
                sales_val = safe_int(row[store_name])
            elif "net_sales_total" in row:
                sales_val = safe_int(row["net_sales_total"])
            else:
                for k, v in row.items():
                    if k.upper() not in ["DATE", "TANGGAL", "STOREADJ", "TOTAL", "ID"]:
                        sales_val = safe_int(v)
                        break

            clean_id = f"{date_val}_{store_name.replace(' ', '_').upper()}"
            records.append({
                "id": clean_id,
                "date": date_val,
                "store_name": store_name,
                "net_sales": sales_val,
                "channel": channel,
                "metric_key": "net_sales",
                "updated_at": now_iso
            })
        return records

    # 2. Cadangan: Parsing dari Detail Chart jika Table kosong
    detail_chart = raw_json.get("detail_chart") or {}
    labels = detail_chart.get("labels") or detail_chart.get("categories") or []
    series = detail_chart.get("series") or detail_chart.get("datasets") or []
    if labels and series:
        data_points = series[0].get("data") if len(series) > 0 else []
        for idx, lbl in enumerate(labels):
            date_val = extract_valid_date(lbl)
            if not date_val: continue
            val = data_points[idx] if idx < len(data_points) else 0
            clean_id = f"{date_val}_{store_name.replace(' ', '_').upper()}"
            records.append({
                "id": clean_id,
                "date": date_val,
                "store_name": store_name,
                "net_sales": safe_int(val),
                "channel": channel,
                "metric_key": "net_sales",
                "updated_at": now_iso
            })

    return records

# ==============================================================================
# UPSERT SUPABASE
# ==============================================================================
def upsert_to_supabase(records: list):
    if not records:
        print("⚠️ Tidak ada data untuk disimpan.")
        return

    print(f"\n🚀 [SUPABASE] Menyimpan total {len(records)} baris data per cabang...")
    batch_size = 150
    total_saved = 0

    for i in range(0, len(records), batch_size):
        chunk = records[i:i + batch_size]
        url = f"{SUPABASE_URL}/rest/v1/jezpro_daily_net_sales"
        res = requests.post(url, headers=HEADERS_SB, json=chunk, timeout=25)
        if res.status_code in [200, 201]:
            total_saved += len(chunk)
        else:
            print(f"❌ Gagal batch {i}: {res.status_code} - {res.text}")

    print(f"✅ [SUPABASE] Sukses! Berhasil menyimpan {total_saved} baris data per cabang!")

# ==============================================================================
# MAIN
# ==============================================================================
def run_sync_sales():
    jez = create_jezpro_session()

    now_wib = datetime.now(WIB)
    start_date = now_wib.strftime("%Y-%m-01")
    last_day = calendar.monthrange(now_wib.year, now_wib.month)[1]
    end_date = f"{now_wib.year}-{now_wib.month:02d}-{last_day:02d}"

    store_list = get_store_list_from_page(jez)
    print(f"\n🏢 Mengambil data detail untuk {len(store_list)} cabang:")
    print(f"   Periode: {start_date} s/d {end_date}\n")

    all_records = []

    for idx, store in enumerate(store_list, 1):
        print(f"   [{idx}/{len(store_list)}] 📡 Mengambil data: {store}...")
        raw_data = fetch_metrics_single_store(jez, start_date, end_date, store)
        if raw_data:
            store_rows = parse_single_store_data(raw_data, store, channel="ALL")
            all_records.extend(store_rows)
            print(f"         -> Ditemukan {len(store_rows)} data tanggal.")
        time.sleep(0.15)  # Jeda halus

    if all_records:
        upsert_to_supabase(all_records)
    else:
        print("❌ Tidak ada data yang berhasil diekstrak.")

if __name__ == "__main__":
    print("=" * 70)
    print("🚀 JEZPRO DASHBOARD NET SALES SCRAPER (PER BRANCH) -> SUPABASE")
    print("=" * 70)
    run_sync_sales()