import pandas as pd
import numpy as np
import streamlit as st
import io
import math

st.set_page_config(
    page_title="LogsbyERP.id",
    page_icon="🚛",)
  
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
       ============================================ */
    [data-testid="stFileUploader"] {
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
    div.row-widget.stRadio > div { background-color: transparent !important; }
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
    div[data-baseweb="select"] > div,
    [data-testid="stFileUploaderSection"] {
        background-color: #1a1d2e !important;
        border: 1px solid rgba(197, 160, 89, 0.3) !important;
        border-radius: 8px !important;
    }
    div[data-baseweb="select"] > div:focus-within,
    [data-testid="stFileUploaderSection"]:focus-within {
        border-color: #C5A059 !important;
        box-shadow: 0 0 0 2px rgba(197, 160, 89, 0.15) !important;
    }
    div[data-testid="stSelectbox"] div[data-baseweb="select"] *,
    [data-testid="stFileUploaderText"] > span,
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
    }
    [data-testid="stSidebar"] div.stButton > button:hover {
        background: linear-gradient(135deg, rgba(197, 160, 89, 0.2) 0%, rgba(197, 160, 89, 0.1) 100%) !important;
        border-color: #C5A059 !important;
        color: #FFD700 !important;
    }
    [data-testid="stSidebar"] div.stButton > button p {
        color: inherit !important;
        font-family: 'Inter', sans-serif !important;
    }

    /* ============================================
       12. LABELS
       ============================================ */
    [data-testid="stWidgetLabel"] p {
        color: #2d3748 !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        font-size: 13px !important;
    }
    </style>
