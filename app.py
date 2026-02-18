import pandas as pd
import numpy as np
import io
import streamlit as st
import mysql.connector
from python_calamine import CalamineWorkbook

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="ERP Surabaya - Pro", layout="wide")

# 2. STYLING CSS CUSTOM (Thema Modern & Anti-Boring)
st.markdown("""
    <style>
    /* Latar belakang aplikasi */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }

    /* Mengatur Sidebar agar tetap Gelap */
    [data-testid="stSidebar"] {
        background-color: #1e1e2f !important;
    }

    /* --- PERBAIKAN TEKS MENU JADI PUTIH --- */
    /* Target semua teks di dalam sidebar agar putih terang */
    [data-testid="stSidebar"] .stText, 
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span {
        color: white !important;
        opacity: 1 !important;
    }

    /* Target khusus untuk teks di dalam Radio Group (Menu Utama) */
    div[data-testid="stSidebar"] div[role="radiogroup"] label div[data-testid="stMarkdownContainer"] p {
        color: white !important;
        font-weight: 500 !important;
    }
    /* -------------------------------------- */

    /* Glassmorphism Header */
    header[data-testid="stHeader"] {
        background-color: rgba(30, 30, 47, 0.85) !important;
        backdrop-filter: blur(12px);
        border-bottom: 2px solid #FFD700;
    }
    header[data-testid="stHeader"] svg { fill: white !important; }

    /* Menu Radio menjadi Card Modern */
    div[data-testid="stSidebar"] div[role="radiogroup"] { gap: 10px; }
    div[data-testid="stSidebar"] div[role="radiogroup"] label {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        padding: 15px 20px !important;
        border-radius: 12px !important;
        transition: all 0.3s ease;
    }
    
    /* Efek Hover & Seleksi */
    div[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
        background-color: rgba(255, 255, 255, 0.1) !important;
        border-color: #FFD700 !important;
        transform: translateX(5px);
    }
    div[data-testid="stSidebar"] div[role="radiogroup"] label[data-selected="true"] {
        background: linear-gradient(45deg, #007bff, #0056b3) !important;
        border: none !important;
    }

    .sidebar-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-top: -50px;
        padding-bottom: 10px;
    }
    .header-text { color: white; font-weight: 800; font-size: 1.1rem; }
    .header-text span { color: #FFD700; font-size: 0.9rem; }
    .sidebar-divider {
        margin: 5px 0px 20px 0px;
        height: 2px;
        background: linear-gradient(to right, #FFD700, transparent);
    }
    </style>
    """, unsafe_allow_html=True)

# 3. KONEKSI DATABASE
def get_db():
    return mysql.connector.connect(
        host="erp-logistik-surabaya1-bpputra01-eb8d.f.aivencloud.com",
        port=15513,
        user="avnadmin",
        password="AVNS_jyNhw1WuDj5spwMpXrV",
        database="defaultdb"
    )

# 4. SIDEBAR MENU
with st.sidebar:
    # Header Sidebar (🚛 Surabaya Logistics)
    st.markdown("""
        <div class="sidebar-header">
            <div class="header-icon">🚛</div>
            <div class="header-text">
                ERP LOGISTIK<br>
                <span>SURABAYA</span>
            </div>
        </div>
        <div class="sidebar-divider"></div>
    """, unsafe_allow_html=True)
    
    st.markdown("<p style='color:white; opacity:0.6; font-size:0.8rem; font-weight:bold;'>INVENTORY</p>", unsafe_allow_html=True)
    
    menu = st.radio(
        "Pilih Modul:", 
        [
            "📊 Dashboard Overview", 
            "⛔ Stock Minus",
            "📦 Database Artikel"
        ],
        label_visibility="collapsed"
    )

# --- LOGIKA HALAMAN ---

# Banner Header untuk Menghilangkan Kesan Putih Polos
def draw_header_banner(title, subtitle):
    st.markdown(f"""
        <div style="background: linear-gradient(90deg, #1e1e2f, #2a2a40); 
                    padding: 20px; border-radius: 15px; border-left: 5px solid #FFD700; 
                    margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
            <h2 style="color: white; margin: 0;">{title}</h2>
            <p style="color: rgba(255,255,255,0.7); margin: 5px 0 0 0; font-size: 0.9rem;">{subtitle}</p>
        </div>
    """, unsafe_allow_html=True)

# 1. DASHBOARD
if menu == "📊 Dashboard Overview":
    draw_header_banner("📊 Warehouse Overview", "Monitoring stok dan database warehouse Surabaya secara real-time.")
    try:
        db = get_db()
        df_db = pd.read_sql("SELECT * FROM data_artikel", db)
        st.dataframe(df_db, use_container_width=True)
        db.close()
    except Exception as e:
        st.error(f"Gagal koneksi database: {e}")

# 2. DATABASE ARTIKEL
elif menu == "📦 Database Artikel":
    draw_header_banner("📦 Database Artikel", "Manajemen data SKU dan profil artikel unit.")
    st.info("Fitur manajemen data artikel unit sedang dalam pengembangan.")

# 3. PENYELESAIAN STOCK MINUS
elif menu == "⛔ Stock Minus":
    draw_header_banner("⛔ Inventory : Stock Minus Clearance", "Sistem otomasi relokasi stok untuk penyelesaian selisih minus.")
    
    uploaded_file = st.file_uploader("Upload File dari Jezpro", type=["xlsx", "xlsm"])

    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file, engine="calamine")
        col_sku, col_bin = 'SKU', 'BIN'
        col_qty = next((c for c in df.columns if 'QTY SYS' in str(c).upper()), 'QTY SYSTEM')

        # Tampilan Metrik
        m1, m2, m3 = st.columns(3)
        with m1: st.metric("Ukuran File", f"{uploaded_file.size / 1024 / 1024:.2f} MB")
        with m2: st.metric("Total Baris Data", f"{len(df):,}")
        with m3:
            total_minus = len(df[df[col_qty] < 0])
            st.metric("Item Stock Minus", f"{total_minus} SKU", delta_color="inverse")

        st.divider()

        if st.button("🚀 PROSES DATA"):
            with st.spinner('Sedang memproses relokasi stok...'):
                # LOGIC SPEED DEMON
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
                df_need_adj = df.iloc[minus_indices][qty_array[minus_indices] < 0].copy()

                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_stock_minus_awal.to_excel(writer, sheet_name='STOCK MINUS', index=False)
                    if not df_setup_final.empty: df_setup_final.to_excel(writer, sheet_name='SET UP STOCK MINUS', index=False)
                    if not df_need_adj.empty: df_need_adj.to_excel(writer, sheet_name='NEED JUSTIFIKASI', index=False)

            st.success("✅ Proses Berhasil Dijalankan!")
            res1, res2 = st.columns(2)
            res1.info(f"📦 **{len(set_up_results)}** Item Set-Up dibuat.")
            res2.warning(f"⚠️ **{len(df_need_adj)}** SKU butuh Justifikasi.")

            st.download_button(
                label="📥 DOWNLOAD HASIL DATA STOCK MINUS",
                data=output.getvalue(),
                file_name="PENYELESAIAN_STOCK_MINUS.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )