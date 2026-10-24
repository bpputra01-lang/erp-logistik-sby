import os
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
        print("❌ SPREADSHEET_URL belum diatur di GitHub Secrets!")
        return

    print("📥 Mengunduh Spreadsheet Permintaan Markom...")
    try:
        if "format=xlsx" in SPREADSHEET_URL or SPREADSHEET_URL.endswith((".xlsx", ".xls")):
            df = pd.read_excel(SPREADSHEET_URL)
        else:
            df = pd.read_csv(SPREADSHEET_URL)
    except Exception as e:
        print(f"❌ Gagal membaca spreadsheet: {e}")
        return

    if df.empty or df.shape[1] < 4:
        print("⚠️ Spreadsheet kosong atau format kolom kurang dari 4 kolom.")
        return

    # Normalisasi Kolom Berdasarkan Posisi Sesuai Screenshot Gambar 1:
    # Col 0 (A): PIC
    # Col 1 (B): NOTE MARKOM (ops)
    # Col 2 (C): SKU
    # Col 3 (D): QTY
    # Col 12 (M): TANGGAL REQ
    # Col 14 (O): BIN PICK (jika ada)

    col_note_series = df.iloc[:, 1].fillna("").astype(str)

    # 🌟 1. PERBAIKAN FILTER: Menangkap kata EVENT, HADIAH, dan GIFT sekaligus
    KEYWORDS = ["EVENT", "HADIAH", "GIFT"]
    pattern = "|".join(KEYWORDS)
    mask_event = col_note_series.str.contains(pattern, case=False, na=False)
    df_filtered = df[mask_event].copy()

    if df_filtered.empty:
        print("ℹ️ Tidak ditemukan baris dengan Note EVENT, HADIAH, atau GIFT.")
        return

    print(f"🔍 Ditemukan total {len(df_filtered)} baris permintaan barang valid.")
    stock_lookup = get_stock_cache()

    # 🌟 2. GROUPING BERDASARKAN KETERANGAN KEPERLUAN & TANGGAL
    # Agar Hadiah Horeg dan Hadiah KOL tidak tercampur jadi 1 memo
    grouped_events = {}

    for row_idx, (_, r) in enumerate(df_filtered.iterrows(), start=1):
        pic_val = str(r.iloc[0]).strip() if len(r) > 0 and pd.notna(r.iloc[0]) else "MARKOM"
        note_val = str(r.iloc[1]).strip().upper() if len(r) > 1 and pd.notna(r.iloc[1]) else "EVENT"

        # Potong tanggal jadi YYYY-MM-DD saja (tanpa jam agar anti-error di PDF dan DB)
        raw_tgl = str(r.iloc[12]).strip() if len(r) > 12 and pd.notna(r.iloc[12]) else ""
        tgl_val = raw_tgl[:10] if len(raw_tgl) >= 10 else datetime.now().strftime("%Y-%m-%d")

        # 🌟 PERBAIKAN INDEX SKU: Kolom C (Index 2), BUKAN Index 3!
        sku_raw = str(r.iloc[2]).split('.')[0].strip().upper() if len(r) > 2 and pd.notna(r.iloc[2]) else ""
        if not sku_raw or sku_raw in ["", "NAN", "NONE"]:
            continue

        qty_val = safe_int(r.iloc[3] if len(r) > 3 else 1, 1)
        bin_val = str(r.iloc[14]).strip() if len(r) > 14 and pd.notna(r.iloc[14]) else "GL1-DC-OUT"

        info = stock_lookup.get(sku_raw, {})
        item_name = info.get("name") or sku_raw
        harga_beli = info.get("cogs", 0)

        distinct_id = f"REQ-{sku_raw}-{row_idx}"

        item_entry = {
            "id": distinct_id,
            "tanggal": tgl_val,
            "pic": pic_val,
            "keterangan": note_val,
            "bin": bin_val,
            "sku": sku_raw,
            "item_name": item_name,
            "cogs": harga_beli,
            "qty": qty_val,
            "subtotal": harga_beli * qty_val
        }

        # Kunci pengelompokan memo: (Nama Keterangan Event, Tanggal)
        group_key = (note_val, tgl_val, pic_val)
        if group_key not in grouped_events:
            grouped_events[group_key] = []
        grouped_events[group_key].append(item_entry)

    # 🌟 3. INSERT / UPDATE KE SUPABASE PER MEMO GROUP
    for (event_name, tgl_doc, pic_doc), items_list in grouped_events.items():
        tot_nom = sum(x["subtotal"] for x in items_list)
        tot_qty = sum(x["qty"] for x in items_list)

        # Cek apakah memo untuk event dan tanggal ini sudah ada di Supabase
        url_check = f"{SUPABASE_URL}/rest/v1/memo_pengajuan?tujuan=eq.{requests.utils.quote(event_name)}&tanggal=eq.{tgl_doc}&select=id,nominal,items"
        res_check = requests.get(url_check, headers=HEADERS)

        if res_check.status_code == 200 and len(res_check.json()) > 0:
            existing = res_check.json()[0]
            existing_id = existing.get("id")
            existing_nom = existing.get("nominal", 0)

            # Jika nominal/jumlah item berbeda (misal ada tambahan barang di sheet), UPDATE memo tersebut!
            if existing_nom != tot_nom:
                print(f"🔄 Memperbarui memo {existing_id} ({event_name}) karena ada perubahan data/qty...")
                url_update = f"{SUPABASE_URL}/rest/v1/memo_pengajuan?id=eq.{existing_id}"
                update_payload = {
                    "nominal": tot_nom,
                    "diajukan_oleh": pic_doc,
                    "items": items_list
                }
                requests.patch(url_update, headers=HEADERS, json=update_payload)
            else:
                print(f"ℹ️ Memo '{event_name}' ({tgl_doc}) sudah identik di Supabase ({len(items_list)} barang).")
            continue

        # Jika belum ada sama sekali, buat memo baru
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

        url_insert = f"{SUPABASE_URL}/rest/v1/memo_pengajuan"
        res_insert = requests.post(url_insert, headers=HEADERS, json=[memo_payload])
        if res_insert.status_code in [200, 201]:
            print(f"🚀 Berhasil membuat Memo baru: {memo_id} - '{event_name}' ({len(items_list)} barang, Total: Rp {tot_nom:,})")
        else:
            print(f"❌ Gagal insert memo: {res_insert.text}")

if __name__ == "__main__":
    run_sync()
