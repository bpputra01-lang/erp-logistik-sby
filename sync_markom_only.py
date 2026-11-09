import os
import re
import json
import time
import random
import urllib.parse
import requests
import pandas as pd
from datetime import datetime, timezone, timedelta

# ==============================================================================
# 🔑 KONFIGURASI PUSAT & KREDENSIAL
# ==============================================================================
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://fanzsmghhbefhhaicrok.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZhbnpzbWdoaGJlZmhoYWljcm9rIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODgxNTQzNDgsImV4cCI6MjEwMzczMDM0OH0.brCSOO9nHAUK8CxDWPperpJ--_NA_nwy5cO9OqGv3I0")

# Masukkan URL Google Spreadsheet Anda di sini jika tidak pakai environment variable
SPREADSHEET_URL = os.environ.get(
    "SPREADSHEET_URL", 
    ""
)

# Interval pengecekan otomatis (dalam satuan detik, misal: 60 = tiap 1 menit)
CHECK_INTERVAL_SECONDS = 60 

WIB = timezone(timedelta(hours=7))

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# ==============================================================================
# HELPER PEMBERSIH & PARSER
# ==============================================================================
def safe_int(val, default=0):
    try:
        if pd.isna(val) or val is None:
            return default
        if isinstance(val, (int, float)):
            return int(round(val))
        s = str(val).replace("Rp", "").replace(" ", "").strip()
        if "," in s and "." in s:
            s = s.replace(".", "").replace(",", ".")
        elif "." in s and len(s.split(".")[-1]) == 3:
            s = s.replace(".", "")
        elif "," in s:
            s = s.replace(",", ".")
        return int(round(float(s)))
    except Exception:
        digits = re.findall(r'-?\d+', str(val).replace(".", "").replace(",", ""))
        return int(digits[0]) if digits else default

def clean_sku(val):
    if pd.isna(val) or val is None: return ""
    s = str(val).strip().upper()
    if s.endswith('.0'): s = s[:-2]
    return s if s not in ["", "NAN", "NONE", "NULL", "-"] else ""

def get_stock_cache():
    lookup = {}
    try:
        url = f"{SUPABASE_URL}/rest/v1/stock_live_cache?select=*"
        res = requests.get(url, headers=HEADERS, timeout=30)
        if res.status_code == 200:
            for row in res.json():
                s_data = row.get("stock_data", [])
                if isinstance(s_data, str):
                    try: s_data = json.loads(s_data)
                    except Exception: s_data = []
                for it in s_data:
                    if not isinstance(it, dict): continue
                    sku_k = clean_sku(it.get("SKU") or it.get("sku") or it.get("BARCODE") or it.get("barcode_sku"))
                    if not sku_k: continue

                    name_v = str(it.get("ITEM NAME") or it.get("item_name") or it.get("ARTIKEL") or it.get("article_name") or "-").strip()
                    cogs_raw = (
                        it.get("HARGA BELI") or it.get("Harga Beli") or 
                        it.get("cogs") or it.get("purchase") or 
                        it.get("cogs_price") or it.get("harga_beli") or 0
                    )
                    cogs_v = safe_int(cogs_raw, 0)
                    norm_k = sku_k.lstrip('0')
                    entry = {"name": name_v, "cogs": cogs_v}
                    
                    if sku_k not in lookup or lookup[sku_k]["cogs"] == 0:
                        lookup[sku_k] = entry
                    if norm_k and (norm_k not in lookup or lookup[norm_k]["cogs"] == 0):
                        lookup[norm_k] = entry
    except Exception as e:
        print(f"   ⚠️ [STOCK CACHE] Gagal load stock_live_cache: {e}")
    return lookup

def get_existing_database_memos():
    existing_map = {}
    try:
        url = f"{SUPABASE_URL}/rest/v1/memo_pengajuan?select=*"
        res = requests.get(url, headers=HEADERS, timeout=30)
        if res.status_code == 200:
            for m in res.json():
                tgl = str(m.get("tanggal", ""))[:10]
                tujuan = str(m.get("tujuan", "")).strip().upper()
                existing_map[(tgl, tujuan)] = m
    except Exception as e:
        print(f"   ⚠️ [DB MEMO] Gagal membaca memo eksisting: {e}")
    return existing_map

