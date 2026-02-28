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
import re

def get_yellow_skus(file, column_index):
    yellow_set = set()
    try:
        wb = load_workbook(file, data_only=True)
        ws = wb.active
        for row_idx in range(2, ws.max_row + 1):
            cell = ws.cell(row=row_idx, column=column_index)
            color = str(cell.fill.start_color.index)
            if color in ['FFFF0000', 'FFFFFF00', 'FFFF00', '00FFFF00']:
                sku_val = str(cell.value).strip().upper() if cell.value else ""
                if sku_val: yellow_set.add(sku_val)
    except: pass
    return yellow_set

def logic_compare_scan_to_stock(df_scan, df_stock):
    ds = df_scan.iloc[:, [0, 1, 2]].copy()
    ds.columns = ['BIN', 'SKU', 'QTY_SCAN']
    dt = df_stock.iloc[:, [1, 2, 9]].copy()
    dt.columns = ['BIN', 'SKU', 'QTY_SYSTEM']
    for df in [ds, dt]:
        df['BIN'] = df['BIN'].astype(str).str.strip().str.upper()
        df['SKU'] = df['SKU'].astype(str).str.strip().str.upper()
        qty_col = 'QTY_SCAN' if 'QTY_SCAN' in df.columns else 'QTY_SYSTEM'
        df[qty_col] = pd.to_numeric(df[qty_col], errors='coerce').fillna(0)
    dict_system = dt.groupby(['BIN', 'SKU'])['QTY_SYSTEM'].sum().to_dict()
    qty_sys_list, diff_list, note_list = [], [], []
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
    return ds

def logic_compare_stock_to_scan(df_stock, df_scan):
    dt = df_stock.copy()
    ds_lite = df_scan.iloc[:, [0, 1, 2]].copy()
    ds_lite.columns = ['BIN', 'SKU', 'QTY_SCAN']
    ds_lite['BIN'] = ds_lite['BIN'].astype(str).str.strip().str.upper()
    ds_lite['SKU'] = ds_lite['SKU'].astype(str).str.strip().str.upper()
    ds_lite['QTY_SCAN'] = pd.to_numeric(ds_lite['QTY_SCAN'], errors='coerce').fillna(0)
    dict_scan = ds_lite.groupby(['BIN', 'SKU'])['QTY_SCAN'].sum().to_dict()
    qty_so_list, diff_list, note_list = [], [], []
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
    for col in ['QTY SO', 'DIFF', 'NOTE']:
        if col in dt.columns: dt = dt.drop(columns=[col])
    dt['QTY_SO'] = qty_so_list
    dt['DIFF'] = diff_list
    dt['NOTE'] = note_list
    dt = dt.loc[:, ~dt.columns.duplicated()].copy()
    return dt

def logic_run_allocation(df_real_plus, df_system_plus, df_bin_coverage):
    sys_lite = df_system_plus.iloc[:, [1, 2, df_system_plus.columns.get_loc('DIFF')]].copy()
    sys_lite.columns = ['BIN', 'SKU', 'QTY_DIFF']
    sys_lite['SKU'] = sys_lite['SKU'].astype(str).str.strip().str.upper()
    sys_lite['QTY_DIFF'] = pd.to_numeric(sys_lite['QTY_DIFF'], errors='coerce').fillna(0)
    dict_system_source = sys_lite.groupby(['BIN', 'SKU'])['QTY_DIFF'].sum().to_dict()

    cov_lite = df_bin_coverage.iloc[:, [1, 2, 9]].copy() 
    cov_lite.columns = ['BIN', 'SKU', 'QTY_COV']
    cov_lite['SKU'] = cov_lite['SKU'].astype(str).str.strip().str.upper()
    cov_lite['QTY_COV'] = pd.to_numeric(cov_lite['QTY_COV'], errors='coerce').fillna(0)
    dict_cov_source = cov_lite.groupby(['BIN', 'SKU'])['QTY_COV'].sum().to_dict()

    df_res = df_real_plus.copy()
    df_sys_updated = df_system_plus.copy()
    bin_alokasi_list, qty_alokasi_list, status_list = [], [], []

    for idx, row in df_res.iterrows():
        sku = row['SKU']
        current_diff = row['DIFF']
        
        if current_diff > 0:
            remaining_diff = current_diff
            temp_alloc_bin, temp_alloc_qty = [], 0
            
            sys_list = [{'BIN': k[0], 'SKU': k[1], 'QTY': v} for k, v in dict_system_source.items() if k[1] == sku and v > 0]
            for src in sys_list:
                if remaining_diff <= 0: break
                qty_alloc = min(src['QTY'], remaining_diff)
                temp_alloc_bin.append(src['BIN'])
                temp_alloc_qty += qty_alloc
                dict_system_source[(src['BIN'], sku)] -= qty_alloc
                
                mask = (df_sys_updated.iloc[:,1].str.upper() == src['BIN']) & (df_sys_updated.iloc[:,2].str.upper() == sku)
                if mask.any():
                    diff_col_idx = df_sys_updated.columns.get_loc('DIFF')
                    df_sys_updated.loc[mask, df_sys_updated.columns[diff_col_idx]] -= qty_alloc
                remaining_diff -= qty_alloc

            if remaining_diff > 0:
                cov_list = [{'BIN': k[0], 'SKU': k[1], 'QTY': v} for k, v in dict_cov_source.items() if k[1] == sku and v > 0]
                for src in cov_list:
                    if remaining_diff <= 0: break
                    qty_alloc = min(src['QTY'], remaining_diff)
                    temp_alloc_bin.append(src['BIN'])
                    temp_alloc_qty += qty_alloc
                    dict_cov_source[(src['BIN'], sku)] -= qty_alloc
                    remaining_diff -= qty_alloc

            if temp_alloc_qty > 0:
                allocated_bin = " & ".join(list(set(temp_alloc_bin)))[:50]
                allocated_qty = temp_alloc_qty
                status = "FULL ALLOCATION" if remaining_diff <= 0 else "PARTIAL ALLOCATION"
            else:
                allocated_bin, allocated_qty, status = "", 0, "NO ALLOCATION"
        else:
            allocated_bin, allocated_qty, status = "", 0, "NO DIFF"

        bin_alokasi_list.append(allocated_bin)
        qty_alokasi_list.append(allocated_qty)
        status_list.append(status)

    df_res['BIN ALOKASI'] = bin_alokasi_list
    df_res['QTY ALLOCATION'] = qty_alokasi_list
    df_res['STATUS'] = status_list
    
    return df_res, df_sys_updated

# =========================================================
# 2. MENU UTAMA - SEMUA KODE DI DALAM FUNGSI INI
# =========================================================

