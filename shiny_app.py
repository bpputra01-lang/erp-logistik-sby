import io
import re
import pandas as pd
from shiny import reactive, req
from shiny.express import input, render, ui

# ==========================================
# CONSTANTS & CONFIGURATION
# ==========================================
PRIOR_BINS = [
    "RAK ACC LT.1", "STAGGING INBOUND", "STAGGING OUTBOUND", "KARANTINA DC",
    "KARANTINA STORE 02", "STAGGING REFUND", "STAGING GAGAL QC", "STAGGING LT.3",
    "STAGGING OUTBOUND SEMARANG", "STAGGING OUTBOUND SIDOARJO", "STAGGING LT.2", "LT.4"
]

# ==========================================
# REACTIVE STATE MANAGEMENT
# ==========================================
logged_in = reactive.value(False)
role = reactive.value("toko")
branch = reactive.value("")
user_display_name = reactive.value("")

# Stock Minus Reactive State
stock_minus_processed = reactive.value(False)
total_qty_minus = reactive.value(0)
total_tercover = reactive.value(0)
total_sisa_adj = reactive.value(0)
df_minus_awal = reactive.value(pd.DataFrame())
df_set_up = reactive.value(pd.DataFrame())
df_need_adj = reactive.value(pd.DataFrame())

# Putaway Reactive State
putaway_processed = reactive.value(False)
putaway_qty_system = reactive.value(0)
putaway_total_setup = reactive.value(0)
putaway_kurang_setup = reactive.value(0)
df_comp = reactive.value(pd.DataFrame())
df_plist = reactive.value(pd.DataFrame())
df_kurang = reactive.value(pd.DataFrame())

# ==========================================
# GLOBAL STYLING & CSS CUSTOM
# ==========================================
ui.tags.style("""
    * { box-sizing: border-box !important; }
    body, html {
        height: 100vh; margin: 0; padding: 0;
        background-color: #0f172a; color: #f8fafc;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    .bg-login {
        background: radial-gradient(circle at 50% 50%, #1e293b 0%, #0f172a 100%);
        min-height: 100vh;
    }
    .login-container {
        display: flex; justify-content: center; align-items: center;
        min-height: 100vh; width: 100%; padding: 1.5rem;
    }
    .login-card {
        width: 100%; max-width: 450px; padding: 2.5rem 2rem;
        background: rgba(15, 23, 42, 0.95) !important;
        border-radius: 16px; border: 1px solid rgba(255, 255, 255, 0.1);
        border-left: 5px solid #E50914 !important;
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.7);
    }
    .custom-field {
        width: 100% !important; background: #020617 !important;
        border: 1px solid rgba(229, 9, 20, 0.4) !important; color: #FFFFFF !important;
        border-radius: 8px !important; padding: 0 1rem !important;
        height: 46px !important; font-size: 0.95rem !important; outline: none !important;
    }
    .custom-field:focus {
        border-color: #E50914 !important;
        box-shadow: 0 0 10px rgba(229, 9, 20, 0.5) !important;
    }
    .btn-login {
        background: linear-gradient(135deg, #E50914 0%, #B20710 100%) !important;
        color: #FFFFFF !important; font-weight: 800 !important;
        border-radius: 8px !important; cursor: pointer !important;
        height: 48px !important; width: 100% !important; border: none !important;
        letter-spacing: 1px; font-size: 0.95rem !important; margin-top: 0.5rem;
    }
    .btn-login:hover { opacity: 0.95; transform: translateY(-1px); }
    .metric-box { padding: 15px; border-radius: 8px; background: #1e293b; text-align: center; border: 1px solid #334155; }
    .metric-val { font-size: 24px; font-weight: bold; }
""")

# ==========================================
# AUTH HANDLERS & ROUTER
# ==========================================

