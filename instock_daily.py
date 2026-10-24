import os
import json
import requests
import re
import time
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup

# ==============================================================================
# 1. KREDENSIAL & KONFIGURASI CABANG (KHUSUS SURABAYA)
# ==============================================================================
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
JEZPRO_EMAIL = os.environ.get("JEZPRO_EMAIL")
JEZPRO_PASS  = os.environ.get("JEZPRO_PASSWORD")

# Hanya menargetkan Cabang Surabaya
BRANCH_NAME = "JEZ SURABAYA"
STORE_ID = 3


# ==============================================================================
# 2. HELPER PEMBERSIH DATA
# ==============================================================================
def strip_html(val):
    if not val:
        return ""
    s = str(val)
    if "<" in s:
        s = re.sub(r'<[^>]+>', '', s)
    return s.strip()


def safe_int_val(val, default=0):
    if not val:
        return default
    s = strip_html(val)
    digits = re.findall(r'-?\d+', s)
    if digits:
        return int(digits[0])
    return default


def parse_to_iso_timestamp(dt_raw):
    if not dt_raw:
        return datetime.now(timezone(timedelta(hours=7))).isoformat()
    s = strip_html(str(dt_raw)).strip()
    s = s.replace('–', '-').replace('—', '-').replace('/', '-')
    formats = (
        "%Y-%m-%d %H:%M:%S", "%d-%m-%Y %H:%M:%S", "%d-%b-%Y %H:%M:%S",
        "%d-%B-%Y %H:%M:%S", "%Y-%m-%d", "%d-%m-%Y", "%d-%b-%Y", "%d-%B-%Y"
    )
    for fmt in formats:
        try:
            dt = datetime.strptime(s[:19].strip(), fmt)
            return dt.isoformat()
        except Exception:
            pass
    return datetime.now(timezone(timedelta(hours=7))).isoformat()


def clean_stock_tracking_article(raw_html):
    if not raw_html:
        return {"article": "-", "brand": "-"}
    s = strip_html(str(raw_html)).strip()

    # Ekstrak Brand di dalam kurung siku
    m_brand = re.search(r'\[(.*?)\]', s)
    brand_val = m_brand.group(1).strip() if m_brand else "-"

    # Hapus tag [BRAND] di depan nama
    clean_name = re.sub(r'^\[.*?\]\s*', '', s)
    # Hapus harga / separator di belakang nama artikel
    clean_name = clean_name.split('|')[0].strip()

    return {"article": clean_name if clean_name else s, "brand": brand_val}


# ==============================================================================
# 3. SESI & AUTENTIKASI JEZPRO
# ==============================================================================
def create_jezpro_session():
    if not JEZPRO_EMAIL or not JEZPRO_PASS:
        raise ValueError("Environment JEZPRO_EMAIL dan JEZPRO_PASSWORD wajib diset!")

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })

    print("🔐 [1/3] Melakukan login ke Jezpro...")
    res_login_page = session.get("https://jezpro.id/")
    soup = BeautifulSoup(res_login_page.text, "html.parser")
    token_input = soup.find("input", {"name": "_token"})
    if not token_input:
        raise Exception("Gagal mendapatkan CSRF Token form login Jezpro!")

    payload = {
        "_token": token_input.get("value"),
        "u_email": JEZPRO_EMAIL,
        "password": JEZPRO_PASS
    }
    session.post("https://jezpro.id/user_login", data=payload, headers={"Referer": "https://jezpro.id/"})
    print("✅ Berhasil login ke Jezpro!")

    # Inisialisasi rute stock tracking
    session.get("https://jezpro.id/stock_tracking")
    return session


