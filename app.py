import pandas as pd
import numpy as np
import streamlit as st
import io
import math

import pandas as pd
from collections import defaultdict
import streamlit as st
from streamlit_autorefresh import st_autorefresh

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
    cols_to_keep = [i for i in range(len(df_s.columns)) if i not in [10, 11]]
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
    single_list = [] # Buat Single

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

    setup_real_data = []
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
    ds.columns = ['BIN_SCAN', 'SKU_SCAN', 'QTY_TOTAL_SCAN']
    
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
        list_sub_kat = ["BAG", "BALL", "BASELAYER", "BOTTLE", "CLEANNING & CARE", "EXTRA SHOES", "HARDWARE", "JACKET", "JERSEY", "LOWER BODY", "NUTRITION", "OTHER", "OTHERS", "PANTS", "RACKET", "SANDALS", "SET APPAREL", "SHIRT", "SHOES", "SHORT", "SWLM", "UKNOWN SC", "UNDERLAYER", "UPPER BODY"]
        selected_sub = st.multiselect("🗂️ Sub Kategori:", list_sub_kat)
    with col_f2:
        list_bin_stock = ["GUDANG LT.2", "LIVE", "KL2", "KL1", "GL2-STORE", "GL2-STR", "OFFLINE", "TOKO", "GL1-DC", "RAK ACC LT.1", "GL3-DC-A", "GL3-DC-B", "GL3-DC-C", "GL3-DC-D", "GL3-DC-E", "GL3-DC-F", "GL3-DC-G", "GL3-DC-H", "GL3-DC-I", "GL3-DC-J", "GL4-DC-A", "GL4-DC-B", "GL4-DC-KL", "GL3-DC-RAK", "GL4-DC-RAK", "PUTAWAY", "KEEP AMP", "MARKOM", "DEFECT", "REJECT", "DAU", "KAV-2", "KAV-7", "KAV-8", "KAV-9", "KAV-10", "C-0", "KDR", "GL3-KOLI", "JBR", "GUDANG", "SDA", "GL2-SMG", "GL2-SMG-CTN-","GUDANG LT 2"]
        selected_bin_sys = st.multiselect("🏭 BIN System:", list_bin_stock)
    with col_f3:
        list_bin_cov = ["KARANTINA", "STAGGING", "STAGING", "GUDANG LT.2", "TOKO", "GL1-DC", "RAK ACC LT.1", "GL3-DC-A", "GL3-DC-B", "GL3-DC-C", "GL3-DC-D", "GL3-DC-E", "GL3-DC-F", "GL3-DC-G", "GL3-DC-H", "GL3-DC-I", "GL3-DC-J", "GL4-DC-A", "GL4-DC-B", "GL4-DC-KL1", "GL4-DC-KL2", "GL3-DC-RAK", "GL4-DC-RAK", "LIVE", "MARKOM", "AMP", "GL2-STORE", "PUTAWAY", "OUT", "INB"]
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
                        cols[cols == dup] = [f"{dup}_{i}" if i != 0 else dup for i in range(cols[cols == dup].count())]
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
            
import math
import pandas as pd
import streamlit as st
import requests

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
    for key in ["df_stock_sby", "df_trx", "summary_refill", "summary_withdraw"]:
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
            df_s.columns = [i for i in range(len(df_s.columns))]
            
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
                is_excluded = any(ex in binLoc for ex in ["DEFECT", "REJECT", "ONLINE", "LIVE", "MARKOM", "KARANTINA", "STAGING", "PUTAWAY"])
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
                elif any(x in binLoc for x in ["DC", "INBOUND", "KL", "RAK"]):
                    dictPreTotDCInbound[sku] = dictPreTotDCInbound.get(sku, 0) + qtySys
                    if qtySys > dictBestValDC.get(sku, -1):
                        dictBestValDC[sku] = qtySys
                        dictDC[sku] = binLoc
                    dictTotDC[sku] = dictTotDC.get(sku, 0) + qtySys
                    dictBinListDC[sku] = dictBinListDC.get(sku, "") + binLoc + ", "
                    dictTotDCKLRAK[sku] = dictTotDCKLRAK.get(sku, 0) + qtySys

            outRef = []; outWdr = []

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
    app_summary = {} 
    for _, r in df_a.iterrows():
        # Ambil semua pasangan SKU & BIN dari AppSheet (Kolom 9&12, 15&16)
        pairs = [(clean_sku(r.get('9')), str(r.get('12','')).strip().upper(), pd.to_numeric(r.get('13',0), errors='coerce') or 0),
                 (clean_sku(r.get('15')) or clean_sku(r.get('9')), str(r.get('16','')).strip().upper(), pd.to_numeric(r.get('17',0), errors='coerce') or 0)]
        
        for s, b, q in pairs:
            if s and b not in ["", "0", "NAN"]:
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
            
            df_res.loc[idx, ['QTY AMBIL', 'NOTE', 'BIN AMBIL LAIN', 'QTY BIN LAIN', 'STATUS']] = \
                [qty_j, note, "", 0, status]
            processed_indices.add(idx)

    # --- 3. TAHAP 2: SISANYA BARU CEK PINDAH BIN / DELETE ---
    for idx, row in df_res.iterrows():
        if idx in processed_indices: continue # Lewati yang sudah OK di Tahap 1

        sku_d = clean_sku(row.iloc[3])
        bin_d = str(row.iloc[8]).strip().upper()
        
        # Cari apakah SKU ini ada di BIN lain yang MASIH punya sisa stok di rem_app
        possible_bins = [k for k, v in rem_app.items() if k[0] == sku_d and v > 0]
        
        if possible_bins:
            # Info BIN lain diambil dari sisa stok yang belum ter-match
            bin_lain = ", ".join([b[1] for b in possible_bins])
            qty_lain = sum([rem_app[b] for b in possible_bins])
            
            df_res.loc[idx, ['QTY AMBIL', 'NOTE', 'BIN AMBIL LAIN', 'QTY BIN LAIN', 'STATUS']] = \
                [0, "PINDAH BIN", bin_lain, qty_lain, "PERLU EDIT BIN DRAFT"]
        else:
            df_res.loc[idx, ['QTY AMBIL', 'NOTE', 'BIN AMBIL LAIN', 'QTY BIN LAIN', 'STATUS']] = \
                [0, "HAPUS ITEM INI", "", 0, "DELETE ITEM"]

    # --- 4. TAHAP 3: ADD NEW (Hanya jika SKU bener-bener gak ada di Draft) ---
    sku_in_draft = set(df_draft.iloc[:, 3].apply(clean_sku).unique())
    new_rows = []

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
    for col in ['QTY AMBIL', 'QTY BIN LAIN', df_res.columns[7]]:
        if col in df_res.columns:
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

import pandas as pd
import math

def process_refill_overstock(df_all_data, df_stock_tracking=None):
    # Inisialisasi awal agar return tidak error
    df_gl3 = pd.DataFrame()
    df_gl4 = pd.DataFrame()
    df_refill_final = pd.DataFrame()
    df_overstock_final = pd.DataFrame()

    try:
        # --- SUB 1: FILTER_ALL_DATA ---
        if df_all_data is None or df_all_data.empty:
            return df_gl3, df_gl4, df_refill_final, df_overstock_final

        srcArr = df_all_data.values
        # AMBIL NAMA KOLOM ASLI
        header_names = df_all_data.columns.tolist()
        
        outGL3 = []
        outGL4 = []

        for i in range(len(srcArr)):
            binCode = str(srcArr[i][1]).upper() if not pd.isna(srcArr[i][1]) else ""
            
            # Logic GL3
            if "GL3" in binCode and "LIVE" not in binCode:
                outGL3.append(srcArr[i][:11])
            # Logic GL4
            if "GL4" in binCode and not any(x in binCode for x in ["DEFECT", "REJECT", "ONLINE", "RAK"]):
                outGL4.append(srcArr[i][:11])

        # PERBAIKAN: Masukkan header_names agar kolom tidak jadi angka
        df_gl3 = pd.DataFrame(outGL3, columns=header_names[:11])
        df_gl4 = pd.DataFrame(outGL4, columns=header_names[:11])

        # --- SUB 2: FILTER STOCK TRACKING (Proteksi jika None/Kosong) ---
        dictTrans = {}
        # Cek apakah df_stock_tracking ada isinya
        if df_stock_tracking is not None and not df_stock_tracking.empty:
            st_data = df_stock_tracking.values
            for i in range(len(st_data)):
                col_a = str(st_data[i][0]).upper() if not pd.isna(st_data[i][0]) else ""
                col_g = str(st_data[i][6]).upper() if not pd.isna(st_data[i][6]) else ""
                
                # Sesuai logic VBA: Bukan INV dan ada DC
                if "INV" not in col_a and "DC" in col_g:
                    sku_st = str(st_data[i][1]).strip()
                    qty_st = float(st_data[i][10]) if not pd.isna(st_data[i][10]) else 0
                    dictTrans[sku_st] = dictTrans.get(sku_st, 0) + qty_st

        # --- SUB 3: CREATE REFILL SHEET ---
        dictGL3 = {}
        if not df_gl3.empty:
            for row in df_gl3.values:
                sku = str(row[2]).strip()
                qty = int(float(row[9])) if not pd.isna(row[9]) else 0
                dictGL3[sku] = dictGL3.get(sku, 0) + qty

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
                    bin_sumber = str(dataGL4[i][1]).upper() if not pd.isna(dataGL4[i][1]) else ""
                    if "LIVE" in bin_sumber: continue
                    
                    if str(dataGL4[i][2]).strip() == sku:
                        q_g4 = int(float(dataGL4[i][9])) if not pd.isna(dataGL4[i][9]) else 0
                        if q_g4 > 0 and sisaLoad > 0:
                            take = min(q_g4, sisaLoad)
                            refill_output.append([dataGL4[i][1], sku, dataGL4[i][3], dataGL4[i][4], dataGL4[i][5], q_g4, take, q_gl3_val])
                            sisaLoad -= take
                            if sisaLoad <= 0: break
        
        if refill_output:
            df_refill_final = pd.DataFrame(refill_output, columns=["BIN", "SKU", "BRAND", "ITEM NAME", "VARIANT", "QTY BIN AMBIL", "LOAD", "QTY GL3"])

        # --- SUB 4: CREATE OVERSTOCK SHEET ---
        overstock_output = []
        if not df_gl3.empty:
            for row in df_gl3.values:
                bin_over = str(row[1]).upper() if not pd.isna(row[1]) else ""
                if "RAK" in bin_over: continue

                sku_g3 = str(row[2]).strip()
                qty_sys = int(float(row[9]))
                if qty_sys > 24:
                    load_os = qty_sys - 24
                    # Jika dictTrans kosong (karena file tidak upload), defaultnya dianggap 0
                    if dictTrans.get(sku_g3, 0) >= 7:
                        load_os = math.ceil(load_os / 3)
                    
                    if load_os > 0:
                        overstock_output.append([row[1], sku_g3, row[3], row[4], row[5], qty_sys, load_os])

        if overstock_output:
            df_overstock_final = pd.DataFrame(overstock_output, columns=["BIN", "SKU", "BRAND", "ITEM NAME", "VARIANT", "QTY BIN AMBIL", "LOAD"])

    except Exception as e:
        print(f"Error caught: {e}")

    return df_gl3, df_gl4, df_refill_final, df_overstock_final
def putaway_system(df_ds, df_asal):
    if df_ds is None or df_asal is None:
        empty = pd.DataFrame()
        return empty, empty, empty, empty, empty, empty

    try:
        df_asal_updated = df_asal.copy()
        
        # Penentuan Kolom Dinamis
        def get_col_idx(df, keywords, default_idx):
            for i, col in enumerate(df.columns):
                if any(k.lower() in str(col).lower() for k in keywords):
                    return i
            return default_idx

        c_bin_a = get_col_idx(df_asal, ['bin', 'lokasi'], 1)
        c_sku_a = get_col_idx(df_asal, ['sku', 'item code'], 2)
        c_qty_a = get_col_idx(df_asal, ['qty system', 'quantity', 'stok'], 9)

        c_bin_d = get_col_idx(df_ds, ['bin', 'tujuan'], 0)
        c_sku_d = get_col_idx(df_ds, ['sku', 'item'], 1)
        c_qty_d = get_col_idx(df_ds, ['qty', 'jumlah'], 2)

        # 1. Dictionary Mapping
        bin_qty_dict = {}
        for _, row in df_asal_updated.iterrows():
            try:
                key = f"{str(row.iloc[c_bin_a])}|{str(row.iloc[c_sku_a])}"
                qty = pd.to_numeric(row.iloc[c_qty_a], errors='coerce')
                bin_qty_dict[key] = qty if pd.notna(qty) else 0
            except: continue

        # 2. Main Logic
        out_data = []
        for _, row in df_ds.iterrows():
            try:
                sku = str(row.iloc[c_sku_d])
                diff_qty = pd.to_numeric(row.iloc[c_qty_d], errors='coerce')
                if pd.isna(diff_qty) or diff_qty <= 0: continue
                
                bin_tujuan = str(row.iloc[c_bin_d])
                rem = int(diff_qty)
                
                # Prioritas Pencarian
                patterns = ["STAGING LT.3", "STAGGING LT.3", "STAGING", "STAGGING", "KARANTINA", "NORMAL"]
                for pattern in patterns:
                    if rem <= 0: break
                    for key in list(bin_qty_dict.keys()):
                        qty_avail = bin_qty_dict[key]
                        if qty_avail <= 0: continue
                        b_name, s_name = key.split("|")
                        if s_name != sku: continue
                        
                        match = False
                        if pattern == "NORMAL":
                            if not any(x in b_name.upper() for x in ["STAG", "KARANTINA"]): match = True
                        else:
                            if pattern in b_name.upper(): match = True
                        
                        if match:
                            take = min(rem, qty_avail)
                            bin_qty_dict[key] -= take
                            rem -= take
                            out_data.append([bin_tujuan, sku, int(diff_qty), b_name, take, rem, 
                                            "FULLY SETUP" if rem == 0 else "PARTIAL SETUP"])
                            if rem <= 0: break
                
                if rem > 0:
                    out_data.append([bin_tujuan, sku, int(diff_qty), "(NO BIN)", 0, rem, "PERLU CARI STOCK MANUAL"])
            except: continue

        # 3. Output Preparation
        df_comp = pd.DataFrame(out_data, columns=["BIN ASAL", "SKU", "QTY PUTAWAY", "BIN DITEMUKAN", "QUANTITY", "DIFF", "STATUS"])
        
        for idx in df_asal_updated.index:
            key = f"{str(df_asal_updated.iloc[idx, c_bin_a])}|{str(df_asal_updated.iloc[idx, c_sku_a])}"
            if key in bin_qty_dict:
                df_asal_updated.iloc[idx, c_qty_a] = bin_qty_dict[key]

        # --- INI BAGIAN YANG TADI HILANG / BERUBAH ---
        df_plist = df_comp[df_comp['STATUS'].str.contains("SETUP")].copy()
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

        df_kurang = df_comp[df_comp['STATUS'] == "PERLU CARI STOCK MANUAL"].copy()
        
        # --- STAGGING & PUTAWAY OUTSTANDING ---
        mask_out = (
            (df_asal_updated.iloc[:, c_qty_a] > 0) & 
            (
                df_asal_updated.iloc[:, c_bin_a].astype(str).str.upper().str.contains("STAG", na=False) | 
                df_asal_updated.iloc[:, c_bin_a].astype(str).str.upper().str.contains("PUTAWAY", na=False)
            )
        )
        df_outstanding = df_asal_updated[mask_out].copy()

        return df_comp, df_plist, df_kurang, df_comp, df_outstanding, df_asal_updated

    except Exception as e:
        print(f"Detail Error: {e}")
        empty = pd.DataFrame()
        return empty, empty, empty, empty, empty, empty
        
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
            'BIN AWAL': bin_fisik, 
            'SKU': sku, 
            'QTY SCAN': 1,
            'Keterangan': keterangan, 
            'Total Qty Setup/Terjual': qty_val,
            'Bin After Set Up': bin_aft, 
            'Invoice': inv
        })

    df_res_raw = pd.DataFrame(final_results)
    
    # --- FIX DUPLICATE COLUMN & CLEAN GROUPBY ---
    df_res = df_res_raw.groupby(['BIN AWAL', 'SKU', 'Keterangan', 'Bin After Set Up', 'Invoice'], dropna=False).agg({
        'QTY SCAN': 'sum',
        'Total Qty Setup/Terjual': 'sum'
    }).reset_index()

    # FORCE: Pastikan kolom 'Keterangan' adalah kolom tunggal, bukan tabel duplikat
    df_res = df_res.loc[:, ~df_res.columns.duplicated()]
    df_res['Keterangan'] = df_res['Keterangan'].fillna('').astype(str)

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

        # Kondisi: DONE SET UP (QTY MISSMATCH)
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
    
import pandas as pd
import streamlit as st
from datetime import datetime
import pytz
from supabase import create_client, Client

# --- 1. CONFIG SUPABASE (GANTI PAKAI DATA LU) ---
SUPABASE_URL = "https://ufhjrsxzcffdfswfqlzk.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVmaGpyc3h6Y2ZmZGZzd2ZxbHprIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYxNTI5NjgsImV4cCI6MjA5MTcyODk2OH0.DDlKkXU5-nVvNYK_uLYzXLgaj8oDT4s8vbjAoWMWacI"
@st.cache_resource
def init_supabase():
    from supabase import create_client
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

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
                    supabase.table("retur_out_v3").insert(records).execute()
                    
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
        response = supabase.table("retur_out_v3").select("*").execute()
        df_db = pd.DataFrame(response.data)

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
                    supabase.table("retur_out_v3").delete().eq("id", target_id).execute()
                    st.success("Data berhasil dihapus dari Cloud!")
                    st.rerun()
        else:
            st.info("❌ Data kosong, Silakan upload file.")

    except Exception as e:
        st.error(f"Sistem Gagal Memuat Cloud Database: {e}")


import pandas as pd
import io

def process_justification(df_case, df_tracking, df_po):
    # 1. Copy data & Standarisasi Header ke Huruf Besar
    res = df_case.copy()
    res.columns = [str(c).upper().strip() for c in res.columns]
    
    df_tracking = df_tracking.copy()
    df_tracking.columns = [str(c).upper().strip() for c in df_tracking.columns]
    
    df_po = df_po.copy()
    df_po.columns = [str(c).upper().strip() for c in df_po.columns]

    # 2. Aggregasi Tracking Berdasarkan Kolom Baru (A-M)
    # Kolom C (Index 2) = SKU
    sku_col_track = df_tracking.columns[2] 
    
    track_agg = df_tracking.groupby(sku_col_track).agg({
        df_tracking.columns[4]: 'sum',   # E: Current Stock
        df_tracking.columns[5]: 'sum',   # F: Total_Stockin
        df_tracking.columns[6]: 'sum',   # G: Total_adj_plus
        df_tracking.columns[7]: 'sum',   # H: Total trf_in
        df_tracking.columns[8]: 'sum',   # I: Total draft_trf_in
        df_tracking.columns[9]: 'sum',   # J: Total Sales
        df_tracking.columns[10]: 'sum',  # K: Total_adj_minus
        df_tracking.columns[11]: 'sum',  # L: Total draft_trf_out
        df_tracking.columns[12]: 'sum'   # M: Total trf_out
    }).reset_index()

    # Nama kolom sementara untuk proses join dan perhitungan
    track_agg.columns = ['SKU_KEY', '_E_CURR', '_F_IN', '_G_ADJ_P', '_H_TRF_IN', '_I_DRAFT_IN', '_J_SALES', '_K_ADJ_M', '_L_DRAFT_OUT', '_M_TRF_OUT']
    
    # Clean SKU agar formatnya sama
    track_agg['SKU_KEY'] = track_agg['SKU_KEY'].astype(str).str.split('.').str[0].str.strip().str.upper()
    res['SKU_KEY_JOIN'] = res['SKU'].astype(str).str.split('.').str[0].str.strip().str.upper()

    # 3. Merge Data Case dengan Data Tracking
    res = res.merge(track_agg, left_on='SKU_KEY_JOIN', right_on='SKU_KEY', how='left').fillna(0)

    # 4. Pemetaan ke Kolom Final
    res['CURRENT STOCK']      = res['_E_CURR']
    res['TOTAL SALES']        = res['_J_SALES']
    res['TOTAL_STOCKIN']      = res['_F_IN']
    res['TOTAL_ADJ_MINUS']    = res['_K_ADJ_M']
    res['TOTAL_ADJ_PLUS']     = res['_G_ADJ_P']
    res['TOTAL DRAFT_TRF_IN'] = res['_I_DRAFT_IN']
    res['TOTAL DRAFT_TRF_OUT']= res['_L_DRAFT_OUT']
    res['TOTAL TRF_IN']       = res['_H_TRF_IN']
    res['TOTAL TRF_OUT']      = res['_M_TRF_OUT']

    # 5. Rumus Baru Sesuai Instruksi
    # REAL QTY = (F + H + I) - (J + L + M)
    res['REAL QTY'] = (res['TOTAL_STOCKIN'] + res['TOTAL TRF_IN'] + res['TOTAL DRAFT_TRF_IN']) - \
                      (res['TOTAL SALES'] + res['TOTAL DRAFT_TRF_OUT'] + res['TOTAL TRF_OUT'])
    
    # GAP ADJUSMENT = G - K
    res['GAP ADJUSMENT'] = res['TOTAL_ADJ_PLUS'] - res['TOTAL_ADJ_MINUS']

    # 6. Update Logika Justifikasi
    def run_formula(row):
        try:
            j2 = round(float(row['QTY SYSTEM']), 2) 
            k2 = round(float(row['QTY SO']), 2)     
            l2 = round(float(row['CURRENT STOCK']), 2) 
            m2 = round(float(row['TOTAL SALES']), 2)   
            n2 = round(float(row['TOTAL_STOCKIN']), 2) 
            r2 = round(float(row['TOTAL TRF_IN']), 2)
            i2 = round(float(row['TOTAL DRAFT_TRF_IN']), 2) # Tambahan I2
            t2 = round(float(row['REAL QTY']), 2)      
            u2 = round(float(row['GAP ADJUSMENT']), 2) 

            # Logika Justifikasi
            if (j2 > k2 and u2 > 0) or (j2 < k2 and u2 < 0):
                return "KESALAHAN ADJUSMENT"
            
            # Update: Memasukkan unsur Stockin Baru (F+H+I)
            if (n2 + r2 + i2) < m2 or t2 < 0:
                return "CEK SALES/RTO"
            
            if t2 == l2 and t2 != 0:
                return "CEK ULANG HASIL REKON"
            
            if ((t2 == 0 and u2 == 0 and l2 != 0) or 
                (j2 > k2 and l2 > t2) or 
                (j2 < k2 and l2 != 0 and t2 != 0)):
                return "INDIKASI BUG SISTEM"
            
            return "UNDEFINED"
        except:
            return "ERROR DATA"

    res['JUSTIFICATION'] = res.apply(run_formula, axis=1)

    # 7. Hitung TOTAL PO IN
    sku_col_po = df_po.columns[3]
    po_counts = df_po[sku_col_po].astype(str).str.split('.').str[0].value_counts().to_dict()
    res['TOTAL PO IN'] = res['SKU_KEY_JOIN'].apply(lambda x: po_counts.get(x, 0))

    # 8. Susun Urutan Header Final
    ordered_headers = [
        'IDENTIFY', 'BIN', 'SKU', 'BRAND', 'ITEM NAME', 'VARIANT', 'SUB KATEGORI', 
        'HARGA BELI', 'HARGA JUAL', 'QTY SYSTEM', 'QTY SO', 'CURRENT STOCK', 
        'TOTAL SALES', 'TOTAL_STOCKIN', 'TOTAL_ADJ_MINUS', 'TOTAL_ADJ_PLUS', 
        'TOTAL DRAFT_TRF_IN', 'TOTAL DRAFT_TRF_OUT', 'TOTAL TRF_IN', 'TOTAL TRF_OUT', 
        'REAL QTY', 'GAP ADJUSMENT', 'JUSTIFICATION', 'TOTAL PO IN'
    ]

    final_cols = [col for col in ordered_headers if col in res.columns]
    return res[final_cols]
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

