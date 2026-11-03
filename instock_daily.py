import os
import json
import requests
import re
import time
from datetime import datetime
import pytz

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
JEZPRO_EMAIL = os.environ.get("JEZPRO_EMAIL")
JEZPRO_PASS  = os.environ.get("JEZPRO_PASSWORD")

BRANCH_NAME = "JEZ SURABAYA"
STORE_ID = 3
POLL_INTERVAL_SECONDS = 15
WIB = pytz.timezone('Asia/Jakarta')

def strip_html(val):
    if not val: return ""
    return re.sub(r'<[^>]+>', '', str(val)).strip()

def safe_int_val(val, default=0):
    if not val: return default
    digits = re.findall(r'-?\d+', strip_html(val))
    return int(digits[0]) if digits else default

def parse_wib_datetime(dt_str):
    """Mengubah format tanggal Jezpro (DD-MM-YYYY HH:MM:SS atau YYYY-MM-DD HH:MM:SS) ke objek datetime WIB"""
    if not dt_str: return None
    clean_str = strip_html(dt_str).strip()
    formats = [
        "%d-%m-%Y %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S"
    ]
    for fmt in formats:
        try:
            naive = datetime.strptime(clean_str[:19], fmt)
            return WIB.localize(naive)
        except Exception:
            pass
    try:
        # Fallback ISO format dari Supabase
        dt = datetime.fromisoformat(clean_str.replace('Z', '+00:00'))
        return dt.astimezone(WIB)
    except Exception:
        return None

def fetch_bin_history_today(session):
    today_str = datetime.now(WIB).strftime("%Y-%m-%d")
    url = "https://jezpro.id/bin_history_datatables"
    params = {
        "draw": "1",
        "start": "0",
        "length": "500",
        "st_id": str(STORE_ID),
        "date": today_str,
        "_": int(time.time() * 1000)
    }
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://jezpro.id/setup_lokasi_stok_v2"
    }

    try:
        res = session.get(url, params=params, headers=headers, timeout=15)
        if res.status_code == 200:
            raw_data = res.json().get("data", [])
            history_list = []
            for item in raw_data:
                # Tangkap ID mutasi unik (pmt_id) dan waktu mutasi asli
                mutasi_id = strip_html(item.get("pmt_id") or item.get("DT_RowIndex") or "")
                raw_time = strip_html(item.get("pm_created_at") or "")
                dt_mutasi = parse_wib_datetime(raw_time)

                history_list.append({
                    "mutasi_id": str(mutasi_id),
                    "sku": strip_html(item.get("ps_barcode") or "").upper(),
                    "bin_awal": strip_html(item.get("start_bin") or "").upper(),
                    "bin_tujuan": strip_html(item.get("end_bin") or "").upper(),
                    "qty_mts": safe_int_val(item.get("pmt_qty"), 0),
                    "notes": strip_html(item.get("notes") or "").upper(),
                    "dt_wib": dt_mutasi,
                    "raw_time": raw_time
                })
            return history_list
    except Exception as e:
        print(f"⚠️ Gagal fetch bin_history: {e}")
    return []

