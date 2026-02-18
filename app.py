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
    /* 1. KOTAK SUMMARY (DEEP DARK NAVY) */
    .m-box { 
        background-color: #1e1e2f !important; /* Biru Gelap Tegas */
        border: 2px solid #3b82f6; 
        border-left: 8px solid #FFD700 !important; /* Aksen Emas Tebal */
        padding: 20px; 
        border-radius: 12px; 
        text-align: center; 
        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
        margin-bottom: 15px;
    }

    /* 2. ANGKA (GOLD) */
    .m-val { 
        font-size: 28px; 
        font-weight: 800; 
        color: #FFD700 !important; /* Warna Emas */
        display: block;
        margin-top: 5px;
    }

    /* 3. LABEL (PUTIH/ABU TERANG) */
    .m-lbl { 
        font-size: 13px; 
        color: #ffffff !important; /* Teks Label Putih biar kebaca di Box Gelap */
        text-transform: uppercase; 
        font-weight: 700;
        letter-spacing: 1.5px;
    }

    /* CSS Tambahan buat Table & Dropdown tetap Dark */
    div[data-baseweb="select"] > div, div[data-testid="stTextInput"] input {
        background-color: #1e1e2f !important;
        color: white !important;
        border: 1px solid #3b82f6 !important;
    }
    
    [data-testid="stDataFrame"] {
        background-color: #1e1e2f !important;
    } </style>
    """, unsafe_allow_html=True)
# --- 3. SIDEBAR (WAJIB DI ATAS AGAR VARIABEL 'MENU' TERDEFINISI) ---
with st.sidebar:
    st.markdown("<h2 style='color: white;'>🚀 ERP LOGISTIK SURABAYA</h2>", unsafe_allow_html=True)
    st.divider()
    menu = st.radio("MODUL UTAMA", ["📊 Dashboard Overview","📝 Dashboard Database","⛔ Stock Minus"])

# --- 4. LOGIKA MODUL ---

if menu == "📊 Dashboard Overview":
    st.markdown("""<div class="hero-header"><h1>📊 DASHBOARD ANALYTICS</h1><p>Analytic Reports Logistics Surabaya</p></div>""", unsafe_allow_html=True)
    
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

elif menu == "📝 Dashboard Database":
    st.title("📓 Check Detail Dashboard")
    # 1. HEADER MEWAH
    st.markdown("""<div class="hero-header"><h1>📓 DETAIL DATABASE ANALYTICS</h1><p>Automatic Sync with Google Sheets Master</p></div>""", unsafe_allow_html=True)
    
    # 2. LINK OTOMATIS (Gak perlu input manual lagi)
    SHEET_URL = "https://docs.google.com/spreadsheets/d/1tuGnu7jKvRkw9MmF92U-5pOoXjUOeTMoL3EvrOzcrQY/edit?usp=sharing"
    
    try:
        # Extract File ID secara otomatis
        file_id = SHEET_URL.split("/d/")[1].split("/")[0]
        xlsx_url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
        
        # Tarik semua sheet
        all_sheets = pd.read_excel(xlsx_url, sheet_name=None, engine='calamine')
        
        # Pilihan Sheet/Tab
        sel_sheet = st.selectbox("📂 PILIH TAB DATABASE:", list(all_sheets.keys()))
        
        if sel_sheet:
            df_master = all_sheets[sel_sheet]
            
            # --- CLEANING DATA ---
            for col in df_master.columns:
                col_name = str(col).upper()
                # Fix Tanggal
                if any(x in col_name for x in ["DATE", "TANGGAL"]):
                    df_master[col] = pd.to_datetime(df_master[col], errors='coerce').dt.date
                # Fix Waktu/Jam (Jika ada)
                elif any(x in col_name for x in ["TIME", "AVERAGE"]):
                    df_master[col] = df_master[col].astype(str).str.split().str[-1]

            # --- SUMMARY BOX (Biar keren) ---
            c1, c2, c3 = st.columns(3)
            with c1: st.markdown(f'<div class="m-box"><span class="m-lbl">TOTAL BARIS</span><span class="m-val">{len(df_master)}</span></div>', unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="m-box"><span class="m-lbl">TOTAL KOLOM</span><span class="m-val">{len(df_master.columns)}</span></div>', unsafe_allow_html=True)
            with c3: st.markdown(f'<div class="m-box"><span class="m-lbl">SYNC STATUS</span><span class="m-val">CONNECTED</span></div>', unsafe_allow_html=True)

            # --- SEARCH BAR ---
            search = st.text_input("🔍 Cari Data di Tabel:", placeholder="Ketik nama atau SKU...")
            if search:
                mask = df_master.apply(lambda row: row.astype(str).str.contains(search, case=False).any(), axis=1)
                st.dataframe(df_master[mask], use_container_width=True, height=500)
            else:
                st.dataframe(df_master, use_container_width=True, height=500)

    except Exception as e:
        st.error(f"❌ Gagal koneksi ke database: {e}")
# --- MODUL STOCK MINUS (FULL LOGIC BALIK!) ---
elif menu == "⛔ Stock Minus":
    st.title("⛔ Inventory : Stock Minus Clearance")
    uploaded_file = st.file_uploader("Upload File dari Jezpro", type=["xlsx", "xlsm"])

    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file, engine="calamine")
        col_sku, col_bin = 'SKU', 'BIN'
        col_qty = next((c for c in df.columns if 'QTY SYS' in str(c).upper()), 'QTY SYSTEM')

        if st.button("🔃 PROSES DATA"):
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

                st.success(f"✅ Done! {len(set_up_results)} item direlokasi. {len(df_need_adj)} Item Butuh Adjusment.")
                st.download_button("📥 DOWNLOAD HASIL LENGKAP", data=output.getvalue(), file_name="PENYELESAIAN_STOCK_MINUS.xlsx")

# --- MODUL DATABASE ARTIKEL (FIX HEADER HILANG & FORMAT WAKTU) ---
elif menu == "📝 Dashboard Database":
    st.title("📓 Check Detail Dashboard")
    
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