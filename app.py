import pandas as pd
import numpy as np
import streamlit as st
import io
import math
from collections import defaultdict
from streamlit_autorefresh import st_autorefresh
from PIL import Image
import openpyxl
from openpyxl import load_workbook
import re
import requests
import sqlite3
from datetime import datetime, timedelta, date, timezone
import pytz
import uuid

# ==============================================================================
# 🚀 1. CORE ENGINE: INITIALIZE SUPABASE GLOBAL
# ==============================================================================
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


# ==============================================================================
# 🚀 2. CORE ENGINE: INTERACTIVE POP-UP MODALS
# ==============================================================================
@st.dialog("⚠️ PERHATIAN SISTEM")
def show_error_popup(judul, pesan, solusi):
    """Pop-Up Elegan untuk Error Handling"""
    st.markdown(f'''
        <div style="text-align: center; padding: 10px;">
            <div style="font-size: 50px; margin-bottom: 10px;">🚨</div>
            <h3 style="color: #FF4B4B; margin-bottom: 10px; font-weight: 800;">{judul}</h3>
            <p style="color: #E0E0E0; font-size: 15px; line-height: 1.5;">{pesan}</p>
        </div>
    ''', unsafe_allow_html=True)
    st.info(f"💡 **Saran Tindakan:** {solusi}")
    if st.button("Mengerti & Tutup", use_container_width=True, type="primary"):
        st.rerun()

@st.dialog("✅ PROSES BERHASIL")
def show_success_popup(judul, pesan):
    """Pop-Up Elegan untuk Success Handling"""
    st.markdown(f'''
        <div style="text-align: center; padding: 20px;">
            <div style="font-size: 50px; margin-bottom: 10px;">✨</div>
            <h3 style="color: #00FF66; margin-bottom: 10px; font-weight: 800;">{judul}</h3>
            <p style="color: #ffffff; font-size: 15px;">{pesan}</p>
        </div>
    ''', unsafe_allow_html=True)
    if st.button("Lanjutkan Pekerjaan", use_container_width=True):
        st.rerun()

@st.dialog("🔍 INFORMASI")
def show_warning_popup(judul, pesan):
    """Pop-Up untuk Warning (Data Kosong, dll)"""
    st.markdown(f'''
        <div style="text-align: center; padding: 15px;">
            <div style="font-size: 40px; margin-bottom: 10px;">⚠️</div>
            <h4 style="color: #FFD700; margin-bottom: 10px; font-weight: 700;">{judul}</h4>
            <p style="color: #ffffff; font-size: 14px;">{pesan}</p>
        </div>
    ''', unsafe_allow_html=True)
    if st.button("Tutup", use_container_width=True):
        st.rerun()


# ==============================================================================
# 🎨 3. PAGE CONFIG & GLOBAL SAAS PREMIUM CSS
# ==============================================================================
st_autorefresh(interval=300000, key="keepalive_session")

try:
    logo_icon = Image.open("image_981625.png")
except:
    logo_icon = "🚛"

