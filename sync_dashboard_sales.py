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
SUPABASE_KEY = os.environ.get(
    "SUPABASE_KEY", 
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZhbnpzbWdoaGJlZmhoYWljcm9rIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODgxNTQzNDgsImV4cCI6MjEwMzczMDM0OH0.brCSOO9nHAUK8CxDWPperpJ--_NA_nwy5cO9OqGv3I0"
)

JEZPRO_EMAIL = os.environ.get("JEZPRO_EMAIL", "fajarbintang786@jez.co.id")
JEZPRO_PASSWORD = os.environ.get("JEZPRO_PASSWORD", "131199")

WIB = timezone(timedelta(hours=7))

HEADERS_SB = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates"
}

STORE_MASTER_MAP = {
    3: "JEZ SURABAYA",
    2: "JEZ MALANG",
    8: "JEZ SIDOARJO",
    5: "JEZ KEDIRI",
    40: "JEZ JEMBER",
    53: "JEZ SEMARANG",
    55: "HUB JAKARTA",
    30: "ONLINE HUB SURABAYA",
    20: "ONLINE HUB MALANG"
}

ALL_KNOWN_STORES = list(STORE_MASTER_MAP.values())

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

def parse_iso_wib(dt_str):
    if not dt_str:
        return datetime.now(WIB).isoformat()
    clean_s = strip_html(str(dt_str)).strip()[:19]
    for fmt in ("%d-%m-%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S", "%d-%m-%Y", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(clean_s, fmt)
            return dt.replace(tzinfo=WIB).isoformat()
        except Exception: pass
    return datetime.now(WIB).isoformat()

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
    res = session.get("https://jezpro.id/", timeout=25)
    soup = BeautifulSoup(res.text, "html.parser")
    token_tag = soup.find("input", {"name": "_token"})
    if not token_tag:
        raise Exception("Gagal mendapatkan CSRF Token Jezpro!")

    csrf_token = token_tag["value"]
    session.post("https://jezpro.id/user_login", data={
        "_token": csrf_token,
        "u_email": JEZPRO_EMAIL,
        "password": JEZPRO_PASSWORD
    }, timeout=25)
    
    session.get("https://jezpro.id/dashboards", timeout=25)
    session.headers.update({"X-CSRF-TOKEN": csrf_token})
    print("✅ Berhasil login ke Jezpro!")
    return session

def get_dynamic_store_map(session):
    try:
        res = session.get("https://jezpro.id/setup_lokasi_stok_v2", timeout=20)
        soup = BeautifulSoup(res.text, "html.parser")
        store_map = {}
        select_tag = soup.find("select", {"id": re.compile(r'st_id|store', re.I)}) or soup.find("select", {"name": re.compile(r'st_id|store', re.I)})
        if select_tag:
            for opt in select_tag.find_all("option"):
                val = opt.get("value", "").strip()
                txt = opt.get_text().strip().upper()
                if val.isdigit() and txt not in ["PILIH", "SEMUA", "ALL", "SELECT STORE"]:
                    store_map[int(val)] = txt
        if store_map:
            return store_map
    except Exception:
        pass
    return STORE_MASTER_MAP

# 🌟 FUNGSI INI DITAMBAHKAN KEMBALI AGAR TIDAK NAMEERROR:
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
# 📦 MODUL 1: SCRAPING MUTASI BIN (HANYA 7 HARI TERAKHIR DARI HARI INI)
# ==============================================================================
def fetch_bin_mutations_page(session, date_str: str, start_idx=0, length=300):
    url = "https://jezpro.id/bin_history_datatables"
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://jezpro.id/setup_lokasi_stok_v2"
    }
    params = {
        "draw": "1",
        "order[0][column]": "0",
        "order[0][dir]": "desc",
        "start": str(start_idx),
        "length": str(length),
        "search": "",
        "date": date_str  # Wajib berisi tanggal (misal: 22-11-2026 atau 2026-11-22)
    }
    try:
        res = session.get(url, params=params, headers=headers, timeout=30)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        print(f"      ⚠️ Gagal fetch mutasi tanggal {date_str}: {e}")
    return None