import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection
import datetime as dt_logic
from io import BytesIO
import plotly.express as px

# --- 1. DATABASE ENGINE (DIRECT INITIALIZATION) ---
# Gue ganti logic-nya biar langsung nembak URL & KEY lu biar gak error ConnectionRefused lagi.
SUPABASE_URL = "https://ufhjrsxzcffdfswfqlzk.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVmaGpyc3h6Y2ZmZGZzd2ZxbHprIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYxNTI5NjgsImV4cCI6MjA5MTcyODk2OH0.DDlKkXU5-nVvNYK_uLYzXLgaj8oDT4s8vbjAoWMWacI"

# Inisialisasi koneksi dengan bypass secrets
conn = st.connection(
    "supabase",
    type=SupabaseConnection,
    url=SUPABASE_URL,
    key=SUPABASE_KEY
)

def save_reject_data(df):
    # Supabase butuh list of dicts. Nama kolom case-sensitive (disarankan lowercase di DB)
    data_dict = df.to_dict(orient='records')
    conn.table("reject_list").insert(data_dict).execute()

def delete_reject_item(row_id):
    # rowid di SQLite diganti dengan 'id' (Primary Key) di Supabase
    conn.table("reject_list").delete().eq("id", row_id).execute()

def clear_all_data():
    # Menghapus semua data (Force delete menggunakan filter id > 0)
    conn.table("reject_list").delete().gt("id", 0).execute()
    st.rerun()

