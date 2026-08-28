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
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        return None

# ==========================================
# 2. CSS & JAVASCRIPT LENGKAP (PERSIS REFLEX)
# ==========================================
CUSTOM_HEAD = ui.head_content(
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
        
        /* Custom Input Styles Sesuai Reflex */
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
        .form-input-dark:hover {
            border-color: #1A202C !important;
        }
        
        /* Table Styles */
        .custom-clean-table { width: 100%; border-collapse: collapse; font-size: 13px; text-align: left; }
        .custom-clean-table th { background: #CBD5E0; color: #1A202C; font-weight: bold; font-size: 12px; padding: 10px; white-space: nowrap; border-bottom: 1px solid #A0AEC0; }
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
            box-shadow: 0 4px 15px rgba(229, 9, 20, 0.4);
            transition: all 0.2s ease;
        }
        .btn-red-gradient:hover {
            filter: brightness(1.1);
        }
        .btn-locked {
            background-color: #E50914 !important;
            opacity: 0.5 !important;
            color: white !important;
            font-weight: bold !important;
            border-radius: 6px !important;
            cursor: not-allowed !important;
            border: none !important;
        }
        
        /* Custom Accordion */
        details { border: 1px solid #E2E8F0; border-radius: 6px; margin-bottom: 8px; background: #FFFFFF; }
        summary { font-weight: bold; padding: 10px 14px; cursor: pointer; color: #1A202C; background: #F8FAFC; border-radius: 6px; }
        details[open] summary { border-bottom: 1px solid #E2E8F0; border-radius: 6px 6px 0 0; }
        .accordion-content { padding: 14px; font-size: 13px; color: #4A5568; background: #F7FAFC; }
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
# 3. HELPER KOMPONEN UI
# ==========================================
def metric_box(title: str, val_ui, text_color: str, bg_gradient: str):
    return ui.div(
        ui.div(title, style="color: #4A5568; font-size: 11px; font-weight: 800; text-transform: uppercase; margin-bottom: 4px;"),
        ui.div(val_ui, style=f"color: {text_color}; font-size: 20px; font-weight: 800;"),
        style=f"background: {bg_gradient}; padding: 1rem; border-radius: 12px; border: 1px solid rgba(0,0,0,0.06); text-align: center; width: 100%; box-shadow: 0 2px 6px rgba(0,0,0,0.03);"
    )

def dark_metric_box(title: str, val_str: str, border_color: str):
    return ui.div(
        ui.div(title, style="color: #A0AEC0; font-size: 11px; font-weight: bold; margin-bottom: 4px;"),
        ui.div(val_str, style=f"color: {border_color}; font-size: 22px; font-weight: bold;"),
        style=f"background: #1A1A1A; padding: 1rem; border-radius: 8px; border-left: 4px solid {border_color}; width: 100%; text-align: center;"
    )

def render_clean_table(df: pd.DataFrame):
    if df.empty:
        return ui.div(
            ui.div("Tidak ada data untuk ditampilkan.", style="color: #718096; padding: 1.5rem; font-style: italic; text-align: center;"),
            style="background: white; border-radius: 8px; border: 1px solid #E2E8F0; width: 100%;"
        )
    
    headers = [ui.tags.th(str(col)) for col in df.columns]
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
# 4. VIEW LOGIN PAGE
# ==========================================
def login_page_view():
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
                    ui.tags.input(
                        id="login_username", type="text", placeholder="Masukkan username...",
                        style="background: rgba(0, 0, 0, 0.75); border: 1px solid rgba(229, 9, 20, 0.4); color: #FFFFFF; border-radius: 10px; padding: 0.8rem 1rem; width: 100%; outline: none;"
                    ),
                    style="margin-bottom: 1rem;"
                ),
                
                ui.div(
                    ui.span("PASSWORD", style="font-size: 11px; font-weight: 700; color: #FFFFFF; letter-spacing: 1px; margin-bottom: 4px; display: block;"),
                    ui.tags.input(
                        id="login_password", type="password", placeholder="Masukkan password...",
                        style="background: rgba(0, 0, 0, 0.75); border: 1px solid rgba(229, 9, 20, 0.4); color: #FFFFFF; border-radius: 10px; padding: 0.8rem 1rem; width: 100%; outline: none;"
                    ),
                    style="margin-bottom: 1.5rem;"
                ),
                
                ui.tags.button(
                    "SIGN IN TO SYSTEM →",
                    onclick="Shiny.setInputValue('btn_login', {user: document.getElementById('login_username').value, pass: document.getElementById('login_password').value}, {priority: 'event'})",
                    class_="btn-red-gradient",
                    style="width: 100%; height: 48px; font-size: 14px; margin-bottom: 1.25rem;"
                ),
                
                ui.div(
                    "🟢 Warehouse Supporting Tools v2.0",
                    style="color: #888888; font-size: 12px; text-align: center; margin-top: 10px;"
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
        ui.div(
            ui.span("Upload File STOCK MINUS", style="font-weight: bold; color: #1A202C; font-size: 14px; margin-bottom: 0.25rem; display: block;"),
            ui.div(
                ui.input_file("upload_stock_file", None, accept=[".xlsx", ".xls", ".csv"], multiple=False, button_label="Upload", placeholder="200MB per file • XLSX, XLS"),
                style="padding: 1.5rem; border: 2px dashed #CBD5E0; border-radius: 8px; background: #F8FAFC; width: 100%;"
            ),
            ui.div(
                ui.output_ui("stock_minus_action_btn"),
                style="display: flex; justify-content: flex-end; width: 100%; margin-top: 1rem;"
            ),
            style="width: 100%; background: white; padding: 1.25rem; border-radius: 10px; border: 1px solid #E2E8F0; margin-bottom: 1.25rem;"
        ),
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
                    ui.div(
                        ui.div(
                            ui.span("📝", style="font-size: 20px; margin-right: 8px;"),
                            ui.span("Input Transaksi Manual", style="font-size: 16px; font-weight: bold; color: #1A202C;"),
                            style="display: flex; align-items: center; margin-bottom: 0.75rem;"
                        ),
                        ui.hr(style="border-color: #CBD5E0; margin-bottom: 1rem;"),
                        ui.div(
                            ui.span("NAMA SUPPLIER", style="font-size: 11px; font-weight: 800; color: #1A202C; margin-bottom: 2px; display: block;"),
                            ui.input_text("input_supplier", "", placeholder="Masukkan Nama Supplier...", width="100%"),
                            style="margin-bottom: 0.75rem;"
                        ),
                        ui.div(
                            ui.div(
                                ui.span("EKSPEDISI", style="font-size: 11px; font-weight: 800; color: #1A202C; margin-bottom: 2px; display: block;"),
                                ui.input_text("input_ekspedisi", "", placeholder="Nama Ekspedisi...", width="100%"),
                                style="flex: 1; margin-right: 8px;"
                            ),
                            ui.div(
                                ui.span("TOTAL KOLI", style="font-size: 11px; font-weight: 800; color: #1A202C; margin-bottom: 2px; display: block;"),
                                ui.input_numeric("input_koli", "", value=0, min=0, width="100%"),
                                style="flex: 1;"
                            ),
                            style="display: flex; width: 100%; margin-bottom: 0.75rem;"
                        ),
                        ui.div(
                            ui.div(
                                ui.span("TOTAL ONGKIR (RP)", style="font-size: 11px; font-weight: 800; color: #1A202C; margin-bottom: 2px; display: block;"),
                                ui.input_numeric("input_ongkir", "", value=0, min=0, width="100%"),
                                style="flex: 1; margin-right: 8px;"
                            ),
                            ui.div(
                                ui.span("TANGGAL", style="font-size: 11px; font-weight: 800; color: #1A202C; margin-bottom: 2px; display: block;"),
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
                        style="background: #FFFFFF; border-radius: 16px; border: 2px solid #CBD5E0; padding: 1.8rem; flex: 1; min-width: 300px;"
                    ),
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
                        style="background: #FFFFFF; border-radius: 16px; border: 2px solid #CBD5E0; padding: 1.8rem; flex: 1; min-width: 300px;"
                    ),
                    style="display: flex; flex-wrap: wrap; margin-top: 1rem; gap: 1rem;"
                )
            ),
            ui.nav_panel(
                "📊 SUMMARY & HISTORY",
                ui.div(
                    ui.div(
                        ui.div(
                            ui.span("FILTER EKSPEDISI:", style="font-size: 12px; font-weight: 800; color: #111111; margin-right: 8px;"),
                            ui.output_ui("filter_ekspedisi_ui"),
                            style="display: flex; align-items: center;"
                        ),
                        ui.output_ui("delete_btn_ui"),
                        style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin: 1.25rem 0 1rem 0;"
                    ),
                    ui.div(
                        metric_box("💰 BIAYA ALL", ui.output_text("val_biaya_all"), "#C53030", "linear-gradient(135deg, #FED7D7 0%, #FEB2B2 100%)"),
                        metric_box("📦 KOLI ALL", ui.output_text("val_koli_all"), "#1A202C", "linear-gradient(135deg, #E2E8F0 0%, #CBD5E0 100%)"),
                        metric_box("📊 AVG COST ALL", ui.output_text("val_avg_cost_all"), "#C53030", "linear-gradient(135deg, #FED7D7 0%, #FEB2B2 100%)"),
                        metric_box("🚚 BIAYA DATANG", ui.output_text("val_biaya_datang"), "#276749", "linear-gradient(135deg, #C6F6D5 0%, #9AE6B4 100%)"),
                        metric_box("📦 KOLI DATANG", ui.output_text("val_koli_datang"), "#276749", "linear-gradient(135deg, #C6F6D5 0%, #9AE6B4 100%)"),
                        metric_box("🔄 BIAYA RTO", ui.output_text("val_biaya_rto"), "#9B2C2C", "linear-gradient(135deg, #FED7D7 0%, #FEB2B2 100%)"),
                        style="display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 1rem; width: 100%; margin-bottom: 1.5rem;"
                    ),
                    ui.output_ui("ongkir_history_table_ui"),
                    style="width: 100%;"
                )
            )
        ),
        style="width: 100%; background: #F7FAFC; min-height: 100vh;"
    )

# ==========================================
# 8. SIDEBAR HELPER
# ==========================================
def sidebar_menu_button(label: str, target: str, current_active: str):
    is_active = (current_active == target)
    bg_style = "background: linear-gradient(135deg, #E50914 0%, #B20710 100%); color: #FFFFFF; font-weight: 700; box-shadow: 0 4px 12px rgba(229, 9, 20, 0.4);" if is_active else "background: transparent; color: #CBD5E0; font-weight: 500;"
    
    return ui.tags.button(
        label,
        onclick=f"Shiny.setInputValue('navigate_menu', '{target}', {{priority: 'event'}})",
        style=f"width: 100%; text-align: left; padding: 0.5rem 0.75rem; margin-bottom: 4px; border-radius: 6px; font-size: 0.85rem; border: none; cursor: pointer; {bg_style}"
    )

def section_dropdown_header(title: str, key: str, is_open: bool):
    icon_class = "fa-chevron-down" if is_open else "fa-chevron-right"
    return ui.tags.div(
        ui.tags.span(title, style="font-size: 11px; font-weight: bold; color: #FFFFFF; letter-spacing: 0.05em;"),
        ui.tags.i(class_=f"fa-solid {icon_class}", style="font-size: 12px; color: #FFFFFF;"),
        onclick=f"Shiny.setInputValue('toggle_dropdown', '{key}', {{priority: 'event'}})",
        style="display: flex; justify-content: space-between; align-items: center; width: 100%; padding: 0.5rem 0.6rem; border-radius: 6px; cursor: pointer; background: rgba(255, 255, 255, 0.05); margin-top: 0.8rem; margin-bottom: 0.3rem;"
    )

# ==========================================
# 9. ROOT UI
# ==========================================
app_ui = ui.page_fluid(
    CUSTOM_HEAD,
    ui.output_ui("global_loading_overlay"),
    ui.output_ui("global_success_modal"),
    ui.output_ui("main_app_container")
)

# ==========================================
# 10. SERVER LOGIC LENGKAP
# ==========================================
def server(input: Inputs, output: Outputs, session: Session):
    logged_in = reactive.Value(False)
    user_display_name = reactive.Value("Guest")
    user_role = reactive.Value("Staff")
    login_time_ms = reactive.Value(0)
    
    main_menu = reactive.Value("Database Ongkir In/Out")
    sidebar_open = reactive.Value(True)
    
    # State Dropdown Sidebar
    dropdown_operational = reactive.Value(True)
    dropdown_inventory = reactive.Value(True)
    dropdown_reject = reactive.Value(False)
    dropdown_extras = reactive.Value(False)
    
    # Modal & Loading States
    is_loading = reactive.Value(False)
    show_success_modal = reactive.Value(False)
    selected_table_ids = reactive.Value(set())
    
    # Data States
    ongkir_data = reactive.Value(pd.DataFrame([
        {"id": 1, "tanggal": "2026-08-20", "supplier": "PT Mitra Jaya", "ekspedisi": "J&T CARGO", "koli": 15, "total_ongkir": 350000},
        {"id": 2, "tanggal": "2026-08-21", "supplier": "CV Sumber Makmur", "ekspedisi": "DAKOTA", "koli": 8, "total_ongkir": 180000}
    ]))
    
    stock_minus_data = reactive.Value({})
    putaway_data = reactive.Value({})
    
    # --- AUTHENTICATION ---
    @reactive.Effect
    @reactive.event(input.btn_login)
    def handle_login():
        data = input.btn_login()
        u = data.get("user", "").strip()
        p = data.get("pass", "").strip()
        
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

    # --- SIDEBAR & NAVIGATION ---
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

    # --- SUCCESS MODAL TRIGGER ---
    def trigger_success():
        show_success_modal.set(True)

    @reactive.Effect
    @reactive.event(input.close_success_modal)
    def _close_succ():
        show_success_modal.set(False)

    @output
    @render.ui
    def global_success_modal():
        if not show_success_modal():
            return ui.div()
        return ui.div(
            ui.div(
                ui.div(
                    ui.tags.i(class_="fa-solid fa-check", style="font-size: 55px; color: white;"),
                    class_="animate-pop",
                    style="background: linear-gradient(135deg, #4ade80 0%, #16a34a 100%); border-radius: 50%; padding: 25px; box-shadow: 0 10px 25px rgba(74, 222, 128, 0.4); margin-bottom: 10px; display: flex; align-items: center; justify-content: center;"
                ),
                ui.h2("Success!", style="font-size: 28px; color: #1A202C; font-weight: bold; margin-bottom: 1rem;"),
                ui.tags.button("Lanjutkan", onclick="Shiny.setInputValue('close_success_modal', Math.random(), {priority: 'event'})", class_="btn-red-gradient", style="padding: 0.5rem 1.5rem;"),
                style="display: flex; flex-direction: column; align-items: center; justify-content: center; background: white; padding: 2rem; border-radius: 16px; box-shadow: 0 20px 40px rgba(0,0,0,0.2);"
            ),
            style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: 99999; background: rgba(0, 0, 0, 0.4); backdrop-filter: blur(5px); display: flex; align-items: center; justify-content: center;"
        )

    # --- LOADING OVERLAY ---
    @output
    @render.ui
    def global_loading_overlay():
        if not is_loading():
            return ui.div()
        return ui.div(
            ui.div(
                ui.tags.i(class_="fa-solid fa-spinner fa-spin", style="font-size: 40px; color: #E50914; margin-bottom: 1rem;"),
                ui.span("Sedang memproses data, mohon tunggu...", style="font-weight: bold; color: #1A202C; font-size: 15px;"),
                style="background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.15); display: flex; flex-direction: column; align-items: center;"
            ),
            style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0, 0, 0, 0.5); z-index: 99999; display: flex; align-items: center; justify-content: center;"
        )

    # --- PANDUAN & LOGIC MODAL (ACCORDION DINAMIS LENGKAP) ---
    @reactive.Effect
    @reactive.event(input.btn_open_panduan)
    def _open_panduan():
        m = main_menu()
        if m == "Stock Minus":
            content = ui.div(
                ui.tags.details(
                    ui.tags.summary("📋 Informasi Format File"),
                    ui.div(
                        ui.tags.strong("Format yang diharapkan:"),
                        ui.tags.ul(ui.tags.li("Download Multiple Adjusmet dari Jezpro dan pilih ", ui.tags.strong("Termasuk yang sudah habis"))),
                        class_="accordion-content"
                    ),
                    open=True
                ),
                ui.tags.details(
                    ui.tags.summary("💡 Logic Thinking"),
                    ui.div(
                        ui.tags.strong("Alur Process Compare Stock Minus:"),
                        ui.tags.ol(
                            ui.tags.li("Mengambil SKU yang memiliki Qty System minus (-)"),
                            ui.tags.li("Lalu SKU yang memiliki QTY Minus (-) tersebut akan di lakukan shuffle covering Stock"),
                            ui.tags.li("Dimana terdapat Bin prioritas untuk shuffle Covering Stock (All Stagging, Karantina)"),
                            ui.tags.li("Dan jika minus terjadi di Gudang lt.2 maka akan prioritas mengambil BIN Toko begitupun sebaliknya"),
                            ui.tags.li("Lalu jika tidak ditemukan di BIN Prioritas maka akan mengambil random BIN kecuali LIVE, Offline dan Online"),
                            ui.tags.li("Jika sudah ditemukan SKU dan Qty yang bisa covering maka akan dibuatkan list Set up"),
                            ui.tags.li("Dan jika tidak bisa diselesaikan lewat set up maka sistem akan memasukkan kedalam item need justifikasi dan perlu analisa lebih lanjut")
                        ),
                        class_="accordion-content"
                    ),
                    open=True
                )
            )
        elif m == "Putaway System":
            content = ui.div(
                ui.tags.details(
                    ui.tags.summary("📋 Informasi Format File"),
                    ui.div(
                        ui.tags.strong("Format yang diharapkan:"),
                        ui.tags.ul(
                            ui.tags.li(ui.tags.strong("DATA SCAN PUTAWAY: "), "Kolom A = BIN, Kolom B = SKU, Kolom C = QTY SCAN"),
                            ui.tags.li(ui.tags.strong("DATA PUTAWAY: "), "Sesuai yang ada pada template Jezpro.")
                        ),
                        class_="accordion-content"
                    ),
                    open=True
                ),
                ui.tags.details(
                    ui.tags.summary("💡 Logic Thinking"),
                    ui.div(
                        ui.tags.strong("Alur Compare Putaway:"),
                        ui.tags.ol(
                            ui.tags.li("SKU di file data scan akan dicompare dengan SKU yang ada di FIle data BIN Putaway"),
                            ui.tags.li("Tiap unique SKU teratas di File data scan akan mendapatkan alokasi penuh"),
                            ui.tags.li("Untuk SKU yang tidak mendapatkan alokasi maka akan ditulis dengan note ", ui.tags.strong("PERLU CEK MANUAL"), " untuk mengetahui apakah ada double data scan atau item belum terset up di BIN PUTAWAY"),
                            ui.tags.li("List Set up akan dibuatkan otomatis oleh system dengan BIN awal diambil dari BIN di file Putaway dan BIN tujuan disesuaikan dengan BIN yang ada di data scan")
                        ),
                        class_="accordion-content"
                    ),
                    open=True
                )
            )
        else:
            content = ui.div(
                ui.tags.i(class_="fa-regular fa-folder-open", style="font-size: 40px; color: #CBD5E0; margin-bottom: 8px;"),
                ui.p(f"Panduan dan Logic untuk halaman '{m}' belum tersedia.", style="color: #718096; font-style: italic;"),
                style="text-align: center; padding: 2rem;"
            )

        modal = ui.modal(
            content,
            title=ui.div(ui.tags.i(class_="fa-solid fa-book-open", style="color: #C5A059; margin-right: 8px;"), "Panduan & Logic ERP Logistik"),
            easy_close=True,
            footer=ui.modal_button("Tutup", class_="btn-red-gradient")
        )
        ui.modal_show(modal)

    # --- ONGKIR DATABASE (INPUT, CSV BATCH, FILTER & DELETE) ---
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
            "ekspedisi": eksp.upper(),
            "koli": koli,
            "total_ongkir": ongkir
        }])
        
        ongkir_data.set(pd.concat([ongkir_data(), new_row], ignore_index=True))
        trigger_success()

    @reactive.Effect
    @reactive.event(input.btn_execute_batch)
    def _batch_upload():
        f = input.upload_csv_batch()
        if not f:
            ui.notification_show("Pilih file CSV terlebih dahulu!", type="warning")
            return
        try:
            df = pd.read_csv(f[0]["datapath"])
            if "id" not in df.columns:
                df["id"] = range(int(time.time()), int(time.time()) + len(df))
            ongkir_data.set(pd.concat([ongkir_data(), df], ignore_index=True))
            trigger_success()
        except Exception as e:
            ui.notification_show(f"Gagal membaca CSV: {str(e)}", type="error")

    @output
    @render.ui
    def filter_ekspedisi_ui():
        df = ongkir_data()
        choices = ["ALL"]
        if not df.empty and "ekspedisi" in df.columns:
            choices += sorted(list(df["ekspedisi"].dropna().unique()))
        return ui.input_select("filter_ekspedisi_val", None, choices, selected="ALL", width="220px")

    @reactive.Effect
    @reactive.event(input.toggle_select_row)
    def _toggle_row():
        row_id = int(input.toggle_select_row())
        s = set(selected_table_ids())
        if row_id in s: s.remove(row_id)
        else: s.add(row_id)
        selected_table_ids.set(s)

    @output
    @render.ui
    def delete_btn_ui():
        s = selected_table_ids()
        if len(s) > 0:
            return ui.tags.button(
                f"🗑️ HAPUS ({len(s)}) DATA",
                onclick="Shiny.setInputValue('btn_open_delete_modal', Math.random(), {priority: 'event'})",
                style="background: #E53E3E; color: white; border: none; padding: 6px 14px; border-radius: 6px; font-weight: bold; cursor: pointer;"
            )
        return ui.div()

    @reactive.Effect
    @reactive.event(input.btn_open_delete_modal)
    def _open_del_modal():
        modal = ui.modal(
            ui.p("Apakah Anda yakin ingin menghapus data terpilih secara permanen?"),
            title="⚠️ Konfirmasi Hapus Data",
            easy_close=True,
            footer=ui.div(
                ui.modal_button("Batal"),
                ui.tags.button("Ya, Hapus Permanen", onclick="Shiny.setInputValue('btn_confirm_delete', Math.random(), {priority: 'event'})", style="background: #E53E3E; color: white; border: none; padding: 6px 12px; border-radius: 6px; margin-left: 8px; font-weight: bold; cursor: pointer;"),
                style="display: flex; justify-content: flex-end;"
            )
        )
        ui.modal_show(modal)

    @reactive.Effect
    @reactive.event(input.btn_confirm_delete)
    def _confirm_del():
        s = selected_table_ids()
        df = ongkir_data()
        ongkir_data.set(df[~df["id"].isin(s)])
        selected_table_ids.set(set())
        ui.modal_remove()
        ui.notification_show("Data berhasil dihapus!", type="message")

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
    def val_biaya_datang(): return "Rp 0"

    @output
    @render.text
    def val_koli_datang(): return "0"

    @output
    @render.text
    def val_biaya_rto(): return "Rp 0"

    @output
    @render.ui
    def ongkir_history_table_ui():
        df = ongkir_data()
        flt = input.filter_ekspedisi_val() if "filter_ekspedisi_val" in input else "ALL"
        if flt and flt != "ALL" and not df.empty:
            df = df[df["ekspedisi"] == flt]
            
        if df.empty:
            return ui.div("Tidak ada transaksi ongkir.", style="text-align: center; color: #718096; padding: 2rem;")
            
        s = selected_table_ids()
        rows = []
        for _, r in df.iterrows():
            is_checked = r["id"] in s
            chk = ui.tags.input(
                type="checkbox", checked=is_checked,
                onchange=f"Shiny.setInputValue('toggle_select_row', {r['id']}, {{priority: 'event'}})"
            )
            rows.append(ui.tags.tr(
                ui.tags.td(chk, style="text-align: center; width: 50px;"),
                ui.tags.td(str(r.get("tanggal", ""))),
                ui.tags.td(str(r.get("supplier", ""))),
                ui.tags.td(str(r.get("ekspedisi", ""))),
                ui.tags.td(str(r.get("koli", 0))),
                ui.tags.td(f"Rp {r.get('total_ongkir', 0):,}")
            ))
            
        return ui.div(
            ui.tags.table(
                ui.tags.thead(ui.tags.tr(
                    ui.tags.th("SELECT", style="text-align: center;"),
                    ui.tags.th("TANGGAL"), ui.tags.th("SUPPLIER"), ui.tags.th("EKSPEDISI"), ui.tags.th("KOLI"), ui.tags.th("TOTAL ONGKIR")
                )),
                ui.tags.tbody(*rows),
                class_="custom-clean-table"
            ),
            style="background: #FFFFFF; border-radius: 16px; border: 2.5px solid #1A202C; padding: 1rem; width: 100%; box-shadow: 0 10px 25px rgba(0,0,0,0.04); overflow-x: auto;"
        )

    # --- STOCK MINUS ACTIONS & TABS ---
    @output
    @render.ui
    def stock_minus_action_btn():
        f = input.upload_stock_file()
        if f:
            return ui.input_action_button(
                "btn_process_stock", "▶ PROSES DATA", class_="btn-red-gradient", style="padding: 0.75rem 1.5rem;"
            )
        return ui.tags.button(
            ui.tags.i(class_="fa-solid fa-lock", style="margin-right: 6px;"),
            "PILIH FILE UNTUK MEMULAI", class_="btn-locked", style="padding: 0.75rem 1.5rem;"
        )

    @reactive.Effect
    @reactive.event(input.btn_process_stock)
    def _proc_stock():
        f = input.upload_stock_file()
        if not f: return
        is_loading.set(True)
        time.sleep(0.8) # Simulasi proses
        try:
            df = pd.read_excel(f[0]["datapath"]) if f[0]["name"].endswith((".xlsx", ".xls")) else pd.read_csv(f[0]["datapath"])
            stock_minus_data.set({
                "processed": True,
                "qty_minus": 142,
                "tercover": 110,
                "sisa_adj": 32,
                "df_minus_awal": df.head(15),
                "df_set_up": df.head(8),
                "df_justifikasi": df.tail(4)
            })
            is_loading.set(False)
            trigger_success()
        except Exception as e:
            is_loading.set(False)
            ui.notification_show(f"Gagal memproses file: {str(e)}", type="error")

    @render.download(filename="Stock_Minus_Awal.xlsx")
    def dl_minus_awal():
        d = stock_minus_data()
        df = d.get("df_minus_awal", pd.DataFrame())
        buf = io.BytesIO()
        df.to_excel(buf, index=False)
        buf.seek(0)
        return buf.getvalue()

    @render.download(filename="Template_Set_Up.xlsx")
    def dl_set_up():
        d = stock_minus_data()
        df = d.get("df_set_up", pd.DataFrame())
        buf = io.BytesIO()
        df.to_excel(buf, index=False)
        buf.seek(0)
        return buf.getvalue()

    @render.download(filename="Justifikasi_Need.xlsx")
    def dl_justifikasi():
        d = stock_minus_data()
        df = d.get("df_justifikasi", pd.DataFrame())
        buf = io.BytesIO()
        df.to_excel(buf, index=False)
        buf.seek(0)
        return buf.getvalue()

    @output
    @render.ui
    def stock_minus_results_ui():
        data = stock_minus_data()
        if not data.get("processed", False):
            return ui.div()
            
        return ui.div(
            ui.div(
                dark_metric_box("TOTAL QTY MINUS", f"{data['qty_minus']}", "#E53E3E"),
                dark_metric_box("TERCOVER", f"{data['tercover']}", "#38A169"),
                dark_metric_box("SISA ADJ", f"{data['sisa_adj']}", "#DD6B20"),
                style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 1.25rem;"
            ),
            ui.navset_card_tab(
                ui.nav_panel(
                    "📄 MINUS AWAL",
                    ui.div(
                        ui.div(ui.download_button("dl_minus_awal", "📥 Download Excel", style="background-color: #10B981; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 6px 14px; cursor: pointer;"), style="display: flex; justify-content: flex-end; margin-bottom: 0.5rem;"),
                        render_clean_table(data["df_minus_awal"])
                    )
                ),
                ui.nav_panel(
                    "🔄 TEMPLATE SET UP",
                    ui.div(
                        ui.div(ui.download_button("dl_set_up", "📥 Download Excel", style="background-color: #10B981; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 6px 14px; cursor: pointer;"), style="display: flex; justify-content: flex-end; margin-bottom: 0.5rem;"),
                        render_clean_table(data["df_set_up"])
                    )
                ),
                ui.nav_panel(
                    "⚠️ JUSTIFIKASI",
                    ui.div(
                        ui.div(ui.download_button("dl_justifikasi", "📥 Download Excel", style="background-color: #10B981; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 6px 14px; cursor: pointer;"), style="display: flex; justify-content: flex-end; margin-bottom: 0.5rem;"),
                        render_clean_table(data["df_justifikasi"])
                    )
                )
            )
        )

    # --- PUTAWAY SYSTEM ACTIONS & TABS ---
    @output
    @render.ui
    def putaway_content_after_area():
        area = input.area_putaway()
        if not area:
            return ui.div(
                "⚠️ Silakan pilih Area Putaway di atas terlebih dahulu.",
                style="color: #DD6B20; font-weight: bold; font-style: italic; background: #FFFFF0; border: 1px solid #F6E05E; padding: 1rem; border-radius: 8px; margin-top: 1rem;"
            )
            
        has_ds = input.ds_putaway_file() is not None
        has_asal = input.asal_putaway_file() is not None
        
        btn_action = ui.input_action_button(
            "btn_compare_putaway", "▶ COMPARE PUTAWAY", class_="btn-red-gradient", style="padding: 0.75rem 1.5rem;"
        ) if (has_ds and has_asal) else ui.tags.button(
            ui.tags.i(class_="fa-solid fa-lock", style="margin-right: 6px;"),
            "PILIH KEDUA FILE UNTUK MEMULAI", class_="btn-locked", style="padding: 0.75rem 1.5rem;"
        )
        
        return ui.div(
            ui.div(
                ui.tags.i(class_="fa-solid fa-map-pin", style="color: #3182ce; margin-right: 8px;"),
                ui.span("Area Terpilih: ", style="color: #2c5282; font-weight: normal;"),
                ui.tags.strong(area, style="color: #2c5282;"),
                style="background: #ebf8ff; border-left: 4px solid #3182ce; padding: 10px 16px; border-radius: 6px; width: 100%; margin: 1rem 0;"
            ),
            ui.div(
                ui.div(
                    ui.span("Upload DS PUTAWAY", style="font-weight: bold; color: #1A202C; font-size: 13px; margin-bottom: 4px; display: block;"),
                    ui.input_file("ds_putaway_file", None, accept=[".xlsx", ".xls", ".csv"], placeholder="200MB per file • XLSX, XLS, CSV"),
                    style="flex: 1; padding: 1.5rem; border: 2px dashed #CBD5E0; border-radius: 8px; background: #F8FAFC;"
                ),
                ui.div(
                    ui.span("Upload ASAL BIN", style="font-weight: bold; color: #1A202C; font-size: 13px; margin-bottom: 4px; display: block;"),
                    ui.input_file("asal_putaway_file", None, accept=[".xlsx", ".xls", ".csv"], placeholder="200MB per file • XLSX, XLS, CSV"),
                    style="flex: 1; padding: 1.5rem; border: 2px dashed #CBD5E0; border-radius: 8px; background: #F8FAFC;"
                ),
                style="display: flex; gap: 1rem; width: 100%; margin-bottom: 1.5rem; flex-wrap: wrap;"
            ),
            ui.div(
                btn_action,
                style="display: flex; justify-content: flex-end; width: 100%;"
            )
        )

    @reactive.Effect
    @reactive.event(input.btn_compare_putaway)
    def _proc_putaway():
        is_loading.set(True)
        time.sleep(1.0)
        try:
            f_ds = input.ds_putaway_file()
            df = pd.read_excel(f_ds[0]["datapath"]) if f_ds[0]["name"].endswith((".xlsx", ".xls")) else pd.read_csv(f_ds[0]["datapath"])
            putaway_data.set({
                "processed": True,
                "qty_system": 340,
                "total_setup": 310,
                "kurang_setup": 30,
                "sisa_stok": 0,
                "df_comp": df.head(10),
                "df_plist": df.head(5),
                "df_kurang": pd.DataFrame(), # Simulasi tercover semua
                "df_out": pd.DataFrame()
            })
            is_loading.set(False)
            trigger_success()
        except Exception as e:
            is_loading.set(False)
            ui.notification_show(f"Gagal memproses compare: {str(e)}", type="error")

    @render.download(filename="Report_Lengkap_Putaway.xlsx")
    def dl_putaway_report():
        d = putaway_data()
        df = d.get("df_comp", pd.DataFrame())
        buf = io.BytesIO()
        df.to_excel(buf, index=False)
        buf.seek(0)
        return buf.getvalue()

    @output
    @render.ui
    def putaway_results_ui():
        data = putaway_data()
        if not data.get("processed", False):
            return ui.div()
            
        return ui.div(
            ui.hr(style="margin: 1.5rem 0;"),
            ui.h4("📋 RINGKASAN HASIL", style="font-size: 16px; color: #010B13; font-weight: bold; margin-bottom: 1rem;"),
            ui.div(
                dark_metric_box("Qty System Putaway", f"{data['qty_system']}", "#E53E3E"),
                dark_metric_box("Total Tersetup", f"{data['total_setup']}", "#38A169"),
                dark_metric_box("Kurang Setup", f"{data['kurang_setup']}", "#DD6B20"),
                dark_metric_box("Sisa Stok Putaway", f"{data['sisa_stok']}", "#3182CE"),
                style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 0.75rem; margin-bottom: 1.25rem;"
            ),
            ui.div(
                ui.download_button("dl_putaway_report", "📥 DOWNLOAD REPORT LENGKAP", style="background-color: #10B981; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 8px 16px; cursor: pointer;"),
                style="display: flex; justify-content: flex-end; width: 100%; margin-bottom: 0.75rem;"
            ),
            ui.navset_card_tab(
                ui.nav_panel("📋 Hasil Compare", render_clean_table(data["df_comp"])),
                ui.nav_panel("📝 List Setup", render_clean_table(data["df_plist"])),
                ui.nav_panel(
                    "⚠️ Kurang Setup",
                    render_clean_table(data["df_kurang"]) if not data["df_kurang"].empty else ui.div("✅ Semua Tercover!", style="background: #C6F6D5; color: #38A169; font-weight: bold; padding: 1rem; border-radius: 8px; text-align: center;")
                ),
                ui.nav_panel(
                    "📦 Outstanding",
                    render_clean_table(data["df_out"]) if not data["df_out"].empty else ui.div("✅ Tidak ada Outstanding!", style="background: #C6F6D5; color: #38A169; font-weight: bold; padding: 1rem; border-radius: 8px; text-align: center;")
                )
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
            style="padding: 12px 20px; background: #D1FAE5; border: 1.5px solid #A7F3D0; border-radius: 16px; display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 1rem;"
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
            ui.div(
                section_dropdown_header("OPERATIONAL", "operational", dropdown_operational()),
                ui.div(
                    sidebar_menu_button("Database Ongkir In/Out", "Database Ongkir In/Out", cur),
                    sidebar_menu_button("Stock Minus", "Stock Minus", cur),
                    sidebar_menu_button("Putaway System", "Putaway System", cur),
                    style="padding-left: 0.5rem;" if dropdown_operational() else "display: none;"
                ),
                section_dropdown_header("INVENTORY", "inventory", dropdown_inventory()),
                ui.div(
                    sidebar_menu_button("Stock Opname", "Stock Opname", cur),
                    sidebar_menu_button("Relokasi BIN", "Relokasi BIN", cur),
                    style="padding-left: 0.5rem;" if dropdown_inventory() else "display: none;"
                ),
                section_dropdown_header("REJECT & DEFECT", "reject", dropdown_reject()),
                ui.div(
                    sidebar_menu_button("Barang Rusak", "Barang Rusak", cur),
                    style="padding-left: 0.5rem;" if dropdown_reject() else "display: none;"
                ),
                section_dropdown_header("EXTRAS", "extras", dropdown_extras()),
                ui.div(
                    sidebar_menu_button("Log Aktivitas", "Log Aktivitas", cur),
                    style="padding-left: 0.5rem;" if dropdown_extras() else "display: none;"
                ),
                style="flex: 1; overflow-y: auto; width: 100%;"
            ),
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
            style="width: 280px; min-width: 280px; padding: 1rem; background: linear-gradient(180deg, #111318 0%, #1A1D24 50%, #0D0F12 100%); border-right: 1px solid #2D3748; height: 100vh; display: flex; flex-direction: column; transition: width 0.3s ease;"
        )

    # --- MAIN ROUTER ---
    @output
    @render.ui
    def main_app_container():
        if not logged_in():
            return login_page_view()
            
        cur_view = main_menu()
        if cur_view in ["Database Ongkir In/Out", "Database Ongkir", "dashboard_ongkir"]:
            page_content = main_dashboard_view()
        elif cur_view == "Stock Minus":
            page_content = stock_minus_view()
        elif cur_view == "Putaway System":
            page_content = putaway_view()
        else:
            page_content = ui.div(
                ui.h2(f"Halaman: {cur_view}", style="color: #1A202C;"),
                ui.p("Halaman ini sedang dalam tahap pengembangan.", style="color: #718096;"),
                style="padding: 3rem; text-align: center; height: 70vh; display: flex; flex-direction: column; align-items: center; justify-content: center;"
            )
            
        return ui.div(
            render_sidebar(),
            ui.div(
                render_global_header(),
                page_content,
                style="flex: 1; height: 100vh; overflow-y: auto; padding: 1.5rem; background-color: #F7FAFC;"
            ),
            style="display: flex; width: 100vw; height: 100vh; overflow: hidden;"
        )

# ==========================================
# 11. INISIALISASI APLIKASI
# ==========================================
app = App(app_ui, server)