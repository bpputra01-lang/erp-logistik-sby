import os
import io
import re
import json
import time
import threading
import requests
import pandas as pd
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup

# ==============================================================================
# 🔑 KREDENSIAL & KONFIGURASI PUSAT (SUDAH TERPASANG LENGKAP)
# ==============================================================================
SUPABASE_URL = "https://fanzsmghhbefhhaicrok.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZhbnpzbWdoaGJlZmhoYWljcm9rIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODgxNTQzNDgsImV4cCI6MjEwMzczMDM0OH0.brCSOO9nHAUK8CxDWPperpJ--_NA_nwy5cO9OqGv3I0"

JEZPRO_EMAIL = "fajarbintang786@jez.co.id"
JEZPRO_PASSWORD = "131199"

# 🌟 MASUKKAN LINK GOOGLE SPREADSHEET MARKOM ANDA DI BAWAH INI:
SPREADSHEET_URL = os.environ.get("SPREADSHEET_URL", "")

STORE_ID_SURABAYA = 3
BRANCH_SURABAYA = "JEZ SURABAYA"
WIB = timezone(timedelta(hours=7))

BRANCH_MAP = {
    "JEZ SURABAYA": {"st_id": 3, "db_id": "SURABAYA_LATEST"},
    "JEZ KEDIRI": {"st_id": 5, "db_id": "KEDIRI_LATEST"},
    "JEZ MALANG": {"st_id": 2, "db_id": "MALANG_LATEST"},
    "JEZ JEMBER": {"st_id": 40, "db_id": "JEMBER_LATEST"},
    "JEZ SIDOARJO": {"st_id": 8, "db_id": "SIDOARJO_LATEST"},
    "JEZ SEMARANG": {"st_id": 53, "db_id": "SEMARANG_LATEST"},
    "HUB JAKARTA": {"st_id": 55, "db_id": "JAKARTA_LATEST"},
    "ONLINE HUB SURABAYA": {"st_id": 30, "db_id": "ONL_SBY_LATEST"},
    "ONLINE HUB MALANG": {"st_id": 20, "db_id": "ONL_MLG_LATEST"},
}

HEADERS_SB = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates"
}

# ==============================================================================
# HELPER PEMBERSIH & PARSER DATA UNIVERSAL
# ==============================================================================
def strip_html(val):
    if not val: return ""
    s = str(val)
    if "<" in s:
        s = re.sub(r'<[^>]+>', '', s)
    return s.strip()

def clean_bin(val):
    txt = strip_html(val)
    return txt.replace('[', '').replace(']', '').strip().upper()

def safe_int(val, default=0):
    if not val: return default
    s = strip_html(str(val)).replace("Rp", "").strip()
    digits = re.findall(r'-?\d+', s)
    return int(digits[0]) if digits else default

def safe_int_val(val, default=0):
    return safe_int(val, default)

def clean_sku_key(sku):
    if not sku: return ""
    s = str(sku).strip().upper()
    if s.endswith('.0'): s = s[:-2]
    return s if s not in ["-", "NAN", "NONE", "NULL", ""] else ""

def clean_article_name(raw_text):
    if not raw_text: return "-"
    t = strip_html(raw_text)
    t = re.sub(r'\b(WAITING OFFLINE|WAITING|REFUND|JEZ SURABAYA|Jml\s*:\s*\d+)\b', '', t, flags=re.IGNORECASE)
    return " ".join(t.split()).strip() or "-"

def clean_stock_tracking_article(raw_html):
    if not raw_html: return {"article": "-", "brand": "-"}
    s = strip_html(str(raw_html)).strip()
    m_brand = re.search(r'\[(.*?)\]', s)
    brand_val = m_brand.group(1).strip() if m_brand else "-"
    clean_name = re.sub(r'^\[.*?\]\s*', '', s).split('|')[0].strip()
    return {"article": clean_name if clean_name else s, "brand": brand_val}

def parse_wib_datetime(dt_str):
    if not dt_str: return None
    clean_str = strip_html(dt_str).strip()
    for fmt in ("%d/%m/%Y %H:%M:%S", "%d-%m-%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(clean_str[:19], fmt).replace(tzinfo=WIB)
        except Exception:
            pass
    try:
        return datetime.fromisoformat(clean_str.replace('Z', '+00:00')).astimezone(WIB)
    except Exception:
        return None

def parse_to_iso_timestamp(dt_raw):
    if not dt_raw:
        return datetime.now(WIB).isoformat()
    s = strip_html(str(dt_raw)).strip().replace('–', '-').replace('—', '-').replace('/', '-')
    for fmt in ("%Y-%m-%d %H:%M:%S", "%d-%m-%Y %H:%M:%S", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(s[:19].strip(), fmt).replace(tzinfo=WIB).isoformat()
        except Exception:
            pass
    return datetime.now(WIB).isoformat()

def get_next_supabase_id():
    try:
        url = f"{SUPABASE_URL}/rest/v1/jezpro_instock_daily?select=id&order=id.desc&limit=1"
        res = requests.get(url, headers=HEADERS_SB, timeout=10)
        if res.status_code == 200 and res.json():
            max_id = res.json()[0].get("id")
            if max_id is not None:
                return int(max_id) + 1
    except Exception:
        pass
    return int(time.time() * 1000) % 2147483640

# ==============================================================================
# AUTENTIKASI KE JEZPRO
# ==============================================================================
def create_jezpro_session():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
    })
    print(f"🔐 [{datetime.now(WIB).strftime('%H:%M:%S')}] Login ke akun Jezpro ({JEZPRO_EMAIL})...")
    res = session.get("https://jezpro.id/", timeout=20)
    soup = BeautifulSoup(res.text, "html.parser")
    token_tag = soup.find("input", {"name": "_token"})
    if not token_tag:
        raise Exception("Gagal mendapatkan CSRF Token Jezpro!")

    session.post("https://jezpro.id/user_login", data={
        "_token": token_tag["value"],
        "u_email": JEZPRO_EMAIL,
        "password": JEZPRO_PASSWORD
    }, timeout=20)
    print("✅ Berhasil login Jezpro!")

    session.get("https://jezpro.id/helper_backup", timeout=15)
    session.get("https://jezpro.id/transfer_stok", timeout=15)
    session.get("https://jezpro.id/mass_adjustment", timeout=15)
    session.get("https://jezpro.id/adjustment", timeout=15)
    session.get("https://jezpro.id/stock_tracking", timeout=15)
    return session


