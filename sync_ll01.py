import os
import json
import requests
import re
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
JEZPRO_EMAIL = os.environ.get("JEZPRO_EMAIL")
JEZPRO_PASS  = os.environ.get("JEZPRO_PASSWORD")

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

def create_jezpro_session():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })
    
    print("🔐 [1/5] Melakukan login ke Jezpro...")
    res_login_page = session.get("https://jezpro.id/")
    soup = BeautifulSoup(res_login_page.text, "html.parser")
    token_input = soup.find("input", {"name": "_token"})
    if not token_input:
        raise Exception("CSRF Token tidak ditemukan di form login Jezpro!")
    
    payload = {
        "_token": token_input.get("value"),
        "u_email": JEZPRO_EMAIL,
        "password": JEZPRO_PASS
    }
    session.post("https://jezpro.id/user_login", data=payload, headers={"Referer": "https://jezpro.id/"})
    print("✅ Berhasil login ke Jezpro!")
    
    session.get("https://jezpro.id/helper_backup")
    session.get("https://jezpro.id/transfer_stok")
    return session

def clean_html_card(raw_html):
    if not raw_html or "<" not in str(raw_html):
        return {"article": str(raw_html).strip(), "brand": "-", "bin": "-"}

    soup = BeautifulSoup(str(raw_html), "html.parser")
    bin_el = soup.find(attrs={"title": "Bin Code"})
    bin_val = bin_el.get_text(strip=True) if bin_el else None

    m_brand = re.search(r'\[(.*?)\]', str(raw_html))
    brand_val = m_brand.group(1).strip() if m_brand else "-"

    spans = soup.find_all("span")
    art_parts = []
    for s in spans:
        t = s.get_text(" ", strip=True)
        if any(w in t for w in ["REFUND", "WAITING", "TUKAR", "INV", "JEZ SURABAYA", "Bin Code"]):
            continue
        cleaned = re.sub(r'\[.*?\]\s*-\s*\d+', '', t)
        if cleaned.strip():
            art_parts.append(cleaned.strip())
            
    article_val = " ".join(art_parts) if art_parts else soup.get_text(" ", strip=True)
    article_val = re.sub(r'\s+', ' ', article_val).strip()

    return {"article": article_val, "brand": brand_val, "bin": bin_val}

# ------------------------------------------------------------------------------
# 1. TARIK DATA STAGING (MASUK RAK & REFUND)
# ------------------------------------------------------------------------------
def fetch_staging_data(session, endpoint_path, kategori_label, waiting_val):
    print(f"📥 [2/5] Menarik data staging [{kategori_label}]...")
    url = f"https://jezpro.id/{endpoint_path}"
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://jezpro.id/helper_backup"
    }
    params = {
        "draw": "1", "columns[0][data]": "article", "columns[0][name]": "article",
        "columns[0][searchable]": "true", "columns[0][orderable]": "false",
        "columns[0][search][value]": "", "columns[0][search][regex]": "false",
        "order[0][column]": "0", "order[0][dir]": "desc",
        "start": "0", "length": "5000", "search": "", "st_id": "", "waiting": waiting_val
    }

    res = session.get(url, params=params, headers=headers)
    if res.status_code != 200:
        return []
    
    raw_list = res.json().get("data", [])
    clean_records = []
    for idx_item, item in enumerate(raw_list):
        raw_art = item.get("article") or item.get("art_name") or "-"
        parsed = clean_html_card(raw_art)

        p_id = item.get("plst_id") or item.get("pls_id") or item.get("id") or item.get("plstr_id")
        if not p_id:
            p_id = abs(hash(f"{kategori_label}_{parsed['article']}_{idx_item}")) % (10**10)

        clean_records.append({
            "plst_id": int(p_id),
            "pls_id": int(item.get("pls_id") or p_id),
            "kategori": kategori_label,
            "waiting_status": item.get("waiting") or waiting_val,
            "brand": parsed["brand"] if parsed["brand"] != "-" else (item.get("brand") or "-"),
            "article_name": parsed["article"],
            "qty": safe_int_val(item.get("plst_qty") or item.get("qty"), 1),
            "bin_target": parsed["bin"] if parsed["bin"] != "-" else strip_html(item.get("rack_name") or item.get("bin") or "-"),
            "pic_name": strip_html(item.get("user_name") or item.get("scanned_by") or "Petugas"),
            "scanned_at": item.get("created_at") or item.get("date") or datetime.now().isoformat(),
            "store_id": 3,
            "raw_json": item,
            "synced_at": datetime.now().isoformat()
        })
    print(f"   -> Ditemukan {len(clean_records)} baris staging {kategori_label}.")
    return clean_records

