import pandas as pd
import numpy as np
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
def process_putaway_system(df_putaway, df_asal_bin):
    working_bin = df_asal_bin.copy()
    results_compare, results_putaway_list, results_kurang_setup = [], [], []
    for _, row_ds in df_putaway.iterrows():
        bin_tujuan_ds, sku_ds, qty_needed = str(row_ds.iloc[0]).strip(), str(row_ds.iloc[1]).strip(), int(row_ds.iloc[2])
        diff_qty = qty_needed
        while diff_qty > 0:
            allocated = False; bin_ketemu = ""; qty_found_in_bin = 0
            def try_allocate(prio_type):
                nonlocal diff_qty, allocated, bin_ketemu, qty_found_in_bin
                for idx, row_bin in working_bin.iterrows():
                    b_code, s_code, q_avail = str(row_bin.iloc[1]).strip().upper(), str(row_bin.iloc[2]).strip(), int(row_bin.iloc[9])
                    if s_code == sku_ds and q_avail > 0:
                        is_match = False
                        if prio_type == 1: is_match = "STAGGING LT.3" in b_code or "STAGING LT.3" in b_code
                        elif prio_type == 2: is_match = ("STAGGING" in b_code or "STAGING" in b_code or "KARANTINA" in b_code) and "LT.3" not in b_code
                        elif prio_type == 3: is_match = "STAGGING" not in b_code and "STAGING" not in b_code and "KARANTINA" not in b_code
                        if is_match:
                            take = min(q_avail, diff_qty); working_bin.iat[idx, 9] = q_avail - take
                            qty_found_in_bin, bin_ketemu, allocated = take, b_code, True; return True
                return False
            if not try_allocate(1):
                if not try_allocate(2): try_allocate(3)
            if allocated:
                note = "FULLY SETUP" if (diff_qty - qty_found_in_bin) == 0 else "PARTIAL SETUP"
                results_compare.append({"BIN ASAL": bin_tujuan_ds, "SKU": sku_ds, "QTY PUTAWAY": qty_needed, "BIN DITEMUKAN": bin_ketemu, "QTY BIN SYSTEM": qty_found_in_bin, "DIFF": diff_qty - qty_found_in_bin, "NOTE": note})
                results_putaway_list.append({"BIN AWAL": bin_ketemu, "BIN TUJUAN": bin_tujuan_ds, "SKU": sku_ds, "QUANTITY": qty_found_in_bin, "NOTES": "PUTAWAY"})
                diff_qty -= qty_found_in_bin
            else:
                results_compare.append({"BIN ASAL": bin_tujuan_ds, "SKU": sku_ds, "QTY PUTAWAY": qty_needed, "BIN DITEMUKAN": "(NO BIN)", "QTY BIN SYSTEM": 0, "DIFF": diff_qty, "NOTE": "PERLU CARI STOCK MANUAL"})
                results_kurang_setup.append({"BIN": bin_tujuan_ds, "SKU": sku_ds, "QTY": diff_qty}); break
    df_comp_final = pd.DataFrame(results_compare)
    df_sum = df_comp_final[df_comp_final['NOTE'].str.contains("SETUP", na=False)].copy()
    if not df_sum.empty:
        df_sum = df_sum[['BIN DITEMUKAN', 'BIN ASAL', 'SKU', 'QTY BIN SYSTEM']]; df_sum.columns = ['BIN AWAL', 'BIN TUJUAN', 'SKU', 'QTY PUTAWAY']
        df_sum['SISA BIN AWAL'] = df_sum.apply(lambda r: working_bin[(working_bin.iloc[:, 1].str.upper() == r['BIN AWAL']) & (working_bin.iloc[:, 2] == r['SKU'])].iloc[:, 9].sum(), axis=1)
    mask_lt3 = (working_bin.iloc[:, 9] != 0) & (working_bin.iloc[:, 1].str.contains("STAGGING LT.3", case=False, na=False))
    df_lt3 = working_bin[mask_lt3].iloc[:, [1, 2, 4, 3, 6, 5, 9]].copy() if any(mask_lt3) else pd.DataFrame()
    if not df_lt3.empty: df_lt3.columns = ["BIN", "SKU", "NAMA BARANG", "BRAND", "CATEGORY", "SATUAN", "QTY"]
    return df_comp_final, pd.DataFrame(results_putaway_list), pd.DataFrame(results_kurang_setup), df_sum, df_lt3, working_bin

