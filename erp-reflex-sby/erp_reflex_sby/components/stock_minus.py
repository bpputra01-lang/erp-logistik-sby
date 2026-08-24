import reflex as rx
from ..state import AppState

def render_dynamic_table(data_list) -> rx.Component:
    return rx.box(
        rx.cond(
            data_list.length() > 0,
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.foreach(
                            data_list[0].keys(),
                            lambda col: rx.table.column_header_cell(col, color="#2D3748", font_weight="bold")
                        )
                    )
                ),
                rx.table.body(
                    rx.foreach(
                        data_list,
                        lambda row: rx.table.row(
                            rx.foreach(
                                row.values(),
                                lambda val: rx.table.cell(val.to_string(), color="#4A5568")
                            )
                        )
                    )
                ),
                variant="surface",
                size="2",
                width="100%",
            ),
            rx.text("Tidak ada data untuk ditampilkan.", color="#718096", padding="1rem"),
        ),
        overflow_x="auto",
        width="100%",
        background="white",
        border_radius="8px",
        padding="0.5rem",
    )

def stock_minus_view() -> rx.Component:
    return rx.vstack(
        # --- MODAL POPUP INFORMASI & LOGIC THINKING ---
        rx.dialog.root(
            rx.dialog.content(
                rx.dialog.title("📖 Panduan & Logic Stock Minus"),
                rx.vstack(
                    rx.heading("1. Informasi Format File", size="3", color="#f39c12"),
                    rx.text("• Download Multiple Adjustment dari Jezpro dan pastikan memilih opsi **Termasuk yang sudah habis**."),
                    
                    rx.heading("2. Logic Thinking", size="3", color="#f39c12", margin_top="1rem"),
                    rx.text("• Mengambil SKU yang memiliki Qty System bernilai minus (-)."),
                    rx.text("• Melakukan alokasi/covering stock dari bin prioritas (All Staging, Karantina, dll)."),
                    rx.text("• Prioritas alokasi antara BIN Toko vs Gudang Lt.2 / Staging Lt.2."),
                    rx.text("• Sisa minus yang tidak ter-cover otomatis masuk ke tabel Item Need Justifikasi."),
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
                    rx.spinner(size="3", color="orange"),
                    rx.text("Sedang memproses data Excel, mohon tunggu...", font_weight="bold", color="#2D3748"),
                    align="center",
                    spacing="4",
                    padding="2rem",
                ),
                show=AppState.is_loading,
            ),
        ),

        # --- UPLOAD SECTION (Tanpa Judul Ganda) ---
        rx.upload(
            rx.vstack(
                rx.icon("upload", size=36, color="#f39c12"),
                rx.text("Drag and drop file Excel di sini atau klik untuk browse", color="#4A5568", font_weight="600"),
                rx.text("Format yang didukung: .xlsx, .xls", color="#A0AEC0", font_size="12px"),
                align="center", spacing="2",
            ),
            id="upload_stock_file",
            border="2px dashed #CBD5E0",
            padding="2.5rem",
            border_radius="12px",
            width="100%",
            background="#FFFFFF",
            multiple=False,
        ),
        
        rx.button(
            "🔃 PROSES DATA",
            on_click=AppState.handle_upload_stock_minus(rx.upload_files("upload_stock_file")),
            color_scheme="orange",
            size="3",
            width="100%",
            margin_top="1rem",
            margin_bottom="1.5rem",
        ),

        # --- DASHBOARD METRICS & TABS (Muncul Setelah Diproses) ---
        rx.cond(
            AppState.stock_minus_processed,
            rx.vstack(
                # Kotak Metrik 3 Kolom
                rx.hstack(
                    rx.box(
                        rx.text("TOTAL QTY MINUS", color="#8e94ab", font_size="12px", font_weight="bold"),
                        rx.text(AppState.total_qty_minus, color="#f39c12", font_size="28px", font_weight="bold"),
                        background="#1e2130", padding="1.5rem", border_radius="10px", border_left="4px solid #f39c12", width="100%", text_align="center",
                    ),
                    rx.box(
                        rx.text("TERCOVER", color="#8e94ab", font_size="12px", font_weight="bold"),
                        rx.text(AppState.total_tercover, color="#10B981", font_size="28px", font_weight="bold"),
                        background="#1e2130", padding="1.5rem", border_radius="10px", border_left="4px solid #10B981", width="100%", text_align="center",
                    ),
                    rx.box(
                        rx.text("SISA ADJ", color="#8e94ab", font_size="12px", font_weight="bold"),
                        rx.text(AppState.total_sisa_adj, color="#E53E3E", font_size="28px", font_weight="bold"),
                        background="#1e2130", padding="1.5rem", border_radius="10px", border_left="4px solid #E53E3E", width="100%", text_align="center",
                    ),
                    width="100%", spacing="4", margin_bottom="1.5rem",
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
                        value="tab1", padding="1rem",
                    ),
                    rx.tabs.content(
                        render_dynamic_table(AppState.df_set_up_data),
                        value="tab2", padding="1rem",
                    ),
                    rx.tabs.content(
                        render_dynamic_table(AppState.df_need_adj_data),
                        value="tab3", padding="1rem",
                    ),
                    default_value="tab1", width="100%",
                ),
            ),
        ),
        width="100%",
        padding="1rem",
    )