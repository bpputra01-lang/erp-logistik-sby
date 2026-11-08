import os
import re
import json
import random
import urllib.parse
import requests
import pandas as pd
from datetime import datetime, timezone, timedelta

# Kredensial & Konfigurasi
SUPABASE_URL = "https://fanzsmghhbefhhaicrok.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZhbnpzbWdoaGJlZmhoYWljcm9rIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODgxNTQzNDgsImV4cCI6MjEwMzczMDM0OH0.brCSOO9nHAUK8CxDWPperpJ--_NA_nwy5cO9OqGv3I0"
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1yjNfDer239OR0tVUl_Xj1UCArqbcMr5dl6C-5EGtrSo/edit?gid=1695087119#gid=1695087119"

WIB = timezone(timedelta(hours=7))
HEADERS_SB = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates"
}

def safe_int(val, default=0):
    try:
        if pd.isna(val) or val is None: return default
        if isinstance(val, (int, float)): return int(round(val))
        s = str(val).replace("Rp", "").strip()
        digits = re.findall(r'-?\d+', s)
        return int(digits[0]) if digits else default
    except Exception:
        return default

def run_sync():
    print(f"\n📑 [{datetime.now(WIB).strftime('%H:%M:%S')}] Memeriksa Spreadsheet 'REQUEST BARANG' (Sheet: Permintaan markom)...")
    try:
        # 1. Ambil Master Harga Beli (COGS) & Nama Artikel dari cache Supabase
        lookup_cogs = {}
        res_cache = requests.get(f"{SUPABASE_URL}/rest/v1/stock_live_cache?select=*", headers=HEADERS_SB, timeout=25)
        if res_cache.status_code == 200:
            for row in res_cache.json():
                s_data = row.get("stock_data", [])
                if isinstance(s_data, str):
                    try: s_data = json.loads(s_data)
                    except: s_data = []
                for it in s_data:
                    sku_k = str(it.get("SKU", it.get("sku", ""))).split('.')[0].strip().upper()
                    if sku_k and (sku_k not in lookup_cogs or lookup_cogs[sku_k]["cogs"] == 0):
                        lookup_cogs[sku_k] = {
                            "name": str(it.get("ITEM NAME", it.get("item_name", it.get("ARTIKEL", "-")))).strip(),
                            "cogs": safe_int(it.get("HARGA BELI", it.get("cogs", 0)), 0)
                        }

        # 2. Ambil Riwayat Memo di Database Supabase
        existing_memos = {}
        res_memo = requests.get(f"{SUPABASE_URL}/rest/v1/memo_pengajuan?select=*", headers=HEADERS_SB, timeout=25)
        if res_memo.status_code == 200:
            for m in res_memo.json():
                tgl = str(m.get("tanggal", ""))[:10]
                tujuan = str(m.get("tujuan", "")).strip().upper()
                existing_memos[(tgl, tujuan)] = m

        # 3. Download Spreadsheet Google Sheets
        dl_url = SPREADSHEET_URL
        m_id = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', SPREADSHEET_URL)
        if m_id:
            dl_url = f"https://docs.google.com/spreadsheets/d/{m_id.group(1)}/export?format=xlsx"

        xl = pd.ExcelFile(dl_url)
        all_sheets = xl.sheet_names

        # Cari sheet 'Permintaan markom'
        tgt_sheet = None
        for s in all_sheets:
            if "PERMINTAAN MARKOM" in s.strip().upper():
                tgt_sheet = s
                break
        if not tgt_sheet:
            tgt_sheet = all_sheets[0]

        print(f"   🎯 Sheet yang Dibaca: '{tgt_sheet}'")
        df = pd.read_excel(xl, sheet_name=tgt_sheet)
        if df.empty or df.shape[1] < 5:
            print("   ⚠️ Data di sheet kosong!")
            return

        # 4. Pemetaan Kolom
        def find_col(candidates, default_idx):
            for cand in candidates:
                for c in df.columns:
                    if cand.upper() in str(c).strip().upper():
                        return c
            return df.columns[default_idx]

        col_pic   = find_col(["PIC"], 0)
        col_note1 = find_col(["NOTE AMP"], 2)
        col_note2 = find_col(["NO TELP"], 1)
        col_sku   = find_col(["SKU", "BARCODE"], 3)
        col_qty   = find_col(["QTY", "JUMLAH"], 4)
        col_tgl   = find_col(["TANGGAL REQ", "TIMESTAMP"], 14)
        col_bin   = find_col(["BIN PICK", "PICK_LOCATION"], 16)

        # 5. Filter baris EVENT / HADIAH / GIFT
        pattern = "EVENT|HADIAH|GIFT"
        mask = (
            df[col_note1].fillna("").astype(str).str.contains(pattern, case=False, na=False) |
            df[col_note2].fillna("").astype(str).str.contains(pattern, case=False, na=False)
        )
        df_filtered = df[mask].copy()

        if df_filtered.empty:
            print("   ℹ️ Tidak ada data dengan note 'EVENT', 'HADIAH', atau 'GIFT'.")
            return

        # 6. Susun Rincian Item Permintaan
        grouped_events = {}
        for row_idx, (_, r) in enumerate(df_filtered.iterrows(), start=1):
            pic_val = str(r[col_pic]).strip() if pd.notna(r[col_pic]) else "MARKOM"
            n1 = str(r[col_note1]).strip() if pd.notna(r[col_note1]) else ""
            n2 = str(r[col_note2]).strip() if pd.notna(r[col_note2]) else ""
            note_val = n1.upper() if n1 else (n2.upper() if n2 else "EVENT")

            raw_tgl = str(r[col_tgl]).strip() if pd.notna(r[col_tgl]) else ""
            try:
                dt_parsed = pd.to_datetime(raw_tgl, dayfirst=True)
                tgl_val = dt_parsed.strftime("%Y-%m-%d")
            except Exception:
                tgl_val = raw_tgl[:10] if len(raw_tgl) >= 10 else datetime.now().strftime("%Y-%m-%d")

            sku_val = str(r[col_sku]).split('.')[0].strip().upper() if pd.notna(r[col_sku]) else ""
            if not sku_val or sku_val in ["-", "NAN", "NONE", "SKU", ""]:
                continue

            q_val = safe_int(r[col_qty], 1)
            b_val = str(r[col_bin]).strip() if pd.notna(r[col_bin]) else "GL1-DC-OUT"
            info = lookup_cogs.get(sku_val, {})
            cogs_val = info.get("cogs", 0)

            item_entry = {
                "id": f"REQ-{sku_val}-{row_idx}",
                "tanggal": tgl_val,
                "pic": pic_val,
                "keterangan": note_val,
                "bin": b_val,
                "sku": sku_val,
                "item_name": info.get("name") or sku_val,
                "cogs": cogs_val,
                "qty": q_val,
                "subtotal": cogs_val * q_val
            }

            group_key = (tgl_val, note_val)
            if group_key not in grouped_events:
                grouped_events[group_key] = {"pic": pic_val, "items": []}
            grouped_events[group_key]["items"].append(item_entry)

        # 7. Update atau Insert ke Supabase
        new_inserts = []
        for (tgl_doc, event_name), grp_data in grouped_events.items():
            items_list = grp_data["items"]
            pic_doc = grp_data["pic"]
            tot_nom = sum(x["subtotal"] for x in items_list)
            key_m = (tgl_doc, event_name)

            if key_m in existing_memos:
                exist = existing_memos[key_m]
                if str(exist.get("status_adj", "PENDING")).upper() == "DONE":
                    continue

                existing_items = exist.get("items", [])
                if isinstance(existing_items, str):
                    try: existing_items = json.loads(existing_items)
                    except Exception: existing_items = []

                sig_new = sorted([(x['sku'], x['qty'], x['subtotal']) for x in items_list])
                sig_old = sorted([(x.get('sku'), x.get('qty'), x.get('subtotal')) for x in existing_items])

                if sig_new == sig_old and exist.get("nominal") == tot_nom and exist.get("diajukan_oleh") == pic_doc:
                    continue

                safe_id = urllib.parse.quote(str(exist['id']), safe='')
                url_upd = f"{SUPABASE_URL}/rest/v1/memo_pengajuan?id=eq.{safe_id}"
                res_patch = requests.patch(
                    url_upd,
                    headers=HEADERS_SB,
                    json={"nominal": tot_nom, "diajukan_oleh": pic_doc, "items": items_list}
                )
                if res_patch.status_code in [200, 204]:
                    print(f"   🔄 [UPDATE] Memo '{event_name}' ({exist['id']}) berhasil diperbarui!")
                else:
                    print(f"   ⚠️ Gagal update memo {exist['id']}: {res_patch.text}")
            else:
                memo_id = f"MEMO/ZKN/{tgl_doc.replace('-', '')}/{random.randint(100, 999)}"
                new_inserts.append({
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

        if new_inserts:
            res_ins = requests.post(f"{SUPABASE_URL}/rest/v1/memo_pengajuan", headers=HEADERS_SB, json=new_inserts)
            if res_ins.status_code in [200, 201]:
                print(f"   🚀 Berhasil membuat {len(new_inserts)} memo baru di Supabase!")
            else:
                print(f"   ⚠️ Gagal insert memo baru: {res_ins.text}")
        else:
            print("   ✅ Memo Markom sudah sinkron dan mutakhir.")

    except Exception as e:
        print(f"   ❌ Terjadi kesalahan: {e}")

if __name__ == "__main__":
    run_sync()