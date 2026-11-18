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

# Daftar default cabang/store Jezpro
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
    """Memastikan hanya string tanggal YYYY-MM-DD yang lolos validasi"""
    if not val: return None
    s = strip_html(str(val)).strip()
    m = re.search(r'\b(20\d{2}[-/]\d{1,2}[-/]\d{1,2})\b', s)
    if m:
        try:
            d_str = m.group(1).replace('/', '-')
            return datetime.strptime(d_str, "%Y-%m-%d").strftime("%Y-%m-%d")
        except Exception:
            pass
    return None

# ==============================================================================
# AUTENTIKASI KE JEZPRO
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
# CORE SCRAPER: NET SALES
# ==============================================================================
def fetch_dashboard_metrics(session, start_date: str, end_date: str, stores: list, metric="net_sales", channel="ALL"):
    url = "https://jezpro.id/dashboards/metrics"
    params = [
        ("start_date", start_date),
        ("end_date", end_date),
        ("channel", channel),
        ("metric_key", metric),
    ]
    for s in stores:
        params.append(("stores[]", s))

    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://jezpro.id/dashboards"
    }

    print(f"📡 Mengambil data Jezpro: {start_date} s/d {end_date} ({len(stores)} Toko)...")
    res = session.get(url, params=params, headers=headers, timeout=30)
    
    if res.status_code != 200:
        print(f"❌ Respon gagal dari Jezpro (HTTP {res.status_code})")
        return None

    try:
        return res.json()
    except Exception as e:
        print(f"❌ Gagal parse JSON respon: {e}")
        return None

def parse_sales_payload(raw_json, channel="ALL"):
    unique_records = {}
    now_iso = datetime.now(WIB).isoformat()

    if not raw_json or not isinstance(raw_json, dict):
        return []

    # Daftar kata kunci yang bukan merupakan nama store
    META_KEYS = {
        "FILTERS", "FILTER", "PARAMS", "REQUEST", "SUMMARY", 
        "META", "TOTAL", "STATUS", "CODE", "STORES", "LABELS", 
        "DATASETS", "START_DATE", "END_DATE", "METRIC_KEY", "CHANNEL"
    }

    # Format 1: Format Datatable [{"DATE": "2026-11-01", "STORE": 1000}]
    table_data = raw_json.get("table") or raw_json.get("data")
    if isinstance(table_data, list) and len(table_data) > 0 and isinstance(table_data[0], dict):
        for row in table_data:
            date_raw = row.get("DATE") or row.get("date") or row.get("tgl")
            valid_date = extract_valid_date(date_raw)
            if not valid_date: continue
            
            for k, v in row.items():
                if k.upper() in ["DATE", "TOTAL", "TGL", "DT_ROWINDEX", "ID"] or k.upper() in META_KEYS:
                    continue
                store_name = k.strip()
                clean_id = f"{valid_date}_{store_name.replace(' ', '_').upper()}"
                unique_records[clean_id] = {
                    "id": clean_id,
                    "date": valid_date,
                    "store_name": store_name,
                    "net_sales": safe_int(v, 0),
                    "channel": channel,
                    "metric_key": "net_sales",
                    "updated_at": now_iso
                }
        return list(unique_records.values())

    # Format 2: Format Chart.js (labels & datasets)
    chart_data = raw_json.get("chart") or raw_json
    labels = chart_data.get("labels") or []
    datasets = chart_data.get("datasets") or []
    if labels and datasets and isinstance(labels, list) and isinstance(datasets, list):
        for ds in datasets:
            store_name = ds.get("label", "UNKNOWN").strip()
            data_points = ds.get("data", [])
            for idx, date_label in enumerate(labels):
                valid_date = extract_valid_date(date_label)
                if not valid_date: continue
                val = data_points[idx] if idx < len(data_points) else 0
                clean_id = f"{valid_date}_{store_name.replace(' ', '_').upper()}"
                unique_records[clean_id] = {
                    "id": clean_id,
                    "date": valid_date,
                    "store_name": store_name,
                    "net_sales": safe_int(val, 0),
                    "channel": channel,
                    "metric_key": "net_sales",
                    "updated_at": now_iso
                }
        if unique_records:
            return list(unique_records.values())

    # Format 3: Nested Dictionary (Store -> Date -> Sales ATAU Date -> Store -> Sales)
    for k_outer, v_outer in raw_json.items():
        if str(k_outer).upper() in META_KEYS:
            continue
        
        if isinstance(v_outer, dict):
            for k_inner, v_inner in v_outer.items():
                # Cek apakah inner key adalah tanggal
                d_val = extract_valid_date(k_inner)
                if d_val:
                    store_name = str(k_outer).strip()
                    val = v_inner
                else:
                    # Cek apakah outer key adalah tanggal
                    d_val = extract_valid_date(k_outer)
                    if d_val:
                        store_name = str(k_inner).strip()
                        val = v_inner
                    else:
                        continue  # Bukan pasangan tanggal dan sales

                if store_name.upper() in META_KEYS:
                    continue

                clean_id = f"{d_val}_{store_name.replace(' ', '_').upper()}"
                unique_records[clean_id] = {
                    "id": clean_id,
                    "date": d_val,
                    "store_name": store_name,
                    "net_sales": safe_int(val, 0),
                    "channel": channel,
                    "metric_key": "net_sales",
                    "updated_at": now_iso
                }

    return list(unique_records.values())

# ==============================================================================
# UPSERT SUPABASE
# ==============================================================================
def upsert_to_supabase(records: list):
    if not records:
        print("⚠️ Tidak ada data records yang valid untuk disimpan.")
        return

    # Tampilkan preview 2 data teratas untuk memastikan format tanggal sudah benar
    print(f"🔍 [PREVIEW DATA]")
    for sample in records[:2]:
        print(f"   -> ID: {sample['id']} | Date: {sample['date']} | Store: {sample['store_name']} | Net Sales: Rp{sample['net_sales']:,}")

    print(f"🚀 [SUPABASE] Mengirim {len(records)} baris data Net Sales...")
    batch_size = 100
    total_saved = 0

    for i in range(0, len(records), batch_size):
        chunk = records[i:i + batch_size]
        url = f"{SUPABASE_URL}/rest/v1/jezpro_daily_net_sales"
        res = requests.post(url, headers=HEADERS_SB, json=chunk, timeout=20)
        
        if res.status_code in [200, 201]:
            total_saved += len(chunk)
        else:
            print(f"❌ Gagal batch {i}: {res.status_code} - {res.text}")

    print(f"✅ [SUPABASE] Berhasil menyimpan/mengupdate total {total_saved} baris data!")

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
    print(f"🏢 Cabang terdaftar ({len(store_list)}): {', '.join(store_list)}")

    raw_response = fetch_dashboard_metrics(
        session=jez,
        start_date=start_date,
        end_date=end_date,
        stores=store_list,
        metric="net_sales",
        channel="ALL"
    )

    if raw_response:
        clean_records = parse_sales_payload(raw_response, channel="ALL")
        print(f"📊 Berhasil mengekstrak {len(clean_records)} rincian baris data harian yang valid.")
        if clean_records:
            upsert_to_supabase(clean_records)
    else:
        print("❌ Gagal mendapatkan respon data dari Jezpro.")

if __name__ == "__main__":
    print("=" * 70)
    print("🚀 JEZPRO DASHBOARD NET SALES SCRAPER & SUPABASE SYNC")
    print("=" * 70)
    run_sync_sales()