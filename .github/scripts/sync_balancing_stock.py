import os
import io
import time
import json
import re
import requests
import pandas as pd
from datetime import datetime, timedelta, timezone
from bs4 import BeautifulSoup

# ==============================================================================
# KREDENSIAL & KONFIGURASI
# ==============================================================================
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://fanzsmghhbefhhaicrok.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
JEZPRO_EMAIL = os.environ.get("JEZPRO_EMAIL", "fajarbintang786@jez.co.id")
JEZPRO_PASSWORD = os.environ.get("JEZPRO_PASSWORD", "")

# Target Khusus Surabaya
SURABAYA_ST_ID = 3
BRANCH_NAME = "JEZ SURABAYA"

HEADERS_SB = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates"
}

# ==============================================================================
# HELPER PEMBERSIH DATA
# ==============================================================================
def strip_html(val):
    if not val:
        return ""
    s = str(val)
    if "<" in s:
        s = re.sub(r'<[^>]+>', '', s)
    return s.strip()

def safe_int(val, default=0):
    if not val:
        return default
    s = strip_html(str(val)).replace("Rp", "").strip()
    digits = re.findall(r'-?\d+', s)
    if digits:
        return int(digits[0])
    return default

# ==============================================================================
# 1. LOGIN KE JEZPRO
# ==============================================================================
def create_jezpro_session():
    print(f"[{datetime.now()}] 🔐 Memulai Login ke Jezpro...")
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })

    r_init = session.get("https://jezpro.id/", timeout=60)
    soup = BeautifulSoup(r_init.text, "html.parser")
    token_tag = soup.find("input", {"name": "_token"})
    if not token_tag:
        raise Exception("Gagal mendapatkan CSRF Token dari halaman login Jezpro.")
    token = token_tag["value"]

    r_login = session.post("https://jezpro.id/user_login", data={
        "_token": token,
        "u_email": JEZPRO_EMAIL,
        "password": JEZPRO_PASSWORD
    }, headers={"Referer": "https://jezpro.id/"}, timeout=60)

    if "user_login" in r_login.url and "Dashboard" not in r_login.text:
        print("⚠️ Cek login: pastikan kredensial JEZPRO_EMAIL dan JEZPRO_PASSWORD benar!")

    print("✅ Berhasil login ke Jezpro!")
    session.get("https://jezpro.id/helper_backup", timeout=30)
    session.get("https://jezpro.id/mass_adjustment", timeout=30)
    session.get("https://jezpro.id/stock_tracking", timeout=30)
    return session

# ==============================================================================
# 2. TARIK DATA STOK SURABAYA (ALL STOCK TEMPLATE)
# ==============================================================================
def fetch_surabaya_stock(session):
    print(f"\n📦 [1/2] Menarik Master Stok: {BRANCH_NAME} (st_id = {SURABAYA_ST_ID})...")
    
    url_export = f"https://jezpro.id/export_mass_adjustment_template?st_id={SURABAYA_ST_ID}&psc_id=&br_id=&pl_id=&qty_filter=1"
    r_exp = session.get(url_export, headers={"Referer": "https://jezpro.id/mass_adjustment"}, timeout=300)

    excel_bytes = None
    content_type = r_exp.headers.get("Content-Type", "")

    if "application/json" in content_type:
        notif_id = r_exp.json().get("notification_id")
        check_url = f"https://jezpro.id/notifications/{notif_id}/open-export"
        final_url = ""

        for i in range(15):
            time.sleep(5)
            r_chk = session.get(check_url, allow_redirects=False, timeout=60)
            loc = r_chk.headers.get("Location", "")
            if r_chk.status_code == 302 and ("neo.id" in loc or "http" in loc):
                final_url = loc
                break
            print(f"   ⏳ Menunggu generate file stok Jezpro... ({i+1}/15)")

        if not final_url:
            raise Exception("Timeout pembuatan file export stok oleh Jezpro.")

        r_file = requests.get(final_url, timeout=300)
        excel_bytes = r_file.content
    else:
        excel_bytes = r_exp.content

    df_stock = pd.read_excel(io.BytesIO(excel_bytes))
    df_stock["STORE_NAME"] = BRANCH_NAME
    
    # Standarisasi Kolom agar siap dipakai balancing stock
    # Col 1: BIN | Col 2: SKU | Col 4: ITEM NAME | Col 6: SUB KATEGORI | Col 9: QTY SYSTEM
    records_stock = df_stock.fillna("").to_dict(orient="records")
    print(f"✅ Berhasil memuat {len(records_stock):,} baris stok untuk {BRANCH_NAME}.")
    return records_stock

