import reflex as rx
from ..state import AppState
from .common import metric_box, render_table_row

def main_dashboard() -> rx.Component:
    return rx.box(
        rx.vstack(
            # --- HEADER ---
            rx.hstack(
                rx.hstack(
                    rx.box(width="10px", height="32px", background="#E50914", border_radius="4px"),
                    rx.vstack(
                        rx.heading("DATABASE ONGKIR IN/OUT", size="5", color="#111111", font_weight="800"),
                        rx.text(f"Logged in as: {AppState.user_display_name} ({AppState.role})", size="2", color="#666666"),
                        align_items="start", spacing="0",
                    ),
                    align="center", spacing="3",
                ),
                rx.hstack(
                    rx.badge("● SUPABASE CONNECTED", color_scheme="green", variant="surface", size="3"),
                    rx.button(
                        "Logout", 
                        on_click=AppState.logout, 
                        variant="soft", 
                        color_scheme="red",
                        size="2",
                        style={"cursor": "pointer", "font-weight": "bold"}
                    ),
                    spacing="3", align="center"
                ),
                justify="between", width="100%", padding_bottom="1.2rem", border_bottom="2px solid #EAEAEA",
            ),

            # --- TABS ---
            rx.tabs.root(
                default_value="tab1",
                items=[
                    rx.tabs.list(
                        rx.tabs.trigger("📥 INPUT & BATCH DATA", value="tab1"),
                        rx.tabs.trigger("📊 SUMMARY & HISTORY", value="tab2"),
                        background="#F1F3F5", padding="4px", border_radius="10px",
                    ),

                    # --- TAB 1: FORM INPUT & CSV UPLOAD ---
                    rx.tabs.content(
                        rx.grid(
                            rx.box(
                                rx.vstack(
                                    rx.hstack(
                                        rx.text("📝", size="5"),
                                        rx.heading("Input Transaksi Manual", size="4", color="#111111"),
                                        align="center", spacing="2",
                                    ),
                                    rx.divider(border_color="#EAEAEA"),
                                    rx.vstack(
                                        rx.text("NAMA SUPPLIER", size="1", font_weight="700", color="#444444"),
                                        rx.input(placeholder="Masukkan Nama Supplier...", value=AppState.input_supplier, on_change=AppState.set_supplier, width="100%", size="3"),
                                        spacing="1", width="100%",
                                    ),
                                    rx.hstack(
                                        rx.vstack(
                                            rx.text("EKSPEDISI", size="1", font_weight="700", color="#444444"),
                                            rx.input(placeholder="Nama Ekspedisi...", value=AppState.input_ekspedisi, on_change=AppState.set_ekspedisi, width="100%", size="3"),
                                            spacing="1", width="100%",
                                        ),
                                        rx.vstack(
                                            rx.text("TOTAL KOLI", size="1", font_weight="700", color="#444444"),
                                            rx.input(type="number", placeholder="Jumlah Koli", value=AppState.input_koli, on_change=AppState.set_koli, width="100%", size="3"),
                                            spacing="1", width="100%",
                                        ),
                                        width="100%", spacing="3",
                                    ),
                                    rx.hstack(
                                        rx.vstack(
                                            rx.text("TOTAL ONGKIR (RP)", size="1", font_weight="700", color="#444444"),
                                            rx.input(type="number", placeholder="Rp 0", value=AppState.input_ongkir, on_change=AppState.set_ongkir, width="100%", size="3"),
                                            spacing="1", width="100%",
                                        ),
                                        rx.vstack(
                                            rx.text("TANGGAL", size="1", font_weight="700", color="#444444"),
                                            rx.input(type="date", value=AppState.input_tgl, on_change=AppState.set_tgl, width="100%", size="3"),
                                            spacing="1", width="100%",
                                        ),
                                        width="100%", spacing="3",
                                    ),
                                    rx.box(height="5px"),
                                    rx.button(
                                        "🚀 SIMPAN DATA ONGKIR", 
                                        on_click=AppState.save_single_data, 
                                        width="100%", size="3",
                                        style={
                                            "background": "linear-gradient(135deg, #E50914 0%, #B20710 100%)",
                                            "color": "#FFFFFF", "font-weight": "800", "border-radius": "10px",
                                            "cursor": "pointer", "box-shadow": "0 4px 12px rgba(229, 9, 20, 0.25)"
                                        }
                                    ),
                                    spacing="4",
                                ),
                                padding="1.8rem", background="#FFFFFF", border_radius="16px", 
                                border="1px solid #EAEAEA", box_shadow="0 10px 30px rgba(0,0,0,0.04)",
                            ),
                            rx.box(
                                rx.vstack(
                                    rx.hstack(
                                        rx.text("📁", size="5"),
                                        rx.heading("Batch CSV Upload", size="4", color="#111111"),
                                        align="center", spacing="2",
                                    ),
                                    rx.divider(border_color="#EAEAEA"),
                                    rx.upload(
                                        rx.vstack(
                                            rx.box(
                                                rx.text("☁️", size="6"),
                                                padding="10px", background="#F8F9FA", border_radius="50%"
                                            ),
                                            rx.button("Pilih File CSV", color_scheme="gray", variant="surface", size="2"),
                                            rx.text("atau tarik & lepaskan file CSV di sini", size="2", color="#888888"),
                                            align="center", spacing="2",
                                        ),
                                        id="upload_csv", 
                                        border="2px dashed #E50914", 
                                        padding="2.5rem", border_radius="12px", width="100%",
                                        background="#FFF8F8",
                                    ),
                                    rx.button(
                                        "⚡ EXECUTE BATCH UPLOAD", 
                                        on_click=AppState.handle_upload(rx.upload_files(upload_id="upload_csv")), 
                                        width="100%", size="3",
                                        style={
                                            "background": "#111111", "color": "#FFFFFF", "font-weight": "800",
                                            "border-radius": "10px", "cursor": "pointer",
                                            "box-shadow": "0 4px 12px rgba(0, 0, 0, 0.15)"
                                        }
                                    ),
                                    spacing="4",
                                ),
                                padding="1.8rem", background="#FFFFFF", border_radius="16px", 
                                border="1px solid #EAEAEA", box_shadow="0 10px 30px rgba(0,0,0,0.04)",
                            ),
                            columns=rx.breakpoints(initial="1", sm="2"), spacing="5", width="100%", margin_top="1.5rem",
                        ),
                        value="tab1",
                    ),

                    # --- TAB 2: METRICS & TABEL HISTORY ---
                    rx.tabs.content(
                        rx.vstack(
                            rx.hstack(
                                rx.hstack(
                                    rx.text("FILTER EKSPEDISI:", size="2", font_weight="bold", color="#555555"),
                                    rx.select(AppState.list_ekspedisi_options, value=AppState.filter_ekspedisi, on_change=AppState.set_filter_ekspedisi, width="220px", size="2"),
                                    align="center", spacing="2",
                                ),
                                rx.cond(
                                    AppState.selected_ids.length() > 0,
                                    rx.button(f"🗑️ HAPUS ({AppState.selected_ids.length()}) DATA", on_click=AppState.open_delete_modal, color_scheme="red", variant="solid", size="2"),
                                ),
                                justify="between", width="100%", margin_top="1.5rem", margin_bottom="0.5rem",
                            ),
                            rx.grid(
                                metric_box("💰 BIAYA ALL", AppState.total_biaya_all, "#E50914"),
                                metric_box("📦 KOLI ALL", AppState.total_koli_all, "#111111"),
                                metric_box("📊 AVG COST ALL", AppState.avg_cost_all, "#E50914"),
                                metric_box("🚚 BIAYA DATANG", AppState.biaya_datang, "#2E7D32"),
                                metric_box("📦 KOLI DATANG", AppState.koli_datang, "#2E7D32"),
                                metric_box("🔄 BIAYA RTO", AppState.biaya_rto, "#C62828"),
                                columns=rx.breakpoints(initial="1", sm="3"), spacing="4", width="100%",
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
                                        style={"background_color": "#F8F9FA"}
                                    ),
                                    rx.table.body(rx.foreach(AppState.filtered_list, render_table_row)),
                                    width="100%",
                                ),
                                background="#FFFFFF", border_radius="16px", border="1px solid #EAEAEA", 
                                padding="1rem", width="100%", box_shadow="0 10px 30px rgba(0,0,0,0.04)",
                            ),
                            spacing="4", width="100%",
                        ),
                        value="tab2",
                    ),
                ],
                width="100%",
            ),

            # --- DELETE MODAL ---
            rx.dialog.root(
                rx.dialog.content(
                    rx.dialog.title("⚠️ Konfirmasi Hapus Data"),
                    rx.dialog.description("Apakah Anda yakin ingin menghapus data terpilih secara permanen dari database Supabase?"),
                    rx.hstack(
                        rx.button("Batal", on_click=AppState.close_delete_modal, variant="soft", color_scheme="gray"),
                        rx.button("Ya, Hapus Permanen", on_click=AppState.execute_delete, color_scheme="red"),
                        justify="end", spacing="3", margin_top="1.5rem",
                    ),
                    background="#FFFFFF", border="1px solid #EAEAEA", border_radius="16px",
                ),
                open=AppState.show_delete_modal,
            ),
            spacing="5", padding="2.5rem", max_width="1280px", margin="0 auto", on_mount=AppState.load_data,
        ),
        background_color="#F8F9FA", min_height="100vh",
    )