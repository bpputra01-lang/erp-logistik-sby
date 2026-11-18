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
    "Prefer": "resolution=merge-duplicates"  # UPSERT otomatis
}

# Daftar default seluruh cabang/store (Offline & Online)
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
# HELPER & CLEANER
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

    res_login = session.post("https://jezpro.id/user_login", data={
        "_token": token_tag["value"],
        "u_email": JEZPRO_EMAIL,
        "password": JEZPRO_PASSWORD
    }, timeout=20)
    
    # Inisialisasi route dashboard
    session.get("https://jezpro.id/dashboards", timeout=20)
    print("✅ Berhasil login ke Jezpro!")
    return session

def get_store_list_from_page(session):
    """Mendeteksi seluruh opsi cabang yang tersedia di dropdown dashboard"""
    try:
        res = session.get("https://jezpro.id/dashboards", timeout=20)
        soup = BeautifulSoup(res.text, "html.parser")
        stores = []
        # Cari elemen select store
        select_tag = soup.find("select", {"id": re.compile(r'store', re.I)}) or soup.find("select", {"name": re.compile(r'store', re.I)})
        if select_tag:
            for opt in select_tag.find_all("option"):
                txt = opt.get_text().strip()
                if txt and txt.upper() not in ["PILIH", "ALL", "SEMUA", "SELECT STORE"]:
                    stores.append(txt)
        if stores:
            return list(dict.fromkeys(stores))
    except Exception as e:
        print(f"⚠️ Gagal deteksi opsi store otomatis ({e}), menggunakan default store list.")
    return ALL_KNOWN_STORES

# ==============================================================================
# CORE SCRAPER: NET SALES DASHBOARD
# ==============================================================================
def fetch_dashboard_metrics(session, start_date: str, end_date: str, stores: list, metric="net_sales", channel="ALL"):
    """
    Menembak API https://jezpro.id/dashboards/metrics
    """
    url = "https://jezpro.id/dashboards/metrics"
    
    # Format parameter array stores[]=...
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
        print(f"❌ Respon gagal dari Jezpro (HTTP {res.status_code}): {res.text[:200]}")
        return None

    try:
        return res.json()
    except Exception as e:
        print(f"❌ Gagal parse JSON respon: {e}")
        return None

def parse_sales_payload(raw_json, channel="ALL"):
    """
    Memetakan response JSON ke bentuk list data harian yang siap di-upsert ke Supabase
    """
    records = []
    now_iso = datetime.now(WIB).isoformat()

    if not raw_json:
        return records

    # Skenario 1: Respons format Tabel (array object berisi tanggal dan kolom toko)
    # Contoh: [{"DATE": "2026-11-01", "ONLINE HUB SURABAYA": 35000000, ...}]
    table_data = raw_json.get("table") or raw_json.get("data")
    if isinstance(table_data, list) and len(table_data) > 0 and isinstance(table_data[0], dict):
        for row in table_data:
            date_val = row.get("DATE") or row.get("date") or row.get("tgl")
            if not date_val: continue
            
            for key, val in row.items():
                if key.upper() in ["DATE", "TOTAL", "TGL", "DT_ROWINDEX", "ID"]:
                    continue
                store_name = key.strip()
                sales_nominal = safe_int(val, 0)
                clean_id = f"{date_val}_{store_name.replace(' ', '_').upper()}"
                
                records.append({
                    "id": clean_id,
                    "date": date_val,
                    "store_name": store_name,
                    "net_sales": sales_nominal,
                    "channel": channel,
                    "metric_key": "net_sales",
                    "updated_at": now_iso
                })
        return records

    # Skenario 2: Respons format Chart (labels = tanggal, datasets = [ {label: 'Store A', data: [...]} ])
    chart_data = raw_json.get("chart") or raw_json
    labels = chart_data.get("labels") or []
    datasets = chart_data.get("datasets") or []

    if labels and datasets:
        for ds in datasets:
            store_name = ds.get("label", "UNKNOWN").strip()
            data_points = ds.get("data", [])
            for idx, date_label in enumerate(labels):
                val = data_points[idx] if idx < len(data_points) else 0
                clean_id = f"{date_label}_{store_name.replace(' ', '_').upper()}"
                records.append({
                    "id": clean_id,
                    "date": date_label,
                    "store_name": store_name,
                    "net_sales": safe_int(val, 0),
                    "channel": channel,
                    "metric_key": "net_sales",
                    "updated_at": now_iso
                })
        return records

    # Skenario 3: Respons format Dictionary langsung {"ONLINE HUB SURABAYA": {"2026-11-01": 10000}}
    if isinstance(raw_json, dict):
        for store_key, date_dict in raw_json.items():
            if isinstance(date_dict, dict):
                for d_key, v in date_dict.items():
                    clean_id = f"{d_key}_{store_key.replace(' ', '_').upper()}"
                    records.append({
                        "id": clean_id,
                        "date": d_key,
                        "store_name": store_key,
                        "net_sales": safe_int(v, 0),
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
        print("⚠️ Tidak ada data records yang akan disimpan.")
        return

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
# MAIN FUNCTION
# ==============================================================================
def run_sync_sales():
    jez = create_jezpro_session()

    # Hitung tanggal dari hari ke-1 bulan ini hingga akhir bulan
    now_wib = datetime.now(WIB)
    start_date = now_wib.strftime("%Y-%m-01")
    
    # Ambil hari terakhir di bulan ini (misal 30 atau 31)
    last_day = calendar.monthrange(now_wib.year, now_wib.month)[1]
    end_date = f"{now_wib.year}-{now_wib.month:02d}-{last_day:02d}"

    # Dapatkan seluruh store
    store_list = get_store_list_from_page(jez)
    print(f"🏢 Cabang terdaftar ({len(store_list)}): {', '.join(store_list)}")

    # Tarik API Net Sales
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
        print(f"📊 Berhasil mengekstrak {len(clean_records)} rincian baris data harian.")
        if clean_records:
            upsert_to_supabase(clean_records)
    else:
        print("❌ Gagal mendapatkan respon data dari Jezpro.")

if __name__ == "__main__":
    print("=" * 70)
    print("🚀 JEZPRO DASHBOARD NET SALES SCRAPER & SUPABASE SYNC")
    print("=" * 70)
    
    # Bisa langsung dijalankan sekali (One-off)
    run_sync_sales()

    # OPSI JIKA INGIN DIJALANKAN OTOMATIS TIAP 1 JAM (Uncomment jika perlu):
    # while True:
    #     print("\n⏳ Menunggu 1 jam untuk sinkronisasi berikutnya...")
    #     time.sleep(3600)
    #     try:
    #         run_sync_sales()
    #     except Exception as e:
    #         print(f"⚠️ Error: {e}")