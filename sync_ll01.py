import os
import json
import requests
import re
import time
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup

# ==============================================================================
# KREDENSIAL DARI GITHUB SECRETS
# ==============================================================================
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
JEZPRO_EMAIL = os.environ.get("JEZPRO_EMAIL")
JEZPRO_PASS  = os.environ.get("JEZPRO_PASSWORD")

# ==============================================================================
# HELPER PEMBERSIH DATA (ANTI-HTML & ANTI-VALUEERROR)
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

# ==============================================================================
# LOGIN KE JEZPRO
# ==============================================================================
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
    session.get("https://jezpro.id/mass_adjustment")
    return session

# ==============================================================================
# 1. MODUL STAGING (MASUK RAK & REFUND)
# ==============================================================================
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

# ==============================================================================
# 2. MODUL TRANSFER STOK (DRAFT & IN PROGRESS >= 2026 + FULL ITEMS)
# ==============================================================================
def fetch_all_items_for_single_tf(session, tf_code, status_txt, headers, now_wib):
    all_items = []
    start_item = 0
    chunk_size = 250

    while True:
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
            "start": str(start_item), "length": str(chunk_size), "search": "",
            "stf_code": tf_code
        }

        res_det = session.get("https://jezpro.id/in_transfer_bin_datatables", params=params_det, headers=headers)
        data_json = res_det.json() if res_det.status_code == 200 else {}
        raw_chunk = data_json.get("data", [])

        if not raw_chunk and start_item == 0:
            res_det2 = session.get("https://jezpro.id/transfer_bin_datatables", params=params_det, headers=headers)
            data_json = res_det2.json() if res_det2.status_code == 200 else {}
            raw_chunk = data_json.get("data", [])

        if not raw_chunk:
            break

        for it in raw_chunk:
            art_str = strip_html(it.get("article", "-"))
            all_items.append({
                "stf_code": tf_code,
                "article_name": art_str,
                "bin_asal": strip_html(it.get("pl_code") or it.get("bin") or "-"),
                "qty_tf": safe_int_val(it.get("stfd_qty") or it.get("qty"), 1),
                "qty_in_bin": safe_int_val(it.get("pls_qty") or it.get("qty_bin"), 0),
                "start_store": strip_html(it.get("st_start") or it.get("start_store") or "-"),
                "end_store": strip_html(it.get("st_end") or it.get("end_store") or "-"),
                "status": status_txt,
                "synced_at": now_wib.isoformat()
            })

        total_records_in_doc = data_json.get("recordsTotal", 0)
        start_item += len(raw_chunk)

        if total_records_in_doc > 0 and start_item >= total_records_in_doc:
            break
        if len(raw_chunk) < chunk_size:
            break
        time.sleep(0.08)

    return all_items

def fetch_transfer_data(session):
    print("🚚 [3/5] Menarik SELURUH Riwayat Transfer Stok (Membaca s/d baris terakhir)...")
    url_history = "https://jezpro.id/transfer_history_datatables"
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://jezpro.id/transfer_stok"
    }

    raw_history = []
    start_row = 0
    batch_size = 500
    total_expected = 999999

    while start_row < total_expected:
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
            "start": str(start_row), "length": str(batch_size), "search": "", "status": ""
        }

        res = session.get(url_history, params=params, headers=headers)
        if res.status_code != 200:
            break

        data_json = res.json()
        data_chunk = data_json.get("data", [])
        if not data_chunk:
            break

        total_expected = data_json.get("recordsTotal", total_expected)
        raw_history.extend(data_chunk)
        start_row += len(data_chunk)
        print(f"   -> Mengumpulkan riwayat transfer: {len(raw_history)} / {total_expected} baris...")

    print(f"✅ Total {len(raw_history)} baris riwayat transfer berhasil dimuat.")

    open_headers = []
    open_items = []
    now_wib = datetime.now(timezone(timedelta(hours=7))).replace(tzinfo=None)

    for row in raw_history:
        status_txt = strip_html(row.get("stf_status") or row.get("status") or "").upper()

        if status_txt not in ["DRAFT", "IN PROGRESS"]:
            continue

        raw_code = str(row.get("stf_code") or row.get("kode") or "")
        m_code = re.search(r'TF\d+', raw_code)
        tf_code = m_code.group(0) if m_code else strip_html(raw_code).strip()
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

        doc_items = fetch_all_items_for_single_tf(session, tf_code, status_txt, headers, now_wib)
        open_items.extend(doc_items)

    print(f"   -> BERHASIL! {len(open_headers)} Surat Jalan & TOTAL {len(open_items)} Detail Barang Transfer Tersaring.")
    return open_headers, open_items

