import reflex as rx
from ..state import AppState
from .common import metric_box, render_table_row

# Style Input Box dengan BORDER TEGAS GELAP & KONTRASTING
STYLE_INPUT = {
    "background_color": "#FFFFFF !important",
    "color": "#111111 !important",
    "border": "2px solid #4A5568 !important",
    "border_radius": "8px !important",
    "font_weight": "600",
    "_focus": {
        "border": "2px solid #E50914 !important",
        "box_shadow": "0 0 0 1px #E50914 !important",
        "outline": "none !important",
    },
    "_hover": {
        "border_color": "#1A202C !important",
    },
    "_placeholder": {
        "color": "#718096 !important",
        "font_weight": "normal",
    }
}

STYLE_LABEL = {
    "size": "1",
    "font_weight": "800",
    "color": "#1A202C",
    "margin_bottom": "2px",
    "letter_spacing": "0.5px"
}

def main_dashboard() -> rx.Component:
    return rx.box(
        rx.vstack(
            # --- HEADER ---
            rx.hstack(
                rx.hstack(
                    rx.box(width="10px", height="32px", background="#E50914", border_radius="4px"),
                    rx.vstack(
                        rx.heading("DATABASE ONGKIR IN/OUT & ANALYTICS", size="5", color="#111111", font_weight="800"),
                        rx.text(f"Logged in as: {AppState.user_display_name} ({AppState.role})", size="2", color="#4A5568"),
                        align_items="start", spacing="0",
                    ),
                    align="center", spacing="3",
                ),
                rx.hstack(
                    # --- TITIK HIJAU DENGAN ANIMASI KEDIP PULSE ---
                    rx.box(
                        width="10px", 
                        height="10px", 
                        background="#10B981", 
                        border_radius="50%",
                        style={
                            "animation": "pulse-glow 1.5s infinite ease-in-out",
                        }
                    ),
                    rx.text("ONLINE", size="2", font_weight="800", color="#065F46"),
                    align="center", spacing="2",
                ),
                padding="8px 16px",
                background="#D1FAE5",
                border="1.5px solid #A7F3D0",
                border_radius="20px",
                justify="between", width="100%", align="center"
            ),
            width="100%", padding_bottom="1.2rem", border_bottom="2px solid #CBD5E0",
        ),

        # --- TABS (Hanya Input dan Summary) ---
        rx.tabs.root(
            rx.tabs.list(
                rx.tabs.trigger(
                    "📥 INPUT & BATCH DATA", 
                    value="tab1",
                    style={
                        "color": "#1A202C", "font-weight": "800", "padding": "8px 16px", "cursor": "pointer",
                        "_selected": {"color": "#E50914 !important", "border-bottom": "3px solid #E50914"}
                    }
                ),
                rx.tabs.trigger(
                    "📊 SUMMARY & HISTORY", 
                    value="tab2",
                    style={
                        "color": "#1A202C", "font-weight": "800", "padding": "8px 16px", "cursor": "pointer",
                        "_selected": {"color": "#E50914 !important", "border-bottom": "3px solid #E50914"}
                    }
                ),
                background="#E2E8F0", padding="4px", border_radius="10px", margin_top="0.5rem",
            ),

            # --- TAB 1: FORM INPUT & CSV UPLOAD ---
            rx.tabs.content(
                rx.grid(
                    rx.box(
                        rx.vstack(
                            rx.hstack(
                                rx.text("📝", size="5"),
                                rx.heading("Input Transaksi Manual", size="4", color="#1A202C"),
                                align="center", spacing="2",
                            ),
                            rx.divider(border_color="#CBD5E0"),
                            rx.vstack(
                                rx.text("NAMA SUPPLIER", **STYLE_LABEL),
                                rx.input(placeholder="Masukkan Nama Supplier...", value=AppState.input_supplier, on_change=AppState.set_supplier, width="100%", size="3", style=STYLE_INPUT),
                                spacing="1", width="100%",
                            ),
                            rx.hstack(
                                rx.vstack(
                                    rx.text("EKSPEDISI", **STYLE_LABEL),
                                    rx.input(placeholder="Nama Ekspedisi...", value=AppState.input_ekspedisi, on_change=AppState.set_ekspedisi, width="100%", size="3", style=STYLE_INPUT),
                                    spacing="1", width="100%",
                                ),
                                rx.vstack(
                                    rx.text("TOTAL KOLI", **STYLE_LABEL),
                                    rx.input(type="number", placeholder="Jumlah Koli", value=AppState.input_koli, on_change=AppState.set_koli, width="100%", size="3", style=STYLE_INPUT),
                                    spacing="1", width="100%",
                                ),
                                width="100%", spacing="3",
                            ),
                            rx.hstack(
                                rx.vstack(
                                    rx.text("TOTAL ONGKIR (RP)", **STYLE_LABEL),
                                    rx.input(type="number", placeholder="Rp 0", value=AppState.input_ongkir, on_change=AppState.set_ongkir, width="100%", size="3", style=STYLE_INPUT),
                                    spacing="1", width="100%",
                                ),
                                rx.vstack(
                                    rx.text("TANGGAL", **STYLE_LABEL),
                                    rx.input(type="date", value=AppState.input_tgl, on_change=AppState.set_tgl, width="100%", size="3", style=STYLE_INPUT),
                                    spacing="1", width="100%",
                                ),
                                width="100%", spacing="3",
                            ),
                            rx.box(height="5px"),
                            rx.button(
                                "🚀 SIMPAN DATA ONGKIR", on_click=AppState.save_single_data, width="100%", size="3",
                                style={
                                    "background": "linear-gradient(135deg, #E50914 0%, #B20710 100%)",
                                    "color": "#FFFFFF !important", "font-weight": "800", "border-radius": "10px",
                                    "cursor": "pointer", "box-shadow": "0 4px 12px rgba(229, 9, 20, 0.25)"
                                }
                            ),
                            spacing="4", width="100%",
                        ),
                        padding="1.8rem", background="#FFFFFF", border_radius="16px", 
                        border="2px solid #CBD5E0", box_shadow="0 10px 25px rgba(0,0,0,0.03)",
                        width="100%",
                    ),
                    rx.box(
                        rx.vstack(
                            rx.hstack(
                                rx.text("📁", size="5"),
                                rx.heading("Batch CSV Upload", size="4", color="#1A202C"),
                                align="center", spacing="2",
                            ),
                            rx.divider(border_color="#CBD5E0"),
                            rx.upload(
                                rx.vstack(
                                    rx.box(rx.text("☁️", size="6"), padding="10px", background="#E2E8F0", border_radius="50%"),
                                    rx.button("Pilih File CSV", style={"background": "#1A202C !important", "color": "#FFFFFF !important", "font-weight": "700"}, size="2"),
                                    rx.text("atau tarik & lepaskan file CSV di sini", size="2", color="#4A5568", font_weight="bold"),
                                    align="center", spacing="2",
                                ),
                                id="upload_csv", border="2px dashed #E50914", padding="2.5rem", border_radius="12px", width="100%", background="#FFF5F5",
                            ),
                            rx.button(
                                "⚡ EXECUTE BATCH UPLOAD", on_click=AppState.handle_upload(rx.upload_files(upload_id="upload_csv")), width="100%", size="3",
                                style={"background": "#1A202C", "color": "#FFFFFF !important", "font-weight": "800", "border-radius": "10px", "cursor": "pointer", "box-shadow": "0 4px 12px rgba(0, 0, 0, 0.15)"}
                            ),
                            spacing="4", width="100%",
                        ),
                        padding="1.8rem", background="#FFFFFF", border_radius="16px", 
                        border="2px solid #CBD5E0", box_shadow="0 10px 25px rgba(0,0,0,0.03)",
                        width="100%",
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
                            rx.text("FILTER EKSPEDISI:", size="2", font_weight="800", color="#111111"),
                            rx.select(
                                AppState.list_ekspedisi_options,
                                value=AppState.filter_ekspedisi,
                                on_change=AppState.set_filter_ekspedisi,
                                width="220px", size="2", color_scheme="gray", variant="classic",
                                style={
                                    "background-color": "#FFFFFF !important", "color": "#000000 !important",
                                    "border": "2.5px solid #1A202C !important", "border-radius": "8px !important",
                                    "font-weight": "800 !important", "box-shadow": "0 2px 5px rgba(0,0,0,0.05)",
                                }
                            ),
                            align="center", spacing="2",
                        ),
                        rx.cond(
                            AppState.selected_ids.length() > 0,
                            rx.button(f"🗑️ HAPUS ({AppState.selected_ids.length()}) DATA", on_click=AppState.open_delete_modal, color_scheme="red", variant="solid", size="2"),
                        ),
                        justify="between", width="100%", margin_top="1.5rem", margin_bottom="0.5rem",
                    ),
                    
                    rx.grid(
                        metric_box("💰 BIAYA ALL", AppState.total_biaya_all, "#C53030", "linear-gradient(135deg, #FED7D7 0%, #FEB2B2 100%)"),
                        metric_box("📦 KOLI ALL", AppState.total_koli_all, "#1A202C", "linear-gradient(135deg, #E2E8F0 0%, #CBD5E0 100%)"),
                        metric_box("📊 AVG COST ALL", AppState.avg_cost_all, "#C53030", "linear-gradient(135deg, #FED7D7 0%, #FEB2B2 100%)"),
                        metric_box("🚚 BIAYA DATANG", AppState.biaya_datang, "#276749", "linear-gradient(135deg, #C6F6D5 0%, #9AE6B4 100%)"),
                        metric_box("📦 KOLI DATANG", AppState.koli_datang, "#276749", "linear-gradient(135deg, #C6F6D5 0%, #9AE6B4 100%)"),
                        metric_box("🔄 BIAYA RTO", AppState.biaya_rto, "#9B2C2C", "linear-gradient(135deg, #FED7D7 0%, #FEB2B2 100%)"),
                        columns=rx.breakpoints(initial="1", sm="3", lg="6"), spacing="4", width="100%",
                    ),
                    
                    rx.box(
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell(rx.text("SELECT", color="#1A202C", font_weight="bold")),
                                    rx.table.column_header_cell(rx.text("TANGGAL", color="#1A202C", font_weight="bold")),
                                    rx.table.column_header_cell(rx.text("SUPPLIER", color="#1A202C", font_weight="bold")),
                                    rx.table.column_header_cell(rx.text("EKSPEDISI", color="#1A202C", font_weight="bold")),
                                    rx.table.column_header_cell(rx.text("KOLI", color="#1A202C", font_weight="bold")),
                                    rx.table.column_header_cell(rx.text("TOTAL ONGKIR", color="#1A202C", font_weight="bold")),
                                ),
                                style={"background-color": "#CBD5E0 !important"}
                            ),
                            rx.table.body(rx.foreach(AppState.filtered_list, render_table_row)),
                            width="100%",
                        ),
                        background="#FFFFFF", border_radius="16px", border="2.5px solid #1A202C", 
                        padding="1rem", width="100%", box_shadow="0 10px 25px rgba(0,0,0,0.04)",
                    ),
                    spacing="4", width="100%",
                ),
                value="tab2",
            ),
            default_value="tab1",
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
                background="#FFFFFF", border="2px solid #CBD5E0", border_radius="16px",
            ),
            open=AppState.show_delete_modal,
        ),
        spacing="5", padding="2rem", width="100%",
        background_color="#F7FAFC", min_height="100vh", on_mount=AppState.load_data,
    )