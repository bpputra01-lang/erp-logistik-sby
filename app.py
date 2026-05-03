import pandas as pd
import numpy as np
import streamlit as st
import io
import math
from collections import defaultdict
from streamlit_autorefresh import st_autorefresh
import openpyxl
from openpyxl import load_workbook
import re
import requests
from datetime import datetime, timedelta, date
import pytz
import uuid
import sqlite3

# ==========================================
# INISIALISASI DATABASE GLOBAL SUPABASE
# ==========================================
try:
    from supabase import create_client, Client
    HAS_SUPABASE = True
except ImportError:
    HAS_SUPABASE = False

SUPABASE_URL = "https://ufhjrsxzcffdfswfqlzk.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVmaGpyc3h6Y2ZmZGZzd2ZxbHprIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYxNTI5NjgsImV4cCI6MjA5MTcyODk2OH0.DDlKkXU5-nVvNYK_uLYzXLgaj8oDT4s8vbjAoWMWacI"

@st.cache_resource
def init_supabase_global():
    if HAS_SUPABASE:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    return None

supabase_global = init_supabase_global()

@st.cache_data(ttl=60)
def fetch_table_data(table_name):
    if supabase_global:
        res = supabase_global.table(table_name).select("*").execute()
        return pd.DataFrame(res.data)
    return pd.DataFrame()
# ==========================================


# Jaga koneksi setiap 5 menit agar tidak timeout/refresh sendiri
st_autorefresh(interval=300000, key="keepalive_session")

st.set_page_config(
    page_title="LogsbyERP.id",
    page_icon="🚛",
    layout="wide",)
  
st.markdown("""
    <style>
    /* ============================================
       FONTS IMPORT
       ============================================ */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Poppins:wght@600;700;800&display=swap');

    /* ============================================
       1. LAYOUT & SPACING
       ============================================ */
    .block-container {
        padding-top: 3.5rem !important;
        padding-bottom: 0rem !important;
    }
    [data-testid="stSidebarUserContent"] { padding-top: 0rem !important; }
    [data-testid="stSidebarNav"] { display: none !important; }

    /* ============================================
       2. APP BACKGROUND
       ============================================ */
    .stApp {
        background-color: #f5f7fa !important;
    }

    /* ============================================
       3. SIDEBAR - PREMIUM DARK
       ============================================ */
    [data-testid="stSidebar"] {
        background-color: #1a1d2e !important;
        border-right: 1px solid rgba(197, 160, 89, 0.15) !important;
    }

    /* ============================================
       4. HERO HEADER - PREMIUM BLUE
       ============================================ */
    .hero-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #1e3c72 100%) !important;
        color: white !important;
        padding: 10px 22px !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 15px rgba(30, 60, 114, 0.25) !important;
        margin-top: 0px !important;
        margin-bottom: 25px !important;
        display: inline-block !important;
        width: auto !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    .hero-header h1 {
        color: white !important;
        font-family: 'Poppins', sans-serif !important;
        font-size: 19px !important;
        font-weight: 700 !important;
        margin: 0 !important;
        letter-spacing: 0.3px;
        line-height: 1.3;
    }

    /* ============================================
       5. MAIN BUTTONS - NAVY BLUE
       ============================================ */
    div.stButton > button {
        background: linear-gradient(135deg, #002b5b 0%, #003874 100%) !important;
        color: white !important;
        border-radius: 8px !important;
        border: 1px solid #001a35 !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        height: 3em !important;
        transition: all 0.25s ease !important;
        box-shadow: 0 2px 8px rgba(0, 43, 91, 0.2) !important;
    }
    div.stButton > button:hover {
        background: linear-gradient(135deg, #003874 0%, #004a9e 100%) !important;
        border-color: #ffc107 !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(0, 43, 91, 0.3) !important;
    }

    /* Clear/Reset Buttons - Red */
    div.stButton > button[key*="reset"],
    div.stButton > button[key*="clear"] {
        background: linear-gradient(135deg, #8b0000 0%, #a00000 100%) !important;
        border-color: #4a0000 !important;
    }
    div.stButton > button[key*="reset"]:hover,
    div.stButton > button[key*="clear"]:hover {
        background: linear-gradient(135deg, #a00000 0%, #b50000 100%) !important;
        border-color: #ff4444 !important;
    }

    /* ============================================ 
       6. FILE UPLOADER 
       ============================================ */[data-testid="stFileUploader"] { 
        background-color: #f0f2f6; 
        border: 2px dashed rgba(0, 43, 91, 0.3) !important; 
        border-radius: 10px; 
        padding: 12px; 
    } 

    [data-testid="stFileUploader"] button { 
        background: linear-gradient(135deg, #C5A059 0%, #b08d4a 100%) !important; 
        color: #1a1d2e !important; 
        font-weight: 600 !important; 
        border-radius: 6px !important; 
        font-size: 12px !important; 
    } 

    /* ============================================ 
       7. METRIC BOXES - PREMIUM CARD 
       ============================================ */ 
    .m-box { 
        background: linear-gradient(135deg, #1a1d2e 0%, #252a3d 100%) !important; 
        padding: 18px 20px !important; 
        border-radius: 10px !important; 
        border-left: 4px solid #C5A059 !important; 
        margin-bottom: 10px !important; 
        text-align: left !important; 
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.15) !important; 
    } 

    .m-lbl { 
        color: rgba(255, 255, 255, 0.65) !important; 
        font-family: 'Inter', sans-serif !important; 
        font-size: 10px !important; 
        font-weight: 600 !important; 
        text-transform: uppercase !important; 
        letter-spacing: 1px !important; 
        display: block; 
        margin-bottom: 6px; 
    } 

    .m-val { 
        color: #C5A059 !important; 
        font-family: 'Poppins', sans-serif !important; 
        font-size: 24px !important; 
        font-weight: 700 !important; 
    } 

    /* ============================================ 
       8. RADIO BUTTONS 
       ============================================ */ 
    div.row-widget.stRadio > div { 
        background-color: transparent !important; 
    } 

    div.row-widget.stRadio label { 
        color: #a0a5b5 !important; 
        font-family: 'Inter', sans-serif !important; 
        font-size: 13px !important; 
        padding: 8px 14px !important; 
        border-radius: 6px !important; 
        background: rgba(26, 29, 46, 0.5) !important; 
        border: 1px solid rgba(197, 160, 89, 0.15) !important; 
        transition: all 0.2s ease !important; 
    } 

    div.row-widget.stRadio label:hover { 
        background: rgba(197, 160, 89, 0.1) !important; 
        border-color: rgba(197, 160, 89, 0.3) !important; 
        color: #C5A059 !important; 
    } 

    /* ============================================ 
       9. INPUT BOXES - GOLD BORDER 
       ============================================ */ 
    div[data-baseweb="select"] > div,[data-testid="stFileUploaderSection"] { 
        background-color: #1a1d2e !important; 
        border: 1px solid rgba(197, 160, 89, 0.3) !important; 
        border-radius: 8px !important; 
    } 

    div[data-baseweb="select"] > div:focus-within,[data-testid="stFileUploaderSection"]:focus-within { 
        border-color: #C5A059 !important; 
        box-shadow: 0 0 0 2px rgba(197, 160, 89, 0.15) !important; 
    } 

    div[data-testid="stSelectbox"] div[data-baseweb="select"] *,[data-testid="stFileUploaderText"] > span, 
    [data-testid="stFileUploaderText"] > small { 
        color: #e0e0e0 !important; 
        -webkit-text-fill-color: #e0e0e0 !important; 
    } 

    /* Text inputs */ 
    div[data-baseweb="input"] { 
        background-color: #1a1d2e !important; 
        border: 1px solid rgba(197, 160, 89, 0.3) !important; 
        border-radius: 8px !important; 
        padding: 10px 14px !important; 
    } 

    div[data-baseweb="input"]:focus-within { 
        border-color: #C5A059 !important; 
        box-shadow: 0 0 0 2px rgba(197, 160, 89, 0.15) !important; 
    } 

    input { 
        color: #ffffff !important; 
        font-family: 'Inter', sans-serif !important; 
        font-size: 14px !important; 
    } 

    /* ============================================ 
       10. BUTTONS LAYOUT 
       ============================================ */ 
    [data-testid="stHorizontalBlock"] { 
        display: flex !important; 
        flex-wrap: wrap !important; 
        gap: 10px !important; 
        justify-content: flex-start !important; 
        width: 100% !important; 
    } 

    [data-testid="column"] { 
        flex: 0 1 auto !important; 
        width: auto !important; 
        min-width: fit-content !important; 
        max-width: fit-content !important; 
    } 

    div.stButton > button { 
        width: 170px !important; 
        min-height: 3.3em !important; 
        white-space: normal !important; 
        word-wrap: break-word !important; 
        padding: 10px 14px !important; 
        display: flex !important; 
        align-items: center !important; 
        justify-content: center !important; 
        text-align: center !important; 
        font-size: 13px !important; 
        line-height: 1.3 !important; 
    } 

    /* ============================================ 
       11. SIDEBAR BUTTONS - GOLD THEME 
       ============================================ */ 
    [data-testid="stSidebar"] div.stButton > button { 
        background: linear-gradient(135deg, rgba(197, 160, 89, 0.1) 0%, rgba(197, 160, 89, 0.05) 100%) !important; 
        color: #C5A059 !important; 
        border: 1px solid rgba(197, 160, 89, 0.25) !important; 
        width: 100% !important; 
        height: auto !important; 
        min-height: 42px !important; 
        border-radius: 8px !important; 
        font-family: 'Inter', sans-serif !important; 
        font-weight: 500 !important; 
        font-size: 12px !important; 
        white-space: nowrap !important; 
        transition: all 0.25s ease !important; 
        margin-bottom: 6px !important; 
    }[data-testid="stSidebar"] div.stButton > button:hover { 
        background: linear-gradient(135deg, rgba(197, 160, 89, 0.2) 0%, rgba(197, 160, 89, 0.1) 100%) !important; 
        border-color: #C5A059 !important; 
        color: #FFD700 !important; 
    }[data-testid="stSidebar"] div.stButton > button p { 
        color: inherit !important; 
        font-family: 'Inter', sans-serif !important; 
    } 

    /* ============================================ 
       12. LABELS 
       ============================================ */[data-testid="stWidgetLabel"] p { 
        color: #2d3748 !important; 
        font-family: 'Inter', sans-serif !important; 
        font-weight: 600 !important; 
        font-size: 13px !important; 
    }
    </style>
""", unsafe_allow_html=True)
    # --- JANGAN UBAH KODE DI ATAS, TAMBAHKAN DI BAWAHNYA ---

# 1. Inisialisasi session state login
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- FUNGSI LOGIN (Hanya muncul jika belum logged_in) ---
if not st.session_state.logged_in:
    st.markdown("""
        <style>
        /* 1. Background & Layout */
        .stApp {
            background: linear-gradient(rgba(0,0,0,0.75), rgba(0,0,0,0.75)), 
                        url('https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?q=80&w=2070') !important;
            background-size: cover !important;
        }
        [data-testid="stSidebar"],[data-testid="stHeader"] { display: none !important; }
    

        /* 3. TOMBOL EMAS - PERBAIKAN PADDING */
button[data-testid="stFormSubmitButton"], 
div.stFormSubmitButton > button {
    background: linear-gradient(135deg, #C5A059 0%, #8E6D35 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 12px !important;
    
    /* GANTI BAGIAN INI */
    padding: 18px 20px !important; /* Naikin dari 14px ke 18px biar lega */
    line-height: 1.2 !important;   /* Pastikan teks di tengah vertikal */
    height: auto !important;       /* Biar tinggi tombol ngikutin padding */
    
    font-weight: 800 !important;
    font-size: 16px !important;
    letter-spacing: 1px !important;
    width: 100% !important;
    box-shadow: 0 8px 20px rgba(197, 160, 89, 0.3) !important;
    text-transform: uppercase !important;
}

        /* Paksa warna tetep emas pas kursor nempel */
        button[data-testid="stFormSubmitButton"]:hover {
            background: linear-gradient(135deg, #D4AF37 0%, #C5A059 100%) !important;
            color: #1e1e2f !important;
            box-shadow: 0 20px 25px rgba(197, 160, 89, 0.5) !important;
            transform: translateY(-2px);
        }

        /* 4. Input Box biar gelap & elegan - PERBAIKAN UTAMA DISINI */
        /* container input */
        div[data-baseweb="input"] {
            background-color: #1a2634 !important;
            border: 1px solid #C5A059 !important;
            border-radius: 10px !important;
            padding: 8px 12px !important;
        }
        
        /* container input focus */
        div[data-baseweb="input"]:focus-within {
            border-color: #D4AF37 !important;
            box-shadow: 0 0 0 2px rgba(212, 175, 55, 0.2) !important;
        }
        
        /* input field (termasuk password) */
        input[type="text"], 
        input[type="password"],
        input[type="email"],
        div[data-baseweb="input"] input {
            background-color: transparent !important;
            border: none !important;
            color: #C5A059 !important;
            font-weight: 600 !important;
            font-size: 15px !important;
            padding: 0 !important;
            margin: 0 !important;
            width: 100% !important;
            outline: none !important;
            box-shadow: none !important;
        }
        
        /* placeholder styling */
        input::placeholder {
            color: rgba(197, 160, 89, 0.5) !important;
            opacity: 1 !important;
        }
        
        /* Firefox placeholder */
        input::-webkit-input-placeholder {
            color: rgba(197, 160, 89, 0.5) !important;
        }
        
        /* password field dots styling */
        input[type="password"] {
            letter-spacing: 2px !important;
        }

        /* Label styling */
        [data-testid="stWidgetLabel"] p {
            color: #E0E0E0 !important;
            font-weight: 600 !important;
            font-size: 14px !important;
            margin-bottom: 8px !important;
        }

        /* Form spacing */
        .stForm {
            background-color: transparent !important;
            border: none !important;
        }
        
        /* Input wrapper styling */
        div[data-testid="stTextInput"] div[data-baseweb="input"] {
            background-color: #1a2634 !important;
            border: 1px solid #C5A059 !important;
            border-radius: 10px !important;
            padding: 12px 16px !important;
            min-height: 50px !important;
        }
        
        /* Pastikan password dots terlihat jelas */
        div[data-testid="stTextInput"] input {
            color: #C5A059 !important;
            -webkit-text-fill-color: #C5A059 !important;
        }

        /* Hilangkan background overlay Streamlit */
        .stTextInput > div > div {
            background-color: transparent !important;
        }

        /* Ubah background st.success jadi hijau solid */
    div[data-testid="stNotification"] {
        background-color: #1e7e34 !important; /* Hijau Tua Surabaya */
        color: white !important;               /* Tulisan Putih */
        border-radius: 10px !important;
        border: 1px solid #C5A059 !important;  /* Kasih border emas dikit biar matching */
    }
    /* Pastikan ikon centangnya juga putih */
    div[data-testid="stNotification"] svg {
        fill: white !important;
    }
    
    </style>
    """, unsafe_allow_html=True)
    # UI Login Center
    _, col_mid, _ = st.columns([1, 2, 1])
    with col_mid:
        # Buka Container Card
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        
        # JUDUL
        st.markdown("""
            <h2 style="
                color: #C5A059; 
                margin-top: -60px; 
                margin-bottom: -5px; 
                font-family: 'Inter', sans-serif; 
                font-weight: 800; 
                text-align: center;
            ">SURABAYA DISTRIBUTION
            CENTER WAREHOUSE</h2>
        """, unsafe_allow_html=True)
        
        # SUB-JUDUL
        st.markdown("""
            <p style="
                color: #FFFFFF; 
                font-size: 14px; 
                margin-bottom: 15px; 
                text-align: center;
            ">🟢Warehouse Management System🟢</p>
        """, unsafe_allow_html=True)

       # BUNGKUS FORM
        with st.form("login_form"):
            user_input = st.text_input("Username", key="user_field", placeholder="Masukkan username")
            pass_input = st.text_input("Password", type="password", key="pass_field", placeholder="Masukkan password")
            
            st.markdown('<div style="margin-top: 20px;"></div>', unsafe_allow_html=True)
            
            submit_button = st.form_submit_button("SIGN IN TO SYSTEM")
            
            # Baris di bawah ini harus sejajar lurus dengan submit_button di atas
            if submit_button:
                if user_input == "admin" and pass_input == "sby123":
                    st.session_state.logged_in = True
                    st.toast("Berhasil Login! Selamat datang kembali.", icon="✅")
                    st.rerun()
                else:
                    st.error("Username atau Password salah!")
        
        # Tutup Container Card
        st.markdown('</div>', unsafe_allow_html=True)

    st.stop()
# --- DASHBOARD UTAMA (Jalan setelah login) ---

# Cek apakah notifikasi sudah pernah muncul
if 'login_success' not in st.session_state:
    st.toast("Berhasil Login! Selamat datang di dashboard.", icon="✅")
    # Set True supaya pas klik menu lain di dashboard, pop-up gak muncul terus-terusan
    st.session_state.login_success = True


# Setelah login berhasil, st.stop() akan dilewati dan CSS dashboard lu bakal jalan 100% normal.

# =========================================================
# 1. FUNGSI PENDUKUNG & LOGIC (UTUH TANPA DIPOTONG)
# =========================================================

def get_yellow_skus(file, column_index):
    yellow_set = set()
    try:
        wb = load_workbook(file, data_only=True)
        ws = wb.active
        for row_idx in range(2, ws.max_row + 1):
            cell = ws.cell(row=row_idx, column=column_index)
            color = str(cell.fill.start_color.index)
            if color in['FFFF0000', 'FFFFFF00', 'FFFF00', '00FFFF00']:
                sku_val = str(cell.value).strip().upper() if cell.value else ""
                if sku_val: yellow_set.add(sku_val)
    except: pass
    return yellow_set

def logic_cek_adjustment_final(df_recon, df_stock_adj):
    df_s = df_stock_adj.copy()
    
    def super_clean(val):
        if pd.isna(val) or str(val).strip().lower() in ['nan', 'null', '']: return ""
        s = str(val).strip().upper()
        if s.endswith('.0'): s = s[:-2]
        return s

    # 1. Bikin Key BIN|SKU di Stock
    df_s['JOIN_KEY'] = df_s.iloc[:, 1].fillna('').astype(str).apply(super_clean) + "|" + \
                       df_s.iloc[:, 2].fillna('').astype(str).apply(super_clean)

    # 2. Map Recon (BIN|SKU -> QTY)
    recon_map = {}
    for _, row in df_recon.iterrows():
        b, s = super_clean(row.iloc[0]), super_clean(row.iloc[1])
        q = pd.to_numeric(row.iloc[6], errors='coerce') or 0
        if b and s and q > 0:
            recon_map[f"{b}|{s}"] = q

    # 3. Hitung QTY SO & DIFF
    new_qty_so = df_s['JOIN_KEY'].map(recon_map)
    sys_qty = pd.to_numeric(df_s.iloc[:, 9], errors='coerce').fillna(0)
    new_diff = np.where(new_qty_so.notna(), (sys_qty - new_qty_so.fillna(0)).abs(), np.nan)

    # --- JALUR PAKSA: HAPUS & TEMPEL (Fix Error Dtype Str) ---
    cols_to_keep =[i for i in range(len(df_s.columns)) if i not in [10, 11]]
    df_final_stock = df_s.iloc[:, cols_to_keep].copy()
    df_final_stock.insert(10, "QTY SO", new_qty_so.fillna(0))
    df_final_stock.insert(11, "DIFF", new_diff)

    # 4. Kumpulin SKU "Missing" (Yang BIN|SKU-nya gak match di Stock)
    matched_keys = set(df_s[new_qty_so.notna()]['JOIN_KEY'])
    df_missing = df_recon[df_recon.apply(lambda x: f"{super_clean(x.iloc[0])}|{super_clean(x.iloc[1])}" not in matched_keys, axis=1)].copy()

    if 'JOIN_KEY' in df_final_stock.columns:
        df_final_stock = df_final_stock.drop(columns=['JOIN_KEY'])

    return df_final_stock, df_missing
def logic_pivot_adjustment(df_stock_final, df_staging_inbound, df_recon_missing):
    def super_clean(val):
        if pd.isna(val) or str(val).strip().lower() in ['nan', 'null', '']: return ""
        s = str(val).strip().upper()
        return s

    pivot_list = [] # Buat Multiple
    single_list =[] # Buat Single

    # A. DARI STOCK (Yang Match BIN|SKU & Selisih Plus)
    df_s = df_stock_final.copy()
    q_so = pd.to_numeric(df_s["QTY SO"], errors='coerce').fillna(0)
    q_sys = pd.to_numeric(df_s.iloc[:, 9], errors='coerce').fillna(0)
    
    mask_plus = (q_so > q_sys) & (df_s["DIFF"].notna())
    if mask_plus.any():
        for idx, r in df_s[mask_plus].iterrows():
            pivot_list.append({'SKU_KEY_TEMP': super_clean(r.iloc[2]), 'QTY_TOTAL': pd.to_numeric(r["DIFF"], errors='coerce')})

    # B. LOOKUP SKU MISSING KE INBOUND (Hanya cek SKU)
    inbound_master = df_staging_inbound.copy()
    inbound_skus_set = {super_clean(x) for x in inbound_master.iloc[:, 2].unique() if super_clean(x)}

    if df_recon_missing is not None and not df_recon_missing.empty:
        for _, row in df_recon_missing.iterrows():
            s_recon = super_clean(row.iloc[1])
            q_recon = pd.to_numeric(row.iloc[6], errors='coerce') or 0
            if not s_recon or q_recon <= 0: continue

            if s_recon in inbound_skus_set:
                # KETEMU SKU DI INBOUND -> MASUK MULTIPLE
                pivot_list.append({'SKU_KEY_TEMP': s_recon, 'QTY_TOTAL': q_recon})
            else:
                # GAK ADA DI MANA-MANA -> SINGLE
                single_list.append({'BIN': row.iloc[0], 'SKU': row.iloc[1], 'QTY ADJ': q_recon})

    # C. PIVOT & MERGE KE MASTER INBOUND
    df_mult_res = pd.DataFrame()
    if pivot_list:
        df_p = pd.DataFrame(pivot_list)
        df_p_grouped = df_p.groupby('SKU_KEY_TEMP')['QTY_TOTAL'].sum().reset_index()
        
        inbound_master['SKU_JOIN'] = inbound_master.iloc[:, 2].apply(super_clean)
        m_clean = inbound_master.drop_duplicates(subset=['SKU_JOIN'])
        
        df_mult_res = df_p_grouped.merge(m_clean, left_on='SKU_KEY_TEMP', right_on='SKU_JOIN', how='left')
        
        if not df_mult_res.empty:
            # Update QTY kolom terakhir (Inbound Format)
            df_mult_res.iloc[:, -2] = df_mult_res['QTY_TOTAL']
            df_mult_res = df_mult_res.drop(columns=['SKU_KEY_TEMP', 'QTY_TOTAL', 'SKU_JOIN'], errors='ignore')

    df_sing_res = pd.DataFrame(single_list) if single_list else pd.DataFrame(columns=['BIN', 'SKU', 'QTY ADJ'])

    return df_mult_res, df_sing_res

def logic_setup_real_plus(df_stock_final, df_multiple_adj_plus, df_recon_missing=None):
    def clean_val(x):
        if pd.isna(x): return ""
        s = str(x).strip().upper()
        if s.startswith("SPE"): s = s[3:] 
        if s.endswith('.0'): s = s[:-2]
        return s

    # 1. Dictionary dari MULTIPLE ADJ + (Untuk validasi barang ijin masuk)
    dict_multi = {}
    if not df_multiple_adj_plus.empty:
        for _, row in df_multiple_adj_plus.iterrows():
            sku = clean_val(row.iloc[2])
            bin_asal = row.iloc[1]
            if sku != "" and sku not in dict_multi:
                dict_multi[sku] = bin_asal

    setup_real_data =[]
    seen_entry = set()

    # --- A. AMBIL DARI DF_STOCK_FINAL (Data Sistem) ---
    df_stock = df_stock_final.copy()
    qty_system = pd.to_numeric(df_stock.iloc[:, 9], errors='coerce').fillna(0)
    qty_so = pd.to_numeric(df_stock.iloc[:, 10], errors='coerce').fillna(0)
    diff_val = pd.to_numeric(df_stock.iloc[:, 11], errors='coerce').fillna(0)

    for i in range(len(df_stock)):
        if qty_so.iloc[i] > qty_system.iloc[i]:
            sku_key = clean_val(df_stock.iloc[i, 2])
            bin_tujuan = df_stock.iloc[i, 1]
            
            if sku_key in dict_multi:
                setup_real_data.append({
                    "BIN AWAL": dict_multi[sku_key],
                    "BIN TUJUAN": bin_tujuan,
                    "SKU": sku_key,
                    "QUANTITY": diff_val.iloc[i],
                    "NOTES": "RELOCATION"
                })
                seen_entry.add(f"{sku_key}|{bin_tujuan}")

    # --- B. AMBIL DARI TAB MISSING (Data Ghaib di Sistem) ---
    if df_recon_missing is not None and not df_recon_missing.empty:
        for _, row_m in df_recon_missing.iterrows():
            bin_tujuan_m = row_m.iloc[0] # Kolom BIN
            sku_raw_m = row_m.iloc[1]    # Kolom SKU
            sku_key_m = clean_val(sku_raw_m)
            qty_m = pd.to_numeric(row_m.iloc[6], errors='coerce') or 0

            # Cek jika SKU ada di daftar ijin tapi belum masuk di proses A
            if sku_key_m in dict_multi and f"{sku_key_m}|{bin_tujuan_m}" not in seen_entry:
                setup_real_data.append({
                    "BIN AWAL": "STAGING INBOUND", # Default asal buat item missing
                    "BIN TUJUAN": bin_tujuan_m,
                    "SKU": sku_key_m,
                    "QUANTITY": qty_m,
                    "NOTES": "RELOCATION (MISSING)"
                })

    result_df = pd.DataFrame(setup_real_data)
    if result_df.empty:
        return pd.DataFrame(columns=["BIN AWAL", "BIN TUJUAN", "SKU", "QUANTITY", "NOTES"])
    
    return result_df[["BIN AWAL", "BIN TUJUAN", "SKU", "QUANTITY", "NOTES"]]

def logic_setup_karantina_with_compare(df_outstanding, df_recon):
    def clean_val(x):
        if pd.isna(x): return ""
        s = str(x).strip().upper()
        # Sesuai preferensi user: hapus prefix SPE jika ada
        if s.startswith("SPE"): s = s[3:].strip() 
        if s.endswith('.0'): s = s[:-2]
        return s

    # 1. Mapping QTY SYSTEM dari file CEK ADJUSTMENT (Uploader 2) -> Kolom J (Index 9)
    sys_map = {}
    if df_recon is not None and not df_recon.empty:
        for _, row in df_recon.iterrows():
            try:
                # Key: BIN (Kolom B/Index 1) | SKU (Kolom C/Index 2)
                k_sys = f"{clean_val(row.iloc[1])}|{clean_val(row.iloc[2])}" 
                val_sys = pd.to_numeric(row.iloc[9], errors='coerce') 
                sys_map[k_sys] = val_sys if not pd.isna(val_sys) else 0
            except: continue

    # 2. Mapping QTY RECON dari file SYSTEM + OUTSTANDING (Uploader 1) -> Kolom N (Index 13)
    recon_map = {}
    if df_outstanding is not None and not df_outstanding.empty:
        for _, row in df_outstanding.iterrows():
            try:
                # Key: BIN (Kolom B/Index 1) | SKU (Kolom C/Index 2)
                k_rec = f"{clean_val(row.iloc[1])}|{clean_val(row.iloc[2])}" 
                val_rec = pd.to_numeric(row.iloc[13], errors='coerce') 
                recon_map[k_rec] = val_rec if not pd.isna(val_rec) else 0
            except: continue

    # 3. Proses Comparison
    df_master = df_outstanding.copy()
    audit_results = []
    karantina_results =[]

    for _, row in df_master.iterrows():
        bin_val = row.iloc[1]
        sku_val = row.iloc[2]
        key = f"{clean_val(bin_val)}|{clean_val(sku_val)}"
        
        q_system = sys_map.get(key, 0)
        q_recon = recon_map.get(key, 0)
        diff = q_system - q_recon

        # TAB PENGECEKAN: Semua selisih (Plus/Minus) masuk sini buat audit
        if diff != 0:
            audit_results.append({
                'BIN': bin_val,
                'SKU': sku_val,
                'QTY_SYSTEM_J': q_system,
                'QTY_RECON_N': q_recon,
                'SELISIH': diff
            })

            # TAB SET UP KARANTINA: HANYA YANG POSITIF (> 0)
            # Nilai minus tidak akan dimasukkan ke list hasil karantina
            if diff > 0:
                karantina_results.append({
                    "BIN AWAL": bin_val,
                    "BIN TUJUAN": "KARANTINA",
                    "SKU": sku_val,
                    "QUANTITY": diff,
                    "NOTES": "MISS LOCATION"
                })

    # 4. Output DataFrames
    # Hasil Karantina sudah bersih dari minus
    df_karantina = pd.DataFrame(karantina_results)
    # Hasil Audit tetep lengkap
    df_check = pd.DataFrame(audit_results) if audit_results else pd.DataFrame(columns=['BIN','SKU','QTY_SYSTEM_J','QTY_RECON_N','SELISIH'])

    return df_karantina, df_check
    
def clean_sku_bin(series):
    """Fungsi helper untuk memastikan SKU/BIN tetap string dan bersih."""
    return (series.astype(str)
            .str.replace(r'\.0$', '', regex=True) # Menghilangkan .0 di ujung SKU jika ada
            .str.replace(r'\s+', ' ', regex=True) # Spasi ganda jadi tunggal
            .str.strip() 
            .str.upper())

def logic_compare_scan_to_stock(df_scan, df_stock):
    # 1. Ambil kolom & Copy
    ds = df_scan.iloc[:, [0, 1, 2]].copy()
    ds.columns = ['BIN', 'SKU', 'QTY_SCAN']
    
    dt = df_stock.iloc[:, [1, 2, 9]].copy()
    dt.columns = ['BIN', 'SKU', 'QTY_SYSTEM']

    # 2. Pembersihan Robust
    for df in [ds, dt]:
        df['BIN'] = clean_sku_bin(df['BIN'])
        df['SKU'] = clean_sku_bin(df['SKU'])
    
    # 3. Paksa QTY jadi Angka
    ds['QTY_SCAN'] = pd.to_numeric(ds['QTY_SCAN'], errors='coerce').fillna(0)
    dt['QTY_SYSTEM'] = pd.to_numeric(dt['QTY_SYSTEM'], errors='coerce').fillna(0)

    # 4. Grouping Data System (SUMIFS) - Pastikan dijumlah dulu sebelum merge
    dt_grouped = dt.groupby(['BIN', 'SKU'], as_index=False)['QTY_SYSTEM'].sum()
    
    # 5. Merge
    ds_merged = ds.merge(dt_grouped, on=['BIN', 'SKU'], how='left').fillna(0)
    
    # 6. Hitung Selisih
    ds_merged['DIFF'] = ds_merged['QTY_SCAN'] - ds_merged['QTY_SYSTEM']
    ds_merged['NOTE'] = ds_merged['DIFF'].apply(lambda x: "REAL +" if x > 0 else ("SYSTEM +" if x < 0 else "OK"))
    
    return ds_merged

def logic_compare_stock_to_scan(df_stock, df_scan):
    dt = df_stock.copy()
    
    # 1. Siapkan Data Scan & Grouping
    ds = df_scan.iloc[:, [0, 1, 2]].copy()
    ds.columns =['BIN_SCAN', 'SKU_SCAN', 'QTY_TOTAL_SCAN']
    
    # Cleaning Data Scan
    ds['BIN_SCAN'] = clean_sku_bin(ds['BIN_SCAN'])
    ds['SKU_SCAN'] = clean_sku_bin(ds['SKU_SCAN'])
    ds['QTY_TOTAL_SCAN'] = pd.to_numeric(ds['QTY_TOTAL_SCAN'], errors='coerce').fillna(0)
    
    # AGREGASI: Ini kunci agar tidak duplikat saat merge
    ds_grouped = ds.groupby(['BIN_SCAN', 'SKU_SCAN'], as_index=False)['QTY_TOTAL_SCAN'].sum()

    # 2. Identifikasi Kolom System
    col_bin_sys = dt.columns[1]
    col_sku_sys = dt.columns[2]
    col_qty_sys = dt.columns[9]
    col_qty_so  = dt.columns[10] 

    # 3. Cleaning Data System
    dt[col_bin_sys] = clean_sku_bin(dt[col_bin_sys])
    dt[col_sku_sys] = clean_sku_bin(dt[col_sku_sys])
    dt[col_qty_sys] = pd.to_numeric(dt[col_qty_sys], errors='coerce').fillna(0)

    # 4. Merge
    dt_merged = dt.merge(
        ds_grouped, 
        left_on=[col_bin_sys, col_sku_sys], 
        right_on=['BIN_SCAN', 'SKU_SCAN'], 
        how='left'
    )

    # 5. Kalkulasi
    dt_merged[col_qty_so] = dt_merged['QTY_TOTAL_SCAN'].fillna(0)
    dt_merged['DIFF'] = dt_merged[col_qty_sys] - dt_merged[col_qty_so]
    dt_merged['NOTE'] = dt_merged['DIFF'].apply(lambda x: "SYSTEM +" if x > 0 else ("REAL +" if x < 0 else "OK"))
    
    return dt_merged.drop(columns=['BIN_SCAN', 'SKU_SCAN', 'QTY_TOTAL_SCAN'])
def logic_run_allocation(df_real_plus, df_system_plus, df_bin_coverage):
    # 1. Siapkan data sumber dalam dictionary
    system_dict = {}
    for _, row in df_system_plus.iterrows():
        key = (str(row['BIN']).strip().upper(), str(row['SKU']).strip().upper())
        system_dict[key] = system_dict.get(key, 0) + row.get('DIFF', 0)
    
    # Ambil daftar BIN yang lolos filter UI (Benerin chaining .str)
    selected_bins = set(df_bin_coverage.iloc[:, 1].astype(str).str.strip().str.upper().unique())

    coverage_dict = {}
    for _, row in df_bin_coverage.iterrows():
        # Kolom: index 1=BIN, index 2=SKU, index 9=QTY
        bin_val = str(row.iloc[1]).strip().upper()
        sku_val = str(row.iloc[2]).strip().upper()
        
        # PERBAIKAN TOTAL: Cuma masukin ke dict kalau BIN-nya ada di list filter
        if bin_val in selected_bins:
            key = (bin_val, sku_val)
            try: val = float(row.iloc[9])
            except: val = 0
            coverage_dict[key] = coverage_dict.get(key, 0) + val

    # 2. List untuk menampung baris baru
    new_rows =[]
    df_sys_updated = df_system_plus.copy()
    sys_reduction = defaultdict(float)

    for _, row in df_real_plus.iterrows():
        sku = str(row['SKU']).strip().upper()
        diff_needed = row['DIFF']
        
        if diff_needed <= 0:
            row_copy = row.to_dict()
            row_copy.update({'BIN ALOKASI': '', 'QTY ALLOCATION': 0, 'STATUS': 'NO DIFF'})
            new_rows.append(row_copy)
            continue

        remaining = diff_needed
        
        # --- TAHAP 1: Cari di System Dictionary ---
        for (bin_src, sku_src), qty_avail in system_dict.items():
            if remaining <= 0: break
            if sku_src == sku and qty_avail > 0:
                alloc = min(qty_avail, remaining)
                
                row_alloc = row.to_dict()
                row_alloc.update({
                    'BIN ALOKASI': bin_src,
                    'QTY ALLOCATION': alloc,
                    'STATUS': 'FULL ALLOCATION' if alloc == remaining else 'PARTIAL ALLOCATION'
                })
                new_rows.append(row_alloc)
                
                system_dict[(bin_src, sku_src)] -= alloc
                sys_reduction[(bin_src, sku_src)] += alloc
                remaining -= alloc

        # --- TAHAP 2: Cari di Coverage Dictionary (DENGAN FILTER BIN KETAT) ---
        if remaining > 0:
            for (bin_src, sku_src), qty_avail in coverage_dict.items():
                if remaining <= 0: break
                # Karena dict sudah difilter di awal, ini buat double safety
                if bin_src in selected_bins and sku_src == sku and qty_avail > 0:
                    alloc = min(qty_avail, remaining)
                    
                    row_alloc = row.to_dict()
                    row_alloc.update({
                        'BIN ALOKASI': bin_src,
                        'QTY ALLOCATION': alloc,
                        'STATUS': 'FULL ALLOCATION' if alloc == remaining else 'PARTIAL ALLOCATION'
                    })
                    new_rows.append(row_alloc)
                    
                    coverage_dict[(bin_src, sku_src)] -= alloc
                    remaining -= alloc

        # --- TAHAP 3: Jika Masih Sisa (NO ALLOCATION) ---
        if remaining > 0:
            row_no = row.to_dict()
            row_no.update({
                'DIFF': remaining,
                'BIN ALOKASI': '',
                'QTY ALLOCATION': 0,
                'STATUS': 'NO ALLOCATION'
            })
            new_rows.append(row_no)

    # 3. Convert kembali ke DataFrame
    df_result = pd.DataFrame(new_rows)

    # 4. Update df_sys_updated
    for (b, s), q in sys_reduction.items():
        mask = (df_sys_updated['BIN'].astype(str).str.upper() == b) & \
               (df_sys_updated['SKU'].astype(str).str.upper() == s)
        if mask.any():
            df_sys_updated.loc[mask, 'DIFF'] -= q

    return df_result, df_sys_updated

def generate_set_up_real_plus(allocated_data):
    filtered = allocated_data[allocated_data['STATUS'].isin(['FULL ALLOCATION', 'PARTIAL ALLOCATION'])].copy()
    if not filtered.empty:
        filtered['BIN AWAL'], filtered['BIN TUJUAN'], filtered['QUANTITY'], filtered['NOTES'] = filtered['BIN ALOKASI'], filtered['BIN'], filtered['QTY ALLOCATION'], "RELOCATION"
        return filtered[['BIN AWAL', 'BIN TUJUAN', 'SKU', 'QUANTITY', 'NOTES']]
    return pd.DataFrame(columns=['BIN AWAL', 'BIN TUJUAN', 'SKU', 'QUANTITY', 'NOTES'])

def generate_real_plus_recon(allocated_data):
    filtered = allocated_data[allocated_data['STATUS'] == "NO ALLOCATION"].copy()
    if not filtered.empty:
        recon_df = filtered[['BIN', 'SKU', 'ITEM NAME', 'QTY_SCAN', 'QTY_SYSTEM', 'DIFF']].copy()
        recon_df['HASIL RECONCILIATION'] = ""
        return recon_df
    return pd.DataFrame(columns=['BIN', 'SKU', 'ITEM NAME', 'QTY SCAN', 'QTY SYSTEM', 'DIFF', 'HASIL RECONCILIATION'])

def logic_miss_location_report(df_setup_real):
    # Header standar sesuai Macro VBA
    columns_ref = ["BIN SYSTEM +", "BIN REAL +", "SKU", "QTY MISS LOC."]
    
    # Cek jika data kosong atau None
    if df_setup_real is None or not isinstance(df_setup_real, pd.DataFrame) or df_setup_real.empty:
        return pd.DataFrame(columns=columns_ref), 0, 0
    
    try:
        df_out = df_setup_real.iloc[:, 0:4].copy()
        df_out.columns = columns_ref
        df_out["QTY MISS LOC."] = pd.to_numeric(df_out["QTY MISS LOC."], errors='coerce').fillna(0)
        
        total_sku = df_out["SKU"].nunique()
        total_qty = int(df_out["QTY MISS LOC."].sum())
        
        return df_out, total_sku, total_qty
    except:
        return pd.DataFrame(columns=columns_ref), 0, 0

def logic_sum_adjustment_final(df_plus_current, df_minus_current, up_plus=None, up_minus=None):
    """
    Logic Hybrid: 
    1. Jika ada file upload (up_plus/up_minus), pakai data dari file tersebut.
    2. Jika tidak ada upload, pakai data current (yang sedang diolah aplikasi).
    """
    cols_header =[
        "BIN", "SKU", "BRAND", "ITEM NAME", "VARIANT", 
        "SUB KATEGORI", "HARGA BELI", "HARGA JUAL", 
        "QTY SYSTEM", "QTY SO", "VALUE ADJ", "STATUS ADJ"
    ]

    def get_active_df(current_df, uploaded_file):
        # Jika ada file yang di-upload, baca file tersebut
        if uploaded_file is not None:
            try:
                uploaded_file.seek(0)
                if uploaded_file.name.endswith(('.xlsx', '.xls')):
                    return pd.read_excel(uploaded_file)
                else:
                    return pd.read_csv(uploaded_file)
            except:
                return current_df # Balik ke current jika file corrupt
        return current_df # Pakai data aplikasi jika tidak ada upload

    def process_data(df, status):
        if df is None or (isinstance(df, pd.DataFrame) and df.empty):
            return pd.DataFrame(columns=cols_header)
        
        # Ambil kolom yang dibutuhkan (Indeks 1-10 sesuai standar VBA lu)
        temp = df.iloc[:, 1:11].copy() 
        temp.columns = cols_header[:10]
        
        # Pastikan numerik untuk perhitungan
        for col in ["HARGA BELI", "QTY SO", "QTY SYSTEM"]:
            temp[col] = pd.to_numeric(temp[col], errors='coerce').fillna(0)

        # Hitung Value Adj
        temp["VALUE ADJ"] = (temp["QTY SO"] - temp["QTY SYSTEM"]) * temp["HARGA BELI"]
        temp["STATUS ADJ"] = status
        return temp

    # Pilih Sumber Data: Prioritas Upload > Current Data
    active_plus = get_active_df(df_plus_current, up_plus)
    active_minus = get_active_df(df_minus_current, up_minus)

    # Proses Data
    df_adj_plus = process_data(active_plus, "ADJ +")
    df_adj_minus = process_data(active_minus, "ADJ -")

    # Gabung untuk report total
    df_final = pd.concat([df_adj_plus, df_adj_minus], ignore_index=True)

    # --- HITUNG SUMMARY ---
    val_plus = df_adj_plus["VALUE ADJ"].sum() if not df_adj_plus.empty else 0
    val_minus = df_adj_minus["VALUE ADJ"].sum() if not df_adj_minus.empty else 0
    
    qty_plus = (df_adj_plus["QTY SO"] - df_adj_plus["QTY SYSTEM"]).abs().sum() if not df_adj_plus.empty else 0
    qty_minus = -(df_adj_minus["QTY SO"] - df_adj_minus["QTY SYSTEM"]).abs().sum() if not df_adj_minus.empty else 0

    df_sum = pd.DataFrame({
        "METRIC":[
            "Total SKU Adj.", "Total Value Adj. +", "Total Value Adj. -", 
            "Total QTY Adj. +", "Total QTY Adj. -", "Total Value", "Total QTY"
        ],
        "VALUE":[
            len(df_final[df_final["SKU"].astype(str).str.strip() != ""]),
            val_plus, val_minus, qty_plus, qty_minus,
            val_plus + val_minus,
            qty_plus + qty_minus
        ]
    })

    return df_final, df_sum
# =========================================================
# 2. MENU UTAMA & STATE MANAGEMENT
# =========================================================

