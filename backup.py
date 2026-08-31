import json
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

print("⏳ Sedang menarik seluruh data lama dari database Supabase...")

try:
    req = urllib.request.Request(f"{SUPABASE_URL}/rest/v1/shipping_costs?select=*", headers=headers)
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        if data:
            df = pd.DataFrame(data)
            # Simpan otomatis ke file Excel dan CSV
            df.to_excel("backup_data_ongkir.xlsx", index=False)
            df.to_csv("backup_data_ongkir.csv", index=False)
            print(f"✅ BERHASIL! Sebanyak {len(df):,} baris data lama berhasil diselamatkan ke file 'backup_data_ongkir.xlsx' & 'backup_data_ongkir.csv'!")
        else:
            print("ℹ️ Database terhubung, tetapi belum ada data tersimpan di tabel shipping_costs.")
except Exception as e:
    print(f"❌ Gagal mengambil data: {e}")