import reflex as rx
from ..state import AppState
from .stock_minus import render_clean_table, success_modal

# Komponen Uploader yang lebih gemuk dan proporsional
def custom_uploader_box(id_str: str, title: str) -> rx.Component:
    return rx.vstack(
        rx.text(title, font_weight="bold", color="#1A202C", size="3", margin_bottom="0.25rem"),
        rx.upload(
            rx.hstack(
                rx.button(
                    rx.hstack(rx.icon("upload", size=16), rx.text("Upload", font_weight="bold")),
                    background_color="#C5A059", color="white", pointer_events="none", border_radius="6px"
                ),
                rx.cond(
                    rx.selected_files(id_str),
                    rx.hstack(
                        rx.icon("check-circle", color="#38A169", size=20),
                        rx.foreach(rx.selected_files(id_str), lambda f: rx.text(f, color="#38A169", font_weight="bold", truncate=True)),
                        spacing="2", align="center"
                    ),
                    rx.text("200MB per file • XLSX, XLS, CSV", color="#718096", size="2")
                ),
                spacing="4", align="center", width="100%"
            ),
            id=id_str, max_files=1, 
            border="2px dashed #CBD5E0", border_radius="8px", 
            padding="2rem 1.5rem", min_height="100px",  # Box dibuat lebih gemuk
            width="100%", cursor="pointer", _hover={"border_color": "#C5A059", "background_color": "#F8FAFC"}
        ),
        width="100%", spacing="0"
    )

