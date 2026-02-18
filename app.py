import pandas as pd
import numpy as np
import io
import streamlit as st
import xlsxwriter
from python_calamine import CalamineWorkbook

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="ERP Surabaya - Pro", layout="wide")

# 2. CUSTOM CSS
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #31333f; }
    [data-testid="stSidebar"] { background-color: #1e1e2f !important; }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: white !important; }
    .m-box { 
        background-color: #1e1e2f !important; 
        border: 2px solid #3b82f6 !important;
        border-left: 12px solid #FFD700 !important;
        padding: 25px !important; 
        border-radius: 15px !important; 
        text-align: center !important; 
        margin-bottom: 15px !important;
    }
    .m-val { font-size: 32px !important; font-weight: 800 !important; color: #FFD700 !important; display: block !important; }
    .m-lbl { font-size: 14px !important; color: #ffffff !important; text-transform: uppercase !important; font-weight: 700 !important; }
    .hero-header {
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        color: white; padding: 1.5rem 2rem;
        border-bottom: 5px solid #FFD700; border-radius: 15px; margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. FUNGSI LOGIKA
def process_putaway(df_ds, df_asal):
    df_asal_working = df_asal.copy()
    results_compare, putaway_list, rekap_kurang = [], [], []
    for _, row_ds in df_ds.iterrows():
        bin_asal_ds = str(row_ds.iloc[0]).strip()
        sku_ds = str(row_ds.iloc[1]).strip()
        diff_qty = int(row_ds.iloc[2])
        qty_awal_request = diff_qty
        while diff_qty > 0:
            allocated = False
            for prio in ["LT3", "STAGING_GEN", "NORMAL"]:
                for idx, row_bin in df_asal_working.iterrows():
                    b_code = str(row_bin.iloc[1]).strip().upper()
                    s_code = str(row_bin.iloc[2]).strip()
                    q_sys = int(row_bin.iloc[9])
                    if s_code == sku_ds and q_sys > 0:
                        match = False
                        if prio == "LT3" and ("STAGGING LT.3" in b_code or "STAGING LT.3" in b_code): match = True
                        elif prio == "STAGING_GEN" and any(x in b_code for x in ["STAGING", "STAGGING", "KARANTINA"]) and "LT.3" not in b_code: match = True
                        elif prio == "NORMAL" and not any(x in b_code for x in ["STAGING", "STAGGING", "KARANTINA"]): match = True
                        if match:
                            take = min(q_sys, diff_qty)
                            df_asal_working.iat[idx, 9] -= take
                            putaway_list.append({"BIN AWAL": b_code, "BIN TUJUAN": bin_asal_ds, "SKU": sku_ds, "QUANTITY": take, "NOTES": "PUTAWAY"})
                            results_compare.append({"BIN ASAL": bin_asal_ds, "SKU": sku_ds, "QTY PUTAWAY": qty_awal_request, "BIN DITEMUKAN": b_code, "QTY SYSTEM": take, "NOTE": "SETUP DONE"})
                            diff_qty -= take; allocated = True; break
                if allocated: break
            if not allocated:
                results_compare.append({"BIN ASAL": bin_asal_ds, "SKU": sku_ds, "QTY PUTAWAY": qty_awal_request, "BIN DITEMUKAN": "(NO BIN)", "QTY SYSTEM": 0, "NOTE": "CARI MANUAL"})
                rekap_kurang.append({"BIN": bin_asal_ds, "SKU": sku_ds, "QTY": diff_qty})
                break
    return pd.DataFrame(results_compare), pd.DataFrame(putaway_list), pd.DataFrame(rekap_kurang), df_asal_working

def process_scan_out(df_scan, df_history, df_stock):
    df_scan['BIN_CLEAN'] = df_scan.iloc[:, 0].astype(str).str.strip()
    df_scan['SKU_CLEAN'] = df_scan.iloc[:, 1].astype(str).str.strip()
    df_scan_clean = df_scan.groupby(['BIN_CLEAN', 'SKU_CLEAN']).size().reset_index(name='QTY')
    results, draft_setup = [], []
    for _, row in df_scan_clean.iterrows():
        sku, bin_scan, qty = row['SKU_CLEAN'], row['BIN_CLEAN'], row['QTY']
        match_stock = df_stock[(df_stock.iloc[:, 1].astype(str).str.strip() == sku) & (df_stock.iloc[:, 6].astype(str).str.strip() == bin_scan)]
        if not match_stock.empty:
            results.append({"BIN": bin_scan, "SKU": sku, "QTY": qty, "Keterangan": "ITEM TELAH TERJUAL"})
        else:
            draft_setup.append({"BIN AWAL": bin_scan, "BIN TUJUAN": "KARANTINA", "SKU": sku, "QUANTITY": qty, "NOTES": "WAITING OFFLINE"})
            results.append({"BIN": bin_scan, "SKU": sku, "QTY": qty, "Keterangan": "BELUM TERSETUP"})
    return pd.DataFrame(results), pd.DataFrame(draft_setup)

# 4. SIDEBAR
with st.sidebar:
    st.markdown("<h2 style='color: white;'>🚀 ERP LOGISTIK SURABAYA</h2>", unsafe_allow_html=True)
    st.divider()
    menu = st.radio("MODUL UTAMA", ["📊 Dashboard Overview", "📥 Putaway System", "📤 Scan Out", "📝 Dashboard Database", "⛔ Stock Minus"])

# 5. MAIN CONTENT
if menu == "📊 Dashboard Overview":
    st.markdown('<div class="hero-header"><h1>📊 DASHBOARD ANALYTICS</h1></div>', unsafe_allow_html=True)
    c1, c2 = st.columns([3, 1])
    with c1:
        pilih = st.selectbox("PILIH LAPORAN", ["WORKING REPORT", "PERSONAL PERFORMANCE", "CYCLE COUNT DAN KERAPIHAN", "DASHBOARD MOVING STOCK"])
    with c2: zoom = st.slider("ZOOM", 0.1, 1.0, 0.35)
    dash_links = {"WORKING REPORT": "864743695", "PERSONAL PERFORMANCE": "251294539", "CYCLE COUNT DAN KERAPIHAN": "1743896821", "DASHBOARD MOVING STOCK": "1671817510"}
    gid = dash_links[pilih]
    st.markdown(f'''<div class="dash-container"><div style="width: 100%; height: 500px; overflow: auto;"><iframe src="https://docs.google.com/spreadsheets/d/e/2PACX-1vRIMd-eghecjZKcOmhz0TW4f-1cG0LOWgD6X9mIK1XhiYSOx-V6xSnZQzBLfru0LhCIinIZAfbYnHv_/pubhtml?gid={gid}&single=true&rm=minimal" style="width: 4000px; height: 1500px; border: none; transform: scale({zoom}); transform-origin: 0 0;"></iframe></div></div>''', unsafe_allow_html=True)

elif menu == "📥 Putaway System":
    st.markdown('<div class="hero-header"><h1>📥 PUTAWAY SYSTEM</h1></div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    up_ds = c1.file_uploader("Upload DS PUTAWAY", type=['xlsx'])
    up_asal = c2.file_uploader("Upload ASAL BIN", type=['xlsx'])
    if up_ds and up_asal and st.button("⚡ JALANKAN"):
        res_comp, res_list, res_kurang, df_upd = process_putaway(pd.read_excel(up_ds, engine='calamine'), pd.read_excel(up_asal, engine='calamine'))
        st.success("Selesai!")
        st.dataframe(res_list, use_container_width=True)

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
                df_h = pd.read_excel(up_hist, engine='calamine')
                df_st = pd.read_excel(up_stock, engine='calamine')
                df_res, df_draft = process_scan_out(df_s, df_h, df_st)
                st.success("Validasi Selesai!")
                st.subheader("📋 DATA SCAN (COMPARED)")
                st.dataframe(df_res, use_container_width=True)
                st.subheader("📝 DRAFT SET UP")
                st.dataframe(df_draft, use_container_width=True)
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_res.to_excel(writer, sheet_name='DATA SCAN', index=False)
                    df_draft.to_excel(writer, sheet_name='DRAFT SET UP', index=False)
                st.download_button("📥 DOWNLOAD HASIL SCAN OUT", data=output.getvalue(), file_name="HASIL_SCAN_OUT.xlsx")
            except Exception as e:
                st.error(f"Error: {e}")

elif menu == "📝 Dashboard Database":
    st.title("📓 Check Detail Dashboard")
    raw_url = st.text_input("MASUKKAN LINK GOOGLE SPREADSHEET LO:")
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
                        row_str = row.astype(str).str.upper().tolist()
                        if any(x in ["NAME", "DATE", "TANGGAL", "AVERAGE", "TOTAL"] for x in row_str):
                            header_row = i
                            break
                    df_master = pd.read_excel(xlsx_url, sheet_name=selected_sheet, header=header_row, engine='calamine')
                    st.dataframe(df_master, use_container_width=True)
        except Exception as e:
            st.error(f"Error: {e}")

elif menu == "⛔ Stock Minus":
    st.markdown('<div class="hero-header"><h1>⛔ STOCK MINUS CLEARANCE</h1></div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload File dari Jezpro", type=["xlsx", "xlsm"])
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file, engine="calamine")
        col_sku, col_bin = 'SKU', 'BIN'
        col_qty = next((c for c in df.columns if 'QTY SYS' in str(c).upper()), 'QTY SYSTEM')
        if st.button("🔃 PROSES DATA"):
            with st.spinner('Sedang memproses...'):
                df_minus_awal = df[df[col_qty] < 0].copy()
                qty_arr = pd.to_numeric(df[col_qty], errors='coerce').fillna(0).values
                sku_arr, bin_arr = df[col_sku].astype(str).values, df[col_bin].astype(str).values
                prior_bins = ["RAK ACC LT.1", "STAGGING INBOUND", "STAGGING OUTBOUND", "KARANTINA DC", 
                              "KARANTINA STORE 02", "STAGGING REFUND", "STAGING GAGAL QC", "STAGGING LT.3", 
                              "STAGGING OUTBOUND SEMARANG", "STAGGING OUTBOUND SIDOARJO", "STAGGING LT.2", "LT.4"]
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
                                take = min(qty_needed, qty_arr[found_idx])
                                qty_arr[found_idx] -= take
                                qty_arr[idx] += take
                                set_up_results.append({"BIN AWAL": bin_arr[found_idx], "BIN TUJUAN": bin_arr[idx], "SKU": sku_target, "QUANTITY": take, "NOTES": "STOCK MINUS"})
                                qty_needed -= take
                            else: break
                st.success("Proses Selesai")
                if set_up_results:
                    st.dataframe(pd.DataFrame(set_up_results), use_container_width=True)
                    