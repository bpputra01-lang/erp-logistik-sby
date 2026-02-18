import pandas as pd
import numpy as np
import math
import io
import streamlit as st
import plotly.express as px
from python_calamine import CalamineWorkbook

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="ERP Surabaya - Adminity Pro", layout="wide")

# 2. THE AUTHENTIC ADMINITY UI ENGINE
st.markdown("""
    <style>
    .stApp { background-color: #f4f7f6; }
    [data-testid="stSidebar"] { background-color: #1e1e2f !important; border-right: 1px solid #2d2d44; }
    [data-testid="stSidebar"] .stMarkdown p { color: #aeb1b5 !important; font-family: 'Inter', sans-serif; }
    .nav-header { font-size: 11px; text-transform: uppercase; letter-spacing: 2px; color: #6c757d; padding: 20px 0 10px 10px; font-weight: 700; border-bottom: 1px solid #2d2d44; margin-bottom: 10px; }
    .hero-header { background: linear-gradient(135deg, #3a7bd5 0%, #00d2ff 100%); color: white; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); margin-bottom: 25px; }
    .m-box { background: #1e1e2f; padding: 15px; border-radius: 8px; border-left: 5px solid #ffce00; margin-bottom: 10px; text-align: center; }
    .m-lbl { color: #ffffff; font-size: 10px; font-weight: 700; text-transform: uppercase; display: block; }
    .m-val { color: #ffce00; font-size: 20px; font-weight: 800; }
    div.row-widget.stRadio > div { background-color: transparent !important; padding: 5px; }
    div.row-widget.stRadio label { color: #d1d1d1 !important; font-size: 14px !important; padding: 8px 15px !important; border-radius: 5px; transition: 0.3s; }
    div.row-widget.stRadio label:hover { background: rgba(255,255,255,0.05); color: white !important; }
    [data-testid="stWidgetLabel"] p
    </style>
    """, unsafe_allow_html=True)

# --- FUNGSI LOGIKA ASLI (TETAP SAMA) ---
import pandas as pd
import math