# ==============================================================================
# MODUL 1: INSTOCK DAILY SURABAYA (JALUR KHUSUS CEPAT - TIAP 45 DETIK)
# ==============================================================================
def run_module_instock_daily(session):
    today_str = datetime.now(WIB).strftime("%Y-%m-%d")
    now_wib = datetime.now(WIB)

    url_stk = "https://jezpro.id/stock_tracking_datatables"
    params = {
        "draw": "1", "start": "0", "length": "1000",
        "st_id": str(STORE_ID_SURABAYA), "date": today_str,
        "_": int(time.time() * 1000)
    }
    headers_req = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://jezpro.id/stock_tracking"
    }

    try:
        res = session.get(url_stk, params=params, headers=headers_req, timeout=25)
        if res.status_code != 200: return
        raw_data = res.json().get("data", [])
    except Exception:
        return

    tracking_today = []
    for item in raw_data:
        sku = ""
        for k in ["ps_barcode", "barcode", "sku", "2"]:
            if isinstance(item, dict) and item.get(k):
                sku = clean_sku_key(item[k]); break
            elif isinstance(item, list) and len(item) > 2:
                sku = clean_sku_key(item[2]); break
        if not sku: continue

        raw_time = ""
        for k in ["datetime", "plst_created", "1"]:
            if isinstance(item, dict) and item.get(k):
                raw_time = strip_html(item[k]); break
            elif isinstance(item, list) and len(item) > 1:
                raw_time = strip_html(item[1]); break

        dt_wib = parse_wib_datetime(raw_time)

        loc_bin = ""
        for k in ["product_location", "pl_code", "7"]:
            if isinstance(item, dict) and item.get(k):
                loc_bin = clean_bin(item[k]); break
            elif isinstance(item, list) and len(item) > 7:
                loc_bin = clean_bin(item[7]); break

        full_row_text = " ".join([str(v) for v in (item.values() if isinstance(item, dict) else item) if v]).upper()
        is_instock = ("INSTOCK" in full_row_text) and ("WAITING" in full_row_text)
        is_waiting = ("WAITING" in full_row_text) and not is_instock

        art_name = ""
        for k in ["article", "p_name", "3"]:
            if isinstance(item, dict) and item.get(k):
                art_name = clean_article_name(item[k])
                if art_name != "-": break

        qty_val = 1
        for k in ["qty", "6"]:
            if isinstance(item, dict) and item.get(k):
                qty_val = safe_int_val(item[k], 1); break

        tracking_today.append({
            "sku": sku, "article": art_name, "qty": qty_val,
            "location": loc_bin if loc_bin else "STAGING INBOUND",
            "is_instock": is_instock, "is_waiting": is_waiting,
            "raw_time": raw_time, "dt_wib": dt_wib
        })

    # Cek Database Supabase
    sb_url = f"{SUPABASE_URL}/rest/v1/jezpro_instock_daily?select=*&sync_date=eq.{today_str}"
    try:
        res_sb = requests.get(sb_url, headers=HEADERS_SB, timeout=15)
        sb_records = res_sb.json() if res_sb.status_code == 200 else []
    except Exception:
        sb_records = []

    waiting_by_sku = {}
    for r in sb_records:
        if r.get("status") == "WAITING OFFLINE":
            s = clean_sku_key(r.get("barcode_sku"))
            if s: waiting_by_sku.setdefault(s, []).append(r)

    need_setup_in_sb = [x for x in sb_records if x.get("status") == "NEED_SETUP"]
    done_setup_in_sb = [x for x in sb_records if x.get("status") == "DONE_SETUP"]
    used_mutasi_ids = set(str(d.get("matched_mutasi_id")) for d in done_setup_in_sb if d.get("matched_mutasi_id"))
    all_sb_skus = set(clean_sku_key(x.get("barcode_sku")) for x in sb_records if clean_sku_key(x.get("barcode_sku")))

    current_auto_id = get_next_supabase_id()
    new_inserts = []

    for tr in tracking_today:
        sku = tr["sku"]
        jam_transaksi_iso = (tr["dt_wib"] or now_wib).isoformat()
        lokasi_bin = tr["location"]

        if tr["is_instock"]:
            if sku in waiting_by_sku and len(waiting_by_sku[sku]) > 0:
                row_target = waiting_by_sku[sku].pop(0)
                t_id = row_target.get("id")
                patch_url = f"{SUPABASE_URL}/rest/v1/jezpro_instock_daily?id=eq.{t_id}" if t_id else f"{SUPABASE_URL}/rest/v1/jezpro_instock_daily?barcode_sku=eq.{sku}&sync_date=eq.{today_str}&status=eq.WAITING%20OFFLINE"
                patch_payload = {
                    "status": "NEED_SETUP",
                    "disappeared_at": jam_transaksi_iso,
                    "bin_code": lokasi_bin
                }
                res_patch = requests.patch(patch_url, headers=HEADERS_SB, json=patch_payload)
                if res_patch.status_code in [200, 204]:
                    row_target["status"] = "NEED_SETUP"
                    row_target["disappeared_at"] = jam_transaksi_iso
                    row_target["bin_code"] = lokasi_bin
                    need_setup_in_sb.append(row_target)
                    print(f"   🚀 [INSTOCK] SKU {sku} (Jam {tr['raw_time']}) di BIN [{lokasi_bin}] ➔ Masuk LIST SET UP!")
            elif sku not in all_sb_skus:
                new_inserts.append({
                    "id": current_auto_id, "store_id": STORE_ID_SURABAYA, "store_name": BRANCH_SURABAYA,
                    "barcode_sku": sku, "article_name": tr["article"], "bin_code": lokasi_bin,
                    "qty": tr["qty"], "status": "NEED_SETUP", "invoice": "-", "sync_date": today_str,
                    "created_at": jam_transaksi_iso, "disappeared_at": jam_transaksi_iso,
                    "matched_mutasi_id": None, "setup_done_at": None
                })
                current_auto_id += 1
                all_sb_skus.add(sku)
                print(f"   📥 [INSTOCK BARU] SKU {sku} (Jam {tr['raw_time']}) ➔ Masuk LIST SET UP!")

    for tr in tracking_today:
        sku = tr["sku"]
        jam_transaksi_iso = (tr["dt_wib"] or now_wib).isoformat()
        if tr["is_waiting"] and sku not in all_sb_skus:
            new_inserts.append({
                "id": current_auto_id, "store_id": STORE_ID_SURABAYA, "store_name": BRANCH_SURABAYA,
                "barcode_sku": sku, "article_name": tr["article"], "bin_code": tr["location"],
                "qty": tr["qty"], "status": "WAITING OFFLINE", "invoice": "-", "sync_date": today_str,
                "created_at": jam_transaksi_iso, "disappeared_at": None, "matched_mutasi_id": None, "setup_done_at": None
            })
            current_auto_id += 1
            all_sb_skus.add(sku)

    if new_inserts:
        res_ins = requests.post(f"{SUPABASE_URL}/rest/v1/jezpro_instock_daily", headers=HEADERS_SB, json=new_inserts)
        if res_ins.status_code in [200, 201]:
            for ins in new_inserts:
                if ins["status"] == "NEED_SETUP": need_setup_in_sb.append(ins)

    # Verifikasi Selesai Mutasi ke GL1-INSTOCK
    if need_setup_in_sb:
        url_bin = "https://jezpro.id/bin_history_datatables"
        params_bin = {"draw": "1", "start": "0", "length": "1000", "st_id": str(STORE_ID_SURABAYA), "date": today_str, "_": int(time.time() * 1000)}
        try:
            r_bin = session.get(url_bin, params=params_bin, headers={"Accept": "application/json", "Referer": "https://jezpro.id/setup_lokasi_stok_v2"}, timeout=20)
            mutasi_today = r_bin.json().get("data", []) if r_bin.status_code == 200 else []
        except Exception:
            mutasi_today = []

        for target in need_setup_in_sb:
            t_sku = clean_sku_key(target.get("barcode_sku"))
            t_qty = safe_int_val(target.get("qty"), 1)
            matched_m = None

            for m in mutasi_today:
                m_id = str(strip_html(m.get("pmt_id") or m.get("DT_RowIndex") or ""))
                if m_id in used_mutasi_ids: continue
                m_sku = clean_sku_key(m.get("ps_barcode") or m.get("barcode"))
                bin_tgt = clean_bin(m.get("end_bin"))
                q_mts = safe_int_val(m.get("pmt_qty"), 0)

                if m_sku == t_sku and ("GL1-INSTOCK" in bin_tgt or "INSTOCK" in bin_tgt) and q_mts >= t_qty:
                    matched_m = m; break

            if matched_m:
                used_mutasi_ids.add(str(matched_m.get("pmt_id") or ""))
                t_id = target.get("id")
                patch_url = f"{SUPABASE_URL}/rest/v1/jezpro_instock_daily?id=eq.{t_id}" if t_id else f"{SUPABASE_URL}/rest/v1/jezpro_instock_daily?barcode_sku=eq.{t_sku}&sync_date=eq.{today_str}&status=eq.NEED_SETUP"
                requests.patch(patch_url, headers=HEADERS_SB, json={
                    "status": "DONE_SETUP",
                    "matched_mutasi_id": str(matched_m.get("pmt_id") or "-"),
                    "setup_done_at": strip_html(matched_m.get("pm_created_at") or "")
                })
                print(f"   🎉 [DONE SETUP] SKU {t_sku} ➔ Selesai Mutasi ke GL1-INSTOCK!")


