import pandas as pd
import numpy as np
import math
import io
import streamlit as st
import plotly.express as px
from python_calamine import CalamineWorkbook

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="ERP Surabaya - Adminity Pro", layout="wide")

# 2. THE AUTHENTIC ADMINITY UI ENGINE (PENGATURAN SPASI ATAS & SIDEBAR)
st.markdown("""
    <style>
    /* MENGHAPUS SPACE KOSONG DI ATAS SIDEBAR & BODY */
    .block-container { padding-top: 1rem !important; }
    [data-testid="stSidebarUserContent"] { padding-top: 0rem !important; }
    [data-testid="stSidebarNav"] { display: none; } 
    
    /* STYLE JUDUL ERP (PAKSA NAIK KE ATAS) */
    .sidebar-title { 
        color: #00d2ff; 
        text-align: center; 
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        font-size: 20px;
        margin-top: -45px; /* Menarik judul ke paling atas */
        padding-bottom: 15px;
        border-bottom: 1px solid #2d2d44;
        margin-bottom: 10px;
    }

    /* STYLE MENU & HEADER */
    .stApp { background-color: #f4f7f6; }
    [data-testid="stSidebar"] { background-color: #1e1e2f !important; border-right: 1px solid #2d2d44; }
    
    .nav-header { 
        font-size: 11px; 
        text-transform: uppercase; 
        letter-spacing: 2px; 
        color: #6c757d; 
        padding: 15px 0 5px 10px; 
        font-weight: 700; 
    }
    
    .hero-header { 
        background: linear-gradient(135deg, #3a7bd5 0%, #00d2ff 100%); 
        color: white; 
        padding: 1.5rem; 
        border-radius: 12px; 
        box-shadow: 0 4px 20px rgba(0,0,0,0.08); 
        margin-bottom: 25px; 
    }

    /* Metric Box */
    .m-box { background: #1e1e2f; padding: 15px; border-radius: 8px; border-left: 5px solid #ffce00; margin-bottom: 10px; text-align: center; }
    .m-lbl { color: #ffffff; font-size: 10px; font-weight: 700; text-transform: uppercase; display: block; }
    .m-val { color: #ffce00; font-size: 20px; font-weight: 800; }

    /* Radio Button styling */
    div.row-widget.stRadio > div { background-color: transparent !important; }
    div.row-widget.stRadio label { color: #d1d1d1 !important; font-size: 14px !important; padding: 8px 15px !important; border-radius: 5px; }
    div.row-widget.stRadio label:hover { background: rgba(255,255,255,0.05); color: white !important; } </style>
    """, unsafe_allow_html=True)

# --- FUNGSI LOGIKA ASLI (TETAP SAMA) ---
import pandas as pd
import numpy as np
import math

