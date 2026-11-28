import os
import re
import time
from datetime import date, datetime, timedelta, timezone
from bs4 import BeautifulSoup
import pandas as pd
import requests

# ==============================================================================
# 🔑 KREDENSIAL & KONFIGURASI PUSAT
# ==============================================================================
SUPABASE_URL = os.environ.get(
    "SUPABASE_URL", "https://fanzsmghhbefhhaicrok.supabase.co"
)
SUPABASE_KEY = os.environ.get(
    "SUPABASE_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZhbnpzbWdoaGJlZmhoYWljcm9rIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODgxNTQzNDgsImV4cCI6MjEwMzczMDM0OH0.brCSOO9nHAUK8CxDWPperpJ--_NA_nwy5cO9OqGv3I0",
)

JEZPRO_EMAIL = os.environ.get("JEZPRO_EMAIL", "fajarbintang786@jez.co.id")
JEZPRO_PASSWORD = os.environ.get("JEZPRO_PASSWORD", "131199")

STORE_ID_SURABAYA = 3
WIB = timezone(timedelta(hours=7))

# Mapping Semua Cabang Resmi Jezpro
BRANCH_MAP = {
    "JEZ SURABAYA": 3,
    "JEZ SEMARANG": 53,
    "JEZ SIDOARJO": 8,
    "JEZ KEDIRI": 5,
    "JEZ MALANG": 2,
    "JEZ JEMBER": 40,
    "HUB JAKARTA": 55,
    "ONLINE HUB SURABAYA": 30,
    "ONLINE HUB MALANG": 20,
}

HEADERS_SB = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates",
}

PATTERN_MISS_LOC = re.compile(r"mis+[\s\-_]*loc", re.IGNORECASE)


# ==============================================================================
# HELPER PEMBERSIH & PARSER UNIVERSAL
# ==============================================================================
def strip_html(val):
    if not val:
        return ""
    s = str(val)
    if "<" in s:
        s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"\s+", " ", s).strip()


def parse_datetime(dt_str):
    if not dt_str:
        return datetime.now(WIB).strftime("%Y-%m-%d %H:%M:%S")
    clean = strip_html(dt_str).strip()
    for fmt in ("%d-%m-%Y %H:%M:%S", "%d/%m/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(clean[:19], fmt).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        except Exception:
            pass
    try:
        return pd.to_datetime(clean, dayfirst=True).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    except Exception:
        return datetime.now(WIB).strftime("%Y-%m-%d %H:%M:%S")


def clean_article_name(raw_text):
    if not raw_text:
        return "-"
    t = strip_html(raw_text)
    t = re.sub(
        r"\b(WAITING OFFLINE|WAITING|REFUND|JEZ SURABAYA|Jml\s*:\s*\d+)\b",
        "",
        t,
        flags=re.IGNORECASE,
    )
    return " ".join(t.split()).strip() or "-"


# ==============================================================================
# AUTENTIKASI KE JEZPRO
# ==============================================================================
def create_jezpro_session():
    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
            " Safari/537.36"
        )
    })
    print(
        f"🔐 [{datetime.now(WIB).strftime('%H:%M:%S')}] Login ke Jezpro"
        f" ({JEZPRO_EMAIL})..."
    )
    res = session.get("https://jezpro.id/", timeout=20)
    soup = BeautifulSoup(res.text, "html.parser")
    token_tag = soup.find("input", {"name": "_token"})
    if not token_tag:
        raise Exception("Gagal mendapatkan CSRF Token Jezpro!")

    session.post(
        "https://jezpro.id/user_login",
        data={
            "_token": token_tag["value"],
            "u_email": JEZPRO_EMAIL,
            "password": JEZPRO_PASSWORD,
        },
        timeout=20,
    )
    session.get("https://jezpro.id/setup_lokasi_stok_v2", timeout=15)
    session.get("https://jezpro.id/stock_tracking", timeout=15)
    print("✅ Berhasil login Jezpro!\n")
    return session


def relogin_jezpro(session):
    try:
        res = session.get("https://jezpro.id/", timeout=20)
        soup = BeautifulSoup(res.text, "html.parser")
        token_tag = soup.find("input", {"name": "_token"})
        if not token_tag:
            return False

        session.post(
            "https://jezpro.id/user_login",
            data={
                "_token": token_tag["value"],
                "u_email": JEZPRO_EMAIL,
                "password": JEZPRO_PASSWORD,
            },
            timeout=20,
        )
        session.get("https://jezpro.id/setup_lokasi_stok_v2", timeout=15)
        session.get("https://jezpro.id/stock_tracking", timeout=15)
        return True
    except Exception:
        return False


