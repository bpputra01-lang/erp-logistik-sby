import os
import io
import re
import json
import time
import random
import threading
import requests
import pandas as pd
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup

# ==============================================================================
# 🔑 KREDENSIAL & KONFIGURASI PUSAT
# ==============================================================================
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://fanzsmghhbefhhaicrok.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZhbnpzbWdoaGJlZmhoYWljcm9rIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODgxNTQzNDgsImV4cCI6MjEwMzczMDM0OH0.brCSOO9nHAUK8CxDWPperpJ--_NA_nwy5cO9OqGv3I0")

JEZPRO_EMAIL = os.environ.get("JEZPRO_EMAIL", "fajarbintang786@jez.co.id")
JEZPRO_PASSWORD = os.environ.get("JEZPRO_PASSWORD", "131199")

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
# HELPER PEMBERSIH & PARSER UNIVERSAL
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
    try:
        if pd.isna(val) or val is None:
            return default
        if isinstance(val, (int, float)):
            return int(round(val))
        s = strip_html(str(val)).replace("Rp", "").strip()
        if "," in s and "." in s:
            s = s.replace(".", "").replace(",", ".")
        elif "," in s:
            s = s.replace(",", ".")
        return int(round(float(s)))
    except Exception:
        digits = re.findall(r'-?\d+', strip_html(str(val)))
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
    for fmt in ("%Y-%m-%d %H:%M:%S", "%d-%m-%Y %H:%M:%S", "%d-%b-%Y %H:%M:%S", "%d-%B-%Y %H:%M:%S", "%Y-%m-%d", "%d-%m-%Y"):
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
    print(f"🔐 [{datetime.now(WIB).strftime('%H:%M:%S')}] Login ke Jezpro ({JEZPRO_EMAIL})...")
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
    session.get("https://jezpro.id/setup_lokasi_stok_v2", timeout=15)
    session.get("https://jezpro.id/transfer_stok", timeout=15)
    session.get("https://jezpro.id/mass_adjustment", timeout=15)
    session.get("https://jezpro.id/adjustment", timeout=15)
    session.get("https://jezpro.id/stock_tracking", timeout=15)
    return session