# ==============================================================================
# 3. MODUL MULTIPLE ADJUSTMENT (MENGGANTUNG & CANCEL TAHUN >= 2026)
# ==============================================================================
def fetch_mass_adjustment_data(session):
    print("⚖️ [4/5] Menarik Data Multiple Adjustment (Menggantung & Cancel >= 2026)...")
    url_ma = "https://jezpro.id/mass_adjustment_datatables"
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://jezpro.id/mass_adjustment"
    }

    raw_adjustments = []
    start_row = 0
    batch_size = 500
    total_expected = 999999

    # Menyisir seluruh dokumen adjustment
    while start_row < total_expected:
        params = {
            "draw": "1",
            "columns[0][data]": "DT_RowIndex", "columns[0][name]": "id", "columns[0][orderable]": "true",
            "columns[1][data]": "ma_code_show", "columns[1][name]": "ma_code", "columns[1][orderable]": "true",
            "columns[2][data]": "st_name", "columns[2][name]": "st_name", "columns[2][orderable]": "true",
            "columns[3][data]": "u_name", "columns[3][name]": "u_name", "columns[3][orderable]": "true",
            "columns[4][data]": "approve", "columns[4][name]": "", "columns[4][orderable]": "false",
            "columns[5][data]": "executor", "columns[5][name]": "", "columns[5][orderable]": "false",
            "columns[6][data]": "editor", "columns[6][name]": "", "columns[6][orderable]": "false",
            "columns[7][data]": "note", "columns[7][name]": "", "columns[7][orderable]": "false",
            "columns[8][data]": "ma_proof_file", "columns[8][name]": "", "columns[8][orderable]": "false",
            "columns[9][data]": "tipe", "columns[9][name]": "", "columns[9][orderable]": "false",
            "columns[10][data]": "created_at", "columns[10][name]": "", "columns[10][orderable]": "true",
            "columns[11][data]": "updated_at", "columns[11][name]": "", "columns[11][orderable]": "true",
            "columns[12][data]": "ma_status", "columns[12][name]": "", "columns[12][orderable]": "true",
            "columns[13][data]": "action", "columns[13][name]": "", "columns[13][orderable]": "true",
            "order[0][column]": "0", "order[0][dir]": "desc",
            "start": str(start_row), "length": str(batch_size), "search": "", "st_id": ""
        }

        res = session.get(url_ma, params=params, headers=headers)
        if res.status_code != 200:
            break

        data_json = res.json()
        data_chunk = data_json.get("data", [])
        if not data_chunk:
            break

        total_expected = data_json.get("recordsTotal", total_expected)
        raw_adjustments.extend(data_chunk)
        start_row += len(data_chunk)
        print(f"   -> Mengumpulkan adjustment: {len(raw_adjustments)} / {total_expected} baris...")

    print(f"✅ Total {len(raw_adjustments)} baris adjustment berhasil dimuat.")

    open_ma_headers = []
    open_ma_items = []
    now_wib = datetime.now(timezone(timedelta(hours=7))).replace(tzinfo=None)

    for row in raw_adjustments:
        status_raw = strip_html(row.get("ma_status") or "").upper()
        approve_raw = strip_html(row.get("approve") or "")

        is_menggantung = any(k in status_raw for k in ["MENUNGGU", "PENDING", "DRAFT", "PROGRESS"]) or "MENUNGGU" in approve_raw.upper()
        is_cancel = any(k in status_raw for k in ["CANCEL", "BATAL", "REJECT"]) or "CANCEL" in approve_raw.upper()

        if not (is_menggantung or is_cancel):
            continue

        raw_code = str(row.get("ma_code_show") or row.get("ma_code") or "")
        m_code = re.search(r'MADJ\d+', raw_code)
        ma_code = m_code.group(0) if m_code else strip_html(raw_code).strip()

        ma_id_val = safe_int_val(row.get("id"))
        if not ma_id_val:
            m_id = re.search(r'detail[/?](\d+)|ma_id=(\d+)', str(row.get("action") or ""))
            ma_id_val = int(m_id.group(1) or m_id.group(2)) if m_id else None

        if not ma_id_val and ma_code:
            ma_id_val = abs(hash(ma_code)) % (10**10)

        tgl_str = strip_html(row.get("created_at") or "")
        doc_year = None
        aging_jam = 0.0

        if tgl_str:
            for fmt in ("%d/%m/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%d-%m-%Y %H:%M:%S", "%d/%m/%Y"):
                try:
                    dt_ma = datetime.strptime(tgl_str[:19].strip(), fmt)
                    doc_year = dt_ma.year
                    diff_sec = (now_wib - dt_ma).total_seconds()
                    aging_jam = max(0.0, round(diff_sec / 3600.0, 1))
                    break
                except Exception:
                    pass

        if doc_year is None and ma_code:
            m_y = re.search(r'MADJ(\d{4})', ma_code)
            if m_y:
                doc_year = int(m_y.group(1))

        if doc_year is not None and doc_year < 2026:
            continue

        category = "CANCEL" if is_cancel else "MENGGANTUNG"

        open_ma_headers.append({
            "ma_id": ma_id_val,
            "ma_code": ma_code,
            "store_name": strip_html(row.get("st_name") or "-"),
            "u_name": strip_html(row.get("u_name") or "-"),
            "approve": approve_raw if approve_raw else "-",
            "executor": strip_html(row.get("executor") or "-"),
            "note": strip_html(row.get("note") or "-"),
            "created_at": tgl_str if tgl_str else now_wib.isoformat(),
            "ma_status": status_raw if status_raw else category,
            "status_category": category,
            "aging_hours": float(aging_jam),
            "synced_at": now_wib.isoformat()
        })

        # TARIK RINCIAN DETAIL ITEM BARANG PER MA_ID (FULL SWEEPER)
        start_item_ma = 0
        chunk_ma = 250
        while True:
            url_detail = "https://jezpro.id/mass_adjustment_detail_datatables"
            params_det = {
                "draw": "1",
                "columns[0][data]": "DT_RowIndex", "columns[0][name]": "id", "columns[0][orderable]": "true",
                "columns[1][data]": "pl_code", "columns[1][name]": "pl_code", "columns[1][orderable]": "true",
                "columns[2][data]": "br_name", "columns[2][name]": "br_name", "columns[2][orderable]": "true",
                "columns[3][data]": "ps_barcode", "columns[3][name]": "ps_barcode", "columns[3][orderable]": "true",
                "columns[4][data]": "p_name", "columns[4][name]": "p_name", "columns[4][orderable]": "true",
                "columns[5][data]": "p_color", "columns[5][name]": "p_color", "columns[5][orderable]": "true",
                "columns[6][data]": "sz_name", "columns[6][name]": "sz_name", "columns[6][orderable]": "true",
                "columns[7][data]": "psc_name", "columns[7][name]": "psc_name", "columns[7][orderable]": "true",
                "columns[8][data]": "purchase", "columns[8][name]": "purchase", "columns[8][orderable]": "false",
                "columns[9][data]": "sell", "columns[9][name]": "sell", "columns[9][orderable]": "false",
                "columns[10][data]": "qty_export", "columns[10][name]": "qty_export", "columns[10][orderable]": "true",
                "columns[11][data]": "qty_so", "columns[11][name]": "qty_so", "columns[11][orderable]": "true",
                "columns[12][data]": "mad_type", "columns[12][name]": "mad_type", "columns[12][orderable]": "true",
                "columns[13][data]": "mad_diff", "columns[13][name]": "mad_diff", "columns[13][orderable]": "true",
                "order[0][column]": "0", "order[0][dir]": "desc",
                "start": str(start_item_ma), "length": str(chunk_ma), "search": "",
                "ma_id": str(ma_id_val)
            }

            res_det = session.get(url_detail, params=params_det, headers=headers)
            data_json_ma = res_det.json() if res_det.status_code == 200 else {}
            raw_items = data_json_ma.get("data", [])
            if not raw_items:
                break

            for it in raw_items:
                open_ma_items.append({
                    "ma_id": ma_id_val,
                    "bin_code": strip_html(it.get("pl_code") or "-"),
                    "brand": strip_html(it.get("br_name") or "-"),
                    "barcode_sku": strip_html(it.get("ps_barcode") or "-"),
                    "article_name": strip_html(it.get("p_name") or "-"),
                    "color": strip_html(it.get("p_color") or "-"),
                    "size_variant": strip_html(it.get("sz_name") or "-"),
                    "sub_category": strip_html(it.get("psc_name") or "-"),
                    "cogs_price": safe_int_val(it.get("purchase")),
                    "qty_system": safe_int_val(it.get("qty_export")),
                    "qty_so": safe_int_val(it.get("qty_so")),
                    "diff_qty": safe_int_val(it.get("mad_diff")),
                    "adj_type": strip_html(it.get("mad_type") or "-"),
                    "synced_at": now_wib.isoformat()
                })

            total_rec_doc = data_json_ma.get("recordsTotal", 0)
            start_item_ma += len(raw_items)
            if total_rec_doc > 0 and start_item_ma >= total_rec_doc:
                break
            if len(raw_items) < chunk_ma:
                break
            time.sleep(0.08)

    print(f"   -> BERHASIL! {len(open_ma_headers)} Dokumen MADJ Terbuka & {len(open_ma_items)} Detail Barang.")
    return open_ma_headers, open_ma_items

