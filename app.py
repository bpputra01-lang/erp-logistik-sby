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
def process_refill_overstock(df_all_data, df_stock_tracking):
    # 1. Standarisasi Header biar gak sensitif spasi/huruf besar kecil
    df_all_data.columns = [str(c).strip().upper() for c in df_all_data.columns]
    df_stock_tracking.columns = [str(c).strip().upper() for c in df_stock_tracking.columns]

    # 2. Cari Kolom Kunci (Biar gak salah tembak indeks lagi)
    # Kita cari kolom yang ada kata 'LOCATION', 'BARCODE', dan 'QTY'
    col_bin = next((c for c in df_all_data.columns if 'LOCATION' in c), None)
    col_sku = next((c for c in df_all_data.columns if 'BARCODE' in c or 'SKU' in c), None)
    col_qty = next((c for c in df_all_data.columns if 'QTY' in c), None)

    # Backup jika nama kolom beda banget (Pakai indeks SS lo: G=6, B=1, K=10)
    if not col_bin: col_bin = df_all_data.columns[6] 
    if not col_sku: col_sku = df_all_data.columns[1]
    if not col_qty: col_qty = df_all_data.columns[10]

    # 3. Paksa Qty jadi angka (penting biar itungan gak 0)
    df_all_data[col_qty] = pd.to_numeric(df_all_data[col_qty], errors='coerce').fillna(0).astype(int)
    df_stock_tracking[col_qty] = pd.to_numeric(df_stock_tracking.iloc[:, 10], errors='coerce').fillna(0).astype(int)

    # 4. FILTERING (Pake Location Code yang bener)
    # Filter GL3: Harus ada GL3 tapi gak boleh ada LIVE
    mask_gl3 = (df_all_data[col_bin].astype(str).str.contains("GL3", case=False, na=False)) & \
               (~df_all_data[col_bin].astype(str).str.contains("LIVE", case=False, na=False))
    
    # Filter GL4: Harus ada GL4 dan bersih dari reject dkk
    mask_gl4 = (df_all_data[col_bin].astype(str).str.contains("GL4", case=False, na=False)) & \
               (~df_all_data[col_bin].astype(str).str.contains("DEFECT|REJECT|ONLINE|RAK", case=False, na=False))

    df_gl3 = df_all_data[mask_gl3].copy()
    df_gl4 = df_all_data[mask_gl4].copy()

    # --- SISA LOGIC REFILL & OVERSTOCK (Pake dictionary biar cepet) ---
    res_refill = []
    res_over = []
    
    if not df_gl3.empty:
        # Grouping GL3 buat tau stok per SKU di GL3
        summary_gl3 = df_gl3.groupby(col_sku)[col_qty].sum().to_dict()
        
        # Logic Refill
        # SKU yang di GL3 < 3 atau SKU yang ada di GL4 tapi ga ada di GL3
        skus_to_check = set([sku for sku, q in summary_gl3.items() if q < 3] + list(df_gl4[col_sku].unique()))
        
        for sku in skus_to_check:
            q_gl3 = summary_gl3.get(sku, 0)
            if q_gl3 < 3 or sku not in summary_gl3:
                sisa_load = 12
                sources = df_gl4[df_gl4[col_sku] == sku]
                for _, row in sources.iterrows():
                    q_g4 = row[col_qty]
                    if q_g4 > 0 and sisa_load > 0:
                        take = min(q_g4, sisa_load)
                        res_refill.append([row[col_bin], sku, row.get('BRAND',''), row.get('PRODUCT NAME',''), row.get('COLOR',''), q_g4, take, q_gl3])
                        sisa_load -= take
                        if sisa_load <= 0: break

        # Logic Overstock (Sesuai VBA lo)
        # Filter Stock Tracking (Indeks 0 bukan INV, Indeks 6 ada DC)
        st_filtered = df_stock_tracking[(~df_stock_tracking.iloc[:,0].astype(str).str.contains("INV", case=False)) & 
                                        (df_stock_tracking.iloc[:,6].astype(str).str.contains("DC", case=False))]
        dict_st = st_filtered.groupby(st_filtered.columns[1])[st_filtered.columns[10]].sum().to_dict()

        for _, row in df_gl3.iterrows():
            q_sys = row[col_qty]
            if q_sys > 24:
                load = q_sys - 24
                if dict_st.get(row[col_sku], 0) >= 7:
                    load = math.ceil(load / 3)
                if load > 0:
                    res_over.append([row[col_bin], row[col_sku], row.get('BRAND',''), row.get('PRODUCT NAME',''), row.get('COLOR',''), q_sys, load])

    # Convert back to DataFrame
    df_refill_final = pd.DataFrame(res_refill, columns=["BIN", "SKU", "BRAND", "ITEM NAME", "VARIANT", "QTY BIN AMBIL", "LOAD", "QTY GL3"])
    df_overstock_final = pd.DataFrame(res_over, columns=["BIN", "SKU", "BRAND", "ITEM NAME", "VARIANT", "QTY BIN AMBIL", "LOAD"])

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