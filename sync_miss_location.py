import datetime
import re
import time
from config import get_supabase
import pandas as pd
import requests

# URL Endpoint History Setup
URL_JEZPRO = "https://jezpro.id/bin_history_datatables"

# ⚠️ GANTI DENGAN COOKIE TERBARU ANDA JIKA SESSION EXPIRED
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:160.0) Gecko/20100101"
        " Firefox/160.0"
    ),
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://jezpro.id/setup_lokasi_stok_v2",
    "Cookie": (
        "cf_clearance=YOUR_CF_CLEARANCE_HERE; "
        "sistemjezcoid_session=YOUR_SESSION_COOKIE_HERE; "
        "XSRF-TOKEN=YOUR_XSRF_TOKEN_HERE"
    ),
}

# Regex fleksibel untuk menangkap seluruh variasi Miss Location
PATTERN_MISS_LOC = re.compile(r"mis+[\s\-_]*loc", re.IGNORECASE)


def clean_html(text):
    if not text:
        return "-"
    clean = re.sub(r"<[^>]+>", " ", str(text))
    return re.sub(r"\s+", " ", clean).strip()


def parse_datetime(dt_str):
    try:
        # Format Jezpro biasanya: DD-MM-YYYY HH:MM:SS
        return pd.to_datetime(dt_str, dayfirst=True).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    except Exception:
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def run_sync_miss_location(days_back: int = 60, batch_upload_size: int = 500):
    client = get_supabase()
    if not client:
        print("❌ Gagal terhubung ke Supabase! Periksa config.py.")
        return False

    session = requests.Session()
    today = datetime.date.today()
    date_list = [
        (today - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
        for i in range(days_back)
    ]

    print(
        f"🚀 Memulai sinkronisasi Miss Location ({date_list[-1]} s/d"
        f" {date_list[0]})...\n"
    )

    all_matched_records = []

    for idx, target_date in enumerate(date_list, start=1):
        params = {
            "draw": str(idx),
            "start": "0",
            "length": "10000",
            "search[value]": "",
            "date": target_date,
            "st_id": "",  # Tarik semua cabang
            "history_bin_start": "",
            "history_bin_end": "",
        }

        try:
            resp = session.get(
                URL_JEZPRO, headers=HEADERS, params=params, timeout=25
            )
            if resp.status_code != 200:
                print(
                    f"⚠️ [{idx}/{len(date_list)}] Tgl {target_date}: HTTP"
                    f" {resp.status_code}"
                )
                continue

            raw_json = resp.json().get("data", [])
            daily_found = 0

            for item in raw_json:
                note_text = str(item.get("notes") or "").strip()
                end_bin = str(item.get("end_bin") or "").strip().upper()

                # SYARAT 1: Catatan variasi Miss Location
                # SYARAT 2: BIN TUJUAN bukan Karantina
                if PATTERN_MISS_LOC.search(note_text) and (
                    "KARANTINA" not in end_bin
                ):
                    clean_dt = parse_datetime(item.get("pm_created_at"))
                    q_val = item.get("pmt_qty", 0)
                    try:
                        q_val = int(q_val)
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
                        "cabang": str(item.get("st_name", "-")).strip().upper(),
                        "user_name": str(item.get("u_name", "-")).strip(),
                        "sku": (
                            str(item.get("ps_barcode", "-"))
                            .split(".")[0]
                            .strip()
                            .upper()
                        ),
                        "artikel": clean_html(item.get("article", "-")),
                        "bin_awal": str(item.get("start_bin", "-"))
                        .strip()
                        .upper(),
                        "qty_mutasi": q_val,
                        "bin_tujuan": end_bin,
                        "catatan": note_text,
                    })
                    daily_found += 1

            if daily_found > 0:
                print(
                    f"✅ [{idx}/{len(date_list)}] Tgl {target_date}: +{daily_found}"
                    " Miss Location"
                )

            time.sleep(0.3)  # Jeda aman Cloudflare

        except Exception as e:
            print(f"❌ Kendala pada tanggal {target_date}: {e}")
            continue

    total_scraped = len(all_matched_records)
    print(
        f"\n🎯 Total data Miss Location terkumpul: {total_scraped:,} baris.\n"
    )

    if total_scraped == 0:
        print("ℹ️ Tidak ada data yang perlu disimpan ke Supabase.")
        return True

    # --- UPLOAD / UPSERT KE SUPABASE DALAM CHUNK BATCH ---
    print("📤 Mengunggah data ke tabel Supabase 'jezpro_miss_location_logs'...")
    inserted_count = 0

    for i in range(0, total_scraped, batch_upload_size):
        chunk = all_matched_records[i : i + batch_upload_size]
        try:
            # on_conflict mencegah error duplikasi data
            client.table("jezpro_miss_location_logs").upsert(
                chunk,
                on_conflict="tanggal,sku,bin_awal,bin_tujuan,qty_mutasi",
                ignore_duplicates=True,
            ).execute()
            inserted_count += len(chunk)
            print(
                f"   ➔ Berhasil upload batch {i + 1} s/d"
                f" {min(i + batch_upload_size, total_scraped)}..."
            )
        except Exception as e_up:
            print(f"   ⚠️ Gagal upload batch {i}: {e_up}")

    print(
        f"\n🎉 SELESAI! {inserted_count:,} baris tersimpan permanen di Supabase."
    )
    return True


if __name__ == "__main__":
    run_sync_miss_location(days_back=60)