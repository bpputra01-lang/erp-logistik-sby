import io
import time
import json
import re
import urllib.request
import urllib.parse
import http.cookiejar
import pandas as pd

def fetch_jezpro_stock_excel_bytes(
    email: str = "andysilvano2406@jez.co.id",
    password: str = "999",
    store_id: int = 3,
    qty_filter: int = 1
) -> bytes:
    """
    Fungsi download otomatis dari Jezpro menggunakan library bawaan Python (urllib.request).
    100% kompatibel dengan Pyodide, Shiny, dan Docker tanpa perlu install 'requests'.
    """
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # 1. Ambil Form CSRF Token dari Halaman Login
    url_login_page = "https://jezpro.id/"
    req_init = urllib.request.Request(url_login_page, headers=headers)
    with opener.open(req_init, timeout=60) as resp:
        html_text = resp.read().decode("utf-8", errors="ignore")

    match = re.search(r'name=["\']_token["\']\s+value=["\']([^"\']+)["\']', html_text)
    if not match:
        raise Exception("CSRF Token tidak ditemukan pada halaman login Jezpro.")
    form_token = match.group(1)

    # 2. POST Login ke Jezpro
    url_action_login = "https://jezpro.id/user_login"
    login_payload = urllib.parse.urlencode({
        "_token": form_token,
        "u_email": email,
        "password": password
    }).encode("utf-8")

    req_login = urllib.request.Request(
        url_action_login,
        data=login_payload,
        headers={
            **headers,
            "Referer": url_login_page,
            "Content-Type": "application/x-www-form-urlencoded"
        }
    )
    with opener.open(req_login, timeout=60) as resp:
        pass  # Cookie sesi login tersimpan otomatis di CookieJar
    time.sleep(1.5)

    # 3. Trigger URL Export Mass Adjustment
    url_download = f"https://jezpro.id/export_mass_adjustment_template?st_id={store_id}&psc_id=&br_id=&pl_id=&qty_filter={qty_filter}"
    req_download = urllib.request.Request(
        url_download,
        headers={**headers, "Referer": "https://jezpro.id/mass_adjustment"}
    )

    with opener.open(req_download, timeout=120) as resp:
        content_type = resp.headers.get("Content-Type", "")
        raw_bytes = resp.read()

    # 4. Handle Antrean Polling (JSON Notification)
    if "application/json" in content_type:
        data_json = json.loads(raw_bytes.decode("utf-8", errors="ignore"))
        notification_id = data_json.get("notification_id")
        if not notification_id:
            raise Exception(f"Gagal mendapatkan antrean export: {data_json}")

        check_export_url = f"https://jezpro.id/notifications/{notification_id}/open-export"
        final_download_url = None

        # Handler khusus agar tidak otomatis follow redirect (untuk membaca header Location 302)
        class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
            def http_error_302(self, req, fp, code, msg, headers):
                return fp
            http_error_301 = http_error_302

        no_redirect_opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(cj),
            NoRedirectHandler
        )

        for _ in range(15):
            time.sleep(4)
            req_check = urllib.request.Request(check_export_url, headers=headers)
            try:
                with no_redirect_opener.open(req_check, timeout=60) as check_resp:
                    loc = check_resp.headers.get("Location") or ""
                    if "neo.id" in loc or loc.startswith("http"):
                        final_download_url = loc
                        break
            except Exception:
                pass

        if not final_download_url:
            raise Exception("Timeout: File Excel belum selesai digenerate oleh server Jezpro.")

        # Download File Asli dari S3
        req_s3 = urllib.request.Request(final_download_url, headers=headers)
        with urllib.request.urlopen(req_s3, timeout=300) as s3_resp:
            return s3_resp.read()

    elif "text/html" in content_type:
        raise Exception("Gagal export. Server mengirimkan HTML (sesi login ditolak/kedaluwarsa).")
    else:
        # File biner Excel langsung diterima
        return raw_bytes