def process_refill_overstock(df_all_data, df_stock_tracking):

    df_gl3, df_gl4 = pd.DataFrame(), pd.DataFrame()
    df_refill_final, df_overstock_final = pd.DataFrame(), pd.DataFrame()

    try:
        # =========================
        # 1️⃣ FILTER GL3 & GL4 (SAMA PERSIS VBA)
        # =========================
        srcArr = df_all_data.values
        outGL3, outGL4 = [], []

        for i in range(len(srcArr)):
            bin_val = str(srcArr[i][6]).upper().strip() if not pd.isna(srcArr[i][6]) else ""

            if "GL3" in bin_val and "LIVE" not in bin_val:
                outGL3.append(srcArr[i])

            if "GL4" in bin_val and not any(x in bin_val for x in ["DEFECT", "REJECT", "ONLINE", "RAK"]):
                outGL4.append(srcArr[i])

        df_gl3 = pd.DataFrame(outGL3, columns=df_all_data.columns)
        df_gl4 = pd.DataFrame(outGL4, columns=df_all_data.columns)

        if df_gl3.empty and df_gl4.empty:
            return df_gl3, df_gl4, df_refill_final, df_overstock_final

        # =========================
        # 2️⃣ REFILL (MATCH VBA)
        # =========================

        # VBA: dictGL3(sku) = qty (Bukan dijumlah! Last overwrite)
        dictGL3 = {}
        for row in df_gl3.values:
            sku = str(row[2]).strip()
            qty = int(float(row[10])) if not pd.isna(row[10]) else 0
            dictGL3[sku] = qty   # overwrite (SAMA PERSIS VBA)

        # SKU target refill
        dictSKUs = {}

        # GL3 qty < 3
        for sku, qty in dictGL3.items():
            if qty < 3:
                dictSKUs[sku] = True

        # SKU baru dari GL4
        for row in df_gl4.values:
            sku = str(row[2]).strip()
            qty = int(float(row[10])) if not pd.isna(row[10]) else 0
            if qty > 0 and sku not in dictGL3:
                dictSKUs[sku] = True

        refill_results = []

        for sku in dictSKUs.keys():

            qtyGL3 = dictGL3.get(sku, 0)
            sisaLoad = 12

            for row_g4 in df_gl4.values:

                if str(row_g4[2]).strip() == sku:

                    qtyGL4 = int(float(row_g4[10])) if not pd.isna(row_g4[10]) else 0

                    if qtyGL4 > 0 and sisaLoad > 0:

                        loadQty = min(qtyGL4, sisaLoad)

                        refill_results.append([
                            row_g4[1],      # BIN (kolom 2 VBA)
                            sku,
                            row_g4[3],      # BRAND
                            row_g4[4],      # ITEM NAME
                            row_g4[5],      # VARIANT
                            qtyGL4,
                            loadQty,
                            qtyGL3
                        ])

                        sisaLoad -= loadQty

                        if sisaLoad <= 0:
                            break

        df_refill_final = pd.DataFrame(
            refill_results,
            columns=["BIN","SKU","BRAND","ITEM NAME","VARIANT","QTY BIN AMBIL","LOAD","QTY GL3"]
        )

        # =========================
        # 3️⃣ OVERSTOCK (MATCH VBA)
        # =========================

        # Stock Tracking Dictionary
        dictTrans = {}
        for st_row in df_stock_tracking.values:

            if "INV" not in str(st_row[0]).upper() and "DC" in str(st_row[6]).upper():

                barcode = str(st_row[1]).strip()
                qty = float(st_row[10]) if not pd.isna(st_row[10]) else 0
                dictTrans[barcode] = dictTrans.get(barcode, 0) + qty

        # STEP 1: Cari SKU GL3 > 24 (per SKU dulu)
        dictOverSKU = {}

        for row_g3 in df_gl3.values:
            sku = str(row_g3[2]).strip()
            qty = int(float(row_g3[10])) if not pd.isna(row_g3[10]) else 0

            if qty > 24:
                dictOverSKU[sku] = qty - 24

        overstock_results = []

        # STEP 2: Process per SKU (SAMA PERSIS VBA)
        for sku, sisaLoad in dictOverSKU.items():

            # cek stock tracking
            if dictTrans.get(sku, 0) >= 7:
                sisaLoad = math.ceil(sisaLoad / 3)

            # loop GL3 cari BIN
            for row_g3 in df_gl3.values:

                if str(row_g3[2]).strip() == sku:

                    qtyGL3 = int(float(row_g3[10])) if not pd.isna(row_g3[10]) else 0

                    if qtyGL3 > 0 and sisaLoad > 0:

                        loadQty = min(qtyGL3, sisaLoad)

                        overstock_results.append([
                            row_g3[1],  # BIN
                            sku,
                            row_g3[3],
                            row_g3[4],
                            row_g3[5],
                            qtyGL3,
                            loadQty
                        ])

                        sisaLoad -= loadQty

                        if sisaLoad <= 0:
                            break

        df_overstock_final = pd.DataFrame(
            overstock_results,
            columns=["BIN","SKU","BRAND","ITEM NAME","VARIANT","QTY BIN AMBIL","LOAD"]
        )

    except Exception as e:
        print(f"ERROR LOGIC: {e}")

    return df_gl3, df_gl4, df_refill_final, df_overstock_final

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown("<h2 style='color: #00d2ff; text-align: center; margin-bottom: 20px;'>🚛 ERP LOGISTIC SURABAYA</h2>", unsafe_allow_html=True)
    st.markdown('<p class="nav-header">MAIN MENU</p>', unsafe_allow_html=True)
    m1 = ["📊 Dashboard Overview", "📓 Database Master"]
    st.markdown('<p class="nav-header">INVENTORY TOOLS</p>', unsafe_allow_html=True)
    m2 = ["📥 Putaway System", "📤 Scan Out Validasi", "🔄 Refill & Overstock", "⛔ Stock Minus"]
    menu = st.radio("Navigation", m1 + m2, label_visibility="visible")
    st.divider()
    st.caption("ERP Logistic Surabaya v2.1 | Surabaya Branch")