# ==============================================================================
# 3. TARIK SALES / STOCK TRACKING SURABAYA (STATUS DONE, 3 BULAN TERAKHIR)
# ==============================================================================
def fetch_surabaya_sales_3months(session):
    now = datetime.now()
    start_date = now - timedelta(days=90)
    date_range = f"{start_date.strftime('%Y-%m-%d')}|{now.strftime('%Y-%m-%d')}"

    print(f"\n📊 [2/2] Menarik Stock Tracking DONE: {BRANCH_NAME}...")
    print(f"   📅 Periode 3 Bulan Terakhir: {date_range}")

    url_dt = "https://jezpro.id/stock_tracking_datatables"
    headers_dt = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://jezpro.id/stock_tracking"
    }

    # Query target status DONE (Offline & Online)
    status_queries = [
        {"status": "DONE", "status_search": ""},
        {"status": "DONE ONLINE", "status_search": ""},
        {"status": "", "status_search": "DONE"}
    ]

    all_done_records = []
    seen_ids = set()

    for sq in status_queries:
        start_row = 0
        batch_size = 500
        total_expected = 999999

        while start_row < total_expected:
            params = {
                "draw": "1",
                "columns[0][data]": "DT_RowIndex", "columns[0][name]": "plst_id", "columns[0][orderable]": "false",
                "columns[1][data]": "datetime", "columns[1][name]": "plst_created", "columns[1][orderable]": "true",
                "columns[2][data]": "ps_barcode", "columns[2][name]": "ps_barcode", "columns[2][orderable]": "true",
                "columns[3][data]": "article", "columns[3][name]": "p_name", "columns[3][orderable]": "true",
                "columns[4][data]": "invoice", "columns[4][name]": "p_name", "columns[4][orderable]": "true",
                "columns[5][data]": "cust_name", "columns[5][name]": "cust_name", "columns[5][orderable]": "true",
                "columns[6][data]": "qty", "columns[6][name]": "p_name", "columns[6][orderable]": "true",
                "columns[7][data]": "product_location", "columns[7][name]": "pl_code", "columns[7][orderable]": "true",
                "columns[8][data]": "status", "columns[8][name]": "plst_status", "columns[8][orderable]": "true",
                "columns[8][search][value]": sq["status_search"],
                "columns[9][data]": "instock_source", "columns[9][name]": "instock_source_status", "columns[9][orderable]": "false",
                "order[0][column]": "1",
                "order[0][dir]": "desc",
                "start": str(start_row),
                "length": str(batch_size),
                "search[value]": "",
                "status": sq["status"],
                "st_id": str(SURABAYA_ST_ID),
                "date": date_range
            }

            try:
                res = session.get(url_dt, params=params, headers=headers_dt, timeout=60)
                if res.status_code != 200:
                    break
                json_data = res.json()
                raw_chunk = json_data.get("data", [])
                if not raw_chunk:
                    break

                total_expected = json_data.get("recordsTotal", total_expected)
                start_row += len(raw_chunk)

                for item in raw_chunk:
                    status_raw = strip_html(item.get("status") or item.get("plst_status") or "").upper()
                    
                    # Pastikan status benar-benar memuat 'DONE'
                    if "DONE" not in status_raw:
                        continue

                    # ID Unik untuk hindari duplikat
                    raw_id = item.get("plst_id") or item.get("id")
                    barcode_clean = strip_html(item.get("ps_barcode") or "").split('.')[0].strip().upper()
                    inv_clean = strip_html(item.get("invoice") or "")
                    dt_clean = strip_html(item.get("datetime") or item.get("plst_created") or "")

                    p_key = f"{raw_id}_{barcode_clean}_{inv_clean}_{dt_clean}"
                    if p_key in seen_ids:
                        continue
                    seen_ids.add(p_key)

                    qty_val = safe_int(item.get("qty"), 1)
                    raw_art = strip_html(item.get("article") or item.get("p_name") or "-")
                    cust_name = strip_html(item.get("cust_name") or "-")
                    
                    # Deteksi Channel Online vs Offline untuk matriks balancing stock
                    inv_upper = inv_clean.upper()
                    cust_upper = cust_name.upper()
                    
                    is_online = any(k in inv_upper or k in cust_upper for k in ["ONL", "ONLINE", "SHOPEE", "TIKTOK", "TOKOPEDIA", "LAZADA", "BLIBLI", "WEB"])
                    channel_label = "ONLINE" if is_online else "OFFLINE"

                    all_done_records.append({
                        "STORE": BRANCH_NAME,
                        "DATETIME": dt_clean,
                        "SKU": barcode_clean,
                        "ARTICLE": raw_art,
                        "INVOICE": inv_clean,
                        "CUST_NAME": cust_name,
                        "QTY_SALES": qty_val,
                        "BIN": strip_html(item.get("product_location") or item.get("pl_code") or "-"),
                        "STATUS": status_raw,
                        "CHANNEL": channel_label
                    })

                time.sleep(0.08)

            except Exception as e:
                print(f"   ⚠️ Error membaca batch: {e}")
                break

    print(f"✅ Selesai! Terkumpul total {len(all_done_records):,} transaksi DONE 3 bulan terakhir.")
    return all_done_records, start_date.strftime('%Y-%m-%d'), now.strftime('%Y-%m-%d')