def menu_Stock_Opname():
    # --- CSS & HERO HEADER ---
    st.markdown("""
       <style>
        .hero-header { background-color: #0E1117; padding: 20px; border-radius: 10px; margin-bottom: 20px; text-align: center; border: 1px solid #333; }
        .hero-header h1 { color: #FF4B4B; margin: 0; font-size: 32px; }
        div[data-baseweb="select"] > div { background-color: #262730 !important; border-color: #464855 !important; color: white !important; }
        div[data-baseweb="select"] input { color: white !important; }
        div[data-baseweb="select"] span { color: white !important; }
        div[data-baseweb="select"] svg { fill: white !important; }
        </style>
    """, unsafe_allow_html=True)
     
    st.markdown('<div class="hero-header"><h1>📦 STOCK OPNAME - COMPARE & ALLOCATION</h1></div>', unsafe_allow_html=True)
    
    # --- FILTER SECTION ---
    with st.container():
        st.markdown('<p style="font-weight: bold; color: #1d3567;">🎯 FILTER DATA</p>', unsafe_allow_html=True)
        col_f1, col_f2, col_f3 = st.columns(3)
        
        with col_f1:
            list_sub_kat = ["GYM&SWIM", "SZ SOCKS", "SZ EQUIPMENT", "JZ EQUIPMENT", "OTHER ACC", "SOCKS", "OTHER EQP", "SHOES", "LOWER BODY", "UPPER BODY", "BALL", "EQUIPMENT SPORT", "SHIRT", "ALL BASELAYER", "JACKET", "SET APPAREL", "JERSEY", "PANTS", "SANDALS", "BASELAYER", "OTHERS", "UKNOWN SC", "NUTRITION", "BAG", "EXTRAS SHOES"]
            selected_sub = st.multiselect("🗂️ Sub Kategori (System):", list_sub_kat, key="filter_sub_v7")

        with col_f2:
            list_bin_stock = ["GUDANG LT.2", "LIVE", "KL2", "KL1", "GL2-STORE", "OFFLINE", "TOKO", "GL1-DC", "RAK ACC LT.1", "GL3-DC-A", "GL3-DC-B", "GL3-DC-C", "GL3-DC-D", "GL3-DC-E", "GL3-DC-F", "GL3-DC-G", "GL3-DC-H", "GL3-DC-I", "GL3-DC-J", "GL4-DC-A", "GL4-DC-B", "GL4-DC-KL", "GL3-DC-RAK", "GL4-DC-RAK", "DAU", "KAV-2", "KAV-7", "KAV-8", "KAV-9", "KAV-10", "C-0", "KDR", "JBR", "GUDANG", "SDA", "SMG"]
            selected_bin_sys = st.multiselect("🏭 BIN System (System):", list_bin_stock, key="filter_bin_sys_v7")

        with col_f3:
            list_bin_cov = ["KARANTINA", "STAGGING", "STAGING", "GUDANG LT.2", "TOKO", "GL1-DC", "RAK ACC LT.1", "GL3-DC-A", "GL3-DC-B", "GL3-DC-C", "GL3-DC-D", "GL3-DC-E", "GL3-DC-F", "GL3-DC-G", "GL3-DC-H", "GL3-DC-I", "GL3-DC-J", "GL4-DC-A", "GL4-DC-B", "GL4-DC-KL1", "GL4-DC-KL2", "GL3-DC-RAK", "GL4-DC-RAK", "LIVE", "MARKOM", "AMP", "GL2-STORE"]
            selected_bin_cov = st.multiselect("📡 BIN Coverage (Scan):", list_bin_cov, key="filter_bin_cov_v7")

    st.markdown("---")

    # --- STEP 1: UPLOAD & COMPARE ---
    st.subheader("1️⃣ Upload & Run Compare")
    c1, c2 = st.columns(2)
    with c1:
        up_scan = st.file_uploader("📥 DATA SCAN", type=['xlsx','csv'], key="up_scan_v7")
    with c2:
        up_stock = st.file_uploader("📥 STOCK SYSTEM", type=['xlsx','csv'], key="up_stock_v7")

    if up_scan and up_stock:
        if st.button("▶️ RUN COMPARE", use_container_width=True, key="btn_run_compare_v7"):
            try:
                df_s_raw = pd.read_excel(up_scan) if up_scan.name.endswith(('.xlsx', '.xls')) else pd.read_csv(up_scan)
                df_t_raw = pd.read_excel(up_stock) if up_stock.name.endswith(('.xlsx', '.xls')) else pd.read_csv(up_stock)
                
                with st.spinner("Memproses..."):
                    if selected_sub:
                        df_t_raw = df_t_raw[df_t_raw.iloc[:, 6].astype(str).str.strip().str.upper().isin([x.upper() for x in selected_sub])]
                    if selected_bin_sys:
                        mask_bin = df_t_raw.iloc[:, 1].astype(str).str.upper().apply(lambda x: any(case.upper() in x for case in selected_bin_sys))
                        df_t_raw = df_t_raw[mask_bin]
                    if selected_bin_cov:
                        mask_cov = df_s_raw.iloc[:, 0].astype(str).str.upper().apply(lambda x: any(case.upper() in x for case in selected_bin_cov))
                        df_s_raw = df_s_raw[mask_cov]

                    if df_t_raw.empty: 
                        st.error("❌ Data System kosong!")
                    else:
                        res_scan = logic_compare_scan_to_stock(df_s_raw, df_t_raw)
                        res_stock = logic_compare_stock_to_scan(df_t_raw, df_s_raw)
                        real_plus = res_scan[res_scan['NOTE'] == "REAL +"].copy()
                        system_plus = res_stock[res_stock['NOTE'] == "SYSTEM +"].copy()
                        
                        try:
                            item_dict = df_t_raw.iloc[:, [2, 4]].dropna()
                            item_dict.columns = ['SKU', 'NAME']
                            item_dict['SKU'] = item_dict['SKU'].astype(str).str.strip().str.upper()
                            map_name = item_dict.drop_duplicates('SKU').set_index('SKU')['NAME'].to_dict()
                            real_plus['ITEM NAME'] = real_plus['SKU'].map(map_name)
                        except: pass

                        st.session_state.compare_result = {
                            'res_scan': res_scan, 
                            'res_stock': res_stock, 
                            'real_plus': real_plus, 
                            'system_plus': system_plus,
                            'df_s_raw': df_s_raw
                        }
                        st.success("✅ Compare Selesai! Silahkan lanjut ke Step 2.")
                        
            except Exception as e:
                st.error(f"❌ Error: {e}")

    # ============================================================
    # ✅ METRICS & TABS - SETELAH COMPARE
    # ============================================================
    if 'compare_result' in st.session_state:
        d = st.session_state.compare_result
        
        total_real = len(d['real_plus'])
        total_sys = len(d['system_plus'])
        qty_real = int(d['real_plus']['DIFF'].sum()) if not d['real_plus'].empty else 0
        qty_sys = int(d['system_plus']['DIFF'].sum()) if not d['system_plus'].empty else 0
        
        st.markdown(f"""
<div style="display: flex; gap: 10px; justify-content: center; margin-bottom: 20px;">
    <div class="m-box" style="flex:1"><span class="m-lbl">🔥 REAL + ITEMS</span><span class="m-val">{total_real}</span></div>
    <div class="m-box" style="flex:1"><span class="m-lbl">🔥 QTY REAL +</span><span class="m-val">{qty_real}</span></div>
    <div class="m-box" style="flex:1"><span class="m-lbl">💻 SYSTEM + ITEMS</span><span class="m-val">{total_sys}</span></div>
    <div class="m-box" style="flex:1"><span class="m-lbl">💻 QTY SYSTEM +</span><span class="m-val">{qty_sys}</span></div>
</div>
""", unsafe_allow_html=True)
        
        st.markdown("---")
        
        t1, t2, t3, t4 = st.tabs(["📋 DATA SCAN", "📊 STOCK SYSTEM", "🔥 REAL +", "💻 SYSTEM +"])
        with t1: st.dataframe(d['res_scan'], use_container_width=True)
        with t2: st.dataframe(d['res_stock'], use_container_width=True)
        with t3: st.dataframe(d['real_plus'], use_container_width=True)
        with t4: st.dataframe(d['system_plus'], use_container_width=True)

        # --- STEP 2: ALLOCATION ---
    st.markdown("---")
    st.subheader("2️⃣ Upload BIN COVERAGE & Run Allocation")
        
    up_bin_cov = st.file_uploader("📥 FILE BIN COVERAGE", type=['xlsx','csv'], key="up_bin_cov_v10")

    if up_bin_cov:
            if st.button("🚀 RUN ALLOCATION", use_container_width=True, key="btn_run_alloc_v10"):
                try:
                    df_cov_raw = pd.read_excel(up_bin_cov) if up_bin_cov.name.endswith(('.xlsx', '.xls')) else pd.read_csv(up_bin_cov)
                    
                    with st.spinner("Memproses Alokasi..."):
                        allocated_data, sys_updated = logic_run_allocation(d['real_plus'], d['system_plus'], df_cov_raw)
                        
                        # 🆕 GENERATE SET UP REAL + (SETELAH ALLOCATION)
                        df_s_raw_copy = d['df_s_raw'].copy()
                        df_s_raw_copy['SKU_UPPER'] = df_s_raw_copy.iloc[:, 2].astype(str).str.strip().str.upper()
                        df_s_raw_copy['BIN_SCAN'] = df_s_raw_copy.iloc[:, 0].astype(str).str.strip()
                        
                        bin_awal_map = df_s_raw_copy.groupby('SKU_UPPER')['BIN_SCAN'].first().to_dict()
                        
                        real_plus_diff = d['real_plus'][d['real_plus']['DIFF'] > 0].copy() if 'DIFF' in d['real_plus'].columns else pd.DataFrame()
                        
                        if not real_plus_diff.empty:
                            real_plus_diff['BIN AWAL'] = real_plus_diff['SKU'].map(bin_awal_map).fillna("NOT FOUND")
                            real_plus_diff['BIN TUJUAN'] = real_plus_diff.iloc[:, 1] if real_plus_diff.shape[1] > 1 else ""
                            real_plus_diff['SKU_COL'] = real_plus_diff['SKU']
                            real_plus_diff['QUANTITY'] = real_plus_diff['DIFF']
                            real_plus_diff['NOTES'] = "RELOCATION"
                            
                            set_up_real_plus = real_plus_diff[['BIN AWAL', 'BIN TUJUAN', 'SKU_COL', 'QUANTITY', 'NOTES', 'ITEM NAME']].copy()
                            set_up_real_plus = set_up_real_plus.rename(columns={'SKU_COL': 'SKU'})
                        else:
                            set_up_real_plus = pd.DataFrame(columns=['BIN AWAL', 'BIN TUJUAN', 'SKU', 'QUANTITY', 'NOTES', 'ITEM NAME'])

                        st.session_state.allocation_result = allocated_data
                        st.session_state.sys_updated_result = sys_updated
                        st.session_state.set_up_real_plus = set_up_real_plus
                        
                        st.success("✅ Allocation Selesai!")
                except Exception as e:
                    st.error(f"❌ Error Allocation: {e}")

    # ============================================================
    # ✅ HASIL ALLOCATION + SET UP REAL + (SETELAH RUN ALLOCATION)
    # ============================================================
    if 'allocation_result' in st.session_state and 'sys_updated_result' in st.session_state and 'set_up_real_plus' in st.session_state:
        st.markdown("---")
        st.subheader("📋 HASIL ALLOCATION")
        
        alloc_data = st.session_state.allocation_result
        sys_updated = st.session_state.sys_updated_result
        set_up_real_plus = st.session_state.set_up_real_plus
        d = st.session_state.compare_result
        
        st.markdown("### 📊 RINGKASAN ALLOCATION")
        
        full_alloc = len(alloc_data[alloc_data['STATUS'] == "FULL ALLOCATION"])
        partial_alloc = len(alloc_data[alloc_data['STATUS'] == "PARTIAL ALLOCATION"])
        no_alloc = len(alloc_data[alloc_data['STATUS'] == "NO ALLOCATION"])
        total_set_up = len(set_up_real_plus)
        
        st.markdown(f"""
<div style="display: flex; gap: 10px; justify-content: center; margin-bottom: 20px;">
    <div class="m-box" style="flex:1"><span class="m-lbl">✅ FULL ALLOCATION</span><span class="m-val">{full_alloc}</span></div>
    <div class="m-box" style="flex:1"><span class="m-lbl">⚠️ PARTIAL ALLOCATION</span><span class="m-val">{partial_alloc}</span></div>
    <div class="m-box" style="flex:1"><span class="m-lbl">❌ NO ALLOCATION</span><span class="m-val">{no_alloc}</span></div>
    <div class="m-box" style="flex:1; background-color: #e74c3c;"><span class="m-lbl">📦 SET UP REAL +</span><span class="m-val">{total_set_up}</span></div>
</div>
""", unsafe_allow_html=True)
        
        st.markdown("---")
        
        ta1, ta2, ta3 = st.tabs(["🔥 REAL + (With Allocation)", "📊 STOCK SYSTEM (Updated)", "📦 SET UP REAL +"])
        
        with ta1:
            st.dataframe(alloc_data, use_container_width=True)
        with ta2:
            st.dataframe(sys_updated, use_container_width=True)
        with ta3:
            st.dataframe(set_up_real_plus, use_container_width=True)
            
        st.markdown("---")
        st.subheader("📥 DOWNLOAD HASIL")
        
        output_alloc = io.BytesIO()
        with pd.ExcelWriter(output_alloc, engine='xlsxwriter') as writer:
            d['res_scan'].to_excel(writer, sheet_name='DATA SCAN', index=False)
            d['res_stock'].to_excel(writer, sheet_name='STOCK SYSTEM (Old)', index=False)
            d['real_plus'].to_excel(writer, sheet_name='REAL +', index=False)
            d['system_plus'].to_excel(writer, sheet_name='SYSTEM +', index=False)
            set_up_real_plus.to_excel(writer, sheet_name='SET UP REAL +', index=False)
            alloc_data.to_excel(writer, sheet_name='REAL + ALLOCATION', index=False)
            sys_updated.to_excel(writer, sheet_name='STOCK SYSTEM (New)', index=False)
        
        st.download_button(
            label="📥 DOWNLOAD HASIL EXCEL (ALLOCATION + SET UP REAL +)",
            data=output_alloc.getvalue(),
            file_name="Hasil_Allocation_SetUpRealPlus.xlsx",
            use_container_width=True,
            key="dl_alloc_final_v1"
        )

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

