import io
import json
import os
import time
import urllib.request
import pandas as pd

SUPABASE_URL = "https://ufhjrsxzcffdfswfqlzk.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVmaGpyc3h6Y2ZmZGZzd2ZxbHprIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYxNTI5NjgsImV4cCI6MjA5MTcyODk2OH0.DDlKkXU5-nVvNYK_uLYzXLgaj8oDT4s8vbjAoWMWacI"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Accept": "application/openapi+json",
    "Content-Type": "application/json"
}

print("=" * 80)
print("🚀 MEMULAI PENYEDOTAN TOTAL SELURUH TABEL SUPABASE LAMA...")
print("=" * 80)

discovered_tables = set()

# 1. BONGKAR SKEMA OPENAPI RESMI POSTGREST
try:
    req_schema = urllib.request.Request(f"{SUPABASE_URL}/rest/v1/", headers=headers)
    with urllib.request.urlopen(req_schema) as resp:
        schema = json.loads(resp.read().decode("utf-8"))
        if "definitions" in schema:
            for tbl in schema["definitions"].keys():
                discovered_tables.add(tbl.strip())
        if "paths" in schema:
            for path in schema["paths"].keys():
                clean_name = path.replace("/", "").strip()
                if clean_name and clean_name != "rpc":
                    discovered_tables.add(clean_name)
    if discovered_tables:
        print(f"📡 DITEMUKAN DARI SKEMA RESMI: {list(discovered_tables)}")
except Exception as e:
    pass

# 2. 250+ VARIASI LENGKAP NAMA TABEL GUDANG, RETUR, RTO, TIMBANG, REJECT
candidates = [
    # RETUR & RTO LENGKAP
    "retur", "returs", "retur_out", "retur_in", "retur_outlet", "retur_toko", "retur_dc", "retur_gudang",
    "retur_barang", "data_retur", "data_retur_out", "data_retur_in", "list_retur", "list_retur_out", "list_retur_in",
    "tb_retur", "tb_retur_out", "t_retur", "pengajuan_retur", "history_retur", "rekap_retur", "log_retur",
    "rto", "rto_out", "rto_in", "rto_data", "data_rto", "list_rto", "tb_rto", "rto_list", "rto_retur",
    "rto_surabaya", "rto_toko", "rto_dc", "rto_gudang", "compare_rto", "compare_penerimaan_rto", "penerimaan_rto",
    "rto_receiving", "rto_masuk", "rto_keluar", "draft_rto", "new_draft_rto", "rto_gateway", "rto_gate",
    "return", "returns", "return_out", "return_in", "sales_return", "purchase_return", "return_order",

    # TIMBANG & ONGKIR
    "shipping_costs", "shipping_cost", "data_timbang_ongkir", "timbang_ongkir", "data_timbang", "timbang", "ongkir",
    "ongkir_in_out", "ongkir_in", "ongkir_out", "timbangan", "data_ongkir", "biaya_ongkir", "rekap_ongkir",

    # REJECT & DEFECT
    "reject", "defect", "rejects", "defects", "reject_list", "defect_list", "reject_defect", "reject_defect_list",
    "data_reject", "data_defect", "data_reject_defect", "pengajuan_reject", "pengajuan_defect", "pengajuan_reject_defect",
    "gagal_qc", "qc_reject", "barang_reject", "barang_defect", "reject_toko", "defect_toko", "reject_dc",

    # KARANTINA
    "karantina", "quarantine", "mutasi_karantina", "pengajuan_karantina", "data_karantina", "list_karantina",
    "karantina_dc", "karantina_store", "karantina_store_02", "quarantine_items",

    # STOCK & CYCLE COUNT & AUDIT
    "stock", "stocks", "inventory", "stock_opname", "cycle_count", "list_bin_cycle_count", "bin_cycle_count",
    "putaway", "picking", "putaway_audit", "picking_audit", "putaway_picking_audit", "scan_out", "refill",
    "overstock", "withdraw", "mutasi", "inbound", "outbound", "staging_inbound", "staging_outbound",
    "purchase_order", "po", "po_receiving", "history", "logs", "users", "profiles", "accounts"
]

all_tables = sorted(list(discovered_tables.union(set(candidates))))
os.makedirs("backup_database_lengkap", exist_ok=True)

saved_data = {}
print(f"📋 Memindai total {len(all_tables)} nama tabel database...")
print("-" * 80)

for tbl in all_tables:
    try:
        url = f"{SUPABASE_URL}/rest/v1/{tbl}?select=*"
        req = urllib.request.Request(url, headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        })
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode("utf-8")
            if raw:
                rows = json.loads(raw)
                if isinstance(rows, list) and len(rows) > 0:
                    df = pd.DataFrame(rows)
                    sheet_name = tbl[:31]
                    saved_data[sheet_name] = df
                    
                    csv_path = os.path.join("backup_database_lengkap", f"{tbl}.csv")
                    df.to_csv(csv_path, index=False)
                    print(f"✅ DITEMUKAN TABEL: '{tbl}' ➔ {len(df):,} baris data diselamatkan!")
                elif isinstance(rows, list) and len(rows) == 0:
                    print(f"⚪ Tabel '{tbl}' ada di database (0 baris).")
    except urllib.error.HTTPError as he:
        if he.code in [401, 403]:
            print(f"🔒 Tabel '{tbl}' terdeteksi tapi terkunci RLS.")
    except Exception:
        pass

print("-" * 80)

# 3. SIMPAN KE MASTER EXCEL (NAMA ANTI-LOCK PERMISSION ERROR)
timestamp = time.strftime("%Y%m%d_%H%M%S")
master_file = f"BACKUP_DATABASE_TOTAL_{timestamp}.xlsx"

if saved_data:
    try:
        with pd.ExcelWriter(master_file, engine="openpyxl") as writer:
            for sheet, df_tbl in saved_data.items():
                df_tbl.to_excel(writer, sheet_name=sheet, index=False)
        print("=" * 80)
        print(f"🎉 SELESAI! Sebanyak {len(saved_data)} TABEL BERHASIL DISEDOT:")
        for name, d in saved_data.items():
            print(f"   👉 Tabel '{name}': {len(d):,} Baris")
        print(f"\n📁 File Master Excel Baru: '{master_file}'")
        print(f"📁 File CSV per tabel di folder: 'backup_database_lengkap/'")
        print("=" * 80)
    except Exception as e:
        print(f"Gagal simpan Excel: {e}")
else:
    print("❌ Tidak ada tabel yang memiliki data.")