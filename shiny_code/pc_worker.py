import time
import json
import urllib.request
from jezpro_service import fetch_jezpro_stock_excel_bytes

SUPABASE_URL = "https://fanzsmghhbefhhaicrok.supabase.co"
SUPABASE_KEY = "sb_secret_Jqy-KREUEOXyjXLQi_5wCQ_aPTx2SKW" # Secret Key

def check_and_execute_task():
    try:
        # 1. Cek apakah ada sinyal PENDING dari Web Shiny
        check_url = f"{SUPABASE_URL}/rest/v1/sync_queue?status=eq.PENDING&order=id.desc&limit=1"
        req = urllib.request.Request(check_url, headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            tasks = json.loads(resp.read().decode('utf-8'))

        if not tasks or len(tasks) == 0:
            return

        task_id = tasks[0]["id"]
        print(f"⚡ Menerima trigger dari Web Shiny (Task #{task_id})!")

        # 2. Ubah status menjadi PROCESSING
        update_url = f"{SUPABASE_URL}/rest/v1/sync_queue?id=eq.{task_id}"
        req_upd = urllib.request.Request(
            update_url,
            data=json.dumps({"status": "PROCESSING"}).encode('utf-8'),
            headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"},
            method="PATCH"
        )
        urllib.request.urlopen(req_upd)

        # 3. Tarik Data dari Jezpro via Jaringan Kantor
        print("🌐 Mendownload stok dari Jezpro...")
        excel_bytes = fetch_jezpro_stock_excel_bytes(
            email="fajarbintang786@jez.co.id",
            password="999", # Gunakan password akun Jezpro Anda
            store_id=3,
            qty_filter=0
        )

        # 4. Upload ke Supabase Storage
        print(f"☁️ Mengunggah ke Supabase Storage ({len(excel_bytes):,} bytes)...")
        upload_url = f"{SUPABASE_URL}/storage/v1/object/stock_files/latest_stock.xlsx"
        req_upload = urllib.request.Request(
            upload_url,
            data=excel_bytes,
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "x-upsert": "true"
            },
            method="POST"
        )
        urllib.request.urlopen(req_upload)

        # 5. Ubah status menjadi DONE
        req_done = urllib.request.Request(
            update_url,
            data=json.dumps({"status": "DONE"}).encode('utf-8'),
            headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"},
            method="PATCH"
        )
        urllib.request.urlopen(req_done)
        print("✅ Task Selesai! Web Shiny siap membaca data.")

    except Exception as e:
        print(f"❌ Error Worker: {e}")

if __name__ == "__main__":
    print("🚀 PC Worker Aktif & Standby Menunggu Sinyal dari Web Shiny...")
    while True:
        check_and_execute_task()
        time.sleep(2) # Cek sinyal setiap 2 detik