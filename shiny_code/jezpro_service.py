import io
import time
import requests
from bs4 import BeautifulSoup
import pandas as pd

def fetch_jezpro_stock_excel_bytes(
    email: str = "fajarbintang786@jez.co.id",
    password: str = "131199",
    store_id: int = 3,
    qty_filter: int = 1
) -> bytes:
    """
    Menggantikan fungsi Java fetchStockData().
    Melakukan login ke jezpro.id, trigger export mass adjustment, polling antrean,
    dan mengembalikan bytes file Excel yang siap diolah.
    """
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })

    url_login_page = "https://jezpro.id/"
    url_action_login = "https://jezpro.id/user_login"
    url_download = f"https://jezpro.id/export_mass_adjustment_template?st_id={store_id}&psc_id=&br_id=&pl_id=&qty_filter={qty_filter}"

    # 1. Ambil Form CSRF Token
    resp_init = session.get(url_login_page, timeout=60)
    soup = BeautifulSoup(resp_init.text, "html.parser")
    token_tag = soup.find("input", {"name": "_token"})
    if not token_tag or not token_tag.get("value"):
        raise Exception("CSRF Token tidak ditemukan pada halaman login Jezpro.")
    form_token = token_tag["value"]

    # 2. POST Login Akun Jezpro
    login_payload = {
        "_token": form_token,
        "u_email": email,
        "password": password
    }
    session.post(url_action_login, data=login_payload, headers={"Referer": url_login_page}, timeout=60)
    time.sleep(1.5)

    # 3. Trigger URL Export
    trigger_res = session.get(url_download, headers={"Referer": "https://jezpro.id/mass_adjustment"}, timeout=120)
    content_type = trigger_res.headers.get("Content-Type", "")

    # 4. Handle Antrean Export (JSON Notification)
    if "application/json" in content_type:
        json_data = trigger_res.json()
        notification_id = json_data.get("notification_id")
        if not notification_id:
            raise Exception(f"Gagal mendapatkan notification_id: {trigger_res.text}")

        check_export_url = f"https://jezpro.id/notifications/{notification_id}/open-export"
        final_download_url = None
        max_retries = 15

        for i in range(max_retries):
            time.sleep(4)
            check_res = session.get(check_export_url, allow_redirects=False, timeout=60)
            if check_res.status_code in [301, 302]:
                loc = check_res.headers.get("Location", "")
                if "neo.id" in loc or loc.startswith("http"):
                    final_download_url = loc
                    break

        if not final_download_url:
            raise Exception("Timeout: File Excel tidak kunjung selesai digenerate oleh server Jezpro.")

        # Download File Asli dari URL S3
        dl_res = session.get(final_download_url, timeout=300)
        return dl_res.content

    elif "text/html" in content_type:
        raise Exception("Gagal export. Server mengirimkan HTML (sesi login ditolak/kedaluwarsa).")
    else:
        # Jika server langsung mengembalikan file excel biner
        return trigger_res.content