def engine_ds_rto_vba_total(df_ds, df_app):
    """
    LOGIKA AWAL: Membandingkan DS RTO dengan AppSheet RTO.
    Menghitung total Qty Ambil dari AppSheet (Slot 1 & Slot 2) 
    dan menentukan status SESUAI/KELEBIHAN/KURANG.
    """
    import pandas as pd
    import numpy as np

    if df_ds is None or df_app is None:
        return pd.DataFrame(), pd.DataFrame()

    # --- 1. PREPARASI DATA APPSHEET ---
    df_a = df_app.copy()
    # Beri nama kolom angka agar aman diakses (1-based index)
    df_a.columns = [str(i) for i in range(1, len(df_a.columns) + 1)]
    
    # Ambil baris yang statusnya DONE atau KURANG AMBIL (Kolom B / index 2)
    mask_status = df_a['2'].astype(str).str.strip().str.upper().isin(['DONE', 'KURANG AMBIL'])
    df_filtered = df_a[mask_status].copy()

    # Mapping Qty Total per SKU (Gabungan Slot 1 & Slot 2)
    dict_qty_total = {}
    for _, row in df_filtered.iterrows():
        # SKU Utama di Kolom 9 (I) atau Kolom 15 (O)
        sku = str(row.get('9', '')).strip().upper()
        if sku in ["", "NAN", "0", "NONE"]: 
            sku = str(row.get('15', '')).strip().upper()
        
        if sku not in ["", "NAN", "0", "NONE"]:
            # Qty Bin 1 (13/M) + Qty Bin 2 (17/Q)
            q13 = pd.to_numeric(row.get('13', 0), errors='coerce') or 0
            q17 = pd.to_numeric(row.get('17', 0), errors='coerce') or 0
            dict_qty_total[sku] = dict_qty_total.get(sku, 0) + (q13 + q17)

    # --- 2. PROSES DATAFRAME DS RTO ---
    res_ds = df_ds.copy()
    # Standarisasi 3 kolom pertama: SKU, QTY SCAN, QTY AMBIL
    cols = list(res_ds.columns)
    sku_col = cols[0]
    scan_col = cols[1]
    
    res_ds['SKU_UPPER'] = res_ds[sku_col].astype(str).str.strip().str.upper()
    res_ds['QTY AMBIL'] = res_ds['SKU_UPPER'].map(dict_qty_total).fillna(0)
    
    # Logika Penentuan Note
    def check_note(row):
        scan = pd.to_numeric(row[scan_col], errors='coerce') or 0
        ambil = row['QTY AMBIL']
        if scan > ambil: return "KELEBIHAN AMBIL"
        elif scan < ambil: return "KURANG AMBIL"
        else: return "SESUAI"
    
    res_ds['NOTE'] = res_ds.apply(check_note, axis=1)

    # --- 3. GENERATE SHEET SELISIH (Detail per BIN) ---
    results_selisih = []
    # Hanya yang tidak sesuai yang masuk ke sheet selisih
    mismatch_df = res_ds[res_ds['NOTE'] != 'SESUAI'].copy()
    
    for _, row in mismatch_df.iterrows():
        sku = row['SKU_UPPER']
        # Cari baris di AppSheet yang mengandung SKU ini
        mask_app = (df_a['9'].astype(str).str.strip().str.upper() == sku) | \
           (df_a['15'].astype(str).str.strip().str.upper() == sku)
        found_rows = df_a[mask_app]
        
        if not found_rows.empty:
            for _, r_app in found_rows.iterrows():
                # Cek Bin 1
                b1 = str(r_app.get('12', '')).strip()
                if b1 not in ["", "nan", "0"]:
                    results_selisih.append([sku, row[scan_col], row['QTY AMBIL'], row['NOTE'], b1, r_app.get('13', 0), 0])
                # Cek Bin 2
                b2 = str(r_app.get('16', '')).strip()
                if b2 not in ["", "nan", "0"]:
                    results_selisih.append([sku, row[scan_col], row['QTY AMBIL'], row['NOTE'], b2, r_app.get('17', 0), 0])
        else:
            # Jika SKU di DS tidak ada di AppSheet sama sekali
            results_selisih.append([sku, row[scan_col], row['QTY AMBIL'], row['NOTE'], "-", 0, 0])

    res_selisih = pd.DataFrame(results_selisih, columns=['SKU','QTY SCAN','QTY AMBIL','NOTE','BIN','QTY AMBIL BIN','HASIL CEK REAL'])
    
    # Bersihkan kolom sementara
    res_ds.drop(columns=['SKU_UPPER'], inplace=True)
    
    return res_ds, res_selisih
def engine_refresh_rto(df_ds, df_app_awal, df_selisih):
    import pandas as pd
    import numpy as np

    if df_app_awal.empty or df_selisih.empty:
        return df_ds, df_app_awal

    df_app_res = df_app_awal.copy()
    df_ds_res = df_ds.copy()

    # --- 1. MAPPING HASIL CEK REAL ---
    real_map = {}
    for _, row in df_selisih.iterrows():
        sku_real = str(row.iloc[0]).strip().upper()
        bin_real = str(row.iloc[4]).strip().upper()
        qty_real = pd.to_numeric(row.iloc[6], errors='coerce') or 0
        if sku_real not in ["", "NAN", "NONE"]:
            real_map[f"{sku_real}|{bin_real}"] = qty_real

    # --- 2. UPDATE APPSHEET RTO (Logika Kolom N) ---
    for idx in df_app_res.index:
        try:
            # SKU: I(8) atau O(14) | BIN: L(11) atau P(15)
            sku = str(df_app_res.iloc[idx, 8]).strip().upper()
            if sku in ["", "NAN", "0", "NONE"]:
                sku = str(df_app_res.iloc[idx, 14]).strip().upper()
            
            b1, b2 = str(df_app_res.iloc[idx, 11]).strip().upper(), str(df_app_res.iloc[idx, 15]).strip().upper()
            
            target_qty = real_map.get(f"{sku}|{b1}") if f"{sku}|{b1}" in real_map else real_map.get(f"{sku}|{b2}")

            if target_qty is not None:
                # Kolom N (index 13) Blank -> M (index 12) | N Isi -> Q (index 16)
                val_n = str(df_app_res.iloc[idx, 13]).strip()
                if val_n == "" or val_n.lower() == "nan":
                    df_app_res.iloc[idx, 12] = target_qty
                else:
                    df_app_res.iloc[idx, 16] = target_qty
        except Exception:
            continue

    # --- 3. SINKRONISASI DS RTO (Ultrafast) ---
    if not df_ds_res.empty:
        # Hitung Summary Qty Ambil terbaru dari AppSheet
        df_app_res['TMP_SKU'] = df_app_res.apply(lambda r: str(r.iloc[8]).strip().upper() if str(r.iloc[8]).strip() not in ["","0","nan"] else str(r.iloc[14]).strip().upper(), axis=1)
        df_app_res['TMP_QTY'] = df_app_res.apply(lambda r: (pd.to_numeric(r.iloc[12], errors='coerce') or 0) + (pd.to_numeric(r.iloc[16], errors='coerce') or 0), axis=1)
        
        summary_map = df_app_res.groupby('TMP_SKU')['TMP_QTY'].sum().to_dict()

        # Update DS menggunakan Mapping (Tanpa Loop)
        sku_col, scan_col, ambil_col = df_ds_res.columns[0], df_ds_res.columns[1], df_ds_res.columns[2]
        df_ds_res[ambil_col] = df_ds_res[sku_col].astype(str).str.strip().str.upper().map(summary_map).fillna(0)
        df_ds_res[scan_col] = df_ds_res[ambil_col] # Samakan agar SESUAI
        
        if 'NOTE' in df_ds_res.columns:
            df_ds_res['NOTE'] = "SESUAI"
        
        df_app_res.drop(columns=['TMP_SKU', 'TMP_QTY'], inplace=True)

    return df_ds_res, df_app_res