# Handler Login
@reactive.effect
@reactive.event(input.btn_login, ignore_none=True)
def _login():
    u = input.login_user().strip() if input.login_user() else ""
    p = input.login_pass().strip() if input.login_pass() else ""
    
    if u == "admin" and p == "sby123":
        logged_in.set(True)
        role.set("DC")
        branch.set("SURABAYA")
        user_display_name.set("Admin DC Surabaya")
        ui.notification_show("Berhasil Login sebagai Admin DC!", type="message")
    elif u == "toko" and p == "toko123":
        logged_in.set(True)
        role.set("CABANG")
        branch.set("SURABAYA")
        user_display_name.set("User Cabang")
        ui.notification_show("Berhasil Login sebagai User Cabang!", type="message")
    elif u != "" or p != "":
        ui.notification_show("❌ Username atau Password Salah!", type="error")

# Handler Logout
@reactive.effect
@reactive.event(input.btn_logout, ignore_none=True)
def _logout():
    logged_in.set(False)
    role.set("toko")
    user_display_name.set("")

# Top Header Bar
@render.ui
def header_auth():
    if not logged_in.get():
        return ui.div()
    return ui.div(
        ui.span(f"👤 {user_display_name.get()} ({role.get()})", style="font-weight: bold; margin-right: 15px;"),
        ui.input_action_button("btn_logout", "Logout", class_="btn-danger btn-sm"),
        style="display: flex; justify-content: flex-end; align-items: center; padding: 15px 25px; background: #1e293b; border-bottom: 1px solid #334155;"
    )

# Main UI Router
@render.ui
def main_app():
    if not logged_in.get():
        return ui.div(
            ui.div(
                ui.div(
                    # Header Card
                    ui.div(
                        ui.div(style="width: 10px; height: 38px; background: #E50914; border-radius: 3px; flex-shrink: 0;"),
                        ui.div(
                            ui.div("LOGISTIC DISTRIBUTION", style="font-size: 1.2rem; font-weight: 800; color: #FFFFFF; letter-spacing: 1px; line-height: 1.2;"),
                            ui.div("CENTER WAREHOUSE • SURABAYA", style="font-size: 0.72rem; font-weight: 700; color: #E50914; letter-spacing: 2px; margin-top: 2px;"),
                        ),
                        style="display: flex; align-items: center; gap: 14px; margin-bottom: 1.5rem;"
                    ),
                    ui.hr(style="border-color: rgba(255, 255, 255, 0.1); margin: 1rem 0 1.2rem 0;"),
                    ui.div("Silakan masuk dengan akun resmi gudang Anda.", style="color: #B0B0B0; font-size: 0.85rem; margin-bottom: 1.5rem;"),

                    # Field Input Username
                    ui.div(
                        ui.div("USERNAME", style="font-size: 0.72rem; font-weight: 700; color: #FFFFFF; letter-spacing: 1px; margin-bottom: 0.4rem;"),
                        ui.input_text("login_user", "", placeholder="Masukkan username...", class_="custom-field"),
                        style="margin-bottom: 1.2rem; width: 100%;"
                    ),

                    # Field Input Password
                    ui.div(
                        ui.div("PASSWORD", style="font-size: 0.72rem; font-weight: 700; color: #FFFFFF; letter-spacing: 1px; margin-bottom: 0.4rem;"),
                        ui.input_password("login_pass", "", placeholder="Masukkan password...", class_="custom-field"),
                        style="margin-bottom: 1.6rem; width: 100%;"
                    ),

                    # Tombol Submit Login
                    ui.input_action_button("btn_login", "SIGN IN TO SYSTEM →", class_="btn-login"),
                    ui.div("🟢 Warehouse Supporting Tools v2.0", style="text-align: center; color: #888888; font-size: 0.75rem; margin-top: 1.6rem;"),
                    
                    class_="login-card"
                ),
                class_="login-container"
            ),
            class_="bg-login"
        )
    
    # Dashboard Utama Setelah Login
    tabs = ["📦 Putaway System", "⚠️ Stock Minus"]
    if role.get() == "DC":
        tabs = ["🚚 Database Ongkir In/Out", "📦 Putaway System", "⚠️ Stock Minus", "🚫 Reject / Defect", "📊 Reporting & PIC"]
        
    return ui.div(
        ui.navset_card_tab(
            *[ui.nav_panel(title, render_tab_content(title)) for title in tabs]
        ),
        style="padding: 20px;"
    )