# ------------------------------------------------------------------------------
# 2. TARIK DATA TRANSFER STOCK (WIB TIMEZONE & ANTI-MINUS)
# ------------------------------------------------------------------------------
def fetch_transfer_data(session):
    print("🚚 [3/5] Menarik data Transfer Stok (Khusus Tahun >= 2026)...")
    url_history = "https://jezpro.id/transfer_history_datatables"
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://jezpro.id/transfer_stok"
    }

    params = {
        "draw": "1",
        "columns[0][data]": "DT_RowIndex", "columns[0][name]": "stf_id", "columns[0][orderable]": "true",
        "columns[1][data]": "stf_code", "columns[1][name]": "stf_code", "columns[1][orderable]": "true",
        "columns[2][data]": "u_name", "columns[2][name]": "u_name", "columns[2][orderable]": "false",
        "columns[3][data]": "stf_notes", "columns[3][name]": "stf_notes", "columns[3][orderable]": "false",
        "columns[4][data]": "qty_send", "columns[4][name]": "qty_send", "columns[4][orderable]": "false",
        "columns[5][data]": "qty_receive", "columns[5][name]": "qty_receive", "columns[5][orderable]": "false",
        "columns[6][data]": "start_store", "columns[6][name]": "start_store", "columns[6][orderable]": "false",
        "columns[7][data]": "end_store", "columns[7][name]": "end_store", "columns[7][orderable]": "false",
        "columns[8][data]": "u_name_receive", "columns[8][name]": "u_name_receive", "columns[8][orderable]": "false",
        "columns[9][data]": "stf_created", "columns[9][name]": "stf_created", "columns[9][orderable]": "true",
        "columns[10][data]": "stf_status", "columns[10][name]": "stf_status", "columns[10][orderable]": "true",
        "order[0][column]": "0", "order[0][dir]": "desc",
        "start": "0", "length": "1000", "search": "", "status": ""
    }

    res = session.get(url_history, params=params, headers=headers)
    if res.status_code != 200:
        print(f"⚠️ Gagal panggil transfer history: HTTP {res.status_code}")
        return [], []

    raw_history = res.json().get("data", [])
    open_headers = []
    open_items = []

    # Waktu acuan saat ini dalam WIB (UTC+7)
    now_wib = datetime.now(timezone(timedelta(hours=7))).replace(tzinfo=None)

    for row in raw_history:
        status_txt = strip_html(row.get("stf_status") or row.get("status") or "").upper()

        if status_txt not in ["DRAFT", "IN PROGRESS"]:
            continue

        tf_code = strip_html(row.get("stf_code") or row.get("kode") or "")
        if not tf_code:
            continue

        tgl_str = strip_html(row.get("stf_created") or row.get("tanggal") or "")
        doc_year = None
        aging_jam = 0.0

        if tgl_str:
            for fmt in ("%Y-%m-%d %H:%M:%S", "%d-%m-%Y %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y %H:%M:%S"):
                try:
                    dt_tf = datetime.strptime(tgl_str[:19].strip(), fmt)
                    doc_year = dt_tf.year
                    # Hitung selisih jam terhadap WIB sekarang (anti-minus)
                    diff_sec = (now_wib - dt_tf).total_seconds()
                    aging_jam = max(0.0, round(diff_sec / 3600.0, 1))
                    break
                except Exception:
                    pass

        if doc_year is None:
            m_year = re.search(r'TF(\d{4})', tf_code)
            if m_year:
                doc_year = int(m_year.group(1))

        if doc_year is not None and doc_year < 2026:
            continue

        open_headers.append({
            "stf_code": tf_code,
            "u_name": strip_html(row.get("u_name") or "-"),
            "stf_notes": strip_html(row.get("stf_notes") or "-"),
            "qty_send": safe_int_val(row.get("qty_send")),
            "qty_receive": safe_int_val(row.get("qty_receive")),
            "start_store": strip_html(row.get("start_store") or "-"),
            "end_store": strip_html(row.get("end_store") or "-"),
            "u_name_receive": strip_html(row.get("u_name_receive") or "-"),
            "stf_created": tgl_str if tgl_str else now_wib.isoformat(),
            "stf_status": status_txt,
            "aging_hours": float(aging_jam),
            "synced_at": now_wib.isoformat()
        })

        # TARIK DETAIL BARANG PER DOKUMEN TF
        url_detail = "https://jezpro.id/in_transfer_bin_datatables"
        params_det = {
            "draw": "1",
            "columns[0][data]": "article", "columns[0][name]": "article", "columns[0][searchable]": "true", "columns[0][orderable]": "false", "columns[0][search][value]": "", "columns[0][search][regex]": "false",
            "columns[1][data]": "pl_code", "columns[1][name]": "pl_code", "columns[1][searchable]": "true", "columns[1][orderable]": "false", "columns[1][search][value]": "", "columns[1][search][regex]": "false",
            "columns[2][data]": "stfd_qty", "columns[2][name]": "stfd_qty", "columns[2][searchable]": "true", "columns[2][orderable]": "false", "columns[2][search][value]": "", "columns[2][search][regex]": "false",
            "columns[3][data]": "pls_qty", "columns[3][name]": "pls_qty", "columns[3][searchable]": "true", "columns[3][orderable]": "false", "columns[3][search][value]": "", "columns[3][search][regex]": "false",
            "columns[4][data]": "st_start", "columns[4][name]": "st_start", "columns[4][searchable]": "true", "columns[4][orderable]": "false", "columns[4][search][value]": "", "columns[4][search][regex]": "false",
            "columns[5][data]": "st_end", "columns[5][name]": "st_end", "columns[5][searchable]": "true", "columns[5][orderable]": "false", "columns[5][search][value]": "", "columns[5][search][regex]": "false",
            "columns[6][data]": "status", "columns[6][name]": "status", "columns[6][searchable]": "true", "columns[6][orderable]": "false", "columns[6][search][value]": "", "columns[6][search][regex]": "false",
            "order[0][column]": "0", "order[0][dir]": "desc",
            "start": "0", "length": "1000", "search": "",
            "stf_code": tf_code
        }
        res_det = session.get(url_detail, params=params_det, headers=headers)
        if res_det.status_code == 200:
            raw_items = res_det.json().get("data", [])
            for it in raw_items:
                art_str = strip_html(it.get("article", "-"))
                open_items.append({
                    "stf_code": tf_code,
                    "article_name": art_str,
                    "bin_asal": strip_html(it.get("pl_code") or "-"),
                    "qty_tf": safe_int_val(it.get("stfd_qty"), 1),
                    "qty_in_bin": safe_int_val(it.get("pls_qty"), 0),
                    "start_store": strip_html(it.get("st_start") or "-"),
                    "end_store": strip_html(it.get("st_end") or "-"),
                    "status": status_txt,
                    "synced_at": now_wib.isoformat()
                })

    print(f"   -> BERHASIL! Didapat {len(open_headers)} Dokumen Terbuka (Tahun >= 2026) & {len(open_items)} Detail Barang.")
    return open_headers, open_items

