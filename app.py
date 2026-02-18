import pandas as pd
import numpy as np
import io
import streamlit as st
import plotly.express as px
from python_calamine import CalamineWorkbook

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="ERP Surabaya - Pro", layout="wide")

# 2. CUSTOM CSS (KEMBALIKAN STYLE LO & FIX FONT)
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }
    [data-testid="stSidebar"] { background-color: #1e1e2f !important; }
    [data-testid="stSidebar"] * { color: white !important; }
    header[data-testid="stHeader"] { background-color: rgba(30, 30, 47, 0.85) !important; backdrop-filter: blur(12px); border-bottom: 2px solid #FFD700; }
    .m-box { background-color: #164e58; border: 1px solid #288494; padding: 10px; border-radius: 5px; text-align: center; color: white; margin-bottom: 10px; }
    .m-val { font-size: 1.2rem; font-weight: 800; color: #FFD700; display: block; }
    .m-lbl { font-size: 0.7rem; color: #8ecad4; text-transform: uppercase; }
    </style>
    """, unsafe_allow_html=True)

# 3. SIDEBAR
with st.sidebar:
    st.markdown("<h2>🚛 ERP SURABAYA</h2>", unsafe_allow_html=True)
    st.divider()
    menu = st.radio("MODUL UTAMA", ["📊 Dashboard Overview", "⛔ Stock Minus", "📦 Database Artikel"])

# --- MODUL DASHBOARD OVERVIEW ---
if menu == "📊 Dashboard Overview":
    st.markdown("<h2 style='text-align: center; color: #1e3a47;'>LOGISTIC OPERATION DASHBOARD</h2>", unsafe_allow_html=True)
    row1 = st.columns(6)
    metrics = [("KOLI RECEIVED", "5378 KOLI"), ("REFILL & WD", "31733 ITEMS"), ("STOCK MINUS", "1898 ITEMS"), ("LEAD TIME", "11 HOURS"), ("TOTAL REFILL", "4212 ITEMS"), ("WITHDRAW", "30 ITEMS")]
    for i, (lbl, val) in enumerate(metrics):
        row1[i].markdown(f'<div class="m-box"><span class="m-lbl">{lbl}</span><span class="m-val">{val}</span></div>', unsafe_allow_html=True)
    
    c_side, c_mid, c_right = st.columns([1, 2.5, 2])
    with c_side:
        st.markdown('<div class="m-box"><span class="m-lbl">TOTAL RTO</span><span class="m-val">1,614</span></div>', unsafe_allow_html=True)
        st.markdown('<div class="m-box"><span class="m-lbl">DIFF SMG</span><span class="m-val">9 (99%)</span></div>', unsafe_allow_html=True)
        st.markdown('<div class="m-box"><span class="m-lbl">DIFF SDA</span><span class="m-val">0 (100%)</span></div>', unsafe_allow_html=True)
    with c_mid:
        df_g = pd.DataFrame({'Cat': ['A', 'B', 'C', 'D'], 'Val': [2, 1, 3, 5]})
        st.plotly_chart(px.bar(df_g, x='Cat', y='Val', title="LEAD TIME GR BY CATEGORY", height=250), use_container_width=True)
    with c_right:
        st.subheader("🏆 PERSONNEL MVP")
        st.info("🏅 LOGISTIC: Yudi Sujud P.\n\n🏅 PICK: Reyvaldo Zakaria I.\n\n🏅 PACK: N. Hamzah")

# --- MODUL STOCK MINUS (FULL LOGIC BALIK!) ---
elif menu == "⛔ Stock Minus":
    st.title("⛔ Inventory : Stock Minus Clearance")
    uploaded_file = st.file_uploader("Upload File dari Jezpro", type=["xlsx", "xlsm"])

    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file, engine="calamine")
        col_sku, col_bin = 'SKU', 'BIN'
        col_qty = next((c for c in df.columns if 'QTY SYS' in str(c).upper()), 'QTY SYSTEM')

        if st.button("🚀 PROSES DATA SPEED DEMON"):
            with st.spinner('Sedang memproses...'):
                # 1. Backup Data Awal
                df_minus_awal = df[df[col_qty] < 0].copy()
                
                # 2. Setup Array (Speed Demon Logic)
                qty_arr = pd.to_numeric(df[col_qty], errors='coerce').fillna(0).values
                sku_arr, bin_arr = df[col_sku].astype(str).values, df[col_bin].astype(str).values
                
                # 3. Mapping posisi stok positif
                pos_map = {sku: [] for sku in np.unique(sku_arr)}
                for i, q in enumerate(qty_arr):
                    if q > 0: pos_map[sku_arr[i]].append(i)

                set_up_results = []
                minus_indices = np.where(qty_arr < 0)[0]
                
                # 4. Proses Relokasi
                for idx in minus_indices:
                    sku_target, qty_needed, bin_tujuan = sku_arr[idx], abs(qty_arr[idx]), bin_arr[idx]
                    if sku_target in pos_map:
                        for p_idx in pos_map[sku_target]:
                            if qty_needed <= 0: break
                            if qty_arr[p_idx] > 0:
                                take = min(qty_needed, qty_arr[p_idx])
                                qty_arr[p_idx] -= take
                                qty_arr[idx] += take
                                set_up_results.append({
                                    "BIN AWAL": bin_arr[p_idx], "BIN TUJUAN": bin_tujuan,
                                    "SKU": sku_target, "QUANTITY": take, "NOTES": "STOCK MINUS"
                                })
                                qty_needed -= take

                # 5. LOGIC NEED JUSTIFIKASI (Stok yang tetep minus setelah diproses)
                df_final_state = df.copy()
                df_final_state[col_qty] = qty_arr
                df_need_adj = df_final_state[df_final_state[col_qty] < 0].copy()

                # 6. Export ke Excel Multi-Sheet
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_minus_awal.to_excel(writer, sheet_name='STOCK MINUS AWAL', index=False)
                    if set_up_results:
                        pd.DataFrame(set_up_results).to_excel(writer, sheet_name='SET UP STOCK MINUS', index=False)
                    if not df_need_adj.empty:
                        df_need_adj.to_excel(writer, sheet_name='NEED JUSTIFIKASI', index=False)

                st.success(f"✅ Kelar! {len(set_up_results)} item direlokasi. {len(df_need_adj)} SKU butuh justifikasi.")
                st.download_button("📥 DOWNLOAD HASIL LENGKAP", data=output.getvalue(), file_name="PENYELESAIAN_STOCK_MINUS.xlsx")