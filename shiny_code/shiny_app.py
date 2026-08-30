import io
import pandas as pd
from shiny import App, Inputs, Outputs, Session, reactive, render, ui
from state import AppState
from views import (
    CUSTOM_HEAD, static_loading_spinner, success_modal, error_modal,
    render_clean_table, metric_box, dark_metric_box,  BRANCH_BIN_MAPPING, 
    custom_uploader_box, compare_system_view, stock_minus_view, stock_opname_view,
    putaway_view, main_dashboard_view, sidebar, compare_rto_view, justification_so_view, cycle_count_view, login_page, ppa_audit_view, cycle_count_analyzer_view, global_header
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
                # --- SECTION 1: FORMAT FILE ---
                ui.tags.details(
                    ui.tags.summary("📋 Informasi Format File"),
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
        elif content_type == "compare_rto": page_content = compare_rto_view(state)
        elif content_type == "stock_opname": page_content = stock_opname_view(state)
        elif content_type == "justification_so": page_content = justification_so_view(state)
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

    # --- KARTU MANDIRI STEP 2 ---
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
                ui.h4("📋 RECON REPORTS (HASIL STEP 1 - 3)", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 1rem;"),
                ui.div(
                    ui.div(ui.h4("📋 REAL + RECON", style="font-size: 14px; font-weight: 800; color: #1A202C; margin-bottom: 0.5rem;"), render_clean_table(state.df_cca_rec_real_headers(), state.df_cca_rec_real_rows(), "tbl_cca_rec_real"), style="flex: 1; min-width: 300px;"),
                    ui.div(ui.h4("🔐 SYSTEM + OUTSTANDING", style="font-size: 14px; font-weight: 800; color: #1A202C; margin-bottom: 0.5rem;"), render_clean_table(state.df_cca_rec_sys_headers(), state.df_cca_rec_sys_rows(), "tbl_cca_rec_sys"), style="flex: 1; min-width: 300px;"),
                    style="display: flex; gap: 1rem; flex-wrap: wrap; width: 100%;"
                )
            )

        return ui.div(
            ui.h4("2️⃣ Upload BIN COVERAGE (ALL BIN DEFAULT & KARANTINA)", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 0.75rem;"),
            custom_uploader_box("cca_up_cov", "📥 FILE BIN COVERAGE"),
            ui.output_ui("cca_step2_btn_ui"),
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

    # --- KARTU MANDIRI STEP 4 ---
    @render.ui
    def cca_step4_card_ui():
        if not state.cca_step2_done(): return ui.div()
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
            ui.output_ui("cca_step4_btn_ui"),
            step4_results,
            class_="step-card-box",
            style="background: white; padding: 1.25rem; border-radius: 10px; border: 1px solid #E2E8F0; margin-bottom: 1.25rem;"
        )

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
        return ui.div(ui.tags.button("UPLOAD HASIL RECON REAL + UNTUK ANALISIS", disabled=True, class_="btn-locked"), style="display: flex; justify-content: flex-end; width: 100%; margin-top: 0.5rem;")

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

    # --- KARTU MANDIRI STEP 5 ---
    @render.ui
    def cca_step5_card_ui():
        if not state.cca_step4_done(): return ui.div()
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
                    ui.download_button("btn_dl_cca_karantina", ui.tags.span(ui.tags.i(class_="fa-solid fa-download", style="margin-right: 6px; font-size: 14px;"), "DOWNLOAD HASIL KARANTINA (.xlsx)"), style="background-color: #10B981; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 8px 16px; cursor: pointer;"),
                    style="display: flex; justify-content: flex-end; width: 100%; margin-bottom: 0.75rem;"
                ),
                ui.navset_card_tab(
                    ui.nav_panel("📦 HASIL KARANTINA", ui.div(render_clean_table(state.df_cca_karantina_headers(), state.df_cca_karantina_rows(), "tbl_cca_karantina"), style="padding: 0.75rem 0;")),
                    ui.nav_panel("🔍 DATA PENGECEKAN (AUDIT)", ui.div(render_clean_table(state.df_cca_check5_headers(), state.df_cca_check5_rows(), "tbl_cca_check5"), style="padding: 0.75rem 0;"))
                )
            )

        return ui.div(
            ui.h4("4️⃣ RECON SYSTEM + PROCESS (SET UP KARANTINA)", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 0.75rem;"),
            custom_uploader_box("cca_up_recon_sys", "📥 Upload SYSTEM + RECON (File Master Hasil Audit)"),
            ui.output_ui("cca_step5_btn_ui"),
            step5_results,
            class_="step-card-box",
            style="background: white; padding: 1.25rem; border-radius: 10px; border: 1px solid #E2E8F0; margin-bottom: 1.25rem;"
        )

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
        return ui.div(ui.tags.button("UPLOAD SYSTEM + RECON UNTUK GENERATE", disabled=True, class_="btn-locked"), style="display: flex; justify-content: flex-end; width: 100%; margin-top: 0.5rem;")

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

    # --- KARTU MANDIRI STEP 6 ---
    @render.ui
    def cca_step6_card_ui():
        if not state.cca_step5_done(): return ui.div()
        step6_results = ui.div()
        if state.cca_step6_done():
            step6_results = ui.div(
                ui.hr(style="margin: 1rem 0; border-color: #E2E8F0;"),
                ui.div(
                    dark_metric_box("📦 TOTAL SKU MISS LOC.", f"{state.cca_sku_miss_loc():,} ITEM", "#E53E3E"),
                    dark_metric_box("🔢 TOTAL QTY MISS LOC.", f"{state.cca_qty_miss_loc():,} ITEM", "#E53E3E"),
                    style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; width: 100%; margin-bottom: 1rem;"
                ),
                ui.div(
                    ui.download_button("btn_dl_cca_miss_loc", ui.tags.span(ui.tags.i(class_="fa-solid fa-download", style="margin-right: 6px; font-size: 14px;"), "DOWNLOAD MISS LOC REPORT (.xlsx)"), style="background-color: #10B981; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 8px 16px; cursor: pointer;"),
                    style="display: flex; justify-content: flex-end; width: 100%; margin-bottom: 0.75rem;"
                ),
                ui.navset_card_tab(
                    ui.nav_panel("📄 Detail List", ui.div(render_clean_table(state.df_cca_miss_loc_headers(), state.df_cca_miss_loc_rows(), "tbl_cca_miss_loc"), style="padding: 0.75rem 0;")),
                    ui.nav_panel("📊 Summary", ui.div(render_clean_table(state.df_cca_sum_miss_headers(), state.df_cca_sum_miss_rows(), "tbl_cca_sum_miss"), style="padding: 0.75rem 0;"))
                )
            )

        return ui.div(
            ui.h4("5️⃣ MISS LOCATION REPORT", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 0.75rem;"),
            ui.tags.button(
                ui.tags.span(ui.tags.i(class_="fa-solid fa-chart-pie", style="margin-right: 6px; font-size: 14px;"), "GENERATE MISS LOC REPORT"),
                onclick="document.body.classList.add('process-running'); Shiny.setInputValue('btn_run_cca_step6', Math.random(), {priority: 'event'});",
                class_="btn-red-gradient"
            ),
            step6_results,
            class_="step-card-box",
            style="background: white; padding: 1.25rem; border-radius: 10px; border: 1px solid #E2E8F0; margin-bottom: 1.25rem;"
        )

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

    # --- STEP 2 & 3: ALLOCATION & RECON ---
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
                ui.h4("📋 RECON REPORTS (HASIL STEP 1 - 3)", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 1rem;"),
                ui.div(
                    ui.div(
                        ui.div(
                            ui.h4("📋 REAL + RECON", style="font-size: 14px; font-weight: 800; color: #1A202C; margin: 0;"),
                            ui.download_button("btn_dl_so_rec_real", ui.tags.span(ui.tags.i(class_="fa-solid fa-download", style="margin-right: 6px; font-size: 13px;"), "Download (.xlsx)"), style="background-color: #10B981; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 4px 10px; cursor: pointer; font-size: 12px;"),
                            style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 0.5rem;"
                        ),
                        render_clean_table(state.df_so_rec_real_headers(), state.df_so_rec_real_rows(), "tbl_so_rec_real"),
                        style="flex: 1; min-width: 300px;"
                    ),
                    ui.div(
                        ui.div(
                            ui.h4("🔐 SYSTEM + RECON (OUTSTANDING)", style="font-size: 14px; font-weight: 800; color: #1A202C; margin: 0;"),
                            ui.download_button("btn_dl_so_rec_sys", ui.tags.span(ui.tags.i(class_="fa-solid fa-download", style="margin-right: 6px; font-size: 13px;"), "Download (.xlsx)"), style="background-color: #10B981; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 4px 10px; cursor: pointer; font-size: 12px;"),
                            style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 0.5rem;"
                        ),
                        render_clean_table(state.df_so_rec_sys_headers(), state.df_so_rec_sys_rows(), "tbl_so_rec_sys"),
                        style="flex: 1; min-width: 300px;"
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
                    onclick="document.body.classList.add('process-running'); Shiny.setInputValue('btn_run_so_step2', Math.random(), {priority: 'event'});",
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
            state._raw_df_so_rec_real.to_excel(writer, sheet_name='REAL_PLUS_RECON', index=False)
        buf.seek(0)
        yield buf.getvalue()

    @render.download(filename="Report_System_Plus_Recon.xlsx")
    def btn_dl_so_rec_sys():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            state._raw_df_so_rec_sys.to_excel(writer, sheet_name='SYSTEM_PLUS_RECON', index=False)
        buf.seek(0)
        yield buf.getvalue()

    # --- STEP 4: FINAL ADJUSTMENT + PROCESS ---
    @render.ui
    def so_step4_card_ui():
        if not state.so_step2_done(): return ui.div()
        step4_results = ui.div()
        if state.so_step4_done():
            # Setup real content
            if state.so_step4_setup_done():
                setup_content = ui.div(
                    ui.div(
                        ui.download_button("btn_dl_so_setup4", ui.tags.span(ui.tags.i(class_="fa-solid fa-download", style="margin-right: 6px; font-size: 13px;"), "Download Set Up Real + (.xlsx)"), style="background-color: #10B981; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 6px 12px; cursor: pointer; font-size: 13px;"),
                        style="display: flex; justify-content: flex-end; width: 100%; margin-bottom: 0.5rem;"
                    ),
                    render_clean_table(state.df_so_setup4_headers(), state.df_so_setup4_rows(), "tbl_so_setup4")
                )
            else:
                setup_content = ui.div(
                    ui.p("➡️ Klik tombol di bawah untuk membuat relokasi mutasi ke STAGING INBOUND:", style="color: #4A5568; font-weight: 600; margin-bottom: 0.75rem;"),
                    ui.tags.button(
                        ui.tags.span(ui.tags.i(class_="fa-solid fa-arrows-split-up-and-left", style="margin-right: 6px; font-size: 14px;"), "GENERATE SET UP REAL +"),
                        onclick="document.body.classList.add('process-running'); Shiny.setInputValue('btn_run_so_step4_setup', Math.random(), {priority: 'event'});",
                        class_="btn-red-gradient"
                    )
                )

            step4_results = ui.div(
                ui.hr(style="margin: 1rem 0; border-color: #E2E8F0;"),
                ui.navset_card_tab(
                    ui.nav_panel(
                        "📦 MULTIPLE ADJ +",
                        ui.div(
                            ui.div(ui.download_button("btn_dl_so_mult", ui.tags.span(ui.tags.i(class_="fa-solid fa-download", style="margin-right: 6px; font-size: 13px;"), "Download Multiple Adj + (.xlsx)"), style="background-color: #10B981; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 6px 12px; cursor: pointer; font-size: 13px;"), style="display: flex; justify-content: flex-end; width: 100%; margin-bottom: 0.5rem;"),
                            render_clean_table(state.df_so_mult_headers(), state.df_so_mult_rows(), "tbl_so_mult"),
                            style="padding: 0.75rem 0;"
                        )
                    ),
                    ui.nav_panel(
                        "⚠️ SINGLE ADJ +",
                        ui.div(
                            ui.div(ui.download_button("btn_dl_so_sing", ui.tags.span(ui.tags.i(class_="fa-solid fa-download", style="margin-right: 6px; font-size: 13px;"), "Download Single Adj + (.xlsx)"), style="background-color: #10B981; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 6px 12px; cursor: pointer; font-size: 13px;"), style="display: flex; justify-content: flex-end; width: 100%; margin-bottom: 0.5rem;"),
                            render_clean_table(state.df_so_sing_headers(), state.df_so_sing_rows(), "tbl_so_sing"),
                            style="padding: 0.75rem 0;"
                        )
                    ),
                    ui.nav_panel(
                        "🔍 CEK ADJ + RESULT",
                        ui.div(
                            ui.div(ui.download_button("btn_dl_so_res4", ui.tags.span(ui.tags.i(class_="fa-solid fa-download", style="margin-right: 6px; font-size: 13px;"), "Download Hasil Cek Adj + (.xlsx)"), style="background-color: #10B981; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 6px 12px; cursor: pointer; font-size: 13px;"), style="display: flex; justify-content: flex-end; width: 100%; margin-bottom: 0.5rem;"),
                            render_clean_table(state.df_so_res4_headers(), state.df_so_res4_rows(), "tbl_so_res4"),
                            style="padding: 0.75rem 0;"
                        )
                    ),
                    ui.nav_panel("➡️ SET UP REAL +", ui.div(setup_content, style="padding: 0.75rem 0;")),
                    ui.nav_panel(
                        "❌ Miss Lookup SKU on BIN",
                        ui.div(
                            ui.div(ui.download_button("btn_dl_so_miss4", ui.tags.span(ui.tags.i(class_="fa-solid fa-download", style="margin-right: 6px; font-size: 13px;"), "Download Missing Items (.xlsx)"), style="background-color: #E50914; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 6px 12px; cursor: pointer; font-size: 13px;"), style="display: flex; justify-content: flex-end; width: 100%; margin-bottom: 0.5rem;"),
                            render_clean_table(state.df_so_miss4_headers(), state.df_so_miss4_rows(), "tbl_so_miss4"),
                            style="padding: 0.75rem 0;"
                        )
                    )
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

    @reactive.Effect
    @reactive.event(input.btn_run_so_step4)
    def _proc_so_step4():
        f1, f2, f3 = input.so_up_r4(), input.so_up_s4(), input.so_up_m5()
        if not f1 or not f2 or not f3:
            state.error_modal_message.set("Pilih ketiga file (Real+ Recon, Cek Stock Adj+, Staging Inbound) terlebih dahulu!")
            state.show_error_modal.set(True)
            return
        succ, msg = state.run_so_step4(f1, f2, f3)
        if succ: state.show_success_modal.set(True)
        else:
            state.error_modal_message.set(msg)
            state.show_error_modal.set(True)

    @reactive.Effect
    @reactive.event(input.btn_run_so_step4_setup)
    def _proc_so_step4_setup():
        succ, msg = state.run_so_step4_setup_real()
        if succ: state.show_success_modal.set(True)
        else:
            state.error_modal_message.set(msg)
            state.show_error_modal.set(True)

    @render.download(filename="final_adj_multiple.xlsx")
    def btn_dl_so_mult():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            state._raw_df_so_mult.to_excel(writer, sheet_name='MULTIPLE_ADJ_PLUS', index=False)
        buf.seek(0)
        yield buf.getvalue()

    @render.download(filename="final_adj_single.xlsx")
    def btn_dl_so_sing():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            state._raw_df_so_sing.to_excel(writer, sheet_name='SINGLE_ADJ_PLUS', index=False)
        buf.seek(0)
        yield buf.getvalue()

    @render.download(filename="hasil_lookup_full.xlsx")
    def btn_dl_so_res4():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            state._raw_df_so_res4.to_excel(writer, sheet_name='CEK_ADJ_RESULT', index=False)
        buf.seek(0)
        yield buf.getvalue()

    @render.download(filename="set_up_real_plus.xlsx")
    def btn_dl_so_setup4():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            state._raw_df_so_setup4.to_excel(writer, sheet_name='SET_UP_REAL_PLUS', index=False)
        buf.seek(0)
        yield buf.getvalue()

    @render.download(filename="missing_items_recon.xlsx")
    def btn_dl_so_miss4():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            state._raw_df_so_miss4.to_excel(writer, sheet_name='MISSING_ITEMS', index=False)
        buf.seek(0)
        yield buf.getvalue()

    # --- STEP 5: RECON SYSTEM + (SET UP KARANTINA) ---
    @render.ui
    def so_step5_card_ui():
        if not state.so_step4_done(): return ui.div()
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
        f1, f2 = input.so_up_k6(), input.so_up_adj6()
        if not f1 or not f2:
            state.error_modal_message.set("Pilih kedua file (System+ Recon & Stock Cek Adj-) terlebih dahulu!")
            state.show_error_modal.set(True)
            return
        succ, msg = state.run_so_step5(f1, f2)
        if succ: state.show_success_modal.set(True)
        else:
            state.error_modal_message.set(msg)
            state.show_error_modal.set(True)

    @render.download(filename="Karantina_SO.xlsx")
    def btn_dl_so_karantina():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            state._raw_df_so_karantina.to_excel(writer, sheet_name='Karantina', index=False)
            state._raw_df_so_check5.to_excel(writer, sheet_name='Data_Pengecekan_Audit', index=False)
        buf.seek(0)
        yield buf.getvalue()

    # --- STEP 6: MISS LOCATION, SUMMARY ADJ, & MASTER REPORT ---
    @render.ui
    def so_step6_card_ui():
        if not state.so_step5_done(): return ui.div()

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
    # JUSTIFICATION SO CONTROLLER & HANDLERS
    # ==========================================================================

    @render.ui
    def justification_so_action_btn_ui():
        f1 = input.uploader_jso_case() if "uploader_jso_case" in input else None
        f2 = input.uploader_jso_track() if "uploader_jso_track" in input else None
        f3 = input.uploader_jso_all() if "uploader_jso_all" in input else None

        # Jika 3 file utama sudah di-upload -> Tombol Merah Aktif
        if (f1 and len(f1) > 0) and (f2 and len(f2) > 0) and (f3 and len(f3) > 0):
            return ui.div(
                ui.tags.button(
                    ui.tags.span(ui.tags.i(class_="fa-solid fa-play", style="margin-right: 6px; font-size: 14px;"), "RUN COMPARE JUSTIFICATION"),
                    onclick="document.body.classList.add('process-running'); Shiny.setInputValue('btn_run_jso', Math.random(), {priority: 'event'});",
                    class_="btn-red-gradient"
                ),
                style="display: flex; justify-content: flex-end; width: 100%; margin-top: 0.5rem;"
            )
        # Jika belum lengkap -> Tombol Terkunci Transparan
        return ui.div(
            ui.tags.button(
                ui.tags.i(class_="fa-solid fa-lock", style="margin-right: 6px; font-size: 14px;"),
                "UPLOAD 3 FILE UTAMA UNTUK MEMULAI",
                disabled=True,
                class_="btn-locked"
            ),
            style="display: flex; justify-content: flex-end; width: 100%; margin-top: 0.5rem;"
        )

    @render.ui
    def justification_so_results_container():
        if not state.jso_processed(): return ui.div()
        return ui.div(
            ui.hr(style="margin: 1rem 0; border-color: #E2E8F0;"),
            ui.h4("📋 RINGKASAN METRIK JUSTIFIKASI ADJUSTMENT", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 1rem;"),
            ui.div(
                dark_metric_box("❓ UNDEFINED", f"{state.jso_c_undef():,} SKU", "#DD6B20"),
                dark_metric_box("💻 SYS ERROR", f"{state.jso_c_sys():,} SKU", "#E53E3E"),
                dark_metric_box("❌ KESALAHAN ADJ", f"{state.jso_c_adj():,} SKU", "#E53E3E"),
                dark_metric_box("🗳️ KESALAHAN RTO", f"{state.jso_c_rto():,} SKU", "#3182CE"),
                dark_metric_box("🔁 CEK REKON", f"{state.jso_c_rekon():,} SKU", "#C5A059"),
                style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; width: 100%; margin-bottom: 1.25rem;"
            ),
            ui.div(
                ui.div(
                    ui.h4("📋 Ringkasan Hasil Analisis Justifikasi", style="font-size: 15px; font-weight: 800; color: #1A202C; margin: 0;"),
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

    @reactive.Effect
    @reactive.event(input.btn_run_jso)
    def _proc_jso():
        f1 = input.uploader_jso_case()
        f2 = input.uploader_jso_track()
        f3 = input.uploader_jso_all()
        f4 = input.uploader_jso_scan()

        if not f1 or not f2 or not f3:
            state.error_modal_message.set("Pilih ketiga file utama (File Adjustment, Summary Stock, All Data Stock) terlebih dahulu!")
            state.show_error_modal.set(True)
            return

        succ, msg = state.process_justification_so(f1, f2, f3, f4)
        if succ: state.show_success_modal.set(True)
        else:
            state.error_modal_message.set(msg)
            state.show_error_modal.set(True)

    @render.download(filename="rekon_stock_so.xlsx")
    def btn_dl_jso_excel():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            state._raw_df_jso_res.to_excel(writer, sheet_name='Summary', index=False)
        buf.seek(0)
        yield buf.getvalue()

app = App(app_ui, server)