def menu_Stock_Opname():
    st.markdown("""
        <style>
         .hero-header { background-color: #0E1117; padding: 20px; border-radius: 10px; margin-bottom: 20px; text-align: center; border: 1px solid #333; }
         .hero-header h1 { color: #FF4B4B; margin: 0; font-size: 32px; }
         .m-box { background: #262730; padding: 15px; border-radius: 8px; border: 1px solid #464855; text-align: center; flex: 1; }
         .m-lbl { display: block; font-size: 12px; color: #808495; margin-bottom: 5px; }
         .m-val { font-size: 20px; font-weight: bold; color: white; }
        </style>
    """, unsafe_allow_html=True)
    st.markdown('<div class="hero-header"><h1> STOCK OPNAME ANALYZER</h1></div>', unsafe_allow_html=True)
    with st.expander("📋 Informasi Format File"):
        st.info("""
        **Format yang diharapkan:**
        - **FILTER**
            - **SUB KATEGORI**
                - Untuk Sub Kategori pilih sesuai dengan kategori yang sedang dianalisa
            - **BIN SYSTEM**
                - Untuk BIN system pilih sesuai dengan bin yang sedang dianalisa
            - **BIN COVERAGE**
                - Untuk BIN COVERAGE sementara non aktifkan dulu dan jangan dipilih
        - **COMPARE DS VS STOCK SYSTEM**
            - **DATA SCAN**: Upload data scan SO yang sudah diberi header :
                - **Kolom A** = BIN
                - **Kolom B** = SKU
                - **Kolom C** = QTY SCAN
            - **STOCK SYSTEM**
                - Download All stock dari **Multiple Adjusment** dan pilih **Termasuk yang sudah habis**
        - **BIN COVERAGE**
            - Download Bin Coverage  dari **Multiple Adjusment**
            - Pilih stocknya **Hanya ada di stock**
        - **FINAL ADJUSMENT + PROCESS**
            - **REAL + RECON**
                - Upload file Recon Real + yang sudah diupload dari step sebelumnya pastikan **KOLOM A** bukan berisi **NUMBER** ➡️ jika berisi Number maka hapus dulu kolomnya sebelum diupload
            - **CEK STOCK ADJ +**
                - Download Stock System yang terbaru dari **Multiple Adjusment** dan pilih **Termasuk yang sudah habis**
            - **STOCK ADJ + (MASTER)**
                - Download Stock System dan pilih hanya *BIN STAGGING INBOUND* dan pilih **Termasuk yang sudah habis**
        - **SET UP KARANTINA GENERATOR**
            - **SYTEM + RECON**
                - Upload file Recon System + yang sudah diupload dari step sebelumnya pastikan **KOLOM A** bukan berisi **NUMBER** ➡️ jika berisi Number maka hapus dulu kolomnya sebelum diupload
            - **CEK STOCK ADJ -**
                - Download Stock System yang terbaru dari *Multiple Adjusment** dan pilih **Termasuk yang sudah habis**
        - **SUMMARY ADJUSMENT REPORT**
            - **OPSI 1**
                - Jika ingin mengetahui value adjusment saat proses running bisa langsung klik tombol **▶️ SUMMARY ADJUSMENT** tanpa upload file**
            - **OPSI 2**
                - Jika ingin mengetahui value adjusment total + dari all bin maka **Gabungkan All Adjusment +** untuk all bin lalu klik tombol **▶️ SUMMARY ADJUSMENT** tanpa upload file Adjusment (-)**
            - **OPSI 3**
                - Jika ingin mengetahui value adjusment total - dari all bin maka **Gabungkan All Adjusment -** untuk all bin lalu klik tombol **▶️ SUMMARY ADJUSMENT** tanpa upload file Adjusment (+)**
            - **OPSI 4**
                - Jika ingin mengetahui value adjusment total dari + dan - secara keseluruhan maka **Gabungkan All Adjusment + & - ** untuk all bin lalu klik tombol **▶️ SUMMARY ADJUSMENT**
        """)
    with st.expander("💡Logic Thinking"):
        st.info("""
        **DS VS Stock System :**
        - **REAL +**
            - Compare antara SKU dan BIN yang ada di data scan dengan SKU dan BIN yang ada di Stock System dimana logic yang digunakan menggunakan loigc rumus (SUMIFS)
            - Fokus di file Data Scan karena yang akan menjadi acuan untuk Real +
            - Apabila **QTY SCAN > QTY SYSTEM** maka yang akan dijadikan sebagai Real +

        **Stock Sytem VS DS :**
        - **SYSTEM +**
            - Jika tadi berfokus pada file Data maka untuk system + berfokus pada file Stock System
            - Apabila **QTY SYSTEM > QTY SCAN** maka akan dijadikan sebagai System +

        **ALLOCATION REAL + :**
        - **BIN COVERAGE**
            - Compare antara SKU yang ada di Real + dengan SKU yang ada BIN Coverage jika SKU ditemukan maka akan diambil untuk cover system di REAL +
            - Jika DIFF real + dapat tercover penuh maka akan diberi note **FULL ALLOCATION**
            - Jika DIFF real + hanya tercover sebagian maka akan diberi note **PARTIAL ALLOCATION**
            - Dan yang tidak dapat tercover sebagian atau tidak tercover secara total maka akan diberi note **NO ALLOCATION**
        - **SYSTEM +**
            - Item memiliki note **NO ALLOCATION** maka apabila tidak ditemukan di BIN COVERAGE akan mencari SKU yang cocok di system +
            - Dan jika ditemukan SKU yang cocok maka note akan sama ketika compare dengan BIN COVERAGE
        - **SET UP ALLOCATION**
            - Item dengan note **FULL ALLOCATION** dan **PARTIAL ALLOCATION** akan dibuatkan list set up dengan note Relocation

        **RECON REAL + & SYSTEM + :**
        - **RECON REAL +**
            - Item yang memiliki note **NO ALLOCATION** akan kembali di lakukan rekonsiliasi apakah item tersebut sesuai dengan total data scan atau hanya double scan
            - Masukkan real yang ditemukan di dalam kolom hasil rekonsiliasi lalu upload
            - Jika **Real yang ditemukan = stock system** maka tidak akan dimasukkan ke list adjusment
            - Jika **Real yang ditemukan > stock system** maka akan dimasukkan ke list adjusment
        - **CEK STOCK ADJUSMENT**
            - Download kembali file multiple adjusment All BIN dan **Termasuk yang sudah habis** untuk dilakukan sumifs antara SKU dan bin hasil recon dengan file multiple terbaru
            - Hal ini dilakukan untuk mendapatkan selisih terupdate untuk dimasukkan ke BIN INBOUND
        - **FILE INBOUND**
            - Jika sudah upload file multiple adjusment **STAGGING INBOUND** maka selisih dari lookup tadi akan dimasukkan ke dalam file inbound untuk nantinya dilakukan proses adjusment
        - **RECON SYSTEM +**
            - System + yang DIFF nya belum teralokasi atau masih memiliki sisa maka akan dilakukan rekonsiliasi apakah item tersebut memang benar systemnya > realnya
            - Masukkan real yang ditemukan di dalam kolom hasil rekonsiliasi lalu upload
            - Jika **Real yang ditemukan = stock system** maka tidak akan dimasukkan ke list adjusment
            - Jika **Real yang ditemukan < stock system** maka akan dimasukkan ke list adjusment
        - **CEK STOCK ADJUSMENT**
            - File Cek adjusment tadi yang sudah di download bisa dimasukkan kembali
            - Logicnya juga tetap sama yaitu dengan melakukan sumifs kemudian akan mengambil diffnya
            - Jika DIFF > 0 maka akan dilakuka mutasi ke **BIN KARANTINA**
        - **SET UP KARANTINA**
            - System akan membuatkan list set up untuk DIFF > 0 dan akan diberikan note **MISS LOCATION**

        **TOTAL MISS LOCATION :**
        - Cek total missloc untuk mengetahui seberapa banyak miss location dari Stock Opname periode tersebut
        - Total miss loc diambil dari berapa banyak SKU dan QTY yang memiliki note **FULL ALLOCATION & PARTIAL ALLOCATION** pada logic Alloacation real +

        **VALUE ADJUSMENT :**
        - Cek Value Adjusment sebagai report dan analisa SO diperiode tersebut
        - Untuk logic Value Adjusment sudah dijelaskan di bagian **INFORMATION FILE**
        """)

    # --- INITIALIZE ALL SESSION STATES ---
    if 'compare_result' not in st.session_state: st.session_state.compare_result = None
    if 'allocation_result' not in st.session_state: st.session_state.allocation_result = None
    if 'set_up_real_plus' not in st.session_state: st.session_state.set_up_real_plus = None
    if 'sys_updated_result' not in st.session_state: st.session_state.sys_updated_result = None
    if 'recon_real_plus' not in st.session_state: st.session_state.recon_real_plus = None
    if 'outstanding_system' not in st.session_state: st.session_state.outstanding_system = None
    
    if 'df_res_lookup' not in st.session_state: st.session_state.df_res_lookup = None
    if 'df_missing_lookup' not in st.session_state: st.session_state.df_missing_lookup = None
    if 'step4_done' not in st.session_state: st.session_state.step4_done = False
    
    if 'df_mult_5' not in st.session_state: st.session_state.df_mult_5 = None
    if 'df_sing_5' not in st.session_state: st.session_state.df_sing_5 = None
    if 'step5_done' not in st.session_state: st.session_state.step5_done = False
    
    if 'df_karantina_6' not in st.session_state: st.session_state.df_karantina_6 = None

    # --- FILTER SECTION ---
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        list_sub_kat =["BAG", "BALL", "BASELAYER", "BOTTLE", "CLEANNING & CARE", "EXTRA SHOES", "HARDWARE", "JACKET", "JERSEY", "LOWER BODY", "NUTRITION", "OTHER", "OTHERS", "PANTS", "RACKET", "SANDALS", "SET APPAREL", "SHIRT", "SHOES", "SHORT", "SWLM", "UKNOWN SC", "UNDERLAYER", "UPPER BODY"]
        selected_sub = st.multiselect("🗂️ Sub Kategori:", list_sub_kat)
    with col_f2:
        list_bin_stock =["GUDANG LT.2", "LIVE", "KL2", "KL1", "GL2-STORE", "GL2-STR", "OFFLINE", "TOKO", "GL1-DC", "RAK ACC LT.1", "GL3-DC-A", "GL3-DC-B", "GL3-DC-C", "GL3-DC-D", "GL3-DC-E", "GL3-DC-F", "GL3-DC-G", "GL3-DC-H", "GL3-DC-I", "GL3-DC-J", "GL4-DC-A", "GL4-DC-B", "GL4-DC-KL", "GL3-DC-RAK", "GL4-DC-RAK", "PUTAWAY", "KEEP AMP", "MARKOM", "DEFECT", "REJECT", "DAU", "KAV-2", "KAV-7", "KAV-8", "KAV-9", "KAV-10", "C-0", "KDR", "GL3-KOLI", "JBR", "GUDANG", "SDA", "GL2-SMG", "GL2-SMG-CTN-","GUDANG LT 2"]
        selected_bin_sys = st.multiselect("🏭 BIN System:", list_bin_stock)
    with col_f3:
        list_bin_cov =["KARANTINA", "STAGGING", "STAGING", "GUDANG LT.2", "TOKO", "GL1-DC", "RAK ACC LT.1", "GL3-DC-A", "GL3-DC-B", "GL3-DC-C", "GL3-DC-D", "GL3-DC-E", "GL3-DC-F", "GL3-DC-G", "GL3-DC-H", "GL3-DC-I", "GL3-DC-J", "GL4-DC-A", "GL4-DC-B", "GL4-DC-KL1", "GL4-DC-KL2", "GL3-DC-RAK", "GL4-DC-RAK", "LIVE", "MARKOM", "AMP", "GL2-STORE", "PUTAWAY", "OUT", "INB"]
        selected_bin_cov = st.multiselect("📡 BIN Coverage:", list_bin_cov)

    st.markdown("---")

    # STEP 1
    st.subheader("1️⃣ Upload & Run Compare")
    c1, c2 = st.columns(2)
    with c1: up_scan = st.file_uploader("📥 DATA SCAN", type=['xlsx','csv'], key="step1_scan")
    with c2: up_stock = st.file_uploader("📥 STOCK SYSTEM", type=['xlsx','csv'], key="step1_stock")

    if up_scan and up_stock:
        if st.button("▶️ RUN COMPARE", use_container_width=True):
            df_s_raw = pd.read_excel(up_scan) if up_scan.name.endswith(('.xlsx', '.xls')) else pd.read_csv(up_scan)
            df_t_raw = pd.read_excel(up_stock) if up_stock.name.endswith(('.xlsx', '.xls')) else pd.read_csv(up_stock)
            
            if selected_sub: df_t_raw = df_t_raw[df_t_raw.iloc[:, 6].astype(str).str.upper().isin([x.upper() for x in selected_sub])]
            if selected_bin_sys: df_t_raw = df_t_raw[df_t_raw.iloc[:, 1].astype(str).str.upper().apply(lambda x: any(c.upper() in x for c in selected_bin_sys))]

            res_scan = logic_compare_scan_to_stock(df_s_raw, df_t_raw)
            res_stock = logic_compare_stock_to_scan(df_t_raw, df_s_raw)
            
            item_map = df_t_raw.iloc[:, [2, 4]].dropna().astype(str)
            item_map.columns = ['SKU', 'NAME']
            map_dict = item_map.drop_duplicates('SKU').set_index('SKU')['NAME'].to_dict()
            res_scan['ITEM NAME'] = res_scan['SKU'].map(map_dict)
            res_stock['ITEM NAME'] = res_stock.iloc[:, 2].astype(str).str.upper().map(map_dict)

            st.session_state.compare_result = {
                'res_scan': res_scan, 'res_stock': res_stock, 
                'real_plus': res_scan[res_scan['NOTE'] == "REAL +"].copy(),
                'system_plus': res_stock[res_stock['NOTE'] == "SYSTEM +"].copy(),
                'map_dict': map_dict
            }
            st.rerun()

    if st.session_state.compare_result:
        d = st.session_state.compare_result
        st.markdown(f"""
            <div style="display: flex; gap: 15px; justify-content: center; margin-bottom: 20px;">
                <div class="m-box"><span class="m-lbl">📦 QTY REAL +</span><span class="m-val">{int(d['real_plus']['DIFF'].sum())}</span></div>
                <div class="m-box"><span class="m-lbl">🔐 QTY SYSTEM +</span><span class="m-val">{int(d['system_plus']['DIFF'].sum())}</span></div>
            </div>
        """, unsafe_allow_html=True)
        t1, t2, t3, t4 = st.tabs(["📋 DATA SCAN", "📊 STOCK SYSTEM", "➕ REAL +", "➖ SYSTEM +"])
        with t1: st.dataframe(d['res_scan'], use_container_width=True)
        with t2: st.dataframe(d['res_stock'], use_container_width=True)
        with t3: st.dataframe(d['real_plus'], use_container_width=True)
        with t4: st.dataframe(d['system_plus'], use_container_width=True)

        st.markdown("---")
        st.subheader("2️⃣ Upload BIN COVERAGE & Run Allocation")
        up_bin_cov = st.file_uploader("📥 FILE BIN COVERAGE", type=['xlsx','csv'], key="step2_cov")
        if up_bin_cov:
            if st.button("▶️ RUN ALLOCATION", use_container_width=True):
                # 1. Baca data original
                df_cov_raw = pd.read_excel(up_bin_cov) if up_bin_cov.name.endswith(('.xlsx', '.xls')) else pd.read_csv(up_bin_cov)
                
                # 2. FILTER DATA BERDASARKAN PILIHAN USER (Logic "Mengandung")
                if selected_bin_cov:
                    import re
                    # Gabungkan pilihan user jadi pattern regex (contoh: "KARANTINA|GL3-DC|GL4-DC")
                    # re.escape gunanya biar karakter spesial kayak titik (.) gak bikin error regex
                    pattern = "|".join([re.escape(str(b).strip().upper()) for b in selected_bin_cov])
                    
                    # Filter: Cari yang mengandung (contains) salah satu pattern di atas
                    # Kolom index 1 (BIN) dipaksa UPPER agar matching-nya akurat
                    mask = df_cov_raw.iloc[:, 1].astype(str).str.strip().str.upper().str.contains(pattern, na=False)
                    df_cov = df_cov_raw[mask].copy()
                else:
                    df_cov = df_cov_raw # Kalau gak pilih apa-apa, hajar semua

                # --- VALIDASI: Kasih peringatan kalau hasil filter kosong ---
                if df_cov.empty and selected_bin_cov:
                    st.error("❌ Data BIN Coverage kosong setelah difilter! Cek lagi pilihan BIN lu.")
                else:
                    # 3. Jalankan logic dengan data yang SUDAH DIFILTER
                    allocated, sys_upd = logic_run_allocation(d['real_plus'], d['system_plus'], df_cov)
                    
                    allocated['ITEM NAME'] = allocated['SKU'].map(d['map_dict'])
                    st.session_state.allocation_result = allocated
                    st.session_state.sys_updated_result = sys_upd
                    st.session_state.set_up_real_plus = generate_set_up_real_plus(allocated)
                    
                    st.success(f"✅ Berhasil! Terfilter {len(df_cov)} baris dari {len(selected_bin_cov)} kriteria BIN.")
                    st.rerun()

    if st.session_state.allocation_result is not None:
        st.markdown("### ✅ HASIL ALOKASI")
        ta1, ta2, ta3 = st.tabs(["📊 ALLOCATION DETAIL", "📉 UPDATED SYSTEM", "📦 SET UP REAL +"])
        with ta1: st.dataframe(st.session_state.allocation_result, use_container_width=True)
        with ta2: st.dataframe(st.session_state.sys_updated_result, use_container_width=True)
        with ta3: st.dataframe(st.session_state.set_up_real_plus, use_container_width=True)

        st.markdown("---")
        st.subheader("3️⃣ RECON REPORTS")
        if st.button("📊 Generate All RECON", use_container_width=True):
            st.session_state.recon_real_plus = generate_real_plus_recon(st.session_state.allocation_result)
            outstanding = st.session_state.sys_updated_result[st.session_state.sys_updated_result['DIFF'] != 0].copy()
            outstanding['HASIL REKONSILIASI'] = ""
            st.session_state.outstanding_system = outstanding
            st.rerun()

    if st.session_state.recon_real_plus is not None:
        st.markdown("#### 📋 REAL + RECON & SYSTEM OUTSTANDING")
        c_rec1, c_rec2 = st.columns(2)
        with c_rec1: st.dataframe(st.session_state.recon_real_plus, use_container_width=True)
        with c_rec2: st.dataframe(st.session_state.outstanding_system, use_container_width=True)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            st.session_state.compare_result['res_scan'].to_excel(writer, sheet_name='DATA SCAN', index=False)
            st.session_state.set_up_real_plus.to_excel(writer, sheet_name='SET UP REAL +', index=False)
            st.session_state.recon_real_plus.to_excel(writer, sheet_name='REAL + RECON', index=False)
            st.session_state.outstanding_system.to_excel(writer, sheet_name='SYSTEM OUTSTANDING', index=False)
        st.download_button("📥 DOWNLOAD ALL EXCEL (STEP 1-3)", data=output.getvalue(), file_name="Report_SO_Part1.xlsx", use_container_width=True)
# ==========================================================
        # 🚀 FINAL ADJUSTMENT PROCESSOR (FIX INDEX & LOOKUP)
        # ==========================================================
        st.markdown("<br><br><br>---", unsafe_allow_html=True)
        st.subheader("4️⃣ FINAL ADJUSTMENT + PROCESS")

        col_a, col_b, col_c = st.columns(3)
        with col_a: 
            up_r4 = st.file_uploader("1️⃣ Sheet REAL + RECON", type=['xlsx','csv'], key="u_r_final_fix")
        with col_b: 
            up_s4 = st.file_uploader("2️⃣ Sheet CEK STOCK ADJ +", type=['xlsx', 'csv'], key="u_s_final_fix")
        with col_c: 
            up_m5 = st.file_uploader("3️⃣ File STAGGING INBOUND", type=['xlsx'], key="u_m_final_fix")

        if up_r4 and up_s4 and up_m5:
            if st.button("▶️ RUNNING PROCESS", use_container_width=True, key="btn_final_proc_v3"):
                try:
                    # 1. Pembacaan file (PASTIKAN NO ILOC GESER DI SINI)
                    df_r4 = pd.read_csv(up_r4) if up_r4.name.endswith('.csv') else pd.read_excel(up_r4)
                    df_s4 = pd.read_csv(up_s4) if up_s4.name.endswith('.csv') else pd.read_excel(up_s4)
                    df_m5 = pd.read_excel(up_m5)

                    # 2. Sinkronisasi Kolom
                    # Jangan di-iloc potong depan, biar BIN tetep di index 0 dan SKU di index 1
                    # Sesuai logic_cek_adjustment_final(df_recon, df_stock_adj)
                    res4, miss4 = logic_cek_adjustment_final(df_r4, df_s4)
                    
                    # 3. Jalankan Pivot
                    df_mult, df_sing = logic_pivot_adjustment(res4, df_m5, miss4)

                    # 4. Pembersihan Data (Pastikan hanya QTY > 0)
                    def clean_final_result(df):
                        if df is not None and not df.empty:
                            last_col = df.columns[-1] # Kolom QTY ADJ atau TOTAL_DIFF
                            df[last_col] = pd.to_numeric(df[last_col], errors='coerce').fillna(0)
                            df = df[df[last_col] > 0].reset_index(drop=True)
                        return df

                    # 5. Simpan ke Session State
                    st.session_state.df_mult_final = clean_final_result(df_mult)
                    st.session_state.df_sing_final = clean_final_result(df_sing)
                    st.session_state.df_res4_final = res4
                    st.session_state.df_miss4_final = miss4
                    st.session_state.process_done = True
                    
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Terjadi Kesalahan: {str(e)}")

        # --- AREA TAMPILAN HASIL ---
        if st.session_state.get("process_done"):
    # 1. Ambil data dengan aman
            df_res4 = st.session_state.get("df_res4_final", pd.DataFrame())
            
            # 2. Cek apakah hasil lookup beneran ada isinya (Pake cara paling aman)
            has_content = False
            try:
                if not df_res4.empty:
                    # Ambil kolom QTY SO, paksa jadi angka, lalu jumlahkan
                    total_cek = pd.to_numeric(df_res4['QTY SO'], errors='coerce').sum()
                    if total_cek > 0:
                        has_content = True
            except:
                has_content = False

            # 3. Validasi Tampilan
            if not has_content:
                st.warning("⚠️ Hasil Lookup Kosong atau Semua QTY adalah 0! Pastikan BIN/SKU sesuai.")
            else:
                st.success(f"✅ Analisis Selesai! (Memproses {len(df_res4):,} baris)")

            # 4. TAMPILAN TABS (PENTING: Perbaiki Nama Kolom Duplikat di sini)
            t1, t2, t3, t4, tmissing = st.tabs(["📦 MULTIPLE ADJ +", "⚠️ SINGLE ADJ +", "🔍 CEK ADJ + RESULT", "➡️ SET UP REAL +", "❌Miss Lookup SKU on BIN"])
            
            with t1:
                df_m = st.session_state.get("df_mult_final", pd.DataFrame())
                st.dataframe(df_m, use_container_width=True, hide_index=True)
                if not df_m.empty:
                    st.download_button("📥 Download Multiple Adj +", df_m.to_csv(index=False).encode('utf-8'), "final_adj_multiple.csv", "text/csv", key="dl_mult_final")
            
            with t2:
                df_s = st.session_state.get("df_sing_final", pd.DataFrame())
                st.dataframe(df_s, use_container_width=True, hide_index=True)
                if not df_s.empty:
                    st.download_button("📥 Download Single Adj +", df_s.to_csv(index=False).encode('utf-8'), "final_adj_single.csv", "text/csv", key="dl_sing_final")
            
            with t3:
                df_r4 = st.session_state.get("df_res4_final", pd.DataFrame())
                # --- TAMBAHKAN INI SEBELUM BARIS 1271 ---
                if not df_r4.empty:
                    # Logic buat deteksi & rename kolom kembar secara otomatis
                    cols = pd.Series(df_r4.columns)
                    for dup in cols[cols.duplicated()].unique(): 
                        cols[cols == dup] =[f"{dup}_{i}" if i != 0 else dup for i in range(cols[cols == dup].count())]
                    df_r4.columns = cols

                # Baris 1271 lu yang lama:
                st.dataframe(df_r4, use_container_width=True, hide_index=True)
                if not df_r4.empty:
                    st.download_button("📥 Download Hasil Cek Adj +", df_r4.to_csv(index=False).encode('utf-8'), "hasil_lookup_full.csv", "text/csv", key="dl_res4_final")

            with t4:
                # Pake variabel lokal biar gak bentrok
                df_m_src = st.session_state.get("df_mult_final")
                df_s_res = st.session_state.get("df_res4_final")
                df_miss_src = st.session_state.get("df_miss4_final")
                
                st.info("➡️ Running Relocation Inbound Setelah Running Process Selesai.")

                if st.button("▶️ GENERATE SET UP REAL +", use_container_width=True, key="btn_gen_real_plus"):
                    if df_m_src is not None and df_s_res is not None:
                        try:
                            df_real = logic_setup_real_plus(df_s_res, df_m_src, df_miss_src)
                            st.session_state.df_setup_real_final = df_real
                            st.success("✅ Mutasi Berhasil Dibuat!")
                            st.rerun() # Tambahin rerun biar langsung muncul
                        except Exception as e:
                            st.error(f"❌ Gagal memproses relokasi: {str(e)}")
                    else:
                        st.warning("⚠️ Data Multiple atau Cek Stock belum tersedia. Silahkan RUNNING PROCESS di atas terlebih dahulu.")

                # Tampilkan hasil jika sudah ada di session state
                if "df_setup_real_final" in st.session_state:
                    df_hasil = st.session_state.df_setup_real_final
                    st.dataframe(df_hasil, use_container_width=True, hide_index=True)
                    
                    if not df_hasil.empty:
                        csv_real = df_hasil.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 Download Set Up Real +", 
                            data=csv_real, 
                            file_name="set_up_real_plus.csv", 
                            mime="text/csv", 
                            key="dl_setup_real_final"
                        )
            with tmissing:
                df_miss = st.session_state.get("df_miss4_final", pd.DataFrame())
                if df_miss.empty:
                    st.info("Tidak ada item missing (Semua BIN|SKU terdaftar di sistem).")
                else:
                    st.warning(f"Ditemukan {len(df_miss)} baris barang yang ada di Fisik tapi TIDAK terdaftar di Sistem.")
                    # Kita ambil kolom BIN, SKU, dan QTY (Biasanya index 0, 1, dan 6 sesuai logic awal lu)
                    df_miss_display = df_miss.copy()
                    st.dataframe(df_miss_display, use_container_width=True, hide_index=True)
                    
                    csv_miss = df_miss_display.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Missing Items", 
                        data=csv_miss, 
                        file_name="missing_items_recon.csv", 
                        mime="text/csv", 
                        key="dl_miss_final"
                    )
    # =========================================================
    # ⚙️ 6. SET UP KARANTINA GENERATOR (DI DALAM FUNGSI MENU)
    # =========================================================
    st.markdown("<br><br><br>---", unsafe_allow_html=True)
    st.subheader("5️⃣ SET UP KARANTINA GENERATOR")

    # Tambahkan dua uploader agar logic compare BIN|SKU bisa jalan
    col_k1, col_k2 = st.columns(2)
    with col_k1:
        up_k6 = st.file_uploader("📥 1. Upload SYSTEM + RECON", type=['xlsx', 'xls', 'csv'], key="u6_karantina")
    with col_k2:
        up_adj6 = st.file_uploader("📥 2. Upload STOCK CEK ADJUSMENT", type=['xlsx', 'xls', 'csv'], key="u6_adj_compare")

    if up_k6 and up_adj6:
        if st.button("▶️ GENERATE KARANTINA", use_container_width=True):
            try:
                # 1. Baca File Outstanding
                up_k6.seek(0)
                df_raw6 = pd.read_excel(up_k6) if up_k6.name.endswith(('.xlsx', '.xls')) else pd.read_csv(up_k6)
                
                # 2. Baca File Recon (Cek Adjustment)
                up_adj6.seek(0)
                df_recon6 = pd.read_excel(up_adj6) if up_adj6.name.endswith(('.xlsx', '.xls')) else pd.read_csv(up_adj6)
                
                # 3. Jalankan Logic Baru dengan Compare BIN|SKU
                df_final6, df_check6 = logic_setup_karantina_with_compare(df_raw6, df_recon6)
                
                # 4. Simpan ke Session State
                st.session_state.df_karantina_6 = df_final6
                st.session_state.df_check_6 = df_check6 # Simpan juga data pengecekannya
                
                st.success("✅ Analisis Karantina Selesai!")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

    # Tampilkan Hasil Jika Sudah Diproses
    if st.session_state.df_karantina_6 is not None:
        tab_res, tab_chk = st.tabs(["📦 HASIL KARANTINA", "🔍 DATA PENGECEKAN (AUDIT)"])
        
        with tab_res:
            st.dataframe(st.session_state.df_karantina_6, use_container_width=True, hide_index=True)
            
            # Download Button (Excel)
            out6 = io.BytesIO()
            with pd.ExcelWriter(out6, engine='xlsxwriter') as writer:
                st.session_state.df_karantina_6.to_excel(writer, index=False, sheet_name='Karantina')
            st.download_button("📥 DOWNLOAD HASIL KARANTINA", data=out6.getvalue(), file_name="Karantina.xlsx", key="dl_k6")

        with tab_chk:
            st.info("Tabel ini menunjukkan perbandingan QTY SYSTEM vs HASIL RECON per BIN|SKU.")
            st.dataframe(st.session_state.df_check_6, use_container_width=True, hide_index=True)