def parse_bin_mutation_row(raw_row, fallback_store=""):
    if not raw_row: return None

    # FORMAT OBJECT / DICTIONARY
    if isinstance(raw_row, dict):
        pmt_id = safe_int(raw_row.get("pmt_id") or raw_row.get("DT_RowIndex") or raw_row.get("id"))
        if not pmt_id: return None
        st_name = strip_html(raw_row.get("st_name", fallback_store)).upper()
        return {
            "pmt_id": pmt_id,
            "created_at": parse_iso_wib(raw_row.get("pm_created_at") or raw_row.get("created_at")),
            "store_name": st_name if st_name else fallback_store,
            "barcode_sku": strip_html(raw_row.get("ps_barcode", "-")).split('.')[0].strip().upper(),
            "article_name": strip_html(raw_row.get("article", "-")),
            "start_bin": strip_html(raw_row.get("start_bin", "-")).upper(),
            "end_bin": strip_html(raw_row.get("end_bin", "-")).upper(),
            "qty_moved": safe_int(raw_row.get("pmt_qty"), 1),
            "old_qty_start": safe_int(raw_row.get("pmt_old_qty")),
            "old_qty_end": safe_int(raw_row.get("pmt_old_qty_new")),
            "user_name": strip_html(raw_row.get("u_name", "-")),
            "notes": strip_html(raw_row.get("notes", "-")),
            "scraped_at": datetime.now(WIB).isoformat()
        }

    # FORMAT LIST / ARRAY (PERSIS SESUAI SCREENSHOT TABEL HISTORY SETUP)
    if isinstance(raw_row, (list, tuple)) and len(raw_row) >= 12:
        raw_no = safe_int(raw_row[0])
        st_name = strip_html(raw_row[4]).upper()
        sku_clean = strip_html(raw_row[3]).split('.')[0].strip().upper()
        tgl_iso = parse_iso_wib(raw_row[11])

        # Buat ID unik berbasis tanggal, toko, SKU, rak & nomor urut agar tidak bentrok
        tgl_num = tgl_iso[:10].replace('-', '')
        unique_hash = abs(hash(st_name + sku_clean + str(raw_row[5]) + str(raw_row[9]) + tgl_iso)) % 100000
        final_pmt_id = safe_int(f"{tgl_num}{unique_hash:05d}{raw_no % 1000:03d}")

        return {
            "pmt_id": final_pmt_id,
            "user_name": strip_html(raw_row[1]),
            "article_name": strip_html(raw_row[2]),
            "barcode_sku": sku_clean,
            "store_name": st_name if st_name else fallback_store,
            "start_bin": strip_html(raw_row[5]).upper(),
            "old_qty_start": safe_int(raw_row[6]),
            "qty_moved": safe_int(raw_row[7], 1),
            "old_qty_end": safe_int(raw_row[8]),
            "end_bin": strip_html(raw_row[9]).upper(),
            "notes": strip_html(raw_row[10]),
            "created_at": tgl_iso,
            "scraped_at": datetime.now(WIB).isoformat()
        }
    return None

def upsert_mutations_to_supabase(records: list):
    if not records:
        print("   ⚠️ Tidak ada data mutasi untuk disimpan.")
        return
    batch_size = 200
    total_saved = 0
    for i in range(0, len(records), batch_size):
        chunk = records[i:i + batch_size]
        url = f"{SUPABASE_URL}/rest/v1/jezpro_bin_mutations"
        res = requests.post(url, headers=HEADERS_SB, json=chunk, timeout=30)
        if res.status_code in [200, 201]:
            total_saved += len(chunk)
        else:
            print(f"   ❌ Gagal simpan batch mutasi {i}: {res.status_code}")
    print(f"   ✅ [SUPABASE] Sukses simpan {total_saved} baris mutasi ke jezpro_bin_mutations!")