def engine_compare_draft_jezpro(df_app, df_draft):
    import pandas as pd
    import numpy as np

    df_res = df_draft.copy()
    df_a = df_app.copy()
    df_a.columns = [str(i) for i in range(1, len(df_a.columns) + 1)]

    # Buat Mapping Bin Lain di awal (Optimasi Ultrafast)
    bin_map = {}
    for _, r in df_a.iterrows():
        s = str(r.get('9', '')).strip().upper() if str(r.get('9','')) not in ["","0","nan"] else str(r.get('15','')).strip().upper()
        if s not in ["", "NAN"]:
            # Simpan semua bin yang tersedia untuk SKU tersebut
            bins = bin_map.get(s, [])
            if str(r.get('12','')) != "": bins.append((str(r.get('12','')), pd.to_numeric(r.get('13',0), errors='coerce') or 0))
            if str(r.get('16','')) != "": bins.append((str(r.get('16','')), pd.to_numeric(r.get('17',0), errors='coerce') or 0))
            bin_map[s] = bins

    for idx, row in df_res.iterrows():
        tf_draft = str(row.iloc[0]).strip().upper() if not pd.isna(row.iloc[0]) else ""
        sku_d = str(row.iloc[3]).strip().upper()
        bin_d = str(row.iloc[8]).strip().upper()
        qty_h = pd.to_numeric(row.iloc[7], errors='coerce') or 0

       # --- 1. CARI MATCH ---
        # Pastikan baris ini sejajar dengan logika di dalam loop 'for idx, row in df_res.iterrows():'
        match_data = df_a[
            ((df_a['9'].astype(str).str.upper() == sku_d) & (df_a['12'].astype(str).str.upper() == bin_d)) | 
            ((df_a['15'].astype(str).str.upper() == sku_d) & (df_a['16'].astype(str).str.upper() == bin_d))
        ]

        # Inisialisasi variabel (Harus sejajar dengan match_data)
        qty_j, bin_l, qty_m, note, status = 0, "", 0, "HAPUS ITEM INI DARI DRAFT", "DELETE ITEM"

        if not match_data.empty:
            r_app = match_data.iloc[0]
            # ... lanjut ke logika penentuan status selanjutnya

        if not match_data.empty:
            r_app = match_data.iloc[0]
            tf_app = str(r_app.get('18', '')).strip().upper()
            if tf_draft in ["", "0", "NAN"] or tf_app in ["", "0", "NAN"] or tf_draft == tf_app:
                qty_j = pd.to_numeric(r_app.get('13', 0) if str(r_app.get('12','')).upper() == bin_d else r_app.get('17',0), errors='coerce') or 0
                
                if qty_j < qty_h:
                    note, status = "QTY AMBIL KURANG DARI DRAFT", "PERLU EDIT QTY DRAFT"
                elif qty_j == qty_h:
                    note, status = "DRAFT SESUAI", "OK"
                else:
                    # Cari Bin Lain dari Mapping
                    for b_ext, q_ext in bin_map.get(sku_d, []):
                        if b_ext.upper() != bin_d:
                            bin_l, qty_m, note = b_ext, q_ext, "ADA BIN LAIN"
                            status = "PERLU EDIT BIN & QTY TF" if (qty_j + qty_m) < qty_h else "PERLU EDIT BIN & HAPUS BIN LAMA"
                            break

        df_res.loc[idx, ['QTY AMBIL', 'NOTE', 'BIN AMBIL LAIN', 'QTY BIN LAIN', 'STATUS']] = [qty_j, note, bin_l, qty_m if qty_m > 0 else "", status]

    return df_res
def engine_generate_new_draft(df_compared):
    import pandas as pd
    if df_compared is None or df_compared.empty:
        return pd.DataFrame(columns=['BIN', 'SKU', 'QUANTITY'])

    dict_final = {}
    for _, row in df_compared.iterrows():
        sku = str(row.iloc[3]).strip().upper()
        bin_i = str(row.iloc[8]).strip().upper()
        bin_l = str(row.iloc[11]).strip().upper() if not pd.isna(row.iloc[11]) else ""
        
        q_j = pd.to_numeric(row['QTY AMBIL'], errors='coerce') or 0
        q_m = pd.to_numeric(row['QTY BIN LAIN'], errors='coerce') or 0
        
        if q_j > 0:
            k = f"{bin_i}|{sku}"
            dict_final[k] = dict_final.get(k, 0) + q_j
        
        if q_m > 0 and bin_l not in ["", "-", "NAN"]:
            k_l = f"{bin_l}|{sku}"
            dict_final[k_l] = dict_final.get(k_l, 0) + q_m

    res = pd.DataFrame([{'BIN': k.split('|')[0], 'SKU': k.split('|')[1], 'QUANTITY': v} for k, v in dict_final.items()])
    return res.sort_values(['BIN', 'SKU']).reset_index(drop=True) if not res.empty else res

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
    # Simpan nama kolom asli sebelum rename
    original_columns = list(df_asal.columns)
    
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
                    
                    out_data.append([bin_asal, sku, original_diff, b, take, diff_after_take, 
                                    "FULLY SETUP" if diff_after_take == 0 else "PARTIAL SETUP"])
                    
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
        
        # --- JIKA TIDAK KETEMU ---
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
    
    # 6. REKAP KURANG SETUP
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
    
    # 8. STAGGING LT.3 OUTSTANDING (PAKE NAMA KOLOM ASLI)
    lt3_mask = (
        (df_asal_updated[col_qty_asal] > 0) & 
        (df_asal_updated[col_bin_asal].astype(str).str.upper().str.contains("STAGGING LT\\.?3|STAGING LT\\.?3", na=False, regex=True))
    )
    df_lt3 = df_asal_updated[lt3_mask].copy()
    
    if not df_lt3.empty:
        # AMBIL KOLOM SESUAI POSISI VBA ASLI
        # Kolom 1 (index 0) = A, Kolom 2 (index 1) = B, dst
        cols_to_take = []
        
        # Sesuaikan dengan posisi asli (1=BIN, 2=SKU, 4=NAMA, 5=BRAND, 6=CAT, 7=SAT, 10=QTY)
        for col_idx in df_lt3.columns:
            if col_idx == 0:  # Kolom A
                cols_to_take.append('Identify')
            elif col_idx == 1:  # Kolom B
                cols_to_take.append('BIN')
            elif col_idx == 2:  # Kolom E
                cols_to_take.append('SKU')
            elif col_idx == 3:  # Kolom F
                cols_to_take.append('BRAND')
            elif col_idx == 4:  # Kolom G
                cols_to_take.append('ITEM NAME')
            elif col_idx == 5:  # Kolom H
                cols_to_take.append('VARIANT')
            elif col_idx == 6:  # Kolom I
                cols_to_take.append('SUB KATEGORI')
            elif col_idx == 7:  # Kolom J
                cols_to_take.append('Harga Beli')
            elif col_idx == 8:  # Kolom K
                cols_to_take.append('Harga Jual')
            elif col_idx == 9:  # Kolom L
                cols_to_take.append('QTY SYSTEM')
            elif col_idx == 10:  # Kolom M
                cols_to_take.append('QTY SO')
            else:
                cols_to_take.append(f'COL_{col_idx}')
        
        df_lt3.columns = cols_to_take
        
    else:
        df_lt3 = pd.DataFrame(columns=["BIN", "SKU", "NAMA BARANG", "BRAND", "CATEGORY", "SATUAN", "QTY"])
    
    return df_comp, df_plist, df_kurang, df_sum, df_lt3, df_asal_updated

import pandas as pd
import numpy as np
import io

