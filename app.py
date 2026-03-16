import pandas as pd
import numpy as np
import streamlit as st
import io
import math

import pandas as pd
from collections import defaultdict


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
import pandas as pd
import numpy as np
import math


import pandas as pd
import streamlit as st
import io
import openpyxl
from openpyxl import load_workbook

import streamlit as st
import pandas as pd
import io
from openpyxl import load_workbook
import re
from collections import defaultdict


import pandas as pd
import streamlit as st
import io
from openpyxl import load_workbook
from collections import defaultdict

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
            if color in ['FFFF0000', 'FFFFFF00', 'FFFF00', '00FFFF00']:
                sku_val = str(cell.value).strip().upper() if cell.value else ""
                if sku_val: yellow_set.add(sku_val)
    except: pass
    return yellow_set

def logic_cek_adjustment_final(df_recon, df_stock_adj):
    df_stock = df_stock_adj.copy()
    
    def clean_val(x):
        if pd.isna(x): return ""
        s = str(x).strip().upper()
        if s.endswith('.0'): s = s[:-2]
        return s

    # 1. Ambil daftar SEMUA SKU yang ada di Stock Report
    # Kita gunakan set SKU agar lookup-nya cepat
    skus_in_stock = set(df_stock.iloc[:, 2].apply(clean_val))

    recon_dict = {}
    all_recon_keys = set()
    for _, row in df_recon.iterrows():
        try:
            qty_so = pd.to_numeric(row.iloc[6], errors='coerce') or 0
            if qty_so > 0:
                # Key tetap BIN|SKU untuk keperluan mapping QTY SO ke baris yang spesifik
                k = f"{clean_val(row.iloc[0])}|{clean_val(row.iloc[1])}"
                recon_dict[k] = row.iloc[6]
                all_recon_keys.add(k)
        except: continue

    while df_stock.shape[1] < 12:
        df_stock[f"Extra_{df_stock.shape[1]}"] = ""

    used_keys = set()
    def do_lookup(row):
        key_stock = f"{clean_val(row.iloc[1])}|{clean_val(row.iloc[2])}"
        if key_stock in recon_dict:
            used_keys.add(key_stock)
            return recon_dict[key_stock]
        return ""

    # Isi QTY SO ke Kolom K
    df_stock.iloc[:, 10] = df_stock.apply(do_lookup, axis=1)

    # Hitung DIFF ke Kolom L
    def do_diff(row):
        try:
            val_sys = row.iloc[9]
            val_so = row.iloc[10]
            if val_so != "" and val_so is not None:
                return abs(float(val_sys) - float(val_so))
        except: return 0
        return ""

    df_stock.iloc[:, 11] = df_stock.apply(do_diff, axis=1)
    
    cols = list(df_stock.columns)
    cols[10] = "QTY SO"
    cols[11] = "DIFF"
    df_stock.columns = cols

    # --- PERBAIKAN LOGIC SINGLE (BERBASIS SKU) ---
    # Item masuk Single ADJ HANYA JIKA SKU-nya tidak ada sama sekali di daftar skus_in_stock
    def check_is_single(row):
        sku_recon = clean_val(row.iloc[1])
        qty_recon = pd.to_numeric(row.iloc[6], errors='coerce') or 0
        # Syarat: Qty > 0 DAN SKU-nya tidak ada di file Stock
        return qty_recon > 0 and sku_recon not in skus_in_stock

    df_need_single = df_recon[df_recon.apply(check_is_single, axis=1)].copy()
    
    return df_stock, df_need_single

def logic_pivot_adjustment(df_stock_final, df_adj_plus_master, df_recon_missing):
    # Logika Multiple tetap (SO > SYS)
    df_filtered = df_stock_final.copy()
    df_filtered.iloc[:, 9] = pd.to_numeric(df_filtered.iloc[:, 9], errors='coerce').fillna(0)
    df_filtered.iloc[:, 10] = pd.to_numeric(df_filtered.iloc[:, 10], errors='coerce').fillna(0)
    df_filtered.iloc[:, 11] = pd.to_numeric(df_filtered.iloc[:, 11], errors='coerce').fillna(0)
    
    mask_multiple = df_filtered.iloc[:, 10] > df_filtered.iloc[:, 9]
    df_to_pivot = df_filtered[mask_multiple].copy()
    
    pivot_multiple = df_to_pivot.groupby(df_to_pivot.columns[2])[df_to_pivot.columns[11]].sum().reset_index()
    pivot_multiple.columns = ['SKU_KEY', 'TOTAL_DIFF']
    
    master_clean = df_adj_plus_master.drop_duplicates(subset=[df_adj_plus_master.columns[2]])
    df_multiple_final = pivot_multiple.merge(master_clean, left_on='SKU_KEY', right_on=master_clean.columns[2], how='left')
    
    if not df_multiple_final.empty:
        df_multiple_final.iloc[:, -1] = df_multiple_final['TOTAL_DIFF']
        if 'SKU_KEY' in df_multiple_final.columns: 
            df_multiple_final = df_multiple_final.drop(columns=['SKU_KEY', 'TOTAL_DIFF'])

    # Logika Single Final
    if not df_recon_missing.empty:
        df_recon_missing.iloc[:, 6] = pd.to_numeric(df_recon_missing.iloc[:, 6], errors='coerce').fillna(0)
        df_recon_missing = df_recon_missing[df_recon_missing.iloc[:, 6] > 0]
        
        if not df_recon_missing.empty:
            df_single_final = df_recon_missing.groupby([df_recon_missing.columns[0], df_recon_missing.columns[1]])[df_recon_missing.columns[6]].sum().reset_index()
            df_single_final.columns = ['BIN', 'SKU', 'QTY ADJ']
        else:
            df_single_final = pd.DataFrame(columns=['BIN', 'SKU', 'QTY ADJ'])
    else:
        df_single_final = pd.DataFrame(columns=['BIN', 'SKU', 'QTY ADJ'])
        
    return df_multiple_final, df_single_final
def logic_setup_real_plus(df_stock_final, df_multiple_adj_plus):
    def clean_val(x):
        if pd.isna(x): return ""
        s = str(x).strip().upper()
        # Sesuai preferensi user: hapus prefix SPE jika ada agar matching
        if s.startswith("SPE"): s = s[3:] 
        if s.endswith('.0'): s = s[:-2]
        return s

    # 1. Dictionary dari MULTIPLE ADJ + (VBA Step 3)
    dict_multi = {}
    if not df_multiple_adj_plus.empty:
        for _, row in df_multiple_adj_plus.iterrows():
            # VBA: SKU di Kolom C (Index 2), BIN di Kolom B (Index 1)
            sku = clean_val(row.iloc[2])
            bin_asal = row.iloc[1]
            if sku != "" and sku not in dict_multi:
                dict_multi[sku] = bin_asal

    # 2. Ambil Data Stock Final (VBA Step 4 & 5)
    df_stock = df_stock_final.copy()
    
    # Pastikan tipe data numerik untuk perbandingan
    # Kolom 10 (Index 9) = QTY SYSTEM
    # Kolom 11 (Index 10) = QTY SO
    # Kolom 12 (Index 11) = DIFF
    qty_system = pd.to_numeric(df_stock.iloc[:, 9], errors='coerce').fillna(0)
    qty_so = pd.to_numeric(df_stock.iloc[:, 10], errors='coerce').fillna(0)
    diff_val = pd.to_numeric(df_stock.iloc[:, 11], errors='coerce').fillna(0)

    setup_real_data = []
    
    for i in range(len(df_stock)):
        # SYARAT: QTY SO > QTY SYSTEM
        if qty_so.iloc[i] > qty_system.iloc[i]:
            sku_key = clean_val(df_stock.iloc[i, 2]) # SKU Kolom C
            
            # LOGIC TAMBAHAN: ABAIKAN JIKA SKU TIDAK ADA DI FILE MULTIPLE (TIDAK ADA NOT FOUND)
            if sku_key in dict_multi:
                setup_real_data.append({
                    "BIN AWAL": dict_multi[sku_key],
                    "BIN TUJUAN": df_stock.iloc[i, 1], # Kolom B
                    "SKU": sku_key,
                    "QUANTITY": diff_val.iloc[i],     # Kolom L
                    "NOTES": "RELOCATION"             # Sesuai request
                })

    # Return DataFrame dengan susunan kolom sesuai Header VBA
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
    karantina_results = []

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
    
