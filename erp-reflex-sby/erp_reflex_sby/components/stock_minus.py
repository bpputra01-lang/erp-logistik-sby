import reflex as rx
from ..state import AppState

def render_clean_table(headers: list, data_rows: list) -> rx.Component:
    """Helper tabel aman memisahkan Header dan Baris agar teks tidak menyatu (mashed)."""
    return rx.box(
        rx.cond(
            data_rows.length() > 0,
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        # Render Kolom Header
                        rx.foreach(
                            headers,
                            lambda col_name: rx.table.column_header_cell(
                                rx.text(col_name, weight="bold", font_size="12px"), 
                                color="#1A202C", 
                                background="#EDF2F7",
                                padding="10px",
                                white_space="nowrap"
                            )
                        )
                    )
                ),
                rx.table.body(
                    # Render Baris Data
                    rx.foreach(
                        data_rows,
                        lambda row: rx.table.row(
                            rx.foreach(
                                row,
                                lambda cell_value: rx.table.cell(
                                    rx.text(cell_value, color="#2D3748", font_size="13px"),
                                    padding="8px 10px",
                                    white_space="nowrap"
                                )
                            )
                        )
                    )
                ),
                variant="surface",
                size="2",
                width="100%",
            ),
            rx.center(
                rx.text("Tidak ada data untuk ditampilkan. Silakan proses file terlebih dahulu.", color="#718096", padding="1.5rem", font_style="italic", size="2"),
                width="100%"
            ),
        ),
        overflow_x="auto",
        width="100%",
        background="white",
        border_radius="8px",
        padding="0.5rem",
        box_shadow="0 1px 3px rgba(0,0,0,0.05)",
        border="1px solid #E2E8F0",
    )

