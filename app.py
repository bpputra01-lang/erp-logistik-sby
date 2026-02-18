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
    .stApp { background-color: #ffffff; color: #31333f; }
    [data-testid="stSidebar"] { background-color: #1e1e2f !important; }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: white !important; }

    div[data-baseweb="select"] > div {
        background-color: #1e1e2f !important;
        color: #FFD700 !important;
        border: 2px solid #3b82f6 !important;
        z-index: 999999 !important;
    }
    div[role="listbox"] ul { background-color: #1e1e2f !important; }
    div[role="option"] { color: white !important; }

    .m-box { 
        background-color: #1e1e2f !important; 
        border: 2px solid #3b82f6 !important;
        border-left: 12px solid #FFD700 !important;
        padding: 25px !important; 
        border-radius: 15px !important; 
        text-align: center !important; 
        box-shadow: 0 8px 20px rgba(0,0,0,0.3) !important;
        margin-bottom: 15px !important;
    }
    .m-val { font-size: 32px !important; font-weight: 800 !important; color: #FFD700 !important; display: block !important; }
    .m-lbl { font-size: 14px !important; color: #ffffff !important; text-transform: uppercase !important; font-weight: 700 !important; letter-spacing: 1.5px !important; }

    .hero-header {
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        color: white; padding: 1.5rem 2rem;
        border-bottom: 5px solid #FFD700; border-radius: 15px; margin-bottom: 20px;
    }
    .dash-container {
        border: 5px solid #1e3a8a; border-radius: 15px;
        padding: 10px; background: #f8f9fa;
        box-shadow: 0 0 25px rgba(59, 130, 246, 0.5);
        overflow: hidden;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNGSI LOGIKA SCAN OUT (HEADER DISAMAKAN DENGAN VBA) ---
def process_scan_out(df_scan, df_history, df_stock):
    # Logic: CLEAN_DATA_SCAN_WITH_COUNTIFS_V2
    df_scan.columns = [str(c).strip().upper() for c in df_scan.columns]
    # Mengasumsikan Kolom A adalah BIN dan B adalah SKU sesuai macro lo
    df_scan['BIN_CLEAN'] = df_scan.iloc[:, 0].astype(str).str.strip()
    df_scan['SKU_CLEAN'] = df_scan.iloc[:, 1].astype(str).str.strip()
    
    # Menghitung QTY (seperti Rumus COUNTIFS di Kolom C macro)
    df_scan_clean = df_scan.groupby(['BIN_CLEAN', 'SKU_CLEAN']).size().reset_index(name='QTY')

    results = []
    draft_setup = []

    # Loop Progres Compare (Logic: CompareDataScan_FullFormat)
    for _, row in df_scan_clean.iterrows():
        sku = row['SKU_CLEAN']
        bin_scan = row['BIN_CLEAN']
        qty = row['QTY']
        
        found_stock = False
        found_history = False
        
        keterangan = ""
        total_qty_setup_terjual = 0
        bin_after_setup = ""
        invoice = ""

        # A. Loop STOCK TRACKING (Cek SKU & BIN)
        match_stock = df_stock[(df_stock.iloc[:, 1].astype(str).str.strip() == sku) & 
                               (df_stock.iloc[:, 6].astype(str).str.strip() == bin_scan)]
        
        if not match_stock.empty:
            found_stock = True
            total_qty_setup_terjual = match_stock.iloc[0, 10] # Kolom K
            invoice = match_stock.iloc[0, 0] # Kolom A
            if total_qty_setup_terjual == qty:
                keterangan = "ITEM TELAH TERJUAL"
            else:
                keterangan = "ITEM TERJUAL (QTY MISSMATCH)"
        
        # B. Jika tidak ketemu di Stock, cek HISTORY SET UP
        if not found_stock:
            match_hist = df_history[df_history.iloc[:, 3].astype(str).str.strip() == sku] # Kolom D
            if not match_hist.empty:
                found_history = True
                total_qty_setup_terjual = match_hist.iloc[0, 10] # Kolom K
                bin_after_setup = match_hist.iloc[0, 12] # Kolom M
                bin_hist_i = str(match_hist.iloc[0, 8]).strip() # Kolom I
                
                if bin_hist_i == bin_scan:
                    keterangan = "DONE AND MATCH SET UP" if total_qty_setup_terjual == qty else "DONE SETUP (QTY MISSMATCH)"
                else:
                    keterangan = "DONE SET UP (BIN MISSMATCH)"

        # C. Fallback: Cek Stock lagi (Hanya SKU, BIN Mismatch)
        if not found_stock and not found_history:
            match_stock_any = df_stock[df_stock.iloc[:, 1].astype(str).str.strip() == sku]
            if not match_stock_any.empty:
                keterangan = "ITEM TERJUAL (BIN MISSMATCH)"
                total_qty_setup_terjual = match_stock_any.iloc[0, 10]
                invoice = match_stock_any.iloc[0, 0]
                found_stock = True

        # D. Final Fallback
        if not found_stock and not found_history:
            keterangan = "ITEM BELUM TERSETUP & TIDAK TERJUAL"

        # --- LOGIKA CreateDraftSetUp_FIXED ---
        # Menggunakan nama kolom persis VBA: BIN AWAL, BIN TUJUAN, SKU, QUANTITY, NOTES
        if keterangan == "DONE SETUP (QTY MISSMATCH)":
            draft_setup.append({
                "BIN AWAL": bin_scan, "BIN TUJUAN": bin_after_setup, 
                "SKU": sku, "QUANTITY": qty - total_qty_setup_terjual, "NOTES": "WAITING OFFLINE"
            })
        elif keterangan == "ITEM BELUM TERSETUP & TIDAK TERJUAL":
            draft_setup.append({
                "BIN AWAL": bin_scan, "BIN TUJUAN": "KARANTINA", 
                "SKU": sku, "QUANTITY": qty, "NOTES": "WAITING OFFLINE"
            })
        elif keterangan == "DONE SET UP (BIN MISSMATCH)":
            # Baris Pertama: Set Up Balik
            draft_setup.append({
                "BIN AWAL": bin_after_setup, "BIN TUJUAN": bin_scan, 
                "SKU": sku, "QUANTITY": total_qty_setup_terjual, "NOTES": "SET UP BALIK"
            })
            # Baris Kedua: Karantina
            draft_setup.append({
                "BIN AWAL": bin_scan, "BIN TUJUAN": "KARANTINA", 
                "SKU": sku, "QUANTITY": qty, "NOTES": "WAITING OFFLINE"
            })

        # Header hasil compare disamakan dengan VBA Array("Keterangan", "Total Qty Setup/Terjual", "Bin After Set Up", "Invoice")
        results.append({
            "BIN": bin_scan,
            "SKU": sku,
            "QTY": qty,
            "Keterangan": keterangan,
            "Total Qty Setup/Terjual": total_qty_setup_terjual,
            "Bin After Set Up": bin_after_setup,
            "Invoice": invoice
        })

    return pd.DataFrame(results), pd.DataFrame(draft_setup)

# --- SIDEBAR & MENU ---
with st.sidebar:
    st.markdown("<h2 style='color: white;'>🚀 ERP LOGISTIK SURABAYA</h2>", unsafe_allow_html=True)
    st.divider()
    menu = st.radio("MODUL UTAMA", ["📊 Dashboard Overview", "📤 Scan Out", "📝 Dashboard Database", "⛔ Stock Minus"])

if menu == "📊 Dashboard Overview":
    st.markdown('<div class="hero-header"><h1>📊 DASHBOARD ANALYTICS</h1></div>', unsafe_allow_html=True)
    c1, c2 = st.columns([3, 1])
    with c1:
        pilih = st.selectbox("PILIH LAPORAN", ["WORKING REPORT", "PERSONAL PERFORMANCE", "CYCLE COUNT DAN KERAPIHAN", "DASHBOARD MOVING STOCK"])
    with c2: zoom = st.slider("ZOOM", 0.1, 1.0, 0.35)
    dash_links = {"WORKING REPORT": "864743695", "PERSONAL PERFORMANCE": "251294539", "CYCLE COUNT DAN KERAPIHAN": "1743896821", "DASHBOARD MOVING STOCK": "1671817510"}
    gid = dash_links[pilih]
    st.markdown(f'''<div class="dash-container"><div style="width: 100%; height: 500px; overflow: auto;"><iframe src="https://docs.google.com/spreadsheets/d/e/2PACX-1vRIMd-eghecjZKcOmhz0TW4f-1cG0LOWgD6X9mIK1XhiYSOx-V6xSnZQzBLfru0LhCIinIZAfbYnHv_/pubhtml?gid={gid}&single=true&rm=minimal" style="width: 4000px; height: 1500px; border: none; transform: scale({zoom}); transform-origin: 0 0;"></iframe></div></div>''', unsafe_allow_html=True)

elif menu == "📤 Scan Out":
    st.markdown('<div class="hero-header"><h1>📤 SCAN OUT & VALIDASI</h1></div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1: up_scan = st.file_uploader("Upload DATA SCAN", type=['xlsx', 'csv'])
    with col2: up_hist = st.file_uploader("Upload HISTORY SET UP", type=['xlsx'])
    with col3: up_stock = st.file_uploader("Upload STOCK TRACKING", type=['xlsx'])

    if up_scan and up_hist and up_stock:
        if st.button("🚀 JALANKAN PROSES VALIDASI"):
            try:
                # Membaca data dengan Calamine
                df_s = pd.read_excel(up_scan, engine='calamine') if up_scan.name.endswith('xlsx') else pd.read_csv(up_scan)
                df_h = pd.read_excel(up_hist, engine='calamine')
                df_st = pd.read_excel(up_stock, engine='calamine')

                df_res, df_draft = process_scan_out(df_s, df_h, df_st)

                st.success("Validasi Selesai!")
                
                def highlight_vba(val):
                    color = 'red' if 'MISSMATCH' in str(val) or 'BELUM' in str(val) else 'black'
                    return f'color: {color}; font-weight: bold'

                st.subheader("📋 DATA SCAN (COMPARED)")
                st.dataframe(df_res.style.applymap(highlight_vba, subset=['Keterangan']), use_container_width=True)

                st.subheader("📝 DRAFT SET UP")
                st.dataframe(df_draft, use_container_width=True)

                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_res.to_excel(writer, sheet_name='DATA SCAN', index=False)
                    df_draft.to_excel(writer, sheet_name='DRAFT SET UP', index=False)
                
                st.download_button("📥 DOWNLOAD HASIL SCAN OUT", data=output.getvalue(), file_name="HASIL_SCAN_OUT.xlsx")
            except Exception as e:
                st.error(f"Error: {e}")

# ... (Menu Dashboard Database & Stock Minus tetap di bawah sini tanpa ubah logic awal lo)

elif menu == "⛔ Stock Minus":
    st.markdown('<div class="hero-header"><h1>⛔ STOCK MINUS CLEARANCE</h1></div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload File dari Jezpro", type=["xlsx", "xlsm"])
    # ... (Sisa logic stock minus lo masukin sini)
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