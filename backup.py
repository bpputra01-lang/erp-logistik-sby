import json
import urllib.request
import urllib.error

SUPABASE_URL = "https://ufhjrsxzcffdfswfqlzk.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVmaGpyc3h6Y2ZmZGZzd2ZxbHprIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYxNTI5NjgsImV4cCI6MjA5MTcyODk2OH0.DDlKkXU5-nVvNYK_uLYzXLgaj8oDT4s8vbjAoWMWacI"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# Cek semua kemungkinan tabel retur & data lainnya
test_tables = [
    "retur_out", "list_retur_out", "data_retur_out", "rto_out", "rto", "retur",
    "data_timbang_ongkir", "pengajuan_reject", "pengajuan_karantina", "reject_list",
    "mutasi_karantina", "shipping_costs"
]

print("=" * 65)
print("🔍 HASIL DETEKSI STATUS FISIK TABEL DI DATABASE POSTGRESQL:")
print("=" * 65)

for tbl in test_tables:
    # Trik: sengaja meminta kolom palsu untuk mengecek keberadaan tabel di Postgres
    url = f"{SUPABASE_URL}/rest/v1/{tbl}?select=kolom_cek_keberadaan_tabel_123"
    req = urllib.request.Request(url, headers=headers)
    try:
        urllib.request.urlopen(req)
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode('utf-8')
        if "schema cache" in err_msg and "table" in err_msg:
            print(f"❌ '{tbl}' ➔ TIDAK PERNAH ADA di database ini.")
        elif "column" in err_msg:
            print(f"✅ '{tbl}' ➔ ADA DI DATABASE! (Terkunci RLS atau kolom sesuai)")
        elif e.code == 404:
            print(f"❌ '{tbl}' ➔ TIDAK DITEMUKAN (404).")
        else:
            print(f"ℹ️ '{tbl}' ➔ Status HTTP {e.code}")
    except Exception as ex:
        print(f"⚠️ '{tbl}': {ex}")

print("=" * 65)