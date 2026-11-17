from datetime import datetime
import json
import os
import time
import pandas as pd
from playwright.sync_api import sync_playwright
from pytz import timezone
import schedule
from supabase import Client, create_client

# ==================== KREDENSIAL ==================== #
SUPABASE_URL = "https://fanzsmghhbefhhaicrok.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZhbnpzbWdoaGJlZmhoYWljcm9rIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODgxNTQzNDgsImV4cCI6MjEwMzczMDM0OH0.brCSOO9nHAUK8CxDWPperpJ--_NA_nwy5cO9OqGv3I0"

PBI_USER = "coor_log"
PBI_PASS = "Us3fu1JEZ"
REPORT_URL = "https://report.jezpro.id/powerbi/?id=f8f93cc4-2ec6-4535-a708-94fd3cf99f22"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

COLS = [
    "order_number",
    "warehouse",
    "order_date_created",
    "resi",
    "platform_name",
    "store",
    "order_status",
    "fdr_status",
    "internal_order_status",
    "tgl_manifest",
    "payment_method",
    "packed_time",
    "fdr_time",
    "shipping_method",
    "created_at",
]


def run_scraper():
  wib = timezone("Asia/Jakarta")
  now_wib = datetime.now(wib)
  print(
      f"\n{'='*55}\n[{now_wib.strftime('%Y-%m-%d %H:%M:%S')} WIB] Memulai"
      " Scraping FDR via Playwright..."
  )

  target_data = []

  with sync_playwright() as p:
    # headless=False agar jendela browser muncul di layar Anda
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(
        http_credentials={"username": PBI_USER, "password": PBI_PASS}
    )
    page = context.new_page()

    # Mencegat (intercept) request data tabel saat Power BI memuat visual
    def handle_response(response):
      if "/querydata" in response.url and response.request.method == "POST":
        try:
          body = response.json()
          results = body.get("results", [])
          if results:
            dm0 = (
                results[0]
                .get("result", {})
                .get("data", {})
                .get("dsr", {})
                .get("DS", [{}])[0]
                .get("PH", [{}])[0]
                .get("DM0", [])
            )
            # Cek jika ini adalah request tabel utama (memiliki lebih dari 5 kolom/cell)
            if dm0 and len(dm0) > 0 and "C" in dm0[0] and len(dm0[0]["C"]) >= 10:
              target_data.append(dm0)
              print(
                  f"🎯 Berhasil mencegat paket data tabel utama FDR! ({len(dm0)}"
                  " baris mentah)"
              )
        except Exception:
          pass

    page.on("response", handle_response)

    try:
      print("🌐 Membuka Power BI report...")
      page.goto(REPORT_URL, timeout=60000)

      # Periksa apakah ada form login HTML di web
      time.sleep(2)
      user_input = page.locator("input[type='text'], input[name*='user']").first
      if user_input.is_visible(timeout=3000):
        print("🔑 Terdeteksi form login web, mengisi username & password...")
        user_input.fill(PBI_USER)
        page.locator("input[type='password']").first.fill(PBI_PASS)
        page.keyboard.press("Enter")

      # Tunggu hingga tabel termuat dan data tertangkap
      print("⏳ Menunggu visual tabel selesai memuat data...")
      for _ in range(30):
        if len(target_data) > 0:
          break
        page.wait_for_timeout(1000)

      # Beri jeda 2 detik sebelum browser ditutup
      page.wait_for_timeout(2000)
      browser.close()

    except Exception as e:
      print(f"❌ Terjadi kesalahan pada browser: {e}")
      browser.close()
      return

  if not target_data:
    print(
        "⚠️ Gagal menangkap data tabel. Pastikan dashboard berhasil terbuka dan"
        " tidak stuck di login."
    )
    return

  # Parsing data
  try:
    dm0 = target_data[0]
    rows = []
    last_row = [None] * len(COLS)
    for item in dm0:
      if "C" in item:
        cells = item["C"]
        row = [
            cells[i] if (i < len(cells) and cells[i] is not None) else None
            for i in range(len(COLS))
        ]
        for i in range(len(row)):
          if row[i] is None and last_row[i] is not None:
            row[i] = last_row[i]
        rows.append(row)
        last_row = row

    df = pd.DataFrame(rows, columns=COLS)
  except Exception as e:
    print(f"❌ Error parsing data: {e}")
    return

  if df.empty:
    print("⚠️ DataFrame kosong.")
    return

  # ==================== FILTER DATA ==================== #
  # 1. Warehouse Surabaya
  df = df[df["warehouse"].fillna("").str.strip().str.upper() == "SURABAYA"]

  # 2. Selain status DONE dan CANCEL
  excluded = [
      "DONE",
      "DONE ONLINE",
      "BATAL",
      "DIBATALKAN",
      "CANCEL",
      "CANCELLED",
      "PEMBATALAN DIAJUKAN",
  ]
  mask_internal = ~df["internal_order_status"].fillna("").str.upper().isin(
      excluded
  )
  mask_order = ~df["order_status"].fillna("").str.upper().isin(excluded)
  df = df[mask_internal & mask_order]

  # 3. Tanggal bulan ini ke depan
  first_day_of_month = now_wib.replace(
      day=1, hour=0, minute=0, second=0, microsecond=0
  )
  df["dt_temp"] = pd.to_datetime(
      df["order_date_created"], errors="coerce"
  ).dt.tz_localize("Asia/Jakarta", ambiguous="NaT")
  df = df[df["dt_temp"].isna() | (df["dt_temp"] >= first_day_of_month)]
  df = df.drop(columns=["dt_temp"])

  print(f"📊 Ditemukan {len(df)} pesanan Surabaya aktif.")

  # ==================== SIMPAN KE SUPABASE ==================== #
  if not df.empty:
    records = df.to_dict(orient="records")
    for r in records:
      for k, v in r.items():
        if pd.isna(v) or v == "":
          r[k] = None

    try:
      supabase.table("fdr_orders").upsert(
          records, on_conflict="order_number"
      ).execute()
      print(
          f"✅ SUKSES! {len(records)} data pesanan masuk ke Supabase"
          " (fdr_orders)!"
      )
    except Exception as e:
      print(f"❌ Gagal simpan ke Supabase: {e}")


# ==================== SCHEDULER ==================== #
if __name__ == "__main__":
  run_scraper()

  schedule.every().day.at("14:00", "Asia/Jakarta").do(run_scraper)
  schedule.every().day.at("21:00", "Asia/Jakarta").do(run_scraper)

  print("\n" + "=" * 55)
  print("⏰ Scheduler AKTIF! Berjalan otomatis setiap:")
  print("   - Pukul 14:00 WIB")
  print("   - Pukul 21:00 WIB")
  print("=" * 55 + "\n")

  while True:
    schedule.run_pending()
    time.sleep(30)