def logic_compare_scan_to_stock(df_scan, df_stock):
    ds = df_scan.iloc[:, [0, 1, 2]].copy()
    ds.columns = ['BIN', 'SKU', 'QTY_SCAN']
    dt = df_stock.iloc[:, [1, 2, 9]].copy()
    dt.columns = ['BIN', 'SKU', 'QTY_SYSTEM']
    for df in [ds, dt]:
        df['BIN'] = df['BIN'].astype(str).str.strip().str.upper()
        df['SKU'] = df['SKU'].astype(str).str.strip().str.upper()
    dt_grouped = dt.groupby(['BIN', 'SKU'])['QTY_SYSTEM'].sum().reset_index()
    ds_merged = ds.merge(dt_grouped, on=['BIN', 'SKU'], how='left').fillna(0)
    ds_merged['DIFF'] = ds_merged['QTY_SCAN'] - ds_merged['QTY_SYSTEM']
    ds_merged['NOTE'] = ds_merged['DIFF'].apply(lambda x: "REAL +" if x > 0 else "OK")
    return ds_merged

def logic_compare_stock_to_scan(df_stock, df_scan):
    dt = df_stock.copy()
    ds = df_scan.iloc[:, [0, 1, 2]].copy()
    ds.columns = ['BIN_SCAN', 'SKU_SCAN', 'QTY_TOTAL_SCAN']
    ds['BIN_SCAN'] = ds['BIN_SCAN'].astype(str).str.strip().str.upper()
    ds['SKU_SCAN'] = ds['SKU_SCAN'].astype(str).str.strip().str.upper()
    ds_grouped = ds.groupby(['BIN_SCAN', 'SKU_SCAN'])['QTY_TOTAL_SCAN'].sum().reset_index()
    col_bin_sys = dt.columns[1]
    col_sku_sys = dt.columns[2]
    col_qty_sys = dt.columns[9]
    col_qty_so  = dt.columns[10] 
    dt[col_bin_sys] = dt[col_bin_sys].astype(str).str.strip().str.upper()
    dt[col_sku_sys] = dt[col_sku_sys].astype(str).str.strip().str.upper()
    dt_merged = dt.merge(ds_grouped, left_on=[col_bin_sys, col_sku_sys], right_on=['BIN_SCAN', 'SKU_SCAN'], how='left')
    dt_merged[col_qty_so] = dt_merged['QTY_TOTAL_SCAN'].fillna(0)
    dt_merged['DIFF'] = dt_merged[col_qty_sys] - dt_merged[col_qty_so]
    dt_merged['NOTE'] = dt_merged['DIFF'].apply(lambda x: "SYSTEM +" if x > 0 else "OK")
    return dt_merged.drop(columns=['BIN_SCAN', 'SKU_SCAN', 'QTY_TOTAL_SCAN'])