# ------------------------------------------------------------------------------
# PUSH KE SUPABASE
# ------------------------------------------------------------------------------
def push_all_to_supabase(staging_data, tf_headers, tf_items):
    print("🚀 [4/5] Mengirim seluruh data ke Supabase...")
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates"
    }

    # 1. Staging Waiting
    if staging_data:
        res_stg = requests.post(f"{SUPABASE_URL}/rest/v1/jezpro_waiting_staging", data=json.dumps(staging_data), headers=headers)
        print(f"   Status Staging: {res_stg.status_code}")
    
    # 2. Transfer Headers
    if tf_headers:
        res_tfh = requests.post(f"{SUPABASE_URL}/rest/v1/jezpro_transfer_headers", data=json.dumps(tf_headers), headers=headers)
        print(f"   Status Transfer Headers: {res_tfh.status_code}")
        if res_tfh.status_code not in [200, 201]:
            print(f"   ⚠️ Detail Alasan Ditolak Supabase: {res_tfh.text}")

    # 3. Transfer Items
    if tf_items:
        requests.delete(f"{SUPABASE_URL}/rest/v1/jezpro_transfer_items?id=gt.0", headers=headers)
        res_tfi = requests.post(f"{SUPABASE_URL}/rest/v1/jezpro_transfer_items", data=json.dumps(tf_items), headers=headers)
        print(f"   Status Transfer Items: {res_tfi.status_code}")

    print("✅ SUKSES! Seluruh data Staging & Transfer Stok tersinkronisasi ke Supabase.")

if __name__ == "__main__":
    jez = create_jezpro_session()
    
    all_staging = []
    all_staging.extend(fetch_staging_data(jez, "scan_product_in_datatables", "MASUK_RAK", "WAITING OFFLINE"))
    all_staging.extend(fetch_staging_data(jez, "scan_product_in_refund_datatables", "REFUND", "Refund"))
    
    tf_headers, tf_items = fetch_transfer_data(jez)
    
    push_all_to_supabase(all_staging, tf_headers, tf_items)
    print("🎉 [5/5] Selesai sempurna!")
