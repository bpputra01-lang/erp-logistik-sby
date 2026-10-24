import os
import re
import json
import random
import requests
import pandas as pd
from datetime import datetime

# Ambil credential dari Environment / Secrets
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://fanzsmghhbefhhaicrok.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZhbnpzbWdoaGJlZmhoYWljcm9rIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODgxNTQzNDgsImV4cCI6MjEwMzczMDM0OH0.brCSOO9nHAUK8CxDWPperpJ--_NA_nwy5cO9OqGv3I0")
SPREADSHEET_URL = os.environ.get("SPREADSHEET_URL", "")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

def safe_int(val, default=0):
    try:
        if pd.isna(val) or val is None: return default
        cleaned = str(val).replace("Rp", "").replace(".", "").replace(",", "").strip()
        return int(float(cleaned))
    except Exception:
        return default

def get_stock_cache():
    """Tarik master harga beli dan nama barang dari stock_live_cache Supabase"""
    lookup = {}
    try:
        url = f"{SUPABASE_URL}/rest/v1/stock_live_cache?select=*"
        res = requests.get(url, headers=HEADERS, timeout=30)
        if res.status_code == 200:
            for row in res.json():
                s_data = row.get("stock_data", [])
                if isinstance(s_data, str):
                    s_data = json.loads(s_data)
                for it in s_data:
                    sku_k = str(it.get("SKU", it.get("sku", ""))).split('.')[0].strip().upper()
                    if not sku_k: continue
                    name_v = str(it.get("ITEM NAME", it.get("item_name", it.get("ARTIKEL", "-")))).strip()
                    cogs_v = safe_int(it.get("HARGA BELI", it.get("Harga Beli", it.get("cogs", 0))), 0)
                    if sku_k not in lookup or lookup[sku_k]["cogs"] == 0:
                        lookup[sku_k] = {"name": name_v, "cogs": cogs_v}
    except Exception as e:
        print(f"⚠️ Gagal load stock_live_cache: {e}")
    return lookup

