import reflex as rx
from ..state import AppState

def render_dynamic_table(data_list) -> rx.Component:
    """Helper untuk merender tabel dinamis data dictionary dengan warna teks yang jelas."""
    return rx.box(
        rx.cond(
            data_list,
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.foreach(
                            data_list,
                            lambda col_key: rx.table.column_header_cell(
                                col_key, color="#1A202C", font_weight="bold", background="#F7FAFC"
                            )
                        )
                    )
                ),
                rx.table.body(
                    rx.foreach(
                        data_list,
                        lambda row: rx.table.row(
                            rx.foreach(
                                row,
                                lambda item: rx.table.cell(
                                    item[1].to_string(), color="#1A202C", font_size="13px"
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
        # --- 1. MODAL LOADING STATE SAAT PROSES DATA ---
        rx.dialog.root(
            rx.dialog.content(
                rx.vstack(
                    rx.spinner(size="3", color="red"),
                    rx.text("Sedang memproses data Excel, mohon tunggu...", font_weight="bold", color="#2D3748", size="2"),
                    align="center",
                    spacing="2",
                    padding="1.25rem",
                ),
                show=AppState.is_loading,
            ),
        ),

        # --- 2. UPLOAD SECTION (Kotak Panjang, Border Hitam Dashed, Tombol Gold) ---
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
                border="2px dashed #000000", # Garis border box warna HITAM
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

        # --- 3. DASHBOARD METRICS & TABS (Muncul Setelah Diproses) ---
        rx.cond(
            AppState.stock_minus_processed,
            rx.vstack(
                # Banner Sukses Bersih di Atas Metrik (Tanpa Floating Modal Mengganggu)
                rx.hstack(
                    rx.icon("check-circle", size=18, color="#38A169"),
                    rx.text("Data Stock Minus Berhasil Diproses & Divalidasi!", font_weight="bold", color="#22543D", size="2"),
                    background="#C6F6D5", 
                    border="1px solid #9AE6B4", 
                    padding="10px 16px", 
                    border_radius="6px",
                    width="100%", 
                    align="center", 
                    spacing="2", 
                    margin_bottom="1rem",
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

                # Tabs Lengkap Termasuk Panduan & Logic yang Dikembalikan
                rx.tabs.root(
                    rx.tabs.list(
                        rx.tabs.trigger("📄 MINUS AWAL", value="tab1"),
                        rx.tabs.trigger("🔄 TEMPLATE SET UP", value="tab2"),
                        rx.tabs.trigger("⚠️ JUSTIFIKASI", value="tab3"),
                        rx.tabs.trigger("📖 PANDUAN & LOGIC", value="tab4"),
                    ),
                    rx.tabs.content(
                        render_dynamic_table(AppState.df_minus_awal_data),
                        value="tab1", padding="0.75rem 0",
                    ),
                    rx.tabs.content(
                        render_dynamic_table(AppState.df_set_up_data),
                        value="tab2", padding="0.75rem 0",
                    ),
                    rx.tabs.content(
                        render_dynamic_table(AppState.df_need_adj_data),
                        value="tab3", padding="0.75rem 0",
                    ),
                    rx.tabs.content(
                        rx.box(
                            rx.vstack(
                                rx.text("Panduan & Logic Stock Minus System", font_weight="bold", color="#1A202C", size="4"),
                                rx.text("1. Sistem membaca file excel stock minus dan melakukan pencocokan data Qty System vs Qty SO.", color="#4A5568", size="2"),
                                rx.text("2. Tab 'Template Set Up' menghasilkan format otomatis untuk penyesuaian database gudang.", color="#4A5568", size="2"),
                                rx.text("3. Tab 'Justifikasi' menampilkan selisih item yang membutuhkanApproval / Adjust manual dari PIC.", color="#4A5568", size="2"),
                                align_items="start", spacing="3", padding="1rem",
                            ),
                            background="white", border_radius="8px", border="1px solid #E2E8F0", padding="1rem", width="100%",
                        ),
                        value="tab4", padding="0.75rem 0",
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