# ==============================================================================
# FUNGSI SINKRONISASI UTAMA
# ==============================================================================
def run_sync():
    now_str = datetime.now(WIB).strftime("%H:%M:%S")
    print(f"\n⏳ [{now_str}] [MARKOM SYNC] Memulai pengecekan Google Spreadsheet Markom...")

    if not SPREADSHEET_URL:
        print("   ❌ [MARKOM SYNC] Gagal: SPREADSHEET_URL belum diatur/masih kosong!")
        return False

    existing_db_memos = get_existing_database_memos()
    print(f"   📂 Ditemukan {len(existing_db_memos)} riwayat memo terdaftar di database.")

    download_url = SPREADSHEET_URL
    match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', SPREADSHEET_URL)
    if match:
        sheet_id = match.group(1)
        download_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"

    try:
        xl = pd.ExcelFile(download_url)
        all_sheets = xl.sheet_names
        target_sheet = next((s for s in all_sheets if "MARKOM" in s.strip().upper()), all_sheets[0])
        print(f"   🎯 Membaca Sheet: '{target_sheet}'...")
        df = pd.read_excel(xl, sheet_name=target_sheet)
    except Exception as e:
        print(f"   ⚠️ Gagal via Excel, mencoba direct CSV: {e}")
        try:
            csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
            df = pd.read_csv(csv_url)
        except Exception as e2:
            print(f"   ❌ [MARKOM SYNC] Gagal mengunduh spreadsheet: {e2}")
            return False

    if df.empty or df.shape[1] < 4:
        print("   ⚠️ [MARKOM SYNC] Sheet kosong atau kolom tidak memadai.")
        return False

    def find_col(candidates, default_idx):
        for cand in candidates:
            for c in df.columns:
                if cand.upper() in str(c).strip().upper():
                    return c
        return df.columns[default_idx] if df.shape[1] > default_idx else df.columns[0]

    col_pic  = find_col(["PIC"], 0)
    col_note = find_col(["NOTE MARKOM", "NOTE AMP", "NOTE"], 1)
    col_sku  = find_col(["SKU", "BARCODE"], 3)
    col_qty  = find_col(["QTY", "JUMLAH"], 4)
    col_tgl  = find_col(["TANGGAL REQ", "TIMESTAMP", "TANGGAL"], 6)
    col_bin  = find_col(["BIN PICK", "PICK_LOCATION", "BIN"], 9)

    KEYWORDS = ["EVENT", "HADIAH", "GIFT"]
    pattern = "|".join(KEYWORDS)
    mask = df[col_note].fillna("").astype(str).str.contains(pattern, case=False, na=False)
    df_filtered = df[mask].copy()

    if df_filtered.empty:
        print("   ℹ️ [MARKOM SYNC] Tidak ada baris bertanda EVENT, HADIAH, atau GIFT di sheet.")
        return True

    print(f"   🔍 Ditemukan {len(df_filtered)} baris permintaan hadiah/event.")
    stock_lookup = get_stock_cache()

    grouped_events = {}
    for row_idx, (_, r) in enumerate(df_filtered.iterrows(), start=1):
        pic_val = str(r[col_pic]).strip() if pd.notna(r[col_pic]) else "MARKOM"
        raw_note = str(r[col_note]).strip() if pd.notna(r[col_note]) else ""
        note_val = raw_note.upper() if raw_note else "EVENT"

        raw_tgl = str(r[col_tgl]).strip() if pd.notna(r[col_tgl]) else ""
        try:
            dt_parsed = pd.to_datetime(raw_tgl)
            tgl_full = dt_parsed.strftime("%Y-%m-%d %H:%M:%S")
            tgl_doc = dt_parsed.strftime("%Y-%m-%d")
        except Exception:
            tgl_full = raw_tgl if len(raw_tgl) >= 10 else datetime.now(WIB).strftime("%Y-%m-%d %H:%M:%S")
            tgl_doc = tgl_full[:10]

        sku_val = clean_sku(r[col_sku])
        if not sku_val: continue

        qty_val = safe_int(r[col_qty], 1)
        b_val = str(r[col_bin]).strip() if pd.notna(r[col_bin]) else "GL1-DC-OUT"

        info = stock_lookup.get(sku_val) or stock_lookup.get(sku_val.lstrip('0')) or {}
        item_name = info.get("name") or sku_val
        harga_beli = safe_int(info.get("cogs", 0), 0)
        subtotal = harga_beli * qty_val

        item_entry = {
            "id": f"REQ-{sku_val}-{row_idx}",
            "tanggal": tgl_full,
            "pic": pic_val,
            "keterangan": note_val,
            "bin": b_val,
            "sku": sku_val,
            "item_name": item_name,
            "cogs": harga_beli,
            "qty": qty_val,
            "subtotal": subtotal
        }

        group_key = (tgl_doc, note_val)
        if group_key not in grouped_events:
            grouped_events[group_key] = {
                "pic": pic_val,
                "latest_time": tgl_full,
                "items": []
            }
        grouped_events[group_key]["items"].append(item_entry)
        if tgl_full > grouped_events[group_key]["latest_time"]:
            grouped_events[group_key]["latest_time"] = tgl_full

    new_memos_to_insert = []
    updated_count = 0
    skipped_count = 0

    for (tgl_doc, event_name), grp_data in grouped_events.items():
        items_list = grp_data["items"]
        pic_doc = grp_data["pic"]
        tot_nom = sum(x["subtotal"] for x in items_list)
        db_match_key = (tgl_doc, event_name)

        if db_match_key in existing_db_memos:
            exist = existing_db_memos[db_match_key]
            st = str(exist.get("status_adj", "PENDING")).upper()
            if st == "DONE":
                skipped_count += 1
                continue

            safe_id = urllib.parse.quote(str(exist['id']), safe='')
            url_update = f"{SUPABASE_URL}/rest/v1/memo_pengajuan?id=eq.{safe_id}"
            update_payload = {
                "nominal": tot_nom,
                "diajukan_oleh": pic_doc,
                "items": items_list
            }
            res_upd = requests.patch(url_update, headers=HEADERS, json=update_payload)
            if res_upd.status_code in [200, 204]:
                updated_count += 1
            continue

        memo_id = f"MEMO/ZKN/{tgl_doc.replace('-', '')}/{random.randint(100, 999)}"
        new_memos_to_insert.append({
            "id": memo_id,
            "tanggal": grp_data["latest_time"],
            "divisi": "MARKOM",
            "jenis": "Pengajuan Adjustment untuk Hadiah",
            "tujuan": event_name,
            "nominal": tot_nom,
            "diajukan_oleh": pic_doc,
            "diproses_oleh": "Tim Purchasing",
            "diperiksa_oleh": "Tim Finance",
            "status_adj": "PENDING",
            "items": items_list
        })

    if new_memos_to_insert:
        url_insert = f"{SUPABASE_URL}/rest/v1/memo_pengajuan"
        res_insert = requests.post(url_insert, headers=HEADERS, json=new_memos_to_insert)
        if res_insert.status_code in [200, 201]:
            print(f"   ✨ [INSERT] Berhasil menambah {len(new_memos_to_insert)} memo baru ke database!")
        else:
            print(f"   ⚠️ [INSERT] Gagal insert memo baru: {res_insert.text}")

    print(f"   ✅ [MARKOM SYNC] Selesai! (+{len(new_memos_to_insert)} Memo Baru, {updated_count} Diperbarui, {skipped_count} Dilewati karena Status DONE).")
    return True

# ==============================================================================
# MAIN CONTINUOUS LOOP
# ==============================================================================
if __name__ == "__main__":
    print("=" * 75)
    print("🚀 DAEMON SYNC MARKOM: SPREADSHEET -> SUPABASE (CONTINUOUS LOOP)")
    print(f"⏱️ Interval Pengecekan Otomatis: Tiap {CHECK_INTERVAL_SECONDS} Detik")
    print("=" * 75)

    try:
        while True:
            # Jalankan proses sinkronisasi
            try:
                run_sync()
            except Exception as e:
                print(f"   ❌ [ERROR UNHANDLED]: {e}")

            # Tampilan Standby / Hitung Mundur agar tahu sistem tetap hidup
            now_wib = datetime.now(WIB).strftime("%H:%M:%S")
            print(f"💤 [{now_wib}] [STANDBY] Pengecekan selesai. Menunggu {CHECK_INTERVAL_SECONDS} detik ke siklus berikutnya...")
            print("-" * 75)

            # Istirahat sesuai interval
            time.sleep(CHECK_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("\n\n🛑 Script dihentikan manual oleh user (Ctrl + C). Selamat tinggal!")