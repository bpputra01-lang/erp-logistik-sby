import io
import json
import os
import urllib.request
import pandas as pd

SUPABASE_URL = "https://ufhjrsxzcffdfswfqlzk.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVmaGpyc3h6Y2ZmZGZzd2ZxbHprIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYxNTI5NjgsImV4cCI6MjA5MTcyODk2OH0.DDlKkXU5-nVvNYK_uLYzXLgaj8oDT4s8vbjAoWMWacI"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

print("=" * 75)
print("🔍 MEMULAI PEMINDAIAN MENDALAM SELURUH TABEL SUPABASE LAMA...")
print("=" * 75)

# 1. BACA OPENAPI SCHEMA UNTUK MENDAPATKAN NAMA TABEL ASLI
discovered_tables = set()
try:
    req_schema = urllib.request.Request(f"{SUPABASE_URL}/rest/v1/?apikey={SUPABASE_KEY}", headers=headers)
    with urllib.request.urlopen(req_schema) as resp:
        schema = json.loads(resp.read().decode("utf-8"))
        if "definitions" in schema:
            for tbl in schema["definitions"].keys():
                discovered_tables.add(tbl)
        if "paths" in schema:
            for path in schema["paths"].keys():
                clean_name = path.replace("/", "").strip()
                if clean_name and clean_name != "rpc":
                    discovered_tables.add(clean_name)
    if discovered_tables:
        print(f"📡 Schema Terdeteksi Otomatis: {list(discovered_tables)}")
except Exception as e:
    print(f"ℹ️ Info schema: {e}")

# 2. DAFTAR LENGKAP VARIASI NAMA TABEL LOGISTIK & RETUR
candidate_tables = [
    # ONGKIR & TIMBANG
    "shipping_costs", "data_timbang_ongkir", "timbang_ongkir", "data_timbang", "timbang", "ongkir",
    
    # RETUR / RTO
    "retur_out", "list_retur_out", "data_retur_out", "retur", "returs", "retur_in", "data_retur", 
    "rto_out", "rto_in", "rto", "data_rto", "list_rto", "retur_toko", "retur_dc", "mutasi_retur",
    "retur_item", "retur_items", "pengajuan_retur", "pengajuan_rto", "returns", "return_out",
    
    # REJECT & DEFECT
    "reject_defect", "reject_defect_list", "data_reject_defect", "reject_list", "defect_list",
    "pengajuan_reject", "pengajuan_defect", "pengajuan_reject_defect", "reject", "defect", "rejects", "defects",
    "data_reject", "data_defect", "reject_toko", "defect_toko",
    
    # KARANTINA
    "pengajuan_karantina", "karantina", "mutasi_karantina", "data_karantina", "list_karantina", "quarantine",
    
    # STOCK & MASTER LAIN
    "stock", "stocks", "inventory", "stock_opname", "cycle_count", "putaway", "users", "profiles", "history"
]

all_tables_to_check = sorted(list(discovered_tables.union(set(candidate_tables))))

os.makedirs("backup_database_lengkap", exist_ok=True)
master_excel_file = "BACKUP_SEMUA_DATA_SUPABASE.xlsx"
saved_dataframes = {}

print(f"📋 Memeriksa total {len(all_tables_to_check)} variasi nama tabel...")
print("-" * 75)

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
                    sheet_name = tbl[:31]
                    saved_dataframes[sheet_name] = df
                    
                    csv_path = os.path.join("backup_database_lengkap", f"{tbl}.csv")
                    df.to_csv(csv_path, index=False)
                    print(f"✅ TABEL BERHASIL DISEDOT: '{tbl}' ➔ {len(df):,} baris data!")
                elif isinstance(rows, list) and len(rows) == 0:
                    print(f"⚪ Tabel '{tbl}' ditemukan, tetapi kosong (0 baris).")
    except urllib.error.HTTPError as he:
        if he.code == 404:
            continue
        elif he.code in [401, 403]:
            print(f"🔒 Tabel '{tbl}' ada di database, tetapi dikunci hak akses (RLS/Private).")
    except Exception:
        continue

print("-" * 75)

# 3. SIMPAN SEMUA TABEL KE MASTER EXCEL
if saved_dataframes:
    with pd.ExcelWriter(master_excel_file, engine="openpyxl") as writer:
        for sheet, df_tbl in saved_dataframes.items():
            df_tbl.to_excel(writer, sheet_name=sheet, index=False)
            
    print("=" * 75)
    print(f"🎉 SELESAI! Sebanyak {len(saved_dataframes)} TABEL berhasil diselamatkan:")
    for name, d in saved_dataframes.items():
        print(f"   👉 Sheet '{name}': {len(d):,} Baris")
    print(f"\n📁 File Master Excel tersimpan di: '{master_excel_file}'")
    print("=" * 75)
else:
    print("❌ Tidak ada tabel data yang ditemukan dengan API Key saat ini.")