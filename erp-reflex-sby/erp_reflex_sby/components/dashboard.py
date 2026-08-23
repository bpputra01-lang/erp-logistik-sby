import reflex as rx
from ..state import AppState
from .common import metric_box, render_table_row

def main_dashboard() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.vstack(
                    rx.heading("🛻 DATABASE ONGKIR IN/OUT", size="6", color="white"),
                    rx.text(f"Logged in as: {AppState.user_display_name} ({AppState.role})", size="2", color="#8F95B2"),
                    align_items="start", spacing="1",
                ),
                rx.hstack(
                    rx.badge("● SUPABASE CONNECTED", color_scheme="green", variant="soft", size="3"),
                    rx.button("Logout", on_click=AppState.logout, color_scheme="red", variant="soft", size="2"),
                    spacing="3",
                ),
                justify="between", width="100%", padding_bottom="1rem", border_bottom="1px solid #232738",
            ),

            rx.tabs.root(
                rx.tabs.list(
                    rx.tabs.trigger("📥 INPUT & BATCH DATA", value="tab1"),
                    rx.tabs.trigger("📊 SUMMARY & HISTORY", value="tab2"),
                    background="#141724", padding="4px", border_radius="8px",
                ),

                rx.tabs.content(
                    rx.grid(
                        rx.box(
                            rx.vstack(
                                rx.heading("📝 Input Transaksi Manual", size="4", color="#FFD700"),
                                rx.input(placeholder="Nama Supplier...", value=AppState.input_supplier, on_change=AppState.set_supplier, width="100%"),
                                rx.hstack(
                                    rx.input(placeholder="Ekspedisi...", value=AppState.input_ekspedisi, on_change=AppState.set_ekspedisi, width="100%"),
                                    rx.input(type="number", placeholder="Total Koli", value=AppState.input_koli, on_change=AppState.set_koli, width="100%"),
                                    width="100%",
                                ),
                                rx.hstack(
                                    rx.input(type="number", placeholder="Total Ongkir (Rp)", value=AppState.input_ongkir, on_change=AppState.set_ongkir, width="100%"),
                                    rx.input(type="date", value=AppState.input_tgl, on_change=AppState.set_tgl, width="100%"),
                                    width="100%",
                                ),
                                rx.button("🚀 SIMPAN DATA ONGKIR", on_click=AppState.save_single_data, color_scheme="gold", width="100%", size="3"),
                                spacing="3",
                            ),
                            padding="1.5rem", background="#141724", border_radius="12px", border="1px solid #232738",
                        ),
                        rx.box(
                            rx.vstack(
                                rx.heading("📁 Batch CSV Upload", size="4", color="#00EB93"),
                                rx.upload(
                                    rx.vstack(
                                        rx.button("Pilih File CSV", color_scheme="gray", variant="outline"),
                                        rx.text("Drag and drop file CSV di sini", size="2", color="#8F95B2"),
                                    ),
                                    id="upload_csv", border="1px dashed #FFD700", padding="2rem", border_radius="10px", width="100%",
                                ),
                                rx.button("⚡ EXECUTE BATCH UPLOAD", on_click=AppState.handle_upload(rx.upload_files(upload_id="upload_csv")), color_scheme="green", width="100%", size="3"),
                                spacing="3",
                            ),
                            padding="1.5rem", background="#141724", border_radius="12px", border="1px solid #232738",
                        ),
                        columns=rx.breakpoints(initial="1", sm="2"), spacing="4", width="100%", margin_top="1rem",
                    ),
                    value="tab1",
                ),

                rx.tabs.content(
                    rx.vstack(
                        rx.hstack(
                            rx.select(AppState.list_ekspedisi_options, value=AppState.filter_ekspedisi, on_change=AppState.set_filter_ekspedisi, width="200px"),
                            rx.cond(
                                AppState.selected_ids.length() > 0,
                                rx.button(f"🗑️ HAPUS ({AppState.selected_ids.length()}) DATA", on_click=AppState.open_delete_modal, color_scheme="red", variant="solid"),
                            ),
                            justify="between", width="100%", margin_top="1rem",
                        ),
                        rx.grid(
                            metric_box("💰 BIAYA ALL", AppState.total_biaya_all, "#FFD700"),
                            metric_box("📦 KOLI ALL", AppState.total_koli_all, "#FFD700"),
                            metric_box("📊 AVG COST ALL", AppState.avg_cost_all, "#FFD700"),
                            metric_box("🚚 BIAYA DATANG", AppState.biaya_datang, "#00EB93"),
                            metric_box("📦 KOLI DATANG", AppState.koli_datang, "#00EB93"),
                            metric_box("🔄 BIAYA RTO", AppState.biaya_rto, "#FF4B4B"),
                            columns=rx.breakpoints(initial="1", sm="3"), spacing="3", width="100%",
                        ),
                        rx.box(
                            rx.table.root(
                                rx.table.header(
                                    rx.table.row(
                                        rx.table.column_header_cell("SELECT"),
                                        rx.table.column_header_cell("TANGGAL"),
                                        rx.table.column_header_cell("SUPPLIER"),
                                        rx.table.column_header_cell("EKSPEDISI"),
                                        rx.table.column_header_cell("KOLI"),
                                        rx.table.column_header_cell("TOTAL ONGKIR"),
                                    ),
                                ),
                                rx.table.body(rx.foreach(AppState.filtered_list, render_table_row)),
                                width="100%",
                            ),
                            background="#141724", border_radius="12px", border="1px solid #232738", padding="1rem", width="100%",
                        ),
                        spacing="4", width="100%",
                    ),
                    value="tab2",
                ),
                width="100%",
            ),

            rx.dialog.root(
                rx.dialog.content(
                    rx.dialog.title("⚠️ Konfirmasi Delete"),
                    rx.dialog.description("Yakin mau menghapus data dari Supabase secara permanen?"),
                    rx.hstack(
                        rx.button("Batal", on_click=AppState.close_delete_modal, variant="soft"),
                        rx.button("Ya, Hapus!", on_click=AppState.execute_delete, color_scheme="red"),
                        justify="end", spacing="3", margin_top="1rem",
                    ),
                    background="#141724", border="1px solid #232738",
                ),
                open=AppState.show_delete_modal,
            ),
            spacing="4", padding="2rem", max_width="1200px", margin="0 auto", on_mount=AppState.load_data,
        ),
        background_color="#0d0f17", min_height="100vh",
    )