def render_tab_content(tab_name):
    if "Stock Minus" in tab_name:
        return ui.div(
            ui.h3("⚙️ STOCK MINUS SYSTEM"),
            ui.input_file("file_stock_minus", "Upload File Stock Opname (Excel/CSV)", accept=[".xlsx", ".xls", ".csv"]),
            ui.output_ui("ui_stock_minus_results")
        )
    elif "Putaway System" in tab_name:
        return ui.div(
            ui.h3("📦 PUTAWAY SYSTEM"),
            ui.input_select("area_putaway", "Pilih Area Putaway", ["DC LANTAI 1", "DC LANTAI 2", "DC LANTAI 3", "JERSEY ZONE", "ALL AREA"]),
            ui.input_file("file_ds", "Upload File Draft Store / Target Putaway", accept=[".xlsx", ".csv"]),
            ui.input_file("file_asal", "Upload File Stok Asal (System/SO)", accept=[".xlsx", ".csv"]),
            ui.input_action_button("btn_process_putaway", "Proses Compare Putaway", class_="btn-success mt-2"),
            ui.output_ui("ui_putaway_results")
        )
    else:
        return ui.div(ui.p(f"Menu {tab_name} aktif dan siap digunakan."))

# ==========================================
# BUSINESS LOGIC (PROCESSORS)
# ==========================================

# PROCESS STOCK MINUS
@reactive.effect
@reactive.event(input.file_stock_minus, ignore_none=True)
def _process_stock_minus():
    file_info = input.file_stock_minus()
    if not file_info: return
    
    path = file_info[0]["datapath"]
    df = pd.read_excel(path) if path.endswith(('.xlsx', '.xls')) else pd.read_csv(path)
    df.columns = [str(c).strip().upper() for c in df.columns]
    
    col_sku, col_bin = 'SKU', 'BIN'
    col_qty = next((c for c in df.columns if 'QTY SYSTEM' in c or 'QTY SYS' in c or 'QTY' in c), None)
    
    if not col_qty:
        ui.notification_show("❌ Kolom 'QTY SYSTEM' tidak ditemukan!", type="error")
        return

    df[col_qty] = pd.to_numeric(df[col_qty], errors='coerce').fillna(0)
    df[col_sku] = df[col_sku].astype(str).str.strip().str.upper()
    df[col_bin] = df[col_bin].astype(str).str.strip().str.upper()
    
    df_minus = df[df[col_qty] < 0].copy()
    df_pos = df[df[col_qty] > 0].copy()
    
    inventory = {}
    for _, row in df_pos.iterrows():
        s, b, q = row[col_sku], row[col_bin], row[col_qty]
        if s not in inventory: inventory[s] = {}
        inventory[s][b] = inventory[s].get(b, 0) + q
        
    set_up_results, need_adj_list = [], []
    
    for _, row in df_minus.iterrows():
        sku, bin_asal = row[col_sku], row[col_bin]
        sisa_minus = abs(row[col_qty])
        
        if sku in inventory:
            sku_stock = inventory[sku]
            while sisa_minus > 0:
                bin_solusi = None
                if bin_asal == "TOKO":
                    if sku_stock.get("STAGGING LT.2", 0) > 0: bin_solusi = "STAGGING LT.2"
                    elif sku_stock.get("LT.2", 0) > 0: bin_solusi = "LT.2"
                elif bin_asal in ["STAGGING LT.2", "LT.2"] and sku_stock.get("TOKO", 0) > 0:
                    bin_solusi = "TOKO"
                    
                if not bin_solusi:
                    for b in PRIOR_BINS:
                        if sku_stock.get(b, 0) > 0:
                            bin_solusi = b
                            break
                            
                if not bin_solusi:
                    for b, qty_b in sku_stock.items():
                        if b != "REJECT DEFECT" and qty_b > 0:
                            bin_solusi = b
                            break
                            
                if not bin_solusi: break
                    
                qty_avail = sku_stock[bin_solusi]
                ambil = min(sisa_minus, qty_avail)
                
                set_up_results.append({
                    'BIN_AWAL': bin_solusi, 'BIN_TUJUAN': bin_asal,
                    'SKU': sku, 'QUANTITY': ambil, 'NOTES': 'STOCK MINUS'
                })
                
                sku_stock[bin_solusi] -= ambil
                sisa_minus -= ambil
                
        if sisa_minus > 0:
            row_adj = row.to_dict()
            row_adj[col_qty] = -sisa_minus
            need_adj_list.append(row_adj)
            
    res_setup = pd.DataFrame(set_up_results)
    res_adj = pd.DataFrame(need_adj_list)
    
    total_qty_minus.set(abs(df_minus[col_qty].sum()))
    total_tercover.set(res_setup['QUANTITY'].sum() if not res_setup.empty else 0)
    total_sisa_adj.set(abs(res_adj[col_qty].sum()) if not res_adj.empty else 0)
    
    df_set_up.set(res_setup)
    stock_minus_processed.set(True)
    ui.notification_show("🚀 Proses Stock Minus Selesai!", type="message")