def stock_minus_view() -> rx.Component:
    return rx.vstack(
        # --- 1. HEADER MODUL ---
        rx.hstack(
            rx.text("Modul Stock Minus & Validation", font_weight="bold", color="#1A202C", size="5"),
            justify="between",
            align="center",
            width="100%",
            margin_bottom="1rem",
        ),

        # --- 2. UPLOAD SECTION ---
        rx.vstack(
            rx.text("Upload File STOCK MINUS", font_weight="bold", color="#1A202C", size="3", margin_bottom="0.25rem"),
            
            rx.upload(
                rx.hstack(
                    rx.button(
                        rx.hstack(rx.icon("upload", size=16), rx.text("Upload"), spacing="2"),
                        background_color="#C5A059",
                        color="white",
                        font_weight="bold",
                        border_radius="6px",
                        padding="0.5rem 1.2rem",
                        size="2",
                        cursor="pointer",
                        box_shadow="0 2px 4px rgba(0,0,0,0.1)",
                        _hover={"background_color": "#B38F4D"},
                    ),
                    rx.text("200MB per file • XLSX, XLS", color="#4A5568", size="2", font_weight="medium"),
                    align="center",
                    spacing="4",
                    width="100%",
                    padding="0.5rem 0",
                ),
                id="upload_stock_file",
                accept={
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
                    "application/vnd.ms-excel": [".xls"],
                },
                max_files=1,
                border="2px dashed #CBD5E0",
                border_radius="8px",
                background="#F8FAFC",
                padding="1rem 1.25rem",
                width="100%",
                _hover={"background": "#F1F5F9"},
                cursor="pointer",
            ),
            
            # Nama file terpilih & Tombol Proses
            rx.hstack(
                rx.cond(
                    rx.selected_files("upload_stock_file"),
                    rx.hstack(
                        rx.icon("file-spreadsheet", size=16, color="#38A169"),
                        rx.text(rx.selected_files("upload_stock_file")[0], size="2", color="#22543D", font_weight="bold", truncate=True),
                        spacing="2", align="center", background="#F0FFF4", border="1px solid #C6F6D5", padding="6px 12px", border_radius="6px",
                    ),
                    rx.fragment(),
                ),
                
                rx.button(
                    rx.hstack(rx.icon("play", size=16), rx.text("PROSES DATA"), spacing="2"),
                    on_click=AppState.handle_upload_stock_minus(rx.upload_files("upload_stock_file")),
                    background_color="#E50914",
                    color="white",
                    font_weight="bold",
                    border_radius="6px",
                    padding="0.5rem 1.25rem",
                    size="2",
                    _hover={"background_color": "#B20710"},
                    cursor="pointer",
                    box_shadow="0 2px 4px rgba(229, 9, 20, 0.2)",
                ),
                width="100%",
                justify="between",
                align="center",
                margin_top="0.5rem",
            ),
            
            width="100%",
            background="white",
            padding="1.25rem",
            border_radius="10px",
            border="1px solid #E2E8F0",
            box_shadow="0 1px 3px rgba(0,0,0,0.02)",
            margin_bottom="1.25rem",
            align_items="start",
        ),

        # --- 3. DASHBOARD METRICS & TABS ---
        rx.cond(
            AppState.stock_minus_processed,
            rx.vstack(
                # Banner Sukses (Gaya Pop-up Inline yang Rapi)
                rx.hstack(
                    rx.icon("check-circle", size=20, color="#15803d"),
                    rx.text("Data Stock Minus Berhasil Diproses & Divalidasi!", font_weight="bold", color="#15803d", size="3"),
                    background="#dcfce7", 
                    border="1px solid #86efac", 
                    padding="12px 18px", 
                    border_radius="8px",
                    width="100%", 
                    align="center", 
                    justify="center",
                    spacing="2", 
                    margin_bottom="1.25rem",
                    box_shadow="0 4px 6px rgba(0,0,0,0.05)",
                ),

                # Kotak Metrik 3 Kolom
                rx.hstack(
                    rx.box(
                        rx.text("TOTAL QTY MINUS", color="#A0AEC0", font_size="11px", font_weight="bold"),
                        rx.text(AppState.total_qty_minus, color="#E53E3E", font_size="22px", font_weight="bold"),
                        background="#1A1A1A", padding="1rem", border_radius="8px", border_left="4px solid #E53E3E", width="100%", text_align="center",
                    ),
                    rx.box(
                        rx.text("TERCOVER", color="#A0AEC0", font_size="11px", font_weight="bold"),
                        rx.text(AppState.total_tercover, color="#38A169", font_size="22px", font_weight="bold"),
                        background="#1A1A1A", padding="1rem", border_radius="8px", border_left="4px solid #38A169", width="100%", text_align="center",
                    ),
                    rx.box(
                        rx.text("SISA ADJ", color="#A0AEC0", font_size="11px", font_weight="bold"),
                        rx.text(AppState.total_sisa_adj, color="#DD6B20", font_size="22px", font_weight="bold"),
                        background="#1A1A1A", padding="1rem", border_radius="8px", border_left="4px solid #DD6B20", width="100%", text_align="center",
                    ),
                    width="100%", spacing="3", margin_bottom="1.25rem",
                ),

                # Tabs Data Bersih menggunakan State baru yang terpisah
                rx.tabs.root(
                    rx.tabs.list(
                        rx.tabs.trigger(rx.hstack(rx.icon("file-text", size=14), rx.text("MINUS AWAL", font_weight="bold")), value="tab1", color="#1A202C", _selected={"color": "#E50914", "border_bottom": "2px solid #E50914"}),
                        rx.tabs.trigger(rx.hstack(rx.icon("refresh-cw", size=14), rx.text("TEMPLATE SET UP", font_weight="bold")), value="tab2", color="#1A202C", _selected={"color": "#E50914", "border_bottom": "2px solid #E50914"}),
                        rx.tabs.trigger(rx.hstack(rx.icon("alert-triangle", size=14), rx.text("JUSTIFIKASI", font_weight="bold")), value="tab3", color="#1A202C", _selected={"color": "#E50914", "border_bottom": "2px solid #E50914"}),
                    ),
                    rx.tabs.content(
                        render_clean_table(AppState.df_minus_awal_headers, AppState.df_minus_awal_rows),
                        value="tab1", padding="0.75rem 0",
                    ),
                    rx.tabs.content(
                        render_clean_table(AppState.df_set_up_headers, AppState.df_set_up_rows),
                        value="tab2", padding="0.75rem 0",
                    ),
                    rx.tabs.content(
                        render_clean_table(AppState.df_need_adj_headers, AppState.df_need_adj_rows),
                        value="tab3", padding="0.75rem 0",
                    ),
                    default_value="tab1", width="100%",
                ),
                width="100%",
                spacing="0",
            ),
        ),
        width="100%",
        padding="1rem",
    )