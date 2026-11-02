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
# KREDENSIAL & KONFIGURASI (MURNI HANYA st_id = 3)
# ==============================================================================
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://fanzsmghhbefhhaicrok.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
JEZPRO_EMAIL = os.environ.get("JEZPRO_EMAIL", "fajarbintang786@jez.co.id")
JEZPRO_PASSWORD = os.environ.get("JEZPRO_PASSWORD", "")

SURABAYA_ST_ID = 3
BRANCH_NAME = "JEZ SURABAYA"

HEADERS_SB = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates"
}

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
    print(f"[{datetime.now()}] 🔐 Login ke akun Jezpro...")
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })

    r_init = session.get("https://jezpro.id/", timeout=60)
    soup = BeautifulSoup(r_init.text, "html.parser")
    token_tag = soup.find("input", {"name": "_token"})
    if not token_tag:
        raise Exception("Gagal mendapatkan CSRF Token dari Jezpro.")
    token = token_tag["value"]

    session.post("https://jezpro.id/user_login", data={
        "_token": token,
        "u_email": JEZPRO_EMAIL,
        "password": JEZPRO_PASSWORD
    }, headers={"Referer": "https://jezpro.id/"}, timeout=60)

    print("✅ Berhasil login ke Jezpro!")
    session.get("https://jezpro.id/mass_adjustment", timeout=30)
    session.get("https://jezpro.id/stock_tracking", timeout=30)
    return session

# ==============================================================================
# 2. TARIK DATA STOK SURABAYA (KHUSUS st_id = 3)
# ==============================================================================
def fetch_surabaya_stock(session):
    print(f"\n📦 [1/2] Menarik Master Stok {BRANCH_NAME} (st_id = {SURABAYA_ST_ID})...")
    url_export = f"https://jezpro.id/export_mass_adjustment_template?st_id={SURABAYA_ST_ID}&psc_id=&br_id=&pl_id=&qty_filter=1"
    r_exp = session.get(url_export, headers={"Referer": "https://jezpro.id/mass_adjustment"}, timeout=300)

    excel_bytes = None
    content_type = r_exp.headers.get("Content-Type", "")

    if "application/json" in content_type:
        notif_id = r_exp.json().get("notification_id")
        check_url = f"https://jezpro.id/notifications/{notif_id}/open-export"
        final_url = ""

        for i in range(15):
            time.sleep(3)
            r_chk = session.get(check_url, allow_redirects=False, timeout=60)
            loc = r_chk.headers.get("Location", "")
            if r_chk.status_code == 302 and ("neo.id" in loc or "http" in loc):
                final_url = loc
                break
            print(f"   ⏳ Menunggu generate export stok... ({i+1}/15)")

        if not final_url:
            raise Exception("Timeout pembuatan file export stok oleh Jezpro.")

        r_file = requests.get(final_url, timeout=300)
        excel_bytes = r_file.content
    else:
        excel_bytes = r_exp.content

    df_stock = pd.read_excel(io.BytesIO(excel_bytes))
    df_stock["STORE_NAME"] = BRANCH_NAME
    records_stock = df_stock.fillna("").to_dict(orient="records")
    print(f"✅ Berhasil memuat {len(records_stock):,} baris stok.")
    return records_stock

