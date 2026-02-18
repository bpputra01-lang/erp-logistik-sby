import pandas as pd
import numpy as np
import io
import streamlit as st
import plotly.express as px
from python_calamine import CalamineWorkbook

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="ERP Surabaya - Pro", layout="wide")

# 2. CUSTOM CSS (KEMBALIKAN STYLE LO & FIX FONT)
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }
    [data-testid="stSidebar"] { background-color: #1e1e2f !important; }
    [data-testid="stSidebar"] * { color: white !important; }
    header[data-testid="stHeader"] { background-color: rgba(30, 30, 47, 0.85) !important; backdrop-filter: blur(12px); border-bottom: 2px solid #FFD700; }
    .m-box { background-color: #164e58; border: 1px solid #288494; padding: 10px; border-radius: 5px; text-align: center; color: white; margin-bottom: 10px; }
    .m-val { font-size: 1.2rem; font-weight: 800; color: #FFD700; display: block; }
    .m-lbl { font-size: 0.7rem; color: #8ecad4; text-transform: uppercase; }
    </style>
    """, unsafe_allow_html=True)

# 3. SIDEBAR
with st.sidebar:
    st.markdown("<h2> ERP SURABAYA</h2>", unsafe_allow_html=True)
    st.divider()
    menu = st.radio("MODUL UTAMA", ["📊 Dashboard Overview", "⛔ Stock Minus", "📦 Database Artikel"])

# --- MODUL DASHBOARD OVERVIEW ---
if menu == "📊 Dashboard Overview":
    st.markdown("<h2 style='text-align: center; color: #1e3a47;'>LOGISTIC OPERATION DASHBOARD</h2>", unsafe_allow_html=True)
    row1 = st.columns(6)
    metrics = [("KOLI RECEIVED", "5378 KOLI"), ("REFILL & WD", "31733 ITEMS"), ("STOCK MINUS", "1898 ITEMS"), ("LEAD TIME", "11 HOURS"), ("TOTAL REFILL", "4212 ITEMS"), ("WITHDRAW", "30 ITEMS")]
    for i, (lbl, val) in enumerate(metrics):
        row1[i].markdown(f'<div class="m-box"><span class="m-lbl">{lbl}</span><span class="m-val">{val}</span></div>', unsafe_allow_html=True)
    
    c_side, c_mid, c_right = st.columns([1, 2.5, 2])
    with c_side:
        st.markdown('<div class="m-box"><span class="m-lbl">TOTAL RTO</span><span class="m-val">1,614</span></div>', unsafe_allow_html=True)
        st.markdown('<div class="m-box"><span class="m-lbl">DIFF SMG</span><span class="m-val">9 (99%)</span></div>', unsafe_allow_html=True)
        st.markdown('<div class="m-box"><span class="m-lbl">DIFF SDA</span><span class="m-val">0 (100%)</span></div>', unsafe_allow_html=True)
    with c_mid:
        df_g = pd.DataFrame({'Cat': ['A', 'B', 'C', 'D'], 'Val': [2, 1, 3, 5]})
        st.plotly_chart(px.bar(df_g, x='Cat', y='Val', title="LEAD TIME GR BY CATEGORY", height=250), use_container_width=True)
    with c_right:
        st.subheader("🏆 PERSONNEL MVP")
        st.info("🏅 LOGISTIC: Yudi Sujud P.\n\n🏅 PICK: Reyvaldo Zakaria I.\n\n🏅 PACK: N. Hamzah")

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

# --- MODUL DATABASE ARTIKEL (VERSI FIX ERROR & MULTI-SHEET) ---
elif menu == "📦 Database Artikel":
    st.title("📦 Master Database : Google Sheets Sync")
    
    # 1. Input link spreadsheet
    raw_url = st.text_input("MASUKKAN LINK GOOGLE SPREADSHEET LO:", 
                             placeholder="https://docs.google.com/spreadsheets/d/ID_FILE/edit...")
    
    if raw_url:
        try:
            # Fungsi buat bersihin link biar narik data murni (CSV), bukan HTML
            if "/d/" in raw_url:
                file_id = raw_url.split("/d/")[1].split("/")[0]
                # Step 1: Tarik Metadata buat dapetin nama-nama Sheet (Tab)
                # Kita pake trik export ke Excel biar bisa baca semua sheet sekaligus
                xlsx_url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
                
                # Baca file Excel dari link tersebut
                all_sheets = pd.read_excel(xlsx_url, sheet_name=None, engine='calamine')
                sheet_names = list(all_sheets.keys())
                
                # 2. DROPDOWN PILIH SHEET (Biar Header & Kolom gak ketuker)
                selected_sheet = st.selectbox("PILIH TAB / SHEET:", sheet_names)
                
                if selected_sheet:
                    df_master = all_sheets[selected_sheet]
                    
                    # --- TEMPAT ISIAN DETAIL DINAMIS ---
                    st.markdown(f"### 📊 Summary: {selected_sheet}")
                    c1, c2, c3, c4 = st.columns(4)
                    
                    with c1:
                        st.markdown(f'<div class="m-box"><span class="m-lbl">TOTAL BARIS</span><span class="m-val">{len(df_master)}</span></div>', unsafe_allow_html=True)
                    with c2:
                        st.markdown(f'<div class="m-box"><span class="m-lbl">TOTAL KOLOM</span><span class="m-val">{len(df_master.columns)}</span></div>', unsafe_allow_html=True)
                    with c3:
                        # Otomatis cari kolom yang ada angka buat di-Sum (Contoh: Stok/Qty)
                        num_cols = df_master.select_dtypes(include=[np.number]).columns
                        if not num_cols.empty:
                            target_col = num_cols[0] # Ambil kolom angka pertama
                            total_val = f"{int(df_master[target_col].sum()):,}"
                            st.markdown(f'<div class="m-box"><span class="m-lbl">TOTAL {target_col}</span><span class="m-val">{total_val}</span></div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="m-box"><span class="m-lbl">TOTAL DATA</span><span class="m-val">N/A</span></div>', unsafe_allow_html=True)
                    with c4:
                        st.markdown(f'<div class="m-box"><span class="m-lbl">STATUS</span><span class="m-val">CONNECTED</span></div>', unsafe_allow_html=True)

                    st.divider()

                    # 3. TAMPILAN TABEL DINAMIS (HEADER & KOLOM PERSIS SPREADSHEET)
                    st.subheader(f"📑 Table View: {selected_sheet}")
                    
                    # Filter search biar gampang nyari artikel
                    search = st.text_input(f"Cari di dalam {selected_sheet}...")
                    if search:
                        # Filter semua kolom yang mengandung kata kunci
                        mask = df_master.apply(lambda row: row.astype(str).str.contains(search, case=False).any(), axis=1)
                        df_display = df_master[mask]
                    else:
                        df_display = df_master

                    st.dataframe(df_display, use_container_width=True, height=500)
            else:
                st.error("Link-nya kagak valid, Bos! Pastiin formatnya link Google Sheets.")

        except Exception as e:
            st.error(f"ERROR: {e}")
            st.info("PASTIIN: Link Spreadsheet udah di-set ke 'Anyone with the link' (Viewer).")
    else:
        st.info("💡 Tempel link Spreadsheet lo di atas, entar semua Sheet/Tab-nya muncul otomatis.")