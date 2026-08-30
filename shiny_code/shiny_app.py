import io
import pandas as pd
from shiny import App, Inputs, Outputs, Session, reactive, render, ui
from state import AppState
from views import (
    CUSTOM_HEAD, static_loading_spinner, success_modal, error_modal,
    render_clean_table, metric_box, dark_metric_box,  BRANCH_BIN_MAPPING, 
    custom_uploader_box, compare_system_view, stock_minus_view,
    putaway_view, main_dashboard_view, sidebar, cycle_count_view, login_page, ppa_audit_view, cycle_count_analyzer_view, global_header
)

app_ui = ui.page_fluid(
    CUSTOM_HEAD,
    static_loading_spinner(),
    ui.output_ui("global_success_modal_ui"),
    ui.output_ui("global_error_modal_ui"),
    ui.output_ui("main_root_container"),
    style="padding: 0; margin: 0; background-color: #111318;"
)

def server(input: Inputs, output: Outputs, session: Session):
    state = AppState()

    # Modal Dismiss Listeners
    @reactive.Effect
    @reactive.event(input.close_success_modal_event)
    def _on_close_success_modal(): state.show_success_modal.set(False)

    @reactive.Effect
    @reactive.event(input.close_error_modal_event)
    def _on_close_error_modal():
        state.show_error_modal.set(False)
        state.error_modal_message.set("")

    @render.ui
    def global_success_modal_ui(): return success_modal(state.show_success_modal())

    @render.ui
    def global_error_modal_ui(): return error_modal(state.show_error_modal(), state.error_modal_message())

    # Authentication & Navigation
    @reactive.Effect
    @reactive.event(input.btn_submit_login)
    def _login_event():
        data = input.btn_submit_login()
        u, p = data.get("user", ""), data.get("pass", "")
        success, msg = state.handle_login(u, p)
        if success:
            state.load_ongkir_data()
            ui.notification_show(msg, type="message", duration=4)
        else:
            state.error_modal_message.set(msg)
            ui.notification_show(msg, type="error", duration=4)

    @reactive.Effect
    @reactive.event(input.btn_execute_logout)
    def _logout_event():
        state.logout()
        ui.notification_show("Anda telah keluar dari sistem.", type="warning", duration=4)

    @reactive.Effect
    @reactive.event(input.select_menu_item)
    def _nav_event(): state.set_main_menu(input.select_menu_item())

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
    # Sub-render Action Buttons
    @render.ui
    def stock_minus_action_btn_ui():
        f = input.upload_stock_file() if "upload_stock_file" in input else None
        if f and len(f) > 0:
            return ui.div(ui.tags.button(ui.tags.span(ui.tags.i(class_="fa-solid fa-play", style="margin-right: 6px; font-size: 14px;"), "PROSES DATA"), onclick="document.body.classList.add('process-running'); Shiny.setInputValue('btn_process_stock_minus', Math.random(), {priority: 'event'});", class_="btn-red-gradient"), style="display: flex; justify-content: flex-end; width: 100%; margin-top: 1rem;")
        return ui.div(ui.tags.button(ui.tags.i(class_="fa-solid fa-lock", style="margin-right: 6px; font-size: 14px;"), "PILIH FILE UNTUK MEMULAI", disabled=True, class_="btn-locked"), style="display: flex; justify-content: flex-end; width: 100%; margin-top: 1rem;")

    @render.ui
    def putaway_action_btn_ui():
        f_ds, f_as = input.ds_putaway_file() if "ds_putaway_file" in input else None, input.asal_putaway_file() if "asal_putaway_file" in input else None
        if (f_ds and len(f_ds) > 0) and (f_as and len(f_as) > 0):
            return ui.div(ui.tags.button(ui.tags.span(ui.tags.i(class_="fa-solid fa-play", style="margin-right: 6px; font-size: 14px;"), "COMPARE PUTAWAY"), onclick="document.body.classList.add('process-running'); Shiny.setInputValue('btn_compare_putaway', Math.random(), {priority: 'event'});", class_="btn-red-gradient"), style="display: flex; justify-content: flex-end; width: 100%; margin-top: 0.5rem;")
        return ui.div(ui.tags.button(ui.tags.i(class_="fa-solid fa-lock", style="margin-right: 6px; font-size: 14px;"), "PILIH KEDUA FILE UNTUK MEMULAI", disabled=True, class_="btn-locked"), style="display: flex; justify-content: flex-end; width: 100%; margin-top: 0.5rem;")

    @render.ui
    def compare_system_action_btn_ui():
        f1, f2 = input.uploader_sys1() if "uploader_sys1" in input else None, input.uploader_sys2() if "uploader_sys2" in input else None
        if (f1 and len(f1) > 0) and (f2 and len(f2) > 0):
            return ui.div(ui.tags.button(ui.tags.span(ui.tags.i(class_="fa-solid fa-play", style="margin-right: 6px; font-size: 14px;"), "RUN COMPARE"), onclick="document.body.classList.add('process-running'); Shiny.setInputValue('btn_run_compare_system', Math.random(), {priority: 'event'});", class_="btn-red-gradient"), style="display: flex; justify-content: flex-end; width: 100%; margin-top: 0.5rem;")
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
        with open(f[0]["datapath"], "rb") as fp:
            succ, msg = state.process_stock_minus_file(fp.read(), f[0]["name"])
        if succ: state.show_success_modal.set(True)
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

    # Main Dynamic Router
    @render.ui
    def main_root_container():
        if not state.logged_in(): return login_page()
        content_type = state.get_active_content_type()

        if content_type == "dashboard_ongkir": page_content = main_dashboard_view(state)
        elif content_type == "stock_minus": page_content = stock_minus_view(state)
        elif content_type == "putaway_system": page_content = putaway_view(state)
        elif content_type == "compare_system": page_content = compare_system_view(state)
        elif content_type == "cycle_count": page_content = cycle_count_view(state)
        elif content_type == "ppa_audit": page_content = ppa_audit_view(state)
        elif content_type == "cycle_count_analyzer": page_content = cycle_count_analyzer_view(state)
        elif content_type == "access_denied":
            page_content = ui.div(ui.h2("⛔ Akses Ditolak", style="font-size: 28px; color: #E53E3E; font-weight: bold;"), ui.p("Maaf, halaman ini dibatasi hak aksesnya.", style="color: #718096; font-size: 15px;"), style="padding: 3rem; text-align: center; height: 70vh; display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%;")
        else:
            page_content = ui.div(ui.h2(f"Halaman: {state.main_menu()}", style="font-size: 28px; color: #1A202C; font-weight: bold;"), ui.p("Halaman ini sedang dalam tahap pengembangan.", style="color: #718096; font-size: 15px;"), style="padding: 3rem; text-align: center; height: 70vh; display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%;")

        return ui.div(
            sidebar(state),
            ui.div(
                global_header(state),
                page_content,
                id="main-scroll-container",   # <-- TAMBAHKAN ID INI DI SINI
                style="flex: 1; height: 100vh; overflow-y: auto; padding: 1.5rem; background-color: #F7FAFC;"
            ),
            style="display: flex; width: 100vw; height: 100vh; overflow: hidden; background-color: #111318;"
        )