# ==============================================================================
# 3. TARIK SALES 2 BULAN & PISAHKAN ONLINE VS OFFLINE
# ==============================================================================
def fetch_surabaya_sales_2months(session):
    now = datetime.now()
    start_date = now - timedelta(days=60)
    date_param = f"{start_date.strftime('%Y-%m-%d')}|{now.strftime('%Y-%m-%d')}"

    print(f"\n📊 [2/2] Menarik Transaksi DONE {BRANCH_NAME} (st_id = {SURABAYA_ST_ID})...")
    print(f"   📅 Parameter Tanggal: '{date_param}'")
    print(f"   🎯 Aturan: Invoice memuat 'INV' = OFFLINE, Tanpa 'INV' = ONLINE")

    url_dt = "https://jezpro.id/stock_tracking_datatables"
    headers_dt = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://jezpro.id/stock_tracking"
    }

    sales_by_sku = {}
    total_raw_rows = 0
    total_offline_qty = 0
    total_online_qty = 0

    start_row = 0
    batch_size = 2000  # Tarik 2.000 row per request agar cepat
    total_expected = 999999
    draw_count = 1

    while start_row < total_expected:
        params = {
            "draw": str(draw_count),
            "columns[0][data]": "DT_RowIndex", "columns[0][name]": "plst_id", "columns[0][searchable]": "false", "columns[0][orderable]": "true", "columns[0][search][value]": "", "columns[0][search][regex]": "false",
            "columns[1][data]": "datetime", "columns[1][name]": "plst_created", "columns[1][searchable]": "false", "columns[1][orderable]": "true", "columns[1][search][value]": "", "columns[1][search][regex]": "false",
            "columns[2][data]": "ps_barcode", "columns[2][name]": "ps_barcode", "columns[2][searchable]": "true", "columns[2][orderable]": "true", "columns[2][search][value]": "", "columns[2][search][regex]": "false",
            "columns[3][data]": "article", "columns[3][name]": "p_name", "columns[3][searchable]": "false", "columns[3][orderable]": "true", "columns[3][search][value]": "", "columns[3][search][regex]": "false",
            "columns[4][data]": "invoice", "columns[4][name]": "p_name", "columns[4][searchable]": "false", "columns[4][orderable]": "true", "columns[4][search][value]": "", "columns[4][search][regex]": "false",
            "columns[5][data]": "cust_name", "columns[5][name]": "cust_name", "columns[5][searchable]": "false", "columns[5][orderable]": "true", "columns[5][search][value]": "", "columns[5][search][regex]": "false",
            "columns[6][data]": "qty", "columns[6][name]": "p_name", "columns[6][searchable]": "false", "columns[6][orderable]": "true", "columns[6][search][value]": "", "columns[6][search][regex]": "false",
            "columns[7][data]": "product_location", "columns[7][name]": "pl_code", "columns[7][searchable]": "false", "columns[7][orderable]": "true", "columns[7][search][value]": "", "columns[7][search][regex]": "false",
            "columns[8][data]": "status", "columns[8][name]": "plst_status", "columns[8][searchable]": "false", "columns[8][orderable]": "true", "columns[8][search][value]": "", "columns[8][search][regex]": "false",
            "columns[9][data]": "instock_source", "columns[9][name]": "instock_source_status", "columns[9][searchable]": "false", "columns[9][orderable]": "false", "columns[9][search][value]": "", "columns[9][search][regex]": "false",
            "order[0][column]": "0",
            "order[0][dir]": "desc",
            "start": str(start_row),
            "length": str(batch_size),
            "search": "",
            "status": "DONE",
            "instock_source": "",
            "psc_id": "",
            "std_id": "",
            "br_id": "",
            "st_id": str(SURABAYA_ST_ID),
            "date": date_param
        }

        try:
            res = session.get(url_dt, params=params, headers=headers_dt, timeout=60)
            if res.status_code != 200:
                print(f"      ⚠️ Gagal request HTTP {res.status_code}")
                break

            json_data = res.json()
            raw_chunk = json_data.get("data", [])
            total_server = json_data.get("recordsFiltered", json_data.get("recordsTotal", 0))
            total_expected = total_server

            if not raw_chunk:
                break

            start_row += len(raw_chunk)
            draw_count += 1

            for item in raw_chunk:
                status_raw = strip_html(item.get("status") or item.get("plst_status") or "").upper()
                if "DONE" not in status_raw:
                    continue

                sku = strip_html(item.get("ps_barcode") or "").split('.')[0].strip().upper()
                if not sku or sku in ["", "NAN", "NONE"]:
                    continue

                qty_val = safe_int(item.get("qty"), 1)
                raw_art = strip_html(item.get("article") or item.get("p_name") or "-")
                inv_raw = strip_html(item.get("invoice") or "").upper()

                # ==============================================================
                # 🎯 ATURAN RESMI ANDA:
                # 1. Mengandung kata 'INV' di depan -> OFFLINE (Kasir Toko)
                # 2. Tidak ada kata 'INV' -> ONLINE (Marketplace)
                # ==============================================================
                if "INV" in inv_raw:
                    is_online = False
                    total_offline_qty += qty_val
                else:
                    is_online = True
                    total_online_qty += qty_val

                if sku not in sales_by_sku:
                    sales_by_sku[sku] = {
                        "SKU": sku,
                        "ARTICLE": raw_art,
                        "SALES_OFFLINE": 0,
                        "SALES_ONLINE": 0,
                        "TOTAL_SALES": 0
                    }

                if is_online:
                    sales_by_sku[sku]["SALES_ONLINE"] += qty_val
                else:
                    sales_by_sku[sku]["SALES_OFFLINE"] += qty_val

                sales_by_sku[sku]["TOTAL_SALES"] += qty_val
                total_raw_rows += 1

            print(f"      -> Berhasil menarik {start_row:,} / {total_expected:,} data...")
            time.sleep(0.02)

        except Exception as e:
            print(f"      ⚠️ Kendala saat request: {e}")
            break

    summary_sales = list(sales_by_sku.values())
    print(f"\n✅ Total {total_raw_rows:,} transaksi DONE berhasil diproses!")
    print(f"   🛒 Total Qty Offline (INV): {total_offline_qty:,} Pcs")
    print(f"   🌐 Total Qty Online (Non-INV): {total_online_qty:,} Pcs")
    print(f"   🏷️ Terkumpul {len(summary_sales):,} SKU aktif terjual.")
    return summary_sales, start_date.strftime('%Y-%m-%d'), now.strftime('%Y-%m-%d'), total_raw_rows