# ==============================================================================
# MODUL 1: INSTOCK DAILY SURABAYA
# ==============================================================================
def run_module_instock_daily(session):
    now_wib = datetime.now(WIB)
    today_str = now_wib.strftime("%Y-%m-%d")
    date_param = f"{today_str}|{today_str}"

    try:
        cleanup_url = f"{SUPABASE_URL}/rest/v1/jezpro_instock_daily?sync_date=lt.{today_str}"
        requests.delete(cleanup_url, headers=HEADERS_SB, timeout=10)
    except Exception:
        pass

    url_stk = "https://jezpro.id/stock_tracking_datatables"
    params = {
        "draw": "1", "start": "0", "length": "2000",
        "st_id": str(STORE_ID_SURABAYA), "date": date_param,
        "status": "",
        "_": int(time.time() * 1000)
    }
    headers_req = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://jezpro.id/stock_tracking"
    }

    try:
        res = session.get(url_stk, params=params, headers=headers_req, timeout=25)
        if res.status_code != 200: 
            return
        raw_data = res.json().get("data", [])
    except Exception:
        return

    raw_tracking_items = []
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
        loc_bin = loc_bin if loc_bin else "STAGING INBOUND"

        status_val = ""
        for k in ["status", "plst_status", "8"]:
            if isinstance(item, dict) and item.get(k):
                status_val = strip_html(item[k]).upper(); break
            elif isinstance(item, list) and len(item) > 8:
                status_val = strip_html(item[8]).upper(); break

        full_row_text = " ".join([str(v) for v in (item.values() if isinstance(item, dict) else item) if v]).upper()
        text_no_bin = full_row_text.replace(loc_bin, "")

        if status_val:
            is_instock = ("INSTOCK" in status_val and "WAITING" not in status_val) or (status_val == "INSTOCK")
            is_waiting = ("WAITING" in status_val) and not is_instock
        else:
            is_instock = ("INSTOCK" in text_no_bin and "WAITING" not in text_no_bin)
            is_waiting = ("WAITING" in text_no_bin) and not is_instock

        if not (is_instock or is_waiting):
            continue

        art_name = ""
        for k in ["article", "p_name", "3"]:
            if isinstance(item, dict) and item.get(k):
                art_name = clean_article_name(item[k])
                if art_name != "-": break

        qty_val = 1
        for k in ["qty", "6"]:
            if isinstance(item, dict) and item.get(k):
                qty_val = safe_int_val(item[k], 1); break

        raw_tracking_items.append({
            "sku": sku, "article": art_name, "qty": qty_val,
            "location": loc_bin, "is_instock": is_instock, "is_waiting": is_waiting,
            "raw_time": raw_time, "dt_wib": dt_wib
        })

    grouped_tracking = {}
    for it in raw_tracking_items:
        st_type = "INSTOCK" if it["is_instock"] else "WAITING"
        group_key = (it["sku"], it["location"], st_type)

        if group_key not in grouped_tracking:
            grouped_tracking[group_key] = dict(it)
        else:
            grouped_tracking[group_key]["qty"] += it["qty"]
            if grouped_tracking[group_key]["article"] in ["-", ""] and it["article"] not in ["-", ""]:
                grouped_tracking[group_key]["article"] = it["article"]
            if it["dt_wib"] and (grouped_tracking[group_key]["dt_wib"] is None or it["dt_wib"] > grouped_tracking[group_key]["dt_wib"]):
                grouped_tracking[group_key]["dt_wib"] = it["dt_wib"]
                grouped_tracking[group_key]["raw_time"] = it["raw_time"]

    tracking_today = list(grouped_tracking.values())

    sb_url = f"{SUPABASE_URL}/rest/v1/jezpro_instock_daily?select=*&sync_date=eq.{today_str}"
    try:
        res_sb = requests.get(sb_url, headers=HEADERS_SB, timeout=15)
        sb_records = res_sb.json() if res_sb.status_code == 200 else []
    except Exception:
        sb_records = []

    waiting_by_sku_bin = {}
    waiting_by_sku_only = {}
    need_setup_by_sku_bin = {}
    all_sb_sku_bin_keys = set()
    done_setup_in_sb = [x for x in sb_records if x.get("status") == "DONE_SETUP"]
    need_setup_in_sb = [x for x in sb_records if x.get("status") == "NEED_SETUP"]
    used_mutasi_ids = set(str(d.get("matched_mutasi_id")) for d in done_setup_in_sb if d.get("matched_mutasi_id"))

    for r in sb_records:
        r_sku = clean_sku_key(r.get("barcode_sku"))
        r_bin = clean_bin(r.get("bin_code") or "STAGING INBOUND")
        if not r_sku: continue

        key_pair = (r_sku, r_bin)
        all_sb_sku_bin_keys.add(key_pair)

        if r.get("status") == "WAITING OFFLINE":
            waiting_by_sku_bin.setdefault(key_pair, []).append(r)
            waiting_by_sku_only.setdefault(r_sku, []).append(r)
        elif r.get("status") == "NEED_SETUP":
            need_setup_by_sku_bin.setdefault(key_pair, []).append(r)

    current_auto_id = get_next_supabase_id()
    new_inserts = []

    for tr in tracking_today:
        sku = tr["sku"]
        lokasi_bin = tr["location"]
        sku_bin_key = (sku, lokasi_bin)
        qty_val = tr["qty"]
        jam_instock_now = now_wib.isoformat()
        jam_transaksi_asal = (tr["dt_wib"] or now_wib).isoformat()

        if tr["is_instock"]:
            matched_wait = None
            if sku_bin_key in waiting_by_sku_bin and len(waiting_by_sku_bin[sku_bin_key]) > 0:
                matched_wait = waiting_by_sku_bin[sku_bin_key].pop(0)
                if sku in waiting_by_sku_only and matched_wait in waiting_by_sku_only[sku]:
                    waiting_by_sku_only[sku].remove(matched_wait)
            elif sku in waiting_by_sku_only and len(waiting_by_sku_only[sku]) > 0:
                matched_wait = waiting_by_sku_only[sku].pop(0)

            if matched_wait:
                t_id = matched_wait.get("id")
                patch_payload = {
                    "status": "NEED_SETUP",
                    "disappeared_at": jam_instock_now,
                    "bin_code": lokasi_bin,
                    "qty": qty_val
                }
                res_patch = requests.patch(f"{SUPABASE_URL}/rest/v1/jezpro_instock_daily?id=eq.{t_id}", headers=HEADERS_SB, json=patch_payload)
                if res_patch.status_code in [200, 204]:
                    matched_wait["status"] = "NEED_SETUP"
                    matched_wait["disappeared_at"] = jam_instock_now
                    matched_wait["bin_code"] = lokasi_bin
                    matched_wait["qty"] = qty_val
                    need_setup_in_sb.append(matched_wait)
            elif sku_bin_key in need_setup_by_sku_bin and len(need_setup_by_sku_bin[sku_bin_key]) > 0:
                exist_need = need_setup_by_sku_bin[sku_bin_key][0]
                if safe_int_val(exist_need.get("qty")) != qty_val:
                    t_id = exist_need.get("id")
                    requests.patch(f"{SUPABASE_URL}/rest/v1/jezpro_instock_daily?id=eq.{t_id}", headers=HEADERS_SB, json={"qty": qty_val})
                    exist_need["qty"] = qty_val
            elif sku_bin_key not in all_sb_sku_bin_keys:
                new_row = {
                    "id": current_auto_id, "store_id": STORE_ID_SURABAYA, "store_name": BRANCH_SURABAYA,
                    "barcode_sku": sku, "article_name": tr["article"], "bin_code": lokasi_bin,
                    "qty": qty_val, "status": "NEED_SETUP", "invoice": "-", "sync_date": today_str,
                    "created_at": jam_transaksi_asal, "disappeared_at": jam_instock_now,
                    "matched_mutasi_id": None, "setup_done_at": None
                }
                new_inserts.append(new_row)
                current_auto_id += 1
                all_sb_sku_bin_keys.add(sku_bin_key)

        elif tr["is_waiting"]:
            if sku_bin_key in waiting_by_sku_bin and len(waiting_by_sku_bin[sku_bin_key]) > 0:
                exist_wait = waiting_by_sku_bin[sku_bin_key][0]
                if safe_int_val(exist_wait.get("qty")) != qty_val:
                    t_id = exist_wait.get("id")
                    requests.patch(f"{SUPABASE_URL}/rest/v1/jezpro_instock_daily?id=eq.{t_id}", headers=HEADERS_SB, json={"qty": qty_val})
                    exist_wait["qty"] = qty_val
            elif sku_bin_key not in all_sb_sku_bin_keys:
                new_row = {
                    "id": current_auto_id, "store_id": STORE_ID_SURABAYA, "store_name": BRANCH_SURABAYA,
                    "barcode_sku": sku, "article_name": tr["article"], "bin_code": lokasi_bin,
                    "qty": qty_val, "status": "WAITING OFFLINE", "invoice": "-", "sync_date": today_str,
                    "created_at": jam_transaksi_asal, "disappeared_at": None, "matched_mutasi_id": None, "setup_done_at": None
                }
                new_inserts.append(new_row)
                current_auto_id += 1
                all_sb_sku_bin_keys.add(sku_bin_key)

    if new_inserts:
        res_ins = requests.post(f"{SUPABASE_URL}/rest/v1/jezpro_instock_daily", headers=HEADERS_SB, json=new_inserts)
        if res_ins.status_code in [200, 201]:
            for ins in new_inserts:
                if ins["status"] == "NEED_SETUP":
                    need_setup_in_sb.append(ins)

    if need_setup_in_sb:
        url_bin = "https://jezpro.id/bin_history_datatables"
        params_bin = {
            "draw": "1", "start": "0", "length": "1000",
            "st_id": str(STORE_ID_SURABAYA), "date": today_str,
            "_": int(time.time() * 1000)
        }
        headers_bin = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://jezpro.id/setup_lokasi_stok_v2"
        }
        try:
            r_bin = session.get(url_bin, params=params_bin, headers=headers_bin, timeout=20)
            mutasi_raw = r_bin.json().get("data", []) if r_bin.status_code == 200 else []
        except Exception:
            mutasi_raw = []

        mutasi_today = []
        for m in mutasi_raw:
            m_time = strip_html(m.get("pm_created_at") or m.get("created_at") or "")
            sku_val = clean_sku_key(m.get("ps_barcode") or m.get("barcode") or m.get("sku") or "")
            bin_tujuan = clean_bin(m.get("end_bin") or m.get("bin_end") or m.get("pl_code_end") or m.get("pl_code") or "")
            qty_mts = safe_int_val(m.get("pmt_qty") or m.get("qty") or m.get("qty_mts"), 1)

            if sku_val:
                mutasi_today.append({
                    "pmt_id": str(strip_html(m.get("pmt_id") or m.get("DT_RowIndex") or m.get("id") or "")),
                    "sku": sku_val, "bin_tujuan": bin_tujuan, "pmt_qty": qty_mts,
                    "pm_created_at": m_time, "dt_wib": parse_wib_datetime(m_time) or now_wib
                })

        mutasi_today = sorted(mutasi_today, key=lambda x: x["dt_wib"])

        for target in need_setup_in_sb:
            t_sku = clean_sku_key(target.get("barcode_sku"))
            t_qty = safe_int_val(target.get("qty"), 1)
            t_id = target.get("id")
            matched_m = None

            for m in mutasi_today:
                m_id = m["pmt_id"]
                if m_id and m_id in used_mutasi_ids: continue
                if m["sku"] == t_sku and ("GL1-INSTOCK" in m["bin_tujuan"] or "INSTOCK" in m["bin_tujuan"]) and m["pmt_qty"] >= t_qty:
                    matched_m = m; break

            if matched_m:
                if matched_m["pmt_id"]: used_mutasi_ids.add(matched_m["pmt_id"])
                requests.patch(
                    f"{SUPABASE_URL}/rest/v1/jezpro_instock_daily?id=eq.{t_id}",
                    headers=HEADERS_SB,
                    json={"status": "DONE_SETUP", "matched_mutasi_id": matched_m["pmt_id"], "setup_done_at": matched_m["pm_created_at"]}
                )

