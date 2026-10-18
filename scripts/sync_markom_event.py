import os
import json
import random
import requests
import pandas as pd
from datetime import datetime

# Ambil credential dari GitHub Secrets / Environment
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://fanzsmghhbefhhaicrok.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZhbnpzbWdoaGJlZmhoYWljcm9rIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODgxNTQzNDgsImV4cCI6MjEwMzczMDM0OH0.brCSOO9nHAUK8CxDWPperpJ--_NA_nwy5cO9OqGv3I0")
# URL export spreadsheet (misal link Google Sheets export XLSX / CSV)
SPREADSHEET_URL = os.environ.get("SPREADSHEET_URL", "https://docs.google.com/spreadsheets/d/1tuGnu7jKvRkw9MmF92U-5pOoXjUOeTMoL3EvrOzcrQY/edit?gid=864743695#gid=864743695")

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

    if df.empty or df.shape[1] < 2:
        print("⚠️ Spreadsheet kosong atau format kurang dari 2 kolom.")
        return

    # Filter hanya baris yang Kolom B (Note) memuat kata 'EVENT'
    col_b = df.iloc[:, 1].fillna("").astype(str)
    df_event = df[col_b.str.contains("EVENT", case=False, na=False)].copy()

    if df_event.empty:
        print("ℹ️ Tidak ada baris dengan Note 'EVENT'.")
        return

    print(f"🔍 Ditemukan {len(df_event)} baris EVENT. Melakukan mapping harga beli...")
    stock_lookup = get_stock_cache()
    event_items = []
    
    pic_peminta = "MARKOM"
    keterangan_event = "EVENT"
    tanggal_req = datetime.now().strftime("%Y-%m-%d")

    for row_idx, (_, r) in enumerate(df_event.iterrows(), start=1):
        pic_val = str(r.iloc[0]).strip() if len(r) > 0 and pd.notna(r.iloc[0]) else ""
        if pic_val: pic_peminta = pic_val

        note_val = str(r.iloc[1]).strip() if len(r) > 1 and pd.notna(r.iloc[1]) else ""
        if note_val: keterangan_event = note_val.upper()

        tgl_val = str(r.iloc[12]).strip() if len(r) > 12 and pd.notna(r.iloc[12]) else ""
        if tgl_val: tanggal_req = tgl_val

        bin_val = str(r.iloc[14]).strip() if len(r) > 14 and pd.notna(r.iloc[14]) else "GL1-DC-OUT"
        qty_val = safe_int(r.iloc[3] if len(r) > 3 else 1, 1)

        sku_raw = ""
        for c_name in r.index:
            if "SKU" in str(c_name).upper():
                sku_raw = str(r[c_name]).split('.')[0].strip().upper()
                break
        if not sku_raw:
            sku_raw = str(r.iloc[3]).split('.')[0].strip().upper()

        info = stock_lookup.get(sku_raw, {})
        item_name = info.get("name") or sku_raw
        harga_beli = info.get("cogs", 0)

        distinct_id = f"EVT-{sku_raw}-{row_idx}-{random.randint(100, 999)}"

        event_items.append({
            "id": distinct_id,
            "tanggal": tanggal_req,
            "pic": pic_peminta,
            "keterangan": keterangan_event,
            "bin": bin_val,
            "sku": sku_raw,
            "item_name": item_name,
            "cogs": harga_beli,
            "qty": qty_val,
            "subtotal": harga_beli * qty_val
        })

    tot_nom = sum(x["subtotal"] for x in event_items)

    # Cek apakah memo dengan tujuan & tanggal yang sama sudah pernah dibuat (Anti-Duplikat)
    url_check = f"{SUPABASE_URL}/rest/v1/memo_pengajuan?tujuan=eq.{requests.utils.quote(keterangan_event)}&tanggal=eq.{tanggal_req}&select=id,nominal"
    res_check = requests.get(url_check, headers=HEADERS)
    if res_check.status_code == 200 and len(res_check.json()) > 0:
        existing_memo = res_check.json()[0]
        # Jika nominal sama persis, lewati agar tidak bikin card ganda
        if existing_memo.get("nominal") == tot_nom:
            print(f"ℹ️ Memo '{keterangan_event}' ({tanggal_req}) sudah ada di Supabase dan datanya identik. Melewati insert.")
            return

    memo_id = f"MEMO/ZKN/{datetime.now().strftime('%Y%m%d')}/{random.randint(100, 999)}"
    memo_payload = {
        "id": memo_id,
        "tanggal": tanggal_req,
        "divisi": "MARKOM",
        "jenis": "Pengajuan Adjustment untuk Hadiah",
        "tujuan": keterangan_event,
        "nominal": tot_nom,
        "diajukan_oleh": pic_peminta,
        "diproses_oleh": "Tim Purchasing",
        "diperiksa_oleh": "Tim Finance",
        "items": event_items
    }
    
    url_insert = f"{SUPABASE_URL}/rest/v1/memo_pengajuan"
    res_insert = requests.post(url_insert, headers=HEADERS, json=[memo_payload])
    if res_insert.status_code in [200, 201]:
        print(f"🚀 Berhasil membuat Memo baru di Supabase: {memo_id} (Rp {tot_nom:,})")
    else:
        print(f"❌ Gagal insert memo ke Supabase: {res_insert.text}")

if __name__ == "__main__":
    run_sync()
