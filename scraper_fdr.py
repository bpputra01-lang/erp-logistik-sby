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

PAYLOAD_QUERY = {
    "version": "1.0.0",
    "queries": [{
        "Query": {
            "Commands": [{
                "SemanticQueryDataShapeCommand": {
                    "Query": {
                        "Version": 2,
                        "From": [
                            {"Name": "f", "Entity": "FDR", "Type": 0},
                            {
                                "Name": "d",
                                "Entity": "Date Filter",
                                "Type": 0,
                            },
                        ],
                        "Select": [
                            {
                                "Column": {
                                    "Expression": {
                                        "SourceRef": {"Source": "f"}
                                    },
                                    "Property": "Order Number",
                                },
                                "Name": "FDR.Order Number",
                            },
                            {
                                "Column": {
                                    "Expression": {
                                        "SourceRef": {"Source": "f"}
                                    },
                                    "Property": "warehouse",
                                },
                                "Name": "FDR.warehouse",
                            },
                            {
                                "Column": {
                                    "Expression": {
                                        "SourceRef": {"Source": "f"}
                                    },
                                    "Property": "order_date_created",
                                },
                                "Name": "FDR.order_date_created",
                            },
                            {
                                "Column": {
                                    "Expression": {
                                        "SourceRef": {"Source": "f"}
                                    },
                                    "Property": "Resi",
                                },
                                "Name": "FDR.Resi",
                            },
                            {
                                "Column": {
                                    "Expression": {
                                        "SourceRef": {"Source": "f"}
                                    },
                                    "Property": "platform_name",
                                },
                                "Name": "FDR.platform_name",
                            },
                            {
                                "Column": {
                                    "Expression": {
                                        "SourceRef": {"Source": "f"}
                                    },
                                    "Property": "Store",
                                },
                                "Name": "FDR.Store",
                            },
                            {
                                "Column": {
                                    "Expression": {
                                        "SourceRef": {"Source": "f"}
                                    },
                                    "Property": "order_status",
                                },
                                "Name": "FDR.order_status",
                            },
                            {
                                "Column": {
                                    "Expression": {
                                        "SourceRef": {"Source": "f"}
                                    },
                                    "Property": "FDRstatus",
                                },
                                "Name": "FDR.FDRstatus",
                            },
                            {
                                "Column": {
                                    "Expression": {
                                        "SourceRef": {"Source": "f"}
                                    },
                                    "Property": "internal_order_status",
                                },
                                "Name": "FDR.internal_order_status",
                            },
                            {
                                "Column": {
                                    "Expression": {
                                        "SourceRef": {"Source": "f"}
                                    },
                                    "Property": "tgl_manifest",
                                },
                                "Name": "FDR.tgl_manifest",
                            },
                            {
                                "Column": {
                                    "Expression": {
                                        "SourceRef": {"Source": "f"}
                                    },
                                    "Property": "payment_method",
                                },
                                "Name": "FDR.payment_method",
                            },
                            {
                                "Column": {
                                    "Expression": {
                                        "SourceRef": {"Source": "f"}
                                    },
                                    "Property": "packed_time",
                                },
                                "Name": "FDR.packed_time",
                            },
                            {
                                "Column": {
                                    "Expression": {
                                        "SourceRef": {"Source": "f"}
                                    },
                                    "Property": "FDRtime",
                                },
                                "Name": "FDR.FDRtime",
                            },
                            {
                                "Column": {
                                    "Expression": {
                                        "SourceRef": {"Source": "f"}
                                    },
                                    "Property": "shipping_method",
                                },
                                "Name": "FDR.shipping_method",
                            },
                            {
                                "Column": {
                                    "Expression": {
                                        "SourceRef": {"Source": "f"}
                                    },
                                    "Property": "created_at",
                                },
                                "Name": "FDR.created_at",
                            },
                        ],
                        "Where": [{
                            "Condition": {
                                "In": {
                                    "Expressions": [{
                                        "Column": {
                                            "Expression": {
                                                "SourceRef": {"Source": "d"}
                                            },
                                            "Property": "Filter",
                                        }
                                    }],
                                    "Values": [[{
                                        "Literal": {
                                            "Value": "'Current Month'"
                                        }
                                    }]],
                                }
                            }
                        }],
                        "OrderBy": [{
                            "Direction": 2,
                            "Expression": {
                                "Column": {
                                    "Expression": {
                                        "SourceRef": {"Source": "f"}
                                    },
                                    "Property": "order_date_created",
                                }
                            },
                          }],
                        "Binding": {
                            "Primary": {
                                "Groupings": [{
                                    "Projections": list(range(15)),
                                    "Subtotal": 1,
                                }]
                            },
                            "DataReduction": {
                                "DataVolume": 3,
                                "Primary": {"Window": {"Count": 2000}},
                            },
                            "Version": 1,
                        },
                    }
                }
            }]
        },
        "QueryId": "",
        "ApplicationContext": {
            "Sources": [{"VisualId": "f7300ca4d0cbc490c149"}]
        },
    }],
    "cancelQueries": [],
    "modelId": "256734217",
    "userPreferredLocale": "en-US",
}

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

  with sync_playwright() as p:
    # Buka browser chromium di background (headless=True)
    # Ubah headless=False jika Anda ingin melihat browsernya terbuka di layar
    browser = p.chromium.launch(headless=True)

    # Otomatis tangani popup login Windows NTLM
    context = browser.new_context(
        http_credentials={"username": PBI_USER, "password": PBI_PASS}
    )
    page = context.new_page()

    try:
      print("🌐 Membuka halaman Power BI report...")
      page.goto(REPORT_URL, wait_until="networkidle", timeout=60000)

      # Cek jika ada form isian login di halaman web
      time.sleep(2)
      user_input = page.locator(
          "input[type='text'], input[name*='user'], input[id*='user']"
      ).first
      if user_input.is_visible(timeout=3000):
        print("🔑 Mengisi form login web...")
        user_input.fill(PBI_USER)
        page.locator("input[type='password']").first.fill(PBI_PASS)
        page.keyboard.press("Enter")
        page.wait_for_load_state("networkidle", timeout=30000)

      print("⏳ Mengambil data kueri dari sesi browser...")

      # Eksekusi kueri langsung di dalam sesi browser yang sudah berhasil login
      js_code = """
            async (payload) => {
                const res = await fetch("https://report.jezpro.id/powerbi/api/explore/reports/f8f93cc4-2ec6-4535-a708-94fd3cf99f22/querydata", {
                    method: "POST",
                    credentials: "include",
                    headers: {
                        "Content-Type": "application/json;charset=UTF-8",
                        "Accept": "application/json, text/plain, */*",
                        "X-PowerBI-ResourceKey": "any"
                    },
                    body: JSON.stringify(payload)
                });
                return await res.json();
            }
            """
      raw_json = page.evaluate(js_code, PAYLOAD_QUERY)

      # Tutup browser
      browser.close()

      # Parsing format DSR Power BI
      dm0 = raw_json["results"][0]["result"]["data"]["dsr"]["DS"][0]["PH"][0][
          "DM0"
      ]
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
      print(f"❌ Terjadi kesalahan saat scraping: {e}")
      browser.close()
      return

  if df.empty:
    print("⚠️ Data kosong.")
    return

  # ==================== FILTER DATA ==================== #
  # 1. Warehouse: HANYA SURABAYA
  df = df[df["warehouse"].fillna("").str.strip().str.upper() == "SURABAYA"]

  # 2. Status: SELAIN DONE & CANCEL
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

  # 3. Tanggal: Mulai awal bulan ini ke depan
  first_day_of_month = now_wib.replace(
      day=1, hour=0, minute=0, second=0, microsecond=0
  )
  df["dt_temp"] = pd.to_datetime(
      df["order_date_created"], errors="coerce"
  ).dt.tz_localize("Asia/Jakarta", ambiguous="NaT")
  df = df[df["dt_temp"].isna() | (df["dt_temp"] >= first_day_of_month)]
  df = df.drop(columns=["dt_temp"])

  print(f"📊 Berhasil memfilter {len(df)} pesanan Surabaya aktif.")

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
      print(f"❌ Gagal menyimpan ke Supabase: {e}")


# ==================== RUNNER & SCHEDULER ==================== #
if __name__ == "__main__":
  # Jalankan 1x saat pertama kali script dijalankan
  run_scraper()

  # Atur jadwal otomatis setiap 14:00 & 21:00 WIB
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