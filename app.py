import pandas as pd
import numpy as np
import io
import streamlit as st
import plotly.express as px
from python_calamine import CalamineWorkbook

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="ERP Surabaya - Pro", layout="wide")

# 2. CUSTOM CSS GLOBAL
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }
    [data-testid="stSidebar"] { background-color: #1e1e2f !important; }
    header[data-testid="stHeader"] { background-color: rgba(30, 30, 47, 0.85) !important; backdrop-filter: blur(12px); border-bottom: 2px solid #FFD700; }
    
    /* Style Header Biru Dashboard */
    .hero-header {
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        color: white; padding: 1.5rem 2rem;
        border-bottom: 4px solid #FFD700;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
        border-radius: 0 0 15px 15px;
        margin-bottom: 15px;
    }
    .hero-header h1 { margin: 0; font-size: 24px; font-weight: 800; text-transform: uppercase; color: white !important; }
    
    .scroll-wrapper {
        width: 100%; height: 80vh; overflow: auto;
        background: #0e1117; border: 1px solid #3b82f6; border-radius: 10px;
    }
    .scroll-wrapper iframe { border: none; transform-origin: 0 0; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR (WAJIB DI ATAS AGAR VARIABEL 'MENU' TERDEFINISI) ---
with st.sidebar:
    st.markdown("<h2 style='color: white;'>🚀 ERP SURABAYA</h2>", unsafe_allow_html=True)
    st.divider()
    menu = st.radio("MODUL UTAMA", ["📊 Dashboard Overview", "⛔ Stock Minus", "📦 Database Artikel"])

# --- 4. LOGIKA MODUL ---

if menu == "📊 Dashboard Overview":
    st.markdown("""<div class="hero-header"><h1>📊 DASHBOARD ANALYTICS</h1><p>Warehouse Management System Surabaya</p></div>""", unsafe_allow_html=True)
    
    c1, c2 = st.columns([2, 1])
    with c1:
        pilih_dash = st.selectbox("PILIH LAPORAN", ["WORKING REPORT", "PERSONAL PERFOMANCE", "CYCLE COUNT DAN KERAPIHAN", "DASHBOARD MOVING STOCK"])
    with c2:
        zoom_val = st.slider("ZOOM", 0.10, 1.0, 0.35, 0.01)

    dash_links = {
        "WORKING REPORT": "https://docs.google.com/spreadsheets/d/e/2PACX-1vRIMd-eghecjZKcOmhz0TW4f-1cG0LOWgD6X9mIK1XhiYSOx-V6xSnZQzBLfru0LhCIinIZAfbYnHv_/pubhtml?gid=864743695&single=true",
        "PERSONAL PERFOMANCE": "https://docs.google.com/spreadsheets/d/e/2PACX-1vRIMd-eghecjZKcOmhz0TW4f-1cG0LOWgD6X9mIK1XhiYSOx-V6xSnZQzBLfru0LhCIinIZAfbYnHv_/pubhtml?gid=251294539&single=true",
        "CYCLE COUNT DAN KERAPIHAN": "https://docs.google.com/spreadsheets/d/e/2PACX-1vRIMd-eghecjZKcOmhz0TW4f-1cG0LOWgD6X9mIK1XhiYSOx-V6xSnZQzBLfru0LhCIinIZAfbYnHv_/pubhtml?gid=1743896821&single=true",
        "DASHBOARD MOVING STOCK": "https://docs.google.com/spreadsheets/d/e/2PACX-1vRIMd-eghecjZKcOmhz0TW4f-1cG0LOWgD6X9mIK1XhiYSOx-V6xSnZQzBLfru0LhCIinIZAfbYnHv_/pubhtml?gid=1671817510&single=true"
    }
    
    st.markdown(f'<div class="scroll-wrapper"><iframe src="{dash_links[pilih_dash]}&rm=minimal" style="width: 3500px; height: 2500px; transform: scale({zoom_val});"></iframe></div>', unsafe_allow_html=True)

elif menu == "⛔ Stock Minus":
    st.title("⛔ Stock Minus Clearance")
    uploaded_file = st.file_uploader("Upload File Jezpro", type=["xlsx", "xlsm"])
    # ... (Gunakan logic processing lo yang lama di sini, sudah aman)

elif menu == "📦 Database Artikel":
    st.title("📦 Google Sheets Sync")
    raw_url = st.text_input("LINK SPREADSHEET:")
    if raw_url and "/d/" in raw_url:
        try:
            file_id = raw_url.split("/d/")[1].split("/")[0]
            xlsx_url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
            all_sheets = pd.read_excel(xlsx_url, sheet_name=None, engine='calamine')
            sel_sheet = st.selectbox("PILIH TAB:", list(all_sheets.keys()))
            
            df_master = all_sheets[sel_sheet]
            # Fix format tanggal/waktu (Cleaning Minimalis)
            for col in df_master.columns:
                if any(x in str(col).upper() for x in ["DATE", "TANGGAL"]):
                    df_master[col] = pd.to_datetime(df_master[col], errors='coerce').dt.date
            
            st.dataframe(df_master, use_container_width=True)
        except Exception as e:
            st.error(f"Error: {e}")
# --- MODUL STOCK MINUS (FULL LOGIC BALIK!) ---
elif menu == "⛔ Stock Minus":
    st.title("⛔ Inventory : Stock Minus Clearance")
    uploaded_file = st.file_uploader("Upload File dari Jezpro", type=["xlsx", "xlsm"])

    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file, engine="calamine")
        col_sku, col_bin = 'SKU', 'BIN'
        col_qty = next((c for c in df.columns if 'QTY SYS' in str(c).upper()), 'QTY SYSTEM')

        if st.button("🚀 PROSES DATA SPEED DEMON"):
            with st.spinner('Sedang memproses...'):
                # 1. Backup Data Awal
                df_minus_awal = df[df[col_qty] < 0].copy()
                
                # 2. Setup Array (Speed Demon Logic)
                qty_arr = pd.to_numeric(df[col_qty], errors='coerce').fillna(0).values
                sku_arr, bin_arr = df[col_sku].astype(str).values, df[col_bin].astype(str).values
                
                # --- LOGIKA PRIORITAS BIN DARI MACRO ---
                prior_bins = ["RAK ACC LT.1", "STAGGING INBOUND", "STAGGING OUTBOUND", "KARANTINA DC", 
                              "KARANTINA STORE 02", "STAGGING REFUND", "STAGING GAGAL QC", "STAGGING LT.3", 
                              "STAGGING OUTBOUND SEMARANG", "STAGGING OUTBOUND SIDOARJO", "STAGGING LT.2", "LT.4"]

                # 3. Mapping posisi stok positif
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
                
                # 4. Proses Relokasi
                for idx in minus_indices:
                    sku_target = sku_arr[idx]
                    qty_needed = abs(qty_arr[idx])
                    bin_tujuan = bin_arr[idx].upper()
                    
                    if sku_target in pos_map:
                        sku_bins = pos_map[sku_target]
                        
                        while qty_needed > 0:
                            found_idx = -1
                            
                            # CROSS-CHECK: TOKO vs AREA LT.2/GL2-STORE
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

                            # JALANKAN PRIORITAS BIN
                            if found_idx == -1:
                                for pb in prior_bins:
                                    if pb in sku_bins:
                                        for p_idx in sku_bins[pb]:
                                            if qty_arr[p_idx] > 0: found_idx = p_idx; break
                                    if found_idx != -1: break

                            # CARI BIN LAIN (KECUALI REJECT)
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
                                set_up_results.append({
                                    "BIN AWAL": bin_arr[found_idx], "BIN TUJUAN": bin_arr[idx],
                                    "SKU": sku_target, "QUANTITY": take, "NOTES": "STOCK MINUS"
                                })
                                qty_needed -= take
                            else:
                                break

                # 5. LOGIC NEED JUSTIFIKASI
                df_final_state = df.copy()
                df_final_state[col_qty] = qty_arr
                df_need_adj = df_final_state[df_final_state[col_qty] < 0].copy()

                # 6. Export ke Excel Multi-Sheet
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_minus_awal.to_excel(writer, sheet_name='STOCK MINUS AWAL', index=False)
                    if set_up_results:
                        pd.DataFrame(set_up_results).to_excel(writer, sheet_name='SET UP STOCK MINUS', index=False)
                    if not df_need_adj.empty:
                        df_need_adj.to_excel(writer, sheet_name='NEED JUSTIFIKASI', index=False)

                st.success(f"✅ Kelar! {len(set_up_results)} item direlokasi. {len(df_need_adj)} SKU butuh justifikasi.")
                st.download_button("📥 DOWNLOAD HASIL LENGKAP", data=output.getvalue(), file_name="PENYELESAIAN_STOCK_MINUS.xlsx")

# --- MODUL DATABASE ARTIKEL (FIX HEADER HILANG & FORMAT WAKTU) ---
elif menu == "📦 Database Artikel":
    st.title("📦 Master Database : Google Sheets Sync")
    
    raw_url = st.text_input("MASUKKAN LINK GOOGLE SPREADSHEET LO:", 
                             placeholder="https://docs.google.com/spreadsheets/d/ID_FILE/edit...")
    
    if raw_url:
        try:
            if "/d/" in raw_url:
                file_id = raw_url.split("/d/")[1].split("/")[0]
                xlsx_url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
                
                # Tarik semua sheet pake calamine
                all_sheets = pd.read_excel(xlsx_url, sheet_name=None, engine='calamine')
                sheet_names = list(all_sheets.keys())
                selected_sheet = st.selectbox("PILIH TAB / SHEET:", sheet_names)
                
                if selected_sheet:
                    # 1. Tarik mentah total tanpa header biar kita filter manual
                    df_raw = pd.read_excel(xlsx_url, sheet_name=selected_sheet, header=None, engine='calamine')
                    
                    # 2. CARI HEADER ASLI: Kita cari baris yang isinya 'NAME', 'DATE', atau 'TOTAL'
                    # Ini buat nendang baris sampah kayak "GALIH PAMUNGKAS" ke bawah
                    header_row = 0
                    for i, row in df_raw.head(20).iterrows():
                        row_str = row.astype(str).str.upper().tolist()
                        if any(x in ["NAME", "DATE", "TANGGAL", "AVERAGE", "TOTAL"] for x in row_str):
                            header_row = i
                            break
                    
                    # 3. Reload dengan baris header yang bener
                    df_master = pd.read_excel(xlsx_url, sheet_name=selected_sheet, 
                                             header=header_row, engine='calamine')

                    # 4. FIX DUPLICATE COLUMNS
                    cols = pd.Series(df_master.columns)
                    for dup in cols[cols.duplicated()].unique(): 
                        cols[cols == dup] = [f"{dup}_{idx}" if idx != 0 else dup for idx in range(sum(cols == dup))]
                    df_master.columns = cols

                    # 5. BERSIHIN FORMAT TANGGAL & WAKTU ANEH
                    for col in df_master.columns:
                        col_name = str(col).upper()
                        
                        # Bersihin Tanggal & Jam (Pake Indentasi yang bener)
                        if any(x in col_name for x in ["DATE", "TANGGAL", "MONTH"]):
                            # Baris ini harus menjorok ke dalam (4 spasi dari 'if')
                            df_master[col] = pd.to_datetime(df_master[col], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')
                        
                        # Bersihin Waktu (Sejajarin 'elif' dengan 'if')
                        elif any(x in col_name for x in ["TIME", "AVERAGE", "MOVE", "QC", "PACK"]):
                            df_master[col] = df_master[col].astype(str).str.split().str[-1]
                            df_master[col] = df_master[col].replace(['nan', 'None', 'NaT'], '')

                    # 6. Buang kolom 'Unnamed' dan baris kosong
                    df_master = df_master.loc[:, ~df_master.columns.astype(str).str.contains('^Unnamed')]
                    df_master = df_master.dropna(how='all').reset_index(drop=True)

                    # --- SUMMARY BOX ---
                    st.markdown(f"### 📊 Summary: {selected_sheet}")
                    c1, c2, c3, c4 = st.columns(4)
                    with c1: st.markdown(f'<div class="m-box"><span class="m-lbl">TOTAL BARIS</span><span class="m-val">{len(df_master)}</span></div>', unsafe_allow_html=True)
                    with c2: st.markdown(f'<div class="m-box"><span class="m-lbl">TOTAL KOLOM</span><span class="m-val">{len(df_master.columns)}</span></div>', unsafe_allow_html=True)
                    with c3: st.markdown(f'<div class="m-box"><span class="m-lbl">STATUS</span><span class="m-val">CONNECTED</span></div>', unsafe_allow_html=True)
                    with c4: st.markdown(f'<div class="m-box"><span class="m-lbl">ENGINE</span><span class="m-val">CALAMINE</span></div>', unsafe_allow_html=True)

                    st.divider()

                    # --- TABLE VIEW ---
                    st.subheader(f"📑 Table View: {selected_sheet}")
                    search = st.text_input(f"Cari data di sini...")
                    if search:
                        mask = df_master.apply(lambda row: row.astype(str).str.contains(search, case=False).any(), axis=1)
                        st.dataframe(df_master[mask], use_container_width=True, height=500)
                    else:
                        st.dataframe(df_master, use_container_width=True, height=500)
            else:
                st.error("Link-nya kagak valid!")

        except Exception as e:
            st.error(f"Error: {e}") # Pastiin kurungnya cuma satu di akhir