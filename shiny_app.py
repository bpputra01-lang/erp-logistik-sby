import io
import time
import pandas as pd
from datetime import datetime
from supabase import create_client, Client
from shiny import App, Inputs, Outputs, Session, reactive, render, ui

# ==========================================
# 1. KONFIGURASI SUPABASE
# ==========================================
SUPABASE_URL = "https://ufhjrsxzcffdfswfqlzk.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVmaGpyc3h6Y2ZmZGZzd2ZxbHprIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYxNTI5NjgsImV4cCI6MjA5MTcyODk2OH0.DDlKkXU5-nVvNYK_uLYzXLgaj8oDT4s8vbjAoWMWacI"

def get_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

# ==========================================
# 2. CSS & JAVASCRIPT ASSETS
# ==========================================
CUSTOM_HEAD = ui.tags.head(
    ui.tags.link(rel="stylesheet", href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"),
    ui.tags.style("""
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
        body, html { height: 100%; width: 100%; overflow-x: hidden; background-color: #F7FAFC; }
        
        @keyframes blinkAnimation {
            0% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.3; transform: scale(0.8); }
            100% { opacity: 1; transform: scale(1); }
        }
        .blink-online { animation: blinkAnimation 1.5s infinite ease-in-out; }
        
        @keyframes popIn {
            0% { transform: scale(0.5); opacity: 0; }
            70% { transform: scale(1.15); opacity: 1; }
            100% { transform: scale(1); opacity: 1; }
        }
        .animate-pop { animation: popIn 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards; }
        
        /* Custom Input Styles */
        .form-input-dark {
            background-color: #FFFFFF !important;
            color: #111111 !important;
            border: 2px solid #4A5568 !important;
            border-radius: 8px !important;
            font-weight: 600;
            padding: 8px 12px;
            width: 100%;
        }
        .form-input-dark:focus {
            border: 2px solid #E50914 !important;
            box-shadow: 0 0 0 1px #E50914 !important;
            outline: none !important;
        }
        
        /* Table Styles */
        .custom-clean-table { width: 100%; border-collapse: collapse; font-size: 13px; text-align: left; }
        .custom-clean-table th { background: #EDF2F7; color: #1A202C; font-weight: bold; font-size: 12px; padding: 10px; white-space: nowrap; border-bottom: 1px solid #E2E8F0; }
        .custom-clean-table td { color: #2D3748; padding: 8px 10px; white-space: nowrap; border-bottom: 1px solid #EDF2F7; }
        .custom-clean-table tr:hover { background-color: #F8FAFC; }
        
        /* Red Button Gradient */
        .btn-red-gradient {
            background: linear-gradient(135deg, #E50914 0%, #B20710 100%) !important;
            color: #FFFFFF !important;
            font-weight: 800 !important;
            border-radius: 8px !important;
            border: none !important;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(229, 9, 20, 0.3);
            transition: all 0.2s ease;
        }
        .btn-red-gradient:hover {
            box-shadow: 0 6px 20px rgba(229, 9, 20, 0.5);
            filter: brightness(1.1);
        }
        
        /* Sidebar active */
        .sidebar-btn-active {
            background: linear-gradient(135deg, #E50914 0%, #B20710 100%) !important;
            color: #FFFFFF !important;
            font-weight: 700 !important;
            box-shadow: 0 4px 12px rgba(229, 9, 20, 0.4) !important;
        }
    """),
    ui.tags.script("""
        setInterval(function() {
            let elStore = document.getElementById('login-time-store');
            let elTimer = document.getElementById('live-timer');
            if (elStore && elTimer) {
                let loginTime = parseInt(elStore.innerText);
                if (loginTime && loginTime > 0) {
                    let now = new Date().getTime();
                    let diff = Math.floor((now - loginTime) / 1000);
                    let h = String(Math.floor(diff / 3600)).padStart(2, '0');
                    let m = String(Math.floor((diff % 3600) / 60)).padStart(2, '0');
                    let s = String(diff % 60).padStart(2, '0');
                    elTimer.innerText = h + ':' + m + ':' + s;
                } else {
                    elTimer.innerText = "00:00:00";
                }
            }
        }, 1000);
    """)
)

# ==========================================
# 3. KOMPONEN UI HELPER
# ==========================================
def metric_box(title: str, val_ui, text_color: str, bg_gradient: str):
    return ui.div(
        ui.div(title, style="color: #4A5568; font-size: 11px; font-weight: 800; text-transform: uppercase; margin-bottom: 4px;"),
        ui.div(val_ui, style=f"color: {text_color}; font-size: 20px; font-weight: 800;"),
        style=f"background: {bg_gradient}; padding: 1rem; border-radius: 12px; border: 1px solid rgba(0,0,0,0.06); text-align: center; width: 100%; box-shadow: 0 2px 6px rgba(0,0,0,0.03);"
    )

def render_table_from_df(df: pd.DataFrame):
    if df.empty:
        return ui.div(
            ui.div("Tidak ada data untuk ditampilkan.", style="color: #718096; padding: 1.5rem; font-style: italic; text-align: center;"),
            style="background: white; border-radius: 8px; border: 1px solid #E2E8F0; width: 100%;"
        )
    
    headers = [ui.tags.th(col) for col in df.columns]
    rows = []
    for _, row in df.iterrows():
        cells = [ui.tags.td(str(val)) for val in row]
        rows.append(ui.tags.tr(*cells))
        
    return ui.div(
        ui.tags.table(
            ui.tags.thead(ui.tags.tr(*headers)),
            ui.tags.tbody(*rows),
            class_="custom-clean-table"
        ),
        style="overflow-x: auto; width: 100%; background: white; border-radius: 8px; padding: 0.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05); border: 1px solid #E2E8F0;"
    )

# ==========================================
# 4. VIEW HALAMAN LOGIN
# ==========================================
def login_view():
    return ui.div(
        ui.div(
            ui.div(
                ui.div(
                    ui.div(style="width: 12px; height: 38px; background: #E50914; border-radius: 4px; margin-right: 12px;"),
                    ui.div(
                        ui.h2("LOGISTIC DISTRIBUTION", style="color: #FFFFFF; font-size: 22px; font-weight: 800; letter-spacing: 1px; margin: 0; line-height: 1.1;"),
                        ui.span("CENTER WAREHOUSE • SURABAYA", style="color: #E50914; font-size: 11px; font-weight: 700; letter-spacing: 2px;"),
                        style="display: flex; flex-direction: column;"
                    ),
                    style="display: flex; align-items: center; margin-bottom: 1.25rem;"
                ),
                ui.hr(style="border-color: rgba(255, 255, 255, 0.1); margin-bottom: 1.25rem;"),
                ui.p("Silakan masuk dengan akun resmi gudang Anda.", style="color: #B0B0B0; font-size: 13px; margin-bottom: 1.5rem;"),
                
                ui.div(
                    ui.span("USERNAME", style="font-size: 11px; font-weight: 700; color: #FFFFFF; letter-spacing: 1px; margin-bottom: 4px; display: block;"),
                    ui.input_text("login_username", "", placeholder="Masukkan username...", width="100%"),
                    style="margin-bottom: 1rem;"
                ),
                
                ui.div(
                    ui.span("PASSWORD", style="font-size: 11px; font-weight: 700; color: #FFFFFF; letter-spacing: 1px; margin-bottom: 4px; display: block;"),
                    ui.input_password("login_password", "", placeholder="Masukkan password...", width="100%"),
                    style="margin-bottom: 1.5rem;"
                ),
                
                ui.input_action_button(
                    "btn_login", "SIGN IN TO SYSTEM →",
                    class_="btn-red-gradient",
                    style="width: 100%; height: 48px; font-size: 14px; margin-bottom: 1.25rem;"
                ),
                
                ui.div(
                    "🟢 Warehouse Supporting Tools v2.0",
                    style="color: #888888; font-size: 12px; text-align: center;"
                ),
                style="width: 100%;"
            ),
            style="""
                width: 100%; max-width: 520px; padding: 3rem 2.5rem;
                background: rgba(12, 12, 15, 0.88); backdrop-filter: blur(20px);
                border-radius: 20px; border: 1px solid rgba(255, 255, 255, 0.12);
                border-left: 5px solid #E50914; box-shadow: 0 25px 60px rgba(0, 0, 0, 0.85);
            """
        ),
        style="""
            background-image: radial-gradient(circle at center, rgba(0, 0, 0, 0.15) 0%, rgba(0, 0, 0, 0.45) 100%), url('https://images.unsplash.com/photo-1553413077-190dd305871c?q=80&w=2070');
            background-size: cover; background-position: center; background-repeat: no-repeat;
            width: 100vw; height: 100vh; display: flex; align-items: center; justify-content: center; padding: 2rem;
        """
    )

# ==========================================
# 5. VIEW STOCK MINUS
# ==========================================
def stock_minus_view():
    return ui.div(
        # Upload box
        ui.div(
            ui.span("Upload File STOCK MINUS", style="font-weight: bold; color: #1A202C; font-size: 14px; margin-bottom: 0.5rem; display: block;"),
            ui.div(
                ui.input_file("upload_stock_file", None, accept=[".xlsx", ".xls", ".csv"], multiple=False, button_label="Upload", placeholder="200MB per file • XLSX, XLS"),
                style="padding: 1.5rem; border: 2px dashed #CBD5E0; border-radius: 8px; background: #F8FAFC; width: 100%;"
            ),
            ui.div(
                ui.input_action_button("btn_process_stock", "▶ PROSES DATA", class_="btn-red-gradient", style="padding: 0.75rem 1.5rem;"),
                style="display: flex; justify-content: flex-end; width: 100%; margin-top: 1rem;"
            ),
            style="width: 100%; background: white; padding: 1.25rem; border-radius: 10px; border: 1px solid #E2E8F0; margin-bottom: 1.25rem;"
        ),
        
        # Results area
        ui.output_ui("stock_minus_results_ui"),
        style="width: 100%; padding: 1rem;"
    )

# ==========================================
# 6. VIEW PUTAWAY SYSTEM
# ==========================================
def putaway_view():
    return ui.div(
        ui.div(
            ui.span("📍 Pilih Area Putaway", style="font-weight: bold; color: #1A202C; font-size: 14px; margin-bottom: 0.5rem; display: block;"),
            ui.input_select(
                "area_putaway", None,
                {"": "-- Pilih Area Putaway --", "DC LANTAI 1": "DC LANTAI 1", "DC LANTAI 2": "DC LANTAI 2", "DC LANTAI 3": "DC LANTAI 3", "JERSEY ZONE": "JERSEY ZONE"},
                selected="",
                width="100%"
            ),
            ui.output_ui("putaway_content_after_area"),
            style="width: 100%; background: white; padding: 1.25rem; border-radius: 10px; border: 1px solid #E2E8F0; margin-bottom: 1.25rem;"
        ),
        ui.output_ui("putaway_results_ui"),
        style="width: 100%; padding: 1rem;"
    )

# ==========================================
# 7. VIEW DATABASE ONGKIR (MAIN DASHBOARD)
# ==========================================
def main_dashboard_view():
    return ui.div(
        ui.navset_card_tab(
            ui.nav_panel(
                "📥 INPUT & BATCH DATA",
                ui.div(
                    # Left: Manual Form
                    ui.div(
                        ui.div(
                            ui.span("📝", style="font-size: 20px; margin-right: 8px;"),
                            ui.span("Input Transaksi Manual", style="font-size: 16px; font-weight: bold; color: #1A202C;"),
                            style="display: flex; align-items: center; margin-bottom: 0.75rem;"
                        ),
                        ui.hr(style="border-color: #CBD5E0; margin-bottom: 1rem;"),
                        ui.div(
                            ui.span("NAMA SUPPLIER", style="font-size: 11px; font-weight: 800; color: #1A202C;"),
                            ui.input_text("input_supplier", "", placeholder="Masukkan Nama Supplier...", width="100%"),
                            style="margin-bottom: 0.75rem;"
                        ),
                        ui.div(
                            ui.div(
                                ui.span("EKSPEDISI", style="font-size: 11px; font-weight: 800; color: #1A202C;"),
                                ui.input_text("input_ekspedisi", "", placeholder="Nama Ekspedisi...", width="100%"),
                                style="flex: 1; margin-right: 8px;"
                            ),
                            ui.div(
                                ui.span("TOTAL KOLI", style="font-size: 11px; font-weight: 800; color: #1A202C;"),
                                ui.input_numeric("input_koli", "", value=0, min=0, width="100%"),
                                style="flex: 1;"
                            ),
                            style="display: flex; width: 100%; margin-bottom: 0.75rem;"
                        ),
                        ui.div(
                            ui.div(
                                ui.span("TOTAL ONGKIR (RP)", style="font-size: 11px; font-weight: 800; color: #1A202C;"),
                                ui.input_numeric("input_ongkir", "", value=0, min=0, width="100%"),
                                style="flex: 1; margin-right: 8px;"
                            ),
                            ui.div(
                                ui.span("TANGGAL", style="font-size: 11px; font-weight: 800; color: #1A202C;"),
                                ui.input_date("input_tgl", "", value=datetime.now().strftime("%Y-%m-%d"), width="100%"),
                                style="flex: 1;"
                            ),
                            style="display: flex; width: 100%; margin-bottom: 1rem;"
                        ),
                        ui.input_action_button(
                            "btn_save_ongkir", "🚀 SIMPAN DATA ONGKIR",
                            class_="btn-red-gradient",
                            style="width: 100%; height: 44px;"
                        ),
                        style="background: #FFFFFF; border-radius: 16px; border: 2px solid #CBD5E0; padding: 1.8rem; flex: 1; margin-right: 1rem;"
                    ),
                    # Right: Batch CSV Upload
                    ui.div(
                        ui.div(
                            ui.span("📁", style="font-size: 20px; margin-right: 8px;"),
                            ui.span("Batch CSV Upload", style="font-size: 16px; font-weight: bold; color: #1A202C;"),
                            style="display: flex; align-items: center; margin-bottom: 0.75rem;"
                        ),
                        ui.hr(style="border-color: #CBD5E0; margin-bottom: 1rem;"),
                        ui.div(
                            ui.input_file("upload_csv_batch", None, accept=[".csv"], multiple=False, button_label="Pilih File CSV", placeholder="tarik & lepaskan file CSV di sini"),
                            style="border: 2px dashed #E50914; padding: 2rem; border-radius: 12px; background: #FFF5F5; text-align: center; margin-bottom: 1.25rem;"
                        ),
                        ui.input_action_button(
                            "btn_execute_batch", "⚡ EXECUTE BATCH UPLOAD",
                            style="background: #1A202C; color: #FFFFFF; font-weight: 800; border-radius: 10px; width: 100%; height: 44px; border: none; cursor: pointer;"
                        ),
                        style="background: #FFFFFF; border-radius: 16px; border: 2px solid #CBD5E0; padding: 1.8rem; flex: 1;"
                    ),
                    style="display: flex; flex-wrap: wrap; margin-top: 1rem; gap: 1rem;"
                )
            ),
            ui.nav_panel(
                "📊 SUMMARY & HISTORY",
                ui.div(
                    # Ekspedisi filter & delete action
                    ui.div(
                        ui.div(
                            ui.span("FILTER EKSPEDISI:", style="font-size: 12px; font-weight: 800; color: #111111; margin-right: 8px;"),
                            ui.input_select("filter_ekspedisi", None, ["ALL"], selected="ALL", width="220px"),
                            style="display: flex; align-items: center;"
                        ),
                        ui.output_ui("delete_btn_ui"),
                        style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin: 1.25rem 0 1rem 0;"
                    ),
                    # Metric Cards Grid
                    ui.div(
                        metric_box("💰 BIAYA ALL", ui.output_text("val_biaya_all"), "#C53030", "linear-gradient(135deg, #FED7D7 0%, #FEB2B2 100%)"),
                        metric_box("📦 KOLI ALL", ui.output_text("val_koli_all"), "#1A202C", "linear-gradient(135deg, #E2E8F0 0%, #CBD5E0 100%)"),
                        metric_box("📊 AVG COST ALL", ui.output_text("val_avg_cost_all"), "#C53030", "linear-gradient(135deg, #FED7D7 0%, #FEB2B2 100%)"),
                        metric_box("🚚 BIAYA DATANG", ui.output_text("val_biaya_datang"), "#276749", "linear-gradient(135deg, #C6F6D5 0%, #9AE6B4 100%)"),
                        metric_box("📦 KOLI DATANG", ui.output_text("val_koli_datang"), "#276749", "linear-gradient(135deg, #C6F6D5 0%, #9AE6B4 100%)"),
                        metric_box("🔄 BIAYA RTO", ui.output_text("val_biaya_rto"), "#9B2C2C", "linear-gradient(135deg, #FED7D7 0%, #FEB2B2 100%)"),
                        style="display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 1rem; width: 100%; margin-bottom: 1.5rem;"
                    ),
                    # History Table
                    ui.output_ui("ongkir_history_table_ui"),
                    style="width: 100%;"
                )
            )
        ),
        style="width: 100%; background: #F7FAFC; min-height: 100vh;"
    )

# ==========================================
# 8. SIDEBAR & GLOBAL HEADER
# ==========================================
def sidebar_menu_button(label: str, target: str, current_active: str):
    is_active = (current_active == target)
    bg_style = "background: linear-gradient(135deg, #E50914 0%, #B20710 100%); color: #FFFFFF; font-weight: 700; box-shadow: 0 4px 12px rgba(229, 9, 20, 0.4);" if is_active else "background: transparent; color: #CBD5E0; font-weight: 500;"
    
    return ui.tags.button(
        label,
        onclick=f"Shiny.setInputValue('navigate_menu', '{target}', {{priority: 'event'}})",
        style=f"""
            width: 100%; text-align: left; padding: 0.5rem 0.75rem; margin-bottom: 4px;
            border-radius: 6px; font-size: 0.85rem; border: none; cursor: pointer;
            {bg_style}
        """
    )

def section_dropdown_header(title: str, key: str, is_open: bool):
    icon_class = "fa-chevron-down" if is_open else "fa-chevron-right"
    return ui.tags.div(
        ui.tags.span(title, style="font-size: 11px; font-weight: bold; color: #FFFFFF; letter-spacing: 0.05em;"),
        ui.tags.i(class_=f"fa-solid {icon_class}", style="font-size: 12px; color: #FFFFFF;"),
        onclick=f"Shiny.setInputValue('toggle_dropdown', '{key}', {{priority: 'event'}})",
        style="""
            display: flex; justify-content: space-between; align-items: center; width: 100%;
            padding: 0.5rem 0.6rem; border-radius: 6px; cursor: pointer;
            background: rgba(255, 255, 255, 0.05); margin-top: 0.8rem; margin-bottom: 0.3rem;
        """
    )

# ==========================================
# 9. ROOT UI LAYOUT
# ==========================================
app_ui = ui.page_fluid(
    CUSTOM_HEAD,
    ui.output_ui("global_modal_ui"),
    ui.output_ui("main_app_container")
)

# ==========================================
# 10. SERVER LOGIC
# ==========================================
def server(input: Inputs, output: Outputs, session: Session):
    # Reactive States
    logged_in = reactive.Value(False)
    user_display_name = reactive.Value("Guest")
    user_role = reactive.Value("Staff")
    login_time_ms = reactive.Value(0)
    
    main_menu = reactive.Value("Database Ongkir In/Out")
    sidebar_open = reactive.Value(True)
    
    # Dropdown states
    dropdown_operational = reactive.Value(True)
    dropdown_inventory = reactive.Value(True)
    dropdown_reject = reactive.Value(False)
    dropdown_extras = reactive.Value(False)
    
    # Data States
    ongkir_data = reactive.Value(pd.DataFrame(columns=["id", "tanggal", "supplier", "ekspedisi", "koli", "total_ongkir"]))
    stock_minus_data = reactive.Value({})
    putaway_data = reactive.Value({})
    
    # --- AUTH LOGIC ---
    @reactive.Effect
    @reactive.event(input.btn_login)
    def handle_login():
        u = input.login_username().strip()
        p = input.login_password().strip()
        
        # Contoh user auth (bisa disesuaikan / hubungkan ke table users Supabase)
        if u != "" and p != "":
            logged_in.set(True)
            user_display_name.set(u.capitalize())
            user_role.set("ADMIN" if u.lower() == "admin" else "OPERATIONAL")
            login_time_ms.set(int(time.time() * 1000))
        else:
            ui.notification_show("Username atau password tidak boleh kosong!", type="error")
            
    @reactive.Effect
    @reactive.event(input.btn_logout)
    def handle_logout():
        logged_in.set(False)
        user_display_name.set("Guest")
        login_time_ms.set(0)

    # --- MENU NAVIGATION & SIDEBAR ---
    @reactive.Effect
    @reactive.event(input.navigate_menu)
    def _change_menu():
        main_menu.set(input.navigate_menu())
        
    @reactive.Effect
    @reactive.event(input.toggle_sidebar)
    def _toggle_sidebar():
        sidebar_open.set(not sidebar_open())
        
    @reactive.Effect
    @reactive.event(input.toggle_dropdown)
    def _toggle_dd():
        k = input.toggle_dropdown()
        if k == "operational": dropdown_operational.set(not dropdown_operational())
        elif k == "inventory": dropdown_inventory.set(not dropdown_inventory())
        elif k == "reject": dropdown_reject.set(not dropdown_reject())
        elif k == "extras": dropdown_extras.set(not dropdown_extras())

    # --- MODAL PANDUAN ---
    @reactive.Effect
    @reactive.event(input.btn_open_panduan)
    def _open_panduan():
        m = main_menu()
        if m == "Stock Minus":
            guide_content = ui.div(
                ui.h5("📋 Informasi Format File", style="font-weight: bold; color: #1A202C;"),
                ui.tags.ul(ui.tags.li("Download Multiple Adjustment dari Jezpro dan pilih 'Termasuk yang sudah habis'.")),
                ui.h5("💡 Logic Thinking", style="font-weight: bold; color: #1A202C; margin-top: 1rem;"),
                ui.tags.ol(
                    ui.tags.li("Mengambil SKU yang memiliki Qty System minus (-)"),
                    ui.tags.li("Lalu SKU akan dilakukan shuffle covering Stock."),
                    ui.tags.li("Prioritas BIN: All Stagging, Karantina, BIN Toko, lalu random.")
                )
            )
        elif m == "Putaway System":
            guide_content = ui.div(
                ui.h5("📋 Informasi Format File", style="font-weight: bold; color: #1A202C;"),
                ui.tags.ul(
                    ui.tags.li("DATA SCAN PUTAWAY: Kolom A = BIN, Kolom B = SKU, Kolom C = QTY SCAN"),
                    ui.tags.li("DATA PUTAWAY: Sesuai template Jezpro.")
                ),
                ui.h5("💡 Logic Thinking", style="font-weight: bold; color: #1A202C; margin-top: 1rem;"),
                ui.tags.ol(
                    ui.tags.li("SKU di file data scan akan dicompare dengan file BIN Putaway."),
                    ui.tags.li("Tiap unique SKU teratas di data scan mendapat alokasi penuh.")
                )
            )
        else:
            guide_content = ui.div(f"Panduan dan Logic untuk halaman '{m}' belum tersedia.", style="color: #718096; font-style: italic;")
            
        modal = ui.modal(
            guide_content,
            title=ui.div(ui.tags.i(class_="fa-solid fa-book-open", style="color: #C5A059; margin-right: 8px;"), "Panduan & Logic ERP Logistik"),
            easy_close=True,
            footer=ui.modal_button("Tutup")
        )
        ui.modal_show(modal)

    # --- ONGKIR DATABASE LOGIC ---
    @reactive.Effect
    @reactive.event(input.btn_save_ongkir)
    def _save_single_ongkir():
        supp = input.input_supplier().strip()
        eksp = input.input_ekspedisi().strip()
        koli = input.input_koli()
        ongkir = input.input_ongkir()
        tgl = str(input.input_tgl())
        
        if not supp or not eksp:
            ui.notification_show("Supplier & Ekspedisi wajib diisi!", type="warning")
            return
            
        new_row = pd.DataFrame([{
            "id": int(time.time()),
            "tanggal": tgl,
            "supplier": supp,
            "ekspedisi": eksp,
            "koli": koli,
            "total_ongkir": ongkir
        }])
        
        ongkir_data.set(pd.concat([ongkir_data(), new_row], ignore_index=True))
        ui.notification_show("Data berhasil disimpan!", type="message")

    @reactive.Effect
    @reactive.event(input.btn_execute_batch)
    def _batch_upload():
        f = input.upload_csv_batch()
        if not f:
            ui.notification_show("Pilih file CSV terlebih dahulu!", type="warning")
            return
        try:
            df = pd.read_csv(f[0]["datapath"])
            ongkir_data.set(pd.concat([ongkir_data(), df], ignore_index=True))
            ui.notification_show("Batch upload sukses diproses!", type="message")
        except Exception as e:
            ui.notification_show(f"Gagal membaca CSV: {str(e)}", type="error")

    # --- ONGKIR METRIC OUTPUTS ---
    @output
    @render.text
    def val_biaya_all():
        df = ongkir_data()
        val = df["total_ongkir"].sum() if not df.empty and "total_ongkir" in df else 0
        return f"Rp {val:,.0f}"

    @output
    @render.text
    def val_koli_all():
        df = ongkir_data()
        val = df["koli"].sum() if not df.empty and "koli" in df else 0
        return f"{val:,}"

    @output
    @render.text
    def val_avg_cost_all():
        df = ongkir_data()
        if not df.empty and df["koli"].sum() > 0:
            avg = df["total_ongkir"].sum() / df["koli"].sum()
            return f"Rp {avg:,.0f}"
        return "Rp 0"

    @output
    @render.text
    def val_biaya_datang():
        return "Rp 0"

    @output
    @render.text
    def val_koli_datang():
        return "0"

    @output
    @render.text
    def val_biaya_rto():
        return "Rp 0"

    @output
    @render.ui
    def ongkir_history_table_ui():
        df = ongkir_data()
        flt = input.filter_ekspedisi()
        if flt and flt != "ALL" and not df.empty:
            df = df[df["ekspedisi"] == flt]
        return render_table_from_df(df)

    # --- STOCK MINUS LOGIC ---
    @reactive.Effect
    @reactive.event(input.btn_process_stock)
    def _proc_stock():
        f = input.upload_stock_file()
        if not f:
            ui.notification_show("Silakan pilih file Stock Minus terlebih dahulu!", type="warning")
            return
            
        try:
            # Dummy process simulation for template
            df = pd.read_excel(f[0]["datapath"]) if f[0]["name"].endswith(".xlsx") else pd.read_csv(f[0]["datapath"])
            stock_minus_data.set({
                "processed": True,
                "qty_minus": 120,
                "tercover": 95,
                "sisa_adj": 25,
                "df_minus_awal": df.head(10),
                "df_set_up": df.head(5),
                "df_justifikasi": df.tail(3)
            })
            ui.notification_show("Data Stock Minus berhasil diproses!", type="message")
        except Exception as e:
            ui.notification_show(f"Gagal memproses file: {str(e)}", type="error")

    @output
    @render.ui
    def stock_minus_results_ui():
        data = stock_minus_data()
        if not data.get("processed", False):
            return ui.div()
            
        return ui.div(
            ui.div(
                metric_box("TOTAL QTY MINUS", f"{data['qty_minus']}", "#E53E3E", "#1A1A1A"),
                metric_box("TERCOVER", f"{data['tercover']}", "#38A169", "#1A1A1A"),
                metric_box("SISA ADJ", f"{data['sisa_adj']}", "#DD6B20", "#1A1A1A"),
                style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem; margin-bottom: 1.25rem;"
            ),
            ui.navset_card_tab(
                ui.nav_panel("📄 MINUS AWAL", render_table_from_df(data["df_minus_awal"])),
                ui.nav_panel("🔄 TEMPLATE SET UP", render_table_from_df(data["df_set_up"])),
                ui.nav_panel("⚠️ JUSTIFIKASI", render_table_from_df(data["df_justifikasi"]))
            )
        )

    # --- PUTAWAY VIEW LOGIC ---
    @output
    @render.ui
    def putaway_content_after_area():
        area = input.area_putaway()
        if not area:
            return ui.div(
                "⚠️ Silakan pilih Area Putaway di atas terlebih dahulu.",
                style="color: #DD6B20; font-weight: bold; font-style: italic; background: #FFFFF0; border: 1px solid #F6E05E; padding: 1rem; border-radius: 8px; margin-top: 1rem;"
            )
            
        return ui.div(
            ui.div(
                ui.tags.i(class_="fa-solid fa-map-pin", style="color: #3182ce; margin-right: 8px;"),
                ui.span("Area Terpilih: ", style="color: #2c5282;"),
                ui.tags.strong(area, style="color: #2c5282;"),
                style="background: #ebf8ff; border-left: 4px solid #3182ce; padding: 10px 16px; border-radius: 6px; width: 100%; margin: 1rem 0;"
            ),
            ui.div(
                ui.div(
                    ui.span("Upload DS PUTAWAY", style="font-weight: bold; color: #1A202C; font-size: 13px; margin-bottom: 4px; display: block;"),
                    ui.input_file("ds_putaway_file", None, accept=[".xlsx", ".xls", ".csv"], placeholder="200MB per file"),
                    style="flex: 1; padding: 1rem; border: 2px dashed #CBD5E0; border-radius: 8px;"
                ),
                ui.div(
                    ui.span("Upload ASAL BIN", style="font-weight: bold; color: #1A202C; font-size: 13px; margin-bottom: 4px; display: block;"),
                    ui.input_file("asal_putaway_file", None, accept=[".xlsx", ".xls", ".csv"], placeholder="200MB per file"),
                    style="flex: 1; padding: 1rem; border: 2px dashed #CBD5E0; border-radius: 8px;"
                ),
                style="display: flex; gap: 1rem; width: 100%; margin-bottom: 1.5rem;"
            ),
            ui.div(
                ui.input_action_button("btn_compare_putaway", "▶ COMPARE PUTAWAY", class_="btn-red-gradient", style="padding: 0.75rem 1.5rem;"),
                style="display: flex; justify-content: flex-end; width: 100%;"
            )
        )

    # --- TOPBAR COMPONENT ---
    def render_global_header():
        return ui.div(
            ui.div(
                ui.div(style="width: 10px; height: 32px; background: #E50914; border-radius: 4px; margin-right: 12px;"),
                ui.div(
                    ui.h3(main_menu(), style="font-size: 18px; color: #111111; font-weight: 800; margin: 0;"),
                    ui.span(f"Logged in as: {user_display_name()} ({user_role()})", style="font-size: 12px; color: #4A5568;"),
                    style="display: flex; flex-direction: column;"
                ),
                style="display: flex; align-items: center;"
            ),
            ui.div(
                ui.tags.button(
                    ui.tags.i(class_="fa-solid fa-bullhorn", style="margin-right: 6px; color: #1A202C;"),
                    "Panduan & Logic",
                    onclick="Shiny.setInputValue('btn_open_panduan', Math.random(), {priority: 'event'})",
                    style="background: #E2E8F0; color: #1A202C; border: none; padding: 6px 12px; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 13px;"
                ),
                ui.div(
                    ui.div(
                        ui.div(style="width: 8px; height: 8px; background: #10B981; border-radius: 50%; margin-right: 6px;", class_="blink-online"),
                        ui.span("ONLINE", style="font-size: 12px; font-weight: 800; color: #065F46;"),
                        style="display: flex; align-items: center;"
                    ),
                    ui.div(
                        ui.span(str(login_time_ms()), id="login-time-store", style="display: none;"),
                        ui.tags.i(class_="fa-regular fa-clock", style="font-size: 12px; color: #4A5568; margin-right: 4px;"),
                        ui.span("00:00:00", id="live-timer", style="color: #4A5568; font-weight: bold; font-size: 12px; font-family: monospace;"),
                        style="display: flex; align-items: center; justify-content: center;"
                    ),
                    style="display: flex; flex-direction: column; align-items: center;"
                ),
                style="display: flex; align-items: center; gap: 1.5rem;"
            ),
            style="""
                padding: 12px 20px; background: #D1FAE5; border: 1.5px solid #A7F3D0;
                border-radius: 16px; display: flex; justify-content: space-between;
                align-items: center; width: 100%; margin-bottom: 1rem;
            """
        )

    # --- SIDEBAR COMPONENT ---
    def render_sidebar():
        cur = main_menu()
        if not sidebar_open():
            return ui.div(
                ui.tags.button(
                    ui.tags.i(class_="fa-solid fa-bars", style="font-size: 18px; color: #FFFFFF;"),
                    onclick="Shiny.setInputValue('toggle_sidebar', Math.random(), {priority: 'event'})",
                    style="background: transparent; border: none; cursor: pointer; padding: 0.5rem;"
                ),
                style="width: 60px; height: 100vh; background: #111318; border-right: 1px solid #2D3748; padding: 1rem 0.5rem; display: flex; flex-direction: column; align-items: center;"
            )
            
        return ui.div(
            # Brand Header
            ui.div(
                ui.div(
                    ui.span("JEZ", style="color: #E50914; font-weight: 900; font-size: 20px;"),
                    ui.span("PRO", style="color: #FFFFFF; font-weight: 900; font-size: 20px;"),
                    style="display: flex; gap: 2px;"
                ),
                ui.tags.button(
                    ui.tags.i(class_="fa-solid fa-xmark", style="font-size: 16px; color: #CBD5E0;"),
                    onclick="Shiny.setInputValue('toggle_sidebar', Math.random(), {priority: 'event'})",
                    style="background: transparent; border: none; cursor: pointer;"
                ),
                style="display: flex; justify-content: space-between; width: 100%; align-items: center; margin-bottom: 1rem;"
            ),
            # Nav Area
            ui.div(
                # Group 1: Operational
                section_dropdown_header("OPERATIONAL", "operational", dropdown_operational()),
                ui.div(
                    sidebar_menu_button("Database Ongkir In/Out", "Database Ongkir In/Out", cur),
                    sidebar_menu_button("Stock Minus", "Stock Minus", cur),
                    sidebar_menu_button("Putaway System", "Putaway System", cur),
                    style="padding-left: 0.5rem;" if dropdown_operational() else "display: none;"
                ),
                # Group 2: Inventory
                section_dropdown_header("INVENTORY", "inventory", dropdown_inventory()),
                ui.div(
                    sidebar_menu_button("Stock Opname", "Stock Opname", cur),
                    sidebar_menu_button("Relokasi BIN", "Relokasi BIN", cur),
                    style="padding-left: 0.5rem;" if dropdown_inventory() else "display: none;"
                ),
                # Group 3: Reject
                section_dropdown_header("REJECT & DEFECT", "reject", dropdown_reject()),
                ui.div(
                    sidebar_menu_button("Barang Rusak", "Barang Rusak", cur),
                    style="padding-left: 0.5rem;" if dropdown_reject() else "display: none;"
                ),
                # Group 4: Extras
                section_dropdown_header("EXTRAS", "extras", dropdown_extras()),
                ui.div(
                    sidebar_menu_button("Log Aktivitas", "Log Aktivitas", cur),
                    style="padding-left: 0.5rem;" if dropdown_extras() else "display: none;"
                ),
                style="flex: 1; overflow-y: auto; width: 100%;"
            ),
            # Logout Button
            ui.div(
                ui.tags.button(
                    ui.tags.i(class_="fa-solid fa-right-from-bracket", style="margin-right: 8px;"),
                    "Logout Sistem",
                    onclick="Shiny.setInputValue('btn_logout', Math.random(), {priority: 'event'})",
                    class_="btn-red-gradient",
                    style="width: 100%; padding: 0.6rem; font-size: 13px;"
                ),
                style="width: 100%; border-top: 1px solid rgba(255, 255, 255, 0.1); padding-top: 0.8rem; margin-top: auto;"
            ),
            style="""
                width: 280px; min-width: 280px; padding: 1rem;
                background: linear-gradient(180deg, #111318 0%, #1A1D24 50%, #0D0F12 100%);
                border-right: 1px solid #2D3748; height: 100vh; display: flex; flex-direction: column;
                transition: width 0.3s