# ==============================================================================
# 4. SIMPAN KE SUPABASE (AGREGASI SUPER RINGAN & ANTI-TIMEOUT)
# ==============================================================================
def push_to_supabase(stock_records, sales_summary, period_start, period_end, total_raw_sales):
    print(f"\n🚀 Mengirim ke Supabase...")
    now_iso = datetime.now(timezone(timedelta(hours=7))).isoformat()

    # 1. Simpan Stok Surabaya
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
        print(f"   ❌ Gagal simpan stok ({res_stk.status_code}): {res_stk.text}")

    # 2. Simpan Rekap Penjualan 2 Bulan (Hanya ~200 KB, simpan 0.1 detik tanpa timeout!)
    body_sales = {
        "id": "SURABAYA_SALES_90D",
        "branch": BRANCH_NAME,
        "period_start": period_start,
        "period_end": period_end,
        "updated_at": now_iso,
        "total_rows": total_raw_sales,
        "total_skus": len(sales_summary),
        "sales_data": sales_summary
    }

    res_sls = requests.post(
        f"{SUPABASE_URL}/rest/v1/balancing_sales_cache",
        headers=HEADERS_SB,
        data=json.dumps(body_sales),
        timeout=120
    )
    if res_sls.status_code in [200, 201]:
        print(f"   ✅ Rekap Sales ({len(sales_summary):,} SKU dari {total_raw_sales:,} transaksi) Berhasil Disimpan!")
    else:
        print(f"   ❌ Gagal simpan sales ({res_sls.status_code}): {res_sls.text}")

# ==============================================================================
# MAIN RUNNER
# ==============================================================================
def run_sync():
    if not JEZPRO_PASSWORD or not SUPABASE_KEY:
        raise ValueError("JEZPRO_PASSWORD atau SUPABASE_KEY belum disetel!")

    session = create_jezpro_session()

    # 1. Tarik Stok Surabaya (st_id: 3)
    stock_data = fetch_surabaya_stock(session)

    # 2. Tarik Sales 2 Bulan (st_id: 3 saja)
    sales_summary, p_start, p_end, total_raw = fetch_surabaya_sales_2months(session)

    # 3. Simpan ke Supabase
    push_to_supabase(stock_data, sales_summary, p_start, p_end, total_raw)
    print("\n🎉 SINKRONISASI BALANCING STOCK SURABAYA SELESAI SEMPURNA!")

if __name__ == "__main__":
    run_sync()