# ==============================================================================
# 4. SCRAPING DATA INSTOCK (KHUSUS SURABAYA HARI INI)
# ==============================================================================
def fetch_instock_daily_surabaya(session):
    yesterday_wib = now_wib - timedelta(days=1)
    yesterday_str = yesterday_wib.strftime("%Y-%m-%d")
    date_range = f"{yesterday_str}|{yesterday_str}"

    print(f"📥 [2/3] Menarik data Stock Tracking INSTOCK untuk {BRANCH_NAME} (Tanggal: {today_str})...")

    url = "https://jezpro.id/stock_tracking_datatables"
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://jezpro.id/stock_tracking"
    }

    # Query target khusus status INSTOCK
    query_targets = [
        {"status": "INSTOCK", "status_search": ""},
        {"status": "", "status_search": "INSTOCK"}
    ]

    all_instock_records = []
    seen_ids = set()

    for q in query_targets:
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
            "columns[8][data]": "status",
            "columns[8][name]": "plst_status",
            "columns[8][searchable]": "true",
            "columns[8][search][value]": q["status_search"],
            "columns[8][search][regex]": "false",
            "columns[8][orderable]": "true",
            "columns[9][data]": "instock_source", "columns[9][name]": "instock_source_status", "columns[9][orderable]": "false",
            "order[0][column]": "1",
            "order[0][dir]": "desc",
            "start": "0",
            "length": "500",
            "search[value]": "",
            "search": "",
            "status": q["status"],
            "st_id": str(STORE_ID),
            "date": date_range
        }

        try:
            res = session.get(url, params=params, headers=headers, timeout=20)
            if res.status_code != 200:
                continue
            raw_list = res.json().get("data", [])
        except Exception as e:
            print(f"   ⚠️ Timeout/Gagal query {BRANCH_NAME}: {e}")
            raw_list = []

        for item in raw_list:
            status_raw = strip_html(item.get("status") or item.get("plst_status") or "").upper()
            loc_raw = strip_html(item.get("product_location") or item.get("pl_code") or "").upper()

            # Filter validasi ketat status INSTOCK
            if "INSTOCK" not in status_raw and "IN STOCK" not in status_raw:
                continue

            raw_id = item.get("plst_id") or item.get("id")
            p_id = safe_int_val(raw_id)
            if not p_id or p_id == 0:
                bar = strip_html(item.get("ps_barcode") or "")
                p_id = abs(hash(f"{STORE_ID}_{bar}_{today_str}_{len(seen_ids)}")) % 2147483647

            if p_id in seen_ids:
                continue
            seen_ids.add(p_id)

            dt_raw = strip_html(item.get("datetime") or item.get("plst_created") or "")
            raw_art = item.get("article") or item.get("p_name") or "-"
            art_info = clean_stock_tracking_article(raw_art)

            all_instock_records.append({
                "id": int(p_id),
                "barcode_sku": strip_html(item.get("ps_barcode") or "-").upper(),
                "article_name": art_info["article"],
                "brand": art_info["brand"],
                "qty": safe_int_val(item.get("qty"), 1),
                "bin_code": loc_raw if loc_raw else "[STAGING INSTOCK]",
                "status": "INSTOCK",
                "invoice": strip_html(item.get("invoice") or "-"),
                "pic_name": strip_html(item.get("u_name") or item.get("user_name") or item.get("cust_name") or "Petugas"),
                "scanned_at": parse_to_iso_timestamp(dt_raw),
                "store_id": int(STORE_ID),
                "store_name": BRANCH_NAME,
                "sync_date": today_str,
                "created_at": now_wib.isoformat()
            })

        time.sleep(0.05)

    print(f"✅ Selesai! Ditemukan {len(all_instock_records)} item INSTOCK untuk {BRANCH_NAME} hari ini ({today_str}).")
    return all_instock_records, today_str


# ==============================================================================
# 5. SYNC KE SUPABASE (AUTO-CLEAN HARI SEBELUMNYA)
# ==============================================================================
def push_instock_to_supabase(records, today_str):
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Environment SUPABASE_URL dan SUPABASE_KEY wajib diset!")

    print(f"🚀 [3/3] Mengosongkan data kemarin & memperbarui data ({today_str}) ke Supabase...")
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates"
    }

    # 1. Hapus transaksi tanggal kemarin / sebelum hari ini
    del_old = requests.delete(
        f"{SUPABASE_URL}/rest/v1/jezpro_instock_daily?sync_date=neq.{today_str}",
        headers=headers
    )
    if del_old.status_code in [200, 204]:
        print("   🧹 Data tanggal kemarin berhasil dibersihkan dari database.")

    # 2. Hapus data hari ini sebelum insert ulang agar tidak duplikat
    requests.delete(
        f"{SUPABASE_URL}/rest/v1/jezpro_instock_daily?sync_date=eq.{today_str}",
        headers=headers
    )

    # 3. Masukkan data terbaru hari ini
    if records:
        total_inserted = 0
        for i in range(0, len(records), 100):
            batch = records[i:i + 100]
            res = requests.post(
                f"{SUPABASE_URL}/rest/v1/jezpro_instock_daily",
                data=json.dumps(batch),
                headers=headers
            )
            if res.status_code in [200, 201]:
                total_inserted += len(batch)
            else:
                print(f"   ❌ Gagal simpan batch {i}: Status {res.status_code} - {res.text}")

        print(f"   ✅ Berhasil menyimpan {total_inserted} dari {len(records)} baris data Instock Surabaya hari ini.")
    else:
        print("   ℹ️ Tidak ada transaksi Instock Surabaya pada tanggal hari ini.")


# ==============================================================================
# 6. PIPELINE UTAMA
# ==============================================================================
if __name__ == "__main__":
    start_time = time.time()
    print("=" * 65)
    print("🚀 MEMULAI PIPELINE INSTOCK DAILY (KHUSUS SURABAYA)")
    print("=" * 65)

    jez_session = create_jezpro_session()
    instock_data, current_date = fetch_instock_daily_surabaya(jez_session)
    push_instock_to_supabase(instock_data, current_date)

    duration = round(time.time() - start_time, 2)
    print(f"\n🏁 Selesai sempurna dalam {duration} detik!")
    print("=" * 65)
