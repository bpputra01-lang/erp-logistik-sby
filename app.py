import pandas as pd
import numpy as np
import io
import streamlit as st
import mysql.connector
import plotly.express as px
from python_calamine import CalamineWorkbook

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="ERP Surabaya - Pro", layout="wide")

# 2. KEMBALIKAN STYLING CSS CUSTOM (Sidebar Gelap & Glassmorphism Anda)
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }
    [data-testid="stSidebar"] { background-color: #1e1e2f !important; }
    [data-testid="stSidebar"] .stText, [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span {
        color: white !important;
        opacity: 1 !important;
    }
    header[data-testid="stHeader"] {
        background-color: rgba(30, 30, 47, 0.85) !important;
        backdrop-filter: blur(12px);
        border-bottom: 2px solid #FFD700;
    }
    /* Style untuk Box Dashboard agar tidak terpotong */
    .metric-card {
        background-color: #1e3a47; padding: 15px; border-radius: 10px;
        border-top: 4px solid #FFD700; color: white; text-align: center;
    }
    .metric-value { font-size: 1.5rem; font-weight: 800; color: #FFD700; }
    </style>
    """, unsafe_allow_html=True)

# 3. SIDEBAR MENU (KEMBALI KE FORMAT AWAL)
with st.sidebar:
    st.markdown("<h2 style='color:white;'>🚛 ERP SURABAYA</h2>", unsafe_allow_html=True)
    st.divider()
    menu = st.radio("MODUL UTAMA", ["📊 Dashboard Overview", "⛔ Stock Minus", "📦 Database Artikel"])

# --- LOGIKA HALAMAN ---

# A. MODUL DASHBOARD (YANG ANDA MINTA TAMBAHKAN)
if menu == "📊 Dashboard Overview":
    st.title("📊 LOGISTIC OPERATION DASHBOARD")
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1: st.markdown('<div class="metric-card">TOTAL KOLI<br><span class="metric-value">5,378</span></div>', unsafe_allow_html=True)
    with m2: st.markdown('<div class="metric-card">REFILL & WD<br><span class="metric-value">31,733</span></div>', unsafe_allow_html=True)
    with m3: st.markdown('<div class="metric-card">STOCK MINUS<br><span class="metric-value">1,898</span></div>', unsafe_allow_html=True)
    with m4: st.markdown('<div class="metric-card">LEAD TIME<br><span class="metric-value">11 HOURS</span></div>', unsafe_allow_html=True)
    with m5: st.markdown('<div class="metric-card">TOTAL RTO<br><span class="metric-value">1,614</span></div>', unsafe_allow_html=True)
    
    st.divider()
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("⏱️ Lead Time by Brand")
        brand_data = pd.DataFrame({'Brand': ['SM SPORT', 'JONAS', 'PATROBAS', 'ARDILES', 'DENS', 'NINETEN'], 'Time': [8, 5, 5, 3, 3, 3]})
        fig = px.bar(brand_data, x='Time', y='Brand', orientation='h', color_discrete_sequence=['#4A90E2'])
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.subheader("🏆 PERSONNEL MVP")
        st.info("🏅 **LOGISTIC:** Yudi Sujud P.\n\n🏅 **PICK:** Reyvaldo Zakaria I.\n\n🏅 **PACK:** N. Hamzah")

# B. MODUL STOCK MINUS (FITUR LAMA ANDA SAYA KEMBALIKAN PENUH)
elif menu == "⛔ Stock Minus":
    st.title("⛔ Inventory : Stock Minus Clearance")
    uploaded_file = st.file_uploader("Upload File dari Jezpro", type=["xlsx", "xlsm"])

    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file, engine="calamine")
        col_sku, col_bin = 'SKU', 'BIN'
        col_qty = next((c for c in df.columns if 'QTY SYS' in str(c).upper()), 'QTY SYSTEM')

        m1, m2, m3 = st.columns(3)
        with m1: st.metric("Ukuran File", f"{uploaded_file.size / 1024 / 1024:.2f} MB")
        with m2: st.metric("Total Baris Data", f"{len(df):,}")
        with m3:
            total_minus = len(df[df[col_qty] < 0])
            st.metric("Item Stock Minus", f"{total_minus} SKU")

        if st.button("🚀 PROSES DATA"):
            with st.spinner('Sedang memproses relokasi stok...'):
                # --- LOGIC ASLI ANDA ---
                df_stock_minus_awal = df[df[col_qty] < 0].copy()
                qty_array = pd.to_numeric(df[col_qty], errors='coerce').fillna(0).values
                sku_array = df[col_sku].astype(str).values 
                bin_array = df[col_bin].astype(str).values
                
                pos_map = {sku: [] for sku in np.unique(sku_array)}
                for i in range(len(qty_array)):
                    if qty_array[i] > 0: pos_map[sku_array[i]].append(i)

                set_up_results = []
                minus_indices = np.where(qty_array < 0)[0]
                
                for idx in minus_indices:
                    sku_target, qty_needed, bin_tujuan = sku_array[idx], abs(qty_array[idx]), bin_array[idx]
                    if sku_target in pos_map:
                        for p_idx in pos_map[sku_target]:
                            if qty_needed <= 0: break
                            if qty_array[p_idx] > 0:
                                take = min(qty_needed, qty_array[p_idx])
                                qty_array[p_idx] -= take; qty_array[idx] += take
                                set_up_results.append({
                                    "BIN AWAL": bin_array[p_idx], "BIN TUJUAN": bin_tujuan,
                                    "SKU": sku_target, "QUANTITY": take, "NOTES": "STOCK MINUS"
                                })
                                qty_needed -= take

                df_setup_final = pd.DataFrame(set_up_results)
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_stock_minus_awal.to_excel(writer, sheet_name='STOCK MINUS', index=False)
                    if not df_setup_final.empty: df_setup_final.to_excel(writer, sheet_name='SET UP STOCK MINUS', index=False)

                st.success("✅ Proses Berhasil!")
                st.download_button("📥 DOWNLOAD HASIL DATA", data=output.getvalue(), file_name="HASIL_STOCK_MINUS.xlsx")

# C. DATABASE ARTIKEL
elif menu == "📦 Database Artikel":
    st.title("📦 Database Artikel")
    st.info("Fitur manajemen data artikel sedang aktif.")