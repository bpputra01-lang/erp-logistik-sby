import os
import io
import time
import json
import requests
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://fanzsmghhbefhhaicrok.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
JEZPRO_EMAIL = os.environ.get("JEZPRO_EMAIL", "fajarbintang786@jez.co.id")
JEZPRO_PASSWORD = os.environ.get("JEZPRO_PASSWORD", "")

# DAFTAR SEMUA CABANG DAN ID JEZPRO
BRANCH_MAP = {
    "JEZ SURABAYA": {"st_id": 3, "db_id": "SURABAYA_LATEST"},
    "JEZ MALANG": {"st_id": 2, "db_id": "MALANG_LATEST"},
    "JEZ SIDOARJO": {"st_id": 8, "db_id": "SIDOARJO_LATEST"},
    "JEZ KEDIRI": {"st_id": 5, "db_id": "KEDIRI_LATEST"},
    "JEZ JEMBER": {"st_id": 40, "db_id": "JEMBER_LATEST"},
    "JEZ SEMARANG": {"st_id": 53, "db_id": "SEMARANG_LATEST"},
}

def run_sync():
    print(f"[{datetime.now()}] Memulai sinkronisasi stok ALL BRANCHES Jezpro...")
    
    if not JEZPRO_PASSWORD or not SUPABASE_KEY:
        raise ValueError("JEZPRO_PASSWORD atau SUPABASE_KEY belum disetel di GitHub Secrets!")

    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })
    
    # 1. Ambil Token CSRF
    print("1. Mengambil CSRF token login...")
    r_init = s.get("https://jezpro.id/", timeout=60)
    soup = BeautifulSoup(r_init.text, "html.parser")
    token_tag = soup.find("input", {"name": "_token"})
    if not token_tag:
        raise Exception("Gagal mendapatkan CSRF Token dari halaman login Jezpro.")
    token = token_tag["value"]

    # 2. Login Cukup Sekali Saja
    print("2. Login ke akun Jezpro...")
    s.post("https://jezpro.id/user_login", data={
        "_token": token,
        "u_email": JEZPRO_EMAIL,
        "password": JEZPRO_PASSWORD
    }, timeout=60)

    # 3. Loop Tarik Data Masing-Masing Cabang
    headers_sb = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates"
    }

    for branch_name, info in BRANCH_MAP.items():
        st_id = info["st_id"]
        db_id = info["db_id"]
        print(f"\n==========================================")
        print(f"Memproses Cabang: {branch_name} (st_id = {st_id})")
        print(f"==========================================")

        try:
            url_export = f"https://jezpro.id/export_mass_adjustment_template?st_id={st_id}&psc_id=&br_id=&pl_id=&qty_filter=1"
            r_exp = s.get(url_export, headers={"Referer": "https://jezpro.id/mass_adjustment"}, timeout=300)

            excel_bytes = None
            content_type = r_exp.headers.get("Content-Type", "")

            if "application/json" in content_type:
                notif_id = r_exp.json().get("notification_id")
                check_url = f"https://jezpro.id/notifications/{notif_id}/open-export"
                final_url = ""

                for i in range(12):
                    time.sleep(5)
                    r_chk = s.get(check_url, allow_redirects=False, timeout=60)
                    loc = r_chk.headers.get("Location", "")
                    if r_chk.status_code == 302 and "neo.id" in loc:
                        final_url = loc
                        break
                    print(f"Menunggu proses export {branch_name}... ({i+1})")

                if not final_url:
                    print(f"⚠️ Lewati {branch_name}: Timeout pembuatan file oleh Jezpro.")
                    continue

                r_file = requests.get(final_url, timeout=300)
                excel_bytes = r_file.content
            else:
                excel_bytes = r_exp.content

            # Parse ke DataFrame
            df = pd.read_excel(io.BytesIO(excel_bytes))
            df["STORE_NAME"] = branch_name
            payload_data = df.fillna("").to_dict(orient="records")
            print(f"Berhasil baca {len(payload_data):,} baris untuk {branch_name}.")

            # Kirim ke Supabase
            body = {
                "id": db_id,
                "branch": branch_name,
                "updated_at": datetime.now().isoformat(),
                "total_rows": len(payload_data),
                "stock_data": payload_data
            }
            sb_res = requests.post(
                f"{SUPABASE_URL}/rest/v1/stock_live_cache",
                headers=headers_sb,
                data=json.dumps(body),
                timeout=120
            )
            if sb_res.status_code in [200, 201]:
                print(f"✅ Berhasil simpan ke Supabase ({db_id})!")
            else:
                print(f"⚠️ Gagal simpan ke Supabase ({sb_res.status_code}): {sb_res.text}")

        except Exception as e:
            print(f"❌ Error saat menarik {branch_name}: {e}")

    print("\n🎉 SINKRONISASI SEMUA CABANG SELESAI!")

if __name__ == "__main__":
    run_sync()