def putaway_view() -> rx.Component:
    return rx.vstack(
        success_modal(), 
        
        rx.hstack(
            rx.text("PUTAWAY SYSTEM COMPARATION", font_weight="bold", color="#1A202C", size="5"),
            justify="between", align="center", width="100%", margin_bottom="1rem",
        ),

        rx.vstack(
            rx.text("📍 Pilih Area Putaway", font_weight="bold", color="#1A202C", size="3", margin_bottom="0.25rem"),
            
            # 🔥 Menggunakan Low-Level Select API agar styling hitam bold-nya benar-benar tembus
            rx.select.root(
                rx.select.trigger(
                    placeholder="-- Pilih Area Putaway --",
                    style={
                        "background-color": "white",
                        "color": "black !important",
                        "font-weight": "bold !important",
                        "border": "1px solid #CBD5E0",
                        "width": "100%",
                        "height": "40px",
                    }
                ),
                rx.select.content(
                    rx.select.item("DC LANTAI 1", value="DC LANTAI 1"),
                    rx.select.item("DC LANTAI 2", value="DC LANTAI 2"),
                    rx.select.item("DC LANTAI 3", value="DC LANTAI 3"),
                    rx.select.item("JERSEY ZONE", value="JERSEY ZONE"),
                    style={"background-color": "white", "color": "black", "font-weight": "bold"}
                ),
                value=AppState.area_putaway,
                on_change=AppState.set_area_putaway,
            ),
            
            
            rx.cond(
                AppState.area_putaway != "",
                rx.vstack(
                    rx.hstack(
                        rx.icon("map-pin", color="#3182ce", size=18),
                        rx.text("Area Terpilih: ", font_weight="normal", color="#2c5282", size="2"),
                        rx.text(AppState.area_putaway, font_weight="bold", color="#2c5282", size="2"),
                        background="#ebf8ff", border_left="4px solid #3182ce", padding="10px 16px", border_radius="6px", width="100%", align="center", spacing="2", margin_bottom="1rem"
                    ),
                    
                    rx.hstack(
                        custom_uploader_box("ds_putaway_file", "Upload DS PUTAWAY"),
                        custom_uploader_box("asal_putaway_file", "Upload ASAL BIN"),
                        spacing="4", width="100%", margin_bottom="1.5rem"
                    ),
                    
                    # PERBAIKAN 2: Tombol rata kanan, warna tetap merah tapi transparan saat locked
                    rx.flex(
                        rx.cond(
                            rx.selected_files("ds_putaway_file") & rx.selected_files("asal_putaway_file"),
                            rx.button(
                                rx.hstack(rx.icon("play", size=16), rx.text("COMPARE PUTAWAY"), spacing="2"), 
                                on_click=[
                                    AppState.start_loading,
                                    AppState.handle_upload_ds(rx.upload_files("ds_putaway_file")),
                                    AppState.handle_upload_asal(rx.upload_files("asal_putaway_file"))
                                ], 
                                background_color="#E50914", color="white", font_weight="bold", 
                                border_radius="6px", padding="0.75rem 1.5rem", cursor="pointer"
                            ),
                            rx.button(
                                rx.hstack(rx.icon("lock", size=16), rx.text("PILIH KEDUA FILE UNTUK MEMULAI"), spacing="2"), 
                                disabled=True,
                                background_color="#E50914", opacity="0.5", color="white", font_weight="bold", 
                                border_radius="6px", padding="0.75rem 1.5rem", cursor="not-allowed"
                            )
                        ),
                        width="100%", justify="end" # Rata Kanan
                    ),
                    width="100%",
                ),
                rx.center(rx.text("⚠️ Silakan pilih Area Putaway di atas terlebih dahulu.", color="#DD6B20", font_weight="bold", font_style="italic"), background="#FFFFF0", border="1px solid #F6E05E", padding="1rem", border_radius="8px", width="100%")
            ),
            width="100%", background="white", padding="1.25rem", border_radius="10px", border="1px solid #E2E8F0", margin_bottom="1.25rem", align_items="start",
        ),

        # --- DASHBOARD METRICS & TABS ---
        rx.cond(
            AppState.putaway_processed,
            rx.vstack(
                rx.divider(),
                rx.heading("📋 RINGKASAN HASIL", size="4", color="#010B13", margin_y="1rem"),
                rx.hstack(
                    rx.box(rx.text("Qty System Putaway", color="#A0AEC0", font_size="11px", font_weight="bold"), rx.text(AppState.putaway_qty_system, color="#E53E3E", font_size="22px", font_weight="bold"), background="#1A1A1A", padding="1rem", border_radius="8px", border_left="4px solid #E53E3E", width="100%", text_align="center"),
                    rx.box(rx.text("Total Tersetup", color="#A0AEC0", font_size="11px", font_weight="bold"), rx.text(AppState.putaway_total_setup, color="#38A169", font_size="22px", font_weight="bold"), background="#1A1A1A", padding="1rem", border_radius="8px", border_left="4px solid #38A169", width="100%", text_align="center"),
                    rx.box(rx.text("Kurang Setup", color="#A0AEC0", font_size="11px", font_weight="bold"), rx.text(AppState.putaway_kurang_setup, color="#DD6B20", font_size="22px", font_weight="bold"), background="#1A1A1A", padding="1rem", border_radius="8px", border_left="4px solid #DD6B20", width="100%", text_align="center"),
                    rx.box(rx.text("Sisa Stok Putaway", color="#A0AEC0", font_size="11px", font_weight="bold"), rx.text(AppState.putaway_sisa_stok, color="#3182CE", font_size="22px", font_weight="bold"), background="#1A1A1A", padding="1rem", border_radius="8px", border_left="4px solid #3182CE", width="100%", text_align="center"),
                    width="100%", spacing="3", margin_bottom="1.25rem",
                ),
                rx.flex(
                    rx.button(
                        rx.hstack(rx.icon("download", size=16), rx.text("DOWNLOAD REPORT LENGKAP"), spacing="2", align="center"),
                        on_click=AppState.download_putaway_report,
                        background_color="#10B981", color="white", font_weight="bold", border_radius="6px",
                        box_shadow="0 2px 4px rgba(0,0,0,0.1)", cursor="pointer", _hover={"background_color": "#059669"},
                    ), justify="end", width="100%", margin_bottom="0.5rem"
                ),
                rx.tabs.root(
                    rx.tabs.list(
                        rx.tabs.trigger(rx.text("📋 Hasil Compare", font_weight="bold"), value="t1", color="#1A202C", _selected={"color": "#E50914", "border_bottom": "2px solid #E50914"}),
                        rx.tabs.trigger(rx.text("📝 List Setup", font_weight="bold"), value="t2", color="#1A202C", _selected={"color": "#E50914", "border_bottom": "2px solid #E50914"}),
                        rx.tabs.trigger(rx.text("⚠️ Kurang Setup", font_weight="bold"), value="t3", color="#1A202C", _selected={"color": "#E50914", "border_bottom": "2px solid #E50914"}),
                        rx.tabs.trigger(rx.text("📦 Outstanding", font_weight="bold"), value="t4", color="#1A202C", _selected={"color": "#E50914", "border_bottom": "2px solid #E50914"}),
                    ),
                    rx.tabs.content(render_clean_table(AppState.df_comp_headers, AppState.df_comp_rows), value="t1", padding="0.75rem 0"),
                    rx.tabs.content(render_clean_table(AppState.df_plist_headers, AppState.df_plist_rows), value="t2", padding="0.75rem 0"),
                    rx.tabs.content(rx.cond(AppState.df_kurang_rows.bool(), render_clean_table(AppState.df_kurang_headers, AppState.df_kurang_rows), rx.center(rx.text("✅ Semua Tercover!", color="#38A169", font_weight="bold"), background="#C6F6D5", padding="1rem", border_radius="8px")), value="t3", padding="0.75rem 0"),
                    rx.tabs.content(rx.cond(AppState.df_out_rows.bool(), render_clean_table(AppState.df_out_headers, AppState.df_out_rows), rx.center(rx.text("✅ Tidak ada Outstanding!", color="#38A169", font_weight="bold"), background="#C6F6D5", padding="1rem", border_radius="8px")), value="t4", padding="0.75rem 0"),
                    default_value="t1", width="100%",
                ),
                width="100%", spacing="0",
            ),
        ),
        width="100%", padding="1rem",
    )