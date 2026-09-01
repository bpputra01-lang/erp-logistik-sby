import sys
from pathlib import Path

# 1. WAJIB DI PALING ATAS (Sebelum import file lokal manapun)
sys.path.insert(0, str(Path(__file__).parent.resolve()))

# 2. Package Library
import io
import uuid
import pandas as pd
from datetime import datetime, timedelta
from shiny import App, Inputs, Outputs, Session, reactive, render, ui


# 3. File Lokal Proyek Anda
import config
import state
from state import AppState, active_users

# 4. Import komponen UI dari views.py
from views import (
    # Komponen Dasar & Modal
    CUSTOM_HEAD, static_loading_spinner, success_modal, error_modal,
    render_clean_table, metric_box, dark_metric_box, BRANCH_BIN_MAPPING, 
    custom_uploader_box, sidebar, login_page, global_header, create_ui,

    # 10 Menu Awal
    main_dashboard_view, ongkir_tab2_view, stock_minus_view, putaway_view, 
    compare_system_view, cycle_count_view, ppa_audit_view, 
    cycle_count_analyzer_view, compare_rto_view, stock_opname_view, 
    justification_so_view,

    # 14 Menu Baru Lengkap
    po_receiving_view, penerimaan_rto_view, scan_out_view,
    refill_overstock_view, balancing_stock_view, fl_request_view,
    refill_toko_view, rto_decision_view, match_karantina_view,
    koli_consolidation_view, stock_allocation_view, refill_withdraw_view,
    fdr_update_view, percentage_display_view, stock_tracking_view,
    retur_out_view, pengajuan_mutasi_view, pengajuan_reject_view,
    reject_list_view, logistic_schedule_view, reporting_pic_view,
    timbang_ongkir_view
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
    
    # Buat ID unik untuk laptop/browser ini
    session_id = str(uuid.uuid4())

    # 1. Hapus session saat browser ditutup
    @session.on_ended
    def _on_session_ended():
        config.remove_active_user(session_id)

    # 2. Polling Heartbeat ke Supabase & Tampilkan User Aktif Global
    @render.text
    def txt_active_users():
        # Otomatis refresh data setiap 15 detik
        reactive.invalidate_later(15)
        
        # Kirim sinyal online
        user_name = state.user_display_name() if state.logged_in() else "Tamu"
        config.ping_active_user(session_id, user_name)
        
        # Ambil total user aktif di semua laptop dari Supabase
        total_online = config.count_online_users()
        return f"{total_online} User Aktif"
    

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
    @reactive.event(input.change_filter_tgl_start)
    def _update_tgl_start():
        state.filter_tgl_start.set(str(input.change_filter_tgl_start() or ""))

    @reactive.Effect
    @reactive.event(input.change_filter_tgl_end)
    def _update_tgl_end():
        state.filter_tgl_end.set(str(input.change_filter_tgl_end() or ""))

    @reactive.Effect
    @reactive.event(input.btn_reset_filter_tgl)
    def _reset_filter_tgl():
        state.filter_tgl_start.set("")
        state.filter_tgl_end.set("")
        state.filter_ekspedisi.set("SEMUA")

    @reactive.Effect
    @reactive.event(input.btn_toggle_sidebar)
    def _side_toggle(): state.toggle_sidebar()

    @reactive.Effect
    @reactive.event(input.toggle_dropdown_section)
    def _drop_toggle(): state.toggle_dropdown(input.toggle_dropdown_section())

    # =========================================================================
    # ACTION LISTENERS TOMBOL "RUN / PROSES" MENU BARU
    # =========================================================================

    # 1. PO Receiving
    @reactive.Effect
    @reactive.event(input.btn_run_po_rec)
    def _proc_po_rec():
        succ, msg = state.run_po_receiving(input.uploader_po_scan(), input.uploader_po_file())
        if succ: state.show_success_modal.set(True)
        else: state.error_modal_message.set(msg); state.show_error_modal.set(True)

    # 2. Penerimaan RTO
    @reactive.Effect
    @reactive.event(input.btn_run_penerimaan_rto)
    def _proc_rto_rec():
        succ, msg = state.run_penerimaan_rto(input.uploader_rto_rec_scan(), input.uploader_rto_rec_tf())
        if succ: state.show_success_modal.set(True)
        else: state.error_modal_message.set(msg); state.show_error_modal.set(True)

    # 3. Scan Out Validation
    @reactive.Effect
    @reactive.event(input.btn_run_scan_out)
    def _proc_scan_out():
        succ, msg = state.run_scan_out(input.uploader_so_scan(), input.uploader_so_hist(), input.uploader_so_track())
        if succ: state.show_success_modal.set(True)
        else: state.error_modal_message.set(msg); state.show_error_modal.set(True)

    # 4. Refill & Overstock
    @reactive.Effect
    @reactive.event(input.btn_run_rf_os)
    def _proc_rf_os():
        succ, msg = state.run_refill_overstock(input.uploader_rf_os_stock())
        if succ: state.show_success_modal.set(True)
        else: state.error_modal_message.set(msg); state.show_error_modal.set(True)

    # 5. Balancing Stock
    @reactive.Effect
    @reactive.event(input.btn_run_bal_stock)
    def _proc_bal_stock():
        succ, msg = state.run_balancing_stock(input.uploader_bal_stock())
        if succ: state.show_success_modal.set(True)
        else: state.error_modal_message.set(msg); state.show_error_modal.set(True)

    # 6. Permintaan FL
    @reactive.Effect
    @reactive.event(input.btn_run_fl_req)
    def _proc_fl_req():
        succ, msg = state.run_fl_request(input.uploader_fl_stock(), input.uploader_fl_req())
        if succ: state.show_success_modal.set(True)
        else: state.error_modal_message.set(msg); state.show_error_modal.set(True)

    # 7. Refill Toko
    @reactive.Effect
    @reactive.event(input.btn_run_refill_toko)
    def _proc_refill_toko():
        f = input.uploader_refill_stock()
        succ, msg = state.process_refill_toko(f)
        if succ: state.show_success_modal.set(True)
        else: state.error_modal_message.set(msg); state.show_error_modal.set(True)

    # 8. Store Leader RTO Decision
    @reactive.Effect
    @reactive.event(input.btn_run_rto_decision)
    def _proc_rto_dec():
        f1, f2 = input.uploader_rto_sby(), input.uploader_rto_smg()
        f3, f4 = input.uploader_rto_sales(), input.uploader_rto_toc()
        succ, msg = state.process_rto_decision(f1, f2, f3, f4)
        if succ: state.show_success_modal.set(True)
        else: state.error_modal_message.set(msg); state.show_error_modal.set(True)

    # 9. Match Real & System
    @reactive.Effect
    @reactive.event(input.btn_run_match_ks)
    def _proc_match_ks():
        succ, msg = state.run_match_karantina(input.uploader_match_sys(), input.uploader_match_real())
        if succ: state.show_success_modal.set(True)
        else: state.error_modal_message.set(msg); state.show_error_modal.set(True)

    # 10. Refill Koli
    @reactive.Effect
    @reactive.event(input.btn_run_koli_conso)
    def _proc_koli():
        succ, msg = state.run_koli_consolidation(input.uploader_koli_file())
        if succ: state.show_success_modal.set(True)
        else: state.error_modal_message.set(msg); state.show_error_modal.set(True)

    # 11. Stock Allocation
    @reactive.Effect
    @reactive.event(input.btn_run_stk_alloc)
    def _proc_stk_alloc():
        succ, msg = state.process_stock_allocation(input.uploader_alloc_stock(), input.uploader_alloc_sales())
        if succ: state.show_success_modal.set(True)
        else: state.error_modal_message.set(msg); state.show_error_modal.set(True)

    # 12. Refill & Withdraw
    @reactive.Effect
    @reactive.event(input.btn_run_rf_wd)
    def _proc_rf_wd():
        succ, msg = state.run_refill_withdraw(input.uploader_rwd_stock(), input.uploader_rwd_trx())
        if succ: state.show_success_modal.set(True)
        else: state.error_modal_message.set(msg); state.show_error_modal.set(True)

    # 13. FDR Update
    @reactive.Effect
    @reactive.event(input.btn_run_fdr)
    def _proc_fdr():
        succ, msg = state.run_fdr_update(input.uploader_fdr_file())
        if succ: state.show_success_modal.set(True)
        else: state.error_modal_message.set(msg); state.show_error_modal.set(True)

    # 14. Percentage Display
    @reactive.Effect
    @reactive.event(input.btn_run_disp_ctrl)
    def _proc_disp_ctrl():
        succ, msg = state.run_percentage_display(input.uploader_disp_stock())
        if succ: state.show_success_modal.set(True)
        else: state.error_modal_message.set(msg); state.show_error_modal.set(True)
   # =========================================================================
    # HANDLER PANDUAN & LOGIC (100% KATA & ISI PERSIS DARI STREAMLIT ASLI)
    # =========================================================================
    @reactive.Effect
    @reactive.event(input.btn_open_panduan_modal)
    def _open_panduan_modal():
        cur = state.main_menu()
        
        guides = {
            # --- 1. STOCK MINUS ---
            "Stock Minus": """
                <b>📋 Informasi Format File</b><br>
                <b>Format yang diharapkan:</b><br>
                - <b>All Data Stock:</b> Download Multiple Adjusmet dari Jezpro dan pilih <b>Termasuk yang sudah habis</b><br><br>
                <hr style='margin: 8px 0; border-color: #E2E8F0;'>
                <b>💡 Logic Thinking</b><br>
                <b>Alur Process Compare Stock Minus:</b><br>
                - Mengambil SKU yang memiliki Qty System minus (-)<br>
                - Lalu SKU yang memiliki QTY Minus (-) tersebut akan di lakukan shuffle covering Stock<br>
                - Dimana terdapat Bin prioritas untuk shuffle Covering Stock (All Stagging, Karantina)<br>
                - Dan jika minus terjadi di Gudang lt.2 maka akan prioritas mengambil BIN Toko begitupun sebaliknya<br>
                - Lalu jika tidak ditemukan di BIN Prioritas maka akan mengambil random BIN kecuali LIVE, Offline dan Online<br>
                - Jika sudah ditemukan SKU dan Qty yang bisa covering maka akan dibuatkan list Set up<br>
                - Dan jika tidak bisa diselesaikan lewat set up maka sistem akan memasukkan kedalam item need justifikasi dan perlu analisa lebih lanjut
            """,

            # --- 2. PUTAWAY SYSTEM ---
            "Putaway System": """
                <b>📋 Informasi Format File</b><br>
                <b>Format yang diharapkan:</b><br>
                - <b>DATA SCAN PUTAWAY:</b> Kolom A = <b>BIN</b>, Kolom B = <b>SKU</b>, Kolom C = <b>QTY SCAN</b><br>
                - <b>DATA PUTAWAY:</b> Sesuai yang ada pada template Jezpro.<br><br>
                <hr style='margin: 8px 0; border-color: #E2E8F0;'>
                <b>💡 Logic Thinking</b><br>
                <b>Alur Compare Putaway:</b><br>
                - SKU di file data scan akan dicompare dengan SKU yang ada di FIle data BIN Putaway<br>
                - Tiap unique SKU teratas di File data scan akan mendapatkan alokasi penuh<br>
                - Untuk SKU yang tidak mendapatkan alokasi maka akan ditulis dengan note <b>PERLU CEK MANUAL</b> untuk mengetahui apakah ada double data scan atau item belum terset up di BIN PUTAWAY<br>
                - List Set up akan dibuatkan otomatis oleh system dengan BIN awal diambil dari BIN di file Putaway dan BIN tujuan disesuaikan dengan BIN yang ada di data scan
            """,

            # --- 3. COMPARE SYSTEM ---
            "Compare System": """
                <b>📋 Informasi Format File & Kolom Mapping</b><br>
                <b>Kondisi Stok Berkurang (Sys1 > Sys2):</b><br>
                1. <b>Stock Tracking:</b> Kolom A=Invoice, Kolom B=SKU, Kolom G=BIN, Kolom K=Qty (Index 10).<br>
                2. <b>RTO Out:</b> Kolom D=No TF, Kolom I=SKU, Kolom J=Qty (Index 9).<br><br>
                <b>Kondisi Stok Bertambah (Sys2 > Sys1):</b><br>
                1. <b>Purchase Order:</b> Kolom A=No PO, Kolom D=SKU, Kolom L=Qty (Index 11).<br>
                2. <b>RTO In:</b> Kolom D=No TF, Kolom I=SKU, Kolom K=Qty (Index 10).<br>
                3. <b>Mutasi Refund:</b> Kolom D=SKU (Index 3), Kolom K=Qty (Index 10).
            """,

            # --- 4. CYCLE COUNT ANALYZER ---
            "Cycle Count": """
                <b>📋 Informasi Format File</b><br>
                <b>Format yang diharapkan:</b><br>
                - <b>FILTER</b><br>
                    - <b>SUB KATEGORI:</b> Untuk Sub Kategori pilih sesuai dengan kategori yang sedang dianalisa<br>
                    - <b>BIN SYSTEM:</b> Untuk BIN system pilih sesuai dengan bin yang sedang dianalisa<br>
                    - <b>BRAND:</b> Untuk BRAND pilih sesuai dengan brand yang sedang dianalisa<br>
                    - <b>BIN COVERAGE:</b> Untuk BIN COVERAGE sementara non aktifkan dulu dan jangan dipilih<br>
                - <b>COMPARE DS VS STOCK SYSTEM</b><br>
                    - <b>DATA SCAN:</b> Upload data scan SO yang sudah diberi header :<br>
                        - <b>Kolom A</b> = BIN<br>
                        - <b>Kolom B</b> = SKU<br>
                        - <b>Kolom C</b> = QTY SCAN<br>
                    - <b>STOCK SYSTEM:</b> Download All stock dari <b>Multiple Adjusment</b> dan pilih <b>Termasuk yang sudah habis</b><br>
                - <b>BIN COVERAGE:</b> Download Bin Coverage dari <b>Multiple Adjusment</b>, Pilih stocknya <b>Hanya ada di stock</b><br>
                - <b>RECON REAL + PROCESS:</b> Upload file Recon Real + yang sudah didownload dari step sebelumnya pastikan <b>KOLOM A</b> bukan berisi <b>NUMBER</b> ➔ jika berisi Number maka hapus dulu kolomnya sebelum diupload<br>
                - <b>SET UP KARANTINA GENERATOR:</b><br>
                    - <b>SYTEM + RECON:</b> Upload file Recon System + yang sudah didownload dari step sebelumnya pastikan <b>KOLOM A</b> bukan berisi <b>NUMBER</b> ➔ jika berisi Number maka hapus dulu kolomnya sebelum diupload<br>
                    - <b>CEK STOCK ADJ -:</b> Download Stock System yang terbaru dari <b>Multiple Adjusment</b> dan pilih <b>Termasuk yang sudah habis</b><br><br>
                <hr style='margin: 8px 0; border-color: #E2E8F0;'>
                <b>💡 Logic Thinking</b><br>
                <b>DS VS Stock System :</b><br>
                - <b>REAL +:</b> Compare antara SKU dan BIN yang ada di data scan dengan SKU dan BIN yang ada di Stock System dimana logic yang digunakan menggunakan loigc rumus (SUMIFS). Fokus di file Data Scan karena yang akan menjadi acuan untuk Real +. Apabila <b>QTY SCAN > QTY SYSTEM</b> maka yang akan dijadikan sebagai Real +.<br>
                - <b>SYSTEM +:</b> Jika tadi berfokus pada file Data maka untuk system + berfokus pada file Stock System. Apabila <b>QTY SYSTEM > QTY SCAN</b> maka akan dijadikan sebagai System +.<br><br>
                <b>ALLOCATION REAL + :</b><br>
                - <b>BIN COVERAGE:</b> Compare antara SKU yang ada di Real + dengan SKU yang ada BIN Coverage jika SKU ditemukan maka akan diambil untuk cover system di REAL +. Jika DIFF real + dapat tercover penuh maka akan diberi note <b>FULL ALLOCATION</b>, jika tercover sebagian <b>PARTIAL ALLOCATION</b>, dan jika tidak tercover <b>NO ALLOCATION</b>.<br>
                - <b>SYSTEM +:</b> Item memiliki note <b>NO ALLOCATION</b> maka apabila tidak ditemukan di BIN COVERAGE akan mencari SKU yang cocok di system +.<br>
                - <b>SET UP ALLOCATION:</b> Item dengan note <b>FULL ALLOCATION</b> dan <b>PARTIAL ALLOCATION</b> akan dibuatkan list set up dengan note Relocation.<br><br>
                <b>RECON REAL + & SYSTEM + :</b><br>
                - <b>RECON REAL +:</b> Item yang memiliki note <b>NO ALLOCATION</b> akan kembali di lakukan rekonsiliasi. Jika <b>Real yang ditemukan = stock system</b> maka tidak akan dimasukkan ke list adjusment. Jika <b>Real yang ditemukan > stock system</b> maka akan dimasukkan ke list adjusment.<br>
                - <b>RECON SYSTEM +:</b> System + yang DIFF nya belum teralokasi akan dilakukan rekonsiliasi. Jika <b>Real yang ditemukan = stock system</b> maka tidak akan dimasukkan ke list adjusment. Jika <b>Real yang ditemukan < stock system</b> maka akan dimasukkan ke list adjusment.<br>
                - <b>CEK STOCK ADJUSMENT:</b> File Cek adjusment tadi yang sudah di download bisa dimasukkan kembali dengan sumifs kemudian mengambil diffnya. Jika DIFF > 0 maka akan dilakukan mutasi ke <b>BIN KARANTINA</b>.<br>
                - <b>SET UP KARANTINA:</b> System akan membuatkan list set up untuk DIFF > 0 dan akan diberikan note <b>MISS LOCATION</b>.<br><br>
                <b>TOTAL MISS LOCATION :</b><br>
                - Cek total missloc diambil dari berapa banyak SKU dan QTY yang memiliki note <b>FULL ALLOCATION & PARTIAL ALLOCATION</b> pada logic Allocation real +.
            """,

            # --- 5. STOCK OPNAME ---
            "Stock Opname": """
                <b>📋 Informasi Format File</b><br>
                <b>Format yang diharapkan:</b><br>
                - <b>FILTER:</b> SUB KATEGORI, BIN SYSTEM, BIN COVERAGE (sementara non aktifkan dulu).<br>
                - <b>COMPARE DS VS STOCK SYSTEM:</b><br>
                    - <b>DATA SCAN:</b> Upload data scan SO (Kolom A = BIN, Kolom B = SKU, Kolom C = QTY SCAN)<br>
                    - <b>STOCK SYSTEM:</b> Download All stock dari <b>Multiple Adjusment</b> dan pilih <b>Termasuk yang sudah habis</b><br>
                - <b>BIN COVERAGE:</b> Download Bin Coverage (ALL BIN DEFAULT & KARANTINA) dari <b>Multiple Adjusment</b> (Pilih stocknya <b>Hanya ada di stock</b>)<br>
                - <b>FINAL ADJUSMENT + PROCESS:</b><br>
                    - <b>REAL + RECON:</b> Upload file Recon Real + (pastikan KOLOM A bukan berisi NUMBER)<br>
                    - <b>CEK STOCK ADJ +:</b> Download Stock System terbaru dari <b>Multiple Adjusment</b> (Termasuk yang sudah habis)<br>
                    - <b>File Stagging Inbound:</b> Download Stock System dan pilih hanya <i>BIN STAGGING INBOUND</i> (Termasuk yang sudah habis)<br>
                - <b>SET UP KARANTINA GENERATOR:</b> SYTEM + RECON & CEK STOCK ADJ - (Termasuk yang sudah habis)<br>
                - <b>SUMMARY ADJUSMENT REPORT:</b> OPSI 1 (Langsung klik tanpa upload), OPSI 2 (Gabungkan All Adj+), OPSI 3 (Gabungkan All Adj-), OPSI 4 (Gabungkan All Adj+ & -)<br><br>
                <hr style='margin: 8px 0; border-color: #E2E8F0;'>
                <b>💡 Logic Thinking</b><br>
                - <b>REAL +:</b> QTY SCAN > QTY SYSTEM (Fokus Data Scan)<br>
                - <b>SYSTEM +:</b> QTY SYSTEM > QTY SCAN (Fokus Stock System)<br>
                - <b>ALLOCATION REAL +:</b> Cover dari BIN Coverage (FULL/PARTIAL/NO ALLOCATION) ➔ Set Up Relocation.<br>
                - <b>FILE INBOUND:</b> Selisih dari lookup dimasukkan ke dalam file inbound untuk proses adjusment.<br>
                - <b>SET UP KARANTINA:</b> DIFF > 0 dimutasi ke BIN KARANTINA dengan note <b>MISS LOCATION</b>.<br>
                - <b>TOTAL MISS LOCATION:</b> Total SKU & QTY yang memiliki note FULL & PARTIAL ALLOCATION.<br>
                - <b>VALUE ADJUSMENT:</b> Cek Value Adjusment sebagai report dan analisa SO diperiode tersebut.
            """,

            # --- 6. JUSTIFICATION SO ---
            "Justification SO": """
                <b>📋 Informasi Format File</b><br>
                <b>Format yang diharapkan:</b><br>
                - <b>ADJUSTMENT FILE:</b> Gabungkan antara Multiple Adjustment <b>(Plus)</b> dan <b>(Minus)</b> dalam 1 File.<br>
                - <b>SUMMARY STOCK:</b> Download dari <b>JEZPRO</b> pada menu <b>Dashboard Asset</b> (Store: <b>JEZ SURABAYA</b>).<br>
                - <b>ALL DATA STOCK:</b> Upload file All data Stock (Multiple Adjustment) <b>HANYA ADA STOCK</b>.<br>
                - <b>DATA SCAN (Opsional):</b> Jika diupload maka perhitungan <b>Real QTY</b> akan mengambil qty dari data scan dan apabila tidak dipload maka akan kembali perhitungan awal.<br><br>
                <hr style='margin: 8px 0; border-color: #E2E8F0;'>
                <b>💡 Logic Thinking (Justification)</b><br>
                <b>REAL QTY / HITUNGAN MANUAL ➔ :</b> <code>BEGINNING STOCK + (TOTAL_STOCKIN + TOTAL TRF_IN) - (TOTAL SALES + TOTAL TRF_OUT + TOTAL DRAFT TRF_OUT)</code><br><br>
                <b>🛑 1. Kesalahan System (Begin Stock Minus)</b><br>
                * <b>Kondisinya:</b> Stok SO lebih besar dari stok Sistem (ADJUSMENT +), Tetapi <i>Beginning Stock</i> bernilai minus (dibawah 0).<br>
                * <b>Artinya:</b> Sistem dari awal sudah eror/bocor datanya karena mencatat stok minus yang artinya memang perlu dilakukan <i>Adjusment +</i><br><br>
                <b>🛡️ 2. Kesalahan System (Ending Stock ≠ Total Stock dari Multiple)</b><br>
                * <b>Kondisinya:</b> <code>GAP ADJUSTMENT</code> dan <code>BEGINNING STOCK</code> sama-sama nol, Total stock antara (<code>Ending Stock</code>, <code>Real Qty</code>, <code>Current Stock</code>) nilainya sama (senilai), tapi total stock di multiple (<code>QTY SYSTEM ALL</code>) malah lebih kecil dari stok akhir.<br>
                * <b>Artinya:</b> Ada miss match antara data di multiple dan summary sehingga menyebabkan adjusment +<br><br>
                <b>⚙️ 3. Kesalahan System (Miss Match Real QTY dengan Ending Stock/Current Stock)</b><br>
                * <b>Kondisinya:</b> Stok SO lebih besar dari stok Sistem (ADJUSMENT +), tidak ada transaksi gantung (<code>Draft TRF</code>), tidak ada <code>GAP ADJUSTMENT</code>, <b>TAPI</b> hasil hitungan manual tidak match dengan nilai <code>ENDING STOCK</code> di sistem.<br>
                * <b>Detail Hitungan Manual:</b> <code>BEGINNING STOCK + (TOTAL_STOCKIN + TOTAL TRF_IN) - (TOTAL SALES + TOTAL TRF_OUT)</code><br>
                * <b>Artinya:</b> Sistem salah hitung mutasi barang.<br><br>
                <b>💻 4. Kesalahan System (Stock System Lost)</b><br>
                * <b>Kondisinya:</b> Tidak ada <code>GAP ADJUSTMENT</code> (<code>= 0</code>), tapi ada selisih antara Sistem dan SO. Ketika selisih itu ditambah/dikurang ke master <code>QTY SYSTEM ALL</code>, hasilnya pas dengan <code>CURRENT STOCK</code>.<br>
                * <b>Artinya:</b> Bug bawaan sistem yang bikin angka di layar tidak update.<br><br>
                <b>🔍 5. Cek Hasil Rekonsiliasi</b><br>
                * <b>Kondisinya:</b> Total stock di multiple (<code>QTY SYSTEM ALL</code>) ternyata pas/sama persis dengan <code>CURRENT STOCK</code> / <code>ENDING STOCK</code>.<br>
                * <b>Artinya:</b> Data sebenarnya aman dan sinkron secara total keseluruhan.<br><br>
                <b>⚠️ 6. Kesalahan Adjustment (+ / -)</b><br>
                * <b>Kondisinya:</b> Stok Sistem > Stok SO, tapi ada data <code>GAP ADJUSTMENT</code> positif (+), atau Stok Sistem < Stok SO, tapi ada data <code>GAP ADJUSTMENT</code> negatif (-).<br>
                * <b>Artinya:</b> Koreksi dari Proses Adjusment Sebelumnya (Reversal)<br><br>
                <b>🚚 7. Kesalahan RTO (Barang Gantung)</b><br>
                * <b>Kondisinya:</b> Masih ada angka di kolom <code>TOTAL DRAFT TRF IN</code> atau <code>TOTAL DRAFT TRF OUT</code> yang menggantung (belum di-approve/finish).<br>
                * <b>Artinya:</b> Masalah klasik RTO/mutasi barang yang statusnya masih draf.
            """,

            # --- 7. PURCHASE ORDER RECEIVING ---
            "Purchase Order Receiving": """
                <b>📋 Informasi Format File</b><br>
                <b>Format yang diharapkan:</b><br>
                - <b>DATA SCAN :</b> Pastikan Formatnya headernya di <b>KOLOM A = SKU</b> dan di <b>KOLOM B = QTY SCAN</b><br>
                - <b>PENERIMAAN:</b> Download data <b>PENERIMAAN</b> pilih yang <b>ITEM ORDERED</b><br>
                - Pastikan setelah download <i>Penerimaan</i> pada <b>KOLOM A</b> tambahkan kolom untuk memasukkan <b>NO PO</b>. Jadi kolom A adalah NO PO dan kolom B baru NAME.<br>
                - Jika ada lebih dari 1 NO PO maka gabungkan menjadi satu file dan tetap berikan NO PO sesuai NO PO nya di kolom A.<br><br>
                <hr style='margin: 8px 0; border-color: #E2E8F0;'>
                <b>💡 Logic Thinking</b><br>
                <b>Alur Compare:</b><br>
                - SKU di data scan akan dilakukan compare dengan SKU yang ada di File Purchase Order.<br>
                - SKU teratas di File Purchase Order akan mendapatkan alokasi penuh dari data scan apabila ada > 1 No PO yang memiliki SKU yang sama.<br>
                - Jika di File Penerimaan ada yang tidak mendapatkan alokasi maka akan dilakukan cek ulang dan akan di FU ke Purchasing apabila ada kesalahan input SKU PO atau QTY PO.<br>
                - Jika di File Data Scan ada SKU yang tidak ada di PO maka akan muncul dalam <b>TAB + QTY SCAN > QTY PO</b> dan muncul keterangan <b>Wrong SKU</b>.<br>
                - Jika di File Data Scan ada SKU yang Qty nya > daripada di PO maka akan muncul dalam <b>TAB + QTY SCAN > QTY PO</b> dan muncul keterangan <b>Over Scan</b>.<br>
                - Jika di File Data Scan ada SKU yang Qty nya < daripada di PO maka akan muncul dalam <b>TAB - QTY PO > QTY SCAN</b>.<br><br>
                <b>Keterangan Note:</b><br>
                - <b>FULL ALLOCATION :</b> Kondisi dimana Qty scan dan Qty PO cocok dan sesuai.<br>
                - <b>PARTIAL ALLOCATION :</b> Kondisi dimana Qty scan < dari Qty PO.<br>
                - <b>NO ALLOCATION :</b> Kondisi dimana terdapat indikasi <b>BARANG TIDAK DIKIRIM / BELUM TERSCAN / SALAH INPUT QTY PO</b>.<br>
                - <b>OVER ALLOCATION :</b> Kondisi dimana terdapat Indikasi <b>KELEBIHAN SCAN / KURANG INPUT QTY PO / ADA SUBSTITUT ANTAR SKU</b>.
            """,

            # --- 8. COMPARE PENERIMAAN RTO ---
            "Compare Penerimaan RTO": """
                <b>📋 Informasi Format File</b><br>
                <b>Format yang diharapkan:</b><br>
                - <b>DATA SCAN :</b> Pastikan Formatnya di <b>KOLOM A = SKU</b> dan di <b>KOLOM B = QTY SCAN</b><br>
                - <b>TRANSFER STOCK :</b> Download data <b>Transfer Stock</b> bukan data <b>Penerimaan Transfer Stock</b><br><br>
                <hr style='margin: 8px 0; border-color: #E2E8F0;'>
                <b>💡 Logic Thinking</b><br>
                <b>Alur Compare:</b><br>
                - SKU di data scan akan dilakukan compare dengan SKU yang ada di File Transfer Stock<br>
                - SKU teratas di File Transfer stock akan mendapatkan alokasi penuh dari data scan apabila ada > 1 No TF yang memiliki SKU yang sama<br>
                - Jika di File Stock Transfer ada yang tidak mendapatkan alokasi maka akan dilakukan cek ulang dan akan di FU ke cabang pengirim apabila barang yang datang < TF Stock<br>
                - Jika di File data scan ada SKU yang tidak terdapat di Stock Transfer maka akan dilakukan pengecekan ulang dan akan di FU ke cabang pengirim apabila ada item yang terkirim namun TF stock belum dibuatkan<br><br>
                <b>Keterangan Note:</b><br>
                - <b>FULL ALLOCATION :</b> Kondisi dimana Qty scan dan Qty tf cocok dan sesuai<br>
                - <b>PARTIAL ALLOCATION :</b> Kondisi dimana Qty scan < dari Qty TF<br>
                - <b>NO ALLOCATION :</b> Kondisi dimana terdapat indikasi <b>BARANG TIDAK DIKIRIM / BELUM TERSCAN / LEBIH TF</b> Sehingga di TF <i>ADA</i> Namun di Data Scan <i>TIDAK ADA</i><br>
                - <b>OVER ALLOCATION :</b> Kondisi dimana terdapat Indikasi <b>KELEBIHAN SCAN / KURANG TF</b> Sehingga menyebabkan QTY Scan > QTY TF
            """,

            # --- 9. SCAN OUT VALIDATION ---
            "Scan Out Validation": """
                <b>📋 Informasi Format File</b><br>
                <b>Format yang diharapkan :</b><br>
                - <b>UPLOAD MENGGUNAKAN FILE DATA SCAN (APPSHEET):</b> Kolom A = <b>BIN</b>, Kolom B = <b>SKU</b> (QTY akan dihitung otomatis)<br>
                - <b>UPLOAD MENGGUNAKAN DATA POWER BI:</b> Berikut cara download permintaan FL by PBI<br>
                    - Buka Power BI<br>
                    - Pilih Menu <b>Moving Stock</b><br>
                    - Pilih Tab atau Sheet <b>Detail</b><br>
                    - Lalu untuk Period pilih <b>YESTERDAY</b><br>
                    - Untuk Trx Type pilih <b>Yesterday</b><br>
                    - Untuk Store_stockadj pilih <b>JEZ SURABAYA (DC)</b><br>
                    - Setelah itu Download filenya<br>
                    - <b>File tidak perlu diedit dan bisa langsung di Uplaod</b><br>
                - <b>HISTORY SET UP:</b> Sesuai yang ada pada template Mutasi Set Up Jezpro<br>
                - <b>STOCK TRACKING:</b> Sesuai yang ada pada template Stock Tracking Jezpro<br>
                - <b>PS ➔</b> <i>Pilih salah satu mau menggunakan file data scan dari Appsheet atau dari file PBI</i><br><br>
                <hr style='margin: 8px 0; border-color: #E2E8F0;'>
                <b>💡 Logic Thinking</b><br>
                <b>Alur Compare Scan Out :</b><br>
                - System akan melakukan compare antara BIN dan SKU yang ada di file data scan dengan file History Set Up dan Stock Tracking<br>
                - Jika BIN dan SKU akan langsung melakukan double cek di kedua file mana yang cocok dan sesuai dengan BIN dan SKU yang ada di data scan<br>
                - Jika ditemukan di File Mutasi dan tidak ditemukan di file Stock Tracking maka akan diberikan note <b>DONE AND MATCH SET UP</b><br>
                - Jika ditemukan di File Mutasi dan tidak ditemukan di file Stock Tracking namun BIN tidak sesuai hanya SKUnya saja yang cocok maka akan diberikan note <b>DONE SETUP (BIN MISSMATCH)</b><br>
                - Jika ditemukan di File Mutasi dan tidak ditemukan di file Stock Tracking namun QTY tidak sesuai hanya SKU dan BIN saja yang cocok maka akan diberikan note <b>DONE SET UP (QTY MISSMATCH)</b><br>
                - Jika ditemukan di File Stock Tracking dan tidak ditemukan di file Mutasi maka akan diberikan note <b>ITEM TELAH TERJUAL</b><br>
                - Jika ditemukan di File Stock Tracking dan tidak ditemukan di file Mutasi namun BIN tidak sesuai hanya SKUnya saja yang cocok maka akan diberikan note <b>ITEM TELAH TERJUAL (BIN MISSMATCH)</b><br>
                - Jika ditemukan di File Stock Tracking dan tidak ditemukan di file Mutasi namun QTY tidak sesuai hanya SKU dan BIN saja yang cocok maka akan diberikan note <b>ITEM TELAH TERJUAL (QTY MISSMATCH)</b><br>
                - Jika permintaan item ada > 1 item dan yang terjual hanya 1 maka akan dilakukan split row dimana akan dilakukan pengecekan di kedua file dan akan split note juga menyesuaikan kondisi hasil compare
            """,

            # --- 10. REFILL & OVERSTOCK ---
            "Refill & Overstock": """
                <b>📋 Informasi Format File</b><br>
                <b>Format yang diharapkan:</b><br>
                - <b>ALL DATA STOCK:</b> Pilih <b>HANYA ADA DI STOCK</b><br>
                - <b>STOCK TRACKING (Opsional):</b> Pilih <b>JEZ SURABAYA</b>, rentang 7 hari.<br><br>
                <hr style='margin: 8px 0; border-color: #E2E8F0;'>
                <b>💡 Logic Thinking</b><br>
                <b>Alur Process Refill & Overstock (With Stock Tracking):</b><br>
                - Melakukan Compare antara SKU yang ada di Gudang Lt.4 dengan SKU di Gudang Lt.3 dan sebaliknya<br>
                - List akan dikumpulkan terlebih dahulu dan akan mengambil SKU dengan Qty di Gudang Lt.3 yang < 3 Pcs untuk Refill dan > 12 Pcs untuk overstock<br>
                - Jika data sudah didapatkan maka selanjutnya adalah compare dengan Stock Tracking<br>
                - Compare akan dilakukan dengan mempertimbangkan penjualan Online untuk SKU tersebut<br>
                - Jika penjualan online < 7 pcs maka refill hanya akan mengambil 1/3 dari total stock di GL4 dan akan mengambil 1/3 dari total Diff total stock - 12 Pcs untuk Overstock<br>
                - Jika penjualan online > 7 pcs maka refill akan mengambil 1/2 dari total stock di GL4 dan akan mengambil 1/2 dari total Diff total stock - 12 Pcs untuk Overstock<br>
                - Maksimal kapasitas untuk tiap SKU di GL3 adalah 12 Pcs jadi tidak akan lebih dari 12 tiap SKU di Gl3<br><br>
                <b>Alur Process Refill & Overstock (Without Stock Tracking):</b><br>
                - Melakukan Compare antara SKU yang ada di Gudang Lt.4 dengan SKU di Gudang Lt.3<br>
                - List akan dikumpulkan terlebih dahulu dan akan mengambil SKU dengan Qty di Gudang Lt.3 yang < 3 Pcs dan > 12 Pcs untuk Overstock<br>
                - Sistem akan memksimalkan tiap SKU untuk mendapatkan total 12 Pcs di Gudang lt.3<br>
                - Maksimal kapasitas untuk tiap SKU di GL3 adalah 12 Pcs jadi tidak akan lebih dari 12 tiap SKU di Gl3
            """,

            # --- 11. BALANCING STOCK ---
            "Balancing Stock": """
                <b>📋 Informasi Format File</b><br>
                <b>Format File :</b><br>
                - Download Multiple Adjusment dan pastikan pilih <b>Termasuk yang sudah habis</b><br>
                - Data yang dihasilkan adalah data dari total SKU bukan total QTY jadi yang dihitung adalah unique SKU nya<br>
                - Presentase minimal untuk <b>GL4 ➔ GL3 adalah 100%</b><br>
                - Presentase minimal untuk <b>ALL DC ➔ Store adalah 98%</b><br><br>
                <hr style='margin: 8px 0; border-color: #E2E8F0;'>
                <b>💡 Logic Thinking</b><br>
                <b>Alur Compare :</b><br>
                - <b>GL3 ➔ GL4:</b> Compare akan dilakukan dengan acuan SKU dan QTY SYSTEM yang ada di GL4. SKU dan QTY SYSTEM yang ada di GL4 namun tidak ada di GL3 akan dilakukan presentase dengan Rumus <code>(TOTAL STOCK GL4 - TOTAL STOCK BELUM TEREFILL)/TOTAL STOCK GL4</code>. Dan akan mengecualikan BIN REJECT, DEFECT, LIVE, ONLINE, STAGGING, PUTAWAY.<br>
                - <b>DC ➔ STORE:</b> Compare akan dilakukan dengan acuan SKU dan QTY SYSTEM yang ada di Gudang DC. SKU dan QTY SYSTEM yang ada di Gudang DC namun tidak ada di Store akan dilakukan presentase dengan Rumus <code>(TOTAL STOCK DC - TOTAL STOCK BELUM TEREFILL)/TOTAL STOCK DC</code>. Dan akan mengecualikan BIN REJECT, DEFECT, LIVE, ONLINE, MARKOM, STAGGING, KARANTINA, OUT
            """,

            # --- 12. PERCENTAGE REQUEST FL TO STORE STOCK ---
            "Precentage Request FL to Store Stock": """
                <b>📋 Informasi Format File</b><br>
                Mapping Kolom:<br>
                - <b>All Stock:</b> B(Bin)=1, C(SKU)=2, J(Qty)=9 (Area Store Surabaya: TOKO, GUDANG, STR, STORE)<br>
                - <b>Permintaan FL:</b> E(SKU)=4, V(Kriteria)=21, W(Qty)=22. Eliminasi Kolom V yang Blank / Empty.<br><br>
                <hr style='margin: 8px 0; border-color: #E2E8F0;'>
                <b>💡 Logic Thinking</b><br>
                - <b>Indikasi Over-Request:</b> Permintaan Stock to DC saat Qty stock di store ≥ 2 Pcs.<br>
                - <b>Rumus Persentase:</b> <code>(Total Bad Qty Requests / Total Qty Permintaan Valid) × 100%</code>.
            """,

            # --- 13. REFILL TOKO ---
            "Refill Toko": """
                <b>💡 Cara Kerja & Logika</b><br>
                <b>Logika Refill:</b><br>
                1. <b>Filter Data:</b> Mengabaikan kategori: <b>Shoes, Sandals, Footwear</b>.<br>
                2. <b>Identifikasi Stok:</b><br>
                   - <b>Stok Toko:</b> Total qty di lokasi 'TOKO'.<br>
                   - <b>Stok Gudang/Cadangan:</b> Total qty di semua lokasi selain 'TOKO' yang bukan bin Defect/Reject/Staging/dll.<br>
                3. <b>Aturan Refill:</b><br>
                   - Hanya muncul jika stok di gudang > 0.<br>
                   - <b>Lower Body:</b> Refill jika stok toko < 6.<br>
                   - <b>Kategori Lain:</b> Refill jika stok toko < 2.
            """,

            # --- 14. MATCH REAL & SYSTEM ---
            "Match Real & System": """
                <b>📋 Informasi Format File</b><br>
                <b>Ketentuan Kolom untuk Masing-masing File Uploader:</b><br>
                * <b>📂 FILE SYSTEM (+)</b><br>
                    * <b>Kolom A:</b> Cabang<br>
                    * <b>Kolom D:</b> SKU System<br>
                    * <b>Kolom K:</b> Qty System<br><br>
                * <b>📂 FILE REAL (+)</b><br>
                    * <b>Kolom A:</b> Cabang<br>
                    * <b>Kolom E:</b> SKU Real<br>
                    * <b>Kolom M:</b> Qty Real<br><br>
                <hr style='margin: 8px 0; border-color: #E2E8F0;'>
                <b>💡 Logic Thinking</b><br>
                <b>Alur Alokasi Stok Lintas Cabang (Cross-Branch):</b><br>
                1. <b>Pool Lock System:</b> Seluruh data dari <i>Uploader System</i> akan dikunci kuotanya berdasarkan kombinasi <b>Cabang + SKU System</b>.<br>
                2. <b>Pencarian Pasangan:</b> Data dari <i>Uploader Real</i> akan discan baris demi baris, lalu diprioritaskan mencari kecocokan di cabang asalnya dulu (<b>MATCH PERFECT</b>).<br>
                3. <b>Alokasi Lintas Cabang:</b> Jika kuota system di cabang asalnya habis, sistem akan otomatis mencarikan sisa kuota ke cabang lain (<b>MATCH CROSS-BRANCH</b>).<br>
                4. <b>Kontrol Kuota:</b> Jika kuota system di semua cabang sudah habis, sisa qty real tidak dialokasikan lagi (<b>UNMATCHED / SYSTEM HABIS</b>).
            """,

            # --- 15. REFILL KOLI TO KOLI / REFILL ---
            "Refill Koli to Koli/Refill": """
                <b>💡 INFORMASI & RULES MUTASI GUDANG (KL1 / KL2 / LT.3)</b><br>
                <b>1. Aturan Penggenapan & Konsolidasi:</b><br>
                * BIN <code>KL1</code> (Max Cap: 6) dan <code>KL2</code> (Max Cap: 12) yang sudah genap atau sukses dipasangkan <b>otomatis hilang</b> dari daftar kerja.<br>
                * Konsolidasi strictly dibatasi <b>maksimal 2 SKU campuran</b> dalam satu BIN.<br><br>
                <b>2. Aturan Mutasi & Refill (Khusus Stok di bawah 9):</b><br>
                * <b>QTY 6 sampai 8:</b> Diambil <b>6 unit</b> untuk diturunkan fungsinya mengisi full 1 Koli <code>KL1</code>. Sisa barangnya (<code>QTY Sekarang - 6</code>) dilempar ke <b>Gudang Lt.3</b>.<br>
                * <b>QTY di bawah 6 (3, 4, 5):</b> Karena tidak cukup barang untuk membuat 1 koli <code>KL1</code> full, maka <b>seluruh isi barang disapu bersih ke Gudang Lt.3</b> agar BIN tersebut kosong/reset.<br>
                * Sisa BIN yang total gabungan QTY-nya masih <b>9 ke atas</b> tidak akan muncul di list karena dianggap masih aman/mendekati kapasitas.
            """,

            # --- 16. DYNAMIC STOCK ALLOCATION ---
            "Stock Allocation": """
                <b>💡 Logic Thinking</b><br>
                <b>KLASIFIKASI SALES & PROPORSI PEMBAGIAN:</b><br>
                Sistem menentukan persentase alokasi tiap SKU berdasarkan performa rasio penjualan 90 hari terakhir.<br><br>
                <table style='width:100%; border-collapse: collapse; font-size:12px;' border='1'>
                    <tr style='background:#EDF2F7;'><th>Kondisi Performa SKU</th><th>Alokasi Online</th><th>Alokasi Offline</th><th>Alokasi Logistik</th></tr>
                    <tr><td>Tidak Ada Histori Sales (0 Unit)</td><td>10%</td><td>10%</td><td>80%</td></tr>
                    <tr><td>Dominan Online (> 70% Penjualan)</td><td>70%</td><td>15%</td><td>15%</td></tr>
                    <tr><td>Dominan Offline (> 70% Penjualan)</td><td>15%</td><td>70%</td><td>15%</td></tr>
                    <tr><td>Balanced / Imbang (Rasio Normal)</td><td>40%</td><td>40%</td><td>20%</td></tr>
                </table>
            """,

            # --- 17. REFILL & WITHDRAW ---
            "Refill & Withdraw": """
                <b>📋 Informasi Format File</b><br>
                <b>Format yang diharapkan:</b><br>
                - <b>ALL DATA STOCK:</b> Download All Data Stock di Jezpro dan pilh <b>HANYA ADA DI STOCK</b><br>
                - <b>STOCK TRACKING:</b> Download Stock Tracking di Jezpro dan pilih <b>JEZ SURABAYA</b> lalu pilih rentang waktu <b>7 HARI SEBELUMNYA</b><br><br>
                <hr style='margin: 8px 0; border-color: #E2E8F0;'>
                <b>💡 Logic Thinking</b><br>
                <b>Alur Process Refill & Withdraw (With Stock Tracking):</b><br>
                - Melakukan Compare antara SKU yang ada di Gudang DC dengan Store dan sebaliknya<br>
                - List akan dikumpulkan terlebih dahulu dan akan mengambil SKU dengan Qty di Store yang < 3 Pcs untuk Refill dan > 6 Pcs untuk Withdraw<br>
                - Jika data sudah didapatkan maka selanjutnya adalah compare dengan Stock Tracking<br>
                - Compare akan dilakukan dengan mempertimbangkan penjualan Offline untuk SKU tersebut<br>
                - Jika penjualan offline < 7 pcs maka refill hanya akan mengambil 1/3 dari total stock di DC dan akan mengambil 1/3 dari total Diff total stock - 12 Pcs untuk Withdraw<br>
                - Jika penjualan offline > 7 pcs maka refill akan mengambil 1/2 dari total stock di DC dan akan mengambil 1/2 dari total Diff total stock - 12 Pcs untuk Withdraw<br>
                - Maksimal kapasitas untuk tiap SKU di STORE adalah 6 Pcs jadi tidak akan lebih dari 6 tiap SKU di Gl3<br><br>
                <b>Alur Process Refill & Withdraw (Without Stock Tracking):</b><br>
                - Melakukan Compare antara SKU yang ada di Gudang DC dengan SKU di Gudang STORE<br>
                - List akan dikumpulkan terlebih dahulu dan akan mengambil SKU dengan Qty di Gudang DC yang < 3 Pcs dan > 6 Pcs untuk Withdraw<br>
                - Sistem akan memksimalkan tiap SKU untuk mendapatkan total 6 Pcs di Gudang Store<br>
                - Maksimal kapasitas untuk tiap SKU di Store adalah 6 Pcs jadi tidak akan lebih dari 6 tiap SKU di Gl3
            """,

            # --- 18. PERCENTAGE DISPLAY CONTROL ---
            "Precentage Display": """
                <b>📋 Logika Penarikan Display</b><br>
                <b>Filter Eksklusi (Tidak Dihitung di List Refill Utama):</b><br>
                - Bin mengandung: <i>OFFLINE, ONLINE, AMP, MARKOM, DEFECT, REJECT, STAGING, STAGGING, KARANTINA, EVENT, BANDING, INB, OUT, PUTAWAY</i>.<br><br>
                <b>Cara Kerja Pemantauan :</b><br>
                - <b>Source (Gudang Store / DC):</b> Semua BIN aktif selain area Toko & Eksklusi.<br>
                  - <b>Gudang Lt. 2 Store:</b> BIN mengandung kata <code>STR</code>, <code>STORE</code>, atau <code>GUDANG</code>.<br>
                  - <b>DC (Distribution Center):</b> BIN mengandung kata <code>DC</code>.<br>
                - <b>Target (Toko):</b> BIN yang mengandung kata <code>TOKO</code> atau <code>DISPLAY</code>.<br>
                - <b>Aturan Proteksi OUT:</b> Jika Article / SKU sudah berada di bin <b>'OUT'</b> dengan Qty > 0, otomatis <b>dihapus dari list penarikan</b>.<br>
                - <b>Logic:</b> Jika SKU memiliki <b>Stok > 0 di Gudang/DC</b> tapi <b>Stok = 0 di Toko</b>, maka SKU wajib tambah display.
            """,

            # --- 19. STOCK TRACKING TIMELINE ---
            "Stock Tracking Timeline": """
                <b>📋 Informasi Format File</b><br>
                <b>Format yang diharapkan:</b><br>
                - <b>File Multiple Adjusment:</b> Download File Multiple adjusment yang akan dianalisa SKU nya<br>
                - <b>File Purchase Order:</b> Download File Purchase Order dari Power BI dengan ketentuan : Buka Power BI ➔ Menu <b>LEADER</b> ➔ Menu <b>Inventory_Processing</b> ➔ Tab <b>Purchase Order</b> (Periode Invoice: All time, ReceivedIN: All time, Store: Jez Surabaya)<br>
                - <b>File Mutasi:</b> Buka Power BI ➔ Menu <b>LEADER</b> ➔ Menu <b>Inventory_Processing</b> ➔ Tab <b>Mutation Stock</b> (Store: Jez Surabaya, Period: All Time)<br>
                - <b>File Adjusment:</b> Buka Power BI ➔ Menu <b>LEADER</b> ➔ Menu <b>Inventory_Processing</b> ➔ Tab <b>Adjusment</b> (Period: All time, Warehouses: Jez Surabaya)<br>
                - <b>File RTO:</b> Buka Power BI ➔ Menu <b>LEADER</b> ➔ Menu <b>Inventory_Processing</b> ➔ Tab <b>Transfer Stock</b> (Status: All, Period: All time, Departure/Destination: ALL)<br>
                - <b>File Stock Tracking:</b> Buka Power BI ➔ Menu <b>LEADER</b> ➔ Menu <b>Sales_Transactions</b> ➔ Tab <b>Cek Trx</b> (Period: All Time, Warehouse: Jez Surabaya, Store Adj: All). <i>*PS: Setelah Download Stock Tracking pastikan COPY & PASTE di file yang baru karena file bawaan dari PBI akan Corrupt dan tidak bisa terbaca.</i>
            """,

            # --- 20. LIST RETUR OUT ---
            "List Retur Out": """
                <b>📋 Informasi Format File</b><br>
                <b>Format yang diharapkan:</b><br>
                - <b>MULTIPLE ADJUSTMENT:</b> Download Multiple Adjusment dimana pilih saja yang <b>hanya ada di stok</b> Lalu filter sesuai dengan BIN dan SKU yang ingin di retur<br>
                - Lalu Upload ke WEB dan setelah upload maka data akan tersimpan secara otomatis di WEB<br>
                - Apabila tidak semua stock dari SKU tersebut diretur maka <b>Pastikan QTY SYSTEM yang ada di file Multiple tersebut di edit dan disesuaikan dengan Realnya</b>
            """,

            # --- 21. FDR UPDATE ---
            "FDR Update": """
                <b>📋 Informasi Format File</b><br>
                <b>Format yang diharapkan:</b><br>
                - <b>FILE MANIFEST:</b> Download Manifest dari jezpro pada menu <b>TRANSAKSI ONLINE V2</b>, pilih Cabang <b>ONLINE SURABAYA</b>, pilih Status Jezpro <b>DONE ONLINE</b>, dan rentang waktunya pilih <b>30 HARI TERAKHIR</b><br><br>
                <hr style='margin: 8px 0; border-color: #E2E8F0;'>
                <b>💡 Logic Thinking</b><br>
                <b>Alur Compare :</b><br>
                - File yang telah diupload hanya akan di split berdasarkan 2 Kategori yaitu <b>NEED FU IT</b> dan <b>BRANCH</b><br>
                - Untuk Need FU IT adalah kondisi dimana ketika kolom No Manifest telah terisi namun status masih <b>DONE ONLINE</b><br>
                - Untuk Branch adalah disesuaikan dan di split berdasarkan cabang dari masing-masing transaksi yang masih berstatus <b>DONE ONLINE</b>
            """,

            # --- 22. STORE LEADER RTO DECISION ---
            "Store Leader RTO Decission": """
                <b>🏬 STORE LEADER RTO DECISSION</b><br>
                <b>Ketentuan 4 File Logistik:</b><br>
                1. <b>Stock Surabaya:</b> Master SKU (Kolom C=SKU, E=Item Name, F=Variant, J=Qty)<br>
                2. <b>Stock Semarang:</b> Kolom C=SKU, Kolom J=Qty<br>
                3. <b>Sales 60d Report:</b> Kolom R=SKU, Kolom Z=Sales Qty<br>
                4. <b>ToC Master Sheet:</b> Kolom C=Article/Item Name, Kolom H=ToC (Last Row Win)<br><br>
                <hr style='margin: 8px 0; border-color: #E2E8F0;'>
                <b>💡 Logic Thinking:</b><br>
                - Left join data Surabaya dengan Semarang dan Sales 60d.<br>
                - Filter mengabaikan baris jika QTY Surabaya dan QTY Semarang keduanya bernilai 0.
            """,

            # --- 23. DATA TIMBANG ONGKIR ---
            "Data Timbang Ongkir": """
                <b>⚖️ SISTEM TIMBANG KOLIAN</b><br><br>
                <b>Logikal Perhitungan Harga Tarif:</b><br>
                - <b>ACCESS + SEMARANG:</b> Total Koli × 40.000 × 3.2<br>
                - <b>ACCESS + HUB JAKARTA:</b> Berat (Kg) × 2.500 × 3.2<br>
                - <b>ADEX + SEMARANG / MALANG:</b> Berat (Kg) × 1.000 × 3.2<br>
                - <b>ADEX + HUB JAKARTA:</b> Berat (Kg) × 2.000 × 3.2
            """,

            # --- 24. DATABASE ONGKIR IN/OUT ---
            "Database Ongkir In/Out": """
                <b>🛻 DATABASE ONGKIR IN/OUT</b><br><br>
                - <b>Single Input:</b> Form input manual transaksi ongkir.<br>
                - <b>Batch Ops (Upload Massal):</b> Upload file CSV dengan kolom <code>SUPPLIER, EKSPEDISI, TOTAL KOLI, ONGKIR, TANGGAL_JAM</code>.<br>
                - <b>Summary Metrics:</b> Total Biaya All, Total Koli All, Avg Cost/Koli All, Biaya & Koli Barang Datang (Non-RTO), dan Biaya & Koli RTO.
            """,

            # --- 25. PENGAJUAN MUTASI KARANTINA ---
            "Pengajuan Mutasi Karantina": """
                <b>📋 Informasi Format File</b><br>
                <b>UNTUK BULK / MULTIPLE UPLOAD:</b><br>
                Pastikan file Excel memiliki kolom dengan urutan dan nama berikut:<br>
                1. <b>BIN AWAL</b><br>
                2. <b>BIN TUJUAN</b><br>
                3. <b>SKU</b><br>
                4. <b>ARTICLE NAME</b><br>
                5. <b>QUANTITY</b><br>
                6. <b>NOTES</b><br>
                7. <b>ALASAN</b><br><br>
                <i>*Pastikan tidak ada kolom yang kosong atau nama kolom yang typo agar terbaca sistem.*</i>
            """
        }

        guide_content = guides.get(
            cur, 
            f"<b>📌 MENU: {cur}</b><br><br>Menu ini digunakan untuk operasional warehouse Surabaya. Pastikan format file yang diunggah sesuai dengan template standar sistem."
        )

        ui.modal_show(ui.modal(
            ui.HTML(f"""
                <div style="padding: 10px; font-size: 13.5px; color: #2D3748; line-height: 1.6;">
                    {guide_content}
                </div>
            """),
            title=ui.div(
                ui.tags.i(class_="fa-solid fa-book-open", style="color: #E50914; margin-right: 8px;"), 
                f"Panduan & Logika Sistem — {cur}"
            ),
            easy_close=True,
            size="l",
            footer=ui.modal_button("Tutup Panduan", class_="btn-red-gradient")
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
    # --- RETUR OUT: UPLOAD & AUTO-SAVE KE SUPABASE LAMA ---
    @reactive.Effect
    @reactive.event(input.btn_save_retur_cloud)
    def _save_retur():
        f = input.uploader_retur_file()
        if not f:
            state.error_modal_message.set("Pilih file Retur terlebih dahulu!")
            state.show_error_modal.set(True)
            return
        try:
            df = config.load_data_from_info(f)
            df.columns = [str(c).strip() for c in df.columns]
            req_cols = {'Identify': 'identify', 'BIN': 'bin', 'SKU': 'sku', 'BRAND': 'brand', 'ITEM NAME': 'item_name', 'VARIANT': 'variant', 'SUB KATEGORI': 'sub_kategori', 'Harga Beli': 'harga_beli', 'Harga Jual': 'harga_jual', 'QTY SYSTEM': 'qty_system', 'QTY SO': 'qty_so'}
            
            df_save = df[[c for c in req_cols.keys() if c in df.columns]].copy()
            df_save.rename(columns=req_cols, inplace=True)
            df_save['tanggal'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            records = df_save.fillna("").to_dict(orient='records')
            
            sb = config.get_supabase_old()
            sb.table("retur_out_v3").insert(records).execute()
            state.show_success_modal.set(True)
        except Exception as e:
            state.error_modal_message.set(f"Gagal upload retur: {e}")
            state.show_error_modal.set(True)

    @render.ui
    def retur_out_metrics_ui():
        try:
            sb = config.get_supabase_old()
            res = sb.table("retur_out_v3").select("*").execute()
            df = pd.DataFrame(res.data) if res and res.data else pd.DataFrame()
            if df.empty: return ui.div()
            
            df['qty_system'] = pd.to_numeric(df.get('qty_system', 0), errors='coerce').fillna(0)
            df['harga_beli'] = pd.to_numeric(df.get('harga_beli', 0), errors='coerce').fillna(0)
            
            tot_sku = df['sku'].nunique() if 'sku' in df.columns else 0
            tot_qty = int(df['qty_system'].sum())
            tot_val = float((df['qty_system'] * df['harga_beli']).sum())
            
            return ui.div(
                dark_metric_box("🗄️ TOTAL SKU", f"{tot_sku:,}", "#8b5cf6"),
                dark_metric_box("📦 TOTAL QTY", f"{tot_qty:,}", "#10b981"),
                dark_metric_box("💰 TOTAL VALUE", f"Rp {tot_val:,.0f}", "#f59e0b"),
                style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem;"
            )
        except Exception: return ui.div()

    @render.ui
    def retur_out_table_ui():
        try:
            sb = config.get_supabase_old()
            res = sb.table("retur_out_v3").select("*").order("tanggal", desc=True).execute()
            df = pd.DataFrame(res.data) if res and res.data else pd.DataFrame()
            if df.empty: return ui.div("Belum ada data di tabel retur_out_v3.")
            return render_clean_table(df.columns.tolist(), df.fillna("").astype(str).values.tolist(), "tbl_retur_out")
        except Exception as e: return ui.div(f"Error load data: {e}")
    
    # --- LOGISTIC SCHEDULE SERVER ENGINE ---
    @reactive.Effect
    @reactive.event(input.btn_add_karyawan)
    def _add_staff():
        nm = str(input.sc_nama_karyawan()).upper().strip()
        if nm:
            try:
                sb = config.get_supabase_old()
                sb.table("karyawan").insert({"nama": nm, "posisi": str(input.sc_posisi()), "tipe": str(input.sc_tipe())}).execute()
                state.show_success_modal.set(True)
            except Exception as e:
                state.error_modal_message.set(f"Gagal: {e}"); state.show_error_modal.set(True)

    @render.ui
    def schedule_libur_form_ui():
        try:
            sb = config.get_supabase_old()
            res_k = sb.table("karyawan").select("nama").execute()
            names = [r['nama'] for r in res_k.data] if res_k and res_k.data else ["-"]
            return ui.div(
                ui.div(
                    ui.input_select("sc_libur_nama", "Pilih Karyawan:", choices=names),
                    ui.input_date("sc_libur_tgl", "Tanggal Libur:", value=datetime.now().strftime("%Y-%m-%d")),
                    ui.input_select("sc_libur_jenis", "Jenis:", choices=["LIBUR", "CUTI", "LPH"]),
                    style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;"
                ),
                ui.tags.button("SUBMIT OFF", onclick="Shiny.setInputValue('btn_submit_libur', Math.random(), {priority: 'event'})", class_="btn-red-gradient", style="margin-top: 10px;")
            )
        except Exception: return ui.div()

    @reactive.Effect
    @reactive.event(input.btn_submit_libur)
    def _sub_libur():
        try:
            sb = config.get_supabase_old()
            sb.table("libur_request").insert({"nama": str(input.sc_libur_nama()), "tanggal": str(input.sc_libur_tgl()), "jenis": str(input.sc_libur_jenis())}).execute()
            state.show_success_modal.set(True)
        except Exception as e:
            state.error_modal_message.set(f"Gagal: {e}"); state.show_error_modal.set(True)

    @render.ui
    def schedule_shift3_form_ui():
        try:
            sb = config.get_supabase_old()
            res_k = sb.table("karyawan").select("*").execute()
            names = [r['nama'] for r in res_k.data] if res_k and res_k.data else ["-"]
            return ui.div(
                ui.div(
                    ui.input_select("sc_s3_nama", "Pilih Nama Tim:", choices=names),
                    ui.input_date("sc_s3_tgl", "Tanggal Masuk Shift 3:", value=datetime.now().strftime("%Y-%m-%d")),
                    style="display: flex; gap: 1rem;"
                ),
                ui.tags.button("SUBMIT PLOT SHIFT 3", onclick="Shiny.setInputValue('btn_submit_s3', Math.random(), {priority: 'event'})", class_="btn-red-gradient", style="margin-top: 10px;")
            )
        except Exception: return ui.div()

    @reactive.Effect
    @reactive.event(input.btn_submit_s3)
    def _sub_s3():
        try:
            sb = config.get_supabase_old()
            sb.table("plot_shift3").insert({"nama": str(input.sc_s3_nama()), "tanggal": str(input.sc_s3_tgl()), "posisi": "SO", "tipe": "Full-Time"}).execute()
            state.show_success_modal.set(True)
        except Exception as e:
            state.error_modal_message.set(f"Gagal: {e}"); state.show_error_modal.set(True)

    # --- ENGINE GENERATOR JADWAL JEZ SBY PERSIS STREAMLIT ---
    df_schedule_res_full = reactive.Value(pd.DataFrame())

    @reactive.Effect
    @reactive.event(input.btn_run_schedule_full)
    def _run_sched_engine():
        try:
            import random
            start_date_val = pd.to_datetime(input.sc_start_monday()).date()
            dates_real = [(start_date_val + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
            day_names = ["SENIN", "SELASA", "RABU", "KAMIS", "JUMAT", "SABTU", "MINGGU"]
            
            sb = config.get_supabase_old()
            karyawan_list = sb.table("karyawan").select("*").execute().data or []
            df_libur = pd.DataFrame(sb.table("libur_request").select("*").execute().data or [])
            df_manual_s3 = pd.DataFrame(sb.table("plot_shift3").select("*").execute().data or [])

            base_roles = [
                ("SHIFT 0", "WF-PICKER"), ("SHIFT 0", "WF-ADMIN"),
                ("SHIFT 1", "LOG-ADMIN"), ("SHIFT 1", "LOG-LOADER"), ("SHIFT 1", "LOG-STORE"), ("SHIFT 1", "WF-ADMIN"), ("SHIFT 1", "WF-PICKER"),
                ("SHIFT 2", "LOG-ADMIN"), ("SHIFT 2", "LOG-LOADER"), ("SHIFT 2", "LOG-STORE"), ("SHIFT 2", "WF-ADMIN"), ("SHIFT 2", "WF-PICKER"), ("SHIFT 2", "SPV"),
                ("SHIFT 3", "SO")
            ]

            storage = {d: {f"{s} - {r}": [] for s, r in base_roles} for d in day_names}
            weekly_counter = {k['nama']: 0 for k in karyawan_list}
            double_day_count = {k['nama']: 0 for k in karyawan_list}
            for k in karyawan_list: k['target_fix'] = 9 if k.get('tipe') == "Part-Full" else 6

            def get_active_shifts(nama, d_name):
                return [slot.split(" - ")[0] for slot in storage[d_name] if any(nama in n for n in storage[d_name][slot])]

            # 1. Plot Shift 3
            for day_name, tgl_str in zip(day_names, dates_real):
                if not df_manual_s3.empty and 'tanggal' in df_manual_s3.columns:
                    names_manual = df_manual_s3[df_manual_s3['tanggal'] == tgl_str]['nama'].tolist()
                    if names_manual:
                        storage[day_name]["SHIFT 3 - SO"] = names_manual
                        for nm in names_manual:
                            if nm in weekly_counter: weekly_counter[nm] += 1

            # 2. Loop Phase Target
            for phase in ["TARGET_1_ORANG", "TARGET_2_ORANG", "SISA_JATAH"]:
                for day_name in day_names:
                    tgl_ini = dates_real[day_names.index(day_name)]
                    for shf_jam, shf_role in base_roles:
                        if shf_jam == "SHIFT 3": continue
                        slot_key = f"{shf_jam} - {shf_role}"
                        current_fill = len(storage[day_name][slot_key])
                        if phase == "TARGET_1_ORANG" and current_fill >= 1: continue
                        if phase == "TARGET_2_ORANG" and current_fill >= 2: continue

                        potential = [k for k in karyawan_list if weekly_counter[k['nama']] < k['target_fix'] and not get_active_shifts(k['nama'], day_name)]
                        if potential:
                            random.shuffle(potential)
                            pick = potential[0]['nama']
                            storage[day_name][slot_key].append(pick)
                            weekly_counter[pick] += 1

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

            df_schedule_res_full.set(pd.DataFrame(final_table))
            state.show_success_modal.set(True)
        except Exception as e:
            state.error_modal_message.set(f"Gagal: {e}"); state.show_error_modal.set(True)

    @render.ui
    def schedule_final_table_ui():
        df = df_schedule_res_full()
        if df.empty: return ui.div("Klik tombol RUN JADWAL SHIFT di atas untuk memproses jadwal.")
        return render_clean_table(df.columns.tolist(), df.values.tolist(), "tbl_sched_final")
    
    # --- SUBMISSION PENGAJUAN REJECT (SUPABASE LAMA) ---
    @reactive.Effect
    @reactive.event(input.btn_sub_pengajuan_reject)
    def _sub_pengajuan():
        try:
            sb = config.get_supabase_old()
            now_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sb.table("submissions").insert({
                "timestamp": now_ts, "nama_tim": str(input.pr_nama()), "bin_asal": str(input.pr_bin_asal()),
                "sku": str(input.pr_sku()).upper().strip(), "article_name": str(input.pr_article()),
                "size": str(input.pr_size()), "keterangan": str(input.pr_ket()),
                "status": 1, "cabang": str(input.pr_cabang())
            }).execute()
            state.show_success_modal.set(True)
        except Exception as e:
            state.error_modal_message.set(f"Gagal simpan pengajuan: {e}"); state.show_error_modal.set(True)

    @render.ui
    def pengajuan_reject_history_ui():
        try:
            sb = config.get_supabase_old()
            res = sb.table("submissions").select("*").order("id", desc=True).execute()
            df = pd.DataFrame(res.data) if res and res.data else pd.DataFrame()
            if df.empty: return ui.div("Belum ada data pengajuan di database.")
            return render_clean_table(df.columns.tolist(), df.fillna("").astype(str).values.tolist(), "tbl_sub_hist")
        except Exception as e: return ui.div(f"Error: {e}")

    # --- CROSS-CHECK MATCHING KIRI KANAN ---
    @render.ui
    def reject_match_kiri_kanan_ui():
        try:
            sb = config.get_supabase_old()
            res = sb.table("reject_list").select("*").eq("status", "PENDING").execute()
            df = pd.DataFrame(res.data) if res and res.data else pd.DataFrame()
            if df.empty: return ui.div("✅ Tidak ditemukan Reject/Defect Match (Semua aman).")
            
            # Cari Pasangan Kiri-Kanan
            def check_kiri_kanan(grp):
                cats = grp['kategori'].astype(str).str.lower().values
                return any('kiri' in c for c in cats) and any('kanan' in c for c in cats)
            
            valid_skus = df.groupby('sku').filter(check_kiri_kanan)['sku'].unique() if 'kategori' in df.columns else []
            df_m = df[df['sku'].isin(valid_skus)].copy() if len(valid_skus) > 0 else pd.DataFrame()
            
            if df_m.empty: return ui.div("Tidak ada pasangan SKU Kiri-Kanan yang match.")
            return render_clean_table(df_m.columns.tolist(), df_m.fillna("").astype(str).values.tolist(), "tbl_match_res")
        except Exception as e: return ui.div(f"Error matching: {e}")

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
        if not state.logged_in(): 
            return login_page()
            
        content_type = state.get_active_content_type()

        # =====================================================================
        # 1. 10 MENU ASLI ANDA
        # =====================================================================
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

        # =====================================================================
        # 2. 14 MENU BARU STREAMLIT HASIL KONVERSI
        # =====================================================================
        elif content_type == "po_receiving": page_content = po_receiving_view(state)
        elif content_type == "penerimaan_rto": page_content = penerimaan_rto_view(state)
        elif content_type == "scan_out": page_content = scan_out_view(state)
        elif content_type == "refill_overstock": page_content = refill_overstock_view(state)
        elif content_type == "balancing_stock": page_content = balancing_stock_view(state)
        elif content_type == "fl_request": page_content = fl_request_view(state)
        elif content_type == "refill_toko": page_content = refill_toko_view(state)
        elif content_type == "rto_decision": page_content = rto_decision_view(state)
        elif content_type == "match_karantina": page_content = match_karantina_view(state)
        elif content_type == "koli_consolidation": page_content = koli_consolidation_view(state)
        elif content_type == "stock_allocation": page_content = stock_allocation_view(state)
        elif content_type == "refill_withdraw": page_content = refill_withdraw_view(state)
        elif content_type == "fdr_update": page_content = fdr_update_view(state)
        elif content_type == "percentage_display": page_content = percentage_display_view(state)
        elif content_type == "stock_tracking": page_content = stock_tracking_view(state)
        elif content_type == "retur_out": page_content = retur_out_view(state)
        elif content_type == "pengajuan_mutasi": page_content = pengajuan_mutasi_view(state)
        elif content_type == "pengajuan_reject": page_content = pengajuan_reject_view(state)
        elif content_type == "reject_list": page_content = reject_list_view(state)
        elif content_type == "logistic_schedule": page_content = logistic_schedule_view(state)
        elif content_type == "reporting_pic": page_content = reporting_pic_view(state)
        elif content_type == "timbang_ongkir": page_content = timbang_ongkir_view(state)
        elif content_type == "access_denied":
            page_content = ui.div(ui.h2("⛔ Akses Ditolak", style="font-size: 28px; color: #E53E3E; font-weight: bold;"), ui.p("Maaf, halaman ini dibatasi hak aksesnya.", style="color: #718096; font-size: 15px;"), style="padding: 3rem; text-align: center; height: 70vh; display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%;")
        else:
            page_content = ui.div(ui.h2(f"Halaman: {state.main_menu()}", style="font-size: 28px; color: #1A202C; font-weight: bold;"), ui.p("Halaman ini sedang dalam tahap pengembangan.", style="color: #718096; font-size: 15px;"), style="padding: 3rem; text-align: center; height: 70vh; display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%;")

        # =====================================================================
        # 3. RENDER LAYOUT
        # =====================================================================
        return ui.div(
            sidebar(state),
            ui.div(
                global_header(state),
                page_content,
                id="main-scroll-container",
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
# 1. Download PO Receiving (Multi-Sheet)
    @render.download(filename="Hasil_PO_Receiving.xlsx")
    def btn_dl_po_all():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            state._df_po_hasil.to_excel(writer, sheet_name='DETAIL_ALOKASI', index=False)
            state._df_po_extra.to_excel(writer, sheet_name='OVER_SCAN', index=False)
            state._df_po_miss.to_excel(writer, sheet_name='KURANG_SCAN', index=False)
        buf.seek(0)
        yield buf.getvalue()

    # 2. Download Refill Toko
    @render.download(filename="Refill_Toko_SBY.xlsx")
    def btn_dl_refill_toko():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            state._df_refill_toko.to_excel(writer, sheet_name='REFILL_TOKO', index=False)
        buf.seek(0)
        yield buf.getvalue()

    # 3. Download Scan Out Validation
    @render.download(filename="SCAN_OUT_RESULT.xlsx")
    def btn_dl_scan_out():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            state._df_scan_out_res.to_excel(writer, sheet_name='DATA_SCAN', index=False)
            state._df_scan_out_draft.to_excel(writer, sheet_name='DRAFT_SETUP', index=False)
        buf.seek(0)
        yield buf.getvalue()

    # 4. Download Refill & Overstock
    @render.download(filename="Refill_Overstock_Report.xlsx")
    def btn_dl_rf_os():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            state._df_rf_res.to_excel(writer, sheet_name='REFILL', index=False)
            state._df_os_res.to_excel(writer, sheet_name='OVERSTOCK', index=False)
        buf.seek(0)
        yield buf.getvalue()

    # 5. Download Store Leader RTO Decision
    @render.download(filename="HASIL_COMPARE_LOGISTIK.xlsx")
    def btn_dl_rto_dec():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            state._df_rto_dec.to_excel(writer, sheet_name='HASIL_COMPARE', index=False)
        buf.seek(0)
        yield buf.getvalue()

    # 6. Download Permintaan FL
    @render.download(filename="Analisis_Permintaan_FL.xlsx")
    def btn_dl_fl_req():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            state._df_fl_bad.to_excel(writer, sheet_name='OVER_REQUEST', index=False)
            state._df_fl_comp.to_excel(writer, sheet_name='COMPARE_ALL', index=False)
        buf.seek(0)
        yield buf.getvalue()

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
        
# ==========================================================================
    # LOGIC: TIMBANG ONGKIR
    # ==========================================================================
    timbang_reload_trigger = reactive.Value(0)

    # 1. SIMPAN DATA MANUAL KE SUPABASE LAMA
    @reactive.Effect
    @reactive.event(input.btn_save_timbang)
    def _save_timbang():
        try:
            sb = config.get_supabase_old()
            
            data_payload = {
                "ekspedisi": str(input.tb_ekspedisi() or "").upper().strip(),
                "jenis_pengiriman": str(input.tb_jenis() or "").strip(),
                "pengiriman_dari": str(input.tb_dari() or "").upper().strip(),
                "pengiriman_ke": str(input.tb_ke() or "").upper().strip(),
                "total_koli": int(input.tb_koli() or 1),
                "berat_total_timbang": float(input.tb_berat() or 0.0),
                "created_at": datetime.now().isoformat()
            }

            res = sb.table("timbang_kolian").insert(data_payload).execute()
            print(f"✅ [TIMBANG INSERT] Response DB: {res.data}")

            if not res.data:
                raise Exception("Data gagal disimpan ke database. Cek koneksi Supabase.")

            # Trigger reload tabel & metrik
            timbang_reload_trigger.set(timbang_reload_trigger() + 1)
            
            if hasattr(state, "show_success_modal"):
                state.show_success_modal.set(True)
        except Exception as e:
            print(f"❌ [TIMBANG INSERT ERROR] {e}")
            if hasattr(state, "error_modal_message"):
                state.error_modal_message.set(f"Gagal simpan data: {e}")
            if hasattr(state, "show_error_modal"):
                state.show_error_modal.set(True)
        finally:
            ui.insert_ui(
                ui.tags.script("document.body.classList.remove('process-running');"),
                selector="body",
                where="beforeEnd"
            )

    # 2. HAPUS DATA SATUAN DARI TABEL
    @reactive.Effect
    @reactive.event(input.btn_delete_timbang_single)
    def _delete_timbang_single():
        target_id = input.btn_delete_timbang_single()
        if not target_id:
            return
        try:
            sb = config.get_supabase_old()
            res = sb.table("timbang_kolian").delete().eq("id", str(target_id).strip()).execute()
            print(f"🗑️ [TIMBANG DELETE] ID {target_id} dihapus. Respon: {res.data}")
            timbang_reload_trigger.set(timbang_reload_trigger() + 1)
        except Exception as e:
            print(f"❌ [TIMBANG DELETE ERROR] {e}")
            if hasattr(state, "error_modal_message"):
                state.error_modal_message.set(f"Gagal menghapus data: {e}")
            if hasattr(state, "show_error_modal"):
                state.show_error_modal.set(True)

    # 3. GANTI FILTER PERIODE
    @reactive.Effect
    @reactive.event(input.change_filter_timbang_periode)
    def _chg_flt_timbang():
        val = str(input.change_filter_timbang_periode() or "ALL")
        if hasattr(state, "timbang_filter_periode"):
            if callable(getattr(state.timbang_filter_periode, "set", None)):
                state.timbang_filter_periode.set(val)
            else:
                state.timbang_filter_periode = val
        timbang_reload_trigger.set(timbang_reload_trigger() + 1)

    # 4. RUMUS HARGA TARIF
    def _hitung_harga_timbang(row):
        try:
            eksp = str(row.get('ekspedisi', '') or '').upper()
            tujuan = str(row.get('pengiriman_ke', '') or '').upper()
            koli = pd.to_numeric(row.get('total_koli', 0), errors='coerce') or 0.0
            berat = pd.to_numeric(row.get('berat_total_timbang', 0), errors='coerce') or 0.0

            if "ACCESS" in eksp and "SEMARANG" in tujuan:
                return float(koli) * 40000.0 * 3.2
            elif "ACCESS" in eksp and "HUB JAKARTA" in tujuan:
                return float(berat) * 2500.0 * 3.2
            elif "ADEX" in eksp and ("SEMARANG" in tujuan or "MALANG" in tujuan):
                return float(berat) * 1000.0 * 3.2
            elif "ADEX" in eksp and "HUB JAKARTA" in tujuan:
                return float(berat) * 2000.0 * 3.2
            return 0.0
        except Exception:
            return 0.0

    # 5. TARIK DATA DARI SUPABASE LAMA DENGAN FILTER TANGGAL (WIB)
    def _get_filtered_timbang_data():
        _ = timbang_reload_trigger()
        try:
            sb = config.get_supabase_old()
            res = sb.table("timbang_kolian").select("*").execute()
            data = res.data if hasattr(res, "data") and res.data else []
            
            print(f"📦 [TIMBANG FETCH] Total baris mentah dari DB: {len(data)}")
            if not data:
                return pd.DataFrame()

            raw_df = pd.DataFrame(data)

            # Konversi Tanggal ke WIB (Persis Streamlit)
            raw_df['created_at'] = pd.to_datetime(raw_df['created_at'], errors='coerce')
            if raw_df['created_at'].dt.tz is None:
                raw_df['created_at'] = raw_df['created_at'].dt.tz_localize('UTC')
            raw_df['created_at'] = raw_df['created_at'].dt.tz_convert('Asia/Jakarta')

            # Urutkan paling baru
            raw_df = raw_df.sort_values(by="created_at", ascending=False).reset_index(drop=True)

            # Hitung Estimasi Harga
            raw_df['Estimasi Harga'] = raw_df.apply(_hitung_harga_timbang, axis=1)

            # Filter Periode
            try:
                filter_waktu = str(input.change_filter_timbang_periode() or "ALL").upper()
            except Exception:
                filter_waktu = "ALL"

            now_jkt = datetime.now(timezone(timedelta(hours=7)))
            df_filtered = raw_df.copy()

            if filter_waktu in ["TODAY", "TODAY (HARI INI)"]:
                df_filtered = df_filtered[df_filtered['created_at'].dt.date == now_jkt.date()]
            elif filter_waktu in ["MONTH", "THIS MONTH (BULAN INI)"]:
                df_filtered = df_filtered[
                    (df_filtered['created_at'].dt.year == now_jkt.year) & 
                    (df_filtered['created_at'].dt.month == now_jkt.month)
                ]
            elif filter_waktu in ["PAST_MONTH", "PAST MONTH (BULAN LALU)"]:
                past_year = now_jkt.year - 1 if now_jkt.month == 1 else now_jkt.year
                past_month = 12 if now_jkt.month == 1 else now_jkt.month - 1
                df_filtered = df_filtered[
                    (df_filtered['created_at'].dt.year == past_year) & 
                    (df_filtered['created_at'].dt.month == past_month)
                ]

            return df_filtered
        except Exception as e:
            print(f"❌ [TIMBANG FETCH ERROR] {e}")
            return pd.DataFrame()

    _fetch_timbang_data = _get_filtered_timbang_data

    # 6. RENDER 4 KOTAK METRIK
    @output
    @render.ui
    def timbang_ongkir_metrics_ui():
        df = _get_filtered_timbang_data()
        if df.empty:
            return ui.div(
                dark_metric_box("📦 TOTAL KOLI", "0", "#FFD700"),
                dark_metric_box("⚖️ TOTAL BERAT", "0.00 Kg", "#FFD700"),
                dark_metric_box("💰 TOTAL BIAYA", "Rp 0", "#00FF66"),
                dark_metric_box("📝 TOTAL DATA", "0", "#FFD700"),
                style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;"
            )

        tot_koli = int(pd.to_numeric(df.get('total_koli', 0), errors='coerce').fillna(0).sum())
        tot_berat = float(pd.to_numeric(df.get('berat_total_timbang', 0), errors='coerce').fillna(0).sum())
        tot_harga = float(pd.to_numeric(df.get('Estimasi Harga', 0), errors='coerce').fillna(0).sum())
        tot_data = len(df)

        return ui.div(
            dark_metric_box("📦 TOTAL KOLI", f"{tot_koli:,}", "#FFD700"),
            dark_metric_box("⚖️ TOTAL BERAT", f"{tot_berat:,.2f} Kg", "#FFD700"),
            dark_metric_box("💰 TOTAL BIAYA", f"Rp {tot_harga:,.0f}", "#00FF66"),
            dark_metric_box("📝 TOTAL DATA", f"{tot_data:,}", "#FFD700"),
            style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;"
        )

    # 7. RENDER TABEL RIWAYAT BESERTA TOMBOL HAPUS SATUAN
    @output
    @render.ui
    def timbang_ongkir_table_ui():
        df = _get_filtered_timbang_data()
        if df.empty:
            return ui.div("💡 Belum ada data timbang masuk untuk periode ini.", style="text-align: center; padding: 2rem; color: #718096; font-style: italic;")

        display_df = df.copy()
        display_df['Waktu'] = display_df['created_at'].dt.strftime('%d-%m-%Y %H:%M')
        display_df['Berat (Kg)'] = display_df['berat_total_timbang'].apply(lambda x: f"{float(x):,.2f} Kg" if pd.notna(x) else "-")
        display_df['Estimasi Harga (Rp)'] = display_df['Estimasi Harga'].apply(lambda x: f"Rp {float(x):,.0f}" if pd.notna(x) else "Rp 0")

        # Tombol Hapus Satuan per baris
        display_df['Aksi'] = display_df['id'].apply(
            lambda x: f'<button type="button" onclick="if(confirm(\'Yakin ingin menghapus data baris ID {x}?\')) {{ Shiny.setInputValue(\'btn_delete_timbang_single\', \'{x}\', {{priority: \'event\'}}); }}" style="background: #FFF5F5; color: #E53E3E; border: 1px solid #FEB2B2; padding: 3px 8px; border-radius: 6px; font-weight: 700; font-size: 11px; cursor: pointer;">🗑️ Hapus</button>'
        )

        cols_show = ['id', 'Waktu', 'ekspedisi', 'jenis_pengiriman', 'total_koli', 'Berat (Kg)', 'pengiriman_dari', 'pengiriman_ke', 'Estimasi Harga (Rp)', 'Aksi']
        final_cols = [c for c in cols_show if c in display_df.columns]

        return render_clean_table(final_cols, display_df[final_cols].fillna("").astype(str).values.tolist(), "tbl_timbang_fast")
             
    # 2. REPORTING & PIC
    current_pic = reactive.Value("VERREL & GALIH")

    @reactive.Effect
    @reactive.event(input.change_pic_user)
    def _chg_pic():
        current_pic.set(input.change_pic_user())

    @render.ui
    def reporting_pic_status_ui():
        try:
            sb = config.get_supabase_old()
            res = sb.table("reports").select("*").execute()
            df = pd.DataFrame(res.data) if res and res.data else pd.DataFrame()
            
            if df.empty:
                default_reports = [
                    {"laporan": "REJECT & DEFECT", "pic": "VERREL & GALIH", "status": "❌ Belum"},
                    {"laporan": "KERAPIHAN STOCK", "pic": "VERREL & GALIH", "status": "❌ Belum"},
                    {"laporan": "CEK STOCK MINUS", "pic": "VERREL & GALIH", "status": "❌ Belum"},
                    {"laporan": "BALANCING STOCK", "pic": "FARIL & YUDI", "status": "❌ Belum"},
                    {"laporan": "CEK RTO", "pic": "FARIL & YUDI", "status": "❌ Belum"},
                    {"laporan": "DASHBOARD SURABAYA", "pic": "HAMZAH", "status": "❌ Belum"},
                    {"laporan": "REFILL GL4 TO GL3", "pic": "KRISNA & DHIVA", "status": "❌ Belum"}
                ]
                sb.table("reports").insert(default_reports).execute()
                res = sb.table("reports").select("*").execute()
                df = pd.DataFrame(res.data)

            pic = current_pic()
            my_tasks = df[df['pic'] == pic] if not df.empty and 'pic' in df.columns else pd.DataFrame()
            
            cards = []
            for _, r in my_tasks.iterrows():
                stat_col = "#10B981" if "Selesai" in str(r.get('status', '')) else "#EF4444"
                cards.append(ui.div(
                    ui.div(
                        ui.span(str(r.get('laporan', '')), style="font-weight: 800; font-size: 14px; color: #1A202C;"),
                        ui.span(f"Status: {r.get('status', '')}", style=f"font-size: 12px; font-weight: 700; color: {stat_col}; margin-top: 4px; display: block;"),
                    ),
                    ui.tags.button("Update Selesai", onclick=f"Shiny.setInputValue('btn_finish_report', '{r.get('laporan', '')}', {{priority: 'event'}})", class_="btn-page-nav", style="background-color: #10B981; color: white; border: none;"),
                    style="background: #F8FAFC; border: 1.5px solid #E2E8F0; padding: 12px 18px; border-radius: 8px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;"
                ))
            return ui.div(*cards) if cards else ui.div("Tidak ada tugas untuk PIC ini.")
        except Exception as e: return ui.div(f"Error PIC: {e}")

    @reactive.Effect
    @reactive.event(input.btn_finish_report)
    def _finish_report():
        try:
            lap = input.btn_finish_report()
            sb = config.get_supabase_old()
            sb.table("reports").update({"status": "✅ Selesai"}).eq("laporan", lap).execute()
        except Exception: pass

    # 3. REJECT/DEFECT LIST
    @reactive.Effect
    @reactive.event(input.btn_submit_single_reject)
    def _save_reject_single():
        try:
            sb = config.get_supabase_old()
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sb.table("reject_list").insert({
                "cabang": str(input.rj_cabang()),
                "bin_awal": str(input.rj_bin_awal()),
                "bin": str(input.rj_bin_tujuan()),
                "sku": str(input.rj_sku()).upper().strip(),
                "article_name": str(input.rj_nama()),
                "size": str(input.rj_size()),
                "kategori": str(input.rj_kategori()),
                "keterangan": str(input.rj_ket()),
                "tanggal_input": now_str,
                "status": "PENDING"
            }).execute()
            state.show_success_modal.set(True)
        except Exception as e:
            state.error_modal_message.set(f"Gagal simpan reject: {e}")
            state.show_error_modal.set(True)

    @render.ui
    def reject_list_metrics_ui():
        try:
            sb = config.get_supabase_old()
            res = sb.table("reject_list").select("*").execute()
            df = pd.DataFrame(res.data) if res and res.data else pd.DataFrame()
            tot = len(df)
            defect = len(df[df['bin'].str.contains('DEFECT', case=False, na=False)]) if not df.empty and 'bin' in df.columns else 0
            reject = len(df[df['bin'].str.contains('REJECT', case=False, na=False)]) if not df.empty and 'bin' in df.columns else 0
            return ui.div(
                dark_metric_box("TOTAL ITEMS", f"{tot} SKU", "#3182CE"),
                dark_metric_box("📦 DEFECT (D)", f"{defect}", "#FFA500"),
                dark_metric_box("❌ REJECT (R)", f"{reject}", "#FF4B4B"),
                style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;"
            )
        except Exception: return ui.div()

    @render.ui
    def reject_list_table_ui():
        try:
            sb = config.get_supabase_old()
            res = sb.table("reject_list").select("*").order("id", desc=True).execute()
            df = pd.DataFrame(res.data) if res and res.data else pd.DataFrame()
            if df.empty: return ui.div("Database Reject/Defect kosong.")
            return render_clean_table(df.columns.tolist(), df.fillna("").astype(str).values.tolist(), "tbl_reject")
        except Exception as e: return ui.div(f"Error database: {e}")

    # 4. LOGISTIC SCHEDULE
    df_schedule_res = reactive.Value(pd.DataFrame())

    @reactive.Effect
    @reactive.event(input.btn_run_schedule)
    def _gen_schedule():
        try:
            import random
            start_date_val = pd.to_datetime(input.sc_start_date()).date()
            day_names = ["SENIN", "SELASA", "RABU", "KAMIS", "JUMAT", "SABTU", "MINGGU"]
            
            sb = config.get_supabase_old()
            res_k = sb.table("karyawan").select("*").execute()
            df_k = pd.DataFrame(res_k.data) if res_k and res_k.data else pd.DataFrame()
            
            if df_k.empty:
                default_staff = [
                    {"nama": "ANDI", "posisi": "LOG-ADMIN", "tipe": "Full-Time"},
                    {"nama": "BUDI", "posisi": "LOG-LOADER", "tipe": "Full-Time"},
                    {"nama": "CITRA", "posisi": "WF-PICKER", "tipe": "Full-Time"},
                    {"nama": "DONI", "posisi": "LOG-STORE", "tipe": "Full-Time"}
                ]
                sb.table("karyawan").insert(default_staff).execute()
                res_k = sb.table("karyawan").select("*").execute()
                df_k = pd.DataFrame(res_k.data)

            staff_list = df_k['nama'].tolist() if not df_k.empty else ["STAF 1", "STAF 2"]
            roles = [
                "SHIFT 0 - WF-PICKER", "SHIFT 1 - LOG-ADMIN", "SHIFT 1 - LOG-LOADER",
                "SHIFT 1 - LOG-STORE", "SHIFT 2 - LOG-ADMIN", "SHIFT 2 - LOG-LOADER", "SHIFT 2 - SPV"
            ]
            
            schedule_data = []
            for r in roles:
                row_item = {"SHIFT - ROLE": r}
                for d in day_names:
                    row_item[d] = random.choice(staff_list)
                schedule_data.append(row_item)

            df_schedule_res.set(pd.DataFrame(schedule_data))
            state.show_success_modal.set(True)
        except Exception as e:
            state.error_modal_message.set(f"Gagal generate jadwal: {e}")
            state.show_error_modal.set(True)

    @render.ui
    def schedule_table_ui():
        df = df_schedule_res()
        if df.empty: return ui.div("Klik tombol GENERATE JADWAL SHIFT di atas untuk membuat jadwal.")
        return render_clean_table(df.columns.tolist(), df.values.tolist(), "tbl_schedule")


app = App(app_ui, server)