# ==============================================================================
# MODUL 2: WAREHOUSE ACTIVITY MONITOR (STAGING, TRANSFER, MADJ, SINGLE ADJ)
# ==============================================================================
def run_module_warehouse_monitor(session):
    print(f"\n📊 [{datetime.now(WIB).strftime('%H:%M:%S')}] Memulai Sinkronisasi Warehouse Activity Monitor (All Area)...")
    headers_req = {"Accept": "application/json, text/javascript, */*; q=0.01", "X-Requested-With": "XMLHttpRequest"}
    now_wib = datetime.now(WIB).replace(tzinfo=None)

    # 1. Staging / Waiting / Refund dari Stock Tracking (All Cabang)
    url_stg = "https://jezpro.id/stock_tracking_datatables"
    date_range = "2026-01-01|2030-12-31"
    query_targets = [
        {"status": "REFUND", "status_search": ""},
        {"status": "", "status_search": "REFUND"},
        {"status": "WAITING OFFLINE", "status_search": ""},
        {"status": "WAITING CHECKOUT", "status_search": ""},
        {"status": "WAITING NAMESET", "status_search": ""},
        {"status": "WAITING ONLINE", "status_search": ""},
        {"status": "DONE ONLINE", "status_search": ""},
        {"status": "", "status_search": "DONE ONLINE"},
        {"status": "WAITING", "status_search": ""}
    ]

    all_staging_records = []
    seen_stg_ids = set()

    for branch_name, b_info in BRANCH_MAP.items():
        st_id = b_info["st_id"]
        for q in query_targets:
            params = {
                "draw": "1", "columns[0][data]": "DT_RowIndex", "columns[0][name]": "plst_id",
                "columns[1][data]": "datetime", "columns[1][name]": "plst_created", "columns[1][orderable]": "true",
                "columns[2][data]": "ps_barcode", "columns[2][name]": "ps_barcode",
                "columns[3][data]": "article", "columns[3][name]": "p_name",
                "columns[6][data]": "qty", "columns[6][name]": "p_name",
                "columns[7][data]": "product_location", "columns[7][name]": "pl_code",
                "columns[8][data]": "status", "columns[8][name]": "plst_status", "columns[8][search][value]": q["status_search"],
                "order[0][column]": "1", "order[0][dir]": "desc",
                "start": "0", "length": "500", "status": q["status"], "st_id": str(st_id), "date": date_range
            }
            try:
                res = session.get(url_stg, params=params, headers=headers_req, timeout=20)
                if res.status_code != 200: continue
                raw_list = res.json().get("data", [])
            except Exception:
                raw_list = []

            for item in raw_list:
                status_raw = strip_html(item.get("status") or item.get("plst_status") or "").upper()
                loc_raw = strip_html(item.get("product_location") or item.get("pl_code") or "").upper()
                is_refund = "REFUND" in status_raw
                is_done_online = "DONE ONLINE" in status_raw or ("DONE" in status_raw and "ONLINE" in status_raw)
                is_waiting = any(k in status_raw for k in ["WAITING", "CHECKOUT", "NAMESET"]) or "WAITING" in loc_raw
                if not (is_refund or is_waiting or is_done_online): continue

                dt_raw = strip_html(item.get("datetime") or item.get("plst_created") or "")
                raw_id = item.get("plst_id") or item.get("id")
                p_id = safe_int_val(raw_id)
                if not p_id:
                    bar = strip_html(item.get("ps_barcode") or "")
                    p_id = abs(hash(f"{st_id}_{bar}_{dt_raw}")) % 2147483647
                if p_id in seen_stg_ids: continue
                seen_stg_ids.add(p_id)

                kategori_label = "REFUND" if is_refund else ("DONE ONLINE" if is_done_online else ("WAITING NAMESET" if "NAMESET" in status_raw else ("WAITING CHECKOUT" if "CHECKOUT" in status_raw else ("WAITING ONLINE" if "ONLINE" in status_raw else "WAITING OFFLINE"))))
                art_info = clean_stock_tracking_article(item.get("article") or item.get("p_name"))

                all_staging_records.append({
                    "plst_id": int(p_id), "pls_id": int(item.get("pls_id") or p_id),
                    "kategori": kategori_label, "waiting_status": status_raw or kategori_label,
                    "brand": art_info["brand"], "article_name": art_info["article"],
                    "qty": safe_int_val(item.get("qty"), 1), "bin_target": loc_raw or "[STAGING INBOUND]",
                    "pic_name": strip_html(item.get("u_name") or item.get("user_name") or "Petugas"),
                    "scanned_at": parse_to_iso_timestamp(dt_raw), "store_id": int(st_id),
                    "synced_at": datetime.now(WIB).isoformat()
                })
            time.sleep(0.04)

    # 2. Transfer Stok (All Store History)
    url_tf = "https://jezpro.id/transfer_history_datatables"
    open_tf_headers, open_tf_items = [], []
    try:
        p_tf = {"draw": "1", "start": "0", "length": "500", "order[0][column]": "0", "order[0][dir]": "desc", "status": ""}
        r_tf = session.get(url_tf, params=p_tf, headers=headers_req, timeout=30)
        raw_tf = r_tf.json().get("data", []) if r_tf.status_code == 200 else []
        for row in raw_tf:
            st_txt = strip_html(row.get("stf_status") or "").upper()
            if st_txt not in ["DRAFT", "IN PROGRESS"]: continue
            m_code = re.search(r'TF\d+', str(row.get("stf_code") or ""))
            tf_code = m_code.group(0) if m_code else strip_html(row.get("stf_code") or "")
            if not tf_code: continue

            tgl_str = strip_html(row.get("stf_created") or "")
            aging_jam = 0.0
            if tgl_str:
                for fmt in ("%Y-%m-%d %H:%M:%S", "%d-%m-%Y %H:%M:%S", "%d/%m/%Y %H:%M:%S"):
                    try:
                        aging_jam = max(0.0, round((now_wib - datetime.strptime(tgl_str[:19].strip(), fmt)).total_seconds() / 3600.0, 1))
                        break
                    except Exception: pass

            open_tf_headers.append({
                "stf_code": tf_code, "u_name": strip_html(row.get("u_name") or "-"),
                "stf_notes": strip_html(row.get("stf_notes") or "-"), "qty_send": safe_int_val(row.get("qty_send")),
                "qty_receive": safe_int_val(row.get("qty_receive")), "start_store": strip_html(row.get("start_store") or "-"),
                "end_store": strip_html(row.get("end_store") or "-"), "u_name_receive": strip_html(row.get("u_name_receive") or "-"),
                "stf_created": tgl_str or now_wib.isoformat(), "stf_status": st_txt,
                "aging_hours": float(aging_jam), "synced_at": now_wib.isoformat()
            })

            # Tarik detail item untuk transfer ini
            p_det = {"draw": "1", "start": "0", "length": "250", "stf_code": tf_code}
            r_det = session.get("https://jezpro.id/in_transfer_bin_datatables", params=p_det, headers=headers_req, timeout=20)
            items_chunk = r_det.json().get("data", []) if r_det.status_code == 200 else []
            if not items_chunk:
                r_det2 = session.get("https://jezpro.id/transfer_bin_datatables", params=p_det, headers=headers_req, timeout=20)
                items_chunk = r_det2.json().get("data", []) if r_det2.status_code == 200 else []

            for it in items_chunk:
                open_tf_items.append({
                    "stf_code": tf_code, "article_name": strip_html(it.get("article", "-")),
                    "bin_asal": strip_html(it.get("pl_code") or it.get("bin") or "-"),
                    "qty_tf": safe_int_val(it.get("stfd_qty") or it.get("qty"), 1),
                    "qty_in_bin": safe_int_val(it.get("pls_qty") or it.get("qty_bin"), 0),
                    "start_store": strip_html(it.get("st_start") or "-"), "end_store": strip_html(it.get("st_end") or "-"),
                    "status": st_txt, "synced_at": now_wib.isoformat()
                })
    except Exception as e:
        print(f"   ⚠️ Transfer error: {e}")

    # 3. Multiple Adjustment (Khusus Menggantung)
    url_ma = "https://jezpro.id/mass_adjustment_datatables"
    open_ma_headers, open_ma_items = [], []
    try:
        p_ma = {"draw": "1", "start": "0", "length": "500", "order[0][column]": "0", "order[0][dir]": "desc", "st_id": ""}
        r_ma = session.get(url_ma, params=p_ma, headers=headers_req, timeout=30)
        raw_ma = r_ma.json().get("data", []) if r_ma.status_code == 200 else []
        for row in raw_ma:
            st_raw = strip_html(row.get("ma_status") or "").upper()
            app_raw = strip_html(row.get("approve") or "")
            if not (any(k in st_raw for k in ["MENUNGGU", "PENDING", "DRAFT", "PROGRESS"]) or "MENUNGGU" in app_raw.upper()):
                continue

            m_code = re.search(r'MADJ\d+', str(row.get("ma_code_show") or row.get("ma_code") or ""))
            ma_code = m_code.group(0) if m_code else strip_html(row.get("ma_code") or "")
            ma_id_val = safe_int_val(row.get("id")) or (abs(hash(ma_code)) % (10**10) if ma_code else 0)

            tgl_str = strip_html(row.get("created_at") or "")
            aging_jam = 0.0
            if tgl_str:
                for fmt in ("%d/%m/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
                    try:
                        aging_jam = max(0.0, round((now_wib - datetime.strptime(tgl_str[:19].strip(), fmt)).total_seconds() / 3600.0, 1))
                        break
                    except Exception: pass

            open_ma_headers.append({
                "ma_id": ma_id_val, "ma_code": ma_code, "store_name": strip_html(row.get("st_name") or "-"),
                "u_name": strip_html(row.get("u_name") or "-"), "approve": app_raw or "-",
                "executor": strip_html(row.get("executor") or "-"), "note": strip_html(row.get("note") or "-"),
                "created_at": tgl_str or now_wib.isoformat(), "ma_status": st_raw or "MENGGANTUNG",
                "status_category": "MENGGANTUNG", "aging_hours": float(aging_jam), "synced_at": now_wib.isoformat()
            })

            # Rincian item MADJ
            p_mdet = {"draw": "1", "start": "0", "length": "250", "ma_id": str(ma_id_val)}
            r_mdet = session.get("https://jezpro.id/mass_adjustment_detail_datatables", params=p_mdet, headers=headers_req, timeout=20)
            items_ma = r_mdet.json().get("data", []) if r_mdet.status_code == 200 else []
            for it in items_ma:
                open_ma_items.append({
                    "ma_id": ma_id_val, "bin_code": strip_html(it.get("pl_code") or "-"),
                    "brand": strip_html(it.get("br_name") or "-"), "barcode_sku": strip_html(it.get("ps_barcode") or "-"),
                    "article_name": strip_html(it.get("p_name") or "-"), "color": strip_html(it.get("p_color") or "-"),
                    "size_variant": strip_html(it.get("sz_name") or "-"), "sub_category": strip_html(it.get("psc_name") or "-"),
                    "cogs_price": safe_int_val(it.get("purchase")), "qty_system": safe_int_val(it.get("qty_export")),
                    "qty_so": safe_int_val(it.get("qty_so")), "diff_qty": safe_int_val(it.get("mad_diff")),
                    "adj_type": strip_html(it.get("mad_type") or "-"), "synced_at": now_wib.isoformat()
                })
    except Exception as e:
        print(f"   ⚠️ MADJ error: {e}")

    # 4. Single Adjustment (All Store Need Approval)
    url_single = "https://jezpro.id/adjustment_history_datatables"
    clean_single_records = []
    for branch_name, b_info in BRANCH_MAP.items():
        st_id = b_info["st_id"]
        try:
            p_sa = {"draw": "1", "start": "0", "length": "250", "st_id": str(st_id), "adjustment_date": f"2026-01-01|{now_wib.strftime('%Y-%m-%d')}", "status": ""}
            r_sa = session.get(url_single, params=p_sa, headers=headers_req, timeout=20)
            raw_sa = r_sa.json().get("data", []) if r_sa.status_code == 200 else []
            for idx, row in enumerate(raw_sa):
                st_raw = strip_html(row.get("ba_status") or "").upper()
                app_raw = strip_html(row.get("ba_approve") or "").upper()
                if any(x in st_raw for x in ["DONE", "SELESAI", "CANCEL", "BATAL"]): continue
                if not (any(k in st_raw for k in ["MENUNGGU", "PENDING", "NEED", "WAITING", "PROGRESS", "DRAFT"]) or app_raw in ["-", "", "NONE"] or "MENUNGGU" in app_raw): continue

                ba_id_val = safe_int_val(row.get("ba_id") or row.get("id")) or (abs(hash(f"{st_id}_{idx}")) % (10**10))
                clean_single_records.append({
                    "id": ba_id_val, "ba_code": strip_html(row.get("ba_code") or "-"),
                    "store_name": strip_html(row.get("st_name") or branch_name),
                    "bin_code": strip_html(row.get("pl_code") or "-"), "creator": strip_html(row.get("u_name") or "-"),
                    "approval": strip_html(row.get("ba_approve") or "-"), "executor": strip_html(row.get("ba_executor") or "-"),
                    "brand": strip_html(row.get("br_name") or "-"), "article_name": strip_html(row.get("p_name") or "-"),
                    "barcode_sku": strip_html(row.get("ps_barcode") or "-"), "color": strip_html(row.get("p_color") or "-"),
                    "size_variant": strip_html(row.get("sz_name") or "-"), "cogs": safe_int_val(row.get("cogs")),
                    "old_qty": safe_int_val(row.get("ba_old_qty")), "new_qty": safe_int_val(row.get("ba_new_qty")),
                    "adjust_qty": safe_int_val(row.get("adjust")), "note": strip_html(row.get("ba_note") or "-"),
                    "status": strip_html(row.get("ba_status") or "Menunggu"), "updated_at": strip_html(row.get("ba_updated_at") or ""),
                    "synced_at": now_wib.isoformat()
                })
        except Exception: pass

    # Kirim Bersih ke Supabase
    try:
        requests.delete(f"{SUPABASE_URL}/rest/v1/jezpro_waiting_staging?plst_id=gt.0", headers=HEADERS_SB)
        if all_staging_records:
            for i in range(0, len(all_staging_records), 100):
                requests.post(f"{SUPABASE_URL}/rest/v1/jezpro_waiting_staging", json=all_staging_records[i:i+100], headers=HEADERS_SB)

        requests.delete(f"{SUPABASE_URL}/rest/v1/jezpro_transfer_headers?stf_code=neq.", headers=HEADERS_SB)
        if open_tf_headers:
            for i in range(0, len(open_tf_headers), 100):
                requests.post(f"{SUPABASE_URL}/rest/v1/jezpro_transfer_headers", json=open_tf_headers[i:i+100], headers=HEADERS_SB)

        requests.delete(f"{SUPABASE_URL}/rest/v1/jezpro_transfer_items?id=gt.0", headers=HEADERS_SB)
        if open_tf_items:
            for i in range(0, len(open_tf_items), 200):
                requests.post(f"{SUPABASE_URL}/rest/v1/jezpro_transfer_items", json=open_tf_items[i:i+200], headers=HEADERS_SB)

        requests.delete(f"{SUPABASE_URL}/rest/v1/jezpro_adjustment_headers?ma_id=gt.0", headers=HEADERS_SB)
        if open_ma_headers:
            for i in range(0, len(open_ma_headers), 100):
                requests.post(f"{SUPABASE_URL}/rest/v1/jezpro_adjustment_headers", json=open_ma_headers[i:i+100], headers=HEADERS_SB)

        requests.delete(f"{SUPABASE_URL}/rest/v1/jezpro_adjustment_items?id=gt.0", headers=HEADERS_SB)
        if open_ma_items:
            for i in range(0, len(open_ma_items), 200):
                requests.post(f"{SUPABASE_URL}/rest/v1/jezpro_adjustment_items", json=open_ma_items[i:i+200], headers=HEADERS_SB)

        requests.delete(f"{SUPABASE_URL}/rest/v1/jezpro_single_adjustments?id=gt.0", headers=HEADERS_SB)
        if clean_single_records:
            for i in range(0, len(clean_single_records), 100):
                requests.post(f"{SUPABASE_URL}/rest/v1/jezpro_single_adjustments", json=clean_single_records[i:i+100], headers=HEADERS_SB)

        print(f"   ✅ Monitor Supabase Updated! (Staging: {len(all_staging_records)}, TF: {len(open_tf_headers)}, MADJ: {len(open_ma_headers)}, SA: {len(clean_single_records)})")
    except Exception as e:
        print(f"   ❌ Gagal update Supabase monitor: {e}")


# ==============================================================================
# MODUL 3: MEMO MARKOM SPREADSHEET (LENGKAP ANTI-DUPLIKAT - TIAP 10 MENIT)
# ==============================================================================
def run_module_memo_markom():
    if not SPREADSHEET_URL or "http" not in SPREADSHEET_URL:
        return
    print(f"\n📑 [{datetime.now(WIB).strftime('%H:%M:%S')}] Memeriksa Spreadsheet Permintaan Markom...")
    try:
        # 1. Ambil Cache Harga Beli dari Supabase
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

        # 2. Ambil Memo Eksisting di Supabase
        existing_memos = {}
        res_memo = requests.get(f"{SUPABASE_URL}/rest/v1/memo_pengajuan?select=*", headers=HEADERS_SB, timeout=25)
        if res_memo.status_code == 200:
            for m in res_memo.json():
                existing_memos[(str(m.get("tanggal", ""))[:10], str(m.get("tujuan", "")).strip().upper())] = m

        # 3. Unduh & Parse Spreadsheet
        dl_url = SPREADSHEET_URL
        m_id = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', SPREADSHEET_URL)
        if m_id: dl_url = f"https://docs.google.com/spreadsheets/d/{m_id.group(1)}/export?format=xlsx"

        xl = pd.ExcelFile(dl_url)
        tgt_sheet = next((s for s in xl.sheet_names if "MARKOM" in s.upper()), xl.sheet_names[0])
        df = pd.read_excel(xl, sheet_name=tgt_sheet)
        if df.empty or df.shape[1] < 4: return

        col_pic, col_note, col_sku, col_qty = df.columns[0], df.columns[1], df.columns[2], df.columns[3]
        col_tgl = df.columns[12] if df.shape[1] > 12 else df.columns[-2]
        col_bin = df.columns[14] if df.shape[1] > 14 else df.columns[-1]

        mask = df[col_note].fillna("").astype(str).str.contains("EVENT|HADIAH|GIFT", case=False, na=False)
        df_filtered = df[mask].copy()
        if df_filtered.empty: return

        grouped_events = {}
        for row_idx, (_, r) in enumerate(df_filtered.iterrows(), start=1):
            pic_val = str(r[col_pic]).strip() if pd.notna(r[col_pic]) else "MARKOM"
            note_val = str(r[col_note]).strip().upper() if pd.notna(r[col_note]) else "EVENT"
            raw_tgl = str(r[col_tgl]).strip() if pd.notna(r[col_tgl]) else ""
            tgl_val = raw_tgl[:10] if len(raw_tgl) >= 10 else datetime.now().strftime("%Y-%m-%d")
            sku_val = str(r[col_sku]).split('.')[0].strip().upper() if pd.notna(r[col_sku]) else ""
            if not sku_val or sku_val in ["-", "NAN", "NONE"]: continue

            q_val = safe_int(r[col_qty], 1)
            b_val = str(r[col_bin]).strip() if pd.notna(r[col_bin]) else "GL1-DC-OUT"
            info = lookup_cogs.get(sku_val, {})
            cogs_val = info.get("cogs", 0)

            grouped_events.setdefault((tgl_val, note_val), {"pic": pic_val, "items": []})["items"].append({
                "id": f"REQ-{sku_val}-{row_idx}", "tanggal": tgl_val, "pic": pic_val,
                "keterangan": note_val, "bin": b_val, "sku": sku_val,
                "item_name": info.get("name") or sku_val, "cogs": cogs_val, "qty": q_val,
                "subtotal": cogs_val * q_val
            })

        new_inserts = []
        for (tgl_doc, event_name), grp_data in grouped_events.items():
            items_list = grp_data["items"]
            pic_doc = grp_data["pic"]
            tot_nom = sum(x["subtotal"] for x in items_list)
            key_m = (tgl_doc, event_name)

            if key_m in existing_memos:
                exist = existing_memos[key_m]
                if str(exist.get("status_adj", "PENDING")).upper() == "DONE": continue
                url_upd = f"{SUPABASE_URL}/rest/v1/memo_pengajuan?id=eq.{exist['id']}"
                requests.patch(url_upd, headers=HEADERS_SB, json={"nominal": tot_nom, "diajukan_oleh": pic_doc, "items": items_list})
            else:
                memo_id = f"MEMO/ZKN/{tgl_doc.replace('-', '')}/{int(time.time() * 1000) % 900 + 100}"
                new_inserts.append({
                    "id": memo_id, "tanggal": tgl_doc, "divisi": "MARKOM",
                    "jenis": "Pengajuan Adjustment untuk Hadiah", "tujuan": event_name,
                    "nominal": tot_nom, "diajukan_oleh": pic_doc, "diproses_oleh": "Tim Purchasing",
                    "diperiksa_oleh": "Tim Finance", "status_adj": "PENDING", "items": items_list
                })

        if new_inserts:
            requests.post(f"{SUPABASE_URL}/rest/v1/memo_pengajuan", headers=HEADERS_SB, json=new_inserts)
            print(f"   🚀 Dibuat {len(new_inserts)} memo pengajuan baru di Supabase!")
        else:
            print("   ✅ Memo Markom sudah sinkron dan mutakhir.")
    except Exception as e:
        print(f"   ⚠️ Memo Markom error: {e}")


# ==============================================================================
# MODUL 4 & 5: EXPORT STOK ALL CABANG & BALANCING SURABAYA (TIAP 3 JAM)
# ==============================================================================
def run_module_exports_and_balancing(session):
    print(f"\n📦 [{datetime.now(WIB).strftime('%H:%M:%S')}] Memulai Ekspor Stok 9 Cabang & Balancing Surabaya...")

    # 1. Ekspor Stok Seluruh 9 Cabang Jezpro -> stock_live_cache
    for branch_name, info in BRANCH_MAP.items():
        st_id = info["st_id"]
        db_id = info["db_id"]
        try:
            print(f"   -> Ekspor Stok {branch_name} (st_id: {st_id})...")
            url_exp = f"https://jezpro.id/export_mass_adjustment_template?st_id={st_id}&psc_id=&br_id=&pl_id=&qty_filter=1"
            r_exp = session.get(url_exp, headers={"Referer": "https://jezpro.id/mass_adjustment"}, timeout=300)
            excel_bytes = None

            if "application/json" in r_exp.headers.get("Content-Type", ""):
                notif_id = r_exp.json().get("notification_id")
                check_url = f"https://jezpro.id/notifications/{notif_id}/open-export"
                final_url = ""
                for _ in range(15):
                    time.sleep(3)
                    r_chk = session.get(check_url, allow_redirects=False, timeout=60)
                    loc = r_chk.headers.get("Location", "")
                    if r_chk.status_code == 302 and ("neo.id" in loc or "http" in loc):
                        final_url = loc; break

                if final_url:
                    excel_bytes = requests.get(final_url, timeout=300).content
            else:
                excel_bytes = r_exp.content

            if excel_bytes:
                df_stk = pd.read_excel(io.BytesIO(excel_bytes))
                df_stk["STORE_NAME"] = branch_name
                payload = df_stk.fillna("").to_dict(orient="records")
                requests.post(f"{SUPABASE_URL}/rest/v1/stock_live_cache", headers=HEADERS_SB, json={
                    "id": db_id, "branch": branch_name, "updated_at": datetime.now(WIB).isoformat(),
                    "total_rows": len(payload), "stock_data": payload
                }, timeout=120)
                print(f"      ✅ Berhasil simpan {len(payload):,} baris ({branch_name})")

                # Jika Surabaya, simpan juga untuk balancing_stock_cache
                if st_id == STORE_ID_SURABAYA:
                    requests.post(f"{SUPABASE_URL}/rest/v1/balancing_stock_cache", headers=HEADERS_SB, json={
                        "id": "SURABAYA_BALANCING_STOCK", "branch": BRANCH_SURABAYA,
                        "updated_at": datetime.now(WIB).isoformat(), "total_rows": len(payload),
                        "stock_data": payload
                    }, timeout=120)
        except Exception as e:
            print(f"      ⚠️ Gagal ekspor {branch_name}: {e}")

    # 2. Tarik Riwayat Penjualan Surabaya 60 Hari (INV vs Non-INV) -> balancing_sales_cache
    try:
        now_dt = datetime.now()
        p_start = (now_dt - timedelta(days=60)).strftime('%Y-%m-%d')
        p_end = now_dt.strftime('%Y-%m-%d')
        date_param = f"{p_start}|{p_end}"

        print(f"   -> Menarik Sales 60 Hari Surabaya ({date_param})...")
        url_dt = "https://jezpro.id/stock_tracking_datatables"
        headers_dt = {"Accept": "application/json, text/javascript, */*; q=0.01", "X-Requested-With": "XMLHttpRequest"}

        sales_by_sku = {}
        start_row, total_expected = 0, 999999
        draw_count, total_sales_rows = 1, 0

        while start_row < total_expected and start_row < 20000:
            params = {
                "draw": str(draw_count), "start": str(start_row), "length": "2000",
                "status": "DONE", "st_id": str(STORE_ID_SURABAYA), "date": date_param,
                "order[0][column]": "0", "order[0][dir]": "desc"
            }
            res_s = session.get(url_dt, params=params, headers=headers_dt, timeout=60)
            if res_s.status_code != 200: break
            j_data = res_s.json()
            chunk = j_data.get("data", [])
            total_expected = j_data.get("recordsFiltered", j_data.get("recordsTotal", 0))
            if not chunk: break

            for item in chunk:
                if "DONE" not in strip_html(item.get("status") or "").upper(): continue
                sku = clean_sku_key(item.get("ps_barcode"))
                if not sku: continue
                q_val = safe_int(item.get("qty"), 1)
                inv_val = strip_html(item.get("invoice") or "").upper()
                is_onl = ("INV" not in inv_val)

                if sku not in sales_by_sku:
                    sales_by_sku[sku] = {
                        "SKU": sku, "ARTICLE": clean_article_name(item.get("article") or item.get("p_name")),
                        "SALES_OFFLINE": 0, "SALES_ONLINE": 0, "TOTAL_SALES": 0
                    }
                if is_onl: sales_by_sku[sku]["SALES_ONLINE"] += q_val
                else: sales_by_sku[sku]["SALES_OFFLINE"] += q_val
                sales_by_sku[sku]["TOTAL_SALES"] += q_val
                total_sales_rows += 1

            start_row += len(chunk)
            draw_count += 1
            time.sleep(0.02)

        summary_sales = list(sales_by_sku.values())
        requests.post(f"{SUPABASE_URL}/rest/v1/balancing_sales_cache", headers=HEADERS_SB, json={
            "id": "SURABAYA_SALES_90D", "branch": BRANCH_SURABAYA, "period_start": p_start, "period_end": p_end,
            "updated_at": datetime.now(WIB).isoformat(), "total_rows": total_sales_rows, "sales_data": summary_sales
        }, timeout=120)
        print(f"      ✅ Sales Balancing Disimpan ({len(summary_sales):,} SKU aktif terjual)")
    except Exception as e:
        print(f"      ⚠️ Gagal balancing sales: {e}")


# ==============================================================================
# THREAD KHUSUS: INSTOCK SURABAYA (TIAP 45 DETIK NONSTOP)
# ==============================================================================
def thread_instock_worker(session):
    while True:
        try:
            run_module_instock_daily(session)
        except Exception as e:
            print(f"⚠️ [Instock Loop Error]: {e}")
        time.sleep(45)


# ==============================================================================
# MAIN ORCHESTRATOR
# ==============================================================================
if __name__ == "__main__":
    print("=" * 75)
    print("🚀 MASTER LOCAL ORCHESTRATOR: JEZPRO -> SUPABASE AKTIF")
    print("=" * 75)
    print("   ✅ Modul 1: Instock Surabaya (Background Thread: Tiap 45 Detik)")
    print("   ✅ Modul 2: Warehouse Monitor Staging/TF/MADJ/SA (Tiap 5 Menit)")
    print("   ✅ Modul 3: Memo Markom Permintaan Hadiah (Tiap 10 Menit)")
    print("   ✅ Modul 4 & 5: Export Stok 9 Cabang & Balancing (Tiap 3 Jam)")
    print("=" * 75)

    jez = create_jezpro_session()

    # 1. Jalankan thread khusus Instock agar bergerak cepat tanpa terganggu
    t_instock = threading.Thread(target=thread_instock_worker, args=(jez,), daemon=True)
    t_instock.start()
    print("🧵 Thread Instock Surabaya telah aktif dan berjalan mandiri tiap 45 detik.")

    # 2. Main Loop untuk jadwal tugas berkala lainnya
    last_monitor = 0
    last_memo = 0
    last_heavy = 0

    while True:
        curr = time.time()

        # Monitor Activity (Tiap 5 Menit / 300 Detik)
        if curr - last_monitor >= 300:
            try:
                run_module_warehouse_monitor(jez)
                last_monitor = curr
            except Exception as e:
                print(f"❌ Error Monitor: {e}")

        # Memo Markom (Tiap 10 Menit / 600 Detik)
        if curr - last_memo >= 600:
            try:
                run_module_memo_markom()
                last_memo = curr
            except Exception as e:
                print(f"❌ Error Memo: {e}")

        # Ekspor Berat & Balancing (Tiap 3 Jam / 10.800 Detik - Langsung jalan sekali di awal)
        if curr - last_heavy >= 10800 or last_heavy == 0:
            try:
                run_module_exports_and_balancing(jez)
                last_heavy = curr
            except Exception as e:
                print(f"❌ Error Heavy Export: {e}")

        time.sleep(10)