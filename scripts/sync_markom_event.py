import os
import re
import json
import random
import requests
import pandas as pd
from datetime import datetime

# Credential Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://fanzsmghhbefhhaicrok.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZhbnpzbWdoaGJlZmhoYWljcm9rIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODgxNTQzNDgsImV4cCI6MjEwMzczMDM0OH0.brCSOO9nHAUK8CxDWPperpJ--_NA_nwy5cO9OqGv3I0")
SPREADSHEET_URL = os.environ.get("SPREADSHEET_URL", "")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# 🌟 PERBAIKAN FATAL: safe_int yang TIDAK merusak angka float (1.0 tetap 1, BUKAN 10)
def safe_int(val, default=0):
    try:
        if pd.isna(val) or val is None:
            return default
        if isinstance(val, (int, float)):
            return int(round(val))
        s = str(val).replace("Rp", "").strip()
        # Jika format angka menggunakan koma desimal, ubah ke titik
        if "," in s and "." in s:
            s = s.replace(".", "").replace(",", ".")
        elif "," in s:
            s = s.replace(",", ".")
        return int(round(float(s)))
    except Exception:
        return default

# 🌟 POIN 1: FUNGSI HAPUS SEMUA DATA LAMA DI SUPABASE
def clear_all_supabase_memos():
    print("🧹 [POIN 1] Menghapus seluruh data memo lama di Supabase agar bersih...")
    try:
        url_del = f"{SUPABASE_URL}/rest/v1/memo_pengajuan?id=not.is.null"
        res = requests.delete(url_del, headers=HEADERS)
        if res.status_code in [200, 204]:
            print("✅ Seluruh data memo lama di Supabase BERHASIL DIKOSONGKAN!")
        else:
            print(f"⚠️ Respon hapus: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"⚠️ Gagal menghapus database lama: {e}")

def get_stock_cache():
    """Tarik master harga beli satuan dan nama barang dari Supabase"""
    lookup = {}
    try:
        url = f"{SUPABASE_URL}/rest/v1/stock_live_cache?select=*"
        res = requests.get(url, headers=HEADERS, timeout=30)
        if res.status_code == 200:
            for row in res.json():
                s_data = row.get("stock_data", [])
                if isinstance(s_data, str):
                    try: s_data = json.loads(s_data)
                    except: s_data = []
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

    # Jalankan pembersihan data lama di awal
    clear_all_supabase_memos()

    download_url = SPREADSHEET_URL
    match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', SPREADSHEET_URL)
    if match:
        sheet_id = match.group(1)
        download_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"

    print("📥 Mengunduh Spreadsheet Permintaan Markom...")
    try:
        xl = pd.ExcelFile(download_url)
        all_sheets = xl.sheet_names
        print(f"📑 Daftar Sheet: {all_sheets}")

        target_sheet = None
        for s in all_sheets:
            if "PERMINTAAN MARKOM" in s.strip().upper():
                target_sheet = s
                break

        if not target_sheet:
            target_sheet = all_sheets[1] if len(all_sheets) > 1 else all_sheets[0]

        print(f"🎯 MEMBACA SHEET: '{target_sheet}'")
        df = xl.parse(target_sheet)

    except Exception as e:
        print(f"❌ Gagal membaca sheet: {e}")
        return

    if df.empty or df.shape[1] < 4:
        print("⚠️ Sheet kosong atau kolom kurang!")
        return

    # 🌟 POIN 5: PEMETAAN KOLOM RESMI SESUAI URUTAN ANDA (KOLOM A S/D P)
    # Col 0 (A): PIC
    # Col 1 (B): NOTE MARKOM (ops)
    # Col 2 (C): SKU
    # Col 3 (D): QTY
    # Col 12 (M): TANGGAL REQ
    # Col 14 (O): BIN PICK
    col_pic = df.columns[0]
    col_note = df.columns[1]
    col_sku = df.columns[2]
    col_qty = df.columns[3]
    col_tgl = df.columns[12] if df.shape[1] > 12 else df.columns[-2]
    col_bin = df.columns[14] if df.shape[1] > 14 else df.columns[-1]

    # Filter kata kunci Kolom B
    KEYWORDS = ["EVENT", "HADIAH", "GIFT"]
    pattern = "|".join(KEYWORDS)
    mask = df[col_note].fillna("").astype(str).str.contains(pattern, case=False, na=False)
    df_filtered = df[mask].copy()

    if df_filtered.empty:
        print("ℹ️ Tidak ditemukan baris EVENT, HADIAH, atau GIFT.")
        return

    print(f"✅ Ditemukan {len(df_filtered)} baris permintaan barang!")
    stock_lookup = get_stock_cache()

    # 🌟 POIN 3: PENGELOMPOKAN BERDASARKAN (TANGGAL PENGAJUAN & NOTE MARKOM)
    grouped_events = {}

    for row_idx, (_, r) in enumerate(df_filtered.iterrows(), start=1):
        pic_val = str(r[col_pic]).strip() if pd.notna(r[col_pic]) else "MARKOM"
        note_val = str(r[col_note]).strip().upper() if pd.notna(r[col_note]) else "EVENT"

        # Tanggal Pengajuan (YYYY-MM-DD)
        raw_tgl = str(r[col_tgl]).strip() if pd.notna(r[col_tgl]) else ""
        tgl_val = raw_tgl[:10] if len(raw_tgl) >= 10 else datetime.now().strftime("%Y-%m-%d")

        # SKU
        sku_val = str(r[col_sku]).split('.')[0].strip().upper() if pd.notna(r[col_sku]) else ""
        if not sku_val or sku_val in ["", "NAN", "NONE", "SKU"]:
            continue

        # 🌟 POIN 4: QTY AKURAT 100% (Tidak melonjak)
        qty_val = safe_int(r[col_qty], 1)
        bin_val = str(r[col_bin]).strip() if pd.notna(r[col_bin]) else "GL1-DC-OUT"

        info = stock_lookup.get(sku_val, {})
        item_name = info.get("name") or sku_val
        harga_beli = info.get("cogs", 0)
        subtotal = harga_beli * qty_val

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
            "subtotal": subtotal
        }

        # Kunci Pengelompokan: (Tanggal Pengajuan, Note Markom)
        group_key = (tgl_val, note_val)
        if group_key not in grouped_events:
            grouped_events[group_key] = {
                "pic": pic_val,
                "items": []
            }
        grouped_events[group_key]["items"].append(item_entry)

    # Simpan Hasil Grouping ke Supabase
    memos_payload = []
    for (tgl_doc, event_name), grp_data in grouped_events.items():
        items_list = grp_data["items"]
        pic_doc = grp_data["pic"]
        tot_nom = sum(x["subtotal"] for x in items_list)

        memo_id = f"MEMO/ZKN/{tgl_doc.replace('-', '')}/{random.randint(100, 999)}"
        memos_payload.append({
            "id": memo_id,
            "tanggal": tgl_doc,
            "divisi": "MARKOM",
            "jenis": "Pengajuan Adjustment untuk Hadiah",
            "tujuan": event_name,  # Murni nama note (tidak ada teks dobel)
            "nominal": tot_nom,
            "diajukan_oleh": pic_doc,
            "diproses_oleh": "Tim Purchasing",
            "diperiksa_oleh": "Tim Finance",
            "items": items_list
        })

    if memos_payload:
        url_insert = f"{SUPABASE_URL}/rest/v1/memo_pengajuan"
        res_insert = requests.post(url_insert, headers=HEADERS, json=memos_payload)
        if res_insert.status_code in [200, 201]:
            print(f"🚀 BERHASIL MEMBUAT {len(memos_payload)} KELOMPOK MEMO RESMI DI SUPABASE!")
            for m in memos_payload:
                print(f"   ➔ [{m['id']}] Tgl: {m['tanggal']} | Note: {m['tujuan']} | {len(m['items'])} Barang | Total: Rp {m['nominal']:,}")
        else:
            print(f"❌ Gagal insert memo: {res_insert.text}")

if __name__ == "__main__":
    run_sync()