# ==============================================================================
# MODUL 1: SINKRONISASI MUTASI SETUP (ALL CABANG MISS LOC + SURABAYA ALL)
# ==============================================================================
def execute_sync_mutasi(session, days_back: int = 90, batch_upload_size: int = 500):
    today = date.today()
    date_list = [
        (today - timedelta(days=i)).strftime("%Y-%m-%d")
        for i in range(days_back)
    ]

    print("=" * 85)
    print(
        f"🚀 [MODUL 1] SINKRONISASI MUTASI SETUP ({days_back} HARI: {date_list[-1]} s/d"
        f" {date_list[0]})"
    )
    print("   -> Cabang Lain      : HANYA Miss Location (Bukan Karantina)")
    print("   -> Khusus SURABAYA  : SEMUA MUTASI SETUP DITARIK TANPA FILTER")
    print("=" * 85)

    url_history = "https://jezpro.id/bin_history_datatables"
    headers_req = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://jezpro.id/setup_lokasi_stok_v2",
    }

    all_matched_records = []
    start_time_all = time.time()
    count_surabaya_all = 0
    count_cabang_missloc = 0

    for b_idx, (branch_name, st_id) in enumerate(BRANCH_MAP.items(), start=1):
        is_surabaya = st_id == STORE_ID_SURABAYA
        mode_desc = "SEMUA MUTASI (TANPA FILTER)" if is_surabaya else "Miss Location Only"
        print(
            f"\n🏢 [{b_idx}/{len(BRANCH_MAP)}] Memeriksa: {branch_name} (ID:"
            f" {st_id}) [{mode_desc}]"
        )
        branch_found = 0

        for d_idx, target_date in enumerate(date_list, start=1):
            params = {
                "draw": str(d_idx),
                "columns[0][data]": "DT_RowIndex",
                "columns[0][name]": "pmt_id",
                "columns[0][orderable]": "true",
                "columns[1][data]": "u_name",
                "columns[1][name]": "u_name",
                "columns[1][orderable]": "true",
                "columns[2][data]": "article",
                "columns[2][name]": "article",
                "columns[2][orderable]": "false",
                "columns[3][data]": "ps_barcode",
                "columns[3][name]": "ps_barcode",
                "columns[3][orderable]": "false",
                "columns[4][data]": "st_name",
                "columns[4][name]": "st_name",
                "columns[4][orderable]": "true",
                "columns[5][data]": "start_bin",
                "columns[5][name]": "start_bin",
                "columns[5][orderable]": "false",
                "columns[6][data]": "pmt_old_qty",
                "columns[6][name]": "pmt_old_qty",
                "columns[6][orderable]": "false",
                "columns[7][data]": "pmt_qty",
                "columns[7][name]": "pmt_qty",
                "columns[7][orderable]": "false",
                "columns[8][data]": "pmt_old_qty_new",
                "columns[8][name]": "pmt_old_qty_new",
                "columns[8][orderable]": "false",
                "columns[9][data]": "end_bin",
                "columns[9][name]": "end_bin",
                "columns[9][orderable]": "false",
                "columns[10][data]": "notes",
                "columns[10][name]": "notes",
                "columns[10][orderable]": "false",
                "columns[11][data]": "pm_created_at",
                "columns[11][name]": "pm_created_at",
                "columns[11][orderable]": "false",
                "order[0][column]": "0",
                "order[0][dir]": "desc",
                "start": "0",
                "length": "1000",
                "search[value]": "",
                "search": "",
                "st_id": str(st_id),
                "date": target_date,
                "history_bin_start": "",
                "history_bin_end": "",
                "_": int(time.time() * 1000),
            }

            try:
                resp = session.get(
                    url_history, headers=headers_req, params=params, timeout=25
                )

                if resp.status_code in [401, 419] or "login" in resp.url:
                    if relogin_jezpro(session):
                        resp = session.get(
                            url_history,
                            headers=headers_req,
                            params=params,
                            timeout=25,
                        )

                if resp.status_code != 200:
                    continue

                raw_json = resp.json().get("data", [])

                for item in raw_json:
                    note_text = strip_html(item.get("notes") or "")
                    start_bin = strip_html(item.get("start_bin") or "").upper()
                    end_bin = strip_html(item.get("end_bin") or "").upper()

                    # Filter Aturan:
                    # Surabaya = Ambil SEMUA mutasi tanpa filter catatan apa pun
                    # Cabang lain = Hanya miss location & bukan karantina
                    if is_surabaya:
                        is_matched = True
                        count_surabaya_all += 1
                    else:
                        is_miss_loc = bool(PATTERN_MISS_LOC.search(note_text))
                        is_karantina = "KARANTINA" in end_bin
                        is_matched = is_miss_loc and (not is_karantina)
                        if is_matched:
                            count_cabang_missloc += 1

                    if is_matched:
                        clean_dt = parse_datetime(item.get("pm_created_at"))
                        try:
                            q_val = int(item.get("pmt_qty", 1))
                        except Exception:
                            q_val = 1

                        pmt_id_raw = item.get("pmt_id") or item.get("id")
                        try:
                            pmt_id_val = int(pmt_id_raw) if pmt_id_raw else None
                        except Exception:
                            pmt_id_val = None

                        all_matched_records.append({
                            "pmt_id": pmt_id_val,
                            "tanggal": clean_dt,
                            "cabang": branch_name,
                            "user_name": strip_html(item.get("u_name", "-")),
                            "sku": (
                                strip_html(item.get("ps_barcode", "-"))
                                .split(".")[0]
                                .upper()
                            ),
                            "artikel": strip_html(item.get("article", "-")),
                            "bin_awal": start_bin,
                            "qty_mutasi": q_val,
                            "bin_tujuan": end_bin,
                            "catatan": note_text,
                        })
                        branch_found += 1

                pct_date = int((d_idx / len(date_list)) * 100)
                print(
                    f"\r   ➔ [{pct_date:02d}%] Tgl {target_date} (Ditemukan:"
                    f" {branch_found} baris)",
                    end="",
                    flush=True,
                )
                time.sleep(0.02)

            except Exception:
                continue

        print(f"\n   ✅ Selesai {branch_name}: Total {branch_found} baris tertangkap.")

    total_scraped = len(all_matched_records)
    durasi = int(time.time() - start_time_all)
    print(f"\n📊 Rangkuman Sesi Mutasi Setup ({durasi} detik):")
    print(f"   -> Mutasi All Surabaya      : {count_surabaya_all:,} baris")
    print(f"   -> Miss Location Cabang Lain : {count_cabang_missloc:,} baris")
    print(f"   -> TOTAL DATA MUTASI TERKUMPUL: {total_scraped:,} baris\n")

    if total_scraped == 0:
        print("ℹ️ Tidak ada data mutasi yang perlu diunggah.")
        return

    # Bersihkan duplikat lokal sebelum upload
    df_upload = pd.DataFrame(all_matched_records).drop_duplicates(
        subset=["tanggal", "sku", "bin_awal", "bin_tujuan", "qty_mutasi"]
    )
    records_to_upload = df_upload.to_dict(orient="records")

    print("🗑️ Menghapus data lama di Supabase 'jezpro_miss_location_logs'...")
    try:
        requests.delete(
            f"{SUPABASE_URL}/rest/v1/jezpro_miss_location_logs?id=gt.0",
            headers=HEADERS_SB,
            timeout=30,
        )
    except Exception as e:
        print(f"   ⚠️ Gagal clear data lama: {e}")

    print("📤 Mengunggah data terbaru ke 'jezpro_miss_location_logs'...")
    inserted_count = 0
    upsert_url = f"{SUPABASE_URL}/rest/v1/jezpro_miss_location_logs?on_conflict=tanggal,sku,bin_awal,bin_tujuan,qty_mutasi"

    for i in range(0, len(records_to_upload), batch_upload_size):
        chunk = records_to_upload[i : i + batch_upload_size]
        try:
            res_up = requests.post(upsert_url, headers=HEADERS_SB, json=chunk, timeout=60)
            if res_up.status_code in [200, 201, 204]:
                inserted_count += len(chunk)
            else:
                print(f"   ⚠️ Gagal batch {i}: {res_up.status_code}")
        except Exception as e:
            print(f"   ⚠️ Kendala upload: {e}")

    print(f"🎉 Sukses mengunggah {inserted_count:,} baris Mutasi Setup ke Supabase!\n")