# --- MENU ROUTING ---
if menu == "📊 Dashboard Overview":
    st.markdown('<div class="hero-header"><h1>📊 DASHBOARD ANALYTICS</h1></div>', unsafe_allow_html=True)
    c1, c2 = st.columns([3, 1])
    with c1: pilih = st.selectbox("PILIH LAPORAN", ["WORKING REPORT", "PERSONAL PERFORMANCE", "CYCLE COUNT DAN KERAPIHAN", "DASHBOARD MOVING STOCK"])
    with c2: zoom = st.slider("ZOOM", 0.1, 1.0, 0.35)
    dash_links = {"WORKING REPORT": "864743695", "PERSONAL PERFORMANCE": "251294539", "CYCLE COUNT DAN KERAPIHAN": "1743896821", "DASHBOARD MOVING STOCK": "1671817510"}
    st.markdown(f'''<div style="background: white; border-radius: 15px; padding: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);"><div style="width: 100%; height: 600px; overflow: auto;"><iframe src="https://docs.google.com/spreadsheets/d/e/2PACX-1vRIMd-eghecjZKcOmhz0TW4f-1cG0LOWgD6X9mIK1XhiYSOx-V6xSnZQzBLfru0LhCIinIZAfbYnHv_/pubhtml?gid={dash_links[pilih]}&single=true&rm=minimal" style="width: 4000px; height: 1500px; border: none; transform: scale({zoom}); transform-origin: 0 0;"></iframe></div></div>''', unsafe_allow_html=True)

