import reflex as rx
from ..state import AppState

def render_clean_table(headers: list, data_rows: list) -> rx.Component:
    return rx.box(
        rx.cond(
            data_rows.length() > 0,
            rx.table.root(
                rx.table.header(rx.table.row(rx.foreach(headers, lambda col_name: rx.table.column_header_cell(rx.text(col_name, weight="bold", font_size="12px"), color="#1A202C", background="#EDF2F7", padding="10px", white_space="nowrap")))),
                rx.table.body(rx.foreach(data_rows, lambda row: rx.table.row(rx.foreach(row, lambda cell_value: rx.table.cell(rx.text(cell_value, color="#2D3748", font_size="13px"), padding="8px 10px", white_space="nowrap"))))),
                variant="surface", size="2", width="100%",
            ),
            rx.center(rx.text("Tidak ada data untuk ditampilkan.", color="#718096", padding="1.5rem", font_style="italic", size="2"), width="100%"),
        ),
        overflow_x="auto", width="100%", background="white", border_radius="8px", padding="0.5rem", box_shadow="0 1px 3px rgba(0,0,0,0.05)", border="1px solid #E2E8F0",
    )

def success_modal() -> rx.Component:
    return rx.cond(
        AppState.show_success_modal,
        rx.center(
            rx.vstack(
                rx.box(
                    rx.icon("check", size=65, color="white", stroke_width=4),
                    class_name="animate-pop",
                    background="linear-gradient(135deg, #4ade80 0%, #16a34a 100%)",
                    border_radius="50%", padding="20px", box_shadow="0 10px 25px rgba(74, 222, 128, 0.4)", margin_bottom="5px"
                ),
                rx.heading("Success!", size="8", color="#1A202C", weight="bold"),
                align_items="center", spacing="3", background="transparent"
            ),
            position="fixed", top="0", left="0", width="100vw", height="100vh", z_index="9999",
            background="rgba(255, 255, 255, 0.7)", backdrop_filter="blur(5px)",
        )
    )