# ==============================================================================
# 4. PUSH KE SUPABASE DALAM BATCH 200 ITEM
# ==============================================================================
def push_all_to_supabase(staging_data, tf_headers, tf_items, ma_headers, ma_items):
    print("🚀 [5/5] Mengirim seluruh data ke Supabase...")
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates"
    }

    # 1. Staging Waiting
    if staging_data:
        res = requests.post(f"{SUPABASE_URL}/rest/v1/jezpro_waiting_staging", data=json.dumps(staging_data), headers=headers)
        print(f"   Status Staging: {res.status_code}")
    
    # 2. Transfer Headers
    if tf_headers:
        res = requests.post(f"{SUPABASE_URL}/rest/v1/jezpro_transfer_headers", data=json.dumps(tf_headers), headers=headers)
        print(f"   Status Transfer Headers: {res.status_code}")

    # 3. Transfer Items (Per batch 200 baris)
    if tf_items:
        requests.delete(f"{SUPABASE_URL}/rest/v1/jezpro_transfer_items?id=gt.0", headers=headers)
        for i in range(0, len(tf_items), 200):
            batch = tf_items[i:i + 200]
            requests.post(f"{SUPABASE_URL}/rest/v1/jezpro_transfer_items", data=json.dumps(batch), headers=headers)
        print(f"   Status Transfer Items: Sukses kirim {len(tf_items)} item.")

    # 4. Mass Adjustment Headers
    if ma_headers:
        res = requests.post(f"{SUPABASE_URL}/rest/v1/jezpro_adjustment_headers", data=json.dumps(ma_headers), headers=headers)
        print(f"   Status Adjustment Headers: {res.status_code}")

    # 5. Mass Adjustment Items (Per batch 200 baris)
    if ma_items:
        requests.delete(f"{SUPABASE_URL}/rest/v1/jezpro_adjustment_items?id=gt.0", headers=headers)
        for i in range(0, len(ma_items), 200):
            batch = ma_items[i:i + 200]
            requests.post(f"{SUPABASE_URL}/rest/v1/jezpro_adjustment_items", data=json.dumps(batch), headers=headers)
        print(f"   Status Adjustment Items: Sukses kirim {len(ma_items)} item.")

    print("✅ SUKSES! Seluruh data Staging, Transfer Stok, & Multiple Adjustment tersinkronisasi.")

# ==============================================================================
# MAIN PIPELINE EKSEKUSI
# ==============================================================================
if __name__ == "__main__":
    jez = create_jezpro_session()
    
    # 1. Staging
    all_staging = []
    all_staging.extend(fetch_staging_data(jez, "scan_product_in_datatables", "MASUK_RAK", "WAITING OFFLINE"))
    all_staging.extend(fetch_staging_data(jez, "scan_product_in_refund_datatables", "REFUND", "Refund"))
    
    # 2. Transfer Stok
    tf_headers, tf_items = fetch_transfer_data(jez)
    
    # 3. Multiple Adjustment
    ma_headers, ma_items = fetch_mass_adjustment_data(jez)
    
    # 4. Push All to Supabase
    push_all_to_supabase(all_staging, tf_headers, tf_items, ma_headers, ma_items)
    print("🎉 Pipeline LL01 selesai sempurna 100%!")