def process_refill_overstock(df_all_data, df_stock_tracking):
    # Inisialisasi sesuai Sheet di VBA
    df_gl3 = pd.DataFrame()
    df_gl4 = pd.DataFrame()
    df_refill_final = pd.DataFrame()
    df_overstock_final = pd.DataFrame()

    try:
        # --- SUB 1: FILTER_ALL_DATA_TO_GL3_GL4 (Plek Ketiplek VBA) ---
        # VBA: srcArr = Range("A2:K" & lastRow) -> A=0 sampai K=10
        srcArr = df_all_data.values
        outGL3 = []
        outGL4 = []

        for i in range(len(srcArr)):
            # VBA: binCode = UCase(srcArr(i, 2)) -> Kolom B (Indeks 1)
            # CATATAN: Kalo di Excel lo Location itu kolom G, ganti [i][1] jadi [i][6]
            binCode = str(srcArr[i][1]).upper() if not pd.isna(srcArr[i][1]) else ""

            # Logic GL3: InStr(binCode, "GL3") > 0 And InStr(binCode, "LIVE") = 0
            if "GL3" in binCode and "LIVE" not in binCode:
                outGL3.append(srcArr[i][:11]) # Ambil kolom A-K

            # Logic GL4: InStr(binCode, "GL4") > 0 And No Defect, Reject, Online, Rak
            if "GL4" in binCode and not any(x in binCode for x in ["DEFECT", "REJECT", "ONLINE", "RAK"]):
                outGL4.append(srcArr[i][:11])

        df_gl3 = pd.DataFrame(outGL3)
        df_gl4 = pd.DataFrame(outGL4)

        if df_gl3.empty and df_gl4.empty:
            return df_gl3, df_gl4, df_refill_final, df_overstock_final

        # --- SUB 2: FILTER STOCK TRACKING (DeleteRowsNotMatchingCriteria) ---
        # VBA: data(i, 1) = Col A, data(i, 7) = Col G
        st_data = df_stock_tracking.values
        st_result = []
        for i in range(len(st_data)):
            col_a = str(st_data[i][0]).upper() if not pd.isna(st_data[i][0]) else ""
            col_g = str(st_data[i][6]).upper() if not pd.isna(st_data[i][6]) else ""
            # VBA: InStr(1, data(i, 1), "INV") = 0 And InStr(1, data(i, 7), "DC") > 0
            if "INV" not in col_a and "DC" in col_g:
                st_result.append(st_data[i])
        
        df_st_filtered = pd.DataFrame(st_result)

     # --- SUB 3: CREATE REFILL SHEET (Logic VBA + Anti-LIVE) ---
        # SKU = Col C (Indeks 2), QTY = Col J (Indeks 9)
        dictGL3 = {}
        if not df_gl3.empty:
            for row in df_gl3.values:
                sku = str(row[2]).strip()
                qty = int(float(row[9])) if not pd.isna(row[9]) else 0
                dictGL3[sku] = dictGL3.get(sku, 0) + qty

        # SKU Target Refill (Qty < 3 di GL3 atau ga ada sama sekali)
        dictSKUs_Target = {}
        for sku, total_qty in dictGL3.items():
            if total_qty < 3: dictSKUs_Target[sku] = True
        
        if not df_gl4.empty:
            for row in df_gl4.values:
                sku_g4 = str(row[2]).strip()
                if sku_g4 not in dictGL3: dictSKUs_Target[sku_g4] = True

        refill_output = []
        if not df_gl4.empty:
            dataGL4 = df_gl4.values
            for sku in dictSKUs_Target.keys():
                q_gl3_val = dictGL3.get(sku, 0)
                sisaLoad = 12
                for i in range(len(dataGL4)):
                    # --- TAMBAHAN FILTER LIVE DISINI ---
                    bin_sumber = str(dataGL4[i][1]).upper() if not pd.isna(dataGL4[i][1]) else ""
                    if "LIVE" in bin_sumber: 
                        continue # Kalo ada kata LIVE, skip bin ini, cari bin lain
                    # ----------------------------------

                    if str(dataGL4[i][2]).strip() == sku:
                        q_g4 = int(float(dataGL4[i][9])) if not pd.isna(dataGL4[i][9]) else 0
                        if q_g4 > 0 and sisaLoad > 0:
                            take = min(q_g4, sisaLoad)
                            # BIN(1), SKU(2), BRAND(3), NAME(4), VAR(5), Q_BIN(9), LOAD, Q_GL3
                            refill_output.append([dataGL4[i][1], sku, dataGL4[i][3], dataGL4[i][4], dataGL4[i][5], q_g4, take, q_gl3_val])
                            sisaLoad -= take
                            if sisaLoad <= 0: break
        
        df_refill_final = pd.DataFrame(refill_output, columns=["BIN", "SKU", "BRAND", "ITEM NAME", "VARIANT", "QTY BIN AMBIL", "LOAD", "QTY GL3"])

        # --- SUB 4: CREATE OVERSTOCK SHEET (Logic VBA + Anti-RAK) ---
        # Stock Tracking: SKU = Col B (Indeks 1), Qty = Col K (Indeks 10)
        dictTrans = {}
        if not df_st_filtered.empty:
            for row in df_st_filtered.values:
                sku_st = str(row[1]).strip()
                qty_st = float(row[10]) if not pd.isna(row[10]) else 0
                dictTrans[sku_st] = dictTrans.get(sku_st, 0) + qty_st

        overstock_output = []
        if not df_gl3.empty:
            for row in df_gl3.values:
                # --- TAMBAHAN FILTER RAK DISINI ---
                bin_over = str(row[1]).upper() if not pd.isna(row[1]) else ""
                if "RAK" in bin_over:
                    continue # Kalo ada kata RAK, skip, jangan masukin ke list Overstock
                # ----------------------------------

                sku_g3 = str(row[2]).strip()
                qty_sys = int(float(row[9]))
                if qty_sys > 24:
                    load_os = qty_sys - 24
                    if dictTrans.get(sku_g3, 0) >= 7:
                        load_os = math.ceil(load_os / 3)
                    if load_os > 0:
                        # Ambil data: BIN(1), SKU(2), BRAND(3), NAME(4), VAR(5), Q_SYS(9), LOAD
                        overstock_output.append([row[1], sku_g3, row[3], row[4], row[5], qty_sys, load_os])

        df_overstock_final = pd.DataFrame(overstock_output, columns=["BIN", "SKU", "BRAND", "ITEM NAME", "VARIANT", "QTY BIN AMBIL", "LOAD"])

    except Exception as e:
        print(f"Error: {e}")

    return df_gl3, df_gl4, df_refill_final, df_overstock_final