def logic_run_allocation(df_real_plus, df_system_plus, df_bin_coverage):
    # 1. Siapkan data sumber dalam dictionary
    system_dict = {}
    for _, row in df_system_plus.iterrows():
        key = (str(row['BIN']).strip().upper(), str(row['SKU']).strip().upper())
        system_dict[key] = system_dict.get(key, 0) + row.get('DIFF', 0)
    
    coverage_dict = {}
    for _, row in df_bin_coverage.iterrows():
        # Asumsi kolom: index 1=BIN, index 2=SKU, index 9=QTY
        key = (str(row.iloc[1]).strip().upper(), str(row.iloc[2]).strip().upper())
        try: val = float(row.iloc[9])
        except: val = 0
        coverage_dict[key] = coverage_dict.get(key, 0) + val

    # 2. List untuk menampung baris baru
    new_rows = []
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
                
                # Buat baris baru untuk alokasi ini
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

        # --- TAHAP 2: Cari di Coverage Dictionary (Jika masih sisa) ---
        if remaining > 0:
            for (bin_src, sku_src), qty_avail in coverage_dict.items():
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
                    
                    coverage_dict[(bin_src, sku_src)] -= alloc
                    remaining -= alloc

        # --- TAHAP 3: Jika Masih Sisa (NO ALLOCATION) ---
        if remaining > 0:
            row_no = row.to_dict()
            row_no.update({
                'DIFF': remaining, # Sisa yang tidak teralokasi
                'BIN ALOKASI': '',
                'QTY ALLOCATION': 0,
                'STATUS': 'NO ALLOCATION'
            })
            new_rows.append(row_no)

    # 3. Convert kembali ke DataFrame
    df_result = pd.DataFrame(new_rows)

    # 4. Update df_sys_updated (Logika pengurangan DIFF di system)
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
    cols_header = [
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
        "METRIC": [
            "Total SKU Adj.", "Total Value Adj. +", "Total Value Adj. -", 
            "Total QTY Adj. +", "Total QTY Adj. -", "Total Value", "Total QTY"
        ],
        "VALUE": [
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
        list_sub_kat = ["GYM&SWIM", "SZ SOCKS", "SZ EQUIPMENT", "JZ EQUIPMENT", "OTHER ACC", "SOCKS", "OTHER EQP", "SHOES", "LOWER BODY", "UPPER BODY", "BALL", "EQUIPMENT SPORT", "SHIRT", "ALL BASELAYER", "JACKET", "SET APPAREL", "JERSEY", "PANTS", "SANDALS", "BASELAYER", "OTHERS", "UKNOWN SC", "NUTRITION", "BAG", "EXTRAS SHOES"]
        selected_sub = st.multiselect("🗂️ Sub Kategori:", list_sub_kat)
    with col_f2:
        list_bin_stock = ["GUDANG LT.2", "LIVE", "KL2", "KL1", "GL2-STORE", "OFFLINE", "TOKO", "GL1-DC", "RAK ACC LT.1", "GL3-DC-A", "GL3-DC-B", "GL3-DC-C", "GL3-DC-D", "GL3-DC-E", "GL3-DC-F", "GL3-DC-G", "GL3-DC-H", "GL3-DC-I", "GL3-DC-J", "GL4-DC-A", "GL4-DC-B", "GL4-DC-KL", "GL3-DC-RAK", "GL4-DC-RAK", "KEEP AMP", "MARKOM", "DEFECT", "REJECT", "DAU", "KAV-2", "KAV-7", "KAV-8", "KAV-9", "KAV-10", "C-0", "KDR", "JBR", "GUDANG", "SDA", "SMG"]
        selected_bin_sys = st.multiselect("🏭 BIN System:", list_bin_stock)
    with col_f3:
        list_bin_cov = ["KARANTINA", "STAGGING", "STAGING", "GUDANG LT.2", "TOKO", "GL1-DC", "RAK ACC LT.1", "GL3-DC-A", "GL3-DC-B", "GL3-DC-C", "GL3-DC-D", "GL3-DC-E", "GL3-DC-F", "GL3-DC-G", "GL3-DC-H", "GL3-DC-I", "GL3-DC-J", "GL4-DC-A", "GL4-DC-B", "GL4-DC-KL1", "GL4-DC-KL2", "GL3-DC-RAK", "GL4-DC-RAK", "LIVE", "MARKOM", "AMP", "GL2-STORE"]
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
            if selected_bin_cov: df_s_raw = df_s_raw[df_s_raw.iloc[:, 0].astype(str).str.upper().apply(lambda x: any(c.upper() in x for c in selected_bin_cov))]

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
                df_cov = pd.read_excel(up_bin_cov) if up_bin_cov.name.endswith(('.xlsx', '.xls')) else pd.read_csv(up_bin_cov)
                allocated, sys_upd = logic_run_allocation(d['real_plus'], d['system_plus'], df_cov)
                allocated['ITEM NAME'] = allocated['SKU'].map(d['map_dict'])
                st.session_state.allocation_result = allocated
                st.session_state.sys_updated_result = sys_upd
                st.session_state.set_up_real_plus = generate_set_up_real_plus(allocated)
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
            up_m5 = st.file_uploader("3️⃣ STOCK ADJ + (MASTER)", type=['xlsx'], key="u_m_final_fix")

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
                    st.session_state.process_done = True
                    
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Terjadi Kesalahan: {str(e)}")

        # --- AREA TAMPILAN HASIL ---
        if st.session_state.get("process_done"):
            # Cek apakah hasil lookup beneran ada isinya
            check_data = st.session_state.df_res4_final
            is_empty = check_data['QTY SO'].replace('', 0).astype(float).sum() == 0
            
            if is_empty:
                st.warning("⚠️ Hasil Lookup Kosong! Pastikan format BIN dan SKU di kedua file sama persis.")
            else:
                st.success("✅ Analisis Selesai!")
            
            t1, t2, t3, t4 = st.tabs(["📦 MULTIPLE ADJ +", "⚠️ SINGLE ADJ +", "🔍 CEK ADJ + RESULT", "➡️ SET UP REAL +"])
            
            with t1:
                st.dataframe(st.session_state.df_mult_final, use_container_width=True, hide_index=True)
                if not st.session_state.df_mult_final.empty:
                    st.download_button("📥 Download Multiple Adj +", st.session_state.df_mult_final.to_csv(index=False).encode('utf-8'), "final_adj_multiple.csv", "text/csv", key="dl_mult_final")
            
            with t2:
                st.dataframe(st.session_state.df_sing_final, use_container_width=True, hide_index=True)
                if not st.session_state.df_sing_final.empty:
                    st.download_button("📥 Download Single Adj +", st.session_state.df_sing_final.to_csv(index=False).encode('utf-8'), "final_adj_single.csv", "text/csv", key="dl_sing_final")
            
            with t3:
                # Tampilkan hasil lookup biar lu bisa cek kolom K (QTY SO)
                st.dataframe(st.session_state.df_res4_final, use_container_width=True, hide_index=True)
                st.download_button("📥 Download Hasil Cek Adj +", st.session_state.df_res4_final.to_csv(index=False).encode('utf-8'), "hasil_lookup_full.csv", "text/csv", key="dl_res4_final")

            with t4:
                # Ambil data dari session state hasil running sebelumnya
                df_m_src = st.session_state.get("df_mult_final")
                df_s_res = st.session_state.get("df_res4_final")

                st.info("➡️ Running Relocation Inbound Setelah Running Process Selesai.")

                # Tombol Terpisah hanya untuk Set Up Real +
                if st.button("▶️ GENERATE SET UP REAL +", use_container_width=True, key="btn_gen_real_plus"):
                    if df_m_src is not None and df_s_res is not None:
                        try:
                            # Jalankan fungsi logic yang sudah kita perbaiki tadi
                            df_real = logic_setup_real_plus(df_s_res, df_m_src)
                            
                            # Simpan hasil ke session state agar tidak hilang saat pindah tab
                            st.session_state.df_setup_real_final = df_real
                            st.success("✅ Mutasi Berhasil Dibuat!")
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
    # =========================================================
    # ⚙️ 6. SET UP KARANTINA GENERATOR (DI DALAM FUNGSI MENU)
    # =========================================================
    st.markdown("<br><br><br>---", unsafe_allow_html=True)
    st.subheader("5️⃣ SET UP KARANTINA GENERATOR")

    # Tambahkan dua uploader agar logic compare BIN|SKU bisa jalan
    col_k1, col_k2 = st.columns(2)
    with col_k1:
        up_k6 = st.file_uploader("📥 1. Upload SYSTEM + OUTSTANDING RECON", type=['xlsx', 'xls', 'csv'], key="u6_karantina")
    with col_k2:
        up_adj6 = st.file_uploader("📥 2. Upload HASIL CEK ADJUSTMENT (RECON)", type=['xlsx', 'xls', 'csv'], key="u6_adj_compare")

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
            "VALUE": [m_sku_val, m_qty_val]
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
        df_p = st.session_state.get('df_mult_final')
    
        if df_p is not None:
        # LOGIC HYBRID: Baca upload jika ada, kalau gak ada baru pake data current aplikasi
            df_p_in = pd.read_excel(up_plus) if up_plus else df_p
        
            df_m_in = None
            if up_minus:
                df_m_in = pd.read_excel(up_minus) if up_minus.name.endswith('.xlsx') else pd.read_csv(up_minus)
        
        # Panggil fungsi logic dengan data yang sudah difilter
            df_res, df_summary = logic_sum_adjustment_final(df_p_in, df_m_in)
        
            st.session_state.report_adj = {"data": df_res, "sum": df_summary}
            st.success("✅ Summary Adjustment Berhasil Dibuat!")
            st.rerun()

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
            with [q1, q2, q3][i]:
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
            st.info("💡 **Master Report Ready:** File ini mencakup SEMUA data dari Step 1 sampai Step 5.")
            
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

import pandas as pd
import numpy as np
import streamlit as st

# =========================================================
# ⚙️ 1. DEFINISI SEMUA ENGINE (LOGIKA TETAP SAMA)
# =========================================================

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
        if s in ["NAN", "0", "NONE", ""]: return ""
        return s

    df_a = df_app.copy()
    # Mengubah nama kolom menjadi string untuk memudahkan akses
    df_a.columns = [str(i) for i in range(1, len(df_a.columns) + 1)]
    
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
            if sku in ["", "NAN", "0", "NONE"]: sku = str(df_app_res.iloc[idx, 14]).strip().upper()
            b1, b2 = str(df_app_res.iloc[idx, 11]).strip().upper(), str(df_app_res.iloc[idx, 15]).strip().upper()
            target_qty = real_map.get(f"{sku}|{b1}") if f"{sku}|{b1}" in real_map else real_map.get(f"{sku}|{b2}")
            if target_qty is not None:
                val_n = str(df_app_res.iloc[idx, 13]).strip()
                if val_n == "" or val_n.lower() == "nan": df_app_res.iloc[idx, 12] = target_qty
                else: df_app_res.iloc[idx, 16] = target_qty
        except: continue

    if not df_ds_res.empty:
        df_app_res['TMP_SKU'] = df_app_res.apply(lambda r: str(r.iloc[8]).strip().upper() if str(r.iloc[8]).strip() not in ["","0","nan"] else str(r.iloc[14]).strip().upper(), axis=1)
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
    df_a.columns = [str(i) for i in range(1, len(df_a.columns) + 1)]
    
    def clean_sku(val):
        if pd.isna(val): return ""
        s = str(val).strip().upper()
        if s.endswith('.0'): s = s[:-2]
        return s if s not in ["NAN", "0", "NONE"] else ""

    # --- 1. REKAP DATA APPSHEET ---
    app_summary = {} # Kunci: (SKU, BIN) -> Value: QTY
    sku_to_bins = {} # Kunci: SKU -> Value: List of (BIN, QTY) untuk lacak pindah BIN

    for _, r in df_a.iterrows():
        # Ambil Pasangan 1 (I & M)
        s1 = clean_sku(r.get('9'))
        b1 = str(r.get('12', '')).strip().upper()
        q1 = pd.to_numeric(r.get('13', 0), errors='coerce') or 0
        
        if s1 and b1 not in ["", "0", "NAN"]:
            app_summary[(s1, b1)] = app_summary.get((s1, b1), 0) + q1
            if s1 not in sku_to_bins: sku_to_bins[s1] = []
            sku_to_bins[s1].append((b1, q1))

        # Ambil Pasangan 2 (O & Q)
        s2_raw = clean_sku(r.get('15'))
        s2 = s2_raw if s2_raw else s1 # Jika O kosong pakai SKU I
        b2 = str(r.get('16', '')).strip().upper()
        q2 = pd.to_numeric(r.get('17', 0), errors='coerce') or 0
        
        if s2 and b2 not in ["", "0", "NAN"]:
            app_summary[(s2, b2)] = app_summary.get((s2, b2), 0) + q2
            if s2 not in sku_to_bins: sku_to_bins[s2] = []
            sku_to_bins[s2].append((b2, q2))

    # --- 2. UPDATE ITEM DI DRAFT ---
    matched_app_keys = set()
    sku_in_draft = set() # Catat SKU apa saja yang sudah ada di Draft

    for idx, row in df_res.iterrows():
        sku_d = clean_sku(row.iloc[3])
        bin_d = str(row.iloc[8]).strip().upper()
        qty_h = pd.to_numeric(row.iloc[7], errors='coerce') or 0
        sku_in_draft.add(sku_d)
        
        key_d = (sku_d, bin_d)
        qty_j, bin_lain, qty_lain = 0, "", ""
        note, status = "", ""
        
        # A. MATCH SEMPURNA (SKU & BIN sama)
        if key_d in app_summary:
            qty_j = app_summary[key_d]
            matched_app_keys.add(key_d)
            if qty_j == qty_h:
                note, status = "DRAFT SESUAI", "OK"
            else:
                note, status = "BEDA QTY", "PERLU EDIT QTY DRAFT"
        
        # B. SKU ADA TAPI BIN BEDA (Ambil data dari BIN lain di AppSheet)
        elif sku_d in sku_to_bins:
            status = "PERLU EDIT BIN DRAFT"
            note = "PINDAH BIN"
            # Ambil detail BIN dan QTY dari AppSheet untuk diinfokan di kolom 'LAIN'
            details = sku_to_bins[sku_d]
            bin_lain = ", ".join([str(d[0]) for d in details])
            qty_lain = sum([d[1] for d in details])
            qty_j = 0 # Di BIN draft aslinya tidak ada pengambilan
            
            # Tandai agar tidak masuk ADD NEW
            for b_a, q_a in details:
                matched_app_keys.add((sku_d, b_a))
            
        # C. TIDAK ADA DI APPSHEET SAMA SEKALI
        else:
            qty_j = 0
            note, status = "HAPUS ITEM INI", "DELETE ITEM"

        df_res.loc[idx, ['QTY AMBIL', 'NOTE', 'BIN AMBIL LAIN', 'QTY BIN LAIN', 'STATUS']] = \
            [qty_j, note, bin_lain, qty_lain, status]

    # --- 3. TAMBAHKAN ITEM BARU (ADD NEW) ---
    new_rows = []
    for (sku_a, bin_a), qty_a in app_summary.items():
        if (sku_a, bin_a) not in matched_app_keys and sku_a not in sku_in_draft:
            new_entry = {col: "" for col in df_res.columns}
            new_entry[df_res.columns[0]] = "-" 
            new_entry[df_res.columns[3]] = sku_a 
            new_entry[df_res.columns[7]] = 0     
            new_entry[df_res.columns[8]] = bin_a 
            new_entry['QTY AMBIL'] = qty_a
            new_entry['NOTE'] = "TAMBAH ITEM BARU"
            new_entry['STATUS'] = "ADD NEW"
            new_rows.append(new_entry)

    if new_rows:
        df_res = pd.concat([df_res, pd.DataFrame(new_rows)], ignore_index=True)

    # --- BAGIAN TAMBAHAN: MENGHILANGKAN ANGKA .0 ---
    cols_qty = ['QTY AMBIL', 'QTY BIN LAIN', df_res.columns[7]]
    for col in cols_qty:
        if col in df_res.columns:
            # Mengubah NaN atau string kosong ke 0, lalu paksa jadi integer
            df_res[col] = pd.to_numeric(df_res[col], errors='coerce').fillna(0).astype(int)

    return df_res

def engine_generate_new_draft(df_compared):
    if df_compared is None or df_compared.empty: return pd.DataFrame(columns=['BIN', 'SKU', 'QUANTITY'])
    dict_final = {}
    for _, row in df_compared.iterrows():
        sku = str(row.iloc[3]).strip().upper()
        bin_i = str(row.iloc[8]).strip().upper()
        bin_l = str(row.iloc[11]).strip().upper() if not pd.isna(row.iloc[11]) else ""
        q_j = pd.to_numeric(row['QTY AMBIL'], errors='coerce') or 0
        q_m = pd.to_numeric(row['QTY BIN LAIN'], errors='coerce') or 0
        if q_j > 0:
            k = f"{bin_i}|{sku}"; dict_final[k] = dict_final.get(k, 0) + q_j
        if q_m > 0 and bin_l not in ["", "-", "NAN"]:
            k_l = f"{bin_l}|{sku}"; dict_final[k_l] = dict_final.get(k_l, 0) + q_m
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
        "BIN ASAL", "SKU", "QTY PUTAWAY", "BIN DITEMUKAN", "QUANTITY", "DIFF", "STATUS"
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
        df_plist = df_plist[["BIN AWAL", "BIN TUJUAN", "SKU", "QUANTITY", "STATUS"]]
        df_plist.columns = ["BIN AWAL", "BIN TUJUAN", "SKU", "QUANTITY", "NOTES"]
        df_plist['NOTES'] = "PUTAWAY"
    else:
        df_plist = pd.DataFrame(columns=["BIN AWAL", "BIN TUJUAN", "SKU", "QUANTITY", "NOTES"])
    
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

def process_scan_out(df_scan, df_history, df_stock):
    # ========== COPY & NORMALISASI (TETAP SAMA) ==========
    df_scan = df_scan.copy()
    df_history = df_history.copy()
    df_stock = df_stock.copy()
    
    df_scan.columns = [str(col).strip().upper() for col in df_scan.columns]
    df_history.columns = [str(col).strip().upper() for col in df_history.columns]
    df_stock.columns = [str(col).strip().upper() for col in df_stock.columns]
    
    df_scan = df_scan.rename(columns={df_scan.columns[0]: 'BIN_AWAL', df_scan.columns[1]: 'SKU'})
    
    if len(df_history.columns) > 3: df_history = df_history.rename(columns={df_history.columns[3]: 'SKU'})
    if len(df_history.columns) > 8: df_history = df_history.rename(columns={df_history.columns[8]: 'BIN_HIST'})
    if len(df_history.columns) > 10: df_history = df_history.rename(columns={df_history.columns[10]: 'QTY_HIST'})
    if len(df_history.columns) > 12: df_history = df_history.rename(columns={df_history.columns[12]: 'BIN_AFTER'})
    
    if len(df_stock.columns) > 0: df_stock = df_stock.rename(columns={df_stock.columns[0]: 'INVOICE'})
    if len(df_stock.columns) > 1: df_stock = df_stock.rename(columns={df_stock.columns[1]: 'SKU'})
    if len(df_stock.columns) > 6: df_stock = df_stock.rename(columns={df_stock.columns[6]: 'BIN_STOCK'})
    if len(df_stock.columns) > 10: df_stock = df_stock.rename(columns={df_stock.columns[10]: 'QTY_STOCK'})
    
    for df in [df_scan, df_history, df_stock]:
        for col in ['SKU', 'BIN_AWAL', 'BIN_HIST', 'BIN_STOCK', 'BIN_AFTER', 'INVOICE']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip().str.upper()

    if 'QTY_HIST' in df_history.columns:
        df_history['QTY_HIST'] = pd.to_numeric(df_history['QTY_HIST'], errors='coerce').fillna(0).astype(int)
    if 'QTY_STOCK' in df_stock.columns:
        df_stock['QTY_STOCK'] = pd.to_numeric(df_stock['QTY_STOCK'], errors='coerce').fillna(0).astype(int)

    final_results = []

    # ========== LOGIKA PROSES ==========
    for _, scan_row in df_scan.iterrows():
        sku = scan_row['SKU']
        bin_fisik = scan_row['BIN_AWAL']
        found = False
        keterangan = ""
        qty_val = 0
        bin_aft = ""
        inv = ""

        # 1. MATCH SEMPURNA HISTORY
        h_exact = df_history[(df_history['SKU'] == sku) & (df_history['BIN_HIST'] == bin_fisik) & (df_history['QTY_HIST'] > 0)]
        if not h_exact.empty:
            idx = h_exact.index[0]
            keterangan = 'DONE AND MATCH SET UP'
            bin_aft = df_history.loc[idx, 'BIN_AFTER']
            df_history.loc[idx, 'QTY_HIST'] -= 1
            qty_val = 1
            found = True

        # 2. MATCH SEMPURNA STOCK
        if not found:
            st_exact = df_stock[(df_stock['SKU'] == sku) & (df_stock['BIN_STOCK'] == bin_fisik) & (df_stock['QTY_STOCK'] > 0)]
            if not st_exact.empty:
                idx = st_exact.index[0]
                keterangan = 'ITEM TELAH TERJUAL'
                inv = df_stock.loc[idx, 'INVOICE']
                df_stock.loc[idx, 'QTY_STOCK'] -= 1
                qty_val = 1
                found = True

        # 3. SKU ONLY HISTORY (BIN MISSMATCH)
        if not found:
            h_sku_only = df_history[(df_history['SKU'] == sku) & (df_history['QTY_HIST'] > 0)]
            if not h_sku_only.empty:
                idx = h_sku_only.index[0]
                keterangan = 'DONE SETUP (BIN MISSMATCH)'
                bin_aft = df_history.loc[idx, 'BIN_AFTER']
                df_history.loc[idx, 'QTY_HIST'] -= 1
                qty_val = 1
                found = True

        # 4. SKU ONLY STOCK (BIN MISSMATCH)
        if not found:
            st_sku_only = df_stock[(df_stock['SKU'] == sku) & (df_stock['QTY_STOCK'] > 0)]
            if not st_sku_only.empty:
                idx = st_sku_only.index[0]
                keterangan = 'ITEM TELAH TERJUAL (BIN MISSMATCH)'
                inv = df_stock.loc[idx, 'INVOICE']
                df_stock.loc[idx, 'QTY_STOCK'] -= 1
                qty_val = 1
                found = True

        if not found:
            keterangan = 'ITEM BELUM TERSETUP & TIDAK TERJUAL'
            qty_val = 0

        final_results.append({
            'BIN AWAL': bin_fisik, 'SKU': sku, 'QTY SCAN': 1,
            'Keterangan': keterangan, 'Total Qty Setup/Terjual': qty_val,
            'Bin After Set Up': bin_aft, 'Invoice': inv
        })

    df_res_raw = pd.DataFrame(final_results)
    df_res = df_res_raw.groupby(['BIN AWAL', 'SKU', 'Keterangan', 'Bin After Set Up', 'Invoice'], dropna=False).agg({
        'QTY SCAN': 'sum',
        'Total Qty Setup/Terjual': 'sum'
    }).reset_index()

    # ========== LOGIKA DRAFT SETUP (UPDATE SESUAI REQUEST) ==========
    draft_data = []
    for _, row in df_res.iterrows():
        ket = row['Keterangan']
        
        # Kondisi: DONE SETUP (BIN MISSMATCH)
        if ket == 'DONE SETUP (BIN MISSMATCH)':
            # Baris 1: Pindahkan dari Bin After ke Bin Awal (Miss Location)
            draft_data.append({
                'BIN AWAL': row['Bin After Set Up'],
                'BIN TUJUAN': row['BIN AWAL'],
                'SKU': row['SKU'],
                'QUANTITY': row['QTY SCAN'],
                'NOTES': 'MISS LOCATION'
            })
            # Baris 2: Pindahkan ke Karantina
            draft_data.append({
                'BIN AWAL': row['BIN AWAL'],
                'BIN TUJUAN': 'KARANTINA',
                'SKU': row['SKU'],
                'QUANTITY': row['QTY SCAN'],
                'NOTES': 'WAITING OFFLINE'
            })

        # Kondisi: DONE SET UP (QTY MISSMATCH) -> Asumsi jika label ini muncul di Keterangan
        elif 'QTY MISSMATCH' in ket:
            draft_data.append({
                'BIN AWAL': row['BIN AWAL'],
                'BIN TUJUAN': 'KARANTINA',
                'SKU': row['SKU'],
                'QUANTITY': row['QTY SCAN'],
                'NOTES': 'MISS LOCATION'
            })

        # Kondisi: Selain dua di atas tapi mengandung MISSMATCH atau BELUM
        elif "MISSMATCH" in ket or "BELUM" in ket:
            draft_data.append({
                'BIN AWAL': row['BIN AWAL'],
                'BIN TUJUAN': 'KARANTINA',
                'SKU': row['SKU'],
                'QUANTITY': row['QTY SCAN'],
                'NOTES': 'WAITING OFFLINE'
            })
    
    df_draft = pd.DataFrame(draft_data) if draft_data else pd.DataFrame(columns=['BIN AWAL', 'BIN TUJUAN', 'SKU', 'QUANTITY', 'NOTES'])
    
    # Reorder columns df_res
    df_res = df_res[['BIN AWAL', 'SKU', 'QTY SCAN', 'Keterangan', 'Total Qty Setup/Terjual', 'Bin After Set Up', 'Invoice']]
    
    return df_res, df_draft
    
def process_justification(df_case, df_tracking, df_po):
    # 1. Copy data biar aman
    res = df_case.copy()
    df_tracking = df_tracking.copy()
    df_po = df_po.copy()

    # 2. Aggregasi Tracking (Pastikan nama kolom sesuai urutan Excel lu)
    sku_col_track = df_tracking.columns[1] # Kolom B (SKU)
    track_agg = df_tracking.groupby(sku_col_track).agg({
        df_tracking.columns[3]: 'sum',  # L: Current Stock
        df_tracking.columns[4]: 'sum',  # M: Total Sales
        df_tracking.columns[5]: 'sum',  # N: Total_Stockin
        df_tracking.columns[6]: 'sum',  # O: Total_adj_minus
        df_tracking.columns[7]: 'sum',  # P: Total_adj_plus
        df_tracking.columns[8]: 'sum',  # Q: Total draft_trf
        df_tracking.columns[9]: 'sum',  # R: Total trf_in (SESUAI REQUEST LU)
        df_tracking.columns[10]: 'sum'  # S: Total trf_out
    }).reset_index()

    # Nama kolom sementara agar unik
    track_agg.columns = ['SKU_KEY', '_L', '_M', '_N', '_O', '_P', '_Q', '_R', '_S']
    
    # Clean SKU
    track_agg['SKU_KEY'] = track_agg['SKU_KEY'].astype(str).str.split('.').str[0].str.strip().str.upper()
    res['SKU_KEY_JOIN'] = res['SKU'].astype(str).str.split('.').str[0].str.strip().str.upper()

    # 3. Merge
    res = res.merge(track_agg, left_on='SKU_KEY_JOIN', right_on='SKU_KEY', how='left').fillna(0)

    # 4. Pindahkan data ke kolom Final
    res['Current Stock']   = res['_L']
    res['Total Sales']     = res['_M']
    res['Total_Stockin']   = res['_N']
    res['Total_adj_minus'] = res['_O']
    res['Total_adj_plus']  = res['_P']
    res['Total draft_trf'] = res['_Q']
    res['Total trf_in']    = res['_R']
    res['Total trf_out']   = res['_S']

    # 5. Hitung REAL QTY (T) & GAP ADJ (U)
    res['REAL QTY'] = (res['Total_Stockin'] + res['Total trf_in']) - \
                      (res['Total Sales'] + res['Total trf_out'] + res['Total draft_trf'])
    res['GAP ADJUSMENT'] = res['Total_adj_plus'] - res['Total_adj_minus']

    # 6. RUMUS LU (PLEK KETIPLEK SESUAI ABJAD EXCEL)
    def run_formula(row):
        # Konversi ke float & round biar ga selisih koma sama Excel
        j2 = round(float(row['QTY SYSTEM']), 2)    # J
        k2 = round(float(row['QTY SO']), 2)        # K
        l2 = round(float(row['Current Stock']), 2) # L
        m2 = round(float(row['Total Sales']), 2)   # M
        n2 = round(float(row['Total_Stockin']), 2) # N
        r2 = round(float(row['Total trf_in']), 2)  # R (Tadi lu koreksi ini)
        t2 = round(float(row['REAL QTY']), 2)      # T
        u2 = round(float(row['GAP ADJUSMENT']), 2) # U

        # Logic Rumus Excel lu:
        if (j2 > k2 and u2 > 0) or (j2 < k2 and u2 < 0):
            return "KESALAHAN ADJUSMENT"
        
        if (n2 + r2) < m2 or t2 < 0:
            return "PERLU CEK CROSS ORDER"
        
        if t2 == l2 and t2 != 0:
            return "CEK ULANG HASIL REKON"
        
        if (t2 == 0 and u2 <= 0 and l2 > 0) or (j2 > k2 and l2 > t2):
            return "INDIKASI BUG SISTEM"
            
        return "UNDEFINED"

    # Jalankan fungsi
    res['JUSTIFICATION'] = res.apply(run_formula, axis=1)

    # 7. PO IN
    po_counts = df_po[df_po.columns[3]].astype(str).str.split('.').str[0].value_counts().to_dict()
    res['TOTAL PO IN'] = res['SKU_KEY_JOIN'].apply(lambda x: po_counts.get(x, 0))

    # 8. Susun Urutan Header (Identify -> TOTAL PO IN)
    ordered_headers = [
        'Identify', 'BIN', 'SKU', 'BRAND', 'ITEM NAME', 'VARIANT', 'SUB KATEGORI', 
        'Harga Beli', 'Harga Jual', 'QTY SYSTEM', 'QTY SO', 'Current Stock', 
        'Total Sales', 'Total_Stockin', 'Total_adj_minus', 'Total_adj_plus', 
        'Total draft_trf', 'Total trf_in', 'Total trf_out', 'REAL QTY', 
        'GAP ADJUSMENT', 'JUSTIFICATION', 'TOTAL PO IN'
    ]

    return res[ordered_headers]

def load_data(file):
    """Membaca file Excel atau CSV."""
    if file.name.endswith('.csv'):
        return pd.read_csv(file)
    return pd.read_excel(file)

def prepare_columns(df):
    """Mengambil kolom B, C, J dan membersihkan data."""
    # Validasi jumlah kolom minimal sampai indeks 9 (Kolom J)
    if df.shape[1] < 10:
        raise ValueError("File tidak memiliki kolom yang cukup (Minimal sampai kolom J).")
        
    # Ambil kolom B(1), C(2), J(9)
    new_df = df.iloc[:, [1, 2, 9]].copy()
    new_df.columns = ['BIN', 'SKU', 'QTY']
    
    # Sanitasi data: Hilangkan spasi dan pastikan tipe data benar
    new_df['BIN'] = new_df['BIN'].astype(str).str.strip()
    new_df['SKU'] = new_df['SKU'].astype(str).str.strip()
    new_df['QTY'] = pd.to_numeric(new_df['QTY'], errors='coerce').fillna(0)
    
    # PENTING: Grouping supaya jika ada SKU+BIN yang sama di baris berbeda, QTY-nya dijumlahkan dulu
    new_df = new_df.groupby(['BIN', 'SKU'], as_index=False)['QTY'].sum()
    
    return new_df

def process_stock_comparison(file1, file2):
    """Fungsi utama untuk memproses perbandingan."""
    try:
        df1 = load_data(file1)
        df2 = load_data(file2)

        data1 = prepare_columns(df1)
        data2 = prepare_columns(df2)

        # Gabungkan data berdasarkan BIN dan SKU
        comparison = pd.merge(
            data1, 
            data2, 
            on=['BIN', 'SKU'], 
            how='outer', 
            suffixes=('_Sys1', '_Sys2')
        ).fillna(0)

        # Hitung Selisih
        comparison['DIFF'] = comparison['QTY_Sys1'] - comparison['QTY_Sys2']
        
        # Ambil hanya yang ada perbedaan
        discrepancies = comparison[comparison['DIFF'] != 0].copy()
        
        return comparison, discrepancies
    except Exception as e:
        # Lempar error agar bisa ditangkap oleh UI (st.error)
        raise e

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
    

import streamlit as st

# --- INITIALIZATION ---
if 'main_menu' not in st.session_state:
    st.session_state.main_menu = "Dashboard Overview"

# Fungsi callback untuk sinkronisasi menu
def change_m1():
    st.session_state.main_menu = st.session_state.m1_key
def change_m2():
    st.session_state.main_menu = st.session_state.m2_key
def change_m3():
    st.session_state.main_menu = st.session_state.m3_key

with st.sidebar:
    # --- KELOMPOK 1: DASHBOARD SUMMARY ---
    st.markdown('<p style="font-weight: bold; color: #808495; margin-top: 10px; margin-bottom: -5px;">MAIN MENU</p>', unsafe_allow_html=True)
    st.markdown('<p style="font-weight: bold; color: #808495; margin-bottom: 5px;">DASHBOARD SUMMARY</p>', unsafe_allow_html=True)
    
    m1_list = ["Dashboard Overview", "Database Master"]
    idx1 = m1_list.index(st.session_state.main_menu) if st.session_state.main_menu in m1_list else 0
    
    st.radio("M1", m1_list, index=idx1, key="m1_key", on_change=change_m1, label_visibility="collapsed")

    # --- KELOMPOK 2: OPERATIONAL ---
    st.markdown('<p style="font-weight: bold; color: #808495; margin-top: 25px; margin-bottom: 5px;">OPERATIONAL</p>', unsafe_allow_html=True)
    
    m2_list = ["Putaway System", "Scan Out Validation", "Refill & Overstock", "Refill & Withdraw", "Compare RTO", "FDR Update"]
    idx2 = m2_list.index(st.session_state.main_menu) if st.session_state.main_menu in m2_list else 0
    
    st.radio("M2", m2_list, index=idx2, key="m2_key", on_change=change_m2, label_visibility="collapsed")

    # --- KELOMPOK 3: INVENTORY ---
    st.markdown('<p style="font-weight: bold; color: #808495; margin-top: 25px; margin-bottom: 5px;">INVENTORY</p>', unsafe_allow_html=True)
    
    m3_list = ["Stock Opname", "Justification SO", "Stock Minus", "Compare System"]
    
    # PERBAIKAN DI SINI: Gunakan m3_list dan idx3, jangan pakai m2_list lagi
    idx3 = m3_list.index(st.session_state.main_menu) if st.session_state.main_menu in m3_list else 0
    
    st.radio("M3", m3_list, index=idx3, key="m3_key", on_change=change_m3, label_visibility="collapsed")

    st.divider()

# Final Menu Variable untuk dipakai di konten utama
menu = st.session_state.main_menu

    

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
                total_list_qty = int(df_plist['QUANTITY'].sum()) if not df_plist.empty else 0
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
        - **HISTORY SET UP**: Sesuai yang ada pada template Mutasi Set Up Jezpro
        - **STOCK TRACKING**: Sesuai yang ada pada template Stock Tracking Jezpro
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
    
    # CSS UNTUK BOX CUSTOM (Tampilan sesuai gambar Anda)
    st.markdown("""
        <style>
        .m-box {
            background-color: #1e2130;
            padding: 20px;
            border-radius: 10px;
            border-left: 5px solid #f39c12;
            text-align: center;
            margin-bottom: 10px;
        }
        .m-lbl { color: #8e94ab; font-size: 14px; display: block; text-transform: uppercase; font-weight: bold; }
        .m-val { color: #f39c12; font-size: 32px; font-weight: bold; }
        </style>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Upload File dari Jezpro", type=["xlsx", "xlsm"])
    
    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file, engine="openpyxl")
            df.columns = [str(c).strip().upper() for c in df.columns]
            
            # Identifikasi Kolom Utama
            col_sku = 'SKU'
            col_bin = 'BIN'
            col_qty = next((c for c in df.columns if 'QTY SYSTEM' in c or 'QTY SYS' in c), None)
            
            if col_qty is None:
                st.error("❌ Kolom 'QTY SYSTEM' tidak ditemukan!")
            else:
                if st.button("🔃 PROSES DATA"):
                    with st.spinner('Memproses...'):
                        # 1. DATA MINUS AWAL
                        df[col_qty] = pd.to_numeric(df[col_qty], errors='coerce').fillna(0)
                        df_minus_awal = df[df[col_qty] < 0].copy()
                        
                        # [LOGIKA PROSES MUTASI DIMULAI]
                        qty_arr = df[col_qty].values.copy()
                        sku_arr = df[col_sku].astype(str).values
                        bin_arr = df[col_bin].astype(str).values
                        
                        # (Logika mapping dan prior_bins tetap di sini)
                        # ... proses pencarian stock ...
                        
                        # [LOGIKA PROSES MUTASI SELESAI]
                        set_up_results = [] # Anggap ini list hasil proses mutasi Anda
                        df_final = df.copy()
                        df_final[col_qty] = qty_arr
                        df_need_adj = df_final[df_final[col_qty] < 0].copy()
                        
                        # --- TAMPILAN BOX CUSTOM ---
                        st.divider()
                        st.subheader("📊 RINGKASAN HASIL PROSES")
                        
                        val_total_minus = len(df_minus_awal)
                        val_mutasi = int(sum([x['QUANTITY'] for x in set_up_results])) if set_up_results else 0
                        val_need_adj = len(df_need_adj)

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.markdown(f'<div class="m-box"><span class="m-lbl">Total Stock Minus</span><span class="m-val">{val_total_minus}</span></div>', unsafe_allow_html=True)
                        with col2:
                            st.markdown(f'<div class="m-box"><span class="m-lbl">Mutasi Stock Minus</span><span class="m-val">{val_mutasi}</span></div>', unsafe_allow_html=True)
                        with col3:
                            st.markdown(f'<div class="m-box"><span class="m-lbl">Need Justification</span><span class="m-val">{val_need_adj}</span></div>', unsafe_allow_html=True)

                        # --- TAMPILAN TAB DENGAN KETERANGAN KOSONG ---
                        tab1, tab2, tab3 = st.tabs(["📄 MINUS AWAL", "🔄 DETAIL MUTASI", "⚠️ JUSTIFIKASI"])
                        
                        with tab1:
                            if not df_minus_awal.empty:
                                st.dataframe(df_minus_awal, use_container_width=True)
                            else:
                                st.info("ℹ️ Tidak ada data stock minus dalam file ini.")
                                
                        with tab2:
                            if set_up_results:
                                st.dataframe(pd.DataFrame(set_up_results), use_container_width=True)
                            else:
                                st.warning("⚠️ Tidak ditemukan stock pendukung. Tidak ada mutasi yang dilakukan.")
                                
                        with tab3:
                            if not df_need_adj.empty:
                                st.dataframe(df_need_adj, use_container_width=True)
                            else:
                                st.success("✅ Semua stock minus berhasil ditutup! Tidak ada item butuh justifikasi.")

                        # --- DOWNLOAD DENGAN SHEET KETERANGAN ---
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                            if not df_minus_awal.empty:
                                df_minus_awal.to_excel(writer, sheet_name='MINUS_AWAL', index=False)
                            if set_up_results:
                                pd.DataFrame(set_up_results).to_excel(writer, sheet_name='SET_UP', index=False)
                            if not df_need_adj.empty:
                                df_need_adj.to_excel(writer, sheet_name='JUSTIFIKASI', index=False)
                            else:
                                pd.DataFrame({"INFO": ["DATA BERSIH - TIDAK ADA MINUS"]}).to_excel(writer, sheet_name='JUSTIFIKASI', index=False)
                        
                        st.download_button("📥 DOWNLOAD HASIL", output.getvalue(), "HASIL_STOCK_MINUS.xlsx")

        except Exception as e:
            st.error(f"Gagal memproses file: {e}")


if menu == "Compare RTO":
    st.markdown('<div class="hero-header"><h1>📦 RTO GATEWAY SYSTEM</h1></div>', unsafe_allow_html=True)
    st.markdown("""<style>.m-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; text-align: center; margin: 5px 0; }.m-lbl { display: block; font-size: 14px; color: #555; font-weight: bold; }.m-val { display: block; font-size: 24px; color: #ff4b4b; font-weight: bold; }</style>""", unsafe_allow_html=True)
    
    if 'rto_df_ds' not in st.session_state: st.session_state.rto_df_ds = None
    if 'rto_df_selisih' not in st.session_state: st.session_state.rto_df_selisih = None
    if 'rto_df_app' not in st.session_state: st.session_state.rto_df_app = None
    if 'rto_draft_compared' not in st.session_state: st.session_state.rto_draft_compared = None
    if 'rto_new_draft' not in st.session_state: st.session_state.rto_new_draft = None
    
    c1, c2 = st.columns(2)
    with c1: f1 = st.file_uploader("1. DS RTO", type=['xlsx','csv'], key="rto_f1")
    with c2: f2 = st.file_uploader("2. APPSHEET RTO", type=['xlsx','csv'], key="rto_f2")
    
    if f1 and f2:
        if st.button("▶️ JALANKAN PROSES", use_container_width=True):
            df1 = pd.read_excel(f1) if f1.name.endswith('xlsx') else pd.read_csv(f1)
            df2 = pd.read_excel(f2) if f2.name.endswith('xlsx') else pd.read_csv(f2)
            st.session_state.rto_df_app = df2.copy()
            res_ds, res_selisih = engine_ds_rto_vba_total(df1, df2)
            st.session_state.rto_df_ds, st.session_state.rto_df_selisih = res_ds, res_selisih
            st.success("✅ Selesai!")
    
    if st.session_state.rto_df_selisih is not None:
        st.divider()
        st.subheader("📊 Hasil Analisis RTO")
        
        # Ambil data lengkap
        df_full = st.session_state.rto_df_ds
        scan_col = df_full.columns[1]
        
        # --- PERHITUNGAN METRIK ---
        q_total = int(pd.to_numeric(df_full.iloc[:, 1], errors='coerce').fillna(0).sum())
        q_sesuai = int(pd.to_numeric(df_full[df_full['NOTE'] == 'SESUAI'].iloc[:, 1], errors='coerce').fillna(0).sum())
        
        q_lebih = int(
            (pd.to_numeric(df_full[df_full['NOTE'] == 'KELEBIHAN AMBIL'][scan_col], errors='coerce').fillna(0) - 
             pd.to_numeric(df_full[df_full['NOTE'] == 'KELEBIHAN AMBIL']['QTY AMBIL'], errors='coerce').fillna(0)
            ).sum()
        )
        
        q_kurang = int(
            (pd.to_numeric(df_full[df_full['NOTE'] == 'KURANG AMBIL']['QTY AMBIL'], errors='coerce').fillna(0) - 
             pd.to_numeric(df_full[df_full['NOTE'] == 'KURANG AMBIL'][scan_col], errors='coerce').fillna(0)
            ).sum()
        )

        # Buat Tab
        tab1, tab2 = st.tabs(["📝 Summary Compare", "⚠️ Item Selisih"])

        with tab1:
            # Matrix Box
            mc1, mc2, mc3, mc4 = st.columns(4)
            with mc1: st.markdown(f'<div class="m-box"><span class="m-lbl">Total Qty Scan</span><span class="m-val">{q_total}</span></div>', unsafe_allow_html=True)
            with mc2: st.markdown(f'<div class="m-box"><span class="m-lbl">Qty Sesuai</span><span class="m-val">{q_sesuai}</span></div>', unsafe_allow_html=True)
            with mc3: st.markdown(f'<div class="m-box"><span class="m-lbl">Qty Kelebihan</span><span class="m-val">{q_lebih}</span></div>', unsafe_allow_html=True)
            with mc4: st.markdown(f'<div class="m-box"><span class="m-lbl">Qty Kurang</span><span class="m-val">{q_kurang}</span></div>', unsafe_allow_html=True)
            
            st.write("### 📋 All Data Comparison")
            # Menampilkan SEMUA data tanpa filter
            st.dataframe(df_full, use_container_width=True, hide_index=True)
            st.download_button("📥 Download All Data", df_full.to_csv(index=False).encode('utf-8'), "ALL_DATA_RTO.csv", "text/csv", key="dl_all", use_container_width=True)

        with tab2:
            st.write("### 🚨 Daftar Item Selisih")
            # Hanya tampilkan yang bermasalah
            df_selisih_saja = df_full[df_full['NOTE'].isin(['KURANG AMBIL', 'KELEBIHAN AMBIL'])]
            
            if not df_selisih_saja.empty:
                st.dataframe(df_selisih_saja, use_container_width=True, hide_index=True)
                st.download_button("📥 Download Item Selisih", df_selisih_saja.to_csv(index=False).encode('utf-8'), "HANYA_SELISIH_RTO.csv", "text/csv", key="dl_selisih", use_container_width=True)
            else:
                st.success("✨ Aman! Tidak ada item yang selisih.")
    st.divider()
    st.subheader("🔄 REFRESH DATA (SETELAH CEK REAL)")
    f_cek = st.file_uploader("Upload Hasil Cek Real", type=['xlsx','csv'], key="rto_cek")
    if f_cek and st.session_state.rto_df_app is not None:
        if st.button("🔄 REFRESH DATA", use_container_width=True):
            df_cek = pd.read_excel(f_cek) if f_cek.name.endswith('xlsx') else pd.read_csv(f_cek)
            ds_ref, app_ref = engine_refresh_rto(st.session_state.rto_df_ds, st.session_state.rto_df_app, df_cek)
            st.session_state.rto_df_ds, st.session_state.rto_df_app = ds_ref, app_ref
            st.success("✅ Refreshed!")

    st.divider()
    st.subheader("📝 COMPARE DRAFT JEZPRO")
    f_draft = st.file_uploader("Upload Draft Jezpro", type=['xlsx','csv'], key="rto_draft_jezpro")
    if f_draft and st.session_state.rto_df_app is not None:
        if st.button("🔍 COMPARE DRAFT JEZPRO", use_container_width=True):
            df_draft = pd.read_excel(f_draft) if f_draft.name.endswith('xlsx') else pd.read_csv(f_draft)
            st.session_state.rto_draft_compared = engine_compare_draft_jezpro(st.session_state.rto_df_app, df_draft)
            st.success("✅ Compare Selesai!")

    if st.session_state.rto_draft_compared is not None:
        st.divider()
        st.subheader("📊 DASHBOARD DRAFT (QTY AMBIL)")
        df_comp = st.session_state.rto_draft_compared
        q_draft_total = int(pd.to_numeric(df_comp['QTY AMBIL'], errors='coerce').sum())
        q_ok = int(pd.to_numeric(df_comp[df_comp['STATUS'] == 'OK']['QTY AMBIL'], errors='coerce').sum())
        q_edit = int(pd.to_numeric(df_comp[df_comp['STATUS'].str.contains('EDIT', na=False)]['QTY AMBIL'], errors='coerce').sum())
        q_del = int(pd.to_numeric(df_comp[df_comp['STATUS'] == 'DELETE ITEM']['Qty Transfer'], errors='coerce').sum())
        
        dc1, dc2, dc3, dc4 = st.columns(4)
        with dc1: st.markdown(f'<div class="m-box"><span class="m-lbl">Total Qty Ambil</span><span class="m-val">{q_draft_total}</span></div>', unsafe_allow_html=True)
        with dc2: st.markdown(f'<div class="m-box"><span class="m-lbl">Qty OK</span><span class="m-val">{q_ok}</span></div>', unsafe_allow_html=True)
        with dc3: st.markdown(f'<div class="m-box"><span class="m-lbl">Qty Perlu Edit</span><span class="m-val">{q_edit}</span></div>', unsafe_allow_html=True)
        with dc4: st.markdown(f'<div class="m-box"><span class="m-lbl">Qty Delete</span><span class="m-val">{q_del}</span></div>', unsafe_allow_html=True)
        
        st.dataframe(df_comp, use_container_width=True, hide_index=True)
        st.download_button("📥 Download Draft Compared", df_comp.to_csv(index=False).encode('utf-8'), "DRAFT_COMPARED.csv", "text/csv", use_container_width=True)

       # --- GENERATE NEW DRAFT ---
    st.subheader("GENERATE NEW DRAFT")
    
    if st.session_state.rto_draft_compared is not None:
        if st.button("▶️ GENERATE NEW DRAFT", use_container_width=True):
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
elif menu == "Justification SO":
    st.markdown('<div class="hero-header"><h1>JUTIFICATION ADJUSMENT</h1></div>', unsafe_allow_html=True)

    # 1. Inisialisasi Session State biar data nggak hilang pas diklik
    if 'result_so' not in st.session_state:
        st.session_state.result_so = None

    # UI Uploader - Dibagi 3 Kolom
    col1, col2, col3 = st.columns(3)
    with col1: 
        up_case = st.file_uploader("Upload Adjusment File", type=['xlsx'], key="up_case_so")
    with col2: 
        up_tracking = st.file_uploader("Upload Tracking Stock", type=['xlsx'], key="up_track_so")
    with col3: 
        up_others = st.file_uploader("Upload Total PO", type=['xlsx'], key="up_po_so")

    # 2. Logika Tombol Run
    if up_case and up_tracking and up_others:
        if st.button("▶️ RUN COMPARISON ANALYSIS", use_container_width=True):
            with st.spinner("Processing Data..."):
                df_c = pd.read_excel(up_case)
                df_t = pd.read_excel(up_tracking)
                df_p = pd.read_excel(up_others)
                
                # Panggil fungsi sakti lo
                st.session_state.result_so = process_justification(df_c, df_t, df_p)

    # 3. TAMPILAN OUTPUT (Hanya muncul kalau data sudah di-run)
    if st.session_state.result_so is not None:
        result = st.session_state.result_so
        
        # --- TAMPILAN METRIC BOX (STYLE M-BOX) ---
        st.divider()
        m1, m2, m3, m4, m5 = st.columns(5)
        
        # Hitung angka buat box
        c_undef = len(result[result['JUSTIFICATION'] == "UNDEFINED"])
        c_bug   = len(result[result['JUSTIFICATION'] == "INDIKASI BUG SISTEM"])
        c_adj   = len(result[result['JUSTIFICATION'] == "KESALAHAN ADJUSMENT"])
        c_cross = len(result[result['JUSTIFICATION'] == "PERLU CEK CROSS ORDER"])
        c_rekon = len(result[result['JUSTIFICATION'] == "CEK ULANG HASIL REKON"])

        m1.markdown(f'<div class="m-box"><span class="m-lbl">❓UNDEFINED</span><span class="m-val">{c_undef}</span></div>', unsafe_allow_html=True)
        m2.markdown(f'<div class="m-box"><span class="m-lbl">💻BUG SISTEM</span><span class="m-val">{c_bug}</span></div>', unsafe_allow_html=True)
        m3.markdown(f'<div class="m-box"><span class="m-lbl">❌KESALAHAN ADJ</span><span class="m-val">{c_adj}</span></div>', unsafe_allow_html=True)
        m4.markdown(f'<div class="m-box"><span class="m-lbl">🗳️CEK CROSS ORDER</span><span class="m-val">{c_cross}</span></div>', unsafe_allow_html=True)
        m5.markdown(f'<div class="m-box"><span class="m-lbl">🔁CEK ULANG HASIL REKON</span><span class="m-val">{c_rekon}</span></div>', unsafe_allow_html=True)
        
        # --- TAMPILAN TABEL ---
        st.divider()
        st.subheader("📋 Summary Report Analysis")
        st.dataframe(result, use_container_width=True, height=450)
        
        # --- DOWNLOAD BUTTON (DI LUAR BUTTON RUN AGAR STAY) ---
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            result.to_excel(writer, index=False, sheet_name='Summary')
        
        st.download_button(
            label="📥 DOWNLOAD HASIL REKON (.XLSX)",
            data=output.getvalue(),
            file_name="rekon_stock_so.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key="btn_download_so" # Key unik agar tidak reset
        )

elif menu == "Compare System":
    st.markdown('<div class="hero-header"><h1>STOCK COMPARATION</h1></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        file_sys1 = st.file_uploader("Upload Stock System 1", type=['xlsx', 'csv'])
    with col2:
        file_sys2 = st.file_uploader("Upload Stock System 2", type=['xlsx', 'csv'])

    if file_sys1 and file_sys2:
        if st.button("▶️RUN COMPARE"):
            try:
                # Ambil data dari fungsi logic lu
                result_all, diff_only = process_stock_comparison(file_sys1, file_sys2)
                
                st.divider()

                # PAKAI STYLE BOX ELEGAN TAPI CUMA 2 (Sesuai data lu)
                m1, m2 = st.columns(2)
                m1.markdown(f'<div class="m-box"><span class="m-lbl">📦 TOTAL ITEM DICEK</span><span class="m-val">{len(result_all)}</span></div>', unsafe_allow_html=True)
                m2.markdown(f'<div class="m-box"><span class="m-lbl">⚠️ ITEM SELISIH</span><span class="m-val">{len(diff_only)}</span></div>', unsafe_allow_html=True)

                if not diff_only.empty:
                    st.warning("Daftar Perbedaan Stok (BIN | SKU | QTY):")
                    st.dataframe(diff_only, use_container_width=True)
                    
                    csv = diff_only.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Hasil Selisih",
                        data=csv,
                        file_name='selisih_stok.csv',
                        mime='text/csv',
                    )
                else:
                    st.success("✅ Tidak ada perbedaan stok! Semua BIN, SKU, dan QTY match.")
            
            except Exception as e:
                st.error(f"Terjadi Kesalahan: {e}")

elif menu == "Refill & Withdraw":
    menu_refill_withdraw()

# --- Navigasi ---
elif menu == "Stock Opname":
    menu_Stock_Opname()