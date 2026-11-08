import os
import re
import json
import random
import urllib.parse
import requests
import pandas as pd
from datetime import datetime

# ==============================================================================
# KREDENSIAL & KONFIGURASI PUSAT
# ==============================================================================
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://fanzsmghhbefhhaicrok.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZhbnpzbWdoaGJlZmhoYWljcm9rIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODgxNTQzNDgsImV4cCI6MjEwMzczMDM0OH0.brCSOO9nHAUK8CxDWPperpJ--_NA_nwy5cO9OqGv3I0")

# 🌟 Link Spreadsheet REQUEST BARANG Anda (SUDAH TERPASANG)
SPREADSHEET_URL = os.environ.get(
    "SPREADSHEET_URL", 
    "https://docs.google.com/spreadsheets/d/1yjNfDer239OR0tVUl_Xj1UCArqbcMr5dl6C-5EGtrSo/edit?gid=1695087119#gid=1695087119"
)

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

def safe_int(val, default=0):
    try:
        if pd.isna(val) or val is None:
            return default
        if isinstance(val, (int, float)):
            return int(round(val))
        s = str(val).replace("Rp", "").strip()
        if "," in s and "." in s:
            s = s.replace(".", "").replace(",", ".")
        elif "," in s:
            s = s.replace(",", ".")
        return int(round(float(s)))
    except Exception:
        digits = re.findall(r'-?\d+', str(val))
        return int(digits[0]) if digits else default

def get_stock_cache():
    """Tarik master harga beli dan nama barang dari Supabase"""
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
                    sku_k = str(it.get("SKU", it.get("sku", ""))).split('.')[0].strip().upper()
                    if not sku_k: continue
                    name_v = str(it.get("ITEM NAME", it.get("item_name", it.get("ARTIKEL", "-")))).strip()
                    cogs_v = safe_int(it.get("HARGA BELI", it.get("Harga Beli", it.get("cogs", 0))), 0)
                    if sku_k not in lookup or lookup[sku_k]["cogs"] == 0:
                        lookup[sku_k] = {"name": name_v, "cogs": cogs_v}
    except Exception as e:
        print(f"⚠️ Gagal load stock_live_cache: {e}")
    return lookup

def get_existing_database_memos():
    """Mengambil memo yang sudah ada di Supabase secara aman (select=*)"""
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
        print(f"⚠️ Gagal membaca memo eksisting: {e}")
    return existing_map

