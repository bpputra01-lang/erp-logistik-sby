iimport pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="LOGISTIC OPERATION DASHBOARD", layout="wide")

# URL Gsheet (Sesuai GID Sheet Working Report Anda)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1tuGnu7jKvRkw9MmF92U-5pOoXjUOeTMoL3EvrOzcrQY/gviz/tq?tqx=out:csv&gid=864743695"

@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        return df
    except:
        return None

# 2. CUSTOM CSS (Untuk menyesuaikan warna Dashboard Biru Tua/Teal Anda)
st.markdown("""
    <style>
    .stApp { background-color: #0d3b44; color: white; }
    [data-testid="stMetric"] { background-color: #164e58; border: 1px solid #288494; padding: 15px; border-radius: 5px; }
    [data-testid="stMetricValue"] { color: white !important; font-size: 2.5rem !important; font-weight: bold; }
    [data-testid="stMetricLabel"] { color: #8ecad4 !important; font-size: 0.9rem !important; text-transform: uppercase; }
    .sidebar-text { color: white !important; }
    h1, h2, h3 { color: white !important; border-bottom: none; }
    div.stButton > button { background-color: #288494; color: white; border-radius: 5px; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

# 3. SIDEBAR
with st.sidebar:
    st.markdown("<h2 class='sidebar-text'>🚛 ERP SURABAYA</h2>", unsafe_allow_html=True)
    st.divider()
    menu = st.radio("MODUL UTAMA", ["📊 Dashboard Overview", "⛔ Stock Minus", "📦 Database Artikel"])

# 4. LOGIKA DASHBOARD OVERVIEW
if menu == "📊 Dashboard Overview":
    st.markdown("<h1 style='text-align: center; border: 2px solid white; padding: 10px;'>LOGISTIC OPERATION DASHBOARD</h1>", unsafe_allow_html=True)
    
    # --- BARIS 1: METRIK UTAMA (Data Real dari Spreadsheet) ---
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("TOTAL KOLI RECEIVED ALL TIME", "5378 KOLI") #
    with col2:
        st.metric("TOTAL REFILL & WD ALL TIME", "31733 ITEMS") #
    with col3:
        st.metric("TOTAL STOCK MINUS ALL TIME", "1898 ITEMS") #
    with col4:
        st.metric("AVERAGE LEAD TIME ALL TIME", "11 HOURS") #
    with col5:
        st.metric("TOTAL RTO", "1614 ITEMS") #

    st.markdown("<br>", unsafe_allow_html=True)

    # --- BARIS 2: SIDE KPI & GRAPHS ---
    left_col, mid_col, right_col = st.columns([1, 2, 2])

    with left_col:
        st.markdown("<div style='border: 1px solid white; padding: 10px; text-align: center;'>", unsafe_allow_html=True)
        st.metric("DIFF SEMARANG", "9") #
        st.metric("ACCURACY PERCENTAGE", "99%") #
        st.metric("DIFF SIDOARJO", "0") #
        st.markdown("</div>", unsafe_allow_html=True)

    with mid_col:
        # GRAFIK LEAD TIME BY CATEGORY (Data Dummy berdasarkan Visual Gsheet)
        cat_data = pd.DataFrame({
            'Category': ['A', 'B', 'C', 'D', 'E'],
            'Days': [2, 1, 3, 3, 5]
        })
        fig_cat = px.bar(cat_data, x='Category', y='Days', title="LEAD TIME GR BY CATEGORY",
                        color_discrete_sequence=['#b0bec5'])
        fig_cat.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
        st.plotly_chart(fig_cat, use_container_width=True)

    with right_col:
        # GRAFIK LEAD TIME BY BRAND (Sesuai Visual Gsheet Anda)
        brand_data = pd.DataFrame({
            'Brand': ['SM SPORT', 'JONAS', 'PATROBAS', 'ARDLILES', 'DENS', 'NINETEN'],
            'Hours': [8, 5, 5, 3, 3, 3]
        }).sort_values('Hours')
        
        fig_brand = px.bar(brand_data, x='Hours', y='Brand', orientation='h', title="LEAD TIME BY BRAND",
                          color_discrete_sequence=['#64b5f6'])
        fig_brand.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
        st.plotly_chart(fig_brand, use_container_width=True)

    # --- BARIS 3: PERFORMANCE MVP (Data dari Sheet Personal Performance) ---
    st.markdown("---")
    st.subheader("🏆 PERSONNEL PERFORMANCE")
    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1:
        st.success("**MVP LOGISTIC**\nYUDI SUJUD P.") #
    with m_col2:
        st.success("**MVP PICK**\nREYVALDO ZAKARIA I.") #
    with m_col3:
        st.success("**MVP PACK**\nN. HAMZAH") #

# 5. MODUL LAIN (Stock Minus)
elif menu == "⛔ Stock Minus":
    st.header("Stock Minus Clearance")
    # Logika proses excel Anda tetap di sini