def process_scan_out(df_scan, df_history, df_stock):
    df_scan.columns = [str(c).strip().upper() for c in df_scan.columns]
    df_scan['BIN_CLEAN'] = df_scan.iloc[:, 0].astype(str).str.strip()
    df_scan['SKU_CLEAN'] = df_scan.iloc[:, 1].astype(str).str.strip()
    df_scan_clean = df_scan.groupby(['BIN_CLEAN', 'SKU_CLEAN']).size().reset_index(name='QTY')
    results, draft_setup = [], []
    for _, row in df_scan_clean.iterrows():
        sku = row['SKU_CLEAN']; bin_scan = row['BIN_CLEAN']; qty = row['QTY']
        found_stock = False; found_history = False; keterangan = ""; total_qty_setup_terjual = 0; bin_after_setup = ""; invoice = ""
        match_stock = df_stock[(df_stock.iloc[:, 1].astype(str).str.strip() == sku) & (df_stock.iloc[:, 6].astype(str).str.strip() == bin_scan)]
        if not match_stock.empty:
            found_stock = True; total_qty_setup_terjual = match_stock.iloc[0, 10]; invoice = match_stock.iloc[0, 0]
            keterangan = "ITEM TELAH TERJUAL" if total_qty_setup_terjual == qty else "ITEM TERJUAL (QTY MISSMATCH)"
        if not found_stock:
            match_hist = df_history[df_history.iloc[:, 3].astype(str).str.strip() == sku]
            if not match_hist.empty:
                found_history = True; total_qty_setup_terjual = match_hist.iloc[0, 10]; bin_after_setup = match_hist.iloc[0, 12]; bin_hist_i = str(match_hist.iloc[0, 8]).strip()
                if bin_hist_i == bin_scan: keterangan = "DONE AND MATCH SET UP" if total_qty_setup_terjual == qty else "DONE SETUP (QTY MISSMATCH)"
                else: keterangan = "DONE SET UP (BIN MISSMATCH)"
        if not found_stock and not found_history:
            match_stock_any = df_stock[df_stock.iloc[:, 1].astype(str).str.strip() == sku]
            if not match_stock_any.empty: keterangan = "ITEM TERJUAL (BIN MISSMATCH)"; total_qty_setup_terjual = match_stock_any.iloc[0, 10]; invoice = match_stock_any.iloc[0, 0]; found_stock = True
        if not found_stock and not found_history: keterangan = "ITEM BELUM TERSETUP & TIDAK TERJUAL"
        if keterangan == "DONE SETUP (QTY MISSMATCH)": draft_setup.append({"BIN AWAL": bin_scan, "BIN TUJUAN": bin_after_setup, "SKU": sku, "QUANTITY": qty - total_qty_setup_terjual, "NOTES": "WAITING OFFLINE"})
        elif keterangan == "ITEM BELUM TERSETUP & TIDAK TERJUAL": draft_setup.append({"BIN AWAL": bin_scan, "BIN TUJUAN": "KARANTINA", "SKU": sku, "QUANTITY": qty, "NOTES": "WAITING OFFLINE"})
        elif keterangan == "DONE SET UP (BIN MISSMATCH)":
            draft_setup.append({"BIN AWAL": bin_after_setup, "BIN TUJUAN": bin_scan, "SKU": sku, "QUANTITY": total_qty_setup_terjual, "NOTES": "SET UP BALIK"})
            draft_setup.append({"BIN AWAL": bin_scan, "BIN TUJUAN": "KARANTINA", "SKU": sku, "QUANTITY": qty, "NOTES": "WAITING OFFLINE"})
        results.append({"BIN": bin_scan, "SKU": sku, "QTY": qty, "Keterangan": keterangan, "Total Qty Setup/Terjual": total_qty_setup_terjual, "Bin After Set Up": bin_after_setup, "Invoice": invoice})
    return pd.DataFrame(results), pd.DataFrame(draft_setup)

# --- FUNGSI BARU: REFILL & OVERSTOCK (Sesuai Logic VBA) ---
def process_refill_overstock(df_all_data, df_stock_tracking):
    # 1. Inisialisasi awal (Wajib)
    df_gl3 = pd.DataFrame()
    df_gl4 = pd.DataFrame()
    df_refill_final = pd.DataFrame()
    df_overstock_final = pd.DataFrame()

    try:
        # PEMBERSIHAN HEADER & DATA
        df_all_data.columns = [str(c).strip().upper() for c in df_all_data.columns]
        df_stock_tracking.columns = [str(c).strip().upper() for c in df_stock_tracking.columns]
        
        # Paksa QTY System jadi numerik (Kolom K = Indeks 10)
        df_all_data.iloc[:, 10] = pd.to_numeric(df_all_data.iloc[:, 10], errors='coerce').fillna(0)

        # STEP 1: Filter_ALL_DATA_to_GL3_GL4 (Sesuai Sub VBA lo)
        # Filter GL3: Ada "GL3" & Gak ada "LIVE" (Indeks 1 = Kolom B)
        mask_gl3 = (df_all_data.iloc[:, 1].astype(str).str.contains("GL3", case=False, na=False)) & \
                   (~df_all_data.iloc[:, 1].astype(str).str.contains("LIVE", case=False, na=False))
        
        # Filter GL4: Ada "GL4", Gak ada "DEFECT", "REJECT", "ONLINE", "RAK"
        exclude_gl4 = "DEFECT|REJECT|ONLINE|RAK"
        mask_gl4 = (df_all_data.iloc[:, 1].astype(str).str.contains("GL4", case=False, na=False)) & \
                   (~df_all_data.iloc[:, 1].astype(str).str.contains(exclude_gl4, case=False, na=False))
        
        df_gl3 = df_all_data[mask_gl3].copy()
        df_gl4 = df_all_data[mask_gl4].copy()

        # STEP 2: DeleteRowsNotMatchingCriteria (Filter Stock Tracking)
        # VBA: No "INV" di Col A (0) AND "DC" di Col G (6)
        st_qty_col = 10 # Kolom K di Stock Tracking
        df_stock_tracking.iloc[:, st_qty_col] = pd.to_numeric(df_stock_tracking.iloc[:, st_qty_col], errors='coerce').fillna(0)
        
        mask_st = (~df_stock_tracking.iloc[:, 0].astype(str).str.contains("INV", case=False, na=False)) & \
                  (df_stock_tracking.iloc[:, 6].astype(str).str.contains("DC", case=False, na=False))
        df_st_filtered = df_stock_tracking[mask_st].copy()

        # STEP 3: CreateRefillSheet (Logic QTY < 3)
        # Dictionary QTY GL3 (Group by SKU di Indeks 2)
        dict_gl3 = df_gl3.groupby(df_gl3.iloc[:, 2])[df_gl3.columns[10]].sum().to_dict()
        
        # List SKU yang butuh refill (QTY < 3 atau SKU baru dari GL4)
        refill_skus = [sku for sku, qty in dict_gl3.items() if qty < 3]
        for sku_gl4 in df_gl4.iloc[:, 2].unique():
            if sku_gl4 not in dict_gl3:
                refill_skus.append(sku_gl4)
        
        refill_list = []
        for sku in set(refill_skus):
            qty_gl3_current = dict_gl3.get(sku, 0)
            sisa_load = 12
            
            # Cari di GL4
            items_in_gl4 = df_gl4[df_gl4.iloc[:, 2] == sku]
            for _, row in items_in_gl4.iterrows():
                qty_gl4 = int(row.iloc[10])
                if qty_gl4 > 0 and sisa_load > 0:
                    take = min(qty_gl4, sisa_load)
                    refill_list.append({
                        "BIN": row.iloc[1], "SKU": sku, "BRAND": row.iloc[3],
                        "ITEM NAME": row.iloc[4], "VARIANT": row.iloc[5],
                        "QTY BIN AMBIL": qty_gl4, "LOAD": take, "QTY GL3": qty_gl3_current
                    })
                    sisa_load -= take
                    if sisa_load <= 0: break
        df_refill_final = pd.DataFrame(refill_list)

        # STEP 4: CreateOverstockSheet (Logic QTY > 24)
        # Dictionary Stock Tracking (Sum Qty per SKU di Indeks 1)
        dict_st_sum = df_st_filtered.groupby(df_st_filtered.iloc[:, 1])[df_st_filtered.columns[10]].sum().to_dict()
        
        overstock_list = []
        for _, row in df_gl3.iterrows():
            sku = str(row.iloc[2])
            qty_gl3_sys = int(row.iloc[10])
            
            if qty_gl3_sys > 24:
                sisa_load_os = qty_gl3_sys - 24
                # Cek Stock Tracking >= 7 (Logic VBA lo)
                if dict_st_sum.get(sku, 0) >= 7:
                    sisa_load_os = int(np.ceil(sisa_load_os / 3))
                
                if sisa_load_os > 0:
                    overstock_list.append({
                        "BIN": row.iloc[1], "SKU": sku, "BRAND": row.iloc[3],
                        "ITEM NAME": row.iloc[4], "VARIANT": row.iloc[5],
                        "QTY BIN AMBIL": qty_gl3_sys, "LOAD": sisa_load_os
                    })
        df_overstock_final = pd.DataFrame(overstock_list)

    except Exception as e:
        st.error(f"Error Logic: {e}")
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