# ==============================================================================
# MODUL 2: SCRAPING STOCK TRACKING SURABAYA (KHUSUS INSTOCK 3 BULAN TERAKHIR)
# ==============================================================================
def execute_sync_surabaya_instock(session, days_back: int = 90, batch_upload_size: int = 500):
    now_dt = datetime.now(WIB)
    start_date = now_dt - timedelta(days=days_back)
    p_start = start_date.strftime("%Y-%m-%d")
    p_end = now_dt.strftime("%Y-%m-%d")
    date_range = f"{p_start}|{p_end}"

    print("=" * 85)
    print(f"📦 [MODUL 2] SCRAPING STOCK TRACKING SURABAYA (STATUS INSTOCK)")
    print(f"   -> Periode: {p_start} s/d {p_end} (90 Hari Terakhir)")
    print("=" * 85)

    url_dt = "https://jezpro.id/stock_tracking_datatables"
    headers_dt = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://jezpro.id/stock_tracking",
    }

    instock_records = []
    start_row = 0
    batch_size = 1000
    draw_count = 1
    total_expected = 999999

    while start_row < total_expected:
        params = {
            "draw": str(draw_count),
            "columns[0][data]": "DT_RowIndex", "columns[0][name]": "plst_id", "columns[0][orderable]": "false",
            "columns[1][data]": "datetime", "columns[1][name]": "plst_created", "columns[1][orderable]": "true",
            "columns[2][data]": "ps_barcode", "columns[2][name]": "ps_barcode", "columns[2][orderable]": "true",
            "columns[3][data]": "article", "columns[3][name]": "p_name", "columns[3][orderable]": "true",
            "columns[4][data]": "invoice", "columns[4][name]": "p_name", "columns[4][orderable]": "true",
            "columns[5][data]": "cust_name", "columns[5][name]": "cust_name", "columns[5][orderable]": "true",
            "columns[6][data]": "qty", "columns[6][name]": "p_name", "columns[6][orderable]": "true",
            "columns[7][data]": "product_location", "columns[7][name]": "pl_code", "columns[7][orderable]": "true",
            "columns[8][data]": "status", "columns[8][name]": "plst_status", "columns[8][orderable]": "true",
            "columns[9][data]": "instock_source", "columns[9][name]": "instock_source_status",
            "order[0][column]": "1", "order[0][dir]": "desc",
            "start": str(start_row),
            "length": str(batch_size),
            "status": "INSTOCK",
            "st_id": str(STORE_ID_SURABAYA),
            "date": date_range,
        }

        try:
            res = session.get(url_dt, params=params, headers=headers_dt, timeout=35)
            if res.status_code in [401, 419] or "login" in res.url:
                if relogin_jezpro(session):
                    res = session.get(url_dt, params=params, headers=headers_dt, timeout=35)

            if res.status_code != 200:
                print(f"   ⚠️ Stock tracking gagal HTTP {res.status_code} pada start={start_row}")
                break

            j_data = res.json()
            chunk = j_data.get("data", [])
            total_expected = int(j_data.get("recordsFiltered") or j_data.get("recordsTotal") or 0)

            if not chunk:
                break

            for item in chunk:
                status_raw = ""
                raw_sku = ""
                raw_qty = 1
                inv_val = ""
                raw_art = ""
                raw_loc = ""
                raw_cust = ""
                raw_dt = ""
                raw_id = None

                if isinstance(item, dict):
                    raw_id = item.get("plst_id") or item.get("id")
                    status_raw = strip_html(item.get("status") or item.get("plst_status") or "").upper()
                    raw_sku = strip_html(item.get("ps_barcode") or item.get("barcode") or item.get("sku") or "")
                    raw_qty = item.get("qty", 1)
                    inv_val = strip_html(item.get("invoice") or "")
                    raw_art = item.get("article") or item.get("p_name") or ""
                    raw_loc = strip_html(item.get("product_location") or item.get("pl_code") or "")
                    raw_cust = strip_html(item.get("cust_name") or "-")
                    raw_dt = item.get("datetime") or item.get("plst_created") or ""
                elif isinstance(item, list) and len(item) > 8:
                    raw_id = item[0]
                    raw_dt = item[1]
                    raw_sku = strip_html(item[2])
                    raw_art = item[3]
                    inv_val = strip_html(item[4])
                    raw_cust = strip_html(item[5])
                    raw_qty = item[6]
                    raw_loc = strip_html(item[7])
                    status_raw = strip_html(item[8]).upper()

                # Filter Note / Status: Hanya ambil INSTOCK & bukan WAITING
                is_instock = ("INSTOCK" in status_raw) and ("WAITING" not in status_raw)
                if not is_instock:
                    continue

                sku_clean = raw_sku.split(".")[0].strip().upper()
                if not sku_clean or sku_clean in ["-", "NAN", "NONE", "NULL", ""]:
                    continue

                try:
                    p_id_int = int(strip_html(raw_id)) if raw_id else None
                except Exception:
                    p_id_int = None

                try:
                    qty_int = int(round(float(str(raw_qty).replace("Rp", "").strip())))
                except Exception:
                    qty_int = 1

                instock_records.append({
                    "plst_id": p_id_int,
                    "datetime": parse_datetime(raw_dt),
                    "cabang": "JEZ SURABAYA",
                    "barcode_sku": sku_clean,
                    "article": clean_article_name(raw_art),
                    "invoice": inv_val or "-",
                    "cust_name": raw_cust,
                    "qty": qty_int,
                    "product_location": raw_loc.replace("[", "").replace("]", "").strip() or "STAGING INBOUND",
                    "status": status_raw,
                    "notes": "INSTOCK",
                    "synced_at": datetime.now(WIB).isoformat(),
                })

            start_row += len(chunk)
            draw_count += 1
            print(
                f"\r   ➔ Mengambil Stock Tracking... {min(start_row, total_expected):,}/{total_expected:,} data",
                end="",
                flush=True,
            )
            time.sleep(0.04)

        except Exception as e:
            print(f"\n   ⚠️ Terjadi error stock tracking: {e}")
            break

    print(f"\n   -> Selesai! Ditemukan {len(instock_records):,} baris data INSTOCK Surabaya.")

    if not instock_records:
        return

    # Bersihkan duplikat lokal
    df_instock = pd.DataFrame(instock_records).drop_duplicates(
        subset=["datetime", "barcode_sku", "product_location", "status", "qty"]
    )
    records_to_upload = df_instock.to_dict(orient="records")

    target_table = "jezpro_surabaya_instock_tracking"
    print(f"🗑️ Membersihkan data lama di tabel Supabase '{target_table}'...")
    try:
        requests.delete(f"{SUPABASE_URL}/rest/v1/{target_table}?id=gt.0", headers=HEADERS_SB, timeout=30)
    except Exception as e:
        print(f"   ⚠️ Catatan: {e}")

    print(f"📤 Mengunggah {len(records_to_upload):,} baris ke '{target_table}'...")
    inserted_count = 0
    for i in range(0, len(records_to_upload), batch_upload_size):
        chunk = records_to_upload[i : i + batch_upload_size]
        try:
            res_up = requests.post(f"{SUPABASE_URL}/rest/v1/{target_table}", headers=HEADERS_SB, json=chunk, timeout=60)
            if res_up.status_code in [200, 201, 204]:
                inserted_count += len(chunk)
        except Exception as e:
            print(f"   ⚠️ Upload batch error: {e}")

    print(f"🎉 Sukses mengunggah {inserted_count:,} baris Stock Tracking Surabaya ke Supabase!\n")