def sync_cycle(session):
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    now_wib = datetime.now(WIB)
    today_date = now_wib.strftime("%Y-%m-%d")

    # Ambil data hari ini dari Supabase
    sb_url = f"{SUPABASE_URL}/rest/v1/jezpro_instock_daily?select=*&sync_date=eq.{today_date}"
    res_sb = requests.get(sb_url, headers=headers)
    sb_records = res_sb.json() if res_sb.status_code == 200 else []

    # Filter record
    waiting_in_sb = [x for x in sb_records if x.get("status") == "WAITING OFFLINE"]
    need_setup_in_sb = [x for x in sb_records if x.get("status") == "NEED_SETUP"]
    done_setup_in_sb = [x for x in sb_records if x.get("status") == "DONE_SETUP"]

    # Kumpulkan mutasi_id yang SUDAH PERNAH terpakai hari ini (Ledger Lock)
    used_mutasi_ids = set()
    for d in done_setup_in_sb:
        m_id = d.get("matched_mutasi_id")
        if m_id:
            used_mutasi_ids.add(str(m_id))

    sb_waiting_map = {f"{it['barcode_sku']}_{it.get('invoice','')}": it for it in waiting_in_sb}

    # ==========================================================================
    # LANGKAH 1: DETEKSI BARANG HILANG DARI HELPER
    # ==========================================================================
    jez_helper = fetch_helper_jezpro(session) # Dari fungsi fetch helper sebelumnya
    current_helper_keys = set()
    new_inserts = []

    for it in jez_helper:
        k = f"{it['barcode_sku']}_{it['invoice']}"
        current_helper_keys.add(k)
        if k not in sb_waiting_map:
            new_inserts.append({
                "barcode_sku": it["barcode_sku"],
                "article_name": it["article_name"],
                "bin_code": it["bin_code"],
                "qty": it["qty"],
                "status": "WAITING OFFLINE",
                "invoice": it["invoice"],
                "sync_date": today_date,
                "created_at": now_wib.isoformat()
            })

    if new_inserts:
        requests.post(f"{SUPABASE_URL}/rest/v1/jezpro_instock_daily", headers=headers, json=new_inserts)
        print(f"   📥 {len(new_inserts)} barang baru masuk antrean WAITING OFFLINE.")

    # Jika hilang dari helper -> tandai NEED_SETUP lengkap dengan TIMESTAMP HILANG
    for k, sb_item in sb_waiting_map.items():
        if k not in current_helper_keys:
            disappeared_timestamp = now_wib.isoformat()
            patch_url = f"{SUPABASE_URL}/rest/v1/jezpro_instock_daily?id=eq.{sb_item['id']}"
            requests.patch(patch_url, headers=headers, json={
                "status": "NEED_SETUP",
                "disappeared_at": disappeared_timestamp
            })
            print(f"   ⚠️ BARANG HILANG DARI HELPER ({now_wib.strftime('%H:%M:%S')}): {sb_item['barcode_sku']} ➔ Siap Setup!")

    # ==========================================================================
    # LANGKAH 2: MATCHING DENGAN VALIDASI WAKTU & KUNCI ID MUTASI
    # ==========================================================================
    if need_setup_in_sb:
        mutasi_today = fetch_bin_history_today(session)
        # Urutkan mutasi dari yang paling awal ke paling baru
        mutasi_today = sorted(mutasi_today, key=lambda x: x["dt_wib"] or now_wib)

        for target in need_setup_in_sb:
            t_sku = target["barcode_sku"]
            t_bin_awal = target["bin_code"]
            t_qty = safe_int_val(target["qty"], 1)
            
            # Waktu saat barang ini HILANG dari helper
            t_disappeared_dt = parse_wib_datetime(target.get("disappeared_at"))

            matched_mutasi = None

            for m in mutasi_today:
                m_id = m["mutasi_id"]
                # 🛑 SYARAT 1: Mutasi ID belum pernah dipakai oleh transaksi lain
                if m_id in used_mutasi_ids:
                    continue

                # 🛑 SYARAT 2: Validasi SKU, BIN, dan QTY
                sku_match = (m["sku"] == t_sku)
                bin_awal_match = (m["bin_awal"] == t_bin_awal or t_bin_awal in m["bin_awal"] or m["bin_awal"] in ["STAGING INBOUND", "WAITING OFFLINE"])
                bin_tujuan_match = ("GL1-INSTOCK" in m["bin_tujuan"] or "INSTOCK" in m["bin_tujuan"])
                qty_match = (m["qty_mts"] >= t_qty)

                # 🛑 SYARAT 3: WAKTU MUTASI HARUS >= WAKTU BARANG HILANG
                # Beri toleransi mundur 60 detik jika jam server Jezpro dan scraper selisih sedikit
                time_valid = True
                if t_disappeared_dt and m["dt_wib"]:
                    tolerance_sec = 60
                    time_diff = (m["dt_wib"] - t_disappeared_dt).total_seconds()
                    if time_diff < -tolerance_sec:
                        # Waktu mutasi terjadi jauh sebelum barang hilang (misal mutasi jam 10 pagi, barang hilang jam 2 siang)
                        time_valid = False

                if sku_match and bin_awal_match and bin_tujuan_match and qty_match and time_valid:
                    matched_mutasi = m
                    break

            if matched_mutasi:
                # Kunci ID mutasi ini agar tidak bisa diklaim lagi
                used_mutasi_ids.add(matched_mutasi["mutasi_id"])

                patch_url = f"{SUPABASE_URL}/rest/v1/jezpro_instock_daily?id=eq.{target['id']}"
                requests.patch(patch_url, headers=headers, json={
                    "status": "DONE_SETUP",
                    "matched_mutasi_id": matched_mutasi["mutasi_id"],
                    "setup_done_at": matched_mutasi["raw_time"]
                })
                print(f"   🎉 MATCH VALID! SKU: {t_sku} (Hilang: {target.get('disappeared_at')[:19]} ➔ Mutasi: {matched_mutasi['raw_time']}) ➔ PINDAH KE DONE SETUP!")