elif menu == "📥 Putaway System":
    st.markdown('<div class="hero-header"><h1>📥 PUTAWAY SYSTEM COMPARATION</h1></div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1: up_ds = st.file_uploader("Upload DS PUTAWAY", type=['xlsx', 'csv'])
    with c2: up_asal = st.file_uploader("Upload ASAL BIN PUTAWAY", type=['xlsx', 'csv'])
    if up_ds and up_asal:
        if st.button("⚡ JALANKAN PROSES PUTAWAY"):
            try:
                df_ds_p = pd.read_csv(up_ds) if up_ds.name.endswith('.csv') else pd.read_excel(up_ds, engine='calamine')
                df_asal_p = pd.read_csv(up_asal) if up_asal.name.endswith('.csv') else pd.read_excel(up_asal, engine='calamine')
                df_comp, df_plist, df_kurang, df_sum, df_lt3, df_updated_bin = process_putaway_system(df_ds_p, df_asal_p)
                st.success("Proses Putaway Selesai!")
                t1, t2, t3, t4, t5 = st.tabs(["📋 Compare", "📝 List", "⚠️ Kurang Setup", "📊 Summary", "📦 LT.3 Out"])
                with t1: st.dataframe(df_comp, use_container_width=True)
                with t2: st.dataframe(df_plist, use_container_width=True)
                with t3: st.dataframe(df_kurang, use_container_width=True)
                with t4: st.dataframe(df_sum, use_container_width=True)
                with t5: st.dataframe(df_lt3, use_container_width=True)
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_comp.to_excel(writer, sheet_name='COMPARE', index=False); df_plist.to_excel(writer, sheet_name='LIST', index=False)
                    df_kurang.to_excel(writer, sheet_name='KURANG', index=False); df_sum.to_excel(writer, sheet_name='SUMMARY', index=False)
                    df_updated_bin.to_excel(writer, sheet_name='UPDATED_BIN', index=False)
                st.download_button("📥 DOWNLOAD REPORT", data=output.getvalue(), file_name="REPORT_PUTAWAY.xlsx")
            except Exception as e: st.error(f"Gagal: {e}")

elif menu == "📤 Scan Out Validasi":
    st.markdown('<div class="hero-header"><h1>📤 SCAN OUT & VALIDASI</h1></div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1: up_scan = st.file_uploader("Upload DATA SCAN", type=['xlsx', 'csv'])
    with col2: up_hist = st.file_uploader("Upload HISTORY SET UP", type=['xlsx'])
    with col3: up_stock = st.file_uploader("Upload STOCK TRACKING", type=['xlsx'])
    if up_scan and up_hist and up_stock:
        if st.button("🚀 JALANKAN PROSES VALIDASI"):
            try:
                df_s = pd.read_excel(up_scan, engine='calamine') if up_scan.name.endswith('xlsx') else pd.read_csv(up_scan)
                df_h = pd.read_excel(up_hist, engine='calamine'); df_st = pd.read_excel(up_stock, engine='calamine')
                df_res, df_draft = process_scan_out(df_s, df_h, df_st)
                st.success("Validasi Selesai!")
                def highlight_vba(val): return f'color: {"red" if "MISSMATCH" in str(val) or "BELUM" in str(val) else "black"}; font-weight: bold'
                st.subheader("📋 DATA SCAN (COMPARED)"); st.dataframe(df_res.style.applymap(highlight_vba, subset=['Keterangan']), use_container_width=True)
                st.subheader("📝 DRAFT SET UP"); st.dataframe(df_draft, use_container_width=True)
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_res.to_excel(writer, sheet_name='DATA SCAN', index=False); df_draft.to_excel(writer, sheet_name='DRAFT', index=False)
                st.download_button("📥 DOWNLOAD SCAN OUT", data=output.getvalue(), file_name="SCAN_OUT_RESULT.xlsx")
            except Exception as e: st.error(f"Error: {e}")

elif menu == "🔄 Refill & Overstock":
    st.markdown('<div class="hero-header"><h1>🔄 REFILL & OVERSTOCK SYSTEM</h1></div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1: up_all = st.file_uploader("Upload ALL DATA STOCK", type=['xlsx'])
    with c2: up_track = st.file_uploader("Upload STOCK TRACKING", type=['xlsx'])
    if up_all and up_track:
        if st.button("🚀 PROSES REFILL & OVERSTOCK"):
            try:
                with st.spinner("Processing..."):
                    df_all = pd.read_excel(up_all, engine='calamine')
                    df_track = pd.read_excel(up_track, engine='calamine')
                    res_gl3, res_gl4, res_refill, res_over = process_refill_overstock(df_all, df_track)
                    st.success("Data Berhasil di Filter!")
                    m1, m2, m3 = st.columns(3)
                    m1.markdown(f'<div class="m-box"><span class="m-lbl">REFILL ITEMS</span><span class="m-val">{len(res_refill)}</span></div>', unsafe_allow_html=True)
                    m2.markdown(f'<div class="m-box"><span class="m-lbl">OVERSTOCK ITEMS</span><span class="m-val">{len(res_over)}</span></div>', unsafe_allow_html=True)
                    m3.markdown(f'<div class="m-box"><span class="m-lbl">GL3/GL4 ROWS</span><span class="m-val">{len(res_gl3)+len(res_gl4)}</span></div>', unsafe_allow_html=True)
                    t1, t2, t3, t4 = st.tabs(["📦 REFILL", "⚠️ OVERSTOCK", "📑 GL3 DATA", "📑 GL4 DATA"])
                    with t1: st.dataframe(res_refill, use_container_width=True)
                    with t2: st.dataframe(res_over, use_container_width=True)
                    with t3: st.dataframe(res_gl3, use_container_width=True)
                    with t4: st.dataframe(res_gl4, use_container_width=True)
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        res_refill.to_excel(writer, sheet_name='REFILL', index=False)
                        res_over.to_excel(writer, sheet_name='OVERSTOCK', index=False)
                        res_gl3.to_excel(writer, sheet_name='GL3', index=False)
                        res_gl4.to_excel(writer, sheet_name='GL4', index=False)
                    st.download_button("📥 DOWNLOAD REPORT", data=output.getvalue(), file_name="REFILL_OVERSTOCK_REPORT.xlsx")
            except Exception as e: st.error(f"Error: {e}")

elif menu == "📓 Database Master":
    st.markdown('<div class="hero-header"><h1>📓 DATABASE MASTER CHECKER</h1></div>', unsafe_allow_html=True)
    raw_url = st.text_input("LINK GOOGLE SPREADSHEET:", placeholder="https://docs.google.com/spreadsheets/d/...")
    if raw_url and "/d/" in raw_url:
        try:
            file_id = raw_url.split("/d/")[1].split("/")[0]
            xlsx_url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
            all_sheets = pd.read_excel(xlsx_url, sheet_name=None, engine='calamine')
            selected_sheet = st.selectbox("PILIH TAB:", list(all_sheets.keys()))
            if selected_sheet:
                df_master = pd.read_excel(xlsx_url, sheet_name=selected_sheet, engine='calamine')
                c1, c2, c3, c4 = st.columns(4)
                with c1: st.markdown(f'<div class="m-box"><span class="m-lbl">BARIS</span><span class="m-val">{len(df_master)}</span></div>', unsafe_allow_html=True)
                with c2: st.markdown(f'<div class="m-box"><span class="m-lbl">KOLOM</span><span class="m-val">{len(df_master.columns)}</span></div>', unsafe_allow_html=True)
                with c3: st.markdown(f'<div class="m-box"><span class="m-lbl">STATUS</span><span class="m-val">LIVE</span></div>', unsafe_allow_html=True)
                with c4: st.markdown(f'<div class="m-box"><span class="m-lbl">ENGINE</span><span class="m-val">PRO</span></div>', unsafe_allow_html=True)
                st.dataframe(df_master, use_container_width=True, height=500)
        except Exception as e: st.error(f"Error: {e}")

elif menu == "⛔ Stock Minus":
    st.markdown('<div class="hero-header"><h1>⛔ STOCK MINUS CLEARANCE</h1></div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload File dari Jezpro", type=["xlsx", "xlsm"])
    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file, engine="calamine")
            col_sku, col_bin = 'SKU', 'BIN'
            col_qty = next((c for c in df.columns if 'QTY SYS' in str(c).upper()), 'QTY SYSTEM')
            if st.button("🔃 PROSES DATA"):
                with st.spinner('Memproses...'):
                    df_minus_awal = df[df[col_qty] < 0].copy()
                    qty_arr = pd.to_numeric(df[col_qty], errors='coerce').fillna(0).values
                    sku_arr, bin_arr = df[col_sku].astype(str).values, df[col_bin].astype(str).values
                    prior_bins = ["RAK ACC LT.1", "STAGGING INBOUND", "STAGGING OUTBOUND", "KARANTINA DC", "KARANTINA STORE 02", "STAGGING REFUND", "STAGING GAGAL QC", "STAGGING LT.3", "STAGGING OUTBOUND SEMARANG", "STAGGING OUTBOUND SIDOARJO", "STAGGING LT.2", "LT.4"]
                    pos_map = {}
                    for i, q in enumerate(qty_arr):
                        if q > 0:
                            s = sku_arr[i]
                            if s not in pos_map: pos_map[s] = {}
                            b = bin_arr[i].upper()
                            if b not in pos_map[s]: pos_map[s][b] = []
                            pos_map[s][b].append(i)
                    set_up_results = []
                    minus_indices = np.where(qty_arr < 0)[0]
                    for idx in minus_indices:
                        sku_target, qty_needed, bin_tujuan = sku_arr[idx], abs(qty_arr[idx]), bin_arr[idx].upper()
                        if sku_target in pos_map:
                            sku_bins = pos_map[sku_target]
                            while qty_needed > 0:
                                found_idx = -1
                                if bin_tujuan == "TOKO":
                                    for b_name, indices in sku_bins.items():
                                        if "LT.2" in b_name or "GL2-STORE" in b_name:
                                            for p_idx in indices:
                                                if qty_arr[p_idx] > 0: found_idx = p_idx; break
                                        if found_idx != -1: break
                                elif "LT.2" in bin_tujuan or "GL2-STORE" in bin_tujuan:
                                    if "TOKO" in sku_bins:
                                        for p_idx in sku_bins["TOKO"]:
                                            if qty_arr[p_idx] > 0: found_idx = p_idx; break
                                if found_idx == -1:
                                    for pb in prior_bins:
                                        if pb in sku_bins:
                                            for p_idx in sku_bins[pb]:
                                                if qty_arr[p_idx] > 0: found_idx = p_idx; break
                                        if found_idx != -1: break
                                if found_idx == -1:
                                    for b_name, indices in sku_bins.items():
                                        if b_name != "REJECT DEFECT":
                                            for p_idx in indices:
                                                if qty_arr[p_idx] > 0: found_idx = p_idx; break
                                        if found_idx != -1: break
                                if found_idx != -1:
                                    take = min(qty_needed, qty_arr[found_idx]); qty_arr[found_idx] -= take; qty_arr[idx] += take
                                    set_up_results.append({"BIN AWAL": bin_arr[found_idx], "BIN TUJUAN": bin_arr[idx], "SKU": sku_target, "QUANTITY": take, "NOTES": "STOCK MINUS"})
                                    qty_needed -= take
                                else: break
                    df_final = df.copy(); df_final[col_qty] = qty_arr; df_need_adj = df_final[df_final[col_qty] < 0].copy()
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df_minus_awal.to_excel(writer, sheet_name='MINUS_AWAL', index=False)
                        if set_up_results: pd.DataFrame(set_up_results).to_excel(writer, sheet_name='SET_UP', index=False)
                        if not df_need_adj.empty: df_need_adj.to_excel(writer, sheet_name='JUSTIFIKASI', index=False)
                    st.success("✅ Berhasil diproses!"); st.download_button("📥 DOWNLOAD HASIL", data=output.getvalue(), file_name="HASIL_STOCK_MINUS.xlsx")
        except Exception as e: st.error(f"Error: {e}")