# ==============================================================================
# MAIN LOOP: BERJALAN OTOMATIS TIAP 2 JAM SEKALI
# ==============================================================================
if __name__ == "__main__":
    INTERVAL_DETIK = 7200  # 2 jam = 7200 detik

    print("=" * 85)
    print("🔄 DAEMON SINKRONISASI JEZPRO INTEGRATED")
    print("   1. Modul Mutasi Setup : Surabaya (Semua) + Cabang Lain (Miss Location Only)")
    print("   2. Modul Stock Tracking : Khusus Surabaya (Status INSTOCK)")
    print("   Periode Rentang       : 90 Hari (3 Bulan Terakhir)")
    print("   Jadwal Interval       : Tiap 2 Jam Sekali")
    print("=" * 85)

    jez = create_jezpro_session()

    while True:
        try:
            # 1. Jalankan Modul Mutasi Setup
            execute_sync_mutasi(jez, days_back=90)

            # 2. Jalankan Modul Stock Tracking Surabaya Instock
            execute_sync_surabaya_instock(jez, days_back=90)

        except Exception as e_main:
            print(f"❌ Terjadi kesalahan runtime: {e_main}")

        waktu_berikutnya = (
            datetime.now(WIB) + timedelta(seconds=INTERVAL_DETIK)
        ).strftime("%H:%M:%S")
        print(
            "💤 Selesai satu siklus. Standby 2 jam. Jadwal berikutnya: pukul"
            f" {waktu_berikutnya} WIB...\n"
        )
        time.sleep(INTERVAL_DETIK)