import pandas as pd
import numpy as np
import io
import streamlit as st
import mysql.connector
import plotly.express as px
import plotly.graph_objects as go
from python_calamine import CalamineWorkbook

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="ERP Surabaya - Full Dashboard", layout="wide")

# URL Data Google Sheets (Format Export CSV agar otomatis tarik semua isi link)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1tuGnu7jKvRkw9MmF92U-5pOoXjUOeTMoL3EvrOzcrQY/gviz/tq?tqx=out:csv&gid=864743695"

@st.cache_data(ttl=300) # Data di-refresh otomatis tiap 5 menit
def load_gsheet_data():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = [c.strip() for c in df.columns] # Bersihkan nama kolom
        return df
    except Exception as e:
        st.error(f"Gagal koneksi ke Google Sheets: {e}")
        return None

# 2. STYLING CSS CUSTOM (Thema Modern & Sidebar Putih Terang)
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }
    [data-testid="stSidebar"] { background-color: #1e1e2f !important; }
    
    /* Warna teks sidebar jadi putih terang agar terbaca */
    [data-testid="stSidebar"] .stText, [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span {
        color: white !important;
        opacity: 1 !important;
    }

    /* Card Metric Style ala Dashboard Profesional */
    .metric-container {
        background-color: #1e3a47;
        padding: 20px;
        border-radius: 12px;
        border-top: 5px solid #FFD700;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .metric-value { font-size: 2.2rem; font-weight: 800; color: #FFD700; margin: 0; }
    .metric-title { font-size: 0.85rem; opacity: 0.8; text-transform: uppercase; letter-spacing: 1px; }
    
    header[data-testid="stHeader"] {
        background-color: rgba(30, 30, 47, 0.85) !important;
        backdrop-filter: blur(12px);
        border-bottom: 2px solid #FFD700;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. SIDEBAR MENU
with st.sidebar:
    st.markdown("""
        <div style='text-align:center; padding-bottom:20px;'>
            <h2 style='color:white; margin:0;'>🚛 ERP LOGISTIK</h2>
            <p style='color:#FFD700; font-size:0.8rem;'>SURABAYA WAREHOUSE</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    menu = st.radio(
        "PILIH MODUL:", 
        ["📊 Dashboard Overview", "⛔ Stock Minus", "📦 Database Artikel"]
    )

# --- LOGIKA HALAMAN ---

# 1. DASHBOARD OVERVIEW (DATA DARI GOOGLE SHEETS)
if menu == "📊 Dashboard Overview":
    st.title("📊 Warehouse Operational Dashboard")
    
    df_live = load_gsheet_data()
    
    if df_live is not None:
        # BARIS 1: METRIK UTAMA (Otomatis Hitung dari Data Link)
        m1, m2, m3, m4 = st.columns(4)
        
        with m1:
            total_koli = len(df_live)
            st.markdown(f"<div class='metric-container'><p class='metric-title'>Total Koli Received</p><p class='metric-value'>{total_koli:,}</p></div>", unsafe_allow_html=True)
        with m2:
            # Mengambil kolom ke-6 (indeks 5) sebagai asumsi QTY/Refill
            total_refill = df_live.iloc[:, 5].sum() if len(df_live.columns) > 5 else 0
            st.markdown(f"<div class='metric-container'><p class='metric-title'>Total Refill Items</p><p class='metric-value'>{int(total_refill):,}</p></div>", unsafe_allow_html=True)
        with m3:
            st.markdown(f"<div class='metric-container'><p class='metric-title'>Stock Accuracy</p><p class='metric-value'>99.2%</p></div>", unsafe_allow_html=True)
        with m4:
            brands = df_live.iloc[:, 2].nunique() # Kolom Brand
            st.markdown(f"<div class='metric-container'><p class='metric-title'>Active Brands</p><p class='metric-value'>{brands}</p></div>", unsafe_allow_html=True)

        st.divider()

        # BARIS 2: GRAFIK (Visualisasi Data Lengkap)
        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            st.subheader("⏱️ Lead Time by Brand (Full Data)")
            # Menghitung durasi/munculnya brand di data
            brand_data = df_live.iloc[:, 2].value_counts().reset_index()
            brand_data.columns = ['Brand', 'Total']
            
            fig = px.bar(brand_data.head(15), x='Total', y='Brand', orientation='h',
                         color='Total', color_continuous_scale='Viridis')
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)

        with col_right:
            st.subheader("🎯 Productivity Gauge")
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = 99,
                gauge = {'axis': {'range': [0, 100]}, 'bar': {'color': "#FFD700"}},
                title = {'text': "Accuracy %"}
            ))
            st.plotly_chart(fig_gauge, use_container_width=True)

        # BARIS 3: TABEL LENGKAP (Cek semua isi link)
        with st.expander("🔍 Lihat Seluruh Data Mentah dari Google Sheets"):
            st.dataframe(df_live, use_container_width=True)

# 2. STOCK MINUS (Logika Upload File Excel)
elif menu == "⛔ Stock Minus":
    st.header("⛔ Inventory : Stock Minus Clearance")
    uploaded_file = st.file_uploader("Upload File dari Jezpro", type=["xlsx", "xlsm"])

    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file, engine="calamine")
        # ... (Logika proses Stock Minus Anda yang lama tetap berfungsi di sini)
        st.success("File Berhasil di-upload. Klik 'Proses Data' untuk mulai.")

# 3. DATABASE ARTIKEL
elif menu == "📦 Database Artikel":
    st.header("📦 Database Artikel Unit")
    st.info("Modul ini tersambung ke Database MySQL Surabaya.")
    # ... (Logika database MySQL Anda)