def run_sync():
    if not SPREADSHEET_URL:
        print("❌ SPREADSHEET_URL belum diatur!")
        return

    existing_db_memos = get_existing_database_memos()
    print(f"📂 Ditemukan {len(existing_db_memos)} riwayat memo yang sudah tercatat di database.")

    download_url = SPREADSHEET_URL
    match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', SPREADSHEET_URL)
    if match:
        sheet_id = match.group(1)
        download_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"

    print("📥 Mengunduh Spreadsheet Permintaan Markom...")
    try:
        xl = pd.ExcelFile(download_url)
        all_sheets = xl.sheet_names
        
        # Cari spesifik sheet 'Permintaan markom'
        target_sheet = None
        for s in all_sheets:
            if "PERMINTAAN MARKOM" in s.strip().upper():
                target_sheet = s
                break

        if not target_sheet:
            target_sheet = all_sheets[1] if len(all_sheets) > 1 else all_sheets[0]

        print(f"🎯 Membaca Sheet: '{target_sheet}'")
        df = pd.read_excel(xl, sheet_name=target_sheet)

    except Exception as e:
        print(f"❌ Gagal membaca sheet: {e}")
        return

    if df.empty or df.shape[1] < 4:
        print("⚠️ Sheet kosong atau kolom kurang!")
        return

    # Pemetaan Kolom Fleksibel (Mencegah masalah pergeseran kolom)
    def find_col(candidates, default_idx):
        for cand in candidates:
            for c in df.columns:
                if cand.upper() in str(c).strip().upper():
                    return c
        return df.columns[default_idx] if df.shape[1] > default_idx else df.columns[0]

    col_pic   = find_col(["PIC"], 0)
    col_note1 = find_col(["NOTE AMP"], 2)
    col_note2 = find_col(["NO TELP"], 1)
    col_sku   = find_col(["SKU", "BARCODE"], 3)
    col_qty   = find_col(["QTY", "JUMLAH"], 4)
    col_tgl   = find_col(["TANGGAL REQ", "TIMESTAMP"], 14)
    col_bin   = find_col(["BIN PICK", "PICK_LOCATION"], 16)

    # Filter Baris EVENT, HADIAH, GIFT (Mengecek NOTE AMP maupun NO TELP)
    KEYWORDS = ["EVENT", "HADIAH", "GIFT"]
    pattern = "|".join(KEYWORDS)
    mask = (
        df[col_note1].fillna("").astype(str).str.contains(pattern, case=False, na=False) |
        df[col_note2].fillna("").astype(str).str.contains(pattern, case=False, na=False)
    )
    df_filtered = df[mask].copy()

    if df_filtered.empty:
        print("ℹ️ Tidak ada baris EVENT, HADIAH, atau GIFT.")
        return

    stock_lookup = get_stock_cache()

    # 1. Susun Rincian Item Permintaan
    grouped_events = {}
    for row_idx, (_, r) in enumerate(df_filtered.iterrows(), start=1):
        pic_val = str(r[col_pic]).strip() if pd.notna(r[col_pic]) else "MARKOM"

        # Ambil note dari NOTE AMP jika ada, jika kosong ambil dari NO TELP
        n1 = str(r[col_note1]).strip() if pd.notna(r[col_note1]) else ""
        n2 = str(r[col_note2]).strip() if pd.notna(r[col_note2]) else ""
        note_val = n1.upper() if n1 else (n2.upper() if n2 else "EVENT")

        # Parsing tanggal
        raw_tgl = str(r[col_tgl]).strip() if pd.notna(r[col_tgl]) else ""
        try:
            dt_parsed = pd.to_datetime(raw_tgl)
            tgl_val = dt_parsed.strftime("%Y-%m-%d")
        except Exception:
            tgl_val = raw_tgl[:10] if len(raw_tgl) >= 10 else datetime.now().strftime("%Y-%m-%d")

        sku_val = str(r[col_sku]).split('.')[0].strip().upper() if pd.notna(r[col_sku]) else ""
        if not sku_val or sku_val in ["", "NAN", "NONE", "SKU", "-"]:
            continue

        qty_val = safe_int(r[col_qty], 1)
        b_val = str(r[col_bin]).strip() if pd.notna(r[col_bin]) else "GL1-DC-OUT"

        info = stock_lookup.get(sku_val, {})
        item_name = info.get("name") or sku_val
        harga_beli = info.get("cogs", 0)
        subtotal = harga_beli * qty_val

        item_entry = {
            "id": f"REQ-{sku_val}-{row_idx}",
            "tanggal": tgl_val,
            "pic": pic_val,
            "keterangan": note_val,
            "bin": b_val,
            "sku": sku_val,
            "item_name": item_name,
            "cogs": harga_beli,
            "qty": qty_val,
            "subtotal": subtotal
        }

        group_key = (tgl_val, note_val)
        if group_key not in grouped_events:
            grouped_events[group_key] = {
                "pic": pic_val,
                "items": []
            }
        grouped_events[group_key]["items"].append(item_entry)

    # 2. Sinkronisasi Pintar (Update Card Lama atau Insert Card Baru)
    new_memos_to_insert = []
    skipped_count = 0

    for (tgl_doc, event_name), grp_data in grouped_events.items():
        items_list = grp_data["items"]
        pic_doc = grp_data["pic"]
        tot_nom = sum(x["subtotal"] for x in items_list)
        db_match_key = (tgl_doc, event_name)

        if db_match_key in existing_db_memos:
            exist = existing_db_memos[db_match_key]
            st = str(exist.get("status_adj", "PENDING")).upper()

            # Lewati jika sudah selesai di-adjustment di gudang
            if st == "DONE":
                print(f"⏩ [SKIP] Tgl {tgl_doc} - '{event_name}' SUDAH DONE ADJUSTMENT.")
                skipped_count += 1
                continue

            # Cek apakah items atau nominalnya benar-benar ada yang berubah
            existing_items = exist.get("items", [])
            if isinstance(existing_items, str):
                try: existing_items = json.loads(existing_items)
                except Exception: existing_items = []

            sig_new = sorted([(x['sku'], x['qty'], x['subtotal']) for x in items_list])
            sig_old = sorted([(x.get('sku'), x.get('qty'), x.get('subtotal')) for x in existing_items])

            if sig_new == sig_old and exist.get("nominal") == tot_nom and exist.get("diajukan_oleh") == pic_doc:
                print(f"⏩ [SKIP] Tgl {tgl_doc} - '{event_name}' identik (tidak ada perubahan).")
                skipped_count += 1
                continue

            # Update memo lama jika ada perubahan QTY/Item
            print(f"🔄 [UPDATE CARD] Tgl {tgl_doc} - '{event_name}' (ID: {exist['id']}) diperbarui dengan QTY/Item terbaru...")
            safe_id = urllib.parse.quote(str(exist['id']), safe='')
            url_update = f"{SUPABASE_URL}/rest/v1/memo_pengajuan?id=eq.{safe_id}"
            update_payload = {
                "nominal": tot_nom,
                "diajukan_oleh": pic_doc,
                "items": items_list
            }
            res_patch = requests.patch(url_update, headers=HEADERS, json=update_payload)
            if res_patch.status_code in [200, 204]:
                print(f"   ✅ Berhasil update memo {exist['id']}")
            else:
                print(f"   ⚠️ Gagal update memo {exist['id']}: {res_patch.text}")
            continue

        # Buat card memo baru jika belum pernah ada
        memo_id = f"MEMO/ZKN/{tgl_doc.replace('-', '')}/{random.randint(100, 999)}"
        new_memos_to_insert.append({
            "id": memo_id,
            "tanggal": tgl_doc,
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

        if res_insert.status_code not in [200, 201] and "status_adj" in res_insert.text:
            for m in new_memos_to_insert:
                m.pop("status_adj", None)
            res_insert = requests.post(url_insert, headers=HEADERS, json=new_memos_to_insert)

        if res_insert.status_code in [200, 201]:
            print(f"🚀 BERHASIL MEMBUAT {len(new_memos_to_insert)} MEMO BARU DI SUPABASE!")
            for m in new_memos_to_insert:
                print(f"   ➔ [{m['id']}] Tgl: {m['tanggal']} | {m['tujuan']} (Rp {m['nominal']:,})")
        else:
            print(f"❌ Gagal insert: {res_insert.text}")
    else:
        print(f"✅ Selesai! Sinkronisasi tuntas ({skipped_count} memo tidak berubah / dilewati).")

if __name__ == "__main__":
    run_sync()