# =========================================================
    # 📊 MISS LOCATION REPORT (FIXED RED ALERT)
    # =========================================================
    st.markdown("#### 📊 MISS LOCATION REPORT")
    if st.button("▶️ GENERATE MISS LOC", key="btn_gen_miss_final_v6"):
        data_src = st.session_state.get('set_up_real_plus')
        df_res, count_sku, count_qty = logic_miss_location_report(data_src)
        st.session_state.report_miss = {"data": df_res, "sku": count_sku, "qty": count_qty}
        st.rerun()

    if "report_miss" in st.session_state:
        df_ml_data = st.session_state.report_miss["data"]
        m_sku_val = int(st.session_state.report_miss["sku"])
        m_qty_val = int(st.session_state.report_miss["qty"])
        
        # WARNA MERAH TETAP (HARDCODED)
        fixed_red = "#FF4B4B"

        m1, m2 = st.columns(2)
        with m1:
            st.markdown(f"""
                <div style="background-color: #1E2129; padding: 20px; border-radius: 10px; border-left: 5px solid {fixed_red};">
                    <p style="color: #808495; font-size: 14px; margin-bottom: 5px;">📦 TOTAL SKU MISS LOC.</p>
                    <h2 style="color: {fixed_red}; margin: 0; font-weight: bold;">{m_sku_val} <span style="font-size: 18px;">ITEM</span></h2>
                </div>
            """, unsafe_allow_html=True)
            
        with m2:
            st.markdown(f"""
                <div style="background-color: #1E2129; padding: 20px; border-radius: 10px; border-left: 5px solid {fixed_red};">
                    <p style="color: #808495; font-size: 14px; margin-bottom: 5px;">🔢 TOTAL QTY MISS LOC.</p>
                    <h2 style="color: {fixed_red}; margin: 0; font-weight: bold;">{m_qty_val} <span style="font-size: 18px;">ITEM</span></h2>
                </div>
            """, unsafe_allow_html=True)

        # --- TAB AREA MISS LOC (2 SHEET DOWNLOAD) ---
        st.markdown("<br>", unsafe_allow_html=True)
        t_ml_1, t_ml_2 = st.tabs(["📄 Detail List", "📊 Summary"])
        
        df_sum_ml = pd.DataFrame({
            "METRIC": ["Total SKU Miss Loc", "Total Qty Miss Loc"],
            "VALUE":[m_sku_val, m_qty_val]
        })

        with t_ml_1:
            st.dataframe(df_ml_data, use_container_width=True, hide_index=True)
            
            fname_ml = "Miss_Location_Report.xlsx"
            with pd.ExcelWriter(fname_ml, engine='xlsxwriter') as writer:
                df_ml_data.to_excel(writer, sheet_name='DETAIL_MISS_LOC', index=False)
                df_sum_ml.to_excel(writer, sheet_name='SUMMARY', index=False)
            
            with open(fname_ml, "rb") as f:
                st.download_button(
                    label="📥 DOWNLOAD MISS LOC REPORT",
                    data=f,
                    file_name=fname_ml,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

        with t_ml_2:
            st.table(df_sum_ml)

    st.markdown("<br><hr>", unsafe_allow_html=True)

# --- BAGIAN B: SUMMARY ADJUSTMENT REPORT ---
    st.markdown("#### 💰 SUMMARY ADJUSTMENT REPORT")
    up_minus = st.file_uploader("📥 Upload STOCK ADJ -", type=['xlsx','csv'], key="up_minus_final_v3")
    up_plus = st.file_uploader("📥 Upload STOCK ADJ +", type=['xlsx','csv'], key="up_plus_final_v3")

    if st.button("▶️ SUMMARY ADJUSTMENT", key="btn_gen_adj_v3"):
        # 1. LOGIC HYBRID CERDAS
        if up_plus:
            # Prioritas: Pakai file yang baru di-upload
            df_p_in = pd.read_excel(up_plus) if up_plus.name.endswith('.xlsx') else pd.read_csv(up_plus)
        else:
            # Fallback: Pakai data dari session state (hasil running sebelumnya)
            df_p_in = st.session_state.get('df_mult_final')

        # 2. Ambil data Minus jika ada upload
        df_m_in = None
        if up_minus:
            df_m_in = pd.read_excel(up_minus) if up_minus.name.endswith('.xlsx') else pd.read_csv(up_minus)

        # 3. Jalankan Logic jika data tersedia
        if df_p_in is not None:
            # Jalankan fungsi logic asli
            df_res, df_summary = logic_sum_adjustment_final(df_p_in, df_m_in)
            
            st.session_state.report_adj = {"data": df_res, "sum": df_summary}
            st.success("✅ Summary Adjustment Berhasil Dibuat!")
            st.rerun()
        else:
            st.error("⚠️ Data tidak ditemukan! Upload file 'STOCK ADJ +' atau jalankan proses master data sebelumnya.")

# --- OVERVIEW ADJUSTMENT (SEMUA BOX WARNA DINAMIS) ---
    if "report_adj" in st.session_state:
        df_s = st.session_state.report_adj["sum"]
        def get_v(m): return df_s.loc[df_s['METRIC'] == m, 'VALUE'].values[0]

        # Financial & Inventory Data
        vals = {
            "v_p": get_v('Total Value Adj. +'), "v_m": get_v('Total Value Adj. -'), "v_n": get_v('Total Value'),
            "s_t": get_v('Total SKU Adj.'), "q_p": get_v('Total QTY Adj. +'), "q_m": get_v('Total QTY Adj. -')
        }

        # Helper buat nentuin warna
        def color(val): return "#00FF00" if val >= 0 else "#FF4B4B"

        # Baris 1: Value
        v1, v2, v3 = st.columns(3)
        for i, (k, title) in enumerate([("v_p", "📈TOTAL VALUE ADJ (+)"), ("v_m", "📉TOTAL VALUE ADJ (-)"), ("v_n", "⚖️NET VALUE ADJ")]):
            with [v1, v2, v3][i]:
                c = color(vals[k])
                st.markdown(f'<div style="background-color: #1E2129; padding: 20px; border-radius: 10px; border-left: 5px solid {c};"><p style="color: #808495; font-size: 13px;">{title}</p><h3 style="color: {c}; margin: 0;">Rp {vals[k]:,.0f}</h3></div>', unsafe_allow_html=True)

        st.markdown("<div style='margin: 10px;'></div>", unsafe_allow_html=True)

        # Baris 2: Inventory (SKU/QTY) - Sekarang Seirama!
        q1, q2, q3 = st.columns(3)
        for i, (k, title) in enumerate([("q_p", "🟢TOTAL QTY ADJ (+)"), ("q_m", "🔴TOTAL QTY ADJ (-)"), ("s_t", "🔺TOTAL SKU ADJ")]):
            with[q1, q2, q3][i]:
                c = color(vals[k])
                st.markdown(f'<div style="background-color: #1E2129; padding: 20px; border-radius: 10px; border-left: 5px solid {c};"><p style="color: #808495; font-size: 13px;">{title}</p><h3 style="color: {c}; margin: 0;">{int(vals[k])} <span style="font-size: 20px;">ITEM</span></h3></div>', unsafe_allow_html=True)

   # --- TAB AREA DENGAN DOWNLOAD 2 SHEET ---
        st.markdown("<br>", unsafe_allow_html=True)
        tab_adj_1, tab_adj_2 = st.tabs(["📄 Detail Report", "📊 Summary Adjusment"])
        
        with tab_adj_1:
            st.dataframe(st.session_state.report_adj["data"], use_container_width=True, hide_index=True)
            
            # --- TOMBOL DOWNLOAD EXCEL (2 SHEET: DETAIL & SUMMARY) ---
            # Cara ini paling simpel buat pecah sheet tanpa library io manual
            file_name = "Master_Adjustment_Report.xlsx"
            
            # Kita siapin data summary yang bersih (angka bulat) buat sheet kedua
            df_disp = df_s.copy()
            df_disp['VALUE'] = df_disp.apply(lambda x: f"{x['VALUE']:,.0f}" if 'Value' in x['METRIC'] else int(x['VALUE']), axis=1)

            # Generate file langsung ke local disk temporary streamlit
            with pd.ExcelWriter(file_name, engine='xlsxwriter') as writer:
                st.session_state.report_adj["data"].to_excel(writer, sheet_name='DETAIL_DATA', index=False)
                df_disp.to_excel(writer, sheet_name='SUMMARY_ADJUSMENT', index=False)
            
            # Kirim ke user
            with open(file_name, "rb") as f:
                st.download_button(
                    label="📥 DOWNLOAD MASTER REPORT",
                    data=f,
                    file_name=file_name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

        with tab_adj_2:
            # Tampilan di UI tetep rapih
            st.table(df_disp)
# =========================================================
    # 🏆 FINAL STEP: DOWNLOAD MASTER REPORT (SUPER LENGKAP)
    # =========================================================
    @st.fragment
    def download_section():
        if "process_done" in st.session_state and st.session_state.process_done:
            st.markdown("<br>", unsafe_allow_html=True)
            st.info("💡 **Master Report Ready:** All data will be saved")
            
            if st.button("🏗️ PREPARE FULL REPORT (ALL TABS)", use_container_width=True):
                with st.spinner("Processing Data..."):
                    output_master = io.BytesIO()
                    with pd.ExcelWriter(output_master, engine='xlsxwriter') as writer:
                        
                        # --- STEP 1: DATA SCAN & STOCK ---
                        if st.session_state.compare_result:
                            d = st.session_state.compare_result
                            d['res_scan'].to_excel(writer, sheet_name='1_DATA SCAN', index=False)
                            d['res_stock'].to_excel(writer, sheet_name='2_STOCK SYSTEM', index=False)
                            d['real_plus'].to_excel(writer, sheet_name='3_REAL PLUS', index=False)
                            d['system_plus'].to_excel(writer, sheet_name='4_SYSTEM PLUS', index=False)
                        
                        # --- STEP 2: ALOKASI ---
                        if st.session_state.set_up_real_plus is not None:
                            st.session_state.set_up_real_plus.to_excel(writer, sheet_name='5_SET UP REAL PLUS', index=False)
                        
                        # --- STEP 3: RECON ---
                        if st.session_state.recon_real_plus is not None:
                            st.session_state.recon_real_plus.to_excel(writer, sheet_name='6_REAL PLUS RECON', index=False)
                        if st.session_state.outstanding_system is not None:
                            st.session_state.outstanding_system.to_excel(writer, sheet_name='7_SYSTEM OUTSTANDING', index=False)
                        
                        # --- STEP 4 & 5: ADJUSTMENT ---
                        if "df_mult_final" in st.session_state:
                            st.session_state.df_mult_final.to_excel(writer, sheet_name='8_MULTIPLE ADJ PLUS', index=False)
                        if "df_sing_final" in st.session_state:
                            st.session_state.df_sing_final.to_excel(writer, sheet_name='9_SINGLE ADJ PLUS', index=False)
                        if "df_res4_final" in st.session_state:
                            st.session_state.df_res4_final.to_excel(writer, sheet_name='10_HASIL CEK ADJ', index=False)
                        
                        # --- STEP 6: KARANTINA ---
                        if st.session_state.df_karantina_6 is not None:
                            st.session_state.df_karantina_6.to_excel(writer, sheet_name='11_KARANTINA', index=False)
                    
                    st.session_state.master_excel_ready = output_master.getvalue()
                    st.success("✅ All Data Set!.")

            if 'master_excel_ready' in st.session_state:
                st.download_button(
                    label="📥 DOWNLOAD FULL MASTER REPORT (.XLSX)",
                    data=st.session_state.master_excel_ready,
                    file_name="FULL_SO_ANALYZER_REPORT.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    key="btn_final_master_ultra_fix"
                )

    download_section()
            
def menu_refill_withdraw():
    # --- STYLING ---
    st.markdown("""
        <style>
        div.stButton > button { 
            width: 100% !important; 
            background-color: #002b5b !important; 
            color: white !important; 
            font-weight: bold !important; 
            border: 1px solid #ffc107 !important; 
            border-radius: 8px;
        }
        .hero-header {
            background: linear-gradient(90deg, #002b5b 0%, #004085 100%);
            padding: 20px;
            border-radius: 10px;
            color: white;
            text-align: center;
            margin-bottom: 20px;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="hero-header"><h1>🔄 REFILL & WITHDRAW SYSTEM</h1></div>', unsafe_allow_html=True)

    with st.expander("📋 Informasi Format File"):
        st.info("""
        **Format yang diharapkan:**
        - **ALL DATA STOCK**: Download All Data Stock di Jezpro dan pilh **HANYA ADA DI STOCK**
        - **STOCK TRACKING**: Download Stock Tracking di Jezpro dan pilih **JEZ SURABAYA** lalu pilih rentang waktu **7 HARI SEBELUMNYA**
        """)
    with st.expander("💡Logic Thinking"):
        st.info("""
        **Alur Process Refill & Withdraw (With Stock Tracking):**
        - Melakukan Compare antara SKU yang ada di Gudang DC dengan Store dan sebaliknya
        - List akan dikumpulkan terlebih dahulu dan akan mengambil SKU dengan Qty di Store yang < 3 Pcs untuk Refill dan > 6 Pcs untuk Withdraw
        - Jika data sudah didapatkan maka selanjutnya adalah compare dengan Stock Tracking
        - Compare akan dilakukan dengan mempertimbangkan penjualan Offline untuk SKU tersebut
        - Jika penjualan offline < 7 pcs maka refill hanya akan mengambil 1/3 dari total stock di DC dan akan mengambil 1/3 dari total Diff total stock - 12 Pcs untuk Withdraw
        - Jika penjualan offline > 7 pcs maka refill akan mengambil 1/2 dari total stock di DC dan akan mengambil 1/2 dari total Diff total stock - 12 Pcs untuk Withdraw
        - Maksimal kapasitas untuk tiap SKU di STORE adalah 6 Pcs jadi tidak akan lebih dari 6 tiap SKU di Gl3

        **Alur Process Refill & Withdraw (Without Stock Tracking):**
        - Melakukan Compare antara SKU yang ada di Gudang DC dengan SKU di Gudang STORE
        - List akan dikumpulkan terlebih dahulu dan akan mengambil SKU dengan Qty di Gudang DC yang < 3 Pcs dan > 6 Pcs untuk Withdraw
        - Sistem akan memksimalkan tiap SKU untuk mendapatkan total 6 Pcs di Gudang Store 
        - Maksimal kapasitas untuk tiap SKU di Store adalah 6 Pcs jadi tidak akan lebih dari 6 tiap SKU di Gl3
        """)

    # --- 0. INIT STATE ---
    for key in["df_stock_sby", "df_trx", "summary_refill", "summary_withdraw"]:
        if key not in st.session_state: 
            st.session_state[key] = None

    # --- 1. UPLOAD SECTION ---
    col1, col2 = st.columns(2)
    with col1:
        u_stock = st.file_uploader("📤 Upload ALL STOCK SURABAYA", type=["xlsx"])
        if u_stock:
            try:
                st.session_state.df_stock_sby = pd.read_excel(u_stock, sheet_name="All Stock SBY")
                st.success("Stock Ready")
            except:
                st.session_state.df_stock_sby = pd.read_excel(u_stock, sheet_name=0)
                st.warning("Pakai Sheet Pertama")

    with col2:
        u_trx = st.file_uploader("📤 Upload STOCK TRACKING", type=["xlsx"])
        if u_trx:
            try:
                st.session_state.df_trx = pd.read_excel(u_trx, sheet_name="Data Transaksi")
                st.success("Trx Ready")
            except:
                st.session_state.df_trx = pd.read_excel(u_trx, sheet_name=0)
                st.warning("Pakai Sheet Pertama")

    st.divider()

    # --- 2. GENERATE BUTTON ---
    if st.button("📝 GENERATE SUMMARY"):
        if st.session_state.df_stock_sby is not None:
            # Setup Dataframe
            df_s = st.session_state.df_stock_sby.copy()
            df_s.columns =[i for i in range(len(df_s.columns))]
            
            df_t = st.session_state.df_trx.copy() if st.session_state.df_trx is not None else pd.DataFrame()
            if not df_t.empty:
                df_t.columns = [i for i in range(len(df_t.columns))]

            # Dictionaries (God Mode Memory Processing)
            dictDC = {}; dict02 = {}; dictTotDC = {}; dictTot02 = {}
            dictTotDCKLRAK = {}; dictBrand = {}; dictItem = {}; dictVar = {}
            dictBinListDC = {}; dictBinList02 = {}; dictPreTotToko = {}
            dictPreTotDCInbound = {}; dictBestValDC = {}; dictBestVal02 = {}
            dictUniqueRef = {}; dictUniqueWdr = {}; dictSubKat = {} 

            # --- STEP 1: SCAN STOCK ---
            for _, row in df_s.iterrows():
                sku = str(row[2]).strip()
                if sku == "" or sku == "nan" or sku == "SKU": continue

                binLoc = str(row[1]).upper().strip()
                qtySys = pd.to_numeric(row[9], errors='coerce') or 0

                # GLOBAL EXCLUSION (Biar gak ambil dari area Live/Online/Rusak)
                is_excluded = any(ex in binLoc for ex in["DEFECT", "REJECT", "ONLINE", "LIVE", "MARKOM", "KARANTINA", "STAGING", "PUTAWAY"])
                if is_excluded: continue

                if sku not in dictBrand:
                    dictBrand[sku] = str(row[3])
                    dictItem[sku] = str(row[4])
                    dictVar[sku] = str(row[5])
                    # PERBAIKAN: Kolom 7 = Indeks 6, tambahkan cek nan
                    raw_sub = row[6]
                    dictSubKat[sku] = str(raw_sub) if pd.notna(raw_sub) and str(raw_sub).lower() != 'nan' else "-"

                # AREA TOKO
                if any(x in binLoc for x in ["02", "TOKO", "STORE", "LT.2", "STR"]):
                    dictPreTotToko[sku] = dictPreTotToko.get(sku, 0) + qtySys
                    if qtySys > dictBestVal02.get(sku, -1):
                        dictBestVal02[sku] = qtySys
                        dict02[sku] = binLoc
                    dictTot02[sku] = dictTot02.get(sku, 0) + qtySys
                    dictBinList02[sku] = dictBinList02.get(sku, "") + binLoc + ", "

                # AREA DC
                elif any(x in binLoc for x in["DC", "INBOUND", "KL", "RAK"]):
                    dictPreTotDCInbound[sku] = dictPreTotDCInbound.get(sku, 0) + qtySys
                    if qtySys > dictBestValDC.get(sku, -1):
                        dictBestValDC[sku] = qtySys
                        dictDC[sku] = binLoc
                    dictTotDC[sku] = dictTotDC.get(sku, 0) + qtySys
                    dictBinListDC[sku] = dictBinListDC.get(sku, "") + binLoc + ", "
                    dictTotDCKLRAK[sku] = dictTotDCKLRAK.get(sku, 0) + qtySys

            outRef = []; outWdr =[]

            # --- STEP 2: LOGIC TRANSAKSI ---
            if not df_t.empty:
                for _, row in df_t.iterrows():
                    sku_t = str(row[1]).strip()
                    if sku_t not in dictBrand: continue
                    
                    safeInvoice = str(row[0]).upper()
                    safeLoc = str(row[6]).upper()

                    # Refill Proaktif via INV
                    if "INV" in safeInvoice and not any(x in safeLoc for x in ["02", "TOKO"]):
                        if sku_t not in dictUniqueRef:
                            if (dictTot02.get(sku_t, 0) + dictTotDC.get(sku_t, 0) <= 3) and sku_t in dictDC:
                                bestQty = dictBestValDC.get(sku_t, 0)
                                if bestQty > 1:
                                    # AMBIL DARI dictSubKat
                                    outRef.append([sku_t, dictBrand[sku_t], dictItem[sku_t], dictVar[sku_t], dictDC[sku_t], bestQty, math.ceil(bestQty/2), dictPreTotToko.get(sku_t, 0), dictBinListDC.get(sku_t, "")[:-2], dictSubKat.get(sku_t, "-")])
                                    dictUniqueRef[sku_t] = True
                    
                    # Withdraw via Trx
                    elif "INV" not in safeInvoice and any(x in safeLoc for x in ["02", "TOKO"]):
                        if sku_t not in dictUniqueWdr:
                            if dictTotDCKLRAK.get(sku_t, 0) <= 3 and sku_t in dict02:
                                bestQty = dictBestVal02.get(sku_t, 0)
                                if bestQty > 1:
                                    # AMBIL DARI dictSubKat
                                    outWdr.append([sku_t, dictBrand[sku_t], dictItem[sku_t], dictVar[sku_t], dict02[sku_t], bestQty, math.ceil(bestQty/2), dictPreTotDCInbound.get(sku_t, 0), dictBinList02.get(sku_t, "")[:-2], dictSubKat.get(sku_t, "-")])
                                    dictUniqueWdr[sku_t] = True

            # --- STEP 3: AUTO-BALANCE ---
            for sku_k in dictBrand.keys():
                # Refill Balancing (Toko Kosong)
                if sku_k not in dictUniqueRef:
                    if dictTotDC.get(sku_k, 0) > 1 and dictPreTotToko.get(sku_k, 0) == 0 and sku_k in dictDC:
                        bestQty = dictBestValDC.get(sku_k, 0)
                        outRef.append([sku_k, dictBrand[sku_k], dictItem[sku_k], dictVar[sku_k], dictDC[sku_k], bestQty, math.ceil(bestQty/2), 0, dictBinListDC.get(sku_k, "")[:-2], dictSubKat.get(sku_k, "-")])
                        dictUniqueRef[sku_k] = True

                # Withdraw Balancing (DC Kosong)
                if sku_k not in dictUniqueWdr:
                    if dictTot02.get(sku_k, 0) > 3 and dictPreTotDCInbound.get(sku_k, 0) == 0 and sku_k in dict02:
                        bestQty = dictBestVal02.get(sku_k, 0)
                        outWdr.append([sku_k, dictBrand[sku_k], dictItem[sku_k], dictVar[sku_k], dict02[sku_k], bestQty, math.ceil(bestQty/2), 0, dictBinList02.get(sku_k, "")[:-2], dictSubKat.get(sku_k, "-")])
                        dictUniqueWdr[sku_k] = True

            # Save Output
            st.session_state.summary_refill = pd.DataFrame(outRef, columns=["SKU", "BRAND", "ITEM NAME", "VARIANT", "BIN AMBIL", "QTY BIN AMBIL", "LOAD", "QTY BIN 02", "BIN LAIN","SUB KATEGORI"])
            st.session_state.summary_withdraw = pd.DataFrame(outWdr, columns=["SKU", "BRAND", "ITEM NAME", "VARIANT", "BIN AMBIL", "QTY BIN AMBIL", "LOAD", "QTY BIN DC", "BIN LAIN","SUB KATEGORI"])
            st.success(f"DONE! Refill: {len(outRef)} | Withdraw: {len(outWdr)}")
        else:
            st.error("Upload Data Stock Dulu!")

    # --- 3. TABS SECTION ---
    t1, t2, t3 = st.tabs(["♻️ Summary Refill", "♻️ Summary Withdraw", "🔺 Upload to Appsheet"])

    with t1:
        if st.session_state.summary_refill is not None:
            st.dataframe(st.session_state.summary_refill, use_container_width=True)

    with t2:
        if st.session_state.summary_withdraw is not None:
            st.dataframe(st.session_state.summary_withdraw, use_container_width=True)

    with t3:
        col_up1, col_up2 = st.columns(2)
        with col_up1:
            if st.session_state.summary_refill is not None:
                if st.button("🔺 Upload Refill"):
                    data_json = st.session_state.summary_refill.astype(str).values.tolist()
                    url = "https://script.google.com/macros/s/AKfycbzJ0jWLefO8t9s7AO2eloEgHXehjSKAQXPUHzSX6VuZhSWOrbWEyVBi5rjZgUbn7YLQ/exec?sheet=REFILL%20STOCK"
                    requests.post(url, json=data_json)
                    st.toast("REFILL UPLOADED!")
        
        with col_up2:
            if st.session_state.summary_withdraw is not None:
                if st.button("🔺 Upload Withdraw"):
                    data_json = st.session_state.summary_withdraw.astype(str).values.tolist()
                    url = "https://script.google.com/macros/s/AKfycbzJ0jWLefO8t9s7AO2eloEgHXehjSKAQXPUHzSX6VuZhSWOrbWEyVBi5rjZgUbn7YLQ/exec?sheet=WITHDRAW%20STOCK"
                    requests.post(url, json=data_json)
                    st.toast("WITHDRAW UPLOADED!")

def engine_ds_rto_vba_total(df_ds, df_app):
    if df_ds is None or df_app is None:
        return pd.DataFrame(), pd.DataFrame()

    # 1. Helper Function untuk membersihkan SKU secara total
    def clean_sku(val):
        if pd.isna(val): return ""
        # Hilangkan .0 jika SKU terbaca sebagai float
        if isinstance(val, float) and val.is_integer():
            s = str(int(val)).strip().upper()
        else:
            s = str(val).strip().upper()
        
        if s.endswith('.0'): s = s[:-2]
        if s in["NAN", "0", "NONE", ""]: return ""
        return s

    df_a = df_app.copy()
    # Mengubah nama kolom menjadi string untuk memudahkan akses
    df_a.columns =[str(i) for i in range(1, len(df_a.columns) + 1)]
    
    # Filter Status: DONE atau KURANG AMBIL
    mask_status = df_a['2'].astype(str).str.strip().str.upper().isin(['DONE', 'KURANG AMBIL'])
    df_filtered = df_a[mask_status].copy()

    # 2. Logic Perbaikan: Cek SKU 9+13 DAN 15+17 secara independen
    dict_qty_total = {}
    for _, row in df_filtered.iterrows():
        # Pasangan 1 (Kolom 9 & 13)
        sku1 = clean_sku(row.get('9', ''))
        qty1 = pd.to_numeric(row.get('13', 0), errors='coerce') or 0
        if sku1:
            dict_qty_total[sku1] = dict_qty_total.get(sku1, 0) + qty1
            
        # Pasangan 2 (Kolom 15 & 17)
        sku2 = clean_sku(row.get('15', ''))
        qty2 = pd.to_numeric(row.get('17', 0), errors='coerce') or 0
        if sku2:
            dict_qty_total[sku2] = dict_qty_total.get(sku2, 0) + qty2

    # 3. Proses DataFrame DS
    res_ds = df_ds.copy()
    cols = list(res_ds.columns)
    sku_col = cols[0]
    scan_col = cols[1]
    
    res_ds['SKU_UPPER'] = res_ds[sku_col].apply(clean_sku)
    # Map ke dict_qty_total yang sudah mencakup kolom 9 dan 15
    res_ds['QTY AMBIL'] = res_ds['SKU_UPPER'].map(dict_qty_total).fillna(0).astype(int)
    
    def check_note(row):
        scan = pd.to_numeric(row[scan_col], errors='coerce') or 0
        ambil = row['QTY AMBIL']
        if scan > ambil: return "KELEBIHAN AMBIL"
        elif scan < ambil: return "KURANG AMBIL"
        else: return "SESUAI"
    
    res_ds['NOTE'] = res_ds.apply(check_note, axis=1)

    # 4. Perhitungan q_del (Status DELETE ITEM)
    # Menjumlahkan QTY dari kolom 13 dan 17 untuk status DELETE
    mask_del = df_a['2'].astype(str).str.upper().str.strip() == 'DELETE ITEM'
    q_del = int(pd.to_numeric(df_a[mask_del]['13'], errors='coerce').sum() + 
                pd.to_numeric(df_a[mask_del]['17'], errors='coerce').sum())

    # 5. Bangun Hasil Selisih untuk Report
    results_selisih = []
    mismatch_ds = res_ds[res_ds['NOTE'] != 'SESUAI'].copy()
    
    for _, row in mismatch_ds.iterrows():
        sku = row['SKU_UPPER']
        # Cari baris yang relevan di AppSheet baik di kolom 9 atau 15
        mask_app = (df_a['9'].apply(clean_sku) == sku) | (df_a['15'].apply(clean_sku) == sku)
        found_rows = df_a[mask_app]
        
        if not found_rows.empty:
            for _, r_app in found_rows.iterrows():
                # Cek apakah SKU tersebut ada di pasangannya masing-masing
                if clean_sku(r_app.get('9')) == sku:
                    results_selisih.append([sku, row[scan_col], row['QTY AMBIL'], row['NOTE'], r_app.get('12', '-'), r_app.get('13', 0), 0])
                if clean_sku(r_app.get('15')) == sku:
                    results_selisih.append([sku, row[scan_col], row['QTY AMBIL'], row['NOTE'], r_app.get('16', '-'), r_app.get('17', 0), 0])
        else:
            results_selisih.append([sku, row[scan_col], row['QTY AMBIL'], row['NOTE'], "-", 0, 0])

    # 6. SKU di AppSheet tapi tidak ada di DS
    skus_in_ds = set(res_ds['SKU_UPPER'].unique())
    for sku_app, total_qty in dict_qty_total.items():
        if sku_app and sku_app not in skus_in_ds:
            mask_app = (df_a['9'].apply(clean_sku) == sku_app) | (df_a['15'].apply(clean_sku) == sku_app)
            found_rows = df_a[mask_app]
            for _, r_app in found_rows.iterrows():
                note_khusus = "DI APPSHEET DIAMBIL DI DS TIDAK ADA"
                if clean_sku(r_app.get('9')) == sku_app:
                    results_selisih.append([sku_app, 0, total_qty, note_khusus, r_app.get('12', '-'), r_app.get('13', 0), 0])
                if clean_sku(r_app.get('15')) == sku_app:
                    results_selisih.append([sku_app, 0, total_qty, note_khusus, r_app.get('16', '-'), r_app.get('17', 0), 0])

    res_selisih = pd.DataFrame(results_selisih, columns=['SKU','QTY SCAN','QTY AMBIL','NOTE','BIN','QTY AMBIL BIN','HASIL CEK REAL'])
    
    # --- PERBAIKAN: Hapus duplikat baris yang sama persis ---
    res_selisih = res_selisih.drop_duplicates(subset=['SKU', 'BIN', 'QTY AMBIL BIN', 'NOTE'], keep='first')
    
    # Final clean-up
    res_selisih['SKU'] = res_selisih['SKU'].apply(clean_sku)
    res_ds.drop(columns=['SKU_UPPER'], inplace=True)
    
    return res_ds, res_selisih

def engine_refresh_rto(df_ds, df_app_awal, df_selisih):
    if df_app_awal.empty or df_selisih.empty: return df_ds, df_app_awal
    df_app_res = df_app_awal.copy()
    df_ds_res = df_ds.copy()

    real_map = {}
    for _, row in df_selisih.iterrows():
        sku_real = str(row.iloc[0]).strip().upper()
        bin_real = str(row.iloc[4]).strip().upper()
        qty_real = pd.to_numeric(row.iloc[6], errors='coerce') or 0
        if sku_real not in ["", "NAN", "NONE"]:
            real_map[f"{sku_real}|{bin_real}"] = qty_real

    for idx in df_app_res.index:
        try:
            sku = str(df_app_res.iloc[idx, 8]).strip().upper()
            if sku in["", "NAN", "0", "NONE"]: sku = str(df_app_res.iloc[idx, 14]).strip().upper()
            b1, b2 = str(df_app_res.iloc[idx, 11]).strip().upper(), str(df_app_res.iloc[idx, 15]).strip().upper()
            target_qty = real_map.get(f"{sku}|{b1}") if f"{sku}|{b1}" in real_map else real_map.get(f"{sku}|{b2}")
            if target_qty is not None:
                val_n = str(df_app_res.iloc[idx, 13]).strip()
                if val_n == "" or val_n.lower() == "nan": df_app_res.iloc[idx, 12] = target_qty
                else: df_app_res.iloc[idx, 16] = target_qty
        except: continue

    if not df_ds_res.empty:
        df_app_res['TMP_SKU'] = df_app_res.apply(lambda r: str(r.iloc[8]).strip().upper() if str(r.iloc[8]).strip() not in["","0","nan"] else str(r.iloc[14]).strip().upper(), axis=1)
        df_app_res['TMP_QTY'] = df_app_res.apply(lambda r: (pd.to_numeric(r.iloc[12], errors='coerce') or 0) + (pd.to_numeric(r.iloc[16], errors='coerce') or 0), axis=1)
        summary_map = df_app_res.groupby('TMP_SKU')['TMP_QTY'].sum().to_dict()
        sku_col, scan_col, ambil_col = df_ds_res.columns[0], df_ds_res.columns[1], df_ds_res.columns[2]
        df_ds_res[ambil_col] = df_ds_res[sku_col].astype(str).str.strip().str.upper().map(summary_map).fillna(0)
        df_ds_res[scan_col] = df_ds_res[ambil_col] 
        if 'NOTE' in df_ds_res.columns: df_ds_res['NOTE'] = "SESUAI"
        df_app_res.drop(columns=['TMP_SKU', 'TMP_QTY'], inplace=True)
    return df_ds_res, df_app_res

def engine_compare_draft_jezpro(df_app, df_draft):
    df_res = df_draft.copy()
    df_a = df_app.copy()
    df_a.columns =[str(i) for i in range(1, len(df_a.columns) + 1)]
    
    def clean_sku(val):
        if pd.isna(val): return ""
        s = str(val).strip().upper()
        if s.endswith('.0'): s = s[:-2]
        return s if s not in ["NAN", "0", "NONE"] else ""

    # --- 1. REKAP DATA APPSHEET ---
    app_summary = {} 
    for _, r in df_a.iterrows():
        # Ambil semua pasangan SKU & BIN dari AppSheet (Kolom 9&12, 15&16)
        pairs =[(clean_sku(r.get('9')), str(r.get('12','')).strip().upper(), pd.to_numeric(r.get('13',0), errors='coerce') or 0),
                 (clean_sku(r.get('15')) or clean_sku(r.get('9')), str(r.get('16','')).strip().upper(), pd.to_numeric(r.get('17',0), errors='coerce') or 0)]
        
        for s, b, q in pairs:
            if s and b not in["", "0", "NAN"]:
                app_summary[(s, b)] = app_summary.get((s, b), 0) + q

    # Kita pakai copy untuk tracking sisa stok yang belum terpakai
    rem_app = app_summary.copy()

    # --- 2. TAHAP 1: PRIORITAS MATCH SEMPURNA (ANTI BARIS DOUBLE) ---
    # Kita tandai dulu baris mana yang sudah OK biar nggak kena tabrak logic PINDAH BIN
    processed_indices = set()

    for idx, row in df_res.iterrows():
        sku_d = clean_sku(row.iloc[3])
        bin_d = str(row.iloc[8]).strip().upper()
        qty_h = pd.to_numeric(row.iloc[7], errors='coerce') or 0
        key_d = (sku_d, bin_d)

        if rem_app.get(key_d, 0) > 0:
            qty_j = rem_app[key_d]
            rem_app[key_d] = 0 # Habiskan kuota karena sudah match sempurna
            
            note = "DRAFT SESUAI" if qty_j == qty_h else "BEDA QTY"
            status = "OK" if qty_j == qty_h else "PERLU EDIT QTY DRAFT"
            
            df_res.loc[idx,['QTY AMBIL', 'NOTE', 'BIN AMBIL LAIN', 'QTY BIN LAIN', 'STATUS']] = \[qty_j, note, "", 0, status]
            processed_indices.add(idx)

    # --- 3. TAHAP 2: SISANYA BARU CEK PINDAH BIN / DELETE ---
    for idx, row in df_res.iterrows():
        if idx in processed_indices: continue # Lewati yang sudah OK di Tahap 1

        sku_d = clean_sku(row.iloc[3])
        bin_d = str(row.iloc[8]).strip().upper()
        
        # Cari apakah SKU ini ada di BIN lain yang MASIH punya sisa stok di rem_app
        possible_bins =[k for k, v in rem_app.items() if k[0] == sku_d and v > 0]
        
        if possible_bins:
            # Info BIN lain diambil dari sisa stok yang belum ter-match
            bin_lain = ", ".join([b[1] for b in possible_bins])
            qty_lain = sum([rem_app[b] for b in possible_bins])
            
            df_res.loc[idx,['QTY AMBIL', 'NOTE', 'BIN AMBIL LAIN', 'QTY BIN LAIN', 'STATUS']] = \[0, "PINDAH BIN", bin_lain, qty_lain, "PERLU EDIT BIN DRAFT"]
        else:
            df_res.loc[idx,['QTY AMBIL', 'NOTE', 'BIN AMBIL LAIN', 'QTY BIN LAIN', 'STATUS']] = \[0, "HAPUS ITEM INI", "", 0, "DELETE ITEM"]

    # --- 4. TAHAP 3: ADD NEW (Hanya jika SKU bener-bener gak ada di Draft) ---
    sku_in_draft = set(df_draft.iloc[:, 3].apply(clean_sku).unique())
    new_rows =[]

    for (sku_a, bin_a), qty_a in rem_app.items():
        if qty_a > 0 and sku_a not in sku_in_draft:
            new_entry = {col: "" for col in df_res.columns}
            new_entry[df_res.columns[0]] = "-" 
            new_entry[df_res.columns[3]] = sku_a 
            new_entry[df_res.columns[7]] = 0 
            new_entry[df_res.columns[8]] = bin_a 
            new_entry['QTY AMBIL'] = qty_a
            new_entry['NOTE'] = "TAMBAH ITEM BARU"
            new_entry['STATUS'] = "ADD NEW"
            new_rows.append(new_entry)
            rem_app[(sku_a, bin_a)] = 0 # Tandai sudah masuk ADD NEW

    if new_rows:
        df_res = pd.concat([df_res, pd.DataFrame(new_rows)], ignore_index=True)

    # Convert angka .0 jadi integer biar bersih
    for col in['QTY AMBIL', 'QTY BIN LAIN', df_res.columns[7]]:
        if col in df_res.columns:
            df_res[col] = pd.to_numeric(df_res[col], errors='coerce').fillna(0).astype(int)

    return df_res

def menu_retur_out_system():
    # Jam Jakarta/Surabaya
    tz_sub = pytz.timezone('Asia/Jakarta')

    # --- 2. CSS DASHBOARD PREMIUM (TIDAK DIUBAH SAMA SEKALI) ---
    st.markdown("""
        <style>
        .hero-header {
            background-color: #1d3e7a;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 25px;
            box-shadow: 0px 4px 15px rgba(0,0,0,0.3);
            border-left: 8px solid #007BFF;
        }
        .hero-text {
            color: white !important;
            margin: 0 !important;
            font-size: 24px !important;
            font-weight: 800 !important;
            letter-spacing: 1px;
        }
        .metric-card {
            background-color: #1E1E2E;
            padding: 18px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            color: white;
            margin-bottom: 15px;
        }
        .metric-label {
            font-size: 11px;
            color: #A0A0A0;
            text-transform: uppercase;
            letter-spacing: 1.2px;
            font-weight: 700;
            margin-bottom: 5px;
        }
        .metric-value {
            font-size: 26px;
            font-weight: 800;
            color: #FFFFFF;
            margin: 0;
        }
        .metric-delta {
            font-size: 10px;
            color: #10b981;
            font-weight: 600;
            margin-top: 5px;
        }
        div[data-baseweb="input"] + div { display: none; }
        .stTextInput>div>div>input {
            background-color: #1E1E2E;
            color: #FFFFFF;
            border-radius: 10px;
            border: 1px solid #3d4455;
            padding: 10px 15px;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="hero-header"><p class="hero-text">RETUR OUT LIST</p></div>', unsafe_allow_html=True)

    # --- 3. UPLOAD & AUTO-SAVE (LOGIC API) ---
    uploaded_file = st.file_uploader("Upload File Retur", type=['xlsx', 'csv'], key="retur_up_v3_anon")
    
    if uploaded_file:
        try:
            # Baca file
            df_upload = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
            df_upload.columns = [str(c).strip() for c in df_upload.columns]
            
            required_cols = {
                'Identify': 'identify', 'BIN': 'bin', 'SKU': 'sku', 
                'BRAND': 'brand', 'ITEM NAME': 'item_name', 'VARIANT': 'variant', 
                'SUB KATEGORI': 'sub_kategori', 'Harga Beli': 'harga_beli', 
                'Harga Jual': 'harga_jual', 'QTY SYSTEM': 'qty_system', 'QTY SO': 'qty_so'
            }

            if all(col in df_upload.columns for col in required_cols.keys()):
                df_to_save = df_upload[list(required_cols.keys())].copy()
                df_to_save.rename(columns=required_cols, inplace=True)
                
                # Tambah timestamp & bersihkan data
                df_to_save['tanggal'] = datetime.now(tz_sub).strftime('%Y-%m-%d %H:%M:%S')
                df_to_save = df_to_save.fillna("") 

                # Cek Double Upload via Session State
                file_key = f"anon_v3_{uploaded_file.name}_{len(df_upload)}"
                if st.session_state.get('last_file_key_v3') != file_key:
                    # Insert data ke Supabase lewat jalur API
                    records = df_to_save.to_dict(orient='records')
                    if supabase_global:
                        supabase_global.table("retur_out_v3").insert(records).execute()
                        st.cache_data.clear()
                    
                    st.session_state['last_file_key_v3'] = file_key
                    st.success(f"✅ Berhasil! {len(records)} Baris masuk Cloud Database.")
                    st.rerun()
            else:
                st.error("Gagal: Kolom di file lu gak match sama sistem!")
        except Exception as e:
            st.error(f"Error Upload: {e}")

    # --- 4. DATA VIEW & METRICS ---
    try:
        # Ambil data dari Supabase via API
        df_db = fetch_table_data("retur_out_v3")

        if not df_db.empty:
            # Pastikan tipe data benar buat kalkulasi
            df_db['qty_system'] = pd.to_numeric(df_db['qty_system'], errors='coerce').fillna(0)
            df_db['harga_beli'] = pd.to_numeric(df_db['harga_beli'], errors='coerce').fillna(0)

            # 1. Kalkulasi Dashboard
            total_sku = df_db['sku'].nunique()
            total_qty_system = df_db['qty_system'].sum()
            total_value = (df_db['qty_system'] * df_db['harga_beli']).sum()

            # 2. Tampilan Metrik Box (Sesuai Desain Awal)
            m1, m2, m3 = st.columns(3)
            with m1:
                st.markdown(f'''
                    <div class="metric-card" style="border-left: 6px solid #8b5cf6;">
                        <div class="metric-label">🗄️ TOTAL SKU</div>
                        <div class="metric-value">{total_sku:,}</div>
                        <div class="metric-delta">↑ TOTAL DATA</div>
                    </div>
                ''', unsafe_allow_html=True)
            with m2:
                st.markdown(f'''
                    <div class="metric-card" style="border-left: 6px solid #10b981;">
                        <div class="metric-label">📦 TOTAL QTY</div>
                        <div class="metric-value">{int(total_qty_system):,}</div>
                        <div class="metric-delta">↑ TOTAL UNIT</div>
                    </div>
                ''', unsafe_allow_html=True)
            with m3:
                st.markdown(f'''
                    <div class="metric-card" style="border-left: 6px solid #f59e0b;">
                        <div class="metric-label">💰 TOTAL VALUE</div>
                        <div class="metric-value">Rp {total_value:,.0f}</div>
                        <div class="metric-delta">↑ ASSET VALUE</div>
                    </div>
                ''', unsafe_allow_html=True)

            st.markdown("### 📜 Database History")
            search_query = st.text_input("🔍 Cari SKU / Nama Barang...", placeholder="Masukkan pencarian...", key="search_v3")

            # Sorting data terbaru di atas
            df_display = df_db.sort_values(by='tanggal', ascending=False)

            if search_query:
                df_display = df_display[
                    df_display['sku'].astype(str).str.contains(search_query, case=False, na=False) | 
                    df_display['item_name'].astype(str).str.contains(search_query, case=False, na=False)
                ]

            # UI Tabel
            event = st.dataframe(
                df_display,
                use_container_width=True, 
                hide_index=True, 
                on_select="rerun", 
                selection_mode="single-row" 
            )

            # Logika Hapus Data (Berdasarkan Primary Key 'id' di Supabase)
            if event.selection.rows:
                row_idx = event.selection.rows[0]
                target_id = df_display.iloc[row_idx]['id']
                target_sku = df_display.iloc[row_idx]['sku']
                
                st.warning(f"⚠️ Hapus SKU: **{target_sku}** dari Cloud?")
                if st.button("🗑️ HAPUS PERMANEN", type="primary", use_container_width=True):
                    if supabase_global:
                        supabase_global.table("retur_out_v3").delete().eq("id", target_id).execute()
                        st.cache_data.clear()
                    st.success("Data berhasil dihapus dari Cloud!")
                    st.rerun()
        else:
            st.info("❌ Data kosong, Silakan upload file.")

    except Exception as e:
        st.error(f"Sistem Gagal Memuat Cloud Database: {e}")

def show_database_ongkir():
    # --- 1. CSS CUSTOM (Sesuai Request: Samakan Style Input & Hero Header) ---
    st.markdown("""
        <style>
        /* Style untuk Hero Header Utama */
        .hero-header {
            background: linear-gradient(135deg, #1e2227 0%, #0e1117 100%);
            padding: 2rem;
            border-radius: 10px;
            border-left: 5px solid #FFD700;
            margin-bottom: 2rem;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        }
        .hero-header h1 {
            color: #ffffff;
            margin: 0;
            font-size: 2.2rem;
            letter-spacing: 1px;
        }

        /* Style Input (Nama Supplier, Total Koli, Total Ongkir) agar Seragam */
        div[data-baseweb="input"], div[data-baseweb="select"] {
            background-color: #0e1117 !important;
            border: 1px solid #3e444d !important;
            border-radius: 5px !important;
        }
        
        /* Gold Border saat Focus/Klik */
        div[data-baseweb="input"]:focus-within {
            border-color: #FFD700 !important;
            box-shadow: 0 0 0 1px #FFD700 !important;
        }
        /* 3. Style Subheader (1. DOWNLOAD & 2. UPLOAD) */
        /* Kita bungkus pakai div khusus untuk background solid Gold */
        .solid-header {
            background-color: #FFD700 !important; /* Background Emas Solid */
            color: #0e1117 !important; /* Teks Hitam biar kontras */
            padding: 10px 15px !important;
            border-radius: 5px !important;
            font-weight: 900 !important;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            margin-bottom: 15px !important;
            display: inline-block; /* Agar background pas sama teks */
        }
        /* 5. Style Tombol Utama (SIMPAN & UPLOAD) */
        /* Background Navy Tua, Border & Text Gold */
        .stButton button, .stDownloadButton button {
            background-color: #1e2227 !important;
            color: #FFD700 !important;
            border: 2px solid #FFD700 !important;
            font-weight: bold !important;
            text-transform: uppercase;
        }
        .stButton button:hover, .stDownloadButton button:hover {
            background-color: #FFD700 !important;
            color: #0e1117 !important;
        }
        /* Mencari semua tombol di form maupun tombol download */
        .stButton button, .stDownloadButton button {
            background-color: #1a1e24 !important; /* Background Navy Tua Gelap */
            color: #FFD700 !important; /* Tulisan warna Emas */
            border: 3px solid #FFD700 !important; /* Bingkai Emas Tebal */
            border-radius: 12px !important; /* Sudut melengkung premium */
            padding: 12px 24px !important;
            font-size: 1.1rem !important;
            font-weight: 800 !important;
            text-transform: uppercase !important; /* Huruf besar semua */
            letter-spacing: 1.5px; /* Spasi antar huruf biar gagah */
            transition: all 0.3s ease-in-out; /* Efek transisi halus */
            box-shadow: 0 4px 10px rgba(0,0,0,0.5); /* Shadow biar timbul */
        }

        /* Efek pas kursor diarahkan ke tombol (Hover) */
        .stButton button:hover, .stDownloadButton button:hover {
            background-color: #FFD700 !important; /* Background berubah jadi Emas Solid */
            color: #0e1117 !important; /* Tulisan berubah jadi Hitam biar kontras parah */
            transform: translateY(-3px); /* Tombol sedikit terangkat */
            box-shadow: 0 8px 20px rgba(255, 215, 0, 0.4); /* Efek glow emas */
        }
        
        /* Menghilangkan border default yang jelek di sekitar tombol saat fokus */
        .stButton button:focus, .stDownloadButton button:focus {
            box-shadow: 0 0 0 4px rgba(255, 215, 0, 0.5) !important;
            outline: none !important;
        }

        /* Memperbaiki alignment icon roket agar sejajar teks */
        .stButton button span {
            display: flex;
            align-items: center;
            justify-content: center;
        }
        /* Samakan warna teks input number (Koli & Ongkir) agar putih */
        input[type="number"] {
            color: #ffffff !important;
            background-color: #0e1117 !important;
        }
        /* 1. TARGETING HEADER EXPANDER (INPUT & BATCH OPS) */
        /* Kita paksa background jadi Navy Gelap dan teks jadi Emas */
        [data-testid="stExpander"] details summary {
            background-color: #1a1e24 !important; /* Warna Gelap Industrial */
            color: #FFFFFF !important; /* Teks Emas */
            border: 1px solid #3e444d !important;
            border-radius: 8px !important;
            padding: 10px 15px !important;
            transition: 0.3s !important;
        }
        /* Style Tombol Hapus (Warna Merah Reject) */
        .stButton button.btn-hapus {
            background-color: #2a1a1a !important;
            color: #ff4b4b !important;
            border: 2px solid #ff4b4b !important;
        }
        .stButton button.btn-hapus:hover {
            background-color: #ff4b4b !important;
            color: #ffffff !important;
        }
        /* Style Tabel & Metric */
        div[data-testid="stMetricValue"] { color: #FFD700; font-weight: bold; }
        .stTable { background-color: #1e2227; border-radius: 5px; }
        /* Matrix/Metric Card Style */
        [data-testid="stMetricValue"] {
            color: #FFD700 !important;
            font-size: 28px !important;
            font-weight: 700 !important;
        }[data-testid="stMetricLabel"] {
            color: #ffffff !important;
            font-size: 14px !important;
            letter-spacing: 1px;
        }
        .stMetric {
            background-color: #1e2227;
            padding: 15px;
            border-radius: 10px;
            border-left: 5px solid #FFD700;
        }
        </style>
        """, unsafe_allow_html=True)

    def clean_currency(value):
        if pd.isna(value) or value == "":
            return 0
        # Buang Rp, buang titik (ribuan), buang koma (desimal), buang spasi
        clean_val = str(value).replace('Rp', '').replace('.', '').replace(',', '').strip()
        try:
            # Pake float dulu baru int buat jaga-jaga kalau ada desimal
            return int(float(clean_val))
        except:
            return 0

    def save_data(supplier, ekspedisi, koli, ongkir, tanggal_jam): 
        try:
            data = {
                "supplier": supplier.upper(), 
                "ekspedisi": ekspedisi, 
                "total_koli": koli, 
                "total_ongkir": ongkir,
                "created_at": tanggal_jam 
            }
            if supabase_global:
                supabase_global.table("shipping_costs").insert(data).execute()
                st.cache_data.clear()
            return True
        except Exception as e:
            st.error(f"Gagal simpan: {e}")
            return False
    
    # --- 4. HERO HEADER ---
    st.markdown("""
        <div class="hero-header">
            <h1>DATABASE ONGKIR IN/OUT</h1>
        </div>
        """, unsafe_allow_html=True)


    # --- 6. DASHBOARD & FILTERING ---
    # --- 2. LOGIKA DATA ---
    df_raw = fetch_table_data("shipping_costs")

    # --- 3. TAMPILAN TABS ---
    tab_input, tab_summary = st.tabs(["📥 INPUT DATA", "📊 SUMMARY & HISTORY"])

    with tab_input:
    # Form Input Manual
        with st.expander("🛻 INPUT DATA ONGKIR BARU", expanded=True):
            with st.form("form_ongkir_single", clear_on_submit=True):
                col_a, col_b = st.columns(2)
                with col_a:
                    supplier_input = st.text_input("Nama Supplier", placeholder="Tulis Nama Supplier....")
                    ekspedisi_input = st.text_input("Nama Ekspedisi", placeholder="Tulis Nama Ekspedisi...").upper()
                    # --- TAMBAHAN INPUT TANGGAL ---
                    input_tgl = st.date_input("Tanggal Transaksi", value=datetime.now())
                with col_b:
                    koli_input = st.number_input("Total Koli", min_value=1, step=1)
                    ongkir_input = st.number_input("Total Ongkir (Rp)", min_value=0, step=5000)
                    # --- TAMBAHAN INPUT JAM ---
                    input_jam = st.time_input("Jam Transaksi", value=datetime.now().time())
                
                # Gabungkan tanggal dan jam biar formatnya bersih
                fix_timestamp = f"{input_tgl} {input_jam.strftime('%H:%M:%S')}"
                
                if st.form_submit_button("▶️ UPLOAD HASIL ONGKIR"):
                    if supplier_input:
                        # Panggil fungsi dengan fix_timestamp
                        if save_data(supplier_input, ekspedisi_input, koli_input, ongkir_input, fix_timestamp):
                            st.success(f"Data {supplier_input.upper()} Berhasil Disimpan!")
                            st.rerun()
                    else:
                        st.error("Nama Supplier wajib diisi!")

        st.markdown("---")

        # Batch Upload
        with st.expander("📁 BATCH OPS: UPLOAD MASSAL", expanded=False):
            c_dl, c_up = st.columns([1, 2])
            with c_dl:
                st.markdown("### 1. Download")
                # Tambah kolom TANGGAL_JAM di template
                template_df = pd.DataFrame(columns=["SUPPLIER", "EKSPEDISI", "TOTAL KOLI", "ONGKIR", "TANGGAL_JAM"])
                st.download_button(
                    label="📄 DOWNLOAD TEMPLATE", 
                    data=template_df.to_csv(index=False).encode('utf-8'), 
                    file_name="template_ongkir_jezpro.csv", 
                    mime="text/csv"
                )
            
            with c_up:
                st.markdown("### 2. Upload")
                uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
                if uploaded_file:
                    df_mass = pd.read_csv(uploaded_file)
                    # Tambah TANGGAL_JAM di required
                    required =["SUPPLIER", "EKSPEDISI", "TOTAL KOLI", "ONGKIR", "TANGGAL_JAM"]
                    if all(col in df_mass.columns for col in required):
                        if st.button("▶️ UPLOAD BULK ONGKIR"):
                            with st.spinner('Processing...'):
                                batch_list =[] # Buat list kosong dulu
                                for _, row in df_mass.iterrows():
                                    data_batch = {
                                        "supplier": str(row["SUPPLIER"]).upper(), 
                                        "ekspedisi": str(row["EKSPEDISI"]).upper(), 
                                        "total_koli": int(row["TOTAL KOLI"]), 
                                        "total_ongkir": clean_currency(row["ONGKIR"]),
                                        "created_at": str(row["TANGGAL_JAM"]) 
                                    }
                                    batch_list.append(data_batch) # Masukkan ke list
                                
                                # Eksekusi insert SEMUA data sekaligus dalam 1x request
                                if batch_list and supabase_global:
                                    supabase_global.table("shipping_costs").insert(batch_list).execute()
                                    st.cache_data.clear() # Bersihkan cache agar data baru langsung terbaca
                                    
                            st.success("Berhasil diinput!")
                            st.rerun()
                    else:
                        st.error(f"Format salah! Harus: {required}")

    with tab_summary:
            if not df_raw.empty:
                # 1. Konversi datetime
                df_raw['created_at'] = pd.to_datetime(df_raw['created_at'])

                st.markdown("### 🔍 FILTER DATA")
                
                # --- FUNGSI CALLBACK (SOLUSI KEDUT-KEDUT) ---
                def update_range_callback():
                    pilihan = st.session_state.preset_choice
                    hari_ini = date.today()
                    if pilihan == "Today":
                        st.session_state.date_val = (hari_ini, hari_ini)
                    elif pilihan == "This Month":
                        st.session_state.date_val = (hari_ini.replace(day=1), hari_ini)
                    elif pilihan == "All Time":
                        # Pastikan df_raw tersedia di scope ini
                        st.session_state.date_val = (df_raw['created_at'].min().date(), df_raw['created_at'].max().date())

                col_f1, col_f2 = st.columns(2)
                
                with col_f1:
                    # Inisialisasi session_state
                    if 'date_val' not in st.session_state:
                        st.session_state.date_val = (df_raw['created_at'].min().date(), df_raw['created_at'].max().date())

                    # INPUT TANGGAL (Gunakan key yang sama dengan session_state)
                    date_range = st.date_input(
                        "Rentang Tanggal", 
                        value=st.session_state.date_val,
                        key="date_val"
                    )

                    # DROPDOWN PRESET
                    st.selectbox(
                        "Quick Select Range:",
                        ["Custom Range", "Today", "This Month", "All Time"],
                        key="preset_choice",
                        index=0,
                        on_change=update_range_callback
                    )

                with col_f2:
                    list_ekspedisi = ["SEMUA"] + sorted(df_raw['ekspedisi'].unique().tolist())
                    pilih_ekspedisi = st.selectbox("Pilih Ekspedisi", list_ekspedisi)

                # --- APPLY FILTER ---
                # Pastikan logic filtering handle tuple dari date_input
                if isinstance(date_range, tuple) and len(date_range) == 2:
                    start_date, end_date = date_range
                    mask = (df_raw['created_at'].dt.date >= start_date) & (df_raw['created_at'].dt.date <= end_date)
                    df_filtered = df_raw.loc[mask].copy()
                else:
                    df_filtered = df_raw.copy()
                    
                if pilih_ekspedisi != "SEMUA":
                    df_filtered = df_filtered[df_filtered['ekspedisi'] == pilih_ekspedisi]

                # --- TAMPILAN MATRIX ---
                st.markdown("""
                    <div style="background-color: #1e2227; padding: 10px 15px; border-radius: 8px; border-left: 5px solid #FFD700; margin-top: 25px; margin-bottom: 15px;">
                        <h4 style="color: white; margin: 0; font-family: 'Inter', sans-serif; font-size: 18px; font-weight: 600;">💲 TOTAL BIAYA ONGKIR</h4>
                    </div>
                """, unsafe_allow_html=True)

                total_biaya = df_filtered['total_ongkir'].sum()
                total_koli = df_filtered['total_koli'].sum()
                avg = total_biaya / total_koli if total_koli > 0 else 0

                mask_rto = df_filtered['supplier'].str.contains('RTO', case=False, na=False)
                biaya_rto = df_filtered[mask_rto]['total_ongkir'].sum()
                biaya_datang = df_filtered[~mask_rto]['total_ongkir'].sum()

                # --- TAMPILAN BARIS 1 ---
                m1, m2, m3 = st.columns(3)
                with m1:
                    st.metric("TOTAL BIAYA ALL", f"Rp {total_biaya:,.0f}")
                with m2:
                    st.metric("TOTAL KOLI", f"{total_koli} Pcs")
                with m3:
                    st.metric("AVG COST/KOLI", f"Rp {avg:,.0f}")

                # --- TAMPILAN BARIS 2 (Breakdown Metrics) ---
                m4, m5 = st.columns(2)
                with m4:
                    st.metric("BIAYA RTO", f"Rp {biaya_rto:,.0f}", delta_color="inverse")
                with m5:
                    st.metric("BIAYA BARANG DATANG", f"Rp {biaya_datang:,.0f}")

                # --- DATA TABLE & DELETE ---
                st.markdown("---")
                st.subheader("📝 Riwayat Transaksi")
                df_display = df_filtered.copy()
                df_display['created_at'] = df_display['created_at'].dt.strftime('%Y-%m-%d %H:%M:%S')

                event = st.dataframe(
                    df_display.sort_values('created_at', ascending=False),
                    use_container_width=True,
                    hide_index=True,
                    on_select="rerun",
                    selection_mode="multi-row"
                )

                selected_rows = event.selection.rows
                if selected_rows:
                    # Ambil ID untuk dihapus
                    df_sorted = df_display.sort_values('created_at', ascending=False)
                    ids_to_delete = df_sorted.iloc[selected_rows]['id'].tolist()
                    
                    st.warning(f"Terpilih {len(ids_to_delete)} data untuk dihapus.")
                    if st.button("🗑️ HAPUS DATA TERPILIH", type="primary"):
                        try:
                            if supabase_global:
                                for tid in ids_to_delete:
                                    supabase_global.table("shipping_costs").delete().eq("id", tid).execute()
                                st.cache_data.clear()
                            st.success("Data berhasil dihapus!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Gagal hapus: {e}")
                else:
                    st.info("💡 Centang baris di tabel untuk menghapus data.")
            else:
                st.info("Data masih kosong.")    

def menu_reject_defect():
    # --- CSS AREA (WAJIB LENGKAP - TIDAK ADA YANG DIPOTONG) ---
    st.markdown("""
        <style>
        /* Header Hero */
        .hero-header {
            background-color: #007BFF;
            color: white;
            padding: 12px;
            border-radius: 8px;
            text-align: center;
            margin-bottom: 25px;
            font-weight: bold;
            font-size: 20px;
            box-shadow: 0 4px 15px rgba(0, 123, 255, 0.3);
        }
        
        /* Label Form Atas */
        [data-testid="stWidgetLabel"] p {
            color: #31333F !important;
            font-weight: 700 !important;
        }

        /* Box Input (Navy Gelap) */
        div[data-testid="stTextInput"] > div > div, 
        div[data-testid="stTextArea"] > div > div,
        div[data-testid="stSelectbox"] > div > div {
            background-color: #1a1c27 !important;
            border: 1px solid #3d4156 !important;
            border-radius: 8px !important;
        }
        
        input, textarea, div[data-baseweb="select"] > div { 
            color: white !important; 
        }

        /* Button Style */
        button[kind="primaryFormSubmit"] {
            background-color: #007BFF !important;
            color: white !important;
            border-radius: 8px !important;
            width: 100% !important;
            height: 48px !important;
            font-weight: bold !important;
        }

        div.stDownloadButton > button {
            background-color: #D4AF37 !important;
            color: white !important;
            border: 1px solid #FFD700 !important;
            border-radius: 8px !important;
            font-weight: bold !important;
        }

        /* --- CSS METRIC BOX: PUTIH, TEBAL, RAPI --- */
        [data-testid="stMetric"] {
            background-color: #1a1c27 !important;
            border: 1px solid #3d4156 !important;
            padding: 20px !important; 
            border-radius: 12px !important;
            min-height: 150px !important; 
        }

        [data-testid="stMetricLabel"] > div {
            color: #FFFFFF !important;
            font-weight: 800 !important;
            font-size: 15px !important;
        }

        [data-testid="stMetricValue"] > div {
            color: #FFFFFF !important; 
            font-weight: 900 !important; 
            font-size: 38px !important;
        }[data-testid="stMetricDelta"] > div {
            font-weight: bold !important;
        }

        /* Judul Mass Adjustment Section */
        h1, h2, h3, .stMarkdown h3 {
            color: #FFFFFF !important;
            font-weight: 800 !important;
        }

        /* Fix Judul Detail Database: Hitam & Tebal */
        .detail-header {
            color: #31333F !important;
            font-weight: 800 !important;
            font-size: 22px !important;
            margin-top: 30px !important;
            margin-bottom: 10px !important;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        /* FIX: p yang ada di Main Content */
        [data-testid="stMain"] .stMarkdown p {
            color: #E0E0E0 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="hero-header">⚠️ REJECT / DEFECT LIST ENTRY</div>', unsafe_allow_html=True)

    tab_entry, tab_analytics, tab_match = st.tabs(["📥 ENTRY DATA", "📊 ANALYTICS DASHBOARD", "🔍 MATCH DEFECT/REJECT"])

    def save_data(df):
        if supabase_global:
            data_dict = df.to_dict(orient='records')
            supabase_global.table("reject_list").insert(data_dict).execute()
            st.cache_data.clear()

    def delete_reject_item(row_id):
        if supabase_global:
            supabase_global.table("reject_list").delete().eq("id", row_id).execute()
            st.cache_data.clear()

    def clear_all_data():
        if supabase_global:
            supabase_global.table("reject_list").delete().gt("id", 0).execute()
            st.cache_data.clear()
            st.rerun()

    with tab_entry:
        with st.form("form_reject_new", clear_on_submit=True):
            cabang_input = st.selectbox("📍 LOKASI OPERASIONAL", ["SURABAYA", "SIDOARJO", "SEMARANG"])
            col1, col2 = st.columns(2)
            with col1:
                bin_awal = st.text_input("BIN AWAL")
                bin_val = st.selectbox("BIN TUJUAN",["REJECT DC", "DEFECT DC", "DEFECT STORE", "REJECT STORE"])
                sku = st.text_input("SKU")
                article = st.text_input("NAMA BARANG")
            with col2:
                size = st.text_input("SIZE")
                kategori = st.selectbox("KATEGORI DEFECT",["D1", "D2", "D3", "D4", "R1", "R3", "R4", "HANYA SEBELAH KIRI", "HANYA SEBELAH KANAN", "BERBEDA ARTICLE", "BERBEDA SIZE"])
                keterangan = st.text_area("DETAIL KERUSAKAN")

            btn_submit = st.form_submit_button("📤 UPLOAD SINGLE LIST")

        if btn_submit and sku:
            jam = (dt_logic.datetime.now() + dt_logic.timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S")
            new_data = pd.DataFrame([{
                'cabang': cabang_input, 'bin_awal': bin_awal, 'bin': bin_val, 'sku': sku, 
                'article_name': article, 'size': size, 'kategori': kategori, 
                'keterangan': keterangan, 'tanggal_input': jam
            }])
            save_data(new_data)
            st.success(f"✅ SKU {sku} Berhasil Disimpan ke Cloud!")
            st.rerun()

        st.markdown('<div style="background-color: #1a1c27; padding: 10px; border-left: 5px solid #007BFF; border-radius: 5px; margin-top: 20px; margin-bottom: 20px;"><h3 style="color: #007BFF; margin: 0; font-size: 18px; font-weight: 900;">📂 MASS ADJUSTMENT - IMPORT EXCEL</h3></div>', unsafe_allow_html=True)
        
        col_dl, col_up = st.columns([1, 2])
        with col_dl:
            template_cols =['cabang', 'bin_awal', 'bin', 'sku', 'article_name', 'size', 'kategori', 'keterangan']
            df_template = pd.DataFrame(columns=template_cols)
            
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_template.to_excel(writer, index=False, sheet_name='Template_Upload')
                workbook = writer.book
                worksheet = writer.sheets['Template_Upload']
                header_format = workbook.add_format({'bold': True, 'bg_color': '#FFD700', 'border': 1})
                for col_num, value in enumerate(df_template.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                    worksheet.set_column(col_num, col_num, 20)

            st.download_button(
                label="📥 Download Template Excel",
                data=output.getvalue(),
                file_name="template_reject_massal.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        with col_up:
            if 'upload_key' not in st.session_state: st.session_state.upload_key = 0
            uploaded_file = st.file_uploader("Upload Excel Massal", type=['xlsx'], key=f"excel_up_{st.session_state.upload_key}")

            if uploaded_file:
                df_upload = pd.read_excel(uploaded_file)
                
                if st.button("⤴️ IMPORT DATA KE DATABASE"):
                    now_plus_7 = (dt_logic.datetime.now() + dt_logic.timedelta(hours=7))
                    df_upload['tanggal_input'] = now_plus_7.isoformat()
                    db_cols =['cabang', 'bin_awal', 'bin', 'sku', 'article_name', 'size', 'kategori', 'keterangan', 'tanggal_input']
                    valid_cols =[c for c in db_cols if c in df_upload.columns]
                    df_final = df_upload[valid_cols].copy()
                    
                    save_data(df_final)
                    
                    st.session_state.upload_key += 1
                    st.success("✅ Import Cloud Berhasil!")
                    st.rerun()

    with tab_analytics:
        try:
            df_chart = fetch_table_data("reject_list")
            if not df_chart.empty and 'tanggal_input' in df_chart.columns:
                df_chart['tanggal_input'] = pd.to_datetime(df_chart['tanggal_input'], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            st.error(f"Gagal narik data: {e}")
            df_chart = pd.DataFrame()
        
        standard_codes =['D1', 'D2', 'D3', 'D4', 'R1', 'R2', 'R3', 'R4']
        if not df_chart.empty:
            df_non_std = df_chart[~df_chart['kategori'].isin(standard_codes)].copy()
            if not df_non_std.empty:
                def find_matches(row, full_df):
                    matches = full_df[(full_df['sku'] == row['sku']) & (full_df['id'] != row['id'])]
                    return ", ".join(matches['cabang'].unique()) if not matches.empty else "TIDAK ADA"
                df_non_std['MATCH_DI_CABANG'] = df_non_std.apply(lambda x: find_matches(x, df_chart), axis=1)
                df_match_result = df_non_std[df_non_std['MATCH_DI_CABANG'] != "TIDAK ADA"]
            else:
                df_match_result = pd.DataFrame()

            col_f1, col_f2 = st.columns([1, 2])
            with col_f1:
                filter_view = st.selectbox("📍 FILTER CABANG:",["SEMUA", "SURABAYA", "SIDOARJO", "SEMARANG"], key="filter_dash")
            with col_f2:
                search_query = st.text_input("🔍 CARI SKU ATAU NAMA BARANG:", placeholder="Ketik SKU / Nama Barang di sini...", key="search_bar")

            df_final = df_chart if filter_view == "SEMUA" else df_chart[df_chart['cabang'] == filter_view]

            if search_query:
                df_final = df_final[
                    (df_final['sku'].str.contains(search_query, case=False, na=False)) | 
                    (df_final['article_name'].str.contains(search_query, case=False, na=False))
                ]

            total_val = len(df_final)
            defect_cnt = len(df_final[df_final['bin'].str.contains('DEFECT', case=False, na=False)])
            reject_cnt = len(df_final[df_final['bin'].str.contains('REJECT', case=False, na=False)])

            if 'last_total' not in st.session_state:
                st.session_state.last_total, st.session_state.last_defect, st.session_state.last_reject = total_val, defect_cnt, reject_cnt

            def get_delta(current, last):
                if current > last: return "↑", "#28a745", "rgba(40,167,69,0.1)"
                elif current < last: return "↓", "#FF4B4B", "rgba(255,75,75,0.1)"
                return "•", "#888", "rgba(136,136,136,0.1)"

            arr_t, col_t, bg_t = get_delta(total_val, st.session_state.last_total)
            arr_d, col_d, bg_d = get_delta(defect_cnt, st.session_state.last_defect)
            arr_r, col_r, bg_r = get_delta(reject_cnt, st.session_state.last_reject)

            st.session_state.last_total, st.session_state.last_defect, st.session_state.last_reject = total_val, defect_cnt, reject_cnt

            m1, m2, m3 = st.columns(3)
            with m1:
                st.markdown(f'<div style="background-color: #1E1E26; padding: 20px; border-radius: 10px; border-left: 5px solid #007BFF;"><p style="color: #888; margin: 0; font-size: 0.9rem;">TOTAL ITEMS</p><h2 style="color: white; margin: 0; font-weight: 800;">{total_val} SKU</h2><span style="color: {col_t}; font-size: 0.8rem; background: {bg_t}; padding: 2px 8px; border-radius: 10px;">{arr_t} {total_val} Result</span></div>', unsafe_allow_html=True)
            with m2:
                p_d = (defect_cnt/total_val*100) if total_val > 0 else 0
                st.markdown(f'<div style="background-color: #1E1E26; padding: 20px; border-radius: 10px; border-left: 5px solid #FFA500;"><p style="color: #888; margin: 0; font-size: 0.9rem;">📦 DEFECT (D)</p><h2 style="color: white; margin: 0; font-weight: 800;">{defect_cnt}</h2><span style="color: {col_d}; font-size: 0.8rem; background: {bg_d}; padding: 2px 8px; border-radius: 10px;">{arr_d} {p_d:.1f}%</span></div>', unsafe_allow_html=True)
            with m3:
                p_r = (reject_cnt/total_val*100) if total_val > 0 else 0
                st.markdown(f'<div style="background-color: #1E1E26; padding: 20px; border-radius: 10px; border-left: 5px solid #FF4B4B;"><p style="color: #888; margin: 0; font-size: 0.9rem;">❌ REJECT (R)</p><h2 style="color: white; margin: 0; font-weight: 800;">{reject_cnt}</h2><span style="color: {col_r}; font-size: 0.8rem; background: {bg_r}; padding: 2px 8px; border-radius: 10px;">{arr_r} {p_r:.1f}%</span></div>', unsafe_allow_html=True)

            st.markdown('<div class="detail-header">📋 DETAIL DATABASE CLOUD</div>', unsafe_allow_html=True)
            df_editor = df_final.copy().sort_values('id', ascending=False)
            df_editor['HAPUS'] = False

            event = st.data_editor(
                df_editor,
                column_config={"id": None, "HAPUS": st.column_config.CheckboxColumn("🗑️", default=False)},
                use_container_width=True, hide_index=True, key="database_editor"
            )

            rows_to_delete = event[event['HAPUS'] == True]
            if not rows_to_delete.empty:
                st.error(f"⚠️ **SIAP DIHAPUS:** {len(rows_to_delete)} item terpilih.")
                if st.button(f"🗑️ HAPUS {len(rows_to_delete)} DATA TERPILIH", type="primary", use_container_width=True):
                    for rid in rows_to_delete['id']: delete_reject_item(rid)
                    st.rerun()
            else:
                if st.button("🚨 KOSONGKAN SEMUA DATABASE", use_container_width=True):
                    clear_all_data()

    with tab_match:
        st.markdown('<div style="background-color: #1E1E26; padding: 15px 20px; border-radius: 5px; border-left: 5px solid #007BFF; margin-bottom: 20px;"><h3 style="color: white !important; margin: 0; font-weight: 700; font-size: 1.2rem; display: flex; align-items: center;">🔍 CROSS-CHECK SKU MATCHING</h3></div>', unsafe_allow_html=True)
        
        if 'df_match_result' in locals() and not df_match_result.empty:
            def check_kiri_kanan_logic(group):
                categories = group['kategori'].astype(str).str.lower().values
                has_kiri = any('kiri' in cat for cat in categories)
                has_kanan = any('kanan' in cat for cat in categories)
                return has_kiri and has_kanan

            sku_valid = df_match_result.groupby('sku').filter(check_kiri_kanan_logic)['sku'].unique()
            df_filtered = df_match_result[df_match_result['sku'].isin(sku_valid)].copy()

            if not df_filtered.empty:
                m_col1, m_col2 = st.columns(2)
                with m_col1:
                    st.markdown(f'<div style="background-color: #1E1E26; padding: 20px; border-radius: 10px; border-left: 5px solid #007BFF;"><p style="color: #888; margin: 0; font-size: 0.8rem;">MATCH FOUND (KIRI-KANAN)</p><h2 style="color: white; margin: 0; font-weight: 800;">{len(df_filtered)} Items</h2></div>', unsafe_allow_html=True)
                with m_col2:
                    st.markdown(f'<div style="background-color: #1E1E26; padding: 20px; border-radius: 10px; border-left: 5px solid #6c757d;"><p style="color: #888; margin: 0; font-size: 0.8rem;">UNIQUE SKU</p><h2 style="color: white; margin: 0; font-weight: 800;">{df_filtered["sku"].nunique()}</h2></div>', unsafe_allow_html=True)
                
                df_core = df_filtered[['sku', 'article_name']].drop_duplicates()
                df_temp = df_filtered[['sku', 'cabang']].drop_duplicates()
                
                df_pivot = df_temp.pivot(index='sku', columns='cabang', values='cabang').notna()
                
                def get_match_route(row):
                    active_branches = [col for col in df_pivot.columns if row[col] == True]
                    return " ↔️ ".join(active_branches) if len(active_branches) > 1 else active_branches[0]

                df_pivot['Match Route'] = df_pivot.apply(get_match_route, axis=1)
                df_pivot = df_pivot.replace({True: '✅', False: ''})
                
                df_final_match = df_core.merge(df_pivot, on='sku', how='left')

                st.markdown('<div style="margin-bottom: 10px; padding: 5px 0;"><span style="color: #000000 !important; font-size: 1.1rem !important; font-weight: 800 !important;">📋 Summary Match SKU & Kategori</span></div>', unsafe_allow_html=True)
                
                cols = ['sku', 'article_name', 'Match Route'] +[c for c in df_temp['cabang'].unique() if c in df_final_match.columns]
                st.data_editor(df_final_match[cols], use_container_width=True, hide_index=True, key="match_pivot_final")
            else:
                st.warning("⚠️ SKU match ditemukan, tapi tidak ada pasangan Kategori yang cocok.")
        else:
            st.success("✅ Tidak ditemukan Reject/Defect Match")

def project_approval_reject():
    st.markdown(""" 
        <style> 
        .hero-header-custom { 
            background: linear-gradient(135deg, #1e468a 0%, #163462 100%); 
            color: white; padding: 12px 25px; border-radius: 10px; 
            margin-bottom: 25px; font-weight: 800; font-size: 22px; 
            box-shadow: 0 4px 15px rgba(0,0,0,0.2); width: fit-content;  
        } 
        .detail-card { 
            background-color: #1a1c27; border: 1px solid #3d4156; 
            padding: 20px; border-radius: 12px; margin-bottom: 20px; 
        }[data-testid="stForm"] { border: none !important; padding: 0 !important; } 
        div[data-testid="stTextInput"] > div > div,  
        div[data-testid="stTextArea"] > div > div, 
        div[data-testid="stSelectbox"] > div > div { 
            background-color: #1a1c27 !important; 
            border: 1px solid #3d4156 !important; 
            border-radius: 8px !important; 
        } 
        input, textarea, div[data-baseweb="select"] span { color: white !important; } 
        label { color: #E0E0E0 !important; font-weight: 600 !important; } 
        div.stButton > button { 
            background: linear-gradient(135deg, #1e468a 0%, #163462 100%) !important; 
            color: white !important; border-radius: 10px !important; 
            width: 100% !important; height: 50px !important; font-weight: bold !important; 
            border: none !important; 
        } 
        .gold-btn button { 
            background-color: #D4AF37 !important; 
            color: white !important; border: none !important; 
            border-radius: 8px !important; font-weight: bold !important; 
            box-shadow: 0 0 10px rgba(255, 215, 0, 0.4), 0 0 20px rgba(255, 215, 0, 0.2); 
            text-shadow: 0 0 5px rgba(255, 255, 255, 0.8); 
            transition: all 0.3s ease-in-out; 
        } 
        .gold-btn button:hover { 
            background-color: #FFD700 !important; 
            color: #1a1c27 !important; 
            box-shadow: 0 0 20px rgba(255, 215, 0, 0.8), 0 0 40px rgba(255, 215, 0, 0.4); 
            transform: translateY(-2px); 
        } 
        .timeline-line { 
            height: 4px; background: #3d4156; margin-top: 15px; border-radius: 2px; 
        } 
        .line-active { 
            background: #1E90FF !important; box-shadow: 0 0 8px rgba(30, 144, 255, 0.6); 
        } 
        </style> 
    """, unsafe_allow_html=True)

    st.markdown('<div class="hero-header-custom">📋 PENGAJUAN REJECT / DEFECT</div>', unsafe_allow_html=True) 
    tabs = st.tabs(["💻 Input Pengajuan", "📑 History & Approval Status"]) 

    with tabs[0]: 
        st.markdown(""" 
            <div style="background-color: #1a1c27; padding: 10px; border-left: 5px solid #007BFF; border-radius: 5px; margin-top: 20px; margin-bottom: 20px;"> 
                <h3 style="color: #FFFFFF; margin: 0; font-size: 18px; font-weight: 900;">Form Pengajuan Reject/Defect</h3> 
            </div> 
        """, unsafe_allow_html=True) 
        
        with st.form("input_form_reject", clear_on_submit=True): 
            col1, col2 = st.columns(2) 
            with col1: 
                nama = st.text_input("Nama Tim (Pengaju)") 
                bin_asal = st.text_input("Bin Asal") 
                sku = st.text_input("SKU") 
                cabang_input = st.selectbox("Pilih Cabang",["SURABAYA", "SIDOARJO", "SEMARANG"]) 
            with col2: 
                article = st.text_input("Article Name") 
                size = st.text_input("Size") 
                keterangan = st.text_area("Keterangan Reject/Defect") 
            
            if st.form_submit_button("▶️ SUBMIT REQUEST"): 
                if nama and sku: 
                    tz_jakarta = pytz.timezone('Asia/Jakarta') 
                    ts = datetime.now(tz_jakarta).strftime("%Y-%m-%d %H:%M:%S") 
                    
                    data_insert = {
                        "timestamp": ts, 
                        "nama_tim": nama, 
                        "bin_asal": bin_asal, 
                        "sku": sku, 
                        "article_name": article, 
                        "size": size, 
                        "keterangan": keterangan, 
                        "status": 1, 
                        "cabang": cabang_input
                    }
                    
                    try: 
                        if supabase_global:
                            supabase_global.table("submissions").insert(data_insert).execute()
                            st.cache_data.clear()
                        st.success(f"✅ Berhasil! Data tercatat jam {ts} WIB") 
                        st.rerun() 
                    except Exception as e: 
                        st.error(f"Gagal simpan ke Supabase: {e}") 
                else: 
                    st.warning("⚠️ Nama Tim dan SKU wajib diisi!") 

    with tabs[1]:
        st.markdown(""" 
            <style> 
            [data-testid="stMain"] div[data-testid="stRadio"] label p { 
                color: #000000 !important; 
                font-weight: 500 !important; 
            } 
            [data-testid="stMain"] div[data-testid="stExpander"] summary p { 
                color: #FFFFFF !important; 
                font-weight: bold !important; 
            } 
            [data-testid="stMain"] div[data-testid="stExpander"] { 
                background-color: #1a1c27 !important; 
                border: 1px solid #3d4156 !important; 
                border-radius: 12px !important; 
                box-shadow: 0 4px 12px rgba(0,0,0,0.5) !important; 
            } 
            .timeline-line {
                height: 4px;
                background: #3d4156;
                margin-top: 15px;
                border-radius: 2px;
            }
            .line-active {
                background: #00ff00 !important;
                box-shadow: 0 0 8px #00ff00;
            }[data-testid="stMain"] .stMarkdown p { 
                color: #FFFFFF !important; 
            } 
            </style> 
        """, unsafe_allow_html=True)
        tab_sby, tab_sda, tab_smg = st.tabs(["📍 SURABAYA", "📍 SIDOARJO", "📍 SEMARANG"]) 
        cabang_list =[("SURABAYA", tab_sby), ("SIDOARJO", tab_sda), ("SEMARANG", tab_smg)] 

        df_all_submissions = fetch_table_data("submissions")

        for cabang_name, tab_obj in cabang_list: 
            with tab_obj: 
                col_search, col_filter = st.columns([1, 1]) 
                with col_search: 
                    search_query = st.text_input(f"🔍 Cari di {cabang_name}:", placeholder="Ketik SKU atau Nama...", key=f"src_{cabang_name}", label_visibility="collapsed").strip() 
                
                with col_filter: 
                    filter_status = st.radio("Pilih Status:",["Semua", "Waiting Approval", "Waiting Set Up", "Done Set Up"], horizontal=True, key=f"rad_{cabang_name}", label_visibility="collapsed") 

                status_map = {"Waiting Approval": 1, "Waiting Set Up": 2, "Done Set Up": 3}
                
                if not df_all_submissions.empty:
                    df = df_all_submissions[df_all_submissions['cabang'] == cabang_name]
                    if filter_status in status_map:
                        df = df[df['status'] == status_map[filter_status]]
                    df = df.sort_values("id", ascending=False)
                else:
                    df = pd.DataFrame()
                
                if not df.empty and search_query:
                    search_query = search_query.lower()
                    df = df[
                        df['sku'].str.lower().str.contains(search_query, na=False) | 
                        df['nama_tim'].str.lower().str.contains(search_query, na=False) |
                        df['article_name'].str.lower().str.contains(search_query, na=False)
                    ]

                if df.empty: 
                    st.info(f"📭 Belum ada data pengajuan untuk cabang {cabang_name}.") 
                else: 
                    df_waiting = df[df['status'] == 2]
                    if not df_waiting.empty:
                        all_excel_data = convert_all_to_excel(df)
                        st.download_button(
                            label=f"📥 Download All ({cabang_name})",
                            data=all_excel_data,
                            file_name=f"MASS_SET_UP_{cabang_name}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key=f"dl_all_{cabang_name}",
                            use_container_width=True 
                        )

                    for index, row in df.iterrows(): 
                        with st.expander(f"📦 {row['sku']} - {row['article_name']} | {row['nama_tim']}"):
                            st.markdown(f"### 📑 Detail [ID: {row['id']}]")
                            
                            c1, c2 = st.columns(2) 
                            with c1: 
                                st.markdown(f"**👤 Pengaju:** `{row['nama_tim']}`") 
                                st.markdown(f"**📍 Bin Asal:** `{row['bin_asal']}`") 
                                st.markdown(f"**🆔 SKU:** `{row['sku']}`") 
                            with c2: 
                                st.markdown(f"**👟 Article:** `{row['article_name']}`") 
                                st.markdown(f"**📏 Size:** `{row['size']}`") 
                                st.markdown(f"**🕒 Waktu:** `{row['timestamp']}`") 
                            
                            st.info(f"**📝 Keterangan:**\n\n{row['keterangan']}") 
                            st.write("---") 

                            st.write("**Progres Status:**")
                            line1_active = "line-active" if row['status'] >= 2 else "" 
                            line2_active = "line-active" if row['status'] >= 3 else "" 

                            tcol1, tline1, tcol2, tline2, tcol3 = st.columns([1.5, 2, 1.5, 2, 1.5]) 
                            
                            with tcol1: 
                                st.markdown("🟢 **Pengajuan**") 
                                st.caption("Waiting Approval") 
                            
                            with tline1: 
                                st.markdown(f'<div class="timeline-line {line1_active}"></div>', unsafe_allow_html=True) 
                            
                            with tcol2: 
                                if row['status'] >= 2: 
                                    st.markdown("🔵 **Approved**") 
                                    st.caption(f"By: {row.get('approved_by') or '-'}") 
                                else: 
                                    st.markdown("🟡 **Purchasing**") 
                                    n_app = st.text_input("Nama Purchasing", key=f"app_inp_{row['id']}", label_visibility="collapsed") 
                                    if st.button("Approve", key=f"bt_ap_{row['id']}", disabled=not n_app): 
                                        if supabase_global:
                                            supabase_global.table("submissions").update({"status": 2, "approved_by": n_app}).eq("id", row['id']).execute()
                                            st.cache_data.clear()
                                        st.rerun() 
                            
                            with tline2: 
                                st.markdown(f'<div class="timeline-line {line2_active}"></div>', unsafe_allow_html=True) 
                            
                            with tcol3: 
                                if row['status'] >= 3: 
                                    st.markdown("🟣 **Done Set Up**") 
                                    st.caption(f"By: {row.get('setup_by') or '-'}") 
                                else: 
                                    st.markdown("⚪ **Finalizing**") 
                                    if row['status'] == 2: 
                                        n_set = st.text_input("Nama Set Up", key=f"set_inp_{row['id']}", label_visibility="collapsed") 
                                        st.markdown('<div class="gold-btn">', unsafe_allow_html=True) 
                                        if st.button("Final Set Up", key=f"bt_set_{row['id']}", disabled=not n_set): 
                                            if supabase_global:
                                                supabase_global.table("submissions").update({"status": 3, "setup_by": n_set}).eq("id", row['id']).execute()
                                                st.cache_data.clear()
                                            st.rerun() 
                                        st.markdown('</div>', unsafe_allow_html=True) 

                            st.write("---") 
                            c_note = row.get('additional_note') or "" 
                            n_note = st.text_area("📝 Catatan Tambahan:", value=c_note, key=f"note_area_{row['id']}") 
                            
                            if n_note != c_note: 
                                if st.button("💾 Update Note", key=f"sn_btn_{row['id']}"): 
                                    if supabase_global:
                                        supabase_global.table("submissions").update({"additional_note": n_note}).eq("id", row['id']).execute()
                                        st.cache_data.clear()
                                    st.success("Note tersimpan!")
                                    st.rerun() 

                            with st.expander("🗑️ Hapus"): 
                                if st.button(f"Konfirmasi Hapus {row['sku']}", key=f"del_btn_{row['id']}"): 
                                    if supabase_global:
                                        supabase_global.table("submissions").delete().eq("id", row['id']).execute()
                                        st.cache_data.clear()
                                    st.rerun() 

def project_mutasi_karantina():
    st.markdown("""
    <style>
        section[data-testid="stMain"] div[data-testid="stWidgetLabel"] label {
            color: #E0E0E0 !important;
            font-weight: 600 !important;
        }
        section[data-testid="stMain"] div[data-testid="stRadio"] label p {
            color: #000000 !important;
            font-weight: 700 !important;
        }
        section[data-testid="stMain"] div[data-testid="stTextInput"] > div > div, 
        section[data-testid="stMain"] div[data-testid="stTextArea"] > div > div,
        section[data-testid="stMain"] div[data-testid="stNumberInput"] > div > div,
        section[data-testid="stMain"] div[data-testid="stSelectbox"] > div > div {
            background-color: #1a1c27 !important;
            border: 1px solid #3d4156 !important;
            border-radius: 8px !important;
        }
        section[data-testid="stMain"] input, 
        section[data-testid="stMain"] textarea, 
        section[data-testid="stMain"] div[data-baseweb="select"] span {
            color: white !important;
        }
        section[data-testid="stMain"] div[data-testid="stNumberInput"] input {
            color: white !important;
            background-color: #1a1c27 !important;
        }
        section[data-testid="stMain"] div[data-testid="stNumberInput"] button {
            background-color: #1a1c27 !important;
            color: white !important;
            border: 1px solid #3d4156 !important;
        }
        section[data-testid="stMain"] div[data-testid="stRadio"] div[role="radiogroup"] {
            gap: 15px;
        }
        .main-header { 
            background: linear-gradient(135deg, #1e468a 0%, #0d1b33 100%); 
            color: white; padding: 15px; border-radius: 10px; font-weight: 800; font-size: 20px;
            margin-bottom: 20px; border-left: 8px solid #cc0000;
        }
        div[data-testid="stForm"] button[kind="primaryFormSubmit"] {
            background: linear-gradient(135deg, #ff4b2b 0%, #ff416c 100%) !important;
            color: white !important;
            border: none !important;
            padding: 10px 20px !important;
            border-radius: 8px !important;
            font-weight: bold !important;
            transition: 0.3s !important;
            width: 100% !important;
        }
        div[data-testid="stForm"] button[kind="primaryFormSubmit"]:hover {
            transform: scale(1.02) !important;
            box-shadow: 0px 4px 15px rgba(255, 65, 108, 0.4) !important;
        }
        div[data-testid="stFileUploader"] {
            border: 1px dashed #ff416c !important;
            border-radius: 10px !important;
            padding: 10px !important;
        }
    </style>
    """, unsafe_allow_html=True)
    st.markdown('<div class="hero-header">☣️ MUTASI KARANTINA SYSTEM</div>', unsafe_allow_html=True)

    with st.expander("📋 Informasi Format File"):
        st.info("""
        **UNTUK BULK / MULTIPLE UPLOAD:**
        
        Pastikan file Excel memiliki kolom dengan urutan dan nama berikut:
        1. **BIN AWAL**
        2. **BIN TUJUAN**
        3. **SKU**
        4. **ARTICLE NAME**
        5. **QUANTITY**
        6. **NOTES**
        7. **ALASAN**
        
        *Pastikan tidak ada kolom yang kosong atau nama kolom yang typo agar terbaca sistem.*
        """)
    tabs = st.tabs(["📥 Input Mutasi", "📑 Monitoring & Approval","📦Mutasi Done Approval"])

    tz = pytz.timezone('Asia/Jakarta')
    ts = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

    with tabs[0]:
        mode = st.radio("Pilih Mode Input:", ["Single Item", "Bulk Excel (Multiple)"], horizontal=True)
        
        if mode == "Single Item":
            with st.form("form_single"):
                c1, c2 = st.columns(2)
                with c1:
                    pengaju = st.text_input("Nama PIC")
                    bin_awal = st.text_input("Bin Awal")
                    bin_tujuan = st.text_input("Bin Tujuan")
                with c2:
                    sku = st.text_input("SKU")
                    article = st.text_input("Article Name")
                    qty = st.number_input("Quantity", min_value=1)
                
                notes = st.selectbox("Notes", ["MISS LOCATION"]) 
                alasan = st.text_area("Alasan Di Mutasi", placeholder="Deskripsikan alasan mutasi di sini...")

                if st.form_submit_button("⤴️ Upload Pengajuan", type="primary"):
                    if pengaju and sku:
                        bid = f"SGL-{uuid.uuid4().hex[:4].upper()}"
                        data = {
                            "batch_id": bid, "timestamp": ts, "nama_tim": pengaju,
                            "bin_awal": bin_awal, "bin_tujuan": bin_tujuan, "sku": sku,
                            "article_name": article, "quantity": qty, "alasan": alasan, 
                            "notes": notes, "status": 1
                        }
                        if supabase_global:
                            supabase_global.table("mutasi_karantina").insert(data).execute()
                            st.cache_data.clear()
                        st.success(f"Berhasil! ID: {bid}")
                        st.rerun()

        else:
            with st.form("form_bulk"):
                pic_m = st.text_input("Nama PIC Pengaju")
                file_xlsx = st.file_uploader("Upload Excel (BIN AWAL, BIN TUJUAN, SKU, ARTICLE NAME, QUANTITY, NOTES, ALASAN)", type=['xlsx'])
                if st.form_submit_button("⤴️ Upload Pengajuan", type="primary"):
                    if pic_m and file_xlsx:
                        df = pd.read_excel(file_xlsx)
                        bid = f"BULK-{uuid.uuid4().hex[:6].upper()}"
                        bulk_data =[]
                        for _, row in df.iterrows():
                            bulk_data.append({
                                "batch_id": bid, "timestamp": ts, "nama_tim": pic_m,
                                "bin_awal": str(row.get('BIN AWAL', '')), "bin_tujuan": str(row.get('BIN TUJUAN', '')),
                                "sku": str(row.get('SKU', '')), "article_name": str(row.get('ARTICLE NAME', '')),
                                "quantity": int(row.get('QUANTITY', 0)), "notes": str(row.get('NOTES', '')),
                                "alasan": str(row.get('ALASAN', 'Bulk Upload')), "status": 1
                            })
                        if supabase_global:
                            supabase_global.table("mutasi_karantina").insert(bulk_data).execute()
                            st.cache_data.clear()
                        st.success(f"Berhasil Upload {len(bulk_data)} Item! Batch: {bid}")
                        st.rerun()

    with tabs[1]:
        st.markdown(""" 
            <style>[data-testid="stMain"] div[data-testid="stRadio"] label p { 
                color: #FFFFFF !important;  
                font-weight: 500 !important; 
            } 
            [data-testid="stMain"] div[data-testid="stExpander"] summary p { 
                color: #FFFFFF !important; 
                font-weight: bold !important; 
            } 
            [data-testid="stMain"] div[data-testid="stExpander"] { 
                background-color: #1a1c27 !important; 
                border: 1px solid #3d4156 !important; 
                border-radius: 12px !important; 
                box-shadow: 0 4px 12px rgba(0,0,0,0.5) !important; 
                margin-bottom: 10px;
            } 
            .timeline-line {
                height: 4px;
                background: #3d4156;
                margin-top: 15px;
                border-radius: 2px;
            }
            .line-active {
                background: #00ff00 !important;
                box-shadow: 0 0 8px #00ff00;
            }
            [data-testid="stMain"] .stMarkdown p { 
                color: #FFFFFF !important; 
            } 
            </style> 
        """, unsafe_allow_html=True)
        
        df_all_mutasi = fetch_table_data("mutasi_karantina")
        df_res = df_all_mutasi.sort_values("id", ascending=False) if not df_all_mutasi.empty else pd.DataFrame()

        if df_res.empty:
            st.info("Belum ada data pengajuan.")
        else:
            col_f1, col_f2 = st.columns([1.5, 1])
            with col_f1:
                filter_status = st.radio(
                    "📌 Filter Status:",
                    ["Semua", "Belum Approved", "Done Approval", "Final Done"],
                    horizontal=True,
                    key="filter_status_radio"
                )
            with col_f2:
                search_sku = st.text_input("🔍 Cari SKU", placeholder="Ketik SKU...").strip()

            df_filtered = df_res.copy()

            if filter_status == "Belum Approved":
                df_filtered = df_filtered[df_filtered['status'] == 1]
            elif filter_status == "Done Approval":
                df_filtered = df_filtered[df_filtered['status'] == 2]
            elif filter_status == "Final Done":
                df_filtered = df_filtered[df_filtered['status'] == 3]

            if search_sku:
                mask = df_filtered['sku'].str.contains(search_sku, case=False, na=False)
                valid_batches = df_filtered[mask]['batch_id'].unique()
                df_display = df_filtered[df_filtered['batch_id'].isin(valid_batches)]
            else:
                df_display = df_filtered

            batches = df_display['batch_id'].unique()
            
            if len(batches) == 0:
                st.warning("Tidak ada data yang cocok dengan filter.")
            else:
                for b_id in batches:
                    items = df_display[df_display['batch_id'] == b_id]
                    head = items.iloc[0]
                    stat = int(head['status'])

                    icon = "🔴" if stat == 1 else "🟡" if stat == 2 else "🟢"

                    with st.expander(f"{icon} {b_id} | {head['nama_tim']} | {len(items)} Item"):
                        st.write(f"**Waktu:** {head['timestamp']} | **Alasan:** {head['alasan']}")
                        st.dataframe(items[['bin_awal', 'bin_tujuan', 'sku', 'article_name', 'quantity']], use_container_width=True)
                        
                        st.write("---")
                        c_st1, c_st2, c_st3 = st.columns(3)
                        
                        with c_st1: 
                            st.markdown("1️⃣ **Approval**")
                            if stat == 1:
                                n_app = st.text_input("Approve By:", key=f"app_{b_id}")
                                if st.button("Approve Batch", key=f"bt_app_{b_id}", disabled=not n_app, type="primary"):
                                    if supabase_global:
                                        supabase_global.table("mutasi_karantina").update({"status": 2, "approved_by": n_app}).eq("batch_id", b_id).execute()
                                        st.cache_data.clear()
                                    st.rerun()
                            else: 
                                st.success(f"By: {head.get('approved_by')}")

                        with c_st2: 
                            active = "line-active" if stat >= 2 else ""
                            st.markdown(f'<div class="timeline-line {active}"></div>', unsafe_allow_html=True)
                            if stat == 2: st.caption("On Process...")

                        with c_st3: 
                            st.markdown("2️⃣ **Final Done**")
                            if stat == 2:
                                n_fin = st.text_input("Selesai By:", key=f"fin_{b_id}")
                                if st.button("Finish Batch", key=f"bt_fin_{b_id}", disabled=not n_fin, type="primary"):
                                    if supabase_global:
                                        supabase_global.table("mutasi_karantina").update({"status": 3, "setup_by": n_fin}).eq("batch_id", b_id).execute()
                                        st.cache_data.clear()
                                    st.rerun()
                            elif stat == 3: 
                                st.success(f"Done: {head.get('setup_by')}")

                        if st.button(f"🗑️ Hapus Batch {b_id}", key=f"del_{b_id}"):
                            if supabase_global:
                                supabase_global.table("mutasi_karantina").delete().eq("batch_id", b_id).execute()
                                st.cache_data.clear()
                            st.rerun()

    with tabs[2]:
        st.markdown("### 📋Template Mutasi")
        
        df_all_mutasi_work = fetch_table_data("mutasi_karantina")
        if not df_all_mutasi_work.empty:
            df_working = df_all_mutasi_work[df_all_mutasi_work['status'] == 2].sort_values("timestamp", ascending=False)
        else:
            df_working = pd.DataFrame()

        if df_working.empty:
            st.info("Tidak ada mutasi yang sedang diproses (Kuning).")
        else:
            search_work = st.text_input("🔍 Cari Data di Working List:", key="search_work_v2")
            
            if search_work:
                mask = df_working.apply(lambda row: row.astype(str).str.contains(search_work, case=False).any(), axis=1)
                df_display_work = df_working[mask]
            else:
                df_display_work = df_working

            cols_final =["batch_id", "bin_awal", "bin_tujuan", "sku", "quantity", "notes"]
            
            if 'notes' not in df_display_work.columns:
                df_display_work['notes'] = ""

            st.write(f"Menampilkan **{len(df_display_work)}** baris data.")

            st.dataframe(
                df_display_work[cols_final], 
                use_container_width=True,
                column_config={
                    "batch_id": "ID BATCH",
                    "bin_awal": "BIN AWAL",
                    "bin_tujuan": "BIN TUJUAN",
                    "sku": "SKU",
                    "quantity": st.column_config.NumberColumn("QUANTITY", format="%d"),
                    "notes": "NOTES"
                },
                hide_index=True 
            )

            if st.button("🔄 Refresh Working List", key="btn_refresh_work"):
                st.rerun()

def sync_data():
    today = datetime.now().strftime('%Y-%m-%d')
    df_date = fetch_table_data("reset_tracker")
    
    if df_date.empty:
        if supabase_global:
            supabase_global.table("reset_tracker").insert({"last_date": today}).execute()
            st.cache_data.clear()
    elif df_date.iloc[0]['last_date'] != today:
        if supabase_global:
            supabase_global.table("reports").update({"status": "❌ Belum"}).neq("status", "❌ Belum").execute()
            supabase_global.table("todo").update({"done": False}).eq("done", True).execute()
            supabase_global.table("reset_tracker").update({"last_date": today}).eq("id", int(df_date.iloc[0]['id'])).execute()
            st.cache_data.clear()

    # B. Tarik data Reports menggunakan cache global yang sudah dibuat
    df_reports = fetch_table_data("reports")
    
    # C. Default Data jika kosong
    if df_reports.empty:
        default_reports =[
            {"laporan": "REJECT & DEFECT", "pic": "VERREL & GALIH", "status": "❌ Belum"},
            {"laporan": "KERAPIHAN STOCK", "pic": "VERREL & GALIH", "status": "❌ Belum"},
            {"laporan": "CEK STOCK MINUS", "pic": "VERREL & GALIH", "status": "❌ Belum"},
            {"laporan": "BALANCING STOCK", "pic": "FARIL & YUDI", "status": "❌ Belum"},
            {"laporan": "CEK RTO", "pic": "FARIL & YUDI", "status": "❌ Belum"},
            {"laporan": "OUTBOUND PROCESS", "pic": "FARIL & YUDI", "status": "❌ Belum"},
            {"laporan": "DASHBOARD SIDOARJO", "pic": "VANO", "status": "❌ Belum"},
            {"laporan": "STORE ACTIVITY", "pic": "VANO", "status": "❌ Belum"},
            {"laporan": "DASHBOARD SURABAYA", "pic": "HAMZAH", "status": "❌ Belum"},
            {"laporan": "DASHBOARD SEMARANG", "pic": "HAMZAH", "status": "❌ Belum"},
            {"laporan": "MANIFEST", "pic": "HAMZAH", "status": "❌ Belum"},
            {"laporan": "REFUND", "pic": "HAMZAH", "status": "❌ Belum"},
            {"laporan": "REFILL GL4 TO GL3", "pic": "KRISNA & DHIVA", "status": "❌ Belum"},
            {"laporan": "COMPARE SYSTEM BEFORE & AFTER", "pic": "KRISNA & DHIVA", "status": "❌ Belum"},
            {"laporan": "COMPARE SCAN OUT", "pic": "BAKCLINER", "status": "❌ Belum"},
            {"laporan": "COMPARE BARANG DATANG", "pic": "BAKCLINER", "status": "❌ Belum"},
            {"laporan": "STAGGING LT.3 DAN GL3.DC PUTAWAY CLEAR", "pic": "WAREHOUSE FULLFILLMENT", "status": "❌ Belum"},
            {"laporan": "TIDAK ADA PESANAN DIBAWAH JAM 21.00 YANG MENGGANTUNG", "pic": "WAREHOUSE FULLFILLMENT", "status": "❌ Belum"}
        ]
        if supabase_global:
            supabase_global.table("reports").insert(default_reports).execute()
            st.cache_data.clear() # Reset cache karena ada insert
        df_reports = fetch_table_data("reports") # Tarik ulang

    # Masukkan ke session state
    st.session_state.db_report =[{"Laporan": r['laporan'], "PIC": r['pic'], "Status": r['status']} for _, r in df_reports.iterrows()] if not df_reports.empty else[]
    
    # D. Tarik Data To Do List
    df_todo = fetch_table_data("todo")
    st.session_state.todo_list = [{"id": t['id'], "task": t['task'], "done": t['done']} for _, t in df_todo.iterrows()] if not df_todo.empty else[]

if 'db_report' not in st.session_state:
    sync_data()

# --- 3. FULL CSS (GABUNGAN SEMUA STYLE) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    html, body,[class*="css"] { font-family: 'Inter', sans-serif; }

    .hero-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        color: white; padding: 25px; border-radius: 12px;
        text-align: center; margin-bottom: 35px; font-weight: 800; font-size: 26px;
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.3); border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .report-card {
        background-color: #1f2937; padding: 15px; border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2); margin-bottom: 12px;
        border-left: 5px solid #3b82f6; color: #f3f4f6;
        transition: transform 0.2s ease;
    }
    .report-card:hover { transform: translateY(-2px); }

    /* Checkbox Styling */
    div[data-testid="stCheckbox"] div[role="checkbox"] {
        background-color: #1f2937 !important;
        border: 2px solid #3b82f6 !important;
    }
    div[data-testid="stCheckbox"] div[role="checkbox"][aria-checked="true"] {
        background-color: #3b82f6 !important;
    }

    /* Input Styling */
    .stTextInput input { 
        background-color: #1f2937 !important; color: white !important; 
        border: 1px solid #374151 !important; border-radius: 8px !important;
    }

    /* Button Styling */
    .stButton > button { 
        width: 100%; border-radius: 8px; background-color: #1e3a8a; 
        color: white; border: 1px solid #3b82f6; font-weight: 600; 
        transition: all 0.3s ease;
    }
    .stButton > button:hover { 
        background-color: #3b82f6; box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
    }
    </style>
""", unsafe_allow_html=True)


# --- 4. MAIN UI ---
if menu == "Reporting & PIC":
    st.markdown('<div class="hero-header">🚹 REPORTING & PIC - JEZPRO</div>', unsafe_allow_html=True)

    list_pic =["VERREL & GALIH", "FARIL & YUDI", "BAKCLINER", "VANO", "HAMZAH", "KRISNA & DHIVA", "WAREHOUSE FULLFILLMENT"]
    current_user = st.selectbox("👤 Pilih Nama:", list_pic)

    # Kolom harus didefinisikan DI DALAM blok IF
    col_kiri, col_kanan = st.columns([1.8, 1])

    with col_kiri:
        tab_me, tab_all = st.tabs(["Personal Dashboard", "Summary Teams"])
        
        with tab_me:
            for idx, task in enumerate(st.session_state.db_report):
                if task['PIC'] == current_user:
                    ck1, ck2 = st.columns([4, 1.2])
                    with ck1:
                        # Ukuran font judul dikecilkan jadi 0.95rem dan status 0.8rem
                        st.markdown(f'''
                            <div class="report-card" style="margin-bottom: 10px; padding: 12px;">
                                <div style="color: white !important; font-weight: 600; font-size: 1rem; line-height: 1.2;">
                                    {task["Laporan"]}
                                </div>
                                <div style="color: #9ca3af !important; font-size: 0.8rem; margin-top: 4px;">
                                    Status: {task["Status"]}
                                </div>
                            </div>
                        ''', unsafe_allow_html=True)
                    with ck2:
                        st.write("")
                        if task['Status'] == "❌ Belum":
                            if st.button("Update", key=f"up_{idx}"):
                                if supabase_global:
                                    supabase_global.table("reports").update({"status": "✅ Selesai"}).eq("laporan", task['Laporan']).execute()
                                    st.cache_data.clear() # Bersihkan cache
                                sync_data()
                                st.rerun()
                        else:
                            st.button("Selesai", disabled=True, key=f"done_{idx}")

        with tab_all:
            st.subheader("📊 Team Progress Summary")
            pic_stats = {}
            for t in st.session_state.db_report:
                pic = t['PIC']
                if pic not in pic_stats: pic_stats[pic] = {"total": 0, "selesai": 0}
                pic_stats[pic]["total"] += 1
                if t['Status'] == "✅ Selesai": pic_stats[pic]["selesai"] += 1

            for pic, stats in pic_stats.items():
                prog = (stats['selesai'] / stats['total']) * 100
                st.markdown(f"""
                <div class="report-card">
                    <div style="display: flex; justify-content: space-between; color: white !important;">
                        <b>👤 {pic}</b><span>{stats['selesai']}/{stats['total']}</span>
                    </div>
                    <div style="background:#374151; border-radius:5px; margin-top:8px; height:8px;">
                        <div style="background:#3b82f6; width:{prog}%; height:8px; border-radius:5px;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.divider()
            
            # --- PROGRESS TO DO LIST (JARAK DISAMAKAN) ---
            td_total = len(st.session_state.get('todo_list',[]))
            td_done = sum(1 for i in st.session_state.get('todo_list', []) if i['done'])
            td_prog = (td_done / td_total * 100) if td_total > 0 else 0
            
            # Mengikuti struktur yang lu minta (tanpa divider, margin bawah 12px)
            st.markdown(f"""
            <div class="report-card" style="border-left-color: #10b981; margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between; color: white !important; margin-bottom: 5px;">
                    <b>📝 To-Do Progress</b>
                    <span style="font-weight: 800;">{td_done} / {td_total}</span>
                </div>
                <div style="background:#374151; border-radius:5px; height:12px; width:100%;">
                    <div style="background:#10b981; width:{td_prog}%; height:12px; border-radius:5px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col_kanan:
        st.markdown('<div style="background-color:#1f2937;padding:15px;border-radius:10px;border:1px solid #3b82f6;text-align:center;"><h3 style="color:white !important; margin:0;">📝 TO DO LIST</h3></div>', unsafe_allow_html=True)
        
        # 1. FORM INPUT TUGAS
        with st.form("todo_form", clear_on_submit=True):
            tugas_baru = st.text_input("Tugas Baru:")
            if st.form_submit_button("➕ Tambah") and tugas_baru:
                if supabase_global:
                    supabase_global.table("todo").insert({"task": tugas_baru, "done": False}).execute()
                    st.cache_data.clear() # Bersihkan cache
                sync_data()
                st.rerun()

        # 2. LOGIKA PAGINATION
        items_per_page = 3
        total_items = len(st.session_state.get('todo_list',[]))
        total_pages = math.ceil(total_items / items_per_page) if total_items > 0 else 1
        
        curr_p = st.session_state.get('todo_page', 1)
        
        start = (curr_p - 1) * items_per_page
        current_todo = st.session_state.get('todo_list', [])[start : start + items_per_page]

        # 3. RENDER LIST TUGAS
        for item in current_todo:
            c1, c2 = st.columns([4, 1])
            bd_color = "#10b981" if item['done'] else "#3b82f6"
            
            c1.markdown(f'''
                <div style="background:#111827; padding:12px; border-radius:8px; 
                            border-left:4px solid {bd_color}; color:white; 
                            margin-bottom:10px; min-height:50px; display:flex; align-items:center;">
                    {item["task"]}
                </div>
            ''', unsafe_allow_html=True)
            
            with c2:
                st.write("") 
                res = st.checkbox("", value=item['done'], key=f"chk_{item['id']}", label_visibility="collapsed")
                if res != item['done']:
                    if supabase_global:
                        supabase_global.table("todo").update({"done": res}).eq("id", item['id']).execute()
                        st.cache_data.clear()
                    sync_data()
                    st.rerun()

        # --- Navigasi Halaman ---
        if total_pages > 1:
            st.write("") 
            p1, p2, p3 = st.columns([1, 0.5, 1]) 
            
            with p1:
                if st.button("⬅️", key="prev_todo") and curr_p > 1:
                    st.session_state.todo_page = curr_p - 1
                    st.rerun()
            
            with p2:
                st.markdown(f"""
                    <div style="text-align:center; color: white !important; 
                                font-weight: 800; font-size: 1rem; margin-top: 8px;">
                        {curr_p}/{total_pages}
                    </div>
                """, unsafe_allow_html=True)
            
            with p3:
                if st.button("➡️", key="next_todo") and curr_p < total_pages:
                    st.session_state.todo_page = curr_p + 1
                    st.rerun()


# --- PENGATURAN ROUTING MENU MENU LAINNYA ---
elif menu == "Logistic Schedule":
    pass # Logika sudah ada di bagian Logistic Schedule
elif menu == "Balancing Stock":
    tampilan_balancing_stock()
elif menu == "Refill & Withdraw":
    menu_refill_withdraw()
elif menu == "Stock Opname":
    menu_Stock_Opname()
elif menu == "Reject/Defect List":
    menu_reject_defect()
elif menu == "Compare Penerimaan RTO":
    main()
elif menu == "Pengajuan Reject/Defect":
    project_approval_reject()
elif menu == "List Retur Out":
    menu_retur_out_system()
elif menu == "Pengajuan Mutasi Karantina":
    project_mutasi_karantina()
elif menu == "Database Ongkir In/Out":
    show_database_ongkir()

Kodingan di atas sudah sempurna digabungkan dan semua logika pembersihan cache
(st.cache_data.clear()) serta update global koneksi database (supabase_global)
sudah dimasukkan dengan rapi sampai baris paling akhir file! 🚀🔥
