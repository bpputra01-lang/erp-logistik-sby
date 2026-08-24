import reflex as rx
from ..state import AppState

def stock_minus_view() -> rx.Component:
    return rx.vstack(
        # Hero Header
        rx.box(
            rx.heading("STOCK MINUS CLEARANCE", size="6", color="#FFFFFF", font_weight="800"),
            padding="1rem 1.5rem",
            background= "linear-gradient(135deg, #1a1d2e 0%, #252a3d 100%)",
            border_radius="12px",
            border_left="5px solid #f39c12",
            width="100%",
            margin_bottom="1.5rem",
        ),

        # Expander Informasi Format File
        rx.disclosure(
            rx.disclosure_button("📋 Informasi Format File", font_weight="bold", color="#2D3748"),
            rx.disclosure_panel(
                rx.text("Format yang diharapkan:", font_weight="bold"),
                rx.text("- **All Data Stock**: Download Multiple Adjustment dari Jezpro dan pilih **Termasuk yang sudah habis**"),
                padding="1rem", background="#EDF2F7", border_radius="8px",
            ),
            width="100%", margin_bottom="1rem",
        ),

        # Expander Logic Thinking
        rx.disclosure(
            rx.disclosure_button("💡 Logic Thinking", font_weight="bold", color="#2D3748"),
            rx.disclosure_panel(
                rx.text("Alur Process Compare Stock Minus:", font_weight="bold"),
                rx.text("- Mengambil SKU yang memiliki Qty System minus (-)"),
                rx.text("- Melakukan shuffle covering stock dari bin prioritas (All Staging, Karantina, dll)"),
                rx.text("- Prioritas BIN Toko vs Gudang Lt.2 / Staging Lt.2"),
                rx.text("- Jika tidak selesai lewat setup, dimasukkan ke item need justifikasi"),
                padding="1rem", background="#EDF2F7", border_radius="8px",
            ),
            width="100%", margin_bottom="1.5rem",
        ),

        # File Upload Component
        rx.upload(
            rx.vstack(
                rx.icon("upload", size=32, color="#f39c12"),
                rx.text("Drag and drop file Excel di sini atau klik untuk browse", color="#4A5568"),
                align="center", spacing="2",
            ),
            id="upload_stock_file",
            border="2px dashed #CBD5E0",
            padding="2rem",
            border_radius="12px",
            width="100%",
            background="#FFFFFF",
        ),
        rx.button(
            "🔃 PROSES DATA",
            on_click=AppState.handle_upload_stock_minus(rx.upload_files("upload_stock_file")),
            color_scheme="orange",
            margin_top="1rem",
            margin_bottom="1.5rem",
        ),

        # Dashboard Metrics (Muncul setelah diproses)
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
                        rx.data_table(data=AppState.df_minus_awal_data, pagination=True, search=True, sort=True),
                        value="tab1", padding="1rem", background="white", border_radius="8px",
                    ),
                    rx.tabs.content(
                        rx.data_table(data=AppState.df_set_up_data, pagination=True, search=True, sort=True),
                        value="tab2", padding="1rem", background="white", border_radius="8px",
                    ),
                    rx.tabs.content(
                        rx.data_table(data=AppState.df_need_adj_data, pagination=True, search=True, sort=True),
                        value="tab3", padding="1rem", background="white", border_radius="8px",
                    ),
                    default_value="tab1", width="100%",
                ),
            ),
        ),
        width="100%",
        padding="1rem",
    )