def run_sync():
    if not SPREADSHEET_URL:
        print("❌ SPREADSHEET_URL belum diatur!")
        return

    # 🌟 1. OTOMATIS UBAH LINK APAPUN MENJADI DOWNLOAD EXCEL (AGAR BISA BACA SEMUA SHEET)
    download_url = SPREADSHEET_URL
    match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', SPREADSHEET_URL)
    if match:
        sheet_id = match.group(1)
        # Mengunduh seluruh workbook Excel agar Sheet 2 ("PERMINTAAN MARKOM") bisa dibaca
        download_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"

    print("📥 Mengunduh Spreadsheet Permintaan Markom...")
    try:
        xl = pd.ExcelFile(download_url)
        all_sheets = xl.sheet_names
        print(f"📑 Daftar Sheet yang ada di G-Sheet: {all_sheets}")

        # 🌟 2. CARI SECARA KHUSUS SHEET 'PERMINTAAN MARKOM' ATAU SHEET KE-2
        target_sheet = None
        for s in all_sheets:
            if "PERMINTAAN MARKOM" in s.strip().upper():
                target_sheet = s
                break

        # Fallback jika nama tab sedikit berbeda, ambil Sheet ke-2 (Index 1)
        if not target_sheet:
            if len(all_sheets) > 1:
                target_sheet = all_sheets[1]
            else:
                target_sheet = all_sheets[0]

        print(f"🎯 MEMBACA SHEET TERPILIH: '{target_sheet}'")
        df = xl.parse(target_sheet)

    except Exception as e:
        print(f"❌ Gagal membaca sheet: {e}")
        return

    if df.empty:
        print(f"⚠️ Sheet '{target_sheet}' kosong.")
        return

    print(f"📊 Ukuran Data di Sheet '{target_sheet}': {df.shape[0]} baris x {df.shape[1]} kolom")

    # 🌟 3. DETEKSI KOLOM SECARA AKURAT
    def find_col(keywords, default_idx):
        for col in df.columns:
            c_str = str(col).strip().upper()
            if any(k in c_str for k in keywords):
                return col
        return df.columns[default_idx] if df.shape[1] > default_idx else df.columns[-1]

    col_pic = find_col(["PIC"], 0)
    col_note = find_col(["NOTE", "MARKOM", "OPS"], 1)
    col_sku = find_col(["SKU"], 2)
    col_qty = find_col(["QTY", "JUMLAH"], 3)
    col_tgl = find_col(["TANGGAL", "REQ"], 12 if df.shape[1] > 12 else -2)
    col_bin = find_col(["BIN"], 14 if df.shape[1] > 14 else -1)

    print(f"🔍 Kolom Terpetakan: PIC=[{col_pic}], Note=[{col_note}], SKU=[{col_sku}], Qty=[{col_qty}]")

    # 🌟 4. FILTER KATA KUNCI: EVENT, HADIAH, GIFT (SEMUA TERANGKUT)
    KEYWORDS = ["EVENT", "HADIAH", "GIFT"]
    pattern = "|".join(KEYWORDS)

    mask = df[col_note].fillna("").astype(str).str.contains(pattern, case=False, na=False)
    df_filtered = df[mask].copy()

    if df_filtered.empty:
        print(f"ℹ️ Tidak ditemukan baris EVENT, HADIAH, atau GIFT di sheet '{target_sheet}'.")
        print("💡 Contoh isi 5 baris pertama pada kolom Note:")
        print(df[col_note].dropna().head(5).tolist())
        return

    print(f"✅ DITEMUKAN {len(df_filtered)} BARIS PERMINTAAN (EVENT & HADIAH)!")
    stock_lookup = get_stock_cache()

    # 🌟 5. GROUPING PER ACARA / KEPERLUAN (Contoh: Horeg jadi 1 memo, Hadiah KOL jadi 1 memo)
    grouped_events = {}

    for row_idx, (_, r) in enumerate(df_filtered.iterrows(), start=1):
        pic_val = str(r[col_pic]).strip() if pd.notna(r[col_pic]) else "MARKOM"
        note_val = str(r[col_note]).strip().upper() if pd.notna(r[col_note]) else "EVENT"

        # Format tanggal YYYY-MM-DD
        raw_tgl = str(r[col_tgl]).strip() if pd.notna(r[col_tgl]) else ""
        tgl_val = raw_tgl[:10] if len(raw_tgl) >= 10 else datetime.now().strftime("%Y-%m-%d")

        # Ambil SKU dari Kolom C
        sku_val = str(r[col_sku]).split('.')[0].strip().upper() if pd.notna(r[col_sku]) else ""
        if not sku_val or sku_val in ["", "NAN", "NONE", "SKU"]:
            continue

        qty_val = safe_int(r[col_qty], 1)
        bin_val = str(r[col_bin]).strip() if pd.notna(r[col_bin]) else "GL1-DC-OUT"

        info = stock_lookup.get(sku_val, {})
        item_name = info.get("name") or sku_val
        harga_beli = info.get("cogs", 0)

        item_entry = {
            "id": f"REQ-{sku_val}-{row_idx}",
            "tanggal": tgl_val,
            "pic": pic_val,
            "keterangan": note_val,
            "bin": bin_val,
            "sku": sku_val,
            "item_name": item_name,
            "cogs": harga_beli,
            "qty": qty_val,
            "subtotal": harga_beli * qty_val
        }

        group_key = (note_val, tgl_val, pic_val)
        if group_key not in grouped_events:
            grouped_events[group_key] = []
        grouped_events[group_key].append(item_entry)

    # 🌟 6. SIMPAN/PERBARUI KE SUPABASE PER ACARA
    for (event_name, tgl_doc, pic_doc), items_list in grouped_events.items():
        tot_nom = sum(x["subtotal"] for x in items_list)

        url_check = f"{SUPABASE_URL}/rest/v1/memo_pengajuan?tujuan=eq.{requests.utils.quote(event_name)}&tanggal=eq.{tgl_doc}&select=id,nominal"
        res_check = requests.get(url_check, headers=HEADERS)

        if res_check.status_code == 200 and len(res_check.json()) > 0:
            existing = res_check.json()[0]
            existing_id = existing.get("id")
            existing_nom = existing.get("nominal", 0)

            # Jika data bertambah di spreadsheet, otomatis update memo tersebut
            if existing_nom != tot_nom:
                print(f"🔄 Mengupdate memo {existing_id} ({event_name}) menjadi {len(items_list)} barang...")
                url_update = f"{SUPABASE_URL}/rest/v1/memo_pengajuan?id=eq.{existing_id}"
                requests.patch(url_update, headers=HEADERS, json={
                    "nominal": tot_nom,
                    "diajukan_oleh": pic_doc,
                    "items": items_list
                })
            else:
                print(f"ℹ️ Memo '{event_name}' sudah up-to-date ({len(items_list)} barang).")
            continue

        memo_id = f"MEMO/ZKN/{datetime.now().strftime('%Y%m%d')}/{random.randint(100, 999)}"
        memo_payload = {
            "id": memo_id,
            "tanggal": tgl_doc,
            "divisi": "MARKOM",
            "jenis": "Pengajuan Adjustment untuk Hadiah",
            "tujuan": f"{event_name} ({len(items_list)} Barang)",
            "nominal": tot_nom,
            "diajukan_oleh": pic_doc,
            "diproses_oleh": "Tim Purchasing",
            "diperiksa_oleh": "Tim Finance",
            "items": items_list
        }

        res_insert = requests.post(f"{SUPABASE_URL}/rest/v1/memo_pengajuan", headers=HEADERS, json=[memo_payload])
        if res_insert.status_code in [200, 201]:
            print(f"🚀 Berhasil membuat Memo: {memo_id} - '{event_name}' ({len(items_list)} barang, Total: Rp {tot_nom:,})")
        else:
            print(f"❌ Gagal insert memo: {res_insert.text}")

if __name__ == "__main__":
    run_sync()