with st.sidebar:
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@800&display=swap');
        
        .elegant-header {
            font-family: 'Inter', sans-serif;
            color: #E2E8F0;
            text-align: left;
            margin-top: -70px;
            font-size: 22px;
            font-weight: 800;
            letter-spacing: -0.5px;
            background: linear-gradient(90deg, #FFFFFF 0%, #94A3B8 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            padding-bottom: 10px;
        }

        section[data-testid="stSidebar"] label p,
        section[data-testid="stSidebar"] .stCaption p {
            color: #E2E8F0;
            font-family: 'Inter', sans-serif;
            font-size: 13px;
            opacity: 1 !important;
            background: linear-gradient(90deg, #FFFFFF 0%, #94A3B8 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        /* FIX 1: INPUT & DROPDOWN */
        div[data-baseweb="input"], div[data-baseweb="select"] > div {
            background-color: #1a2634 !important;
            border: 1px solid #C5A059 !important;
            border-radius: 8px !important;
        } 

        input {
            color: #FFFFFF !important;
        }

        /* FIX 2: LABEL DI ATAS BOX JADI PUTIH (Gue benerin typo ## jadi #) */
        div[data-testid="stWidgetLabel"] p, label {
            color: #FFFFFF !important;
            -webkit-text-fill-color: #FFFFFF !important;
            font-family: 'Inter', sans-serif;
            font-weight: bold !important;
        }

        div[data-baseweb="input"]:focus-within, div[data-baseweb="select"]:focus-within {
            border: 1px solid #FFD700 !important;
            box-shadow: 0 0 10px rgba(197, 160, 89, 0.4) !important;
        }

        /* 4. FILE UPLOADER - PAKSA BORDER EMAS MUNCUL */
        /* Kita pasang di kontainer paling luar biar pasti kelihatan */
        [data-testid="stFileUploader"] {
            border: 2px dashed #C5A059 !important;
            border-radius: 12px !important;
            padding: 8px !important;
            background-color: #1a2634 !important;
        }

        /* Hilangkan border bawaan dalemnya biar gak double */
        [data-testid="stFileUploaderSection"] {
            border: none !important;
            background-color: transparent !important;
        }

        [data-testid="stFileUploaderText"] > span,
        [data-testid="stFileUploaderText"] > small {
            color: #FFFFFF !important;
            -webkit-text-fill-color: #FFFFFF !important;
        }

        [data-testid="stFileUploader"] button {
            background-color: #C5A059 !important;
            color: #1a2634 !important;
            border-radius: 5px !important;
            font-weight: bold !important;
            border: none !important;
            padding: 5px 15px !important;
        }

        [data-testid="stFileUploader"] button:hover {
            background-color: #FFD700 !important;
            box-shadow: 0 0 10px rgba(197, 160, 89, 0.4) !important;
        }

        [data-testid="stFileUploader"] svg {
            fill: #C5A059 !important;
        }
    </style>
    <div class="elegant-header">
        🚚 ERP LOGISTIC<br>SURABAYA
    </div>
""", unsafe_allow_html=True)
    
    # Inisialisasi session state agar menu tersinkron
    if 'main_menu' not in st.session_state:
        st.session_state.main_menu = "Dashboard Overview"

    # --- KELOMPOK 1: DASHBOARD SUMMARY ---
    st.markdown('<p style="font-weight: bold; color: #808495; margin-top: 10px; margin-bottom: -5px;">MAIN MENU</p>', unsafe_allow_html=True)
    st.markdown('<p style="font-weight: bold; color: #808495; margin-bottom: 5px;">DASHBOARD SUMMARY</p>', unsafe_allow_html=True)
    
    m1_list = ["Dashboard Overview", "Database Master"]
    
    # Cek apakah pilihan sekarang ada di kelompok 1
    def change_m1():
        st.session_state.main_menu = st.session_state.m1_key

    # Jika menu yang terpilih ada di Kelompok 2, maka radio ini kita "kosongkan" secara visual (atau pilih default)
    idx1 = m1_list.index(st.session_state.main_menu) if st.session_state.main_menu in m1_list else 0
    
    menu_1 = st.radio("M1", m1_list, index=idx1, key="m1_key", on_change=change_m1, label_visibility="collapsed")

    # --- KELOMPOK 2: OPERATIONAL ---
    st.markdown('<p style="font-weight: bold; color: #808495; margin-top: 25px; margin-bottom: 5px;">OPERATIONAL</p>', unsafe_allow_html=True)
    
    m2_list = ["Putaway System", "Scan Out Validation", "Refill & Overstock", "Stock Minus"]
    
    def change_m2():
        st.session_state.main_menu = st.session_state.m2_key

    # Jika menu yang terpilih ada di Kelompok 2, arahkan indexnya. Jika tidak, biarkan di posisi default tapi jangan bentrok
    idx2 = m2_list.index(st.session_state.main_menu) if st.session_state.main_menu in m2_list else 0
    
    menu_2 = st.radio("M2", m2_list, index=idx2, key="m2_key", on_change=change_m2, label_visibility="collapsed")

    # Final Menu Variable untuk dipakai di konten utama
    menu = st.session_state.main_menu

    st.divider()
    st.caption("ERP Logistic Surabaya v2.1")

# --- MENU ROUTING ---
if menu == "Dashboard Overview":
    st.markdown('<div class="hero-header"><h1>DASHBOARD ANALYTICS</h1></div>', unsafe_allow_html=True)
    c1, c2 = st.columns([3, 1])
    with c1: pilih = st.selectbox("PILIH LAPORAN", ["WORKING REPORT", "PERSONAL PERFORMANCE", "CYCLE COUNT DAN KERAPIHAN", "DASHBOARD MOVING STOCK"])
    with c2: zoom = st.slider("ZOOM", 0.1, 1.0, 0.35)
    dash_links = {"WORKING REPORT": "864743695", "PERSONAL PERFORMANCE": "251294539", "CYCLE COUNT DAN KERAPIHAN": "1743896821", "DASHBOARD MOVING STOCK": "1671817510"}
    st.markdown(f'''<div style="background: white; border-radius: 15px; padding: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);"><div style="width: 100%; height: 600px; overflow: auto;"><iframe src="https://docs.google.com/spreadsheets/d/e/2PACX-1vRIMd-eghecjZKcOmhz0TW4f-1cG0LOWgD6X9mIK1XhiYSOx-V6xSnZQzBLfru0LhCIinIZAfbYnHv_/pubhtml?gid={dash_links[pilih]}&single=true&rm=minimal" style="width: 4000px; height: 1500px; border: none; transform: scale({zoom}); transform-origin: 0 0;"></iframe></div></div>''', unsafe_allow_html=True)

elif menu == "Putaway System":
    st.markdown('<div class="hero-header"><h1>PUTAWAY SYSTEM COMPARATION</h1></div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1: up_ds = st.file_uploader("Upload DS PUTAWAY", type=['xlsx', 'csv'])
    with c2: up_asal = st.file_uploader("Upload ASAL BIN PUTAWAY", type=['xlsx', 'csv'])
    if up_ds and up_asal:
        if st.button("⚡COMPARE PUTAWAY"):
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

elif menu == "Scan Out Validation":
    st.markdown('<div class="hero-header"><h1> COMPARE AND ANLYZE ITEM SCAN OUT</h1></div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1: up_scan = st.file_uploader("Upload DATA SCAN", type=['xlsx', 'csv'])
    with col2: up_hist = st.file_uploader("Upload HISTORY SET UP", type=['xlsx'])
    with col3: up_stock = st.file_uploader("Upload STOCK TRACKING", type=['xlsx'])
    if up_scan and up_hist and up_stock:
        if st.button("🚀 COMPARE DATA SCAN OUT"):
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

elif menu == "Refill & Overstock":
    st.markdown('<div class="hero-header"><h1>REFILL & OVERSTOCK SYSTEM</h1></div>', unsafe_allow_html=True)
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

elif menu == "Database Master":
    # Link Google Sheets lo yang sudah dikunci
    SHEET_URL = "https://docs.google.com/spreadsheets/d/1tuGnu7jKvRkw9MmF92U-5pOoXjUOeTMoL3EvrOzcrQY/edit?usp=sharing"
    
    st.markdown('<div class="hero-header"><h1>DATABASE MASTER CHECKER</h1><p>Koneksi Otomatis ke Master Data ERP</p></div>', unsafe_allow_html=True)
    
    try:
        # Ekstrak File ID secara otomatis dari link
        file_id = "1tuGnu7jKvRkw9MmF92U-5pOoXjUOeTMoL3EvrOzcrQY"
        xlsx_url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
        
        with st.spinner("Sedang mengambil data terbaru..."):
            # Baca semua sheet (tab) yang ada
            all_sheets = pd.read_excel(xlsx_url, sheet_name=None, engine='calamine')
            
            # Pilihan Tab/Sheet
            tab_names = list(all_sheets.keys())
            c_select, c_empty = st.columns([1, 2])
            with c_select:
                selected_sheet = st.selectbox("PILIH TAB DATA:", tab_names)
            
            if selected_sheet:
                df_master = all_sheets[selected_sheet]
                
                # Baris metrik informasi data
                c1, c2, c3, c4 = st.columns(4)
                with c1: st.markdown(f'<div class="m-box"><span class="m-lbl">TOTAL BARIS</span><span class="m-val">{len(df_master)}</span></div>', unsafe_allow_html=True)
                with c2: st.markdown(f'<div class="m-box"><span class="m-lbl">TOTAL KOLOM</span><span class="m-val">{len(df_master.columns)}</span></div>', unsafe_allow_html=True)
                with c3: st.markdown(f'<div class="m-box"><span class="m-lbl">STATUS</span><span class="m-val">CONNECTED</span></div>', unsafe_allow_html=True)
                with c4: st.markdown(f'<div class="m-box"><span class="m-lbl">SOURCE</span><span class="m-val">G-SHEET</span></div>', unsafe_allow_html=True)
                
                # Tampilkan tabel data
                st.dataframe(df_master, use_container_width=True, height=600)
                
                # Tombol Download kalau sewaktu-waktu butuh offline
                csv = df_master.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 DOWNLOAD TAB INI (.CSV)",
                    data=csv,
                    file_name=f"Master_{selected_sheet}.csv",
                    mime='text/csv',
                )

    except Exception as e:
        st.error(f"⚠️ Gagal terhubung ke Google Sheets. Pastikan aksesnya sudah 'Anyone with the link'. Error: {e}")
elif menu == "Stock Minus":
    st.markdown('<div class="hero-header"><h1>STOCK MINUS CLEARANCE</h1></div>', unsafe_allow_html=True)
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