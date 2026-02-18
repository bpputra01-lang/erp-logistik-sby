import pandas as pd
import numpy as np
import io
import streamlit as st
import plotly.express as px
from python_calamine import CalamineWorkbook

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="ERP Surabaya - Pro", layout="wide")

# 2. CUSTOM CSS GLOBAL
# GANTI BAGIAN CUSTOM CSS (NOMOR 2) DENGAN TEMPLATE INI:

# --- 2. THE ULTIMATE ENTERPRISE TEMPLATE ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;700;800&display=swap');

    /* Global Body */
    .stApp {
        background: #fdfdfd;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Sidebar - Modern Dark Nav */
    [data-testid="stSidebar"] {
        background: #0f172a !important;
        box-shadow: 5px 0 15px rgba(0,0,0,0.1);
    }
    [data-testid="stSidebarNav"] {
        padding-top: 2rem;
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: #94a3b8 !important;
        font-size: 14px;
    }

    /* Hero Header - Enterprise Style */
    .hero-header {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border-radius: 24px;
        padding: 40px;
        margin-bottom: 35px;
        position: relative;
        overflow: hidden;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        border: 1px solid rgba(255,255,255,0.1);
    }
    .hero-header::after {
        content: "";
        position: absolute;
        top: -50%; right: -20%;
        width: 300px; height: 300px;
        background: rgba(59, 130, 246, 0.1);
        border-radius: 50%;
        filter: blur(50px);
    }
    .hero-header h1 {
        font-weight: 800 !important;
        color: white !important;
        font-size: 2.5rem !important;
        letter-spacing: -1px !important;
        margin: 0 !important;
    }

    /* Metric Box - Glass Card */
    .m-box { 
        background: #1e293b !important; 
        border: 1px solid rgba(255,255,255,0.1) !important;
        padding: 30px !important; 
        border-radius: 20px !important; 
        text-align: left !important; 
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        position: relative;
    }
    .m-box:hover {
        transform: translateY(-8px);
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        border-color: #3b82f6 !important;
    }
    .m-val { 
        font-size: 42px !important; 
        font-weight: 800 !important; 
        color: #3b82f6 !important; /* Neon Blue */
        display: block !important;
        text-shadow: 0 0 10px rgba(59, 130, 246, 0.3);
    }
    .m-lbl { 
        font-size: 12px !important; 
        color: #cbd5e1 !important; 
        text-transform: uppercase !important; 
        font-weight: 700 !important; 
        letter-spacing: 2px !important;
        opacity: 0.8;
    }

    /* Input & Dropdown - Dark Chrome Look */
    div[data-baseweb="select"] > div, 
    div[data-baseweb="input"] > div,
    .stTextInput input {
        background-color: #1e293b !important;
        color: #ffffff !important;
        border: 1px solid #334155 !important;
        border-radius: 14px !important;
        padding: 12px !important;
        transition: 0.3s;
    }
    div[data-baseweb="select"]:focus-within, 
    .stTextInput:focus-within {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.2) !important;
    }

    /* Buttons - Glow Action */
    .stButton>button {
        background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%) !important;
        color: white !important;
        border: none !important;
        padding: 12px 28px !important;
        border-radius: 14px !important;
        font-weight: 700 !important;
        font-size: 16px !important;
        width: 100%;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .stButton>button:hover {
        box-shadow: 0 10px 20px -5px rgba(37, 99, 235, 0.5);
        transform: scale(1.02);
    }

    /* Tabs Customization */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background: #f1f5f9;
        padding: 8px;
        border-radius: 16px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 12px;
        padding: 10px 20px;
        font-weight: 600;
        color: #64748b;
    }
    .stTabs [aria-selected="true"] {
        background-color: white !important;
        color: #0f172a !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }

    /* Dataframe Styling */
    [data-testid="stDataFrame"] {
        background: white;
        padding: 15px;
        border-radius: 20px;
        border: 1px solid #e2e8f0;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNGSI LOGIKA PUTAWAY SYSTEM ---
def process_putaway_system(df_putaway, df_asal_bin):
    working_bin = df_asal_bin.copy()
    results_compare = []
    results_putaway_list = []
    results_kurang_setup = []

    # Loop DS PUTAWAY (A:BIN_ASAL, B:SKU, C:QTY)
    for _, row_ds in df_putaway.iterrows():
        bin_tujuan_ds = str(row_ds.iloc[0]).strip()
        sku_ds = str(row_ds.iloc[1]).strip()
        qty_needed = int(row_ds.iloc[2])
        diff_qty = qty_needed
        
        while diff_qty > 0:
            allocated = False
            bin_ketemu = ""
            qty_found_in_bin = 0

            def try_allocate(prio_type):
                nonlocal diff_qty, allocated, bin_ketemu, qty_found_in_bin
                for idx, row_bin in working_bin.iterrows():
                    b_code = str(row_bin.iloc[1]).strip().upper() 
                    s_code = str(row_bin.iloc[2]).strip()         
                    q_avail = int(row_bin.iloc[9])                
                    
                    if s_code == sku_ds and q_avail > 0:
                        is_match = False
                        if prio_type == 1: 
                            if "STAGGING LT.3" in b_code or "STAGING LT.3" in b_code: is_match = True
                        elif prio_type == 2: 
                            if ("STAGGING" in b_code or "STAGING" in b_code or "KARANTINA" in b_code) and "LT.3" not in b_code: is_match = True
                        elif prio_type == 3: 
                            if "STAGGING" not in b_code and "STAGING" not in b_code and "KARANTINA" not in b_code: is_match = True
                        
                        if is_match:
                            take = min(q_avail, diff_qty)
                            working_bin.iat[idx, 9] = q_avail - take 
                            qty_found_in_bin = take
                            bin_ketemu = b_code
                            allocated = True
                            return True
                return False

            if not try_allocate(1):
                if not try_allocate(2):
                    try_allocate(3)

            if allocated:
                note = "FULLY SETUP" if (diff_qty - qty_found_in_bin) == 0 else "PARTIAL SETUP"
                results_compare.append({
                    "BIN ASAL": bin_tujuan_ds, "SKU": sku_ds, "QTY PUTAWAY": qty_needed,
                    "BIN DITEMUKAN": bin_ketemu, "QTY BIN SYSTEM": qty_found_in_bin,
                    "DIFF": diff_qty - qty_found_in_bin, "NOTE": note
                })
                results_putaway_list.append({
                    "BIN AWAL": bin_ketemu, "BIN TUJUAN": bin_tujuan_ds,
                    "SKU": sku_ds, "QUANTITY": qty_found_in_bin, "NOTES": "PUTAWAY"
                })
                diff_qty -= qty_found_in_bin
            else:
                results_compare.append({
                    "BIN ASAL": bin_tujuan_ds, "SKU": sku_ds, "QTY PUTAWAY": qty_needed,
                    "BIN DITEMUKAN": "(NO BIN)", "QTY BIN SYSTEM": 0,
                    "DIFF": diff_qty, "NOTE": "PERLU CARI STOCK MANUAL"
                })
                results_kurang_setup.append({"BIN": bin_tujuan_ds, "SKU": sku_ds, "QTY": diff_qty})
                break

    # --- TAMBAHAN 2 MACRO (TANPA NGURANGIN LOGIC DI ATAS) ---
    df_comp_final = pd.DataFrame(results_compare)
    
    # Macro 1: Summary Putaway (Logic SumIfs)
    df_sum = df_comp_final[df_comp_final['NOTE'].str.contains("SETUP", na=False)].copy()
    if not df_sum.empty:
        df_sum = df_sum[['BIN DITEMUKAN', 'BIN ASAL', 'SKU', 'QTY BIN SYSTEM']]
        df_sum.columns = ['BIN AWAL', 'BIN TUJUAN', 'SKU', 'QTY PUTAWAY']
        # Sisa Bin Awal setelah dipotong
        df_sum['SISA BIN AWAL'] = df_sum.apply(lambda r: working_bin[(working_bin.iloc[:, 1].str.upper() == r['BIN AWAL']) & (working_bin.iloc[:, 2] == r['SKU'])].iloc[:, 9].sum(), axis=1)

    # Macro 2: Stagging LT.3 Outstanding (Sisa Stock yang masih ada di Stagging LT.3)
    mask_lt3 = (working_bin.iloc[:, 9] != 0) & (working_bin.iloc[:, 1].str.contains("STAGGING LT.3", case=False, na=False))
    df_lt3 = working_bin[mask_lt3].iloc[:, [1, 2, 4, 3, 6, 5, 9]].copy() if any(mask_lt3) else pd.DataFrame()
    if not df_lt3.empty: df_lt3.columns = ["BIN", "SKU", "NAMA BARANG", "BRAND", "CATEGORY", "SATUAN", "QTY"]

    return df_comp_final, pd.DataFrame(results_putaway_list), pd.DataFrame(results_kurang_setup), df_sum, df_lt3, working_bin

# --- FUNGSI LOGIKA SCAN OUT (TETAP) ---
def process_scan_out(df_scan, df_history, df_stock):
    df_scan.columns = [str(c).strip().upper() for c in df_scan.columns]
    df_scan['BIN_CLEAN'] = df_scan.iloc[:, 0].astype(str).str.strip()
    df_scan['SKU_CLEAN'] = df_scan.iloc[:, 1].astype(str).str.strip()
    df_scan_clean = df_scan.groupby(['BIN_CLEAN', 'SKU_CLEAN']).size().reset_index(name='QTY')
    results = []
    draft_setup = []
    for _, row in df_scan_clean.iterrows():
        sku = row['SKU_CLEAN']; bin_scan = row['BIN_CLEAN']; qty = row['QTY']
        found_stock = False; found_history = False; keterangan = ""
        total_qty_setup_terjual = 0; bin_after_setup = ""; invoice = ""
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

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='color: white;'>🚀 ERP LOGISTIK SURABAYA</h2>", unsafe_allow_html=True)
    st.divider()
    menu = st.radio("MODUL UTAMA", ["📊 Dashboard Overview", "📥 Putaway System", "📤 Scan Out", "📝 Dashboard Database", "⛔ Stock Minus"])

# --- MENU PUTAWAY SYSTEM (UPDATED WITH 2 MACROS) ---
if menu == "📥 Putaway System":
    st.markdown('<div class="hero-header"><h1>📥 PUTAWAY SYSTEM COMPARATION</h1></div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1: up_ds = st.file_uploader("Upload DS PUTAWAY", type=['xlsx', 'csv'])
    with c2: up_asal = st.file_uploader("Upload ASAL BIN PUTAWAY", type=['xlsx', 'csv'])
    
    if up_ds and up_asal:
        if st.button("⚡ JALANKAN PROSES PUTAWAY"):
            try:
                if up_ds.name.endswith('.csv'): df_ds_p = pd.read_csv(up_ds)
                else: df_ds_p = pd.read_excel(up_ds, engine='calamine')
                
                if up_asal.name.endswith('.csv'): df_asal_p = pd.read_csv(up_asal)
                else: df_asal_p = pd.read_excel(up_asal, engine='calamine')
                
                # Panggil fungsi (Sekarang return 6 variabel)
                df_comp, df_plist, df_kurang, df_sum, df_lt3, df_updated_bin = process_putaway_system(df_ds_p, df_asal_p)
                
                st.success("Proses Putaway Selesai!")
                t1, t2, t3, t4, t5 = st.tabs(["📋 Compare", "📝 List", "⚠️ Kurang Setup", "📊 Summary", "📦 LT.3 Out"])
                with t1: st.dataframe(df_comp, use_container_width=True)
                with t2: st.dataframe(df_plist, use_container_width=True)
                with t3: st.dataframe(df_kurang, use_container_width=True)
                with t4: st.dataframe(df_sum, use_container_width=True)
                with t5: st.dataframe(df_lt3, use_container_width=True)
                
                # Export ke Excel dengan Sheet Tambahan
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_comp.to_excel(writer, sheet_name='COMPARE PUTAWAY', index=False)
                    df_plist.to_excel(writer, sheet_name='PUTAWAY LIST', index=False)
                    df_kurang.to_excel(writer, sheet_name='REKAP KURANG SETUP', index=False)
                    df_sum.to_excel(writer, sheet_name='SUMMARY PUTAWAY', index=False)
                    df_lt3.to_excel(writer, sheet_name='STAGGING LT.3 OUTSTANDING', index=False)
                    df_updated_bin.to_excel(writer, sheet_name='UPDATED ASAL BIN', index=False)
                
                st.download_button("📥 DOWNLOAD LAPORAN PUTAWAY", data=output.getvalue(), file_name="REPORT_PUTAWAY_SYSTEM.xlsx")
                
            except Exception as e:
                st.error(f"Gagal memproses: {e}")

# (SISA KODE MENU LAINNYA TETAP SAMA SEPERTI ASLINYA)
elif menu == "📊 Dashboard Overview":
    st.markdown('<div class="hero-header"><h1>📊 DASHBOARD ANALYTICS</h1></div>', unsafe_allow_html=True)
    c1, c2 = st.columns([3, 1])
    with c1: pilih = st.selectbox("PILIH LAPORAN", ["WORKING REPORT", "PERSONAL PERFORMANCE", "CYCLE COUNT DAN KERAPIHAN", "DASHBOARD MOVING STOCK"])
    with c2: zoom = st.slider("ZOOM", 0.1, 1.0, 0.35)
    dash_links = {"WORKING REPORT": "864743695", "PERSONAL PERFORMANCE": "251294539", "CYCLE COUNT DAN KERAPIHAN": "1743896821", "DASHBOARD MOVING STOCK": "1671817510"}
    st.markdown(f'''<div class="dash-container"><div style="width: 100%; height: 500px; overflow: auto;"><iframe src="https://docs.google.com/spreadsheets/d/e/2PACX-1vRIMd-eghecjZKcOmhz0TW4f-1cG0LOWgD6X9mIK1XhiYSOx-V6xSnZQzBLfru0LhCIinIZAfbYnHv_/pubhtml?gid={dash_links[pilih]}&single=true&rm=minimal" style="width: 4000px; height: 1500px; border: none; transform: scale({zoom}); transform-origin: 0 0;"></iframe></div></div>''', unsafe_allow_html=True)

elif menu == "📤 Scan Out":
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
                    df_res.to_excel(writer, sheet_name='DATA SCAN', index=False)
                    df_draft.to_excel(writer, sheet_name='DRAFT SET UP', index=False)
                st.download_button("📥 DOWNLOAD HASIL SCAN OUT", data=output.getvalue(), file_name="HASIL_SCAN_OUT.xlsx")
            except Exception as e: st.error(f"Error: {e}")

elif menu == "📝 Dashboard Database":
    st.title("📓 Check Detail Dashboard")
    raw_url = st.text_input("MASUKKAN LINK GOOGLE SPREADSHEET LO:", placeholder="https://docs.google.com/spreadsheets/d/ID_FILE/edit...")
    if raw_url:
        try:
            if "/d/" in raw_url:
                file_id = raw_url.split("/d/")[1].split("/")[0]
                xlsx_url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
                all_sheets = pd.read_excel(xlsx_url, sheet_name=None, engine='calamine')
                selected_sheet = st.selectbox("PILIH TAB / SHEET:", list(all_sheets.keys()))
                if selected_sheet:
                    df_raw = pd.read_excel(xlsx_url, sheet_name=selected_sheet, header=None, engine='calamine')
                    header_row = 0
                    for i, row in df_raw.head(20).iterrows():
                        if any(x in row.astype(str).str.upper().tolist() for x in ["NAME", "DATE", "TANGGAL", "AVERAGE", "TOTAL"]):
                            header_row = i; break
                    df_master = pd.read_excel(xlsx_url, sheet_name=selected_sheet, header=header_row, engine='calamine')
                    cols = pd.Series(df_master.columns)
                    for dup in cols[cols.duplicated()].unique(): cols[cols == dup] = [f"{dup}_{idx}" if idx != 0 else dup for idx in range(sum(cols == dup))]
                    df_master.columns = cols
                    for col in df_master.columns:
                        col_name = str(col).upper()
                        if any(x in col_name for x in ["DATE", "TANGGAL", "MONTH"]): df_master[col] = pd.to_datetime(df_master[col], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')
                        elif any(x in col_name for x in ["TIME", "AVERAGE", "MOVE", "QC", "PACK"]): 
                            df_master[col] = df_master[col].astype(str).str.split().str[-1].replace(['nan', 'None', 'NaT'], '')
                    df_master = df_master.loc[:, ~df_master.columns.astype(str).str.contains('^Unnamed')].dropna(how='all').reset_index(drop=True)
                    st.markdown(f"### 📊 Summary: {selected_sheet}")
                    c1, c2, c3, c4 = st.columns(4)
                    with c1: st.markdown(f'<div class="m-box"><span class="m-lbl">TOTAL BARIS</span><span class="m-val">{len(df_master)}</span></div>', unsafe_allow_html=True)
                    with c2: st.markdown(f'<div class="m-box"><span class="m-lbl">TOTAL KOLOM</span><span class="m-val">{len(df_master.columns)}</span></div>', unsafe_allow_html=True)
                    with c3: st.markdown(f'<div class="m-box"><span class="m-lbl">STATUS</span><span class="m-val">CONNECTED</span></div>', unsafe_allow_html=True)
                    with c4: st.markdown(f'<div class="m-box"><span class="m-lbl">ENGINE</span><span class="m-val">CALAMINE</span></div>', unsafe_allow_html=True)
                    st.divider(); st.subheader(f"📑 Table View: {selected_sheet}")
                    search = st.text_input(f"Cari data di sini...")
                    if search:
                        mask = df_master.apply(lambda row: row.astype(str).str.contains(search, case=False).any(), axis=1)
                        st.dataframe(df_master[mask], use_container_width=True, height=500)
                    else: st.dataframe(df_master, use_container_width=True, height=500)
        except Exception as e: st.error(f"Error: {e}")

elif menu == "⛔ Stock Minus":
    st.markdown('<div class="hero-header"><h1>⛔ STOCK MINUS CLEARANCE</h1></div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload File dari Jezpro", type=["xlsx", "xlsm"])
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file, engine="calamine")
        col_sku, col_bin = 'SKU', 'BIN'; col_qty = next((c for c in df.columns if 'QTY SYS' in str(c).upper()), 'QTY SYSTEM')
        if st.button("🔃 PROSES DATA"):
            with st.spinner('Sedang memproses...'):
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
                    sku_target = sku_arr[idx]; qty_needed = abs(qty_arr[idx]); bin_tujuan = bin_arr[idx].upper()
                    if sku_target in pos_map:
                        sku_bins = pos_map[sku_target]
                        while qty_needed > 0:
                            found_idx = -1
                            if bin_tujuan == "TOKO":
                                for b_name, indices in sku_bins.items():
                                    if ("LT.2" in b_name or "GL2-STORE" in b_name):
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
                df_final_state = df.copy(); df_final_state[col_qty] = qty_arr; df_need_adj = df_final_state[df_final_state[col_qty] < 0].copy()
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_minus_awal.to_excel(writer, sheet_name='STOCK MINUS AWAL', index=False)
                    if set_up_results: pd.DataFrame(set_up_results).to_excel(writer, sheet_name='SET UP STOCK MINUS', index=False)
                    if not df_need_adj.empty: df_need_adj.to_excel(writer, sheet_name='NEED JUSTIFIKASI', index=False)
                st.success(f"✅ Done! {len(set_up_results)} item direlokasi."); st.download_button("📥 DOWNLOAD HASIL LENGKAP", data=output.getvalue(), file_name="PENYELESAIAN_STOCK_MINUS.xlsx")