# ==============================================================================
# MODUL 2: WAREHOUSE ACTIVITY MONITOR (ALL AREA)
# ==============================================================================
def run_module_warehouse_monitor(session):
    print(f"\n📊 [{datetime.now(WIB).strftime('%H:%M:%S')}] Memulai Sinkronisasi Warehouse Activity Monitor (All Area)...")
    headers_req = {"Accept": "application/json, text/javascript, */*; q=0.01", "X-Requested-With": "XMLHttpRequest"}

    url_stg = "https://jezpro.id/stock_tracking_datatables"
    date_range = "2026-01-01|2030-12-31"
    query_targets = [
        {"status": "REFUND", "status_search": ""}, {"status": "", "status_search": "REFUND"},
        {"status": "WAITING OFFLINE", "status_search": ""}, {"status": "WAITING CHECKOUT", "status_search": ""},
        {"status": "CHECKOUT", "status_search": ""}, {"status": "WAITING NAMESET", "status_search": ""},
        {"status": "NAMESET", "status_search": ""}, {"status": "WAITING ONLINE", "status_search": ""},
        {"status": "DONE ONLINE", "status_search": ""}, {"status": "", "status_search": "DONE ONLINE"},
        {"status": "WAITING", "status_search": ""}, {"status": "", "status_search": "WAITING"}, {"status": "", "status_search": ""}
    ]

    all_staging_records = []
    seen_stg_ids = set()

    for branch_name, b_info in BRANCH_MAP.items():
        st_id = b_info["st_id"]
        for q in query_targets:
            params = {
                "draw": "1",
                "columns[0][data]": "DT_RowIndex", "columns[0][name]": "plst_id", "columns[0][orderable]": "false",
                "columns[1][data]": "datetime", "columns[1][name]": "plst_created", "columns[1][orderable]": "true",
                "columns[2][data]": "ps_barcode", "columns[2][name]": "ps_barcode", "columns[2][orderable]": "true",
                "columns[3][data]": "article", "columns[3][name]": "p_name", "columns[3][orderable]": "true",
                "columns[4][data]": "invoice", "columns[4][name]": "p_name", "columns[4][orderable]": "true",
                "columns[5][data]": "cust_name", "columns[5][name]": "cust_name", "columns[5][orderable]": "true",
                "columns[6][data]": "qty", "columns[6][name]": "p_name", "columns[6][orderable]": "true",
                "columns[7][data]": "product_location", "columns[7][name]": "pl_code", "columns[7][orderable]": "true",
                "columns[8][data]": "status", "columns[8][name]": "plst_status", "columns[8][search][value]": q["status_search"],
                "columns[9][data]": "instock_source", "columns[9][name]": "instock_source_status",
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

                doc_year = None
                for fmt in ("%d/%m/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%d-%m-%Y %H:%M:%S", "%d/%m/%Y", "%Y-%m-%d"):
                    try:
                        doc_year = datetime.strptime(dt_raw[:19].strip(), fmt).year; break
                    except Exception: pass
                if doc_year is None:
                    y_match = re.findall(r'\b(20\d{2})\b', dt_raw)
                    if y_match: doc_year = int(y_match[0])
                if doc_year is not None and doc_year < 2026: continue

                raw_id = item.get("plst_id") or item.get("id")
                p_id = safe_int_val(raw_id)
                if not p_id:
                    bar = strip_html(item.get("ps_barcode") or "")
                    p_id = abs(hash(f"{st_id}_{bar}_{dt_raw}")) % 2147483647
                if p_id in seen_stg_ids: continue
                seen_stg_ids.add(p_id)

                if is_refund: kategori_label = "REFUND"
                elif is_done_online: kategori_label = "DONE ONLINE"
                elif "NAMESET" in status_raw: kategori_label = "WAITING NAMESET"
                elif "CHECKOUT" in status_raw: kategori_label = "WAITING CHECKOUT"
                elif "ONLINE" in status_raw: kategori_label = "WAITING ONLINE"
                elif "RECEIPT" in status_raw: kategori_label = "WAITING RECEIPT"
                else: kategori_label = "WAITING OFFLINE"

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

    try:
        requests.delete(f"{SUPABASE_URL}/rest/v1/jezpro_waiting_staging?plst_id=gt.0", headers=HEADERS_SB)
        if all_staging_records:
            for i in range(0, len(all_staging_records), 100):
                requests.post(f"{SUPABASE_URL}/rest/v1/jezpro_waiting_staging", json=all_staging_records[i:i+100], headers=HEADERS_SB)
        print(f"   ✅ Warehouse Monitor Staging Updated! ({len(all_staging_records)} baris)")
    except Exception as e:
        print(f"   ❌ Gagal update Supabase monitor: {e}")

# ==============================================================================
# EKSPOR STOK & SALES SURABAYA
# ==============================================================================
def fetch_surabaya_sales_2months(session):
    now_dt = datetime.now(WIB)
    start_date = now_dt - timedelta(days=60)
    p_start = start_date.strftime('%Y-%m-%d')
    p_end = now_dt.strftime('%Y-%m-%d')
    date_param = f"{p_start}|{p_end}"

    url_dt = "https://jezpro.id/stock_tracking_datatables"
    headers_dt = {"Accept": "application/json, text/javascript, */*; q=0.01", "X-Requested-With": "XMLHttpRequest"}
    sales_by_sku = {}
    total_raw_rows = 0

    start_row = 0
    batch_size = 2000
    total_expected = 999999
    draw_count = 1

    while start_row < total_expected:
        params = {
            "draw": str(draw_count),
            "columns[0][data]": "DT_RowIndex", "columns[1][data]": "datetime",
            "columns[2][data]": "ps_barcode", "columns[3][data]": "article",
            "columns[4][data]": "invoice", "columns[5][data]": "cust_name",
            "columns[6][data]": "qty", "columns[7][data]": "product_location",
            "columns[8][data]": "status", "columns[9][data]": "instock_source",
            "order[0][column]": "0", "order[0][dir]": "desc",
            "start": str(start_row), "length": str(batch_size),
            "status": "", "st_id": str(STORE_ID_SURABAYA), "date": date_param
        }
        try:
            res_s = session.get(url_dt, params=params, headers=headers_dt, timeout=60)
            if res_s.status_code != 200: break
            j_data = res_s.json()
            chunk = j_data.get("data", [])
            total_expected = j_data.get("recordsFiltered", j_data.get("recordsTotal", 0))
            if not chunk: break

            for item in chunk:
                status_raw = strip_html(item.get("status") or item.get("plst_status") or "").upper()
                if "DONE" not in status_raw: continue

                raw_sku = strip_html(item.get("ps_barcode") or "")
                sku = raw_sku.split('.')[0].strip().upper()
                if not sku or sku in ["-", "NAN", "NONE", "NULL"]: continue

                qty_val = safe_int(item.get("qty"), 1)
                inv_val = strip_html(item.get("invoice") or "").upper()
                is_online = ("INV" not in inv_val)

                if sku not in sales_by_sku:
                    sales_by_sku[sku] = {
                        "SKU": sku, "ARTICLE": clean_article_name(item.get("article") or item.get("p_name")),
                        "SALES_OFFLINE": 0, "SALES_ONLINE": 0, "TOTAL_SALES": 0
                    }

                if is_online: sales_by_sku[sku]["SALES_ONLINE"] += qty_val
                else: sales_by_sku[sku]["SALES_OFFLINE"] += qty_val
                sales_by_sku[sku]["TOTAL_SALES"] += qty_val
                total_raw_rows += 1

            start_row += len(chunk)
            draw_count += 1
            time.sleep(0.02)
        except Exception:
            break

    summary_sales = list(sales_by_sku.values())
    if summary_sales:
        requests.post(f"{SUPABASE_URL}/rest/v1/balancing_sales_cache", headers=HEADERS_SB, json={
            "id": "SURABAYA_SALES_90D", "branch": BRANCH_SURABAYA,
            "period_start": p_start, "period_end": p_end,
            "updated_at": datetime.now(WIB).isoformat(), "total_rows": total_raw_rows,
            "sales_data": summary_sales
        }, timeout=120)

def run_module_exports_and_balancing(session):
    for branch_name, info in BRANCH_MAP.items():
        st_id = info["st_id"]
        db_id = info["db_id"]
        try:
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
                if final_url: excel_bytes = requests.get(final_url, timeout=300).content
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

                if st_id == STORE_ID_SURABAYA:
                    requests.post(f"{SUPABASE_URL}/rest/v1/balancing_stock_cache", headers=HEADERS_SB, json={
                        "id": "SURABAYA_BALANCING_STOCK", "branch": BRANCH_SURABAYA,
                        "updated_at": datetime.now(WIB).isoformat(), "total_rows": len(payload),
                        "stock_data": payload
                    }, timeout=120)
        except Exception as e:
            print(f"⚠️ Gagal ekspor {branch_name}: {e}")

    try:
        fetch_surabaya_sales_2months(session)
    except Exception as e:
        print(f"⚠️ Gagal balancing sales: {e}")

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
    print("🚀 MASTER LOCAL ORCHESTRATOR: JEZPRO -> SUPABASE (CLEAN VERSION)")
    print("=" * 75)

    jez = create_jezpro_session()

    t_instock = threading.Thread(target=thread_instock_worker, args=(jez,), daemon=True)
    t_instock.start()
    print("🧵 Thread Instock Surabaya telah aktif mandiri tiap 45 detik.")

    last_monitor = 0
    last_heavy = 0

    while True:
        curr = time.time()

        if curr - last_monitor >= 300:
            try:
                run_module_warehouse_monitor(jez)
                last_monitor = curr
            except Exception as e:
                print(f"❌ Error Monitor: {e}")

        if curr - last_heavy >= 10800 or last_heavy == 0:
            try:
                run_module_exports_and_balancing(jez)
                last_heavy = curr
            except Exception as e:
                print(f"❌ Error Heavy Export: {e}")

        time.sleep(10)