# --- 2. UI MENU ---
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
        }

        [data-testid="stMetricDelta"] > div {
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

    with tab_entry:
        with st.form("form_reject_new", clear_on_submit=True):
            cabang_input = st.selectbox("📍 LOKASI OPERASIONAL", ["SURABAYA", "SIDOARJO", "SEMARANG"])
            col1, col2 = st.columns(2)
            with col1:
                bin_awal = st.text_input("BIN AWAL")
                bin_val = st.selectbox("BIN TUJUAN", ["REJECT DC", "DEFECT DC", "DEFECT STORE", "REJECT STORE"])
                sku = st.text_input("SKU")
                article = st.text_input("NAMA BARANG")
            with col2:
                size = st.text_input("SIZE")
                kategori = st.selectbox("KATEGORI DEFECT", ["D1", "D2", "D3", "D4", "R1", "R3", "R4", "HANYA SEBELAH KIRI", "HANYA SEBELAH KANAN", "BERBEDA ARTICLE", "BERBEDA SIZE"])
                keterangan = st.text_area("DETAIL KERUSAKAN")

            btn_submit = st.form_submit_button("📤 UPLOAD SINGLE LIST")

        if btn_submit and sku:
            jam = (dt_logic.datetime.now() + dt_logic.timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S")
            new_data = pd.DataFrame([{
                'cabang': cabang_input, 'bin_awal': bin_awal, 'bin': bin_val, 'sku': sku, 
                'article_name': article, 'size': size, 'kategori': kategori, 
                'keterangan': keterangan, 'tanggal_input': jam
            }])
            save_reject_data(new_data)
            st.success(f"✅ SKU {sku} Berhasil Disimpan ke Cloud!")
            st.rerun()

        st.markdown('<div style="background-color: #1a1c27; padding: 10px; border-left: 5px solid #007BFF; border-radius: 5px; margin-top: 20px; margin-bottom: 20px;"><h3 style="color: #007BFF; margin: 0; font-size: 18px; font-weight: 900;">📂 MASS ADJUSTMENT - IMPORT EXCEL</h3></div>', unsafe_allow_html=True)
        
        col_dl, col_up = st.columns([1, 2])
        with col_dl:
            # Sesuaikan dengan kolom di Supabase lo: cabang, bin_awal, bin, sku, article_name, size, kategori, keterangan
            template_cols = ['cabang', 'bin_awal', 'bin', 'sku', 'article_name', 'size', 'kategori', 'keterangan']
            
            # Kita kasih contoh 1 baris kosong atau dummy biar user tau cara isinya
            df_template = pd.DataFrame(columns=template_cols)
            
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_template.to_excel(writer, index=False, sheet_name='Template_Upload')
                
                # --- TAMBAHAN BIAR TEMPLATE CAKEP ---
                workbook = writer.book
                worksheet = writer.sheets['Template_Upload']
                
                # Kasih warna header biar admin lo gak salah baris
                header_format = workbook.add_format({'bold': True, 'bg_color': '#FFD700', 'border': 1})
                for col_num, value in enumerate(df_template.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                    worksheet.set_column(col_num, col_num, 20) # Lebarin kolomnya otomatis

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

            # --- BAGIAN YANG PERLU DIUBAH DI DALAM TAB ENTRY (Mass Upload) ---

            if uploaded_file:
                df_upload = pd.read_excel(uploaded_file)
                
                if st.button("⤴️ IMPORT DATA KE DATABASE"):
                    now_plus_7 = (dt_logic.datetime.now() + dt_logic.timedelta(hours=7))
                    
                    # 1. Pastikan kolom timestamp ada
                    df_upload['tanggal_input'] = now_plus_7.isoformat()
                    
                    # 2. Ambil hanya kolom yang valid
                    db_cols = ['cabang', 'bin_awal', 'bin', 'sku', 'article_name', 'size', 'kategori', 'keterangan', 'tanggal_input']
                    valid_cols = [c for c in db_cols if c in df_upload.columns]
                    df_final = df_upload[valid_cols].copy()
                    
                    # --- FIX UTAMA: HANDLING TYPE ERROR ---
                    # Ubah semua data menjadi string dan hilangkan NaN (sel kosong)
                    df_final = df_final.astype(str).replace('nan', '') 
                    
                    # 3. Simpan data
                    try:
                        save_reject_data(df_final)
                        st.success("✅ Import Cloud Berhasil!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal Simpan: {e}")
    with tab_analytics:
        # Fetch data dari Supabase
        try:
            response = conn.table("reject_list").select("*").execute()
            df_chart = pd.DataFrame(response.data)
            
            # --- FIX FORMAT TANGGAL DI SINI (SETELAH DATAFRAME TERBENTUK) ---
            if not df_chart.empty and 'tanggal_input' in df_chart.columns:
                # Ubah ke datetime, lalu format jadi string yang rapi
                df_chart['tanggal_input'] = pd.to_datetime(df_chart['tanggal_input'], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')
        
        except Exception as e:
            st.error(f"Gagal narik data: {e}")
            df_chart = pd.DataFrame()
        
        standard_codes = ['D1', 'D2', 'D3', 'D4', 'R1', 'R2', 'R3', 'R4']
        if not df_chart.empty:
            # --- LOGIKA MATCHING (WAJIB ADA) ---
            df_non_std = df_chart[~df_chart['kategori'].isin(standard_codes)].copy()
            if not df_non_std.empty:
                def find_matches(row, full_df):
                    matches = full_df[(full_df['sku'] == row['sku']) & (full_df['id'] != row['id'])]
                    return ", ".join(matches['cabang'].unique()) if not matches.empty else "TIDAK ADA"
                df_non_std['MATCH_DI_CABANG'] = df_non_std.apply(lambda x: find_matches(x, df_chart), axis=1)
                df_match_result = df_non_std[df_non_std['MATCH_DI_CABANG'] != "TIDAK ADA"]
            else:
                df_match_result = pd.DataFrame()

            # --- SEARCH & FILTER AREA ---
            col_f1, col_f2 = st.columns([1, 2])
            with col_f1:
                filter_view = st.selectbox("📍 FILTER CABANG:", ["SEMUA", "SURABAYA", "SIDOARJO", "SEMARANG"], key="filter_dash")
            with col_f2:
                # --- TAMBAHAN SEARCH BAR ---
                search_query = st.text_input("🔍 CARI SKU ATAU NAMA BARANG:", placeholder="Ketik SKU / Nama Barang di sini...", key="search_bar")

            # 1. Filter Cabang dulu
            df_final = df_chart if filter_view == "SEMUA" else df_chart[df_chart['cabang'] == filter_view]

            # 2. Filter Search Bar (Jika ada input)
            if search_query:
                df_final = df_final[
                    (df_final['sku'].astype(str).str.contains(search_query, case=False, na=False)) | 
                    (df_final['article_name'].astype(str).str.contains(search_query, case=False, na=False))
                ]

            # --- DASHBOARD LOGIC (METRICS) ---
            total_val = len(df_final)
            defect_cnt = len(df_final[df_final['bin'].str.contains('DEFECT', case=False, na=False)])
            reject_cnt = len(df_final[df_final['bin'].str.contains('REJECT', case=False, na=False)])

            # LOGIKA DELTA (PANAH OTOMATIS)
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

            # BOX METRIC DISPLAY (Akan otomatis update sesuai hasil search)
            m1, m2, m3 = st.columns(3)
            with m1:
                st.markdown(f'<div style="background-color: #1E1E26; padding: 20px; border-radius: 10px; border-left: 5px solid #007BFF;"><p style="color: #888; margin: 0; font-size: 0.9rem;">TOTAL ITEMS</p><h2 style="color: white; margin: 0; font-weight: 800;">{total_val} SKU</h2><span style="color: {col_t}; font-size: 0.8rem; background: {bg_t}; padding: 2px 8px; border-radius: 10px;">{arr_t} {total_val} Result</span></div>', unsafe_allow_html=True)
            with m2:
                p_d = (defect_cnt/total_val*100) if total_val > 0 else 0
                st.markdown(f'<div style="background-color: #1E1E26; padding: 20px; border-radius: 10px; border-left: 5px solid #FFA500;"><p style="color: #888; margin: 0; font-size: 0.9rem;">📦 DEFECT (D)</p><h2 style="color: white; margin: 0; font-weight: 800;">{defect_cnt}</h2><span style="color: {col_d}; font-size: 0.8rem; background: {bg_d}; padding: 2px 8px; border-radius: 10px;">{arr_d} {p_d:.1f}%</span></div>', unsafe_allow_html=True)
            with m3:
                p_r = (reject_cnt/total_val*100) if total_val > 0 else 0
                st.markdown(f'<div style="background-color: #1E1E26; padding: 20px; border-radius: 10px; border-left: 5px solid #FF4B4B;"><p style="color: #888; margin: 0; font-size: 0.9rem;">❌ REJECT (R)</p><h2 style="color: white; margin: 0; font-weight: 800;">{reject_cnt}</h2><span style="color: {col_r}; font-size: 0.8rem; background: {bg_r}; padding: 2px 8px; border-radius: 10px;">{arr_r} {p_r:.1f}%</span></div>', unsafe_allow_html=True)

            # Tabel Detail juga akan mengikuti hasil search
            st.markdown('<div class="detail-header">📋 DETAIL DATABASE CLOUD</div>', unsafe_allow_html=True)
            df_editor = df_final.copy().sort_values('id', ascending=False)
            df_editor['HAPUS'] = False

            event = st.data_editor(
                df_editor,
                column_config={"id": None, "HAPUS": st.column_config.CheckboxColumn("🗑️", default=False)},
                use_container_width=True, hide_index=True, key="database_editor"
            )

            # Logika hapus tetap sama
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
            # --- LOGIK 2: FILTER KATEGORI (KIRI vs KANAN) ---
            # Memastikan jika satu SKU punya kategori 'Kiri', pasangannya harus ada yang 'Kanan'
            def check_kiri_kanan_logic(group):
                categories = group['kategori'].astype(str).str.lower().values
                has_kiri = any('kiri' in cat for cat in categories)
                has_kanan = any('kanan' in cat for cat in categories)
                return has_kiri and has_kanan

            # Filter SKU yang memenuhi syarat Kiri-Kanan
            sku_valid = df_match_result.groupby('sku').filter(check_kiri_kanan_logic)['sku'].unique()
            df_filtered = df_match_result[df_match_result['sku'].isin(sku_valid)].copy()

            if not df_filtered.empty:
                m_col1, m_col2 = st.columns(2)
                with m_col1:
                    st.markdown(f'<div style="background-color: #1E1E26; padding: 20px; border-radius: 10px; border-left: 5px solid #007BFF;"><p style="color: #888; margin: 0; font-size: 0.8rem;">MATCH FOUND (KIRI-KANAN)</p><h2 style="color: white; margin: 0; font-weight: 800;">{len(df_filtered)} Items</h2></div>', unsafe_allow_html=True)
                with m_col2:
                    st.markdown(f'<div style="background-color: #1E1E26; padding: 20px; border-radius: 10px; border-left: 5px solid #6c757d;"><p style="color: #888; margin: 0; font-size: 0.8rem;">UNIQUE SKU</p><h2 style="color: white; margin: 0; font-weight: 800;">{df_filtered["sku"].nunique()}</h2></div>', unsafe_allow_html=True)
                
                # --- LOGIK 1: PIVOT DENGAN KETERANGAN CABANG ---
                df_core = df_filtered[['sku', 'article_name']].drop_duplicates()
                df_temp = df_filtered[['sku', 'cabang']].drop_duplicates()
                
                # Membuat Pivot
                df_pivot = df_temp.pivot(index='sku', columns='cabang', values='cabang').notna()
                
                # Tambahkan kolom "Route Match" untuk melihat cabang mana saja yang cocok
                def get_match_route(row):
                    active_branches = [col for col in df_pivot.columns if row[col] == True]
                    return " ↔️ ".join(active_branches) if len(active_branches) > 1 else active_branches[0]

                df_pivot['Match Route'] = df_pivot.apply(get_match_route, axis=1)
                df_pivot = df_pivot.replace({True: '✅', False: ''})
                
                df_final_match = df_core.merge(df_pivot, on='sku', how='left')

                st.markdown('<div style="margin-bottom: 10px; padding: 5px 0;"><span style="color: #000000 !important; font-size: 1.1rem !important; font-weight: 800 !important;">📋 Summary Match SKU & Kategori</span></div>', unsafe_allow_html=True)
                
                # Tampilkan dengan kolom Match Route di awal setelah Nama Artikel
                cols = ['sku', 'article_name', 'Match Route'] + [c for c in df_temp['cabang'].unique() if c in df_final_match.columns]
                st.data_editor(df_final_match[cols], use_container_width=True, hide_index=True, key="match_pivot_final")
            else:
                st.warning("⚠️ SKU match ditemukan, tapi tidak ada pasangan Kategori yang cocok.")
        else:
            st.success("✅ Tidak ditemukan Reject/Defect Match")

import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
from supabase import create_client, Client

# --- SETUP SUPABASE ---
# Pastikan nama tabel di Supabase lu adalah: submissions
SUPABASE_URL = "https://ufhjrsxzcffdfswfqlzk.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVmaGpyc3h6Y2ZmZGZzd2ZxbHprIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYxNTI5NjgsImV4cCI6MjA5MTcyODk2OH0.DDlKkXU5-nVvNYK_uLYzXLgaj8oDT4s8vbjAoWMWacI"
@st.cache_resource
def init_supabase():
    from supabase import create_client
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()
def convert_all_to_excel(df):
    import io
    output = io.BytesIO()
    
    # 1. Tetap pertahankan filter hanya Status 2
    df_download = df[df['status'] == 2].copy()
    
    if not df_download.empty:
        # 2. Standarisasi kolom (QTY, ARTICLE, SIZE, KETERANGAN)
        # Pastikan kolom-kolom ini tidak bikin error jika salah satu kosong di DB
        if 'qty' not in df_download.columns:
            df_download['qty'] = 1 
            
        if 'article_name' not in df_download.columns:
            df_download['article_name'] = "-" # Nama kolom sesuaikan dengan DB lo (misal: 'article')
        
        if 'size' not in df_download.columns:
            df_download['size'] = "-" 
            
        if 'keterangan' not in df_download.columns:
            df_download['keterangan'] = "-" 
            
        # 3. Pilih kolom termasuk ARTICLE
        # Urutan: SKU, ARTICLE, BIN ASAL, QTY, SIZE, KETERANGAN
        final_df = df_download[['sku', 'article_name', 'bin_asal', 'qty', 'size', 'keterangan']]
        
        # 4. Bikin Header Kapital (Biar rapi di Excel)
        final_df.columns = ['SKU', 'ARTICLE', 'BIN ASAL', 'QTY', 'SIZE', 'KETERANGAN']
        
        # 5. Proses tulis ke Excel
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            final_df.to_excel(writer, index=False, sheet_name='Mass_Request_Setup')
            
            # Auto-fit lebar kolom biar gak usah geser manual
            worksheet = writer.sheets['Mass_Request_Setup']
            for i, col in enumerate(final_df.columns):
                column_len = max(final_df[col].astype(str).map(len).max(), len(col)) + 2
                worksheet.set_column(i, i, column_len)
                
    return output.getvalue()

def project_approval_reject():
    # --- CSS CUSTOM --- 
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
        } 
        [data-testid="stForm"] { border: none !important; padding: 0 !important; } 
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

    # --- TAB 0: INPUT DATA ---
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
                cabang_input = st.selectbox("Pilih Cabang", ["SURABAYA", "SIDOARJO", "SEMARANG"]) 
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
                        supabase.table("submissions").insert(data_insert).execute()
                        st.success(f"✅ Berhasil! Data tercatat jam {ts} WIB") 
                        st.rerun() 
                    except Exception as e: 
                        st.error(f"Gagal simpan ke Supabase: {e}") 
                else: 
                    st.warning("⚠️ Nama Tim dan SKU wajib diisi!") 


    # --- TAB 1: HISTORY & APPROVAL ---
    with tabs[1]:
    # --- TAB 1: HISTORY & APPROVAL (VERSI SUPABASE + CSS FIX) ---
        st.markdown(""" 
            <style> 
            [data-testid="stMain"] div[data-testid="stRadio"] label p { 
                color: #000000 !important;  /* Diubah ke putih agar terlihat di dark mode */
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
            /* CSS UNTUK GARIS TIMELINE */
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
                color: #FFFFFF !important;  /* Pastikan teks markdown umum jadi putih */
            } 
            </style> 
        """, unsafe_allow_html=True)
        tab_sby, tab_sda, tab_smg = st.tabs(["📍 SURABAYA", "📍 SIDOARJO", "📍 SEMARANG"]) 
        cabang_list = [("SURABAYA", tab_sby), ("SIDOARJO", tab_sda), ("SEMARANG", tab_smg)] 

        for cabang_name, tab_obj in cabang_list: 
            with tab_obj: 
                col_search, col_filter = st.columns([1, 1]) 
                with col_search: 
                    search_query = st.text_input(f"🔍 Cari di {cabang_name}:", placeholder="Ketik SKU atau Nama...", key=f"src_{cabang_name}", label_visibility="collapsed").strip() 
                
                with col_filter: 
                    filter_status = st.radio("Pilih Status:", ["Semua", "Waiting Approval", "Waiting Set Up", "Done Set Up"], horizontal=True, key=f"rad_{cabang_name}", label_visibility="collapsed") 

                # Building Query Supabase
                query = supabase.table("submissions").select("*").eq("cabang", cabang_name)

                # Status Mapping
                status_map = {"Waiting Approval": 1, "Waiting Set Up": 2, "Done Set Up": 3}
                if filter_status in status_map:
                    query = query.eq("status", status_map[filter_status])

                try: 
                    response = query.order("id", desc=True).execute()
                    df = pd.DataFrame(response.data)
                except Exception as e: 
                    st.error(f"Database Error: {e}") 
                    df = pd.DataFrame() 
                
                # Filter Search di sisi Client (Pandas) agar lebih fleksibel
                if not df.empty and search_query:
                    search_query = search_query.lower()
                    df = df[
                        df['sku'].str.lower().str.contains(search_query, na=False) | 
                        df['nama_tim'].str.lower().str.contains(search_query, na=False) |
                        df['article_name'].str.lower().str.contains(search_query, na=False)
                    ]

                # --- BAGIAN LOGIKA TAMPILAN (YANG TADI SALAH INDENTASI) ---
                if df.empty: 
                    st.info(f"📭 Belum ada data pengajuan untuk cabang {cabang_name}.") 
                else: 
                    # --- TOMBOL DOWNLOAD MASSAL (VERSI RAPI & KECIL) ---
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

                    # 2. LOOP DATA (Baru masuk ke detail satu per satu)
                    for index, row in df.iterrows(): 
                        with st.expander(f"📦 {row['sku']} - {row['article_name']} | {row['nama_tim']}"):
                            st.markdown(f"### 📑 Detail [ID: {row['id']}]")
                            
                            # --- Detail Kolom ---
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

                            # --- Progres Timeline ---
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
                                        supabase.table("submissions").update({"status": 2, "approved_by": n_app}).eq("id", row['id']).execute()
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
                                            supabase.table("submissions").update({"status": 3, "setup_by": n_set}).eq("id", row['id']).execute()
                                            st.rerun() 
                                        st.markdown('</div>', unsafe_allow_html=True) 

                            # --- NOTE & DELETE ---
                            st.write("---") 
                            c_note = row.get('additional_note') or "" 
                            n_note = st.text_area("📝 Catatan Tambahan:", value=c_note, key=f"note_area_{row['id']}") 
                            
                            if n_note != c_note: 
                                if st.button("💾 Update Note", key=f"sn_btn_{row['id']}"): 
                                    supabase.table("submissions").update({"additional_note": n_note}).eq("id", row['id']).execute()
                                    st.success("Note tersimpan!")
                                    st.rerun() 

                            with st.expander("🗑️ Hapus"): 
                                if st.button(f"Konfirmasi Hapus {row['sku']}", key=f"del_btn_{row['id']}"): 
                                    supabase.table("submissions").delete().eq("id", row['id']).execute()
                                    st.rerun() 

import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import uuid
from supabase import create_client, Client

# --- SETUP SUPABASE ---
SUPABASE_URL = "https://ufhjrsxzcffdfswfqlzk.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVmaGpyc3h6Y2ZmZGZzd2ZxbHprIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYxNTI5NjgsImV4cCI6MjA5MTcyODk2OH0.DDlKkXU5-nVvNYK_uLYzXLgaj8oDT4s8vbjAoWMWacI"
@st.cache_resource
def init_supabase():
    from supabase import create_client
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

def project_mutasi_karantina():
    # --- CSS UI ---
    st.markdown("""
    <style>
        /* 1. Targetkan hanya label judul input di area UTAMA (Main), bukan Sidebar */
        section[data-testid="stMain"] div[data-testid="stWidgetLabel"] label {
            color: #E0E0E0 !important;
            font-weight: 600 !important;
        }

        /* 2. Overwrite Khusus Radio Button di area utama agar teks pilihannya Hitam */
        section[data-testid="stMain"] div[data-testid="stRadio"] label p {
            color: #000000 !important;
            font-weight: 700 !important;
        }

        /* 3. Menggelapkan Box Input hanya di area utama */
        section[data-testid="stMain"] div[data-testid="stTextInput"] > div > div, 
        section[data-testid="stMain"] div[data-testid="stTextArea"] > div > div,
        section[data-testid="stMain"] div[data-testid="stNumberInput"] > div > div,
        section[data-testid="stMain"] div[data-testid="stSelectbox"] > div > div {
            background-color: #1a1c27 !important;
            border: 1px solid #3d4156 !important;
            border-radius: 8px !important;
        }

        /* 4. Memastikan teks di dalam kolom input berwarna putih */
        section[data-testid="stMain"] input, 
        section[data-testid="stMain"] textarea, 
        section[data-testid="stMain"] div[data-baseweb="select"] span {
            color: white !important;
        }

        /* 5. Khusus Number Input (Quantity) & Tombol Plus Minus */
        section[data-testid="stMain"] div[data-testid="stNumberInput"] input {
            color: white !important;
            background-color: #1a1c27 !important;
        }
        section[data-testid="stMain"] div[data-testid="stNumberInput"] button {
            background-color: #1a1c27 !important;
            color: white !important;
            border: 1px solid #3d4156 !important;
        }

        /* 6. Spasi antar pilihan radio */
        section[data-testid="stMain"] div[data-testid="stRadio"] div[role="radiogroup"] {
            gap: 15px;
        }

        /* Header Style */
        .main-header { 
            background: linear-gradient(135deg, #1e468a 0%, #0d1b33 100%); 
            color: white; padding: 15px; border-radius: 10px; font-weight: 800; font-size: 20px;
            margin-bottom: 20px; border-left: 8px solid #cc0000;
        }
        /* Styling Tombol Upload Batch agar berwarna Orange/Red Gradient */
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

        /* Efek Hover (saat kursor di atas tombol) */
        div[data-testid="stForm"] button[kind="primaryFormSubmit"]:hover {
            transform: scale(1.02) !important;
            box-shadow: 0px 4px 15px rgba(255, 65, 108, 0.4) !important;
        }

        /* Memberikan border berwarna pada area upload file */
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

    # --- TAB 1: INPUT (SINGLE & MULTIPLE) ---
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
                
                # Urutan dibalik: Notes dulu (jadi selectbox), baru Alasan (jadi text_input/area)
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
                        supabase.table("mutasi_karantina").insert(data).execute()
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
                        bulk_data = []
                        for _, row in df.iterrows():
                            bulk_data.append({
                                "batch_id": bid, "timestamp": ts, "nama_tim": pic_m,
                                "bin_awal": str(row.get('BIN AWAL', '')), "bin_tujuan": str(row.get('BIN TUJUAN', '')),
                                "sku": str(row.get('SKU', '')), "article_name": str(row.get('ARTICLE NAME', '')),
                                "quantity": int(row.get('QUANTITY', 0)), "notes": str(row.get('NOTES', '')),
                                "alasan": str(row.get('ALASAN', 'Bulk Upload')), "status": 1
                            })
                        supabase.table("mutasi_karantina").insert(bulk_data).execute()
                        st.success(f"Berhasil Upload {len(bulk_data)} Item! Batch: {bid}")
                        st.rerun()

    # --- TAB 2: MONITORING & BATCH APPROVAL ---
    with tabs[1]:
    # CSS Custom (Input dari lu dimasukkan ke sini)
        st.markdown(""" 
            <style> 
            [data-testid="stMain"] div[data-testid="stRadio"] label p { 
                color: #FFFFFF !important;  /* Fix: Diubah ke putih agar terlihat di dark mode */
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
            /* CSS UNTUK GARIS TIMELINE */
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
        # Ambil data dari Supabase
        res = supabase.table("mutasi_karantina").select("*").order("id", desc=True).execute()
        df_res = pd.DataFrame(res.data)

        if df_res.empty:
            st.info("Belum ada data pengajuan.")
        else:
            # --- 1. SEARCH & FILTER UI ---
            # Dibuat dalam kolom agar rapi
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

            # --- 2. LOGIKA FILTERING BERLAPIS ---
            df_filtered = df_res.copy()

            # A. Filter berdasarkan Status
            if filter_status == "Belum Approved":
                df_filtered = df_filtered[df_filtered['status'] == 1]
            elif filter_status == "Done Approval":
                df_filtered = df_filtered[df_filtered['status'] == 2]
            elif filter_status == "Final Done":
                df_filtered = df_filtered[df_filtered['status'] == 3]

            # B. Filter berdasarkan SKU
            if search_sku:
                mask = df_filtered['sku'].str.contains(search_sku, case=False, na=False)
                # Ambil batch_id yang mengandung SKU tersebut
                valid_batches = df_filtered[mask]['batch_id'].unique()
                df_display = df_filtered[df_filtered['batch_id'].isin(valid_batches)]
            else:
                df_display = df_filtered

            # --- 3. LOOPING DISPLAY ---
            batches = df_display['batch_id'].unique()
            
            if len(batches) == 0:
                st.warning("Tidak ada data yang cocok dengan filter.")
            else:
                for b_id in batches:
                    items = df_display[df_display['batch_id'] == b_id]
                    head = items.iloc[0]
                    stat = int(head['status'])

                    # Penanda warna icon berdasarkan status
                    icon = "🔴" if stat == 1 else "🟡" if stat == 2 else "🟢"

                    with st.expander(f"{icon} {b_id} | {head['nama_tim']} | {len(items)} Item"):
                        st.write(f"**Waktu:** {head['timestamp']} | **Alasan:** {head['alasan']}")
                        st.dataframe(items[['bin_awal', 'bin_tujuan', 'sku', 'article_name', 'quantity']], use_container_width=True)
                        
                        st.write("---")
                        c_st1, c_st2, c_st3 = st.columns(3)
                        
                        with c_st1: # STEP 1
                            st.markdown("1️⃣ **Approval**")
                            if stat == 1:
                                n_app = st.text_input("Approve By:", key=f"app_{b_id}")
                                if st.button("Approve Batch", key=f"bt_app_{b_id}", disabled=not n_app, type="primary"):
                                    supabase.table("mutasi_karantina").update({"status": 2, "approved_by": n_app}).eq("batch_id", b_id).execute()
                                    st.rerun()
                            else: 
                                st.success(f"By: {head.get('approved_by')}")

                        with c_st2: # STEP 2 (LINE)
                            active = "line-active" if stat >= 2 else ""
                            st.markdown(f'<div class="timeline-line {active}"></div>', unsafe_allow_html=True)
                            if stat == 2: st.caption("On Process...")

                        with c_st3: # STEP 3
                            st.markdown("2️⃣ **Final Done**")
                            if stat == 2:
                                n_fin = st.text_input("Selesai By:", key=f"fin_{b_id}")
                                if st.button("Finish Batch", key=f"bt_fin_{b_id}", disabled=not n_fin, type="primary"):
                                    supabase.table("mutasi_karantina").update({"status": 3, "setup_by": n_fin}).eq("batch_id", b_id).execute()
                                    st.rerun()
                            elif stat == 3: 
                                st.success(f"Done: {head.get('setup_by')}")

                        # Tombol Hapus (Dibuat kecil di bawah)
                        if st.button(f"🗑️ Hapus Batch {b_id}", key=f"del_{b_id}"):
                            supabase.table("mutasi_karantina").delete().eq("batch_id", b_id).execute()
                            st.rerun()
    # --- TAB 3: WORKING LIST (ON PROCESS) ---
    with tabs[2]:
        st.markdown("### 📋Template Mutasi")
        
        # Ambil data status 2 (Done Approval / Kuning)
        res_working = supabase.table("mutasi_karantina").select("*").eq("status", 2).order("timestamp", desc=True).execute()
        df_working = pd.DataFrame(res_working.data)

        if df_working.empty:
            st.info("Tidak ada mutasi yang sedang diproses (Kuning).")
        else:
            # Filter Pencarian
            search_work = st.text_input("🔍 Cari Data di Working List:", key="search_work_v2")
            
            if search_work:
                mask = df_working.apply(lambda row: row.astype(str).str.contains(search_work, case=False).any(), axis=1)
                df_display_work = df_working[mask]
            else:
                df_display_work = df_working

            # Pilih kolom sesuai request
            cols_final = ["batch_id", "bin_awal", "bin_tujuan", "sku", "quantity", "notes"]
            
            # Pastikan kolom notes ada, jika tidak ada di DB beri string kosong
            if 'notes' not in df_display_work.columns:
                df_display_work['notes'] = ""

            st.write(f"Menampilkan **{len(df_display_work)}** baris data.")

            # Menampilkan tabel dengan konfigurasi header yang rapi
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
                hide_index=True # Menghilangkan angka index di kiri agar lebih clean
            )

            if st.button("🔄 Refresh Working List", key="btn_refresh_work"):
                st.rerun()
import pandas as pd
import streamlit as st
from io import BytesIO

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="RTO Compare System", layout="wide")

# --- 2. FUNGSI UI & CSS ---
def apply_custom_ui():
    st.markdown("""
    <style>
        .stApp { background-color: #f0f7ff !important; }
        .hero-header {
            background-color: #007BFF;
            color: white;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            margin-bottom: 25px;
            font-weight: bold;
            font-size: 26px;
        }
        .m-box {
            background-color: white;
            padding: 15px;
            border-radius: 10px;
            border-left: 5px solid #007BFF;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
            text-align: center;
        }
        .m-lbl { font-size: 14px; color: #666; display: block; }
        .m-val { font-size: 22px; font-weight: bold; color: #007BFF; }
        div.stButton > button {
            background-color: #007BFF !important;
            color: white !important;
            font-weight: bold !important;
            height: 50px !important;
            width: 100% !important;
            border-radius: 8px !important;
        }
    </style>
    <div class="hero-header">RTO RECEIVING PROCESS</div>
    """, unsafe_allow_html=True)

# --- 3. LOGIKA ALOKASI & PERHITUNGAN ---
def process_rto_logic(df_scan, df_tf):
    # Inisialisasi awal agar tidak ada error 'not defined'
    metrics = {"total_tf": 0, "total_scan": 0, "kurang_tf": 0, "lebih_tf": 0}
    df_hasil = pd.DataFrame()
    df_split_detail = pd.DataFrame()
    df_kurang = pd.DataFrame()
    df_lebih = pd.DataFrame()

    # Mapping Index (Sesuaikan dengan file lu)
    scan_sku_idx, scan_qty_idx = 0, 1
    tf_no_idx, tf_sku_idx, tf_qty_idx = 0, 3, 7

    # Pembersihan Data
    df_scan = df_scan.copy()
    df_tf = df_tf.copy()
    df_scan.iloc[:, scan_sku_idx] = df_scan.iloc[:, scan_sku_idx].astype(str).str.strip().str.upper()
    df_tf.iloc[:, tf_sku_idx] = df_tf.iloc[:, tf_sku_idx].astype(str).str.strip().str.upper()
    
    col_tf_no = df_tf.columns[tf_no_idx]
    col_tf_sku = df_tf.columns[tf_sku_idx]
    
    # Agregasi Total
    agg_scan = df_scan.groupby(df_scan.columns[scan_sku_idx])[df_scan.columns[scan_qty_idx]].sum()
    agg_tf = df_tf.groupby(df_tf.columns[tf_sku_idx])[df_tf.columns[tf_qty_idx]].sum()
    
    # Gabungkan untuk perbandingan
    comp = pd.concat([agg_scan, agg_tf], axis=1).fillna(0)
    comp.columns = ['QTY_SCAN', 'QTY_TF']
    
    # ISI METRICS
    metrics["total_tf"] = int(agg_tf.sum())
    metrics["total_scan"] = int(agg_scan.sum())
    metrics["kurang_tf"] = int(comp[comp['QTY_SCAN'] > comp['QTY_TF']].apply(lambda x: x['QTY_SCAN'] - x['QTY_TF'], axis=1).sum())
    metrics["lebih_tf"] = int(comp[comp['QTY_TF'] > comp['QTY_SCAN']].apply(lambda x: x['QTY_TF'] - x['QTY_SCAN'], axis=1).sum())

    # LOGIKA KURANG TF (Fisik > Sistem)
    selisih_kurang = comp[comp['QTY_SCAN'] > comp['QTY_TF']].copy().reset_index()
    selisih_kurang.rename(columns={selisih_kurang.columns[0]: 'SKU'}, inplace=True)
    if not selisih_kurang.empty:
        df_kurang = pd.merge(selisih_kurang, df_tf[[col_tf_no, col_tf_sku]], left_on='SKU', right_on=col_tf_sku, how='left')
        df_kurang.rename(columns={col_tf_no: 'NO TRANSFER'}, inplace=True)
        df_kurang['NO TRANSFER'] = df_kurang['NO TRANSFER'].fillna("TIDAK ADA DI TF")
        df_kurang = df_kurang[['NO TRANSFER', 'SKU', 'QTY_SCAN', 'QTY_TF']]

    # LOGIKA LEBIH TF (Sistem > Fisik)
    selisih_lebih = comp[comp['QTY_TF'] > comp['QTY_SCAN']].copy().reset_index()
    selisih_lebih.rename(columns={selisih_lebih.columns[0]: 'SKU'}, inplace=True)
    if not selisih_lebih.empty:
        df_lebih = pd.merge(selisih_lebih, df_tf[[col_tf_no, col_tf_sku]], left_on='SKU', right_on=col_tf_sku, how='left')
        df_lebih.rename(columns={col_tf_no: 'NO TRANSFER'}, inplace=True)
        df_lebih = df_lebih[['NO TRANSFER', 'SKU', 'QTY_SCAN', 'QTY_TF']]

    # FIFO ALOKASI
    hasil_alokasi = []
    df_tf_work = df_tf.copy()
    for sku in agg_scan.index:
        available_qty = agg_scan[sku]
        mask_tf = df_tf_work.iloc[:, tf_sku_idx] == sku
        for idx, row in df_tf_work[mask_tf].iterrows():
            if available_qty <= 0: break
            needed = float(row.iloc[tf_qty_idx])
            allocated = min(needed, available_qty)
            if allocated > 0:
                hasil_alokasi.append({'No Transfer': row.iloc[tf_no_idx], 'SKU': sku, 'Qty Alokasi': allocated})
                available_qty -= allocated

    df_hasil = pd.DataFrame(hasil_alokasi)
    
    # Detail untuk Split TF (Tab 2)
    if not df_hasil.empty:
        df_comp_reset = comp[['QTY_TF']].reset_index()
        df_comp_reset.columns = ['SKU', 'QTY_TF_SISTEM'] 
        df_split_detail = pd.merge(df_hasil, df_comp_reset, on='SKU', how='left')
        df_split_detail = df_split_detail.rename(columns={'Qty Alokasi': 'QTY SCAN', 'QTY_TF_SISTEM': 'QTY_TF'})
    
    return df_hasil, df_split_detail, df_kurang, df_lebih, metrics

# --- 4. MAIN APP ---
def main():
    apply_custom_ui()

    if "rto_data" not in st.session_state:
        st.session_state.rto_data = None

    col1, col2 = st.columns(2)
    with col1:
        file_scan = st.file_uploader("Upload Hasil Scan RTO/RTD", type=['xlsx', 'csv'])
    with col2:
        file_tf = st.file_uploader("Upload Transfer Stock Jezpro", type=['xlsx', 'csv'])

    if file_scan and file_tf:
        if st.button("▶️ RUN DATA COMPARISON"):
            try:
                df_s = pd.read_excel(file_scan) if file_scan.name.endswith('.xlsx') else pd.read_csv(file_scan)
                df_t = pd.read_excel(file_tf) if file_tf.name.endswith('.xlsx') else pd.read_csv(file_tf)
                
                st.session_state.rto_data = process_rto_logic(df_s, df_t)
                st.success("Analisis Selesai!")
            except Exception as e:
                st.error(f"Gagal memproses data: {e}")

    if st.session_state.rto_data:
        df_hasil, df_split, df_kurang, df_lebih, metrics = st.session_state.rto_data

        # 1. METRICS BOX
        m1, m2, m3, m4 = st.columns(4)
        with m1: st.markdown(f'<div class="m-box"><span class="m-lbl">Total Qty TF</span><span class="m-val">{metrics["total_tf"]:,}</span></div>', unsafe_allow_html=True)
        with m2: st.markdown(f'<div class="m-box"><span class="m-lbl">Total Qty Scan</span><span class="m-val">{metrics["total_scan"]:,}</span></div>', unsafe_allow_html=True)
        with m3: st.markdown(f'<div class="m-box"><span class="m-lbl">Total Kurang TF</span><span class="m-val" style="color:red;">{metrics["kurang_tf"]:,}</span></div>', unsafe_allow_html=True)
        with m4: st.markdown(f'<div class="m-box"><span class="m-lbl">Total Lebih TF</span><span class="m-val" style="color:orange;">{metrics["lebih_tf"]:,}</span></div>', unsafe_allow_html=True)

        st.divider()

        # 2. TABS SYSTEM
        t1, t2, t3, t4 = st.tabs(["📊 Compare Alokasi", "✂️ Split TF", "📥 Kurang TF (Fisik > TF)", "📤 Lebih TF (TF > Fisik)"])
        
        with t1:
            st.dataframe(df_hasil, use_container_width=True)
        
        with t2:
            st.subheader("✂️ SPLIT PER NOMOR TRANSFER")
            if not df_split.empty:
                col_no_tf = "No Transfer" if "No Transfer" in df_split.columns else "NO TRANSFER"
                list_tf = sorted(df_split[col_no_tf].unique().tolist())
                selected_tf = st.selectbox("🎯 Pilih Nomor Transfer:", list_tf)
                
                # Filter data
                detail_tf = df_split[df_split[col_no_tf] == selected_tf].copy()
                
                # --- FIX DUPLIKAT: AGREGASI DISINI ---
                # Gabungkan SKU yang sama agar tidak muncul berulang barisnya
                detail_grouped = detail_tf.groupby('SKU').agg({
                    'QTY SCAN': 'sum',
                    'QTY_TF': 'first' # Ambil salah satu nilai TF asli sistem
                }).reset_index()
                
                # Hitung Metric Berdasarkan Data yang sudah bersih
                total_scan_tf = detail_grouped['QTY SCAN'].sum()
                total_tf_sistem = detail_grouped['QTY_TF'].sum()
                
                c1, c2 = st.columns(2)
                c1.metric("Total Qty Scan", f"{total_scan_tf:,.0f}")
                c2.metric("Total Qty TF Sistem", f"{total_tf_sistem:,.0f}")

                st.dataframe(
                    detail_grouped, 
                    use_container_width=True, 
                    hide_index=True
                )

        with t3:
            st.warning("⚠️ SKU yang ada di Fisik tapi di Transfer Stock kurang/tidak ada")
            st.dataframe(df_kurang, use_container_width=True, hide_index=True)
            
        with t4:
            st.error("❌ SKU yang ada di Transfer Stock tapi barang Fisiknya KURANG")
            st.dataframe(df_lebih, use_container_width=True, hide_index=True)

        # 3. DOWNLOAD BUTTON
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_hasil.to_excel(writer, index=False, sheet_name='Alokasi_Detail')
            df_split.to_excel(writer, index=False, sheet_name='Split_TF')
            df_kurang.to_excel(writer, index=False, sheet_name='Kurang_TF')
            df_lebih.to_excel(writer, index=False, sheet_name='Lebih_TF')
        
        st.download_button(
            label="📥 Download Full Report (.xlsx)",
            data=output.getvalue(),
            file_name="RTO_Comparison_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
                
import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

def init_db():
    # Database fisik biar data aman di Surabaya branch
    conn = sqlite3.connect('database_sby.db', check_same_thread=False)
    return conn

def tampilan_balancing_stock():
    # --- 1. CSS CUSTOM (STYLE DASHBOARD PREMIUM) ---
    st.markdown("""
        <style>
        .metric-label-header {
            background-color: #f8f9fa;
            padding: 10px 15px;
            border-left: 5px solid #007BFF;
            border-radius: 4px;
            margin-bottom: 15px;
            margin-top: 20px;
        }
        .metric-card {
            background-color: #1E1E2E;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.3);
            text-align: center;
            color: white;
            min-height: 140px;
            margin-bottom: 10px;
        }
        .metric-value {
            font-size: 28px;
            font-weight: bold;
            margin: 0;
            color: #FFFFFF;
        }
        .metric-label {
            font-size: 12px;
            color: #A0A0A0;
            text-transform: uppercase;
            margin-bottom: 8px;
            letter-spacing: 1px;
        }
        .metric-arrow {
            font-size: 12px;
            margin-top: 8px;
            font-weight: bold;
        }
        .hero-header {
            background-color: #007BFF; /* Biru Hero */
            padding: 15px 25px;
            border-radius: 10px;
            margin-bottom: 25px;
            box-shadow: 0px 4px 12px rgba(0, 123, 255, 0.3);
            text-align: left;
        }
        .hero-text {
            color: white !important;
            margin: 0 !important;
            font-size: 24px !important;
            font-weight: 800 !important;
            letter-spacing: 1.5px;
            text-transform: uppercase;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="hero-header"><p class="hero-text">DISTRIBUTION STOCK CONTROL</p></div>', unsafe_allow_html=True)
    with st.expander("📋 Informasi Format File"):
        st.info("""
        **Format File :**
        - Download Multiple Adjusment dan pastikan pilih **Termasuk yang sudah habis**
        - Data yang dihasilkan adalah data dari total SKU bukan total QTY jadi yang dihitung adalah unique SKU nya
        - Presentase minimal untuk **GL4 ➡️ GL3 adalah 100%**
        - Presentase minimal untuk **ALL DC ➡️ Store adalah 98%**
        """)
    with st.expander("💡Logic Thinking"):
        st.info("""
        **ALur Compare :**
        - **GL3 ➡️ GL4**
            - Compare akan dilakukan dengan acuan SKU dan QTY SYSTEM yang ada di GL4
            - SKU dan QTY SYSTEM yang ada di GL4 namun tidak ada di GL3 akan dilakukan presentase dengan Rumus **(TOTAL STOCK GL4 - TOTAL STOCK BELUM TEREFILL)/TOTAL STOCK GL4
            - Dan akan mengecualikan BIN REJECT, DEFECT, LIVE, ONLINE, STAGGING, PUTAWAY
        - **DC ➡️ STORE**
            - Compare akan dilakukan dengan acuan SKU dan QTY SYSTEM yang ada di Gudang DC
            - SKU dan QTY SYSTEM yang ada di Gudang DC namun tidak ada di Store akan dilakukan presentase dengan Rumus **(TOTAL STOCK DC - TOTAL STOCK BELUM TEREFILL)/TOTAL STOCK DC
            - Dan akan mengecualikan BIN REJECT, DEFECT, LIVE, ONLINE, MARKOM, STAGGING, KARANTINA, OUT    
        """)
    conn = init_db()
    uploaded_file = st.file_uploader("Upload All Stock", type=['xlsx', 'csv'], key="balancer_upload")

    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
            df.columns = [str(c).strip() for c in df.columns]
            df.to_sql('stock_raw', conn, index=False, if_exists='replace')
            st.success("Data Berhasil Diperbarui!")
        except Exception as e:
            st.error(f"Gagal upload: {e}")

    # --- 2. LOGIKA ANALISIS (REVISED: STOK VS STOK COMPARISON) ---
    try:
        df_check = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table' AND name='stock_raw'", conn)
        if df_check.empty:
            st.info("Upload data dulu buat narik metriks.")
            return

        # Ambil kolom secara dinamis
        cols = pd.read_sql("SELECT * FROM stock_raw LIMIT 1", conn).columns
        col_bin = next((c for c in cols if 'BIN' in c.upper()), cols[1])
        col_sku = next((c for c in cols if 'SKU' in c.upper()), cols[2])
        col_qty = next((c for c in cols if 'QTY' in c.upper() or 'SYSTEM' in c.upper()), cols[9])
        col_desc_e = cols[4] # Kolom E untuk Deskripsi

        # --- GLOBAL EXCLUSION FILTER SURABAYA BRANCH ---
        base_excl = f"""
            UPPER("{col_bin}") NOT LIKE '%DEFECT%' AND UPPER("{col_bin}") NOT LIKE '%REJECT%' AND 
            UPPER("{col_bin}") NOT LIKE '%ONLINE%' AND UPPER("{col_bin}") NOT LIKE '%LIVE%' AND
            UPPER("{col_bin}") NOT LIKE '%MARKOM%' AND UPPER("{col_bin}") NOT LIKE '%KARANTINA%' AND
            UPPER("{col_bin}") NOT LIKE '%STAGING%' AND UPPER("{col_bin}") NOT LIKE '%STAGGING%' AND
            UPPER("{col_bin}") NOT LIKE '%PUTAWAY%' AND UPPER("{col_bin}") NOT LIKE '%OUT%' AND
            UPPER("{col_bin}") NOT LIKE '%INB%' AND UPPER("{col_bin}") NOT LIKE '%AMP%' AND
            UPPER("{col_bin}") NOT LIKE '%INB%' AND UPPER("{col_bin}") NOT LIKE '%RAK%'
        """

        # --- DEFINISI AREA FILTER ---
        # Target GL3: Kecualikan PUTAWAY & RAK
        f_target_gl3 = f"UPPER(\"{col_bin}\") LIKE '%GL3%' AND UPPER(\"{col_bin}\") NOT LIKE '%PUTAWAY%' AND UPPER(\"{col_bin}\") NOT LIKE '%RAK%'"
        
        # Source GL4: Area asal stok
        f_source_gl4 = f"""
            UPPER("{col_bin}") LIKE '%GL4%' 
            AND UPPER("{col_bin}") NOT LIKE '%REJECT%' AND UPPER("{col_bin}") NOT LIKE '%DEFECT%' 
            AND UPPER("{col_bin}") NOT LIKE '%LIVE%' AND UPPER("{col_bin}") NOT LIKE '%ONLINE%' 
            AND UPPER("{col_bin}") NOT LIKE '%RAK%'
        """

        # Target Store: TOKO, STORE, GUDANG LT.2
        f_target_store = f"(UPPER(\"{col_bin}\") LIKE '%TOKO%' OR UPPER(\"{col_bin}\") LIKE '%GL2-STORE%' OR UPPER(\"{col_bin}\") LIKE '%GUDANG LT.2%')"
        
        # Source DC: Area pusat
        f_source_dc = f"UPPER(\"{col_bin}\") LIKE '%DC%' AND {base_excl}"

        # --- 1. LOGIKA MISSING (STOK SOURCE > 0 DAN STOK TARGET <= 0) ---
        
        # GL4 to GL3 Tetap (Sesuai Excel 52 SKU)
        q_logic_gl_missing = f"""
            SELECT "{col_sku}" FROM stock_raw 
            WHERE {base_excl}
            GROUP BY "{col_sku}"
            HAVING SUM(CASE WHEN {f_source_gl4} THEN "{col_qty}" ELSE 0 END) > 0
               AND SUM(CASE WHEN {f_target_gl3} THEN "{col_qty}" ELSE 0 END) <= 0
        """

        # DC to Store (TAMBAHAN FILTER: STOK DC WAJIB > 1)
        q_logic_dc_missing = f"""
            SELECT "{col_sku}" FROM stock_raw 
            WHERE {base_excl}
            GROUP BY "{col_sku}"
            HAVING SUM(CASE WHEN {f_source_dc} THEN "{col_qty}" ELSE 0 END) > 1
               AND SUM(CASE WHEN {f_target_store} THEN "{col_qty}" ELSE 0 END) <= 0
        """

        # --- 2. QUERY METRIKS ---
        q_data = pd.read_sql(f"""
            SELECT  
                (SELECT COUNT(DISTINCT "{col_sku}") FROM stock_raw WHERE {base_excl} AND "{col_qty}" > 0) as Total_SKU_Clean,
                (SELECT COUNT(*) FROM (SELECT "{col_sku}" FROM stock_raw WHERE {f_source_dc} GROUP BY "{col_sku}" HAVING SUM("{col_qty}") > 0)) as DC_Clean_Total,
                (SELECT COUNT(*) FROM ({q_logic_dc_missing})) as DC_Missing_Count,
                (SELECT COUNT(*) FROM (SELECT "{col_sku}" FROM stock_raw WHERE {f_source_gl4} GROUP BY "{col_sku}" HAVING SUM("{col_qty}") > 0)) as GL4_Clean_Total,
                (SELECT COUNT(*) FROM ({q_logic_gl_missing})) as GL_Missing_Count
        """, conn).iloc[0]

        # Kalkulasi Variabel Card
        dc_total = int(q_data['DC_Clean_Total'])
        dc_missing = int(q_data['DC_Missing_Count'])
        gl4_total = int(q_data['GL4_Clean_Total'])
        gl4_missing = int(q_data['GL_Missing_Count'])

        # --- 3. TAMPILAN DASHBOARD ---
        st.markdown('<div class="metric-label-header"><h4 style="color: #007BFF; margin: 0; font-size: 16px; font-weight: 900;">📊 PRECENTAGE & BALANCING STOCK</h4></div>', unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f'<div class="metric-card" style="border-left: 5px solid #7B61FF;"><p class="metric-label">📦 Total SKU Aktif</p><p class="metric-value">{int(q_data["Total_SKU_Clean"]):,}</p><p class="metric-arrow" style="color: #00FF00;">↑ OVERALL</p></div>', unsafe_allow_html=True)
        with c2:
            dc_avail = dc_total - dc_missing
            perc = (dc_avail / dc_total * 100) if dc_total > 0 else 0
            st.markdown(f'<div class="metric-card" style="border-left: 5px solid #00C853;"><p class="metric-label">🏪 DC to Store</p><p class="metric-value">{dc_avail:,}</p><p class="metric-arrow" style="color: #00FF00;">↑ {perc:.1f}% Tersedia</p></div>', unsafe_allow_html=True)
        with c3:
            gl_avail = gl4_total - gl4_missing
            perc = (gl_avail / gl4_total * 100) if gl4_total > 0 else 0
            st.markdown(f'<div class="metric-card" style="border-left: 5px solid #FFAB00;"><p class="metric-label">🏗️ GL4 to GL3</p><p class="metric-value">{gl_avail:,}</p><p class="metric-arrow" style="color: #00FF00;">↑ {perc:.1f}% Tersedia</p></div>', unsafe_allow_html=True)

        cc1, cc2 = st.columns(2)
        with cc1:
            perc = (dc_missing / dc_total * 100) if dc_total > 0 else 0
            st.markdown(f'<div class="metric-card" style="border-left: 5px solid #E91E63;"><p class="metric-label">⚠️ Not Yet Distributed DC to Store</p><p class="metric-value">{dc_missing:,} SKU</p><p class="metric-arrow" style="color: #FF5252;">{perc:.1f}% Belum Terdistribusi</p></div>', unsafe_allow_html=True)
        with cc2:
            perc = (gl4_missing / gl4_total * 100) if gl4_total > 0 else 0
            st.markdown(f'<div class="metric-card" style="border-left: 5px solid #FF9800;"><p class="metric-label">⚠️ Not Yet Refill GL4 to GL3</p><p class="metric-value">{gl4_missing:,} SKU</p><p class="metric-arrow" style="color: #FF5252;">{perc:.1f}% Belum Turun</p></div>', unsafe_allow_html=True)

        st.divider()
        st.markdown("### 📋 Detail List SKU Need Distributed")
        t1, t2 = st.tabs(["DC ➔ Store", "GL4 ➔ GL3"])
        
        with t1:
            # Mengambil deskripsi terbaru untuk SKU yang missing
            df_dc = pd.read_sql(f"""
                SELECT "{col_sku}" as SKU, MAX("{col_desc_e}") as Deskripsi 
                FROM stock_raw 
                WHERE "{col_sku}" IN ({q_logic_dc_missing}) 
                GROUP BY "{col_sku}"
            """, conn)
            if not df_dc.empty:
                st.dataframe(df_dc, use_container_width=True)
            else:
                st.info("✅ DC sinkron.")

        with t2:
            # Mengambil deskripsi terbaru untuk SKU yang missing
            df_gl = pd.read_sql(f"""
                SELECT "{col_sku}" as SKU, MAX("{col_desc_e}") as Deskripsi 
                FROM stock_raw 
                WHERE "{col_sku}" IN ({q_logic_gl_missing}) 
                GROUP BY "{col_sku}"
            """, conn)
            if not df_gl.empty:
                st.dataframe(df_gl, use_container_width=True)
            else:
                st.info("✅ GL4 to GL3 sinkron.")

    except Exception as e:
        st.error(f"Error pada sistem analisis: {e}")
    finally:
        conn.close()

def process_picking_audit(file1, file2, file_tracking=None):
    try:
        # Load data utama
        df1 = load_data(file1)
        df2 = load_data(file2)

        data1 = prepare_columns(df1)
        data2 = prepare_columns(df2)

        # 1. Gabungkan data System 1 & System 2
        comparison = pd.merge(
            data1, 
            data2, 
            on=['BIN', 'SKU'], 
            how='outer', 
            suffixes=('_Sys1', '_Sys2')
        ).fillna(0)

        comparison['DIFF'] = comparison['QTY_Sys1'] - comparison['QTY_Sys2']
        discrepancies = comparison[comparison['DIFF'] != 0].copy()

        # 2. Jika ada file tracking, lakukan investigasi selisih
        if file_tracking is not None and not discrepancies.empty:
            df_track = pd.read_excel(file_tracking) 
            
            # AMANKAN DISINI: Paksa astype(str) sebelum di-upper
            df_track_clean = pd.DataFrame({
                'INVOICE': df_track.iloc[:, 0].astype(str),
                'SKU': df_track.iloc[:, 1].astype(str).str.strip().str.upper(),
                'BIN': df_track.iloc[:, 6].astype(str).str.strip().str.upper(),
                'QTY_TRACK': pd.to_numeric(df_track.iloc[:, 10], errors='coerce').fillna(0)
            })

            resolved_list = []
            
            for idx, row in discrepancies.iterrows():
                # Pastikan data pembanding juga dipaksa jadi string & upper
                sku_val = str(row['SKU']).strip().upper()
                bin_sys = str(row['BIN']).strip().upper()
                diff_val = abs(float(row['DIFF']))
                
                # Filter tracking berdasarkan SKU
                match_sku = df_track_clean[df_track_clean['SKU'] == sku_val]
                
                if not match_sku.empty:
                    # 1. Kumpulkan semua Invoice unik
                    all_inv = ", ".join(match_sku['INVOICE'].unique())
                    
                    # 2. Cek apakah ada baris yang BIN-nya cocok
                    match_bin = match_sku[match_sku['BIN'] == bin_sys]
                    
                    # 3. TOTAL QTY di tracking untuk SKU tersebut
                    total_qty_track = abs(match_sku['QTY_TRACK'].sum())
                    
                    bin_exists = not match_bin.empty
                    qty_matches = (total_qty_track == diff_val)
                    
                    if bin_exists and qty_matches:
                        status = "Terjual (Match)"
                    elif bin_exists and not qty_matches:
                        status = f"Terjual tapi qty masih selisih (Track Total: {total_qty_track})"
                    elif not bin_exists and qty_matches:
                        status = "Terjual tapi BIN masih selisih"
                    else:
                        status = "Terjual tapi BIN & QTY tidak sesuai"
                    
                    inv_display = all_inv
                else:
                    inv_display = "-"
                    status = "Tidak ditemukan di Tracking"
                
                resolved_list.append({'INVOICE': inv_display, 'KETERANGAN': status})
            
            res_df = pd.DataFrame(resolved_list)
            discrepancies['INVOICE'] = res_df['INVOICE'].values
            discrepancies['KETERANGAN'] = res_df['KETERANGAN'].values
        
        elif file_tracking is None and not discrepancies.empty:
            discrepancies['INVOICE'] = "-"
            discrepancies['KETERANGAN'] = "File Tracking tidak diupload"

        return comparison, discrepancies

    except Exception as e:
        raise Exception(f"Gagal memproses data: {str(e)}")

import streamlit as st
from supabase import create_client, Client
from datetime import datetime, date, timedelta
import pandas as pd

# --- 1. KONEKSI & CONFIG SUPABASE ---
SUPABASE_URL = "https://ufhjrsxzcffdfswfqlzk.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVmaGpyc3h6Y2ZmZGZzd2ZxbHprIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYxNTI5NjgsImV4cCI6MjA5MTcyODk2OH0.DDlKkXU5-nVvNYK_uLYzXLgaj8oDT4s8vbjAoWMWacI"

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

# --- 2. DEFINISI FUNGSI ---
def fetch_data():
    try:
        # Mengambil data dari tabel shipping_costs di Supabase
        res = supabase.table("shipping_costs").select("*").execute()
        return pd.DataFrame(res.data)
    except Exception:
        return pd.DataFrame()

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

def save_data_ongkir(supplier, ekspedisi, koli, ongkir, tanggal_jam): 
    try:
        data = {
            "supplier": supplier.upper(), 
            "ekspedisi": ekspedisi, 
            "total_koli": koli, 
            "total_ongkir": ongkir,
            "created_at": tanggal_jam 
        }
        supabase.table("shipping_costs").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Gagal simpan: {e}")
        return False

def sync_data():
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        # Pakai upsert biar kalau tanggalnya udah ada dia cuma update
        supabase.table("reset_tracker").upsert({"last_date": today}, on_conflict="last_date").execute()
    except Exception as e:
        print(f"⚠️ {e}")

def show_database_ongkir():
    # --- CSS CUSTOM ---
    st.markdown("""
        <style>
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
        div[data-baseweb="input"], div[data-baseweb="select"] {
            background-color: #0e1117 !important;
            border: 1px solid #3e444d !important;
            border-radius: 5px !important;
        }
        div[data-baseweb="input"]:focus-within {
            border-color: #FFD700 !important;
            box-shadow: 0 0 0 1px #FFD700 !important;
        }
        .solid-header {
            background-color: #FFD700 !important; 
            color: #0e1117 !important; 
            padding: 10px 15px !important;
            border-radius: 5px !important;
            font-weight: 900 !important;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            margin-bottom: 15px !important;
            display: inline-block;
        }
        .stButton button, .stDownloadButton button {
            background-color: #1a1e24 !important; 
            color: #FFD700 !important; 
            border: 3px solid #FFD700 !important; 
            border-radius: 12px !important; 
            padding: 12px 24px !important;
            font-size: 1.1rem !important;
            font-weight: 800 !important;
            text-transform: uppercase !important; 
            letter-spacing: 1.5px; 
            transition: all 0.3s ease-in-out; 
            box-shadow: 0 4px 10px rgba(0,0,0,0.5); 
        }
        .stButton button:hover, .stDownloadButton button:hover {
            background-color: #FFD700 !important; 
            color: #0e1117 !important; 
            transform: translateY(-3px); 
            box-shadow: 0 8px 20px rgba(255, 215, 0, 0.4); 
        }
        .stButton button:focus, .stDownloadButton button:focus {
            box-shadow: 0 0 0 4px rgba(255, 215, 0, 0.5) !important;
            outline: none !important;
        }
        input[type="number"] {
            color: #ffffff !important;
            background-color: #0e1117 !important;
        }
        [data-testid="stExpander"] details summary {
            background-color: #1a1e24 !important; 
            color: #FFFFFF !important; 
            border: 1px solid #3e444d !important;
            border-radius: 8px !important;
            padding: 10px 15px !important;
            transition: 0.3s !important;
        }
        [data-testid="stMetricValue"] {
            color: #FFD700 !important;
            font-size: 28px !important;
            font-weight: 700 !important;
        }
        [data-testid="stMetricLabel"] {
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

    # --- HERO HEADER ---
    st.markdown('<div class="hero-header"><h1>DATABASE ONGKIR IN/OUT</h1></div>', unsafe_allow_html=True)

    # --- DASHBOARD & LOGIKA DATA ---
    df_raw = fetch_data()

    # --- TAMPILAN TABS ---
    tab_input, tab_summary = st.tabs(["📥 INPUT DATA", "📊 SUMMARY & HISTORY"])

    with tab_input:
        with st.expander("🛻 INPUT DATA ONGKIR BARU", expanded=True):
            with st.form("form_ongkir_single", clear_on_submit=True):
                col_a, col_b = st.columns(2)
                with col_a:
                    supplier_input = st.text_input("Nama Supplier", placeholder="Tulis Nama Supplier....")
                    ekspedisi_input = st.text_input("Nama Ekspedisi", placeholder="Tulis Nama Ekspedisi...").upper()
                    input_tgl = st.date_input("Tanggal Transaksi", value=datetime.now())
                with col_b:
                    koli_input = st.number_input("Total Koli", min_value=1, step=1)
                    ongkir_input = st.number_input("Total Ongkir (Rp)", min_value=0, step=5000)
                    input_jam = st.time_input("Jam Transaksi", value=datetime.now().time())
                
                fix_timestamp = f"{input_tgl.strftime('%Y-%m-%d')} {input_jam.strftime('%H:%M:%S')}"
                
                if st.form_submit_button("▶️ UPLOAD HASIL ONGKIR"):
                    if supplier_input:
                        if save_data_ongkir(supplier_input, ekspedisi_input, koli_input, ongkir_input, fix_timestamp):
                            st.success(f"Data {supplier_input.upper()} Berhasil Disimpan!")
                            st.rerun()
                    else:
                        st.error("Nama Supplier wajib diisi!")

        st.markdown("---")

        with st.expander("📁 BATCH OPS: UPLOAD MASSAL", expanded=False):
            c_dl, c_up = st.columns([1, 2])
            with c_dl:
                st.markdown("### 1. Download")
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
                    required = ["SUPPLIER", "EKSPEDISI", "TOTAL KOLI", "ONGKIR", "TANGGAL_JAM"]
                    if all(col in df_mass.columns for col in required):
                        if st.button("▶️ UPLOAD BULK ONGKIR"):
                            with st.spinner('Processing...'):
                                batch_data = []
                                for _, row in df_mass.iterrows():
                                    batch_data.append({
                                        "supplier": str(row["SUPPLIER"]).upper(), 
                                        "ekspedisi": str(row["EKSPEDISI"]).upper(), 
                                        "total_koli": int(row["TOTAL KOLI"]), 
                                        "total_ongkir": clean_currency(row["ONGKIR"]),
                                        "created_at": str(row["TANGGAL_JAM"])
                                    })
                                supabase.table("shipping_costs").insert(batch_data).execute()
                            st.success("Berhasil diinput!")
                            st.rerun()
                    else:
                        st.error(f"Format salah! Harus: {required}")

    with tab_summary:
        if not df_raw.empty:
            df_raw['created_at'] = pd.to_datetime(df_raw['created_at'])
            st.markdown("### 🔍 FILTER DATA")
            
            def update_range_callback():
                pilihan = st.session_state.preset_choice
                hari_ini = date.today()
                if pilihan == "Today":
                    st.session_state.date_val = (hari_ini, hari_ini)
                elif pilihan == "This Month":
                    st.session_state.date_val = (hari_ini.replace(day=1), hari_ini)
                elif pilihan == "All Time":
                    st.session_state.date_val = (df_raw['created_at'].min().date(), df_raw['created_at'].max().date())

            col_f1, col_f2 = st.columns(2)
            with col_f1:
                if 'date_val' not in st.session_state:
                    st.session_state.date_val = (df_raw['created_at'].min().date(), df_raw['created_at'].max().date())

                date_range = st.date_input("Rentang Tanggal", value=st.session_state.date_val, key="date_val")
                st.selectbox("Quick Select Range:", ["Custom Range", "Today", "This Month", "All Time"], key="preset_choice", index=0, on_change=update_range_callback)

            with col_f2:
                list_ekspedisi = ["SEMUA"] + sorted(df_raw['ekspedisi'].unique().tolist())
                pilih_ekspedisi = st.selectbox("Pilih Ekspedisi", list_ekspedisi)

            if isinstance(date_range, tuple) and len(date_range) == 2:
                start_date, end_date = date_range
                mask = (df_raw['created_at'].dt.date >= start_date) & (df_raw['created_at'].dt.date <= end_date)
                df_filtered = df_raw.loc[mask].copy()
            else:
                df_filtered = df_raw.copy()
                
            if pilih_ekspedisi != "SEMUA":
                df_filtered = df_filtered[df_filtered['ekspedisi'] == pilih_ekspedisi]

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

            m1, m2, m3 = st.columns(3)
            m1.metric("TOTAL BIAYA ALL", f"Rp {total_biaya:,.0f}")
            m2.metric("TOTAL KOLI", f"{total_koli} Pcs")
            m3.metric("AVG COST/KOLI", f"Rp {avg:,.0f}")

            m4, m5 = st.columns(2)
            m4.metric("BIAYA RTO", f"Rp {biaya_rto:,.0f}", delta_color="inverse")
            m5.metric("BIAYA BARANG DATANG", f"Rp {biaya_datang:,.0f}")

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
                df_sorted = df_display.sort_values('created_at', ascending=False)
                ids_to_delete = df_sorted.iloc[selected_rows]['id'].tolist()
                st.warning(f"Terpilih {len(ids_to_delete)} data untuk dihapus.")
                if st.button("🗑️ HAPUS DATA TERPILIH", type="primary"):
                    try:
                        # Langsung hapus semua ID yang ada di dalam list
                        supabase.table("shipping_costs").delete().in_("id", ids_to_delete).execute()
                        st.success(f"Berhasil menghapus {len(ids_to_delete)} data!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal hapus: {e}")
            else:
                st.info("💡 Centang baris di tabel untuk menghapus data.")
        else:
            st.info("Data masih kosong.")


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
def change_m4():
    st.session_state.main_menu = st.session_state.m4_key
def change_m5():
    st.session_state.main_menu = st.session_state.m5_key

with st.sidebar:
    # --- KELOMPOK 1: DASHBOARD SUMMARY ---
    st.markdown('<p style="font-weight: bold; color: #808495; margin-top: 10px; margin-bottom: -5px;">MAIN MENU</p>', unsafe_allow_html=True)
    st.markdown('<p style="font-weight: bold; color: #808495; margin-bottom: 5px;">DASHBOARD SUMMARY</p>', unsafe_allow_html=True)
    
    m1_list = ["Dashboard Overview", "Database Master"]
    idx1 = m1_list.index(st.session_state.main_menu) if st.session_state.main_menu in m1_list else 0
    st.radio("M1", m1_list, index=idx1, key="m1_key", on_change=change_m1, label_visibility="collapsed")

    # --- KELOMPOK 2: OPERATIONAL ---
    st.markdown('<p style="font-weight: bold; color: #808495; margin-top: 25px; margin-bottom: 5px;">OPERATIONAL</p>', unsafe_allow_html=True)
    
    m2_list = ["Putaway System", "Scan Out Validation", "Refill & Overstock", "Refill & Withdraw", "Compare RTO", "Compare Penerimaan RTO", "FDR Update"]
    idx2 = m2_list.index(st.session_state.main_menu) if st.session_state.main_menu in m2_list else 0
    st.radio("M2", m2_list, index=idx2, key="m2_key", on_change=change_m2, label_visibility="collapsed")

    # --- KELOMPOK 3: INVENTORY ---
    st.markdown('<p style="font-weight: bold; color: #808495; margin-top: 25px; margin-bottom: 5px;">INVENTORY</p>', unsafe_allow_html=True)
    
    m3_list = ["Stock Opname", "Justification SO", "Stock Minus", "Compare System", "List Retur Out", "Pengajuan Mutasi Karantina", "Picking Audit"]
    idx3 = m3_list.index(st.session_state.main_menu) if st.session_state.main_menu in m3_list else 0
    st.radio("M3", m3_list, index=idx3, key="m3_key", on_change=change_m3, label_visibility="collapsed")

    # --- KELOMPOK 4: REJECT/DEFECT ---
    st.markdown('<p style="font-weight: bold; color: #808495; margin-top: 25px; margin-bottom: 5px;">REJECT & DEFECT</p>', unsafe_allow_html=True)
    
    m4_list = ["Pengajuan Reject/Defect", "Reject/Defect List"]
    idx4 = m4_list.index(st.session_state.main_menu) if st.session_state.main_menu in m4_list else 0
    st.radio("M4", m4_list, index=idx4, key="m4_key", on_change=change_m4, label_visibility="collapsed")

    # --- KELOMPOK 5: EXTRAS ---
    st.markdown('<p style="font-weight: bold; color: #808495; margin-top: 25px; margin-bottom: 5px;">EXTRAS</p>', unsafe_allow_html=True)
    
    m5_list = ["Logistic Schedule", "Balancing Stock", "Reporting & PIC", "Database Ongkir In/Out"]
    idx5 = m5_list.index(st.session_state.main_menu) if st.session_state.main_menu in m5_list else 0
    st.radio("M5", m5_list, index=idx5, key="m5_key", on_change=change_m5, label_visibility="collapsed")

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

import streamlit as st
import pandas as pd
import io

# Inisialisasi Session State di awal agar data tidak hilang
if 'putaway_results' not in st.session_state:
    st.session_state['putaway_results'] = None

# --- UI APP ---
if menu == "Putaway System":
    st.markdown('<div class="hero-header"><h1>PUTAWAY SYSTEM COMPARATION</h1></div>', unsafe_allow_html=True)
    
    # --- CSS ---
    st.markdown("""
        <style>
        .m-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; text-align: center; margin: 5px 0; border: 1px solid #e0e0e0; }
        .m-lbl { display: block; font-size: 14px; color: #555; font-weight: bold; }
        .m-val { display: block; font-size: 24px; color: #ff4b4b; font-weight: bold; }
        </style>
    """, unsafe_allow_html=True)

    with st.expander("📋 Informasi Format File"):
        st.info("""
        **Format yang diharapkan:**
        - **DATA SCAN PUTAWAY**: Kolom A = **BIN**, Kolom B = **SKU**, Kolom C = **QTY SCAN**
        - **DATA PUTAWAY**: Sesuai yang ada pada template Jezpro.
        """)
    with st.expander("💡 Logic Thinking"):
        st.info("""
        **Alur Compare Putaway:**
        - SKU di file data scan akan dicompare dengan SKU yang ada di FIle data BIN Putaway
        - Tiap unique SKU teratas di File data scan akan mendapatkan alokasi penuh
        - Untuk SKU yang tidak mendapatkan alokasi maka akan ditulis dengan note **PERLU CEK MANUAL** untuk mengetahui apakah ada double data scan atau item belum terset up di BIN PUTAWAY
        - List Set up akan dibuatkan otomatis oleh system dengan BIN awal diambil dari BIN di file Putaway dan BIN tujuan disesuaikan dengan BIN yang ada di data scan
        """)
    
    c1, c2 = st.columns(2)
    with c1: up_ds = st.file_uploader("📥Upload DS PUTAWAY", type=['xlsx', 'csv'], key="ds_up")
    with c2: up_asal = st.file_uploader("📥Upload ASAL BIN PUTAWAY", type=['xlsx', 'csv'], key="asal_up")

    # BARU MASUK KE BLOK YANG LU TULIS TADI
    if up_ds and up_asal:
        if st.button("▶️ COMPARE PUTAWAY"):
            # ... kode yang lu kirim tadi ...
            try:
                # 1. LOAD DATA
                df_ds_p = pd.read_csv(up_ds) if up_ds.name.endswith('.csv') else pd.read_excel(up_ds)
                df_asal_p = pd.read_csv(up_asal) if up_asal.name.endswith('.csv') else pd.read_excel(up_asal)
                
                # 2. DEFINISIKAN TOTAL AWAL (Ambil Kolom J / Index 9)
                # Taruh baris ini sebelum masuk ke 'res' atau 'session_state'
                total_awal = int(pd.to_numeric(df_asal_p.iloc[:, 9], errors='coerce').sum())
                
                # 3. PROSES FUNGSI
                res = putaway_system(df_ds_p, df_asal_p)
                
                # 4. SIMPAN KE SESSION STATE
                st.session_state['putaway_results'] = {
                    'df_comp': res[0],
                    'df_plist': res[1],  # Ini List Setup yang kolomnya sudah bersih
                    'df_kurang': res[2],
                    'df_sum': res[3],
                    'df_lt3': res[4],
                    'df_updated_bin': res[5],
                    'total_awal': total_awal  # Sekarang variabel ini sudah dikenal
                }
                st.success("✅ Proses Putaway Selesai!")
                
            except Exception as e:
                st.error(f"Gagal saat memproses: {e}")

    # --- TAMPILKAN HASIL (Jika sudah diproses) ---
    if st.session_state['putaway_results'] is not None:
        r = st.session_state['putaway_results']
        
        st.divider()
        st.markdown('<h3 style="color: #010B13;">📋 RINGKASAN HASIL</h3>', unsafe_allow_html=True)
        
        # --- HITUNG METRICS ---
        
        # 1. Gunakan 'total_awal' yang sudah disimpan di session state (Angka 278)
        total_compare_qty = r.get('total_awal', 0)
        
        # 2. Total yang berhasil tersetup
        total_list_qty = int(r['df_plist']['QUANTITY'].sum()) if not r['df_plist'].empty else 0
        
        # 3. Total yang gagal/kurang setup
        total_kurang_qty = int(r['df_kurang']['DIFF'].sum()) if not r['df_kurang'].empty else 0
        
        # 4. Outstanding (Sisa di Staging/Putaway System)
        lt3_total_qty = 0
        if not r['df_lt3'].empty:
            qty_col = [c for c in r['df_lt3'].columns if 'qty' in str(c).lower()]
            if qty_col:
                lt3_total_qty = int(r['df_lt3'][qty_col[0]].sum())

        # --- TAMPILKAN METRICS BOX ---
        m1, m2, m3, m4 = st.columns(4)
        m1.markdown(f'<div class="m-box"><span class="m-lbl">Qty Sytem Putaway</span><span class="m-val">{total_compare_qty}</span></div>', unsafe_allow_html=True)
        m2.markdown(f'<div class="m-box"><span class="m-lbl">Total Tersetup</span><span class="m-val">{total_list_qty}</span></div>', unsafe_allow_html=True)
        m3.markdown(f'<div class="m-box"><span class="m-lbl">Kurang Setup</span><span class="m-val">{total_kurang_qty}</span></div>', unsafe_allow_html=True)
        m4.markdown(f'<div class="m-box"><span class="m-lbl">Sisa Stok Putaway</span><span class="m-val">{lt3_total_qty}</span></div>', unsafe_allow_html=True)

    # ... (Sisa kode Tabs dan Download tetap sama)        # --- TABS HASIL ---
        t1, t2, t3, t4 = st.tabs(["📋 Hasil Compare", "📝 List Setup", "⚠️ Kurang Setup", "📦 Outstanding"])
        
        with t1: st.dataframe(r['df_comp'], use_container_width=True)
        with t2: st.dataframe(r['df_plist'], use_container_width=True)
        with t3: 
            if not r['df_kurang'].empty: st.dataframe(r['df_kurang'], use_container_width=True)
            else: st.success("✅ Semua Tercover!")
        with t4: 
            if not r['df_lt3'].empty: st.dataframe(r['df_lt3'], use_container_width=True)
            else: st.success("✅ Tidak ada Outstanding!")

        # --- TOMBOL DOWNLOAD (Excel) ---
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            r['df_comp'].to_excel(writer, sheet_name='COMPARE', index=False)
            r['df_plist'].to_excel(writer, sheet_name='PUTAWAY_LIST', index=False)
            r['df_kurang'].to_excel(writer, sheet_name='KURANG_SETUP', index=False)
            r['df_lt3'].to_excel(writer, sheet_name='OUTSTANDING', index=False)
            r['df_updated_bin'].to_excel(writer, sheet_name='SISA_STOK_SYSTEM', index=False)
        
        st.download_button(
            label="📥 DOWNLOAD REPORT",
            data=output.getvalue(),
            file_name="REPORT_PUTAWAY_SYSTEM.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

elif menu == "Scan Out Validation":
    st.markdown('<div class="hero-header"><h1> COMPARE AND ANALYZE ITEM SCAN OUT</h1></div>', unsafe_allow_html=True)
    
    with st.expander("📋 Informasi Format File"):
        st.info("""
        **Format yang diharapkan :**
        - **DATA SCAN**: Kolom A = **BIN**, Kolom B = **SKU** (QTY akan dihitung otomatis)
        - **HISTORY SET UP**: Sesuai yang ada pada template Mutasi Set Up Jezpro
        - **STOCK TRACKING**: Sesuai yang ada pada template Stock Tracking Jezpro
        """)
        
    with st.expander("💡Logic Thinking"):
        st.info("""
        **Alur Compare Scan Out :**
        - System akan melakukan compare antara BIN dan SKU yang ada di file data scan dengan file History Set Up dan Stock Tracking
        - Jika BIN dan SKU akan langsung melakukan double cek di kedua file mana yang cocok dan sesuai dengan BIN dan SKU yang ada di data scan
        - Jika ditemukan di File Mutasi dan tidak ditemukan di file Stock Tracking maka akan diberikan note **DONE AND MATCH SET UP**
        - Jika ditemukan di File Mutasi dan tidak ditemukan di file Stock Tracking namun BIN tidak sesuai hanya SKUnya saja yang cocok maka akan diberikan note **DONE SETUP (BIN MISSMATCH)**
        - Jika ditemukan di File Mutasi dan tidak ditemukan di file Stock Tracking namun QTY tidak sesuai hanya SKU dan BIN saja yang cocok maka akan diberikan note **DONE SET UP (QTY MISSMATCH)**
        - Jika ditemukan di File Stock Tracking dan tidak ditemukan di file Mutasi maka akan diberikan note **ITEM TELAH TERJUAL**
        - Jika ditemukan di File Stock Tracking dan tidak ditemukan di file Mutasi namun BIN tidak sesuai hanya SKUnya saja yang cocok maka akan diberikan note **ITEM TELAH TERJUAL (BIN MISSMATCH)**
        - Jika ditemukan di File Stock Tracking dan tidak ditemukan di file Mutasi namun QTY tidak sesuai hanya SKU dan BIN saja yang cocok maka akan diberikan note **ITEM TELAH TERJUAL (QTY MISSMATCH)**
        - Jika permintaan item ada > 1 item dan yang terjual hanya 1 maka akan dilakukan split row dimana akan dilakukan pengecekan di kedua file dan akan split note juga menyesuaikan kondisi hasil compare 
        """)
    
    col1, col2, col3 = st.columns(3)
    with col1: 
        up_scan = st.file_uploader("📥Upload DATA SCAN", type=['xlsx', 'csv'], help="File dengan Kolom A=BIN, B=SKU")
    with col2: 
        up_hist = st.file_uploader("📥Upload HISTORY SET UP", type=['xlsx'], help="File dengan Kolom D=SKU")
    with col3: 
        up_stock = st.file_uploader("📥Upload STOCK TRACKING", type=['xlsx'], help="File dengan Kolom B=SKU, A=Invoice")
    
    if up_scan and up_hist and up_stock:
        # 1. Inisialisasi Session State (Tempat penitipan data)
        if "df_res" not in st.session_state:
            st.session_state.df_res = None
        if "df_draft" not in st.session_state:
            st.session_state.df_draft = None

        if st.button("▶️ COMPARE DATA SCAN OUT"):
            try:
                if up_scan.name.endswith('.csv'):
                    df_s = pd.read_csv(up_scan)
                else:
                    df_s = pd.read_excel(up_scan, engine='openpyxl')
                
                df_h = pd.read_excel(up_hist, engine='openpyxl')
                df_st = pd.read_excel(up_stock, engine='openpyxl')
                
                # Standarisasi kolom
                df_s.columns = [str(col).strip().upper() for col in df_s.columns]
                df_h.columns = [str(col).strip().upper() for col in df_h.columns]
                df_st.columns = [str(col).strip().upper() for col in df_st.columns]
                
                if len(df_s.columns) < 2:
                    st.error("❌ DATA SCAN harus memiliki minimal 2 kolom (BIN, SKU)")
                    st.stop()
                
                with st.spinner('🔄 Sedang memproses data...'):
                    # Masukkan hasil ke session state
                    res, draft = process_scan_out(df_s, df_h, df_st)
                    st.session_state.df_res = res
                    st.session_state.df_draft = draft
                
                st.success("✅ Validasi Selesai!")
                
            except Exception as e:
                st.error(f"❌ Error saat proses: {str(e)}")

        # 2. Tampilkan Hasil jika data sudah ada di Session State
        if st.session_state.df_res is not None:
            df_res = st.session_state.df_res
            df_draft = st.session_state.df_draft

            # ========== STATISTIK (SAFE VERSION) ==========
            st.divider()
            st.markdown('<div style="background-color: #f0f2f6; padding: 10px; border-left: 5px solid #007BFF; border-radius: 5px; margin-bottom: 20px;"><h3 style="color: #010B13; margin: 0; font-size: 30px;">📋RINGKASAN HASIL</h3></div>', unsafe_allow_html=True)
            
            # Hitung statistik dengan proteksi tipe data
            kets = df_res['Keterangan'].astype(str)
            terjual_count = kets.apply(lambda x: 'TERJUAL' in x.upper()).sum()
            mismatch_count = kets.apply(lambda x: 'MISSMATCH' in x.upper()).sum()
            belum_count = kets.apply(lambda x: 'BELUM' in x.upper()).sum()
            done_count = kets.apply(lambda x: 'DONE' in x.upper()).sum()
            total_items = len(df_res)

            sc1, sc2, sc3, sc4, sc5 = st.columns(5)
            with sc1: st.markdown(f'''<div class="m-box"><span class="m-lbl">📦 Total Items</span><span class="m-val">{total_items}</span></div>''', unsafe_allow_html=True)
            with sc2: st.markdown(f'''<div class="m-box"><span class="m-lbl">✅ DONE SETUP</span><span class="m-val">{done_count}</span></div>''', unsafe_allow_html=True)
            with sc3: st.markdown(f'''<div class="m-box"><span class="m-lbl">📤 TERJUAL</span><span class="m-val">{terjual_count}</span></div>''', unsafe_allow_html=True)
            with sc4: st.markdown(f'''<div class="m-box"><span class="m-lbl">⚠️ MISSMATCH</span><span class="m-val">{mismatch_count}</span></div>''', unsafe_allow_html=True)
            with sc5: st.markdown(f'''<div class="m-box"><span class="m-lbl">❌ BELUM SETUP</span><span class="m-val">{belum_count}</span></div>''', unsafe_allow_html=True)
            
            st.divider()

            # ========== TAMPILKAN DATAFRAME ==========
            st.subheader("📋 DATA SCAN (COMPARED)")
            def highlight_vba(val):
                v = str(val).upper()
                if 'MISSMATCH' in v or 'BELUM' in v: return 'color: red; font-weight: bold'
                if 'DONE AND MATCH' in v: return 'color: green; font-weight: bold'
                if 'TERJUAL' in v: return 'color: blue; font-weight: bold'
                return ''

            st.dataframe(df_res.style.map(highlight_vba, subset=['Keterangan']), use_container_width=True, height=400)
            
            if len(df_draft) > 0:
                st.subheader("📝 DRAFT SET UP")
                st.dataframe(df_draft, use_container_width=True, height=300)

            # ========== DOWNLOAD SECTION ==========
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_res.to_excel(writer, sheet_name='DATA SCAN', index=False)
                if len(df_draft) > 0:
                    df_draft.to_excel(writer, sheet_name='DRAFT SET UP', index=False)
                
                # (Optional) Tambahkan formatting writer.book di sini jika perlu
            
            st.download_button(
                label="📥 DOWNLOAD HASIL (DATA SCAN + DRAFT)",
                data=output.getvalue(),
                file_name="SCAN_OUT_RESULT.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
                
elif menu == "Refill & Overstock":
    st.markdown('<div class="hero-header"><h1>REFILL & OVERSTOCK SYSTEM</h1></div>', unsafe_allow_html=True)
    
    st.markdown("""
    <style>
    .m-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; text-align: center; margin: 5px 0; }
    .m-lbl { display: block; font-size: 14px; color: #555; font-weight: bold; }
    .m-val { display: block; font-size: 24px; color: #ff4b4b; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

    with st.expander("📋 Informasi Format File"):
        st.info("""
        **Format yang diharapkan:**
        - **ALL DATA STOCK**: Pilih **HANYA ADA DI STOCK**
        - **STOCK TRACKING (Opsional)**: Pilih **JEZ SURABAYA**, rentang 7 hari. 
        """)
    with st.expander("💡Logic Thinking"):
        st.info("""
        **Alur Process Refill & Overstock (With Stock Tracking):**
        - Melakukan Compare antara SKU yang ada di Gudang Lt.4 dengan SKU di Gudang Lt.3 dan sebaliknya
        - List akan dikumpulkan terlebih dahulu dan akan mengambil SKU dengan Qty di Gudang Lt.3 yang < 3 Pcs untuk Refill dan > 12 Pcs untuk overstock
        - Jika data sudah didapatkan maka selanjutnya adalah compare dengan Stock Tracking
        - Compare akan dilakukan dengan mempertimbangkan penjualan Online untuk SKU tersebut
        - Jika penjualan online < 7 pcs maka refill hanya akan mengambil 1/3 dari total stock di GL4 dan akan mengambil 1/3 dari total Diff total stock - 12 Pcs untuk Overstock
        - Jika penjualan online > 7 pcs maka refill akan mengambil 1/2 dari total stock di GL4 dan akan mengambil 1/2 dari total Diff total stock - 12 Pcs untuk Overstock
        - Maksimal kapasitas untuk tiap SKU di GL3 adalah 12 Pcs jadi tidak akan lebih dari 12 tiap SKU di Gl3

        **Alur Process Refill & Overstock (Without Stock Tracking):**
        - Melakukan Compare antara SKU yang ada di Gudang Lt.4 dengan SKU di Gudang Lt.3
        - List akan dikumpulkan terlebih dahulu dan akan mengambil SKU dengan Qty di Gudang Lt.3 yang < 3 Pcs dan > 12 Pcs untuk Overstock
        - Sistem akan memksimalkan tiap SKU untuk mendapatkan total 12 Pcs di Gudang lt.3 
        - Maksimal kapasitas untuk tiap SKU di GL3 adalah 12 Pcs jadi tidak akan lebih dari 12 tiap SKU di Gl3
        """)

    c1, c2 = st.columns(2)
    with c1: up_all = st.file_uploader("📥 Upload ALL DATA STOCK", type=['xlsx'])
    with c2: up_track = st.file_uploader("📥 Upload STOCK TRACKING (Opsional)", type=['xlsx'])
    
    # PERBAIKAN: Hanya ALL DATA yang wajib untuk memunculkan tombol
    if up_all:
        if st.button("▶️ PROSES REFILL & OVERSTOCK"):
            try:
                with st.spinner("Processing..."):
                    # Load file wajib
                    df_all = pd.read_excel(up_all, engine='openpyxl')
                    
                    # PERBAIKAN: Load file opsional (jika ada)
                    df_track = None
                    if up_track:
                        df_track = pd.read_excel(up_track, engine='openpyxl')
                    else:
                        st.warning("⚠️ Berjalan tanpa Stock Tracking. Kalkulasi Overstock mungkin tidak maksimal.")
                    
                    # Panggil fungsi yang sudah kita perbaiki tadi
                    res_gl3, res_gl4, res_refill, res_over = process_refill_overstock(df_all, df_track)
                    
                    st.success("Data Berhasil di Filter!")
                    
                    # Tampilan Metrics
                    m1, m2, m3 = st.columns(3)
                    # Gunakan len() dengan proteksi jika dataframe kosong
                    count_refill = len(res_refill) if not res_refill.empty else 0
                    count_over = len(res_over) if not res_over.empty else 0
                    count_total = (len(res_gl3) if not res_gl3.empty else 0) + (len(res_gl4) if not res_gl4.empty else 0)

                    m1.markdown(f'<div class="m-box"><span class="m-lbl">REFILL ITEMS</span><span class="m-val">{count_refill}</span></div>', unsafe_allow_html=True)
                    m2.markdown(f'<div class="m-box"><span class="m-lbl">OVERSTOCK ITEMS</span><span class="m-val">{count_over}</span></div>', unsafe_allow_html=True)
                    m3.markdown(f'<div class="m-box"><span class="m-lbl">TOTAL GL3/GL4</span><span class="m-val">{count_total}</span></div>', unsafe_allow_html=True)
                    
                    # Tabs
                    t1, t2, t3, t4 = st.tabs(["📦 REFILL", "⚠️ OVERSTOCK", "📑 GL3 DATA", "📑 GL4 DATA"])
                    with t1: st.dataframe(res_refill, use_container_width=True)
                    with t2: st.dataframe(res_over, use_container_width=True)
                    with t3: st.dataframe(res_gl3, use_container_width=True)
                    with t4: st.dataframe(res_gl4, use_container_width=True)
                    
                    # Download Report
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        res_refill.to_excel(writer, sheet_name='REFILL', index=False)
                        res_over.to_excel(writer, sheet_name='OVERSTOCK', index=False)
                        res_gl3.to_excel(writer, sheet_name='GL3', index=False)
                        res_gl4.to_excel(writer, sheet_name='GL4', index=False)
                    
                    st.download_button(
                        label="📥 DOWNLOAD REPORT",
                        data=output.getvalue(),
                        file_name=f"REFILL_REPORT_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    
            except Exception as e: 
                st.error(f"Terjadi kesalahan saat memproses data: {e}")
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

    with st.expander("📋 Informasi Format File"):
        st.info("""
        **Format yang diharapkan:**
        - **All Data Stock**: Download Multiple Adjusmet dari Jezpro dan pilih **Termasuk yang sudah habis**
        """)
    with st.expander("💡Logic Thinking"):
        st.info("""
        **Alur Process Compare Stock Minus:**
        - Mengambil SKU yang memiliki Qty System minus (-)
        - Lalu SKU yang memiliki QTY Minus (-) tersebut akan di lakukan shuffle covering Stock
        - Dimana terdapat Bin prioritas untuk shuffle Covering Stock (All Stagging, Karantina)
        - Dan jika minus terjadi di Gudang lt.2 maka akan prioritas mengambil BIN Toko begitupun sebaliknya
        - Lalu jika tidak ditemukan di BIN Prioritas maka akan mengambil random BIN kecuali LIVE, Offline dan Online
        - Jika sudah ditemukan SKU dan Qty yang bisa covering maka akan dibuatkan list Set up
        - Dan jika tidak bisa diselesaikan lewat set up maka sistem akan memasukkan kedalam item need justifikasi dan perlu analisa lebih lanjut
        """)

    uploaded_file = st.file_uploader("Upload File ALL DATA STOCK", type=["xlsx", "xlsm"])
    
    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file, engine="openpyxl")
            df.columns = [str(c).strip().upper() for c in df.columns]
            
            col_sku = 'SKU'
            col_bin = 'BIN'
            col_qty = next((c for c in df.columns if 'QTY SYSTEM' in c or 'QTY SYS' in c), None)
            
            if col_qty is None:
                st.error("❌ Kolom 'QTY SYSTEM' tidak ditemukan!")
            else:
                # TOMBOL PROSES
                if st.button("🔃 PROSES DATA"):
                    with st.spinner('Memproses...'):
                        # 1. Persiapan Data
                        df[col_qty] = pd.to_numeric(df[col_qty], errors='coerce').fillna(0)
                        df[col_sku] = df[col_sku].astype(str).str.strip().str.upper()
                        df[col_bin] = df[col_bin].astype(str).str.strip().str.upper()

                        df_minus_awal = df[df[col_qty] < 0].copy()
                        df_positif = df[df[col_qty] > 0]
                        
                        inventory = {}
                        for _, row in df_positif.iterrows():
                            sku, bn, qt = row[col_sku], row[col_bin], row[col_qty]
                            if sku not in inventory: inventory[sku] = {}
                            inventory[sku][bn] = inventory[sku].get(bn, 0) + qt

                        prior_bins = ["RAK ACC LT.1", "STAGGING INBOUND", "STAGGING OUTBOUND", "KARANTINA DC",
                                      "KARANTINA STORE 02", "STAGGING REFUND", "STAGING GAGAL QC", "STAGGING LT.3",
                                      "STAGGING OUTBOUND SEMARANG", "STAGGING OUTBOUND SIDOARJO", "STAGGING LT.2", "LT.4"]

                        set_up_results = []
                        df_need_adj_list = []

                        # 2. Proses Alokasi & Sisa
                        for _, row in df_minus_awal.iterrows():
                            sku = row[col_sku]
                            bin_asal = row[col_bin]
                            sisa_minus = abs(row[col_qty])
                            
                            if sku in inventory and any(v > 0 for v in inventory[sku].values()):
                                sku_stock = inventory[sku]
                                while sisa_minus > 0:
                                    bin_solusi = ""
                                    if bin_asal == "TOKO":
                                        if sku_stock.get("STAGGING LT.2", 0) > 0: bin_solusi = "STAGGING LT.2"
                                        elif sku_stock.get("LT.2", 0) > 0: bin_solusi = "LT.2"
                                    elif bin_asal in ["STAGGING LT.2", "LT.2"] and sku_stock.get("TOKO", 0) > 0:
                                        bin_solusi = "TOKO"

                                    if not bin_solusi:
                                        for b in prior_bins:
                                            if sku_stock.get(b, 0) > 0: bin_solusi = b; break
                                    
                                    if not bin_solusi:
                                        for b, q in sku_stock.items():
                                            if b != "REJECT DEFECT" and q > 0: bin_solusi = b; break

                                    if not bin_solusi: break
                                    else:
                                        qty_tersedia = sku_stock[bin_solusi]
                                        ambil = min(sisa_minus, qty_tersedia)
                                        set_up_results.append({
                                            "BIN AWAL": bin_solusi, "BIN TUJUAN": bin_asal,
                                            "SKU": sku, "QUANTITY": ambil, "NOTES": "STOCK MINUS"
                                        })
                                        sku_stock[bin_solusi] -= ambil
                                        sisa_minus -= ambil

                            if sisa_minus > 0:
                                row_adj = row.to_dict()
                                row_adj[col_qty] = -sisa_minus 
                                df_need_adj_list.append(row_adj)

                        # --- SIMPAN KE SESSION STATE AGAR TIDAK HILANG ---
                        st.session_state['df_minus_awal'] = df_minus_awal
                        st.session_state['df_set_up'] = pd.DataFrame(set_up_results)
                        st.session_state['df_need_adj'] = pd.DataFrame(df_need_adj_list)
                        st.session_state['proses_selesai'] = True

                # Tampilkan hasil JIKA sudah pernah diproses
                if st.session_state.get('proses_selesai'):
                    df_m = st.session_state['df_minus_awal']
                    df_s = st.session_state['df_set_up']
                    df_n = st.session_state['df_need_adj']

                    if not df_m.empty:
                        # Kita paksa konversi ke float dulu, baru di-sum, baru di-abs
                        nilai_total = pd.to_numeric(df_m[col_qty], errors='coerce').sum()
                        total_qty = abs(nilai_total)
                    else:
                        total_qty = 0
                    # Dashboard Metrics
                    c1, c2, c3 = st.columns(3)
                    c1.markdown(f'<div class="m-box"><span class="m-lbl">Total Qty Minus</span><span class="m-val">{int(total_qty)}</span></div>', unsafe_allow_html=True)
                    c2.markdown(f'<div class="m-box"><span class="m-lbl">Tercover</span><span class="m-val">{int(df_s["QUANTITY"].sum()) if not df_s.empty else 0}</span></div>', unsafe_allow_html=True)
                    # Hitung total qty dari df_need_adj (df_n)
                    total_sisa_qty = abs(df_n[col_qty].sum()) if not df_n.empty else 0

                    c3.markdown(f'<div class="m-box"><span class="m-lbl">Sisa Adj</span><span class="m-val">{int(total_sisa_qty)}</span></div>', unsafe_allow_html=True)

                    t1, t2, t3 = st.tabs(["📄 MINUS AWAL", "🔄 TEMPLATE SET UP", "⚠️ JUSTIFIKASI"])
                    with t1: st.dataframe(df_m, use_container_width=True)
                    with t2: st.dataframe(df_s, use_container_width=True)
                    with t3: st.dataframe(df_n, use_container_width=True)

                    # Persiapan File Download
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df_m.to_excel(writer, sheet_name='MINUS_AWAL', index=False)
                        df_s.to_excel(writer, sheet_name='SET_UP', index=False)
                        if not df_n.empty: df_n.to_excel(writer, sheet_name='JUSTIFIKASI', index=False)
                    
                    st.download_button("📥 DOWNLOAD HASIL", output.getvalue(), "HASIL_STOCK_MINUS.xlsx")

        except Exception as e:
            st.error(f"Gagal: {e}")

if menu == "Compare RTO":
    st.markdown('<div class="hero-header"><h1>RTO GATEWAY SYSTEM</h1></div>', unsafe_allow_html=True)
    st.markdown("""<style>.m-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; text-align: center; margin: 5px 0; }.m-lbl { display: block; font-size: 14px; color: #555; font-weight: bold; }.m-val { display: block; font-size: 24px; color: #ff4b4b; font-weight: bold; }</style>""", unsafe_allow_html=True)
    with st.expander("📋 Informasi Format File"):
        st.info("""
        **Format yang diharapkan:**
        - **DS RTO**: Diisi dengan Kolom A = **SKU** , Kolom B = **QTY SCAN**
        - **APPSHEET RTO**: Download Spreadsheets Rekap Appsheet sesuai dengan sheet dari RTO yang akan dituju
        - **UPLOAD HASIL CEK REAL**: Upload hasil rekonsiliasi RTO yang sudah di download dan diisi sesuai real yang ditemukan
        - **DRAFT RTO**: Download Draft RTO yang sudah di buatkan purchasing di awal
        """)
    with st.expander("💡Logic Thinking"):
        st.info("""
        **Alur Process Compare RTO (DS Vs Appsheet):**
        - Melakukan Compare antara SKU yang ada di DS dan di Appsheet apakah ada SKU yang berbeda dan Qty yang berbeda
        - Jika ada SKU yang berbeda dan Qty yang berbeda maka akan masuk di process Rekonsiliasi
        - Note Kelebihan ambil adalah ketika **QTY DI DS > APPSHEET**, dan Note Kurang Ambil adalah ketika **QTY DI DS < APPSHEET**
        - Hasil rekonsiliasi dimasukkan kedalam kolom tersedia untuk dilakukan running ulang
        - Lalu selanjutnya adalah compare antara hasil Appsheet dengan Draft RTO
        - Pengecekan akan dilakukan antara SKU dan BIN yang ada di Appsheet dengan Draft RTO
        - Jika BIN berbeda namun SKU sama maka akan muncul note **Perlu Edit Draft**
        - Jika Qty berbeda namun SKU sama maka akan muncul note **Perlu Edit QTY Draft**
        - Jika ada SKU tambahan yang tidak ada di draft namun di appsheet ada akan ada note **Tambah item Draft**
        """)
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
        st.markdown("""
                <div style="background-color: #f0f2f6; padding: 10px; border-left: 5px solid #007BFF; border-radius: 5px; margin-bottom: 20px;">
                <h3 style="color: #010B13; margin: 0; font-size: 30px;">📋RINGKASAN HASIL DATA SCAN VS APPSHEET</h3>
                </div>
                """, unsafe_allow_html=True)
        
        # Ambil data lengkap
        df_full = st.session_state.rto_df_ds
        scan_col = df_full.columns[1]
        
# --- PERHITUNGAN METRIK (WAJIB PAKAI DATA DETAIL BIN AGAR KUMULATIF) ---
        
        # 1. Gunakan data selisih yang sudah dipecah per BIN oleh engine
        df_detail = st.session_state.rto_df_selisih 
        
        # 2. Pastikan numerik agar bisa dijumlahkan
        v_scan = pd.to_numeric(df_detail['QTY SCAN'], errors='coerce').fillna(0)
        v_ambil = pd.to_numeric(df_detail['QTY AMBIL BIN'], errors='coerce').fillna(0) # Pakai QTY AMBIL BIN
        v_notes = df_detail['NOTE'].astype(str).str.strip().str.upper()

        # 3. Metrik Utama (Tetap pakai df_full untuk total scan gudang)
        q_total = int(pd.to_numeric(df_full[scan_col], errors='coerce').sum())
        q_sesuai = int(pd.to_numeric(df_full[df_full['NOTE'] == 'SESUAI'][scan_col], errors='coerce').sum())
        
        # 4. QTY KELEBIHAN (Hajar semua baris yang muncul di Tabel Selisih)
        # Jika satu SKU pecah jadi 3 BIN dan masing-masing selisih, bakal dijumlah semua di sini
        mask_l = v_notes == 'KELEBIHAN AMBIL'
        # Logika: Di baris detail, kita hitung selisih per barisnya
        # Jika QTY SCAN (Total) vs QTY AMBIL BIN (Eceran), 
        # kita hitung akumulasi selisih yang muncul di tampilan
        q_lebih = int((v_scan[mask_l] - df_detail.loc[mask_l, 'QTY AMBIL']).sum()) 
        
        # 5. QTY KURANG (Kumulatif semua baris selisih di tabel)
        mask_k = v_notes == 'KURANG AMBIL'
        mask_m = v_notes == 'DI APPSHEET DIAMBIL DI DS TIDAK ADA'
        
        # Hitung selisih dari semua baris yang muncul di tab 2
        selisih_k = (df_detail.loc[mask_k, 'QTY AMBIL'] - v_scan[mask_k]).sum()
        total_m = v_ambil[mask_m].sum()
        
        q_kurang = int(selisih_k + total_m)

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
            
            # --- PERBAIKAN DI SINI ---
            # Kita gunakan rto_df_selisih karena variabel ini yang menyimpan detail BIN
            df_selisih_detail = st.session_state.rto_df_selisih
            
            if not df_selisih_detail.empty:
                # Menampilkan dataframe dengan kolom detail BIN sesuai request
                st.dataframe(df_selisih_detail, use_container_width=True, hide_index=True)
                
                # Tombol download juga menggunakan data detail
                st.download_button(
                    "📥 Download Item Selisih (Detail BIN)", 
                    df_selisih_detail.to_csv(index=False).encode('utf-8'), 
                    "DETAIL_SELISIH_RTO.csv", 
                    "text/csv", 
                    key="dl_selisih_detail", 
                    use_container_width=True
                )
            else:
                st.success("✨ Aman! Tidak ada item yang selisih.")
    st.subheader("🔄 REFRESH DATA (SETELAH CEK REAL)")
    f_cek = st.file_uploader("Upload Hasil Cek Real", type=['xlsx','csv'], key="rto_cek")
    if f_cek and st.session_state.rto_df_app is not None:
        if st.button("🔄 REFRESH DATA", use_container_width=True):
            df_cek = pd.read_excel(f_cek) if f_cek.name.endswith('xlsx') else pd.read_csv(f_cek)
            ds_ref, app_ref = engine_refresh_rto(st.session_state.rto_df_ds, st.session_state.rto_df_app, df_cek)
            st.session_state.rto_df_ds, st.session_state.rto_df_app = ds_ref, app_ref
            st.success("✅ Refreshed!")

    st.divider()
    st.markdown("""
                <div style="background-color: #f0f2f6; padding: 10px; border-left: 5px solid #007BFF; border-radius: 5px; margin-bottom: 20px;">
                <h3 style="color: #010B13; margin: 0; font-size: 30px;">📋RINGKASAN HASIL APPSHEET VS DRAFT</h3>
                </div>
                """, unsafe_allow_html=True)
    
    f_draft = st.file_uploader("Upload Draft Jezpro", type=['xlsx','csv'], key="rto_draft_jezpro")
    if f_draft and st.session_state.rto_df_app is not None:
        if st.button("🔍 COMPARE DRAFT JEZPRO", use_container_width=True):
            df_draft = pd.read_excel(f_draft) if f_draft.name.endswith('xlsx') else pd.read_csv(f_draft)
            st.session_state.rto_draft_compared = engine_compare_draft_jezpro(st.session_state.rto_df_app, df_draft)
            st.success("✅ Compare Selesai!")

    if st.session_state.rto_draft_compared is not None:
        st.divider()
        st.markdown("""
                <div style="background-color: #f0f2f6; padding: 10px; border-left: 5px solid #007BFF; border-radius: 5px; margin-bottom: 20px;">
                <h3 style="color: #010B13; margin: 0; font-size: 30px;">📋FINAL RESULT</h3>
                </div>
                """, unsafe_allow_html=True)
        df_comp = st.session_state.rto_draft_compared
        # Pastikan kolom sudah numerik dulu biar gak error saat dijumlah
        qty_ambil = pd.to_numeric(df_comp['QTY AMBIL'], errors='coerce').fillna(0)
        qty_lain = pd.to_numeric(df_comp['QTY BIN LAIN'], errors='coerce').fillna(0)

        # 1. QTY DRAFT TOTAL (Menjumlahkan semua qty ambil dan qty bin lain)
        q_draft_total = int((qty_ambil + qty_lain).sum())

        # 2. QTY OK (Hanya yang statusnya 'OK', menjumlahkan qty ambil + qty bin lain)
        mask_ok = (df_comp['STATUS'] == 'OK')
        q_ok = int((qty_ambil[mask_ok] + qty_lain[mask_ok]).sum())

        # 3. QTY PERLU EDIT (Yang statusnya mengandung kata 'EDIT', menjumlahkan qty ambil + qty bin lain)
        mask_edit = df_comp['STATUS'].str.contains('EDIT', na=False)
        q_edit = int((qty_ambil[mask_edit] + qty_lain[mask_edit]).sum())
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
    st.markdown('<div class="hero-header"><h1>FDR UPDATE - MANIFEST CHECKER</h1></div>', unsafe_allow_html=True)
    
    st.markdown("""
        <style>
        .m-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; text-align: center; margin: 5px 0; }
        .m-lbl { display: block; font-size: 14px; color: #555; font-weight: bold; }
        .m-val { display: block; font-size: 24px; color: #ff4b4b; font-weight: bold; }
        </style>
    """, unsafe_allow_html=True)
    with st.expander("📋 Informasi Format File"):
        st.info("""
        **Format yang diharapkan:**
        - **FILE MANIFEST**: Download Manifest dari jezpro pada menu **TRANSAKSI ONLINE V2**, pilih Cabang **ONLINE SURABAYA**, pilih Status Jezpro **DONE ONLINE**, dan rentang waktunya pilih **30 HARI TERAKHIR**
        """)
    with st.expander("💡Logic Thinking"):
        st.info("""
        **Alur Compare :**
        - File yang telah diupload hanya akan di split berdasarkan 2 Kategori yaitu **NEED FU IT** dan **BRANCH**
        - Untuk Need FU IT adalah kondisi dimana ketika kolom No Manifest telah terisi namun status masih **DONE ONLINE**
        - Untuk Branch adalah disesuaikan dan di split berdasarkan cabang dari masing-masing transaksi yang masih berstatus **DONE ONLINE**
        """)
    # --- INIT STATE ---
    if "ws_manifest_fdr" not in st.session_state: st.session_state.ws_manifest_fdr = None
    if "ws_fu_it_fdr" not in st.session_state: st.session_state.ws_fu_it_fdr = None
    if "dict_kurir_fdr" not in st.session_state: st.session_state.dict_kurir_fdr = {}
    if "fdr_current_file" not in st.session_state: st.session_state.fdr_current_file = None
    if "metrics_data" not in st.session_state: st.session_state.metrics_data = {}

    # --- FILE UPLOAD ---
    u_file = st.file_uploader("📂 Upload File Manifest", type=["xlsx"], key="fdr_upload_fix")

    # --- TOMBOL RUN UTAMA ---
    if u_file:
        if st.button("▶️PROCESS DATA", type="primary", use_container_width=True):
            try:
                with st.spinner("🔄 Processing..."):
                    # 1. LOAD DATA
                    df_raw = pd.read_excel(u_file)
                    
                    # 2. HAPUS KOLOM (G,H,I,K,L,M,R,S,T,U,V,W)
                    # Ini urutan kolom Excel: 7,8,9,11,12,13,18,19,20,21,22,23
                    # Di Python (0-indexed): 6,7,8,10,11,12,17,18,19,20,21,22
                    cols_to_drop = [6, 7, 8, 10, 11, 12, 17, 18, 19, 20, 21, 22]
                    existing_cols = [df_raw.columns[i] for i in cols_to_drop if i < len(df_raw.columns)]
                    df_clean = df_raw.drop(columns=existing_cols) if existing_cols else df_raw.copy()
                    
                    # 3. BERSIHKAN "NONE/NAN" (Biar nggak ada tulisan babi di dashboard)
                    df_clean = df_clean.fillna("")
                    for col in df_clean.columns:
                        df_clean[col] = df_clean[col].astype(str).replace(['None', 'nan', 'NaN', '0', '0.0'], '').str.strip()
                    
                    st.session_state.ws_manifest_fdr = df_clean

                    # 4. LOGIKA COPY-PASTE MACRO (AutoFilter Field 13 & 12)
                    # Field 13 VBA = Index 12 Python (Kolom M) -> PERLU FU IT
                    # Field 12 VBA = Index 11 Python (Kolom L) -> BRANCH
                    
                    if len(df_clean.columns) >= 13:
                        c_it = df_clean.iloc[:, 12]     # Kolom M (Field 13)
                        c_branch = df_clean.iloc[:, 11] # Kolom L (Field 12)

                        # FU IT: Kolom M (Field 13) TIDAK KOSONG ("<>")
                        mask_fu = c_it != ""
                        st.session_state.ws_fu_it_fdr = df_clean[mask_fu].copy()

                        # BRANCH: Kolom M KOSONG & Kolom L ADA ISI
                        mask_br = (c_it == "") & (c_branch != "")
                        df_br = df_clean[mask_br].copy()

                        if not df_br.empty:
                            st.session_state.dict_kurir_fdr = {
                                str(n): g for n, g in df_br.groupby(c_branch[mask_br].str.upper())
                            }
                        else:
                            st.session_state.dict_kurir_fdr = {}
                    else:
                        st.session_state.ws_fu_it_fdr = pd.DataFrame()
                        st.session_state.dict_kurir_fdr = {}
                    
                    # 5. Metrics Update
                    st.session_state.metrics_data = {
                        'total': len(st.session_state.ws_manifest_fdr),
                        'fu': len(st.session_state.ws_fu_it_fdr),
                        'kurir': len(st.session_state.dict_kurir_fdr)
                    }
                    
                    st.rerun()

            except Exception as e:
                st.error(f"❌ Error saat proses: {e}")

    # --- TAMPILKAN HASIL & METRICS ---
    if st.session_state.ws_manifest_fdr is not None:
        m = st.session_state.metrics_data
        
        # --- LOGIKA SISA DATA (MANIFEST - FU IT) ---
        total_val = m.get('total', 0)
        fu_val = m.get('fu', 0)
        sisa_data = total_val - fu_val 
        
        st.markdown(f"""
        <div style="display: flex; gap: 10px; justify-content: center; margin-bottom: 20px;">
            <div class="m-box" style="flex:1"><span class="m-lbl">TOTAL MANIFEST</span><span class="m-val">{total_val}</span></div>
            <div class="m-box" style="flex:1"><span class="m-lbl">FU IT</span><span class="m-val" style="color:#FFA500">{fu_val}</span></div>
            <div class="m-box" style="flex:1"><span class="m-lbl">NEED CHECK BRANCH</span><span class="m-val" style="color:#FF4B4B">{sisa_data}</span></div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🗑️ RESET DATA"): 
            st.session_state.ws_manifest_fdr = None
            st.session_state.dict_kurir_fdr = {}
            st.rerun()

        t1, t2, t3 = st.tabs(["📥 MANIFEST", "📋 FU IT", "🏭 BRANCH"])

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
                # --- DOWNLOAD ALL EXCEL (FIX DUPLICATE SHEET NAMES) ---
                import io
                buff = io.BytesIO()
                with pd.ExcelWriter(buff, engine='xlsxwriter') as w:
                    used_names = set() # Buat nyatet nama sheet yang udah dipake
                    for n, d in st.session_state.dict_kurir_fdr.items():
                        # 1. Bersihin nama: max 31 karakter & hapus karakter terlarang [ ] : * ? / \
                        sheet_name = str(n)[:31].strip()
                        for char in "[]:*?/\ ": sheet_name = sheet_name.replace(char, "_")
                        
                        # 2. Logic Anti-Duplikat
                        original_name = sheet_name
                        counter = 1
                        while sheet_name.lower() in used_names:
                            suffix = f"_{counter}"
                            sheet_name = f"{original_name[:31-len(suffix)]}{suffix}"
                            counter += 1
                        
                        used_names.add(sheet_name.lower())
                        d.to_excel(w, sheet_name=sheet_name, index=False)
                
                st.download_button("📊 Download All Excel", buff.getvalue(), "All_Warehouse.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                
                # Download Selected
                if opt:
                    st.download_button(f"📥 {opt}", st.session_state.dict_kurir_fdr[opt].to_csv(index=False).encode('utf-8'), f"{opt}.csv", "text/csv")
                    st.dataframe(st.session_state.dict_kurir_fdr[opt], use_container_width=True, hide_index=True)

elif menu == "Justification SO":
    st.markdown('<div class="hero-header"><h1>JUSTIFICATION ADJUSTMENT</h1></div>', unsafe_allow_html=True)
    
    with st.expander("📋 Informasi Format File"):
        st.info("""
        **Format yang diharapkan:**
        - **ADJUSTMENT FILE**: Gabungkan antara Adjustment **(Plus)** dan **(Minus)** dalam 1 File dan **QTY SO** yang telah terisi dengan qty yang akan diadjustment.
        - **SUMMARY STOCK**: Download **SUMMARY STOCK** dari **POWER BI** (Store: **JEZ SURABAYA**).
        - **PURCHASE ORDER**: Download **PURCHASE ORDER** dari **POWER BI**, Period Invoice & Receive IN: **ALL TIME** (Store: **JEZ SURABAYA**).
        """)

    with st.expander("💡 Logic Thinking"):
        st.info("""
        **Logic Justifikasi:**
        - **Kesalahan Adjustment**
            - **Kondisi 1:** Jika **QTY System > QTY SO (ADJ -)**, namun **Gap Adjustment bernilai (+)**.
            - **Kondisi 2:** Jika **QTY System < QTY SO (ADJ +)**, namun **Gap Adjustment bernilai (-)**.
        - **Perlu Cek Sales/RTO**
            - Jika Total Sales > (Total PO IN + Total TF IN).
        - **Cek Ulang Hasil Rekon**
            - Jika **Real QTY** [(PO IN + TF IN) - (SALES + TF OUT + DRAFT TF)] hasilnya sama dengan (=) **Current Stock**.
        - **Indikasi Bug Sistem**
            - **Kondisi 1:** Jika (Real QTY = 0 AND Gap Adjustment = 0) tapi **Current Stock ≠ 0**.
            - **Kondisi 2:** Jika QTY System > QTY SO AND Current Stock > Real QTY.
            - **Kondisi 3:** Jika QTY System < QTY SO AND Current Stock < Real QTY (L2 & T2 ≠ 0).
        - **UNDEFINED**
            - **Kondisi dimana ke-4 Logic diatas tidak ada yang sesuai sehingga memerlukan analisa detail secara manual untuk cek justifikasinya.**
        """)
    # 1. Inisialisasi Session State biar data nggak hilang pas diklik
    if 'result_so' not in st.session_state:
        st.session_state.result_so = None

    # UI Uploader - Dibagi 3 Kolom
    col1, col2, col3 = st.columns(3)
    with col1: 
        up_case = st.file_uploader("Upload FILE ADJUSMENT", type=['xlsx'], key="up_case_so")
    with col2: 
        up_tracking = st.file_uploader("Upload SUMMARY STOCK", type=['xlsx'], key="up_track_so")
    with col3: 
        up_others = st.file_uploader("Upload PURCHASE ORDER", type=['xlsx'], key="up_po_so")

    # 2. Logika Tombol Run
    if up_case and up_tracking and up_others:
        if st.button("▶️ RUN COMPARE", use_container_width=True):
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
        c_sales = len(result[result['JUSTIFICATION'] == "CEK SALES/RTO"])
        c_rekon = len(result[result['JUSTIFICATION'] == "CEK ULANG HASIL REKON"])

        m1.markdown(f'<div class="m-box"><span class="m-lbl">❓UNDEFINED</span><span class="m-val">{c_undef}</span></div>', unsafe_allow_html=True)
        m2.markdown(f'<div class="m-box"><span class="m-lbl">💻BUG SISTEM</span><span class="m-val">{c_bug}</span></div>', unsafe_allow_html=True)
        m3.markdown(f'<div class="m-box"><span class="m-lbl">❌KESALAHAN ADJ</span><span class="m-val">{c_adj}</span></div>', unsafe_allow_html=True)
        m4.markdown(f'<div class="m-box"><span class="m-lbl">🗳️CEK SALES/RTO</span><span class="m-val">{c_sales}</span></div>', unsafe_allow_html=True)
        m5.markdown(f'<div class="m-box"><span class="m-lbl">🔁CEK ULANG HASIL REKON</span><span class="m-val">{c_rekon}</span></div>', unsafe_allow_html=True)
        
        # --- TAMPILAN TABEL ---
        st.divider()
        st.markdown("""
                <div style="background-color: #f0f2f6; padding: 10px; border-left: 5px solid #007BFF; border-radius: 5px; margin-bottom: 20px;">
                <h3 style="color: #010B13; margin: 0; font-size: 30px;">📋RINGKASAN HASIL</h3>
                </div>
                """, unsafe_allow_html=True)
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
    with st.expander("📋 Informasi Format File"):
        st.info("""
        **Format yang diharapkan:**
        - **STOCK SYSTEM 1**: Download ALL DATA STOCK Setelah jam operasional **Shift 2 (22:00)**
        - **STOCK SYSTEM 2**: Download ALL DATA STOCK Sebelum jam operasional **Shift 0 (07:30)**
        """)
    with st.expander("💡Logic Thinking"):
        st.info("""
        **Alur Compare :**
        - Untuk Compare hanya menggunakan logic rumus **SUMIFS** dimana akan dilakukan di kedua file sehingga mengetahui apakah terdapat perbedaan QTY saat tidak terjadi transaksi
        - Untuk item yang berbeda akan dipisahkan dan akan dilakukan follow Up ke tim IT untuk dilakukan perbaikan
        """)
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

import pandas as pd
import random
from datetime import datetime, timedelta
import streamlit as st
from supabase import create_client

# 1. INISIALISASI SUPABASE
SUPABASE_URL = "https://ufhjrsxzcffdfswfqlzk.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVmaGpyc3h6Y2ZmZGZzd2ZxbHprIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYxNTI5NjgsImV4cCI6MjA5MTcyODk2OH0.DDlKkXU5-nVvNYK_uLYzXLgaj8oDT4s8vbjAoWMWacI"
@st.cache_resource
def init_supabase():
    from supabase import create_client
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# 2. FUNGSI DATABASE (SINKRON SUPABASE)
@st.cache_data(ttl=60) # Cache data 60 detik biar gak loading terus
def get_karyawan():
    res = supabase.table("karyawan").select("*").execute()
    return pd.DataFrame(res.data)

def add_karyawan(nama, posisi, tipe):
    try:
        nama_fix = nama.upper().strip()
        supabase.table("karyawan").insert({"nama": nama_fix, "posisi": posisi, "tipe": tipe}).execute()
        st.cache_data.clear() # <--- TAMBAHKAN INI AGAR CACHE KERESET SAAT NAMBAH ORANG
    except Exception as e:
        st.error(f"Gagal tambah: {e}")

# --- START UI LOGISTIC SCHEDULE ---
if menu == "Logistic Schedule":
    # --- CSS V-PREMIUM: ELEGAN, CLEAN & PROFESIONAL (RESTORASI TOTAL) ---
    st.markdown("""
        <style>
            /* 1. Header Utama - Efek Gradient Glass */
            .hero-header {
                background: linear-gradient(135deg, #0062E6 0%, #33AEFF 100%);
                color: white !important;
                padding: 25px;
                border-radius: 12px;
                text-align: center;
                margin-bottom: 35px;
                font-weight: 800;
                font-size: 26px;
                letter-spacing: 0.5px;
                box-shadow: 0 10px 20px rgba(0, 123, 255, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.1);
            }

            /* FIX: Gunakan [data-testid="stMain"] agar Sidebar TIDAK IKUT TERGANTI */
            [data-testid="stMain"] div[data-testid="stVerticalBlock"] h3 {
                color: #000000 !important;
                border-left: 5px solid #0062E6;
                padding-left: 15px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-top: 20px;
            }

            /* Tombol hapus kecil */
            .small-del-container div.stButton > button {
                width: 45px !important;
                height: 35px !important;
                padding: 0px !important;
                min-height: 35px !important;
                min-width: 45px !important;
                line-height: 1 !important;
                font-size: 16px !important;
                background: #1a1d2e !important;
                border: 1px solid rgba(255,255,255,0.1) !important;
                border-radius: 6px !important;
                margin-top: 5px !important;
            }

            .small-del-container div.stButton > button:hover {
                background: #FF4B4B !important;
                border-color: #FF4B4B !important;
            }

            /* Efek Focus */
            div[data-testid="stTextInput"] > div > div:focus-within, 
            div[data-testid="stDateInput"] > div > div:focus-within {
                border-color: #007BFF !important;
                box-shadow: 0 0 12px rgba(0, 123, 255, 0.3) !important;
            }

            /* Font & Labels - Batasi juga ke area Main agar label sidebar aman */
            [data-testid="stMain"] label { 
                color: #B0B3B8 !important; 
                font-size: 14px !important;
                font-weight: 500 !important;
                margin-bottom: 8px !important;
            }

            .custom-card {
                display: flex;
                align-items: center;
                justify-content: space-between;
                background-color: #1a1c27;
                border-radius: 8px;
                padding: 12px 18px;
                margin-bottom: 10px;
                border-left: 5px solid #00FF00;
                box-shadow: 0 4px 6px rgba(0,0,0,0.2);
            }
            .card-text { color: #FFFFFF !important; font-weight: 700; text-transform: uppercase; font-size: 14px; }
            .card-subtext { color: #888888 !important; font-size: 12px; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="hero-header">📅 LOGISTIC SCHEDULE MAKER</div>', unsafe_allow_html=True)

    # --- 1. DATABASE TIM ---
    st.subheader("👤 1. Database & Input Tim")
    with st.form("form_tim_komplit", clear_on_submit=True): 
        c1, c2, c3 = st.columns(3)
        nama_input = c1.text_input("Nama Lengkap")
        posisi_input = c2.selectbox("Posisi/Role", 
            ["WF-PICKER", "WF-ADMIN", "LOG-ADMIN", "LOG-LOADER", "LOG-STORE", "LOG-SO", "WF-SO", "SPV"])
        tipe_input = c3.selectbox("Tipe Kontrak", ["Full-Time", "Part-Full", "Part-Time"])
        
        if st.form_submit_button("💾 SIMPAN TIM"):
            if nama_input:
                add_karyawan(nama_input, posisi_input, tipe_input)
                st.success("✅ Tim Berhasil Terdaftar!")
                st.rerun()

    # --- DAFTAR KARYAWAN AKTIF ---
    with st.expander("🔍 Staff Database", expanded=True):
        df_cek = get_karyawan()
        if not df_cek.empty:
            for i, row in df_cek.iterrows():
                cc1, cc2 = st.columns([6, 1])
                with cc1:
                    st.markdown(f"""
                        <div class="custom-card" style="border-left-color: #007BFF;">
                            <div>
                                <div class="card-text">{row['nama']}</div>
                                <div class="card-subtext">{row['posisi']} • {row['tipe']}</div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                with cc2:
                    # Saat menghapus karyawan:
                    if st.button("🗑️", key=f"staff_{row['nama']}_{i}", use_container_width=True):
                        supabase.table("karyawan").delete().eq("nama", row['nama']).execute()
                        st.cache_data.clear() # <--- TAMBAHKAN INI
                        st.rerun()
        else:
            st.info("Belum ada data tim di database.") 

    st.divider()

    # --- 2. PLOT LIBUR ---
    st.subheader("🚫 2. Day Off Request")
    col_l1, col_l2 = st.columns([1, 2])
    with col_l1:
        df_k = get_karyawan()
        with st.form("form_libur_komplit", clear_on_submit=True):
            target = st.selectbox("Pilih Nama", df_k['nama']) if not df_k.empty else None
            tgl_off = st.date_input("Tanggal Off")
            jenis_off = st.radio("Jenis", ["LIBUR", "CUTI", "LPH"], horizontal=True)
            if st.form_submit_button("SUBMIT OFF"):
                if target:
                    supabase.table("libur_request").insert({"nama": target, "tanggal": str(tgl_off), "jenis": jenis_off}).execute()
                    st.rerun()

    with col_l2:
        res_off = supabase.table("libur_request").select("*").order("tanggal", desc=True).execute()
        df_off_view = pd.DataFrame(res_off.data)
        if not df_off_view.empty:
            for i, row in df_off_view.iterrows():
                m1, m2 = st.columns([6, 1])
                with m1:
                    st.markdown(f"""
                        <div class="custom-card" style="border-left-color: #FF4B4B;">
                            <div>
                                <div class="card-text">{row['nama']}</div>
                                <div class="card-subtext">{row['tanggal']} • {row['jenis']}</div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                with m2:
                    if st.button("🗑️", key=f"libur_{row['nama']}_{row['tanggal']}_{i}", use_container_width=True):
                        supabase.table("libur_request").delete().eq("nama", row['nama']).eq("tanggal", row['tanggal']).execute()
                        st.rerun()

    st.divider()

    # --- 3. DATABASE CHECK & MONITORING SHIFT 3 ---
    st.subheader("🌙 2. Stock Opname Plot")
    res_s3 = supabase.table("plot_shift3").select("*").order("tanggal", desc=True).execute()
    df_monitor_s3 = pd.DataFrame(res_s3.data)

    df_karyawan_s3 = get_karyawan()
    karyawan_options = df_karyawan_s3['nama'].tolist() if not df_karyawan_s3.empty else []

    col_in1, col_in2 = st.columns(2)
    with col_in1:
        nama_s3 = st.selectbox("Pilih Nama Tim", karyawan_options, key="s3_name_input")
        tgl_s3 = st.date_input("Tanggal Masuk Shift 3", datetime.now(), key="s3_date_input")

    with col_in2:
        if not df_karyawan_s3.empty and nama_s3:
            selected_data = df_karyawan_s3[df_karyawan_s3['nama'] == nama_s3].iloc[0]
            st.info(f"Posisi: {selected_data['posisi']} | Tipe: {selected_data['tipe']}")

    if st.button("SUBMIT PLOT SHIFT 3", use_container_width=True):
        check = supabase.table("plot_shift3").select("*").eq("nama", nama_s3).eq("tanggal", tgl_s3.strftime('%Y-%m-%d')).execute()
        if not check.data:
            supabase.table("plot_shift3").insert({
                "nama": nama_s3, "tanggal": tgl_s3.strftime('%Y-%m-%d'), 
                "posisi": selected_data['posisi'], "tipe": selected_data['tipe']
            }).execute()
            st.success(f"✅ {nama_s3} Masuk Plot Shift 3!")
            st.rerun()
        else:
            st.warning("Nama ini sudah terdaftar di tanggal tersebut!")

    if not df_monitor_s3.empty:
        for index, row in df_monitor_s3.iterrows():
            lc1, lc2, lc3 = st.columns([3, 1, 0.5])
            with lc1:
                st.markdown(f"""
                    <div style="background-color: #1a1c27; padding: 10px; border-radius: 5px; border-left: 5px solid #00FF00; margin-bottom: 5px;">
                        <span style="color: #FFFFFF; font-weight: bold;">{row['nama']}</span>
                    </div>
                """, unsafe_allow_html=True)
            with lc2:
                st.markdown(f"<div style='padding: 10px; color: #888;'>{row['tanggal']}</div>", unsafe_allow_html=True)
            with lc3:
                if st.button("🗑️", key=f"del_s3_{index}"):
                    supabase.table("plot_shift3").delete().eq("nama", row['nama']).eq("tanggal", row['tanggal']).execute()
                    st.rerun()
    else:
        st.info("Belum ada tim yang di-plot ke Shift 3.")

    st.divider()

    # --- 4. GENERATOR JADWAL JEZ SBY (ENGINE FULL RECOVERY) ---
    st.subheader("✅ 3. Schedule Shift")
    start_date = st.date_input("Pilih Hari Senin", datetime.now(), key="log_gen_date_v_final")
    df_staff_master = get_karyawan()
    karyawan_list = df_staff_master.to_dict('records')

    if st.button("▶️ RUN JADWAL", use_container_width=True):
        dates_real = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
        day_names = ["SENIN", "SELASA", "RABU", "KAMIS", "JUMAT", "SABTU", "MINGGU"]
        
        libur_data = supabase.table("libur_request").select("*").execute()
        df_libur = pd.DataFrame(libur_data.data)
        
        manual_s3_data = supabase.table("plot_shift3").select("*").execute()
        df_manual_s3 = pd.DataFrame(manual_s3_data.data)

        base_roles = [
            ("SHIFT 0", "WF-PICKER"), ("SHIFT 0", "WF-ADMIN"),
            ("SHIFT 1", "LOG-ADMIN"), ("SHIFT 1", "LOG-LOADER"), ("SHIFT 1", "LOG-STORE"), ("SHIFT 1", "WF-ADMIN"), ("SHIFT 1", "WF-PICKER"),
            ("SHIFT 2", "LOG-ADMIN"), ("SHIFT 2", "LOG-LOADER"), ("SHIFT 2", "LOG-STORE"), ("SHIFT 2", "WF-ADMIN"), ("SHIFT 2", "WF-PICKER"), ("SHIFT 2", "SPV"),
            ("SHIFT 3", "SO") 
        ]

        storage = {d: {f"{s} - {r}": [] for s, r in base_roles} for d in day_names}
        weekly_counter = {k['nama']: 0 for k in karyawan_list}
        double_day_count = {k['nama']: 0 for k in karyawan_list}
        for k in karyawan_list: k['target_fix'] = 9 if k['tipe'] == "Part-Full" else 6

        def get_active_shifts(nama, day_name):
            return [slot.split(" - ")[0] for slot in storage[day_name] if any(nama in n for n in storage[day_name][slot])]

        # --- 1. PLOT MANUAL SHIFT 3 ---
        for day_name, tgl_str in zip(day_names, dates_real):
            if not df_manual_s3.empty:
                names_manual = df_manual_s3[df_manual_s3['tanggal'] == tgl_str]['nama'].tolist()
                if names_manual:
                    storage[day_name]["SHIFT 3 - SO"] = names_manual
                    for nm in names_manual:
                        if nm in weekly_counter: weekly_counter[nm] += 1

        # --- 2. ENGINE GENERATOR (PHASE LOOP) ---
        for phase in ["TARGET_1_ORANG", "TARGET_2_ORANG", "SISA_JATAH"]:
            for day_name in day_names:
                tgl_ini = dates_real[day_names.index(day_name)]
                
                def count_s0(day):
                    count = 0
                    for k_slot in storage[day]:
                        if "SHIFT 0" in k_slot: count += len(storage[day][k_slot])
                    return count

                for shf_jam, shf_role in base_roles:
                    if shf_jam == "SHIFT 3": continue 
                    slot_key = f"{shf_jam} - {shf_role}"

                    # --- [PRIORITAS 1: JALUR VIP RECOVERY] ---
                    if shf_jam == "SHIFT 2":
                        day_index = day_names.index(day_name)
                        if day_index > 0:
                            day_kemarin = day_names[day_index - 1]
                            for k_rec in karyawan_list:
                                n_rec = k_rec['nama']
                                if weekly_counter[n_rec] >= k_rec['target_fix']: continue
                                if not df_libur.empty and not df_libur[(df_libur['nama'] == n_rec) & (df_libur['tanggal'] == tgl_ini)].empty: continue
                                if "SHIFT 3" in get_active_shifts(n_rec, day_kemarin) and k_rec['posisi'] == shf_role:
                                    if not get_active_shifts(n_rec, day_name):
                                        current_fill = len(storage[day_name][slot_key])
                                        if (phase == "TARGET_1_ORANG" and current_fill < 1) or \
                                           (phase == "TARGET_2_ORANG" and shf_role != "SPV" and current_fill < 2) or \
                                           (phase == "SISA_JATAH"):
                                            if n_rec not in storage[day_name][slot_key]:
                                                storage[day_name][slot_key].append(n_rec)
                                                weekly_counter[n_rec] += 1

                    # --- [PRIORITAS 2: LOGIKA STANDAR] ---
                    if shf_jam == "SHIFT 0" and count_s0(day_name) >= 2: continue
                    if phase == "TARGET_1_ORANG" and len(storage[day_name][slot_key]) >= 1: continue
                    if phase == "TARGET_2_ORANG" and (shf_role == "SPV" or len(storage[day_name][slot_key]) >= 2): continue

                    potential = []
                    for k in karyawan_list:
                        nama = k['nama']
                        active_shifts = get_active_shifts(nama, day_name)
                        if weekly_counter[nama] >= k['target_fix']: continue
                        if not df_libur.empty and not df_libur[(df_libur['nama'] == nama) & (df_libur['tanggal'] == tgl_ini)].empty: continue
                        
                        tgl_besok = (datetime.strptime(tgl_ini, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
                        tgl_kemarin = (datetime.strptime(tgl_ini, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')
                        is_libur_besok = not df_libur.empty and not df_libur[(df_libur['nama'] == nama) & (df_libur['tanggal'] == tgl_besok)].empty
                        is_libur_kemarin = not df_libur.empty and not df_libur[(df_libur['nama'] == nama) & (df_libur['tanggal'] == tgl_kemarin)].empty
                        
                        if is_libur_besok and shf_jam != "SHIFT 1": continue
                        if is_libur_kemarin and shf_jam != "SHIFT 2": continue

                        day_index = day_names.index(day_name)
                        if day_index > 0:
                            if "SHIFT 3" in get_active_shifts(nama, day_names[day_index - 1]) and shf_jam != "SHIFT 2": continue

                        if shf_role in ["LOG-ADMIN", "LOG-STORE", "SPV"] and k['posisi'] != shf_role: continue
                        if k['posisi'] == "SPV" and shf_role != "SPV": continue
                        if shf_jam in active_shifts: continue 

                        if k['tipe'] == "Part-Full":
                            if is_libur_besok or is_libur_kemarin or (day_index > 0 and "SHIFT 3" in get_active_shifts(nama, day_names[day_index-1])):
                                if active_shifts: continue 
                            if len(active_shifts) >= 2 or (len(active_shifts) == 1 and double_day_count[nama] >= 3): continue
                        else:
                            if active_shifts: continue

                        potential.append({'k': k, 'match': (k['posisi'] == shf_role)})

                    if potential:
                        random.shuffle(potential)
                        potential = sorted(potential, key=lambda x: x['match'], reverse=True)
                        p = potential[0]
                        nm_fix = p['k']['nama']
                        if nm_fix not in storage[day_name][slot_key]:
                            storage[day_name][slot_key].append(nm_fix)
                            weekly_counter[nm_fix] += 1
                            if len(get_active_shifts(nm_fix, day_name)) == 2: double_day_count[nm_fix] += 1

        # --- 3. SIMPAN HASIL ---
        final_table = []
        for shf_jam, shf_role in base_roles:
            slot_key = f"{shf_jam} - {shf_role}"
            max_r = max([len(storage[d][slot_key]) for d in day_names])
            for r in range(max(1, max_r)):
                row = {"SHIFT - ROLE": slot_key}
                for d in day_names:
                    names = storage[d][slot_key]
                    row[d] = names[r] if r < len(names) else ""
                final_table.append(row)

        st.session_state.res_df = pd.DataFrame(final_table)
        st.session_state.summary_shift = weekly_counter
        st.rerun()

    # --- 5. TAMPILAN TABEL JADWAL ---
    if 'res_df' in st.session_state:
        st.divider()
        col_v1, col_v2 = st.columns([5, 2])
        
        with col_v1:
            st.markdown("### 📋 WEEKLY SCHEDULE LOGISTIC SBY")
            def color_by_shift(row):
                shift_type = str(row['SHIFT - ROLE'])
                base_style = 'color: #FFFFFF; font-weight: 600; border: 0.5px solid #222;'
                if "SHIFT 0" in shift_type: bg = "background-color: #004e92;"
                elif "SHIFT 1" in shift_type: bg = "background-color: #1b4d3e;"
                elif "SHIFT 2" in shift_type: bg = "background-color: #4b0082;"
                elif "SHIFT 3" in shift_type: bg = "background-color: #b45f06;"
                else: bg = "background-color: #1a1c27;"
                return [bg + base_style for _ in row]

            st.dataframe(st.session_state.res_df.style.apply(color_by_shift, axis=1), 
                         use_container_width=True, height=800, hide_index=True)

        with col_v2:
            st.markdown("### 📈 TOTAL SHIFT")
            sum_data = []
            df_staff_master = get_karyawan()
            for _, k in df_staff_master.iterrows():
                n = k['nama']
                t = st.session_state.summary_shift.get(n, 0)
                if t > 0:
                    target = 9 if k['tipe'] == "Part-Full" else 6
                    sum_data.append({"NAMA": n, "SHIFT": int(t), "STATUS": "✅ OK" if t >= target else "⚠️ KURANG"})
            
            if sum_data:
                st.dataframe(pd.DataFrame(sum_data).sort_values(by="SHIFT", ascending=False), 
                             use_container_width=True, hide_index=True)

elif menu == "Balancing Stock":
    tampilan_balancing_stock()

elif menu == "Refill & Withdraw":
    menu_refill_withdraw()

# --- Navigasi ---
elif menu == "Stock Opname":
    menu_Stock_Opname()

# --- Navigasi ---
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

import streamlit as st
import pandas as pd
from datetime import datetime

# Trik agar tidak error di laptop meskipun library supabase belum terinstall
try:
    from supabase import create_client, Client
    HAS_SUPABASE = True
except ImportError:
    HAS_SUPABASE = False

# Konfigurasi Supabase
if HAS_SUPABASE:
    # Nama variabel harus konsisten
    SUPABASE_URL = "https://ufhjrsxzcffdfswfqlzk.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVmaGpyc3h6Y2ZmZGZzd2ZxbHprIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYxNTI5NjgsImV4cCI6MjA5MTcyODk2OH0.DDlKkXU5-nVvNYK_uLYzXLgaj8oDT4s8vbjAoWMWacI"
    
    # PERBAIKAN: Gunakan nama variabel yang sudah didefinisikan di atas
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    st.warning("Menjalankan mode lokal tanpa Database Cloud (Hanya untuk Testing)")

# --- FUNGSI UPDATE STATUS ---
def update_report_status(laporan_name):
    if HAS_SUPABASE:
        try:
            supabase.table("reports").update({"status": "✅ Selesai"}).eq("laporan", laporan_name).execute()
        except Exception as e:
            st.error(f"Gagal update ke database: {e}")
    else:
        # Fallback ke session state saja kalau di lokal
        if 'db_report' in st.session_state:
            for item in st.session_state.db_report:
                if item['Laporan'] == laporan_name:
                    item['Status'] = "✅ Selesai"

import pandas as pd
import streamlit as st
import math
from datetime import datetime
from supabase import create_client, Client

# --- 1. KONEKSI SUPABASE ---
SUPABASE_URL = "https://ufhjrsxzcffdfswfqlzk.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVmaGpyc3h6Y2ZmZGZzd2ZxbHprIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYxNTI5NjgsImV4cCI6MjA5MTcyODk2OH0.DDlKkXU5-nVvNYK_uLYzXLgaj8oDT4s8vbjAoWMWacI"
@st.cache_resource
def init_supabase():
    from supabase import create_client
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# --- 2. FUNGSI SINKRONISASI & RESET HARIAN ---
def sync_data():
    """Tarik data dari Supabase ke Session State & Handle Reset Harian"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    # A. Cek & Reset Harian
    res_date = supabase.table("reset_tracker").select("*").execute()
    
    if not res_date.data:
        supabase.table("reset_tracker").insert({"last_date": today}).execute()
    elif res_date.data[0]['last_date'] != today:
        # Reset Reports & To-Do (Ganti hari)
        supabase.table("reports").update({"status": "❌ Belum"}).neq("status", "❌ Belum").execute()
        supabase.table("todo").update({"done": False}).eq("done", True).execute()
        # Update tanggal
        supabase.table("reset_tracker").update({"last_date": today}).eq("id", res_date.data[0]['id']).execute()

    # B. Tarik data Reports
    res_reports = supabase.table("reports").select("*").order("id").execute()
    
    # C. Default Data jika kosong
    if not res_reports.data:
        default_reports = [
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
        supabase.table("reports").insert(default_reports).execute()
        res_reports = supabase.table("reports").select("*").order("id").execute()

    st.session_state.db_report = [{"Laporan": r['laporan'], "PIC": r['pic'], "Status": r['status']} for r in res_reports.data]
    
    # D. Tarik Data To Do List
    res_todo = supabase.table("todo").select("*").order("id").execute()
    st.session_state.todo_list = [{"id": t['id'], "task": t['task'], "done": t['done']} for t in res_todo.data]

if 'db_report' not in st.session_state:
    sync_data()

# --- 3. FULL CSS (GABUNGAN SEMUA STYLE) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

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


# --- 4. MAIN UI (PASTIKAN KUTIPAN DITUTUP & INDENTASI BENAR) ---
# --- 4. MAIN UI ---
# Pastikan variabel 'menu' sudah didefinisikan sebelumnya di sidebar
if menu == "Reporting & PIC":
    st.markdown('<div class="hero-header">🚹 REPORTING & PIC - JEZPRO</div>', unsafe_allow_html=True)

    list_pic = ["VERREL & GALIH", "FARIL & YUDI", "BAKCLINER", "VANO", "HAMZAH", "KRISNA & DHIVA", "WAREHOUSE FULLFILLMENT"]
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
                                supabase.table("reports").update({"status": "✅ Selesai"}).eq("laporan", task['Laporan']).execute()
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
            td_total = len(st.session_state.todo_list)
            td_done = sum(1 for i in st.session_state.todo_list if i['done'])
            td_prog = (td_done / td_total * 100) if td_total > 0 else 0
            
            # --- PROGRESS TO DO LIST (JARAK DISAMAKAN) ---
            td_total = len(st.session_state.get('todo_list', []))
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
                supabase.table("todo").insert({"task": tugas_baru, "done": False}).execute()
                sync_data()
                st.rerun()

        # 2. LOGIKA PAGINATION (Penting biar current_todo kedeteksi)
        items_per_page = 3
        total_items = len(st.session_state.get('todo_list', []))
        total_pages = math.ceil(total_items / items_per_page) if total_items > 0 else 1
        
        # Ambil halaman aktif
        curr_p = st.session_state.get('todo_page', 1)
        
        # Hitung data yang tampil di halaman ini
        start = (curr_p - 1) * items_per_page
        current_todo = st.session_state.get('todo_list', [])[start : start + items_per_page]

        # 3. RENDER LIST TUGAS
        for item in current_todo:
            c1, c2 = st.columns([4, 1])
            bd_color = "#10b981" if item['done'] else "#3b82f6"
            
            # Card dengan margin-bottom 10px biar gak mepet
            c1.markdown(f'''
                <div style="background:#111827; padding:12px; border-radius:8px; 
                            border-left:4px solid {bd_color}; color:white; 
                            margin-bottom:10px; min-height:50px; display:flex; align-items:center;">
                    {item["task"]}
                </div>
            ''', unsafe_allow_html=True)
            
            with c2:
                st.write("") # Spacer biar sejajar tengah
                res = st.checkbox("", value=item['done'], key=f"chk_{item['id']}", label_visibility="collapsed")
                if res != item['done']:
                    supabase.table("todo").update({"done": res}).eq("id", item['id']).execute()
                    sync_data()
                    st.rerun()

        # --- Navigasi Halaman yang Dirapatkan ---
        if total_pages > 1:
            # Gunakan perbandingan kolom yang lebih sempit di tengah (0.5)
            # biar tombol kiri dan kanan lebih mendekat ke angka
            st.write("") 
            p1, p2, p3 = st.columns([1, 0.5, 1]) 
            
            with p1:
                if st.button("⬅️", key="prev_todo") and curr_p > 1:
                    st.session_state.todo_page = curr_p - 1
                    st.rerun()
            
            with p2:
                # Teks angka halaman dengan padding atas dikit biar sejajar tombol
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

elif menu == "Picking Audit":
    st.markdown('<div class="hero-header"><h1>PICKING AUDIT</h1></div>', unsafe_allow_html=True)
    
    with st.expander("📋 Informasi Format File"):
        st.info("""
        - **STOCK SYSTEM 1**: Data Awal Shift 0 (07.:30)
        - **STOCK SYSTEM 2**: Data End Shift 2 (21:30 - 22.00)
        - **STOCK TRACKING**: Download Stock Tracking **(TODAY)**, Pilih Statusnya **DONE**
        """)

    # --- 1. INISIALISASI (Taruh di paling atas menu) ---
    if 'audit_results' not in st.session_state:
        st.session_state.audit_results = None
    if 'audit_diff' not in st.session_state:
        st.session_state.audit_diff = None

    # --- 2. LAYOUT UPLOADER ---
    u1, u2, u3 = st.columns(3)
    with u1:
        file_sys1 = st.file_uploader("Upload Stock System 1", type=['xlsx', 'csv'])
    with u2:
        file_sys2 = st.file_uploader("Upload Stock System 2", type=['xlsx', 'csv'])
    with u3:
        file_tracking = st.file_uploader("Upload Stock Tracking", type=['xlsx', 'csv'])

    # --- 3. PROSES DATA (Hanya untuk simpan ke memory) ---
    if file_sys1 and file_sys2:
        if st.button("▶️ RUN COMPARE"):
            try:
                # Simpan hasil ke session_state agar tidak hilang
                all_data, diff_data = process_picking_audit(file_sys1, file_sys2, file_tracking)
                st.session_state.audit_results = all_data
                st.session_state.audit_diff = diff_data
            except Exception as e:
                st.error(f"Terjadi Kesalahan: {e}")

    # --- 4. TAMPILKAN HASIL (DI LUAR BLOK BUTTON) ---
    # Ini kuncinya! Selama session_state ada isinya, data bakal tetap muncul di layar
    if st.session_state.audit_results is not None:
        result_all = st.session_state.audit_results
        diff_only = st.session_state.audit_diff

        st.divider()

        # Summary Metrics
        m1, m2, m3 = st.columns(3)
        m1.markdown(f'<div class="m-box"><span class="m-lbl">📦 TOTAL ITEM</span><span class="m-val">{len(result_all)}</span></div>', unsafe_allow_html=True)
        m2.markdown(f'<div class="m-box"><span class="m-lbl">⚠️ SELISIH</span><span class="m-val">{len(diff_only)}</span></div>', unsafe_allow_html=True)
        
        if 'KETERANGAN' in diff_only.columns:
            sold_count = len(diff_only[diff_only['KETERANGAN'].str.contains("Terjual", na=False)])
            m3.markdown(f'<div class="m-box"><span class="m-lbl">📑 ITEM TERJUAL</span><span class="m-val">{sold_count}</span></div>', unsafe_allow_html=True)

        if not diff_only.empty:
            st.warning("Hasil Analisis Perbedaan Stok:")
            st.dataframe(diff_only, use_container_width=True)
            
            # Button download ditaruh di sini
            csv = diff_only.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Report Selisih",
                data=csv,
                file_name='hasil_Pick_stok.csv',
                mime='text/csv',
                key="download_audit_final" # Tambah key unik
            )
        else:
            st.success("✅ Tidak ada perbedaan stok!")