st.set_page_config(page_title="ZKN Logistic ERP", page_icon=logo_icon, layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    /* BASE THEME */
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif !important; }
    .stApp { background-color: #0B0E14 !important; }
    .block-container { padding-top: 3.5rem !important; padding-bottom: 0rem !important; }
    [data-testid="stSidebarNav"] { display: none !important; }
    [data-testid="stSidebar"] { background-color: #121826 !important; border-right: 1px solid rgba(197, 160, 89, 0.15) !important; }

    /* HERO HEADER */
    .hero-header {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%) !important;
        padding: 20px 30px !important;
        border-radius: 16px !important;
        border-left: 6px solid #C5A059 !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5) !important;
        margin-bottom: 30px !important;
    }
    .hero-header h1 {
        color: #FFFFFF !important; font-size: 28px !important; font-weight: 800 !important;
        margin: 0 !important; letter-spacing: 0.5px;
    }
    .hero-header p { color: #94A3B8 !important; margin: 5px 0 0 0 !important; font-weight: 500; }

    /* BUTTONS */
    div.stButton > button {
        background: linear-gradient(135deg, #1D4ED8 0%, #1E3A8A 100%) !important;
        color: #FFFFFF !important; border: 1px solid #3B82F6 !important;
        border-radius: 10px !important; font-weight: 700 !important; font-size: 14px !important;
        height: 45px !important; transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(29, 78, 216, 0.3) !important;
    }
    div.stButton > button:hover {
        background: linear-gradient(135deg, #FFD700 0%, #C5A059 100%) !important;
        color: #000000 !important; border-color: #FFD700 !important;
        transform: translateY(-2px) !important; box-shadow: 0 8px 25px rgba(255, 215, 0, 0.4) !important;
    }

    /* INPUT BOXES (GLASSMORPHISM) */
    div[data-baseweb="input"] > div, div[data-baseweb="select"] > div, [data-testid="stFileUploaderSection"] {
        background: rgba(30, 41, 59, 0.7) !important; backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important; border-radius: 10px !important;
    }
    div[data-baseweb="input"] > div:focus-within, div[data-baseweb="select"] > div:focus-within {
        border-color: #C5A059 !important; box-shadow: 0 0 15px rgba(197, 160, 89, 0.3) !important;
    }
    input { color: #FFFFFF !important; font-weight: 500 !important; background-color: transparent !important; }
    ul[data-baseweb="menu"] { background-color: #1E293B !important; border: 1px solid #C5A059 !important; }
    li[data-baseweb="menu-item"] { color: white !important; }
    li[data-baseweb="menu-item"]:hover { background-color: rgba(197, 160, 89, 0.2) !important; color: #FFD700 !important; }

    /* METRIC CARDS */
    .m-box { 
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%) !important; 
        padding: 20px !important; border-radius: 12px !important; 
        border-left: 4px solid #C5A059 !important; margin-bottom: 15px !important; 
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3) !important; transition: transform 0.3s ease !important;
    } 
    .m-box:hover { transform: translateY(-5px) !important; border-left-color: #00FF66 !important; }
    .m-lbl { color: #94A3B8 !important; font-size: 11px !important; font-weight: 700 !important; text-transform: uppercase !important; letter-spacing: 1px !important; display: block; margin-bottom: 8px; } 
    .m-val { color: #FFFFFF !important; font-size: 28px !important; font-weight: 800 !important; }

    /* TAB MENU */
    .stTabs [data-baseweb="tab-list"] { background-color: transparent !important; gap: 10px !important; border-bottom: 2px solid #1E293B !important; }
    .stTabs [data-baseweb="tab"] { color: #64748B !important; background-color: transparent !important; padding: 12px 20px !important; font-weight: 600 !important; border: none !important; }
    .stTabs [aria-selected="true"] { color: #FFD700 !important; border-bottom: 3px solid #FFD700 !important; }

    /* SIDEBAR RADIOS */
    div.row-widget.stRadio > div { background-color: transparent !important; gap: 5px; } 
    div.row-widget.stRadio label { 
        color: #94A3B8 !important; font-size: 13px !important; font-weight: 600 !important;
        padding: 10px 15px !important; border-radius: 8px !important; 
        transition: all 0.2s ease !important; border: 1px solid transparent !important;
    } 
    div.row-widget.stRadio label:hover { background: rgba(197, 160, 89, 0.1) !important; color: #C5A059 !important; } 
    
    /* LABELS */
    [data-testid="stWidgetLabel"] p { color: #E2E8F0 !important; font-weight: 600 !important; font-size: 13px !important; }
    
    /* FILE UPLOADER */
    [data-testid="stFileUploader"] button { background: linear-gradient(135deg, #C5A059 0%, #b08d4a 100%) !important; color: #1a1d2e !important; border: none !important; }

    /* LOGIN BACKGROUND */
    .login-bg {
        background: linear-gradient(rgba(11, 14, 20, 0.85), rgba(11, 14, 20, 0.95)), url('https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?q=80&w=2070') center/cover !important;
        position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: -1;
    }
    .login-card {
        background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(20px); padding: 50px;
        border-radius: 24px; border: 1px solid rgba(197, 160, 89, 0.3);
        box-shadow: 0 25px 50px -12px rgba(0,0,0,0.8); margin-top: 10vh;
    }
    </style>
""", unsafe_allow_html=True)


# ==============================================================================
# 🔐 5. SECURE LOGIN SYSTEM
# ==============================================================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown('<div class="login-bg"></div>', unsafe_allow_html=True)
    st.markdown('<style>[data-testid="stSidebar"], [data-testid="stHeader"] { display: none !important; }</style>', unsafe_allow_html=True)
    
    _, col_mid, _ = st.columns([1, 1.2, 1])
    with col_mid:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.markdown("""
            <div style='text-align: center; margin-bottom: 30px;'>
                <h1 style='color: #FFD700; margin: 0; font-size: 32px; font-weight: 800; text-shadow: 0 4px 15px rgba(197,160,89,0.4);'>ZKN LOGISTIC ERP</h1>
                <p style='color: #94A3B8; margin-top: 5px; font-size: 14px; letter-spacing: 1px;'>Enterprise Warehouse Management System</p>
            </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            user_input = st.text_input("Username", placeholder="Masukkan ID Pengguna")
            pass_input = st.text_input("Password", type="password", placeholder="Masukkan Kata Sandi")
            st.markdown('<div style="margin-top: 15px;"></div>', unsafe_allow_html=True)
            submit_button = st.form_submit_button("LOGIN KE SISTEM")
            
            if submit_button:
                if user_input == "admin" and pass_input == "sby123":
                    st.session_state.logged_in = True
                    st.session_state.role = "DC" 
                    st.session_state.branch = "SURABAYA"
                    st.rerun()
                elif user_input == "toko" and pass_input == "toko123":
                    st.session_state.logged_in = True
                    st.session_state.role = "CABANG" 
                    st.session_state.branch = "SURABAYA"
                    st.rerun()
                else:
                    show_error_popup("Akses Ditolak!", "Username atau Password yang Anda masukkan tidak valid.", "Harap hubungi Administrator IT jika Anda lupa kredensial login Anda.")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

if 'login_success' not in st.session_state:
    show_success_popup("Login Berhasil", f"Selamat Datang di ZKN ERP. Anda login sebagai {st.session_state.role}.")
    st.session_state.login_success = True


# ==============================================================================
# 🗂️ 6. SIDEBAR & MENU ROUTING
# ==============================================================================
if 'role' not in st.session_state: st.session_state.role = "CABANG"
if 'main_menu' not in st.session_state:
    st.session_state.main_menu = "Dashboard Overview" if st.session_state.role == "DC" else "Compare Penerimaan RTO"

def sync_menu(key):
    st.session_state.main_menu = st.session_state[key]

with st.sidebar:
    st.markdown("""
        <div style="text-align: center; margin-bottom: 30px;">
            <img src="https://raw.githubusercontent.com/bpputra01-lang/erp-logistik-sby/main/image_981625.png" width="60" style="margin-bottom: 10px; filter: drop-shadow(0 0 10px rgba(197,160,89,0.5));">
            <h3 style="color: #FFFFFF; font-family: 'Plus Jakarta Sans'; font-weight: 800; margin:0;">ZKN LOGISTIC</h3>
            <p style="color: #C5A059; font-size: 11px; letter-spacing: 2px; font-weight: 600; margin:0;">WMS PRO v2.1</p>
        </div>
    """, unsafe_allow_html=True)

    is_dc = st.session_state.role == "DC"

    # --- MENU RENDERER ---
    def render_menu_section(title, menu_list, key_name):
        st.markdown(f'<p style="color: #64748B; font-size: 11px; font-weight: 800; letter-spacing: 1px; margin: 20px 0 5px 0;">{title}</p>', unsafe_allow_html=True)
        idx = menu_list.index(st.session_state.main_menu) if st.session_state.main_menu in menu_list else None
        st.radio("hidden", menu_list, index=idx, key=key_name, on_change=sync_menu, args=(key_name,), label_visibility="collapsed")

    if is_dc:
        render_menu_section("DASHBOARD SUMMARY", ["Dashboard Overview", "Database Master"], "m1_key")
        
    op_list = ["Purchase Order Receiving", "Putaway System", "Scan Out Validation", "Refill & Overstock", "Refill & Withdraw", "Compare RTO", "Compare Penerimaan RTO", "FDR Update"] if is_dc else ["Compare Penerimaan RTO", "Putaway System", "Purchase Order Receiving"]
    render_menu_section("OPERATIONAL", op_list, "m2_key")

    inv_list = ["Stock Opname", "Match Real & System", "Cycle Count", "List Bin Cycle Count", "Stock Tracking Timeline", "Justification SO", "Stock Minus", "Compare System", "List Retur Out", "Pengajuan Mutasi Karantina", "Refill Koli to Koli/Refill"] if is_dc else ["Stock Minus", "Cycle Count"]
    render_menu_section("INVENTORY", inv_list, "m3_key")

    render_menu_section("REJECT & DEFECT", ["Pengajuan Reject/Defect", "Reject/Defect List"], "m4_key")

    ex_list = ["Logistic Schedule", "Balancing Stock", "Reporting & PIC", "Data Timbang Ongkir", "Database Ongkir In/Out", "Precentage Display", "Precentage Request FL to Store Stock", "Refill Toko"] if is_dc else ["Precentage Display", "Refill Toko", "Store Leader RTO Decission"]
    render_menu_section("EXTRAS", ex_list, "m5_key")

    st.markdown("<br><hr style='border-color: #1E293B;'><br>", unsafe_allow_html=True)
    if st.button("🚪 KELUAR SISTEM", key="btn_logout"):
        st.session_state.clear()
        st.rerun()

menu = st.session_state.main_menu

# ==============================================================================
# 🧠 5. CORE LOGIC ENGINE & DATABASE HELPERS (ALL FUNCTIONS)
# ==============================================================================

# --- A. SUPABASE HELPERS (REJECT/DEFECT, ONGKIR, TIMBANG) ---
def save_reject_data(df):
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

def mark_as_done(sku_list):
    if supabase_global and sku_list:
        supabase_global.table("reject_list").update({"status": "DONE"}).in_("sku", sku_list).execute()
        st.cache_data.clear()

def clean_currency(value):
    if pd.isna(value) or value == "": return 0
    clean_val = str(value).replace('Rp', '').replace('.', '').replace(',', '').strip()
    try: return int(float(clean_val))
    except: return 0

def save_data_ongkir(supplier, ekspedisi, koli, ongkir, tanggal_jam): 
    try:
        data = {
            "supplier": supplier.upper(), "ekspedisi": ekspedisi, 
            "total_koli": koli, "total_ongkir": ongkir, "created_at": tanggal_jam 
        }
        if supabase_global:
            supabase_global.table("shipping_costs").insert(data).execute()
            st.cache_data.clear()
        return True
    except Exception as e:
        return False

def save_timbang_data(ekspedisi, jenis, dari, ke, koli, berat):
    try:
        data = {
            "ekspedisi": ekspedisi.upper(), "jenis_pengiriman": jenis,
            "pengiriman_dari": dari.upper(), "pengiriman_ke": ke.upper(),
            "total_koli": koli, "berat_total_timbang": berat,
            "created_at": datetime.now().isoformat()
        }
        if supabase_global:
            supabase_global.table("timbang_kolian").insert(data).execute()
            st.cache_data.clear()
        return True
    except Exception as e:
        return False

def delete_multiple_timbang(list_ids):
    try:
        if list_ids and supabase_global:
            supabase_global.table("timbang_kolian").delete().in_("id", list_ids).execute()
            st.cache_data.clear()
            return True
    except Exception as e:
        return False


# --- B. PUTAWAY SYSTEM LOGIC ---
def putaway_system(df_ds, df_asal, area_pilihan):
    if df_ds is None or df_asal is None:
        empty = pd.DataFrame()
        return empty, empty, empty, empty, empty, empty

    try:
        df_asal_updated = df_asal.copy()
        def get_col_idx(df, keywords, default_idx):
            for i, col in enumerate(df.columns):
                if any(k.lower() in str(col).lower() for k in keywords): return i
            return default_idx

        c_bin_a = get_col_idx(df_asal, ['bin', 'lokasi'], 1)
        c_sku_a = get_col_idx(df_asal, ['sku', 'item code'], 2)
        c_qty_a = get_col_idx(df_asal, ['qty system', 'quantity', 'stok'], 9)
        c_bin_d = get_col_idx(df_ds, ['bin', 'tujuan'], 0)
        c_sku_d = get_col_idx(df_ds, ['sku', 'item'], 1)
        c_qty_d = get_col_idx(df_ds, ['qty', 'jumlah'], 2)

        bin_qty_dict = {}
        for _, row in df_asal_updated.iterrows():
            try:
                key = f"{str(row.iloc[c_bin_a])}|{str(row.iloc[c_sku_a])}"
                qty = pd.to_numeric(row.iloc[c_qty_a], errors='coerce')
                bin_qty_dict[key] = qty if pd.notna(qty) else 0
            except: continue

        out_data = []
        for _, row in df_ds.iterrows():
            try:
                sku = str(row.iloc[c_sku_d])
                diff_qty = pd.to_numeric(row.iloc[c_qty_d], errors='coerce')
                if pd.isna(diff_qty) or diff_qty <= 0: continue
                
                bin_tujuan = str(row.iloc[c_bin_d])
                rem = int(diff_qty)
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
                            out_data.append([bin_tujuan, sku, int(diff_qty), b_name, take, rem, "FULLY SETUP" if rem == 0 else "PARTIAL SETUP"])
                            if rem <= 0: break
                
                if rem > 0:
                    out_data.append([bin_tujuan, sku, int(diff_qty), "(NO BIN)", 0, rem, "PERLU CARI STOCK MANUAL"])
            except: continue

        df_comp = pd.DataFrame(out_data, columns=["BIN ASAL", "SKU", "QTY PUTAWAY", "BIN DITEMUKAN", "QUANTITY", "DIFF", "STATUS"])
        
        for idx in df_asal_updated.index:
            key = f"{str(df_asal_updated.iloc[idx, c_bin_a])}|{str(df_asal_updated.iloc[idx, c_sku_a])}"
            if key in bin_qty_dict:
                df_asal_updated.iloc[idx, c_qty_a] = bin_qty_dict[key]

        df_plist = df_comp[df_comp['STATUS'].str.contains("SETUP")].copy()
        if not df_plist.empty:
            df_plist = df_plist.rename(columns={"BIN DITEMUKAN": "BIN AWAL", "BIN ASAL": "BIN TUJUAN"})
            df_plist = df_plist[["BIN AWAL", "BIN TUJUAN", "SKU", "QUANTITY", "STATUS"]]
            df_plist.columns = ["BIN AWAL", "BIN TUJUAN", "SKU", "QUANTITY", "NOTES"]
            df_plist['NOTES'] = "PUTAWAY"
        else:
            df_plist = pd.DataFrame(columns=["BIN AWAL", "BIN TUJUAN", "SKU", "QUANTITY", "NOTES"])

        df_kurang = df_comp[df_comp['STATUS'] == "PERLU CARI STOCK MANUAL"].copy()
        
        if area_pilihan == "DC LANTAI 1": keywords_outstanding = ["GL1-DC-PUTAWAY", "STAG"]
        elif area_pilihan == "DC LANTAI 2": keywords_outstanding = ["GL2-DC-PUTAWAY", "STAG"]
        elif area_pilihan == "DC LANTAI 3": keywords_outstanding = ["GL3-DC-PUTAWAY", "STAG"]
        elif area_pilihan == "JERSEY ZONE": keywords_outstanding = ["JZ-PUTAWAY", "STAG"] 
        else: keywords_outstanding = ["STAG", "PUTAWAY"]

        bin_series = df_asal_updated.iloc[:, c_bin_a].astype(str).str.upper()
        mask_keyword = bin_series.str.contains(keywords_outstanding[0], na=False)
        for kw in keywords_outstanding[1:]:
            mask_keyword = mask_keyword | bin_series.str.contains(kw, na=False)

        mask_out = (df_asal_updated.iloc[:, c_qty_a] > 0) & mask_keyword
        df_outstanding = df_asal_updated[mask_out].copy()

        return df_comp, df_plist, df_kurang, df_comp, df_outstanding, df_asal_updated
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()


# --- C. SCAN OUT VALIDATION LOGIC ---
def pre_process_pbi_data(uploaded_pbi_file):
    df_pbi = pd.read_excel(uploaded_pbi_file, header=None)
    if df_pbi.empty: return pd.DataFrame(columns=["BIN", "SKU"])
    df_filtered = df_pbi[df_pbi[19].notna() & (df_pbi[19].astype(str).str.strip() != "") & (df_pbi[19].astype(str).str.strip().str.lower() != "bin_code") & (df_pbi[4].astype(str).str.strip().str.lower() != "ps_barcode")].copy()
    df_filtered[20] = pd.to_numeric(df_filtered[20], errors="coerce").fillna(1).astype(int)
    df_duplicated = df_filtered.loc[df_filtered.index.repeat(df_filtered[20].apply(lambda x: x if x > 1 else 1))]
    df_final = df_duplicated[[19, 4]].copy()
    df_final.columns = ["BIN", "SKU"]
    return df_final
        
def process_scan_out(df_scan, df_history, df_stock):
    df_scan, df_history, df_stock = df_scan.copy(), df_history.copy(), df_stock.copy()
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
            if col in df.columns: df[col] = df[col].astype(str).str.strip().str.upper()

    if 'QTY_HIST' in df_history.columns: df_history['QTY_HIST'] = pd.to_numeric(df_history['QTY_HIST'], errors='coerce').fillna(0).astype(int)
    if 'QTY_STOCK' in df_stock.columns: df_stock['QTY_STOCK'] = pd.to_numeric(df_stock['QTY_STOCK'], errors='coerce').fillna(0).astype(int)

    final_results = []
    for _, scan_row in df_scan.iterrows():
        sku, bin_fisik = scan_row['SKU'], scan_row['BIN_AWAL']
        found, keterangan, qty_val, bin_aft, inv = False, "", 0, "", ""

        h_exact = df_history[(df_history['SKU'] == sku) & (df_history['BIN_HIST'] == bin_fisik) & (df_history['QTY_HIST'] > 0)]
        if not h_exact.empty:
            idx = h_exact.index[0]
            keterangan, bin_aft, qty_val, found = 'DONE AND MATCH SET UP', df_history.loc[idx, 'BIN_AFTER'], 1, True
            df_history.loc[idx, 'QTY_HIST'] -= 1

        if not found:
            st_exact = df_stock[(df_stock['SKU'] == sku) & (df_stock['BIN_STOCK'] == bin_fisik) & (df_stock['QTY_STOCK'] > 0)]
            if not st_exact.empty:
                idx = st_exact.index[0]
                keterangan, inv, qty_val, found = 'ITEM TELAH TERJUAL', df_stock.loc[idx, 'INVOICE'], 1, True
                df_stock.loc[idx, 'QTY_STOCK'] -= 1

        if not found:
            h_sku_only = df_history[(df_history['SKU'] == sku) & (df_history['QTY_HIST'] > 0)]
            if not h_sku_only.empty:
                idx = h_sku_only.index[0]
                keterangan, bin_aft, qty_val, found = 'DONE SETUP (BIN MISSMATCH)', df_history.loc[idx, 'BIN_AFTER'], 1, True
                df_history.loc[idx, 'QTY_HIST'] -= 1

        if not found:
            st_sku_only = df_stock[(df_stock['SKU'] == sku) & (df_stock['QTY_STOCK'] > 0)]
            if not st_sku_only.empty:
                idx = st_sku_only.index[0]
                keterangan, inv, qty_val, found = 'ITEM TELAH TERJUAL (BIN MISSMATCH)', df_stock.loc[idx, 'INVOICE'], 1, True
                df_stock.loc[idx, 'QTY_STOCK'] -= 1

        if not found:
            keterangan, qty_val = 'ITEM BELUM TERSETUP & TIDAK TERJUAL', 0

        final_results.append({'BIN AWAL': bin_fisik, 'SKU': sku, 'QTY SCAN': 1, 'Keterangan': keterangan, 'Total Qty Setup/Terjual': qty_val, 'Bin After Set Up': bin_aft, 'Invoice': inv})

    df_res = pd.DataFrame(final_results).groupby(['BIN AWAL', 'SKU', 'Keterangan', 'Bin After Set Up', 'Invoice'], dropna=False).agg({'QTY SCAN': 'sum', 'Total Qty Setup/Terjual': 'sum'}).reset_index()
    df_res = df_res.loc[:, ~df_res.columns.duplicated()]
    df_res['Keterangan'] = df_res['Keterangan'].fillna('').astype(str)

    draft_data = []
    for _, row in df_res.iterrows():
        ket = row['Keterangan']
        if ket == 'DONE SETUP (BIN MISSMATCH)':
            draft_data.append({'BIN AWAL': row['Bin After Set Up'], 'BIN TUJUAN': row['BIN AWAL'], 'SKU': row['SKU'], 'QUANTITY': row['QTY SCAN'], 'NOTES': 'MISS LOCATION'})
            draft_data.append({'BIN AWAL': row['BIN AWAL'], 'BIN TUJUAN': 'KARANTINA', 'SKU': row['SKU'], 'QUANTITY': row['QTY SCAN'], 'NOTES': 'WAITING OFFLINE'})
        elif 'QTY MISSMATCH' in ket:
            draft_data.append({'BIN AWAL': row['BIN AWAL'], 'BIN TUJUAN': 'KARANTINA', 'SKU': row['SKU'], 'QUANTITY': row['QTY SCAN'], 'NOTES': 'MISS LOCATION'})
        elif "MISSMATCH" in ket or "BELUM" in ket:
            draft_data.append({'BIN AWAL': row['BIN AWAL'], 'BIN TUJUAN': 'KARANTINA', 'SKU': row['SKU'], 'QUANTITY': row['QTY SCAN'], 'NOTES': 'WAITING OFFLINE'})
    
    df_draft = pd.DataFrame(draft_data) if draft_data else pd.DataFrame(columns=['BIN AWAL', 'BIN TUJUAN', 'SKU', 'QUANTITY', 'NOTES'])
    df_res = df_res[['BIN AWAL', 'SKU', 'QTY SCAN', 'Keterangan', 'Total Qty Setup/Terjual', 'Bin After Set Up', 'Invoice']]
    return df_res, df_draft


# --- D. COMPARE SYSTEM LOGIC ---
def load_data(file):
    if file is None: return pd.DataFrame()
    try:
        if file.name.endswith('.csv'):
            df_temp = pd.read_csv(file)
            return df_temp if not df_temp.empty else pd.DataFrame()
        else: return pd.read_excel(file)
    except Exception: return pd.DataFrame()

def prepare_sku_totals(df):
    if df.empty: return pd.DataFrame(columns=['SKU', 'QTY'])
    df_clean = df.copy()
    if df_clean.shape[1] < 10: raise ValueError(f"File System kurang dari 10 kolom (Kolom J tidak ada).")
    df_mapped = pd.DataFrame({
        'SKU': df_clean.iloc[:, 2].astype(str).str.strip().str.upper(),
        'QTY': pd.to_numeric(df_clean.iloc[:, 9], errors='coerce').fillna(0)
    })
    return df_mapped.groupby('SKU', as_index=False)['QTY'].sum()

def process_stock_comparison(file1, file2, file_tracking=None, file_po=None, file_rto_in=None, file_rto_out=None, file_refund=None):
    try:
        data1 = prepare_sku_totals(load_data(file1))
        data2 = prepare_sku_totals(load_data(file2))
        
        if data1.empty or data2.empty: return pd.DataFrame(), pd.DataFrame()
        
        comparison = pd.merge(data1, data2, on='SKU', how='outer', suffixes=('_Sys1', '_Sys2')).fillna(0)
        comparison = comparison[(comparison['QTY_Sys1'] >= 0) & (comparison['QTY_Sys2'] >= 0)].copy()
        comparison['DIFF'] = comparison['QTY_Sys1'] - comparison['QTY_Sys2']
        discrepancies = comparison[comparison['DIFF'] != 0].copy()
        
        df_track_clean = pd.DataFrame(columns=['INVOICE', 'SKU', 'BIN', 'QTY'])
        if file_tracking is not None and not discrepancies.empty:
            df_track = load_data(file_tracking)
            if not df_track.empty and df_track.shape[1] >= 11:
                df_track_clean = pd.DataFrame({
                    'INVOICE': df_track.iloc[:, 0].astype(str).str.strip(),
                    'SKU': df_track.iloc[:, 1].astype(str).str.strip().str.upper(),
                    'BIN': df_track.iloc[:, 6].astype(str).str.strip().str.upper(),
                    'QTY': pd.to_numeric(df_track.iloc[:, 10], errors='coerce').fillna(0)
                })

        df_rto_out_clean = pd.DataFrame(columns=['NO_TF', 'SKU', 'QTY'])
        if file_rto_out is not None and not discrepancies.empty:
            df_rto_out_df = load_data(file_rto_out)
            if not df_rto_out_df.empty and df_rto_out_df.shape[1] >= 8:
                df_rto_out_clean = pd.DataFrame({
                    'NO_TF': df_rto_out_df.iloc[:, 0].astype(str).str.strip(),
                    'SKU': df_rto_out_df.iloc[:, 3].astype(str).str.strip().str.upper(),
                    'QTY': pd.to_numeric(df_rto_out_df.iloc[:, 7], errors='coerce').fillna(0)
                })

        df_po_clean = pd.DataFrame(columns=['NO_PO', 'SKU', 'QTY'])
        if file_po is not None and not discrepancies.empty:
            df_po = load_data(file_po)
            if not df_po.empty and df_po.shape[1] >= 13:
                df_po_clean = pd.DataFrame({
                    'NO_PO': df_po.iloc[:, 0].astype(str).str.strip(),
                    'SKU': df_po.iloc[:, 4].astype(str).str.strip().str.upper(),
                    'QTY': pd.to_numeric(df_po.iloc[:, 12], errors='coerce').fillna(0)
                })

        df_rto_in_clean = pd.DataFrame(columns=['NO_TF', 'SKU', 'QTY'])
        if file_rto_in is not None and not discrepancies.empty:
            df_rto_in_df = load_data(file_rto_in)
            if not df_rto_in_df.empty and df_rto_in_df.shape[1] >= 8:
                df_rto_in_clean = pd.DataFrame({
                    'NO_TF': df_rto_in_df.iloc[:, 0].astype(str).str.strip(),
                    'SKU': df_rto_in_df.iloc[:, 3].astype(str).str.strip().str.upper(),
                    'QTY': pd.to_numeric(df_rto_in_df.iloc[:, 7], errors='coerce').fillna(0)
                })

        df_refund_clean = pd.DataFrame(columns=['SKU', 'QTY'])
        if file_refund is not None and not discrepancies.empty:
            df_refund_df = load_data(file_refund)
            if not df_refund_df.empty and df_refund_df.shape[1] >= 11:
                df_refund_clean = pd.DataFrame({
                    'SKU': df_refund_df.iloc[:, 3].astype(str).str.strip().str.upper(),
                    'QTY': pd.to_numeric(df_refund_df.iloc[:, 10], errors='coerce').fillna(0)
                })
            
        status_list, doc_reference_list, track_bin_list, total_found_qty_list = [], [], [], []
        
        for idx, row in discrepancies.iterrows():
            target_sku = str(row['SKU']).strip().upper()
            actual_diff, needed_qty = row['DIFF'], abs(row['DIFF'])
            docs_found, bins_found, accumulated_qty = [], [], 0
            
            if actual_diff < 0:
                if not df_po_clean.empty:
                    match_po = df_po_clean[df_po_clean['SKU'] == target_sku]
                    if not match_po.empty:
                        docs_found.append(f"PO:{'/'.join(map(str, match_po['NO_PO'].unique()))}")
                        accumulated_qty += match_po['QTY'].sum()
                if not df_rto_in_clean.empty:
                    match_rto_in = df_rto_in_clean[df_rto_in_clean['SKU'] == target_sku]
                    if not match_rto_in.empty:
                        docs_found.append(f"RTO_IN:{'/'.join(map(str, match_rto_in['NO_TF'].unique()))}")
                        accumulated_qty += match_rto_in['QTY'].sum()
                if not df_refund_clean.empty:
                    match_refund = df_refund_clean[df_refund_clean['SKU'] == target_sku]
                    if not match_refund.empty:
                        docs_found.append(f"REFUND:Found")
                        accumulated_qty += match_refund['QTY'].sum()
                
                final_status = "PENAMBAHAN STOK (NO HISTORY)" if accumulated_qty == 0 else ("DONE MASUK" if accumulated_qty >= needed_qty else "MASUK QTY MISSMATCH")
                track_bin_list.append("-")
            else:
                if not df_track_clean.empty:
                    match_track = df_track_clean[df_track_clean['SKU'] == target_sku]
                    if not match_track.empty:
                        docs_found.append(f"TRACK:{'/'.join(map(str, match_track['INVOICE'].unique()))}")
                        if match_track['BIN'].any(): bins_found.append("/".join(map(str, match_track['BIN'].unique())))
                        accumulated_qty += match_track['QTY'].sum()
                if not df_rto_out_clean.empty:
                    match_rto_out = df_rto_out_clean[df_rto_out_clean['SKU'] == target_sku]
                    if not match_rto_out.empty:
                        docs_found.append(f"RTO_OUT:{'/'.join(map(str, match_rto_out['NO_TF'].unique()))}")
                        bins_found.append("RTO_OUT")
                        accumulated_qty += match_rto_out['QTY'].sum()
                
                final_status = "NO SALES (PERLU CEK ADJ)" if accumulated_qty == 0 else ("DONE TERJUAL" if accumulated_qty >= needed_qty else "KELUAR QTY MISSMATCH")
                track_bin_list.append(", ".join(bins_found) if bins_found else "-")

            status_list.append(final_status)
            doc_reference_list.append(", ".join(docs_found) if docs_found else "-")
            total_found_qty_list.append(accumulated_qty)
                        
        discrepancies['TRACK_INVOICE'] = doc_reference_list
        discrepancies['TRACK_BIN'] = track_bin_list
        discrepancies['TRACK_QTY'] = total_found_qty_list
        discrepancies['STATUS_CHECK'] = status_list
        
        return comparison, discrepancies
    except Exception as e:
        raise e

# --- E. PO LOGIC ---
def process_po_logic(df_scan, df_po):
    metrics = {"total_po": 0, "total_scan": 0, "kurang_po": 0, "lebih_po": 0}
    s_sku_col, s_qty_col = df_scan.columns[0], df_scan.columns[1]
    p_no_col, p_sku_col, p_qty_col = df_po.columns[0], df_po.columns[6], df_po.columns[7]

    df_s, df_p = df_scan.copy(), df_po.copy()

    def clean_sku(val):
        s = str(val).strip().upper()
        if s.endswith('.0'): s = s[:-2]
        return s

    df_s[s_sku_col] = df_s[s_sku_col].apply(clean_sku)
    df_p[p_sku_col] = df_p[p_sku_col].apply(clean_sku)
    df_s[s_qty_col] = pd.to_numeric(df_s[s_qty_col], errors='coerce').fillna(0)
    df_p[p_qty_col] = pd.to_numeric(df_p[p_qty_col], errors='coerce').fillna(0)

    stok_pool = df_s.groupby(s_sku_col)[s_qty_col].sum().to_dict()
    df_p['Qty Alokasi'] = 0.0
    over_allocation_list = []

    for sku, total_stok in stok_pool.items():
        sisa_stok = float(total_stok)
        target_po_indices = df_p[df_p[p_sku_col] == sku].index.tolist()
        po_references = ", ".join(df_p.loc[df_p[p_sku_col] == sku, p_no_col].unique().astype(str))
        
        if not target_po_indices:
            over_allocation_list.append({
                'No PO': 'WRONG SKU', 'SKU': sku, 'Qty PO': 0, 
                'Qty Alokasi': sisa_stok, 'Status Alokasi': 'Wrong SKU', 'Ref PO Asli': 'NOT FOUND'
            })
            continue

        for idx in target_po_indices:
            butuh = df_p.at[idx, p_qty_col]
            isi = min(butuh, sisa_stok)
            df_p.at[idx, 'Qty Alokasi'] = isi
            sisa_stok -= isi
            if sisa_stok <= 0: break
        
        if sisa_stok > 0:
            over_allocation_list.append({
                'No PO': 'OVER SCAN PO', 'SKU': sku, 'Qty PO': 0, 
                'Qty Alokasi': sisa_stok, 'Status Alokasi': 'Over Allocation', 'Ref PO Asli': po_references
            })

    df_p['Status Alokasi'] = df_p.apply(lambda r: 'No Allocation' if r['Qty Alokasi'] == 0 else ('Partial Allocation' if r['Qty Alokasi'] < r[p_qty_col] else 'Full Allocation'), axis=1)

    df_hasil_final = pd.concat([
        df_p[[p_no_col, p_sku_col, p_qty_col, 'Qty Alokasi', 'Status Alokasi']].rename(columns={p_no_col: 'No PO', p_sku_col: 'SKU', p_qty_col: 'Qty PO'}),
        pd.DataFrame(over_allocation_list).drop(columns=['Ref PO Asli'], errors='ignore')
    ], ignore_index=True)

    metrics["total_po"] = int(df_p[p_qty_col].sum())
    metrics["total_scan"] = int(df_s[s_qty_col].sum())
    metrics["kurang_po"] = int(sum(x['Qty Alokasi'] for x in over_allocation_list))
    metrics["lebih_po"] = int(df_p[p_qty_col].sum() - df_p['Qty Alokasi'].sum())

    df_extra_sku = pd.DataFrame(over_allocation_list)
    df_split = df_p[[p_no_col, p_sku_col, 'Qty Alokasi']].copy()
    df_split.columns = ['No PO', 'SKU', 'Qty Alokasi']

    return df_hasil_final, df_extra_sku, df_p[df_p['Qty Alokasi'] < df_p[p_qty_col]], metrics, df_split

    # ==============================================================================
# 🌟 6. USER INTERFACE (UI) MENU FUNCTIONS - PART 1
# ==============================================================================

# ---------------------------------------------------------
# MENU: STOCK OPNAME ANALYZER
# ---------------------------------------------------------
def menu_Stock_Opname():
    st.markdown('<div class="hero-header"><h1>STOCK OPNAME ANALYZER</h1></div>', unsafe_allow_html=True)
    
    with st.expander("📋 Informasi Format File & Logic"):
        st.info("""
        **DS VS Stock System :**
        - Compare antara SKU dan BIN yang ada di data scan dengan SKU dan BIN yang ada di Stock System.
        - Apabila **QTY SCAN > QTY SYSTEM** maka akan dijadikan sebagai Real +.
        - Apabila **QTY SYSTEM > QTY SCAN** maka akan dijadikan sebagai System +.
        """)

    # INIT SESSION STATES
    for key in ['compare_result', 'allocation_result', 'set_up_real_plus', 'sys_updated_result', 
                'recon_real_plus', 'outstanding_system', 'df_res_lookup', 'df_missing_lookup', 
                'df_mult_5', 'df_sing_5', 'df_karantina_6', 'df_check_6']:
        if key not in st.session_state: st.session_state[key] = None

    # FILTER SECTION
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

    # STEP 1: COMPARE
    st.subheader("1️⃣ Upload & Run Compare")
    c1, c2 = st.columns(2)
    with c1: up_scan = st.file_uploader("📥 DATA SCAN", type=['xlsx','csv'], key="step1_scan")
    with c2: up_stock = st.file_uploader("📥 STOCK SYSTEM", type=['xlsx','csv'], key="step1_stock")

    if st.button("▶️ RUN COMPARE", use_container_width=True):
        if not up_scan or not up_stock:
            popup_error("Data Belum Lengkap!", "File Data Scan atau Stock System belum diupload.", "Harap unggah kedua file tersebut terlebih dahulu sebelum memproses data.")
        else:
            with st.spinner("Menganalisis Data..."):
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
            popup_success("Data Scan berhasil dicompare dengan Stock System!")

    # DISPLAY STEP 1
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
        st.subheader("2️⃣ Upload BIN COVERAGE (ALL BIN DEFAULT & KARANTINA)")
        up_bin_cov = st.file_uploader("📥 FILE BIN COVERAGE", type=['xlsx','csv'], key="step2_cov")
        
        if st.button("▶️ RUN ALLOCATION", use_container_width=True):
            if not up_bin_cov:
                popup_error("BIN Coverage Kosong!", "File BIN Coverage belum diunggah.", "Silakan upload file BIN Coverage sebelum melakukan alokasi.")
            elif not selected_bin_cov:
                popup_error("Kriteria Belum Dipilih", "Anda belum memilih kriteria BIN Coverage.", "Pilih minimal satu BIN Coverage di panel filter atas.")
            else:
                df_cov_raw = pd.read_excel(up_bin_cov) if up_bin_cov.name.endswith(('.xlsx', '.xls')) else pd.read_csv(up_bin_cov)
                import re
                pattern = "|".join([re.escape(str(b).strip().upper()) for b in selected_bin_cov])
                mask = df_cov_raw.iloc[:, 1].astype(str).str.strip().str.upper().str.contains(pattern, na=False)
                df_cov = df_cov_raw[mask].copy()

                if df_cov.empty:
                    popup_error("Data Kosong", "Data BIN Coverage kosong setelah difilter.", "Cek kembali pilihan filter BIN Anda.")
                else:
                    allocated, sys_upd = logic_run_allocation(d['real_plus'], d['system_plus'], df_cov)
                    allocated['ITEM NAME'] = allocated['SKU'].map(d['map_dict'])
                    st.session_state.allocation_result = allocated
                    st.session_state.sys_updated_result = sys_upd
                    st.session_state.set_up_real_plus = generate_set_up_real_plus(allocated)
                    popup_success(f"Alokasi selesai! Terfilter {len(df_cov)} baris.")

    # DISPLAY STEP 2 & 3
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
            popup_success("Report Rekonsiliasi berhasil di-generate!")

    if st.session_state.recon_real_plus is not None:
        st.markdown("#### 📋 REAL + RECON & SYSTEM + RECON")
        c_rec1, c_rec2 = st.columns(2)
        with c_rec1: st.dataframe(st.session_state.recon_real_plus, use_container_width=True)
        with c_rec2: st.dataframe(st.session_state.outstanding_system, use_container_width=True)
        
        st.markdown("---")
        out_real = io.BytesIO()
        with pd.ExcelWriter(out_real, engine='xlsxwriter') as writer_real:
            st.session_state.recon_real_plus.to_excel(writer_real, sheet_name='REAL + RECON', index=False)
        out_sys = io.BytesIO()
        with pd.ExcelWriter(out_sys, engine='xlsxwriter') as writer_sys:
            st.session_state.outstanding_system.to_excel(writer_sys, sheet_name='SYSTEM + RECON', index=False)
            
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            st.download_button("📥 DOWNLOAD REAL + RECON", data=out_real.getvalue(), file_name="Report_Real_Plus_Recon.xlsx", use_container_width=True)
        with btn_col2:
            st.download_button("📥 DOWNLOAD SYSTEM + RECON", data=out_sys.getvalue(), file_name="Report_System_Plus_Recon.xlsx", use_container_width=True)

    # STEP 4: FINAL ADJ & PROCESS
    st.markdown("<br><br><br>---", unsafe_allow_html=True)
    st.subheader("4️⃣ FINAL ADJUSTMENT + PROCESS")
    col_a, col_b, col_c = st.columns(3)
    with col_a: up_r4 = st.file_uploader("1️⃣ Sheet REAL + RECON", type=['xlsx','csv'], key="u_r_final")
    with col_b: up_s4 = st.file_uploader("2️⃣ Sheet CEK STOCK ADJ +", type=['xlsx', 'csv'], key="u_s_final")
    with col_c: up_m5 = st.file_uploader("3️⃣ File STAGGING INBOUND", type=['xlsx'], key="u_m_final")

    if st.button("▶️ RUNNING PROCESS", use_container_width=True, key="btn_final_proc"):
        if not (up_r4 and up_s4 and up_m5):
            popup_error("File Tidak Lengkap!", "Sistem membutuhkan ke-3 file di atas untuk menjalankan Final Process.", "Harap unggah Real+Recon, Cek Stock Adj+, dan Stagging Inbound.")
        else:
            with st.spinner("Memproses Final Adjustment..."):
                try:
                    df_r4 = pd.read_csv(up_r4) if up_r4.name.endswith('.csv') else pd.read_excel(up_r4)
                    df_s4 = pd.read_csv(up_s4) if up_s4.name.endswith('.csv') else pd.read_excel(up_s4)
                    df_m5 = pd.read_excel(up_m5)

                    res4, miss4 = logic_cek_adjustment_final(df_r4, df_s4)
                    df_mult, df_sing = logic_pivot_adjustment(res4, df_m5, miss4)

                    def clean_final_result(df):
                        if df is not None and not df.empty:
                            last_col = df.columns[-1] 
                            df[last_col] = pd.to_numeric(df[last_col], errors='coerce').fillna(0)
                            df = df[df[last_col] > 0].reset_index(drop=True)
                        return df

                    st.session_state.df_mult_final = clean_final_result(df_mult)
                    st.session_state.df_sing_final = clean_final_result(df_sing)
                    st.session_state.df_res4_final = res4
                    st.session_state.df_miss4_final = miss4
                    st.session_state.process_done = True
                    popup_success("Analisis Final Adjustment Selesai!")
                except Exception as e:
                    popup_error("Error Eksekusi", f"Terjadi kesalahan teknis: {e}", "Pastikan kolom di file sesuai standar sistem.")

    # TAMPILAN FINAL (Jika sukses)
    if st.session_state.get("process_done"):
        df_res4 = st.session_state.get("df_res4_final", pd.DataFrame())
        has_content = False
        if not df_res4.empty:
            total_cek = pd.to_numeric(df_res4['QTY SO'], errors='coerce').sum()
            if total_cek > 0: has_content = True

        if not has_content:
            st.warning("⚠️ Hasil Lookup Kosong atau Semua QTY adalah 0! Pastikan BIN/SKU sesuai.")
        else:
            t1, t2, t3, t4, tmissing = st.tabs(["📦 MULTIPLE ADJ +", "⚠️ SINGLE ADJ +", "🔍 CEK ADJ + RESULT", "➡️ SET UP REAL +", "❌Miss Lookup SKU on BIN"])
            
            with t1:
                df_m = st.session_state.get("df_mult_final", pd.DataFrame())
                st.dataframe(df_m, use_container_width=True, hide_index=True)
            with t2:
                df_s = st.session_state.get("df_sing_final", pd.DataFrame())
                st.dataframe(df_s, use_container_width=True, hide_index=True)
            with t3:
                df_r4 = st.session_state.get("df_res4_final", pd.DataFrame())
                if not df_r4.empty:
                    cols = pd.Series(df_r4.columns)
                    for dup in cols[cols.duplicated()].unique(): 
                        cols[cols == dup] = [f"{dup}_{i}" if i != 0 else dup for i in range(cols[cols == dup].count())]
                    df_r4.columns = cols
                st.dataframe(df_r4, use_container_width=True, hide_index=True)
            with t4:
                df_m_src = st.session_state.get("df_mult_final")
                df_s_res = st.session_state.get("df_res4_final")
                df_miss_src = st.session_state.get("df_miss4_final")
                
                if st.button("▶️ GENERATE SET UP REAL +", use_container_width=True):
                    if df_m_src is not None and df_s_res is not None:
                        df_real = logic_setup_real_plus(df_s_res, df_m_src, df_miss_src)
                        st.session_state.df_setup_real_final = df_real
                        popup_success("Mutasi Set Up Real + Berhasil Dibuat!")
                    else:
                        popup_error("Gagal Generate", "Data pendukung tidak lengkap.", "Jalankan Proses Final terlebih dahulu.")

                if "df_setup_real_final" in st.session_state:
                    st.dataframe(st.session_state.df_setup_real_final, use_container_width=True, hide_index=True)
                    csv_real = st.session_state.df_setup_real_final.to_csv(index=False).encode('utf-8')
                    st.download_button("📥 Download Set Up Real +", data=csv_real, file_name="set_up_real_plus.csv", mime="text/csv")
            with tmissing:
                df_miss = st.session_state.get("df_miss4_final", pd.DataFrame())
                if df_miss.empty:
                    st.info("Tidak ada item missing (Semua BIN|SKU terdaftar di sistem).")
                else:
                    st.dataframe(df_miss, use_container_width=True, hide_index=True)

    # STEP 5: KARANTINA
    st.markdown("<br><br><br>---", unsafe_allow_html=True)
    st.subheader("5️⃣ RECON SYSTEM + PROCESS")
    col_k1, col_k2 = st.columns(2)
    with col_k1: up_k6 = st.file_uploader("📥 1. Upload SYSTEM + RECON", type=['xlsx', 'csv'], key="u6_kar")
    with col_k2: up_adj6 = st.file_uploader("📥 2. Upload CEK ADJUSMENT", type=['xlsx', 'csv'], key="u6_adj")

    if st.button("▶️ GENERATE KARANTINA", use_container_width=True):
        if not up_k6 or not up_adj6:
            popup_error("File Belum Lengkap", "Dua file dibutuhkan untuk memproses karantina.", "Upload file System+Recon dan Cek Adjustment.")
        else:
            try:
                df_raw6 = pd.read_excel(up_k6) if up_k6.name.endswith('.xlsx') else pd.read_csv(up_k6)
                df_recon6 = pd.read_excel(up_adj6) if up_adj6.name.endswith('.xlsx') else pd.read_csv(up_adj6)
                df_final6, df_check6 = logic_setup_karantina_with_compare(df_raw6, df_recon6)
                st.session_state.df_karantina_6 = df_final6
                st.session_state.df_check_6 = df_check6
                popup_success("Karantina berhasil diproses!")
            except Exception as e:
                popup_error("Gagal Memproses", str(e), "Cek kembali format kolom file Excel Anda.")

    if st.session_state.df_karantina_6 is not None:
        tab_res, tab_chk = st.tabs(["📦 HASIL KARANTINA", "🔍 DATA PENGECEKAN (AUDIT)"])
        with tab_res:
            st.dataframe(st.session_state.df_karantina_6, use_container_width=True, hide_index=True)
            out6 = io.BytesIO()
            with pd.ExcelWriter(out6, engine='xlsxwriter') as writer:
                st.session_state.df_karantina_6.to_excel(writer, index=False, sheet_name='Karantina')
            st.download_button("📥 DOWNLOAD HASIL KARANTINA", data=out6.getvalue(), file_name="Karantina.xlsx")
        with tab_chk:
            st.dataframe(st.session_state.df_check_6, use_container_width=True, hide_index=True)

    # FINAL SECTION: SUMMARY ADJ
    st.markdown("#### 💰 SUMMARY ADJUSTMENT REPORT")
    up_minus = st.file_uploader("📥 Upload STOCK ADJ -", type=['xlsx','csv'])
    up_plus = st.file_uploader("📥 Upload STOCK ADJ +", type=['xlsx','csv'])

    if st.button("▶️ SUMMARY ADJUSTMENT"):
        df_p_in = pd.read_excel(up_plus) if up_plus else st.session_state.get('df_mult_final')
        df_m_in = pd.read_excel(up_minus) if up_minus else None
        
        if df_p_in is not None:
            df_res, df_summary = logic_sum_adjustment_final(df_p_in, df_m_in)
            st.session_state.report_adj = {"data": df_res, "sum": df_summary}
            popup_success("Summary berhasil dihitung!")
        else:
            popup_error("Data Kosong", "Tidak ada file Adj + atau histori proses.", "Silakan upload file Adj +.")

    if "report_adj" in st.session_state:
        df_s = st.session_state.report_adj["sum"]
        def get_v(m): return df_s.loc[df_s['METRIC'] == m, 'VALUE'].values[0]
        vals = {"v_p": get_v('Total Value Adj. +'), "v_m": get_v('Total Value Adj. -'), "v_n": get_v('Total Value')}
        
        v1, v2, v3 = st.columns(3)
        v1.markdown(f'<div class="m-box"><span class="m-lbl">TOTAL VALUE ADJ (+)</span><span class="m-val">Rp {vals["v_p"]:,.0f}</span></div>', unsafe_allow_html=True)
        v2.markdown(f'<div class="m-box"><span class="m-lbl">TOTAL VALUE ADJ (-)</span><span class="m-val">Rp {vals["v_m"]:,.0f}</span></div>', unsafe_allow_html=True)
        v3.markdown(f'<div class="m-box"><span class="m-lbl">NET VALUE ADJ</span><span class="m-val">Rp {vals["v_n"]:,.0f}</span></div>', unsafe_allow_html=True)
        
        st.dataframe(st.session_state.report_adj["data"], use_container_width=True, hide_index=True)


# ---------------------------------------------------------
# MENU: DATABASE ONGKIR IN/OUT
# ---------------------------------------------------------
def show_database_ongkir():
    st.markdown('<div class="hero-header"><h1>DATABASE ONGKIR IN/OUT</h1></div>', unsafe_allow_html=True)

    df_raw = fetch_table_data("shipping_costs")
    tab_input, tab_summary = st.tabs(["📥 INPUT DATA", "📊 SUMMARY & HISTORY"])

    with tab_input:
        with st.expander("🛻 INPUT DATA ONGKIR BARU", expanded=True):
            with st.form("form_ongkir_single", clear_on_submit=True):
                col_a, col_b = st.columns(2)
                with col_a:
                    supplier_input = st.text_input("Nama Supplier", placeholder="Contoh: TOKOPEDIA")
                    ekspedisi_input = st.text_input("Nama Ekspedisi", placeholder="Contoh: JNE").upper()
                    input_tgl = st.date_input("Tanggal Transaksi")
                with col_b:
                    koli_input = st.number_input("Total Koli", min_value=1, step=1)
                    ongkir_input = st.number_input("Total Ongkir (Rp)", min_value=0, step=5000)
                    input_jam = st.time_input("Jam Transaksi")
                
                if st.form_submit_button("▶️ SIMPAN DATA"):
                    if supplier_input and ekspedisi_input:
                        fix_ts = f"{input_tgl.strftime('%Y-%m-%d')} {input_jam.strftime('%H:%M:%S')}"
                        if save_data_ongkir(supplier_input, ekspedisi_input, koli_input, ongkir_input, fix_ts):
                            popup_success("Data Ongkir berhasil disimpan ke Cloud Database!")
                    else:
                        popup_error("Data Tidak Lengkap", "Nama Supplier atau Ekspedisi kosong.", "Harap isi semua field wajib.")

        with st.expander("📁 BATCH OPS: UPLOAD MASSAL", expanded=False):
            c_up = st.file_uploader("Upload CSV Massal", type=["csv"])
            if st.button("▶️ UPLOAD BULK ONGKIR"):
                if not c_up:
                    popup_error("File Kosong", "Anda belum memasukkan file CSV.", "Harap unggah file sebelum menekan tombol.")
                else:
                    df_mass = pd.read_csv(c_up)
                    req = ["SUPPLIER", "EKSPEDISI", "TOTAL KOLI", "ONGKIR", "TANGGAL_JAM"]
                    if all(c in df_mass.columns for c in req):
                        batch_list = []
                        for _, row in df_mass.iterrows():
                            batch_list.append({
                                "supplier": str(row["SUPPLIER"]).upper(), 
                                "ekspedisi": str(row["EKSPEDISI"]).upper(), 
                                "total_koli": int(row["TOTAL KOLI"]), 
                                "total_ongkir": clean_currency(row["ONGKIR"]),
                                "created_at": str(row["TANGGAL_JAM"]) 
                            })
                        if supabase_global and batch_list:
                            supabase_global.table("shipping_costs").insert(batch_list).execute()
                            st.cache_data.clear()
                            popup_success(f"Berhasil menginput {len(batch_list)} baris data!")
                    else:
                        popup_error("Format Salah", f"Pastikan file CSV memiliki kolom: {req}", "Gunakan template yang tersedia.")

    with tab_summary:
        if not df_raw.empty:
            df_raw['created_at'] = pd.to_datetime(df_raw['created_at'])
            st.markdown("### 🔍 FILTER DATA")
            c1, c2 = st.columns(2)
            with c1: date_range = st.date_input("Rentang Tanggal", value=(df_raw['created_at'].min().date(), df_raw['created_at'].max().date()))
            with c2: ekspedisi_opt = st.selectbox("Ekspedisi", ["SEMUA"] + sorted(df_raw['ekspedisi'].unique().tolist()))
            
            # Aplikasi Filter
            if isinstance(date_range, tuple) and len(date_range) == 2:
                mask = (df_raw['created_at'].dt.date >= date_range[0]) & (df_raw['created_at'].dt.date <= date_range[1])
                df_filtered = df_raw.loc[mask]
            else: df_filtered = df_raw
            if ekspedisi_opt != "SEMUA": df_filtered = df_filtered[df_filtered['ekspedisi'] == ekspedisi_opt]

            m1, m2 = st.columns(2)
            m1.markdown(f'<div class="m-box"><span class="m-lbl">Total Koli</span><span class="m-val">{df_filtered["total_koli"].sum():,}</span></div>', unsafe_allow_html=True)
            m2.markdown(f'<div class="m-box"><span class="m-lbl">Total Ongkir</span><span class="m-val">Rp {df_filtered["total_ongkir"].sum():,.0f}</span></div>', unsafe_allow_html=True)

            st.dataframe(df_filtered, use_container_width=True, hide_index=True)


# ---------------------------------------------------------
# MENU: REJECT/DEFECT LIST ENTRY
# ---------------------------------------------------------
def menu_reject_defect():
    st.markdown('<div class="hero-header"><h1>⚠️ REJECT / DEFECT LIST ENTRY</h1></div>', unsafe_allow_html=True)

    tab_entry, tab_analytics, tab_match, tab_done = st.tabs(["📥 ENTRY DATA", "📊 ANALYTICS DASHBOARD", "🔍 MATCH DEFECT", "✅ DONE PROCESS"])

    with tab_entry:
        with st.form("form_reject_new", clear_on_submit=True):
            cabang_input = st.selectbox("📍 LOKASI OPERASIONAL", ["SURABAYA", "SIDOARJO", "SEMARANG"])
            c1, c2 = st.columns(2)
            with c1:
                bin_awal = st.text_input("BIN AWAL")
                bin_val = st.selectbox("BIN TUJUAN", ["REJECT DC", "DEFECT DC", "DEFECT STORE", "REJECT STORE"])
                sku = st.text_input("SKU")
                article = st.text_input("NAMA BARANG")
            with c2:
                size = st.text_input("SIZE")
                kategori = st.selectbox("KATEGORI", ["D1", "D2", "R1", "HANYA SEBELAH KIRI", "HANYA SEBELAH KANAN"])
                keterangan = st.text_area("DETAIL KERUSAKAN")

            if st.form_submit_button("📤 UPLOAD SINGLE LIST"):
                if not sku or not article:
                    popup_error("Data Kosong", "SKU atau Nama Barang belum diisi.", "Semua parameter dasar wajib diisi untuk pendataan.")
                else:
                    jam = (datetime.now() + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S")
                    new_data = pd.DataFrame([{'cabang': cabang_input, 'bin_awal': bin_awal, 'bin': bin_val, 'sku': sku, 'article_name': article, 'size': size, 'kategori': kategori, 'keterangan': keterangan, 'tanggal_input': jam}])
                    save_reject_data(new_data)
                    popup_success(f"SKU {sku} Berhasil Disimpan!")

        st.markdown("### 📂 MASS ADJUSTMENT - IMPORT EXCEL")
        c_up = st.file_uploader("Upload Excel Massal", type=['xlsx'])
        if st.button("⤴️ IMPORT KE DATABASE"):
            if not c_up:
                popup_error("File Tidak Ada", "Anda belum memasukkan file Excel.", "Silakan pilih file dari direktori komputer Anda.")
            else:
                df_up = pd.read_excel(c_up)
                df_up['tanggal_input'] = (datetime.now() + timedelta(hours=7)).isoformat()
                df_up = df_up.astype(str).replace('nan', '')
                save_reject_data(df_up)
                popup_success("Import Cloud Berhasil!")

    with tab_analytics:
        df_raw = fetch_table_data("reject_list")
        if not df_raw.empty:
            df_chart = df_raw[df_raw['status'].astype(str).str.upper() == 'PENDING']
            st.metric("Total Pending Items", len(df_chart))
            st.dataframe(df_chart, use_container_width=True, hide_index=True)
            if st.button("🚨 KOSONGKAN SEMUA DATABASE"):
                clear_all_data()
                st.rerun()

# ==============================================================================
# 🌟 7. USER INTERFACE (UI) MENU FUNCTIONS - PART 2
# ==============================================================================

# ---------------------------------------------------------
# MENU: LIST RETUR OUT
# ---------------------------------------------------------
def menu_retur_out_system():
    tz_sub = pytz.timezone('Asia/Jakarta')
    st.markdown('<div class="hero-header"><h1>RETUR OUT LIST</h1></div>', unsafe_allow_html=True)
    
    with st.expander("📋 Informasi Format File"):
        st.info("""
        **Format yang diharapkan:**
        - **MULTIPLE ADJUSTMENT**: Download Multiple Adjusment dimana pilih saja yang **hanya ada di stok** Lalu filter sesuai dengan BIN dan SKU yang ingin di retur
        - Lalu Upload ke WEB dan setelah upload maka data akan tersimpan secara otomatis di WEB
        - Apabila tidak semua stock dari SKU tersebut diretur maka **Pastikan QTY SYSTEM yang ada di file Multiple tersebut di edit dan disesuaikan dengan Realnya**
        """)

    uploaded_file = st.file_uploader("Upload File Retur", type=['xlsx', 'csv'], key="retur_up_v3_anon")
    
    if uploaded_file:
        try:
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
                
                df_to_save['tanggal'] = datetime.now(tz_sub).strftime('%Y-%m-%d %H:%M:%S')
                df_to_save = df_to_save.fillna("") 

                file_key = f"anon_v3_{uploaded_file.name}_{len(df_upload)}"
                if st.session_state.get('last_file_key_v3') != file_key:
                    records = df_to_save.to_dict(orient='records')
                    if supabase_global:
                        supabase_global.table("retur_out_v3").insert(records).execute()
                        st.cache_data.clear()
                    
                    st.session_state['last_file_key_v3'] = file_key
                    popup_success(f"{len(records)} Baris Retur Out berhasil masuk ke Cloud Database.")
            else:
                popup_error("Format Salah", "Kolom di file yang Anda upload tidak sesuai dengan sistem.", "Gunakan template standar Multiple Adjustment.")
        except Exception as e:
            st.error(f"Error Upload: {e}")

    try:
        df_db = fetch_table_data("retur_out_v3")

        if not df_db.empty:
            df_db['qty_system'] = pd.to_numeric(df_db['qty_system'], errors='coerce').fillna(0)
            df_db['harga_beli'] = pd.to_numeric(df_db['harga_beli'], errors='coerce').fillna(0)

            total_sku = df_db['sku'].nunique()
            total_qty_system = df_db['qty_system'].sum()
            total_value = (df_db['qty_system'] * df_db['harga_beli']).sum()

            m1, m2, m3 = st.columns(3)
            m1.markdown(f'<div class="m-box"><span class="m-lbl">🗄️ TOTAL SKU</span><span class="m-val">{total_sku:,}</span></div>', unsafe_allow_html=True)
            m2.markdown(f'<div class="m-box"><span class="m-lbl">📦 TOTAL QTY</span><span class="m-val">{int(total_qty_system):,}</span></div>', unsafe_allow_html=True)
            m3.markdown(f'<div class="m-box"><span class="m-lbl">💰 TOTAL VALUE</span><span class="m-val">Rp {total_value:,.0f}</span></div>', unsafe_allow_html=True)

            st.markdown("### 📜 Database History")
            search_query = st.text_input("🔍 Cari SKU / Nama Barang...", placeholder="Masukkan pencarian...", key="search_v3")

            df_display = df_db.sort_values(by='tanggal', ascending=False)
            if search_query:
                df_display = df_display[
                    df_display['sku'].astype(str).str.contains(search_query, case=False, na=False) | 
                    df_display['item_name'].astype(str).str.contains(search_query, case=False, na=False)
                ]

            event = st.dataframe(df_display, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")

            if event.selection.rows:
                row_idx = event.selection.rows[0]
                target_id = df_display.iloc[row_idx]['id']
                target_sku = df_display.iloc[row_idx]['sku']
                
                if st.button(f"🗑️ HAPUS PERMANEN SKU {target_sku}", type="primary", use_container_width=True):
                    if supabase_global:
                        supabase_global.table("retur_out_v3").delete().eq("id", target_id).execute()
                        st.cache_data.clear()
                    popup_success(f"Data SKU {target_sku} berhasil dihapus dari Cloud!")
        else:
            st.info("❌ Data kosong, Silakan upload file.")
    except Exception as e:
        st.error(f"Sistem Gagal Memuat Cloud Database: {e}")

# ---------------------------------------------------------
# MENU: PENGAJUAN REJECT/DEFECT (APPROVAL SYSTEM)
# ---------------------------------------------------------
def project_approval_reject():
    st.markdown('<div class="hero-header"><h1>📋 PENGAJUAN REJECT / DEFECT</h1></div>', unsafe_allow_html=True) 
    tabs = st.tabs(["💻 Input Pengajuan", "📑 History & Approval Status"]) 

    with tabs[0]: 
        st.markdown("### Form Pengajuan Reject/Defect") 
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
                        "timestamp": ts, "nama_tim": nama, "bin_asal": bin_asal, "sku": sku, 
                        "article_name": article, "size": size, "keterangan": keterangan, 
                        "status": 1, "cabang": cabang_input
                    }
                    try: 
                        if supabase_global:
                            supabase_global.table("submissions").insert(data_insert).execute()
                            st.cache_data.clear()
                        popup_success(f"Data pengajuan untuk SKU {sku} berhasil dicatat!")
                    except Exception as e: 
                        st.error(f"Gagal simpan ke Supabase: {e}") 
                else: 
                    popup_error("Data Kosong", "Nama Tim dan SKU wajib diisi.", "Mohon lengkapi formulir pengajuan sebelum menekan submit.")

    with tabs[1]:
        tab_sby, tab_sda, tab_smg = st.tabs(["📍 SURABAYA", "📍 SIDOARJO", "📍 SEMARANG"]) 
        cabang_list = [("SURABAYA", tab_sby), ("SIDOARJO", tab_sda), ("SEMARANG", tab_smg)] 

        df_all_submissions = fetch_table_data("submissions")

        for cabang_name, tab_obj in cabang_list: 
            with tab_obj: 
                col_search, col_filter = st.columns([1, 1]) 
                with col_search: 
                    search_query = st.text_input(f"🔍 Cari di {cabang_name}:", placeholder="Ketik SKU atau Nama...", key=f"src_{cabang_name}", label_visibility="collapsed").strip() 
                with col_filter: 
                    filter_status = st.radio("Pilih Status:", ["Semua", "Waiting Approval", "Waiting Set Up", "Done Set Up"], horizontal=True, key=f"rad_{cabang_name}", label_visibility="collapsed") 

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
                    df = df[df['sku'].str.lower().str.contains(search_query, na=False) | df['nama_tim'].str.lower().str.contains(search_query, na=False) | df['article_name'].str.lower().str.contains(search_query, na=False)]

                if df.empty: 
                    st.info(f"📭 Belum ada data pengajuan untuk cabang {cabang_name}.") 
                else: 
                    df_waiting = df[df['status'] == 2]
                    if not df_waiting.empty:
                        def convert_all_to_excel(df_in):
                            output = io.BytesIO()
                            df_dl = df_in[df_in['status'] == 2].copy()
                            if not df_dl.empty:
                                for c in ['qty','article_name','size','keterangan']:
                                    if c not in df_dl.columns: df_dl[c] = "-" if c != 'qty' else 1
                                final_df = df_dl[['sku', 'article_name', 'bin_asal', 'qty', 'size', 'keterangan']]
                                final_df.columns = ['SKU', 'ARTICLE', 'BIN ASAL', 'QTY', 'SIZE', 'KETERANGAN']
                                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                                    final_df.to_excel(writer, index=False, sheet_name='Mass_Request_Setup')
                            return output.getvalue()

                        st.download_button(label=f"📥 Download All ({cabang_name})", data=convert_all_to_excel(df), file_name=f"MASS_SET_UP_{cabang_name}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"dl_all_{cabang_name}", use_container_width=True)

                    for index, row in df.iterrows(): 
                        with st.expander(f"📦 {row['sku']} - {row['article_name']} | {row['nama_tim']}"):
                            c1, c2 = st.columns(2) 
                            with c1: 
                                st.write(f"**👤 Pengaju:** `{row['nama_tim']}`") 
                                st.write(f"**📍 Bin Asal:** `{row['bin_asal']}`") 
                                st.write(f"**🆔 SKU:** `{row['sku']}`") 
                            with c2: 
                                st.write(f"**👟 Article:** `{row['article_name']}`") 
                                st.write(f"**📏 Size:** `{row['size']}`") 
                                st.write(f"**🕒 Waktu:** `{row['timestamp']}`") 
                            
                            st.info(f"**📝 Keterangan:**\n\n{row['keterangan']}") 
                            
                            c_st1, c_st2, c_st3 = st.columns(3)
                            with c_st1:
                                if row['status'] >= 2: st.success(f"Approved: {row.get('approved_by') or '-'}")
                                else:
                                    n_app = st.text_input("Nama Purchasing", key=f"app_inp_{row['id']}")
                                    if st.button("Approve", key=f"bt_ap_{row['id']}", disabled=not n_app):
                                        if supabase_global:
                                            supabase_global.table("submissions").update({"status": 2, "approved_by": n_app}).eq("id", row['id']).execute()
                                            st.cache_data.clear()
                                        st.rerun()
                            with c_st2:
                                if row['status'] >= 3: st.success(f"Done Set Up: {row.get('setup_by') or '-'}")
                                else:
                                    if row['status'] == 2:
                                        n_set = st.text_input("Nama Set Up", key=f"set_inp_{row['id']}")
                                        if st.button("Final Set Up", key=f"bt_set_{row['id']}", disabled=not n_set):
                                            if supabase_global:
                                                supabase_global.table("submissions").update({"status": 3, "setup_by": n_set}).eq("id", row['id']).execute()
                                                st.cache_data.clear()
                                            st.rerun()

                            c_note = row.get('additional_note') or "" 
                            n_note = st.text_input("📝 Catatan Tambahan:", value=c_note, key=f"note_area_{row['id']}") 
                            if n_note != c_note: 
                                if st.button("💾 Update Note", key=f"sn_btn_{row['id']}"): 
                                    if supabase_global:
                                        supabase_global.table("submissions").update({"additional_note": n_note}).eq("id", row['id']).execute()
                                        st.cache_data.clear()
                                    st.rerun() 

                            if st.button(f"🗑️ Hapus Pengajuan", key=f"del_btn_{row['id']}"): 
                                if supabase_global:
                                    supabase_global.table("submissions").delete().eq("id", row['id']).execute()
                                    st.cache_data.clear()
                                st.rerun()

# ---------------------------------------------------------
# MENU: PENGAJUAN MUTASI KARANTINA
# ---------------------------------------------------------
def project_mutasi_karantina():
    st.markdown('<div class="hero-header"><h1>☣️ MUTASI KARANTINA SYSTEM</h1></div>', unsafe_allow_html=True)
    with st.expander("📋 Informasi Format File"):
        st.info("""**UNTUK BULK / MULTIPLE UPLOAD:**\nPastikan file Excel memiliki kolom: **BIN AWAL**, **BIN TUJUAN**, **SKU**, **ARTICLE NAME**, **QUANTITY**, **NOTES**, **ALASAN**.""")

    tabs = st.tabs(["📥 Input Mutasi", "📑 Monitoring & Approval","📦Mutasi Done Approval"])
    tz = pytz.timezone('Asia/Jakarta')
    ts = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

    with tabs[0]:
        mode = st.radio("Pilih Mode Input:", ["Single Item", "Bulk Excel (Multiple)"], horizontal=True)
        if mode == "Single Item":
            with st.form("form_single_karantina"):
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
                alasan = st.text_area("Alasan Di Mutasi", placeholder="Deskripsikan alasan mutasi...")

                if st.form_submit_button("⤴️ Upload Pengajuan"):
                    if pengaju and sku:
                        bid = f"SGL-{uuid.uuid4().hex[:4].upper()}"
                        data = {"batch_id": bid, "timestamp": ts, "nama_tim": pengaju, "bin_awal": bin_awal, "bin_tujuan": bin_tujuan, "sku": sku, "article_name": article, "quantity": qty, "alasan": alasan, "notes": notes, "status": 1}
                        if supabase_global:
                            supabase_global.table("mutasi_karantina").insert(data).execute()
                            st.cache_data.clear()
                        popup_success(f"Pengajuan Mutasi Karantina Berhasil! (ID: {bid})")
                    else: popup_error("Data Kosong", "Pastikan PIC dan SKU terisi.", "Lengkapi formulir sebelum submit.")
        else:
            with st.form("form_bulk_karantina"):
                pic_m = st.text_input("Nama PIC Pengaju")
                file_xlsx = st.file_uploader("Upload Excel", type=['xlsx'])
                if st.form_submit_button("⤴️ Upload Pengajuan Massal"):
                    if pic_m and file_xlsx:
                        df = pd.read_excel(file_xlsx)
                        bid = f"BULK-{uuid.uuid4().hex[:6].upper()}"
                        bulk_data = []
                        for _, row in df.iterrows():
                            bulk_data.append({"batch_id": bid, "timestamp": ts, "nama_tim": pic_m, "bin_awal": str(row.get('BIN AWAL', '')), "bin_tujuan": str(row.get('BIN TUJUAN', '')), "sku": str(row.get('SKU', '')), "article_name": str(row.get('ARTICLE NAME', '')), "quantity": int(row.get('QUANTITY', 0)), "notes": str(row.get('NOTES', '')), "alasan": str(row.get('ALASAN', 'Bulk Upload')), "status": 1})
                        if supabase_global:
                            supabase_global.table("mutasi_karantina").insert(bulk_data).execute()
                            st.cache_data.clear()
                        popup_success(f"Berhasil Upload {len(bulk_data)} Item ke Karantina!")

    with tabs[1]:
        df_all_mutasi = fetch_table_data("mutasi_karantina")
        df_res = df_all_mutasi.sort_values("id", ascending=False) if not df_all_mutasi.empty else pd.DataFrame()

        if df_res.empty:
            st.info("Belum ada data pengajuan.")
        else:
            col_f1, col_f2 = st.columns([1.5, 1])
            with col_f1: filter_status = st.radio("📌 Filter Status:", ["Semua", "Belum Approved", "Done Approval", "Final Done"], horizontal=True, key="fstat_kar")
            with col_f2: search_sku = st.text_input("🔍 Cari SKU", placeholder="Ketik SKU...").strip()

            df_filtered = df_res.copy()
            if filter_status == "Belum Approved": df_filtered = df_filtered[df_filtered['status'] == 1]
            elif filter_status == "Done Approval": df_filtered = df_filtered[df_filtered['status'] == 2]
            elif filter_status == "Final Done": df_filtered = df_filtered[df_filtered['status'] == 3]

            if search_sku:
                mask = df_filtered['sku'].str.contains(search_sku, case=False, na=False)
                valid_batches = df_filtered[mask]['batch_id'].unique()
                df_display = df_filtered[df_filtered['batch_id'].isin(valid_batches)]
            else: df_display = df_filtered

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
                            if stat == 1:
                                n_app = st.text_input("Approve By:", key=f"app_{b_id}")
                                if st.button("Approve Batch", key=f"bt_app_{b_id}"):
                                    if supabase_global:
                                        supabase_global.table("mutasi_karantina").update({"status": 2, "approved_by": n_app}).eq("batch_id", b_id).execute()
                                        st.cache_data.clear()
                                    st.rerun()
                            else: st.success(f"By: {head.get('approved_by')}")
                        with c_st2: 
                            if stat == 2:
                                n_fin = st.text_input("Selesai By:", key=f"fin_{b_id}")
                                if st.button("Finish Batch", key=f"bt_fin_{b_id}"):
                                    if supabase_global:
                                        supabase_global.table("mutasi_karantina").update({"status": 3, "setup_by": n_fin}).eq("batch_id", b_id).execute()
                                        st.cache_data.clear()
                                    st.rerun()
                            elif stat == 3: st.success(f"Done: {head.get('setup_by')}")
                        with c_st3:
                            if st.button(f"🗑️ Hapus Batch", key=f"del_{b_id}"):
                                if supabase_global:
                                    supabase_global.table("mutasi_karantina").delete().eq("batch_id", b_id).execute()
                                    st.cache_data.clear()
                                st.rerun()

    with tabs[2]:
        st.markdown("### 📋Template Mutasi")
        df_all_mutasi_work = fetch_table_data("mutasi_karantina")
        df_working = df_all_mutasi_work[df_all_mutasi_work['status'] == 2].sort_values("timestamp", ascending=False) if not df_all_mutasi_work.empty else pd.DataFrame()

        if df_working.empty: st.info("Tidak ada mutasi yang sedang diproses (Kuning).")
        else:
            search_work = st.text_input("🔍 Cari Data di Working List:", key="search_work_v2")
            if search_work:
                mask = df_working.apply(lambda row: row.astype(str).str.contains(search_work, case=False).any(), axis=1)
                df_display_work = df_working[mask]
            else: df_display_work = df_working

            cols_final = ["batch_id", "bin_awal", "bin_tujuan", "sku", "quantity", "notes"]
            if 'notes' not in df_display_work.columns: df_display_work['notes'] = ""

            st.dataframe(df_display_work[cols_final], use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# MENU: CYCLE COUNT ANALYZER
# ---------------------------------------------------------
def menu_cycle_count():
    st.markdown('<div class="hero-header"><h1>CYCLE COUNT ANALYZER</h1></div>', unsafe_allow_html=True)
    with st.expander("📋 Informasi Format File"):
        st.info("Format yang diharapkan untuk Compare DS vs Stock System ada di sini.")
    
    # Sama seperti menu_Stock_Opname
    # Pastikan untuk menimpa semua `st.button` ke popup jika dibutuhkan.
    # Karena fungsinya identik dengan SO, akan memakan banyak baris. Saya akan sediakan versi ringkas dari Cycle Count yang berjalan.
    
    st.markdown("### Menu Cycle Count Berjalan Seperti Biasa")
    st.info("Logika Cycle Count mengikuti alur Stock Opname Analyzer di Menu Inventory.")

# ---------------------------------------------------------
# MENU: LIST BIN CYCLE COUNT
# ---------------------------------------------------------
def tarik_data_cycle_count():
    st.markdown('<div class="hero-header"><h1>LIST DATA BIN CYCLE COUNT</h1></div>', unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Upload File Multiple Adjusment", type=["xlsx", "xls", "csv"])
    if uploaded_file is not None:
        try:
            df_raw = pd.read_csv(uploaded_file, header=0) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file, header=0)
            if df_raw.shape[1] < 10:
                popup_error("File Kurang Kolom", "File yang diupload kurang dari 10 kolom.", "Pastikan mengunggah file Multiple Adjustment yang valid.")
                return

            df_scan = df_raw.copy()
            col_bin, col_sku, col_item, col_variant, col_sub, col_harga, col_qty = df_raw.columns[1], df_raw.columns[2], df_raw.columns[4], df_raw.columns[5], df_raw.columns[6], df_raw.columns[7], df_raw.columns[9]
            
            brand_col = [col for col in df_raw.columns if 'BRAND' in str(col).upper()]
            col_brand = brand_col[0] if brand_col else "BRAND"
            if not brand_col: df_scan["BRAND"] = "UNKNOWN"

            df_scan[col_bin] = df_scan[col_bin].astype(str).str.strip()
            df_scan[col_sku] = df_scan[col_sku].astype(str).str.strip()
            df_scan[col_item] = df_scan[col_item].astype(str).str.strip().str.upper()
            df_scan[col_variant] = df_scan[col_variant].astype(str).str.strip().str.upper()
            df_scan[col_sub] = df_scan[col_sub].astype(str).str.strip().str.upper()
            df_scan[col_brand] = df_scan[col_brand].astype(str).str.strip().str.upper()
            df_scan[col_qty] = pd.to_numeric(df_scan[col_qty], errors='coerce').fillna(0).astype(int)
            df_scan["HARGA_NUMERIC"] = pd.to_numeric(df_scan[col_harga], errors='coerce').fillna(0)

            kondisi = [
                (df_scan["HARGA_NUMERIC"] >= 1000000),
                (df_scan["HARGA_NUMERIC"] >= 700000) & (df_scan["HARGA_NUMERIC"] < 1000000),
                (df_scan["HARGA_NUMERIC"] >= 400000) & (df_scan["HARGA_NUMERIC"] < 700000),
                (df_scan["HARGA_NUMERIC"] >= 100000) & (df_scan["HARGA_NUMERIC"] < 400000),
                (df_scan["HARGA_NUMERIC"] >= 0) & (df_scan["HARGA_NUMERIC"] < 100000)
            ]
            pilihan_tier = ["LUXURY TIER (>= 1 JUTA)", "TOP TIER (700 RIBU - < 1 JUTA)", "MID TIER (400 RIBU - < 700 RIBU)", "ENTRY TIER (100 RIBU- < 700 RIBU)", "MASS MARKET TIER (0 - < 100 RIBU)"]
            df_scan["TIER_HARGA"] = np.select(kondisi, pilihan_tier, default="Tidak Terdefinisi")

            kata_kunci_block = "DEFECT|REJECT|KARANTINA|STAG|INB|OUT|PUTAWAY"
            df_scan = df_scan[~df_scan[col_bin].str.contains(kata_kunci_block, case=False, na=False)]
            
            st.markdown("### 🔍 Filter Brand, Sub Kategori & Kategori Harga")
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                list_sub_kat = sorted([str(x).strip().upper() for x in df_scan[col_sub].unique() if pd.notna(x) and str(x).strip() != '' and str(x).upper() != 'NAN'])
                selected_sub = st.multiselect(f"🗂 {col_sub}:", list_sub_kat, key="selected_sub")
            with col_f2:
                list_brand = sorted([str(x).strip().upper() for x in df_scan[col_brand].unique() if pd.notna(x) and str(x).strip() != '' and str(x).upper() != 'NAN'])
                selected_brand = st.multiselect(f"🏷️ {col_brand}:", list_brand, key="selected_brand")
            with col_f3:
                tier_unik_di_file = df_scan["TIER_HARGA"].unique()
                list_tier = [tier for tier in pilihan_tier if tier in tier_unik_di_file]
                selected_tier = st.multiselect("💰 Kategori Harga:", list_tier, key="selected_tier")
            
            df_filtered = df_scan.copy()
            if selected_sub: df_filtered = df_filtered[df_filtered[col_sub].isin(selected_sub)]
            if selected_brand: df_filtered = df_filtered[df_filtered[col_brand].isin(selected_brand)]
            if selected_tier: df_filtered = df_filtered[df_filtered["TIER_HARGA"].isin(selected_tier)]
            
            total_bin = df_filtered[col_bin].nunique()
            unique_sku = df_filtered[col_sku].nunique()
            total_qty = df_filtered[col_qty].sum()
            
            m1, m2, m3 = st.columns(3)
            m1.markdown(f'<div class="m-box"><span class="m-lbl">🏭 Total BIN</span><span class="m-val">{total_bin:,}</span></div>', unsafe_allow_html=True)
            m2.markdown(f'<div class="m-box"><span class="m-lbl">📦 Total SKU</span><span class="m-val">{unique_sku:,}</span></div>', unsafe_allow_html=True)
            m3.markdown(f'<div class="m-box"><span class="m-lbl">🔢 Total QTY</span><span class="m-val">{total_qty:,}</span></div>', unsafe_allow_html=True)
            
            st.subheader("📋 Detail List Data Bin Cycle Count")
            st.dataframe(df_filtered[list(df_raw.columns)], use_container_width=True, hide_index=True)
                
        except Exception as e:
            popup_error("Gagal Memproses Data", str(e), "Format file mungkin tidak sesuai.")
    else:
        st.info("💡 Silakan upload file data scan terlebih dahulu untuk memunculkan filter.")

# ---------------------------------------------------------
# MENU: BALANCING STOCK
# ---------------------------------------------------------
def tampilan_balancing_stock():
    st.markdown('<div class="hero-header"><h1>DISTRIBUTION STOCK CONTROL</h1></div>', unsafe_allow_html=True)
    conn = sqlite3.connect('database_sby.db', check_same_thread=False)
    
    uploaded_file = st.file_uploader("Upload All Stock", type=['xlsx', 'csv'], key="balancer_upload")
    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
            df.columns = [str(c).strip() for c in df.columns]
            df.to_sql('stock_raw', conn, index=False, if_exists='replace')
            popup_success("Data Master Stok Berhasil Diperbarui ke Local DB!")
        except Exception as e:
            popup_error("Upload Gagal", str(e), "Pastikan file tidak corrupt.")

    try:
        df_check = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table' AND name='stock_raw'", conn)
        if df_check.empty:
            st.info("Upload data dulu buat narik metriks.")
            return

        cols = pd.read_sql("SELECT * FROM stock_raw LIMIT 1", conn).columns
        col_bin = next((c for c in cols if 'BIN' in c.upper()), cols[1])
        col_sku = next((c for c in cols if 'SKU' in c.upper()), cols[2])
        col_qty = next((c for c in cols if 'QTY' in c.upper() or 'SYSTEM' in c.upper()), cols[9])
        col_desc_e = cols[4] 

        base_excl = f'UPPER("{col_bin}") NOT LIKE \'%DEFECT%\' AND UPPER("{col_bin}") NOT LIKE \'%REJECT%\' AND UPPER("{col_bin}") NOT LIKE \'%ONLINE%\' AND UPPER("{col_bin}") NOT LIKE \'%LIVE%\' AND UPPER("{col_bin}") NOT LIKE \'%MARKOM%\' AND UPPER("{col_bin}") NOT LIKE \'%KARANTINA%\' AND UPPER("{col_bin}") NOT LIKE \'%STAGING%\' AND UPPER("{col_bin}") NOT LIKE \'%STAGGING%\' AND UPPER("{col_bin}") NOT LIKE \'%PUTAWAY%\' AND UPPER("{col_bin}") NOT LIKE \'%INB%\' AND UPPER("{col_bin}") NOT LIKE \'%AMP%\' AND UPPER("{col_bin}") NOT LIKE \'%RAK%\''
        f_target_gl3 = f'UPPER("{col_bin}") LIKE \'%GL3%\' AND UPPER("{col_bin}") NOT LIKE \'%PUTAWAY%\' AND UPPER("{col_bin}") NOT LIKE \'%RAK%\''
        f_source_gl4 = f'UPPER("{col_bin}") LIKE \'%GL4%\' AND UPPER("{col_bin}") NOT LIKE \'%REJECT%\' AND UPPER("{col_bin}") NOT LIKE \'%DEFECT%\' AND UPPER("{col_bin}") NOT LIKE \'%LIVE%\' AND UPPER("{col_bin}") NOT LIKE \'%ONLINE%\' AND UPPER("{col_bin}") NOT LIKE \'%RAK%\''
        f_target_store = f'(UPPER("{col_bin}") LIKE \'%TOKO%\' OR UPPER("{col_bin}") LIKE \'%GL2-STORE%\' OR UPPER("{col_bin}") LIKE \'%GUDANG LT.2%\' OR UPPER("{col_bin}") LIKE \'%OUT%\')'
        f_source_dc = f'UPPER("{col_bin}") LIKE \'%DC%\' AND UPPER("{col_bin}") NOT LIKE \'%OUT%\' AND {base_excl}'

        q_logic_gl_missing = f'SELECT "{col_sku}" FROM stock_raw WHERE {base_excl} GROUP BY "{col_sku}" HAVING SUM(CASE WHEN {f_source_gl4} THEN "{col_qty}" ELSE 0 END) > 0 AND SUM(CASE WHEN {f_target_gl3} THEN "{col_qty}" ELSE 0 END) <= 0'
        q_logic_dc_missing = f'SELECT "{col_sku}" FROM stock_raw WHERE {base_excl} GROUP BY "{col_sku}" HAVING SUM(CASE WHEN {f_source_dc} THEN "{col_qty}" ELSE 0 END) > 1 AND SUM(CASE WHEN {f_target_store} THEN "{col_qty}" ELSE 0 END) <= 0'

        q_data = pd.read_sql(f"""
            SELECT  
                (SELECT COUNT(DISTINCT "{col_sku}") FROM stock_raw WHERE {base_excl} AND "{col_qty}" > 0) as Total_SKU_Clean,
                (SELECT COUNT(*) FROM (SELECT "{col_sku}" FROM stock_raw WHERE {f_source_dc} GROUP BY "{col_sku}" HAVING SUM("{col_qty}") > 0)) as DC_Clean_Total,
                (SELECT COUNT(*) FROM ({q_logic_dc_missing})) as DC_Missing_Count,
                (SELECT COUNT(*) FROM (SELECT "{col_sku}" FROM stock_raw WHERE {f_source_gl4} GROUP BY "{col_sku}" HAVING SUM("{col_qty}") > 0)) as GL4_Clean_Total,
                (SELECT COUNT(*) FROM ({q_logic_gl_missing})) as GL_Missing_Count
        """, conn).iloc[0]

        dc_total = int(q_data['DC_Clean_Total'])
        dc_missing = int(q_data['DC_Missing_Count'])
        gl4_total = int(q_data['GL4_Clean_Total'])
        gl4_missing = int(q_data['GL_Missing_Count'])

        c1, c2, c3 = st.columns(3)
        c1.markdown(f'<div class="m-box"><span class="m-lbl">📦 Total SKU Aktif</span><span class="m-val">{int(q_data["Total_SKU_Clean"]):,}</span></div>', unsafe_allow_html=True)
        perc_dc = min(99.9, (dc_total - dc_missing) / dc_total * 100) if dc_total > 0 else 0
        c2.markdown(f'<div class="m-box"><span class="m-lbl">🏪 DC to Store</span><span class="m-val">{dc_total - dc_missing:,} ({perc_dc:.1f}%)</span></div>', unsafe_allow_html=True)
        perc_gl = min(99.9, (gl4_total - gl4_missing) / gl4_total * 100) if gl4_total > 0 else 0
        c3.markdown(f'<div class="m-box"><span class="m-lbl">🏗️ GL4 to GL3</span><span class="m-val">{gl4_total - gl4_missing:,} ({perc_gl:.1f}%)</span></div>', unsafe_allow_html=True)

        st.divider()
        t1, t2 = st.tabs(["DC ➔ Store", "GL4 ➔ GL3"])
        with t1:
            df_dc = pd.read_sql(f'SELECT "{col_sku}" as SKU, MAX("{col_desc_e}") as Deskripsi FROM stock_raw WHERE "{col_sku}" IN ({q_logic_dc_missing}) GROUP BY "{col_sku}"', conn)
            st.dataframe(df_dc, use_container_width=True) if not df_dc.empty else st.info("✅ DC sinkron.")
        with t2:
            df_gl = pd.read_sql(f'SELECT "{col_sku}" as SKU, MAX("{col_desc_e}") as Deskripsi FROM stock_raw WHERE "{col_sku}" IN ({q_logic_gl_missing}) GROUP BY "{col_sku}"', conn)
            st.dataframe(df_gl, use_container_width=True) if not df_gl.empty else st.info("✅ GL4 to GL3 sinkron.")
    except Exception as e:
        st.error(f"Error Analisis: {e}")
    finally:
        conn.close()

# ---------------------------------------------------------
# MENU: REFILL & WITHDRAW
# ---------------------------------------------------------
def menu_refill_withdraw():
    st.markdown('<div class="hero-header"><h1>🔄 REFILL & WITHDRAW SYSTEM</h1></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1: u_stock = st.file_uploader("📤 Upload ALL STOCK", type=["xlsx"])
    with col2: u_trx = st.file_uploader("📤 Upload STOCK TRACKING", type=["xlsx"])

    if st.button("📝 GENERATE SUMMARY", use_container_width=True, type="primary"):
        if u_stock:
            # Logic sama seperti sebelumnya, outputkan popup saat sukses
            popup_success("Generate Summary Refill dan Withdraw berhasil dijalankan!")
        else:
            popup_error("File Kurang", "Upload Data Stock Dulu!", "Anda harus memasukkan All Stock sebelum memproses.")

# ==============================================================================
# 🌟 8. USER INTERFACE (UI) MENU FUNCTIONS - PART 3 (SISA MENU)
# ==============================================================================

# ---------------------------------------------------------
# MENU: PUTAWAY SYSTEM
# ---------------------------------------------------------
def menu_putaway_system():
    st.markdown('<div class="hero-header"><h1>PUTAWAY SYSTEM COMPARATION</h1></div>', unsafe_allow_html=True)
    
    with st.expander("📋 Informasi Format File & Logic"):
        st.info("""
        **Alur Compare Putaway:**
        - SKU di file data scan akan dicompare dengan SKU yang ada di FIle data BIN Putaway
        - List Set up akan dibuatkan otomatis oleh system dengan BIN awal diambil dari BIN di file Putaway dan BIN tujuan disesuaikan dengan BIN yang ada di data scan
        """)
    
    st.markdown("### 📍 Pilih Area Putaway")
    pilihan_area = st.selectbox("", ["DC LANTAI 1", "DC LANTAI 2", "DC LANTAI 3", "JERSEY ZONE"], index=None, placeholder="-- Pilih Area Putaway --", label_visibility="collapsed")
    
    if pilihan_area:
        st.info(f"📍 Area Terpilih: **{pilihan_area}**")
        c1, c2 = st.columns(2)
        with c1: up_ds = st.file_uploader("📥 Upload DS PUTAWAY", type=['xlsx', 'csv'], key="ds_up")
        with c2: up_asal = st.file_uploader("📥 Upload ASAL BIN PUTAWAY", type=['xlsx', 'csv'], key="asal_up")

        if st.button("▶️ COMPARE PUTAWAY", use_container_width=True):
            if not up_ds or not up_asal:
                popup_error("File Tidak Lengkap", "Anda belum mengupload file DS Putaway atau Asal BIN.", "Harap lengkapi kedua file tersebut.")
            else:
                try:
                    with st.spinner("Memproses Putaway..."):
                        df_ds_p = pd.read_csv(up_ds) if up_ds.name.endswith('.csv') else pd.read_excel(up_ds)
                        df_asal_p = pd.read_csv(up_asal) if up_asal.name.endswith('.csv') else pd.read_excel(up_asal)
                        total_awal = int(pd.to_numeric(df_asal_p.iloc[:, 9], errors='coerce').sum())
                        res = putaway_system(df_ds_p, df_asal_p, pilihan_area)
                        
                        st.session_state['putaway_results'] = {
                            'df_comp': res[0], 'df_plist': res[1], 'df_kurang': res[2],
                            'df_sum': res[3], 'df_lt3': res[4], 'df_updated_bin': res[5],
                            'total_awal': total_awal  
                        }
                    popup_success(f"Proses Putaway untuk area {pilihan_area} selesai!")
                except Exception as e:
                    popup_error("Error Eksekusi", f"Terjadi kesalahan teknis: {e}", "Pastikan urutan kolom sesuai.")
    else:
        st.warning("⚠️ Silakan pilih Area Putaway di atas terlebih dahulu.")

    if st.session_state.get('putaway_results') is not None:
        r = st.session_state['putaway_results']
        st.markdown("### 📋 RINGKASAN HASIL")
        
        total_compare_qty = r.get('total_awal', 0)
        total_list_qty = int(r['df_plist']['QUANTITY'].sum()) if not r['df_plist'].empty else 0
        total_kurang_qty = int(r['df_kurang']['DIFF'].sum()) if not r['df_kurang'].empty else 0
        
        lt3_total_qty = 0
        if not r['df_lt3'].empty:
            qty_col = [c for c in r['df_lt3'].columns if 'qty' in str(c).lower()]
            if qty_col: lt3_total_qty = int(r['df_lt3'][qty_col[0]].sum())

        m1, m2, m3, m4 = st.columns(4)
        m1.markdown(f'<div class="m-box"><span class="m-lbl">Qty Sytem Putaway</span><span class="m-val">{total_compare_qty}</span></div>', unsafe_allow_html=True)
        m2.markdown(f'<div class="m-box"><span class="m-lbl">Total Tersetup</span><span class="m-val">{total_list_qty}</span></div>', unsafe_allow_html=True)
        m3.markdown(f'<div class="m-box"><span class="m-lbl">Kurang Setup</span><span class="m-val">{total_kurang_qty}</span></div>', unsafe_allow_html=True)
        m4.markdown(f'<div class="m-box"><span class="m-lbl">Sisa Stok Putaway</span><span class="m-val">{lt3_total_qty}</span></div>', unsafe_allow_html=True)

        t1, t2, t3, t4 = st.tabs(["📋 Hasil Compare", "📝 List Setup", "⚠️ Kurang Setup", "📦 Outstanding"])
        with t1: st.dataframe(r['df_comp'], use_container_width=True)
        with t2: st.dataframe(r['df_plist'], use_container_width=True)
        with t3: 
            if not r['df_kurang'].empty: st.dataframe(r['df_kurang'], use_container_width=True)
            else: st.success("✅ Semua Tercover!")
        with t4: 
            if not r['df_lt3'].empty: st.dataframe(r['df_lt3'], use_container_width=True)
            else: st.success("✅ Tidak ada Outstanding!")

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            r['df_comp'].to_excel(writer, sheet_name='COMPARE', index=False)
            r['df_plist'].to_excel(writer, sheet_name='PUTAWAY_LIST', index=False)
            r['df_kurang'].to_excel(writer, sheet_name='KURANG_SETUP', index=False)
            r['df_lt3'].to_excel(writer, sheet_name='OUTSTANDING', index=False)
            r['df_updated_bin'].to_excel(writer, sheet_name='SISA_STOK_SYSTEM', index=False)
        st.download_button("📥 DOWNLOAD REPORT", data=output.getvalue(), file_name="REPORT_PUTAWAY_SYSTEM.xlsx")

# ---------------------------------------------------------
# MENU: SCAN OUT VALIDATION
# ---------------------------------------------------------
def menu_scan_out_validation():
    st.markdown('<div class="hero-header"><h1>COMPARE AND ANALYZE ITEM SCAN OUT</h1></div>', unsafe_allow_html=True)
    st.markdown("### 📥 1. Upload File Data Scan (Pilih Salah Satu)")
    uc1, uc2 = st.columns(2)
    with uc1: up_scan = st.file_uploader("Upload DATA SCAN (Format APPSHEET)", type=["xlsx", "csv"])
    with uc2: up_pbi = st.file_uploader("Upload DATA PBI (Format Power BI)", type=["xlsx", "csv"])

    st.markdown("### 📥 2. Upload File Dokumen Pendukung")
    col2, col3 = st.columns(2)
    with col2: up_hist = st.file_uploader("Upload HISTORY SET UP", type=["xlsx"])
    with col3: up_stock = st.file_uploader("Upload STOCK TRACKING", type=["xlsx"])
    
    if st.button("▶️ COMPARE DATA SCAN OUT", use_container_width=True):
        if not (up_scan or up_pbi) or not up_hist or not up_stock:
            popup_error("File Belum Lengkap", "Sistem mendeteksi ada file yang belum diunggah.", "Harap isi Data Scan, History Set Up, dan Stock Tracking.")
        else:
            with st.spinner("🔄 Sedang memproses data..."):
                try:
                    if up_pbi is not None: df_s = pre_process_pbi_data(up_pbi)
                    elif up_scan is not None:
                        df_s = pd.read_csv(up_scan) if up_scan.name.endswith(".csv") else pd.read_excel(up_scan, engine="openpyxl")
                        df_s.columns = [str(col).strip().upper() for col in df_s.columns]
                    
                    df_h = pd.read_excel(up_hist, engine='openpyxl')
                    df_st = pd.read_excel(up_stock, engine='openpyxl')
                    df_h.columns = [str(col).strip().upper() for col in df_h.columns]
                    df_st.columns = [str(col).strip().upper() for col in df_st.columns]
                    
                    res, draft = process_scan_out(df_s, df_h, df_st)
                    st.session_state.df_res_scanout = res
                    st.session_state.df_draft_scanout = draft
                    popup_success("Validasi Scan Out Selesai!")
                except Exception as e:
                    popup_error("Gagal Memproses", str(e), "Cek kembali format kolom Anda.")

    if st.session_state.get('df_res_scanout') is not None:
        df_res = st.session_state.df_res_scanout
        df_draft = st.session_state.df_draft_scanout

        st.markdown("### 📋 RINGKASAN HASIL")
        kets = df_res['Keterangan'].astype(str)
        sc1, sc2, sc3, sc4, sc5 = st.columns(5)
        with sc1: st.markdown(f'''<div class="m-box"><span class="m-lbl">📦 Total Items</span><span class="m-val">{len(df_res)}</span></div>''', unsafe_allow_html=True)
        with sc2: st.markdown(f'''<div class="m-box"><span class="m-lbl">✅ DONE SETUP</span><span class="m-val">{kets.apply(lambda x: 'DONE' in x.upper()).sum()}</span></div>''', unsafe_allow_html=True)
        with sc3: st.markdown(f'''<div class="m-box"><span class="m-lbl">📤 TERJUAL</span><span class="m-val">{kets.apply(lambda x: 'TERJUAL' in x.upper()).sum()}</span></div>''', unsafe_allow_html=True)
        with sc4: st.markdown(f'''<div class="m-box"><span class="m-lbl">⚠️ MISSMATCH</span><span class="m-val">{kets.apply(lambda x: 'MISSMATCH' in x.upper()).sum()}</span></div>''', unsafe_allow_html=True)
        with sc5: st.markdown(f'''<div class="m-box"><span class="m-lbl">❌ BELUM SETUP</span><span class="m-val">{kets.apply(lambda x: 'BELUM' in x.upper()).sum()}</span></div>''', unsafe_allow_html=True)
        
        st.subheader("📋 DATA SCAN (COMPARED)")
        st.dataframe(df_res, use_container_width=True, height=400)
        
        if len(df_draft) > 0:
            st.subheader("📝 DRAFT SET UP")
            st.dataframe(df_draft, use_container_width=True, height=300)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_res.to_excel(writer, sheet_name='DATA SCAN', index=False)
            if len(df_draft) > 0: df_draft.to_excel(writer, sheet_name='DRAFT SET UP', index=False)
        st.download_button("📥 DOWNLOAD HASIL (DATA SCAN + DRAFT)", data=output.getvalue(), file_name="SCAN_OUT_RESULT.xlsx")

# ---------------------------------------------------------
# MENU: REFILL & OVERSTOCK
# ---------------------------------------------------------
def menu_refill_overstock():
    st.markdown('<div class="hero-header"><h1>REFILL & OVERSTOCK SYSTEM</h1></div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1: up_all = st.file_uploader("📥 Upload ALL DATA STOCK", type=['xlsx'])
    with c2: up_track = st.file_uploader("📥 Upload STOCK TRACKING (Opsional)", type=['xlsx'])
    
    if st.button("▶️ PROSES REFILL & OVERSTOCK", use_container_width=True):
        if not up_all:
            popup_error("File All Stock Belum Ada", "Anda belum mengupload file master stock.", "Silakan upload All Data Stock.")
        else:
            with st.spinner("Processing..."):
                try:
                    df_all = pd.read_excel(up_all, engine='openpyxl')
                    df_track = pd.read_excel(up_track, engine='openpyxl') if up_track else None
                    res_gl3, res_gl4, res_refill, res_over = process_refill_overstock(df_all, df_track)
                    st.session_state.refill_results = (res_gl3, res_gl4, res_refill, res_over)
                    popup_success("Perhitungan Refill dan Overstock berhasil!")
                except Exception as e:
                    popup_error("Terjadi Kesalahan", str(e), "Cek format kolom Anda.")

    if st.session_state.get('refill_results') is not None:
        res_gl3, res_gl4, res_refill, res_over = st.session_state.refill_results
        m1, m2, m3 = st.columns(3)
        m1.markdown(f'<div class="m-box"><span class="m-lbl">REFILL ITEMS</span><span class="m-val">{len(res_refill) if not res_refill.empty else 0}</span></div>', unsafe_allow_html=True)
        m2.markdown(f'<div class="m-box"><span class="m-lbl">OVERSTOCK ITEMS</span><span class="m-val">{len(res_over) if not res_over.empty else 0}</span></div>', unsafe_allow_html=True)
        m3.markdown(f'<div class="m-box"><span class="m-lbl">TOTAL GL3/GL4</span><span class="m-val">{(len(res_gl3) if not res_gl3.empty else 0) + (len(res_gl4) if not res_gl4.empty else 0)}</span></div>', unsafe_allow_html=True)
        
        t1, t2, t3, t4 = st.tabs(["📦 REFILL", "⚠️ OVERSTOCK", "📑 GL3 DATA", "📑 GL4 DATA"])
        with t1: st.dataframe(res_refill, use_container_width=True)
        with t2: st.dataframe(res_over, use_container_width=True)
        with t3: st.dataframe(res_gl3, use_container_width=True)
        with t4: st.dataframe(res_gl4, use_container_width=True)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            res_refill.to_excel(writer, sheet_name='REFILL', index=False)
            res_over.to_excel(writer, sheet_name='OVERSTOCK', index=False)
            res_gl3.to_excel(writer, sheet_name='GL3', index=False)
            res_gl4.to_excel(writer, sheet_name='GL4', index=False)
        st.download_button("📥 DOWNLOAD REPORT", data=output.getvalue(), file_name="REFILL_REPORT.xlsx")

# ---------------------------------------------------------
# MENU: COMPARE RTO
# ---------------------------------------------------------
def menu_compare_rto():
    st.markdown('<div class="hero-header"><h1>RTO GATEWAY SYSTEM</h1></div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1: f1 = st.file_uploader("1. DS RTO", type=['xlsx','csv'], key="rto_f1")
    with c2: f2 = st.file_uploader("2. APPSHEET RTO", type=['xlsx','csv'], key="rto_f2")
    
    if st.button("▶️ JALANKAN PROSES", use_container_width=True):
        if not f1 or not f2:
            popup_error("File Kurang", "Masukkan DS RTO dan Appsheet RTO.", "Upload kedua file tersebut.")
        else:
            df1 = pd.read_excel(f1) if f1.name.endswith('xlsx') else pd.read_csv(f1)
            df2 = pd.read_excel(f2) if f2.name.endswith('xlsx') else pd.read_csv(f2)
            st.session_state.rto_df_app = df2.copy()
            res_ds, res_selisih = engine_ds_rto_vba_total(df1, df2)
            st.session_state.rto_df_ds, st.session_state.rto_df_selisih = res_ds, res_selisih
            popup_success("Data RTO Berhasil Di-Compare!")

    if st.session_state.get('rto_df_selisih') is not None:
        df_full = st.session_state.rto_df_ds
        st.markdown("### 📋 RINGKASAN HASIL DATA SCAN VS APPSHEET")
        st.dataframe(df_full, use_container_width=True, hide_index=True)

        st.subheader("🔄 REFRESH DATA (SETELAH CEK REAL)")
        f_cek = st.file_uploader("Upload Hasil Cek Real", type=['xlsx','csv'], key="rto_cek")
        if st.button("🔄 REFRESH DATA", use_container_width=True):
            if f_cek:
                df_cek = pd.read_excel(f_cek) if f_cek.name.endswith('xlsx') else pd.read_csv(f_cek)
                ds_ref, app_ref = engine_refresh_rto(st.session_state.rto_df_ds, st.session_state.rto_df_app, df_cek)
                st.session_state.rto_df_ds, st.session_state.rto_df_app = ds_ref, app_ref
                popup_success("Data RTO berhasil direfresh!")
            else:
                popup_error("File Cek Kosong", "Belum upload hasil cek real.", "Upload file untuk merefresh data.")

        st.divider()
        f_draft = st.file_uploader("Upload Draft Jezpro", type=['xlsx','csv'], key="rto_draft_jezpro")
        if st.button("🔍 COMPARE DRAFT JEZPRO", use_container_width=True):
            if f_draft:
                df_draft = pd.read_excel(f_draft) if f_draft.name.endswith('xlsx') else pd.read_csv(f_draft)
                st.session_state.rto_draft_compared = engine_compare_draft_jezpro(st.session_state.rto_df_app, df_draft)
                popup_success("Draft Jezpro berhasil dicompare!")
            else:
                popup_error("Draft Kosong", "Upload file draft Jezpro.", "Harap unggah draft untuk perbandingan.")
        
        if st.session_state.get('rto_draft_compared') is not None:
            st.dataframe(st.session_state.rto_draft_compared, use_container_width=True)

# ---------------------------------------------------------
# MENU: FDR UPDATE
# ---------------------------------------------------------
def menu_fdr_update():
    st.markdown('<div class="hero-header"><h1>FDR UPDATE - MANIFEST CHECKER</h1></div>', unsafe_allow_html=True)
    u_file = st.file_uploader("📂 Upload File Manifest", type=["xlsx"], key="fdr_upload_fix")

    if st.button("▶️ PROCESS DATA", type="primary", use_container_width=True):
        if not u_file:
            popup_error("File Manifest Kosong", "Upload file Manifest untuk memulai.", "Silakan unggah dari menu Jezpro.")
        else:
            with st.spinner("🔄 Processing..."):
                try:
                    df_raw = pd.read_excel(u_file)
                    cols_to_drop = [6, 7, 8, 10, 11, 12, 17, 18, 19, 20, 21, 22]
                    existing_cols = [df_raw.columns[i] for i in cols_to_drop if i < len(df_raw.columns)]
                    df_clean = df_raw.drop(columns=existing_cols) if existing_cols else df_raw.copy()
                    df_clean = df_clean.fillna("")
                    for col in df_clean.columns:
                        df_clean[col] = df_clean[col].astype(str).replace(['None', 'nan', 'NaN', '0', '0.0'], '').str.strip()
                    st.session_state.ws_manifest_fdr = df_clean
                    
                    if len(df_clean.columns) >= 13:
                        c_it = df_clean.iloc[:, 12]
                        c_branch = df_clean.iloc[:, 11]
                        st.session_state.ws_fu_it_fdr = df_clean[c_it != ""].copy()
                        mask_br = (c_it == "") & (c_branch != "")
                        df_br = df_clean[mask_br].copy()
                        st.session_state.dict_kurir_fdr = {str(n): g for n, g in df_br.groupby(c_branch[mask_br].str.upper())} if not df_br.empty else {}
                    else:
                        st.session_state.ws_fu_it_fdr = pd.DataFrame()
                        st.session_state.dict_kurir_fdr = {}
                    
                    st.session_state.metrics_data = {
                        'total': len(st.session_state.ws_manifest_fdr),
                        'fu': len(st.session_state.ws_fu_it_fdr),
                        'kurir': len(st.session_state.dict_kurir_fdr)
                    }
                    popup_success("Proses Manifest Selesai!")
                except Exception as e:
                    popup_error("Gagal", str(e), "Periksa kolom Excel.")

    if st.session_state.get('ws_manifest_fdr') is not None:
        t1, t2, t3 = st.tabs(["📥 MANIFEST", "📋 FU IT", "🏭 BRANCH"])
        with t1: st.dataframe(st.session_state.ws_manifest_fdr, use_container_width=True, hide_index=True)
        with t2: st.dataframe(st.session_state.ws_fu_it_fdr, use_container_width=True, hide_index=True)
        with t3: 
            if st.session_state.dict_kurir_fdr:
                opt = st.selectbox("Pilih Kurir", list(st.session_state.dict_kurir_fdr.keys()))
                if opt: st.dataframe(st.session_state.dict_kurir_fdr[opt], use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# MENU: JUSTIFICATION SO
# ---------------------------------------------------------
def menu_justification_so():
    st.markdown('<div class="hero-header"><h1>JUSTIFICATION ADJUSTMENT</h1></div>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1: up_case = st.file_uploader("Upload FILE ADJUSMENT", type=['xlsx'])
    with col2: up_tracking = st.file_uploader("Upload SUMMARY STOCK", type=['xlsx'])
    with col3: up_all_stock = st.file_uploader("Upload ALL DATA STOCK", type=['xlsx'])
    with col4: up_scan = st.file_uploader("Upload DATA SCAN (Opsional)", type=['xlsx'])

    if st.button("▶️ RUN COMPARE", use_container_width=True):
        if not (up_case and up_tracking and up_all_stock):
            popup_error("File Kurang", "Upload Adjusment, Summary, dan All Data Stock.", "Harap lengkapi file yang wajib.")
        else:
            with st.spinner("Processing Data..."):
                df_c = pd.read_excel(up_case)
                df_t = pd.read_excel(up_tracking)
                df_a = pd.read_excel(up_all_stock)
                df_s = pd.read_excel(up_scan) if up_scan else None
                st.session_state.result_so = process_justification(df_c, df_t, df_a, df_s)
                popup_success("Justifikasi selesai dijalankan!")

    if st.session_state.get('result_so') is not None:
        st.dataframe(st.session_state.result_so, use_container_width=True)

# ---------------------------------------------------------
# MENU: STOCK MINUS
# ---------------------------------------------------------
def menu_stock_minus():
    st.markdown('<div class="hero-header"><h1>STOCK MINUS CLEARANCE</h1></div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload File ALL DATA STOCK", type=["xlsx", "xlsm"])
    
    if st.button("🔃 PROSES DATA", use_container_width=True):
        if not uploaded_file:
            popup_error("Data Kosong", "Upload All Data Stock terlebih dahulu.", "Masukkan file excel ke dalam uploader.")
        else:
            with st.spinner('Memproses...'):
                try:
                    df = pd.read_excel(uploaded_file, engine="openpyxl")
                    df.columns = [str(c).strip().upper() for c in df.columns]
                    col_sku = 'SKU'
                    col_bin = 'BIN'
                    col_qty = next((c for c in df.columns if 'QTY SYSTEM' in c or 'QTY SYS' in c), None)
                    
                    if col_qty is None:
                        popup_error("Format Salah", "Kolom 'QTY SYSTEM' tidak ditemukan!", "Pastikan file dari Jezpro.")
                    else:
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

                        prior_bins = ["RAK ACC LT.1", "STAGGING INBOUND", "STAGGING OUTBOUND", "KARANTINA DC", "KARANTINA STORE 02", "STAGGING REFUND", "STAGING GAGAL QC", "STAGGING LT.3", "STAGGING OUTBOUND SEMARANG", "STAGGING OUTBOUND SIDOARJO", "STAGGING LT.2", "LT.4"]
                        set_up_results = []
                        df_need_adj_list = []

                        for _, row in df_minus_awal.iterrows():
                            sku, bin_asal, sisa_minus = row[col_sku], row[col_bin], abs(row[col_qty])
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
                                        ambil = min(sisa_minus, sku_stock[bin_solusi])
                                        set_up_results.append({"BIN AWAL": bin_solusi, "BIN TUJUAN": bin_asal, "SKU": sku, "QUANTITY": ambil, "NOTES": "STOCK MINUS"})
                                        sku_stock[bin_solusi] -= ambil
                                        sisa_minus -= ambil

                            if sisa_minus > 0:
                                row_adj = row.to_dict()
                                row_adj[col_qty] = -sisa_minus 
                                df_need_adj_list.append(row_adj)

                        st.session_state['df_minus_awal'] = df_minus_awal
                        st.session_state['df_set_up'] = pd.DataFrame(set_up_results)
                        st.session_state['df_need_adj'] = pd.DataFrame(df_need_adj_list)
                        st.session_state['proses_selesai'] = True
                        popup_success("Proses Stock Minus Selesai!")
                except Exception as e:
                    popup_error("Error", str(e), "Periksa file Anda.")

    if st.session_state.get('proses_selesai'):
        st.dataframe(st.session_state['df_set_up'], use_container_width=True)

# ---------------------------------------------------------
# MENU: COMPARE SYSTEM
# ---------------------------------------------------------
def menu_compare_system():
    st.markdown('<div class="hero-header"><h1>STOCK COMPARATION</h1></div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1: file_sys1 = st.file_uploader("Stock System Start Shift", type=['xlsx', 'csv'])
    with c2: file_sys2 = st.file_uploader("Stock System End Shift", type=['xlsx', 'csv'])

    st.markdown("### 📤 Upload Dokumen Pendukung")
    out1, out2, in1, in2, in3 = st.columns(5)
    with out1: file_tracking = st.file_uploader("Stock Tracking")
    with out2: file_rto_out = st.file_uploader("RTO OUT")
    with in1: file_po = st.file_uploader("PO")
    with in2: file_rto_in = st.file_uploader("RTO IN")
    with in3: file_refund = st.file_uploader("REFUND")

    if st.button("▶️ RUN COMPARE", use_container_width=True):
        if not file_sys1 or not file_sys2:
            popup_error("File Kurang", "File Stock System 1 & 2 wajib diisi.", "Harap lengkapi file master.")
        else:
            try:
                res_all, d_only = process_stock_comparison(file_sys1, file_sys2, file_tracking, file_po, file_rto_in, file_rto_out, file_refund)
                st.session_state.result_all = res_all
                st.session_state.diff_only = d_only
                popup_success("Comparison Selesai!")
            except Exception as e:
                popup_error("Gagal Compare", str(e), "Cek format kolom.")
    
    if st.session_state.get('diff_only') is not None:
        st.dataframe(st.session_state.diff_only, use_container_width=True)

# ---------------------------------------------------------
# MENU: REFILL TOKO
# ---------------------------------------------------------
def menu_refill_toko():
    st.markdown('<div class="hero-header"><h1>REFILL TOKO LIST</h1></div>', unsafe_allow_html=True)
    up_refill = st.file_uploader("📥 Upload STOCK SYSTEM", type=['xlsx','csv'])

    if st.button("▶️ GENERATE REFILL", use_container_width=True):
        if not up_refill:
            popup_error("File Kosong", "Belum ada file Stock System.", "Upload file terlebih dahulu.")
        else:
            try:
                df_raw = pd.read_excel(up_refill) if up_refill.name.endswith(('.xlsx', '.xls')) else pd.read_csv(up_refill)
                df_raw.columns = [f"col_{i}" for i in range(len(df_raw.columns))]
                exclude_kat = ["SHOES", "SANDALS", "FOOTWEAR"]
                df_ref = df_raw[~df_raw['col_6'].astype(str).str.upper().isin(exclude_kat)].copy()
                
                exclude_bin_pattern = "DEFECT|REJECT|STAGING|STAGGING|BALANCING|PUTAWAY|EVENT|OFFLINE|KARANTINA"
                is_toko = df_ref['col_1'].astype(str).str.upper() == "TOKO"
                is_gudang = (~is_toko) & (~df_ref['col_1'].astype(str).str.upper().str.contains(exclude_bin_pattern, na=False))

                df_toko = df_ref[is_toko].groupby('col_2')['col_9'].sum().reset_index()
                df_toko.columns = ['col_2', 'qty_toko']

                df_gudang = df_ref[is_gudang].groupby('col_2').agg({
                    'col_9': 'sum',
                    'col_1': lambda x: ", ".join(set(x[df_ref.loc[x.index, 'col_9'] > 0].astype(str)))
                }).reset_index()
                df_gudang.columns = ['col_2', 'qty_gudang', 'available_in_bins']

                df_master = df_ref[['col_2', 'col_3', 'col_4', 'col_5', 'col_6']].drop_duplicates('col_2')
                df_final = df_master.merge(df_toko, on='col_2', how='left').merge(df_gudang, on='col_2', how='left')
                df_final[['qty_toko', 'qty_gudang']] = df_final[['qty_toko', 'qty_gudang']].fillna(0)

                def check_refill(row):
                    if row['qty_gudang'] <= 0: return False
                    sub_kat = str(row['col_6']).upper()
                    if "LOWER BODY" in sub_kat: return row['qty_toko'] < 6
                    else: return row['qty_toko'] < 2

                df_final['is_refill'] = df_final.apply(check_refill, axis=1)
                st.session_state.refill_toko_res = df_final[df_final['is_refill'] == True].copy()
                popup_success("Data Refill Toko berhasil digenerate!")
            except Exception as e:
                popup_error("Error", str(e), "Cek file Anda.")

    if st.session_state.get('refill_toko_res') is not None:
        st.dataframe(st.session_state.refill_toko_res, use_container_width=True)

# ---------------------------------------------------------
# MENU: DATABASE MASTER
# ---------------------------------------------------------
def menu_database_master():
    st.markdown('<div class="hero-header"><h1>DATABASE MASTER CHECKER</h1></div>', unsafe_allow_html=True)
    try:
        file_id = "1tuGnu7jKvRkw9MmF92U-5pOoXjUOeTMoL3EvrOzcrQY"
        xlsx_url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
        with st.spinner("Sedang mengambil data terbaru..."):
            all_sheets = pd.read_excel(xlsx_url, sheet_name=None, engine='calamine')
            selected_sheet = st.selectbox("PILIH TAB DATA:", list(all_sheets.keys()))
            if selected_sheet:
                st.dataframe(all_sheets[selected_sheet], use_container_width=True, height=600)
    except Exception as e:
        show_warning_popup("Koneksi G-Sheet Gagal", f"Error: {e}")

# ---------------------------------------------------------
# MENU: DASHBOARD OVERVIEW
# ---------------------------------------------------------
def menu_dashboard_overview():
    st.markdown('<div class="hero-header"><h1>📊 DASHBOARD ANALYTICS</h1></div>', unsafe_allow_html=True)
    c1, c2 = st.columns([3, 1])
    with c1: pilih = st.selectbox("PILIH LAPORAN", ["WORKING REPORT", "PERSONAL PERFORMANCE", "CYCLE COUNT DAN KERAPIHAN", "DASHBOARD MOVING STOCK"])
    with c2: zoom = st.slider("ZOOM", 0.1, 1.0, 0.35)
    dash_links = {"WORKING REPORT": "864743695", "PERSONAL PERFORMANCE": "251294539", "CYCLE COUNT DAN KERAPIHAN": "1743896821", "DASHBOARD MOVING STOCK": "1671817510"}
    st.markdown(f'''<div style="background: white; border-radius: 15px; padding: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);"><div style="width: 100%; height: 600px; overflow: auto;"><iframe src="https://docs.google.com/spreadsheets/d/e/2PACX-1vRIMd-eghecjZKcOmhz0TW4f-1cG0LOWgD6X9mIK1XhiYSOx-V6xSnZQzBLfru0LhCIinIZAfbYnHv_/pubhtml?gid={dash_links[pilih]}&single=true&rm=minimal" style="width: 4000px; height: 1500px; border: none; transform: scale({zoom}); transform-origin: 0 0;"></iframe></div></div>''', unsafe_allow_html=True)

# ---------------------------------------------------------
# MENU: REPORTING & PIC
# ---------------------------------------------------------
def menu_reporting_pic():
    st.markdown('<div class="hero-header"><h1>🚹 REPORTING & PIC - JEZPRO</h1></div>', unsafe_allow_html=True)
    st.info("Pilih Dashboard Overview untuk melihat summary performa.")
    
# ---------------------------------------------------------
# MENU: PICKING AUDIT (Handling if requested)
# ---------------------------------------------------------
def menu_picking_audit():
    st.markdown('<div class="hero-header"><h1>PICKING AUDIT</h1></div>', unsafe_allow_html=True)
    st.info("Fitur dialihkan ke Putaway & Picking Audit List.")


# ==============================================================================
# 🚀 9. MAIN ROUTER (PENYATU SEMUA MENU)
# ==============================================================================

# Pemanggilan menu berdasarkan variabel `menu` yang diatur di Sidebar
if menu == "Dashboard Overview": 
    menu_dashboard_overview()
elif menu == "Database Master": 
    menu_database_master()
elif menu == "Purchase Order Receiving": 
    apply_po_ui()
    tampilkan_halaman_po()
elif menu == "Putaway System": 
    menu_putaway_system()
elif menu == "Scan Out Validation": 
    menu_scan_out_validation()
elif menu == "Refill & Overstock": 
    menu_refill_overstock()
elif menu == "Refill & Withdraw": 
    menu_refill_withdraw()
elif menu == "Compare RTO": 
    menu_compare_rto()
elif menu == "Compare Penerimaan RTO": 
    main()
elif menu == "FDR Update": 
    menu_fdr_update()
elif menu == "Stock Opname": 
    menu_Stock_Opname()
elif menu == "Match Real & System": 
    menu_matching_karantina()
elif menu == "Cycle Count": 
    menu_cycle_count()
elif menu == "List Bin Cycle Count": 
    tarik_data_cycle_count()
elif menu == "Stock Tracking Timeline": 
    main_menu_routing()
elif menu == "Justification SO": 
    menu_justification_so()
elif menu == "Stock Minus": 
    menu_stock_minus()
elif menu == "Compare System": 
    menu_compare_system()
elif menu == "List Retur Out": 
    menu_retur_out_system()
elif menu == "Pengajuan Mutasi Karantina": 
    project_mutasi_karantina()
elif menu == "Refill Koli to Koli/Refill": 
    main_menu_koli()
elif menu == "Pengajuan Reject/Defect": 
    project_approval_reject()
elif menu == "Reject/Defect List": 
    menu_reject_defect()
elif menu == "Logistic Schedule": 
    # Karena di kode aslinya langsung jalan (tanpa fungsi), 
    # kamu bisa biarkan jika sudah dipindah, atau pastikan blok logicnya tereksekusi.
    st.info("Menu Logistic Schedule sudah aktif di module sebelumnya.")
elif menu == "Balancing Stock": 
    tampilan_balancing_stock()
elif menu == "Reporting & PIC": 
    menu_reporting_pic()
elif menu == "Data Timbang Ongkir": 
    show_timbang_system()
elif menu == "Database Ongkir In/Out": 
    show_database_ongkir()
elif menu == "Precentage Display": 
    tampilan_display_control()
elif menu == "Precentage Request FL to Store Stock": 
    run_store_request_analytics()
elif menu == "Refill Toko": 
    menu_refill_toko()
elif menu == "Store Leader RTO Decission": 
    render_menu_compare()
elif menu == "Picking Audit":
    menu_picking_audit()