# ==============================================================================
# 4. PUSH KEDUA HASIL KE SUPABASE
# ==============================================================================
def push_to_supabase(stock_records, sales_records, period_start, period_end):
    print(f"\n🚀 Mengirim Data Balancing Stock ke Supabase...")

    now_iso = datetime.now(timezone(timedelta(hours=7))).isoformat()

    # 1. Simpan Data Master Stok Surabaya
    body_stock = {
        "id": "SURABAYA_BALANCING_STOCK",
        "branch": BRANCH_NAME,
        "updated_at": now_iso,
        "total_rows": len(stock_records),
        "stock_data": stock_records
    }

    res_stk = requests.post(
        f"{SUPABASE_URL}/rest/v1/balancing_stock_cache",
        headers=HEADERS_SB,
        data=json.dumps(body_stock),
        timeout=120
    )
    if res_stk.status_code in [200, 201]:
        print(f"   ✅ Stok Surabaya ({len(stock_records):,} baris) Berhasil Disimpan!")
    else:
        print(f"   ❌ Gagal simpan stok ke Supabase ({res_stk.status_code}): {res_stk.text}")

    # 2. Simpan Data Sales Tracking DONE 3 Bulan Terakhir
    body_sales = {
        "id": "SURABAYA_SALES_90D",
        "branch": BRANCH_NAME,
        "period_start": period_start,
        "period_end": period_end,
        "updated_at": now_iso,
        "total_rows": len(sales_records),
        "sales_data": sales_records
    }

    res_sls = requests.post(
        f"{SUPABASE_URL}/rest/v1/balancing_sales_cache",
        headers=HEADERS_SB,
        data=json.dumps(body_sales),
        timeout=120
    )
    if res_sls.status_code in [200, 201]:
        print(f"   ✅ Sales 90 Hari ({len(sales_records):,} baris) Berhasil Disimpan!")
    else:
        print(f"   ❌ Gagal simpan sales ke Supabase ({res_sls.status_code}): {res_sls.text}")

# ==============================================================================
# MAIN RUNNER
# ==============================================================================
def run_sync():
    if not JEZPRO_PASSWORD or not SUPABASE_KEY:
        raise ValueError("JEZPRO_PASSWORD atau SUPABASE_KEY belum disetel di Environment / GitHub Secrets!")

    session = create_jezpro_session()

    # 1. Tarik Stok Surabaya
    stock_data = fetch_surabaya_stock(session)

    # 2. Tarik Sales DONE 3 Bulan Terakhir Surabaya
    sales_data, p_start, p_end = fetch_surabaya_sales_3months(session)

    # 3. Simpan Keduanya ke Supabase
    push_to_supabase(stock_data, sales_data, p_start, p_end)
    print("\n🎉 SINKRONISASI BALANCING STOCK SURABAYA SELESAI SEMPURNA!")

if __name__ == "__main__":
    run_sync()
