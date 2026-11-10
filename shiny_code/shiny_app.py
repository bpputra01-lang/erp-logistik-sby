import io
import time
from datetime import datetime
import pandas as pd
from config import get_supabase, safe_int
from shiny import App, Inputs, Outputs, Session, reactive, render, ui
from state import AppState
from views import (
    CUSTOM_HEAD, static_loading_spinner, success_modal, error_modal,
    render_clean_table, metric_box, dark_metric_box, BRANCH_BIN_MAPPING, 
    custom_uploader_box, compare_system_view, stock_minus_view, stock_opname_view,
    putaway_view, main_dashboard_view, sidebar, ongkir_tab2_view, compare_rto_view, 
    justification_so_view, cycle_count_view, login_page, ppa_audit_view, 
    cycle_count_analyzer_view, global_header, cross_check_real_system_view,
    balancing_stock_view, physical_inventory_list_view, validation_barcode_sku_view, percentage_display_view,excel_practice_view,
    auditor_view, memo_pengajuan_view, warehouse_activity_monitor_view, compliance_audit_view, instock_validation_view
)

app_ui = ui.page_fluid(
    CUSTOM_HEAD,
    static_loading_spinner(),
    ui.output_ui("global_success_modal_ui"),
    ui.output_ui("global_error_modal_ui"),
    ui.output_ui("main_root_container"),
    title="ZKN WAREHOUSE ERP",  # <-- TAMBAHKAN INI AGAR SHINY TIDAK MENGGANTI KE 'Shiny App'
    style="padding: 0; margin: 0; background-color: #111318;"
)

def server(input: Inputs, output: Outputs, session: Session):
    state = AppState()
    _last_filter_state = {"c_brands": [], "c_subs": [], "c_bins": []}
    _last_seen_fl_id = reactive.Value(None)
    
    # 🌟 Gunakan list 1 elemen agar aman antar-sesi (session-safe) tanpa butuh 'global'
    _is_fl_polling = [False]

    # 🔄 Cek data Supabase otomatis tiap 3 detik SECARA AMAN & ANTI-OVERLAP
    @reactive.effect
    async def _poll_fl_requests_from_supabase():
        # 🛑 1. Jangan jalankan jika belum login
        if not state.logged_in():
            return

        # ⏱️ 2. Jadwalkan timer berikutnya 3 detik dari sekarang
        reactive.invalidate_later(3)

        # 🛑 3. JIKA POLLING SESI INI MASIH BERJALAN, LEWATI SIKLUS INI
        if _is_fl_polling[0]:
            return

        _is_fl_polling[0] = True
        try:
            import asyncio
            import re
            from datetime import datetime

            client = get_supabase()
            if not client:
                _is_fl_polling[0] = False
                return

            def fetch_data():
                return client.table("jezpro_fl_requests").select("*").execute()

            # ⏱️ 4. Beri batas timeout 2.5 detik agar jika Supabase lambat, app tidak ikut menggantung
            res = await asyncio.wait_for(asyncio.to_thread(fetch_data), timeout=2.5)
            raw_data = res.data if res and hasattr(res, "data") and res.data else []

            if raw_data:
                sorted_data = sorted(
                    raw_data, 
                    key=lambda x: safe_int(x.get("id") or x.get("req_id") or 0), 
                    reverse=True
                )[:20]

                # Ambil ID terbaru untuk pengecekan perubahan
                first_row = sorted_data[0]
                newest_id = str(first_row.get("id") or first_row.get("req_id") or first_row.get("created_at") or "")

                with reactive.isolate():
                    prev_id = _last_seen_fl_id()

                # 🌟 5. KUNCI UTAMA: HANYA UPDATE STATE JIKA ADA DATA BARU (Mencegah Re-render Spam)
                if newest_id != prev_id:
                    cards = []
                    for row in sorted_data:
                        tgl_str = str(row.get("created_at", "-"))[:19].replace("T", " ")
                        raw_art = str(row.get("article_name", "-"))
                        clean_art = re.sub(r'<[^>]+>', '', raw_art).strip() or "-"

                        cards.append({
                            "id": str(row.get("req_id") or row.get("id")),
                            "article": clean_art,
                            "datetime": tgl_str,
                            "pic": row.get("pic", "Tim FL"),
                            "bin": row.get("bin", "-"),
                            "status": "WAITING OFFLINE",
                            "qty": safe_int(row.get("qty", 1), 1)
                        })

                    # Update state hanya saat datanya benar-benar berubah/ada baru
                    state.fl_request_list.set(cards)
                    state.fl_last_check_time.set(datetime.now().strftime("%H:%M:%S"))

                    # Pemicu suara barang baru (Hanya jika bukan data pertama kali load)
                    if prev_id is not None:
                        art_name = re.sub(r'<[^>]+>', '', str(first_row.get("article_name", "Barang Baru"))).strip()
                        pic_name = first_row.get("pic", "Tim FL")

                        await session.send_custom_message("trigger_fl_sound", {
                            "id": newest_id,
                            "article": art_name,
                            "pic": pic_name
                        })
                        ui.notification_show(f"🚨 Barang Baru: {art_name} ({pic_name})", type="warning", duration=6)

                    _last_seen_fl_id.set(newest_id)
                else:
                    # Jika data sama, kita cukup update jam indikator live-nya saja secara ringan
                    state.fl_last_check_time.set(datetime.now().strftime("%H:%M:%S"))
            else:
                with reactive.isolate():
                    current_list = state.fl_request_list()
                if current_list:
                    state.fl_request_list.set([])

        except asyncio.TimeoutError:
            # Jika Supabase timeout karena internet lambat, abaikan pelan-pelan tanpa merusak app / bikin redup
            print("⚠️ Warning: Polling Supabase timeout (jaringan lambat).")
        except Exception as e:
            print("⚠️ Error polling FL:", e)
        finally:
            # Selalu buka kembali kuncinya di akhir siklus khusus sesi ini
            _is_fl_polling[0] = False
                        # Modal Dismiss Listeners
    @reactive.Effect
    @reactive.event(input.close_success_modal_event)
    def _on_close_success_modal():
        state.show_success_modal.set(False)

    @reactive.Effect
    @reactive.event(input.change_filter_tgl_start)
    def _update_filter_tgl_start():
        state.filter_tgl_start.set(input.change_filter_tgl_start())

    @reactive.Effect
    @reactive.event(input.change_filter_tgl_end)
    def _update_filter_tgl_end():
        state.filter_tgl_end.set(input.change_filter_tgl_end())

    @reactive.Effect
    @reactive.event(input.btn_reset_filter_tgl)
    def _reset_filter_tgl():
        state.filter_tgl_start.set("")
        state.filter_tgl_end.set("")

    @reactive.Effect
    @reactive.event(input.btn_toggle_select_all)
    def _toggle_select_all():
        state.toggle_select_all_filtered()

    @reactive.Effect
    @reactive.event(input.btn_fetch_stock_minus_jezpro)
    def _fetch_stock_minus_jezpro():
        succ, msg = state.trigger_pc_sync_and_load()
        if succ:
            state.show_success_modal.set(True)
        else:
            state.error_modal_message.set(msg)
            state.show_error_modal.set(True)

    @reactive.Effect
    @reactive.event(input.close_error_modal_event)
    def _on_close_error_modal():
        state.show_error_modal.set(False)
        state.error_modal_message.set("")

    @render.ui
    def global_success_modal_ui():
        return success_modal(state.show_success_modal())

    @render.ui
    def global_error_modal_ui():
        return error_modal(state.show_error_modal(), state.error_modal_message())

    # Authentication & Navigation
    @render.ui
    def ongkir_tab2_dynamic_ui():
        return ongkir_tab2_view(state)

    # Authentication & Navigation
    @reactive.Effect
    @reactive.event(input.btn_submit_login)
    def _login_event():
        data = input.btn_submit_login()
        u, p = data.get("user", ""), data.get("pass", "")
        success, msg = state.handle_login(u, p)
        if success:
            state.load_ongkir_data()
            state.load_memo_data()
            state.load_auditor_history()
            state.load_compliance_history()
            ui.notification_show(msg, type="message", duration=4)
        else:
            state.error_modal_message.set(msg)
            ui.notification_show(msg, type="error", duration=4)

    @reactive.Effect
    @reactive.event(input.btn_execute_logout)
    def _logout_event():
        state.logout()
        ui.notification_show("Anda telah keluar dari sistem.", type="warning", duration=4)

    SLUG_TO_MENU = {
        "database-ongkir-in-out": "Database Ongkir In/Out",
        "stock-minus": "Stock Minus",
        "putaway-system": "Putaway System",
        "compare-system": "Compare System",
        "cycle-count": "Cycle Count",
        "compare-rto": "Compare RTO",
        "stock-opname": "Stock Opname",
        "justification-so": "Justification SO",
        "cross-check-real-system": "Cross Check Real & System",
        "balancing-stock": "Balancing Stock",
        "physical-inventory-list": "Physical Inventory List",
        "validation-barcode-sku": "Validation Barcode SKU",
        "precentage-display": "Precentage Display",
        "percentage-display": "Percentage Display",
        "latihan-excel": "Latihan Excel",
        "excel-practice": "Latihan Excel",
        "form-auditor": "Form Auditor",
        "auditor-pack": "Form Auditor",
        "memo-pengajuan": "Memo Pengajuan",
        "warehouse-activity-monitor": "Warehouse Activity Monitor",
        "warehouse-monitoring": "Warehouse Activity Monitor",
        "ll01-monitor": "Warehouse Activity Monitor",
        "warehouse-compliance-audit": "Warehouse Compliance Audit",
        "instock-validation": "Instock Validation",
        "instock_validation": "Instock Validation",
        "permintaan-fl": "Permintaan FL",
        "refill-shelving": "Refill Shelving",
        "refill_shelving": "Refill Shelving",
        "reloc-koli-to-koli": "Reloc Koli to Koli",
        "reloc_koli_to_koli": "Reloc Koli to Koli"
    }

    # 1. Saat menu diklik di sidebar -> URL di browser otomatis berubah
    @reactive.Effect
    @reactive.event(input.select_menu_item)
    def _nav_event():
        menu = input.select_menu_item()
        state.set_main_menu(menu)
        # Update URL address bar tanpa refresh
        ui.insert_ui(
            ui.tags.script(f"window.updateUrlMenu('{menu}');"),
            selector="head",
            where="beforeEnd"
        )

    # 2. Saat web dibuka langsung lewat link spesifik (misal: #balancing-stock)
    @reactive.Effect
    @reactive.event(input.initial_url_hash)
    def _on_initial_hash_load():
        slug = input.initial_url_hash().lower().strip()
        if slug in SLUG_TO_MENU:
            state.set_main_menu(SLUG_TO_MENU[slug])

    

    @reactive.Effect
    @reactive.event(input.btn_toggle_sidebar)
    def _side_toggle(): state.toggle_sidebar()

    @reactive.Effect
    @reactive.event(input.toggle_dropdown_section)
    def _drop_toggle(): state.toggle_dropdown(input.toggle_dropdown_section())

    # Panduan & Logic Modal
   # ==========================================================================
    # MODAL PANDUAN & LOGIC LENGKAP UNTUK SELURUH MENU
    # ==========================================================================
    @reactive.Effect
    @reactive.event(input.btn_open_panduan_modal)
    def _panduan_modal():
        cur = state.main_menu()

        # 1. PANDUAN: CYCLE COUNT (ANALYZER)
        if cur == "Cycle Count":
            guide_body = ui.div(
                ui.tags.details(
                    ui.tags.summary("📋 Informasi Format File"),
                    ui.div(
                        ui.tags.strong("Format yang diharapkan:"),
                        ui.tags.ul(
                            ui.tags.li(ui.strong("FILTER:"), " Pilih Cabang, Sub Kategori, Brand, dan BIN System sesuai data yang dianalisa."),
                            ui.tags.li(ui.strong("1. DATA SCAN:"), " Kolom A = BIN, Kolom B = SKU, Kolom C = QTY SCAN."),
                            ui.tags.li(ui.strong("2. STOCK SYSTEM:"), " Download All Stock dari Multiple Adjustment (Pilih 'Termasuk yang sudah habis')."),
                            ui.tags.li(ui.strong("3. BIN COVERAGE:"), " Download dari Multiple Adjustment (Pilih 'Hanya ada di stock')."),
                            ui.tags.li(ui.strong("4. RECON REAL +:"), " Upload file hasil recon (Pastikan Kolom A bukan Number)."),
                            ui.tags.li(ui.strong("5. SYSTEM + RECON:"), " Upload file master audit hasil rekonsiliasi untuk generate Karantina.")
                        ),
                        class_="accordion-content"
                    ), open=True
                ),
                ui.tags.details(
                    ui.tags.summary("💡 Logic Thinking"),
                    ui.div(
                        ui.tags.strong("Alur Logika Cycle Count Analyzer:"),
                        ui.tags.ol(
                            ui.tags.li(ui.strong("REAL +:"), " QTY SCAN > QTY SYSTEM (Fokus pada data scan aktual fisik)."),
                            ui.tags.li(ui.strong("SYSTEM +:"), " QTY SYSTEM > QTY SCAN (Fokus pada data sistem yang belum terscan)."),
                            ui.tags.li(ui.strong("ALOKASI REAL +:"), " Mencari kover stok dari System + dan BIN Coverage (Status: FULL, PARTIAL, atau NO ALLOCATION)."),
                            ui.tags.li(ui.strong("RECON REPORT:"), " Item NO ALLOCATION otomatis ditarik untuk investigasi rekonsiliasi lanjutan."),
                            ui.tags.li(ui.strong("SET UP KARANTINA:"), " Item selisih (DIFF > 0) dimutasi ke BIN KARANTINA dengan note MISS LOCATION."),
                            ui.tags.li(ui.strong("MISS LOCATION REPORT:"), " Rekapitulasi total SKU & QTY yang mengalami salah letak lokasi.")
                        ),
                        class_="accordion-content"
                    ), open=True
                )
            )

        # 2. PANDUAN: COMPARE SYSTEM
        elif cur == "Compare System":
            guide_body = ui.div(
                ui.tags.details(
                    ui.tags.summary("📋 Informasi Format File & Mapping"),
                    ui.div(
                        ui.tags.strong("Kondisi Stok Berkurang (Sys1 > Sys2):"),
                        ui.tags.ul(
                            ui.tags.li(ui.strong("Stock Tracking:"), " Kolom A=Invoice, Kolom B=SKU, Kolom G=BIN, Kolom K=Qty (Index 10)."),
                            ui.tags.li(ui.strong("RTO Out:"), " Kolom A=No TF, Kolom D=SKU (Index 3), Kolom H=Qty (Index 7).")
                        ),
                        ui.tags.strong("Kondisi Stok Bertambah (Sys2 > Sys1):"),
                        ui.tags.ul(
                            ui.tags.li(ui.strong("Purchase Order:"), " Kolom A=No PO, Kolom E=SKU (Index 4), Kolom M=Qty (Index 12)."),
                            ui.tags.li(ui.strong("RTO In:"), " Kolom A=No TF, Kolom D=SKU (Index 3), Kolom H=Qty (Index 7)."),
                            ui.tags.li(ui.strong("Mutasi Refund:"), " Kolom D=SKU (Index 3), Kolom K=Qty (Index 10).")
                        ),
                        class_="accordion-content"
                    ), open=True
                )
            )

        # 3. PANDUAN: LIST BIN CYCLE COUNT
        elif cur == "List Bin Cycle Count":
            guide_body = ui.div(
                ui.tags.details(
                    ui.tags.summary("📋 Informasi Format File"),
                    ui.div(
                        ui.tags.strong("Format yang diharapkan:"),
                        ui.tags.ul(
                            ui.tags.li("Upload file ", ui.strong("Multiple Adjustment"), " dari Jezpro."),
                            ui.tags.li("File minimal memiliki 10 kolom: Kolom B (BIN), Kolom C (SKU), Kolom G (Sub Kategori), Kolom H (Harga Jual), dan Kolom J (Qty System)."),
                            ui.tags.li("Gunakan filter interaktif untuk memilah berdasarkan Sub Kategori, Brand, atau Tiering Kategori Harga.")
                        ),
                        class_="accordion-content"
                    ), open=True
                )
            )

        # 4. PANDUAN: PUTAWAY & PICKING AUDIT LIST
        elif cur in ["Putaway & Picking Audit List", "Putaway & Picking Audit"]:
            guide_body = ui.div(
                ui.tags.details(
                    ui.tags.summary("📋 Format Dokumen Audit"),
                    ui.div(
                        ui.tags.ul(
                            ui.tags.li(ui.strong("1. File Sales:"), " Memeriksa data penjualan (Minimal hingga Kolom K / Qty Sales)."),
                            ui.tags.li(ui.strong("2. File RTO:"), " Memeriksa data retur keluar (Minimal hingga Kolom I / Qty RTO)."),
                            ui.tags.li(ui.strong("3. File Mutasi:"), " Memeriksa rantai perjalanan perpindahan BIN secara kronologis (Kolom A=Waktu, D=SKU, I=Bin Awal, M=Bin Tujuan)."),
                            ui.tags.li(ui.strong("4. Final Match BIN:"), " Menghasilkan irisan BIN yang mengalami Picking dan Putaway secara bersamaan.")
                        ),
                        class_="accordion-content"
                    ), open=True
                )
            )

        # 5. PANDUAN: STOCK MINUS
        elif cur == "Stock Minus":
            guide_body = ui.div(
                ui.tags.details(
                    ui.tags.summary("📋 Informasi Format File & Logic"),
                    ui.div(
                        ui.tags.ul(
                            ui.tags.li("Download file ", ui.strong("Multiple Adjustment"), " dari Jezpro dan pilih ", ui.strong("'Termasuk yang sudah habis'"), "."),
                            ui.tags.li("Sistem akan mendeteksi seluruh SKU dengan Qty System minus (-)."),
                            ui.tags.li("Sistem memprioritaskan penutupan stok minus dari BIN Prioritas (Staging Inbound/Outbound, Karantina, dll)."),
                            ui.tags.li("Jika stok minus terjadi di Toko, sistem akan memprioritaskan kover dari Gudang Lt.2, begitupun sebaliknya.")
                        ),
                        class_="accordion-content"
                    ), open=True
                )
            )

        # 6. PANDUAN: PUTAWAY SYSTEM
        elif cur == "Putaway System":
            guide_body = ui.div(
                ui.tags.details(
                    ui.tags.summary("📋 Format File Putaway"),
                    ui.div(
                        ui.tags.ul(
                            ui.tags.li(ui.strong("DATA SCAN PUTAWAY:"), " Kolom A = BIN, Kolom B = SKU, Kolom C = QTY SCAN."),
                            ui.tags.li(ui.strong("DATA ASAL BIN:"), " Sesuai format template Jezpro."),
                            ui.tags.li("Pilih Area Putaway terlebih dahulu (DC Lt.1, Lt.2, Lt.3, atau Jersey Zone) sebelum komparasi.")
                        ),
                        class_="accordion-content"
                    ), open=True
                )
            )

        # 7. PANDUAN: DATABASE ONGKIR
        elif cur in ["Database Ongkir In/Out", "Database Ongkir", "dashboard_ongkir"]:
            guide_body = ui.div(
                ui.tags.details(
                    ui.tags.summary("📋 Panduan Input & Upload Ongkir"),
                    ui.div(
                        ui.tags.ul(
                            ui.tags.li(ui.strong("Input Manual:"), " Masukkan Supplier, Ekspedisi, Total Koli, Total Biaya Ongkir, dan Tanggal Transaksi."),
                            ui.tags.li(ui.strong("Batch CSV Upload:"), " Format header CSV wajib: SUPPLIER, EKSPEDISI, TOTAL KOLI, ONGKIR, TANGGAL_JAM.")
                        ),
                        class_="accordion-content"
                    ), open=True
                )
            )

        elif cur == "Compare RTO":
            guide_body = ui.div(
                ui.tags.details(
                    ui.tags.summary("📋 Informasi Format File"),
                    ui.div(
                        ui.tags.strong("Format yang diharapkan:"),
                        ui.tags.ul(
                            ui.tags.li(ui.strong("DS RTO:"), " Kolom A = SKU, Kolom B = QTY SCAN."),
                            ui.tags.li(ui.strong("APPSHEET RTO:"), " Download Spreadsheet Rekap AppSheet sesuai sheet RTO yang dituju."),
                            ui.tags.li(ui.strong("UPLOAD HASIL CEK REAL:"), " Upload hasil rekonsiliasi yang sudah diisi real fisik."),
                            ui.tags.li(ui.strong("DRAFT RTO:"), " Download Draft RTO yang dibuat purchasing di awal.")
                        ),
                        class_="accordion-content"
                    ), open=True
                ),
                ui.tags.details(
                    ui.tags.summary("💡 Logic Thinking"),
                    ui.div(
                        ui.tags.strong("Alur Process Compare RTO (DS vs AppSheet vs Draft):"),
                        ui.tags.ol(
                            ui.tags.li("Compare SKU & QTY antara Data Scan (DS) vs AppSheet."),
                            ui.tags.li(ui.strong("Kelebihan Ambil:"), " QTY di DS > AppSheet. ", ui.strong("Kurang Ambil:"), " QTY di DS < AppSheet."),
                            ui.tags.li("Hasil rekonsiliasi dimasukkan untuk refresh sinkronisasi."),
                            ui.tags.li("Compare hasil AppSheet dengan Draft RTO Jezpro (Validasi QTY & BIN)."),
                            ui.tags.li("Status: ", ui.strong("OK"), ", ", ui.strong("Perlu Edit QTY Draft"), ", ", ui.strong("Perlu Edit BIN Draft"), ", ", ui.strong("Delete Item"), ", dan ", ui.strong("Add New"), "."),
                            ui.tags.li("Generate New Draft otomatis untuk upload balik ke Jezpro.")
                        ),
                        class_="accordion-content"
                    ), open=True
                )
            )

        elif cur == "Stock Opname":
            guide_body = ui.div(
                ui.tags.details(
                    ui.tags.summary("📋 Informasi Format File"),
                    ui.div(
                        ui.tags.strong("Format yang diharapkan:"),
                        ui.tags.ul(
                            ui.tags.li(ui.strong("FILTER:"), " Pilih Cabang, Sub Kategori, dan BIN System."),
                            ui.tags.li(ui.strong("1. DATA SCAN:"), " Kolom A = BIN, Kolom B = SKU, Kolom C = QTY SCAN."),
                            ui.tags.li(ui.strong("2. STOCK SYSTEM:"), " Download All Stock dari Multiple Adjustment (Termasuk yang sudah habis)."),
                            ui.tags.li(ui.strong("3. BIN COVERAGE:"), " Download All BIN & Karantina (Hanya ada di stock)."),
                            ui.tags.li(ui.strong("4. FINAL ADJ +:"), " Upload Real+ Recon, Cek Stock Adj+, dan File Staging Inbound."),
                            ui.tags.li(ui.strong("5. KARANTINA:"), " Upload System+ Recon dan Stock Cek Adj (-)."),
                            ui.tags.li(ui.strong("6. SUMMARY ADJ:"), " Laporan rekapitulasi finansial & QTY adjustment.")
                        ),
                        class_="accordion-content"
                    ), open=True
                ),
                ui.tags.details(
                    ui.tags.summary("💡 Logic Thinking"),
                    ui.div(
                        ui.tags.strong("Alur Logika Stock Opname Analyzer:"),
                        ui.tags.ol(
                            ui.tags.li(ui.strong("DS VS Stock System:"), " Real + (QTY Scan > Qty System), System + (Qty System > Qty Scan)."),
                            ui.tags.li(ui.strong("Alokasi Real +:"), " Cover stok ke BIN Coverage & System +."),
                            ui.tags.li(ui.strong("Recon Reports:"), " Validasi rekonsiliasi Real + & System Outstanding."),
                            ui.tags.li(ui.strong("Final Adjustment:"), " Sinkronisasi ke Staging Inbound untuk Multiple & Single Adj +."),
                            ui.tags.li(ui.strong("Set Up Karantina:"), " Selisih fisik positif (DIFF > 0) dimutasi ke BIN Karantina (Note: NOT FOUND)."),
                            ui.tags.li(ui.strong("Miss Location & Summary:"), " Evaluasi rekapitulasi salah letak dan net finansial value adjustment.")
                        ),
                        class_="accordion-content"
                    ), open=True
                )
            )

        elif cur == "Justification SO":
            # Helper untuk membuat tabel mini contoh kasus yang rapi
            def mini_tbl(headers, rows):
                th_list = [ui.tags.th(h, style="background: #E2E8F0; padding: 6px 10px; border: 1px solid #CBD5E0; font-size: 11px; text-align: center; color: #1A202C;") for h in headers]
                tr_list = []
                for r in rows:
                    td_list = [ui.tags.td(ui.HTML(str(c)), style="padding: 6px 10px; border: 1px solid #E2E8F0; font-size: 11px; text-align: center; color: #2D3748;") for c in r]
                    tr_list.append(ui.tags.tr(*td_list))
                return ui.tags.table(
                    ui.tags.thead(ui.tags.tr(*th_list)),
                    ui.tags.tbody(*tr_list),
                    style="border-collapse: collapse; width: 100%; margin: 8px 0; background: white; border-radius: 6px; overflow: hidden;"
                )

            guide_body = ui.div(

                # ==============================================================
                # PANDUAN MODE 1: JUSTIFIKASI REVERSAL
                # ==============================================================
                ui.tags.details(
                    ui.tags.summary("🔄 MODE 1: PANDUAN & LOGIKA JUSTIFIKASI REVERSAL (HISTORI PBI)"),
                    ui.div(
                        ui.div(
                            ui.p(ui.strong("Tujuan Mode Reversal:"), " Membuktikan apakah selisih stok bulan ini merupakan akibat dari kesalahan input penambahan/pengurangan di masa lalu (*Reversal Adjustment*) berdasarkan histori transaksi resmi PBI.", style="margin-bottom: 8px; color: #2D3748; font-size: 13px;"),
                            style="background: #EBF8FF; border-left: 4px solid #3182CE; padding: 10px 14px; border-radius: 6px; margin-bottom: 1rem;"
                        ),
                        ui.tags.strong("📋 Ketentuan File & Filter Tanggal:"),
                        ui.tags.ul(
                            ui.tags.li(ui.strong("Filter Tanggal PBI:"), " Sistem HANYA memeriksa data transaksi PBI pada rentang tanggal yang dipilih. Transaksi di luar rentang tanggal otomatis diabaikan 100%."),
                            ui.tags.li(ui.strong("File 1 (Multiple Adjustment):"), " File gabungan hasil SO (Real & System) yang berisi kolom SKU, Qty System, dan Qty SO."),
                            ui.tags.li(ui.strong("File 2 (File Adjustment PBI):"), " Laporan histori transaksi adjustment dari PBI dengan acuan kolom wajib:"),
                            ui.tags.ul(
                                ui.tags.li("Kolom A (Index 0): ", ui.code("No Adjustment")),
                                ui.tags.li("Kolom C (Index 2): ", ui.code("SKU")),
                                ui.tags.li("Kolom E (Index 4): ", ui.code("Datetime Transaksi")),
                                ui.tags.li("Kolom Q (Index 16): ", ui.code("Qty Adjustment"), " (+ berarti Adj Tambah, - berarti Adj Kurang)")
                            )
                        ),
                        ui.hr(style="margin: 10px 0; border-color: #CBD5E0;"),
                        ui.tags.strong("💡 Arti Hasil Status Justification Reversal:"),
                        ui.tags.ol(
                            ui.tags.li(ui.strong("KESALAHAN ADJUSMENT (REVERSAL EXACT MATCH):"), " Ditemukan 1 dokumen PBI masa lalu yang nilainya 100% pas (berlawanan tanda) dengan selisih sekarang. Dokumen tersebut sah sebagai biang keladi selisih."),
                            ui.tags.li(ui.strong("KESALAHAN ADJUSMENT (REVERSAL CUMULATIVE MATCH):"), " Total penjumlahan bersih (*net sum*) transaksi PBI di rentang tanggal tersebut nilainya persis sama dengan selisih saat ini."),
                            ui.tags.li(ui.strong("INDIKASI REVERSAL (LAST OPPOSITE ADJ: X):"), " Ditemukan transaksi adjustment berlawanan arah di PBI, namun nilainya tidak pas 1:1 (*over-adjustment* atau tersisa sebagian karena mutasi/sales lain)."),
                            ui.tags.li(ui.strong("BUKAN REVERSAL (ARAH TRANSAKSI TIDAK SESUAI):"), " Ada transaksi di PBI pada tanggal tersebut, tetapi arahnya searah/tidak dapat menjelaskan selisih saat ini. Selisih kemungkinan murni fisik hilang, salah taruh rak (*miss location*), atau salah picking."),
                            ui.tags.li(ui.strong("BUKAN REVERSAL (TIDAK ADA HISTORY PBI):"), " SKU ini sama sekali tidak pernah di-adjustment pada rentang tanggal yang dipilih.")
                        ),
                        ui.hr(style="margin: 10px 0; border-color: #CBD5E0;"),
                        ui.tags.strong("📊 Penjelasan Kolom Tambahan Hasil Reversal:"),
                        ui.tags.ul(
                            ui.tags.li(ui.strong("ADJUSTMENT +:"), " Total akumulasi kuantitas penambahan stok di PBI untuk SKU tersebut dalam periode filter."),
                            ui.tags.li(ui.strong("ADJUSTMENT -:"), " Total akumulasi kuantitas pengurangan stok di PBI untuk SKU tersebut dalam periode filter."),
                            ui.tags.li(ui.strong("NO ADJUSTMENT & TGL ADJUSTMENT:"), " Nomor dokumen dan waktu transaksi PBI yang teridentifikasi sebagai penyebab selisih.")
                        ),
                        class_="accordion-content"
                    ), open=True
                ),

                # --- SECTION 1: FORMAT FILE ---
                ui.tags.details(
                    ui.tags.summary("🔄 MODE 2: PANDUAN & LOGIKA JUSTIFIKASI NON REVERSAL"),
                    ui.div(
                        ui.tags.strong("Format yang diharapkan:"),
                        ui.tags.ul(
                            ui.tags.li(ui.strong("ADJUSTMENT FILE:"), " Gabungkan antara Multiple Adjustment ", ui.strong("(Plus)"), " dan ", ui.strong("(Minus)"), " dalam 1 File."),
                            ui.tags.li(ui.strong("SUMMARY STOCK:"), " Download dari ", ui.strong("JEZPRO"), " pada menu ", ui.strong("Dashboard Asset"), " (Store: ", ui.strong("JEZ SURABAYA"), ")."),
                            ui.tags.li(ui.strong("ALL DATA STOCK:"), " Upload file All data Stock (Multiple Adjustment) ", ui.strong("HANYA ADA STOCK"), "."),
                            ui.tags.li(ui.strong("DATA SCAN (Opsional):"), " Jika diupload maka perhitungan ", ui.strong("Real QTY"), " akan mengambil qty dari data scan dan apabila tidak diupload maka akan kembali ke perhitungan awal.")
                        ),
                        class_="accordion-content"
                    ), open=True
                ),

                # --- SECTION 2: 7 ATURAN LOGIKA LENGKAP & CONTOH KASUS ---
                ui.tags.details(
                    ui.tags.summary("💡 Logic Thinking (Justification) - 7 Aturan Lengkap"),
                    ui.div(
                        # Rumus Banner
                        ui.div(
                            ui.span("REAL QTY / HITUNGAN MANUAL ➡️ : ", style="font-weight: 800; color: #2C5282;"),
                            ui.span("BEGINNING STOCK + (TOTAL_STOCKIN + TOTAL TRF_IN) - (TOTAL SALES + TOTAL TRF_OUT + TOTAL DRAFT TRF_OUT)", style="font-weight: bold; font-family: monospace; color: #1A365D;"),
                            style="background: #EBF8FF; border-left: 4px solid #3182CE; padding: 10px 14px; border-radius: 6px; margin-bottom: 1rem;"
                        ),

                        # 1. Kesalahan System (Begin Stock Minus)
                        ui.div(
                            ui.h5("🛑 1. Kesalahan System (Begin Stock Minus)", style="font-weight: 800; color: #C53030; font-size: 13px; margin: 0 0 4px 0;"),
                            ui.tags.ul(
                                ui.tags.li(ui.strong("Kondisinya:"), " Stok SO lebih besar dari stok Sistem (ADJUSTMENT +), Tetapi ", ui.strong("Beginning Stock bernilai minus (di bawah 0)"), "."),
                                ui.tags.li(ui.strong("Artinya:"), " Sistem dari awal sudah error/bocor datanya karena mencatat stok minus yang artinya memang perlu dilakukan Adjustment +.")
                            ),
                            ui.p("Contoh Kasus:", style="font-weight: bold; margin: 4px 0 2px 0; font-size: 11px;"),
                            mini_tbl(
                                ["Stok SO", "Stok Sistem", "BEGINNING STOCK", "GAP ADJUSTMENT"],
                                [["10", "5", "<b style='color: #E53E3E;'>-2</b>", "0"]]
                            ),
                            style="background: #FFF5F5; padding: 10px; border-radius: 8px; border: 1px solid #FED7D7; margin-bottom: 0.75rem;"
                        ),

                        # 2. Kesalahan System (Ending Stock != Total Stock Multiple)
                        ui.div(
                            ui.h5("🛡️ 2. Kesalahan System (Ending Stock ≠ Total Stock dari Multiple)", style="font-weight: 800; color: #DD6B20; font-size: 13px; margin: 0 0 4px 0;"),
                            ui.tags.ul(
                                ui.tags.li(ui.strong("Kondisinya:"), " ", ui.code("GAP ADJUSTMENT"), " dan ", ui.code("BEGINNING STOCK"), " sama-sama nol. Total stock antara (", ui.strong("Ending Stock, Real Qty, Current Stock"), ") nilainya sama (senilai), tapi total stock di multiple (", ui.strong("QTY SYSTEM ALL"), ") malah lebih kecil dari stok akhir."),
                                ui.tags.li(ui.strong("Artinya:"), " Ada mismatch antara data di multiple dan summary sehingga menyebabkan adjustment +.")
                            ),
                            ui.p("Contoh Kasus:", style="font-weight: bold; margin: 4px 0 2px 0; font-size: 11px;"),
                            mini_tbl(
                                ["GAP ADJ", "BEGINNING STOCK", "ENDING / REAL / CURR STOCK", "QTY SYSTEM ALL"],
                                [["0", "0", "<b style='color: #3182CE;'>10 (Kembar)</b>", "<b style='color: #E53E3E;'>3 (Lebih Kecil)</b>"]]
                            ),
                            style="background: #FFFAF0; padding: 10px; border-radius: 8px; border: 1px solid #FEEBC8; margin-bottom: 0.75rem;"
                        ),

                        # 3. Kesalahan System (Miss Match Real QTY Manual dengan Ending Stock)
                        ui.div(
                            ui.h5("⚙️ 3. Kesalahan System (Miss Match Real QTY dengan Ending Stock/Current Stock)", style="font-weight: 800; color: #2B6CB0; font-size: 13px; margin: 0 0 4px 0;"),
                            ui.tags.ul(
                                ui.tags.li(ui.strong("Kondisinya:"), " Stok SO lebih besar dari stok Sistem (ADJUSTMENT +), tidak ada transaksi gantung (Draft TRF), tidak ada GAP ADJUSTMENT, ", ui.strong("TAPI hasil hitungan manual tidak match dengan nilai ENDING STOCK"), " di sistem."),
                                ui.tags.li(ui.strong("Detail Hitungan Manual:"), " BEGINNING STOCK + (TOTAL_STOCKIN + TOTAL TRF_IN) - (TOTAL SALES + TOTAL TRF_OUT)."),
                                ui.tags.li(ui.strong("Artinya:"), " Sistem salah hitung mutasi barang (hasil gabungan barang masuk dan keluar tidak sinkron dengan stok akhir).")
                            ),
                            ui.p("Contoh Kasus:", style="font-weight: bold; margin: 4px 0 2px 0; font-size: 11px;"),
                            mini_tbl(
                                ["BEGINNING", "STOCKIN + TRF_IN", "SALES + TRF_OUT", "Hitungan Manual", "ENDING STOCK"],
                                [["10", "5", "2", "<b style='color: #276749;'>13</b>", "<b style='color: #E53E3E;'>15 (Gak Match!)</b>"]]
                            ),
                            style="background: #EBF8FF; padding: 10px; border-radius: 8px; border: 1px solid #BEE3F8; margin-bottom: 0.75rem;"
                        ),

                        # 4. Kesalahan System (Stock System Lost)
                        ui.div(
                            ui.h5("💻 4. Kesalahan System (Stock System Lost)", style="font-weight: 800; color: #805AD5; font-size: 13px; margin: 0 0 4px 0;"),
                            ui.tags.ul(
                                ui.tags.li(ui.strong("Kondisinya:"), " Tidak ada GAP ADJUSTMENT (= 0), tapi ada selisih antara Sistem dan SO. Ketika selisih itu ditambah/dikurang ke master QTY SYSTEM ALL, hasilnya pas dengan CURRENT STOCK."),
                                ui.tags.li(ui.strong("Artinya:"), " Bug bawaan sistem yang membuat angka di layar tidak ter-update.")
                            ),
                            ui.p("Contoh Kasus:", style="font-weight: bold; margin: 4px 0 2px 0; font-size: 11px;"),
                            mini_tbl(
                                ["QTY SO", "QTY System", "Selisih (Diff)", "QTY SYSTEM ALL", "CURRENT STOCK"],
                                [
                                    ["12", "10", "<b>+2</b>", "15", "<b style='color: #276749;'>17 (15 + 2 Pas!)</b>"],
                                    ["8", "10", "<b>-2</b>", "15", "<b style='color: #276749;'>13 (15 - 2 Pas!)</b>"]
                                ]
                            ),
                            style="background: #FAF5FF; padding: 10px; border-radius: 8px; border: 1px solid #E9D8FD; margin-bottom: 0.75rem;"
                        ),

                        # 5. Cek Hasil Rekonsiliasi
                        ui.div(
                            ui.h5("🔍 5. Cek Hasil Rekonsiliasi", style="font-weight: 800; color: #D69E2E; font-size: 13px; margin: 0 0 4px 0;"),
                            ui.tags.ul(
                                ui.tags.li(ui.strong("Kondisinya:"), " Total stock di multiple (", ui.strong("QTY SYSTEM ALL"), ") ternyata pas/sama persis dengan ", ui.strong("CURRENT STOCK / ENDING STOCK"), "."),
                                ui.tags.li(ui.strong("Artinya:"), " Data sebenarnya aman dan sinkron secara total keseluruhan.")
                            ),
                            ui.p("Contoh Kasus:", style="font-weight: bold; margin: 4px 0 2px 0; font-size: 11px;"),
                            mini_tbl(
                                ["QTY SYSTEM ALL", "CURRENT STOCK", "ENDING STOCK"],
                                [["<b style='color: #276749;'>25</b>", "<b style='color: #276749;'>25</b>", "<b style='color: #276749;'>25</b>"]]
                            ),
                            style="background: #FFFFF0; padding: 10px; border-radius: 8px; border: 1px solid #FEFCBF; margin-bottom: 0.75rem;"
                        ),

                        # 6. Kesalahan Adjustment (+ / -)
                        ui.div(
                            ui.h5("⚠️ 6. Kesalahan Adjustment (+ / -)", style="font-weight: 800; color: #C53030; font-size: 13px; margin: 0 0 4px 0;"),
                            ui.tags.ul(
                                ui.tags.li("Stok Sistem > Stok SO, tapi ada data GAP ADJUSTMENT positif (+)."),
                                ui.tags.li("Stok Sistem < Stok SO, tapi ada data GAP ADJUSTMENT negatif (-)."),
                                ui.tags.li(ui.strong("Artinya:"), " Koreksi dari Proses Adjustment Sebelumnya (Reversal).")
                            ),
                            ui.p("Contoh Kasus:", style="font-weight: bold; margin: 4px 0 2px 0; font-size: 11px;"),
                            mini_tbl(
                                ["Kondisi Lapangan", "GAP ADJUSTMENT di Sistem", "Keterangan"],
                                [
                                    ["QTY Sistem (10) > QTY SO (5)", "<b style='color: #276749;'>+5</b>", "Ada Koreksi (Reversal)"],
                                    ["QTY Sistem (5) < QTY SO (10)", "<b style='color: #E53E3E;'>-5</b>", "Ada Koreksi (Reversal)"]
                                ]
                            ),
                            style="background: #FFF5F5; padding: 10px; border-radius: 8px; border: 1px solid #FED7D7; margin-bottom: 0.75rem;"
                        ),

                        # 7. Kesalahan RTO (Barang Gantung)
                        ui.div(
                            ui.h5("🚚 7. Kesalahan RTO (Barang Gantung)", style="font-weight: 800; color: #2B6CB0; font-size: 13px; margin: 0 0 4px 0;"),
                            ui.tags.ul(
                                ui.tags.li(ui.strong("Kondisinya:"), " Masih ada angka di kolom TOTAL DRAFT TRF IN atau TOTAL DRAFT TRF OUT yang menggantung (belum di-approve/finish)."),
                                ui.tags.li(ui.strong("Artinya:"), " Masalah klasik RTO/mutasi barang yang statusnya masih draf.")
                            ),
                            ui.p("Contoh Kasus:", style="font-weight: bold; margin: 4px 0 2px 0; font-size: 11px;"),
                            mini_tbl(
                                ["TOTAL DRAFT TRF IN", "TOTAL DRAFT TRF OUT", "Status"],
                                [
                                    ["<b style='color: #DD6B20;'>5</b>", "0", "Ada barang gantung"],
                                    ["0", "<b style='color: #DD6B20;'>3</b>", "Ada barang gantung"]
                                ]
                            ),
                            style="background: #EBF8FF; padding: 10px; border-radius: 8px; border: 1px solid #BEE3F8; margin-bottom: 0.75rem;"
                        ),

                        # Catatan Tambahan (Undefined & Error Data)
                        ui.div(
                            ui.p("❓ Kenapa muncul UNDEFINED? ➔ Berarti kasus item tersebut tidak masuk ke dalam 7 kondisi di atas (butuh dicek manual).", style="margin: 0 0 4px 0; font-weight: bold; color: #4A5568; font-size: 12px;"),
                            ui.p("❓ Kenapa muncul ERROR DATA? ➔ Ada kolom yang isinya kosong, teks rusak, atau tidak bisa dihitung angka.", style="margin: 0; font-weight: bold; color: #E53E3E; font-size: 12px;"),
                            style="background: #EDF2F7; padding: 10px 14px; border-radius: 6px; margin-top: 0.5rem;"
                        ),
                        class_="accordion-content"
                    ), open=True
                )
            )

# 8. PANDUAN: CROSS CHECK REAL & SYSTEM
        elif cur in ["Cross Check Real & System", "Match Real & System"]:
            guide_body = ui.div(
                ui.tags.details(
                    ui.tags.summary("📋 Informasi Format File"),
                    ui.div(
                        ui.tags.strong("Ketentuan Kolom untuk Masing-masing File Uploader:"),
                        ui.tags.ul(
                            ui.tags.li(ui.strong("1. FILE SYSTEM (+):"), " Kolom A = Cabang, Kolom D = SKU System, Kolom K = Qty System."),
                            ui.tags.li(ui.strong("2. FILE REAL (+):"), " Kolom A = Cabang, Kolom E = SKU Real, Kolom M = Qty Real.")
                        ),
                        class_="accordion-content"
                    ), open=True
                ),
                ui.tags.details(
                    ui.tags.summary("💡 Logic Thinking"),
                    ui.div(
                        ui.tags.strong("Alur Alokasi Stok Lintas Cabang (Cross-Branch):"),
                        ui.tags.ol(
                            ui.tags.li(ui.strong("Pool Lock System:"), " Seluruh data dari Uploader System akan dikunci kuotanya berdasarkan kombinasi Cabang + SKU System."),
                            ui.tags.li(ui.strong("Pencarian Pasangan:"), " Data dari Uploader Real discan baris demi baris, lalu diprioritaskan mencari kecocokan di cabang asalnya dulu (", ui.strong("MATCH PERFECT"), ")."),
                            ui.tags.li(ui.strong("Alokasi Lintas Cabang:"), " Jika kuota system di cabang asalnya habis, sistem otomatis mencarikan sisa kuota ke cabang lain (", ui.strong("MATCH CROSS-BRANCH"), ")."),
                            ui.tags.li(ui.strong("Kontrol Kuota:"), " Jika kuota system di semua cabang sudah habis, sisa qty real dicatat sebagai ", ui.strong("UNMATCHED / NO SYSTEM QTY"), ".")
                        ),
                        class_="accordion-content"
                    ), open=True
                )
            )

            # 9. PANDUAN: BALANCING STOCK & DYNAMIC ALLOCATION
        # 9. PANDUAN & LOGIC: BALANCING STOCK & DYNAMIC ALLOCATION (VERSI TERBARU)
        elif cur in ["Balancing Stock", "Stock Allocation"]:
            guide_body = ui.div(
                # --- SECTION 1: SUMBER DATA & PEMETAAN KOLOM ---
                ui.tags.details(
                    ui.tags.summary("📋 1. Sumber Data & Ketentuan Kolom (Supabase Cache)"),
                    ui.div(
                        ui.div(
                            ui.p(ui.strong("Sinkronisasi Otomatis Supabase:"), " Data ditarik langsung dari tabel ", ui.code("balancing_stock_cache"), " dan ", ui.code("balancing_sales_cache"), " tanpa perlu upload manual.", style="margin-bottom: 6px; color: #1A365D; font-size: 13px;"),
                            style="background: #EBF8FF; border-left: 4px solid #3182CE; padding: 10px 14px; border-radius: 6px; margin-bottom: 0.75rem;"
                        ),
                        ui.tags.strong("Struktur Kolom Acuan:"),
                        ui.tags.ul(
                            ui.tags.li(ui.strong("Stok (All Stock):"), " Kolom B (BIN), Kolom C (SKU), Kolom D (Brand), Kolom E (Item Name), Kolom F (Size/Variant), Kolom G (Sub Kategori), dan ", ui.strong("Kolom J (Qty System)"), "."),
                            ui.tags.li(ui.strong("Sales (Report/Tracking):"), " Kolom A (Invoice), Kolom B (SKU), dan ", ui.strong("Kolom L (Qty Sales)"), "."),
                            ui.tags.li(ui.strong("Normalisasi SKU:"), " SKU dengan angka nol di depan (misal: 00009048) otomatis dicocokkan dengan angka murninya (9048) secara dua arah agar data penjualan terbaca akurat.")
                        ),
                        ui.hr(style="margin: 8px 0; border-color: #CBD5E0;"),
                        ui.tags.strong("Pengecualian & Klasifikasi Area BIN:"),
                        ui.tags.ul(
                            ui.tags.li("🛑 ", ui.strong("BIN yang Dikecualikan:"), " BIN yang mengandung kata ", ui.code("DEFECT"), ", ", ui.code("REJECT"), ", ", ui.code("KARANTINA"), ", ", ui.code("PERBAIKAN"), ", dan ", ui.code("TOKO"), " otomatis dihapus dari perhitungan stok."),
                            ui.tags.li("📦 ", ui.strong("Area Logistik (QTY LOG):"), " Dihitung dari seluruh BIN yang mengandung kata ", ui.code("LOG"), "."),
                            ui.tags.li("🏪 ", ui.strong("Area Offline (QTY OFF):"), " Dihitung dari seluruh BIN yang mengandung kata ", ui.code("OFF"), " atau ", ui.code("RSN"), "."),
                            ui.tags.li("🌐 ", ui.strong("Area Online (QTY ONL):"), " Dihitung dari seluruh BIN yang mengandung kata ", ui.code("ONL"), ".")
                        ),
                        class_="accordion-content"
                    ), open=True
                ),

                # --- SECTION 2: LOGIKA ALOKASI DINAMIS BERDASARKAN TURNOVER ---
                ui.tags.details(
                    ui.tags.summary("💡 2. Logika Alokasi Dinamis & Kuota Presisi (Turnover-Based)"),
                    ui.div(
                        ui.div(
                            ui.span("RUMUS KONTROL KUOTA: ", style="font-weight: 800; color: #744210; font-size: 12px;"),
                            ui.span("TARGET LOG + TARGET OFF + TARGET ONL = TOTAL STOK (TIDAK BOLEH LEBIH/KURANG)", style="font-weight: bold; font-family: monospace; color: #975A16; font-size: 12px;"),
                            style="background: #FEFCBF; border-left: 4px solid #D69E2E; padding: 10px 14px; border-radius: 6px; margin-bottom: 0.75rem;"
                        ),
                        ui.tags.strong("Aturan Alokasi Berdasarkan Kecepatan Penjualan (Turnover Rate = Sales / Stok):"),
                        ui.tags.ol(
                            ui.tags.li(ui.strong("Stok 1 Unit:"), " Dialokasikan utuh 1 unit ke channel yang penjualannya lebih tinggi (atau Logistik jika belum ada sales). Tidak akan pernah dibagi 1 di Offline dan 1 di Online."),
                            ui.tags.li(ui.strong("No Sales (0 Penjualan):"), " Alokasi ", ui.strong("80% Disimpan di Buffer Logistik"), ", 10% Offline, 10% Online."),
                            ui.tags.li(ui.strong("Slow-Moving (Penjualan <= 2 pcs atau < 40% dari Stok):"), " Karena penjualan lambat/jauh di bawah total stok, ", ui.strong("Logistik tetap memegang mayoritas (65%)"), ", channel penjualan hanya diberi kuota wajar (25% Offline atau 25% Online) agar toko tidak kebanjiran stok mati."),
                            ui.tags.li(ui.strong("Medium Turnover (40% - 74% dari Stok):"), " Alokasi 35% Logistik, 50% Channel Dominan, 15% Channel Lain."),
                            ui.tags.li(ui.strong("Fast-Moving (>= 75% dari Stok & Sales > 2):"), " Barang terbukti laris dan perputaran cepat, barulah channel dominan dialokasikan porsi besar ", ui.strong("70%"), ", 15% Logistik, 15% Channel Lain."),
                            ui.tags.li(ui.strong("Metode Pembagian Pecahan:"), " Menggunakan ", ui.em("Largest Remainder Method"), " sehingga sisa desimal diberikan kepada channel dengan penjualan tertinggi. Total target dijamin pas senilai total stok fisik.")
                        ),
                        class_="accordion-content"
                    ), open=True
                ),

                # --- SECTION 3: LOGIKA TAB 2 (LIST REFILL PROGRESIF) ---
                ui.tags.details(
                    ui.tags.summary("🔄 3. Alur Logika Tab 2 (List Refill Progresif per BIN)"),
                    ui.div(
                        ui.tags.strong("Format Output & Ketentuan Refill:"),
                        ui.tags.ul(
                            ui.tags.li("Header Tabel: ", ui.code("BIN | SKU | BRAND | ITEM NAME | SIZE | QTY LOG | QTY OFF | QTY ONL")),
                            ui.tags.li(ui.strong("Status 'NO REFILL':"), " Jika stok aktual di suatu area sudah mencukupi target alokasinya, kolom kuotanya otomatis bertuliskan ", ui.strong("'NO REFILL'"), "."),
                            ui.tags.li(ui.strong("Alokasi Bertingkat (Progresif):"), " Jika BIN awal tidak cukup memenuhi kuota refill, sistem otomatis memunculkan baris BIN berikutnya dan ", ui.strong("hanya mencatat sisa kekurangannya saja"), " hingga target terpenuhi."),
                            ui.tags.li(ui.strong("Filter Area Refill:"), " Gunakan dropdown filter di Tab 2 untuk memilah instruksi kerja:"),
                            ui.tags.ul(
                                ui.tags.li(ui.strong("AREA OFFLINE:"), " Hanya memunculkan baris barang yang benar-benar wajib di-refill ke Offline (menyembunyikan baris NO REFILL dan 0)."),
                                ui.tags.li(ui.strong("AREA ONLINE:"), " Hanya memunculkan baris barang yang wajib di-refill ke Online/Hub."),
                                ui.tags.li(ui.strong("AREA LOGISTIK:"), " Hanya memunculkan baris barang yang wajib dikembalikan ke buffer Logistik.")
                            ),
                            ui.tags.li(ui.strong("Download Excel Dinamis:"), " Tombol unduh file Excel otomatis mengikuti filter Area dan Sub Kategori yang sedang aktif.")
                        ),
                        class_="accordion-content"
                    ), open=True
                )
            )

        elif cur in ["Percentage Display", "Precentage Display"]:
            guide_body = ui.div(
                # --- SECTION 1: METRIK RINGKASAN & ATURAN UMUM ---
                ui.tags.details(
                    ui.tags.summary("📊 1. Penjelasan Metrik Ringkasan & BIN Eksklusi"),
                    ui.div(
                        ui.div(
                            ui.p(ui.strong("Tujuan Menu:"), " Memonitor ketersediaan display toko fisik (Article Base) dan memberikan instruksi refill terarah per BIN untuk kategori Lower Body.", style="margin-bottom: 6px; color: #1A365D; font-size: 13px;"),
                            style="background: #EBF8FF; border-left: 4px solid #3182CE; padding: 10px 14px; border-radius: 6px; margin-bottom: 0.75rem;"
                        ),
                        ui.tags.strong("📋 Ketentuan Metrik Box:"),
                        ui.tags.ul(
                            ui.tags.li(ui.strong("Total Article:"), " Total artikel unik yang terdaftar pada sistem cabang terpilih."),
                            ui.tags.li(ui.strong("On Display (%):"), " Persentase artikel yang sudah memiliki stok pajangan di area toko (BIN Toko/Display > 0)."),
                            ui.tags.li(ui.strong("Need Display (%):"), " Persentase artikel yang belum dipajang di toko, namun stok fisiknya tersedia di gudang."),
                            ui.tags.li(ui.strong("Artikel Tersedia di Gudang:"), " Menghitung akumulasi artikel siap tarik dari seluruh area gudang penyimpanan (OFF / LOG / ONL / Lainnya)."),
                            ui.tags.li(ui.strong("🚫 SKU di BIN Dikecualikan:"), " Menghitung total SKU unik yang berada di BIN non-operasional: ", ui.code("EVENT"), ", ", ui.code("REJECT"), ", ", ui.code("DEFECT"), ", ", ui.code("KARANTINA"), ", ", ui.code("PERBAIKAN"), ", ", ui.code("RESELLER"), ", ", ui.code("GARAGE"), ", dan ", ui.code("LIVE"), ".")
                        ),
                        class_="accordion-content"
                    ), open=True
                ),

                # --- SECTION 2: LOGIKA TAB 1 (DISPLAY AVAILABILITY) ---
                ui.tags.details(
                    ui.tags.summary("🧥 2. Logika Tab 1: Display Availability (Article Base)"),
                    ui.div(
                        ui.tags.strong("Kriteria Artikel Masuk List Display:"),
                        ui.tags.ul(
                            ui.tags.li("Stok artikel di area Toko kosong (", ui.strong("Qty di Toko <= 0"), ")."),
                            ui.tags.li("Memiliki stok fisik yang valid dan tersedia di gudang (", ui.strong("Qty Gudang > 0"), ")."),
                            ui.tags.li("Terdapat kolom ", ui.strong("Qty di Toko"), " untuk memudahkan verifikasi kekosongan barang di display.")
                        ),
                        ui.hr(style="margin: 8px 0; border-color: #CBD5E0;"),
                        ui.tags.strong("🎯 Alur Prioritas Pencarian Lokasi BIN Sumber:"),
                        ui.tags.ol(
                            ui.tags.li(ui.strong("Prioritas 1 (Area Offline):"), " Sistem memprioritaskan pencarian dari BIN yang mengandung kata ", ui.code("OFF"), " atau ", ui.code("RSN"), "."),
                            ui.tags.li(ui.strong("Prioritas 2 (Area Logistik):"), " Jika di area Offline tidak ditemukan, sistem mencari dari BIN yang mengandung kata ", ui.code("LOG"), "."),
                            ui.tags.li(ui.strong("Prioritas 3 (Area Online):"), " Jika di Logistik tidak ditemukan, sistem mencari dari BIN yang mengandung kata ", ui.code("ONL"), "."),
                            ui.tags.li(ui.strong("Prioritas 4 (Area Lainnya):"), " Jika tidak ada di ketiga area di atas, sistem mengambil dari BIN penyimpanan valid lainnya di luar BIN yang dikecualikan dan di luar Toko.")
                        ),
                        class_="accordion-content"
                    ), open=True
                ),

                # --- SECTION 3: LOGIKA TAB 2 (REFILL TOKO LOWER BODY) ---
                ui.tags.details(
                    ui.tags.summary("👖 3. Logika Tab 2: Refill Toko (Khusus Lower Body - Maks 10 Pcs)"),
                    ui.div(
                        ui.tags.strong("Ketentuan Syarat & Target Refill:"),
                        ui.tags.ul(
                            ui.tags.li("Khusus memproses sub kategori ", ui.strong("LOWER BODY"), "."),
                            ui.tags.li("Item masuk antrean jika stok di Toko ", ui.strong("< 10 pcs"), " dan stok gudang ", ui.strong("> 0"), "."),
                            ui.tags.li("Target refill maksimal adalah ", ui.strong("10 pcs per SKU"), " (Kebutuhan = min(10 - Qty Toko, Stok Gudang))."),
                            ui.tags.li("Item dengan ", ui.strong("Qty Toko = 0"), " otomatis ditempatkan di urutan teratas sebagai prioritas utama (*Priority Restock*).")
                        ),
                        ui.hr(style="margin: 8px 0; border-color: #CBD5E0;"),
                        ui.tags.strong("📦 Format Tabel & Sistem Progresif 1 BIN per Baris:"),
                        ui.tags.ol(
                            ui.tags.li(ui.strong("Posisi Kolom BIN:"), " Kolom ", ui.code("BIN"), " diletakkan di posisi ", ui.strong("paling kiri"), " (sebelah kiri kolom SKU)."),
                            ui.tags.li(ui.strong("Tunggal per Baris:"), " Setiap baris hanya memuat ", ui.strong("1 lokasi BIN penarikan"), " (tidak digabung tanda koma)."),
                            ui.tags.li(ui.strong("Pecah Baris Progresif (Split Defisit):"), " Jika stok di BIN pertama tidak mencukupi target kekurangan 10 pcs, sistem otomatis menduplikasi baris SKU tersebut ke BIN berikutnya dan ", ui.strong("hanya mengambil sisa kekurangannya saja"), " hingga target terpenuhi."),
                            ui.tags.li(ui.strong("Hierarki Pengambilan:"), " Pengambilan stok per BIN tetap mematuhi urutan prioritas: ", ui.strong("OFF"), " ➔ ", ui.strong("LOG"), " ➔ ", ui.strong("ONL"), " ➔ ", ui.strong("BIN Lainnya"), ".")
                        ),
                        class_="accordion-content"
                    ), open=True
                )
            )
            
            # PANDUAN: PHYSICAL INVENTORY LIST (2-IN-1 MODE)
        elif cur == "Physical Inventory List":
            guide_body = ui.div(
                ui.tags.details(
                    ui.tags.summary("📋 Mode 1: Putaway & Picking Audit"),
                    ui.div(
                        ui.tags.strong("Format Dokumen Audit:"),
                        ui.tags.ul(
                            ui.tags.li(ui.strong("1. File Sales:"), " Data riwayat penjualan (Minimal hingga Kolom K / Qty Sales)."),
                            ui.tags.li(ui.strong("2. File RTO:"), " Data riwayat retur keluar (Minimal hingga Kolom I / Qty RTO)."),
                            ui.tags.li(ui.strong("3. File Mutasi:"), " Rantai mutasi BIN kronologis (Kolom A=Waktu, D=SKU, I=Bin Awal, M=Bin Tujuan)."),
                            ui.tags.li(ui.strong("4. Final Match BIN:"), " Menghasilkan irisan BIN yang mengalami Picking dan Putaway secara bersamaan.")
                        ),
                        class_="accordion-content"
                    ), open=True
                ),
                ui.tags.details(
                    ui.tags.summary("📋 Mode 2: Non Audit (Filter Multiple Adjustment)"),
                    ui.div(
                        ui.tags.strong("Format Dokumen Multiple Adjustment:"),
                        ui.tags.ul(
                            ui.tags.li("Upload file ", ui.strong("Multiple Adjustment"), " dari Jezpro."),
                            ui.tags.li("File minimal 10 kolom: Kolom B (BIN), Kolom C (SKU), Kolom G (Sub Kategori), Kolom H (Harga Jual), dan Kolom J (Qty System)."),
                            ui.tags.li("Gunakan filter interaktif untuk memilah target BIN berdasarkan Sub Kategori, Brand, atau Tiering Kategori Harga (Luxury, Top, Mid, Entry, Mass Market).")
                        ),
                        class_="accordion-content"
                    ), open=True
                )
            )

        elif cur == "Validation Barcode SKU":
            guide_body = ui.div(
                ui.tags.details(
                    ui.tags.summary("📋 Panduan Validasi & Perubahan Barcode SKU"),
                    ui.div(
                        ui.tags.strong("Ketentuan 2 File Upload:"),
                        ui.tags.ul(
                            ui.tags.li(ui.strong("1. File Data Scan:"), " Kolom A = BIN, Kolom B = SKU fisik yang terscan, Kolom C = Qty Scan."),
                            ui.tags.li(ui.strong("2. File List Perubahan SKU:"), " Kolom A = SKU Resmi/Baru, Kolom B = Item Name, Kolom C = Variant.")
                        ),
                        ui.hr(style="margin: 8px 0; border-color: #CBD5E0;"),
                        ui.tags.strong("Alur Logika 2-Tahap:"),
                        ui.tags.ol(
                            ui.tags.li(ui.strong("Deteksi Cerdas:"), " Sistem mengecek apakah SKU scan mengandung kata pertama dari Item Name dan nomor variant-nya. Jika cocok, sistem menandai sebagai kandidat perubahan."),
                            ui.tags.li(ui.strong("Tahap 1 (Review):"), " Anda dapat memeriksa detail perbandingan di Tab Compare Detail sebelum data diubah."),
                            ui.tags.li(ui.strong("Tahap 2 (Eksekusi & Pivot):"), " Klik tombol 'EKSEKUSI PERUBAHAN SKU' untuk menerapkan SKU baru dan mengelompokkan (pivot) total stok per BIN dan SKU secara otomatis.")
                        ),
                        class_="accordion-content"
                    ), open=True
                )
            )

        # FALLBACK JIKA MENU LAIN
        else:
            guide_body = ui.div(
                ui.tags.i(class_="fa-regular fa-folder-open", style="font-size: 40px; color: #CBD5E0; margin-bottom: 8px;"),
                ui.p(f"Panduan dan Logic untuk halaman '{cur}' belum tersedia.", style="color: #718096; font-style: italic;"),
                style="text-align: center; padding: 2rem;"
            )

        ui.modal_show(ui.modal(
            guide_body, 
            title=ui.div(ui.tags.i(class_="fa-solid fa-book-open", style="color: #C5A059; margin-right: 8px;"), f"Panduan & Logic - {cur}"), 
            easy_close=True, 
            footer=ui.modal_button("Tutup", class_="btn-red-gradient")
        ))

        
    @render.ui
    def stock_minus_action_btn_ui():
        f = input.upload_stock_file() if "upload_stock_file" in input else None
        if f and len(f) > 0:
            return ui.div(
                ui.tags.button(
                    ui.tags.span(ui.tags.i(class_="fa-solid fa-play", style="margin-right: 6px; font-size: 14px;"), "PROSES DATA"), 
                    onclick="window.showGlobalSpinner(); Shiny.setInputValue('btn_process_stock_minus', Math.random(), {priority: 'event'});", 
                    class_="btn-red-gradient"
                ), 
                style="display: flex; justify-content: flex-end; width: 100%; margin-top: 1rem;"
            )
        return ui.div(
            ui.tags.button(
                ui.tags.i(class_="fa-solid fa-lock", style="margin-right: 6px; font-size: 14px;"), 
                "PILIH FILE UNTUK MEMULAI", disabled=True, class_="btn-locked"
            ), 
            style="display: flex; justify-content: flex-end; width: 100%; margin-top: 1rem;"
        )
    @render.ui
    def putaway_action_btn_ui():
        f_ds, f_as = input.ds_putaway_file() if "ds_putaway_file" in input else None, input.asal_putaway_file() if "asal_putaway_file" in input else None
        if (f_ds and len(f_ds) > 0) and (f_as and len(f_as) > 0):
            return ui.div(ui.tags.button(ui.tags.span(ui.tags.i(class_="fa-solid fa-play", style="margin-right: 6px; font-size: 14px;"), "COMPARE PUTAWAY"), onclick="window.showGlobalSpinner(); Shiny.setInputValue('btn_compare_putaway', Math.random(), {priority: 'event'});", class_="btn-red-gradient"), style="display: flex; justify-content: flex-end; width: 100%; margin-top: 0.5rem;")
        return ui.div(ui.tags.button(ui.tags.i(class_="fa-solid fa-lock", style="margin-right: 6px; font-size: 14px;"), "PILIH KEDUA FILE UNTUK MEMULAI", disabled=True, class_="btn-locked"), style="display: flex; justify-content: flex-end; width: 100%; margin-top: 0.5rem;")

    @render.ui
    def compare_system_action_btn_ui():
        f1, f2 = input.uploader_sys1() if "uploader_sys1" in input else None, input.uploader_sys2() if "uploader_sys2" in input else None
        if (f1 and len(f1) > 0) and (f2 and len(f2) > 0):
            return ui.div(ui.tags.button(ui.tags.span(ui.tags.i(class_="fa-solid fa-play", style="margin-right: 6px; font-size: 14px;"), "RUN COMPARE"), onclick="window.showGlobalSpinner(); Shiny.setInputValue('btn_run_compare_system', Math.random(), {priority: 'event'});", class_="btn-red-gradient"), style="display: flex; justify-content: flex-end; width: 100%; margin-top: 0.5rem;")
        return ui.div(ui.tags.button(ui.tags.i(class_="fa-solid fa-lock", style="margin-right: 6px; font-size: 14px;"), "PILIH FILE UTAMA (SYS 1 & SYS 2) UNTUK MEMULAI", disabled=True, class_="btn-locked"), style="display: flex; justify-content: flex-end; width: 100%; margin-top: 0.5rem;")
    # Result Views
    @render.ui
    def compare_system_results_container():
        if not state.compare_sys_processed(): return ui.div()
        diff_rows = state.df_cs_rows()
        if diff_rows and len(diff_rows) > 0:
            table_display = ui.div(
                ui.div(
                    ui.span("⚠️ Daftar Perbedaan Stok Berdasarkan Compare In & Out:", style="font-weight: bold; color: #DD6B20; font-size: 14px;"),
                    ui.download_button("btn_dl_compare_system", ui.tags.span(ui.tags.i(class_="fa-solid fa-download", style="margin-right: 6px; font-size: 14px;"), "Download Hasil Selisih (.xlsx)"), style="background-color: #10B981; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 8px 16px; cursor: pointer;"),
                    style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 0.75rem;"
                ),
                render_clean_table(state.df_cs_headers(), state.df_cs_rows())
            )
        else:
            table_display = ui.div("✅ Tidak ada perbedaan stok! Semua data match.", style="background: #C6F6D5; color: #276749; font-weight: bold; padding: 1.25rem; border-radius: 8px; text-align: center; font-size: 15px;")

        return ui.div(
            ui.hr(style="margin: 1.5rem 0; border-color: #CBD5E0;"),
            ui.h4("📋 RINGKASAN PERBANDINGAN STOK", style="font-size: 16px; color: #010B13; font-weight: 800; margin-bottom: 1rem;"),
            
            # --- 2 KOTAK ATAS: SEKARANG WARNA GELAP SAMA DENGAN BAWAH ---
            ui.div(
                dark_metric_box("📦 TOTAL ITEM DICEK", f"{state.cs_total_checked():,} ROW", "#3182CE"),
                dark_metric_box("⚠️ TOTAL ITEM SELISIH", f"{state.cs_total_diff():,} SKU", "#E53E3E"),
                style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; width: 100%; margin-bottom: 1rem;"
            ),
            
            # --- 3 KOTAK BAWAH ---
            ui.div(
                dark_metric_box("✅ SELISIH MATCH (DONE)", f"{state.cs_match_count()} SKU", "#C5A059"),
                dark_metric_box("⚠️ QTY SELISIH ≠ QTY FOUND", f"{state.cs_unmatch_count()} SKU", "#E53E3E"),
                dark_metric_box("🔍 SELISIH (NO HISTORY)", f"{state.cs_no_sales_count()} SKU", "#ECC94B"),
                style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; width: 100%; margin-bottom: 1.5rem;"
            ),
            table_display,
            style="width: 100%; background: white; padding: 1.5rem; border-radius: 12px; border: 1px solid #E2E8F0;"
        )

    @render.ui
    def stock_minus_results_container():
        if not state.stock_minus_processed(): return ui.div()
        return ui.div(
            ui.div(ui.div(ui.div("TOTAL QTY MINUS", style="color: #A0AEC0; font-size: 11px; font-weight: bold;"), ui.div(f"{state.total_qty_minus()}", style="color: #E53E3E; font-size: 22px; font-weight: bold;"), style="background: #1A1A1A; padding: 1rem; border-radius: 8px; border-left: 4px solid #E53E3E; text-align: center;"), ui.div(ui.div("TERCOVER", style="color: #A0AEC0; font-size: 11px; font-weight: bold;"), ui.div(f"{state.total_tercover()}", style="color: #38A169; font-size: 22px; font-weight: bold;"), style="background: #1A1A1A; padding: 1rem; border-radius: 8px; border-left: 4px solid #38A169; text-align: center;"), ui.div(ui.div("SISA ADJ", style="color: #A0AEC0; font-size: 11px; font-weight: bold;"), ui.div(f"{state.total_sisa_adj()}", style="color: #DD6B20; font-size: 22px; font-weight: bold;"), style="background: #1A1A1A; padding: 1rem; border-radius: 8px; border-left: 4px solid #DD6B20; text-align: center;"), style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 0.75rem; width: 100%; margin-bottom: 1.25rem;"),
            ui.navset_card_tab(
                ui.nav_panel("MINUS AWAL", ui.div(ui.div(ui.download_button("btn_dl_minus_awal", ui.tags.span(ui.tags.i(class_="fa-solid fa-download", style="margin-right: 6px; font-size: 14px;"), "Download Excel"), style="background-color: #10B981; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 6px 14px; cursor: pointer;"), style="display: flex; justify-content: flex-end; width: 100%; margin-bottom: 0.5rem;"), render_clean_table(state.df_minus_awal_headers(), state.df_minus_awal_rows()), style="padding: 0.75rem 0;")),
                ui.nav_panel("TEMPLATE SET UP", ui.div(ui.div(ui.download_button("btn_dl_set_up", ui.tags.span(ui.tags.i(class_="fa-solid fa-download", style="margin-right: 6px; font-size: 14px;"), "Download Excel"), style="background-color: #10B981; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 6px 14px; cursor: pointer;"), style="display: flex; justify-content: flex-end; width: 100%; margin-bottom: 0.5rem;"), render_clean_table(state.df_set_up_headers(), state.df_set_up_rows()), style="padding: 0.75rem 0;")),
                ui.nav_panel("JUSTIFIKASI", ui.div(ui.div(ui.download_button("btn_dl_justifikasi", ui.tags.span(ui.tags.i(class_="fa-solid fa-download", style="margin-right: 6px; font-size: 14px;"), "Download Excel"), style="background-color: #10B981; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 6px 14px; cursor: pointer;"), style="display: flex; justify-content: flex-end; width: 100%; margin-bottom: 0.5rem;"), render_clean_table(state.df_need_adj_headers(), state.df_need_adj_rows()), style="padding: 0.75rem 0;"))
            ), style="width: 100%;"
        )

    @render.ui
    def putaway_results_container():
        if not state.putaway_processed(): return ui.div()
        kurang_rows = state.df_kurang_rows()
        kurang_content = render_clean_table(state.df_kurang_headers(), kurang_rows) if kurang_rows else ui.div("✅ Semua Tercover!", style="background: #C6F6D5; color: #38A169; font-weight: bold; padding: 1rem; border-radius: 8px; text-align: center;")
        out_rows = state.df_out_rows()
        out_content = render_clean_table(state.df_out_headers(), out_rows) if out_rows else ui.div("✅ Tidak ada Outstanding!", style="background: #C6F6D5; color: #38A169; font-weight: bold; padding: 1rem; border-radius: 8px; text-align: center;")

        return ui.div(
            ui.hr(style="margin: 1.5rem 0 1rem 0; border-color: #E2E8F0;"),
            ui.h4("📋 RINGKASAN HASIL", style="font-size: 16px; color: #010B13; font-weight: 800; margin: 1rem 0;"),
            ui.div(ui.div(ui.div("Qty System Putaway", style="color: #A0AEC0; font-size: 11px; font-weight: bold;"), ui.div(f"{state.putaway_qty_system()}", style="color: #E53E3E; font-size: 22px; font-weight: bold;"), style="background: #1A1A1A; padding: 1rem; border-radius: 8px; border-left: 4px solid #E53E3E; text-align: center;"), ui.div(ui.div("Total Tersetup", style="color: #A0AEC0; font-size: 11px; font-weight: bold;"), ui.div(f"{state.putaway_total_setup()}", style="color: #38A169; font-size: 22px; font-weight: bold;"), style="background: #1A1A1A; padding: 1rem; border-radius: 8px; border-left: 4px solid #38A169; text-align: center;"), ui.div(ui.div("Kurang Setup", style="color: #A0AEC0; font-size: 11px; font-weight: bold;"), ui.div(f"{state.putaway_kurang_setup()}", style="color: #DD6B20; font-size: 22px; font-weight: bold;"), style="background: #1A1A1A; padding: 1rem; border-radius: 8px; border-left: 4px solid #DD6B20; text-align: center;"), ui.div(ui.div("Sisa Stok Putaway", style="color: #A0AEC0; font-size: 11px; font-weight: bold;"), ui.div(f"{state.putaway_sisa_stok()}", style="color: #3182CE; font-size: 22px; font-weight: bold;"), style="background: #1A1A1A; padding: 1rem; border-radius: 8px; border-left: 4px solid #3182CE; text-align: center;"), style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 0.75rem; width: 100%; margin-bottom: 1.25rem;"),
            ui.div(ui.download_button("btn_dl_putaway_report", ui.tags.span(ui.tags.i(class_="fa-solid fa-download", style="margin-right: 6px; font-size: 14px;"), "DOWNLOAD REPORT LENGKAP"), style="background-color: #10B981; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 8px 16px; cursor: pointer;"), style="display: flex; justify-content: flex-end; width: 100%; margin-bottom: 0.5rem;"),
            ui.navset_card_tab(ui.nav_panel("📋 Hasil Compare", ui.div(render_clean_table(state.df_comp_headers(), state.df_comp_rows()), style="padding: 0.75rem 0;")), ui.nav_panel("📝 List Setup", ui.div(render_clean_table(state.df_plist_headers(), state.df_plist_rows()), style="padding: 0.75rem 0;")), ui.nav_panel("⚠️ Kurang Setup", ui.div(kurang_content, style="padding: 0.75rem 0;")), ui.nav_panel("📦 Outstanding", ui.div(out_content, style="padding: 0.75rem 0;"))),
            style="width: 100%;"
        )

    # Process Action Listeners
    @reactive.Effect
    @reactive.event(input.btn_run_compare_system)
    def _proc_compare_system():
        f1, f2 = input.uploader_sys1(), input.uploader_sys2()
        if not f1 or not f2:
            state.error_modal_message.set("Pilih kedua file Stock System Start Shift & End Shift terlebih dahulu!")
            state.show_error_modal.set(True)
            return
        succ, msg = state.process_compare_system(f1, f2, input.uploader_track(), input.uploader_po(), input.uploader_rto_in(), input.uploader_rto_out(), input.uploader_refund())
        if succ: state.show_success_modal.set(True)
        else:
            state.error_modal_message.set(msg)
            state.show_error_modal.set(True)

    @render.download(filename="selisih_stok_validated.xlsx")
    def btn_dl_compare_system():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            state._raw_df_cs_diff.to_excel(writer, sheet_name='SELISIH_VALIDATED', index=False)
            state._raw_df_cs_all.to_excel(writer, sheet_name='ALL_COMPARISON', index=False)
        buf.seek(0)
        yield buf.getvalue()

    @reactive.Effect
    @reactive.event(input.btn_save_ongkir_manual)
    def _save_manual():
        d = input.btn_save_ongkir_manual()
        succ, msg = state.save_single_ongkir(d.get("supplier", ""), d.get("ekspedisi", ""), d.get("koli", "1"), d.get("ongkir", "0"), d.get("tgl", ""))
        if succ: state.show_success_modal.set(True)
        else:
            state.error_modal_message.set(msg)
            state.show_error_modal.set(True)

    @reactive.Effect
    @reactive.event(input.btn_execute_batch_upload)
    def _save_batch():
        f = input.upload_csv_batch()
        if not f:
            state.error_modal_message.set("Pilih file CSV terlebih dahulu!")
            state.show_error_modal.set(True)
            return
        with open(f[0]["datapath"], "rb") as fp:
            succ, msg = state.batch_upload_csv(fp.read())
        if succ: state.show_success_modal.set(True)
        else:
            state.error_modal_message.set(msg)
            state.show_error_modal.set(True)

    @reactive.Effect
    @reactive.event(input.toggle_row_id)
    def _toggle_chk(): state.toggle_select_id(str(input.toggle_row_id()))

    @reactive.Effect
    @reactive.event(input.change_filter_ekspedisi)
    def _filter_chg(): state.filter_ekspedisi.set(input.change_filter_ekspedisi())

    @reactive.Effect
    @reactive.event(input.btn_open_delete_modal)
    def _del_modal():
        ui.modal_show(ui.modal(
            ui.p("Apakah Anda yakin ingin menghapus data terpilih secara permanen dari database Supabase?"),
            title="⚠️ Konfirmasi Hapus Data", easy_close=True,
            footer=ui.div(ui.modal_button("Batal"), ui.tags.button("Ya, Hapus Permanen", onclick="document.body.classList.add('process-running'); Shiny.setInputValue('btn_confirm_delete_permanent', Math.random(), {priority: 'event'});", style="background: #E53E3E; color: white; border: none; padding: 6px 12px; border-radius: 6px; margin-left: 8px; font-weight: bold; cursor: pointer;"), style="display: flex; justify-content: flex-end;")
        ))

    @reactive.Effect
    @reactive.event(input.btn_confirm_delete_permanent)
    def _del_exec():
        succ, msg = state.execute_delete()
        ui.modal_remove()
        if succ:
            state.show_success_modal.set(True)
            ui.notification_show(msg, type="message", duration=4)
        else:
            state.error_modal_message.set(msg)
            state.show_error_modal.set(True)
            ui.notification_show(msg, type="error", duration=4)

    @reactive.Effect
    @reactive.event(input.btn_process_stock_minus)
    def _proc_stock_file():
        f = input.upload_stock_file()
        if not f:
            state.error_modal_message.set("Pilih file Stock Minus terlebih dahulu!")
            state.show_error_modal.set(True)
            return
        
        # Oper langsung file path dari temp folder shiny (tidak perlu fp.read() memakan RAM)
        succ, msg = state.process_stock_minus_file(f[0]["datapath"], f[0]["name"])
        if succ: 
            state.show_success_modal.set(True)
        else:
            state.error_modal_message.set(msg)
            state.show_error_modal.set(True)

    @render.download(filename="Data_Minus_Awal.xlsx")
    def btn_dl_minus_awal():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer: state._raw_df_minus_awal.to_excel(writer, index=False)
        buf.seek(0)
        yield buf.getvalue()

    @render.download(filename="Template_Set_Up.xlsx")
    def btn_dl_set_up():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer: state._raw_df_set_up.to_excel(writer, index=False)
        buf.seek(0)
        yield buf.getvalue()

    @render.download(filename="Data_Justifikasi.xlsx")
    def btn_dl_justifikasi():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer: state._raw_df_need_adj.to_excel(writer, index=False)
        buf.seek(0)
        yield buf.getvalue()

    @reactive.Effect
    @reactive.event(input.select_area_putaway)
    def _area_sel(): state.area_putaway.set(input.select_area_putaway())

    @reactive.Effect
    @reactive.event(input.btn_compare_putaway)
    def _proc_putaway_files():
        f_ds, f_as = input.ds_putaway_file(), input.asal_putaway_file()
        if not f_ds or not f_as:
            state.error_modal_message.set("Kedua file (DS Putaway & Asal Bin) wajib diupload!")
            state.show_error_modal.set(True)
            return
        with open(f_ds[0]["datapath"], "rb") as fp_ds, open(f_as[0]["datapath"], "rb") as fp_as:
            succ, msg = state.process_putaway_compare(fp_ds.read(), f_ds[0]["name"], fp_as.read(), f_as[0]["name"])
        if succ: state.show_success_modal.set(True)
        else:
            state.error_modal_message.set(msg)
            state.show_error_modal.set(True)

    @render.download(filename="REPORT_PUTAWAY_SYSTEM.xlsx")
    def btn_dl_putaway_report():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            state._raw_df_comp.to_excel(writer, sheet_name='COMPARE', index=False)
            state._raw_df_plist.to_excel(writer, sheet_name='PUTAWAY_LIST', index=False)
            state._raw_df_kurang.to_excel(writer, sheet_name='KURANG_SETUP', index=False)
            state._raw_df_out.to_excel(writer, sheet_name='OUTSTANDING', index=False)
            state._raw_df_updated.to_excel(writer, sheet_name='SISA_STOK_SYSTEM', index=False)
        buf.seek(0)
        yield buf.getvalue()

    # 1. Main Root Container (Hanya dibuat sekali & tidak akan hancur-bangun saat ganti menu)
    @render.ui
    def main_root_container():
        if not state.logged_in(): 
            return login_page()

        return ui.div(
            sidebar(state),
            ui.div(
                global_header(state),
                ui.output_ui("dynamic_page_content_area"),  # 👈 Sub-renderer terisolasi di sini!
                id="main-scroll-container",
                style="flex: 1; height: 100vh; overflow-y: auto; padding: 1.5rem; background-color: #F7FAFC;"
            ),
            style="display: flex; width: 100vw; height: 100vh; overflow: hidden; background-color: #111318;"
        )

    # 2. Sub-Renderer (Hanya bagian dalam ini saja yang berganti saat menu dipilih)
    @render.ui
    def dynamic_page_content_area():
        if not state.logged_in():
            return ui.div()
            
        content_type = state.get_active_content_type()

        if content_type == "dashboard_ongkir": return main_dashboard_view(state)
        elif content_type == "stock_minus": return stock_minus_view(state)
        elif content_type == "putaway_system": return putaway_view(state)
        elif content_type == "compare_system": return compare_system_view(state)
        elif content_type == "cycle_count": return cycle_count_view(state)
        elif content_type == "ppa_audit": return ppa_audit_view(state)
        elif content_type == "cycle_count_analyzer": return cycle_count_analyzer_view(state)
        elif content_type == "compare_rto": return compare_rto_view(state)
        elif content_type == "stock_opname": return stock_opname_view(state)
        elif content_type == "justification_so": return justification_so_view(state)
        elif content_type == "cross_check_real_sys": return cross_check_real_system_view(state)
        elif content_type == "balancing_stock": return balancing_stock_view(state)
        elif content_type == "physical_inventory_list": return physical_inventory_list_view(state)
        elif content_type == "validation_barcode_sku": return validation_barcode_sku_view(state)
        elif content_type in ["percentage_display", "percentage-display"]: return percentage_display_view(state)
        elif content_type in ["excel_practice", "latihan_excel"]: return excel_practice_view(state)
        elif content_type == "form_auditor": return auditor_view(state)
        elif content_type in ["memo_pengajuan", "memo-pengajuan"]: return memo_pengajuan_view(state)
        elif content_type == "warehouse_activity_monitor": return warehouse_activity_monitor_view(state)
        elif content_type == "compliance_audit": return compliance_audit_view(state)
        elif content_type in ["instock_validation", "instock-validation"]: return instock_validation_view(state)
        elif content_type in ["permintaan_fl", "permintaan-fl"]: 
            from views import permintaan_fl_view
            return permintaan_fl_view(state)
        elif content_type == "refill_shelving": 
            from views import refill_shelving_view
            return refill_shelving_view(state)
        elif content_type == "access_denied":
            return ui.div(ui.h2("⛔ Akses Ditolak", style="color: #E53E3E; font-weight: bold;"), style="padding: 3rem; text-align: center;")
        else:
            return ui.div(ui.h2(f"Halaman: {state.main_menu()}", style="font-weight: bold;"), style="padding: 3rem; text-align: center;")
# ==========================================================================
    # CYCLE COUNT / NON AUDIT CONTROLLER (FIXED: ANTI-RESET FILTER)
    # ==========================================================================
    @render.ui
    def cycle_count_action_btn_ui():
        f = input.upload_cycle_count_file() if "upload_cycle_count_file" in input else None
        if f and len(f) > 0:
            return ui.div(
                ui.tags.button(
                    ui.tags.span(ui.tags.i(class_="fa-solid fa-play", style="margin-right: 6px; font-size: 14px;"), "PROSES DATA"),
                    onclick="window.showGlobalSpinner(); Shiny.setInputValue('btn_process_cycle_count', Math.random(), {priority: 'event'});",
                    class_="btn-red-gradient"
                ),
                style="display: flex; justify-content: flex-end; width: 100%; margin-top: 1rem;"
            )
        return ui.div(
            ui.tags.button(
                ui.tags.i(class_="fa-solid fa-lock", style="margin-right: 6px; font-size: 14px;"),
                "PILIH FILE UNTUK MEMULAI", disabled=True, class_="btn-locked"
            ),
            style="display: flex; justify-content: flex-end; width: 100%; margin-top: 1rem;"
        )
    # 1. Container Filter: HANYA merender kontrol input (TIDAK membaca cc_total_* agar tidak ter-reset)
    @render.ui
    def cycle_count_results_container():
        if not state.cc_processed():
            return ui.div()

        return ui.div(
            # --- 1. FILTER MULTI-SELECT (Stabil & Tetap Terbuka) ---
            ui.div(
                ui.h4("🔍 Filter Brand, Sub Kategori & Kategori Harga", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 0.75rem;"),
                ui.div(
                    ui.div(ui.input_selectize("cc_filter_sub", "🗂 Sub Kategori:", choices=state.cc_list_sub(), multiple=True), style="flex: 1; min-width: 200px;"),
                    ui.div(ui.input_selectize("cc_filter_brand", "🏷️ Brand:", choices=state.cc_list_brand(), multiple=True), style="flex: 1; min-width: 200px;"),
                    ui.div(ui.input_selectize("cc_filter_tier", "💰 Kategori Harga:", choices=state.cc_list_tier(), multiple=True), style="flex: 1; min-width: 200px;"),
                    style="display: flex; gap: 1rem; flex-wrap: wrap; width: 100%; margin-bottom: 1rem;"
                ),
                style="background: white; padding: 1.25rem; border-radius: 10px; border: 1px solid #E2E8F0; margin-bottom: 1.25rem;"
            ),
            # --- WADAH METRIK & TABEL TERPISAH ---
            ui.output_ui("cycle_count_data_display_ui"),
            style="width: 100%;"
        )

    # 2. Container Data: Khusus merender Metrik & Tabel yang update secara reaktif tanpa mengganggu filter
    @render.ui
    def cycle_count_data_display_ui():
        if not state.cc_processed():
            return ui.div()

        return ui.div(
            # --- 2. KOTAK METRIK DARK GOLD THEME ---
            ui.div(
                dark_metric_box("🏭 Total BIN Harus Di-Scan", f"{state.cc_total_bin():,}", "#C5A059"),
                dark_metric_box("📦 Total SKU Harus Di-Scan", f"{state.cc_total_sku():,}", "#C5A059"),
                dark_metric_box("🔢 Total QTY Harus di Scan", f"{state.cc_total_qty():,}", "#C5A059"),
                style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; width: 100%; margin-bottom: 1.25rem;"
            ),

            # --- 3. DETAIL PREVIEW TABLE & DOWNLOAD ---
            ui.div(
                ui.div(
                    ui.h4("📋 Detail List Data Bin Cycle Count", style="font-size: 15px; font-weight: 800; color: #1A202C; margin: 0;"),
                    ui.download_button(
                        "btn_dl_cycle_count",
                        ui.tags.span(ui.tags.i(class_="fa-solid fa-download", style="margin-right: 6px; font-size: 14px;"), "Download Excel (.xlsx)"),
                        style="background-color: #10B981; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 8px 16px; cursor: pointer;"
                    ),
                    style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 0.75rem;"
                ),
                render_clean_table(state.df_cc_headers(), state.df_cc_rows(), "tbl_cc_filtered_preview"),
                style="background: white; padding: 1.25rem; border-radius: 10px; border: 1px solid #E2E8F0;"
            ),
            style="width: 100%;"
        )

    # Listener Filter Interaktif (Real-time Filter dengan casting list aman)
    @reactive.Effect
    def _on_cc_filter_change():
        if state.cc_processed():
            sub = list(input.cc_filter_sub()) if "cc_filter_sub" in input and input.cc_filter_sub() is not None else []
            brand = list(input.cc_filter_brand()) if "cc_filter_brand" in input and input.cc_filter_brand() is not None else []
            tier = list(input.cc_filter_tier()) if "cc_filter_tier" in input and input.cc_filter_tier() is not None else []
            state.apply_cc_filters(sub, brand, tier)

    # Eksekusi Proses File
    @reactive.Effect
    @reactive.event(input.btn_process_cycle_count)
    def _proc_cycle_count():
        f = input.upload_cycle_count_file()
        if not f:
            state.error_modal_message.set("Pilih file Multiple Adjustment terlebih dahulu!")
            state.show_error_modal.set(True)
            return
        with open(f[0]["datapath"], "rb") as fp:
            succ, msg = state.process_cycle_count_file(fp.read(), f[0]["name"])
        if succ:
            state.show_success_modal.set(True)
        else:
            state.error_modal_message.set(msg)
            state.show_error_modal.set(True)

    # Handler Download Excel
    @render.download(filename="List_Bin_Cycle_Count.xlsx")
    def btn_dl_cycle_count():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            state._raw_df_cc_filtered.to_excel(writer, sheet_name='CYCLE_COUNT', index=False)
        buf.seek(0)
        yield buf.getvalue()

# --- PUTAWAY & PICKING AUDIT BUTTON & HASIL ---
    @render.ui
    def ppa_action_btn_ui():
        f1 = input.uploader_ppa_sales() if "uploader_ppa_sales" in input else None
        f2 = input.uploader_ppa_rto() if "uploader_ppa_rto" in input else None
        f3 = input.uploader_ppa_mutasi() if "uploader_ppa_mutasi" in input else None

        if (f1 and len(f1) > 0) or (f2 and len(f2) > 0) or (f3 and len(f3) > 0):
            return ui.div(
                ui.tags.button(
                    ui.tags.span(ui.tags.i(class_="fa-solid fa-play", style="margin-right: 6px; font-size: 14px;"), "RUN AUDIT PROCESS"),
                    onclick="window.showGlobalSpinner(); Shiny.setInputValue('btn_process_ppa_audit', Math.random(), {priority: 'event'});",
                    class_="btn-red-gradient"
                ),
                style="display: flex; justify-content: flex-end; width: 100%; margin-top: 0.5rem;"
            )
        return ui.div(
            ui.tags.button(
                ui.tags.i(class_="fa-solid fa-lock", style="margin-right: 6px; font-size: 14px;"),
                "UPLOAD SETIDAKNYA 1 FILE UNTUK MEMULAI", disabled=True, class_="btn-locked"
            ),
            style="display: flex; justify-content: flex-end; width: 100%; margin-top: 0.5rem;"
        )

    @render.ui
    def ppa_results_container():
        if not state.ppa_processed():
            return ui.div()

        # Tab 5 matching alert
        if state.ppa_final_matching_bin() > 0:
            final_content = render_clean_table(state.df_ppa_final_headers(), state.df_ppa_final_rows())
        else:
            final_content = ui.div("⚠️ Tidak ada BIN yang sama/cocok antara hasil Picking Audit dan Putaway Audit.", style="background: #FFF5F5; color: #E53E3E; font-weight: bold; padding: 1.25rem; border-radius: 8px; text-align: center;")

        return ui.div(
            ui.hr(style="margin: 1.5rem 0; border-color: #CBD5E0;"),
            ui.h4("📋 RINGKASAN DETAIL AUDIT", style="font-size: 16px; color: #010B13; font-weight: 800; margin-bottom: 1rem;"),
            
            # --- 4 KOTAK METRIK DARK THEME ---
            ui.div(
                dark_metric_box("🔢 Total QTY Picking (Sales/RTO)", f"{state.ppa_total_picking_qty():,}", "#C5A059"),
                dark_metric_box("🎯 Unique BIN Picking", f"{state.ppa_unique_picking_bin():,} BIN", "#3182CE"),
                dark_metric_box("🎯 Unique Last BIN Mutasi", f"{state.ppa_unique_putaway_bin():,} BIN", "#10B981"),
                dark_metric_box("✅ Final Match BIN Audit", f"{state.ppa_final_matching_bin():,} BIN", "#E50914"),
                style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; width: 100%; margin-bottom: 1.25rem;"
            ),

            # --- DOWNLOAD REPORT LENGKAP MULTI-SHEET ---
            ui.div(
                ui.download_button(
                    "btn_dl_ppa_all",
                    ui.tags.span(ui.tags.i(class_="fa-solid fa-download", style="margin-right: 6px; font-size: 14px;"), "DOWNLOAD ALL AUDIT REPORT (.xlsx)"),
                    style="background-color: #10B981; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 8px 16px; cursor: pointer;"
                ),
                style="display: flex; justify-content: flex-end; width: 100%; margin-bottom: 0.75rem;"
            ),

            # --- 5 TAB DETAIL HASIL ---
            ui.navset_card_tab(
                ui.nav_panel("📋 DETAIL PICKING AUDIT", ui.div(render_clean_table(state.df_ppa_picking_headers(), state.df_ppa_picking_rows()), style="padding: 0.75rem 0;")),
                ui.nav_panel("🎯 UNIQUE BIN PICKING", ui.div(render_clean_table(state.df_ppa_upicking_headers(), state.df_ppa_upicking_rows()), style="padding: 0.75rem 0;")),
                ui.nav_panel("📋 DETAIL PUTAWAY AUDIT", ui.div(render_clean_table(state.df_ppa_putaway_headers(), state.df_ppa_putaway_rows()), style="padding: 0.75rem 0;")),
                ui.nav_panel("🎯 UNIQUE LAST BIN PUTAWAY", ui.div(render_clean_table(state.df_ppa_uputaway_headers(), state.df_ppa_uputaway_rows()), style="padding: 0.75rem 0;")),
                ui.nav_panel("✅ FINAL LIST (MATCH BIN)", ui.div(final_content, style="padding: 0.75rem 0;"))
            ),
            style="width: 100%; background: white; padding: 1.5rem; border-radius: 12px; border: 1px solid #E2E8F0;"
        )

    # Eksekusi Proses Audit
    @reactive.Effect
    @reactive.event(input.btn_process_ppa_audit)
    def _proc_ppa_audit():
        f_sales = input.uploader_ppa_sales()
        f_rto = input.uploader_ppa_rto()
        f_mutasi = input.uploader_ppa_mutasi()

        succ, msg = state.process_ppa_audit(f_sales, f_rto, f_mutasi)
        if succ:
            state.show_success_modal.set(True)
        else:
            state.error_modal_message.set(msg)
            state.show_error_modal.set(True)

    # Handler Download Excel Multi-Sheet
    @render.download(filename="REPORT_PUTAWAY_PICKING_AUDIT.xlsx")
    def btn_dl_ppa_all():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            state._raw_df_ppa_final.to_excel(writer, sheet_name='FINAL_MATCH_BIN', index=False)
            state._raw_df_ppa_picking.to_excel(writer, sheet_name='PICKING_DETAIL', index=False)
            state._raw_df_ppa_upicking.to_excel(writer, sheet_name='UNIQUE_BIN_PICKING', index=False)
            state._raw_df_ppa_putaway.to_excel(writer, sheet_name='PUTAWAY_DETAIL', index=False)
            state._raw_df_ppa_uputaway.to_excel(writer, sheet_name='UNIQUE_LAST_BIN', index=False)
        buf.seek(0)
        yield buf.getvalue()

# ==========================================================================
    # CYCLE COUNT ANALYZER CONTROLLER (KARTU MANDIRI ANTI-LONCAT)
    # ==========================================================================
    @render.ui
    def cca_bin_sys_ui():
        b = input.cca_branch() if "cca_branch" in input else "SURABAYA"
        choices = BRANCH_BIN_MAPPING.get(b, [])
        return ui.input_selectize("cca_bin_sys", "🏭 BIN System:", choices=choices, multiple=True, width="100%")

    # --- STEP 1 ---
    @render.ui
    def cca_step1_btn_ui():
        f1 = input.cca_up_scan() if "cca_up_scan" in input else None
        f2 = input.cca_up_stock() if "cca_up_stock" in input else None
        if f1 and f2:
            return ui.div(
                ui.tags.button(
                    ui.tags.span(ui.tags.i(class_="fa-solid fa-play", style="margin-right: 6px; font-size: 14px;"), "RUN COMPARE"),
                    onclick="document.body.classList.add('process-running'); Shiny.setInputValue('btn_run_cca_step1', Math.random(), {priority: 'event'});",
                    class_="btn-red-gradient"
                ), style="display: flex; justify-content: flex-end; width: 100%; margin-top: 0.5rem;"
            )
        return ui.div(
            ui.tags.button("UPLOAD DATA SCAN & STOCK SYSTEM UNTUK MEMULAI", disabled=True, class_="btn-locked"),
            style="display: flex; justify-content: flex-end; width: 100%; margin-top: 0.5rem;"
        )

    @render.ui
    def cca_step1_results_ui():
        if not state.cca_step1_done(): return ui.div()
        return ui.div(
            ui.hr(style="margin: 1rem 0; border-color: #E2E8F0;"),
            ui.div(
                dark_metric_box("📦 QTY REAL +", f"{state.cca_qty_real_plus():,}", "#C5A059"),
                dark_metric_box("🔐 QTY SYSTEM +", f"{state.cca_qty_sys_plus():,}", "#E53E3E"),
                style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; width: 100%; margin-bottom: 1rem;"
            ),
            ui.div(
                ui.download_button(
                    "btn_dl_cca_step1",
                    ui.tags.span(ui.tags.i(class_="fa-solid fa-download", style="margin-right: 6px; font-size: 14px;"), "DOWNLOAD EXCEL STEP 1 (.xlsx)"),
                    style="background-color: #10B981; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 8px 16px; cursor: pointer;"
                ),
                style="display: flex; justify-content: flex-end; width: 100%; margin-bottom: 0.75rem;"
            ),
            ui.navset_card_tab(
                ui.nav_panel("📋 DATA SCAN", ui.div(render_clean_table(state.df_cca_scan_headers(), state.df_cca_scan_rows(), "tbl_cca_scan"), style="padding: 0.75rem 0;")),
                ui.nav_panel("📊 STOCK SYSTEM", ui.div(render_clean_table(state.df_cca_stock_headers(), state.df_cca_stock_rows(), "tbl_cca_stock"), style="padding: 0.75rem 0;")),
                ui.nav_panel("➕ REAL +", ui.div(render_clean_table(state.df_cca_real_headers(), state.df_cca_real_rows(), "tbl_cca_real"), style="padding: 0.75rem 0;")),
                ui.nav_panel("➖ SYSTEM +", ui.div(render_clean_table(state.df_cca_sys_headers(), state.df_cca_sys_rows(), "tbl_cca_sys"), style="padding: 0.75rem 0;"))
            ), style="width: 100%;"
        )

    @reactive.Effect
    @reactive.event(input.btn_run_cca_step1)
    def _proc_cca_step1():
        f_scan, f_stock = input.cca_up_scan(), input.cca_up_stock()
        sub = input.cca_sub_kat() if "cca_sub_kat" in input else []
        brand = input.cca_brand() if "cca_brand" in input else []
        bin_sys = input.cca_bin_sys() if "cca_bin_sys" in input else []
        succ, msg = state.run_cca_step1(f_scan, f_stock, sub, brand, bin_sys)
        if succ: state.show_success_modal.set(True)
        else:
            state.error_modal_message.set(msg)
            state.show_error_modal.set(True)

    @render.download(filename="Step1_Compare_Scan_Stock.xlsx")
    def btn_dl_cca_step1():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            state._raw_df_cca_scan.to_excel(writer, sheet_name='DATA_SCAN', index=False)
            state._raw_df_cca_stock.to_excel(writer, sheet_name='STOCK_SYSTEM', index=False)
            state._raw_df_cca_real_plus.to_excel(writer, sheet_name='REAL_PLUS', index=False)
            state._raw_df_cca_sys_plus.to_excel(writer, sheet_name='SYSTEM_PLUS', index=False)
        buf.seek(0)
        yield buf.getvalue()

    # --- KARTU MANDIRI STEP 2 & 3 (CYCLE COUNT) ---
    @render.ui
    def cca_step2_card_ui():
        if not state.cca_step1_done(): return ui.div()
        step2_results = ui.div()
        if state.cca_step2_done():
            step2_results = ui.div(
                ui.hr(style="margin: 1rem 0; border-color: #E2E8F0;"),
                ui.div(
                    ui.h4("✅ HASIL ALOKASI", style="font-size: 15px; font-weight: 800; color: #1A202C; margin: 0;"),
                    ui.download_button("btn_dl_cca_step2", ui.tags.span(ui.tags.i(class_="fa-solid fa-download", style="margin-right: 6px; font-size: 14px;"), "DOWNLOAD HASIL ALOKASI (.xlsx)"), style="background-color: #10B981; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 8px 16px; cursor: pointer;"),
                    style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 0.75rem;"
                ),
                ui.navset_card_tab(
                    ui.nav_panel("📊 ALLOCATION DETAIL", ui.div(render_clean_table(state.df_cca_alloc_headers(), state.df_cca_alloc_rows(), "tbl_cca_alloc"), style="padding: 0.75rem 0;")),
                    ui.nav_panel("📉 UPDATED SYSTEM", ui.div(render_clean_table(state.df_cca_sys_upd_headers(), state.df_cca_sys_upd_rows(), "tbl_cca_sys_upd"), style="padding: 0.75rem 0;")),
                    ui.nav_panel("📦 SET UP REAL +", ui.div(render_clean_table(state.df_cca_setup_real_headers(), state.df_cca_setup_real_rows(), "tbl_cca_setup_real"), style="padding: 0.75rem 0;"))
                ),
                ui.hr(style="margin: 1.5rem 0; border-color: #E2E8F0;"),
                ui.div(
                    ui.h4("📋 RECON REPORTS (HASIL STEP 1 - 3)", style="font-size: 15px; font-weight: 800; color: #1A202C; margin: 0;"),
                    ui.download_button(
                        "btn_dl_cca_rec_all", 
                        ui.tags.span(ui.tags.i(class_="fa-solid fa-file-excel", style="margin-right: 6px; font-size: 13px;"), "DOWNLOAD RECON STEP 3 FULL (.xlsx)"), 
                        style="background: linear-gradient(135deg, #10B981 0%, #059669 100%); color: white; font-weight: bold; border-radius: 6px; border: none; padding: 8px 16px; cursor: pointer; font-size: 13px; box-shadow: 0 2px 6px rgba(16,185,129,0.25);"
                    ),
                    style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 1rem; flex-wrap: wrap; gap: 8px;"
                ),
                ui.div(
                    ui.div(
                        ui.div(
                            ui.h5("📋 REAL + RECON", style="font-size: 14px; font-weight: 800; color: #1A202C; margin: 0;"),
                            ui.download_button("btn_dl_cca_rec_real", ui.tags.span(ui.tags.i(class_="fa-solid fa-download", style="margin-right: 6px; font-size: 12px;"), "Download (.xlsx)"), style="background-color: #10B981; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 5px 12px; cursor: pointer; font-size: 12px;"),
                            style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 0.6rem;"
                        ),
                        render_clean_table(state.df_cca_rec_real_headers(), state.df_cca_rec_real_rows(), "tbl_cca_rec_real"),
                        style="flex: 1; min-width: 320px; background: #F8FAFC; padding: 1rem; border-radius: 8px; border: 1px solid #CBD5E0;"
                    ),
                    ui.div(
                        ui.div(
                            ui.h5("🔐 SYSTEM + OUTSTANDING", style="font-size: 14px; font-weight: 800; color: #1A202C; margin: 0;"),
                            ui.download_button("btn_dl_cca_rec_sys", ui.tags.span(ui.tags.i(class_="fa-solid fa-download", style="margin-right: 6px; font-size: 12px;"), "Download (.xlsx)"), style="background-color: #10B981; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 5px 12px; cursor: pointer; font-size: 12px;"),
                            style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 0.6rem;"
                        ),
                        render_clean_table(state.df_cca_rec_sys_headers(), state.df_cca_rec_sys_rows(), "tbl_cca_rec_sys"),
                        style="flex: 1; min-width: 320px; background: #F8FAFC; padding: 1rem; border-radius: 8px; border: 1px solid #CBD5E0;"
                    ),
                    style="display: flex; gap: 1rem; flex-wrap: wrap; width: 100%;"
                )
            )

        return ui.div(
            ui.h4("2️⃣ Upload BIN COVERAGE (ALL BIN DEFAULT & KARANTINA)", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 0.75rem;"),
            custom_uploader_box("cca_up_cov", "📥 FILE BIN COVERAGE"),
            # 👇 TOMBOL LANGSUNG (PASTI MUNCUL) 👇
            ui.div(
                ui.tags.button(
                    ui.tags.span(ui.tags.i(class_="fa-solid fa-play", style="margin-right: 6px; font-size: 14px;"), "RUN ALLOCATION"),
                    onclick="window.showGlobalSpinner(); Shiny.setInputValue('btn_run_cca_step2', Math.random(), {priority: 'event'});",
                    class_="btn-red-gradient"
                ),
                style="display: flex; justify-content: flex-end; width: 100%; margin-top: 0.75rem;"
            ),
            step2_results,
            class_="step-card-box",
            style="background: white; padding: 1.25rem; border-radius: 10px; border: 1px solid #E2E8F0; margin-bottom: 1.25rem;"
        )
    @render.ui
    def cca_step2_btn_ui():
        f = input.cca_up_cov() if "cca_up_cov" in input else None
        if f:
            return ui.div(
                ui.tags.button(
                    ui.tags.span(ui.tags.i(class_="fa-solid fa-play", style="margin-right: 6px; font-size: 14px;"), "RUN ALLOCATION"),
                    onclick="document.body.classList.add('process-running'); Shiny.setInputValue('btn_run_cca_step2', Math.random(), {priority: 'event'});",
                    class_="btn-red-gradient"
                ), style="display: flex; justify-content: flex-end; width: 100%; margin-top: 0.5rem;"
            )
        return ui.div(ui.tags.button("UPLOAD FILE BIN COVERAGE UNTUK ALOKASI", disabled=True, class_="btn-locked"), style="display: flex; justify-content: flex-end; width: 100%; margin-top: 0.5rem;")

    @reactive.Effect
    @reactive.event(input.btn_run_cca_step2)
    def _proc_cca_step2():
        f = input.cca_up_cov()
        bin_cov = input.cca_bin_cov() if "cca_bin_cov" in input else []
        succ, msg = state.run_cca_step2(f, bin_cov)
        ui.insert_ui(ui.tags.script("if (window.hideGlobalSpinner) window.hideGlobalSpinner();"), selector="head", where="beforeEnd")
        if succ: 
            state.show_success_modal.set(True)
        else:
            state.error_modal_message.set(msg)
            state.show_error_modal.set(True)

    @render.download(filename="Hasil_Alokasi_Step2.xlsx")
    def btn_dl_cca_step2():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            state._raw_df_cca_alloc.to_excel(writer, sheet_name='ALLOCATION_DETAIL', index=False)
            state._raw_df_cca_sys_upd.to_excel(writer, sheet_name='UPDATED_SYSTEM', index=False)
            state._raw_df_cca_setup_real.to_excel(writer, sheet_name='SET_UP_REAL_PLUS', index=False)
        buf.seek(0)
        yield buf.getvalue()
# Handler Download Recon Step 3 di Cycle Count
    @render.download(filename="CycleCount_Real_Plus_Recon.xlsx")
    def btn_dl_cca_rec_real():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            df = state._raw_df_cca_rec_real if not state._raw_df_cca_rec_real.empty else pd.DataFrame(columns=['BIN', 'SKU', 'ITEM NAME', 'QTY_SCAN', 'QTY_SYSTEM', 'DIFF', 'HASIL RECONCILIATION'])
            df.to_excel(writer, sheet_name='REAL_PLUS_RECON', index=False)
        buf.seek(0)
        yield buf.getvalue()

    @render.download(filename="CycleCount_System_Plus_Recon.xlsx")
    def btn_dl_cca_rec_sys():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            df = state._raw_df_cca_rec_sys if not state._raw_df_cca_rec_sys.empty else pd.DataFrame(columns=['BIN', 'SKU', 'DIFF', 'HASIL REKONSILIASI'])
            df.to_excel(writer, sheet_name='SYSTEM_PLUS_RECON', index=False)
        buf.seek(0)
        yield buf.getvalue()

    @render.download(filename="CycleCount_Recon_Step3_Full.xlsx")
    def btn_dl_cca_rec_all():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            df_r = state._raw_df_cca_rec_real if not state._raw_df_cca_rec_real.empty else pd.DataFrame(columns=['BIN', 'SKU', 'ITEM NAME', 'QTY_SCAN', 'QTY_SYSTEM', 'DIFF', 'HASIL RECONCILIATION'])
            df_s = state._raw_df_cca_rec_sys if not state._raw_df_cca_rec_sys.empty else pd.DataFrame(columns=['BIN', 'SKU', 'DIFF', 'HASIL REKONSILIASI'])
            df_r.to_excel(writer, sheet_name='REAL_PLUS_RECON', index=False)
            df_s.to_excel(writer, sheet_name='SYSTEM_OUTSTANDING', index=False)
        buf.seek(0)
        yield buf.getvalue()

# ==========================================================================
    # CYCLE COUNT ANALYZER - STEP 4 EVENT HANDLER
    # ==========================================================================
    @reactive.Effect
    @reactive.event(input.btn_run_cca_step4)
    def _proc_cca_step4():
        f = input.cca_up_recon_real() if "cca_up_recon_real" in input else None
        succ, msg = state.run_cca_step4(f)
        ui.insert_ui(ui.tags.script("if (window.hideGlobalSpinner) window.hideGlobalSpinner();"), selector="head", where="beforeEnd")
        if succ:
            state.show_success_modal.set(True)
        else:
            state.error_modal_message.set(msg)
            state.show_error_modal.set(True)

    @render.download(filename="Hasil_Recon_Real_Plus_CCA.xlsx")
    def btn_dl_cca_step4():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            state._raw_df_cca_adj4.to_excel(writer, sheet_name='REAL_PLUS_ADJ', index=False)
        buf.seek(0)
        yield buf.getvalue()
    # ==========================================================================
    # CYCLE COUNT ANALYZER CONTROLLER (STEP 4, 5, & 6)
    # ==========================================================================
    @render.ui
    def cca_step4_card_ui():
        if not state.cca_step2_done(): return ui.div()
        
        # JIKA DATA KOSONG: Tampilkan kartu hijau ringkas
        if state._raw_df_cca_rec_real.empty:
            return ui.div(
                ui.h4("3️⃣ RECON REAL + PROCESS", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 0.5rem;"),
                ui.div(
                    ui.tags.i(class_="fa-solid fa-circle-check", style="color: #22543D; font-size: 18px; margin-right: 8px;"),
                    ui.span("Semua item Real + telah ter-cover penuh oleh System + dan BIN Coverage (0 Selisih). Langkah rekonsiliasi Real + selesai otomatis.", style="font-weight: 600; font-size: 13px;"),
                    style="background: #C6F6D5; color: #22543D; padding: 0.85rem 1.25rem; border-radius: 8px; border: 1px solid #9AE6B4; display: flex; align-items: center;"
                ),
                class_="step-card-box",
                style="background: white; padding: 1.25rem; border-radius: 10px; border: 1px solid #E2E8F0; margin-bottom: 1.25rem;"
            )

        # JIKA ADA DATA: Tampilkan uploader dan hasil
        step4_results = ui.div()
        if state.cca_step4_done():
            step4_results = ui.div(
                ui.hr(style="margin: 1rem 0; border-color: #E2E8F0;"),
                ui.div(
                    dark_metric_box("⚠️ TOTAL REAL + NEED ADJ", f"{state.cca_qty_need_adj():,} QTY", "#E53E3E"),
                    dark_metric_box("📦 TOTAL SKU", f"{state.cca_sku_need_adj():,} SKU", "#3182CE"),
                    style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; width: 100%; margin-bottom: 1rem;"
                ),
                ui.div(
                    ui.download_button("btn_dl_cca_step4", ui.tags.span(ui.tags.i(class_="fa-solid fa-download", style="margin-right: 6px; font-size: 14px;"), "DOWNLOAD HASIL RECON REAL + (.xlsx)"), style="background-color: #10B981; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 8px 16px; cursor: pointer;"),
                    style="display: flex; justify-content: flex-end; width: 100%; margin-bottom: 0.75rem;"
                ),
                render_clean_table(state.df_cca_adj4_headers(), state.df_cca_adj4_rows(), "tbl_cca_adj4")
            )

        return ui.div(
            ui.h4("3️⃣ RECON REAL + PROCESS", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 0.75rem;"),
            custom_uploader_box("cca_up_recon_real", "📥 Upload HASIL RECON REAL +"),
            # 👇 TOMBOL LANGSUNG (PASTI MUNCUL) 👇
            ui.div(
                ui.tags.button(
                    ui.tags.span(ui.tags.i(class_="fa-solid fa-play", style="margin-right: 6px; font-size: 14px;"), "RUN RECON ANALYSIS"),
                    onclick="window.showGlobalSpinner(); Shiny.setInputValue('btn_run_cca_step4', Math.random(), {priority: 'event'});",
                    class_="btn-red-gradient"
                ),
                style="display: flex; justify-content: flex-end; width: 100%; margin-top: 0.75rem;"
            ),
            step4_results,
            class_="step-card-box",
            style="background: white; padding: 1.25rem; border-radius: 10px; border: 1px solid #E2E8F0; margin-bottom: 1.25rem;"
        )
    # ==========================================================================
    # CYCLE COUNT ANALYZER - STEP 5: RECON SYSTEM + & CEK ADJUSTMENT
    # ==========================================================================
    @render.ui
    def cca_step5_card_ui():
        if not state.cca_step2_done() or not state.cca_step4_done():
            return ui.div()

        if state._raw_df_cca_rec_sys.empty:
            return ui.div(
                ui.h4("4️⃣ RECON SYSTEM + (SET UP KARANTINA)", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 0.5rem;"),
                ui.div(
                    ui.tags.i(class_="fa-solid fa-circle-check", style="color: #22543D; font-size: 18px; margin-right: 8px;"),
                    ui.span("Tidak ada item System + Outstanding (0 Selisih). Tidak ada stok yang perlu dimutasi ke Karantina. Langkah karantina selesai otomatis.", style="font-weight: 600; font-size: 13px;"),
                    style="background: #C6F6D5; color: #22543D; padding: 0.85rem 1.25rem; border-radius: 8px; border: 1px solid #9AE6B4; display: flex; align-items: center;"
                ),
                class_="step-card-box",
                style="background: white; padding: 1.25rem; border-radius: 10px; border: 1px solid #E2E8F0; margin-bottom: 1.25rem;"
            )

        step5_results = ui.div()
        if state.cca_step5_done():
            step5_results = ui.div(
                ui.hr(style="margin: 1rem 0; border-color: #E2E8F0;"),
                ui.div(
                    dark_metric_box("☣️ QTY TO KARANTINA", f"{state.cca_qty_karantina():,} QTY", "#ECC94B"),
                    dark_metric_box("🏷️ SKU TO KARANTINA", f"{state.cca_sku_karantina():,} SKU", "#ECC94B"),
                    style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; width: 100%; margin-bottom: 1rem;"
                ),
                ui.div(
                    ui.download_button(
                        "btn_dl_cca_karantina",
                        ui.tags.span(ui.tags.i(class_="fa-solid fa-download", style="margin-right: 6px; font-size: 14px;"), "DOWNLOAD HASIL KARANTINA (.xlsx)"),
                        style="background-color: #10B981; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 8px 16px; cursor: pointer;"
                    ),
                    style="display: flex; justify-content: flex-end; width: 100%; margin-bottom: 0.75rem;"
                ),
                ui.navset_card_tab(
                    ui.nav_panel("📦 HASIL KARANTINA", ui.div(render_clean_table(state.df_cca_karantina_headers(), state.df_cca_karantina_rows(), "tbl_cca_karantina"), style="padding: 0.75rem 0;")),
                    ui.nav_panel("🔍 DATA PENGECEKAN (AUDIT)", ui.div(render_clean_table(state.df_cca_check5_headers(), state.df_cca_check5_rows(), "tbl_cca_check5"), style="padding: 0.75rem 0;"))
                )
            )

        return ui.div(
            ui.h4("4️⃣ Recon System + Process (Set Up Karantina & Cek Adjustment)", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 0.75rem;"),
            ui.div(
                custom_uploader_box("cca_up_recon_sys", "1. Upload SYSTEM + RECON"),
                custom_uploader_box("cca_up_adj_sys", "2. Upload STOCK CEK ADJUSMENT (-) (Opsional)"),
                style="display: flex; gap: 1rem; width: 100%; margin-bottom: 0.5rem; flex-wrap: wrap;"
            ),
            ui.div(
                ui.tags.button(
                    ui.tags.span(ui.tags.i(class_="fa-solid fa-play", style="margin-right: 6px; font-size: 14px;"), "GENERATE KARANTINA"),
                    onclick="window.showGlobalSpinner(); Shiny.setInputValue('btn_run_cca_step5', Math.random(), {priority: 'event'});",
                    class_="btn-red-gradient"
                ),
                style="display: flex; justify-content: flex-end; width: 100%; margin-top: 0.75rem;"
            ),
            step5_results,
            class_="step-card-box",
            style="background: white; padding: 1.25rem; border-radius: 10px; border: 1px solid #E2E8F0; margin-bottom: 1.25rem;"
        )

    @reactive.Effect
    @reactive.event(input.btn_run_cca_step5)
    def _proc_cca_step5():
        f1 = input.cca_up_recon_sys() if "cca_up_recon_sys" in input else None
        f2 = input.cca_up_adj_sys() if "cca_up_adj_sys" in input else None

        if state._raw_df_cca_rec_sys.empty:
            succ, msg = state.run_cca_step5(None, None)
        else:
            if not f1:
                ui.insert_ui(ui.tags.script("window.hideGlobalSpinner();"), selector="head", where="beforeEnd")
                state.error_modal_message.set("Upload file SYSTEM + RECON terlebih dahulu!")
                state.show_error_modal.set(True)
                return
            succ, msg = state.run_cca_step5(f1, f2)

        ui.insert_ui(ui.tags.script("window.hideGlobalSpinner();"), selector="head", where="beforeEnd")
        if succ: state.show_success_modal.set(True)
        else:
            state.error_modal_message.set(msg)
            state.show_error_modal.set(True)

    # ==========================================================================
    # CYCLE COUNT ANALYZER - STEP 6: MISS LOCATION REPORT LENGKAP
    # ==========================================================================
    @render.ui
    def cca_step6_card_ui():
        if not state.cca_step2_done() or not state.cca_step5_done():
            return ui.div()

        step6_results = ui.div()
        if state.cca_step6_done():
            step6_results = ui.div(
                ui.hr(style="margin: 1rem 0; border-color: #E2E8F0;"),
                ui.div(
                    dark_metric_box("📦 TOTAL SKU MISS LOC.", f"{state.cca_sku_miss_loc():,} ITEM", "#3182CE"),
                    dark_metric_box("🔢 TOTAL QTY MISS LOC.", f"{state.cca_qty_miss_loc():,} ITEM", "#E53E3E"),
                    dark_metric_box("☣️ QTY KE KARANTINA", f"{state.cca_qty_karantina():,} ITEM", "#ECC94B"),
                    style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; width: 100%; margin-bottom: 1rem;"
                ),
                ui.div(
                    ui.download_button(
                        "btn_dl_cca_miss_loc", 
                        ui.tags.span(ui.tags.i(class_="fa-solid fa-download", style="margin-right: 6px; font-size: 14px;"), "DOWNLOAD MISS LOC REPORT FULL (.xlsx)"), 
                        style="background-color: #10B981; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 8px 16px; cursor: pointer;"
                    ),
                    style="display: flex; justify-content: flex-end; width: 100%; margin-bottom: 0.75rem;"
                ),
                ui.navset_card_tab(
                    ui.nav_panel("📄 Salah Letak (Rak ke Rak)", ui.div(render_clean_table(state.df_cca_miss_loc_headers(), state.df_cca_miss_loc_rows(), "tbl_cca_miss_loc"), style="padding: 0.75rem 0;")),
                    ui.nav_panel("☣️ Miss Loc ke Karantina", ui.div(render_clean_table(state.df_cca_karantina_headers(), state.df_cca_karantina_rows(), "tbl_cca_karan_loc"), style="padding: 0.75rem 0;")),
                    ui.nav_panel("📊 Summary Rekapitulasi", ui.div(render_clean_table(state.df_cca_sum_miss_headers(), state.df_cca_sum_miss_rows(), "tbl_cca_sum_miss"), style="padding: 0.75rem 0;"))
                )
            )

        return ui.div(
            ui.h4("5️⃣ MISS LOCATION REPORT", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 0.75rem;"),
            ui.div(
                ui.tags.button(
                    ui.tags.span(ui.tags.i(class_="fa-solid fa-chart-pie", style="margin-right: 6px; font-size: 14px;"), "GENERATE MISS LOC REPORT"),
                    onclick="window.showGlobalSpinner(); Shiny.setInputValue('btn_run_cca_step6', Math.random(), {priority: 'event'});",
                    class_="btn-red-gradient"
                ),
                style="display: flex; justify-content: flex-end; width: 100%; margin-top: 0.5rem;"
            ),
            step6_results,
            class_="step-card-box",
            style="background: white; padding: 1.25rem; border-radius: 10px; border: 1px solid #E2E8F0; margin-bottom: 1.25rem;"
        )

    @reactive.Effect
    @reactive.event(input.btn_run_cca_step6)
    def _proc_cca_step6():
        succ, msg = state.run_cca_step6()
        ui.insert_ui(ui.tags.script("window.hideGlobalSpinner();"), selector="head", where="beforeEnd")
        if succ: state.show_success_modal.set(True)
        else:
            state.error_modal_message.set(msg)
            state.show_error_modal.set(True)

    @render.download(filename="Miss_Location_Report_Cycle_Count.xlsx")
    def btn_dl_cca_miss_loc():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            state._raw_df_cca_miss_loc.to_excel(writer, sheet_name='MISS_LOC_RAK_KE_RAK', index=False)
            state._raw_df_cca_karantina.to_excel(writer, sheet_name='MISS_LOC_KE_KARANTINA', index=False)
            state._raw_df_cca_sum_miss.to_excel(writer, sheet_name='SUMMARY_MISS_LOCATION', index=False)
        buf.seek(0)
        yield buf.getvalue()

# ==========================================================================
    # COMPARE RTO CONTROLLER & HANDLERS
    # ==========================================================================
    @render.ui
    def rto_step1_results_ui():
        if not state.rto_step1_done(): return ui.div()
        return ui.div(
            ui.hr(style="margin: 1rem 0; border-color: #E2E8F0;"),
            ui.h4("📋 RINGKASAN HASIL DATA SCAN VS APPSHEET", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 1rem;"),
            ui.div(
                dark_metric_box("Total Qty Scan", f"{state.rto_q_total():,}", "#C5A059"),
                dark_metric_box("Qty Sesuai", f"{state.rto_q_sesuai():,}", "#10B981"),
                dark_metric_box("Qty Kelebihan", f"{state.rto_q_lebih():,}", "#E53E3E"),
                dark_metric_box("Qty Kurang", f"{state.rto_q_kurang():,}", "#DD6B20"),
                style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; width: 100%; margin-bottom: 1.25rem;"
            ),
            ui.navset_card_tab(
                ui.nav_panel(
                    "📝 Summary Compare",
                    ui.div(
                        ui.div(
                            ui.download_button(
                                "btn_dl_rto_all",
                                ui.tags.span(ui.tags.i(class_="fa-solid fa-download", style="margin-right: 6px; font-size: 14px;"), "Download All Data (.xlsx)"),
                                style="background-color: #10B981; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 8px 16px; cursor: pointer;"
                            ),
                            style="display: flex; justify-content: flex-end; width: 100%; margin-bottom: 0.75rem;"
                        ),
                        render_clean_table(state.df_rto_ds_headers(), state.df_rto_ds_rows(), "tbl_rto_ds"),
                        style="padding: 0.75rem 0;"
                    )
                ),
                ui.nav_panel(
                    "⚠️ Item Selisih",
                    ui.div(
                        ui.div(
                            ui.download_button(
                                "btn_dl_rto_selisih",
                                ui.tags.span(ui.tags.i(class_="fa-solid fa-download", style="margin-right: 6px; font-size: 14px;"), "Download Item Selisih (.xlsx)"),
                                style="background-color: #E50914; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 8px 16px; cursor: pointer;"
                            ),
                            style="display: flex; justify-content: flex-end; width: 100%; margin-bottom: 0.75rem;"
                        ),
                        render_clean_table(state.df_rto_selisih_headers(), state.df_rto_selisih_rows(), "tbl_rto_selisih"),
                        style="padding: 0.75rem 0;"
                    )
                )
            ),
            style="width: 100%;"
        )

    @reactive.Effect
    @reactive.event(input.btn_run_rto_step1)
    def _proc_rto_step1():
        f1, f2 = input.uploader_rto_ds(), input.uploader_rto_app()
        if not f1 or not f2:
            state.error_modal_message.set("Pilih kedua file DS RTO & AppSheet RTO terlebih dahulu!")
            state.show_error_modal.set(True)
            return
        succ, msg = state.run_rto_step1(f1, f2)
        if succ: state.show_success_modal.set(True)
        else:
            state.error_modal_message.set(msg)
            state.show_error_modal.set(True)

    @render.download(filename="ALL_DATA_RTO.xlsx")
    def btn_dl_rto_all():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            state._raw_df_rto_ds.to_excel(writer, sheet_name='ALL_DATA_RTO', index=False)
        buf.seek(0)
        yield buf.getvalue()

    @render.download(filename="DETAIL_SELISIH_RTO.xlsx")
    def btn_dl_rto_selisih():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            state._raw_df_rto_selisih.to_excel(writer, sheet_name='SELISIH_RTO', index=False)
        buf.seek(0)
        yield buf.getvalue()

    # --- STEP 2: REFRESH DATA (SETELAH CEK REAL) ---
    @render.ui
    def rto_step2_card_ui():
        if not state.rto_step1_done(): return ui.div()
        return ui.div(
            ui.h4("🔄 2. Refresh Data (Setelah Cek Real)", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 0.75rem;"),
            custom_uploader_box("uploader_rto_cek", "Upload Hasil Cek Real"),
            ui.div(
                ui.tags.button(
                    ui.tags.span(ui.tags.i(class_="fa-solid fa-arrows-rotate", style="margin-right: 6px; font-size: 14px;"), "REFRESH DATA"),
                    onclick="document.body.classList.add('process-running'); Shiny.setInputValue('btn_run_rto_step2_refresh', Math.random(), {priority: 'event'});",
                    class_="btn-red-gradient"
                ),
                style="display: flex; justify-content: flex-end; width: 100%; margin-top: 0.5rem;"
            ),
            style="background: white; padding: 1.25rem; border-radius: 10px; border: 1px solid #E2E8F0; margin-bottom: 1.25rem;"
        )

    @reactive.Effect
    @reactive.event(input.btn_run_rto_step2_refresh)
    def _proc_rto_step2_refresh():
        f = input.uploader_rto_cek()
        if not f:
            state.error_modal_message.set("Pilih file Hasil Cek Real terlebih dahulu!")
            state.show_error_modal.set(True)
            return
        succ, msg = state.run_rto_step2_refresh(f)
        if succ: state.show_success_modal.set(True)
        else:
            state.error_modal_message.set(msg)
            state.show_error_modal.set(True)

    # --- STEP 3: COMPARE APPSHEET VS DRAFT JEZPRO ---
    @render.ui
    def rto_step3_card_ui():
        if not state.rto_step1_done(): return ui.div()
        step3_results = ui.div()
        if state.rto_draft_done():
            step3_results = ui.div(
                ui.hr(style="margin: 1rem 0; border-color: #E2E8F0;"),
                ui.h4("📋 RINGKASAN HASIL APPSHEET VS DRAFT", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 1rem;"),
                ui.div(
                    dark_metric_box("Total Qty Ambil", f"{state.rto_q_draft_total():,}", "#C5A059"),
                    dark_metric_box("Qty OK", f"{state.rto_q_ok():,}", "#10B981"),
                    dark_metric_box("Qty Perlu Edit", f"{state.rto_q_edit():,}", "#DD6B20"),
                    dark_metric_box("Qty Delete", f"{state.rto_q_del():,}", "#E53E3E"),
                    style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; width: 100%; margin-bottom: 1rem;"
                ),
                ui.div(
                    ui.download_button(
                        "btn_dl_rto_draft_comp",
                        ui.tags.span(ui.tags.i(class_="fa-solid fa-download", style="margin-right: 6px; font-size: 14px;"), "Download Draft Compared (.xlsx)"),
                        style="background-color: #10B981; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 8px 16px; cursor: pointer;"
                    ),
                    style="display: flex; justify-content: flex-end; width: 100%; margin-bottom: 0.75rem;"
                ),
                render_clean_table(state.df_rto_draft_comp_headers(), state.df_rto_draft_comp_rows(), "tbl_rto_draft_comp")
            )

        return ui.div(
            ui.h4("3️⃣ Upload Draft Jezpro & Compare", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 0.75rem;"),
            custom_uploader_box("uploader_rto_draft", "Upload Draft Jezpro"),
            ui.div(
                ui.tags.button(
                    ui.tags.span(ui.tags.i(class_="fa-solid fa-magnifying-glass", style="margin-right: 6px; font-size: 14px;"), "COMPARE DRAFT JEZPRO"),
                    onclick="document.body.classList.add('process-running'); Shiny.setInputValue('btn_run_rto_step3_draft', Math.random(), {priority: 'event'});",
                    class_="btn-red-gradient"
                ),
                style="display: flex; justify-content: flex-end; width: 100%; margin-top: 0.5rem;"
            ),
            step3_results,
            style="background: white; padding: 1.25rem; border-radius: 10px; border: 1px solid #E2E8F0; margin-bottom: 1.25rem;"
        )

    @reactive.Effect
    @reactive.event(input.btn_run_rto_step3_draft)
    def _proc_rto_step3_draft():
        f = input.uploader_rto_draft()
        if not f:
            state.error_modal_message.set("Pilih file Draft Jezpro terlebih dahulu!")
            state.show_error_modal.set(True)
            return
        succ, msg = state.run_rto_step3_draft(f)
        if succ: state.show_success_modal.set(True)
        else:
            state.error_modal_message.set(msg)
            state.show_error_modal.set(True)

    @render.download(filename="DRAFT_COMPARED.xlsx")
    def btn_dl_rto_draft_comp():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            state._raw_df_rto_draft_comp.to_excel(writer, sheet_name='DRAFT_COMPARED', index=False)
        buf.seek(0)
        yield buf.getvalue()

    # --- STEP 4: GENERATE NEW DRAFT RTO ---
    @render.ui
    def rto_step4_card_ui():
        if not state.rto_draft_done(): return ui.div()
        step4_results = ui.div()
        if state.rto_new_draft_done():
            step4_results = ui.div(
                ui.hr(style="margin: 1rem 0; border-color: #E2E8F0;"),
                ui.div(
                    dark_metric_box("📦 Total QTY New Draft", f"{state.rto_q_new_draft_total():,} PCS", "#10B981"),
                    style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1rem; width: 100%; margin-bottom: 1rem;"
                ),
                ui.div(
                    ui.download_button(
                        "btn_dl_rto_new_draft",
                        ui.tags.span(ui.tags.i(class_="fa-solid fa-download", style="margin-right: 6px; font-size: 14px;"), "Download New Draft (.xlsx)"),
                        style="background-color: #10B981; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 8px 16px; cursor: pointer;"
                    ),
                    style="display: flex; justify-content: flex-end; width: 100%; margin-bottom: 0.75rem;"
                ),
                render_clean_table(state.df_rto_new_draft_headers(), state.df_rto_new_draft_rows(), "tbl_rto_new_draft")
            )

        return ui.div(
            ui.h4("4️⃣ Generate New Draft Jezpro", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 0.75rem;"),
            ui.div(
                ui.tags.button(
                    ui.tags.span(ui.tags.i(class_="fa-solid fa-file-circle-plus", style="margin-right: 6px; font-size: 14px;"), "GENERATE NEW DRAFT"),
                    onclick="document.body.classList.add('process-running'); Shiny.setInputValue('btn_run_rto_step4_new_draft', Math.random(), {priority: 'event'});",
                    class_="btn-red-gradient"
                ),
                style="display: flex; justify-content: flex-end; width: 100%; margin-top: 0.5rem;"
            ),
            step4_results,
            style="background: white; padding: 1.25rem; border-radius: 10px; border: 1px solid #E2E8F0; margin-bottom: 1.25rem;"
        )

    @reactive.Effect
    @reactive.event(input.btn_run_rto_step4_new_draft)
    def _proc_rto_step4_new_draft():
        succ, msg = state.run_rto_step4_new_draft()
        if succ: state.show_success_modal.set(True)
        else:
            state.error_modal_message.set(msg)
            state.show_error_modal.set(True)

    @render.download(filename="NEW_DRAFT_RTO.xlsx")
    def btn_dl_rto_new_draft():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            state._raw_df_rto_new_draft.to_excel(writer, sheet_name='NEW_DRAFT', index=False)
        buf.seek(0)
        yield buf.getvalue()

# ==========================================================================
    # STOCK OPNAME ANALYZER CONTROLLER & HANDLERS
    # ==========================================================================
    @render.ui
    def so_bin_sys_ui():
        b = input.so_branch() if "so_branch" in input else "SURABAYA"
        choices = BRANCH_BIN_MAPPING.get(b, [])
        return ui.input_selectize("so_bin_sys", "🏭 BIN System:", choices=choices, multiple=True, width="100%")

# --- KUNCI OTOMATIS TOMBOL STEP 1 (STOCK OPNAME) ---
    @render.ui
    def so_step1_btn_ui():
        f1 = input.so_up_scan() if "so_up_scan" in input else None
        f2 = input.so_up_stock() if "so_up_stock" in input else None
        
        # Jika kedua file sudah di-upload -> Tombol Merah Aktif
        if (f1 and len(f1) > 0) and (f2 and len(f2) > 0):
            return ui.div(
                ui.tags.button(
                    ui.tags.span(ui.tags.i(class_="fa-solid fa-play", style="margin-right: 6px; font-size: 14px;"), "RUN COMPARE"),
                    onclick="window.showGlobalSpinner(); Shiny.setInputValue('btn_run_so_step1', Math.random(), {priority: 'event'});",
                    class_="btn-red-gradient"
                ),
                style="display: flex; justify-content: flex-end; width: 100%; margin-top: 0.5rem;"
            )
        
        # Jika belum ada file / belum lengkap -> Tombol Terkunci (Gembok Abu-abu)
        return ui.div(
            ui.tags.button(
                ui.tags.i(class_="fa-solid fa-lock", style="margin-right: 6px; font-size: 14px;"),
                "UPLOAD DATA SCAN & STOCK SYSTEM UNTUK MEMULAI",
                disabled=True,
                class_="btn-locked"
            ),
            style="display: flex; justify-content: flex-end; width: 100%; margin-top: 0.5rem;"
        )
    # --- STEP 1 ---
    @render.ui
    def so_step1_results_ui():
        if not state.so_step1_done(): return ui.div()
        return ui.div(
            ui.hr(style="margin: 1rem 0; border-color: #E2E8F0;"),
            ui.div(
                dark_metric_box("📦 QTY REAL +", f"{state.so_qty_real_plus():,}", "#C5A059"),
                dark_metric_box("🔐 QTY SYSTEM +", f"{state.so_qty_sys_plus():,}", "#E53E3E"),
                style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; width: 100%; margin-bottom: 1rem;"
            ),
            ui.div(
                ui.download_button(
                    "btn_dl_so_step1",
                    ui.tags.span(ui.tags.i(class_="fa-solid fa-download", style="margin-right: 6px; font-size: 14px;"), "DOWNLOAD EXCEL STEP 1 (.xlsx)"),
                    style="background-color: #10B981; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 8px 16px; cursor: pointer;"
                ),
                style="display: flex; justify-content: flex-end; width: 100%; margin-bottom: 0.75rem;"
            ),
            ui.navset_card_tab(
                ui.nav_panel("📋 DATA SCAN", ui.div(render_clean_table(state.df_so_scan_headers(), state.df_so_scan_rows(), "tbl_so_scan"), style="padding: 0.75rem 0;")),
                ui.nav_panel("📊 STOCK SYSTEM", ui.div(render_clean_table(state.df_so_stock_headers(), state.df_so_stock_rows(), "tbl_so_stock"), style="padding: 0.75rem 0;")),
                ui.nav_panel("➕ REAL +", ui.div(render_clean_table(state.df_so_real_headers(), state.df_so_real_rows(), "tbl_so_real"), style="padding: 0.75rem 0;")),
                ui.nav_panel("➖ SYSTEM +", ui.div(render_clean_table(state.df_so_sys_headers(), state.df_so_sys_rows(), "tbl_so_sys"), style="padding: 0.75rem 0;"))
            ), style="width: 100%;"
        )

    @reactive.Effect
    @reactive.event(input.btn_run_so_step1)
    def _proc_so_step1():
        f_scan, f_stock = input.so_up_scan(), input.so_up_stock()
        if not f_scan or not f_stock:
            state.error_modal_message.set("Pilih kedua file Data Scan & Stock System terlebih dahulu!")
            state.show_error_modal.set(True)
            return

        sub = input.so_sub_kat() if "so_sub_kat" in input else []
        bin_sys = input.so_bin_sys() if "so_bin_sys" in input else []
        succ, msg = state.run_so_step1(f_scan, f_stock, sub, bin_sys)
        if succ: state.show_success_modal.set(True)
        else:
            state.error_modal_message.set(msg)
            state.show_error_modal.set(True)

    @render.download(filename="Step1_SO_Compare.xlsx")
    def btn_dl_so_step1():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            state._raw_df_so_scan.to_excel(writer, sheet_name='DATA_SCAN', index=False)
            state._raw_df_so_stock.to_excel(writer, sheet_name='STOCK_SYSTEM', index=False)
            state._raw_df_so_real_plus.to_excel(writer, sheet_name='REAL_PLUS', index=False)
            state._raw_df_so_sys_plus.to_excel(writer, sheet_name='SYSTEM_PLUS', index=False)
        buf.seek(0)
        yield buf.getvalue()

    # --- KARTU MANDIRI STEP 2 & 3 (STOCK OPNAME) ---
    @render.ui
    def so_step2_card_ui():
        if not state.so_step1_done(): return ui.div()
        step2_results = ui.div()
        if state.so_step2_done():
            step2_results = ui.div(
                ui.hr(style="margin: 1rem 0; border-color: #E2E8F0;"),
                ui.div(
                    ui.h4("✅ HASIL ALOKASI", style="font-size: 15px; font-weight: 800; color: #1A202C; margin: 0;"),
                    ui.download_button("btn_dl_so_step2", ui.tags.span(ui.tags.i(class_="fa-solid fa-download", style="margin-right: 6px; font-size: 14px;"), "DOWNLOAD HASIL ALOKASI (.xlsx)"), style="background-color: #10B981; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 8px 16px; cursor: pointer;"),
                    style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 0.75rem;"
                ),
                ui.navset_card_tab(
                    ui.nav_panel("📊 ALLOCATION DETAIL", ui.div(render_clean_table(state.df_so_alloc_headers(), state.df_so_alloc_rows(), "tbl_so_alloc"), style="padding: 0.75rem 0;")),
                    ui.nav_panel("📉 UPDATED SYSTEM", ui.div(render_clean_table(state.df_so_sys_upd_headers(), state.df_so_sys_upd_rows(), "tbl_so_sys_upd"), style="padding: 0.75rem 0;")),
                    ui.nav_panel("📦 SET UP REAL +", ui.div(render_clean_table(state.df_so_setup_real_headers(), state.df_so_setup_real_rows(), "tbl_so_setup_real"), style="padding: 0.75rem 0;"))
                ),
                ui.hr(style="margin: 1.5rem 0; border-color: #E2E8F0;"),
                
                # --- BAGIAN RECON STEP 3 DENGAN TOMBOL DOWNLOAD LENGKAP & STABIL ---
                ui.div(
                    ui.h4("📋 RECON REPORTS (HASIL STEP 1 - 3)", style="font-size: 15px; font-weight: 800; color: #1A202C; margin: 0;"),
                    ui.download_button(
                        "btn_dl_so_rec_all", 
                        ui.tags.span(ui.tags.i(class_="fa-solid fa-file-excel", style="margin-right: 6px; font-size: 13px;"), "DOWNLOAD RECON STEP 3 FULL (.xlsx)"), 
                        style="background: linear-gradient(135deg, #10B981 0%, #059669 100%); color: white; font-weight: bold; border-radius: 6px; border: none; padding: 8px 16px; cursor: pointer; font-size: 13px; box-shadow: 0 2px 6px rgba(16,185,129,0.25);"
                    ),
                    style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 1rem; flex-wrap: wrap; gap: 8px;"
                ),
                ui.div(
                    # Box 1: Real + Recon
                    ui.div(
                        ui.div(
                            ui.h5("📋 REAL + RECON", style="font-size: 14px; font-weight: 800; color: #1A202C; margin: 0;"),
                            ui.download_button("btn_dl_so_rec_real", ui.tags.span(ui.tags.i(class_="fa-solid fa-download", style="margin-right: 6px; font-size: 12px;"), "Download (.xlsx)"), style="background-color: #10B981; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 5px 12px; cursor: pointer; font-size: 12px;"),
                            style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 0.6rem;"
                        ),
                        render_clean_table(state.df_so_rec_real_headers(), state.df_so_rec_real_rows(), "tbl_so_rec_real"),
                        style="flex: 1; min-width: 320px; background: #F8FAFC; padding: 1rem; border-radius: 8px; border: 1px solid #CBD5E0;"
                    ),
                    # Box 2: System + Recon
                    ui.div(
                        ui.div(
                            ui.h5("🔐 SYSTEM + RECON (OUTSTANDING)", style="font-size: 14px; font-weight: 800; color: #1A202C; margin: 0;"),
                            ui.download_button("btn_dl_so_rec_sys", ui.tags.span(ui.tags.i(class_="fa-solid fa-download", style="margin-right: 6px; font-size: 12px;"), "Download (.xlsx)"), style="background-color: #10B981; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 5px 12px; cursor: pointer; font-size: 12px;"),
                            style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 0.6rem;"
                        ),
                        render_clean_table(state.df_so_rec_sys_headers(), state.df_so_rec_sys_rows(), "tbl_so_rec_sys"),
                        style="flex: 1; min-width: 320px; background: #F8FAFC; padding: 1rem; border-radius: 8px; border: 1px solid #CBD5E0;"
                    ),
                    style="display: flex; gap: 1rem; flex-wrap: wrap; width: 100%;"
                )
            )

        return ui.div(
            ui.h4("2️⃣ Upload BIN COVERAGE (ALL BIN DEFAULT & KARANTINA)", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 0.75rem;"),
            custom_uploader_box("so_up_cov", "📥 FILE BIN COVERAGE"),
            ui.div(
                ui.tags.button(
                    ui.tags.span(ui.tags.i(class_="fa-solid fa-play", style="margin-right: 6px; font-size: 14px;"), "RUN ALLOCATION"),
                    onclick="window.showGlobalSpinner(); Shiny.setInputValue('btn_run_so_step2', Math.random(), {priority: 'event'});",
                    class_="btn-red-gradient"
                ),
                style="display: flex; justify-content: flex-end; width: 100%; margin-top: 0.5rem;"
            ),
            step2_results,
            style="background: white; padding: 1.25rem; border-radius: 10px; border: 1px solid #E2E8F0; margin-bottom: 1.25rem;"
        )

    @reactive.Effect
    @reactive.event(input.btn_run_so_step2)
    def _proc_so_step2():
        f = input.so_up_cov()
        if not f:
            state.error_modal_message.set("Pilih file BIN Coverage terlebih dahulu!")
            state.show_error_modal.set(True)
            return
        bin_cov = input.so_bin_cov() if "so_bin_cov" in input else []
        succ, msg = state.run_so_step2(f, bin_cov)
        if succ: state.show_success_modal.set(True)
        else:
            state.error_modal_message.set(msg)
            state.show_error_modal.set(True)

    @render.download(filename="Hasil_Alokasi_SO.xlsx")
    def btn_dl_so_step2():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            state._raw_df_so_alloc.to_excel(writer, sheet_name='ALLOCATION_DETAIL', index=False)
            state._raw_df_so_sys_upd.to_excel(writer, sheet_name='UPDATED_SYSTEM', index=False)
            state._raw_df_so_setup_real.to_excel(writer, sheet_name='SET_UP_REAL_PLUS', index=False)
        buf.seek(0)
        yield buf.getvalue()

    @render.download(filename="Report_Real_Plus_Recon.xlsx")
    def btn_dl_so_rec_real():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            df = state._raw_df_so_rec_real if not state._raw_df_so_rec_real.empty else pd.DataFrame(columns=['BIN', 'SKU', 'ITEM NAME', 'QTY_SCAN', 'QTY_SYSTEM', 'DIFF', 'HASIL RECONCILIATION'])
            df.to_excel(writer, sheet_name='REAL_PLUS_RECON', index=False)
        buf.seek(0)
        yield buf.getvalue()

    @render.download(filename="Report_System_Plus_Recon.xlsx")
    def btn_dl_so_rec_sys():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            df = state._raw_df_so_rec_sys if not state._raw_df_so_rec_sys.empty else pd.DataFrame(columns=['BIN', 'SKU', 'DIFF', 'HASIL REKONSILIASI'])
            df.to_excel(writer, sheet_name='SYSTEM_PLUS_RECON', index=False)
        buf.seek(0)
        yield buf.getvalue()

    # Tombol Download 2 Sheet Sekaligus untuk Stock Opname
    @render.download(filename="Report_SO_Recon_Step3_Full.xlsx")
    def btn_dl_so_rec_all():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            df_r = state._raw_df_so_rec_real if not state._raw_df_so_rec_real.empty else pd.DataFrame(columns=['BIN', 'SKU', 'ITEM NAME', 'QTY_SCAN', 'QTY_SYSTEM', 'DIFF', 'HASIL RECONCILIATION'])
            df_s = state._raw_df_so_rec_sys if not state._raw_df_so_rec_sys.empty else pd.DataFrame(columns=['BIN', 'SKU', 'DIFF', 'HASIL REKONSILIASI'])
            df_r.to_excel(writer, sheet_name='REAL_PLUS_RECON', index=False)
            df_s.to_excel(writer, sheet_name='SYSTEM_OUTSTANDING', index=False)
        buf.seek(0)
        yield buf.getvalue()

    # ==========================================================================
    # STOCK OPNAME ANALYZER - STEP 4 EVENT HANDLER
    # ==========================================================================
    @reactive.Effect
    @reactive.event(input.btn_run_so_step4)
    def _proc_so_step4():
        f_r = input.so_up_r4() if "so_up_r4" in input else None
        f_s = input.so_up_s4() if "so_up_s4" in input else None
        f_m = input.so_up_m5() if "so_up_m5" in input else None

        succ, msg = state.run_so_step4(f_r, f_s, f_m)
        ui.insert_ui(ui.tags.script("if (window.hideGlobalSpinner) window.hideGlobalSpinner();"), selector="head", where="beforeEnd")
        if succ:
            state.show_success_modal.set(True)
        else:
            state.error_modal_message.set(msg)
            state.show_error_modal.set(True)
    # ==========================================================================
    # HANDLER DOWNLOAD EXCEL UNTUK STOCK OPNAME STEP 4 (FINAL ADJUSTMENT +)
    # ==========================================================================
    @render.download(filename="Multiple_Adj_Plus_SO.xlsx")
    def btn_dl_so_mult():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            df = getattr(state, "_raw_df_so_mult", pd.DataFrame())
            df.to_excel(writer, sheet_name='MULTIPLE_ADJ_PLUS', index=False)
        buf.seek(0)
        yield buf.getvalue()

    @render.download(filename="Single_Adj_Plus_SO.xlsx")
    def btn_dl_so_sing():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            df = getattr(state, "_raw_df_so_sing", pd.DataFrame())
            df.to_excel(writer, sheet_name='SINGLE_ADJ_PLUS', index=False)
        buf.seek(0)
        yield buf.getvalue()

    @render.download(filename="Hasil_Cek_Adj_Plus_SO.xlsx")
    def btn_dl_so_res4():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            df = getattr(state, "_raw_df_so_res4", pd.DataFrame())
            df.to_excel(writer, sheet_name='HASIL_CEK_ADJ_PLUS', index=False)
        buf.seek(0)
        yield buf.getvalue()

    @render.download(filename="Set_Up_Real_Plus_SO.xlsx")
    def btn_dl_so_setup4():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            df = getattr(state, "_raw_df_so_setup4", pd.DataFrame())
            df.to_excel(writer, sheet_name='SET_UP_REAL_PLUS', index=False)
        buf.seek(0)
        yield buf.getvalue()

    @render.download(filename="Miss_Lookup_SKU_SO.xlsx")
    def btn_dl_so_miss4():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            df = getattr(state, "_raw_df_so_miss4", pd.DataFrame())
            df.to_excel(writer, sheet_name='MISS_LOOKUP_SKU', index=False)
        buf.seek(0)
        yield buf.getvalue()

    # 🌟 Sekalian lengkapi untuk Step 5 (Karantina) yang tombolnya juga belum ada handlernya:
    @render.download(filename="Hasil_Karantina_SO.xlsx")
    def btn_dl_so_karantina():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            df = getattr(state, "_raw_df_so_karantina", pd.DataFrame())
            df.to_excel(writer, sheet_name='KARANTINA_SO', index=False)
        buf.seek(0)
        yield buf.getvalue()
    # ==========================================================================
    # STOCK OPNAME CONTROLLER (STEP 4, 5, & 6)
    # ==========================================================================
    # --- STEP 4 STOCK OPNAME ---
    @render.ui
    def so_step4_card_ui():
        if not state.so_step2_done(): return ui.div()

        # JIKA DATA KOSONG: Tampilkan kartu hijau ringkas
        if state._raw_df_so_rec_real.empty:
            return ui.div(
                ui.h4("3️⃣ Final Adjustment + Process", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 0.5rem;"),
                ui.div(
                    ui.tags.i(class_="fa-solid fa-circle-check", style="color: #22543D; font-size: 18px; margin-right: 8px;"),
                    ui.span("Semua item Real + telah ter-cover penuh oleh System + dan BIN Coverage (0 Selisih). Langkah penyesuaian plus selesai otomatis.", style="font-weight: 600; font-size: 13px;"),
                    style="background: #C6F6D5; color: #22543D; padding: 0.85rem 1.25rem; border-radius: 8px; border: 1px solid #9AE6B4; display: flex; align-items: center;"
                ),
                style="background: white; padding: 1.25rem; border-radius: 10px; border: 1px solid #E2E8F0; margin-bottom: 1.25rem;"
            )

        # JIKA ADA DATA: Tampilkan 3 uploader dan hasil tab normal
        # JIKA ADA DATA: Tampilkan 3 uploader dan hasil tab normal
        step4_results = ui.div()
        btn_green_style = "background-color: #10B981; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 6px 14px; cursor: pointer; font-size: 12px;"
        btn_red_style = "background-color: #E53E3E; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 6px 14px; cursor: pointer; font-size: 12px;"

        if state.so_step4_done():
            step4_results = ui.div(
                ui.hr(style="margin: 1rem 0; border-color: #E2E8F0;"),
                ui.navset_card_tab(
                    ui.nav_panel("📦 MULTIPLE ADJ +", ui.div(ui.div(ui.download_button("btn_dl_so_mult", ui.tags.span(ui.tags.i(class_="fa-solid fa-download", style="margin-right: 6px;"), "Download Multiple Adj + (.xlsx)"), style=btn_green_style), style="display: flex; justify-content: flex-end; margin-bottom: 0.5rem;"), render_clean_table(state.df_so_mult_headers(), state.df_so_mult_rows(), "tbl_so_mult"))),
                    ui.nav_panel("⚠️ SINGLE ADJ +", ui.div(ui.div(ui.download_button("btn_dl_so_sing", ui.tags.span(ui.tags.i(class_="fa-solid fa-download", style="margin-right: 6px;"), "Download Single Adj + (.xlsx)"), style=btn_green_style), style="display: flex; justify-content: flex-end; margin-bottom: 0.5rem;"), render_clean_table(state.df_so_sing_headers(), state.df_so_sing_rows(), "tbl_so_sing"))),
                    ui.nav_panel("🔍 CEK ADJ + RESULT", ui.div(ui.div(ui.download_button("btn_dl_so_res4", ui.tags.span(ui.tags.i(class_="fa-solid fa-download", style="margin-right: 6px;"), "Download Hasil Cek Adj + (.xlsx)"), style=btn_green_style), style="display: flex; justify-content: flex-end; margin-bottom: 0.5rem;"), render_clean_table(state.df_so_res4_headers(), state.df_so_res4_rows(), "tbl_so_res4"))),
                    ui.nav_panel("➡️ SET UP REAL +", ui.div(ui.div(ui.download_button("btn_dl_so_setup4", ui.tags.span(ui.tags.i(class_="fa-solid fa-download", style="margin-right: 6px;"), "Download Set Up Real + (.xlsx)"), style=btn_green_style), style="display: flex; justify-content: flex-end; margin-bottom: 0.5rem;"), render_clean_table(state.df_so_setup4_headers(), state.df_so_setup4_rows(), "tbl_so_setup4"))),
                    ui.nav_panel("❌ Miss Lookup SKU on BIN", ui.div(ui.div(ui.download_button("btn_dl_so_miss4", ui.tags.span(ui.tags.i(class_="fa-solid fa-download", style="margin-right: 6px;"), "Download Missing Items (.xlsx)"), style=btn_red_style), style="display: flex; justify-content: flex-end; margin-bottom: 0.5rem;"), render_clean_table(state.df_so_miss4_headers(), state.df_so_miss4_rows(), "tbl_so_miss4")))
                )
            )
        return ui.div(
            ui.h4("3️⃣ Final Adjustment + Process (3 File Upload)", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 0.75rem;"),
            ui.div(
                custom_uploader_box("so_up_r4", "1. Sheet REAL + RECON"),
                custom_uploader_box("so_up_s4", "2. Sheet CEK STOCK ADJ +"),
                custom_uploader_box("so_up_m5", "3. File STAGGING INBOUND"),
                style="display: flex; gap: 1rem; width: 100%; margin-bottom: 0.5rem; flex-wrap: wrap;"
            ),
            ui.div(
                ui.tags.button(
                    ui.tags.span(ui.tags.i(class_="fa-solid fa-play", style="margin-right: 6px; font-size: 14px;"), "RUN FINAL ADJUSTMENT"),
                    onclick="document.body.classList.add('process-running'); Shiny.setInputValue('btn_run_so_step4', Math.random(), {priority: 'event'});",
                    class_="btn-red-gradient"
                ),
                style="display: flex; justify-content: flex-end; width: 100%; margin-top: 0.5rem;"
            ),
            step4_results,
            style="background: white; padding: 1.25rem; border-radius: 10px; border: 1px solid #E2E8F0; margin-bottom: 1.25rem;"
        )

    # --- STEP 5 STOCK OPNAME ---
    @render.ui
    def so_step5_card_ui():
        if not state.so_step2_done() or not state.so_step4_done():
            return ui.div()

        # JIKA DATA KOSONG: Tampilkan kartu hijau ringkas
        if state._raw_df_so_rec_sys.empty:
            return ui.div(
                ui.h4("4️⃣ Recon System + Process (Set Up Karantina)", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 0.5rem;"),
                ui.div(
                    ui.tags.i(class_="fa-solid fa-circle-check", style="color: #22543D; font-size: 18px; margin-right: 8px;"),
                    ui.span("Tidak ada item System + Outstanding (0 Selisih). Tidak ada stok yang perlu dimutasi ke Karantina. Langkah karantina selesai otomatis.", style="font-weight: 600; font-size: 13px;"),
                    style="background: #C6F6D5; color: #22543D; padding: 0.85rem 1.25rem; border-radius: 8px; border: 1px solid #9AE6B4; display: flex; align-items: center;"
                ),
                style="background: white; padding: 1.25rem; border-radius: 10px; border: 1px solid #E2E8F0; margin-bottom: 1.25rem;"
            )

        # JIKA ADA DATA: Tampilkan 2 uploader karantina normal
        step5_results = ui.div()
        if state.so_step5_done():
            step5_results = ui.div(
                ui.hr(style="margin: 1rem 0; border-color: #E2E8F0;"),
                ui.div(
                    dark_metric_box("☣️ QTY TO KARANTINA", f"{state.so_qty_karantina():,} QTY", "#ECC94B"),
                    dark_metric_box("🏷️ SKU TO KARANTINA", f"{state.so_sku_karantina():,} SKU", "#ECC94B"),
                    style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; width: 100%; margin-bottom: 1rem;"
                ),
                ui.div(
                    ui.download_button("btn_dl_so_karantina", ui.tags.span(ui.tags.i(class_="fa-solid fa-download", style="margin-right: 6px; font-size: 14px;"), "DOWNLOAD HASIL KARANTINA (.xlsx)"), style="background-color: #10B981; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 8px 16px; cursor: pointer;"),
                    style="display: flex; justify-content: flex-end; width: 100%; margin-bottom: 0.75rem;"
                ),
                ui.navset_card_tab(
                    ui.nav_panel("📦 HASIL KARANTINA", ui.div(render_clean_table(state.df_so_karantina_headers(), state.df_so_karantina_rows(), "tbl_so_karantina"), style="padding: 0.75rem 0;")),
                    ui.nav_panel("🔍 DATA PENGECEKAN (AUDIT)", ui.div(render_clean_table(state.df_so_check5_headers(), state.df_so_check5_rows(), "tbl_so_check5"), style="padding: 0.75rem 0;"))
                )
            )

        return ui.div(
            ui.h4("4️⃣ Recon System + Process (Set Up Karantina)", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 0.75rem;"),
            ui.div(
                custom_uploader_box("so_up_k6", "1. Upload SYSTEM + RECON"),
                custom_uploader_box("so_up_adj6", "2. Upload STOCK CEK ADJUSMENT (-)"),
                style="display: flex; gap: 1rem; width: 100%; margin-bottom: 0.5rem; flex-wrap: wrap;"
            ),
            ui.div(
                ui.tags.button(
                    ui.tags.span(ui.tags.i(class_="fa-solid fa-play", style="margin-right: 6px; font-size: 14px;"), "GENERATE KARANTINA"),
                    onclick="document.body.classList.add('process-running'); Shiny.setInputValue('btn_run_so_step5', Math.random(), {priority: 'event'});",
                    class_="btn-red-gradient"
                ),
                style="display: flex; justify-content: flex-end; width: 100%; margin-top: 0.5rem;"
            ),
            step5_results,
            style="background: white; padding: 1.25rem; border-radius: 10px; border: 1px solid #E2E8F0; margin-bottom: 1.25rem;"
        )

    @reactive.Effect
    @reactive.event(input.btn_run_so_step5)
    def _proc_so_step5():
        f1 = input.so_up_k6() if "so_up_k6" in input else None
        f2 = input.so_up_adj6() if "so_up_adj6" in input else None

        if state._raw_df_so_rec_sys.empty:
            succ, msg = state.run_so_step5(None, None)
        else:
            if not f1 or not f2:
                state.error_modal_message.set("Upload kedua file (System+ Recon & Stock Cek Adj -) terlebih dahulu!")
                state.show_error_modal.set(True)
                return
            succ, msg = state.run_so_step5(f1, f2)

        if succ:
            state.show_success_modal.set(True)
        else:
            state.error_modal_message.set(msg)
            state.show_error_modal.set(True)

    # --- STEP 6 STOCK OPNAME ---
    @render.ui
    def so_step6_card_ui():
        # Step 6 baru muncul jika Step 5 selesai
        if not state.so_step2_done() or not state.so_step5_done():
            return ui.div()

        # Miss Location Results
        miss_loc_results = ui.div()
        if state.so_step6a_done():
            miss_loc_results = ui.div(
                ui.hr(style="margin: 1rem 0; border-color: #E2E8F0;"),
                ui.div(
                    dark_metric_box("📦 TOTAL SKU MISS LOC.", f"{state.so_sku_miss_loc():,} ITEM", "#E53E3E"),
                    dark_metric_box("🔢 TOTAL QTY MISS LOC.", f"{state.so_qty_miss_loc():,} ITEM", "#E53E3E"),
                    style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; width: 100%; margin-bottom: 1rem;"
                ),
                ui.div(
                    ui.download_button("btn_dl_so_miss_loc", ui.tags.span(ui.tags.i(class_="fa-solid fa-download", style="margin-right: 6px; font-size: 14px;"), "DOWNLOAD MISS LOC REPORT (.xlsx)"), style="background-color: #10B981; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 8px 16px; cursor: pointer;"),
                    style="display: flex; justify-content: flex-end; width: 100%; margin-bottom: 0.75rem;"
                ),
                ui.navset_card_tab(
                    ui.nav_panel("📄 Detail List", ui.div(render_clean_table(state.df_so_miss_loc_headers(), state.df_so_miss_loc_rows(), "tbl_so_miss_loc"), style="padding: 0.75rem 0;")),
                    ui.nav_panel("📊 Summary", ui.div(render_clean_table(state.df_so_sum_miss_headers(), state.df_so_sum_miss_rows(), "tbl_so_sum_miss"), style="padding: 0.75rem 0;"))
                )
            )

        # Summary Adj Results
        summary_adj_results = ui.div()
        if state.so_step6b_done():
            c_val_p = "#10B981" if state.so_adj_val_p() >= 0 else "#E53E3E"
            c_val_m = "#10B981" if state.so_adj_val_m() >= 0 else "#E53E3E"
            c_val_n = "#10B981" if state.so_adj_val_net() >= 0 else "#E53E3E"

            summary_adj_results = ui.div(
                ui.hr(style="margin: 1rem 0; border-color: #E2E8F0;"),
                ui.div(
                    dark_metric_box("📈 TOTAL VALUE ADJ (+)", f"Rp {state.so_adj_val_p():,.0f}", c_val_p),
                    dark_metric_box("📉 TOTAL VALUE ADJ (-)", f"Rp {state.so_adj_val_m():,.0f}", c_val_m),
                    dark_metric_box("⚖️ NET VALUE ADJ", f"Rp {state.so_adj_val_net():,.0f}", c_val_n),
                    style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; width: 100%; margin-bottom: 1rem;"
                ),
                ui.div(
                    dark_metric_box("🟢 TOTAL QTY ADJ (+)", f"{state.so_adj_qty_p():,} ITEM", "#10B981"),
                    dark_metric_box("🔴 TOTAL QTY ADJ (-)", f"{state.so_adj_qty_m():,} ITEM", "#E53E3E"),
                    dark_metric_box("🔺 TOTAL SKU ADJ", f"{state.so_adj_sku_tot():,} SKU", "#3182CE"),
                    style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; width: 100%; margin-bottom: 1rem;"
                ),
                ui.div(
                    ui.download_button("btn_dl_so_adj_master", ui.tags.span(ui.tags.i(class_="fa-solid fa-download", style="margin-right: 6px; font-size: 14px;"), "DOWNLOAD MASTER ADJUSTMENT REPORT (.xlsx)"), style="background-color: #10B981; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 8px 16px; cursor: pointer;"),
                    style="display: flex; justify-content: flex-end; width: 100%; margin-bottom: 0.75rem;"
                ),
                ui.navset_card_tab(
                    ui.nav_panel("📄 Detail Report", ui.div(render_clean_table(state.df_so_adj_detail_headers(), state.df_so_adj_detail_rows(), "tbl_so_adj_det"), style="padding: 0.75rem 0;")),
                    ui.nav_panel("📊 Summary Adjustment", ui.div(render_clean_table(state.df_so_adj_sum_headers(), state.df_so_adj_sum_rows(), "tbl_so_adj_sum"), style="padding: 0.75rem 0;"))
                )
            )

        return ui.div(
            # 5A. Miss Location Section
            ui.div(
                ui.h4("5️⃣ Miss Location Report", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 0.75rem;"),
                ui.div(
                    ui.tags.button(
                        ui.tags.span(ui.tags.i(class_="fa-solid fa-chart-pie", style="margin-right: 6px; font-size: 14px;"), "GENERATE MISS LOC REPORT"),
                        onclick="document.body.classList.add('process-running'); Shiny.setInputValue('btn_run_so_step6_miss', Math.random(), {priority: 'event'});",
                        class_="btn-red-gradient"
                    ),
                    style="display: flex; justify-content: flex-end; width: 100%; margin-top: 0.5rem;"
                ),
                miss_loc_results,
                style="background: white; padding: 1.25rem; border-radius: 10px; border: 1px solid #E2E8F0; margin-bottom: 1.25rem;"
            ),

            # 5B. Summary Adjustment Section
            ui.div(
                ui.h4("6️⃣ Summary Adjustment Report (Financial & Inventory)", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 0.75rem;"),
                ui.div(
                    custom_uploader_box("so_up_adj_minus", "Upload STOCK ADJ - (Opsional)"),
                    custom_uploader_box("so_up_adj_plus", "Upload STOCK ADJ + (Opsional)"),
                    style="display: flex; gap: 1rem; width: 100%; margin-bottom: 0.5rem; flex-wrap: wrap;"
                ),
                ui.div(
                    ui.tags.button(
                        ui.tags.span(ui.tags.i(class_="fa-solid fa-calculator", style="margin-right: 6px; font-size: 14px;"), "RUN SUMMARY ADJUSTMENT"),
                        onclick="document.body.classList.add('process-running'); Shiny.setInputValue('btn_run_so_step6_adj', Math.random(), {priority: 'event'});",
                        class_="btn-red-gradient"
                    ),
                    style="display: flex; justify-content: flex-end; width: 100%; margin-top: 0.5rem;"
                ),
                summary_adj_results,
                style="background: white; padding: 1.25rem; border-radius: 10px; border: 1px solid #E2E8F0; margin-bottom: 1.25rem;"
            ),

            # 5C. Master Full Report (All 11 Sheets)
            ui.div(
                ui.div(
                    ui.h4("🏆 Download Full Master Report (All 11 Sheets)", style="font-size: 16px; font-weight: 800; color: #065F46; margin: 0;"),
                    ui.download_button(
                        "btn_dl_so_master_all",
                        ui.tags.span(ui.tags.i(class_="fa-solid fa-file-excel", style="margin-right: 8px; font-size: 16px;"), "DOWNLOAD FULL SO ANALYZER REPORT (.XLSX)"),
                        style="background: linear-gradient(135deg, #10B981 0%, #059669 100%); color: white; font-weight: 800; border-radius: 8px; border: none; padding: 12px 24px; cursor: pointer; box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);"
                    ),
                    style="display: flex; justify-content: space-between; align-items: center; width: 100%;"
                ),
                style="background: #D1FAE5; border: 1.5px solid #A7F3D0; padding: 1.5rem; border-radius: 12px; margin-bottom: 1rem;"
            )
        )

    @reactive.Effect
    @reactive.event(input.btn_run_so_step6_miss)
    def _proc_so_step6_miss():
        succ, msg = state.run_so_step6_miss_loc()
        if succ: state.show_success_modal.set(True)
        else:
            state.error_modal_message.set(msg)
            state.show_error_modal.set(True)

    @render.download(filename="Miss_Location_Report_SO.xlsx")
    def btn_dl_so_miss_loc():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            state._raw_df_so_miss_loc.to_excel(writer, sheet_name='DETAIL_MISS_LOC', index=False)
            state._raw_df_so_sum_miss.to_excel(writer, sheet_name='SUMMARY', index=False)
        buf.seek(0)
        yield buf.getvalue()

    @reactive.Effect
    @reactive.event(input.btn_run_so_step6_adj)
    def _proc_so_step6_adj():
        f_p = input.so_up_adj_plus()
        f_m = input.so_up_adj_minus()
        succ, msg = state.run_so_step6_summary_adj(f_p, f_m)
        if succ: state.show_success_modal.set(True)
        else:
            state.error_modal_message.set(msg)
            state.show_error_modal.set(True)

    @render.download(filename="Master_Adjustment_Report.xlsx")
    def btn_dl_so_adj_master():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            state._raw_df_so_adj_detail.to_excel(writer, sheet_name='DETAIL_DATA', index=False)
            state._raw_df_so_adj_sum.to_excel(writer, sheet_name='SUMMARY_ADJUSTMENT', index=False)
        buf.seek(0)
        yield buf.getvalue()

    @render.download(filename="FULL_SO_ANALYZER_REPORT.xlsx")
    def btn_dl_so_master_all():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            if not state._raw_df_so_scan.empty: state._raw_df_so_scan.to_excel(writer, sheet_name='1_DATA SCAN', index=False)
            if not state._raw_df_so_stock.empty: state._raw_df_so_stock.to_excel(writer, sheet_name='2_STOCK SYSTEM', index=False)
            if not state._raw_df_so_real_plus.empty: state._raw_df_so_real_plus.to_excel(writer, sheet_name='3_REAL PLUS', index=False)
            if not state._raw_df_so_sys_plus.empty: state._raw_df_so_sys_plus.to_excel(writer, sheet_name='4_SYSTEM PLUS', index=False)
            if not state._raw_df_so_setup_real.empty: state._raw_df_so_setup_real.to_excel(writer, sheet_name='5_SET UP REAL PLUS', index=False)
            if not state._raw_df_so_rec_real.empty: state._raw_df_so_rec_real.to_excel(writer, sheet_name='6_REAL PLUS RECON', index=False)
            if not state._raw_df_so_rec_sys.empty: state._raw_df_so_rec_sys.to_excel(writer, sheet_name='7_SYSTEM OUTSTANDING', index=False)
            if not state._raw_df_so_mult.empty: state._raw_df_so_mult.to_excel(writer, sheet_name='8_MULTIPLE ADJ PLUS', index=False)
            if not state._raw_df_so_sing.empty: state._raw_df_so_sing.to_excel(writer, sheet_name='9_SINGLE ADJ PLUS', index=False)
            if not state._raw_df_so_res4.empty: state._raw_df_so_res4.to_excel(writer, sheet_name='10_HASIL CEK ADJ', index=False)
            if not state._raw_df_so_karantina.empty: state._raw_df_so_karantina.to_excel(writer, sheet_name='11_KARANTINA', index=False)
        buf.seek(0)
        yield buf.getvalue()

# ==========================================================================
    # JUSTIFICATION SO CONTROLLER (DYNAMIC MODE: REVERSAL & NON REVERSAL)
    # ==========================================================================
    @reactive.Effect
    @reactive.event(input.change_jso_mode)
    def _on_change_jso_mode():
        state.jso_mode.set(input.change_jso_mode())

    @render.ui
    def jso_dynamic_body_ui():
        mode = state.jso_mode()

        # 0. Kondisi Belum Memilih Mode
        if not mode or mode == "":
            return ui.div(
                ui.div(
                    ui.tags.i(class_="fa-solid fa-hand-pointer", style="font-size: 32px; color: #C5A059; margin-bottom: 12px;"),
                    ui.h4("Silakan Pilih Mode Justifikasi Terlebih Dahulu", style="font-size: 16px; font-weight: 800; color: #1A202C; margin: 0 0 6px 0;"),
                    ui.p("Pilih antara 'JUSTIFIKASI REVERSAL' atau 'JUSTIFIKASI NON REVERSAL' pada dropdown di atas untuk memunculkan form uploader dokumen.", style="color: #718096; font-size: 13px; margin: 0;"),
                    style="background: #FFFFFF; border: 2px dashed #CBD5E0; border-radius: 12px; padding: 3rem 1.5rem; text-align: center; display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; box-shadow: 0 4px 12px rgba(0,0,0,0.02);"
                )
            )

        # 1. MODE: JUSTIFIKASI REVERSAL (2 Uploader + Filter Tanggal)
        elif mode == "JUSTIFIKASI REVERSAL":
            upload_section = ui.div(
                ui.h4("🔄 Upload Dokumen Justifikasi Reversal (Histori PBI)", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 0.75rem;"),
                ui.div(
                    ui.div(
                        ui.span("📅 Tanggal Awal PBI:", style="font-size: 12px; font-weight: 800; color: #1A202C; margin-bottom: 4px; display: block;"),
                        ui.input_date("jso_rev_start", None, value=state.jso_rev_start_date()),
                        style="flex: 1; min-width: 180px;"
                    ),
                    ui.div(
                        ui.span("📅 Tanggal Akhir PBI:", style="font-size: 12px; font-weight: 800; color: #1A202C; margin-bottom: 4px; display: block;"),
                        ui.input_date("jso_rev_end", None, value=state.jso_rev_end_date()),
                        style="flex: 1; min-width: 180px;"
                    ),
                    style="display: flex; gap: 1rem; width: 100%; margin-bottom: 1.25rem; flex-wrap: wrap; background: #F8FAFC; padding: 1rem; border-radius: 8px; border: 1px solid #E2E8F0;"
                ),
                ui.div(
                    custom_uploader_box("uploader_jso_rev_case", "1. File Multiple Adjustment (Real & System)"),
                    custom_uploader_box("uploader_jso_rev_pbi", "2. File Adjustment PBI (Excel / CSV)"),
                    style="display: flex; gap: 1rem; width: 100%; margin-bottom: 0.5rem; flex-wrap: wrap;"
                ),
                ui.output_ui("jso_rev_action_btn_ui"),
                style="background: white; padding: 1.5rem; border-radius: 12px; border: 1px solid #E2E8F0; margin-bottom: 1.5rem;"
            )
            return ui.div(upload_section, ui.output_ui("jso_rev_results_container"))

        # 2. MODE: JUSTIFIKASI NON REVERSAL
        elif mode == "JUSTIFIKASI NON REVERSAL":
            upload_section = ui.div(
                ui.h4("📥 Upload Dokumen Justifikasi Non Reversal (Sistem & Mutasi)", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 0.75rem;"),
                ui.div(
                    custom_uploader_box("uploader_jso_case", "1. File Adjustment (Plus & Minus)"),
                    custom_uploader_box("uploader_jso_track", "2. Summary Stock (Dashboard Asset)"),
                    custom_uploader_box("uploader_jso_all", "3. All Data Stock (Multiple Adj.)"),
                    custom_uploader_box("uploader_jso_scan", "4. Data Scan (Opsional)"),
                    style="display: flex; gap: 1rem; width: 100%; margin-bottom: 0.5rem; flex-wrap: wrap;"
                ),
                ui.output_ui("justification_so_action_btn_ui"),
                style="background: white; padding: 1.5rem; border-radius: 12px; border: 1px solid #E2E8F0; margin-bottom: 1.5rem;"
            )
            return ui.div(upload_section, ui.output_ui("justification_so_results_container"))

    # --- CONTROLLER MODE REVERSAL ---
    @render.ui
    def jso_rev_action_btn_ui():
        f1 = input.uploader_jso_rev_case() if "uploader_jso_rev_case" in input else None
        f2 = input.uploader_jso_rev_pbi() if "uploader_jso_rev_pbi" in input else None

        if (f1 and len(f1) > 0) and (f2 and len(f2) > 0):
            return ui.div(
                ui.tags.button(
                    ui.tags.span(ui.tags.i(class_="fa-solid fa-play", style="margin-right: 6px; font-size: 14px;"), "RUN ANALISIS REVERSAL"),
                    onclick="window.showGlobalSpinner(); Shiny.setInputValue('btn_run_jso_rev', Math.random(), {priority: 'event'});",
                    class_="btn-red-gradient"
                ),
                style="display: flex; justify-content: flex-end; width: 100%; margin-top: 0.5rem;"
            )
        return ui.div(
            ui.tags.button(
                ui.tags.i(class_="fa-solid fa-lock", style="margin-right: 6px; font-size: 14px;"),
                "UPLOAD KEDUA FILE UNTUK MEMULAI REVERSAL",
                disabled=True,
                class_="btn-locked"
            ),
            style="display: flex; justify-content: flex-end; width: 100%; margin-top: 0.5rem;"
        )

    @reactive.Effect
    @reactive.event(input.btn_run_jso_rev)
    def _proc_jso_rev():
        f1 = input.uploader_jso_rev_case()
        f2 = input.uploader_jso_rev_pbi()
        sd = input.jso_rev_start() if "jso_rev_start" in input else None
        ed = input.jso_rev_end() if "jso_rev_end" in input else None

        if not f1 or not f2:
            state.error_modal_message.set("Upload kedua file (Multiple Adjustment & File PBI) terlebih dahulu!")
            state.show_error_modal.set(True)
            return

        succ, msg = state.process_justification_reversal(f1, f2, sd, ed)
        if succ: state.show_success_modal.set(True)
        else:
            state.error_modal_message.set(msg)
            state.show_error_modal.set(True)

    # ==========================================================================
    # JUSTIFICATION SO - REVERSAL RESULTS CONTAINER (3 TAB: HASIL & 2 FILE MULTIPLE)
    # ==========================================================================
    @render.ui
    def jso_rev_results_container():
        if not state.jso_rev_processed(): return ui.div()
        return ui.div(
            ui.hr(style="margin: 1rem 0; border-color: #E2E8F0;"),
            ui.h4("📋 RINGKASAN HASIL ANALISIS REVERSAL (HISTORI PBI)", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 1rem;"),
            ui.div(
                dark_metric_box("🔄 TERINDIKASI REVERSAL", f"{state.jso_rev_c_match():,} SKU", "#10B981"),
                dark_metric_box("❌ BUKAN REVERSAL / TIDAK COCOK", f"{state.jso_rev_c_nomatch():,} SKU", "#E53E3E"),
                style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; width: 100%; margin-bottom: 1.25rem;"
            ),
            ui.navset_card_tab(
                # TAB 1: HASIL DETAIL REVERSAL
                ui.nav_panel(
                    "📊 HASIL ANALISIS LENGKAP",
                    ui.div(
                        ui.div(
                            ui.p("Rekapitulasi lengkap hasil penelusuran PBI dan status reversal untuk setiap baris adjustment.", style="font-size: 13px; color: #718096; margin: 0;"),
                            ui.download_button(
                                "btn_dl_jso_rev_excel",
                                ui.tags.span(ui.tags.i(class_="fa-solid fa-download", style="margin-right: 6px; font-size: 14px;"), "DOWNLOAD ANALISIS FULL (.XLSX)"),
                                style="background-color: #10B981; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 8px 16px; cursor: pointer;"
                            ),
                            style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 0.75rem; flex-wrap: wrap; gap: 8px;"
                        ),
                        render_clean_table(state.df_jso_rev_headers(), state.df_jso_rev_rows(), "tbl_jso_rev_summary"),
                        style="padding: 0.75rem 0;"
                    )
                ),
                # TAB 2: MULTIPLE REVERSAL
                ui.nav_panel(
                    "🔄 MULTIPLE ADJ (REVERSAL)",
                    ui.div(
                        ui.div(
                            ui.div(
                                ui.strong("Format File Multiple Asli: "),
                                ui.span(f"Baris yang terbukti Reversal ({len(state._raw_df_jso_rev_mult_rev):,} baris). Kolom sama persis dengan file awal.", style="color: #2D3748; font-size: 13px;")
                            ),
                            ui.download_button(
                                "btn_dl_jso_rev_mult_rev",
                                ui.tags.span(ui.tags.i(class_="fa-solid fa-file-excel", style="margin-right: 6px; font-size: 14px;"), "DOWNLOAD FILE MULTIPLE REVERSAL (.XLSX)"),
                                style="background-color: #10B981; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 8px 16px; cursor: pointer;"
                            ),
                            style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 0.75rem; flex-wrap: wrap; gap: 8px;"
                        ),
                        render_clean_table(state.df_jso_rev_mult_rev_headers(), state.df_jso_rev_mult_rev_rows(), "tbl_jso_rev_mult_rev"),
                        style="padding: 0.75rem 0;"
                    )
                ),
                # TAB 3: MULTIPLE BUKAN REVERSAL (UNTUK DI-UPLOAD KE NON-REVERSAL)
                ui.nav_panel(
                    "➡️ MULTIPLE ADJ (BUKAN REVERSAL ➔ UNTUK NON-REVERSAL)",
                    ui.div(
                        ui.div(
                            ui.div(
                                ui.div(ui.strong("💡 File Siap Pakai Untuk Cek Non-Reversal:"), style="color: #C53030; font-weight: 800; font-size: 13px; margin-bottom: 2px;"),
                                ui.span(f"Berisi {len(state._raw_df_jso_rev_mult_nonrev):,} baris yang BUKAN Reversal dengan struktur kolom sama persis dengan file awal. Download file ini dan langsung upload ke Mode 'JUSTIFIKASI NON REVERSAL'.", style="color: #742A2A; font-size: 12px;")
                            ),
                            ui.download_button(
                                "btn_dl_jso_rev_mult_nonrev",
                                ui.tags.span(ui.tags.i(class_="fa-solid fa-cloud-arrow-down", style="margin-right: 6px; font-size: 14px;"), "DOWNLOAD MULTIPLE BUKAN REVERSAL (.XLSX)"),
                                style="background: linear-gradient(135deg, #E53E3E 0%, #C53030 100%); color: white; font-weight: bold; border-radius: 6px; border: none; padding: 8px 16px; cursor: pointer; box-shadow: 0 2px 6px rgba(229,62,62,0.3);"
                            ),
                            style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 0.75rem; flex-wrap: wrap; gap: 8px; background: #FFF5F5; border: 1px solid #FEB2B2; padding: 10px 14px; border-radius: 8px;"
                        ),
                        render_clean_table(state.df_jso_rev_mult_nonrev_headers(), state.df_jso_rev_mult_nonrev_rows(), "tbl_jso_rev_mult_nonrev"),
                        style="padding: 0.75rem 0;"
                    )
                )
            ),
            style="width: 100%; background: white; padding: 1.5rem; border-radius: 12px; border: 1px solid #E2E8F0;"
        )

    @render.download(filename="Hasil_Justifikasi_Reversal_Full.xlsx")
    def btn_dl_jso_rev_excel():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            state._raw_df_jso_rev_res.to_excel(writer, sheet_name='REVERSAL_ANALYSIS', index=False)
        buf.seek(0)
        yield buf.getvalue()

    @render.download(filename="Multiple_Adj_Terindikasi_Reversal.xlsx")
    def btn_dl_jso_rev_mult_rev():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            state._raw_df_jso_rev_mult_rev.to_excel(writer, sheet_name='MULTIPLE_ADJ_REVERSAL', index=False)
        buf.seek(0)
        yield buf.getvalue()

    @render.download(filename="Multiple_Adj_Bukan_Reversal_Untuk_NonRev.xlsx")
    def btn_dl_jso_rev_mult_nonrev():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            state._raw_df_jso_rev_mult_nonrev.to_excel(writer, sheet_name='BUKAN_REVERSAL', index=False)
        buf.seek(0)
        yield buf.getvalue()


    # ==========================================================================
    # JUSTIFICATION SO - NON REVERSAL RESULTS CONTAINER (KEMBALI KE TAMPILAN AWAL)
    # ==========================================================================
    @render.ui
    def justification_so_action_btn_ui():
        f1 = input.uploader_jso_case() if "uploader_jso_case" in input else None
        f2 = input.uploader_jso_track() if "uploader_jso_track" in input else None
        f3 = input.uploader_jso_all() if "uploader_jso_all" in input else None

        # Jika ketiga file utama sudah di-upload -> Tombol Merah Aktif
        if (f1 and len(f1) > 0) and (f2 and len(f2) > 0) and (f3 and len(f3) > 0):
            return ui.div(
                ui.tags.button(
                    ui.tags.span(ui.tags.i(class_="fa-solid fa-play", style="margin-right: 6px; font-size: 14px;"), "RUN COMPARE JUSTIFIKASI NON REVERSAL"),
                    onclick="window.showGlobalSpinner(); Shiny.setInputValue('btn_run_jso', Math.random(), {priority: 'event'});",
                    class_="btn-red-gradient"
                ),
                style="display: flex; justify-content: flex-end; width: 100%; margin-top: 0.5rem;"
            )
        # Jika belum lengkap -> Tombol Terkunci (Gembok)
        return ui.div(
            ui.tags.button(
                ui.tags.i(class_="fa-solid fa-lock", style="margin-right: 6px; font-size: 14px;"),
                "UPLOAD 3 FILE UTAMA UNTUK MEMULAI",
                disabled=True,
                class_="btn-locked"
            ),
            style="display: flex; justify-content: flex-end; width: 100%; margin-top: 0.5rem;"
        )

    @reactive.Effect
    @reactive.event(input.btn_run_jso)
    def _proc_jso():
        f1 = input.uploader_jso_case()
        f2 = input.uploader_jso_track()
        f3 = input.uploader_jso_all()
        f4 = input.uploader_jso_scan() if "uploader_jso_scan" in input else None

        if not f1 or not f2 or not f3:
            state.error_modal_message.set("Pilih ketiga file utama terlebih dahulu!")
            state.show_error_modal.set(True)
            return

        succ, msg = state.process_justification_so(f1, f2, f3, f4)
        if succ:
            state.show_success_modal.set(True)
        else:
            state.error_modal_message.set(msg)
            state.show_error_modal.set(True)
    @render.ui
    def justification_so_results_container():
        if not state.jso_processed(): return ui.div()
        return ui.div(
            ui.hr(style="margin: 1rem 0; border-color: #E2E8F0;"),
            ui.h4("📋 RINGKASAN METRIK JUSTIFIKASI NON REVERSAL", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 1rem;"),
            ui.div(
                dark_metric_box("❓ UNDEFINED", f"{state.jso_c_undef():,} SKU", "#DD6B20"),
                dark_metric_box("💻 SYS ERROR", f"{state.jso_c_sys():,} SKU", "#E53E3E"),
                dark_metric_box("🗳️ KESALAHAN RTO", f"{state.jso_c_rto():,} SKU", "#3182CE"),
                dark_metric_box("🔁 CEK REKON", f"{state.jso_c_rekon():,} SKU", "#C5A059"),
                style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; width: 100%; margin-bottom: 1.25rem;"
            ),
            ui.div(
                ui.div(
                    ui.h4("📋 Ringkasan Hasil Analisis Non Reversal", style="font-size: 15px; font-weight: 800; color: #1A202C; margin: 0;"),
                    ui.download_button(
                        "btn_dl_jso_excel",
                        ui.tags.span(ui.tags.i(class_="fa-solid fa-download", style="margin-right: 6px; font-size: 14px;"), "DOWNLOAD HASIL REKON (.XLSX)"),
                        style="background-color: #10B981; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 8px 16px; cursor: pointer;"
                    ),
                    style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 0.75rem;"
                ),
                render_clean_table(state.df_jso_headers(), state.df_jso_rows(), "tbl_jso_summary"),
                style="background: white; padding: 1.25rem; border-radius: 10px; border: 1px solid #E2E8F0;"
            ),
            style="width: 100%;"
        )

    @render.download(filename="rekon_stock_so_non_reversal.xlsx")
    def btn_dl_jso_excel():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            state._raw_df_jso_res.to_excel(writer, sheet_name='Summary', index=False)
        buf.seek(0)
        yield buf.getvalue()
    # ==========================================================================
    # CROSS CHECK REAL & SYSTEM CONTROLLER & HANDLERS (PERSIS COMPARE SYSTEM)
    # ==========================================================================
    @render.ui
    def cross_check_action_btn_ui():
        f1 = input.uploader_crs_sys() if "uploader_crs_sys" in input else None
        f2 = input.uploader_crs_real() if "uploader_crs_real" in input else None

        if (f1 and len(f1) > 0) and (f2 and len(f2) > 0):
            return ui.div(
                ui.tags.button(
                    ui.tags.span(ui.tags.i(class_="fa-solid fa-play", style="margin-right: 6px; font-size: 14px;"), "RUN MATCHING PROCESS"),
                    onclick="window.showGlobalSpinner(); Shiny.setInputValue('btn_run_cross_check', Math.random(), {priority: 'event'});",
                    class_="btn-red-gradient"
                ),
                style="display: flex; justify-content: flex-end; width: 100%; margin-top: 0.5rem;"
            )
        return ui.div(
            ui.tags.button(
                ui.tags.i(class_="fa-solid fa-lock", style="margin-right: 6px; font-size: 14px;"),
                "UPLOAD KEDUA FILE UNTUK MEMULAI",
                disabled=True,
                class_="btn-locked"
            ),
            style="display: flex; justify-content: flex-end; width: 100%; margin-top: 0.5rem;"
        )
    @reactive.Effect
    @reactive.event(input.btn_run_cross_check)
    def _proc_cross_check():
        f_sys = input.uploader_crs_sys()
        f_real = input.uploader_crs_real()
        if not f_sys or not f_real:
            state.error_modal_message.set("Pilih kedua file (Laporan System & Real Aktual) terlebih dahulu!")
            state.show_error_modal.set(True)
            return

        succ, msg = state.process_cross_check_real_system(f_sys, f_real)
        if succ:
            state.show_success_modal.set(True)
        else:
            state.error_modal_message.set(msg)
            state.show_error_modal.set(True)

    @render.ui
    def cross_check_results_container():
        if not state.crs_processed():
            return ui.div()

        cross_rows = state.df_crs_cross_rows()
        if cross_rows and len(cross_rows) > 0:
            cross_table_ui = render_clean_table(state.df_crs_cross_headers(), cross_rows, "tbl_crs_cross")
        else:
            cross_table_ui = ui.div(
                "✅ Tidak ada selisih lintas cabang (semua match di cabang sendiri atau tidak ditemukan).",
                style="background: #C6F6D5; color: #276749; font-weight: bold; padding: 1.25rem; border-radius: 8px; text-align: center;"
            )

        return ui.div(
            ui.hr(style="margin: 1.5rem 0; border-color: #CBD5E0;"),
            ui.h4("📋 RINGKASAN HASIL MATCHING LINTAS CABANG", style="font-size: 16px; color: #010B13; font-weight: 800; margin-bottom: 1rem;"),
            
            # --- 5 KOTAK METRIK DARK THEME LENGKAP ---
            ui.div(
                dark_metric_box("📦 TOTAL QTY REAL +", f"{state.crs_total_real():,} QTY", "#C5A059"),
                dark_metric_box("💻 TOTAL QTY SYSTEM", f"{state.crs_total_system():,} QTY", "#3182CE"),
                dark_metric_box("✅ TOTAL MATCHED", f"{state.crs_total_matched():,} QTY", "#10B981"),
                dark_metric_box("⚠️ TOTAL UNMATCHED", f"{state.crs_total_unmatched():,} QTY", "#E53E3E"),
                dark_metric_box("🏪 SISA QTY SYSTEM", f"{state.crs_system_left():,} QTY", "#DD6B20"),
                style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; width: 100%; margin-bottom: 1.25rem;"
            ),

            # --- 2 TAB HASIL ---
            ui.navset_card_tab(
                # TAB 1: SEMUA DATA
                ui.nav_panel(
                    "📋 SEMUA HASIL MATCHING",
                    ui.div(
                        ui.div(
                            ui.download_button(
                                "btn_dl_cross_check_all",
                                ui.tags.span(ui.tags.i(class_="fa-solid fa-download", style="margin-right: 6px; font-size: 14px;"), "Download Semua Hasil (.xlsx)"),
                                style="background-color: #10B981; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 8px 16px; cursor: pointer;"
                            ),
                            style="display: flex; justify-content: flex-end; width: 100%; margin-bottom: 0.75rem;"
                        ),
                        render_clean_table(state.df_crs_headers(), state.df_crs_rows(), "tbl_crs_all"),
                        style="padding: 0.75rem 0;"
                    )
                ),
                # TAB 2: KHUSUS BEDA CABANG (CROSS-BRANCH MATCH ONLY)
                ui.nav_panel(
                    "🔄 MATCH LINTAS CABANG (BEDA CABANG)",
                    ui.div(
                        ui.div(
                            ui.div(
                                ui.strong("Hanya Menampilkan Cross-Branch Match: "),
                                ui.span(f"Ditemukan {len(state._raw_df_crs_cross):,} baris perpindahan lintas cabang. Cabang yang sama otomatis dikecualikan.", style="color: #4A5568; font-size: 13px;")
                            ),
                            ui.download_button(
                                "btn_dl_cross_check_cross",
                                ui.tags.span(ui.tags.i(class_="fa-solid fa-file-excel", style="margin-right: 6px; font-size: 14px;"), "Download Match Lintas Cabang (.xlsx)"),
                                style="background-color: #3182CE; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 8px 16px; cursor: pointer;"
                            ),
                            style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 0.75rem; flex-wrap: wrap; gap: 8px;"
                        ),
                        cross_table_ui,
                        style="padding: 0.75rem 0;"
                    )
                )
            ),
            style="width: 100%; background: white; padding: 1.5rem; border-radius: 12px; border: 1px solid #E2E8F0;"
        )

    @render.download(filename="Hasil_Matching_Semua.xlsx")
    def btn_dl_cross_check_all():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            state._raw_df_crs_all.to_excel(writer, sheet_name='ALL_MATCHING', index=False)
        buf.seek(0)
        yield buf.getvalue()

    @render.download(filename="Hasil_Matching_Lintas_Cabang.xlsx")
    def btn_dl_cross_check_cross():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            state._raw_df_crs_cross.to_excel(writer, sheet_name='CROSS_BRANCH_ONLY', index=False)
        buf.seek(0)
        yield buf.getvalue()

    # ==========================================================================
    # BALANCING STOCK: CONTROLLER MURNI SUPABASE (TANPA UPLOADER MANUAL)
    # ==========================================================================
    @reactive.Effect
    @reactive.event(input.btn_sync_balancing_supabase)
    def _on_sync_balancing_supabase():
        succ, msg = state.load_balancing_data_from_supabase()
        ui.insert_ui(ui.tags.script("if (window.hideGlobalSpinner) window.hideGlobalSpinner();"), selector="head", where="beforeEnd")
        if succ:
            state.show_success_modal.set(True)
            ui.notification_show(f"✅ {msg}", type="message", duration=4)
        else:
            state.error_modal_message.set(msg)
            state.show_error_modal.set(True)

    @render.ui
    def bs_category_filter_container_ui():
        if not state.bs_processed():
            return ui.div()

        choices = state.bs_category_list()
        return ui.div(
            ui.div(
                ui.span("📁 Filter Sub Kategori (Category):", style="font-size: 12px; font-weight: 800; color: #1A202C; margin-bottom: 4px; display: block;"),
                ui.input_selectize(
                    "bs_filter_category_select",
                    None,
                    choices=choices,
                    multiple=True,
                    width="100%"
                ),
                style="width: 100%;"
            ),
            style="background: #F8FAFC; border: 1px solid #CBD5E0; padding: 12px 16px; border-radius: 8px; margin-top: 1rem;"
        )

    @reactive.Effect
    def _on_bs_category_filter_change():
        if state.bs_processed() and "bs_filter_category_select" in input:
            sel = input.bs_filter_category_select()
            cats = list(sel) if sel is not None else []
            state.apply_bs_category_filter(cats)
    
    @reactive.Effect
    @reactive.event(input.change_bs_filter_area)
    def _on_bs_area_filter_change():
        val = input.change_bs_filter_area()
        state.apply_bs_area_filter(val)

    # ==========================================================================
    # BALANCING STOCK: WADAH TAB STATIS (ANTI-RESET / ANTI-LONCAT KE TAB 1)
    # ==========================================================================
    @render.ui
    def balancing_stock_results_container():
        # HANYA bergantung pada status proses (Render sekali saja saat data siap)
        if not state.bs_processed():
            return ui.div()

        return ui.div(
            ui.hr(style="margin: 1.5rem 0; border-color: #CBD5E0;"),
            # 1. Metrik diisolasi di output_ui tersendiri
            ui.output_ui("bs_metrics_container_ui"),
            # 2. Kerangka Tab dibuat statis (Tidak akan di-recreate saat filter berubah)
            ui.navset_card_tab(
                ui.nav_panel("1. COMPARE STOK & SALES (UNIQUE SKU)", ui.output_ui("bs_tab1_content_ui")),
                ui.nav_panel("2. LIST REFILL PROGRESIF", ui.output_ui("bs_tab2_content_ui")),
                id="bs_navset_tab"
            ),
            style="width: 100%; background: white; padding: 1.5rem; border-radius: 12px; border: 1px solid #E2E8F0;"
        )

    # --------------------------------------------------------------------------
    # 1. OUTPUT REAKTIF METRIK (UPDATE OTOMATIS TANPA MENGGANGGU TAB)
    # --------------------------------------------------------------------------
    @render.ui
    def bs_metrics_container_ui():
        if not state.bs_processed():
            return ui.div()

        def get_balance_color(pct):
            if pct >= 90.0: return "#10B981"
            elif pct >= 70.0: return "#DD6B20"
            return "#E53E3E"

        c_log = get_balance_color(state.bs_perc_logistik())
        c_off = get_balance_color(state.bs_perc_offline())
        c_on = get_balance_color(state.bs_perc_online())

        return ui.div(
            # BARIS 1: PERSENTASE KESEIMBANGAN (% BALANCE RATE)
            ui.div(
                dark_metric_box("📦 BALANCE AREA LOGISTIK", f"{state.bs_perc_logistik():.1f}%", c_log),
                dark_metric_box("🏪 BALANCE AREA OFFLINE", f"{state.bs_perc_offline():.1f}%", c_off),
                dark_metric_box("🌐 BALANCE AREA ONLINE", f"{state.bs_perc_online():.1f}%", c_on),
                style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; width: 100%; margin-bottom: 1rem;"
            ),
            # BARIS 2: VOLUME TOTAL & DEFISIT SKU YANG PERLU REFILL
            ui.div(
                dark_metric_box("📦 TOTAL UNIQUE SKU", f"{state.bs_total_sku():,} SKU", "#3182CE"),
                dark_metric_box("🔢 TOTAL QTY STOCK", f"{state.bs_total_stock():,} PCS", "#C5A059"),
                dark_metric_box("🏪 DEFISIT OFFLINE", f"{state.bs_sku_need_off():,} SKU", "#DD6B20"),
                dark_metric_box("💻 DEFISIT ONLINE", f"{state.bs_sku_need_on():,} SKU", "#3182CE"),
                dark_metric_box("🚚 DEFISIT LOGISTIK", f"{state.bs_sku_need_log():,} SKU", "#805AD5"),
                style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; width: 100%; margin-bottom: 1.25rem;"
            )
        )

    # --------------------------------------------------------------------------
    # 2. OUTPUT REAKTIF KONTEN TAB 1 (COMPARE SKU)
    # --------------------------------------------------------------------------
    @render.ui
    def bs_tab1_content_ui():
        if not state.bs_processed():
            return ui.div()

        return ui.div(
            ui.div(
                ui.div(
                    ui.h4("📊 Summary Comparation Total Stock to Stock Area", style="font-size: 15px; font-weight: 800; color: #1A202C; margin: 0 0 2px 0;"),
                    ui.p("Pengecualian otomatis terhadap BIN Defect, Reject, Karantina, Perbaikan, dan Toko.", style="color: #718096; font-size: 12px; margin: 0;"),
                ),
                ui.download_button(
                    "btn_dl_bs_tab1",
                    ui.tags.span(ui.tags.i(class_="fa-solid fa-file-excel", style="margin-right: 6px; font-size: 13px;"), "DOWNLOAD TAB 1 (.XLSX)"),
                    style="background: #10B981; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 8px 16px; cursor: pointer; font-size: 12px;"
                ),
                style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 0.75rem; flex-wrap: wrap; gap: 8px;"
            ),
            render_clean_table(state.df_bs_alloc_headers(), state.df_bs_alloc_rows(), "tbl_bs_tab1"),
            style="padding: 0.75rem 0;"
        )

    # --------------------------------------------------------------------------
    # 3. OUTPUT REAKTIF KONTEN TAB 2 (LIST REFILL & FILTER AREA)
    # --------------------------------------------------------------------------
    @render.ui
    def bs_tab2_content_ui():
        if not state.bs_processed():
            return ui.div()

        cur_area = state.bs_selected_area()

        return ui.div(
            ui.div(
                ui.div(
                    ui.h4("🔄 List Refill Area Logistik | Offline | Online", style="font-size: 15px; font-weight: 800; color: #1A202C; margin: 0 0 4px 0;"),
                    ui.p(f"Menampilkan instruksi refill untuk: {cur_area}. Baris tanpa alokasi refill disembunyikan otomatis.", style="color: #718096; font-size: 12px; margin: 0;"),
                ),
                ui.div(
                    # 🌟 FILTER AREA KHUSUS TAB 2
                    ui.div(
                        ui.span("🎯 Filter Area Refill:", style="font-size: 12px; font-weight: 800; color: #1A202C; margin-right: 6px;"),
                        ui.tags.select(
                            ui.tags.option("SEMUA AREA", value="SEMUA AREA", selected=(cur_area == "SEMUA AREA")),
                            ui.tags.option("AREA OFFLINE", value="AREA OFFLINE", selected=(cur_area == "AREA OFFLINE")),
                            ui.tags.option("AREA ONLINE", value="AREA ONLINE", selected=(cur_area == "AREA ONLINE")),
                            ui.tags.option("AREA LOGISTIK", value="AREA LOGISTIK", selected=(cur_area == "AREA LOGISTIK")),
                            id="bs_filter_area_select",
                            onchange="Shiny.setInputValue('change_bs_filter_area', this.value, {priority: 'event'})",
                            style="padding: 6px 12px; border-radius: 6px; border: 1.5px solid #CBD5E0; font-weight: 700; font-size: 12px; background: white; cursor: pointer; min-width: 150px;"
                        ),
                        style="display: flex; align-items: center;"
                    ),
                    ui.download_button(
                        "btn_dl_bs_tab2",
                        ui.tags.span(ui.tags.i(class_="fa-solid fa-file-excel", style="margin-right: 6px; font-size: 13px;"), "DOWNLOAD TEMPLATE REFILL (.XLSX)"),
                        style="background: #3182CE; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 8px 16px; cursor: pointer; font-size: 12px;"
                    ),
                    style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;"
                ),
                style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 0.75rem; flex-wrap: wrap; gap: 10px;"
            ),
            render_clean_table(state.df_bs_refill_headers(), state.df_bs_refill_rows(), "tbl_bs_tab2"),
            style="padding: 0.75rem 0;"
        )


    @render.download(filename="BALANCING_COMPARE_UNIQUE_SKU.xlsx")
    def btn_dl_bs_tab1():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            state._raw_df_bs_alloc.to_excel(writer, sheet_name='COMPARE_SKU', index=False)
        buf.seek(0)
        yield buf.getvalue()

    @render.download(filename="TEMPLATE_LIST_REFILL_PROGRESIF.xlsx")
    def btn_dl_bs_tab2():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            state._raw_df_bs_refill.to_excel(writer, sheet_name='LIST_REFILL', index=False)
        buf.seek(0)
        yield buf.getvalue()

        # ==========================================================================
    # PHYSICAL INVENTORY LIST CONTROLLER (UNIFIED DYNAMIC UI)
    # ==========================================================================
    @reactive.Effect
    @reactive.event(input.change_pil_mode)
    def _on_change_pil_mode():
        state.pil_mode.set(input.change_pil_mode())

    @render.ui
    def pil_dynamic_body_ui():
        mode = state.pil_mode()

        # 0. KONDISI AWAL (BLANK / BELUM MEMILIH MODE)
        if not mode or mode == "":
            return ui.div(
                ui.div(
                    ui.tags.i(class_="fa-solid fa-hand-pointer", style="font-size: 32px; color: #C5A059; margin-bottom: 12px;"),
                    ui.h4("Silakan Pilih Metode Penarikan Data Terlebih Dahulu", style="font-size: 16px; font-weight: 800; color: #1A202C; margin: 0 0 6px 0;"),
                    ui.p("Pilih salah satu metode pada dropdown di atas untuk memunculkan form upload dokumen & proses penarikan data.", style="color: #718096; font-size: 13px; margin: 0;"),
                    style="background: #FFFFFF; border: 2px dashed #CBD5E0; border-radius: 12px; padding: 3rem 1.5rem; text-align: center; display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; box-shadow: 0 4px 12px rgba(0,0,0,0.02);"
                )
            )

        # 1. MODE 1: BY PUTAWAY & PICKING AUDIT
        elif mode == "PUTAWAY & PICKING AUDIT":
            return ui.div(
                ui.div(
                    ui.h4("📥 Upload Dokumen Audit (Sales, RTO, & Mutasi)", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 0.75rem;"),
                    ui.div(
                        custom_uploader_box("uploader_ppa_sales", "1. File Sales (Excel / CSV)"),
                        custom_uploader_box("uploader_ppa_rto", "2. File RTO (Excel / CSV)"),
                        custom_uploader_box("uploader_ppa_mutasi", "3. File Mutasi (Excel / CSV)"),
                        style="display: flex; gap: 1rem; width: 100%; margin-bottom: 1.25rem; flex-wrap: wrap;"
                    ),
                    ui.output_ui("ppa_action_btn_ui"),
                    style="width: 100%; background: white; padding: 1.5rem; border-radius: 12px; border: 1px solid #E2E8F0; margin-bottom: 1.5rem;"
                ),
                ui.output_ui("ppa_results_container")
            )

        # 2. MODE 2: BY NON AUDIT (FILTER MULTIPLE ADJUSTMENT)
        elif mode == "NON AUDIT (MULTIPLE ADJ)":
            return ui.div(
                ui.div(
                    ui.h4("📥 Upload File Multiple Adjustment", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 0.75rem;"),
                    custom_uploader_box("upload_cycle_count_file", "Upload File Multiple Adjustment"),
                    ui.output_ui("cycle_count_action_btn_ui"),
                    style="width: 100%; background: white; padding: 1.25rem; border-radius: 10px; border: 1px solid #E2E8F0; margin-bottom: 1.25rem;"
                ),
                ui.output_ui("cycle_count_results_container")
            )

            # ==========================================================================
    # VALIDATION BARCODE SKU CONTROLLER & HANDLERS
    # ==========================================================================
    @render.ui
    def vbs_action_btn_ui():
        f1 = input.uploader_vbs_scan() if "uploader_vbs_scan" in input else None
        f2 = input.uploader_vbs_list() if "uploader_vbs_list" in input else None

        if (f1 and len(f1) > 0) and (f2 and len(f2) > 0):
            return ui.div(
                ui.tags.button(
                    ui.tags.span(ui.tags.i(class_="fa-solid fa-magnifying-glass", style="margin-right: 6px; font-size: 14px;"), "CEK & VALIDASI BARCODE SKU"),
                    onclick="window.showGlobalSpinner(); Shiny.setInputValue('btn_run_vbs_stage1', Math.random(), {priority: 'event'});",
                    class_="btn-red-gradient"
                ),
                style="display: flex; justify-content: flex-end; width: 100%; margin-top: 0.5rem;"
            )
        return ui.div(
            ui.tags.button(
                ui.tags.i(class_="fa-solid fa-lock", style="margin-right: 6px; font-size: 14px;"),
                "UPLOAD KEDUA FILE UNTUK MEMULAI VALIDASI",
                disabled=True,
                class_="btn-locked"
            ),
            style="display: flex; justify-content: flex-end; width: 100%; margin-top: 0.5rem;"
        )

    @reactive.Effect
    @reactive.event(input.btn_run_vbs_stage1)
    def _proc_vbs_stage1():
        f_scan = input.uploader_vbs_scan()
        f_list = input.uploader_vbs_list()
        if not f_scan or not f_list:
            state.error_modal_message.set("Pilih kedua file terlebih dahulu!")
            state.show_error_modal.set(True)
            return

        succ, msg = state.process_vbs_stage1(f_scan, f_list)
        if succ: state.show_success_modal.set(True)
        else:
            state.error_modal_message.set(msg)
            state.show_error_modal.set(True)

    @reactive.Effect
    @reactive.event(input.btn_run_vbs_stage2)
    def _proc_vbs_stage2():
        succ, msg = state.process_vbs_stage2()
        if succ: state.show_success_modal.set(True)
        else:
            state.error_modal_message.set(msg)
            state.show_error_modal.set(True)

    @render.ui
    def vbs_results_container():
        if not state.vbs_stage1_done(): return ui.div()

        # Banner Konfirmasi / Eksekusi Tahap 2
        if not state.vbs_stage2_done():
            action_stage2_banner = ui.div(
                ui.div(
                    ui.div(
                        ui.h4("⚡ Konfirmasi Perubahan Barcode SKU", style="font-size: 15px; font-weight: 800; color: #92400E; margin: 0 0 4px 0;"),
                        ui.p(f"Ditemukan {state.vbs_total_change_rows():,} baris SKU scan yang perlu diperbarui. Periksa daftar di Tab 'Compare Detail' di bawah. Jika data sudah sesuai, klik tombol di sebelah kanan untuk mengeksekusi.", style="color: #78350F; font-size: 13px; margin: 0;"),
                    ),
                    ui.tags.button(
                        ui.tags.span(ui.tags.i(class_="fa-solid fa-wand-magic-sparkles", style="margin-right: 6px; font-size: 14px;"), "EKSEKUSI PERUBAHAN SKU & PIVOT"),
                        onclick="window.showGlobalSpinner(); Shiny.setInputValue('btn_run_vbs_stage2', Math.random(), {priority: 'event'});",
                        style="background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%); color: white; font-weight: 800; border-radius: 8px; border: none; padding: 10px 20px; cursor: pointer; white-space: nowrap; box-shadow: 0 4px 12px rgba(217, 119, 6, 0.3);"
                    ),
                    style="display: flex; justify-content: space-between; align-items: center; width: 100%; flex-wrap: wrap; gap: 10px;"
                ),
                style="background: #FEF3C7; border: 1.5px solid #FCD34D; border-radius: 10px; padding: 1.25rem; margin-bottom: 1.25rem;"
            )
            tabs_ui = ui.navset_card_tab(
                ui.nav_panel("📋 DATA COMPARE DETAIL", ui.div(render_clean_table(state.df_vbs_compare_headers(), state.df_vbs_compare_rows(), "tbl_vbs_compare"), style="padding: 0.75rem 0;"))
            )
        else:
            action_stage2_banner = ui.div(
                ui.div(
                    ui.div(
                        ui.h4("✅ Perubahan SKU Berhasil Diterapkan!", style="font-size: 15px; font-weight: 800; color: #065F46; margin: 0 0 4px 0;"),
                        ui.p("SKU scan telah diperbarui dan dikelompokkan (pivot) kembali per BIN & SKU. Anda dapat mengunduh laporannya di bawah.", style="color: #047857; font-size: 13px; margin: 0;"),
                    ),
                    ui.download_button(
                        "btn_dl_vbs_all",
                        ui.tags.span(ui.tags.i(class_="fa-solid fa-file-excel", style="margin-right: 6px; font-size: 14px;"), "DOWNLOAD LAPORAN VALIDASI (.XLSX)"),
                        style="background: linear-gradient(135deg, #10B981 0%, #059669 100%); color: white; font-weight: 800; border-radius: 8px; border: none; padding: 10px 20px; cursor: pointer; white-space: nowrap; box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);"
                    ),
                    style="display: flex; justify-content: space-between; align-items: center; width: 100%; flex-wrap: wrap; gap: 10px;"
                ),
                style="background: #D1FAE5; border: 1.5px solid #A7F3D0; border-radius: 10px; padding: 1.25rem; margin-bottom: 1.25rem;"
            )
            tabs_ui = ui.navset_card_tab(
                ui.nav_panel("📋 DATA COMPARE DETAIL", ui.div(render_clean_table(state.df_vbs_compare_headers(), state.df_vbs_compare_rows(), "tbl_vbs_compare"), style="padding: 0.75rem 0;")),
                ui.nav_panel("🔄 PERUBAHAN SKU (BEFORE & AFTER)", ui.div(render_clean_table(state.df_vbs_changes_headers(), state.df_vbs_changes_rows(), "tbl_vbs_changes"), style="padding: 0.75rem 0;")),
                ui.nav_panel("📊 DATA SCAN FINAL (PIVOT BIN & SKU)", ui.div(render_clean_table(state.df_vbs_pivot_headers(), state.df_vbs_pivot_rows(), "tbl_vbs_pivot"), style="padding: 0.75rem 0;"))
            )

        return ui.div(
            ui.hr(style="margin: 1.5rem 0; border-color: #CBD5E0;"),
            ui.h4("📋 RINGKASAN VALIDASI BARCODE SKU", style="font-size: 16px; color: #010B13; font-weight: 800; margin-bottom: 1rem;"),
            
            # 4 Kotak Metrik
            ui.div(
                dark_metric_box("📦 TOTAL BARIS SCAN", f"{state.vbs_total_scan_rows():,} BARIS", "#C5A059"),
                dark_metric_box("✅ SUDAH VALID / SESUAI", f"{state.vbs_total_valid_rows():,} BARIS", "#10B981"),
                dark_metric_box("🔄 PERLU UBAH SKU", f"{state.vbs_total_change_rows():,} BARIS", "#DD6B20"),
                dark_metric_box("❓ TIDAK DITEMUKAN (TETAP)", f"{state.vbs_total_unmatched_rows():,} BARIS", "#E53E3E"),
                style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; width: 100%; margin-bottom: 1.25rem;"
            ),
            action_stage2_banner,
            tabs_ui,
            style="width: 100%; background: white; padding: 1.5rem; border-radius: 12px; border: 1px solid #E2E8F0;"
        )

    @render.download(filename="LAPORAN_VALIDASI_BARCODE_SKU.xlsx")
    def btn_dl_vbs_all():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            state._raw_df_vbs_pivot.to_excel(writer, sheet_name='DATA_SCAN_PIVOT_FINAL', index=False)
            state._raw_df_vbs_changes.to_excel(writer, sheet_name='PERUBAHAN_BEFORE_AFTER', index=False)
            state._raw_df_vbs_compare.to_excel(writer, sheet_name='COMPARE_DETAIL', index=False)
        buf.seek(0)
        yield buf.getvalue()



    @reactive.Effect
    @reactive.event(input.btn_process_percentage_display)
    def _proc_percentage_display():
        f = input.upload_percentage_display_file()
        if not f:
            state.error_modal_message.set("Upload file Stock terlebih dahulu!")
            state.show_error_modal.set(True)
            return

        succ, msg = state.process_percentage_display(f)
        if succ:
            state.show_success_modal.set(True)
        else:
            state.error_modal_message.set(msg)
            state.show_error_modal.set(True)
# 1. Event saat User Mengganti Dropdown Cabang
    # ==========================================================================
    # CONTROLLER PERCENTAGE DISPLAY (VERSI BARU: 3 AREA & REFILL LOWER BODY)
    # ==========================================================================
    @reactive.Effect
    @reactive.event(input.pd_branch_selector)
    def _on_pd_branch_change():
        br = input.pd_branch_selector()
        if br and br != state.pd_selected_branch():
            state.pd_selected_branch.set(br)
            succ, msg = state.load_stock_from_supabase_for_percentage_display(branch_name=br, silent=True)
            if succ:
                ui.notification_show(f"🏬 Menampilkan stok {br}", type="message", duration=3)
            else:
                ui.notification_show(f"⚠️ {msg}", type="warning", duration=4)

    @reactive.Effect
    @reactive.event(input.btn_fetch_stock_jezpro_pd)
    def _fetch_cloud_stock_pd():
        current_br = state.pd_selected_branch()
        succ, msg = state.load_stock_from_supabase_for_percentage_display(branch_name=current_br)
        ui.insert_ui(ui.tags.script("if (window.hideGlobalSpinner) window.hideGlobalSpinner();"), selector="head", where="beforeEnd")
        if succ:
            state.show_success_modal.set(True)
            ui.notification_show(f"✅ {msg}", type="message", duration=4)
        else:
            state.error_modal_message.set(msg)
            state.show_error_modal.set(True)

    @render.ui
    def percentage_display_results_container():
        if not state.pd_processed():
            return ui.div()

        # TAB 1: DISPLAY AVAILABILITY (ARTICLE BASE)
        tab1_display_content = ui.div(
            # BARIS 1: METRIK UTAMA DISPLAY
            ui.div(
                dark_metric_box("🧥 TOTAL ARTICLE", f"{state.pd_total_art():,} ART", "#7B61FF"),
                dark_metric_box("✅ ON DISPLAY", f"{state.pd_on_display():,} ({state.pd_perc_display():.1f}%)", "#10B981"),
                dark_metric_box("⚠️ NEED DISPLAY", f"{state.pd_need_display():,} ({state.pd_perc_need():.1f}%)", "#E53E3E"),
                style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; width: 100%; margin-bottom: 1rem;"
            ),
            # BARIS 2: METRIK GUDANG (DISATUKAN) & SKU DIKECUALIKAN
            ui.div(
                dark_metric_box("📦 ARTIKEL TERSEDIA DI GUDANG (OFF / LOG / ONL / LAINNYA)", f"{state.pd_need_display():,} ART", "#3182CE"),
                dark_metric_box("🚫 SKU DI BIN DIKECUALIKAN", f"{state.pd_excluded_sku():,} SKU", "#E53E3E"),
                style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem; width: 100%; margin-bottom: 1.25rem;"
            ),
            ui.div(
                ui.div(
                    ui.h4("📋 List Article Kosong di Toko (Wajib Dipajang)", style="font-size: 15px; font-weight: 800; color: #1A202C; margin: 0;"),
                    ui.download_button(
                        "btn_dl_display_refill",
                        ui.tags.span(ui.tags.i(class_="fa-solid fa-download", style="margin-right: 6px; font-size: 14px;"), "Download List Display (.xlsx)"),
                        style="background-color: #10B981; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 8px 16px; cursor: pointer; font-size: 12px;"
                    ),
                    style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 0.75rem;"
                ),
                render_clean_table(state.df_pd_display_headers(), state.df_pd_display_rows(), "tbl_pd_display"),
                style="padding: 0.75rem 0;"
            )
        )

        # TAB 2: REFILL TOKO (KHUSUS LOWER BODY, TARGET 10 PCS)
        tab2_refill_content = ui.div(
            ui.div(
                dark_metric_box("👖 TOTAL SKU LOWER BODY PERLU REFILL", f"{state.rt_total_sku():,} SKU", "#3182CE"),
                dark_metric_box("🔥 PRIORITY (QTY TOKO 0)", f"{state.rt_priority_sku():,} SKU", "#DD6B20"),
                dark_metric_box("🔢 TOTAL QTY REFILL (TARGET 10)", f"{state.rt_total_qty_refill():,} PCS", "#10B981"),
                style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1rem; width: 100%; margin-bottom: 1.25rem;"
            ),
            ui.div(
                ui.div(
                    ui.div(
                        ui.h4("📋 Detail List Refill Toko (Khusus Lower Body - Maks 10 Pcs)", style="font-size: 15px; font-weight: 800; color: #1A202C; margin: 0 0 2px 0;"),
                        ui.p("Item masuk antrean jika stok di Toko < 10 pcs dan stok gudang > 0. Baris dipecah per 1 BIN (Prioritas: OFF ➔ LOG ➔ ONL ➔ Lainnya).", style="color: #718096; font-size: 12px; margin: 0;")
                    ),
                    ui.download_button(
                        "btn_dl_rt_refill",
                        ui.tags.span(ui.tags.i(class_="fa-solid fa-download", style="margin-right: 6px; font-size: 14px;"), "Download Refill Lower Body (.xlsx)"),
                        style="background-color: #3182CE; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 8px 16px; cursor: pointer; font-size: 12px;"
                    ),
                    style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 0.75rem; flex-wrap: wrap; gap: 8px;"
                ),
                render_clean_table(state.df_rt_headers(), state.df_rt_rows(), "tbl_rt_refill"),
                style="padding: 0.75rem 0;"
            )
        )

        return ui.div(
            ui.hr(style="margin: 1.5rem 0; border-color: #CBD5E0;"),
            ui.navset_card_tab(
                ui.nav_panel("📊 DISPLAY AVAILABILITY (ARTICLE BASE)", tab1_display_content),
                ui.nav_panel("🏬 REFILL TOKO (KHUSUS LOWER BODY)", tab2_refill_content)
            ),
            style="width: 100%; background: white; padding: 1.5rem; border-radius: 12px; border: 1px solid #E2E8F0;"
        )
    # Handler Download Excel
    @render.download(filename="LIST_PENARIKAN_DISPLAY.xlsx")
    def btn_dl_display_refill():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            state._raw_df_pd_display.to_excel(writer, sheet_name='DISPLAY_REFILL', index=False)
        buf.seek(0)
        yield buf.getvalue()

    @render.download(filename="LIST_REFILL_TOKO.xlsx")
    def btn_dl_rt_refill():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            state._raw_df_rt_filtered.to_excel(writer, sheet_name='REFILL_TOKO', index=False)
        buf.seek(0)
        yield buf.getvalue()

# ==========================================================================
    # CONTROLLER: LATIHAN FORMULA EXCEL & AUTO-GRADING
    # ==========================================================================
    @render.ui
    def excel_practice_action_btn_ui():
        f = input.upload_exam_answer_file() if "upload_exam_answer_file" in input else None
        if f and len(f) > 0:
            return ui.div(
                ui.tags.button(
                    ui.tags.span(ui.tags.i(class_="fa-solid fa-wand-magic-sparkles", style="margin-right: 6px; font-size: 14px;"), "Cek Nilai Saya"),
                    onclick="window.showGlobalSpinner(); Shiny.setInputValue('btn_process_exam_grading', Math.random(), {priority: 'event'});",
                    class_="btn-red-gradient"
                ),
                style="display: flex; justify-content: flex-end; width: 100%; margin-top: 0.75rem;"
            )
        return ui.div(
            ui.tags.button(
                ui.tags.i(class_="fa-solid fa-lock", style="margin-right: 6px; font-size: 14px;"),
                "Upload File Dulu Untuk Cek Nilai",
                disabled=True,
                class_="btn-locked"
            ),
            style="display: flex; justify-content: flex-end; width: 100%; margin-top: 0.75rem;"
        )

    @render.ui
    def excel_practice_results_container():
        if not state.excel_exam_graded():
            return ui.div()

        score = state.excel_exam_score()
        score_color = "#10B981" if score >= 75 else ("#DD6B20" if score >= 50 else "#E53E3E")

        return ui.div(
            ui.hr(style="margin: 1.5rem 0; border-color: #CBD5E0;"),
            ui.h4("Hasil Latihan Kamu", style="font-size: 16px; font-weight: 800; color: #1A202C; margin-bottom: 1rem;"),
            
            ui.div(
                dark_metric_box("🎯 Nilai Kamu", f"{score} / 100", score_color),
                dark_metric_box("✅ Rumus Bener", f"{state.excel_exam_correct()} Bagian", "#10B981"),
                dark_metric_box("❌ Perlu Dicek Lagi", f"{state.excel_exam_wrong()} Bagian", "#E53E3E"),
                style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; width: 100%; margin-bottom: 1.25rem;"
            ),

            ui.div(
                ui.div(
                    ui.h4("Rincian Jawaban", style="font-size: 15px; font-weight: 800; color: #1A202C; margin: 0;"),
                    ui.download_button(
                        "btn_dl_exam_report",
                        ui.tags.span(ui.tags.i(class_="fa-solid fa-file-excel", style="margin-right: 6px; font-size: 14px;"), "Download Rekap Nilai (.xlsx)"),
                        onclick="setTimeout(function() { document.body.classList.remove('process-running'); }, 1500);",
                        style="background-color: #10B981; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 8px 16px; cursor: pointer;"
                    ),
                    style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 0.75rem;"
                ),
                render_clean_table(state.df_exam_result_headers(), state.df_exam_result_rows(), "tbl_exam_report"),
                style="padding: 0.75rem 0;"
            ),
            style="width: 100%; background: white; padding: 1.5rem; border-radius: 12px; border: 1px solid #E2E8F0;"
        )

    @render.download(filename="LAPORAN_EVALUASI_EXCEL_PESERTA.xlsx")
    def btn_dl_exam_report():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            df = getattr(state, "_raw_df_exam_result", None)
            if df is not None and not df.empty:
                df.to_excel(writer, sheet_name='SCORECARD_EVALUASI', index=False)
            else:
                pd.DataFrame(columns=["NO", "SOAL / MATERI", "STATUS", "KETERANGAN"]).to_excel(
                    writer, sheet_name='SCORECARD_EVALUASI', index=False
                )
        buf.seek(0)
        yield buf.getvalue()

    @render.download(
        filename=lambda: f"SOAL_LATIHAN_EXCEL_{datetime.now().strftime('%d_%m_%Y_%H%M')}.xlsx"
    )
    def btn_dl_excel_practice():
        try:
            content = state.generate_excel_practice_package()
            if content is not None:
                if hasattr(content, "getvalue"):
                    yield content.getvalue()
                elif isinstance(content, (bytes, bytearray)):
                    yield content
                else:
                    yield bytes(content)
            else:
                yield b""
        except Exception as e:
            import traceback
            print(f"Error generate excel: {e}")
            traceback.print_exc()
            yield b""

    @reactive.Effect
    @reactive.event(input.btn_process_exam_grading)
    def _proc_exam_grading():
        f = input.upload_exam_answer_file()
        if not f:
            ui.insert_ui(ui.tags.script("window.hideGlobalSpinner();"), selector="head", where="beforeEnd")
            ui.notification_show("Upload file jawaban Excel kamu terlebih dahulu ya!", type="warning", duration=4)
            return

        try:
            succ, msg = state.grade_excel_practice(f)
            if succ:
                ui.notification_show(msg, type="message", duration=5)
            else:
                ui.notification_show(msg, type="error", duration=6)
        except Exception as e:
            ui.notification_show(f"Terjadi kesalahan saat memeriksa file: {str(e)}", type="error", duration=6)
        finally:
            ui.insert_ui(ui.tags.script("window.hideGlobalSpinner();"), selector="head", where="beforeEnd")

# ==========================================================================
    # CONTROLLER: MENU FORM AUDITOR (EXTERNAL AUDIT PACK)
    # ==========================================================================
    # 1. Saat file berhasil dimuat -> isi seluruh opsi awal
    @reactive.Effect
    @reactive.event(input.btn_load_auditor_file)
    def _proc_load_auditor():
        f = input.upload_auditor_file()
        if not f:
            ui.insert_ui(ui.tags.script("window.hideGlobalSpinner();"), selector="head", where="beforeEnd")
            ui.notification_show("Pilih file All Data Stock terlebih dahulu!", type="warning", duration=4)
            return

        succ, msg = state.process_auditor_upload(f)
        ui.insert_ui(ui.tags.script("window.hideGlobalSpinner();"), selector="head", where="beforeEnd")
        if succ:
            # Set cache opsi awal
            _last_filter_state["c_brands"] = state.auditor_list_brand()
            _last_filter_state["c_subs"] = state.auditor_list_sub()
            _last_filter_state["c_bins"] = state.auditor_list_bin()

            # Update ketiga dropdown di browser
            ui.update_selectize("aud_filter_brand", choices=state.auditor_list_brand(), selected=[])
            ui.update_selectize("aud_filter_sub", choices=state.auditor_list_sub(), selected=[])
            ui.update_selectize("aud_filter_bin", choices=state.auditor_list_bin(), selected=[])

            state.show_success_modal.set(True)
        else:
            state.error_modal_message.set(msg)
            state.show_error_modal.set(True)

    # 2. Logika Saling Mengerucut Real-time (Anti-Flicker & Presisi)
    @reactive.Effect
    def _on_auditor_filter_change():
        if not state.auditor_uploaded():
            return

        brands = list(input.aud_filter_brand()) if "aud_filter_brand" in input and input.aud_filter_brand() is not None else []
        subs = list(input.aud_filter_sub()) if "aud_filter_sub" in input and input.aud_filter_sub() is not None else []
        bins = list(input.aud_filter_bin()) if "aud_filter_bin" in input and input.aud_filter_bin() is not None else []

        # Hitung opsi yang mengerucut (masing-masing dropdown dibatasi 2 dropdown lainnya)
        avail_brands, avail_subs, avail_bins = state.get_cascading_auditor_choices(brands, subs, bins)

        # Pertahankan pilihan user yang masih valid
        valid_brands = [b for b in brands if b in avail_brands]
        valid_subs = [s for s in subs if s in avail_subs]
        valid_bins = [bn for bn in bins if bn in avail_bins]

        # Update opsi di browser HANYA jika list opsinya berubah (mencegah dropdown menutup sendiri saat diklik)
        if avail_brands != _last_filter_state["c_brands"] or len(valid_brands) != len(brands):
            ui.update_selectize("aud_filter_brand", choices=avail_brands, selected=valid_brands)
            _last_filter_state["c_brands"] = avail_brands

        if avail_subs != _last_filter_state["c_subs"] or len(valid_subs) != len(subs):
            ui.update_selectize("aud_filter_sub", choices=avail_subs, selected=valid_subs)
            _last_filter_state["c_subs"] = avail_subs

        if avail_bins != _last_filter_state["c_bins"] or len(valid_bins) != len(bins):
            ui.update_selectize("aud_filter_bin", choices=avail_bins, selected=valid_bins)
            _last_filter_state["c_bins"] = avail_bins

        # Terapkan filter ke tabel data dan metrik
        state.apply_auditor_filters(valid_brands, valid_subs, valid_bins)
    
# RENDER REAKTIF KOTAK DOWNLOAD PDF AUDIT
    @render.ui
    def auditor_pdf_downloader_container_ui():
        sel = state.auditor_selected_for_pdf()
        if not sel:
            return ui.div()
        return ui.div(
            ui.div(
                ui.span(f"📄 Dokumen Audit {sel.get('id')} Siap Diunduh:", style="font-weight: 700; font-size: 13px; color: #065F46;"),
                ui.download_button(
                    "btn_dl_audit_pdf_file_hidden",
                    ui.tags.span(ui.tags.i(class_="fa-solid fa-download", style="margin-right: 6px;"), f"DOWNLOAD {str(sel.get('id')).replace('/', '_')}.PDF"),
                    style="background: #10B981; color: white; border: none; padding: 8px 16px; border-radius: 6px; font-weight: 800; font-size: 12px; cursor: pointer;"
                ),
                style="display: flex; justify-content: space-between; align-items: center; width: 100%;"
            ),
            style="background: #D1FAE5; border: 1.5px solid #6EE7B7; border-radius: 8px; padding: 12px 16px; margin-top: 1rem;"
        )

    # PEMBERSIH STATE PDF AUDIT SETELAH DIKLIK
    @reactive.Effect
    @reactive.event(input.btn_clear_audit_pdf_state)
    def _clear_audit_pdf():
        state.auditor_selected_for_pdf.set(None)

    # PEMBERSIH STATE PDF MEMO SETELAH DIKLIK
    @reactive.Effect
    @reactive.event(input.btn_clear_memo_pdf_state)
    def _clear_memo_pdf():
        state.memo_selected_for_pdf.set(None)
# --------------------------------------------------------------------------
    # CONTROLLER AUDITOR (LANGSUNG KETIK DI TABEL - POP-UP HILANG TOTAL)
    # --------------------------------------------------------------------------
    @render.ui
    def auditor_results_container():
        if not state.auditor_processed():
            return ui.div()

        from views import render_auditor_editable_table

        return ui.div(
            ui.hr(style="margin: 1.5rem 0; border-color: #CBD5E0;"),
            ui.h4("📋 RINGKASAN DATA SASARAN AUDIT", style="font-size: 16px; font-weight: 800; color: #1A202C; margin-bottom: 1rem;"),
            
            # Kartu Metrik Live Update
            ui.output_ui("auditor_metrics_cards_ui"),

            # Tabel Detail Yang Bisa Diketik Langsung
            ui.div(
                ui.div(
                    ui.div(
                        ui.h4("Stock Count Sheet (Tabel Hitung Langsung di Web)", style="font-size: 15px; font-weight: 800; color: #1A202C; margin: 0 0 2px 0;"),
                        ui.span(f"Petugas Counter: {state.auditor_counter()} | Masukkan angka fisik langsung pada kotak kuning di bawah.", style="color: #059669; font-weight: 700; font-size: 12px;"),
                    ),
                    ui.download_button(
                        "btn_dl_auditor_pack",
                        ui.tags.span(ui.tags.i(class_="fa-solid fa-file-excel", style="margin-right: 8px; font-size: 14px;"), "DOWNLOAD EXCEL COUNT SHEET (.XLSX)"),
                        style="background: linear-gradient(135deg, #10B981 0%, #059669 100%); color: white; font-weight: 800; border-radius: 6px; border: none; padding: 8px 16px; cursor: pointer; box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);"
                    ),
                    style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 0.75rem; flex-wrap: wrap; gap: 8px;"
                ),
                render_auditor_editable_table(state._raw_df_auditor_filtered, state.auditor_counter()),
                style="background: white; padding: 1.5rem; border-radius: 12px; border: 1px solid #E2E8F0;"
            ),
            style="width: 100%;"
        )

    # Kartu Ringkasan (Terpisah agar tidak membuat tabel refresh saat user mengetik)
    @render.ui
    def auditor_metrics_cards_ui():
        var_col = "#10B981" if state.auditor_total_var() == 0 else "#E53E3E"
        # Format nilai variance ke format Rupiah
        tot_var_rp = f"Rp {state.auditor_total_var():,}" if state.auditor_total_var() >= 0 else f"-Rp {abs(state.auditor_total_var()):,}"
        
        return ui.div(
            dark_metric_box("🏭 TOTAL LOKASI BIN", f"{state.auditor_total_bin():,} BIN", "#3182CE"),
            dark_metric_box("📦 TOTAL SKU HARUS DICEK", f"{state.auditor_total_sku():,} SKU", "#C5A059"),
            dark_metric_box("🔢 TOTAL QTY SYSTEM", f"{state.auditor_total_qty():,} PCS", "#10B981"),
            dark_metric_box("🎯 TOTAL PHYSICAL COUNT", f"{state.auditor_total_phys():,} PCS", "#3182CE"),
            dark_metric_box("⚖️ TOTAL NET VARIANCE VALUE", tot_var_rp, var_col),
            style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; width: 100%; margin-bottom: 1.25rem;"
        )
    # Handler Saat Angka Diketik Langsung di Baris Tabel
    @reactive.Effect
    @reactive.event(input.auditor_row_inline_update)
    def _on_auditor_inline_update():
        d = input.auditor_row_inline_update() or {}
        idx = d.get("idx", 0)
        phys = d.get("phys", "")
        ver = d.get("ver", "No")
        rem = d.get("rem", "")

        state.update_single_count_row(idx, phys, ver, rem)

    # Handler Download Excel Bawaan
    @render.download(
        filename=lambda: f"EXTERNAL_AUDIT_PACK_{datetime.now().strftime('%d_%m_%Y_%H%M')}.xlsx"
    )
    def btn_dl_auditor_pack():
        meta_dict = {
            "company": input.aud_company() if "aud_company" in input else "PT ZONA KARYA NUSANTARA",
            "branch": input.aud_branch() if "aud_branch" in input else "SZ SURABAYA",
            "date": input.aud_date() if "aud_date" in input else "12 JANUARI 2027",
            "start_time": input.aud_start_time() if "aud_start_time" in input else "08:00",
            "end_time": input.aud_end_time() if "aud_end_time" in input else "17:00",
            "method": input.aud_method() if "aud_method" in input else "Full count (wall-to-wall)",
            "lead": input.aud_lead() if "aud_lead" in input else "",
            "manager": input.aud_manager() if "aud_manager" in input else "",
            "supervisor": input.aud_supervisor() if "aud_supervisor" in input else "",
            "currency": input.aud_currency() if "aud_currency" in input else "IDR",
            "counter_name": state.auditor_counter(),
            "checker_name": input.sign_checker() if "sign_checker" in input else "",
            "finance_manager": input.sign_finance() if "sign_finance" in input else "",
            "audit_firm": input.sign_kap() if "sign_kap" in input else "KAP Independent & Partners",
            "audit_partner": input.sign_partner() if "sign_partner" in input else "",
        }
        content = state.generate_auditor_excel_pack(meta_dict)
        yield content

# ==========================================================================
    # 4. Handler Upload File Excel yang Sudah Diisi (Poin 3)
    @reactive.Effect
    @reactive.event(input.btn_execute_import_count_sheet)
    def _proc_import_count_sheet():
        f = input.upload_filled_count_sheet() if "upload_filled_count_sheet" in input else None
        if not f:
            ui.insert_ui(ui.tags.script("if (window.hideGlobalSpinner) window.hideGlobalSpinner();"), selector="head", where="beforeEnd")
            ui.notification_show("Pilih file Excel yang telah diisi terlebih dahulu!", type="warning", duration=4)
            return

        succ, msg = state.import_filled_count_sheet(f)
        ui.insert_ui(ui.tags.script("if (window.hideGlobalSpinner) window.hideGlobalSpinner();"), selector="head", where="beforeEnd")
        if succ:
            ui.notification_show(msg, type="message", duration=5)
        else:
            ui.notification_show(msg, type="error", duration=5)

    # 5. Handler Tambah & Hapus Findings Dinamis di Tab 3 (Poin 7)
    @reactive.Effect
    @reactive.event(input.btn_add_obs_finding)
    def _add_obs_finding():
        d = input.btn_add_obs_finding() or {}
        succ, msg = state.add_auditor_finding(d.get("area", ""), d.get("case", ""), d.get("risk", "Medium"), d.get("recom", ""), d.get("status", "Open"))
        if succ:
            ui.notification_show("✅ " + msg, type="message", duration=3)
        else:
            ui.notification_show("⚠️ " + msg, type="warning", duration=4)

    @reactive.Effect
    @reactive.event(input.btn_delete_obs_finding_idx)
    def _del_obs_finding():
        idx = input.btn_delete_obs_finding_idx()
        state.delete_auditor_finding(idx)
        ui.notification_show("🗑️ Temuan berhasil dihapus.", type="message", duration=2)

    @render.ui
    def auditor_findings_table_ui():
        findings = state.auditor_findings_list()
        if not findings:
            return ui.div(
                ui.p("Belum ada temuan pengecualian fisik yang ditambahkan. Gunakan formulir di atas untuk mencatat temuan auditor.", style="color: #718096; font-style: italic; text-align: center; padding: 1.5rem;"),
                style="background: #F8FAFC; border: 1px dashed #CBD5E0; border-radius: 8px;"
            )

        tr_list = []
        for idx, it in enumerate(findings, start=1):
            del_btn = ui.tags.button(
                ui.tags.i(class_="fa-solid fa-trash", style="color: #E53E3E;"),
                onclick=f"Shiny.setInputValue('btn_delete_obs_finding_idx', {idx-1}, {{priority: 'event'}})",
                style="background: transparent; border: none; cursor: pointer; padding: 4px;"
            )
            r_col = "#E53E3E" if it.get('risk') == "High" else ("#DD6B20" if it.get('risk') == "Medium" else "#3182CE")
            tr_list.append(ui.tags.tr(
                ui.tags.td(str(idx), style="text-align: center; font-weight: bold;"),
                ui.tags.td(str(it.get("area", "-"))),
                ui.tags.td(str(it.get("case", "-"))),
                ui.tags.td(str(it.get("risk", "Medium")), style=f"font-weight: 800; color: {r_col}; text-align: center;"),
                ui.tags.td(str(it.get("recom", "-"))),
                ui.tags.td(str(it.get("status", "Open")), style="text-align: center; font-weight: bold;"),
                ui.tags.td(del_btn, style="text-align: center;")
            ))

        headers = ["NO", "AREA", "TEMUAN / CASE", "RISK", "REKOMENDASI", "STATUS", "AKSI"]
        th_list = [ui.tags.th(h, style="text-align: center;" if h in ["NO", "RISK", "STATUS", "AKSI"] else "") for h in headers]

        return ui.div(
            ui.tags.table(
                ui.tags.thead(ui.tags.tr(*th_list)),
                ui.tags.tbody(*tr_list),
                class_="custom-clean-table",
                style="border: 1px solid #CBD5E0; border-radius: 8px; overflow: hidden; width: 100%;"
            ),
            style="width: 100%; overflow-x: auto;"
        )

    # 6. Handler Simpan Sesi Audit Lengkap ke Supabase (Poin 4 & 6)
    @reactive.Effect
    @reactive.event(input.btn_execute_save_audit_supabase)
    def _save_audit_session_supabase():
        meta = input.btn_execute_save_audit_supabase() or {}
        succ, msg = state.save_audit_session_to_supabase(meta)
        ui.insert_ui(ui.tags.script("if (window.hideGlobalSpinner) window.hideGlobalSpinner();"), selector="head", where="beforeEnd")
        if succ:
            state.show_success_modal.set(True)
            ui.update_navs("auditor_navset_tab", selected="5. AUDIT HISTORY & PDF")
            ui.notification_show(msg, type="message", duration=5)
        else:
            state.error_modal_message.set(msg)
            state.show_error_modal.set(True)

    # 7. Render History di Tab 5 & Download PDF (Poin 5)
    @reactive.Effect
    @reactive.event(input.btn_refresh_audit_history)
    def _refresh_audit_hist():
        state.load_auditor_history()
        ui.notification_show("Data riwayat audit telah dimuat ulang dari Supabase.", type="message", duration=3)

    # --------------------------------------------------------------------------
    # RENDER RIWAYAT AUDIT (KARTU HISTORY DENGAN DIRECT DOWNLOAD PDF)
    # --------------------------------------------------------------------------
    # RENDER KARTU RIWAYAT (HAPUS DOWNLOAD BAR STATIS DARI DALAM KARTU)
    @render.ui
    def auditor_history_cards_ui():
        histories = state.auditor_history_list()
        if not histories:
            return ui.div(
                ui.p("Belum ada riwayat audit tersimpan di database Supabase. Selesaikan sesi audit pada Tab 4 untuk menyimpan dokumen.", style="color: #718096; font-style: italic; text-align: center; padding: 2rem;"),
                style="background: #F8FAFC; border-radius: 10px; border: 1px dashed #CBD5E0;"
            )

        cards = []
        for h in histories:
            h_id = h.get("id", "-")
            dt = h.get("count_date", "-")
            br = h.get("branch", "-")
            lead = h.get("lead_auditor", "-")
            sku_cnt = h.get("total_sku", 0)
            sys_cnt = h.get("total_qty_system", 0)
            phys_cnt = h.get("total_qty_physical", 0)
            var_cnt = h.get("total_variance_qty", 0)
            open_findings = sum(1 for f in h.get("findings", []) if f.get("status") == "Open")
            var_color = "#E53E3E" if var_cnt != 0 else "#10B981"

            cards.append(ui.div(
                ui.div(
                    ui.div(
                        ui.div(
                            ui.span(h_id, style="font-weight: 800; font-size: 15px; color: #1A202C; margin-right: 8px;"),
                            ui.span(f"Tanggal: {dt}", style="background: #EDF2F7; color: #2D3748; font-weight: 700; font-size: 11px; padding: 3px 8px; border-radius: 4px; margin-right: 6px;"),
                            ui.span(f"⚠️ {open_findings} Open Findings", style="background: #FED7D7; color: #9B2C2C; font-weight: 700; font-size: 11px; padding: 3px 8px; border-radius: 4px;") if open_findings > 0 else ui.span("✅ All Closed", style="background: #C6F6D5; color: #22543D; font-weight: 700; font-size: 11px; padding: 3px 8px; border-radius: 4px;"),
                            style="display: flex; align-items: center; margin-bottom: 4px; flex-wrap: wrap; gap: 4px;"
                        ),
                        ui.p(f"Cabang: {br} • Lead Auditor: {lead}", style="margin: 0; font-size: 12px; color: #718096;")
                    ),
                    ui.div(
                        # 1. Tombol Buka Hasil di Web
                        ui.tags.button(
                            ui.tags.i(class_="fa-solid fa-eye", style="margin-right: 6px;"), "BUKA",
                            onclick=f"Shiny.setInputValue('btn_open_audit_detail_modal', '{h_id}', {{priority: 'event'}})",
                            style="background: #3182CE; color: white; border: none; padding: 8px 14px; border-radius: 6px; font-weight: 800; font-size: 12px; cursor: pointer; margin-right: 6px;"
                        ),
                        # 2. Tombol Persiapan PDF
                        ui.tags.button(
                            ui.tags.i(class_="fa-solid fa-file-pdf", style="margin-right: 6px;"), "SIAPKAN PDF",
                            onclick=f"Shiny.setInputValue('btn_prepare_audit_pdf', '{h_id}', {{priority: 'event'}});",
                            style="background: linear-gradient(135deg, #E50914 0%, #B20710 100%); color: white; border: none; padding: 8px 14px; border-radius: 6px; font-weight: 800; font-size: 12px; cursor: pointer; margin-right: 6px;"
                        ),
                        # 3. Tombol Hapus Sesi Audit
                        ui.tags.button(
                            ui.tags.i(class_="fa-solid fa-trash", style="margin-right: 4px;"), "Hapus",
                            onclick=f"Shiny.setInputValue('btn_open_del_audit_modal', '{h_id}', {{priority: 'event'}})",
                            style="background: #FFF5F5; color: #E53E3E; border: 1.5px solid #FEB2B2; padding: 7px 12px; border-radius: 6px; font-weight: 700; font-size: 12px; cursor: pointer;"
                        ),
                        style="display: flex; align-items: center; flex-wrap: wrap; gap: 4px;"
                    ),
                    style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;"
                ),
                ui.div(
                    ui.span(f"📦 Total SKU: {sku_cnt:,} | 💻 Qty System: {sys_cnt:,} | 🎯 Physical Count: {phys_cnt:,} | ", style="font-size: 12px; color: #4A5568;"),
                    ui.span(f"Net Variance: {var_cnt:,} PCS", style=f"font-size: 12px; font-weight: 800; color: {var_color};"),
                    style="border-top: 1px dashed #E2E8F0; padding-top: 8px; margin-top: 8px;"
                ),
                style="background: white; border: 1.5px solid #CBD5E0; border-radius: 10px; padding: 1rem 1.25rem; margin-bottom: 0.85rem;"
            ))

        return ui.div(*cards)

    # TAB 5: PASTIKAN MEMANGGIL OUTPUT UI REAKTIF
    tab5_history = ui.div(
        ui.div(
            ui.div(
                ui.h4("📂 Riwayat & Arsip Audit Pack (Tersimpan di Supabase)", style="font-size: 15px; font-weight: 800; color: #1A202C; margin: 0 0 4px 0;"),
                ui.p("Auditor dapat meninjau hasil stock opname terdahulu dan mengunduh laporan PDF resmi.", style="color: #718096; font-size: 13px; margin: 0;"),
            ),
            ui.tags.button(
                ui.tags.i(class_="fa-solid fa-arrows-rotate", style="margin-right: 6px;"), "Refresh History",
                onclick="Shiny.setInputValue('btn_refresh_audit_history', Math.random(), {priority: 'event'})",
                style="background: #EDF2F7; color: #2D3748; border: 1.5px solid #CBD5E0; padding: 6px 14px; border-radius: 6px; font-weight: 700; font-size: 12px; cursor: pointer;"
            ),
            style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.25rem; flex-wrap: wrap; gap: 8px;"
        ),
        ui.output_ui("auditor_history_cards_ui"),
        ui.output_ui("auditor_pdf_downloader_container_ui"),  # <-- Kotak hijau ini sekarang reaktif & bisa hilang otomatis
        style="padding: 0.5rem 0;"
    )
    # --------------------------------------------------------------------------
    # POP-UP DETAIL HASIL AUDIT DI WEB
    # --------------------------------------------------------------------------
    def _render_and_show_detail_modal(a_id):
        target = next((h for h in state.auditor_history_list() if h.get("id") == a_id), None)
        if not target:
            ui.notification_show("Data sesi audit tidak ditemukan!", type="error")
            return

        state.auditor_selected_detail.set(target)

        findings = target.get("findings", [])
        if findings:
            finding_rows = []
            for f_idx, fd in enumerate(findings, start=1):
                cur_stat = fd.get("status", "Open")
                is_closed = (cur_stat == "Closed")
                
                # Desain badge status dengan ID unik agar mudah di-update lewat JS
                stat_badge_id = f"badge_stat_{a_id.replace('/', '_')}_{f_idx-1}"
                stat_badge_html = (
                    f'<span id="{stat_badge_id}" style="background: #C6F6D5; color: #22543D; font-weight: 800; padding: 3px 8px; border-radius: 4px; font-size: 11px;">Closed</span>'
                    if is_closed else 
                    f'<span id="{stat_badge_id}" style="background: #FED7D7; color: #9B2C2C; font-weight: 800; padding: 3px 8px; border-radius: 4px; font-size: 11px;">Open</span>'
                )
                
                btn_id = f"btn_toggle_f_{a_id.replace('/', '_')}_{f_idx-1}"
                
                # Tombol aksi interaktif instan (mengubah UI browser tanpa reload modal)
                btn_action_html = f"""
                    <button id="{btn_id}" onclick="
                        let isCurrentlyClosed = {str(is_closed).lower()};
                        let badge = document.getElementById('{stat_badge_id}');
                        let btn = document.getElementById('{btn_id}');
                        
                        if (!isCurrentlyClosed) {{
                            badge.style.background = '#C6F6D5';
                            badge.style.color = '#22543D';
                            badge.innerText = 'Closed';
                            btn.style.background = '#EDF2F7';
                            btn.style.color = '#4A5568';
                            btn.style.border = '1px solid #CBD5E0';
                            btn.innerHTML = '<i class=\\'fa-solid fa-arrow-rotate-left\\'></i> Buka Kembali';
                        }} else {{
                            badge.style.background = '#FED7D7';
                            badge.style.color = '#9B2C2C';
                            badge.innerText = 'Open';
                            btn.style.background = '#10B981';
                            btn.style.color = '#FFFFFF';
                            btn.style.border = 'none';
                            btn.innerHTML = '<i class=\\'fa-solid fa-check\\'></i> Selesaikan (Close)';
                        }}
                        
                        // Kirim request ke backend Python secara senyap (silent update) tanpa ganggu modal
                        Shiny.setInputValue('btn_toggle_audit_finding_status', {{id: '{a_id}', idx: {f_idx-1}}}, {{priority: 'event'}});
                    " style="background: {'#EDF2F7' if is_closed else '#10B981'}; color: {'#4A5568' if is_closed else '#FFFFFF'}; border: {'1px solid #CBD5E0' if is_closed else 'none'}; padding: {'4px 10px' if is_closed else '5px 12px'}; border-radius: 4px; font-size: 11px; font-weight: 800; cursor: pointer;">
                        <i class="fa-solid {'fa-arrow-rotate-left' if is_closed else 'fa-check'}"></i> {'Buka Kembali' if is_closed else 'Selesaikan (Close)'}
                    </button>
                """

                risk_color = "#E53E3E" if fd.get("risk") == "High" else ("#DD6B20" if fd.get("risk") == "Medium" else "#3182CE")

                finding_rows.append(ui.tags.tr(
                    ui.tags.td(str(f_idx), style="text-align: center; font-weight: bold;"),
                    ui.tags.td(str(fd.get("area", "-"))),
                    ui.tags.td(str(fd.get("case", "-"))),
                    ui.tags.td(str(fd.get("risk", "-")), style=f"font-weight: 800; color: {risk_color}; text-align: center;"),
                    ui.tags.td(str(fd.get("recom", "-"))),
                    ui.tags.td(ui.HTML(stat_badge_html), style="text-align: center;"),
                    ui.tags.td(ui.HTML(btn_action_html), style="text-align: center;")
                ))

            tbl_findings = ui.tags.table(
                ui.tags.thead(ui.tags.tr(
                    ui.tags.th("No", style="text-align: center;"),
                    ui.tags.th("Area"), ui.tags.th("Temuan / Case"),
                    ui.tags.th("Risk", style="text-align: center;"),
                    ui.tags.th("Rekomendasi Auditor"),
                    ui.tags.th("Status", style="text-align: center;"),
                    ui.tags.th("Aksi Tindak Lanjut", style="text-align: center;")
                )),
                ui.tags.tbody(*finding_rows),
                class_="custom-clean-table", style="width: 100%; border: 1px solid #CBD5E0; border-radius: 8px;"
            )
        else:
            tbl_findings = ui.p("Tidak ada temuan pengecualian yang dicatat pada sesi audit ini.", style="color: #718096; font-style: italic; padding: 1rem; text-align: center;")
        # 2. Tabel Item Count Sheet
        items = target.get("items", [])
        if items:
            item_rows = []
            for i_idx, it in enumerate(items[:200], start=1):
                q_sys = safe_int(it.get("Qty System", 0))
                q_phys = safe_int(it.get("Physical Count", 0)) if str(it.get("Physical Count", "")).strip() != "" else "-"
                v_val = it.get("Variance Value", "-")
                v_str = f"Rp {safe_int(v_val):,}" if v_val != "-" and str(v_val).strip() != "" else "-"

                item_rows.append(ui.tags.tr(
                    ui.tags.td(str(i_idx), style="text-align: center;"),
                    ui.tags.td(str(it.get("Bin Location", "-"))),
                    ui.tags.td(str(it.get("SKU", "-")), style="font-weight: 700; color: #2B6CB0;"),
                    ui.tags.td(str(it.get("Description", "-"))),
                    ui.tags.td(str(it.get("UoM (PAIR / PCS)", "PCS")), style="text-align: center;"),
                    ui.tags.td(str(q_sys), style="text-align: right; font-weight: 700;"),
                    ui.tags.td(str(q_phys), style="text-align: right; font-weight: 700; color: #22543D;"),
                    ui.tags.td(v_str, style="text-align: right; font-weight: 800;"),
                    ui.tags.td(str(it.get("Counter", "-")), style="text-align: center;"),
                    ui.tags.td(str(it.get("Auditor Verified", "No")), style="text-align: center;"),
                    ui.tags.td(str(it.get("Remarks", "")))
                ))

            tbl_items = ui.div(
                ui.tags.table(
                    ui.tags.thead(ui.tags.tr(
                        ui.tags.th("No", style="text-align: center;"),
                        ui.tags.th("Bin Location"), ui.tags.th("SKU"), ui.tags.th("Description"),
                        ui.tags.th("UoM", style="text-align: center;"),
                        ui.tags.th("Qty System", style="text-align: right;"),
                        ui.tags.th("Physical Count", style="text-align: right;"),
                        ui.tags.th("Variance Value", style="text-align: right;"),
                        ui.tags.th("Counter", style="text-align: center;"),
                        ui.tags.th("Verified", style="text-align: center;"),
                        ui.tags.th("Remarks")
                    )),
                    ui.tags.tbody(*item_rows),
                    class_="custom-clean-table", style="width: 100%;"
                ),
                style="max-height: 400px; overflow-y: auto; border: 1px solid #CBD5E0; border-radius: 8px;"
            )
        else:
            tbl_items = ui.p("Data count sheet kosong.", style="color: #718096; font-style: italic; padding: 1rem; text-align: center;")

        # 3. Preview Tanda Tangan Digital
        def sign_box(role_title, name_val, img_data):
            img_tag = ui.tags.img(src=img_data, style="max-height: 60px; max-width: 150px; display: block; margin: 4px auto;") if (img_data and len(img_data) > 50) else ui.span("(Belum ada goresan TTD)", style="color: #A0AEC0; font-size: 11px; font-style: italic;")
            return ui.div(
                ui.strong(role_title, style="font-size: 12px; color: #1A202C; display: block; margin-bottom: 2px;"),
                ui.span(name_val if name_val else "-", style="font-size: 12px; color: #4A5568; display: block; margin-bottom: 6px; font-weight: 600;"),
                ui.div(img_tag, style="height: 65px; display: flex; align-items: center; justify-content: center; background: #FFF; border: 1px dashed #CBD5E0; border-radius: 6px;"),
                style="flex: 1; min-width: 170px; background: #F8FAFC; padding: 10px; border-radius: 8px; border: 1px solid #E2E8F0; text-align: center;"
            )

        signatures_ui = ui.div(
            sign_box("Counter", target.get("sign_counter_name"), target.get("sign_counter_img")),
            sign_box("Supervisor", target.get("sign_supervisor_name"), target.get("sign_supervisor_img")),
            sign_box("Ops. Manager", target.get("sign_manager_name"), target.get("sign_manager_img")),
            sign_box("Lead Auditor", target.get("sign_lead_name"), target.get("sign_lead_img")),
            style="display: flex; gap: 10px; flex-wrap: wrap; width: 100%; margin-top: 1rem;"
        )

        modal_body = ui.div(
            ui.div(
                ui.div(
                    ui.span(f"🏢 Perusahaan: {target.get('company')}", style="font-size: 13px; font-weight: 700; color: #1A202C; display: block;"),
                    ui.span(f"🏬 Cabang: {target.get('branch')} | 📅 Tanggal Hitung: {target.get('count_date')} ({target.get('start_time')} - {target.get('end_time')})", style="font-size: 12px; color: #4A5568; display: block; margin-top: 2px;"),
                    ui.span(f"👤 Tim: Lead Auditor: {target.get('lead_auditor')} • Manager: {target.get('manager')} • SPV: {target.get('supervisor')}", style="font-size: 12px; color: #718096; display: block; margin-top: 2px;"),
                ),
                style="background: #EDF2F7; padding: 12px 16px; border-radius: 8px; margin-bottom: 1.25rem;"
            ),
            ui.navset_card_tab(
                ui.nav_panel(
                    "🔍 OBSERVASI & TEMUAN AUDITOR",
                    ui.div(
                        ui.p("Daftar temuan fisik yang dicatat auditor. Klik tombol 'Selesaikan (Close)' jika tindak lanjut sudah rampung:", style="font-size: 12px; color: #718096; margin-bottom: 8px;"),
                        tbl_findings,
                        style="padding: 10px 0;"
                    )
                ),
                ui.nav_panel(
                    "📦 DETAIL STOCK COUNT SHEET",
                    ui.div(
                        ui.p(f"Menampilkan total {len(items):,} item yang diperiksa secara fisik:", style="font-size: 12px; color: #718096; margin-bottom: 8px;"),
                        tbl_items,
                        style="padding: 10px 0;"
                    )
                ),
                ui.nav_panel(
                    "✍️ TANDA TANGAN DIGITAL RESMI",
                    ui.div(
                        ui.p("Tanda tangan para penanggung jawab yang tercatat dalam sistem:", style="font-size: 12px; color: #718096; margin-bottom: 4px;"),
                        signatures_ui,
                        style="padding: 10px 0;"
                    )
                )
            ),
            style="width: 100%;"
        )

        ui.modal_show(ui.modal(
            modal_body,
            title=ui.div(ui.tags.i(class_="fa-solid fa-file-invoice", style="color: #3182CE; margin-right: 8px;"), f"Detail Hasil Audit: {a_id}"),
            size="xl",
            easy_close=True,
            footer=ui.div(
                ui.modal_button("Tutup", class_="btn-page-nav"),
                style="display: flex; justify-content: flex-end;"
            )
        ))

    # --------------------------------------------------------------------------
    # HANDLER BUKA HASIL AUDIT DI WEB (MENYIMPAN STATE DETAIL)
    # --------------------------------------------------------------------------
    @reactive.Effect
    @reactive.event(input.btn_open_audit_detail_modal)
    def _open_audit_detail():
        a_id = input.btn_open_audit_detail_modal()
        target = next((h for h in state.auditor_history_list() if h.get("id") == a_id), None)
        if not target:
            ui.notification_show("Data sesi audit tidak ditemukan!", type="error")
            return
        
        # Set data detail ke state agar UI reaktif merender halaman detail
        state.auditor_selected_detail.set(target)
        # Buka modal menggunakan UI interaktif Shiny yang aman
        from views import show_audit_detail_modal
        show_audit_detail_modal(target)

    # Handler Ubah Status Temuan Audit (Open <-> Closed)
    @reactive.Effect
    @reactive.event(input.btn_toggle_audit_finding_status)
    def _on_toggle_finding():
        data = input.btn_toggle_audit_finding_status() or {}
        a_id = data.get("id")
        idx = data.get("idx")
        
        if a_id is not None and idx is not None:
            succ, msg = state.toggle_audit_finding_status(a_id, int(idx))
            if succ:
                ui.notification_show(f"✅ {msg}", type="message", duration=2)
            else:
                ui.notification_show(f"⚠️ {msg}", type="warning", duration=3)

    # --------------------------------------------------------------------------
    # MODAL & HANDLER HAPUS SESI AUDIT (POIN 2)
    # --------------------------------------------------------------------------
    @reactive.Effect
    @reactive.event(input.btn_open_del_audit_modal)
    def _open_del_audit_modal():
        a_id = input.btn_open_del_audit_modal()
        ui.modal_show(ui.modal(
            ui.div(
                ui.tags.i(class_="fa-solid fa-triangle-exclamation", style="font-size: 40px; color: #E53E3E; margin-bottom: 8px;"),
                ui.h4(f"Hapus Sesi Audit {a_id}?", style="font-weight: 800; color: #1A202C; margin: 0 0 6px 0;"),
                ui.p("Apakah Anda yakin ingin menghapus data audit ini secara permanen dari database Supabase? Data yang dihapus tidak dapat dipulihkan.", style="color: #718096; font-size: 13px; margin: 0;"),
                style="text-align: center; padding: 1rem 0;"
            ),
            title="🗑️ Konfirmasi Hapus Sesi Audit",
            easy_close=True,
            footer=ui.div(
                ui.modal_button("Batal"),
                ui.tags.button(
                    "Ya, Hapus Permanen",
                    onclick=f"Shiny.setInputValue('btn_confirm_del_audit', '{a_id}', {{priority: 'event'}})",
                    style="background: #E53E3E; color: white; border: none; padding: 6px 14px; border-radius: 6px; font-weight: bold; cursor: pointer; margin-left: 8px;"
                ),
                style="display: flex; justify-content: flex-end;"
            )
        ))

    @reactive.Effect
    @reactive.event(input.btn_confirm_del_audit)
    def _confirm_del_audit():
        a_id = input.btn_confirm_del_audit()
        ui.modal_remove()
        succ, msg = state.delete_audit_session(a_id)
        ui.notification_show(f"🗑️ {msg}", type="message", duration=4)

    # SINKRONISASI NAMA COUNTER DARI TAB 1 KE TAB 2
    @reactive.Effect
    @reactive.event(input.change_auditor_counter_name)
    def _update_auditor_counter():
        val = input.change_auditor_counter_name()
        state.update_auditor_counter(val)

    # HANDLER PERSIAPAN DOWNLOAD PDF AUDIT
    @reactive.Effect
    @reactive.event(input.btn_prepare_audit_pdf)
    def _prep_audit_pdf():
        a_id = input.btn_prepare_audit_pdf()
        matches = [h for h in state.auditor_history_list() if h.get("id") == a_id]
        if matches:
            state.auditor_selected_for_pdf.set(matches[0])
            ui.notification_show(f"File PDF untuk {a_id} siap diunduh!", type="message", duration=3)

    @render.download(filename=lambda: f"{str(state.auditor_selected_for_pdf().get('id', 'AUDIT')).replace('/', '_')}.pdf" if state.auditor_selected_for_pdf() else "AUDIT_REPORT.pdf")
    def btn_dl_audit_pdf_file_hidden():
        from config import generate_audit_pack_pdf_bytes
        sel = state.auditor_selected_for_pdf()
        if not sel:
            yield b""
        else:
            yield generate_audit_pack_pdf_bytes(sel)
    
# ==========================================================================
    # WAREHOUSE ACTIVITY MONITOR (LL01) EVENT HANDLERS
    # ==========================================================================
    @reactive.Effect
    @reactive.event(input.btn_refresh_ll01)
    def _on_refresh_ll01():
        succ, msg = state.load_ll01_data_from_supabase()
        ui.insert_ui(ui.tags.script("if (window.hideGlobalSpinner) window.hideGlobalSpinner();"), selector="head", where="beforeEnd")
        if succ:
            ui.notification_show(f"✅ {msg}", type="message", duration=4)
        else:
            ui.notification_show(f"⚠️ {msg}", type="error", duration=5)

    @reactive.Effect
    @reactive.event(input.change_ll01_kategori)
    def _on_change_ll01_kat():
        state.ll01_filter_kategori.set(input.change_ll01_kategori())

    @reactive.Effect
    @reactive.event(input.change_ll01_aging)
    def _on_change_ll01_aging():
        state.ll01_filter_aging.set(input.change_ll01_aging())

    # Download Excel Report
    @render.download(
        filename=lambda: f"LL01_WAREHOUSE_MONITOR_{datetime.now().strftime('%d_%m_%Y_%H%M')}.xlsx"
    )
    def btn_dl_ll01_report():
        buf = io.BytesIO()
        df_export = pd.DataFrame(state.get_filtered_ll01())
        if not df_export.empty:
            cols = [c for c in ['kategori', 'waiting_status', 'article_name', 'qty', 'bin_target', 'pic_name', 'waktu_scan_str', 'durasi_aging', 'll01_status'] if c in df_export.columns]
            df_export = df_export[cols]
        else:
            df_export = pd.DataFrame(columns=["kategori", "article_name", "qty", "bin_target", "durasi_aging", "ll01_status"])

        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            df_export.to_excel(writer, sheet_name='LL01_STAGING_MONITOR', index=False)
        buf.seek(0)
        yield buf.getvalue()
        
    @reactive.Effect
    @reactive.event(input.btn_refresh_ll01_all)
    def refresh_warehouse_monitor():
        state.load_ll01_data_from_supabase()
        state.load_transfer_orders_from_supabase()
        state.load_mass_adjustments_from_supabase()
        state.load_single_adjustments_from_supabase()
        state.load_special_buffer_stock_from_supabase()
        # Modal hijau langsung muncul tanpa tirai gelap di belakangnya
        state.show_success_modal.set(True)
    # ==========================================================================
    # POP-UP DETAIL ITEM TRANSFER (ANTI-CRASH, NATIVE REGEX, DIRECT QUERY)
    # ==========================================================================
    @reactive.Effect
    @reactive.event(input.btn_open_tf_items_modal)
    def _open_tf_detail():
        import re
        import traceback

        raw_code = input.btn_open_tf_items_modal()
        tf_code = str(raw_code).strip()

        matched_items = []

        try:
            # 1. TEMBAK LANGSUNG KE SUPABASE DENGAN QUERY RESMI (stf_code=eq.X)
            client = get_supabase()
            tbl = client.table("jezpro_transfer_items").select("*")
            tbl.params.append(f"stf_code=eq.{tf_code}")
            res_items = tbl.execute()

            if res_items and hasattr(res_items, 'data') and res_items.data:
                matched_items = res_items.data
            else:
                # Fallback: jika tidak ketemu di query spesifik, coba cari di state lokal
                matched_items = [it for it in state.ll01_tf_items() if str(it.get("stf_code", "")).strip() == tf_code]

        except Exception as e:
            print(f"⚠️ Kendala load item Supabase: {e}")
            traceback.print_exc()
            matched_items = [it for it in state.ll01_tf_items() if str(it.get("stf_code", "")).strip() == tf_code]

        # 2. SUSUN TABEL RINCIAN ITEM (Menggunakan Regex Bawaan - Tanpa bs4 agar tidak freeze)
        rows = []
        for idx, it in enumerate(matched_items, start=1):
            art_raw = str(it.get("article_name", "-"))
            # Bersihkan tag HTML menggunakan regex standar bawaan Python (super aman)
            art_clean = re.sub(r'<[^>]+>', ' ', art_raw)
            art_clean = re.sub(r'\s+', ' ', art_clean).strip()

            bin_asal = re.sub(r'<[^>]+>', '', str(it.get("bin_asal", "-"))).strip()
            start_st = re.sub(r'<[^>]+>', '', str(it.get("start_store", "-"))).strip()
            end_st = re.sub(r'<[^>]+>', '', str(it.get("end_store", "-"))).strip()
            qty_tf = it.get('qty_tf', 1)
            qty_bin = it.get('qty_in_bin', 0)

            rows.append(ui.tags.tr(
                ui.tags.td(str(idx), style="text-align: center; font-weight: bold;"),
                ui.tags.td(art_clean, style="font-weight: 700; color: #1A202C; max-width: 320px; white-space: normal;"),
                ui.tags.td(ui.tags.code(bin_asal, style="font-weight: bold; color: #2B6CB0;")),
                ui.tags.td(f"{qty_tf} Pcs", style="text-align: center; font-weight: 800; color: #E50914;"),
                ui.tags.td(f"{qty_bin} Pcs", style="text-align: center; color: #718096;"),
                ui.tags.td(f"{start_st} ➔ {end_st}", style="font-size: 12px;")
            ))

        # 3. TAMPILKAN MODAL SECARA AMAN
        try:
            ui.modal_show(ui.modal(
                ui.div(
                    ui.h4(f"📋 Rincian Item Barang: {tf_code}", style="font-weight: 800; color: #1A202C; margin-bottom: 4px; font-size: 15px;"),
                    ui.p(f"Ditemukan total {len(matched_items)} item barang pada dokumen transfer ini.", style="color: #718096; font-size: 12px; margin-bottom: 12px;"),
                    ui.tags.table(
                        ui.tags.thead(ui.tags.tr(
                            ui.tags.th("NO", style="text-align: center;"),
                            ui.tags.th("NAMA ARTIKEL / DESKRIPSI"),
                            ui.tags.th("BIN ASAL"),
                            ui.tags.th("QTY TF", style="text-align: center;"),
                            ui.tags.th("STOK BIN", style="text-align: center;"),
                            ui.tags.th("RUTE STORE")
                        )),
                        ui.tags.tbody(*rows) if rows else ui.tags.tr(
                            ui.tags.td("Rincian barang kosong pada dokumen transfer ini.", colspan=6, style="text-align: center; padding: 1.5rem; color: #718096; font-style: italic;")
                        ),
                        class_="custom-clean-table", style="width: 100%; border: 1px solid #CBD5E0; border-radius: 8px;"
                    ),
                    style="max-height: 480px; overflow-y: auto; padding: 0.5rem 0;"
                ),
                title=f"🚚 Transfer Order Detail: {tf_code}",
                size="l",
                easy_close=True,
                footer=ui.modal_button("Tutup", class_="btn-page-nav")
            ))
        except Exception as err_modal:
            print("Gagal render modal:", err_modal)
            ui.notification_show(f"Gagal menampilkan pop-up: {err_modal}", type="error")
            # Pop-Up Modal Detail Item Multiple Adjustment (Anti-Freeze & Bebas Limit)

    # ==========================================================================
    # POP-UP MODAL DETAIL ITEM MULTIPLE ADJUSTMENT (FIXED QUERY & AMAN DARI BLOKIR)
    # ==========================================================================
    @reactive.Effect
    @reactive.event(input.btn_open_ma_items_modal)
    def _open_ma_detail():
        import re
        import traceback

        raw_id = input.btn_open_ma_items_modal()
        ma_id = safe_int(raw_id) if raw_id else 0

        matched_items = []
        try:
            client = get_supabase()
            if client and ma_id > 0:
                # 🌟 SINTAKS RESMI SUPABASE PYTHON (.eq dan .limit)
                res_items = client.table("jezpro_adjustment_items") \
                                  .select("*") \
                                  .eq("ma_id", ma_id) \
                                  .limit(1000) \
                                  .execute()
                if res_items and hasattr(res_items, 'data') and res_items.data:
                    matched_items = res_items.data
        except Exception as e:
            print(f"⚠️ Gagal ambil item MADJ #{ma_id} dari Supabase:", e)
            traceback.print_exc()

        rows = []
        for idx, it in enumerate(matched_items, start=1):
            diff = safe_int(it.get('diff_qty', 0))
            diff_col = "#10B981" if diff > 0 else "#E53E3E"
            rows.append(ui.tags.tr(
                ui.tags.td(str(idx), style="text-align: center; font-weight: bold;"),
                ui.tags.td(ui.tags.code(str(it.get("bin_code", "-")), style="font-weight: bold; color: #2B6CB0;")),
                ui.tags.td(str(it.get("barcode_sku", "-")), style="font-weight: 700;"),
                ui.tags.td(str(it.get("article_name", "-")), style="max-width: 250px; white-space: normal; font-size: 12px;"),
                ui.tags.td(f"{it.get('color', '-')} / {it.get('size_variant', '-')}", style="text-align: center; font-size: 12px;"),
                ui.tags.td(str(safe_int(it.get("qty_system", 0))), style="text-align: right;"),
                ui.tags.td(str(safe_int(it.get("qty_so", 0))), style="text-align: right; font-weight: 700;"),
                ui.tags.td(f"{diff:+d}", style=f"text-align: right; font-weight: 800; color: {diff_col};")
            ))

        # Bungkus tabel dengan tbody yang benar (mencegah HTML parser error)
        tbody_content = ui.tags.tbody(*rows) if rows else ui.tags.tbody(
            ui.tags.tr(
                ui.tags.td("Rincian barang adjustment kosong atau tidak ditemukan pada dokumen ini.", colspan="8", style="text-align: center; padding: 1.5rem; color: #718096; font-style: italic;")
            )
        )

        ui.modal_show(ui.modal(
            ui.div(
                ui.div(
                    ui.h4(f"📋 Rincian Item Multiple Adjustment: ID #{ma_id}", style="font-weight: 800; color: #1A202C; margin-bottom: 4px; font-size: 15px;"),
                    ui.p(f"Ditemukan total {len(matched_items):,} baris barang pada dokumen adjustment ini.", style="color: #718096; font-size: 12px; margin: 0;"),
                    style="margin-bottom: 12px;"
                ),
                ui.div(
                    ui.tags.table(
                        ui.tags.thead(ui.tags.tr(
                            ui.tags.th("NO", style="text-align: center;"),
                            ui.tags.th("BIN"),
                            ui.tags.th("SKU"),
                            ui.tags.th("NAMA ARTIKEL"),
                            ui.tags.th("WARNA / SIZE", style="text-align: center;"),
                            ui.tags.th("QTY SYS", style="text-align: right;"),
                            ui.tags.th("QTY SO", style="text-align: right;"),
                            ui.tags.th("SELISIH", style="text-align: right;")
                        )),
                        tbody_content,
                        class_="custom-clean-table", style="width: 100%; border: 1px solid #CBD5E0; border-radius: 8px;"
                    ),
                    style="max-height: 480px; overflow-y: auto;"
                ),
                style="padding: 0.5rem 0;"
            ),
            title=f"⚖️ Detail Dokumen Adjustment #{ma_id}",
            size="l",
            easy_close=True,
            footer=ui.modal_button("Tutup", class_="btn-page-nav")
        ))
    @reactive.Effect
    @reactive.event(input.change_ll01_stock_branch)
    def _on_change_ll01_stk_br():
        state.ll01_stock_filter_branch.set(input.change_ll01_stock_branch())

    @reactive.Effect
    @reactive.event(input.change_ll01_stock_type)
    def _on_change_ll01_stk_tp():
        state.ll01_stock_filter_type.set(input.change_ll01_stock_type())

    @render.download(
        filename=lambda: f"STOK_BUFFER_TRANSIT_{datetime.now().strftime('%d_%m_%Y_%H%M')}.xlsx"
    )
    def btn_dl_ll01_transit_stock():
        buf = io.BytesIO()
        df_export = pd.DataFrame(state.get_filtered_ll01_special_stock())
        if not df_export.empty:
            cols = [c for c in ['branch', 'tipe_bin', 'bin', 'sku', 'item_name', 'brand', 'variant', 'sub_kategori', 'qty'] if c in df_export.columns]
            df_export = df_export[cols]
        else:
            df_export = pd.DataFrame(columns=["branch", "tipe_bin", "bin", "sku", "item_name", "brand", "variant", "sub_kategori", "qty"])

        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            df_export.to_excel(writer, sheet_name='BUFFER_TRANSIT_STOCK', index=False)
        buf.seek(0)
        yield buf.getvalue()

    @reactive.Effect
    @reactive.event(input.change_ll01_single_branch)
    def _on_change_ll01_sa_br():
        state.ll01_single_adj_filter_branch.set(input.change_ll01_single_branch())

    @reactive.Effect
    @reactive.event(input.change_ll01_single_status)
    def _on_change_ll01_sa_st():
        state.ll01_single_adj_filter_status.set(input.change_ll01_single_status())

    @render.download(
        filename=lambda: f"SINGLE_ADJUSTMENT_{datetime.now().strftime('%d_%m_%Y_%H%M')}.xlsx"
    )
    def btn_dl_ll01_single_adj():
        buf = io.BytesIO()
        df_export = pd.DataFrame(state.get_filtered_single_adj_data())
        if not df_export.empty:
            cols = [c for c in ['ba_code', 'store_name', 'bin_code', 'barcode_sku', 'article_name', 'brand', 'size_variant', 'old_qty', 'new_qty', 'adjust_qty', 'cogs', 'status', 'note', 'creator', 'updated_at'] if c in df_export.columns]
            df_export = df_export[cols]
        else:
            df_export = pd.DataFrame(columns=["ba_code", "store_name", "bin_code", "barcode_sku", "article_name", "brand", "size_variant", "old_qty", "new_qty", "adjust_qty", "cogs", "status", "note", "creator", "updated_at"])

        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            df_export.to_excel(writer, sheet_name='SINGLE_ADJUSTMENT', index=False)
        buf.seek(0)
        yield buf.getvalue()

# ==========================================================================
    # EVENT HANDLER UNTUK GLOBAL FILTER WAREHOUSE ACTIVITY MONITOR
    # ==========================================================================
    @reactive.Effect
    @reactive.event(input.change_ll01_global_store)
    def _on_change_ll01_global_store():
        state.ll01_global_store.set(input.change_ll01_global_store())

    @reactive.Effect
    @reactive.event(input.change_ll01_global_dates)
    def _on_change_ll01_global_dates():
        data = input.change_ll01_global_dates() or {}
        state.ll01_global_tgl_start.set(data.get("start", ""))
        state.ll01_global_tgl_end.set(data.get("end", ""))

    @reactive.Effect
    @reactive.event(input.change_ll01_global_note)
    def _on_change_ll01_global_note():
        state.ll01_global_note.set(input.change_ll01_global_note())

    
# ==========================================================================
    # WAREHOUSE COMPLIANCE AUDIT CONTROLLERS & EVENT HANDLERS
    # ==========================================================================

    # 1. Update Hasil Item Checklist Live
# ==========================================================================
    # WAREHOUSE COMPLIANCE AUDIT: RENDER CHECKLIST TERISOLASI (ANTI-LONCAT)
    # ==========================================================================
# ==========================================================================
    # WAREHOUSE COMPLIANCE AUDIT - TABEL CHECKLIST (LIVE UPDATE SKOR & POIN)
    # ==========================================================================
    @render.ui
    def comp_checklist_container_ui():
        checklist_items = state.comp_audit_checklist()
        if not checklist_items:
            return ui.p("Data checklist kosong.", style="color: #718096; font-style: italic; padding: 1rem;")

        # Header persis foto screenshot Anda
        headers_chk = ["Area Audit", "ID", "Kriteria Audit", "Bobot", "Hasil Pemeriksaan", "Skor", "Poin Diraih", "Catatan / Bukti"]
        th_cells = [ui.tags.th(h, style="text-align: center;" if h in ["ID", "Bobot", "Hasil Pemeriksaan", "Skor", "Poin Diraih"] else "") for h in headers_chk]

        tr_chk_rows = []
        for idx, it in enumerate(checklist_items):
            cur_hasil = str(it.get("hasil", "Sesuai"))
            b = float(it.get("bobot", 1))
            catatan = str(it.get("catatan", ""))
            
            # Hitung nilai awal
            if cur_hasil == "Sesuai": skor_str, diraih = "100%", f"{b:.1f}"
            elif "Minor" in cur_hasil: skor_str, diraih = "50%", f"{(b * 0.5):.1f}"
            elif "Mayor" in cur_hasil: skor_str, diraih = "0%", "0.0"
            else: skor_str, diraih = "-", "-"

            # Dropdown kotak kuning Excel persis foto
            select_hasil = ui.tags.select(
                ui.tags.option("Sesuai", value="Sesuai", selected=(cur_hasil == "Sesuai")),
                ui.tags.option("NC Minor", value="NC Minor", selected=("Minor" in cur_hasil)),
                ui.tags.option("NC Mayor", value="NC Mayor", selected=("Mayor" in cur_hasil)),
                ui.tags.option("N/A", value="N/A", selected=(cur_hasil == "N/A")),
                id=f"chk_hasil_{idx}",
                onchange=f"window.updateCompRow({idx}, {b})",
                style="padding: 4px 8px; border-radius: 6px; font-weight: 800; font-size: 12px; cursor: pointer; border: 1.5px solid #CBD5E0;"
            )

            input_cat = ui.tags.input(
                id=f"chk_cat_{idx}", 
                type="text", 
                value=catatan, 
                placeholder="Catatan temuan...",
                onchange=f"window.updateCompRow({idx}, {b})",
                style="width: 100%; min-width: 180px; padding: 4px 8px; font-size: 12px; border: 1px solid #CBD5E0; border-radius: 6px;"
            )

            bobot_color = "#E53E3E" if b == 3 else ("#DD6B20" if b == 2 else "#4A5568")

            tr_chk_rows.append(ui.tags.tr(
                ui.tags.td(str(it.get("area")), style="font-weight: 600; font-size: 12px;"),
                ui.tags.td(ui.tags.code(str(it.get("id")), style="font-weight: bold; color: #2B6CB0;"), style="text-align: center;"),
                ui.tags.td(str(it.get("kriteria")), style="max-width: 320px; white-space: normal; font-size: 12.5px;"),
                ui.tags.td(f"{int(b)}", style=f"text-align: center; font-weight: 800; color: {bobot_color};"),
                ui.tags.td(select_hasil, style="text-align: center; background: #FEFCBF;"),
                # 👇 ID INI YANG MEMBUAT SKOR DAN POIN DIRAIS LANGSUNG BERUBAH DI SCREENSHOT
                ui.tags.td(skor_str, id=f"chk_skor_cell_{idx}", style="text-align: center; font-weight: 700;"),
                ui.tags.td(diraih, id=f"chk_diraih_cell_{idx}", style="text-align: right; font-weight: 800; color: #2B6CB0;"),
                ui.tags.td(input_cat)
            ))

        return ui.div(
            ui.tags.table(
                ui.tags.thead(ui.tags.tr(*th_cells)),
                ui.tags.tbody(*tr_chk_rows),
                class_="custom-clean-table", 
                style="width: 100%; border: 1px solid #CBD5E0; border-radius: 8px;"
            ),
            # Skrip otomatis: mengubah angka seketika & kirim ke Python di background
            ui.tags.script("""
                window.updateCompRow = function(idx, bobotVal) {
                    let selectEl = document.getElementById('chk_hasil_' + idx);
                    let catEl = document.getElementById('chk_cat_' + idx);
                    let skorEl = document.getElementById('chk_skor_cell_' + idx);
                    let diraihEl = document.getElementById('chk_diraih_cell_' + idx);

                    let val = selectEl ? selectEl.value : 'Sesuai';
                    let cat = catEl ? catEl.value : '';
                    let b = parseFloat(bobotVal) || 1.0;

                    // 1. Langsung ubah teks Skor dan Poin Diraih di layar (0 detik)
                    if (skorEl && diraihEl) {
                        if (val === 'Sesuai') {
                            skorEl.innerText = '100%';
                            diraihEl.innerText = b.toFixed(1);
                        } else if (val.includes('Minor')) {
                            skorEl.innerText = '50%';
                            diraihEl.innerText = (b * 0.5).toFixed(1);
                        } else if (val.includes('Mayor')) {
                            skorEl.innerText = '0%';
                            diraihEl.innerText = '0.0';
                        } else {
                            skorEl.innerText = '-';
                            diraihEl.innerText = '-';
                        }
                    }

                    // 2. Simpan nilai ke Python Shiny secara senyap
                    if (window.Shiny && window.Shiny.setInputValue) {
                        Shiny.setInputValue('comp_item_changed', {idx: idx, hasil: val, cat: cat}, {priority: 'event'});
                    }
                };
            """),
            style="overflow-x: auto; width: 100%; background: white; margin-bottom: 1rem;"
        )
    
    @reactive.Effect
    @reactive.event(input.comp_item_changed)
    def _on_comp_item_changed():
        d = input.comp_item_changed() or {}
        idx = d.get("idx", 0)
        hasil = d.get("hasil", "Sesuai")
        cat = d.get("cat", "")
        # Gunakan isolate agar tidak memicu render ulang halaman utama
        with reactive.isolate():
            state.update_compliance_item(idx, hasil, cat)

    # 2. Reset Default Items
    @reactive.Effect
    @reactive.event(input.btn_reset_comp_checklist)
    def _on_reset_comp():
        state.reset_compliance_checklist_defaults()
        ui.notification_show("Daftar periksa dikembalikan ke 27 butir standar WH-AUD-001.", type="message", duration=3)

    # 3. Tambah & Hapus CAPA
    @reactive.Effect
    @reactive.event(input.btn_add_comp_capa)
    def _on_add_comp_capa():
        d = input.btn_add_comp_capa() or {}
        succ, msg = state.add_compliance_capa(
            d.get("id_audit", "RCV-01"),
            d.get("uraian", ""),
            d.get("tingkat", "NC Minor"),
            d.get("akar", ""),
            d.get("tindakan", ""),
            d.get("pic", ""),
            d.get("due", "")
        )
        if succ:
            ui.notification_show(f"✅ {msg}", type="message", duration=3)
        else:
            ui.notification_show(f"⚠️ {msg}", type="warning", duration=4)

    @reactive.Effect
    @reactive.event(input.btn_delete_comp_capa)
    def _on_del_comp_capa():
        idx = input.btn_delete_comp_capa()
        state.delete_compliance_capa(idx)
        ui.notification_show("🗑️ Temuan CAPA berhasil dihapus.", type="message", duration=2)

    @reactive.Effect
    @reactive.event(input.btn_toggle_comp_capa)
    def _on_toggle_comp_capa():
        idx = input.btn_toggle_comp_capa()
        succ, msg = state.toggle_compliance_capa_status(idx)
        if succ:
            ui.notification_show(msg, type="message", duration=2)

    # 4. Simpan ke Supabase
    @reactive.Effect
    @reactive.event(input.btn_save_comp_audit_supabase)
    def _on_save_comp_supabase():
        meta = input.btn_save_comp_audit_supabase() or {}
        succ, msg = state.save_compliance_session_to_supabase(meta)
        ui.insert_ui(ui.tags.script("if (window.hideGlobalSpinner) window.hideGlobalSpinner();"), selector="head", where="beforeEnd")
        if succ:
            state.show_success_modal.set(True)
            ui.update_navs("comp_audit_navset_tab", selected="📂 5. RIWAYAT & ARSIP")
            ui.notification_show(msg, type="message", duration=5)
        else:
            state.error_modal_message.set(msg)
            state.show_error_modal.set(True)

    # 5. Download Excel WH-AUD-001
    @render.download(
        filename=lambda: f"WH_AUD_001_COMPLIANCE_{datetime.now().strftime('%d_%m_%Y_%H%M')}.xlsx"
    )
    def btn_dl_comp_excel():
        meta_dict = {
            "branch": input.comp_branch() if "comp_branch" in input else "Surabaya",
            "address": input.comp_address() if "comp_address" in input else "-",
            "lead": input.comp_lead() if "comp_lead" in input else "",
            "auditee": input.comp_auditee() if "comp_auditee" in input else "",
            "date": input.comp_date() if "comp_date" in input else datetime.now().strftime("%Y-%m-%d"),
            "type": input.comp_type() if "comp_type" in input else "Internal",
            "scope": input.comp_scope() if "comp_scope" in input else "Gudang Pusat (DC)",
            "doc_no": input.comp_doc_no() if "comp_doc_no" in input else "WH-AUD-001",
            "trading_period": input.comp_trading() if "comp_trading" in input else "Reguler"
        }
        content = state.generate_compliance_excel_pack(meta_dict)
        yield content

    # 6. Impor Excel Terisi
    @reactive.Effect
    @reactive.event(input.btn_import_comp_excel)
    def _on_import_comp_excel():
        f = input.upload_filled_comp_excel() if "upload_filled_comp_excel" in input else None
        if not f:
            ui.insert_ui(ui.tags.script("if (window.hideGlobalSpinner) window.hideGlobalSpinner();"), selector="head", where="beforeEnd")
            ui.notification_show("Pilih file Excel WH-AUD-001 terlebih dahulu!", type="warning", duration=4)
            return

        succ, msg = state.import_filled_compliance_excel(f)
        ui.insert_ui(ui.tags.script("if (window.hideGlobalSpinner) window.hideGlobalSpinner();"), selector="head", where="beforeEnd")
        if succ:
            ui.notification_show(msg, type="message", duration=4)
        else:
            ui.notification_show(msg, type="error", duration=4)

    # 7. Refresh & Hapus History
    @reactive.Effect
    @reactive.event(input.btn_refresh_comp_history)
    def _on_refresh_comp_hist():
        state.load_compliance_history()
        ui.notification_show("Riwayat audit kepatuhan telah dimuat ulang.", type="message", duration=2)

    @reactive.Effect
    @reactive.event(input.btn_delete_comp_history)
    def _on_del_comp_hist():
        a_id = input.btn_delete_comp_history()
        succ, msg = state.delete_compliance_session(a_id)
        ui.notification_show(f"🗑️ {msg}", type="message", duration=3)

    # ==========================================================================
    # 1. RENDER TABEL LOG TEMUAN & CAPA DI TAB 3 (AGAR MUNCUL SAAT DIKLIK TAMBAH)
    # ==========================================================================
    @render.ui
    def comp_capa_table_ui():
        capa_list = state.comp_audit_capa_list()
        if not capa_list:
            return ui.div(
                ui.p("Belum ada temuan ketidaksesuaian (CAPA) yang dicatat.", style="color: #718096; font-style: italic; text-align: center; padding: 1.5rem;"),
                style="background: #F8FAFC; border: 1px dashed #CBD5E0; border-radius: 8px;"
            )

        tr_capa = []
        for idx_cp, cp in enumerate(capa_list):
            c_status = cp.get("status", "Terbuka")
            is_done = (c_status == "Selesai")
            
            badge_stat = (
                ui.span("Selesai", style="background: #C6F6D5; color: #22543D; font-weight: 800; padding: 3px 8px; border-radius: 4px; font-size: 11px;")
                if is_done else 
                ui.span(c_status, style="background: #FED7D7; color: #9B2C2C; font-weight: 800; padding: 3px 8px; border-radius: 4px; font-size: 11px;")
            )

            btn_toggle = ui.tags.button(
                "Buka" if is_done else "Selesaikan",
                onclick=f"Shiny.setInputValue('btn_toggle_comp_capa', {idx_cp}, {{priority: 'event'}})",
                style="background: #EDF2F7; border: 1px solid #CBD5E0; font-size: 11px; padding: 3px 8px; border-radius: 4px; cursor: pointer; margin-right: 4px; font-weight: 600;"
            )
            btn_del = ui.tags.button(
                ui.tags.i(class_="fa-solid fa-trash", style="color: #E53E3E;"),
                onclick=f"Shiny.setInputValue('btn_delete_comp_capa', {idx_cp}, {{priority: 'event'}})",
                style="background: transparent; border: none; cursor: pointer; padding: 4px;"
            )

            tr_capa.append(ui.tags.tr(
                ui.tags.td(str(cp.get("id")), style="font-weight: bold; text-align: center;"),
                ui.tags.td(str(cp.get("tanggal"))),
                ui.tags.td(ui.tags.code(str(cp.get("id_audit")), style="color: #2B6CB0; font-weight: bold;")),
                ui.tags.td(str(cp.get("area"))),
                ui.tags.td(str(cp.get("uraian")), style="max-width: 250px; white-space: normal;"),
                ui.tags.td(str(cp.get("tingkat")), style="font-weight: 700; text-align: center;"),
                ui.tags.td(str(cp.get("akar"))),
                ui.tags.td(str(cp.get("tindakan"))),
                ui.tags.td(str(cp.get("pic"))),
                ui.tags.td(str(cp.get("due_date"))),
                ui.tags.td(badge_stat, style="text-align: center;"),
                ui.tags.td(ui.div(btn_toggle, btn_del, style="display: flex; align-items: center; justify-content: center;"))
            ))

        headers_capa = ["ID", "Tanggal", "Butir", "Area", "Uraian Temuan", "Tingkat", "Akar Masalah", "Tindakan CAPA", "PIC", "Batas Waktu", "Status", "Aksi"]
        th_list = [ui.tags.th(h, style="text-align: center;" if h in ["ID", "Tingkat", "Status", "Aksi"] else "") for h in headers_capa]

        return ui.div(
            ui.tags.table(
                ui.tags.thead(ui.tags.tr(*th_list)),
                ui.tags.tbody(*tr_capa),
                class_="custom-clean-table", style="width: 100%; border: 1px solid #CBD5E0; border-radius: 8px;"
            ),
            style="overflow-x: auto; background: white; margin-top: 1rem;"
        )

    # ==========================================================================
    # 2. RENDER KARTU RIWAYAT DI TAB 5 (DITAMPILKAN DARI SUPABASE)
    # ==========================================================================
    @render.ui
    def comp_history_cards_ui():
        histories = state.comp_audit_history_list()
        if not histories:
            return ui.div(
                ui.p("Belum ada riwayat audit kepatuhan yang tersimpan di Supabase.", style="color: #718096; font-style: italic; text-align: center; padding: 2rem;"),
                style="background: #F8FAFC; border: 1px dashed #CBD5E0; border-radius: 8px; margin-top: 1rem;"
            )

        h_cards = []
        for h in histories:
            h_id = h.get("id", "-")
            dt = str(h.get("audit_date", "-"))
            br = h.get("branch", "-")
            pct_val = h.get("score_pct", 0.0)
            grade_val = h.get("grade", "-")
            passed_val = h.get("passed", False)

            pass_badge = (
                ui.span("LULUS AUDIT", style="background: #C6F6D5; color: #22543D; font-weight: 800; padding: 3px 8px; border-radius: 4px; font-size: 11px;")
                if passed_val else 
                ui.span("BELUM LULUS", style="background: #FED7D7; color: #9B2C2C; font-weight: 800; padding: 3px 8px; border-radius: 4px; font-size: 11px;")
            )

            h_cards.append(ui.div(
                ui.div(
                    ui.div(
                        ui.div(
                            ui.span(h_id, style="font-weight: 800; font-size: 15px; color: #1A202C; margin-right: 8px;"),
                            ui.span(f"Tanggal: {dt}", style="background: #EDF2F7; color: #2D3748; font-weight: 700; font-size: 11px; padding: 3px 8px; border-radius: 4px; margin-right: 6px;"),
                            pass_badge,
                            style="display: flex; align-items: center; margin-bottom: 4px; flex-wrap: wrap; gap: 4px;"
                        ),
                        ui.p(f"Cabang: {br} • Skor: {pct_val}% ({grade_val}) • Lead Auditor: {h.get('lead_auditor', '-')}", style="margin: 0; font-size: 12px; color: #718096;")
                    ),
                    ui.div(
                        ui.tags.button(
                            ui.tags.i(class_="fa-solid fa-trash", style="margin-right: 4px;"), "Hapus",
                            onclick=f"Shiny.setInputValue('btn_delete_comp_history', '{h_id}', {{priority: 'event'}})",
                            style="background: #FFF5F5; color: #E53E3E; border: 1.5px solid #FEB2B2; padding: 6px 12px; border-radius: 6px; font-weight: 700; font-size: 12px; cursor: pointer;"
                        ),
                        style="display: flex; align-items: center;"
                    ),
                    style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;"
                ),
                style="background: white; border: 1.5px solid #CBD5E0; border-radius: 10px; padding: 1rem 1.25rem; margin-bottom: 0.85rem;"
            ))

        return ui.div(
            ui.div(
                ui.div(
                    ui.h4("📂 Riwayat Laporan Audit Kepatuhan (Supabase)", style="font-size: 15px; font-weight: 800; color: #1A202C; margin: 0 0 4px 0;"),
                    ui.p("Seluruh hasil kepatuhan gudang tersimpan otomatis dan dapat ditinjau kapan saja.", style="color: #718096; font-size: 13px; margin: 0;"),
                ),
                ui.tags.button(
                    ui.tags.i(class_="fa-solid fa-arrows-rotate", style="margin-right: 6px;"), "Refresh History",
                    onclick="Shiny.setInputValue('btn_refresh_comp_history', Math.random(), {priority: 'event'})",
                    style="background: #EDF2F7; color: #2D3748; border: 1.5px solid #CBD5E0; padding: 6px 14px; border-radius: 6px; font-weight: 700; font-size: 12px; cursor: pointer;"
                ),
                style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.25rem; flex-wrap: wrap; gap: 8px;"
            ),
            *h_cards,
            style="margin-top: 1rem;"
        )

    # ==========================================================================
    # MEMO PENGAJUAN: DIRECT SCRAPING & 2 MODEL PDF (TANPA APPROVAL)
    # ==========================================================================

    # 1. TIMER OTOMATIS SCRAPING SETIAP 5 MENIT (300 DETIK)
    # 1. TIMER OTOMATIS SCRAPING SETIAP 15 MENIT (900 DETIK) DI BACKGROUND THREAD
    @reactive.Effect
    def _auto_scrape_markom_timer():
        reactive.invalidate_later(900)  # 900 detik = 15 menit
        with reactive.isolate():
            if state.logged_in():
                import threading
                threading.Thread(target=state.sync_markom_event_requests, kwargs={"silent": True}, daemon=True).start()

    # 2. TRIGGER MANUAL SYNC DARI TOMBOL TAB 1
    @reactive.Effect
    @reactive.event(input.btn_trigger_sync_markom_event)
    def _manual_sync_markom_event():
        succ, msg = state.sync_markom_event_requests(silent=False)
        ui.insert_ui(ui.tags.script("if (window.hideGlobalSpinner) window.hideGlobalSpinner();"), selector="head", where="beforeEnd")
        if succ:
            state.show_success_modal.set(True)
            ui.notification_show(f"✅ {msg}", type="message", duration=4)
        else:
            ui.notification_show(f"ℹ️ {msg}", type="warning", duration=4)

# ==========================================================================
    # 1. TAB 1: DETAIL SCRAPING (FAST PAGINATION 10 DATA + DOWNLOAD EXCEL)
    # ==========================================================================
    @render.ui
    def memo_scraped_items_detail_table_ui():
        items = state.memo_scraped_event_items()
        if not items:
            return ui.div(
                ui.p("Belum ada data permintaan barang aktif (Note: 'EVENT', 'HADIAH', atau 'GIFT').", style="color: #718096; font-style: italic; text-align: center; padding: 2rem;"),
                style="background: white; border-radius: 10px; border: 1px dashed #CBD5E0;"
            )

        # Urutkan berdasarkan waktu lengkap (terbaru di paling atas)
        def parse_full_dt(it):
            try:
                return pd.to_datetime(it.get("tanggal", ""))
            except Exception:
                return pd.Timestamp.min

        items_sorted = sorted(items, key=parse_full_dt, reverse=True)

        headers = ["NO", "UNIQUE ID", "WAKTU REQ", "PIC", "KETERANGAN", "BIN PICK", "SKU", "NAMA ARTIKEL", "QTY", "HARGA BELI", "SUBTOTAL"]
        rows = []
        tot_qty = 0
        tot_nominal = 0

        for idx, it in enumerate(items_sorted, start=1):
            q = safe_int(it.get("qty", 1), 1)
            cogs = safe_int(it.get("cogs", 0), 0)
            subtot = safe_int(it.get("subtotal", 0), 0)
            if subtot == 0 and cogs > 0:
                subtot = q * cogs

            tot_qty += q
            tot_nominal += subtot

            rows.append([
                str(idx),
                str(it.get("id", "-")),
                str(it.get("tanggal", "-")),
                str(it.get("pic", "-")),
                str(it.get("keterangan", "-")),
                str(it.get("bin", "-")),
                str(it.get("sku", "-")),
                str(it.get("item_name", "-")),
                str(q),
                f"Rp {cogs:,}",
                f"Rp {subtot:,}"
            ])

        return ui.div(
            ui.div(
                dark_metric_box("📦 TOTAL BARIS EVENT", f"{len(items_sorted):,} ITEM", "#3182CE"),
                dark_metric_box("🔢 TOTAL QTY BARANG", f"{tot_qty:,} PCS", "#C5A059"),
                dark_metric_box("💰 TOTAL VALUASI HARGA BELI", f"Rp {tot_nominal:,}", "#10B981"),
                style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; width: 100%; margin-bottom: 1.25rem;"
            ),
            ui.div(
                ui.div(
                    ui.h4("📋 Daftar Rincian Barang Markom", style="font-size: 15px; font-weight: 800; color: #1A202C; margin: 0;"),
                    ui.download_button(
                        "btn_dl_memo_scraped_excel",
                        ui.tags.span(ui.tags.i(class_="fa-solid fa-file-excel", style="margin-right: 6px; font-size: 13px;"), "DOWNLOAD EXCEL (.XLSX)"),
                        style="background: #10B981; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 7px 14px; cursor: pointer; font-size: 12px;"
                    ),
                    style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 0.75rem; flex-wrap: wrap; gap: 8px;"
                ),
                render_clean_table(headers, rows, "tbl_memo_scraped_fast"),
                style="background: white; border-radius: 12px; border: 1px solid #E2E8F0; padding: 1.25rem;"
            )
        )

    @render.download(
        filename=lambda: f"DETAIL_SCRAPING_MARKOM_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    )
    def btn_dl_memo_scraped_excel():
        items = state.memo_scraped_event_items()
        buf = io.BytesIO()
        df_dl = pd.DataFrame(items)
        if not df_dl.empty:
            cols_map = {
                "id": "UNIQUE ID", "tanggal": "TANGGAL", "pic": "PIC", "keterangan": "KETERANGAN",
                "bin": "BIN PICK", "sku": "SKU", "item_name": "NAMA ARTIKEL", "qty": "QTY",
                "cogs": "HARGA BELI", "subtotal": "SUBTOTAL"
            }
            df_dl = df_dl.rename(columns=cols_map)
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            df_dl.to_excel(writer, sheet_name='SCRAPING_MARKOM', index=False)
        buf.seek(0)
        yield buf.getvalue()

    # ==========================================================================
    # 2. FILTER TANGGAL MEMO
    # ==========================================================================
    @reactive.Effect
    @reactive.event(input.change_memo_filter_tgl_start)
    def _on_memo_tgl_start():
        if hasattr(state, "memo_filter_tgl_start"):
            state.memo_filter_tgl_start.set(input.change_memo_filter_tgl_start())

    @reactive.Effect
    @reactive.event(input.change_memo_filter_tgl_end)
    def _on_memo_tgl_end():
        if hasattr(state, "memo_filter_tgl_end"):
            state.memo_filter_tgl_end.set(input.change_memo_filter_tgl_end())

    @reactive.Effect
    @reactive.event(input.btn_reset_memo_filter_tgl)
    def _on_reset_memo_tgl():
        if hasattr(state, "memo_filter_tgl_start"):
            state.memo_filter_tgl_start.set("")
        if hasattr(state, "memo_filter_tgl_end"):
            state.memo_filter_tgl_end.set("")

    def _render_memo_date_filter_bar(total_count: int, label_suffix: str):
        tgl_s = state.memo_filter_tgl_start() if hasattr(state, "memo_filter_tgl_start") else ""
        tgl_e = state.memo_filter_tgl_end() if hasattr(state, "memo_filter_tgl_end") else ""
        return ui.div(
            ui.div(
                ui.div(
                    ui.span("📅 Tanggal Awal:", style="font-size: 11px; font-weight: 800; color: #4A5568; margin-right: 4px;"),
                    ui.tags.input(
                        type="date", id="memo_filter_tgl_start_in", value=tgl_s,
                        onchange="Shiny.setInputValue('change_memo_filter_tgl_start', this.value, {priority: 'event'})",
                        style="padding: 4px 8px; border-radius: 6px; border: 1.5px solid #CBD5E0; font-weight: 700; font-size: 12px; background: white;"
                    ),
                    style="display: flex; align-items: center;"
                ),
                ui.div(
                    ui.span("📅 Tanggal Akhir:", style="font-size: 11px; font-weight: 800; color: #4A5568; margin-left: 8px; margin-right: 4px;"),
                    ui.tags.input(
                        type="date", id="memo_filter_tgl_end_in", value=tgl_e,
                        onchange="Shiny.setInputValue('change_memo_filter_tgl_end', this.value, {priority: 'event'})",
                        style="padding: 4px 8px; border-radius: 6px; border: 1.5px solid #CBD5E0; font-weight: 700; font-size: 12px; background: white;"
                    ),
                    style="display: flex; align-items: center;"
                ),
                ui.tags.button(
                    "🔄 Reset",
                    onclick="Shiny.setInputValue('btn_reset_memo_filter_tgl', Math.random(), {priority: 'event'})",
                    style="background: #EDF2F7; color: #4A5568; border: 1.5px solid #CBD5E0; border-radius: 6px; font-weight: 700; font-size: 12px; padding: 4px 10px; cursor: pointer; margin-left: 6px;"
                ),
                style="display: flex; align-items: center; flex-wrap: wrap; gap: 4px;"
            ),
            ui.span(f"Ditemukan {total_count} Memo {label_suffix}", style="font-weight: 800; font-size: 12px; color: #2B6CB0;"),
            style="display: flex; justify-content: space-between; align-items: center; background: white; padding: 10px 16px; border-radius: 8px; border: 1.5px solid #CBD5E0; margin-bottom: 1rem; flex-wrap: wrap; gap: 8px;"
        )

    # Helper pembaca data (MARKOM vs LOGISTIK vs DONE)
    def _get_memos_by_category(category: str):
        memos = state.memo_list()
        start = str(state.memo_filter_tgl_start()).strip() if hasattr(state, "memo_filter_tgl_start") else ""
        end = str(state.memo_filter_tgl_end()).strip() if hasattr(state, "memo_filter_tgl_end") else ""

        res = []
        for m in memos:
            st = str(m.get("status_adj", "PENDING")).upper().strip()

            if category == "MARKOM":
                # Belum request adjustment
                if st in ["REQUESTED", "DONE"]:
                    continue
            elif category == "LOGISTIK":
                # Sudah request adjustment, menunggu eksekusi
                if st != "REQUESTED":
                    continue
            elif category == "DONE":
                # Sudah selesai dieksekusi
                if st != "DONE":
                    continue

            tgl = str(m.get("tanggal", ""))[:10]
            if start and tgl < start: continue
            if end and tgl > end: continue
            res.append(m)
        return res

    def _render_single_memo_card(m: dict, stage: str):
        m_id = m.get("id", "-")
        divisi = m.get("divisi", "MARKOM")
        tujuan = m.get("tujuan", "-")
        
        items = m.get("items", [])
        if isinstance(items, str):
            import json
            try: items = json.loads(items)
            except: items = []
        items_cnt = len(items)

        # 🌟 SOLUSI POIN 4: Jika nominal di memo 0, hitung langsung dari item-item di dalamnya!
        nominal = safe_int(m.get("nominal", 0), 0)
        if nominal == 0 and items:
            calculated_subtotal = sum(
                safe_int(x.get("subtotal", 0)) or (safe_int(x.get("qty", 1), 1) * safe_int(x.get("cogs", 0), 0))
                for x in items
            )
            if calculated_subtotal > 0:
                nominal = calculated_subtotal

        # 1. MARKOM SUB-TAB
        if stage == "MARKOM":
            badge_status = ui.span("BELUM REQUEST", style="background: #FEFCBF; color: #744210; font-weight: 800; font-size: 10.5px; padding: 2px 8px; border-radius: 4px;")
            btn_action = ui.tags.button(
                ui.tags.i(class_="fa-solid fa-paper-plane", style="margin-right: 5px;"), "REQUEST ADJUSTMENT",
                onclick=f"window.showGlobalSpinner(); Shiny.setInputValue('btn_request_memo_adj', '{m_id}', {{priority: 'event'}})",
                style="background: linear-gradient(135deg, #DD6B20 0%, #C05621 100%); color: white; border: none; padding: 7px 13px; border-radius: 6px; font-weight: 800; font-size: 11.5px; cursor: pointer; box-shadow: 0 2px 6px rgba(221,107,32,0.3);"
            )
            # Terdapat tombol PDF di Tab 2
            buttons_group = [
                ui.tags.button(
                    ui.tags.i(class_="fa-solid fa-eye", style="margin-right: 4px;"), "DETAIL",
                    onclick=f"Shiny.setInputValue('btn_open_memo_detail_modal', '{m_id}', {{priority: 'event'}})",
                    style="background: #3182CE; color: white; border: none; padding: 7px 11px; border-radius: 6px; font-weight: 800; font-size: 11.5px; cursor: pointer;"
                ),
                ui.tags.button(
                    ui.tags.i(class_="fa-solid fa-file-invoice-dollar", style="margin-right: 4px;"), "MEMO KAS (PDF)",
                    onclick=f"Shiny.setInputValue('btn_prepare_pdf_memo_kas', '{m_id}', {{priority: 'event'}})",
                    style="background: linear-gradient(135deg, #E50914 0%, #B20710 100%); color: white; border: none; padding: 7px 11px; border-radius: 6px; font-weight: 800; font-size: 11.5px; cursor: pointer;"
                ),
                ui.tags.button(
                    ui.tags.i(class_="fa-solid fa-file-lines", style="margin-right: 4px;"), "PENGAJUAN (PDF)",
                    onclick=f"Shiny.setInputValue('btn_prepare_pdf_memo_std', '{m_id}', {{priority: 'event'}})",
                    style="background: #2D3748; color: white; border: none; padding: 7px 11px; border-radius: 6px; font-weight: 700; font-size: 11.5px; cursor: pointer;"
                ),
                btn_action,
                ui.tags.button(
                    ui.tags.i(class_="fa-solid fa-trash", style="color: #E53E3E;"),
                    onclick=f"Shiny.setInputValue('btn_open_del_memo_modal', '{m_id}', {{priority: 'event'}})",
                    style="background: #FFF5F5; border: 1px solid #FEB2B2; padding: 7px 10px; border-radius: 6px; cursor: pointer;"
                )
            ]
            nominal_color = "#E50914"

        # 2. LOGISTIK SUB-TAB
        elif stage == "LOGISTIK":
            badge_status = ui.span("MENUNGGU EKSEKUSI ADJUSTMENT", style="background: #BEE3F8; color: #2B6CB0; font-weight: 800; font-size: 10.5px; padding: 2px 8px; border-radius: 4px;")
            btn_action = ui.tags.button(
                ui.tags.i(class_="fa-solid fa-check-double", style="margin-right: 5px;"), "DONE ADJUSTMENT",
                onclick=f"window.showGlobalSpinner(); Shiny.setInputValue('btn_mark_memo_done', '{m_id}', {{priority: 'event'}})",
                style="background: linear-gradient(135deg, #10B981 0%, #059669 100%); color: white; border: none; padding: 7px 13px; border-radius: 6px; font-weight: 800; font-size: 11.5px; cursor: pointer; box-shadow: 0 2px 6px rgba(16,185,129,0.3);"
            )
            # Terdapat tombol PDF di Tab 2
            buttons_group = [
                ui.tags.button(
                    ui.tags.i(class_="fa-solid fa-eye", style="margin-right: 4px;"), "DETAIL",
                    onclick=f"Shiny.setInputValue('btn_open_memo_detail_modal', '{m_id}', {{priority: 'event'}})",
                    style="background: #3182CE; color: white; border: none; padding: 7px 11px; border-radius: 6px; font-weight: 800; font-size: 11.5px; cursor: pointer;"
                ),
                ui.tags.button(
                    ui.tags.i(class_="fa-solid fa-file-invoice-dollar", style="margin-right: 4px;"), "MEMO KAS (PDF)",
                    onclick=f"Shiny.setInputValue('btn_prepare_pdf_memo_kas', '{m_id}', {{priority: 'event'}})",
                    style="background: linear-gradient(135deg, #E50914 0%, #B20710 100%); color: white; border: none; padding: 7px 11px; border-radius: 6px; font-weight: 800; font-size: 11.5px; cursor: pointer;"
                ),
                ui.tags.button(
                    ui.tags.i(class_="fa-solid fa-file-lines", style="margin-right: 4px;"), "PENGAJUAN (PDF)",
                    onclick=f"Shiny.setInputValue('btn_prepare_pdf_memo_std', '{m_id}', {{priority: 'event'}})",
                    style="background: #2D3748; color: white; border: none; padding: 7px 11px; border-radius: 6px; font-weight: 700; font-size: 11.5px; cursor: pointer;"
                ),
                btn_action,
                ui.tags.button(
                    ui.tags.i(class_="fa-solid fa-trash", style="color: #E53E3E;"),
                    onclick=f"Shiny.setInputValue('btn_open_del_memo_modal', '{m_id}', {{priority: 'event'}})",
                    style="background: #FFF5F5; border: 1px solid #FEB2B2; padding: 7px 10px; border-radius: 6px; cursor: pointer;"
                )
            ]
            nominal_color = "#E50914"

        # 3. TAB 3: DONE ADJUSTMENT (TANPA TOMBOL DOWNLOAD PDF SESUAI INSTRUKSI)
        else:
            done_at_str = m.get("done_at", "-")
            badge_status = ui.span(f"✅ DONE ({done_at_str})", style="background: #C6F6D5; color: #22543D; font-weight: 800; font-size: 10.5px; padding: 2px 6px; border-radius: 4px;")
            buttons_group = [
                ui.tags.button(
                    ui.tags.i(class_="fa-solid fa-eye", style="margin-right: 4px;"), "DETAIL",
                    onclick=f"Shiny.setInputValue('btn_open_memo_detail_modal', '{m_id}', {{priority: 'event'}})",
                    style="background: #3182CE; color: white; border: none; padding: 7px 11px; border-radius: 6px; font-weight: 800; font-size: 11.5px; cursor: pointer;"
                ),
                ui.tags.button(
                    ui.tags.i(class_="fa-solid fa-rotate-left", style="margin-right: 4px;"), "Buka Kembali",
                    onclick=f"window.showGlobalSpinner(); Shiny.setInputValue('btn_revert_memo_done', '{m_id}', {{priority: 'event'}})",
                    style="background: #EDF2F7; color: #4A5568; border: 1.5px solid #CBD5E0; padding: 6px 11px; border-radius: 6px; font-weight: 700; font-size: 11.5px; cursor: pointer;"
                ),
                ui.tags.button(
                    ui.tags.i(class_="fa-solid fa-trash", style="color: #E53E3E;"),
                    onclick=f"Shiny.setInputValue('btn_open_del_memo_modal', '{m_id}', {{priority: 'event'}})",
                    style="background: #FFF5F5; border: 1px solid #FEB2B2; padding: 7px 10px; border-radius: 6px; cursor: pointer;"
                )
            ]
            nominal_color = "#10B981"

        return ui.div(
            ui.div(
                ui.div(
                    ui.div(
                        ui.span(m_id, style="font-weight: 800; font-size: 14px; color: #1A202C; margin-right: 8px;"),
                        ui.span(f"Tanggal: {m.get('tanggal')}", style="background: #EDF2F7; color: #4A5568; font-weight: 700; font-size: 11px; padding: 2px 6px; border-radius: 4px; margin-right: 6px;"),
                        badge_status,
                        style="display: flex; align-items: center; margin-bottom: 4px; flex-wrap: wrap; gap: 4px;"
                    ),
                    ui.p(f"Pengaju: {m.get('diajukan_oleh')} • Divisi: {divisi} • Keperluan: {tujuan} ({items_cnt} Barang)", style="margin: 0; font-size: 12px; color: #718096;"),
                    style="flex: 1;"
                ),
                ui.div(
                    ui.span(f"Total: Rp {nominal:,}", style=f"font-weight: 800; font-size: 14px; color: {nominal_color}; margin-right: 10px;"),
                    *buttons_group,
                    style="display: flex; align-items: center; gap: 5px; flex-wrap: wrap;"
                ),
                style="display: flex; justify-content: space-between; align-items: center; background: white; border: 1.5px solid #CBD5E0; border-radius: 8px; padding: 12px 16px; margin-bottom: 0.75rem;"
            )
        )

    # ==========================================================================
    # 3. TAB 2 CONTAINER: MEMILIKI 2 SUB-TAB (MARKOM & LOGISTIK)
    # ==========================================================================
    # ==========================================================================
    # TAB 2 CONTAINER: KERANGKA SUB-TAB DIBUAT STATIS (ANTI-LONCAT KE MARKOM)
    # ==========================================================================
    @render.ui
    def memo_tab2_subtabs_container_ui():
        # Kerangka tabset dibuat statis sekali saja (tidak akan recreate saat status memo berubah)
        return ui.div(
            ui.output_ui("memo_tab2_filter_bar_ui"),
            ui.navset_card_tab(
                ui.nav_panel("📢 MARKOM", ui.output_ui("memo_subtab_markom_content_ui"), value="SUB_MARKOM"),
                ui.nav_panel("🚚 LOGISTIK", ui.output_ui("memo_subtab_logistik_content_ui"), value="SUB_LOGISTIK"),
                id="memo_subtabs_navset"
            )
        )

    # 1. Baris Filter Tanggal Tab 2
    @render.ui
    def memo_tab2_filter_bar_ui():
        m_markom = _get_memos_by_category("MARKOM")
        m_logistik = _get_memos_by_category("LOGISTIK")
        total_pending = len(m_markom) + len(m_logistik)
        return _render_memo_date_filter_bar(total_pending, "Pending (Markom & Logistik)")

    # 2. Konten Kartu Khusus Sub-tab Markom
    @render.ui
    def memo_subtab_markom_content_ui():
        m_markom = _get_memos_by_category("MARKOM")
        cards_markom = [_render_single_memo_card(m, "MARKOM") for m in m_markom]
        if not cards_markom:
            return ui.div(
                ui.p("Tidak ada memo di antrean Markom (Semua sudah diajukan).", style="color: #718096; font-style: italic; text-align: center; padding: 2rem;"),
                style="background: white; border-radius: 8px; border: 1px dashed #CBD5E0; margin-top: 0.5rem;"
            )
        return ui.div(*cards_markom, style="padding: 0.75rem 0;")

    # 3. Konten Kartu Khusus Sub-tab Logistik
    @render.ui
    def memo_subtab_logistik_content_ui():
        m_logistik = _get_memos_by_category("LOGISTIK")
        cards_logistik = [_render_single_memo_card(m, "LOGISTIK") for m in m_logistik]
        if not cards_logistik:
            return ui.div(
                ui.p("Tidak ada memo di antrean Logistik (Menunggu Eksekusi Adjustment).", style="color: #718096; font-style: italic; text-align: center; padding: 2rem;"),
                style="background: white; border-radius: 8px; border: 1px dashed #CBD5E0; margin-top: 0.5rem;"
            )
        return ui.div(*cards_logistik, style="padding: 0.75rem 0;")


    # ==========================================================================
    # 4. TAB 3: DONE ADJUSTMENT (TANPA TOMBOL DOWNLOAD PDF)
    # ==========================================================================
    @render.ui
    def memo_done_table_ui():
        done_memos = _get_memos_by_category("DONE")
        filter_bar = _render_memo_date_filter_bar(len(done_memos), "Selesai (Done)")

        if not done_memos:
            return ui.div(
                filter_bar,
                ui.div(
                    ui.p("Belum ada memo yang ditandai Done Adjustment. Klik tombol 'DONE ADJUSTMENT' pada sub-tab Logistik untuk memindahkan dokumen ke sini.", style="color: #718096; font-style: italic; text-align: center; padding: 2rem;"),
                    style="background: white; border-radius: 10px; border: 1px dashed #CBD5E0;"
                )
            )

        cards = [_render_single_memo_card(m, "DONE") for m in done_memos]

        return ui.div(
            filter_bar,
            *cards
        )

    # ==========================================================================
    # 5. LISTENERS PINDAH STATUS (REQUEST -> LOGISTIK -> DONE -> REVERT)
    # ==========================================================================
    # ==========================================================================
    # 3. EVENT HANDLERS: STATUS PINDAH DENGAN GEMBOK POSISI SUB-TAB
    # ==========================================================================
    @reactive.Effect
    @reactive.event(input.btn_request_memo_adj)
    def _on_request_memo_adj():
        m_id = input.btn_request_memo_adj()
        try:
            memos = list(state.memo_list())
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            for m in memos:
                if m.get("id") == m_id:
                    m["status_adj"] = "REQUESTED"
                    m["requested_at"] = now_str
                    break
            client = get_supabase()
            if client:
                client.table("memo_pengajuan").update({
                    "status_adj": "REQUESTED",
                    "requested_at": now_str
                }).in_("id", [m_id]).execute()
            
            state.memo_list.set(memos)
            succ, msg = True, f"Memo {m_id} dipindahkan ke Sub-tab LOGISTIK!"
        except Exception as e:
            succ, msg = False, str(e)

        ui.insert_ui(ui.tags.script("if (window.hideGlobalSpinner) window.hideGlobalSpinner();"), selector="head", where="beforeEnd")
        if succ:
            ui.notification_show(f"🚀 {msg}", type="message", duration=4)
        else:
            ui.notification_show(f"⚠️ {msg}", type="warning", duration=4)

    @reactive.Effect
    @reactive.event(input.btn_mark_memo_done)
    def _on_mark_memo_done():
        m_id = input.btn_mark_memo_done()
        try:
            memos = list(state.memo_list())
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            for m in memos:
                if m.get("id") == m_id:
                    m["status_adj"] = "DONE"
                    m["done_at"] = now_str
                    break
            client = get_supabase()
            if client:
                client.table("memo_pengajuan").update({
                    "status_adj": "DONE",
                    "done_at": now_str
                }).in_("id", [m_id]).execute()
            
            state.memo_list.set(memos)
            succ, msg = True, f"Memo {m_id} selesai adjustment dan dipindahkan ke Tab 3 (Done)!"
        except Exception as e:
            succ, msg = False, str(e)

        ui.insert_ui(ui.tags.script("if (window.hideGlobalSpinner) window.hideGlobalSpinner();"), selector="head", where="beforeEnd")
        if succ:
            # 🌟 GEMBOK: Tetap pertahankan user di sub-tab LOGISTIK (tidak loncat ke Markom)
            ui.update_navs("memo_subtabs_navset", selected="SUB_LOGISTIK")
            ui.notification_show(f"✅ {msg}", type="message", duration=4)
        else:
            ui.notification_show(f"⚠️ {msg}", type="warning", duration=4)

    @reactive.Effect
    @reactive.event(input.btn_revert_memo_done)
    def _on_revert_memo_done():
        m_id = input.btn_revert_memo_done()
        try:
            memos = list(state.memo_list())
            for m in memos:
                if m.get("id") == m_id:
                    m["status_adj"] = "REQUESTED"
                    m["done_at"] = None
                    break
            client = get_supabase()
            if client:
                client.table("memo_pengajuan").update({
                    "status_adj": "REQUESTED",
                    "done_at": None
                }).in_("id", [m_id]).execute()
            
            state.memo_list.set(memos)
            succ, msg = True, f"Memo {m_id} dikembalikan ke Sub-tab Logistik!"
        except Exception as e:
            succ, msg = False, str(e)

        ui.insert_ui(ui.tags.script("if (window.hideGlobalSpinner) window.hideGlobalSpinner();"), selector="head", where="beforeEnd")
        if succ:
            ui.notification_show(f"↩️ {msg}", type="message", duration=3)
        else:
            ui.notification_show(f"⚠️ {msg}", type="warning", duration=4)
# ==========================================================================
    # MODAL BUKA DETAIL MEMO DI WEB (YANG SEBELUMNYA HILANG)
    # ==========================================================================
    @reactive.Effect
    @reactive.event(input.btn_open_memo_detail_modal)
    def _open_memo_detail():
        m_id = input.btn_open_memo_detail_modal()
        target = next((m for m in state.memo_list() if m.get("id") == m_id), None)
        if not target:
            ui.notification_show("Data memo tidak ditemukan!", type="error")
            return

        items = target.get("items", [])
        if isinstance(items, str):
            import json
            try: items = json.loads(items)
            except: items = []

        item_rows = []
        tot_qty = 0
        tot_sub = 0
        for idx, it in enumerate(items, start=1):
            q = safe_int(it.get("qty", 1), 1)
            cogs = safe_int(it.get("cogs", 0), 0)
            subtot = safe_int(it.get("subtotal", q * cogs), q * cogs)
            tot_qty += q
            tot_sub += subtot

            item_rows.append(ui.tags.tr(
                ui.tags.td(str(idx), style="text-align: center; font-weight: bold;"),
                ui.tags.td(ui.tags.code(str(it.get("sku", "-")), style="font-weight: bold; color: #2B6CB0;")),
                ui.tags.td(str(it.get("item_name", "-")), style="max-width: 280px; white-space: normal;"),
                ui.tags.td(str(q), style="text-align: center; font-weight: bold;"),
                ui.tags.td(f"Rp {cogs:,}", style="text-align: right;"),
                ui.tags.td(f"Rp {subtot:,}", style="text-align: right; font-weight: 800; color: #10B981;")
            ))

        ui.modal_show(ui.modal(
            ui.div(
                ui.div(
                    ui.span(f"📄 Nomor Memo: {target.get('id')}", style="font-size: 14px; font-weight: 800; color: #1A202C; display: block;"),
                    ui.span(f"👤 Pengaju: {target.get('diajukan_oleh')} • Tanggal: {target.get('tanggal')}", style="font-size: 12px; color: #4A5568; display: block; margin-top: 2px;"),
                    ui.span(f"📌 Keperluan: {target.get('tujuan')}", style="font-size: 12px; font-weight: 700; color: #C53030; display: block; margin-top: 2px;"),
                    style="background: #EDF2F7; padding: 12px 16px; border-radius: 8px; margin-bottom: 1rem;"
                ),
                ui.div(
                    ui.tags.table(
                        ui.tags.thead(ui.tags.tr(
                            ui.tags.th("NO", style="text-align: center;"),
                            ui.tags.th("SKU"),
                            ui.tags.th("NAMA ARTIKEL"),
                            ui.tags.th("QTY", style="text-align: center;"),
                            ui.tags.th("HARGA BELI", style="text-align: right;"),
                            ui.tags.th("SUBTOTAL", style="text-align: right;")
                        )),
                        ui.tags.tbody(*item_rows) if item_rows else ui.tags.tr(
                            ui.tags.td("Rincian barang memo ini kosong.", colspan=6, style="text-align: center; padding: 1.5rem; color: #718096;")
                        ),
                        class_="custom-clean-table", style="width: 100%; border: 1px solid #CBD5E0; border-radius: 8px;"
                    ),
                    style="max-height: 400px; overflow-y: auto;"
                ),
                ui.div(
                    ui.span(f"Total Qty: {tot_qty:,} Pcs | Grand Total: Rp {tot_sub:,}", style="font-weight: 800; font-size: 14px; color: #E50914;"),
                    style="display: flex; justify-content: flex-end; margin-top: 10px;"
                )
            ),
            title=f"📋 Detail Memo Pengajuan: {m_id}",
            size="l",
            easy_close=True,
            footer=ui.modal_button("Tutup", class_="btn-page-nav")
        ))
    # ==========================================================================
    # 6. POP-UP MODAL DOWNLOAD PDF (ANTI-GAGAL / ANTI-KORUP)
    # ==========================================================================
    def _open_memo_pdf_modal(target: dict, doc_title: str):
        m_id = target.get("id", "-")
        nom = safe_int(target.get("nominal", 0), 0)
        tujuan = target.get("tujuan", "-")

        ui.modal_show(ui.modal(
            ui.div(
                ui.div(
                    ui.tags.i(class_="fa-solid fa-file-pdf", style="font-size: 46px; color: #E50914; margin-bottom: 10px;"),
                    ui.h3(f"Cetak {doc_title}", style="font-size: 17px; font-weight: 800; color: #1A202C; margin: 0 0 6px 0;"),
                    ui.p(f"Nomor Dokumen: {m_id}", style="font-size: 13px; font-weight: bold; color: #2B6CB0; margin-bottom: 2px;"),
                    ui.p(f"Pengaju: {target.get('diajukan_oleh', '-')} • Total: Rp {nom:,}", style="font-size: 12px; color: #4A5568; margin-bottom: 4px;"),
                    ui.p(f"Keperluan: {tujuan}", style="font-size: 12px; color: #718096; margin-bottom: 18px;"),
                    ui.download_button(
                        "btn_dl_memo_pdf_modal",
                        ui.tags.span(ui.tags.i(class_="fa-solid fa-cloud-arrow-down", style="margin-right: 8px; font-size: 15px;"), f"DOWNLOAD {doc_title}"),
                        style="background: linear-gradient(135deg, #10B981 0%, #059669 100%); color: white; font-weight: 800; border-radius: 8px; border: none; padding: 12px 24px; font-size: 13px; cursor: pointer; width: 100%; box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);"
                    ),
                    style="text-align: center; padding: 1rem 0.5rem;"
                )
            ),
            title="📄 Download Dokumen PDF",
            easy_close=True,
            footer=ui.modal_button("Tutup", class_="btn-page-nav")
        ))

    @reactive.Effect
    @reactive.event(input.btn_prepare_pdf_memo_kas)
    def _prep_memo_kas():
        m_id = input.btn_prepare_pdf_memo_kas()
        matches = [m for m in state.memo_list() if m.get("id") == m_id]
        if matches:
            target = {**matches[0], "_pdf_mode": "KAS"}
            state.memo_selected_for_pdf.set(target)
            state._last_memo_pdf_data = target
            _open_memo_pdf_modal(target, "MEMO KAS (PDF)")

    @reactive.Effect
    @reactive.event(input.btn_prepare_pdf_memo_std)
    def _prep_memo_std():
        m_id = input.btn_prepare_pdf_memo_std()
        matches = [m for m in state.memo_list() if m.get("id") == m_id]
        if matches:
            target = {**matches[0], "_pdf_mode": "STD"}
            state.memo_selected_for_pdf.set(target)
            state._last_memo_pdf_data = target
            _open_memo_pdf_modal(target, "SURAT PENGAJUAN (PDF)")

    @render.download(
        filename=lambda: f"MEMO_KAS_{str((state.memo_selected_for_pdf() or getattr(state, '_last_memo_pdf_data', {})).get('id', 'DOC')).replace('/', '_')}.pdf" if (state.memo_selected_for_pdf() or getattr(state, '_last_memo_pdf_data', {})).get("_pdf_mode") == "KAS" else f"MEMO_PENGAJUAN_{str((state.memo_selected_for_pdf() or getattr(state, '_last_memo_pdf_data', {})).get('id', 'DOC')).replace('/', '_')}.pdf"
    )
    def btn_dl_memo_pdf_modal():
        sel = state.memo_selected_for_pdf()
        if not sel and hasattr(state, "_last_memo_pdf_data"):
            sel = state._last_memo_pdf_data
        if not sel:
            yield b""
            return

        import json
        memo_clean = dict(sel)
        items = memo_clean.get("items", [])
        if isinstance(items, str):
            try: items = json.loads(items)
            except: items = []
        memo_clean["items"] = items

        try:
            if memo_clean.get("_pdf_mode") == "KAS":
                from config import generate_memo_kas_pdf_bytes
                content = generate_memo_kas_pdf_bytes(memo_clean)
            else:
                from config import generate_memo_pdf_bytes
                content = generate_memo_pdf_bytes(memo_clean)

            if content:
                yield content
            else:
                yield b""
        except Exception as e_pdf:
            print("Gagal generate PDF memo:", e_pdf)
            ui.notification_show(f"Gagal memproses file PDF: {e_pdf}", type="error")
            yield b""
    # ==========================================================================
    # 8. MODAL & HANDLER HAPUS MEMO
    # ==========================================================================
    @reactive.Effect
    @reactive.event(input.btn_open_del_memo_modal)
    def _open_del_memo_modal():
        m_id = input.btn_open_del_memo_modal()
        ui.modal_show(ui.modal(
            ui.div(
                ui.tags.i(class_="fa-solid fa-trash", style="font-size: 36px; color: #E53E3E; margin-bottom: 8px;"),
                ui.h4(f"Hapus Memo {m_id}?", style="font-weight: 800; color: #1A202C; margin: 0 0 6px 0;"),
                ui.p("Data memo ini akan dihapus dari sistem.", style="color: #718096; font-size: 13px; margin: 0;"),
                style="text-align: center; padding: 1rem 0;"
            ),
            title="Konfirmasi Hapus Memo", easy_close=True,
            footer=ui.div(
                ui.modal_button("Batal"),
                ui.tags.button(
                    "Ya, Hapus",
                    onclick=f"Shiny.setInputValue('btn_confirm_del_memo', '{m_id}', {{priority: 'event'}})",
                    style="background: #E53E3E; color: white; border: none; padding: 6px 14px; border-radius: 6px; font-weight: bold; cursor: pointer; margin-left: 8px;"
                ),
                style="display: flex; justify-content: flex-end;"
            )
        ))

    @reactive.Effect
    @reactive.event(input.btn_confirm_del_memo)
    def _on_confirm_del_memo():
        m_id = input.btn_confirm_del_memo()
        ui.modal_remove()
        succ, msg = state.delete_memo(m_id)
        ui.notification_show(f"🗑️ {msg}", type="message", duration=3)
    @reactive.Effect
    @reactive.event(input.btn_process_refill_shelving)
    def _proc_refill_shelving():
        f = input.upload_refill_stock_file()
        if not f:
            state.error_modal_message.set("Upload file stock terlebih dahulu!")
            state.show_error_modal.set(True)
            return
        succ, msg = state.process_refill_shelving(f)
        ui.insert_ui(ui.tags.script("if (window.hideGlobalSpinner) window.hideGlobalSpinner();"), selector="head", where="beforeEnd")
        if succ:
            state.show_success_modal.set(True)
        else:
            state.error_modal_message.set(msg)
            state.show_error_modal.set(True)

    @render.ui
    def refill_shelving_results_container():
        if not state.rs_processed():
            return ui.div()

        total_rows = len(state.df_rs_rows())

        return ui.div(
            ui.hr(style="margin: 1.5rem 0; border-color: #CBD5E0;"),
            ui.h4("📋 HASIL INSTRUKSI REFILL SHELVING", style="font-size: 16px; color: #010B13; font-weight: 800; margin-bottom: 1rem;"),
            
            # 🌟 3 KARTU METRIK (DENGAN % ITEMS ON SHELVING)
            ui.div(
                dark_metric_box("📦 TOTAL SKU PERLU REFILL", f"{state.rs_total_sku():,} SKU", "#3182CE"),
                dark_metric_box("🔢 TOTAL QTY PICK (PCS)", f"{state.rs_total_pick():,} PCS", "#C5A059"),
                dark_metric_box("✅ ITEMS ON SHELVING", f"{state.rs_shelving_pct():.1f}%", "#10B981"),
                style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; width: 100%; margin-bottom: 1.25rem;"
            ),
            
            ui.div(
                ui.div(
                    ui.download_button(
                        "btn_dl_refill_shelving",
                        ui.tags.span(ui.tags.i(class_="fa-solid fa-download", style="margin-right: 6px;"), "DOWNLOAD REFILL SHELVING (.XLSX)"),
                        style="background-color: #10B981; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 8px 16px; cursor: pointer; font-size: 12px;"
                    ),
                    style="display: flex; justify-content: flex-end; width: 100%; margin-bottom: 0.75rem;"
                ),
                render_clean_table(state.df_rs_headers(), state.df_rs_rows(), "tbl_refill_shelving"),
                style="background: white; padding: 1.25rem; border-radius: 10px; border: 1px solid #E2E8F0;"
            ),
            style="width: 100%;"
        )

    @render.download(
        filename=lambda: f"REFILL_SHELVING_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    )
    def btn_dl_refill_shelving():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            state._raw_df_rs.to_excel(writer, sheet_name='REFILL_SHELVING', index=False)
        buf.seek(0)
        yield buf.getvalue()
    # ==========================================================================
    # INSTOCK VALIDATION CONTROLLER (BERSIH, TUNGGAL, & ANTI-REDUP)
    # ==========================================================================
    
    # 1. Tarik data saat pertama kali menu dibuka
    @reactive.Effect
    def _auto_load_instock_on_menu():
        if state.main_menu() in ["Instock Validation", "instock_validation", "instock-validation"]:
            if not state.iv_processed():
                state.load_instock_daily_from_supabase()

    # 2. Listener Refresh Instock Supabase (Tombol Refresh)
    @reactive.Effect
    @reactive.event(input.btn_refresh_iv_supabase, input.btn_run_transit_instock)
    def _on_refresh_iv():
        succ, msg = state.load_instock_daily_from_supabase()
        ui.insert_ui(ui.tags.script("if (window.hideGlobalSpinner) window.hideGlobalSpinner();"), selector="head", where="beforeEnd")
        if succ:
            ui.notification_show(f"✅ {msg}", type="message", duration=3)
        else:
            ui.notification_show(f"⚠️ {msg}", type="warning", duration=4)

    # 3. Listener Perubahan Filter Waktu
    @reactive.Effect
    @reactive.event(input.change_iv_filter_waktu)
    def _on_iv_filter_waktu_change():
        val = input.change_iv_filter_waktu()
        state.iv_filter_waktu.set(val)
        state.load_instock_daily_from_supabase()

    # 4. EVENT HANDLER TUNGGAL SAAT SKU DI-INPUT / DI-SCAN (ANTI-DOUBLE)
    @reactive.Effect
    @reactive.event(input.btn_process_iv_sku_scan)
    def _on_process_iv_sku_scan():
        scanned_sku = input.btn_process_iv_sku_scan()
        if not scanned_sku:
            return
        
        # Bersihkan string SKU dari suffix waktu acak (jika ada dari JS)
        clean_sku = scanned_sku.split("_")[0] if "_" in scanned_sku else scanned_sku
        
        succ, msg = state.move_instock_sku_to_mutasi(clean_sku)
        
        # KUNCI UTAMA: Kosongkan kotak input teks di server secara otomatis
        ui.update_text("iv_sku_scan_box", value="")

        if succ:
            ui.notification_show(f"✅ {msg}", type="message", duration=3)
        else:
            # Memunculkan pop-up error jika item tidak ada di list
            state.error_modal_message.set("Item tidak ada di list!")
            state.show_error_modal.set(True)

    # 5. RENDER CONTAINER UTAMA INSTOCK VALIDATION (HANYA ADA 1 FUNGSI INI)
    @render.ui
    def instock_validation_results_container():
        tot_need_rows = len(state.df_iv_setup_rows())
        tot_need_qty = state.iv_total_allocated_qty()
        tot_done_rows = len(state.df_iv_done_rows())
        tot_done_qty = state.iv_total_done_qty()
        tot_mutasi_rows = len(state.df_iv_mutasi_rows())

        cur_filter_waktu = state.iv_filter_waktu() if hasattr(state, "iv_filter_waktu") else "BARUSAN_5"

        metric_ui = ui.div(
            dark_metric_box("⏳ PERLU DI-SETUP (TAB 1)", f"{tot_need_rows:,} BARIS ({tot_need_qty:,} PCS)", "#E53E3E"),
            dark_metric_box("🚀 SIAP MUTASI (TAB 3)", f"{tot_mutasi_rows:,} BARIS", "#3182CE"),
            dark_metric_box("✅ DONE SETUP (TAB 2)", f"{tot_done_rows:,} BARIS ({tot_done_qty:,} PCS)", "#10B981"),
            style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; width: 100%; margin-bottom: 1.25rem;"
        )

        # 🌟 KOTAK INPUT / SCAN SKU (DIPROTEKSI ANTI-DOUBLE DENGAN TIMESTAMP & AUTO-CLEAR)
        sku_input_box = ui.div(
            ui.div(
                ui.h4("🔍 Scan / Input SKU untuk Dipindah ke Tab 3 (Mutasi)", style="font-size: 14px; font-weight: 800; color: #1A202C; margin-bottom: 6px;"),
                ui.div(
                    ui.input_text("iv_sku_scan_box", None, placeholder="Scan barcode atau ketik SKU lalu tekan Enter..."),
                    ui.tags.button(
                        "PINDAHKAN",
                        id="btn_submit_iv_sku", 
                        class_="btn-red-gradient",
                        style="padding: 8px 18px; font-size: 12px; height: 38px; white-space: nowrap; border: none; cursor: pointer;"
                    ),
                    style="display: flex; gap: 10px; align-items: center;"
                ),
                # Skrip JS agar Enter mengirim data unik dan membersihkan kotak seketika
                ui.tags.script("""
                    if (!window._ivScannerListenerAdded) {
                        window._ivScannerListenerAdded = true;
                        document.addEventListener("keydown", function(event) {
                            if (event.key === "Enter" && document.activeElement && document.activeElement.id === "iv_sku_scan_box") {
                                event.preventDefault();
                                let inputEl = document.getElementById("iv_sku_scan_box");
                                let val = inputEl ? inputEl.value.trim() : "";
                                
                                if (val !== "") {
                                    // Tambahkan timestamp agar Shiny mendeteksi perubahan nilai unik (mencegah abaikan data kembar)
                                    Shiny.setInputValue("btn_process_iv_sku_scan", val + "_" + Date.now(), {priority: "event"});
                                    if (inputEl) inputEl.value = ""; // Kosongkan langsung
                                }
                            }
                        });
                    }
                """),
                style="background: #F8FAFC; border: 1.5px solid #CBD5E0; padding: 1rem; border-radius: 10px; margin-bottom: 1rem;"
            )
        )

        filter_control_bar = ui.div(
            ui.div(
                ui.span("⏱️ Filter Waktu Instock:", style="font-size: 12px; font-weight: 800; color: #1A202C; margin-right: 8px;"),
                ui.tags.select(
                    ui.tags.option("🔥 Barusan Saja (< 5 Menit)", value="BARUSAN_5", selected=(cur_filter_waktu == "BARUSAN_5")),
                    ui.tags.option("⚡ 15 Menit Terakhir", value="BARUSAN_15", selected=(cur_filter_waktu == "BARUSAN_15")),
                    ui.tags.option("⏳ 30 Menit Terakhir", value="BARUSAN_30", selected=(cur_filter_waktu == "BARUSAN_30")),
                    ui.tags.option("📋 Semua Antrean Hari Ini", value="SEMUA", selected=(cur_filter_waktu == "SEMUA")),
                    id="iv_filter_waktu_select",
                    onchange="Shiny.setInputValue('change_iv_filter_waktu', this.value, {priority: 'event'})",
                    style="padding: 6px 12px; border-radius: 6px; border: 1.5px solid #CBD5E0; font-weight: 700; font-size: 12px; background: white; cursor: pointer; min-width: 220px;"
                ),
                style="display: flex; align-items: center;"
            ),
            style="display: flex; justify-content: flex-start; align-items: center; width: 100%; margin-bottom: 0.75rem;"
        )

        # TAB 1: LIST SETUP
        tab1_need = ui.div(
            sku_input_box,
            filter_control_bar,
            render_clean_table(state.df_iv_setup_headers(), state.df_iv_setup_rows(), "tbl_iv_setup"),
            style="padding: 0.75rem 0;"
        )

        # TAB 2: DONE SETUP
        tab2_done = ui.div(
            ui.div(
                ui.div(
                    ui.h4("✅ Riwayat Mutasi Sukses Tervalidasi", style="font-size: 15px; font-weight: 800; color: #1A202C; margin: 0 0 2px 0;"),
                    ui.p("Barang yang mutasinya sudah diverifikasi cocok dengan riwayat Jezpro.", style="color: #718096; font-size: 12px; margin: 0;")
                ),
                ui.download_button(
                    "btn_dl_iv_done",
                    ui.tags.span(ui.tags.i(class_="fa-solid fa-file-excel", style="margin-right: 6px;"), "DOWNLOAD RIWAYAT DONE (.XLSX)"),
                    style="background-color: #3182CE; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 8px 16px; cursor: pointer; font-size: 12px;"
                ),
                style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 0.75rem; flex-wrap: wrap; gap: 8px;"
            ),
            render_clean_table(state.df_iv_done_headers(), state.df_iv_done_rows(), "tbl_iv_done"),
            style="padding: 0.75rem 0;"
        )

        # TAB 3: ITEM MUTASI
        tab3_mutasi = ui.div(
            ui.div(
                ui.div(
                    ui.h4("📄 Template Mutasi Jezpro (Item Hasil Scan)", style="font-size: 15px; font-weight: 800; color: #1A202C; margin: 0 0 2px 0;"),
                    ui.p("Item yang berhasil dipindah melalui scan SKU akan terkumpul di sini, siap di-upload ke Mutasi Bin Jezpro.", style="color: #718096; font-size: 12px; margin: 0;")
                ),
                ui.download_button(
                    "btn_dl_iv_mutasi_5col",
                    ui.tags.span(ui.tags.i(class_="fa-solid fa-cloud-arrow-down", style="margin-right: 6px;"), "DOWNLOAD TEMPLATE MUTASI (.XLSX)"),
                    style="background: linear-gradient(135deg, #10B981 0%, #059669 100%); color: white; font-weight: 800; border-radius: 6px; border: none; padding: 8px 18px; cursor: pointer; font-size: 12px; box-shadow: 0 2px 6px rgba(16,185,129,0.3);"
                ),
                style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 0.75rem; flex-wrap: wrap; gap: 8px;"
            ),
            render_clean_table(state.df_iv_mutasi_headers(), state.df_iv_mutasi_rows(), "tbl_iv_mutasi_clean"),
            style="padding: 0.75rem 0;"
        )

        return ui.div(
            ui.hr(style="margin: 1.5rem 0; border-color: #CBD5E0;"),
            metric_ui,
            ui.navset_card_tab(
                ui.nav_panel(f"⏳ 1. LIST SETUP ({tot_need_rows})", tab1_need),
                ui.nav_panel(f"✅ 2. DONE SETUP ({tot_done_rows})", tab2_done),
                ui.nav_panel(f"📄 3. ITEM MUTASI ({tot_mutasi_rows})", tab3_mutasi)
            ),
            style="width: 100%; background: white; padding: 1.5rem; border-radius: 12px; border: 1px solid #E2E8F0;"
        )

    # Handler Download File Excel 5 Kolom Tab 3
    @render.download(
        filename=lambda: f"TEMPLATE_MUTASI_JEZPRO_5KOLOM_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    )
    def btn_dl_iv_mutasi_5col():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            state._raw_df_iv_mutasi.to_excel(writer, sheet_name='TEMPLATE_MUTASI', index=False)
        buf.seek(0)
        yield buf.getvalue()

    @render.download(
        filename=lambda: f"DONE_SETUP_INSTOCK_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    )
    def btn_dl_iv_done():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            state._raw_df_iv_done.to_excel(writer, sheet_name='DONE_SETUP', index=False)
        buf.seek(0)
        yield buf.getvalue()

    # Listener untuk membunyikan suara di browser saat ada permintaan FL baru
    @reactive.Effect
    @reactive.event(state.fl_audio_trigger)
    def _trigger_fl_sound():
        if state.fl_audio_trigger() > 0:
            ui.insert_ui(
                ui.tags.script("if (window.playFLSound) window.playFLSound();"),
                selector="head",
                where="beforeEnd"
            )
        
from pathlib import Path

# Daftarkan folder root agar file mp3 dapat diakses browser client
APP_DIR = Path(__file__).parent
app = App(app_ui, server, static_assets={"/static": APP_DIR})

    