import os
import json
import requests
from datetime import datetime
from bs4 import BeautifulSoup

# Ambil kredensial dari GitHub Secrets
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
JEZPRO_EMAIL = os.environ.get("JEZPRO_EMAIL")
JEZPRO_PASS  = os.environ.get("JEZPRO_PASSWORD")

def create_jezpro_session():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
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
    return session

def fetch_data(session, endpoint_path, kategori_label, waiting_val=""):
    print(f"📥 [2/4] Menarik data [{kategori_label}]...")
    url = f"https://jezpro.id/{endpoint_path}"
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://jezpro.id/helper_backup"
    }
    params = {
        "draw": 1,
        "start": 0,
        "length": 5000,
        "st_id": "3",                 # Store Surabaya
        "order[0][column]": 0,
        "order[0][dir]": "desc"
    }

    # Kosongkan jika refund agar seluruh Retur & Cancel Packing ikut terambil
    if waiting_val:
        params["waiting"] = waiting_val

    res = session.get(url, params=params, headers=headers)
    if res.status_code != 200:
        print(f"⚠️ Warning: Gagal memanggil {kategori_label} (HTTP {res.status_code})")
        return []
    
    raw_list = res.json().get("data", [])
    print(f"   -> Ditemukan {len(raw_list)} baris data pada {kategori_label}.")
    
    clean_records = []
    for item in raw_list:
        p_id = item.get("plst_id") or item.get("pls_id") or item.get("id")
        if not p_id:
            continue
            
        clean_records.append({
            "plst_id": int(p_id),
            "pls_id": item.get("pls_id") or int(p_id),
            "kategori": kategori_label,
            "waiting_status": item.get("waiting") or item.get("status") or ("REFUND" if kategori_label == "REFUND" else "WAITING"),
            "brand": item.get("brand") or item.get("br_name") or "-",
            "article_name": item.get("article") or item.get("art_name") or item.get("product_name") or "-",
            "qty": int(item.get("plst_qty") or item.get("qty") or 1),
            "bin_target": item.get("rack_name") or item.get("bin") or item.get("lokasi") or "-",
            "pic_name": item.get("user_name") or item.get("scanned_by") or item.get("name") or "Petugas",
            "scanned_at": item.get("created_at") or item.get("date") or datetime.now().isoformat(),
            "store_id": 3,
            "raw_json": item,
            "synced_at": datetime.now().isoformat()
        })
    return clean_records

def push_to_supabase(records):
    print(f"🚀 [3/4] Mengirim {len(records)} baris data ke Supabase...")
    if not records:
        print("ℹ️ Tidak ada item waiting saat ini. Melewati pengiriman.")
        return
        
    url = f"{SUPABASE_URL}/rest/v1/jezpro_waiting_staging"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates" # Upsert otomatis
    }
    
    res = requests.post(url, data=json.dumps(records), headers=headers)
    if res.status_code in [200, 201]:
        print("✅ SUKSES! Data berhasil di-update ke tabel jezpro_waiting_staging.")
    else:
        print(f"❌ Supabase Error [{res.status_code}]: {res.text}")

if __name__ == "__main__":
    jez = create_jezpro_session()
    
    semua_data = []
    # 1. Ambil Masuk Rak (kosongkan filter waiting agar seluruh item masuk)
    semua_data.extend(fetch_data(jez, "scan_product_in_datatables", "MASUK_RAK", waiting_val=""))
    # 2. Ambil Refund (RETUR & CANCEL PACKING)
    semua_data.extend(fetch_data(jez, "scan_product_in_refund_datatables", "REFUND", waiting_val=""))
    
    # 3. Kirim ke Supabase
    push_to_supabase(semua_data)
    print("🎉 [4/4] Sinkronisasi selesai sempurna!")
