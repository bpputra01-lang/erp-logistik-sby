import io
import pandas as pd
from shiny import App, Inputs, Outputs, Session, reactive, render, ui
from state import AppState
from views import (
    CUSTOM_HEAD, static_loading_spinner, success_modal, error_modal,
    render_clean_table, metric_box, dark_metric_box,   # <-- Tambahkan metric_box & dark_metric_box di sini
    compare_system_view, stock_minus_view,
    putaway_view, main_dashboard_view, sidebar, login_page, global_header
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
            state.show_error_modal.set(True)
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
    @reactive.Effect
    @reactive.event(input.btn_open_panduan_modal)
    def _panduan_modal():
        cur = state.main_menu()
        if cur == "Compare System":
            guide_body = ui.div(
                ui.tags.details(
                    ui.tags.summary("📋 Informasi Format File & Mapping"),
                    ui.div(
                        ui.tags.strong("Kondisi Stok Berkurang (Sys1 > Sys2):"),
                        ui.tags.ul(ui.tags.li(ui.strong("Stock Tracking:"), " Kolom A=Invoice, Kolom B=SKU, Kolom G=BIN, Kolom K=Qty (Index 10)."), ui.tags.li(ui.strong("RTO Out:"), " Kolom A=No TF, Kolom D=SKU (Index 3), Kolom H=Qty (Index 7).")),
                        ui.tags.strong("Kondisi Stok Bertambah (Sys2 > Sys1):"),
                        ui.tags.ul(ui.tags.li(ui.strong("Purchase Order:"), " Kolom A=No PO, Kolom E=SKU (Index 4), Kolom M=Qty (Index 12)."), ui.tags.li(ui.strong("RTO In:"), " Kolom A=No TF, Kolom D=SKU (Index 3), Kolom H=Qty (Index 7)."), ui.tags.li(ui.strong("Mutasi Refund:"), " Kolom D=SKU (Index 3), Kolom K=Qty (Index 10).")),
                        class_="accordion-content"
                    ), open=True
                )
            )
        elif cur == "Stock Minus":
            guide_body = ui.div(ui.tags.details(ui.tags.summary("📋 Format File"), ui.div("Download Multiple Adjusmet dari Jezpro dan pilih 'Termasuk yang sudah habis'.", class_="accordion-content"), open=True))
        elif cur == "Putaway System":
            guide_body = ui.div(ui.tags.details(ui.tags.summary("📋 Format File"), ui.div("Upload Data Scan Putaway & Data Asal Bin Jezpro.", class_="accordion-content"), open=True))
        else:
            guide_body = ui.div(ui.p(f"Panduan dan Logic untuk halaman '{cur}' belum tersedia.", style="color: #718096; font-style: italic;"), style="text-align: center; padding: 2rem;")

        ui.modal_show(ui.modal(guide_body, title=ui.div(ui.tags.i(class_="fa-solid fa-book-open", style="color: #C5A059; margin-right: 8px;"), f"Panduan & Logic - {cur}"), easy_close=True, footer=ui.modal_button("Tutup", class_="btn-red-gradient")))

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
        elif content_type == "access_denied":
            page_content = ui.div(ui.h2("⛔ Akses Ditolak", style="font-size: 28px; color: #E53E3E; font-weight: bold;"), ui.p("Maaf, halaman ini dibatasi hak aksesnya.", style="color: #718096; font-size: 15px;"), style="padding: 3rem; text-align: center; height: 70vh; display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%;")
        else:
            page_content = ui.div(ui.h2(f"Halaman: {state.main_menu()}", style="font-size: 28px; color: #1A202C; font-weight: bold;"), ui.p("Halaman ini sedang dalam tahap pengembangan.", style="color: #718096; font-size: 15px;"), style="padding: 3rem; text-align: center; height: 70vh; display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%;")

        return ui.div(
            sidebar(state),
            ui.div(global_header(state), page_content, style="flex: 1; height: 100vh; overflow-y: auto; padding: 1.5rem; background-color: #F7FAFC;"),
            style="display: flex; width: 100vw; height: 100vh; overflow: hidden; background-color: #111318;"
        )

app = App(app_ui, server)