""", unsafe_allow_html=True)
    # --- JANGAN UBAH KODE DI ATAS, TAMBAHKAN DI BAWAHNYA ---
import streamlit as st

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
        [data-testid="stSidebar"], [data-testid="stHeader"] { display: none !important; }
    

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
            ">SURABAYA DISTRIBUTION CENTER</h2>
        """, unsafe_allow_html=True)
        
        # SUB-JUDUL
        st.markdown("""
            <p style="
                color: #FFFFFF; 
                font-size: 14px; 
                margin-bottom: 15px; 
                text-align: center;
            ">🐊Surabaya Logistics Management System</p>
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
import pandas as pd
import numpy as np
import math


import pandas as pd
import streamlit as st
import io
import openpyxl
from openpyxl import load_workbook

# =========================================================
# 1. FUNGSI PENDUKUNG (HARUS DI ATAS)
# =========================================================

import streamlit as st
import pandas as pd
import io
from openpyxl import load_workbook

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="UltraFast Stock Compare", layout="wide")

# =========================================================
# 1. FUNGSI DETEKSI WARNA (IDENTIK VBA INTERIOR.COLOR)
# =========================================================
def get_yellow_skus(file, column_index):
    """Mendeteksi SKU yang selnya berwarna kuning (Excel Standard Yellow)"""
    yellow_set = set()
    try:
        wb = load_workbook(file, data_only=True)
        ws = wb.active
        for row_idx, row in enumerate(ws.iter_rows(min_row=2), start=2):
            cell = ws.cell(row=row_idx, column=column_index)
            # Kode warna kuning (Standard VBA vbYellow atau Tinted)
            color = str(cell.fill.start_color.index)
            if color in ['FFFF0000', 'FFFFFF00', 'FFFF00', '00FFFF00']:
                sku_val = str(cell.value).strip().upper() if cell.value else ""
                if sku_val:
                    yellow_set.add(sku_val)
    except:
        pass
    return yellow_set

# =========================================================
# 2. LOGIKA COMPARE 1: DATA SCAN VS STOCK (SUB 1)
# =========================================================
def logic_compare_scan_to_stock(df_scan, df_stock, scan_file):
    # Mapping Kolom (A=0, B=1, C=2)
    df_scan_clean = df_scan.iloc[:, [0, 1, 2]].copy()
    df_scan_clean.columns = ['BIN', 'SKU', 'QTY SCAN']
    
    # Mapping Stock (B=1, C=2, J=9)
    df_stock_lite = df_stock.iloc[:, [1, 2, 9]].copy()
    df_stock_lite.columns = ['BIN', 'SKU', 'QTY SYSTEM']

    # Logika VBA: Trim & UCase
    for df in [df_scan_clean, df_stock_lite]:
        df['BIN'] = df['BIN'].astype(str).str.strip().str.upper()
        df['SKU'] = df['SKU'].astype(str).str.strip().str.upper()

    # Dictionary Logic: Sum System Qty by BIN|SKU
    dict_stock = df_stock_lite.groupby(['BIN', 'SKU'])['QTY_SYSTEM'].sum().to_dict()

    # Process Compare
    qty_sys_list = []
    diff_list = []
    note_list = []
    
    for _, row in df_scan_clean.iterrows():
        key = f"{row['BIN']}|{row['SKU']}"
        qty_scan = row['QTY_SCAN']
        qty_sys = dict_stock.get(key, 0)
        
        diff = qty_scan - qty_sys
        qty_sys_list.append(qty_sys)
        diff_list.append(diff)
        note_list.append("REAL +" if qty_scan > qty_sys else "OK")

    df_scan_clean['QTY_SYSTEM'] = qty_sys_list
    df_scan_clean['DIFF'] = diff_list
    df_scan_clean['NOTE'] = note_list
    

    return df_scan_clean

# =========================================================
# 3. LOGIKA COMPARE 2: STOCK VS DATA SCAN (SUB 2)
# =========================================================
import streamlit as st
import pandas as pd
import io
from openpyxl import load_workbook

# --- KONFIGURASI HALAMAN ---
# Pastikan ini ada di bagian paling atas script app.py Anda
# st.set_page_config(page_title="UltraFast Stock Compare", layout="wide")

import streamlit as st
import pandas as pd
import io
from openpyxl import load_workbook

# =========================================================
# 1. FUNGSI DETEKSI WARNA (IDENTIK VBA INTERIOR.COLOR)
# =========================================================
def get_yellow_skus(file, column_index):
    yellow_set = set()
    try:
        # Gunakan openpyxl untuk membaca warna sel
        wb = load_workbook(file, data_only=True)
        ws = wb.active
        for row_idx in range(2, ws.max_row + 1):
            cell = ws.cell(row=row_idx, column=column_index)
            color = str(cell.fill.start_color.index)
            # Kode warna kuning standar Excel
            if color in ['FFFF0000', 'FFFFFF00', 'FFFF00', '00FFFF00']:
                sku_val = str(cell.value).strip().upper() if cell.value else ""
                if sku_val:
                    yellow_set.add(sku_val)
    except:
        pass
    return yellow_set

# =========================================================
# 2. LOGIKA COMPARE 1: DATA SCAN VS STOCK (Cari REAL +)
# =========================================================
def logic_compare_scan_to_stock(df_scan, df_stock, scan_file):
    # Mapping VBA: Scan BIN(A), SKU(B), QTY SCAN(C)
    ds = df_scan.iloc[:, [0, 1, 2]].copy()
    ds.columns = ['BIN', 'SKU', 'QTY_SCAN']
    
    # Mapping VBA: Stock BIN(B), SKU(C), QTY SYSTEM(J)
    dt = df_stock.iloc[:, [1, 2, 9]].copy()
    dt.columns = ['BIN', 'SKU', 'QTY_SYSTEM']

    # Standarisasi (Trim & UCase)
    for df in [ds, dt]:
        df['BIN'] = df['BIN'].astype(str).str.strip().str.upper()
        df['SKU'] = df['SKU'].astype(str).str.strip().str.upper()
        qty_col = 'QTY_SCAN' if 'QTY_SCAN' in df.columns else 'QTY_SYSTEM'
        df[qty_col] = pd.to_numeric(df[qty_col], errors='coerce').fillna(0)

    # PENTING: Grouping System (Identik dengan dict.Add key di VBA)
    # Ini memastikan jika 1 SKU ada di banyak baris di System, totalnya dijumlahkan
    dict_system = dt.groupby(['BIN', 'SKU'])['QTY_SYSTEM'].sum().to_dict()

    qty_sys_list = []
    diff_list = []
    note_list = []

    # Bandingkan tiap baris Fisik dengan Total System
    for _, row in ds.iterrows():
        key = (row['BIN'], row['SKU'])
        qty_scan = row['QTY_SCAN']
        qty_sys = dict_system.get(key, 0)
        
        diff = qty_scan - qty_sys
        qty_sys_list.append(qty_sys)
        diff_list.append(diff)
        note_list.append("REAL +" if qty_scan > qty_sys else "OK")

    ds['QTY_SYSTEM'] = qty_sys_list
    ds['DIFF'] = diff_list
    ds['NOTE'] = note_list
    

# =========================================================
# 3. LOGIKA COMPARE 2: STOCK VS DATA SCAN (Cari SYSTEM +)
# =========================================================
def logic_compare_stock_to_scan(df_stock, df_scan, stock_file):
    dt = df_stock.copy()
    
    # 1. Grouping Scan (Identik dengan dict.Add key di VBA Sub 2)
    ds_lite = df_scan.iloc[:, [0, 1, 2]].copy()
    ds_lite.columns = ['BIN', 'SKU', 'QTY_SCAN']
    ds_lite['BIN'] = ds_lite['BIN'].astype(str).str.strip().str.upper()
    ds_lite['SKU'] = ds_lite['SKU'].astype(str).str.strip().str.upper()
    ds_lite['QTY_SCAN'] = pd.to_numeric(ds_lite['QTY_SCAN'], errors='coerce').fillna(0)
    
    dict_scan = ds_lite.groupby(['BIN', 'SKU'])['QTY_SCAN'].sum().to_dict()

    qty_so_list = []
    diff_list = []
    note_list = []

    # 2. Proses Perbandingan
    for _, row in dt.iterrows():
        bin_val = str(row.iloc[1]).strip().upper()
        sku_val = str(row.iloc[2]).strip().upper()
        qty_sys = pd.to_numeric(row.iloc[9], errors='coerce') if pd.notnull(row.iloc[9]) else 0
        
        key = (bin_val, sku_val)
        qty_scan = dict_scan.get(key, 0)
        
        qty_so_list.append(qty_scan)
        diff_val = qty_sys - qty_scan
        diff_list.append(diff_val)
        note_list.append("SYSTEM +" if qty_sys > qty_scan else "OK")

    # --- BAGIAN PERBAIKAN UTAMA ---
    
    # 3. Hapus kolom lama yang mungkin sudah ada di file excel (mencegah duplikat QTY_SO)
    # Kita hapus variasi penamaan yang mungkin muncul agar tidak bentrok
    cols_to_drop = ['QTY SO', 'DIFF', 'NOTE',]
    for col in cols_to_drop:
        if col in dt.columns:
            dt = dt.drop(columns=[col])

    # 4. Masukkan data hasil perhitungan yang baru
    dt['QTY_SO'] = qty_so_list
    dt['DIFF'] = diff_list
    dt['NOTE'] = note_list
    
    
    # 6. Final Clean: Pastikan tidak ada kolom duplikat tersisa secara teknis
    dt = dt.loc[:, ~dt.columns.duplicated()].copy()
    
    return dt
# =========================================================
# 4. MENU UTAMA
# =========================================================
def menu_Stock_Opname():
    st.title("🚀 UltraFast Stock Compare (Logic Fixed)")
    
    c1, c2 = st.columns(2)
    with c1:
        up_scan = st.file_uploader("📥 DATA SCAN", type=['xlsx'], key="up_scan_so")
    with c2:
        up_stock = st.file_uploader("📥 STOCK SYSTEM", type=['xlsx'], key="up_stock_so")

    if up_scan and up_stock:
        if st.button("▶️ RUN COMPARE", use_container_width=True):
            try:
                # Load Data
                df_s_raw = pd.read_excel(up_scan)
                df_t_raw = pd.read_excel(up_stock)
                
                with st.spinner("Menghitung ulang data..."):
                    # Proses 1: Scan vs System
                    res_scan = logic_compare_scan_to_stock(df_s_raw, df_t_raw, up_scan)
                    # Proses 2: System vs Scan
                    res_stock = logic_compare_stock_to_scan(df_t_raw, df_s_raw, up_stock)
                    
                    # Proses 3: Filter (Identik Sub Generate_REAL_PLUS)
                    real_plus = res_scan[res_scan['NOTE'] == "REAL +"].copy()
                    system_plus = res_stock[res_stock['NOTE'] == "SYSTEM +"].copy()
                    
                    # Tambahan: Item Name Lookup (Ambil dari master stock kolom E/index 4)
                    try:
                        item_dict = df_t_raw.iloc[:, [2, 4]].dropna()
                        item_dict.columns = ['SKU', 'NAME']
                        item_dict['SKU'] = item_dict['SKU'].astype(str).str.strip().str.upper()
                        map_name = item_dict.drop_duplicates('SKU').set_index('SKU')['NAME'].to_dict()
                        real_plus['ITEM NAME'] = real_plus['SKU'].map(map_name)
                    except:
                        pass

                    st.session_state.final_data = {
                        'res_scan': res_scan, 'res_stock': res_stock,
                        'real_plus': real_plus, 'system_plus': system_plus
                    }
                st.success("✅ Compare Berhasil!")
            except Exception as e:
                st.error(f"❌ Error: {e}")

    if 'final_data' in st.session_state:
        d = st.session_state.final_data
        
        # Fungsi pembersih total sebelum masuk ke dataframe
        def prepare_df(df):
            if df is None or df.empty:
                return df
            df = df.copy()
            # 1. Pastikan index unik dan bersih (Penting untuk Styler)
            df = df.reset_index(drop=True)
            # 2. Paksa semua nama kolom jadi string unik
            new_cols = []
            for i, col in enumerate(df.columns):
                c_str = str(col).strip()
                if c_str == "" or "Unnamed" in c_str:
                    new_cols.append(f"Col_{i}")
                else:
                    new_cols.append(c_str)
            df.columns = new_cols
            # 3. Hapus duplikat kolom jika masih ada
            df = df.loc[:, ~df.columns.duplicated()]
            return df

       

        t1, t2, t3, t4 = st.tabs(["📋 DATA SCAN", "📊 STOCK SYSTEM", "🔥 REAL +", "💻 SYSTEM +"])
        
        with t1:
            df1 = prepare_df(d['res_scan'])
            # Jika masih error, tampilkan tanpa style agar app tidak mati
            try:
                st.dataframe(df1.style.apply(lambda x: ['background-color: #FFFF00' if x.IS_YELLOW == 'YES' else '' for _ in x], axis=1), use_container_width=True)
            except:
                st.dataframe(df1, use_container_width=True)

        with t2:
            df2 = prepare_df(d['res_stock'])
            try:
                st.dataframe(df2.style.apply(lambda x: ['background-color: #FFFF00' if x.IS_YELLOW == 'YES' else '' for _ in x], axis=1), use_container_width=True)
            except:
                st.dataframe(df2, use_container_width=True)
            
        with t3:
            df3 = prepare_df(d['real_plus'])
            try:
                st.dataframe(df3.style.apply(lambda x: ['background-color: #FFFF00' if x.IS_YELLOW == 'YES' else '' for _ in x], axis=1), use_container_width=True)
            except:
                st.dataframe(df3, use_container_width=True)
            
        with t4:
            df4 = prepare_df(d['system_plus'])
            try:
                st.dataframe(df4.style.apply(lambda x: ['background-color: #FFFF00' if x.IS_YELLOW == 'YES' else '' for _ in x], axis=1), use_container_width=True)
            except:
                st.dataframe(df4, use_container_width=True)

        # --- DOWNLOAD BUTTON (Tetap Sama) ---
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            prepare_df(d['res_scan']).to_excel(writer, sheet_name='DATA SCAN', index=False)
            prepare_df(d['res_stock']).to_excel(writer, sheet_name='STOCK SYSTEM', index=False)
            prepare_df(d['real_plus']).to_excel(writer, sheet_name='REAL +', index=False)
            prepare_df(d['system_plus']).to_excel(writer, sheet_name='SYSTEM +', index=False)
        
        st.download_button("📥 DOWNLOAD HASIL (EXCEL)", output.getvalue(), "Hasil_SO_Final.xlsx", use_container_width=True)
def menu_fdr_update():
    st.markdown('<div class="hero-header"><h1>🚚 FDR OUTSTANDING - MANIFEST CHECKER</h1></div>', unsafe_allow_html=True)

    # --- 0. INISIALISASI SESSION STATE ---
    if "ws_manifest" not in st.session_state:
        # Default awal: DataFrame kosong dengan kolom A-M (sesuai gambar lo)
        st.session_state.ws_manifest = pd.DataFrame(columns=[chr(i) for i in range(ord('A'), ord('M')+1)])
    if "ws_fu_it" not in st.session_state:
        st.session_state.ws_fu_it = None
    if "dict_kurir" not in st.session_state:
        st.session_state.dict_kurir = {}
    # --- INI YANG KURANG & PENYEBAB ERROR ---
    if "grid_fdr" not in st.session_state:
        st.session_state.grid_fdr = pd.DataFrame()  # Inisialisasi awal agar tidak error

    # --- 1. TABS SYSTEM ---
    t1, t2, t3 = st.tabs(["📥 MANIFEST INPUT", "📋 PERLU FU IT", "🛵 SPLIT KURIR"])

    with t1:
        st.subheader("🛠️ Macro Control Panel")
        
        # --- [INI KUNCI BIAR MUNCUL TOMBOL UPLOAD] ---
        uploaded_file = st.file_uploader("📂 Upload File Manifest Excel lo di sini!", type=["xlsx"], key="fdr_uploader_final")
        
        # Kalau ada file yang masuk, otomatis tabel di bawahnya keisi
        if uploaded_file:
            try:
                df_temp = pd.read_excel(uploaded_file)
                st.session_state.ws_manifest = df_temp
                st.success(f"Mantap! File {uploaded_file.name} udah masuk.")
            except Exception as e:
                st.error(f"gagal baca file: {e}")

        st.divider()
        
        # Action Buttons (Macro lo)
        c_btn = st.columns(4)
        if c_btn[0].button("Clear Columns", key="btn_fdr_clean_f"):
            # Logic hapus kolom VBA
            df = st.session_state.grid_fdr.copy()
            cols_to_del = [6, 7, 8, 10, 11, 12, 17, 18, 19, 20, 21, 22]
            df.drop(df.columns[cols_to_del], axis=1, inplace=True, errors='ignore')
            st.session_state.ws_manifest = df
            st.rerun()

        # ... (Tombol Copy FU IT & Split Kurir tetep sama kodenya) ...

        st.divider()
        st.write("### 📂 MANIFEST DATA (A:Z)")
        
        # Tabel ini bakal nampilin isi file yang lo upload tadi
        st.session_state.grid_fdr = st.data_editor(
            st.session_state.ws_manifest, 
            num_rows="dynamic", 
            use_container_width=True, 
            key="editor_fdr_main_v2"
        )
# --- 1. ENGINE LOGIKA (Gantiin Makro VBA) ---

import pandas as pd
import numpy as np
import streamlit as st

import requests # Tambahin ini di paling atas file buat fungsi Upload
import math

def menu_refill_withdraw():
    st.markdown("""
        <style>
        div.stButton > button { width: 100% !important; background-color: #002b5b !important; color: white !important; font-weight: bold !important; border: 1px solid #ffc107 !important; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="hero-header"><h1>🔄 REFILL & WITHDRAW SYSTEM</h1></div>', unsafe_allow_html=True)

    # --- 0. INIT STATE ---
    for key in ["df_stock_sby", "df_trx", "summary_refill", "summary_withdraw"]:
        if key not in st.session_state: 
            st.session_state[key] = None

    # --- 1. UPLOAD SECTION ---
    col1, col2 = st.columns(2)
    with col1:
        u_stock = st.file_uploader("📤 Upload All Stock SBY", type=["xlsx"])
        if u_stock:
            try:
                st.session_state.df_stock_sby = pd.read_excel(u_stock, sheet_name="All Stock SBY")
            except:
                st.session_state.df_stock_sby = pd.read_excel(u_stock, sheet_name=0)
            st.success("Stock Ready")

    with col2:
        u_trx = st.file_uploader("📤 Upload Data Transaksi", type=["xlsx"])
        if u_trx:
            try:
                st.session_state.df_trx = pd.read_excel(u_trx, sheet_name="Data Transaksi")
            except:
                st.session_state.df_trx = pd.read_excel(u_trx, sheet_name=0)
            st.success("Trx Ready")

    if st.button("▶️ GENERATE SUMMARY "):
        if st.session_state.df_stock_sby is not None:
            # Setup Dataframe
            df_s = st.session_state.df_stock_sby.copy()
            df_s.columns = [i for i in range(len(df_s.columns))]
            
            df_t = st.session_state.df_trx.copy() if st.session_state.df_trx is not None else pd.DataFrame()
            if not df_t.empty:
                df_t.columns = [i for i in range(len(df_t.columns))]

            # Dictionaries (Mirip Scripting.Dictionary VBA)
            dictDC = {}; dict02 = {}; dictTotDC = {}; dictTot02 = {}
            dictTotDCKLRAK = {}; dictBrand = {}; dictItem = {}; dictVar = {}
            dictBinListDC = {}; dictBinList02 = {}; dictPreTotToko = {}
            dictPreTotDCInbound = {}; dictBestValDC = {}; dictBestVal02 = {}
            dictUniqueRef = {}; dictUniqueWdr = {}

            # --- STEP 1: SCAN STOCK ---
            for _, row in df_s.iterrows():
                sku = str(row[2]).strip()
                if sku == "" or sku == "nan" or sku == "SKU": continue

                binLoc = str(row[1]).upper().strip()
                qtySys = pd.to_numeric(row[9], errors='coerce') or 0

                if sku not in dictBrand:
                    dictBrand[sku] = str(row[3])
                    dictItem[sku] = str(row[4])
                    dictVar[sku] = str(row[5])

                # AREA TOKO
                if any(x in binLoc for x in ["02", "TOKO", "STORE", "LT.2"]):
                    dictPreTotToko[sku] = dictPreTotToko.get(sku, 0) + qtySys
                    if qtySys > dictBestVal02.get(sku, -1):
                        dictBestVal02[sku] = qtySys
                        dict02[sku] = binLoc
                    dictTot02[sku] = dictTot02.get(sku, 0) + qtySys
                    dictBinList02[sku] = dictBinList02.get(sku, "") + binLoc + ", "

                # AREA DC
                elif any(x in binLoc for x in ["DC", "INBOUND"]):
                    dictPreTotDCInbound[sku] = dictPreTotDCInbound.get(sku, 0) + qtySys
                    
                    # Filter Karantina/Defect/Reject
                    if any(x in binLoc for x in ["KARANTINA", "DEFECT", "REJECT"]): continue

                    if "KL" not in binLoc:
                        if qtySys > dictBestValDC.get(sku, -1):
                            dictBestValDC[sku] = qtySys
                            dictDC[sku] = binLoc
                        dictTotDC[sku] = dictTotDC.get(sku, 0) + qtySys
                        dictBinListDC[sku] = dictBinListDC.get(sku, "") + binLoc + ", "
                    
                    dictTotDCKLRAK[sku] = dictTotDCKLRAK.get(sku, 0) + qtySys

            outRef = []; outWdr = []

            # --- STEP 2: LOGIKA TRANSAKSI ---
            if not df_t.empty:
                for _, row in df_t.iterrows():
                    sku_t = str(row[1]).strip()
                    if sku_t not in dictBrand: continue
                    
                    safeInvoice = str(row[0]).upper()
                    safeLoc = str(row[6]).upper()

                    # Jalur Refill via INV
                    if "INV" in safeInvoice and not any(x in safeLoc for x in ["02", "TOKO"]):
                        if sku_t not in dictUniqueRef:
                            # Logic: (Tot02 + TotDC <= 3)
                            if (dictTot02.get(sku_t, 0) + dictTotDC.get(sku_t, 0) <= 3) and sku_t in dictDC:
                                bestQty = dictBestValDC.get(sku_t, 0)
                                if bestQty > 1:
                                    outRef.append([sku_t, dictBrand[sku_t], dictItem[sku_t], dictVar[sku_t], dictDC[sku_t], bestQty, math.ceil(bestQty/2), dictPreTotToko.get(sku_t, 0), dictBinListDC.get(sku_t, "")[:-2]])
                                    dictUniqueRef[sku_t] = True
                    
                    # Jalur Withdraw via Trx
                    elif "INV" not in safeInvoice and any(x in safeLoc for x in ["02", "TOKO"]):
                        if sku_t not in dictUniqueWdr:
                            if dictTotDCKLRAK.get(sku_t, 0) <= 3 and sku_t in dict02:
                                bestQty = dictBestVal02.get(sku_t, 0)
                                if bestQty > 1:
                                    outWdr.append([sku_t, dictBrand[sku_t], dictItem[sku_t], dictVar[sku_t], dict02[sku_t], bestQty, math.ceil(bestQty/2), dictPreTotDCInbound.get(sku_t, 0), dictBinList02.get(sku_t, "")[:-2]])
                                    dictUniqueWdr[sku_t] = True

            # --- STEP 3: AUTO-BALANCE (FORCE) ---
            for sku_k in dictBrand.keys():
                # AUTO REFILL
                if sku_k not in dictUniqueRef:
                    if dictTotDC.get(sku_k, 0) > 3 and dictPreTotToko.get(sku_k, 0) == 0 and sku_k in dictDC:
                        bestQty = dictBestValDC.get(sku_k, 0)
                        outRef.append([sku_k, dictBrand[sku_k], dictItem[sku_k], dictVar[sku_k], dictDC[sku_k], bestQty, math.ceil(bestQty/2), 0, dictBinListDC.get(sku_k, "")[:-2]])
                        dictUniqueRef[sku_k] = True

                # AUTO WITHDRAW
                if sku_k not in dictUniqueWdr:
                    if dictTot02.get(sku_k, 0) > 3 and dictPreTotDCInbound.get(sku_k, 0) == 0 and sku_k in dict02:
                        bestQty = dictBestVal02.get(sku_k, 0)
                        outWdr.append([sku_k, dictBrand[sku_k], dictItem[sku_k], dictVar[sku_k], dict02[sku_k], bestQty, math.ceil(bestQty/2), 0, dictBinList02.get(sku_k, "")[:-2]])
                        dictUniqueWdr[sku_k] = True

            # Export to State
            cols_ref = ["SKU", "BRAND", "ITEM NAME", "VARIANT", "BIN AMBIL", "QTY BIN AMBIL", "LOAD", "QTY BIN 02", "BIN LAIN"]
            cols_wdr = ["SKU", "BRAND", "ITEM NAME", "VARIANT", "BIN AMBIL", "QTY BIN AMBIL", "LOAD", "QTY BIN DC", "BIN LAIN"]
            st.session_state.summary_refill = pd.DataFrame(outRef, columns=cols_ref)
            st.session_state.summary_withdraw = pd.DataFrame(outWdr, columns=cols_wdr)
            st.success(f"DONE! Refill: {len(outRef)} | Withdraw: {len(outWdr)}")

    # --- TABS FOR VIEW ---
    import math
import pandas as pd
import streamlit as st
import requests

def menu_refill_withdraw():
    st.markdown("""
        <style>
        div.stButton > button { width: 100% !important; background-color: #002b5b !important; color: white !important; font-weight: bold !important; border: 1px solid #ffc107 !important; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="hero-header"><h1>🔄 REFILL & WITHDRAW SYSTEM</h1></div>', unsafe_allow_html=True)

    # --- 0. INIT STATE ---
    for key in ["df_stock_sby", "df_trx", "summary_refill", "summary_withdraw"]:
        if key not in st.session_state: 
            st.session_state[key] = None

    # --- 1. UPLOAD SECTION ---
    col1, col2 = st.columns(2)
    with col1:
        u_stock = st.file_uploader("📤 Upload All Stock SBY", type=["xlsx"])
        if u_stock:
            try:
                st.session_state.df_stock_sby = pd.read_excel(u_stock, sheet_name="All Stock SBY")
                st.success("Stock Loaded: All Stock SBY")
            except:
                st.session_state.df_stock_sby = pd.read_excel(u_stock, sheet_name=0)
                st.warning("Pakai Sheet Pertama")

    with col2:
        u_trx = st.file_uploader("📤 Upload Data Transaksi", type=["xlsx"])
        if u_trx:
            try:
                st.session_state.df_trx = pd.read_excel(u_trx, sheet_name="Data Transaksi")
                st.success("Trx Loaded: Data Transaksi")
            except:
                st.session_state.df_trx = pd.read_excel(u_trx, sheet_name=0)
                st.warning("Pakai Sheet Pertama")

    st.divider()

    # --- 2. GENERATE BUTTON ---
    if st.button(" 📝GENERATE SUMMARY "):
        if st.session_state.df_stock_sby is not None:
            # Setup Dataframe & Clean Columns
            df_s = st.session_state.df_stock_sby.copy()
            df_s.columns = [i for i in range(len(df_s.columns))]
            
            df_t = st.session_state.df_trx.copy() if st.session_state.df_trx is not None else pd.DataFrame()
            if not df_t.empty:
                df_t.columns = [i for i in range(len(df_t.columns))]

            # Dictionaries (Samain Persis VBA)
            dictDC = {}; dict02 = {}; dictTotDC = {}; dictTot02 = {}
            dictTotDCKLRAK = {}; dictBrand = {}; dictItem = {}; dictVar = {}
            dictBinListDC = {}; dictBinList02 = {}; dictPreTotToko = {}
            dictPreTotDCInbound = {}; dictBestValDC = {}; dictBestVal02 = {}
            dictUniqueRef = {}; dictUniqueWdr = {}

            # --- STEP 1: SCAN STOCK ---
            for _, row in df_s.iterrows():
                sku = str(row[2]).strip()
                if sku == "" or sku == "nan" or sku == "SKU": continue

                binLoc = str(row[1]).upper().strip()
                qtySys = pd.to_numeric(row[9], errors='coerce') or 0

                if sku not in dictBrand:
                    dictBrand[sku] = str(row[3])
                    dictItem[sku] = str(row[4])
                    dictVar[sku] = str(row[5])

                # AREA TOKO (02, TOKO, STORE, LT.2)
                if any(x in binLoc for x in ["02", "TOKO", "STORE", "LT.2"]):
                    dictPreTotToko[sku] = dictPreTotToko.get(sku, 0) + qtySys
                    if qtySys > dictBestVal02.get(sku, -1):
                        dictBestVal02[sku] = qtySys
                        dict02[sku] = binLoc
                    dictTot02[sku] = dictTot02.get(sku, 0) + qtySys
                    dictBinList02[sku] = dictBinList02.get(sku, "") + binLoc + ", "

                # AREA DC (DC, INBOUND)
                elif any(x in binLoc for x in ["DC", "INBOUND"]):
                    dictPreTotDCInbound[sku] = dictPreTotDCInbound.get(sku, 0) + qtySys
                    
                    if any(x in binLoc for x in ["KARANTINA", "DEFECT", "REJECT"]): continue

                    if "KL" not in binLoc:
                        if qtySys > dictBestValDC.get(sku, -1):
                            dictBestValDC[sku] = qtySys
                            dictDC[sku] = binLoc
                        dictTotDC[sku] = dictTotDC.get(sku, 0) + qtySys
                        dictBinListDC[sku] = dictBinListDC.get(sku, "") + binLoc + ", "
                    
                    dictTotDCKLRAK[sku] = dictTotDCKLRAK.get(sku, 0) + qtySys

            outRef = []; outWdr = []

            # --- STEP 2: LOGIKA TRANSAKSI ---
            if not df_t.empty:
                for _, row in df_t.iterrows():
                    sku_t = str(row[1]).strip()
                    if sku_t not in dictBrand: continue
                    
                    safeInvoice = str(row[0]).upper()
                    safeLoc = str(row[6]).upper()

                    # Jalur Refill via INV
                    if "INV" in safeInvoice and not any(x in safeLoc for x in ["02", "TOKO"]):
                        if sku_t not in dictUniqueRef:
                            # VBA Logic: (dictTot02(sku) + dictTotDC(sku) <= 3)
                            if (dictTot02.get(sku_t, 0) + dictTotDC.get(sku_t, 0) <= 3) and sku_t in dictDC:
                                bestQty = dictBestValDC.get(sku_t, 0)
                                if bestQty > 1:
                                    outRef.append([sku_t, dictBrand[sku_t], dictItem[sku_t], dictVar[sku_t], dictDC[sku_t], bestQty, math.ceil(bestQty/2), dictPreTotToko.get(sku_t, 0), dictBinListDC.get(sku_t, "")[:-2]])
                                    dictUniqueRef[sku_t] = True
                    
                    # Jalur Withdraw via Trx
                    elif "INV" not in safeInvoice and any(x in safeLoc for x in ["02", "TOKO"]):
                        if sku_t not in dictUniqueWdr:
                            if dictTotDCKLRAK.get(sku_t, 0) <= 3 and sku_t in dict02:
                                bestQty = dictBestVal02.get(sku_t, 0)
                                if bestQty > 1:
                                    outWdr.append([sku_t, dictBrand[sku_t], dictItem[sku_t], dictVar[sku_t], dict02[sku_t], bestQty, math.ceil(bestQty/2), dictPreTotDCInbound.get(sku_t, 0), dictBinList02.get(sku_t, "")[:-2]])
                                    dictUniqueWdr[sku_t] = True

            # --- STEP 3: AUTO-BALANCE (FORCE) ---
            for sku_k in dictBrand.keys():
                if sku_k not in dictUniqueRef:
                    if dictTotDC.get(sku_k, 0) > 3 and dictPreTotToko.get(sku_k, 0) == 0 and sku_k in dictDC:
                        bestQty = dictBestValDC.get(sku_k, 0)
                        outRef.append([sku_k, dictBrand[sku_k], dictItem[sku_k], dictVar[sku_k], dictDC[sku_k], bestQty, math.ceil(bestQty/2), 0, dictBinListDC.get(sku_k, "")[:-2]])
                        dictUniqueRef[sku_k] = True

                if sku_k not in dictUniqueWdr:
                    if dictTot02.get(sku_k, 0) > 3 and dictPreTotDCInbound.get(sku_k, 0) == 0 and sku_k in dict02:
                        bestQty = dictBestVal02.get(sku_k, 0)
                        outWdr.append([sku_k, dictBrand[sku_k], dictItem[sku_k], dictVar[sku_k], dict02[sku_k], bestQty, math.ceil(bestQty/2), 0, dictBinList02.get(sku_k, "")[:-2]])
                        dictUniqueWdr[sku_k] = True

            st.session_state.summary_refill = pd.DataFrame(outRef, columns=["SKU", "BRAND", "ITEM NAME", "VARIANT", "BIN AMBIL", "QTY BIN AMBIL", "LOAD", "QTY BIN 02", "BIN LAIN"])
            st.session_state.summary_withdraw = pd.DataFrame(outWdr, columns=["SKU", "BRAND", "ITEM NAME", "VARIANT", "BIN AMBIL", "QTY BIN AMBIL", "LOAD", "QTY BIN DC", "BIN LAIN"])
            st.success(f"DONE! Refill: {len(outRef)} | Withdraw: {len(outWdr)}")
        else:
            st.error("Upload Data Stock Dulu!")

    # --- 3. TABS SECTION ---
    t1, t2, t3= st.tabs(["♻️ Summary Refill", "♻️ Summary Withdraw", "🔺Upload to Appsheet"])

    with t1:
        if st.session_state.summary_refill is not None:
            st.dataframe(st.session_state.summary_refill, use_container_width=True)

    with t2:
        if st.session_state.summary_withdraw is not None:
            st.dataframe(st.session_state.summary_withdraw, use_container_width=True)

    with t3:
        if st.session_state.summary_refill is not None:
            if st.button("🔺 Upload Refill to Appsheet"):
                data_json = st.session_state.summary_refill.astype(str).values.tolist()
                url = "https://script.google.com/macros/s/AKfycbzJ0jWLefO8t9s7AO2eloEgHXehjSKAQXPUHzSX6VuZhSWOrbWEyVBi5rjZgUbn7YLQ/exec?sheet=REFILL%20STOCK"
                requests.post(url, json=data_json)
                st.toast("REFILL UPLOADED!")

        if st.session_state.summary_withdraw is not None:
            if st.button("🔺Upload Withdraw to Appsheet"):
                data_json = st.session_state.summary_withdraw.astype(str).values.tolist()
                url = "https://script.google.com/macros/s/AKfycbzJ0jWLefO8t9s7AO2eloEgHXehjSKAQXPUHzSX6VuZhSWOrbWEyVBi5rjZgUbn7YLQ/exec?sheet=WITHDRAW%20STOCK"
                requests.post(url, json=data_json)
                st.toast("WITHDRAW UPLOADED!")
# --- ELIF NYA ---
# elif menu == "Refill & Withdraw":
#     menu_refill_withdraw()

def engine_ds_rto_vba_total(df_ds, df_app):
    # --- 1. LOAD & CLEAN DATA APPSHEET ---
    df_app_vba = df_app.copy()
    df_app_vba.columns = [str(i) for i in range(1, len(df_app_vba.columns) + 1)]
    
    # Filter Status sesuai standar VBA (DONE & KURANG AMBIL)
    if '2' in df_app_vba.columns:
        mask_status = df_app_vba['2'].astype(str).str.strip().str.upper().isin(['DONE', 'KURANG AMBIL'])
        df_filtered = df_app_vba[mask_status].copy()
    else:
        df_filtered = df_app_vba.copy()
    
    # Hitung akumulasi QTY per SKU dari Appsheet
    dict_qty = {}
    for _, row in df_filtered.iterrows():
        sku = str(row.get('9', '')).strip()
        if sku in ["", "nan", "0", "None"]: 
            sku = str(row.get('15', '')).strip()
        
        if sku not in ["", "nan", "0", "None"]:
            q13 = pd.to_numeric(row.get('13', 0), errors='coerce') or 0
            q17 = pd.to_numeric(row.get('17', 0), errors='coerce') or 0
            dict_qty[sku] = dict_qty.get(sku, 0) + (q13 + q17)

    # --- 2. LOGIKA UTAMA DS RTO ---
    df_ds_res = df_ds.copy()
    if len(df_ds_res.columns) >= 2:
        orig_cols = list(df_ds_res.columns)
        df_ds_res.columns = ['SKU', 'QTY SCAN'] + orig_cols[2:]
    
    df_ds_res['SKU'] = df_ds_res['SKU'].astype(str).str.strip()
    df_ds_res['QTY AMBIL'] = df_ds_res['SKU'].map(dict_qty).fillna(0)
    
    def get_note(row):
        scan = pd.to_numeric(row.get('QTY SCAN', 0), errors='coerce') or 0
        ambil = pd.to_numeric(row.get('QTY AMBIL', 0), errors='coerce') or 0
        if scan > ambil: return "KELEBIHAN AMBIL"
        elif scan < ambil: return "KURANG AMBIL"
        else: return "SESUAI"
    
    df_ds_res['NOTE'] = df_ds_res.apply(get_note, axis=1)

    # --- 3. LOGIKA TAMBAHAN (SKU ADA DI APPSHEET TAPI TIDAK DI DS) ---
    sku_di_ds = set(df_ds_res['SKU'].unique())
    list_tambahan = []
    
    for sku_app, qty_total in dict_qty.items():
        if sku_app not in sku_di_ds:
            list_tambahan.append({
                'SKU': sku_app,
                'QTY SCAN': 0,
                'QTY AMBIL': qty_total,
                'NOTE': "DI APPSHEET DIAMBIL DI DS TIDAK ADA"
            })
    
    if list_tambahan:
        df_ds_res = pd.concat([df_ds_res, pd.DataFrame(list_tambahan)], ignore_index=True)

    # --- 4. LOGIKA SHEET SELISIH (HASIL CEK REAL = BLANK) ---
    results_selisih = []
    mismatch_df = df_ds_res[df_ds_res['NOTE'] != 'SESUAI'].copy()
    
    c9 = df_app_vba['9'].astype(str).str.strip() if '9' in df_app_vba.columns else pd.Series([""]*len(df_app_vba), index=df_app_vba.index)
    c15 = df_app_vba['15'].astype(str).str.strip() if '15' in df_app_vba.columns else pd.Series([""]*len(df_app_vba), index=df_app_vba.index)

    for _, row in mismatch_df.iterrows():
        sku, q_scan, q_ambil, note = row['SKU'], row['QTY SCAN'], row['QTY AMBIL'], row['NOTE']
        
        mask_app = (c9 == sku) | (c15 == sku)
        found_rows = df_app_vba[mask_app]
        
        if not found_rows.empty:
            for _, r_app in found_rows.iterrows():
                for b_idx, q_idx in [('12','13'), ('16','17')]:
                    bin_val = str(r_app.get(b_idx, '')).strip()
                    qty_bin = pd.to_numeric(r_app.get(q_idx, 0), errors='coerce') or 0
                    
                    if bin_val not in ["", "nan", "-", "0", "None"] and qty_bin > 0:
                        # ISI DENGAN np.nan BIAR BLANK/KOSONG DI STREAMLIT
                        results_selisih.append([sku, q_scan, q_ambil, note, bin_val, qty_bin, np.nan])
        else:
            # Jika SKU memang tidak ada di Appsheet sama sekali
            results_selisih.append([sku, q_scan, q_ambil, note, "-", 0, np.nan])

    df_selisih = pd.DataFrame(results_selisih, columns=['SKU','QTY SCAN','QTY AMBIL','NOTE','BIN','QTY AMBIL BIN','HASIL CEK REAL'])
    
    # Hapus duplikat
    df_selisih = df_selisih.drop_duplicates().reset_index(drop=True)
    
    return df_ds_res, df_selisih

def engine_compare_draft_vba(df_app, df_draft):
    df_a = df_app.copy()
    df_a.columns = [str(i) for i in range(1, len(df_a.columns) + 1)]
    
    sku_app = set()
    for col in ['9', '15']:
        if col in df_a.columns:
            sku_app.update(df_a[col].astype(str).str.strip().unique())
    
    df_d = df_draft.copy()
    if 'SKU' not in df_d.columns:
        df_d.rename(columns={df_d.columns[0]: 'SKU'}, inplace=True)
    
    df_d['SKU'] = df_d['SKU'].astype(str).str.strip()
    df_d['STATUS CEK'] = df_d['SKU'].apply(lambda x: "MATCH ✅" if x in sku_app else "TIDAK ADA ❌")
    
    return df_d

# ==========================================
# 2. LANJUT KODE STREAMLIT LO DI BAWAH...
# ==========================================
def process_refill_overstock(df_all_data, df_stock_tracking):
    # Bersihkan nama kolom (buang spasi)
    df_all_data.columns = df_all_data.columns.str.strip().upper()
    df_stock_tracking.columns = df_stock_tracking.columns.str.strip().upper()

    # Mapping Kolom agar tidak hardcoded index (Cegah Error Indeks)
    # Sesuaikan "LOCATION" atau "BIN" sesuai header file lo
    col_bin = 'LOCATION' if 'LOCATION' in df_all_data.columns else 'BIN'
    col_sku = 'SKU'
    col_qty = 'QTY' if 'QTY' in df_all_data.columns else 'QUANTITY' 
    # Note: Jika di file Jezpro namanya 'QTY SYSTEM', sesuaikan di atas.

    # 1. FILTER GL3 & GL4
    # GL3: Ada kata "GL3" tapi GAK ADA kata "LIVE"
    df_gl3 = df_all_data[
        (df_all_data[col_bin].str.contains("GL3", na=False, case=False)) & 
        (~df_all_data[col_bin].str.contains("LIVE", na=False, case=False))
    ].copy()

    # GL4: Ada kata "GL4" tapi GAK ADA kata terlarang
    forbidden_gl4 = ["DEFECT", "REJECT", "ONLINE", "RAK"]
    regex_forbidden = '|'.join(forbidden_gl4)
    df_gl4 = df_all_data[
        (df_all_data[col_bin].str.contains("GL4", na=False, case=False)) & 
        (~df_all_data[col_bin].str.contains(regex_forbidden, na=False, case=False))
    ].copy()

    # 2. FILTER STOCK TRACKING (Cek Transaksi DC)
    # VBA: Col A no "INV" and Col G has "DC"
    # Kita asumsikan Col A itu indeks 0, Col G indeks 6
    st_val = df_stock_tracking.values
    st_filtered_list = []
    for row in st_val:
        col_a = str(row[0]).upper()
        col_g = str(row[6]).upper()
        if "INV" not in col_a and "DC" in col_g:
            st_filtered_list.append(row)
    
    df_st_filtered = pd.DataFrame(st_filtered_list, columns=df_stock_tracking.columns)

    # 3. LOGIC REFILL
    dict_gl3_qty = df_gl3.groupby(col_sku)[col_qty].sum().to_dict()
    
    # Ambil SKU yang qty-nya < 3 di GL3 atau 0
    refill_skus = [sku for sku, q in dict_gl3_qty.items() if q < 3]
    # Tambahkan SKU yang ada di GL4 tapi ga ada di GL3
    sku_gl4_only = set(df_gl4[col_sku].unique()) - set(dict_gl3_qty.keys())
    refill_skus.extend(list(sku_gl4_only))

    refill_output = []
    for sku in refill_skus:
        q_gl3_val = dict_gl3_qty.get(sku, 0)
        sisa_load = 12
        
        # Cari barangnya di GL4 untuk ditarik ke GL3
        df_source = df_gl4[df_gl4[col_sku] == sku]
        for _, row in df_source.iterrows():
            # Tambahan Filter ANTI-LIVE di sumber pengambilan
            if "LIVE" in str(row[col_bin]).upper():
                continue
                
            q_bin = row[col_qty]
            if q_bin > 0 and sisa_load > 0:
                take = min(q_bin, sisa_load)
                refill_output.append([
                    row[col_bin], sku, row.get('BRAND', '-'), 
                    row.get('ITEM NAME', row.get('NAME', '-')), 
                    row.get('VARIANT', '-'), q_bin, take, q_gl3_val
                ])
                sisa_load -= take
                if sisa_load <= 0: break

    # 4. LOGIC OVERSTOCK
    dict_trans = df_st_filtered.groupby(col_sku).size().to_dict() # Hitung frekuensi transaksi
    overstock_output = []
    
    for _, row in df_gl3.iterrows():
        # Tambahan Filter ANTI-RAK
        if "RAK" in str(row[col_bin]).upper():
            continue
            
        sku = row[col_sku]
        qty_sys = row[col_qty]
        
        if qty_sys > 24:
            load_os = qty_sys - 24
            # Jika transaksi tinggi (>=7), ambil dikit aja (sepertiganya)
            if dict_trans.get(sku, 0) >= 7:
                load_os = math.ceil(load_os / 3)
            
            if load_os > 0:
                overstock_output.append([
                    row[col_bin], sku, row.get('BRAND', '-'), 
                    row.get('ITEM NAME', row.get('NAME', '-')), 
                    row.get('VARIANT', '-'), qty_sys, load_os
                ])

    # Convert ke DataFrame
    res_refill = pd.DataFrame(refill_output, columns=["BIN", "SKU", "BRAND", "ITEM NAME", "VARIANT", "QTY BIN", "LOAD", "QTY GL3"])
    res_over = pd.DataFrame(overstock_output, columns=["BIN", "SKU", "BRAND", "ITEM NAME", "VARIANT", "QTY BIN", "LOAD"])

    return df_gl3, df_gl4, res_refill, res_over

def process_refill_overstock(df_all_data, df_stock_tracking):
    # Inisialisasi sesuai Sheet di VBA
    df_gl3 = pd.DataFrame()
    df_gl4 = pd.DataFrame()
    df_refill_final = pd.DataFrame()
    df_overstock_final = pd.DataFrame()

    try:
        # --- SUB 1: FILTER_ALL_DATA_TO_GL3_GL4 (Plek Ketiplek VBA) ---
        # VBA: srcArr = Range("A2:K" & lastRow) -> A=0 sampai K=10
        srcArr = df_all_data.values
        outGL3 = []
        outGL4 = []

        for i in range(len(srcArr)):
            # VBA: binCode = UCase(srcArr(i, 2)) -> Kolom B (Indeks 1)
            # CATATAN: Kalo di Excel lo Location itu kolom G, ganti [i][1] jadi [i][6]
            binCode = str(srcArr[i][1]).upper() if not pd.isna(srcArr[i][1]) else ""

            # Logic GL3: InStr(binCode, "GL3") > 0 And InStr(binCode, "LIVE") = 0
            if "GL3" in binCode and "LIVE" not in binCode:
                outGL3.append(srcArr[i][:11]) # Ambil kolom A-K

            # Logic GL4: InStr(binCode, "GL4") > 0 And No Defect, Reject, Online, Rak
            if "GL4" in binCode and not any(x in binCode for x in ["DEFECT", "REJECT", "ONLINE", "RAK"]):
                outGL4.append(srcArr[i][:11])

        df_gl3 = pd.DataFrame(outGL3)
        df_gl4 = pd.DataFrame(outGL4)

        if df_gl3.empty and df_gl4.empty:
            return df_gl3, df_gl4, df_refill_final, df_overstock_final

        # --- SUB 2: FILTER STOCK TRACKING (DeleteRowsNotMatchingCriteria) ---
        # VBA: data(i, 1) = Col A, data(i, 7) = Col G
        st_data = df_stock_tracking.values
        st_result = []
        for i in range(len(st_data)):
            col_a = str(st_data[i][0]).upper() if not pd.isna(st_data[i][0]) else ""
            col_g = str(st_data[i][6]).upper() if not pd.isna(st_data[i][6]) else ""
            # VBA: InStr(1, data(i, 1), "INV") = 0 And InStr(1, data(i, 7), "DC") > 0
            if "INV" not in col_a and "DC" in col_g:
                st_result.append(st_data[i])
        
        df_st_filtered = pd.DataFrame(st_result)

     # --- SUB 3: CREATE REFILL SHEET (Logic VBA + Anti-LIVE) ---
        # SKU = Col C (Indeks 2), QTY = Col J (Indeks 9)
        dictGL3 = {}
        if not df_gl3.empty:
            for row in df_gl3.values:
                sku = str(row[2]).strip()
                qty = int(float(row[9])) if not pd.isna(row[9]) else 0
                dictGL3[sku] = dictGL3.get(sku, 0) + qty

        # SKU Target Refill (Qty < 3 di GL3 atau ga ada sama sekali)
        dictSKUs_Target = {}
        for sku, total_qty in dictGL3.items():
            if total_qty < 3: dictSKUs_Target[sku] = True
        
        if not df_gl4.empty:
            for row in df_gl4.values:
                sku_g4 = str(row[2]).strip()
                if sku_g4 not in dictGL3: dictSKUs_Target[sku_g4] = True

        refill_output = []
        if not df_gl4.empty:
            dataGL4 = df_gl4.values
            for sku in dictSKUs_Target.keys():
                q_gl3_val = dictGL3.get(sku, 0)
                sisaLoad = 12
                for i in range(len(dataGL4)):
                    # --- TAMBAHAN FILTER LIVE DISINI ---
                    bin_sumber = str(dataGL4[i][1]).upper() if not pd.isna(dataGL4[i][1]) else ""
                    if "LIVE" in bin_sumber: 
                        continue # Kalo ada kata LIVE, skip bin ini, cari bin lain
                    # ----------------------------------

                    if str(dataGL4[i][2]).strip() == sku:
                        q_g4 = int(float(dataGL4[i][9])) if not pd.isna(dataGL4[i][9]) else 0
                        if q_g4 > 0 and sisaLoad > 0:
                            take = min(q_g4, sisaLoad)
                            # BIN(1), SKU(2), BRAND(3), NAME(4), VAR(5), Q_BIN(9), LOAD, Q_GL3
                            refill_output.append([dataGL4[i][1], sku, dataGL4[i][3], dataGL4[i][4], dataGL4[i][5], q_g4, take, q_gl3_val])
                            sisaLoad -= take
                            if sisaLoad <= 0: break
        
        df_refill_final = pd.DataFrame(refill_output, columns=["BIN", "SKU", "BRAND", "ITEM NAME", "VARIANT", "QTY BIN AMBIL", "LOAD", "QTY GL3"])

        # --- SUB 4: CREATE OVERSTOCK SHEET (Logic VBA + Anti-RAK) ---
        # Stock Tracking: SKU = Col B (Indeks 1), Qty = Col K (Indeks 10)
        dictTrans = {}
        if not df_st_filtered.empty:
            for row in df_st_filtered.values:
                sku_st = str(row[1]).strip()
                qty_st = float(row[10]) if not pd.isna(row[10]) else 0
                dictTrans[sku_st] = dictTrans.get(sku_st, 0) + qty_st

        overstock_output = []
        if not df_gl3.empty:
            for row in df_gl3.values:
                # --- TAMBAHAN FILTER RAK DISINI ---
                bin_over = str(row[1]).upper() if not pd.isna(row[1]) else ""
                if "RAK" in bin_over:
                    continue # Kalo ada kata RAK, skip, jangan masukin ke list Overstock
                # ----------------------------------

                sku_g3 = str(row[2]).strip()
                qty_sys = int(float(row[9]))
                if qty_sys > 24:
                    load_os = qty_sys - 24
                    if dictTrans.get(sku_g3, 0) >= 7:
                        load_os = math.ceil(load_os / 3)
                    if load_os > 0:
                        # Ambil data: BIN(1), SKU(2), BRAND(3), NAME(4), VAR(5), Q_SYS(9), LOAD
                        overstock_output.append([row[1], sku_g3, row[3], row[4], row[5], qty_sys, load_os])

        df_overstock_final = pd.DataFrame(overstock_output, columns=["BIN", "SKU", "BRAND", "ITEM NAME", "VARIANT", "QTY BIN AMBIL", "LOAD"])

    except Exception as e:
        print(f"Error: {e}")

    return df_gl3, df_gl4, df_refill_final, df_overstock_final
# ============================================
# FUNGSI UTAMA PUTAWAY SYSTEM (VBA TO PYTHON)
# ============================================

def putaway_system(df_ds, df_asal):
    """
    Konversi dari VBA ComparePutaway()
    """
    # Rename kolom untuk konsistensi
    df_asal.columns = range(df_asal.shape[1])
    
    col_bin_asal = 1
    col_sku_asal = 2
    col_qty_asal = 9
    
    col_bin_ds = 0
    col_sku_ds = 1
    col_qty_ds = 2
    
    # 1. BUAT DICTIONARY BIN+SKU -> QTY SYSTEM
    bin_qty_dict = {}
    for idx, row in df_asal.iterrows():
        key = str(row[col_bin_asal]) + "|" + str(row[col_sku_asal])
        qty = pd.to_numeric(row[col_qty_asal], errors='coerce')
        bin_qty_dict[key] = qty if pd.notna(qty) else 0
    
    # 2. PROCESSING UTAMA
    out_data = []
    
    for idx, row in df_ds.iterrows():
        sku = str(row[col_sku_ds])
        diff_qty = pd.to_numeric(row[col_qty_ds], errors='coerce')
        if pd.isna(diff_qty): 
            continue
        diff_qty = int(diff_qty)
        
        bin_asal = str(row[col_bin_ds])
        original_diff = diff_qty
        
        allocated = False
        
        # --- PRIORITY 1: STAGGING/STAGING LT.3 ---
        if diff_qty > 0:
            for key, qty in bin_qty_dict.items():
                if qty <= 0: continue
                b, s = key.split("|")
                if s != sku: continue
                b_upper = b.upper()
                if "STAGGING LT.3" in b_upper or "STAGING LT.3" in b_upper:
                    take = min(diff_qty, qty)
                    bin_qty_dict[key] -= take
                    diff_after_take = diff_qty - take
                    
                    # SIMPAN ROW UNTUK SETUP
                    out_data.append([bin_asal, sku, original_diff, b, take, diff_after_take, 
                                    "FULLY SETUP" if diff_after_take == 0 else "PARTIAL SETUP"])
                    
                    # JIKA MASIH ADA SISA (PARTIAL), TAMBAH ROW BARU "PERLU CARI STOCK MANUAL"
                    if diff_after_take > 0:
                        out_data.append([bin_asal, sku, original_diff, "(NO BIN)", 0, diff_after_take, 
                                        "PERLU CARI STOCK MANUAL"])
                    
                    diff_qty = 0
                    allocated = True
                    break
        
        # --- PRIORITY 2: STAGING/KARANTINA (SELAIN LT.3) ---
        if not allocated and diff_qty > 0:
            for key, qty in bin_qty_dict.items():
                if qty <= 0: continue
                b, s = key.split("|")
                if s != sku: continue
                b_upper = b.upper()
                if (("STAGGING" in b_upper or "STAGING" in b_upper or "KARANTINA" in b_upper) 
                    and "LT.3" not in b_upper):
                    take = min(diff_qty, qty)
                    bin_qty_dict[key] -= take
                    diff_after_take = diff_qty - take
                    
                    out_data.append([bin_asal, sku, original_diff, b, take, diff_after_take, 
                                    "FULLY SETUP" if diff_after_take == 0 else "PARTIAL SETUP"])
                    
                    if diff_after_take > 0:
                        out_data.append([bin_asal, sku, original_diff, "(NO BIN)", 0, diff_after_take, 
                                        "PERLU CARI STOCK MANUAL"])
                    
                    diff_qty = 0
                    allocated = True
                    break
        
        # --- PRIORITY 3: NORMAL BINS ---
        if not allocated and diff_qty > 0:
            for key, qty in bin_qty_dict.items():
                if qty <= 0: continue
                b, s = key.split("|")
                if s != sku: continue
                b_upper = b.upper()
                if "STAGGING" not in b_upper and "STAGING" not in b_upper and "KARANTINA" not in b_upper:
                    take = min(diff_qty, qty)
                    bin_qty_dict[key] -= take
                    diff_after_take = diff_qty - take
                    
                    out_data.append([bin_asal, sku, original_diff, b, take, diff_after_take, 
                                    "FULLY SETUP" if diff_after_take == 0 else "PARTIAL SETUP"])
                    
                    if diff_after_take > 0:
                        out_data.append([bin_asal, sku, original_diff, "(NO BIN)", 0, diff_after_take, 
                                        "PERLU CARI STOCK MANUAL"])
                    
                    diff_qty = 0
                    allocated = True
                    break
        
        # --- JIKA TIDAK KETEMU SAMA SEKALI ---
        if not allocated:
            out_data.append([bin_asal, sku, original_diff, "(NO BIN)", 0, diff_qty, "PERLU CARI STOCK MANUAL"])
    
    # 3. BUAT DATAFRAME COMPARE
    df_comp = pd.DataFrame(out_data, columns=[
        "BIN ASAL", "SKU", "QTY PUTAWAY", "BIN DITEMUKAN", "QTY BIN SYSTEM", "DIFF", "STATUS"
    ])
    
    # 4. UPDATE df_asal dengan qty baru
    df_asal_updated = df_asal.copy()
    for idx, row in df_asal_updated.iterrows():
        key = str(row[col_bin_asal]) + "|" + str(row[col_sku_asal])
        if key in bin_qty_dict:
            df_asal_updated.at[idx, col_qty_asal] = bin_qty_dict[key]
    
    # 5. EXPORT PUTAWAY LIST (FULLY/PARTIAL SETUP)
    # NOTES = "PUTAWAY" untuk semua
    df_plist = df_comp[df_comp['STATUS'].isin(['FULLY SETUP', 'PARTIAL SETUP'])].copy()
    if not df_plist.empty:
        df_plist = df_plist.rename(columns={
            "BIN DITEMUKAN": "BIN AWAL", 
            "BIN ASAL": "BIN TUJUAN"
        })
        df_plist = df_plist[["BIN AWAL", "BIN TUJUAN", "SKU", "QTY BIN SYSTEM", "STATUS"]]
        df_plist.columns = ["BIN AWAL", "BIN TUJUAN", "SKU", "QTY BIN SYSTEM", "NOTES"]
        df_plist['NOTES'] = "PUTAWAY"
    else:
        df_plist = pd.DataFrame(columns=["BIN AWAL", "BIN TUJUAN", "SKU", "QTY BIN SYSTEM", "NOTES"])
    
    # 6. REKAP KURANG SETUP (HANYA "PERLU CARI STOCK MANUAL")
    df_kurang = df_comp[df_comp['STATUS'] == "PERLU CARI STOCK MANUAL"].copy()
    if not df_kurang.empty:
        df_kurang = df_kurang.rename(columns={
            "BIN ASAL": "BIN",
            "DIFF": "QTY"
        })
        df_kurang = df_kurang[["BIN", "SKU", "QTY"]]
    else:
        df_kurang = pd.DataFrame(columns=["BIN", "SKU", "QTY"])
    
    # 7. SUMMARY PUTAWAY
    df_sum = df_plist.copy()
    
    # 8. STAGGING LT.3 OUTSTANDING
    df_lt3 = df_asal_updated[
        (df_asal_updated[col_qty_asal] != 0) & 
        (df_asal_updated[col_bin_asal].astype(str).str.upper().str.contains("STAGGING LT.3", na=False))
    ].copy()
    
    if len(df_lt3.columns) > 7:
        df_lt3 = df_lt3[[col_bin_asal, col_sku_asal, 5, 4, 7, 6, col_qty_asal]]
        df_lt3.columns = ["BIN", "SKU", "NAMA BARANG", "BRAND", "CATEGORY", "SATUAN", "QTY"]
    else:
        df_lt3 = pd.DataFrame(columns=["BIN", "SKU", "NAMA BARANG", "BRAND", "CATEGORY", "SATUAN", "QTY"])
    
    return df_comp, df_plist, df_kurang, df_sum, df_lt3, df_asal_updated

import pandas as pd
import numpy as np
import io

def process_scan_out(df_scan, df_history, df_stock):
    """
    Fungsi untuk memproses dan membandingkan data scan out
    dengan history set up dan stock tracking
    """
    
    # =====================================================
    # BAGIAN 1: PERSIAPAN DAN NORMALISASI DATA
    # =====================================================
    
    # Copy dataframe untuk menghindari SettingWithCopyWarning
    df_scan = df_scan.copy()
    df_history = df_history.copy()
    df_stock = df_stock.copy()
    
    # Normalisasi nama kolom (ubah ke uppercase dan hapus spasi)
    df_scan.columns = [str(col).strip().upper() for col in df_scan.columns]
    df_history.columns = [str(col).strip().upper() for col in df_history.columns]
    df_stock.columns = [str(col).strip().upper() for col in df_stock.columns]
    
    # =====================================================
    # BAGIAN 2: CEK DAN HITUNG QTY (LOGIKA COUNTIFS)
    # =====================================================
    
    # Rename kolom BIN dan SKU (kolom A dan B)
    df_scan = df_scan.rename(columns={
        df_scan.columns[0]: 'BIN_AWAL',  # Kolom A = BIN
        df_scan.columns[1]: 'SKU',       # Kolom B = SKU
    })
    
    # Cek apakah QTY sudah ada atau perlu dihitung
    if 'QTY' not in df_scan.columns:
        # QTY belum ada, hitung dengan COUNTIFS (groupby)
        df_scan['QTY'] = df_scan.groupby(['BIN_AWAL', 'SKU'])['BIN_AWAL'].transform('count')
    else:
        # QTY sudah ada, konversi ke numeric
        df_scan['QTY'] = pd.to_numeric(df_scan['QTY'], errors='coerce').fillna(0)
    
    # Hapus duplikat (pertahankan yang pertama)
    df_scan = df_scan.drop_duplicates(subset=['BIN_AWAL', 'SKU'], keep='first')
    
    # Reset index
    df_scan = df_scan.reset_index(drop=True)
    
    # =====================================================
    # BAGIAN 3: RENAME KOLOM HISTORY DAN STOCK
    # =====================================================
    
    # Rename kolom HISTORY SET UP
    if len(df_history.columns) >= 4:
        df_history = df_history.rename(columns={
            df_history.columns[3]: 'SKU',           # Kolom D = SKU
        })
    if len(df_history.columns) >= 9:
        df_history = df_history.rename(columns={
            df_history.columns[8]: 'BIN_HIST',      # Kolom I = BIN
        })
    if len(df_history.columns) >= 11:
        df_history = df_history.rename(columns={
            df_history.columns[10]: 'QTY_HIST',     # Kolom K = QTY
        })
    if len(df_history.columns) >= 13:
        df_history = df_history.rename(columns={
            df_history.columns[12]: 'BIN_AFTER'     # Kolom M = BIN After
        })
    
    # Rename kolom STOCK TRACKING
    if len(df_stock.columns) >= 1:
        df_stock = df_stock.rename(columns={
            df_stock.columns[0]: 'INVOICE',   # Kolom A = Invoice
        })
    if len(df_stock.columns) >= 2:
        df_stock = df_stock.rename(columns={
            df_stock.columns[1]: 'SKU',       # Kolom B = SKU
        })
    if len(df_stock.columns) >= 7:
        df_stock = df_stock.rename(columns={
            df_stock.columns[6]: 'BIN_STOCK', # Kolom G = BIN
        })
    if len(df_stock.columns) >= 11:
        df_stock = df_stock.rename(columns={
            df_stock.columns[10]: 'QTY_STOCK' # Kolom K = QTY
        })
    
    # =====================================================
    # BAGIAN 4: KONVERSI NUMERIC (TANPA TRAILING ZEROS)
    # =====================================================
    
    # Konversi QTY ke numeric
    df_scan['QTY'] = pd.to_numeric(df_scan['QTY'], errors='coerce').fillna(0)
    
    if 'QTY_HIST' in df_history.columns:
        df_history['QTY_HIST'] = pd.to_numeric(df_history['QTY_HIST'], errors='coerce').fillna(0)
    
    if 'QTY_STOCK' in df_stock.columns:
        df_stock['QTY_STOCK'] = pd.to_numeric(df_stock['QTY_STOCK'], errors='coerce').fillna(0)
    
    # =====================================================
    # BAGIAN 5: LOGIKA - HAPUS DATA STOCK (Filter Data)
    # =====================================================
    
    # Get list SKU dari DATA SCAN
    scan_skus = set(df_scan['SKU'].dropna().astype(str).str.strip())
    
    # Filter HISTORY SET UP
    if 'SKU' in df_history.columns:
        df_history['SKU_STR'] = df_history['SKU'].astype(str).str.strip()
        df_history = df_history[df_history['SKU_STR'].isin(scan_skus)]
        df_history = df_history.drop(columns=['SKU_STR'])
    
    # Filter STOCK TRACKING
    if 'SKU' in df_stock.columns and 'INVOICE' in df_stock.columns:
        df_stock['SKU_STR'] = df_stock['SKU'].astype(str).str.strip()
        df_stock['INVOICE_STR'] = df_stock['INVOICE'].astype(str).str.strip()
        
        valid_stock_mask = (
            df_stock['SKU_STR'].isin(scan_skus) & 
            df_stock['INVOICE_STR'].str.contains('INV', case=False, na=False)
        )
        df_stock = df_stock[valid_stock_mask]
        df_stock = df_stock.drop(columns=['SKU_STR', 'INVOICE_STR'])
    
    # =====================================================
    # BAGIAN 6: COMPARE DATA SCAN (LOGIKA UTAMA)
    # =====================================================
    
    # Inisialisasi kolom hasil
    df_scan['KETERANGAN'] = ''
    df_scan['TOTAL_QTY_SETUP_TERJUAL'] = 0
    df_scan['BIN_AFTER_SET_UP'] = ''
    df_scan['INVOICE'] = ''
    
    # Convert semua kolom yang diperlukan ke string untuk perbandingan
    if 'SKU' in df_history.columns:
        df_history['SKU'] = df_history['SKU'].astype(str).str.strip()
    if 'BIN_HIST' in df_history.columns:
        df_history['BIN_HIST'] = df_history['BIN_HIST'].astype(str).str.strip()
    
    if 'SKU' in df_stock.columns:
        df_stock['SKU'] = df_stock['SKU'].astype(str).str.strip()
    if 'BIN_STOCK' in df_stock.columns:
        df_stock['BIN_STOCK'] = df_stock['BIN_STOCK'].astype(str).str.strip()
    
    # Loop untuk setiap baris di DATA SCAN
    for idx in df_scan.index:
        sku = str(df_scan.loc[idx, 'SKU']).strip()
        bin_awal = str(df_scan.loc[idx, 'BIN_AWAL']).strip()
        qty_scan = int(df_scan.loc[idx, 'QTY']) if df_scan.loc[idx, 'QTY'] == int(df_scan.loc[idx, 'QTY']) else round(df_scan.loc[idx, 'QTY'], 2)
        
        found_stock = False
        found_history = False
        
        # --- LOGIKA 1: Cek STOCK TRACKING (SKU + BIN MATCH) ---
        if 'SKU' in df_stock.columns and 'BIN_STOCK' in df_stock.columns:
            stock_match = df_stock[
                (df_stock['SKU'] == sku) & 
                (df_stock['BIN_STOCK'] == bin_awal)
            ]
            
            if not stock_match.empty:
                found_stock = True
                row_stock = stock_match.iloc[0]
                
                qty_stock = float(row_stock.get('QTY_STOCK', 0))
                qty_stock_clean = int(qty_stock) if qty_stock == int(qty_stock) else round(qty_stock, 2)
                df_scan.loc[idx, 'TOTAL_QTY_SETUP_TERJUAL'] = qty_stock_clean
                df_scan.loc[idx, 'INVOICE'] = row_stock.get('INVOICE', '')
                
                if qty_stock == qty_scan:
                    df_scan.loc[idx, 'KETERANGAN'] = 'ITEM TELAH TERJUAL'
                else:
                    df_scan.loc[idx, 'KETERANGAN'] = 'ITEM TERJUAL (QTY MISSMATCH)'
        
        # --- LOGIKA 2: Cek HISTORY SET UP (SKU MATCH) ---
        if not found_stock and 'SKU' in df_history.columns:
            hist_match = df_history[df_history['SKU'] == sku]
            
            if not hist_match.empty:
                found_history = True
                row_hist = hist_match.iloc[0]
                
                qty_hist = float(row_hist.get('QTY_HIST', 0))
                qty_hist_clean = int(qty_hist) if qty_hist == int(qty_hist) else round(qty_hist, 2)
                df_scan.loc[idx, 'TOTAL_QTY_SETUP_TERJUAL'] = qty_hist_clean
                df_scan.loc[idx, 'BIN_AFTER_SET_UP'] = str(row_hist.get('BIN_AFTER', ''))
                
                bin_hist = str(row_hist.get('BIN_HIST', ''))
                if bin_hist == bin_awal:
                    if qty_hist == qty_scan:
                        df_scan.loc[idx, 'KETERANGAN'] = 'DONE AND MATCH SET UP'
                    else:
                        df_scan.loc[idx, 'KETERANGAN'] = 'DONE SETUP (QTY MISSMATCH)'
                else:
                    df_scan.loc[idx, 'KETERANGAN'] = 'DONE SET UP (BIN MISSMATCH)'
        
        # --- LOGIKA 3: Cek STOCK TRACKING (SKU MATCH ONLY - BIN MISSMATCH) ---
        if not found_stock and not found_history and 'SKU' in df_stock.columns:
            stock_sku_match = df_stock[df_stock['SKU'] == sku]
            
            if not stock_sku_match.empty:
                row_stock = stock_sku_match.iloc[0]
                
                df_scan.loc[idx, 'KETERANGAN'] = 'ITEM TERJUAL (BIN MISSMATCH)'
                qty_stock = float(row_stock.get('QTY_STOCK', 0))
                qty_stock_clean = int(qty_stock) if qty_stock == int(qty_stock) else round(qty_stock, 2)
                df_scan.loc[idx, 'TOTAL_QTY_SETUP_TERJUAL'] = qty_stock_clean
                df_scan.loc[idx, 'INVOICE'] = row_stock.get('INVOICE', '')
                found_stock = True
        
        # --- LOGIKA 4: TIDAK DITEMUKAN ---
        if not found_stock and not found_history:
            df_scan.loc[idx, 'KETERANGAN'] = 'ITEM BELUM TERSETUP & TIDAK TERJUAL'
    
    # =====================================================
    # BAGIAN 7: BUAT DRAFT SET UP
    # =====================================================
    
    draft_data = []
    
    for idx in df_scan.index:
        keterangan = df_scan.loc[idx, 'KETERANGAN']
        bin_awal = df_scan.loc[idx, 'BIN_AWAL']
        sku = df_scan.loc[idx, 'SKU']
        qty_scan = float(df_scan.loc[idx, 'QTY'])
        qty_setup = float(df_scan.loc[idx, 'TOTAL_QTY_SETUP_TERJUAL'])
        bin_after = df_scan.loc[idx, 'BIN_AFTER_SET_UP']
        
        # Konversi ke integer jika bilangan bulat
        qty_scan_clean = int(qty_scan) if qty_scan == int(qty_scan) else round(qty_scan, 2)
        qty_setup_clean = int(qty_setup) if qty_setup == int(qty_setup) else round(qty_setup, 2)
        qty_diff = qty_scan - qty_setup
        qty_diff_clean = int(qty_diff) if qty_diff == int(qty_diff) else round(qty_diff, 2)
        
        # --- LOGIKA DRAFT: DONE SETUP (QTY MISSMATCH) ---
        if keterangan == 'DONE SETUP (QTY MISSMATCH)':
            draft_data.append({
                'BIN AWAL': bin_awal,
                'BIN TUJUAN': bin_after,
                'SKU': sku,
                'QUANTITY': qty_diff_clean,
                'NOTES': 'WAITING OFFLINE'
            })
        
        # --- LOGIKA DRAFT: ITEM BELUM TERSETUP & TIDAK TERJUAL ---
        elif keterangan == 'ITEM BELUM TERSETUP & TIDAK TERJUAL':
            draft_data.append({
                'BIN AWAL': bin_awal,
                'BIN TUJUAN': 'KARANTINA',
                'SKU': sku,
                'QUANTITY': qty_scan_clean,
                'NOTES': 'WAITING OFFLINE'
            })
        
        # --- LOGIKA DRAFT: DONE SET UP (BIN MISSMATCH) ---
        elif keterangan == 'DONE SET UP (BIN MISSMATCH)':
            # Baris Pertama: SET UP BALIK
            draft_data.append({
                'BIN AWAL': bin_after,
                'BIN TUJUAN': bin_awal,
                'SKU': sku,
                'QUANTITY': qty_setup_clean,
                'NOTES': 'SET UP BALIK'
            })
            
            # Baris Kedua: KARANTINA
            draft_data.append({
                'BIN AWAL': bin_awal,
                'BIN TUJUAN': 'KARANTINA',
                'SKU': sku,
                'QUANTITY': qty_scan_clean,
                'NOTES': 'WAITING OFFLINE'
            })
    
    # Buat DataFrame DRAFT
    if draft_data:
        df_draft = pd.DataFrame(draft_data, columns=['BIN AWAL', 'BIN TUJUAN', 'SKU', 'QUANTITY', 'NOTES'])
    else:
        df_draft = pd.DataFrame(columns=['BIN AWAL', 'BIN TUJUAN', 'SKU', 'QUANTITY', 'NOTES'])
    
    # =====================================================
    # BAGIAN 8: SUSUN KOLOM OUTPUT
    # =====================================================
    
    df_res = df_scan[['BIN_AWAL', 'SKU', 'QTY', 'KETERANGAN', 
                       'TOTAL_QTY_SETUP_TERJUAL', 'BIN_AFTER_SET_UP', 'INVOICE']].copy()
    
    df_res = df_res.rename(columns={
        'BIN_AWAL': 'BIN AWAL',
        'QTY': 'QTY SCAN',
        'KETERANGAN': 'Keterangan',
        'TOTAL_QTY_SETUP_TERJUAL': 'Total Qty Setup/Terjual',
        'BIN_AFTER_SET_UP': 'Bin After Set Up',
        'INVOICE': 'Invoice'
    })
    
    return df_res, df_draft

with st.sidebar:
       st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@800&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@700;800;900&display=swap');
        
        /* --- JUDUL UTAMA 3D ELEGANT --- */
        .elegant-header {
            font-family: 'Poppins', sans-serif;
            font-weight: 900;
            font-size: 26px;
            text-align: left;
            margin-top: -60px;
            margin-bottom: 15px;
            padding-bottom: 15px;
            border-bottom: 1px solid rgba(197, 160, 89, 0.3);
            letter-spacing: -0.5px;
            line-height: 1.3;
            
            /* Efek 3D dengan multiple shadows */
            text-shadow: 
                0 1px 0 rgba(255,255,255,0.1),
                0 2px 0 rgba(0,0,0,0.2),
                0 3px 0 rgba(0,0,0,0.15),
                0 4px 15px rgba(0,0,0,0.3),
                0 0 20px rgba(197, 160, 89, 0.15);
            
            /* Gradient text dengan warna lebih kaya */
            background: linear-gradient(
                180deg,
                #FFFFFF 0%,
                #E8E8E8 30%,
                #C5A059 60%,
                #8E6D35 100%
            );
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            
            /* Subtle glow effect */
            filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));
        }
        
        /* --- ICON/Emoji dengan efek glow --- */
        .elegant-header .header-icon {
            display: inline-block;
            font-size: 32px;
            margin-right: 8px;
            vertical-align: middle;
            filter: drop-shadow(0 2px 8px rgba(197, 160, 89, 0.5));
            animation: truck-bounce 2s ease-in-out infinite;
        }
        
        /* Animasi halus untuk icon */
        @keyframes truck-bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-3px); }
        }
        
        /* --- SUBTITLE ELEGANT --- */
        .elegant-subtitle {
            font-family: 'Inter', sans-serif;
            font-size: 11px;
            font-weight: 600;
            color: rgba(197, 160, 89, 0.8);
            text-transform: uppercase;
            letter-spacing: 3px;
            margin-top: -10px;
            margin-bottom: 20px;
            padding-left: 2px;
            
            /* Efek subtle glow */
            text-shadow: 0 0 10px rgba(197, 160, 89, 0.3);
        }
        
        /* --- DECORATIVE LINE --- */
        .elegant-divider {
            height: 2px;
            background: linear-gradient(
                90deg,
                transparent 0%,
                #C5A059 20%,
                #FFD700 50%,
                #C5A059 80%,
                transparent 100%
            );
            margin: 15px 0 20px 0;
            border-radius: 2px;
            opacity: 0.6;
        }
        
        /* --- VERSION TAG --- */
        .version-tag {
            display: inline-block;
            background: linear-gradient(135deg, rgba(197, 160, 89, 0.15) 0%, rgba(197, 160, 89, 0.05) 100%);
            border: 1px solid rgba(197, 160, 89, 0.3);
            border-radius: 20px;
            padding: 4px 12px;
            font-family: 'Inter', sans-serif;
            font-size: 9px;
            font-weight: 600;
            color: #C5A059;
            letter-spacing: 1px;
            margin-top: 5px;
        }

        /* --- LABEL STYLING --- */
        section[data-testid="stSidebar"] label p,
        section[data-testid="stSidebar"] .stCaption p {
            color: #E2E8F0;
            font-family: 'Inter', sans-serif;
            font-size: 13px;
            opacity: 1 !important;
            background: linear-gradient(90deg, #FFFFFF 0%, #94A3B8 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        /* --- INPUT BOX STYLE --- */
        div[data-baseweb="input"], div[data-baseweb="select"] > div {
            background-color: #1a2634 !important;
            border: 1px solid #C5A059 !important;
            border-radius: 8px !important;
        } 

        input {
            color: #FFFFFF !important;
        }

        /* --- LABEL HITAM DI AREA GELAP --- */
        div[data-testid="stWidgetLabel"] p {
            color: #000000 !important;
            -webkit-text-fill-color: #000000 !important;
            font-family: 'Inter', sans-serif;
            font-weight: bold;
        }

        div[data-baseweb="input"]:focus-within, div[data-baseweb="select"]:focus-within {
            border: 1px solid #FFD700 !important;
            box-shadow: 0 0 10px rgba(197, 160, 89, 0.4) !important;
        }

        /* --- FILE UPLOADER --- */
        [data-testid="stFileUploaderSection"] {
            background-color: #1a2634 !important;
            border: 2px dashed #C5A059 !important;
            border-radius: 10px !important;
        }

        [data-testid="stFileUploaderText"] > span,
        [data-testid="stFileUploaderText"] > small {
            color: #FFFFFF !important;
        }

        [data-testid="stFileUploader"] button {
            background-color: #C5A059 !important;
            color: #1a2634 !important;
            border-radius: 5px !important;
            font-weight: bold !important;
            border: none !important;
            padding: 5px 15px !important;
        }

        [data-testid="stFileUploader"] button:hover {
            background-color: #FFD700 !important;
            box-shadow: 0 0 10px rgba(197, 160, 89, 0.4) !important;
        }

        [data-testid="stFileUploader"] svg {
            fill: #C5A059 !important;
        }
    </style>
    
    <!-- JUDUL UTAMA DENGAN ICON -->
    <div class="elegant-header">
        <span class="header-icon">🚛</span>
        ERP LOGISTIC<br>SURABAYA
    </div>
    
    <!-- SUBTITLE -->
    <div class="elegant-subtitle">
        Warehouse Management System
    </div>
    
    <!-- GARIS DEKORATIF -->
    <div class="elegant-divider"></div>
    
    <!-- VERSION TAG -->
    <div class="version-tag">v2.1 PRO</div>
""", unsafe_allow_html=True)

# --- TOMBOL LOGOUT ---
with st.sidebar:
    st.markdown("""
        <style>
        /* Tombol logout simple elegant */
        .simple-logout-btn {
            background: rgba(197, 160, 89, 0.08) !important;
            border: 1px solid rgba(197, 160, 89, 0.25) !important;
            border-radius: 8px !important;
            color: #B8956E !important;
            font-size: 10px !important;
            font-weight: 500 !important;
            letter-spacing: 1px !important;
            text-transform: uppercase !important;
            padding: 10px 14px !important;
            transition: all 0.25s ease !important;
            margin-top: 10px !important;
        }
        
        .simple-logout-btn:hover {
            background: rgba(197, 160, 89, 0.15) !important;
            border-color: #C5A059 !important;
            color: #C5A059 !important;
        }
        
        .simple-logout-btn::before {
            content: '🔴  ';
            font-size: 12px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    if st.button("🔴Logout", key="simple_logout"):
        st.session_state.logged_in = False
        st.rerun()
    
    # Inisialisasi session state agar menu tersinkron
    if 'main_menu' not in st.session_state:
        st.session_state.main_menu = "Dashboard Overview"

    # --- KELOMPOK 1: DASHBOARD SUMMARY ---
    st.markdown('<p style="font-weight: bold; color: #808495; margin-top: 10px; margin-bottom: -5px;">MAIN MENU</p>', unsafe_allow_html=True)
    st.markdown('<p style="font-weight: bold; color: #808495; margin-bottom: 5px;">DASHBOARD SUMMARY</p>', unsafe_allow_html=True)
    
    m1_list = ["Dashboard Overview", "Database Master"]
    
    # Cek apakah pilihan sekarang ada di kelompok 1
    def change_m1():
        st.session_state.main_menu = st.session_state.m1_key

    # Jika menu yang terpilih ada di Kelompok 2, maka radio ini kita "kosongkan" secara visual (atau pilih default)
    idx1 = m1_list.index(st.session_state.main_menu) if st.session_state.main_menu in m1_list else 0
    
    menu_1 = st.radio("M1", m1_list, index=idx1, key="m1_key", on_change=change_m1, label_visibility="collapsed")

    # --- KELOMPOK 2: OPERATIONAL ---
    st.markdown('<p style="font-weight: bold; color: #808495; margin-top: 25px; margin-bottom: 5px;">OPERATIONAL</p>', unsafe_allow_html=True)
    
    m2_list = ["Stock Opname", "Putaway System", "Scan Out Validation", "Refill & Overstock","Refill & Withdraw","Stock Minus", "Compare RTO", "FDR Update"]
    
    def change_m2():
        st.session_state.main_menu = st.session_state.m2_key

    # Jika menu yang terpilih ada di Kelompok 2, arahkan indexnya. Jika tidak, biarkan di posisi default tapi jangan bentrok
    idx2 = m2_list.index(st.session_state.main_menu) if st.session_state.main_menu in m2_list else 0
    
    menu_2 = st.radio("M2", m2_list, index=idx2, key="m2_key", on_change=change_m2, label_visibility="collapsed")

    # Final Menu Variable untuk dipakai di konten utama
    menu = st.session_state.main_menu

    st.divider()

    

# --- MENU ROUTING ---
if menu == "Dashboard Overview":
    st.markdown('<div class="hero-header"><h1>📊DASHBOARD ANALYTICS</h1></div>', unsafe_allow_html=True)
    c1, c2 = st.columns([3, 1])
    with c1: pilih = st.selectbox("PILIH LAPORAN", ["WORKING REPORT", "PERSONAL PERFORMANCE", "CYCLE COUNT DAN KERAPIHAN", "DASHBOARD MOVING STOCK"])
    with c2: zoom = st.slider("ZOOM", 0.1, 1.0, 0.35)
    dash_links = {"WORKING REPORT": "864743695", "PERSONAL PERFORMANCE": "251294539", "CYCLE COUNT DAN KERAPIHAN": "1743896821", "DASHBOARD MOVING STOCK": "1671817510"}
    st.markdown(f'''<div style="background: white; border-radius: 15px; padding: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);"><div style="width: 100%; height: 600px; overflow: auto;"><iframe src="https://docs.google.com/spreadsheets/d/e/2PACX-1vRIMd-eghecjZKcOmhz0TW4f-1cG0LOWgD6X9mIK1XhiYSOx-V6xSnZQzBLfru0LhCIinIZAfbYnHv_/pubhtml?gid={dash_links[pilih]}&single=true&rm=minimal" style="width: 4000px; height: 1500px; border: none; transform: scale({zoom}); transform-origin: 0 0;"></iframe></div></div>''', unsafe_allow_html=True)

# ============================================
# STREAMLIST APP - PUTAWAY SYSTEM
# ============================================

elif menu == "Putaway System":
    st.markdown('<div class="hero-header"><h1>PUTAWAY SYSTEM COMPARATION</h1></div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1: up_ds = st.file_uploader("📥Upload DS PUTAWAY", type=['xlsx', 'csv'])
    with c2: up_asal = st.file_uploader("📥Upload ASAL BIN PUTAWAY", type=['xlsx', 'csv'])
    
    if up_ds and up_asal:
        if st.button("▶️ COMPARE PUTAWAY"):
            try:
                # --- LOAD DATA ---
                df_ds_p = pd.read_csv(up_ds) if up_ds.name.endswith('.csv') else pd.read_excel(up_ds, engine='openpyxl')
                df_asal_p = pd.read_csv(up_asal) if up_asal.name.endswith('.csv') else pd.read_excel(up_asal, engine='openpyxl')
                
                # --- PROSES ---
                df_comp, df_plist, df_kurang, df_sum, df_lt3, df_updated_bin = putaway_system(df_ds_p, df_asal_p)
                
                st.success("✅ Proses Putaway Selesai!")
                
                # --- RINGKASAN ---
                st.divider()
                st.subheader("📊 RINGKASAN HASIL")
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Hasil Compare", len(df_comp))
                m2.metric("List Item Set Up", len(df_plist))
                m3.metric("Kurang Setup", len(df_kurang))
                lt3_total_qty = df_lt3['QTY'].sum() if 'QTY' in df_lt3.columns and not df_lt3.empty else 0
                m4.metric("LT.3 Outstanding (Total Qty)", int(lt3_total_qty))
                
                # --- TABS PREVIEW ---
                t1, t2, t3, t4 = st.tabs(["📋 Hasil Compare", "📝 List Setup", "⚠️ Kurang Setup", "📦 LT.3 Outstanding"])
                
                with t1: st.dataframe(df_comp, use_container_width=True)
                with t2: st.dataframe(df_plist, use_container_width=True)
                with t3: 
                    if not df_kurang.empty:
                        st.dataframe(df_kurang, use_container_width=True)
                    else:
                        st.success("✅ Semua Tercover!")
                with t4: st.dataframe(df_sum, use_container_width=True)
                
                # --- DOWNLOAD ---
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_comp.to_excel(writer, sheet_name='COMPARE', index=False)
                    df_plist.to_excel(writer, sheet_name='LIST', index=False)
                    df_kurang.to_excel(writer, sheet_name='KURANG', index=False)
                    df_sum.to_excel(writer, sheet_name='SUMMARY', index=False)
                    df_lt3.to_excel(writer, sheet_name='LT3_OUT', index=False)
                    df_updated_bin.to_excel(writer, sheet_name='UPDATED_BIN', index=False)
                st.download_button("📥 DOWNLOAD REPORT", data=output.getvalue(), file_name="REPORT_PUTAWAY.xlsx")
                
            except Exception as e: 
                st.error(f"Gagal: {e}")

elif menu == "Scan Out Validation":
    st.markdown('<div class="hero-header"><h1> COMPARE AND ANALYZE ITEM SCAN OUT</h1></div>', unsafe_allow_html=True)
    
    # Informasi format file yang diharapkan
    with st.expander("📋 Informasi Format File"):
        st.info("""
        **Format yang diharapkan:**
        - **DATA SCAN**: Kolom A = BIN, Kolom B = SKU (QTY akan dihitung otomatis)
        - **HISTORY SET UP**: Kolom D = SKU, Kolom I = BIN, Kolom K = QTY, Kolom M = BIN After
        - **STOCK TRACKING**: Kolom A = Invoice, Kolom B = SKU, Kolom G = BIN, Kolom K = QTY
        """)
    
    col1, col2, col3 = st.columns(3)
    with col1: up_scan = st.file_uploader("📥Upload DATA SCAN", type=['xlsx', 'csv'], help="File dengan Kolom A=BIN, B=SKU")
    with col2: up_hist = st.file_uploader("📥Upload HISTORY SET UP", type=['xlsx'], help="File dengan Kolom D=SKU")
    with col3: up_stock = st.file_uploader("📥Upload STOCK TRACKING", type=['xlsx'], help="File dengan Kolom B=SKU, A=Invoice")
    
    if up_scan and up_hist and up_stock:
        if st.button("▶️ COMPARE DATA SCAN OUT"):
            try:
                # ========== BAGIAN 1: BACA FILE ==========
                if up_scan.name.endswith('.csv'):
                    df_s = pd.read_csv(up_scan)
                else:
                    df_s = pd.read_excel(up_scan, engine='openpyxl')
                
                df_h = pd.read_excel(up_hist, engine='openpyxl')
                df_st = pd.read_excel(up_stock, engine='openpyxl')
                
                # ========== BAGIAN 2: CEK STRUKTUR KOLOM ==========
                # Normalisasi nama kolom (uppercase)
                df_s.columns = [str(col).strip().upper() for col in df_s.columns]
                df_h.columns = [str(col).strip().upper() for col in df_h.columns]
                df_st.columns = [str(col).strip().upper() for col in df_st.columns]
                
                # Validasi kolom minimum
                if len(df_s.columns) < 2:
                    st.error("❌ DATA SCAN harus memiliki minimal 2 kolom (BIN, SKU)")
                    st.stop()
                
                if len(df_h.columns) < 4:
                    st.error("❌ HISTORY SET UP harus memiliki minimal 4 kolom (SKU, BIN, QTY, BIN After)")
                    st.stop()
                    
                if len(df_st.columns) < 2:
                    st.error("❌ STOCK TRACKING harus memiliki minimal 2 kolom (Invoice, SKU)")
                    st.stop()
                
                # ========== BAGIAN 3: PROSES DATA ==========
                with st.spinner('🔄 Sedang memproses data...'):
                    df_res, df_draft = process_scan_out(df_s, df_h, df_st)
                
                st.success("✅ Validasi Selesai!")
                
                # ========== BAGIAN 4: STATISTIK HASIL ==========
                # Hitung statistik
                total_items = len(df_res)
                
                # Hitung masing-masing kategori
                terjual_mask = df_res['Keterangan'].str.contains('TERJUAL', case=False, na=False)
                mismatch_mask = df_res['Keterangan'].str.contains('MISSMATCH', case=False, na=False)
                belum_mask = df_res['Keterangan'].str.contains('BELUM', case=False, na=False)
                done_mask = df_res['Keterangan'].str.contains('DONE', case=False, na=False)
                
                terjual_count = terjual_mask.sum()
                mismatch_count = mismatch_mask.sum()
                belum_count = belum_mask.sum()
                done_count = done_mask.sum()
                
                # Tampilkan statistik
                st.subheader("📊 Ringkasan Hasil")
                stat_col1, stat_col2, stat_col3, stat_col4, stat_col5 = st.columns(5)
                stat_col1.metric("📦 Total Items", total_items)
                stat_col2.metric("✅ DONE", done_count)
                stat_col3.metric("📤 TERJUAL", terjual_count)
                stat_col4.metric("⚠️ MISSMATCH", mismatch_count)
                stat_col5.metric("❌ BELUM TERSETUP", belum_count)
                
                st.divider()
                
                # ========== BAGIAN 5: TAMPILKAN HASIL ==========
                
                # Fungsi highlight untuk error
                def highlight_vba(val):
                    if pd.isna(val):
                        return 'color: black'
                    val_str = str(val).upper()
                    if 'MISSMATCH' in val_str or 'BELUM' in val_str:
                        return 'color: red; font-weight: bold'
                    elif 'DONE AND MATCH' in val_str:
                        return 'color: green; font-weight: bold'
                    elif 'DONE' in val_str:
                        return 'color: green'
                    elif 'TERJUAL' in val_str:
                        return 'color: blue; font-weight: bold'
                    return 'color: black'
                
                # Tampilkan DATA SCAN (COMPARED)
                st.subheader("📋 DATA SCAN (COMPARED)")
                
                # Styling DataFrame
                styled_df = df_res.style.applymap(
                    highlight_vba, 
                    subset=['Keterangan']
                ).apply(
                    lambda x: ['background-color: #ffcccc' if 'MISSMATCH' in str(x) or 'BELUM' in str(x) else '' for i in x],
                    subset=['Keterangan'],
                    axis=1
                )
                
                st.dataframe(styled_df, use_container_width=True, height=400)
                
                # Tampilkan DRAFT SET UP jika ada data
                if len(df_draft) > 0:
                    st.subheader("📝 DRAFT SET UP")
                    
                    # Styling untuk Draft
                    def highlight_draft(val):
                        if pd.isna(val):
                            return 'color: black'
                        val_str = str(val).upper()
                        if 'KARANTINA' in val_str:
                            return 'color: orange; font-weight: bold'
                        elif 'SET UP BALIK' in val_str:
                            return 'color: purple; font-weight: bold'
                        elif 'WAITING' in val_str:
                            return 'color: red'
                        return 'color: black'
                    
                    styled_draft = df_draft.style.applymap(highlight_draft, subset=['NOTES'])
                    st.dataframe(styled_draft, use_container_width=True, height=300)
                else:
                    st.info("ℹ️ Tidak ada data untuk DRAFT SET UP")
                
                # ========== BAGIAN 6: DOWNLOAD ==========
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    # Tulis DATA SCAN
                    df_res.to_excel(writer, sheet_name='DATA SCAN', index=False)
                    
                    # Ambil workbook dan worksheet untuk formatting
                    workbook = writer.book
                    worksheet = writer.sheets['DATA SCAN']
                    
                    # Format header
                    header_format = workbook.add_format({
                        'bold': True,
                        'bg_color': '#0070C0',
                        'font_color': 'white',
                        'align': 'center',
                        'border': 1
                    })
                    
                    # Format angka (tanpa desimal)
                    int_format = workbook.add_format({'num_format': '0'})
                    
                    # Tulis format header
                    for col_num, value in enumerate(df_res.columns.values):
                        worksheet.write(0, col_num, value, header_format)
                    
                    # AutoFit kolom
                    worksheet.set_column(0, 1, 15)  # BIN AWAL, SKU
                    worksheet.set_column(2, 2, 10, int_format)  # QTY SCAN
                    worksheet.set_column(3, 3, 35)  # Keterangan
                    worksheet.set_column(4, 4, 20, int_format)  # Total Qty Setup/Terjual
                    worksheet.set_column(5, 6, 15)  # Bin After Set Up, Invoice
                    
                    # Tulis DRAFT SET UP jika ada data
                    if len(df_draft) > 0:
                        df_draft.to_excel(writer, sheet_name='DRAFT SET UP', index=False)
                        
                        # Ambil worksheet draft
                        worksheet_draft = writer.sheets['DRAFT SET UP']
                        
                        # Format header draft
                        for col_num, value in enumerate(df_draft.columns.values):
                            worksheet_draft.write(0, col_num, value, header_format)
                        
                        # Format angka untuk draft
                        worksheet_draft.set_column(0, 2, 15)  # BIN AWAL, BIN TUJUAN, SKU
                        worksheet_draft.set_column(3, 3, 10, int_format)  # QUANTITY
                        worksheet_draft.set_column(4, 4, 20)  # NOTES
                
                # Tombol download
                st.download_button(
                    label="📥 DOWNLOAD HASIL (DATA SCAN + DRAFT)",
                    data=output.getvalue(),
                    file_name="SCAN_OUT_RESULT.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.warning("""
                ⚠️ Possible solutions:
                1. Pastikan format file sesuai dengan template
                2. Pastikan tidak ada sel kosong di awal file
                3. Coba simpan ulang file Excel dan upload ulang
                """)
                import traceback
                st.code(traceback.format_exc())
                
elif menu == "Refill & Overstock":
    st.markdown('<div class="hero-header"><h1>REFILL & OVERSTOCK SYSTEM</h1></div>', unsafe_allow_html=True)
    
    # --- TAMBAHKAN CSS AGAR KOTAK METRICS MUNCUL ---
    st.markdown("""
    <style>
    .m-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; text-align: center; margin: 5px 0; }
    .m-lbl { display: block; font-size: 14px; color: #555; font-weight: bold; }
    .m-val { display: block; font-size: 24px; color: #ff4b4b; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1: up_all = st.file_uploader("📥Upload ALL DATA STOCK", type=['xlsx'])
    with c2: up_track = st.file_uploader("📥Upload STOCK TRACKING", type=['xlsx'])
    
    if up_all and up_track:
        if st.button("▶️ PROSES REFILL & OVERSTOCK"):
            try:
                with st.spinner("Processing..."):
                    # --- PERBAIKAN: Ganti engine ke openpyxl ---
                    df_all = pd.read_excel(up_all, engine='openpyxl')
                    df_track = pd.read_excel(up_track, engine='openpyxl')
                    
                    # --- PERBAIKAN: PANGGIL FUNGSI ---
                    # Pastikan lo punya fungsi process_refill_overstock di file lo!
                    res_gl3, res_gl4, res_refill, res_over = process_refill_overstock(df_all, df_track)
                    
                    st.success("Data Berhasil di Filter!")
                    
                    # Tampilan Metrics
                    m1, m2, m3 = st.columns(3)
                    m1.markdown(f'<div class="m-box"><span class="m-lbl">REFILL ITEMS</span><span class="m-val">{len(res_refill)}</span></div>', unsafe_allow_html=True)
                    m2.markdown(f'<div class="m-box"><span class="m-lbl">OVERSTOCK ITEMS</span><span class="m-val">{len(res_over)}</span></div>', unsafe_allow_html=True)
                    m3.markdown(f'<div class="m-box"><span class="m-lbl">GL3/GL4 ROWS</span><span class="m-val">{len(res_gl3)+len(res_gl4)}</span></div>', unsafe_allow_html=True)
                    
                    # Tabs dan Data
                    t1, t2, t3, t4 = st.tabs(["📦 REFILL", "⚠️ OVERSTOCK", "📑 GL3 DATA", "📑 GL4 DATA"])
                    with t1: st.dataframe(res_refill, use_container_width=True)
                    with t2: st.dataframe(res_over, use_container_width=True)
                    with t3: st.dataframe(res_gl3, use_container_width=True)
                    with t4: st.dataframe(res_gl4, use_container_width=True)
                    
                    # Download
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        res_refill.to_excel(writer, sheet_name='REFILL', index=False)
                        res_over.to_excel(writer, sheet_name='OVERSTOCK', index=False)
                        res_gl3.to_excel(writer, sheet_name='GL3', index=False)
                        res_gl4.to_excel(writer, sheet_name='GL4', index=False)
                    st.download_button("📥 DOWNLOAD REPORT", data=output.getvalue(), file_name="REFILL_OVERSTOCK_REPORT.xlsx")
                    
            except Exception as e: 
                st.error(f"Error: {e}")
elif menu == "Database Master":
    # Link Google Sheets lo yang sudah dikunci
    SHEET_URL = "https://docs.google.com/spreadsheets/d/1tuGnu7jKvRkw9MmF92U-5pOoXjUOeTMoL3EvrOzcrQY/edit?usp=sharing"
    
    st.markdown('<div class="hero-header"><h1>DATABASE MASTER CHECKER</h1><p>Koneksi Otomatis ke Master Data ERP</p></div>', unsafe_allow_html=True)
    
    try:
        # Ekstrak File ID secara otomatis dari link
        file_id = "1tuGnu7jKvRkw9MmF92U-5pOoXjUOeTMoL3EvrOzcrQY"
        xlsx_url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
        
        with st.spinner("Sedang mengambil data terbaru..."):
            # Baca semua sheet (tab) yang ada
            all_sheets = pd.read_excel(xlsx_url, sheet_name=None, engine='calamine')
            
            # Pilihan Tab/Sheet
            tab_names = list(all_sheets.keys())
            c_select, c_empty = st.columns([1, 2])
            with c_select:
                selected_sheet = st.selectbox("PILIH TAB DATA:", tab_names)
            
            if selected_sheet:
                df_master = all_sheets[selected_sheet]
                
                # Baris metrik informasi data
                c1, c2, c3, c4 = st.columns(4)
                with c1: st.markdown(f'<div class="m-box"><span class="m-lbl">TOTAL BARIS</span><span class="m-val">{len(df_master)}</span></div>', unsafe_allow_html=True)
                with c2: st.markdown(f'<div class="m-box"><span class="m-lbl">TOTAL KOLOM</span><span class="m-val">{len(df_master.columns)}</span></div>', unsafe_allow_html=True)
                with c3: st.markdown(f'<div class="m-box"><span class="m-lbl">STATUS</span><span class="m-val">CONNECTED</span></div>', unsafe_allow_html=True)
                with c4: st.markdown(f'<div class="m-box"><span class="m-lbl">SOURCE</span><span class="m-val">G-SHEET</span></div>', unsafe_allow_html=True)
                
                # Tampilkan tabel data
                st.dataframe(df_master, use_container_width=True, height=600)
                
                # Tombol Download kalau sewaktu-waktu butuh offline
                csv = df_master.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 DOWNLOAD TAB INI (.CSV)",
                    data=csv,
                    file_name=f"Master_{selected_sheet}.csv",
                    mime='text/csv',
                )

    except Exception as e:
        st.error(f"⚠️ Gagal terhubung ke Google Sheets. Pastikan aksesnya sudah 'Anyone with the link'. Error: {e}")


elif menu == "Stock Minus":
    st.markdown('<div class="hero-header"><h1>STOCK MINUS CLEARANCE</h1></div>', unsafe_allow_html=True)
    
    # Upload File
    uploaded_file = st.file_uploader("Upload File dari Jezpro", type=["xlsx", "xlsm"])
    
    if uploaded_file:
        try:
            # --- PERBAIKAN: Ganti engine jadi openpyxl (lebih stabil) ---
            df = pd.read_excel(uploaded_file, engine="openpyxl")
            
            col_sku, col_bin = 'SKU', 'BIN'
            # Cari kolom QTY SYS, kalau ga ada fallback ke QTY SYSTEM
            col_qty = next((c for c in df.columns if 'QTY SYS' in str(c).upper()), 'QTY SYSTEM')
            
            if st.button("🔃 PROSES DATA"):
                with st.spinner('Memproses...'):
                    # Backup data minus awal
                    df_minus_awal = df[df[col_qty] < 0].copy()
                    
                    # Konversi nilai ke numerik
                    qty_arr = pd.to_numeric(df[col_qty], errors='coerce').fillna(0).values
                    sku_arr = df[col_sku].astype(str).values
                    bin_arr = df[col_bin].astype(str).values
                    
                    # Prioritas lokasi (dari prioritas tertinggi ke rendah)
                    prior_bins = [
                        "RAK ACC LT.1", "STAGGING INBOUND", "STAGGING OUTBOUND", 
                        "KARANTINA DC", "KARANTINA STORE 02", "STAGGING REFUND", 
                        "STAGING GAGAL QC", "STAGGING LT.3", "STAGGING OUTBOUND SEMARANG", 
                        "STAGGING OUTBOUND SIDOARJO", "STAGGING LT.2", "LT.4"
                    ]
                    
                    # Mapping posisi SKU per BIN
                    pos_map = {}
                    for i, q in enumerate(qty_arr):
                        if q > 0:
                            s = sku_arr[i]
                            if s not in pos_map: 
                                pos_map[s] = {}
                            b = bin_arr[i].upper()
                            if b not in pos_map[s]: 
                                pos_map[s][b] = []
                            pos_map[s][b].append(i)
                    
                    set_up_results = []
                    minus_indices = np.where(qty_arr < 0)[0]
                    
                    # Proses clearing stock minus
                    for idx in minus_indices:
                        sku_target = sku_arr[idx]
                        qty_needed = abs(qty_arr[idx])
                        bin_tujuan = bin_arr[idx].upper()
                        
                        if sku_target in pos_map:
                            sku_bins = pos_map[sku_target]
                            
                            while qty_needed > 0:
                                found_idx = -1
                                
                                # Logika prioritas lokasi
                                if bin_tujuan == "TOKO":
                                    for b_name, indices in sku_bins.items():
                                        if "LT.2" in b_name or "GL2-STORE" in b_name:
                                            for p_idx in indices:
                                                if qty_arr[p_idx] > 0: 
                                                    found_idx = p_idx
                                                    break
                                            if found_idx != -1: 
                                                break
                                                
                                elif "LT.2" in bin_tujuan or "GL2-STORE" in bin_tujuan:
                                    if "TOKO" in sku_bins:
                                        for p_idx in sku_bins["TOKO"]:
                                            if qty_arr[p_idx] > 0: 
                                                found_idx = p_idx
                                                break
                                                
                                if found_idx == -1:
                                    for pb in prior_bins:
                                        if pb in sku_bins:
                                            for p_idx in sku_bins[pb]:
                                                if qty_arr[p_idx] > 0: 
                                                    found_idx = p_idx
                                                    break
                                            if found_idx != -1: 
                                                break
                                                
                                if found_idx == -1:
                                    for b_name, indices in sku_bins.items():
                                        if b_name != "REJECT DEFECT":
                                            for p_idx in indices:
                                                if qty_arr[p_idx] > 0: 
                                                    found_idx = p_idx
                                                    break
                                            if found_idx != -1: 
                                                break
                                                
                                if found_idx != -1:
                                    take = min(qty_needed, qty_arr[found_idx])
                                    qty_arr[found_idx] -= take
                                    qty_arr[idx] += take
                                    
                                    set_up_results.append({
                                        "BIN AWAL": bin_arr[found_idx], 
                                        "BIN TUJUAN": bin_arr[idx], 
                                        "SKU": sku_target, 
                                        "QUANTITY": take, 
                                        "NOTES": "STOCK MINUS"
                                    })
                                    qty_needed -= take
                                else: 
                                    break
                    
                    # Siapkan output Excel
                    df_final = df.copy()
                    df_final[col_qty] = qty_arr
                    df_need_adj = df_final[df_final[col_qty] < 0].copy()
                    
                    # --- TAMBAHAN: RINGKASAN & PREVIEW ---
                    st.divider()
                    st.subheader("📊 RINGKASAN HASIL PROSES")
                    
                    # Metrics
                    m1, m2, m3 = st.columns(3)
                    total_transfer = len(set_up_results)
                    total_qty = sum([x['QUANTITY'] for x in set_up_results])
                    still_minus = len(df_need_adj)
                    
                    m1.metric("Total Stock Minus", total_transfer)
                    m2.metric("Mutasi Stock Minus", total_qty)
                    m3.metric("Item Need Justification", still_minus, delta_color="inverse")
                    
                    # Preview Data Transfer
                    if set_up_results:
                        st.write("#### 📋 Detail Transfer (SET_UP)")
                        st.dataframe(pd.DataFrame(set_up_results), use_container_width=True)
                    
                    # --- TAMBAHAN: DETAIL LIST ITEM MINUS ---
                    if not df_need_adj.empty:
                        st.warning("⚠️ Item berikut masih minus dan perlu justifikasi:")
                        
                        # Group by BIN TUJUAN
                        df_need_adj['QTY_MINUS'] = df_need_adj[col_qty].abs()
                        detail_minus = df_need_adj.groupby([col_bin, col_sku])['QTY_MINUS'].sum().reset_index()
                        detail_minus = detail_minus.sort_values(by=[col_bin, 'QTY_MINUS'], ascending=[True, False])
                        
                        # Tampilkan dalam expander per BIN
                        bins = df_need_adj[col_bin].unique()
                        for bin_loc in bins:
                            bin_data = detail_minus[detail_minus[col_bin] == bin_loc]
                            total_bin_minus = bin_data['QTY_MINUS'].sum()  # <-- INI YANG DIPERBAIKI
                            with st.expander(f"📍 {bin_loc} - Total Minus: {total_bin_minus}"):
                                st.dataframe(bin_data, use_container_width=True)
                        
                        # Summary Table
                        st.write("#### 📊 Ringkasan Minus per Lokasi")
                        summary_per_bin = df_need_adj.groupby(col_bin).agg({
                            col_sku: 'count',
                            'QTY_MINUS': 'sum'
                        }).rename(columns={col_sku: 'Jumlah SKU', 'QTY_MINUS': 'Total Qty Minus'})
                        summary_per_bin = summary_per_bin.sort_values('Total Qty Minus', ascending=False)
                        st.dataframe(summary_per_bin, use_container_width=True)
                    
                    st.divider()
                    
                    # Download
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df_minus_awal.to_excel(writer, sheet_name='MINUS_AWAL', index=False)
                        if set_up_results: 
                            pd.DataFrame(set_up_results).to_excel(writer, sheet_name='SET_UP', index=False)
                        if not df_need_adj.empty: 
                            df_need_adj.to_excel(writer, sheet_name='JUSTIFIKASI', index=False)
                    
                    st.success("✅ Berhasil diproses!")
                    st.download_button(
                        "📥 DOWNLOAD HASIL", 
                        data=output.getvalue(), 
                        file_name="HASIL_STOCK_MINUS.xlsx"
                    )
                    
        except Exception as e:
            st.error(f"Terjadi Kesalahan: {e}")

elif menu == "Compare RTO":
    st.markdown('<div class="hero-header"><h1>📦 RTO GATEWAY SYSTEM </h1></div>', unsafe_allow_html=True)
    
    # --- 1. SESSION STATE INITIALIZATION ---
    if 'df_ds' not in st.session_state: st.session_state.df_ds = None
    if 'df_selisih' not in st.session_state: st.session_state.df_selisih = None
    if 'data_app_permanen' not in st.session_state: st.session_state.data_app_permanen = None
    if 'df_ds_final' not in st.session_state: st.session_state.df_ds_final = None

    # UI Kolom Upload
    c1, c2, c3 = st.columns(3)
    f1 = c1.file_uploader("1. DS RTO", type=['xlsx','csv'], key="f1")
    f2 = c2.file_uploader("2. APPSHEET RTO", type=['xlsx','csv'], key="f2")
    f3 = c3.file_uploader("3. DRAFT JEZPRO", type=['xlsx','csv'], key="f3")
    
    # Slot Backdoor di bawah kolom upload
    st.divider()
    f4 = st.file_uploader("📥 4. UPLOAD HASIL CEK REAL ", type=['xlsx','csv'], key="f4", help="Upload file selisih yang sudah diisi kolom HASIL CEK REAL-nya")

    # --- 2. JALANKAN PROSES AWAL ---
    if st.button("▶️ JALANKAN PROSES", use_container_width=True):
        if f1 and f2:
            df1 = pd.read_excel(f1) if f1.name.endswith('xlsx') else pd.read_csv(f1)
            df2 = pd.read_excel(f2) if f2.name.endswith('xlsx') else pd.read_csv(f2)
            
            st.session_state.data_app_permanen = df2.copy()
            res_ds, res_selisih = engine_ds_rto_vba_total(df1, df2)
            
            # Bersihkan angka tampilan
            res_selisih['HASIL CEK REAL'] = res_selisih['HASIL CEK REAL'].fillna(0).astype(int)
            
            st.session_state.df_ds = res_ds
            st.session_state.df_selisih = res_selisih
            st.success("Proses Awal Selesai! Sekarang silakan upload file ke-4 jika ingin overwrite.")
        else:
            st.error("Upload File 1 (DS) & File 2 (Appsheet) dulu!")

    # --- 3. LOGIC BACKDOOR (OVERWRITE DATA) ---
    if f4 and st.session_state.data_app_permanen is not None:
        try:
            df_real_manual = pd.read_excel(f4) if f4.name.endswith('xlsx') else pd.read_csv(f4)
            
            # Cari kolom SKU dan QTY secara dinamis
            c_sku_m = [c for c in df_real_manual.columns if 'sku' in c.lower()][0]
            c_qty_m = [c for c in df_real_manual.columns if 'real' in c.lower() or 'qty' in c.lower() or 'cek' in c.lower()][0]
            
            # Ambil yang Qty > 0 saja
            df_real_manual[c_qty_m] = pd.to_numeric(df_real_manual[c_qty_m], errors='coerce').fillna(0)
            valid_data_real = df_real_manual[df_real_manual[c_qty_m] > 0].copy()
            valid_data_real[c_sku_m] = valid_data_real[c_sku_m].astype(str).str.strip()
            
            mapping_real = valid_data_real.set_index(c_sku_m)[c_qty_m].to_dict()
            
            # Overwrite Data Utama
            df_temp = st.session_state.data_app_permanen.copy()
            c_sku_u = [c for c in df_temp.columns if 'sku' in c.lower()][0]
            df_temp[c_sku_u] = df_temp[c_sku_u].astype(str).str.strip()
            
            # FILTER: Buang SKU yang gak ada di file cek real lo (Ini yang bikin jadi 231)
            df_temp = df_temp[df_temp[c_sku_u].isin(mapping_real.keys())]
            
            # Update Nilai Qty
            c_qty_u = [c for c in df_temp.columns if 'qty' in c.lower()][0]
            df_temp[c_qty_u] = df_temp[c_sku_u].map(mapping_real)
            
            st.session_state.df_ds_final = df_temp
            st.info(f"✅ Backdoor Aktif: {len(df_temp)} SKU valid terdeteksi.")
        except Exception as e:
            st.error(f"Gagal baca File 4: {e}")

    # --- 4. LOGIC DRAFT JEZPRO ---
    if f3:
        st.divider()
        st.subheader("📝 DRAFT JEZPRO FINAL COMPARE")
        
        if st.button("🏁 FINAL COMPARE TO DRAFT RTO", use_container_width=True):
            # Cek data mana yang dipake
            data_siap = st.session_state.df_ds_final if st.session_state.df_ds_final is not None else st.session_state.df_ds
            
            if data_siap is not None:
                df3_draft = pd.read_excel(f3) if f3.name.endswith('xlsx') else pd.read_csv(f3)
                
                # Compare
                hasil_draft = engine_compare_draft_vba(data_siap, df3_draft)
                
                # Filter Qty > 0 biar baris kosong gak ikut
                col_qty_f = [c for c in hasil_draft.columns if 'qty' in c.lower() or 'ambil' in c.lower()][0]
                hasil_draft = hasil_draft[pd.to_numeric(hasil_draft[col_qty_f], errors='coerce').fillna(0) > 0]
                
                total_vba = int(hasil_draft[col_qty_f].sum())
                st.metric("Total Qty Akhir", f"{total_vba} Pcs")
                
                if total_vba == 231:
                    st.success("✅ PROSES BERHASIL")
                
                st.dataframe(hasil_draft, use_container_width=True, hide_index=True)
                
                csv = hasil_draft.to_csv(index=False).encode('utf-8')
                st.download_button(f"📥 Download Draft Final ({total_vba} Pcs)", csv, f"Draft_Final_{total_vba}.csv", "text/csv", use_container_width=True)
            else:
                st.error("Jalankan Proses Awal dulu,!")
elif menu == "FDR Update":
    st.markdown('<div class="hero-header"><h1>🚚 FDR UPDATE - MANIFEST CHECKER</h1></div>', unsafe_allow_html=True)

    # --- 0. INIT STATE ---
    if "ws_manifest" not in st.session_state:
        st.session_state.ws_manifest = None
    if "ws_fu_it" not in st.session_state:
        st.session_state.ws_fu_it = None
    if "dict_kurir" not in st.session_state:
        st.session_state.dict_kurir = {}

    t1, t2, t3 = st.tabs(["MANIFEST INPUT", "PERLU FU IT", "SPLIT KURIR"])

    with t1:
        st.subheader("🛵 CEK MANIFEST OUTSTANDING")
        
        # 1. UPLOAD (Langsung masukin ke State)
        u_file = st.file_uploader("📂 Choose Your File", type=["xlsx"], key="fdr_up")
        if u_file:
            # Cek biar nggak loading terus-terusan
            if st.session_state.ws_manifest is None:
                st.session_state.ws_manifest = pd.read_excel(u_file)
                st.rerun()

        st.divider()
        c = st.columns(4)
        
        # --- MACRO 1: CLEAN COLUMNS (Anti-Error) ---
        if c[0].button("🚮 CLEAR COLUMNS", key="btn_clean"):
            if st.session_state.ws_manifest is not None:
                df = st.session_state.ws_manifest.copy()
                
                # Indeks kolom yang mau dihapus (VBA: G,H,I,K,L,M,R,S,T,U,V,W)
                cols_idx = [6, 7, 8, 10, 11, 12, 17, 18, 19, 20, 21, 22]
                
                # --- FIX: Filter indeks yang VALID aja (biar gak IndexError) ---
                # Artinya: Cuma hapus kalau kolomnya emang ada di file itu
                existing_cols = [df.columns[i] for i in cols_idx if i < len(df.columns)]
                
                if existing_cols:
                    df.drop(columns=existing_cols, inplace=True)
                    st.session_state.ws_manifest = df
                    st.success("KOLOM BERHASIL DIBERSIHKAN!")
                    st.rerun()
                else:
                    st.warning("Kolom sudah bersih atau tidak ditemukan!")
            else: 
                st.error("UPLOAD FILE DULU!")

        # --- MACRO 2: COPY FU IT (M / Index 12 TIDAK KOSONG) ---
        if c[1].button("🖥️ NEED FU IT", key="btn_fu"):
            if st.session_state.ws_manifest is not None:
                df = st.session_state.ws_manifest.copy()
                # Filter M (12) <> ""
                mask = df.iloc[:, 12].astype(str).str.strip().replace(['nan', 'None'], '') != ""
                st.session_state.ws_fu_it = df[mask].iloc[:, 0:13] # Ambil A-M
                st.success(f"Copy {len(st.session_state.ws_fu_it)} Baris!")
            else: st.error("Data Kosong!")

        # --- MACRO 3: SPLIT KURIR (F Isi & M Kosong) ---
        if c[2].button("🛵 OUTSTANDING COURIER", key="btn_split"):
            if st.session_state.ws_manifest is not None:
                df = st.session_state.ws_manifest.copy()
                f_val = df.iloc[:, 5].astype(str).str.strip().replace(['nan', 'None'], '')
                m_val = df.iloc[:, 12].astype(str).str.strip().replace(['nan', 'None'], '')
                
                mask = (f_val != "") & (m_val == "")
                filtered = df[mask].copy()
                
                if not filtered.empty:
                    d_kurir = {str(n): g.iloc[:, 0:13] for n, g in filtered.groupby(filtered.iloc[:, 5])}
                    st.session_state.dict_kurir = d_kurir
                    st.success("Split Beres!")
                else: st.error("No Data Split!")

        if c[3].button("🗑️ CLEAR", type="primary"):
            st.session_state.ws_manifest = None
            st.session_state.ws_fu_it = None
            st.session_state.dict_kurir = {}
            st.rerun()

        st.divider()
        # PREVIEW (Read-only, biar nggak ketimpa input kosong)
        if st.session_state.ws_manifest is not None:
            st.write("### 📂 MANIFEST DATA (A:Z)")
            st.dataframe(st.session_state.ws_manifest, use_container_width=True, hide_index=True)

    with t2:
        if st.session_state.ws_fu_it is not None:
            st.dataframe(st.session_state.ws_fu_it, use_container_width=True, hide_index=True)
            
    with t3:
        if st.session_state.dict_kurir:
            for k, d in st.session_state.dict_kurir.items():
                with st.expander(f"📦 {k}"):
                    st.dataframe(d, use_container_width=True)

elif menu == "Refill & Withdraw":
    menu_refill_withdraw()

# --- Navigasi ---
elif menu == "Stock Opname":
    menu_Stock_Opname()