# --- CYCLE COUNT BUTTON & HASIL ---
    @render.ui
    def cycle_count_action_btn_ui():
        f = input.upload_cycle_count_file() if "upload_cycle_count_file" in input else None
        if f and len(f) > 0:
            return ui.div(
                ui.tags.button(
                    ui.tags.span(ui.tags.i(class_="fa-solid fa-play", style="margin-right: 6px; font-size: 14px;"), "PROSES DATA"),
                    onclick="document.body.classList.add('process-running'); Shiny.setInputValue('btn_process_cycle_count', Math.random(), {priority: 'event'});",
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
    def cycle_count_results_container():
        if not state.cc_processed():
            return ui.div()

        return ui.div(
            # --- 1. FILTER MULTI-SELECT ---
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
                render_clean_table(state.df_cc_headers(), state.df_cc_rows()),
                style="background: white; padding: 1.25rem; border-radius: 10px; border: 1px solid #E2E8F0;"
            ),
            style="width: 100%;"
        )

    # Listener Filter Interaktif (Real-time Filter)
    @reactive.Effect
    def _on_cc_filter_change():
        if state.cc_processed():
            sub = input.cc_filter_sub() if "cc_filter_sub" in input else []
            brand = input.cc_filter_brand() if "cc_filter_brand" in input else []
            tier = input.cc_filter_tier() if "cc_filter_tier" in input else []
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
                    onclick="document.body.classList.add('process-running'); Shiny.setInputValue('btn_process_ppa_audit', Math.random(), {priority: 'event'});",
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
    # CYCLE COUNT ANALYZER CONTROLLER & HANDLERS (PERBAIKAN TOTAL)
    # ==========================================================================
    @render.ui
    def cca_bin_sys_ui():
        b = input.cca_branch() if "cca_branch" in input else "SURABAYA"
        choices = BRANCH_BIN_MAPPING.get(b, [])
        return ui.input_selectize("cca_bin_sys", "🏭 BIN System:", choices=choices, multiple=True, width="100%")

    # --- STEP 1: BUTTON, HASIL & DOWNLOAD ---
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
            # Tombol Download Excel Khusus Step 1
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
        f_scan = input.cca_up_scan()
        f_stock = input.cca_up_stock()
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

    # --- PROGRESSIVE DYNAMIC STEPS (STEP 2 SAMPAI 6 BERTAHAP) ---
    @render.ui
    def cca_dynamic_steps_ui():
        if not state.cca_step1_done():
            return ui.div()

        # Step 2 & 3 UI Container
        step2_results = ui.div()
        if state.cca_step2_done():
            step2_results = ui.div(
                ui.hr(style="margin: 1rem 0; border-color: #E2E8F0;"),
                # Header Step 2 dengan Tombol Download Excel Khusus Step 2
                ui.div(
                    ui.h4("✅ HASIL ALOKASI", style="font-size: 15px; font-weight: 800; color: #1A202C; margin: 0;"),
                    ui.download_button(
                        "btn_dl_cca_step2",
                        ui.tags.span(ui.tags.i(class_="fa-solid fa-download", style="margin-right: 6px; font-size: 14px;"), "DOWNLOAD HASIL ALOKASI (.xlsx)"),
                        style="background-color: #10B981; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 8px 16px; cursor: pointer;"
                    ),
                    style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 0.75rem;"
                ),
                ui.navset_card_tab(
                    ui.nav_panel("📊 ALLOCATION DETAIL", ui.div(render_clean_table(state.df_cca_alloc_headers(), state.df_cca_alloc_rows(), "tbl_cca_alloc"), style="padding: 0.75rem 0;")),
                    ui.nav_panel("📉 UPDATED SYSTEM", ui.div(render_clean_table(state.df_cca_sys_upd_headers(), state.df_cca_sys_upd_rows(), "tbl_cca_sys_upd"), style="padding: 0.75rem 0;")),
                    ui.nav_panel("📦 SET UP REAL +", ui.div(render_clean_table(state.df_cca_setup_real_headers(), state.df_cca_setup_real_rows(), "tbl_cca_setup_real"), style="padding: 0.75rem 0;"))
                ),
                ui.hr(style="margin: 1.5rem 0; border-color: #E2E8F0;"),
                ui.h4("📋 RECON REPORTS (HASIL STEP 1 - 3)", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 1rem;"),
                ui.div(
                    ui.div(
                        ui.h4("📋 REAL + RECON", style="font-size: 14px; font-weight: 800; color: #1A202C; margin-bottom: 0.5rem;"),
                        render_clean_table(state.df_cca_rec_real_headers(), state.df_cca_rec_real_rows(), "tbl_cca_rec_real"),
                        style="flex: 1; min-width: 300px;"
                    ),
                    ui.div(
                        ui.h4("🔐 SYSTEM + OUTSTANDING", style="font-size: 14px; font-weight: 800; color: #1A202C; margin-bottom: 0.5rem;"),
                        render_clean_table(state.df_cca_rec_sys_headers(), state.df_cca_rec_sys_rows(), "tbl_cca_rec_sys"),
                        style="flex: 1; min-width: 300px;"
                    ),
                    style="display: flex; gap: 1rem; flex-wrap: wrap; width: 100%;"
                )
            )

        step2_box = ui.div(
            ui.h4("2️⃣ Upload BIN COVERAGE (ALL BIN DEFAULT & KARANTINA)", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 0.75rem;"),
            custom_uploader_box("cca_up_cov", "📥 FILE BIN COVERAGE"),
            ui.output_ui("cca_step2_btn_ui"),
            step2_results,
            style="background: white; padding: 1.25rem; border-radius: 10px; border: 1px solid #E2E8F0; margin-bottom: 1.25rem;"
        )

        # Step 4 (Hanya Muncul Jika Step 2 Sudah Selesai)
        step4_box = ui.div()
        if state.cca_step2_done():
            step4_results = ui.div()
            if state.cca_step4_done():
                step4_results = ui.div(
                    ui.hr(style="margin: 1rem 0; border-color: #E2E8F0;"),
                    ui.div(
                        dark_metric_box("⚠️ TOTAL REAL + NEED ADJ", f"{state.cca_qty_need_adj():,} QTY", "#E53E3E"),
                        dark_metric_box("📦 TOTAL SKU", f"{state.cca_sku_need_adj():,} SKU", "#3182CE"),
                        style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; width: 100%; margin-bottom: 1rem;"
                    ),
                    # Tombol Download Excel Khusus Step 4
                    ui.div(
                        ui.download_button(
                            "btn_dl_cca_step4",
                            ui.tags.span(ui.tags.i(class_="fa-solid fa-download", style="margin-right: 6px; font-size: 14px;"), "DOWNLOAD HASIL RECON REAL + (.xlsx)"),
                            style="background-color: #10B981; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 8px 16px; cursor: pointer;"
                        ),
                        style="display: flex; justify-content: flex-end; width: 100%; margin-bottom: 0.75rem;"
                    ),
                    render_clean_table(state.df_cca_adj4_headers(), state.df_cca_adj4_rows(), "tbl_cca_adj4")
                )

            step4_box = ui.div(
                ui.h4("3️⃣ RECON REAL + PROCESS", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 0.75rem;"),
                custom_uploader_box("cca_up_recon_real", "📥 Upload HASIL RECON REAL +"),
                ui.output_ui("cca_step4_btn_ui"),
                step4_results,
                style="background: white; padding: 1.25rem; border-radius: 10px; border: 1px solid #E2E8F0; margin-bottom: 1.25rem;"
            )

        # Step 5 (Hanya Muncul Jika Step 4 Sudah Selesai)
        step5_box = ui.div()
        if state.cca_step4_done():
            step5_results = ui.div()
            if state.cca_step5_done():
                step5_results = ui.div(
                    ui.hr(style="margin: 1rem 0; border-color: #E2E8F0;"),
                    ui.div(
                        dark_metric_box("☣️ QTY TO KARANTINA", f"{state.cca_qty_karantina():,} QTY", "#ECC94B"),
                        dark_metric_box("🏷️ SKU TO KARANTINA", f"{state.cca_sku_karantina():,} SKU", "#ECC94B"),
                        style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; width: 100%; margin-bottom: 1rem;"
                    ),
                    # Tombol Download Excel Khusus Step 5
                    ui.div(
                        ui.download_button(
                            "btn_dl_cca_karantina",
                            ui.tags.span(ui.tags.i(class_="fa-solid fa-download", style="margin-right: 6px; font-size: 14px;"), "DOWNLOAD HASIL KARANTINA (.xlsx)"),
                            style="background-color: #10B981; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 8px 16px; cursor: pointer;"
                        ), style="display: flex; justify-content: flex-end; width: 100%; margin-bottom: 0.75rem;"
                    ),
                    ui.navset_card_tab(
                        ui.nav_panel("📦 HASIL KARANTINA", ui.div(render_clean_table(state.df_cca_karantina_headers(), state.df_cca_karantina_rows(), "tbl_cca_karantina"), style="padding: 0.75rem 0;")),
                        ui.nav_panel("🔍 DATA PENGECEKAN (AUDIT)", ui.div(render_clean_table(state.df_cca_check5_headers(), state.df_cca_check5_rows(), "tbl_cca_check5"), style="padding: 0.75rem 0;"))
                    )
                )

            step5_box = ui.div(
                ui.h4("4️⃣ RECON SYSTEM + PROCESS (SET UP KARANTINA)", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 0.75rem;"),
                custom_uploader_box("cca_up_recon_sys", "📥 Upload SYSTEM + RECON (File Master Hasil Audit)"),
                ui.output_ui("cca_step5_btn_ui"),
                step5_results,
                style="background: white; padding: 1.25rem; border-radius: 10px; border: 1px solid #E2E8F0; margin-bottom: 1.25rem;"
            )

        # Step 6 (Hanya Muncul Jika Step 5 Sudah Selesai)
        step6_box = ui.div()
        if state.cca_step5_done():
            step6_results = ui.div()
            if state.cca_step6_done():
                step6_results = ui.div(
                    ui.hr(style="margin: 1rem 0; border-color: #E2E8F0;"),
                    ui.div(
                        dark_metric_box("📦 TOTAL SKU MISS LOC.", f"{state.cca_sku_miss_loc():,} ITEM", "#E53E3E"),
                        dark_metric_box("🔢 TOTAL QTY MISS LOC.", f"{state.cca_qty_miss_loc():,} ITEM", "#E53E3E"),
                        style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; width: 100%; margin-bottom: 1rem;"
                    ),
                    # Tombol Download Excel Khusus Step 6
                    ui.div(
                        ui.download_button(
                            "btn_dl_cca_miss_loc",
                            ui.tags.span(ui.tags.i(class_="fa-solid fa-download", style="margin-right: 6px; font-size: 14px;"), "DOWNLOAD MISS LOC REPORT (.xlsx)"),
                            style="background-color: #10B981; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 8px 16px; cursor: pointer;"
                        ), style="display: flex; justify-content: flex-end; width: 100%; margin-bottom: 0.75rem;"
                    ),
                    ui.navset_card_tab(
                        ui.nav_panel("📄 Detail List", ui.div(render_clean_table(state.df_cca_miss_loc_headers(), state.df_cca_miss_loc_rows(), "tbl_cca_miss_loc"), style="padding: 0.75rem 0;")),
                        ui.nav_panel("📊 Summary", ui.div(render_clean_table(state.df_cca_sum_miss_headers(), state.df_cca_sum_miss_rows(), "tbl_cca_sum_miss"), style="padding: 0.75rem 0;"))
                    )
                )

            step6_box = ui.div(
                ui.h4("5️⃣ MISS LOCATION REPORT", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 0.75rem;"),
                ui.tags.button(
                    ui.tags.span(ui.tags.i(class_="fa-solid fa-chart-pie", style="margin-right: 6px; font-size: 14px;"), "GENERATE MISS LOC REPORT"),
                    onclick="document.body.classList.add('process-running'); Shiny.setInputValue('btn_run_cca_step6', Math.random(), {priority: 'event'});",
                    class_="btn-red-gradient"
                ),
                step6_results,
                style="background: white; padding: 1.25rem; border-radius: 10px; border: 1px solid #E2E8F0; margin-bottom: 1.25rem;"
            )

        return ui.div(
            step2_box,
            step4_box,
            step5_box,
            step6_box
        )

    # --- STEP 2 EXECUTION & DOWNLOAD HANDLER ---
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
        return ui.div(
            ui.tags.button("UPLOAD FILE BIN COVERAGE UNTUK ALOKASI", disabled=True, class_="btn-locked"),
            style="display: flex; justify-content: flex-end; width: 100%; margin-top: 0.5rem;"
        )

    @reactive.Effect
    @reactive.event(input.btn_run_cca_step2)
    def _proc_cca_step2():
        f = input.cca_up_cov()
        bin_cov = input.cca_bin_cov() if "cca_bin_cov" in input else []
        succ, msg = state.run_cca_step2(f, bin_cov)
        if succ: state.show_success_modal.set(True)
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

    # --- STEP 4 EXECUTION & DOWNLOAD HANDLER ---
    @render.ui
    def cca_step4_btn_ui():
        f = input.cca_up_recon_real() if "cca_up_recon_real" in input else None
        if f:
            return ui.div(
                ui.tags.button(
                    ui.tags.span(ui.tags.i(class_="fa-solid fa-play", style="margin-right: 6px; font-size: 14px;"), "RUN RECON ANALYSIS"),
                    onclick="document.body.classList.add('process-running'); Shiny.setInputValue('btn_run_cca_step4', Math.random(), {priority: 'event'});",
                    class_="btn-red-gradient"
                ), style="display: flex; justify-content: flex-end; width: 100%; margin-top: 0.5rem;"
            )
        return ui.div(
            ui.tags.button("UPLOAD HASIL RECON REAL + UNTUK ANALISIS", disabled=True, class_="btn-locked"),
            style="display: flex; justify-content: flex-end; width: 100%; margin-top: 0.5rem;"
        )

    @reactive.Effect
    @reactive.event(input.btn_run_cca_step4)
    def _proc_cca_step4():
        f = input.cca_up_recon_real()
        succ, msg = state.run_cca_step4(f)
        if succ: state.show_success_modal.set(True)
        else:
            state.error_modal_message.set(msg)
            state.show_error_modal.set(True)

    @render.download(filename="Hasil_Recon_Real_Plus_Need_Adj.xlsx")
    def btn_dl_cca_step4():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            state._raw_df_cca_adj4.to_excel(writer, sheet_name='RECON_REAL_PLUS_ADJ', index=False)
        buf.seek(0)
        yield buf.getvalue()

    # --- STEP 5 EXECUTION & DOWNLOAD HANDLER ---
    @render.ui
    def cca_step5_btn_ui():
        f = input.cca_up_recon_sys() if "cca_up_recon_sys" in input else None
        if f:
            return ui.div(
                ui.tags.button(
                    ui.tags.span(ui.tags.i(class_="fa-solid fa-play", style="margin-right: 6px; font-size: 14px;"), "GENERATE KARANTINA"),
                    onclick="document.body.classList.add('process-running'); Shiny.setInputValue('btn_run_cca_step5', Math.random(), {priority: 'event'});",
                    class_="btn-red-gradient"
                ), style="display: flex; justify-content: flex-end; width: 100%; margin-top: 0.5rem;"
            )
        return ui.div(
            ui.tags.button("UPLOAD SYSTEM + RECON UNTUK GENERATE", disabled=True, class_="btn-locked"),
            style="display: flex; justify-content: flex-end; width: 100%; margin-top: 0.5rem;"
        )

    @reactive.Effect
    @reactive.event(input.btn_run_cca_step5)
    def _proc_cca_step5():
        f = input.cca_up_recon_sys()
        succ, msg = state.run_cca_step5(f)
        if succ: state.show_success_modal.set(True)
        else:
            state.error_modal_message.set(msg)
            state.show_error_modal.set(True)

    @render.download(filename="Karantina.xlsx")
    def btn_dl_cca_karantina():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            state._raw_df_cca_karantina.to_excel(writer, sheet_name='Karantina', index=False)
            state._raw_df_cca_check5.to_excel(writer, sheet_name='Data_Pengecekan_Audit', index=False)
        buf.seek(0)
        yield buf.getvalue()

    # --- STEP 6 EXECUTION & DOWNLOAD HANDLER ---
    @reactive.Effect
    @reactive.event(input.btn_run_cca_step6)
    def _proc_cca_step6():
        succ, msg = state.run_cca_step6()
        if succ: state.show_success_modal.set(True)
        else:
            state.error_modal_message.set(msg)
            state.show_error_modal.set(True)

    @render.download(filename="Miss_Location_Report.xlsx")
    def btn_dl_cca_miss_loc():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            state._raw_df_cca_miss_loc.to_excel(writer, sheet_name='DETAIL_MISS_LOC', index=False)
            state._raw_df_cca_sum_miss.to_excel(writer, sheet_name='SUMMARY', index=False)
        buf.seek(0)
        yield buf.getvalue()

app = App(app_ui, server)