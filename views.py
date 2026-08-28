from datetime import datetime
from shiny import ui
from state import AppState
from config import safe_int

# ==============================================================================
# CSS & JAVASCRIPT ASSETS (PERSIS REFLEX)
# ==============================================================================
CUSTOM_HEAD = ui.head_content(
    ui.tags.link(rel="stylesheet", href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"),
    ui.tags.style("""
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
        body, html { height: 100%; width: 100%; overflow-x: hidden; background-color: #111318; margin: 0; padding: 0; }
        
        .reflex-spinner-red {
            width: 38px; height: 38px;
            border: 3.5px solid rgba(229, 9, 20, 0.2);
            border-top-color: #E50914; border-radius: 50%;
            animation: reflexSpin 0.75s linear infinite;
        }
        @keyframes reflexSpin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

        #global_reflex_loading { display: none; }
        body.process-running #global_reflex_loading {
            display: flex !important; position: fixed !important;
            top: 0 !important; left: 0 !important; width: 100vw !important; height: 100vh !important;
            background: rgba(0, 0, 0, 0.5) !important; z-index: 99999 !important;
            align-items: center !important; justify-content: center !important;
        }

        @keyframes popIn { 0% { transform: scale(0.5); opacity: 0; } 70% { transform: scale(1.15); opacity: 1; } 100% { transform: scale(1); opacity: 1; } }
        .animate-pop { animation: popIn 0.45s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards; }
        
        #shiny-notification-panel { top: 25px !important; right: 25px !important; bottom: auto !important; left: auto !important; position: fixed !important; z-index: 999999 !important; width: 360px !important; }
        .shiny-notification { border-radius: 10px !important; box-shadow: 0 10px 25px rgba(0,0,0,0.18) !important; font-weight: 700 !important; font-size: 13px !important; padding: 14px 18px !important; margin-bottom: 10px !important; }
        .shiny-notification-message { background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important; color: #FFFFFF !important; border: none !important; }
        .shiny-notification-error { background: linear-gradient(135deg, #E50914 0%, #B20710 100%) !important; color: #FFFFFF !important; border: none !important; }
        .shiny-notification-warning { background: linear-gradient(135deg, #DD6B20 0%, #C05621 100%) !important; color: #FFFFFF !important; border: none !important; }

        .custom-clean-table { width: 100%; border-collapse: collapse; font-size: 13px; text-align: left; }
        .custom-clean-table th { background: #EDF2F7; color: #1A202C; font-weight: bold; font-size: 12px; padding: 10px; white-space: nowrap; border-bottom: 1px solid #CBD5E0; }
        .custom-clean-table td { color: #2D3748; padding: 8px 10px; white-space: nowrap; border-bottom: 1px solid #EDF2F7; }
        .custom-clean-table tr:hover { background-color: #F8FAFC; }
        
        .btn-red-gradient {
            background: linear-gradient(135deg, #E50914 0%, #B20710 100%) !important;
            color: #FFFFFF !important; font-weight: 800 !important; border-radius: 6px !important;
            border: none !important; cursor: pointer; box-shadow: 0 4px 12px rgba(229, 9, 20, 0.25);
            padding: 0.75rem 1.5rem; transition: all 0.2s ease;
        }
        .btn-red-gradient:hover { filter: brightness(1.1); }
        .btn-locked { background-color: #E50914 !important; opacity: 0.5 !important; color: white !important; font-weight: bold !important; border-radius: 6px !important; cursor: not-allowed !important; border: none !important; padding: 0.75rem 1.5rem; }

        .reflex-upload-container {
            border: 2px dashed #000000 !important;   /* <-- Ganti warna di sini */
            border-radius: 8px;
            background: #F8FAFC;
            padding: 1.25rem 1.5rem;
            min-height: 85px;
            width: 100%;
            display: flex !important;
            align-items: center !important;
            justify-content: flex-start !important;
            position: relative;
            transition: all 0.2s ease;
        }
        .reflex-upload-container:hover { border-color: #C5A059; background-color: #FFFFFF; }
        .reflex-upload-container .shiny-input-container { margin-bottom: 0 !important; width: 100%; display: flex !important; align-items: center !important; }
        .reflex-upload-container .input-group { display: flex !important; align-items: center !important; width: 100% !important; margin-bottom: 0 !important; }
        .reflex-upload-container .input-group-prepend, .reflex-upload-container .input-group-btn { display: flex !important; align-items: center !important; margin: 0 !important; }
        .reflex-upload-container .btn-file {
            background-color: #C5A059 !important; color: white !important; font-weight: bold !important;
            border-radius: 6px !important; border: none !important; padding: 8px 18px !important;
            margin-right: 14px !important; display: inline-flex !important; align-items: center !important; height: 38px !important;
        }
        .reflex-upload-container input[type="text"].form-control {
            background-color: transparent !important; border: none !important; color: #38A169 !important;
            font-weight: 700 !important; font-size: 14px !important; box-shadow: none !important;
            padding: 0 !important; height: 38px !important; line-height: 38px !important; display: flex !important;
            align-items: center !important; width: 100% !important; flex: 1 1 auto !important;
            overflow: hidden !important; text-overflow: ellipsis !important; white-space: nowrap !important;
        }
        .reflex-upload-container input[type="text"].form-control::placeholder { color: #718096 !important; font-weight: normal !important; font-size: 13px !important; }

        .reflex-upload-container .shiny-file-input-progress,
        .reflex-upload-container .progress,
        .csv-batch-box .shiny-file-input-progress,
        .csv-batch-box .progress { display: none !important; visibility: hidden !important; height: 0 !important; margin: 0 !important; padding: 0 !important; opacity: 0 !important; }

        .csv-batch-box {
            border: 2px dashed #E50914 !important; border-radius: 12px; background: #FFF5F5;
            padding: 2rem 1.5rem; width: 100%; text-align: center; margin-bottom: 1.25rem;
            display: flex; flex-direction: column; align-items: center; justify-content: center;
        }
        .csv-batch-box .shiny-input-container { margin-bottom: 0 !important; width: 100%; }
        .csv-batch-box .input-group { display: flex !important; align-items: center !important; width: 100% !important; margin-bottom: 0 !important; }
        .csv-batch-box .btn-file { background: #1A202C !important; color: #FFFFFF !important; font-weight: 700 !important; border-radius: 6px !important; border: none !important; padding: 8px 16px !important; margin-right: 10px !important; }
        .csv-batch-box input[type="text"].form-control { background-color: transparent !important; border: none !important; color: #2D3748 !important; font-weight: 700 !important; font-size: 13px !important; box-shadow: none !important; }

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
                } else { elTimer.innerText = "00:00:00"; }
            }
        }, 1000);
    """)
)

# Helper UI Components
def metric_box(title: str, val_str: str, text_color: str, bg_gradient: str):
    return ui.div(
        ui.div(title, style="color: #4A5568; font-size: 11px; font-weight: 800; text-transform: uppercase; margin-bottom: 4px;"),
        ui.div(val_str, style=f"color: {text_color}; font-size: 20px; font-weight: 800;"),
        style=f"background: {bg_gradient}; padding: 1rem; border-radius: 12px; border: 1px solid rgba(0,0,0,0.06); text-align: center; width: 100%; box-shadow: 0 2px 6px rgba(0,0,0,0.03);"
    )

def dark_metric_box(title: str, val_str: str, border_color: str):
    return ui.div(
        ui.div(title, style="color: #A0AEC0; font-size: 11px; font-weight: bold; margin-bottom: 4px;"),
        ui.div(val_str, style=f"color: {border_color}; font-size: 22px; font-weight: bold;"),
        style=f"background: #1A1A1A; padding: 1rem; border-radius: 8px; border-left: 4px solid {border_color}; width: 100%; text-align: center;"
    )

def render_clean_table(headers: list, rows: list):
    if not rows or len(rows) == 0:
        return ui.div(ui.div("Tidak ada data untuk ditampilkan.", style="color: #718096; padding: 1.5rem; font-style: italic; text-align: center;"), style="background: white; border-radius: 8px; border: 1px solid #E2E8F0; width: 100%;")
    th_cells = [ui.tags.th(str(h)) for h in headers]
    tr_rows = [ui.tags.tr(*[ui.tags.td(str(c)) for c in r]) for r in rows]
    return ui.div(ui.tags.table(ui.tags.thead(ui.tags.tr(*th_cells)), ui.tags.tbody(*tr_rows), class_="custom-clean-table"), style="overflow-x: auto; width: 100%; background: white; border-radius: 8px; padding: 0.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05); border: 1px solid #E2E8F0;")

def success_modal(show: bool):
    if not show: return ui.div()
    return ui.div(
        ui.div(
            ui.div(ui.tags.i(class_="fa-solid fa-check", style="font-size: 55px; color: white;"), class_="animate-pop", style="background: linear-gradient(135deg, #4ade80 0%, #16a34a 100%); border-radius: 50%; width: 95px; height: 95px; box-shadow: 0 10px 30px rgba(74, 222, 128, 0.5); margin-bottom: 10px; display: flex; align-items: center; justify-content: center;"),
            ui.h2("Success!", style="font-size: 32px; color: #1A202C; font-weight: 800; margin: 0;"),
            style="display: flex; flex-direction: column; align-items: center; justify-content: center; background: transparent;"
        ),
        ui.tags.script("""
            document.body.classList.remove('process-running');
            setTimeout(function() {
                let el = document.getElementById('success-modal-overlay');
                if (el) { el.remove(); Shiny.setInputValue('close_success_modal_event', Math.random(), {priority: 'event'}); }
            }, 1800);
        """),
        id="success-modal-overlay",
        onclick="document.body.classList.remove('process-running'); this.remove(); Shiny.setInputValue('close_success_modal_event', Math.random(), {priority: 'event'});",
        style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: 99999; background: rgba(255, 255, 255, 0.7); backdrop-filter: blur(5px); display: flex; align-items: center; justify-content: center; cursor: pointer;"
    )

def error_modal(show: bool, message: str = ""):
    if not show: return ui.div()
    return ui.div(
        ui.div(
            ui.div(ui.tags.i(class_="fa-solid fa-xmark", style="font-size: 55px; color: white;"), class_="animate-pop", style="background: linear-gradient(135deg, #EF4444 0%, #B91C1C 100%); border-radius: 50%; width: 95px; height: 95px; box-shadow: 0 10px 30px rgba(239, 68, 68, 0.5); margin-bottom: 10px; display: flex; align-items: center; justify-content: center;"),
            ui.h2("Gagal / Error!", style="font-size: 30px; color: #E53E3E; font-weight: 800; margin: 0 0 6px 0;"),
            ui.p(message if message else "Terjadi kesalahan saat memproses data!", style="color: #2D3748; font-size: 15px; font-weight: 700; text-align: center; max-width: 450px; margin: 0;"),
            style="display: flex; flex-direction: column; align-items: center; justify-content: center; background: transparent;"
        ),
        ui.tags.script("""
            document.body.classList.remove('process-running');
            setTimeout(function() {
                let el = document.getElementById('error-modal-overlay');
                if (el) { el.remove(); Shiny.setInputValue('close_error_modal_event', Math.random(), {priority: 'event'}); }
            }, 2600);
        """),
        id="error-modal-overlay",
        onclick="document.body.classList.remove('process-running'); this.remove(); Shiny.setInputValue('close_error_modal_event', Math.random(), {priority: 'event'});",
        style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: 99999; background: rgba(255, 255, 255, 0.7); backdrop-filter: blur(5px); display: flex; align-items: center; justify-content: center; cursor: pointer;"
    )

def static_loading_spinner():
    return ui.div(
        ui.div(
            ui.div(class_="reflex-spinner-red"),
            ui.span("Sedang memproses data, mohon tunggu...", style="font-weight: bold; color: #1A202C; font-size: 14px; text-align: center;"),
            style="background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 10px 25px rgba(0, 0, 0, 0.25); display: flex; flex-direction: column; align-items: center; gap: 1rem; min-width: 280px;"
        ),
        id="global_reflex_loading"
    )

def custom_uploader_box(id_str: str, title: str, placeholder: str = "200MB per file • XLSX, CSV"):
    return ui.div(
        ui.span(title, style="font-weight: bold; color: #1A202C; font-size: 14px; margin-bottom: 0.25rem; display: block;"),
        ui.div(
            ui.input_file(id_str, None, accept=[".xlsx", ".xls", ".csv"], multiple=False, button_label=ui.tags.span(ui.tags.i(class_="fa-solid fa-upload", style="margin-right: 6px; font-size: 14px;"), "Upload"), placeholder=placeholder),
            class_="reflex-upload-container"
        ),
        style="flex: 1; min-width: 260px; margin-bottom: 0.5rem;"
    )

# Page Views
def compare_system_view(state: AppState):
    upload_section = ui.div(
        ui.h4("📥 1. Upload File Utama Stock System", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 0.5rem;"),
        ui.div(
            custom_uploader_box("uploader_sys1", "Stock System Start Shift"),
            custom_uploader_box("uploader_sys2", "Stock System End Shift"),
            style="display: flex; gap: 1rem; width: 100%; margin-bottom: 1.25rem; flex-wrap: wrap;"
        ),
        ui.h4("📤 2. Upload Dokumen Pendukung (Stok Berkurang)", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 0.5rem;"),
        ui.div(
            custom_uploader_box("uploader_track", "Upload Stock Tracking"),
            custom_uploader_box("uploader_rto_out", "Upload RTO OUT"),
            style="display: flex; gap: 1rem; width: 100%; margin-bottom: 1.25rem; flex-wrap: wrap;"
        ),
        ui.h4("📥 3. Upload Dokumen Pendukung (Stok Bertambah)", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 0.5rem;"),
        ui.div(
            custom_uploader_box("uploader_po", "Upload Purchase Order (PO)"),
            custom_uploader_box("uploader_rto_in", "Upload RTO IN"),
            custom_uploader_box("uploader_refund", "Upload Mutasi REFUND"),
            style="display: flex; gap: 1rem; width: 100%; margin-bottom: 1.25rem; flex-wrap: wrap;"
        ),
        ui.output_ui("compare_system_action_btn_ui"),
        style="width: 100%; background: white; padding: 1.5rem; border-radius: 12px; border: 1px solid #E2E8F0; margin-bottom: 1.5rem;"
    )

    results_ui = ui.output_ui("compare_system_results_container")

    return ui.div(
        upload_section,
        results_ui,
        style="width: 100%; padding: 1rem;"
    )
def stock_minus_view(state: AppState):
    return ui.div(
        ui.div(
            ui.span("Upload File STOCK MINUS", style="font-weight: bold; color: #1A202C; font-size: 14px; margin-bottom: 0.25rem; display: block;"),
            ui.div(ui.input_file("upload_stock_file", None, accept=[".xlsx", ".xls"], multiple=False, button_label=ui.tags.span(ui.tags.i(class_="fa-solid fa-upload", style="margin-right: 6px; font-size: 14px;"), "Upload"), placeholder="200MB per file • XLSX, XLS"), class_="reflex-upload-container"),
            ui.output_ui("stock_minus_action_btn_ui"),
            style="width: 100%; background: white; padding: 1.25rem; border-radius: 10px; border: 1px solid #E2E8F0; margin-bottom: 1.25rem;"
        ),
        ui.output_ui("stock_minus_results_container"),
        style="width: 100%; padding: 1rem;"
    )

def putaway_view(state: AppState):
    cur_area = state.area_putaway()
    if cur_area != "":
        area_content = ui.div(
            ui.div(ui.tags.i(class_="fa-solid fa-map-pin", style="color: #3182ce; font-size: 18px; margin-right: 8px;"), ui.span("Area Terpilih: ", style="font-weight: normal; color: #2c5282; font-size: 13px;"), ui.span(cur_area, style="font-weight: bold; color: #2c5282; font-size: 13px;"), style="background: #ebf8ff; border-left: 4px solid #3182ce; padding: 10px 16px; border-radius: 6px; width: 100%; display: flex; align-items: center; margin-bottom: 1rem;"),
            ui.div(custom_uploader_box("ds_putaway_file", "Upload DS PUTAWAY"), custom_uploader_box("asal_putaway_file", "Upload ASAL BIN"), style="display: flex; gap: 1rem; width: 100%; margin-bottom: 1rem; flex-wrap: wrap;"),
            ui.output_ui("putaway_action_btn_ui"), style="width: 100%;"
        )
    else:
        area_content = ui.div("⚠️ Silakan pilih Area Putaway di atas terlebih dahulu.", style="color: #DD6B20; font-weight: bold; font-style: italic; background: #FFFFF0; border: 1px solid #F6E05E; padding: 1rem; border-radius: 8px; width: 100%; text-align: center;")

    top_section = ui.div(
        ui.span("📍 Pilih Area Putaway", style="font-weight: bold; color: #1A202C; font-size: 14px; margin-bottom: 0.5rem; display: block;"),
        ui.tags.select(ui.tags.option("-- Pilih Area Putaway --", value=""), ui.tags.option("DC LANTAI 1", value="DC LANTAI 1"), ui.tags.option("DC LANTAI 2", value="DC LANTAI 2"), ui.tags.option("DC LANTAI 3", value="DC LANTAI 3"), ui.tags.option("JERSEY ZONE", value="JERSEY ZONE"), id="area_putaway_select", onchange="Shiny.setInputValue('select_area_putaway', this.value, {priority: 'event'})", style="width: 100%; padding: 10px 14px; background-color: #FFFFFF; color: #000000; font-weight: bold; font-size: 14px; border: 1.5px solid #CBD5E0; border-radius: 8px; outline: none; cursor: pointer; margin-bottom: 1rem;"),
        area_content, style="width: 100%; background: white; padding: 1.25rem; border-radius: 10px; border: 1px solid #E2E8F0; margin-bottom: 1.25rem;"
    )
    return ui.div(top_section, ui.output_ui("putaway_results_container"), style="width: 100%; padding: 1rem;")

def main_dashboard_view(state: AppState):
    STYLE_LABEL_CSS = "font-size: 11px; font-weight: 800; color: #1A202C; margin-bottom: 2px; letter-spacing: 0.5px; display: block;"
    tab1_content = ui.div(
        ui.div(
            ui.div(ui.span("📝", style="font-size: 20px; margin-right: 8px;"), ui.h4("Input Transaksi Manual", style="font-size: 16px; font-weight: bold; color: #1A202C; margin: 0;"), style="display: flex; align-items: center; margin-bottom: 0.75rem;"),
            ui.hr(style="border-color: #CBD5E0; margin-bottom: 1rem;"),
            ui.div(ui.span("NAMA SUPPLIER", style=STYLE_LABEL_CSS), ui.tags.input(id="input_supplier", type="text", placeholder="Masukkan Nama Supplier...", style="background-color: #FFFFFF; color: #111111; border: 2px solid #4A5568; border-radius: 8px; font-weight: 600; padding: 0.6rem 0.8rem; width: 100%; outline: none;"), style="margin-bottom: 0.75rem; width: 100%;"),
            ui.div(ui.div(ui.span("EKSPEDISI", style=STYLE_LABEL_CSS), ui.tags.input(id="input_ekspedisi", type="text", placeholder="Nama Ekspedisi...", style="background-color: #FFFFFF; color: #111111; border: 2px solid #4A5568; border-radius: 8px; font-weight: 600; padding: 0.6rem 0.8rem; width: 100%; outline: none;"), style="flex: 1; margin-right: 8px;"), ui.div(ui.span("TOTAL KOLI", style=STYLE_LABEL_CSS), ui.tags.input(id="input_koli", type="number", value="1", placeholder="Jumlah Koli", style="background-color: #FFFFFF; color: #111111; border: 2px solid #4A5568; border-radius: 8px; font-weight: 600; padding: 0.6rem 0.8rem; width: 100%; outline: none;"), style="flex: 1;"), style="display: flex; width: 100%; margin-bottom: 0.75rem;"),
            ui.div(ui.div(ui.span("TOTAL ONGKIR (RP)", style=STYLE_LABEL_CSS), ui.tags.input(id="input_ongkir", type="number", value="0", placeholder="Rp 0", style="background-color: #FFFFFF; color: #111111; border: 2px solid #4A5568; border-radius: 8px; font-weight: 600; padding: 0.6rem 0.8rem; width: 100%; outline: none;"), style="flex: 1; margin-right: 8px;"), ui.div(ui.span("TANGGAL", style=STYLE_LABEL_CSS), ui.tags.input(id="input_tgl", type="date", value=datetime.now().strftime("%Y-%m-%d"), style="background-color: #FFFFFF; color: #111111; border: 2px solid #4A5568; border-radius: 8px; font-weight: 600; padding: 0.6rem 0.8rem; width: 100%; outline: none;"), style="flex: 1;"), style="display: flex; width: 100%; margin-bottom: 1.25rem;"),
            ui.tags.button("🚀 SIMPAN DATA ONGKIR", onclick="document.body.classList.add('process-running'); Shiny.setInputValue('btn_save_ongkir_manual', {supplier: document.getElementById('input_supplier').value, ekspedisi: document.getElementById('input_ekspedisi').value, koli: document.getElementById('input_koli').value, ongkir: document.getElementById('input_ongkir').value, tgl: document.getElementById('input_tgl').value}, {priority: 'event'});", class_="btn-red-gradient", style="width: 100%; height: 48px; font-size: 14px;"),
            style="background: #FFFFFF; border-radius: 16px; border: 2px solid #CBD5E0; box-shadow: 0 10px 25px rgba(0,0,0,0.03); padding: 1.8rem; flex: 1; min-width: 320px;"
        ),
        ui.div(
            ui.div(ui.span("📁", style="font-size: 20px; margin-right: 8px;"), ui.h4("Batch CSV Upload", style="font-size: 16px; font-weight: bold; color: #1A202C; margin: 0;"), style="display: flex; align-items: center; margin-bottom: 0.75rem;"),
            ui.hr(style="border-color: #CBD5E0; margin-bottom: 1rem;"),
            ui.div(ui.div(ui.span("☁️", style="font-size: 24px;"), style="padding: 10px; background: #E2E8F0; border-radius: 50%; width: 50px; height: 50px; display: flex; align-items: center; justify-content: center; margin-bottom: 8px;"), ui.span("atau tarik & lepaskan file CSV di sini", style="font-size: 13px; color: #4A5568; font-weight: bold; margin-bottom: 10px;"), ui.input_file("upload_csv_batch", None, accept=[".csv"], multiple=False, button_label="Pilih File CSV", placeholder="Pilih file CSV..."), class_="csv-batch-box"),
            ui.tags.button("⚡ EXECUTE BATCH UPLOAD", onclick="document.body.classList.add('process-running'); Shiny.setInputValue('btn_execute_batch_upload', Math.random(), {priority: 'event'});", style="background: #1A202C; color: #FFFFFF !important; font-weight: 800; border-radius: 10px; cursor: pointer; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15); width: 100%; height: 48px; border: none; font-size: 14px;"),
            style="background: #FFFFFF; border-radius: 16px; border: 2px solid #CBD5E0; box-shadow: 0 10px 25px rgba(0,0,0,0.03); padding: 1.8rem; flex: 1; min-width: 320px;"
        ), style="display: flex; flex-wrap: wrap; gap: 1.25rem; width: 100%; margin-top: 1.5rem;"
    )

    selected_count = len(state.selected_ids())
    del_btn_ui = ui.tags.button(f"🗑️ HAPUS ({selected_count}) DATA", onclick="Shiny.setInputValue('btn_open_delete_modal', Math.random(), {priority: 'event'})", style="background: #E53E3E; color: white; border: none; padding: 6px 14px; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 13px;") if selected_count > 0 else ui.div()
    select_options = [ui.tags.option(opt, value=opt, selected=(opt == state.filter_ekspedisi())) for opt in state.get_list_ekspedisi_options()]
    table_rows = [
        ui.tags.tr(
            ui.tags.td(ui.tags.input(type="checkbox", checked=(str(r.get("id", "")) in set(state.selected_ids())), onchange=f"Shiny.setInputValue('toggle_row_id', '{r.get('id', '')}', {{priority: 'event'}})")),
            ui.tags.td(str(r.get("created_at", r.get("tanggal", "")))), ui.tags.td(str(r.get("supplier", ""))), ui.tags.td(str(r.get("ekspedisi", ""))),
            ui.tags.td(str(safe_int(r.get("total_koli", r.get("koli", 0))))), ui.tags.td(f"Rp {safe_int(r.get('total_ongkir', 0)):,}")
        ) for r in state.get_filtered_ongkir()
    ]

    tab2_content = ui.div(
        ui.div(ui.div(ui.span("FILTER EKSPEDISI:", style="font-size: 12px; font-weight: 800; color: #111111; margin-right: 8px;"), ui.tags.select(*select_options, id="select_filter_ekspedisi", onchange="Shiny.setInputValue('change_filter_ekspedisi', this.value, {priority: 'event'})", style="background-color: #FFFFFF !important; color: #000000 !important; border: 2.5px solid #1A202C !important; border-radius: 8px !important; font-weight: 800 !important; width: 220px; padding: 6px 10px; cursor: pointer;"), style="display: flex; align-items: center;"), del_btn_ui, style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin-top: 1.5rem; margin-bottom: 0.5rem;"),
        ui.div(
            metric_box("💰 BIAYA ALL", state.metric_total_biaya_all(), "#C53030", "linear-gradient(135deg, #FED7D7 0%, #FEB2B2 100%)"),
            metric_box("📦 KOLI ALL", state.metric_total_koli_all(), "#1A202C", "linear-gradient(135deg, #E2E8F0 0%, #CBD5E0 100%)"),
            metric_box("📊 AVG COST ALL", state.metric_avg_cost_all(), "#C53030", "linear-gradient(135deg, #FED7D7 0%, #FEB2B2 100%)"),
            metric_box("🚚 BIAYA DATANG", state.metric_biaya_datang(), "#276749", "linear-gradient(135deg, #C6F6D5 0%, #9AE6B4 100%)"),
            metric_box("📦 KOLI DATANG", state.metric_koli_datang(), "#276749", "linear-gradient(135deg, #C6F6D5 0%, #9AE6B4 100%)"),
            metric_box("🔄 BIAYA RTO", state.metric_biaya_rto(), "#9B2C2C", "linear-gradient(135deg, #FED7D7 0%, #FEB2B2 100%)"),
            style="display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 1rem; width: 100%; margin-bottom: 1.5rem;"
        ),
        ui.div(ui.tags.table(ui.tags.thead(ui.tags.tr(ui.tags.th("SELECT", style="text-align: center;"), ui.tags.th("TANGGAL"), ui.tags.th("SUPPLIER"), ui.tags.th("EKSPEDISI"), ui.tags.th("KOLI"), ui.tags.th("TOTAL ONGKIR")), style="background-color: #CBD5E0 !important;"), ui.tags.tbody(*table_rows) if len(table_rows) > 0 else ui.tags.tr(ui.tags.td("Tidak ada transaksi ongkir.", colspan="6", style="text-align: center; color: #718096; padding: 2rem;")), class_="custom-clean-table"), style="background: #FFFFFF; border-radius: 16px; border: 2.5px solid #1A202C; padding: 1rem; width: 100%; box-shadow: 0 10px 25px rgba(0,0,0,0.04); overflow-x: auto;"),
        style="width: 100%;"
    )
    return ui.div(ui.navset_card_tab(ui.nav_panel("📥 INPUT & BATCH DATA", tab1_content), ui.nav_panel("📊 SUMMARY & HISTORY", tab2_content)), style="width: 100%; background-color: #F7FAFC; min-height: 100vh; padding: 1rem;")

def menu_item(label: str, target_menu: str, current_menu: str):
    is_active = (current_menu == target_menu)
    bg_style = "background: linear-gradient(135deg, #E50914 0%, #B20710 100%); color: #FFFFFF; font-weight: 700; box-shadow: 0 4px 12px rgba(229, 9, 20, 0.4);" if is_active else "background: transparent; color: #CBD5E0; font-weight: 500;"
    return ui.tags.button(label, onclick=f"Shiny.setInputValue('select_menu_item', '{target_menu}', {{priority: 'event'}})", style=f"width: 100%; text-align: left; padding: 0.5rem 0.75rem; margin-bottom: 3px; border-radius: 6px; font-size: 0.85rem; border: none; cursor: pointer; justify-content: flex-start; transition: all 0.2s ease; {bg_style}")

def section_dropdown_header(title: str, dropdown_key: str, is_open: bool):
    icon_tag = "fa-chevron-down" if is_open else "fa-chevron-right"
    return ui.tags.div(ui.tags.span(title, style="font-size: 11px; font-weight: bold; color: #FFFFFF; letter-spacing: 0.05em;"), ui.tags.i(class_=f"fa-solid {icon_tag}", style="font-size: 12px; color: #FFFFFF;"), onclick=f"Shiny.setInputValue('toggle_dropdown_section', '{dropdown_key}', {{priority: 'event'}})", style="display: flex; justify-content: space-between; align-items: center; width: 100%; padding: 0.5rem 0.6rem; border-radius: 6px; cursor: pointer; background: rgba(255, 255, 255, 0.05); margin-top: 0.8rem; margin-bottom: 0.3rem;")

def sidebar(state: AppState):
    cur_menu = state.main_menu()

    # --- KONDISI KETIKA SIDEBAR DITUTUP (HANYA ICON BARS) ---
    if not state.sidebar_open():
        return ui.div(
            ui.tags.button(
                ui.tags.i(class_="fa-solid fa-bars", style="font-size: 18px; color: #FFFFFF;"),
                onclick="Shiny.setInputValue('btn_toggle_sidebar', Math.random(), {priority: 'event'})",
                style="background: transparent; border: none; cursor: pointer; padding: 0.5rem; border-radius: 6px;"
            ),
            style="width: 60px; min-width: 60px; padding: 1rem 0.5rem; background: #111318; border-right: 1px solid #2D3748; height: 100vh; display: flex; flex-direction: column; align-items: center;"
        )

    # --- KONDISI KETIKA SIDEBAR TERBUKA PENUH ---
    return ui.div(
        # 1. HEADER LOGO + BRAND + TOMBOL CLOSE (<<)
        ui.div(
            ui.div(
                # Box Logo Merah
                ui.div(
                    ui.tags.i(class_="fa-solid fa-boxes-stacked", style="color: #FFFFFF; font-size: 16px;"),
                    style="""
                        width: 38px; height: 38px; 
                        background: linear-gradient(135deg, #E50914 0%, #B20710 100%); 
                        border-radius: 8px; display: flex; align-items: center; justify-content: center; 
                        box-shadow: 0 4px 12px rgba(229, 9, 20, 0.4); flex-shrink: 0;
                    """
                ),
                # Teks Brand 2 Baris
                ui.div(
                    ui.span("ZKN LOGISTIC", style="color: #E50914; font-weight: 900; font-size: 14px; letter-spacing: 0.5px; line-height: 1.2;"),
                    ui.span("WAREHOUSE SYSTEM", style="color: #FFFFFF; font-weight: 700; font-size: 10px; letter-spacing: 1.5px; opacity: 0.9;"),
                    style="display: flex; flex-direction: column; justify-content: center;"
                ),
                style="display: flex; align-items: center; gap: 10px;"
            ),
            # Tombol Collapse Sidebar (<<)
            ui.tags.button(
                ui.tags.i(class_="fa-solid fa-angles-left", style="font-size: 14px; color: #CBD5E0;"),
                onclick="Shiny.setInputValue('btn_toggle_sidebar', Math.random(), {priority: 'event'})",
                style="background: transparent; border: none; cursor: pointer; padding: 6px; border-radius: 4px; display: flex; align-items: center;"
            ),
            style="""
                display: flex; justify-content: space-between; width: 100%; align-items: center; 
                margin-bottom: 0.8rem; padding-bottom: 0.6rem; border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            """
        ),

        # 2. DAFTAR MENU SIDEBAR (SCROLLABLE)
        ui.div(
            # OPERATIONAL
            ui.div(
                section_dropdown_header("OPERATIONAL", "operational", state.dropdown_operational()),
                ui.div(
                    *[menu_item(item, item, cur_menu) for item in state.get_menu_operational()],
                    style="width: 100%; padding-left: 0.5rem; display: flex; flex-direction: column;" if state.dropdown_operational() else "display: none;"
                ),
                style="width: 100%;"
            ),
            # INVENTORY
            ui.div(
                section_dropdown_header("INVENTORY", "inventory", state.dropdown_inventory()),
                ui.div(
                    *[menu_item(item, item, cur_menu) for item in state.get_menu_inventory()],
                    style="width: 100%; padding-left: 0.5rem; display: flex; flex-direction: column;" if state.dropdown_inventory() else "display: none;"
                ),
                style="width: 100%;"
            ),
            # REJECT & DEFECT
            ui.div(
                section_dropdown_header("REJECT & DEFECT", "reject", state.dropdown_reject()),
                ui.div(
                    *[menu_item(item, item, cur_menu) for item in state.get_menu_reject()],
                    style="width: 100%; padding-left: 0.5rem; display: flex; flex-direction: column;" if state.dropdown_reject() else "display: none;"
                ),
                style="width: 100%;"
            ),
            # EXTRAS
            ui.div(
                section_dropdown_header("EXTRAS", "extras", state.dropdown_extras()),
                ui.div(
                    *[menu_item(item, item, cur_menu) for item in state.get_menu_extras()],
                    style="width: 100%; padding-left: 0.5rem; display: flex; flex-direction: column;" if state.dropdown_extras() else "display: none;"
                ),
                style="width: 100%;"
            ),
            style="width: 100%; flex: 1; overflow-y: auto; padding-right: 4px;"
        ),

        # 3. TOMBOL LOGOUT SISTEM
        ui.div(
            ui.tags.button(
                ui.tags.span(
                    ui.tags.i(class_="fa-solid fa-right-from-bracket", style="margin-right: 8px; font-size: 14px;"),
                    ui.span("Logout Sistem", style="font-weight: bold; font-size: 13px;")
                ),
                onclick="Shiny.setInputValue('btn_execute_logout', Math.random(), {priority: 'event'})",
                class_="btn-red-gradient",
                style="width: 100%; padding: 0.5rem; border-radius: 6px; display: flex; align-items: center; justify-content: center;"
            ),
            style="width: 100%; padding-top: 0.8rem; border-top: 1px solid rgba(255, 255, 255, 0.1); margin-top: auto;"
        ),

        # Styling Container Utama Sidebar
        style="""
            width: 280px; min-width: 280px; padding: 1rem;
            background: linear-gradient(180deg, #111318 0%, #1A1D24 50%, #0D0F12 100%);
            border-right: 1px solid #2D3748; height: 100vh; display: flex; flex-direction: column;
            align-items: flex-start; transition: width 0.3s ease;
        """
    )
def login_page():
    return ui.div(
        ui.div(
            ui.div(
                ui.div(ui.div(style="width: 12px; height: 38px; background: #E50914; border-radius: 4px; margin-right: 12px;"), ui.div(ui.h2("LOGISTIC DISTRIBUTION", style="color: #FFFFFF; font-size: 22px; font-weight: 800; letter-spacing: 1px; margin: 0; line-height: 1.1;"), ui.span("CENTER WAREHOUSE • SURABAYA", style="color: #E50914; font-size: 11px; font-weight: 700; letter-spacing: 2px;"), style="display: flex; flex-direction: column;"), style="display: flex; align-items: center; margin-bottom: 1.25rem;"),
                ui.hr(style="border-color: rgba(255, 255, 255, 0.1); margin-bottom: 1.25rem;"),
                ui.p("Silakan masuk dengan akun resmi gudang Anda.", style="color: #B0B0B0; font-size: 13px; margin-bottom: 1.5rem;"),
                ui.div(ui.span("USERNAME", style="font-size: 11px; font-weight: 700; color: #FFFFFF; letter-spacing: 1px; margin-bottom: 4px; display: block;"), ui.tags.input(id="login_username_field", type="text", placeholder="Masukkan username...", onkeydown="if (event.key === 'Enter') document.getElementById('btn_sign_in').click();", style="background: rgba(0, 0, 0, 0.75); border: 1px solid rgba(229, 9, 20, 0.4); color: #FFFFFF; border-radius: 10px; padding: 0.8rem 1rem; width: 100%; outline: none;"), style="margin-bottom: 1rem;"),
                ui.div(ui.span("PASSWORD", style="font-size: 11px; font-weight: 700; color: #FFFFFF; letter-spacing: 1px; margin-bottom: 4px; display: block;"), ui.tags.input(id="login_password_field", type="password", placeholder="Masukkan password...", onkeydown="if (event.key === 'Enter') document.getElementById('btn_sign_in').click();", style="background: rgba(0, 0, 0, 0.75); border: 1px solid rgba(229, 9, 20, 0.4); color: #FFFFFF; border-radius: 10px; padding: 0.8rem 1rem; width: 100%; outline: none;"), style="margin-bottom: 1.5rem;"),
                ui.div(style="height: 10px;"),
                ui.tags.button("SIGN IN TO SYSTEM →", id="btn_sign_in", onclick="Shiny.setInputValue('btn_submit_login', {user: document.getElementById('login_username_field').value, pass: document.getElementById('login_password_field').value}, {priority: 'event'})", class_="btn-red-gradient", style="width: 100%; height: 48px; font-size: 14px; font-weight: 800; border-radius: 10px; cursor: pointer; box-shadow: 0 4px 15px rgba(229, 9, 20, 0.4);"),
                ui.div("🟢 Warehouse Supporting Tools v2.0", style="color: #888888; font-size: 12px; text-align: center; margin-top: 10px;"),
                style="display: flex; flex-direction: column; width: 100%;"
            ),
            style="width: 100%; max-width: 520px; padding: 3rem 2.5rem; background: rgba(12, 12, 15, 0.88); backdrop-filter: blur(20px); border-radius: 20px; border: 1px solid rgba(255, 255, 255, 0.12); border-left: 5px solid #E50914; box-shadow: 0 25px 60px rgba(0, 0, 0, 0.85);"
        ),
        style="background-image: radial-gradient(circle at center, rgba(0, 0, 0, 0.15) 0%, rgba(0, 0, 0, 0.45) 100%), url('https://images.unsplash.com/photo-1553413077-190dd305871c?q=80&w=2070'); background-size: cover; background-position: center; width: 100vw; height: 100vh; display: flex; align-items: center; justify-content: center; padding: 2rem;"
    )

def global_header(state: AppState):
    return ui.div(
        ui.div(ui.div(style="width: 10px; height: 32px; background: #E50914; border-radius: 4px; margin-right: 12px;"), ui.div(ui.h3(state.main_menu(), style="font-size: 18px; color: #111111; font-weight: 800; margin: 0; line-height: 1.2;"), ui.span(f"Logged in as: {state.user_display_name()} ({state.role()})", style="font-size: 12px; color: #4A5568;"), style="display: flex; flex-direction: column; align-items: flex-start;"), style="display: flex; align-items: center;"),
        ui.div(
            ui.tags.button(ui.tags.i(class_="fa-solid fa-bullhorn", style="margin-right: 6px; color: #1A202C; font-size: 14px;"), "Panduan & Logic", onclick="Shiny.setInputValue('btn_open_panduan_modal', Math.random(), {priority: 'event'})", style="background: #E2E8F0; color: #1A202C; border: none; padding: 6px 14px; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 13px;"),
            ui.div(ui.div(ui.div(style="width: 8px; height: 8px; background: #10B981; border-radius: 50%; margin-right: 6px;"), ui.span("ONLINE", style="font-size: 12px; font-weight: 800; color: #065F46;"), style="display: flex; align-items: center;"), ui.div(ui.span(str(state.login_timestamp_ms()), id="login-time-store", style="display: none;"), ui.tags.i(class_="fa-regular fa-clock", style="font-size: 12px; color: #4A5568; margin-right: 4px;"), ui.span("00:00:00", id="live-timer", style="color: #4A5568; font-weight: bold; font-size: 12px; font-family: monospace;"), style="display: flex; align-items: center; justify-content: center;"), style="display: flex; flex-direction: column; align-items: center; gap: 2px;"),
            style="display: flex; align-items: center; gap: 1.25rem;"
        ),
        style="padding: 12px 20px; background: #D1FAE5; border: 1.5px solid #A7F3D0; border-radius: 16px; display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 1rem;"
    )