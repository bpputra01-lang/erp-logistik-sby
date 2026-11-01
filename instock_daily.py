import os
import json
import requests
import re
import time
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup

# ==============================================================================
# 1. KREDENSIAL & TARGET KHUSUS JEZ SURABAYA
# ==============================================================================
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
JEZPRO_EMAIL = os.environ.get("JEZPRO_EMAIL")
JEZPRO_PASS  = os.environ.get("JEZPRO_PASSWORD")

BRANCH_NAME = "JEZ SURABAYA"
STORE_ID = 3  # ID resmi JEZ SURABAYA
TARGET_STATUS = "WAITING OFFLINE"

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

def clean_stock_tracking_article(raw_html):
    if not raw_html:
        return {"article": "-", "brand": "-"}
    s = strip_html(str(raw_html)).strip()
    
    # Ambil brand di dalam kurung siku pertama
    m_brand = re.search(r'\[(.*?)\]', s)
    brand_val = m_brand.group(1).strip() if m_brand else "-"
    
    # Hapus tag [BRAND] di depan nama artikel
    clean_name = re.sub(r'^\[.*?\]\s*', '', s)
    # Hapus harga / pemisah di belakang nama artikel
    clean_name = clean_name.split('|')[0].strip()
    
    return {"article": clean_name if clean_name else s, "brand": brand_val}

# ==============================================================================
# 3. AUTENTIKASI KE JEZPRO
# ==============================================================================
def create_jezpro_session():
    if not JEZPRO_EMAIL or not JEZPRO_PASS:
        raise ValueError("Environment JEZPRO_EMAIL dan JEZPRO_PASSWORD belum diset!")

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

    session.get("https://jezpro.id/stock_tracking")
    return session

# ==============================================================================
# 4. TARIK DATA KHUSUS WAITING OFFLINE (JEZ SURABAYA)
# ==============================================================================
def fetch_waiting_offline_surabaya(session):
    print(f"📥 [2/3] Menarik data KHUSUS '{TARGET_STATUS}' untuk {BRANCH_NAME} (Store ID: {STORE_ID})...")
    url = "https://jezpro.id/stock_tracking_datatables"
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://jezpro.id/stock_tracking"
    }

    date_range = "2026-01-01|2030-12-31"

    # Hanya menembak parameter WAITING OFFLINE
    query_targets = [
        {"status": "WAITING OFFLINE", "status_search": ""},
        {"status": "", "status_search": "WAITING OFFLINE"}
    ]

    clean_records = []
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
            "instock_source": "",
            "psc_id": "",
            "std_id": "",
            "br_id": "",
            "st_id": str(STORE_ID),
            "date": date_range
        }

        try:
            res = session.get(url, params=params, headers=headers, timeout=25)
            if res.status_code != 200:
                continue
            raw_list = res.json().get("data", [])
        except Exception:
            raw_list = []

        for item in raw_list:
            status_raw = strip_html(item.get("status") or item.get("plst_status") or "").upper()
            loc_raw = strip_html(item.get("product_location") or item.get("pl_code") or "").upper()

            # 🛑 FILTER KETAT: Hanya izinkan WAITING OFFLINE
            if "WAITING OFFLINE" not in status_raw:
                continue

            # Abaikan jika ada embel-embel online, refund, checkout, nameset
            if any(x in status_raw for x in ["ONLINE", "REFUND", "CHECKOUT", "NAMESET"]):
                continue

            # Filter Tahun Dokumen >= 2026
            dt_raw = strip_html(item.get("datetime") or item.get("plst_created") or "")
            doc_year = None
            for fmt in ("%d/%m/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%d-%m-%Y %H:%M:%S", "%d/%m/%Y", "%Y-%m-%d"):
                try:
                    dt_obj = datetime.strptime(dt_raw[:19].strip(), fmt)
                    doc_year = dt_obj.year
                    break
                except Exception:
                    pass

            if doc_year is None:
                years = re.findall(r'\b(20\d{2})\b', dt_raw)
                if years:
                    doc_year = int(years[0])

            if doc_year is not None and doc_year < 2026:
                continue

            # Primary Key unik
            raw_id = item.get("plst_id") or item.get("id")
            p_id = safe_int_val(raw_id)
            if not p_id or p_id == 0:
                bar = strip_html(item.get("ps_barcode") or "")
                inv = strip_html(item.get("invoice") or "")
                p_id = abs(hash(f"{STORE_ID}_{bar}_{inv}_{dt_raw}")) % 2147483647

            if p_id in seen_ids:
                continue
            seen_ids.add(p_id)

            raw_art = item.get("article") or item.get("p_name") or "-"
            art_info = clean_stock_tracking_article(raw_art)

            # Format data sesuai persis dengan kolom Supabase di screenshot
            clean_records.append({
                "id": int(p_id),
                "barcode_sku": strip_html(item.get("ps_barcode") or "-").upper(),
                "article_name": art_info["article"],
                "brand": art_info["brand"],
                "qty": safe_int_val(item.get("qty"), 1),
                "bin_code": loc_raw if loc_raw else "[WAITING OFFLINE]",
                "status": "WAITING OFFLINE",
                "invoice": strip_html(item.get("invoice") or "-")
            })

        time.sleep(0.08)

    print(f"✅ Selesai! Berhasil mengumpulkan {len(clean_records)} baris data WAITING OFFLINE JEZ SURABAYA.")
    return clean_records

# ==============================================================================
# 5. SYNC KE SUPABASE (TABEL: jezpro_instock_daily)
# ==============================================================================
def push_to_supabase(records):
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Environment SUPABASE_URL dan SUPABASE_KEY wajib diset!")

    table_name = "jezpro_instock_daily"
    print(f"🚀 [3/3] Mengosongkan data lama & mengunggah data WAITING OFFLINE ke tabel '{table_name}'...")
    
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates"
    }

    # 1. Kosongkan tabel jezpro_instock_daily
    del_res = requests.delete(f"{SUPABASE_URL}/rest/v1/{table_name}?id=gt.0", headers=headers)
    if del_res.status_code in [200, 204]:
        print(f"   🧹 Tabel '{table_name}' berhasil dibersihkan.")

    # 2. Insert data baru
    if records:
        total_inserted = 0
        for i in range(0, len(records), 100):
            batch = records[i:i + 100]
            res = requests.post(
                f"{SUPABASE_URL}/rest/v1/{table_name}",
                data=json.dumps(batch),
                headers=headers
            )
            if res.status_code in [200, 201]:
                total_inserted += len(batch)
            else:
                print(f"   ❌ Gagal simpan batch baris {i}: Status {res.status_code}")
                print(f"      Detail Error Supabase: {res.text}")

        print(f"   ✅ Berhasil menyimpan {total_inserted} dari {len(records)} baris data WAITING OFFLINE ke Supabase.")
    else:
        print("   ℹ️ Tidak ada antrean WAITING OFFLINE untuk JEZ SURABAYA saat ini (Tabel Bersih).")

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================
if __name__ == "__main__":
    t0 = time.time()
    print("=" * 65)
    print("🚀 MENJALANKAN PIPELINE KHUSUS WAITING OFFLINE (JEZ SURABAYA)")
    print("=" * 65)

    jez_session = create_jezpro_session()
    records_surabaya = fetch_waiting_offline_surabaya(jez_session)
    push_to_supabase(records_surabaya)

    durasi = round(time.time() - t0, 2)
    print(f"\n🏁 Selesai dalam waktu {durasi} detik!")
    print("=" * 65)
