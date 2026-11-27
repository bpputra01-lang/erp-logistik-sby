from datetime import date, datetime, timedelta, timezone
import os
import re
import time
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
# HELPER PEMBERSIH & PARSER
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
        return True
    except Exception:
        return False


# ==============================================================================
# FUNGSI UTAMA SINKRONISASI (ALL CABANG MISS LOC + KHUSUS SURABAYA OFF/ONL/TOKO)
# ==============================================================================
def execute_sync_all(session, days_back: int = 60, batch_upload_size: int = 500):
    today = date.today()
    date_list = [
        (today - timedelta(days=i)).strftime("%Y-%m-%d")
        for i in range(days_back)
    ]

    print("=" * 85)
    print(
        f"🚀 SINKRONISASI MUTASI SETUP (2 BULAN: {date_list[-1]} s/d"
        f" {date_list[0]})"
    )
    print(
        f"   -> Semua Cabang ({len(BRANCH_MAP)}) : Miss Location (Bukan"
        " Karantina)"
    )
    print(
        "   -> Khusus SURABAYA  : + Masuk OFF/ONL (Beda Asal) & Masuk TOKO"
        " (Non-Missloc)"
    )
    print("=" * 85 + "\n")

    url_history = "https://jezpro.id/bin_history_datatables"
    headers_req = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://jezpro.id/setup_lokasi_stok_v2",
    }

    all_matched_records = []
    start_time_all = time.time()

    count_rule_missloc = 0
    count_rule_off_onl = 0
    count_rule_toko = 0

    for b_idx, (branch_name, st_id) in enumerate(BRANCH_MAP.items(), start=1):
        is_surabaya = st_id == STORE_ID_SURABAYA
        mode_desc = (
            "MissLoc + OFF/ONL + TOKO" if is_surabaya else "Miss Location Only"
        )
        print(
            f"🏢 [{b_idx}/{len(BRANCH_MAP)}] Memeriksa: {branch_name} (ID:"
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

                    is_miss_loc = bool(PATTERN_MISS_LOC.search(note_text))
                    is_karantina = "KARANTINA" in end_bin

                    # ----------------------------------------------------------
                    # ATURAN 1 (BERLAKU UNTUK SEMUA CABANG): MISS LOCATION
                    # ----------------------------------------------------------
                    rule_1 = is_miss_loc and (not is_karantina)

                    # ----------------------------------------------------------
                    # ATURAN 2 & 3 (KHUSUS CABANG SURABAYA SAJA)
                    # ----------------------------------------------------------
                    rule_2 = False
                    rule_3 = False
                    if is_surabaya:
                        # Masuk OFF/ONL namun tidak berasal dari jenis yang sama
                        rule_2_off = ("OFF" in end_bin) and (
                            "OFF" not in start_bin
                        )
                        rule_2_onl = ("ONL" in end_bin) and (
                            "ONL" not in start_bin
                        )
                        rule_2 = (rule_2_off or rule_2_onl) and (
                            not is_karantina
                        )

                        # Masuk TOKO dengan catatan bukan Miss Location
                        rule_3 = ("TOKO" in end_bin) and (not is_miss_loc)

                    if rule_1 or rule_2 or rule_3:
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

                        if rule_1:
                            count_rule_missloc += 1
                        elif rule_2:
                            count_rule_off_onl += 1
                        elif rule_3:
                            count_rule_toko += 1

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

                time.sleep(0.03)

            except Exception:
                continue

        print(
            f"\n   ✅ Selesai {branch_name}: Total {branch_found} baris"
            " tertangkap.\n"
        )

    total_scraped = len(all_matched_records)
    durasi = int(time.time() - start_time_all)
    print(f"📊 Rangkuman Sesi ({durasi} detik):")
    print(f"   -> Miss Location (All Cabang)    : {count_rule_missloc:,} baris")
    print(f"   -> Mutasi ke OFF/ONL (Surabaya)  : {count_rule_off_onl:,} baris")
    print(f"   -> Mutasi ke TOKO (Surabaya)     : {count_rule_toko:,} baris")
    print(f"   -> TOTAL DATA TERKUMPUL          : {total_scraped:,} baris\n")

    if total_scraped == 0:
        print("ℹ️ Tidak ada data yang perlu diunggah (Data lama di Supabase dipertahankan).")
        return

    # ==========================================================================
    # HAPUS DATA LAMA & UPLOAD DATA TERBARU KE SUPABASE
    # ==========================================================================
    df_upload = pd.DataFrame(all_matched_records).drop_duplicates(
        subset=["tanggal", "sku", "bin_awal", "bin_tujuan", "qty_mutasi"]
    )
    records_to_upload = df_upload.to_dict(orient="records")

    print("🗑️ Menghapus data lama di tabel Supabase 'jezpro_miss_location_logs'...")
    try:
        res_del = requests.delete(
            f"{SUPABASE_URL}/rest/v1/jezpro_miss_location_logs?id=gt.0",
            headers=HEADERS_SB,
            timeout=30,
        )
        if res_del.status_code in [200, 204]:
            print("   ✅ Data lama berhasil dibersihkan.")
        else:
            print(
                f"   ⚠️ Gagal hapus data lama ({res_del.status_code}):"
                f" {res_del.text}"
            )
    except Exception as e_del:
        print(f"   ⚠️ Error saat menghapus data lama: {e_del}")

    print("📤 Mengunggah data terbaru ke tabel Supabase 'jezpro_miss_location_logs'...")
    inserted_count = 0
    upsert_url = (
        f"{SUPABASE_URL}/rest/v1/jezpro_miss_location_logs?on_conflict=tanggal,sku,bin_awal,bin_tujuan,qty_mutasi"
    )

    for i in range(0, len(records_to_upload), batch_upload_size):
        chunk = records_to_upload[i : i + batch_upload_size]
        try:
            res_up = requests.post(
                upsert_url, headers=HEADERS_SB, json=chunk, timeout=60
            )
            if res_up.status_code in [200, 201, 204]:
                inserted_count += len(chunk)
                print(
                    f"   ➔ Upload batch {i + 1} s/d"
                    f" {min(i + batch_upload_size, len(records_to_upload))}..."
                )
            else:
                print(
                    f"   ⚠️ Respons Supabase ({res_up.status_code}):"
                    f" {res_up.text}"
                )
        except Exception as e_up:
            print(f"   ⚠️ Kendala upload: {e_up}")

    print(
        f"\n🎉 Sukses! {inserted_count:,} baris data terbaru menggantikan data"
        " lama di Supabase.\n"
    )


# ==============================================================================
# MAIN LOOP: BERJALAN OTOMATIS TIAP 2 JAM SEKALI
# ==============================================================================
if __name__ == "__main__":
    INTERVAL_DETIK = 7200  # 2 jam = 2 * 3600 detik

    print("=" * 85)
    print(
        "🔄 DAEMON SINKRONISASI: ALL CABANG (MISS LOC) + SURABAYA (OFF/ONL/TOKO)"
    )
    print("   Berjalan continuous otomatis setiap 2 jam sekali.")
    print("=" * 85)

    jez = create_jezpro_session()

    while True:
        try:
            execute_sync_all(jez, days_back=60)
        except Exception as e_main:
            print(f"❌ Terjadi kesalahan pada siklus ini: {e_main}")

        waktu_berikutnya = (
            datetime.now(WIB) + timedelta(seconds=INTERVAL_DETIK)
        ).strftime("%H:%M:%S")
        print(
            "💤 Standby 2 jam. Jadwal sinkronisasi berikutnya: pukul"
            f" {waktu_berikutnya} WIB...\n"
        )

        time.sleep(INTERVAL_DETIK) 