def process_scan_out(df_scan, df_history, df_stock):
    """
    Fungsi Scan Out - Cari SEMUA data match, bukan cuma yang pertama
    """
    
    # ========== COPY DATA ==========
    df_scan = df_scan.copy()
    df_history = df_history.copy()
    df_stock = df_stock.copy()
    
    # ========== NORMALISASI ==========
    df_scan.columns = [str(col).strip().upper() for col in df_scan.columns]
    df_history.columns = [str(col).strip().upper() for col in df_history.columns]
    df_stock.columns = [str(col).strip().upper() for col in df_stock.columns]
    
    # ========== RENAME KOLOM ==========
    # DATA SCAN: A=BIN, B=SKU
    df_scan = df_scan.rename(columns={
        df_scan.columns[0]: 'BIN_AWAL',
        df_scan.columns[1]: 'SKU',
    })
    
    # HISTORY SET UP: D=SKU, I=BIN, K=QTY, M=BIN After
    if len(df_history.columns) > 3:
        df_history = df_history.rename(columns={df_history.columns[3]: 'SKU'})
    if len(df_history.columns) > 8:
        df_history = df_history.rename(columns={df_history.columns[8]: 'BIN_HIST'})
    if len(df_history.columns) > 10:
        df_history = df_history.rename(columns={df_history.columns[10]: 'QTY_HIST'})
    if len(df_history.columns) > 12:
        df_history = df_history.rename(columns={df_history.columns[12]: 'BIN_AFTER'})
    
    # STOCK TRACKING: A=INV, B=SKU, G=BIN, K=QTY
    if len(df_stock.columns) > 0:
        df_stock = df_stock.rename(columns={df_stock.columns[0]: 'INVOICE'})
    if len(df_stock.columns) > 1:
        df_stock = df_stock.rename(columns={df_stock.columns[1]: 'SKU'})
    if len(df_stock.columns) > 6:
        df_stock = df_stock.rename(columns={df_stock.columns[6]: 'BIN_STOCK'})
    if len(df_stock.columns) > 10:
        df_stock = df_stock.rename(columns={df_stock.columns[10]: 'QTY_STOCK'})
    
    # ========== FILTER DATA ==========
    scan_skus = set(df_scan['SKU'].dropna().astype(str).str.strip())
    
    # Filter HISTORY
    if 'SKU' in df_history.columns:
        df_history['SKU'] = df_history['SKU'].astype(str).str.strip()
        df_history = df_history[df_history['SKU'].isin(scan_skus)].copy()
    
    # Filter STOCK
    if 'SKU' in df_stock.columns and 'INVOICE' in df_stock.columns:
        df_stock['SKU'] = df_stock['SKU'].astype(str).str.strip()
        df_stock['INVOICE'] = df_stock['INVOICE'].astype(str).str.strip()
        valid_mask = df_stock['SKU'].isin(scan_skus) & df_stock['INVOICE'].str.contains('INV', case=False, na=False)
        df_stock = df_stock[valid_mask].copy()
    
    # ========== HITUNG QTY (COUNTIFS) ==========
    df_scan['QTY'] = df_scan.groupby(['BIN_AWAL', 'SKU'])['BIN_AWAL'].transform('count')
    df_scan = df_scan.drop_duplicates(subset=['BIN_AWAL', 'SKU'], keep='first').copy()
    df_scan = df_scan.reset_index(drop=True)
    
    # ========== KONVERSI NUMERIC ==========
    df_scan['QTY'] = pd.to_numeric(df_scan['QTY'], errors='coerce').fillna(0)
    if 'QTY_HIST' in df_history.columns:
        df_history['QTY_HIST'] = pd.to_numeric(df_history['QTY_HIST'], errors='coerce').fillna(0)
    if 'QTY_STOCK' in df_stock.columns:
        df_stock['QTY_STOCK'] = pd.to_numeric(df_stock['QTY_STOCK'], errors='coerce').fillna(0)
    
    # ========== CONVERT KE STRING ==========
    df_history['SKU'] = df_history['SKU'].astype(str).str.strip()
    df_history['BIN_HIST'] = df_history['BIN_HIST'].astype(str).str.strip() if 'BIN_HIST' in df_history.columns else ''
    df_stock['SKU'] = df_stock['SKU'].astype(str).str.strip()
    df_stock['BIN_STOCK'] = df_stock['BIN_STOCK'].astype(str).str.strip() if 'BIN_STOCK' in df_stock.columns else ''
    
    # ========== COMPARE DATA (LOGIKA BARU: CARI SEMUA) ==========
    df_scan['KETERANGAN'] = ''
    df_scan['TOTAL_QTY_SETUP_TERJUAL'] = 0
    df_scan['BIN_AFTER_SET_UP'] = ''
    df_scan['INVOICE'] = ''
    
    for idx in df_scan.index:
        sku = str(df_scan.loc[idx, 'SKU']).strip()
        bin_awal = str(df_scan.loc[idx, 'BIN_AWAL']).strip()
        qty_scan = int(df_scan.loc[idx, 'QTY'])
        
        # ===== CARI SEMUA DATA DI STOCK (SKU + BIN) =====
        stock_matches = df_stock[
            (df_stock['SKU'] == sku) & 
            (df_stock['BIN_STOCK'] == bin_awal)
        ]
        
        if not stock_matches.empty:
            # Ada data di STOCK dengan BIN yang sama
            total_qty_stock = stock_matches['QTY_STOCK'].sum()
            invoices = ', '.join(stock_matches['INVOICE'].astype(str).unique())
            
            df_scan.loc[idx, 'TOTAL_QTY_SETUP_TERJUAL'] = int(total_qty_stock)
            df_scan.loc[idx, 'INVOICE'] = invoices
            
            if int(total_qty_stock) == qty_scan:
                df_scan.loc[idx, 'KETERANGAN'] = 'ITEM TELAH TERJUAL'
            else:
                df_scan.loc[idx, 'KETERANGAN'] = 'ITEM TERJUAL (QTY MISSMATCH)'
        
        else:
            # ===== CARI SEMUA DATA DI HISTORY (SKU) =====
            hist_matches = df_history[df_history['SKU'] == sku]
            
            if not hist_matches.empty:
                # Ada data di HISTORY, cari apakah ada yang MATCH
                match_found = False
                total_qty_hist = 0
                bin_after_result = ''
                
                for _, hist_row in hist_matches.iterrows():
                    bin_hist = str(hist_row.get('BIN_HIST', '')).strip()
                    qty_hist = int(hist_row.get('QTY_HIST', 0))
                    bin_after = str(hist_row.get('BIN_AFTER', '')).strip()
                    
                    total_qty_hist += qty_hist
                    bin_after_result = bin_after
                    
                    # Cek apakah ada yang MATCH (BIN sama DAN QTY sama)
                    if bin_hist == bin_awal and qty_hist == qty_scan:
                        match_found = True
                        break
                
                df_scan.loc[idx, 'TOTAL_QTY_SETUP_TERJUAL'] = total_qty_hist
                df_scan.loc[idx, 'BIN_AFTER_SET_UP'] = bin_after_result
                
                if match_found:
                    df_scan.loc[idx, 'KETERANGAN'] = 'DONE AND MATCH SET UP'
                else:
                    # Cek apakah ada yang BIN sama (tapi QTY berbeda)
                    bin_same_qty_diff = hist_matches[hist_matches['BIN_HIST'] == bin_awal]
                    if not bin_same_qty_diff.empty:
                        df_scan.loc[idx, 'KETERANGAN'] = 'DONE SETUP (QTY MISSMATCH)'
                    else:
                        df_scan.loc[idx, 'KETERANGAN'] = 'DONE SET UP (BIN MISSMATCH)'
            
            else:
                # ===== CARI SEMUA DATA DI STOCK (SKU saja - BIN berbeda) =====
                stock_sku_matches = df_stock[df_stock['SKU'] == sku]
                
                if not stock_sku_matches.empty:
                    total_qty_stock = stock_sku_matches['QTY_STOCK'].sum()
                    invoices = ', '.join(stock_sku_matches['INVOICE'].astype(str).unique())
                    
                    df_scan.loc[idx, 'KETERANGAN'] = 'ITEM TERJUAL (BIN MISSMATCH)'
                    df_scan.loc[idx, 'TOTAL_QTY_SETUP_TERJUAL'] = int(total_qty_stock)
                    df_scan.loc[idx, 'INVOICE'] = invoices
                else:
                    # ===== TIDAK DITEMUKAN =====
                    df_scan.loc[idx, 'KETERANGAN'] = 'ITEM BELUM TERSETUP & TIDAK TERJUAL'
    
    # ========== BUAT DRAFT ==========
    draft_data = []
    
    for idx in df_scan.index:
        ket = df_scan.loc[idx, 'KETERANGAN']
        bin_awal = df_scan.loc[idx, 'BIN_AWAL']
        sku = df_scan.loc[idx, 'SKU']
        qty_scan = int(df_scan.loc[idx, 'QTY'])
        qty_total = int(df_scan.loc[idx, 'TOTAL_QTY_SETUP_TERJUAL'])
        bin_after = df_scan.loc[idx, 'BIN_AFTER_SET_UP']
        
        if ket == 'DONE SETUP (QTY MISSMATCH)':
            draft_data.append({
                'BIN AWAL': bin_awal,
                'BIN TUJUAN': bin_after,
                'SKU': sku,
                'QUANTITY': qty_scan - qty_total,
                'NOTES': 'WAITING OFFLINE'
            })
        elif ket == 'ITEM BELUM TERSETUP & TIDAK TERJUAL':
            draft_data.append({
                'BIN AWAL': bin_awal,
                'BIN TUJUAN': 'KARANTINA',
                'SKU': sku,
                'QUANTITY': qty_scan,
                'NOTES': 'WAITING OFFLINE'
            })
        elif ket == 'DONE SET UP (BIN MISSMATCH)':
            draft_data.append({
                'BIN AWAL': bin_after,
                'BIN TUJUAN': bin_awal,
                'SKU': sku,
                'QUANTITY': qty_total,
                'NOTES': 'SET UP BALIK'
            })
            draft_data.append({
                'BIN AWAL': bin_awal,
                'BIN TUJUAN': 'KARANTINA',
                'SKU': sku,
                'QUANTITY': qty_scan,
                'NOTES': 'WAITING OFFLINE'
            })
    
    df_draft = pd.DataFrame(draft_data, columns=['BIN AWAL', 'BIN TUJUAN', 'SKU', 'QUANTITY', 'NOTES']) if draft_data else pd.DataFrame(columns=['BIN AWAL', 'BIN TUJUAN', 'SKU', 'QUANTITY', 'NOTES'])
    
    # ========== OUTPUT ==========
    df_res = df_scan[['BIN_AWAL', 'SKU', 'QTY', 'KETERANGAN', 'TOTAL_QTY_SETUP_TERJUAL', 'BIN_AFTER_SET_UP', 'INVOICE']].copy()
    df_res.columns = ['BIN AWAL', 'SKU', 'QTY SCAN', 'Keterangan', 'Total Qty Setup/Terjual', 'Bin After Set Up', 'Invoice']
    
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
    
    # --- CSS ---
    st.markdown("""
        <style>
        .m-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; text-align: center; margin: 5px 0; }
        .m-lbl { display: block; font-size: 14px; color: #555; font-weight: bold; }
        .m-val { display: block; font-size: 24px; color: #ff4b4b; font-weight: bold; }
        </style>
    """, unsafe_allow_html=True)
    
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
                
                # --- RINGKASAN (PERBAIKAN: GUNAKAN QTY, BUKAN ROW!) ---
                st.divider()
                st.subheader("📊 RINGKASAN HASIL")
                
                # PERBAIKAN: GUNAKAN SUM QTY, BUKAN LEN
                total_compare_qty = int(df_comp['QTY PUTAWAY'].sum()) if not df_comp.empty else 0
                total_list_qty = int(df_plist['QTY BIN SYSTEM'].sum()) if not df_plist.empty else 0
                total_kurang_qty = int(df_kurang['QTY'].sum()) if not df_kurang.empty else 0
                
                # QTY LT3
                lt3_total_qty = 0
                if not df_lt3.empty:
                    # Cari kolom QTY di df_lt3
                    for col in df_lt3.columns:
                        if 'qty' in col.lower():
                            lt3_total_qty = int(df_lt3[col].sum())
                            break
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown(f'''<div class="m-box"><span class="m-lbl">Hasil Compare (Qty)</span><span class="m-val">{total_compare_qty}</span></div>''', unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f'''<div class="m-box"><span class="m-lbl">List Item Set Up (Qty)</span><span class="m-val">{total_list_qty}</span></div>''', unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f'''<div class="m-box"><span class="m-lbl">Kurang Setup (Qty)</span><span class="m-val">{total_kurang_qty}</span></div>''', unsafe_allow_html=True)
                
                with col4:
                    st.markdown(f'''<div class="m-box"><span class="m-lbl">STG.LT.3 Outstanding</span><span class="m-val">{lt3_total_qty}</span></div>''', unsafe_allow_html=True)
                
                # --- TABS ---
                t1, t2, t3, t4 = st.tabs(["📋 Hasil Compare", "📝 List Setup", "⚠️ Kurang Setup", "📦 STG.LT.3 Outstanding"])
                
                with t1: st.dataframe(df_comp, use_container_width=True)
                with t2: st.dataframe(df_plist, use_container_width=True)
                with t3: 
                    if not df_kurang.empty:
                        st.dataframe(df_kurang, use_container_width=True)
                    else:
                        st.success("✅ Semua Tercover!")
                with t4: 
                    if not df_lt3.empty:
                        st.dataframe(df_lt3, use_container_width=True)
                    else:
                        st.success("✅ Tidak ada STG.LT.3 Outstanding!")
                
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
                if up_scan.name.endswith('.csv'):
                    df_s = pd.read_csv(up_scan)
                else:
                    df_s = pd.read_excel(up_scan, engine='openpyxl')
                
                df_h = pd.read_excel(up_hist, engine='openpyxl')
                df_st = pd.read_excel(up_stock, engine='openpyxl')
                
                df_s.columns = [str(col).strip().upper() for col in df_s.columns]
                df_h.columns = [str(col).strip().upper() for col in df_h.columns]
                df_st.columns = [str(col).strip().upper() for col in df_st.columns]
                
                if len(df_s.columns) < 2:
                    st.error("❌ DATA SCAN harus memiliki minimal 2 kolom (BIN, SKU)")
                    st.stop()
                if len(df_h.columns) < 4:
                    st.error("❌ HISTORY SET UP harus memiliki minimal 4 kolom")
                    st.stop()
                if len(df_st.columns) < 2:
                    st.error("❌ STOCK TRACKING harus memiliki minimal 2 kolom")
                    st.stop()
                
                with st.spinner('🔄 Sedang memproses data...'):
                    df_res, df_draft = process_scan_out(df_s, df_h, df_st)
                
                st.success("✅ Validasi Selesai!")
                
                # ========== STATISTIK DENGAN KOTAK CUSTOM ==========
                st.divider()
                st.subheader("📊 Ringkasan Hasil")
                
                total_items = len(df_res)
                terjual_count = df_res['Keterangan'].str.contains('TERJUAL', case=False, na=False).sum()
                mismatch_count = df_res['Keterangan'].str.contains('MISSMATCH', case=False, na=False).sum()
                belum_count = df_res['Keterangan'].str.contains('BELUM', case=False, na=False).sum()
                done_count = df_res['Keterangan'].str.contains('DONE', case=False, na=False).sum()
                
                sc1, sc2, sc3, sc4, sc5 = st.columns(5)
                
                with sc1:
                    st.markdown(f'''
                    <div class="m-box">
                        <span class="m-lbl">📦 Total Items</span>
                        <span class="m-val">{total_items}</span>
                    </div>
                    ''', unsafe_allow_html=True)
                
                with sc2:
                    st.markdown(f'''
                    <div class="m-box">
                        <span class="m-lbl">✅ DONE</span>
                        <span class="m-val">{done_count}</span>
                    </div>
                    ''', unsafe_allow_html=True)
                
                with sc3:
                    st.markdown(f'''
                    <div class="m-box">
                        <span class="m-lbl">📤 TERJUAL</span>
                        <span class="m-val">{terjual_count}</span>
                    </div>
                    ''', unsafe_allow_html=True)
                
                with sc4:
                    st.markdown(f'''
                    <div class="m-box">
                        <span class="m-lbl">⚠️ MISSMATCH</span>
                        <span class="m-val">{mismatch_count}</span>
                    </div>
                    ''', unsafe_allow_html=True)
                
                with sc5:
                    st.markdown(f'''
                    <div class="m-box">
                        <span class="m-lbl">❌ BELUM TERSETUP</span>
                        <span class="m-val">{belum_count}</span>
                    </div>
                    ''', unsafe_allow_html=True)
                
                st.divider()
                
                # ========== TAMPILKAN HASIL ==========
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
                
                st.subheader("📋 DATA SCAN (COMPARED)")
                styled_df = df_res.style.applymap(highlight_vba, subset=['Keterangan']).apply(
                    lambda x: ['background-color: #ffcccc' if 'MISSMATCH' in str(x) or 'BELUM' in str(x) else '' for i in x],
                    subset=['Keterangan'], axis=1
                )
                st.dataframe(styled_df, use_container_width=True, height=400)
                
                if len(df_draft) > 0:
                    st.subheader("📝 DRAFT SET UP")
                    
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
                
                # ========== DOWNLOAD ==========
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_res.to_excel(writer, sheet_name='DATA SCAN', index=False)
                    workbook = writer.book
                    worksheet = writer.sheets['DATA SCAN']
                    
                    header_format = workbook.add_format({
                        'bold': True,
                        'bg_color': '#0070C0',
                        'font_color': 'white',
                        'align': 'center',
                        'border': 1
                    })
                    
                    int_format = workbook.add_format({'num_format': '0'})
                    
                    for col_num, value in enumerate(df_res.columns.values):
                        worksheet.write(0, col_num, value, header_format)
                    
                    worksheet.set_column(0, 1, 15)
                    worksheet.set_column(2, 2, 10, int_format)
                    worksheet.set_column(3, 3, 35)
                    worksheet.set_column(4, 4, 20, int_format)
                    worksheet.set_column(5, 6, 15)
                    
                    if len(df_draft) > 0:
                        df_draft.to_excel(writer, sheet_name='DRAFT SET UP', index=False)
                        worksheet_draft = writer.sheets['DRAFT SET UP']
                        for col_num, value in enumerate(df_draft.columns.values):
                            worksheet_draft.write(0, col_num, value, header_format)
                        worksheet_draft.set_column(0, 2, 15)
                        worksheet_draft.set_column(3, 3, 10, int_format)
                        worksheet_draft.set_column(4, 4, 20)
                
                st.download_button(
                    label="📥 DOWNLOAD HASIL (DATA SCAN + DRAFT)",
                    data=output.getvalue(),
                    file_name="SCAN_OUT_RESULT.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                
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
            df = pd.read_excel(uploaded_file, engine="openpyxl")
            
            col_sku, col_bin = 'SKU', 'BIN'
            col_qty = next((c for c in df.columns if 'QTY SYS' in str(c).upper()), 'QTY SYSTEM')
            
            if st.button("🔃 PROSES DATA"):
                with st.spinner('Memproses...'):
                    # Backup data minus awal (SEMUA item minus)
                    df_minus_awal = df[df[col_qty] < 0].copy()
                    
                    # Konversi nilai ke numerik
                    qty_arr = pd.to_numeric(df[col_qty], errors='coerce').fillna(0).values
                    sku_arr = df[col_sku].astype(str).values
                    bin_arr = df[col_bin].astype(str).values
                    
                    # Prioritas lokasi
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
                    
                    # --- RINGKASAN DENGAN KOTAK CUSTOM ---
                    st.divider()
                    st.subheader("📊 RINGKASAN HASIL PROSES")
                    
                    # Hitung nilai
                    total_transfer = len(set_up_results)
                    total_qty = int(sum([x['QUANTITY'] for x in set_up_results]))
                    still_minus = len(df_need_adj)
                    
                    # Tampilkan dalam kotak custom
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown(f'''
                        <div class="m-box">
                            <span class="m-lbl">Total Stock Minus</span>
                            <span class="m-val">{total_transfer}</span>
                        </div>
                        ''', unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown(f'''
                        <div class="m-box">
                            <span class="m-lbl">Mutasi Stock Minus</span>
                            <span class="m-val">{total_qty}</span>
                        </div>
                        ''', unsafe_allow_html=True)
                    
                    with col3:
                        st.markdown(f'''
                        <div class="m-box">
                            <span class="m-lbl">Need Justification</span>
                            <span class="m-val">{still_minus}</span>
                        </div>
                        ''', unsafe_allow_html=True)
                    
                    # Preview Data Transfer
                    if set_up_results:
                        st.write("#### 📋 Detail Transfer (SET_UP)")
                        st.dataframe(pd.DataFrame(set_up_results), use_container_width=True)
                    
                    # --- PERBAIKAN: RINGKASAN MINUS PER LOKASI (SEMUA ITEM MINUS) ---
                    if not df_minus_awal.empty:
                        st.warning("⚠️ Ringkasan Minus per Lokasi (SEMUA Item Minus):")
                        
                        # Group by BIN - GUNAKAN df_minus_awal (SEMUA minus awal)
                        df_minus_awal['QTY_MINUS'] = df_minus_awal[col_qty].abs()
                        detail_minus = df_minus_awal.groupby([col_bin, col_sku])['QTY_MINUS'].sum().reset_index()
                        detail_minus = detail_minus.sort_values(by=[col_bin, 'QTY_MINUS'], ascending=[True, False])
                        
                        # Tampilkan dalam expander per BIN
                        bins = sorted(df_minus_awal[col_bin].unique())
                        for bin_loc in bins:
                            bin_data = detail_minus[detail_minus[col_bin] == bin_loc]
                            total_bin_minus = int(bin_data['QTY_MINUS'].sum())
                            with st.expander(f"📍 {bin_loc} - Total Minus: {total_bin_minus}"):
                                st.dataframe(bin_data, use_container_width=True)
                        
                        # Summary Table - TAMPILKAN SEMUA
                        st.write("#### 📊 Ringkasan Minus per Lokasi")
                        summary_per_bin = df_minus_awal.groupby(col_bin).agg({
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
            import traceback
            st.code(traceback.format_exc())


elif menu == "Compare RTO":
    st.markdown('<div class="hero-header"><h1>📦 RTO GATEWAY SYSTEM</h1></div>', unsafe_allow_html=True)
    
    # --- CSS ---
    st.markdown("""
        <style>
        .m-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; text-align: center; margin: 5px 0; }
        .m-lbl { display: block; font-size: 14px; color: #555; font-weight: bold; }
        .m-val { display: block; font-size: 24px; color: #ff4b4b; font-weight: bold; }
        </style>
    """, unsafe_allow_html=True)
    
    # --- INIT SESSION STATE ---
    if 'rto_df_ds' not in st.session_state:
        st.session_state.rto_df_ds = None
    if 'rto_df_selisih' not in st.session_state:
        st.session_state.rto_df_selisih = None
    if 'rto_df_app' not in st.session_state:
        st.session_state.rto_df_app = None
    if 'rto_draft_compared' not in st.session_state:
        st.session_state.rto_draft_compared = None
    if 'rto_new_draft' not in st.session_state:
        st.session_state.rto_new_draft = None
    
    # --- FILE UPLOAD ---
    c1, c2 = st.columns(2)
    with c1: f1 = st.file_uploader("1. DS RTO", type=['xlsx','csv'], key="rto_f1")
    with c2: f2 = st.file_uploader("2. APPSHEET RTO", type=['xlsx','csv'], key="rto_f2")
    
    st.divider()
    
    # --- PROSES AWAL (DS vs APPSHEET) ---
    if f1 and f2:
        if st.button("▶️ JALANKAN PROSES", use_container_width=True):
            with st.spinner("Memproses..."):
                df1 = pd.read_excel(f1) if f1.name.endswith('xlsx') else pd.read_csv(f1)
                df2 = pd.read_excel(f2) if f2.name.endswith('xlsx') else pd.read_csv(f2)
                
                st.session_state.rto_df_app = df2.copy()
                res_ds, res_selisih = engine_ds_rto_vba_total(df1, df2)
                
                st.session_state.rto_df_ds = res_ds
                st.session_state.rto_df_selisih = res_selisih
                
                st.success("✅ Proses Awal Selesai!")
    
    # --- TAMPILKAN HASIL AWAL ---
    if st.session_state.rto_df_selisih is not None:
        st.divider()
        st.subheader("📊 HASIL COMPARE AWAL (DS vs APPSHEET)")
        
        total_rows = len(st.session_state.rto_df_selisih)
        match_count = len(st.session_state.rto_df_ds[st.session_state.rto_df_ds['NOTE'] == 'SESUAI']) if 'NOTE' in st.session_state.rto_df_ds.columns else 0
        lebih_count = len(st.session_state.rto_df_ds[st.session_state.rto_df_ds['NOTE'] == 'KELEBIHAN AMBIL']) if 'NOTE' in st.session_state.rto_df_ds.columns else 0
        kurang_count = len(st.session_state.rto_df_ds[st.session_state.rto_df_ds['NOTE'] == 'KURANG AMBIL']) if 'NOTE' in st.session_state.rto_df_ds.columns else 0
        
        mc1, mc2, mc3, mc4 = st.columns(4)
        with mc1:
            st.markdown(f'<div class="m-box"><span class="m-lbl">Total Rows</span><span class="m-val">{total_rows}</span></div>', unsafe_allow_html=True)
        with mc2:
            st.markdown(f'<div class="m-box"><span class="m-lbl">SESUAI</span><span class="m-val">{match_count}</span></div>', unsafe_allow_html=True)
        with mc3:
            st.markdown(f'<div class="m-box"><span class="m-lbl">KELEBIHAN</span><span class="m-val">{lebih_count}</span></div>', unsafe_allow_html=True)
        with mc4:
            st.markdown(f'<div class="m-box"><span class="m-lbl">KURANG</span><span class="m-val">{kurang_count}</span></div>', unsafe_allow_html=True)
        
        st.dataframe(st.session_state.rto_df_selisih, use_container_width=True, hide_index=True)
        
        csv_selisih = st.session_state.rto_df_selisih.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Sheet Selisih", csv_selisih, "SELISIH_RTO.csv", "text/csv", use_container_width=True)

    st.divider()
    
    # --- REFRESH DATA (SETELAH CEK REAL) ---
    st.subheader("🔄 REFRESH DATA (SETELAH CEK REAL)")
    f_cek = st.file_uploader("📥 Upload File Hasil Cek Real (isian dari Sheet Selisih)", type=['xlsx','csv'], key="rto_cek")
    
    if f_cek and st.session_state.rto_df_app is not None:
        if st.button("🔄 REFRESH DATA", use_container_width=True):
            with st.spinner("Memproses Refresh..."):
                df_cek = pd.read_excel(f_cek) if f_cek.name.endswith('xlsx') else pd.read_csv(f_cek)
                
                ds_refreshed, app_refreshed = engine_refresh_rto(
                    st.session_state.rto_df_ds,
                    st.session_state.rto_df_app,
                    df_cek
                )
                
                st.session_state.rto_df_ds = ds_refreshed
                st.session_state.rto_df_app = app_refreshed
                
                st.success("✅ Refresh Selesai!")

    st.divider()
    
    # --- COMPARE DRAFT JEZPRO ---
    st.subheader("📝 COMPARE DRAFT JEZPRO")
    
    # Upload Draft + Appsheet (sudah diupload di atas)
    if f2:
        f_draft = st.file_uploader("📥 Upload DRAFT JEZPRO", type=['xlsx','csv'], key="rto_draft_jezpro")
        
        if f_draft and st.session_state.rto_df_app is not None:
            if st.button("🔍 COMPARE DRAFT JEZPRO", use_container_width=True):
                with st.spinner("Memproses..."):
                    df_draft = pd.read_excel(f_draft) if f_draft.name.endswith('xlsx') else pd.read_csv(f_draft)
                    
                    # Panggil engine compare draft
                    df_compared = engine_compare_draft_jezpro(st.session_state.rto_df_app, df_draft)
                    st.session_state.rto_draft_compared = df_compared
                    
                    st.success("✅ Compare Draft Selesai!")
    
    # Tampilkan hasil compare draft
    if st.session_state.rto_draft_compared is not None:
        st.divider()
        st.subheader("📊 HASIL COMPARE DRAFT JEZPRO")
        
        # Metrics
        total_draft = len(st.session_state.rto_draft_compared)
        ok_count = len(st.session_state.rto_draft_compared[st.session_state.rto_draft_compared['STATUS'] == 'OK']) if 'STATUS' in st.session_state.rto_draft_compared.columns else 0
        perlu_edit = len(st.session_state.rto_draft_compared[st.session_state.rto_draft_compared['STATUS'].str.contains('EDIT', na=False)]) if 'STATUS' in st.session_state.rto_draft_compared.columns else 0
        delete_count = len(st.session_state.rto_draft_compared[st.session_state.rto_draft_compared['STATUS'] == 'DELETE ITEM']) if 'STATUS' in st.session_state.rto_draft_compared.columns else 0
        
        dc1, dc2, dc3, dc4 = st.columns(4)
        with dc1:
            st.markdown(f'<div class="m-box"><span class="m-lbl">Total Draft</span><span class="m-val">{total_draft}</span></div>', unsafe_allow_html=True)
        with dc2:
            st.markdown(f'<div class="m-box"><span class="m-lbl">OK</span><span class="m-val">{ok_count}</span></div>', unsafe_allow_html=True)
        with dc3:
            st.markdown(f'<div class="m-box"><span class="m-lbl">Perlu Edit</span><span class="m-val">{perlu_edit}</span></div>', unsafe_allow_html=True)
        with dc4:
            st.markdown(f'<div class="m-box"><span class="m-lbl">Delete</span><span class="m-val">{delete_count}</span></div>', unsafe_allow_html=True)
        
        st.dataframe(st.session_state.rto_draft_compared, use_container_width=True, hide_index=True)
        
        csv_draft = st.session_state.rto_draft_compared.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Draft Compared", csv_draft, "DRAFT_COMPARED.csv", "text/csv", use_container_width=True)

    st.divider()
    
    # --- GENERATE NEW DRAFT ---
    st.subheader("🏁 GENERATE NEW DRAFT")
    
    if st.session_state.rto_draft_compared is not None:
        if st.button("🏁 GENERATE NEW DRAFT", use_container_width=True):
            with st.spinner("Memproses..."):
                new_draft = engine_generate_new_draft(st.session_state.rto_draft_compared)
                st.session_state.rto_new_draft = new_draft
                
                total_qty = int(new_draft['QUANTITY'].sum()) if not new_draft.empty else 0
                
                st.success(f"✅ Generate Selesai! Total: {total_qty} Pcs")
                st.dataframe(new_draft, use_container_width=True, hide_index=True)
                
                csv_new = new_draft.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download New Draft", csv_new, "NEW_DRAFT_RTO.csv", "text/csv", use_container_width=True)

## MENU: FDR UPDATE (YANG DIPERBAIKI & LENGKAP)
# =====================================================
# =========================================================
# 3. MENU: FDR UPDATE (DENGAN TOMBOL RUN)
# =========================================================
elif menu == "FDR Update":
    # --- CSS & HEADER ---
    st.markdown('<div class="hero-header"><h1>🚚 FDR UPDATE - MANIFEST CHECKER</h1></div>', unsafe_allow_html=True)
    
    st.markdown("""
        <style>
        .m-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; text-align: center; margin: 5px 0; }
        .m-lbl { display: block; font-size: 14px; color: #555; font-weight: bold; }
        .m-val { display: block; font-size: 24px; color: #ff4b4b; font-weight: bold; }
        </style>
    """, unsafe_allow_html=True)
    
    # --- INIT STATE ---
    if "ws_manifest_fdr" not in st.session_state: st.session_state.ws_manifest_fdr = None
    if "ws_fu_it_fdr" not in st.session_state: st.session_state.ws_fu_it_fdr = None
    if "dict_kurir_fdr" not in st.session_state: st.session_state.dict_kurir_fdr = {}
    if "fdr_current_file" not in st.session_state: st.session_state.fdr_current_file = None
    if "metrics_data" not in st.session_state: st.session_state.metrics_data = {}

    # --- FILE UPLOAD ---
    u_file = st.file_uploader("📂 Upload File Manifest", type=["xlsx"], key="fdr_upload_fix")

    # --- TOMBOL RUN UTAMA ---
    # Hanya aktif jika ada file dan tombol ditekan
    if u_file:
        if st.button("▶️PROCESS DATA", type="primary", use_container_width=True):
            try:
                with st.spinner("🔄 Processing..."):
                    # 1. Load & Clear Columns
                    df_raw = pd.read_excel(u_file)
                    cols_idx = [6, 7, 8, 10, 11, 12, 17, 18, 19, 20, 21, 22]
                    existing_cols = [df_raw.columns[i] for i in cols_idx if i < len(df_raw.columns)]
                    df_clean = df_raw.drop(columns=existing_cols) if existing_cols else df_raw.copy()
                    
                    st.session_state.ws_manifest_fdr = df_clean

                    # 2. FU IT Logic (Kolom M Index 12 tidak kosong)
                    if len(df_clean.columns) > 12:
                        mask_fu = df_clean.iloc[:, 12].astype(str).str.strip().replace(['nan', 'None'], '') != ""
                        st.session_state.ws_fu_it_fdr = df_clean[mask_fu].iloc[:, 0:13]
                    else:
                        st.session_state.ws_fu_it_fdr = pd.DataFrame()

                    # 3. Split Kurir Logic (Kolom F Index 5 ada, Kolom M Index 12 kosong)
                    if len(df_clean.columns) > 12:
                        f_val = df_clean.iloc[:, 5].astype(str).str.strip().replace(['nan', 'None'], '')
                        m_val = df_clean.iloc[:, 12].astype(str).str.strip().replace(['nan', 'None'], '')
                        mask_out = (f_val != "") & (m_val == "")
                        filtered_out = df_clean[mask_out].copy()
                        
                        if not filtered_out.empty:
                            st.session_state.dict_kurir_fdr = {str(n): g.iloc[:, 0:13] for n, g in filtered_out.groupby(filtered_out.iloc[:, 5])}
                        else:
                            st.session_state.dict_kurir_fdr = {}
                    
                    # 4. Metrics
                    st.session_state.metrics_data = {
                        'total': len(st.session_state.ws_manifest_fdr),
                        'fu': len(st.session_state.ws_fu_it_fdr) if st.session_state.ws_fu_it_fdr is not None else 0,
                        'kurir': len(st.session_state.dict_kurir_fdr)
                    }
                    
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error saat proses: {e}")

    # --- TAMPILKAN HASIL & METRICS ---
    if st.session_state.ws_manifest_fdr is not None:
        m = st.session_state.metrics_data
        
        st.markdown(f"""
        <div style="display: flex; gap: 10px; justify-content: center; margin-bottom: 20px;">
            <div class="m-box" style="flex:1"><span class="m-lbl">TOTAL MANIFEST</span><span class="m-val">{m.get('total', 0)}</span></div>
            <div class="m-box" style="flex:1"><span class="m-lbl">FU IT</span><span class="m-val" style="color:#FFA500">{m.get('fu', 0)}</span></div>
            <div class="m-box" style="flex:1"><span class="m-lbl">KURIR</span><span class="m-val" style="color:#FF4B4B">{m.get('kurir', 0)}</span></div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🗑️ RESET DATA"): 
            st.session_state.ws_manifest_fdr = None
            st.session_state.dict_kurir_fdr = {}
            st.rerun()

        t1, t2, t3 = st.tabs(["📥 MANIFEST", "📋 FU IT", "🛵 KURIR"])

        with t1:
            st.dataframe(st.session_state.ws_manifest_fdr, use_container_width=True, hide_index=True)

        with t2:
            if st.session_state.ws_fu_it_fdr is not None:
                st.download_button("📥 Download FU IT", st.session_state.ws_fu_it_fdr.to_csv(index=False).encode('utf-8'), "FU_IT.csv", "text/csv")
                st.dataframe(st.session_state.ws_fu_it_fdr, use_container_width=True, hide_index=True)

        with t3:
            if st.session_state.dict_kurir_fdr:
                opt = st.selectbox("Pilih Kurir", list(st.session_state.dict_kurir_fdr.keys()))
                
                # Download All Excel
                import io
                buff = io.BytesIO()
                with pd.ExcelWriter(buff, engine='xlsxwriter') as w:
                    for n, d in st.session_state.dict_kurir_fdr.items(): d.to_excel(w, sheet_name=str(n)[:31], index=False)
                st.download_button("📊 Download All Excel", buff.getvalue(), "All.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                
                # Download Selected
                if opt:
                    st.download_button(f"📥 {opt}", st.session_state.dict_kurir_fdr[opt].to_csv(index=False).encode('utf-8'), f"{opt}.csv", "text/csv")
                    st.dataframe(st.session_state.dict_kurir_fdr[opt], use_container_width=True, hide_index=True)

elif menu == "Refill & Withdraw":
    menu_refill_withdraw()

# --- Navigasi ---
elif menu == "Stock Opname":
    menu_Stock_Opname()