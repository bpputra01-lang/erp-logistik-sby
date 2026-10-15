import os
import json
import re
import requests
from datetime import datetime
from bs4 import BeautifulSoup

def parse_card_html(raw_html):
    """Mengekstrak BIN, Brand, dan Nama Artikel murni dari HTML Jezpro"""
    if not raw_html or "<" not in str(raw_html):
        return {"article": str(raw_html).strip(), "brand": "-", "bin": "-"}

    soup = BeautifulSoup(str(raw_html), "html.parser")
    
    # 1. Ekstrak BIN target (ada di title="Bin Code")
    bin_el = soup.find(attrs={"title": "Bin Code"})
    bin_val = bin_el.get_text(strip=True) if bin_el else None

    # 2. Ekstrak Brand (misal [ORTUSEIGHT])
    m_brand = re.search(r'\[(.*?)\]', str(raw_html))
    brand_val = m_brand.group(1).strip() if m_brand else "-"

    # 3. Ekstrak Nama Artikel Bersih
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

    return {
        "article": article_val,
        "brand": brand_val,
        "bin": bin_val
    }
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
JEZPRO_EMAIL = os.environ.get("JEZPRO_EMAIL")
JEZPRO_PASS  = os.environ.get("JEZPRO_PASSWORD")

def create_jezpro_session():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })
    
    print("🔐 [1/4] Melakukan login ke Jezpro...")
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
    
    # BUKA HALAMAN HELPER DULU AGAR SESI TOKO AKTIF DI LARAVEL
    print("🔄 Mengaktifkan sesi gudang (helper_backup)...")
    session.get("https://jezpro.id/helper_backup")
    
    return session

def fetch_data(session, endpoint_path, kategori_label, waiting_val):
    print(f"📥 [2/4] Menarik data [{kategori_label}] (waiting='{waiting_val}')...")
    url = f"https://jezpro.id/{endpoint_path}"
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://jezpro.id/helper_backup"
    }
    
    # PARAMETER LENGKAP PERSIS SEPERTI DEVTOOLS FIREFOX (MENCEGAH HTTP 500)
    params = {
        "draw": "1",
        "columns[0][data]": "article",
        "columns[0][name]": "article",
        "columns[0][searchable]": "true",
        "columns[0][orderable]": "false",
        "columns[0][search][value]": "",
        "columns[0][search][regex]": "false",
        "order[0][column]": "0",
        "order[0][dir]": "desc",
        "start": "0",
        "length": "5000",
        "search": "",
        "st_id": "",
        "waiting": waiting_val
    }

    res = session.get(url, params=params, headers=headers)
    if res.status_code != 200:
        print(f"⚠️ Gagal panggil {kategori_label}: HTTP {res.status_code}")
        print(f"   Pesan Error Server: {res.text[:300]}")
        return []
    
    try:
        res_json = res.json()
    except Exception as e:
        print(f"⚠️ Respon bukan JSON: {res.text[:200]}")
        return []

    raw_list = res_json.get("data", [])
    print(f"   -> BERHASIL! Ditemukan {len(raw_list)} baris data pada {kategori_label}!")

    clean_records = []
    for idx_item, item in enumerate(raw_list):
        raw_art = item.get("article") or item.get("art_name") or "-"
        parsed = parse_card_html(raw_art)

        p_id = (
            item.get("plst_id") or 
            item.get("pls_id") or 
            item.get("id") or 
            item.get("plstr_id")
        )
        if not p_id:
            p_id = abs(hash(f"{kategori_label}_{parsed['article']}_{idx_item}")) % (10**10)

        clean_records.append({
            "plst_id": int(p_id),
            "pls_id": int(item.get("pls_id") or p_id),
            "kategori": kategori_label,
            "waiting_status": item.get("waiting") or waiting_val,
            "brand": parsed["brand"] if parsed["brand"] != "-" else (item.get("brand") or "-"),
            "article_name": parsed["article"],
            "qty": int(item.get("plst_qty") or item.get("qty") or 1),
            "bin_target": parsed["bin"] if parsed["bin"] != "-" else (item.get("rack_name") or item.get("bin") or "-"),
            "pic_name": item.get("user_name") or item.get("scanned_by") or "Petugas",
            "scanned_at": item.get("created_at") or item.get("date") or datetime.now().isoformat(),
            "store_id": 3,
            "raw_json": item,
            "synced_at": datetime.now().isoformat()
        }) 
    return clean_records

def push_to_supabase(records):
    print(f"🚀 [3/4] Mengirim {len(records)} baris data ke Supabase...")
    if not records:
        print("⚠️ Data kosong, tidak ada yang dikirim ke Supabase.")
        return
        
    url = f"{SUPABASE_URL}/rest/v1/jezpro_waiting_staging"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates"
    }
    
    res = requests.post(url, data=json.dumps(records), headers=headers)
    if res.status_code in [200, 201]:
        print(f"✅ SUKSES BESAR! {len(records)} baris berhasil masuk ke Supabase.")
    else:
        print(f"❌ Supabase Error [{res.status_code}]: {res.text}")
        raise Exception(f"Gagal simpan ke Supabase: {res.text}")

if __name__ == "__main__":
    jez = create_jezpro_session()
    
    semua_data = []
    
    # 1. Tarik Scan Barang Masuk
    data_masuk = fetch_data(jez, "scan_product_in_datatables", "MASUK_RAK", waiting_val="WAITING OFFLINE")
    semua_data.extend(data_masuk)
    
    # 2. Tarik Scan Barang Masuk Refund
    data_refund = fetch_data(jez, "scan_product_in_refund_datatables", "REFUND", waiting_val="Refund")
    semua_data.extend(data_refund)
    
    # 3. Kirim ke Supabase
    push_to_supabase(semua_data)
    print(f"🎉 [4/4] Selesai! Total {len(semua_data)} baris berhasil diproses.")