def run_sync_all_branches_mutations(session):
    """
    🌟 Mengambil mutasi untuk SEMUA CABANG khusus 7 HARI TERAKHIR dari hari ini.
    Penarikan dilakukan per tanggal agar Jezpro merespons data dengan akurat.
    """
    now_wib = datetime.now(WIB)
    cutoff_dt = (now_wib - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    print(f"\n📦 [{now_wib.strftime('%H:%M:%S')}] Memulai Scraping Mutasi BIN (7 Hari Terakhir):")
    print(f"   ⏳ Rentang: {cutoff_dt.strftime('%d-%m-%Y')} s/d {now_wib.strftime('%d-%m-%Y')}")

    total_mutations = []

    # Loop 7 hari ke belakang (mulai dari hari ini mundur ke H-6)
    for day_offset in range(7):
        target_date = now_wib - timedelta(days=day_offset)
        d_dmy = target_date.strftime("%d-%m-%Y")  # Format web: 22-11-2026
        d_iso = target_date.strftime("%Y-%m-%d")  # Format alternatif: 2026-11-22
        
        print(f"   📅 Mengambil mutasi tanggal: {d_dmy}...")
        daily_records = []

        # Paginate jika ada lebih dari 300 transaksi per hari
        for page in range(10):
            start_idx = page * 300
            # Coba format DD-MM-YYYY terlebih dahulu
            raw_res = fetch_bin_mutations_page(session, date_str=d_dmy, start_idx=start_idx, length=300)
            
            # Jika kosong, fallback ke format YYYY-MM-DD
            if not raw_res or not raw_res.get("data"):
                raw_res = fetch_bin_mutations_page(session, date_str=d_iso, start_idx=start_idx, length=300)

            if not raw_res or not isinstance(raw_res, dict):
                break

            data_rows = raw_res.get("data", [])
            if not data_rows:
                break

            for item in data_rows:
                parsed = parse_bin_mutation_row(item)
                if parsed:
                    daily_records.append(parsed)

            if len(data_rows) < 300:
                break
            time.sleep(0.15)

        print(f"         -> Ditemukan {len(daily_records)} mutasi.")
        total_mutations.extend(daily_records)

    upsert_mutations_to_supabase(total_mutations)

# ==============================================================================
# 💰 MODUL 2: SCRAPING NET SALES UNTUK SEMUA CABANG (TETAP SAMA)
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
        print(f"      ⚠️ Gagal fetch sales {store_name}: {e}")
    return None

def parse_single_store_data(raw_json, store_name: str, channel="ALL"):
    records = []
    now_iso = datetime.now(WIB).isoformat()
    if not raw_json or not isinstance(raw_json, dict):
        return records

    detail_table = raw_json.get("detail_table")
    if isinstance(detail_table, dict):
        detail_table = detail_table.get("data") or detail_table.get("rows") or []

    if isinstance(detail_table, list) and len(detail_table) > 0:
        for row in detail_table:
            if not isinstance(row, dict): continue
            date_val = None
            for d_k in ["DATE", "date", "tgl", "tanggal"]:
                if d_k in row:
                    date_val = extract_valid_date(row[d_k])
                    if date_val: break
            if not date_val: continue

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

def upsert_sales_to_supabase(records: list):
    if not records: return
    batch_size = 150
    total_saved = 0
    for i in range(0, len(records), batch_size):
        chunk = records[i:i + batch_size]
        url = f"{SUPABASE_URL}/rest/v1/jezpro_daily_net_sales"
        res = requests.post(url, headers=HEADERS_SB, json=chunk, timeout=25)
        if res.status_code in [200, 201]:
            total_saved += len(chunk)
    print(f"   ✅ [SUPABASE] Sukses simpan {total_saved} baris data sales!")

def run_sync_all_branches_sales(session, full_history=False):
    now_wib = datetime.now(WIB)
    store_list = get_store_list_from_page(session)

    if full_history:
        current_year, current_month = 2026, 9
        end_year, end_month = now_wib.year, now_wib.month
        print(f"\n🏢 [SALES] Full Sync Semua Cabang: Sept 2026 s/d {now_wib.strftime('%Y-%m-%d')}")
    else:
        current_year, current_month = now_wib.year, now_wib.month
        end_year, end_month = now_wib.year, now_wib.month
        print(f"\n🏢 [SALES] Hourly Sync Semua Cabang ({now_wib.strftime('%B %Y')})")

    while (current_year < end_year) or (current_year == end_year and current_month <= end_month):
        start_date = f"{current_year}-{current_month:02d}-01"
        if current_year == now_wib.year and current_month == now_wib.month:
            end_date = now_wib.strftime("%Y-%m-%d")
        else:
            last_day = calendar.monthrange(current_year, current_month)[1]
            end_date = f"{current_year}-{current_month:02d}-{last_day:02d}"

        print(f"   📅 Sales Periode: {start_date} s/d {end_date} ({len(store_list)} Cabang)")
        month_records = []
        for idx, store in enumerate(store_list, 1):
            raw_data = fetch_metrics_single_store(session, start_date, end_date, store)
            if raw_data:
                store_rows = parse_single_store_data(raw_data, store, channel="ALL")
                month_records.extend(store_rows)
            time.sleep(0.1)

        upsert_sales_to_supabase(month_records)

        if current_month == 12:
            current_month = 1
            current_year += 1
        else:
            current_month += 1

# ==============================================================================
# SIKLUS UTAMA / SCHEDULER SETIAP 1 JAM (DAEMON LOOP)
# ==============================================================================
def execute_master_sync(is_first_cycle=False):
    print("\n" + "=" * 70)
    print(f"⏰ MEMULAI SIKLUS SYNC ALL CABANG: {datetime.now(WIB).strftime('%d-%m-%Y %H:%M:%S')} WIB")
    print("=" * 70)

    try:
        session = create_jezpro_session()

        # 1. Tarik Mutasi BIN Semua Cabang (7 Hari Terakhir)
        run_sync_all_branches_mutations(session)

        # 2. Tarik Net Sales Semua Cabang (Sept 2026 jika first_cycle)
        run_sync_all_branches_sales(session, full_history=is_first_cycle)

        print(f"\n🎉 [SELESAI] Semua data cabang berhasil di-sync pukul {datetime.now(WIB).strftime('%H:%M:%S')} WIB.")
    except Exception as e:
        print(f"\n❌ Terjadi kesalahan pada siklus ini: {e}")

def start_hourly_scheduler():
    print("=" * 70)
    print("🚀 JEZPRO ALL-BRANCH MASTER SCRAPER WORKER")
    print("   Target 1: Mutasi BIN SEMUA CABANG (HANYA 7 HARI TERAKHIR) -> public.jezpro_bin_mutations")
    print("   Target 2: Net Sales SEMUA CABANG (SEPT 2026 ONWARDS)     -> public.jezpro_daily_net_sales")
    print("   Frekuensi: Otomatis Setiap 1 Jam (3600 Detik)")
    print("=" * 70)

    first_run = True
    while True:
        execute_master_sync(is_first_cycle=first_run)
        first_run = False

        sleep_seconds = 3600
        next_run = datetime.now(WIB) + timedelta(seconds=sleep_seconds)
        print(f"💤 Tidur 1 jam. Siklus berikutnya dijadwalkan pukul: {next_run.strftime('%H:%M:%S')} WIB\n")
        time.sleep(sleep_seconds)

if __name__ == "__main__":
    start_hourly_scheduler()