@render.ui
def ui_stock_minus_results():
    if not stock_minus_processed.get(): return ui.div()
    return ui.div(
        ui.hr(),
        ui.row(
            ui.column(4, ui.div(ui.div("Total Qty Minus Awal", class_="text-muted"), ui.div(f"{total_qty_minus.get():,}", class_="metric-val text-danger"), class_="metric-box")),
            ui.column(4, ui.div(ui.div("Total Ter-cover Set Up", class_="text-muted"), ui.div(f"{total_tercover.get():,}", class_="metric-val text-success"), class_="metric-box")),
            ui.column(4, ui.div(ui.div("Sisa Qty (Need Adj)", class_="text-muted"), ui.div(f"{total_sisa_adj.get():,}", class_="metric-val text-warning"), class_="metric-box")),
        ),
        ui.hr(),
        ui.h5("Preview Template Set Up:"),
        render.data_frame(render.DataGrid(df_set_up.get().head(10)))
    )

# PROCESS PUTAWAY
@reactive.effect
@reactive.event(input.btn_process_putaway, ignore_none=True)
def _process_putaway():
    f_ds, f_asal = input.file_ds(), input.file_asal()
    if not f_ds or not f_asal:
        ui.notification_show("⚠️ Mohon upload kedua file terlebih dahulu!", type="warning")
        return
        
    df_ds = pd.read_excel(f_ds[0]["datapath"]) if f_ds[0]["datapath"].endswith(('.xlsx', '.xls')) else pd.read_csv(f_ds[0]["datapath"])
    df_asal = pd.read_excel(f_asal[0]["datapath"]) if f_asal[0]["datapath"].endswith(('.xlsx', '.xls')) else pd.read_csv(f_asal[0]["datapath"])
    
    df_ds.columns = [str(c).strip().upper() for c in df_ds.columns]
    df_asal.columns = [str(c).strip().upper() for c in df_asal.columns]
    
    c_bin_a = next((c for c in df_asal.columns if 'BIN' in c or 'LOKASI' in c), df_asal.columns[0])
    c_sku_a = next((c for c in df_asal.columns if 'SKU' in c or 'ITEM' in c), df_asal.columns[1])
    c_qty_a = next((c for c in df_asal.columns if 'QTY SYSTEM' in c or 'QTY' in c or 'STOK' in c), df_asal.columns[-1])
    
    c_bin_d = next((c for c in df_ds.columns if 'BIN' in c or 'TUJUAN' in c), df_ds.columns[0])
    c_sku_d = next((c for c in df_ds.columns if 'SKU' in c or 'ITEM' in c), df_ds.columns[1])
    c_qty_d = next((c for c in df_ds.columns if 'QTY' in c or 'JUMLAH' in c), df_ds.columns[2])
    
    df_asal[c_qty_a] = pd.to_numeric(df_asal[c_qty_a], errors='coerce').fillna(0)
    putaway_qty_system.set(df_asal[c_qty_a].sum())
    
    bin_qty_dict = {}
    for _, r in df_asal.iterrows():
        key = f"{r[c_bin_a]}|{r[c_sku_a]}"
        bin_qty_dict[key] = bin_qty_dict.get(key, 0) + r[c_qty_a]
        
    out_data = []
    for _, r in df_ds.iterrows():
        sku = str(r[c_sku_d])
        diff_qty = float(r[c_qty_d]) if pd.notnull(r[c_qty_d]) else 0
        if diff_qty <= 0: continue
        
        bin_tujuan = str(r[c_bin_d])
        rem = diff_qty
        
        patterns = ["STAGING LT.3", "STAGGING LT.3", "STAGING", "STAGGING", "KARANTINA", "NORMAL"]
        for ptn in patterns:
            if rem <= 0: break
            for k, qty_avail in list(bin_qty_dict.items()):
                if qty_avail <= 0: continue
                b_name, s_name = k.split("|")
                if s_name != sku: continue
                
                match = False
                if ptn == "NORMAL":
                    if not re.search(r'STAG|KARANTINA', b_name, re.IGNORECASE): match = True
                else:
                    if re.search(ptn, b_name, re.IGNORECASE): match = True
                    
                if match:
                    take = min(rem, qty_avail)
                    bin_qty_dict[k] -= take
                    rem -= take
                    out_data.append({
                        'BIN_ASAL': bin_tujuan, 'SKU': sku, 'QTY_PUTAWAY': diff_qty,
                        'BIN_DITEMUKAN': b_name, 'QUANTITY': take, 'DIFF': rem,
                        'STATUS': 'FULLY SETUP' if rem == 0 else 'PARTIAL SETUP'
                    })
                    if rem <= 0: break
                    
        if rem > 0:
            out_data.append({
                'BIN_ASAL': bin_tujuan, 'SKU': sku, 'QTY_PUTAWAY': diff_qty,
                'BIN_DITEMUKAN': '(NO BIN)', 'QUANTITY': 0, 'DIFF': rem,
                'STATUS': 'PERLU CARI STOCK MANUAL'
            })
            
    res_comp = pd.DataFrame(out_data)
    res_plist = res_comp[res_comp['STATUS'].str.contains('SETUP', na=False)].rename(columns={'BIN_DITEMUKAN':'BIN_AWAL', 'BIN_ASAL':'BIN_TUJUAN'})
    if not res_plist.empty: res_plist['NOTES'] = 'PUTAWAY'
    res_kurang = res_comp[res_comp['STATUS'] == 'PERLU CARI STOCK MANUAL']
    
    putaway_total_setup.set(res_plist['QUANTITY'].sum() if not res_plist.empty else 0)
    putaway_kurang_setup.set(res_kurang['DIFF'].sum() if not res_kurang.empty else 0)
    
    df_plist.set(res_plist)
    putaway_processed.set(True)
    ui.notification_show("✅ System Compare Putaway Selesai!", type="message")

@render.ui
def ui_putaway_results():
    if not putaway_processed.get(): return ui.div()
    return ui.div(
        ui.hr(),
        ui.row(
            ui.column(4, ui.div(ui.div("Total Qty System", class_="text-muted"), ui.div(f"{putaway_qty_system.get():,}", class_="metric-val text-info"), class_="metric-box")),
            ui.column(4, ui.div(ui.div("Total Putaway Setup", class_="text-muted"), ui.div(f"{putaway_total_setup.get():,}", class_="metric-val text-success"), class_="metric-box")),
            ui.column(4, ui.div(ui.div("Kurang Setup (Manual)", class_="text-muted"), ui.div(f"{putaway_kurang_setup.get():,}", class_="metric-val text-danger"), class_="metric-box")),
        ),
        ui.hr(),
        ui.h5("Preview Putaway List:"),
        render.data_frame(render.DataGrid(df_plist.get().head(10)))
    )