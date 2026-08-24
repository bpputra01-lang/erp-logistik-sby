import reflex as rx
from ..state import AppState

def render_dynamic_table(data_list) -> rx.Component:
    """Helper untuk merender tabel dinamis berdasarkan list of dict dari Pandas."""
    return rx.box(
        rx.cond(
            data_list,
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.foreach(
                            data_list[0],
                            lambda col_key: rx.table.column_header_cell(
                                col_key, color="#1A202C", font_weight="bold"
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
                                    item[1].to_string(), color="#4A5568"
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
                rx.text("Tidak ada data untuk ditampilkan. Silakan proses file terlebih dahulu.", color="#718096", padding="2rem", font_style="italic", size="2"),
                width="100%"
            ),
        ),
        overflow_x="auto",
        width="100%",
        background="white",
        border_radius="10px",
        padding="0.5rem",
        box_shadow="0 1px 3px rgba(0,0,0,0.05)",
        border="1px solid #E2E8F0",
    )

def stock_minus_view() -> rx.Component:
    return rx.vstack(
        # --- MODAL POPUP INFORMASI & LOGIC THINKING ---
        rx.dialog.root(
            rx.dialog.content(
                rx.dialog.title("📖 Panduan & Logic Stock Minus"),
                rx.vstack(
                    rx.heading("1. Informasi Format File", size="3", color="#E50914"),
                    rx.text("• Download Multiple Adjustment dari Jezpro dan pastikan memilih opsi **Termasuk yang sudah habis**.", color="#4A5568", size="2"),
                    
                    rx.heading("2. Logic Thinking", size="3", color="#E50914", margin_top="1rem"),
                    rx.text("• Mengambil SKU yang memiliki Qty System bernilai minus (-).", color="#4A5568", size="2"),
                    rx.text("• Melakukan alokasi/covering stock dari bin prioritas (All Staging, Karantina, dll).", color="#4A5568", size="2"),
                    rx.text("• Prioritas alokasi antara BIN Toko vs Gudang Lt.2 / Staging Lt.2.", color="#4A5568", size="2"),
                    rx.text("• Sisa minus yang tidak ter-cover otomatis masuk ke tabel Item Need Justifikasi.", color="#4A5568", size="2"),
                    spacing="2",
                    align_items="start",
                ),
                rx.flex(
                    rx.dialog.close(
                        rx.button("Tutup", variant="soft", color_scheme="gray"),
                    ),
                    justify="end",
                    margin_top="1.5rem",
                ),
            ),
            open=AppState.is_info_open,
            on_open_change=AppState.set_is_info_open,
        ),

        # --- MODAL LOADING STATE SAAT PROSES DATA ---
        rx.dialog.root(
            rx.dialog.content(
                rx.vstack(
                    rx.spinner(size="3", color="red"),
                    rx.text("Sedang memproses data Excel, mohon tunggu...", font_weight="bold", color="#2D3748"),
                    align="center",
                    spacing="4",
                    padding="2rem",
                ),
                show=AppState.is_loading,
            ),
        ),

        # --- UPLOAD SECTION (Desain Bersih & Elegan) ---
        rx.vstack(
            rx.upload(
                rx.vstack(
                    rx.circle(
                        rx.icon("upload", size=24, color="#E50914"),
                        size="48px",
                        background="#FFF5F5",
                        border="1px solid #FED7D7",
                    ),
                    rx.vstack(
                        rx.text("Drag and drop file Excel di sini atau klik untuk browse", font_weight="bold", color="#2D3748", size="3"),
                        rx.text("Format yang didukung: .xlsx, .xls", color="#A0AEC0", font_size="12px"),
                        align="center", spacing="1",
                    ),
                    align="center", spacing="3",
                    padding="2.5rem",
                ),
                id="upload_stock_file",
                accept={
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
                    "application/vnd.ms-excel": [".xls"],
                },
                max_files=1,
                border="2px dashed #CBD5E0",
                border_radius="12px",
                width="100%",
                background="#FFFFFF",
                _hover={"background": "#F7FAFC", "border_color": "#E50914"},
                cursor="pointer",
            ),
            
            rx.button(
                rx.hstack(rx.icon("refresh-cw", size=18), rx.text("PROSES DATA SEKARANG"), spacing="2"),
                on_click=AppState.handle_upload_stock_minus(rx.upload_files("upload_stock_file")),
                background_color="#E50914",
                color="white",
                font_weight="bold",
                border_radius="8px",
                width="100%",
                padding="0.75rem",
                _hover={"background_color": "#B20710"},
                cursor="pointer",
                box_shadow="0 2px 4px rgba(229, 9, 20, 0.2)",
            ),
            width="100%",
            spacing="3",
            background="white",
            padding="1.5rem",
            border_radius="12px",
            border="1px solid #E2E8F0",
            box_shadow="0 1px 3px rgba(0,0,0,0.02)",
            margin_bottom="1.5rem",
        ),

        # --- DASHBOARD METRICS & TABS (Muncul Setelah Diproses) ---
        rx.cond(
            AppState.stock_minus_processed,
            rx.vstack(
                # Kotak Metrik 3 Kolom (Tema Gelap Elegan dengan Aksen Merah/Hijau/Abu)
                rx.hstack(
                    rx.box(
                        rx.text("TOTAL QTY MINUS", color="#A0AEC0", font_size="11px", font_weight="bold"),
                        rx.text(AppState.total_qty_minus, color="#E53E3E", font_size="24px", font_weight="bold"),
                        background="#1A1A1A", padding="1.25rem", border_radius="10px", border_left="4px solid #E53E3E", width="100%", text_align="center",
                    ),
                    rx.box(
                        rx.text("TERCOVER", color="#A0AEC0", font_size="11px", font_weight="bold"),
                        rx.text(AppState.total_tercover, color="#38A169", font_size="24px", font_weight="bold"),
                        background="#1A1A1A", padding="1.25rem", border_radius="10px", border_left="4px solid #38A169", width="100%", text_align="center",
                    ),
                    rx.box(
                        rx.text("SISA ADJ", color="#A0AEC0", font_size="11px", font_weight="bold"),
                        rx.text(AppState.total_sisa_adj, color="#DD6B20", font_size="24px", font_weight="bold"),
                        background="#1A1A1A", padding="1.25rem", border_radius="10px", border_left="4px solid #DD6B20", width="100%", text_align="center",
                    ),
                    width="100%", spacing="3", margin_bottom="1.5rem",
                ),

                # Tabs untuk Tabel Hasil
                rx.tabs.root(
                    rx.tabs.list(
                        rx.tabs.trigger("📄 MINUS AWAL", value="tab1"),
                        rx.tabs.trigger("🔄 TEMPLATE SET UP", value="tab2"),
                        rx.tabs.trigger("⚠️ JUSTIFIKASI", value="tab3"),
                    ),
                    rx.tabs.content(
                        render_dynamic_table(AppState.df_minus_awal_data),
                        value="tab1", padding="1rem 0",
                    ),
                    rx.tabs.content(
                        render_dynamic_table(AppState.df_set_up_data),
                        value="tab2", padding="1rem 0",
                    ),
                    rx.tabs.content(
                        render_dynamic_table(AppState.df_need_adj_data),
                        value="tab3", padding="1rem 0",
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