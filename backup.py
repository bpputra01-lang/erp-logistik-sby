import io
import json
import os
import urllib.request
import pandas as pd

# Kunci Supabase Lama Anda
SUPABASE_URL = "https://ufhjrsxzcffdfswfqlzk.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVmaGpyc3h6Y2ZmZGZzd2ZxbHprIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYxNTI5NjgsImV4cCI6MjA5MTcyODk2OH0.DDlKkXU5-nVvNYK_uLYzXLgaj8oDT4s8vbjAoWMWacI"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

print("=" * 70)
print("🔍 MEMULAI PEMINDAIAN SELURUH TABEL DATABASE SUPABASE LAMA...")
print("=" * 70)

# 1. Deteksi Otomatis Semua Nama Tabel via OpenAPI Schema PostgREST
discovered_tables = set()
try:
    req_schema = urllib.request.Request(f"{SUPABASE_URL}/rest/v1/?apikey={SUPABASE_KEY}", headers=headers)
    with urllib.request.urlopen(req_schema) as resp:
        schema = json.loads(resp.read().decode("utf-8"))
        # Ambil nama tabel dari definisi OpenAPI
        if "definitions" in schema:
            for tbl in schema["definitions"].keys():
                discovered_tables.add(tbl)
        if "paths" in schema:
            for path in schema["paths"].keys():
                tbl_name = path.replace("/", "").strip()
                if tbl_name and tbl_name != "rpc":
                    discovered_tables.add(tbl_name)
except Exception as e:
    print(f"ℹ️ Deteksi otomatis schema: {e}")

# Daftar fallback nama tabel umum jika schema terproteksi
candidate_tables = [
    "shipping_costs", "data_timbang_ongkir", "timbang_ongkir", "data_timbang",
    "retur_out", "list_retur_out", "data_retur_out", "retur",
    "reject_defect", "reject_defect_list", "data_reject_defect", "reject_list", "defect_list",
    "pengajuan_reject", "pengajuan_defect", "pengajuan_reject_defect",
    "pengajuan_karantina", "karantina", "mutasi_karantina", "data_karantina",
    "users", "profiles", "history"
]

all_tables_to_check = sorted(list(discovered_tables.union(set(candidate_tables))))

# Folder untuk menyimpan backup CSV
os.makedirs("backup_database_lengkap", exist_ok=True)
master_excel_file = "BACKUP_SEMUA_DATA_SUPABASE.xlsx"

saved_dataframes = {}

print(f"📋 Memeriksa {len(all_tables_to_check)} potensi tabel database...")
print("-" * 70)

for tbl in all_tables_to_check:
    try:
        url = f"{SUPABASE_URL}/rest/v1/{tbl}?select=*"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            raw_data = resp.read().decode("utf-8")
            if raw_data:
                rows = json.loads(raw_data)
                if isinstance(rows, list) and len(rows) > 0:
                    df = pd.DataFrame(rows)
                    sheet_name = tbl[:31] # Batas panjang sheet excel max 31 karakter
                    saved_dataframes[sheet_name] = df
                    
                    # Simpan juga file CSV per tabel
                    csv_path = os.path.join("backup_database_lengkap", f"{tbl}.csv")
                    df.to_csv(csv_path, index=False)
                    print(f"✅ TABEL DITEMUKAN: '{tbl}' ➔ {len(df):,} baris data diselamatkan!")
                elif isinstance(rows, list) and len(rows) == 0:
                    print(f"⚪ Tabel '{tbl}' ada di database, tetapi masih kosong (0 baris).")
    except urllib.error.HTTPError as he:
        if he.code == 404:
            continue # Tabel memang tidak dibuat
        else:
            print(f"⚠️ Akses tabel '{tbl}' (HTTP {he.code})")
    except Exception as e:
        continue

print("-" * 70)

# 2. Simpan Semua Tabel ke dalam 1 File Master Excel
if saved_dataframes:
    with pd.ExcelWriter(master_excel_file, engine="openpyxl") as writer:
        for sheet, df_tbl in saved_dataframes.items():
            df_tbl.to_excel(writer, sheet_name=sheet, index=False)
            
    print("=" * 70)
    print(f"🎉 SUKSES TOTAL! Sebanyak {len(saved_dataframes)} TABEL berhasil disedot lengkap!")
    print(f"📁 File Master Excel: '{master_excel_file}' (Berisi Sheet per tabel)")
    print(f"📁 File CSV per tabel tersimpan di folder: 'backup_database_lengkap/'")
    print("=" * 70)
else:
    print("❌ Tidak ada tabel yang memiliki data untuk di-download.")