def stock_minus_view() -> rx.Component:
    return rx.vstack(
        success_modal(), 
        
        rx.hstack(
            justify="between", align="center", width="100%", margin_bottom="1rem",
        ),

        rx.vstack(
            rx.text("Upload File STOCK MINUS", font_weight="bold", color="#1A202C", size="3", margin_bottom="0.25rem"),
            rx.upload(
                rx.hstack(
                    rx.button(rx.hstack(rx.icon("upload", size=16), rx.text("Upload"), spacing="2"), background_color="#C5A059", color="white", font_weight="bold", border_radius="6px", padding="0.5rem 1.2rem", cursor="pointer"),
                    rx.text("200MB per file • XLSX, XLS", color="#4A5568", size="2", font_weight="medium"),
                    align="center", spacing="4", width="100%", padding="0.5rem 0",
                ),
                id="upload_stock_file", max_files=1, border="2px dashed black", border_radius="8px", background="#F8FAFC", padding="1rem 1.25rem", width="100%", cursor="pointer",
            ),
            rx.hstack(
                rx.cond(rx.selected_files("upload_stock_file"), rx.hstack(rx.icon("file-spreadsheet", size=16, color="#38A169"), rx.text(rx.selected_files("upload_stock_file")[0], size="2", color="#22543D", font_weight="bold", truncate=True), spacing="2", align="center", background="#F0FFF4", border="1px solid #C6F6D5", padding="6px 12px", border_radius="6px"), rx.fragment()),
                rx.button(rx.hstack(rx.icon("play", size=16), rx.text("PROSES DATA"), spacing="2"), on_click=AppState.handle_upload_stock_minus(rx.upload_files("upload_stock_file")), background_color="#E50914", color="white", font_weight="bold", border_radius="6px", padding="0.5rem 1.25rem", cursor="pointer"),
                width="100%", justify="between", align="center", margin_top="0.5rem",
            ),
            width="100%", background="white", padding="1.25rem", border_radius="10px", border="1px solid #E2E8F0", margin_bottom="1.25rem", align_items="start",
        ),

        rx.cond(
            AppState.stock_minus_processed,
            rx.vstack(
                rx.hstack(
                    rx.box(rx.text("TOTAL QTY MINUS", color="#A0AEC0", font_size="11px", font_weight="bold"), rx.text(AppState.total_qty_minus, color="#E53E3E", font_size="22px", font_weight="bold"), background="#1A1A1A", padding="1rem", border_radius="8px", border_left="4px solid #E53E3E", width="100%", text_align="center"),
                    rx.box(rx.text("TERCOVER", color="#A0AEC0", font_size="11px", font_weight="bold"), rx.text(AppState.total_tercover, color="#38A169", font_size="22px", font_weight="bold"), background="#1A1A1A", padding="1rem", border_radius="8px", border_left="4px solid #38A169", width="100%", text_align="center"),
                    rx.box(rx.text("SISA ADJ", color="#A0AEC0", font_size="11px", font_weight="bold"), rx.text(AppState.total_sisa_adj, color="#DD6B20", font_size="22px", font_weight="bold"), background="#1A1A1A", padding="1rem", border_radius="8px", border_left="4px solid #DD6B20", width="100%", text_align="center"),
                    width="100%", spacing="3", margin_bottom="1.25rem",
                ),
                rx.tabs.root(
                    rx.tabs.list(
                        rx.tabs.trigger(rx.hstack(rx.icon("file-text", size=14), rx.text("MINUS AWAL", font_weight="bold")), value="tab1", color="#1A202C", _selected={"color": "#E50914", "border_bottom": "2px solid #E50914"}),
                        rx.tabs.trigger(rx.hstack(rx.icon("refresh-cw", size=14), rx.text("TEMPLATE SET UP", font_weight="bold")), value="tab2", color="#1A202C", _selected={"color": "#E50914", "border_bottom": "2px solid #E50914"}),
                        rx.tabs.trigger(rx.hstack(rx.icon("alert-triangle", size=14), rx.text("JUSTIFIKASI", font_weight="bold")), value="tab3", color="#1A202C", _selected={"color": "#E50914", "border_bottom": "2px solid #E50914"}),
                    ),
                    
                    # --- TAB 1: MINUS AWAL ---
                    rx.tabs.content(
                        rx.vstack(
                            rx.flex(
                                rx.button(
                                    rx.hstack(rx.icon("download", size=16), rx.text("Download Excel"), spacing="2", align="center"),
                                    on_click=AppState.download_excel_data("minus_awal"),
                                    background_color="#10B981", color="white", font_weight="bold", border_radius="6px",
                                    box_shadow="0 2px 4px rgba(0,0,0,0.1)", cursor="pointer", _hover={"background_color": "#059669"},
                                ), justify="end", width="100%", margin_bottom="0.5rem"
                            ),
                            render_clean_table(AppState.df_minus_awal_headers, AppState.df_minus_awal_rows),
                        ), value="tab1", padding="0.75rem 0"
                    ),
                    
                    # --- TAB 2: TEMPLATE SET UP ---
                    rx.tabs.content(
                        rx.vstack(
                            rx.flex(
                                rx.button(
                                    rx.hstack(rx.icon("download", size=16), rx.text("Download Excel"), spacing="2", align="center"),
                                    on_click=AppState.download_excel_data("set_up"),
                                    background_color="#10B981", color="white", font_weight="bold", border_radius="6px",
                                    box_shadow="0 2px 4px rgba(0,0,0,0.1)", cursor="pointer", _hover={"background_color": "#059669"},
                                ), justify="end", width="100%", margin_bottom="0.5rem"
                            ),
                            render_clean_table(AppState.df_set_up_headers, AppState.df_set_up_rows),
                        ), value="tab2", padding="0.75rem 0"
                    ),
                    
                    # --- TAB 3: JUSTIFIKASI ---
                    rx.tabs.content(
                        rx.vstack(
                            rx.flex(
                                rx.button(
                                    rx.hstack(rx.icon("download", size=16), rx.text("Download Excel"), spacing="2", align="center"),
                                    on_click=AppState.download_excel_data("justifikasi"),
                                    background_color="#10B981", color="white", font_weight="bold", border_radius="6px",
                                    box_shadow="0 2px 4px rgba(0,0,0,0.1)", cursor="pointer", _hover={"background_color": "#059669"},
                                ), justify="end", width="100%", margin_bottom="0.5rem"
                            ),
                            render_clean_table(AppState.df_need_adj_headers, AppState.df_need_adj_rows),
                        ), value="tab3", padding="0.75rem 0"
                    ),
                    
                    default_value="tab1", width="100%",
                ),
                width="100%", spacing="0",
            ),
        ),
        width="100%", padding="1rem",
    )