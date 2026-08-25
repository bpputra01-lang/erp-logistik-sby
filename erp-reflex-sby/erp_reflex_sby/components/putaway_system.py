import reflex as rx
from ..state import AppState
from .stock_minus import render_clean_table, success_modal  # Pinjam helper yang sudah rapi

def putaway_view() -> rx.Component:
    return rx.vstack(
        success_modal(), 
        
        # --- HEADER ---
        rx.hstack(
            rx.text("PUTAWAY SYSTEM COMPARATION", font_weight="bold", color="#1A202C", size="5"),
            justify="between", align="center", width="100%", margin_bottom="1rem",
        ),

        # --- SELECTION & UPLOAD SECTION ---
        rx.vstack(
            rx.text("📍 Pilih Area Putaway", font_weight="bold", color="#1A202C", size="3", margin_bottom="0.25rem"),
            rx.select(
                ["DC LANTAI 1", "DC LANTAI 2", "DC LANTAI 3", "JERSEY ZONE"],
                placeholder="-- Pilih Area Putaway --",
                value=AppState.area_putaway,
                on_change=AppState.set_area_putaway,
                size="3", width="100%", margin_bottom="1rem"
            ),
            
            # Form Upload HANYA muncul jika area sudah dipilih
            rx.cond(
                AppState.area_putaway != "",
                rx.vstack(
                    rx.hstack(
                        rx.icon("map-pin", color="#3182ce", size=18),
                        rx.text(f"Area Terpilih: ", font_weight="normal", color="#2c5282", size="2"),
                        rx.text(AppState.area_putaway, font_weight="bold", color="#2c5282", size="2"),
                        background="#ebf8ff", border_left="4px solid #3182ce", padding="10px 16px", border_radius="6px", width="100%", align="center", spacing="2", margin_bottom="1rem"
                    ),
                    
                    rx.hstack(
                        # Upload 1: DS Putaway
                        rx.upload(
                            rx.vstack(rx.icon("upload", size=24, color="#C5A059"), rx.text("Upload DS PUTAWAY", font_weight="bold", color="#4A5568", size="2"), align="center"),
                            id="ds_putaway_file", max_files=1, border="2px dashed black", border_radius="8px", background="#F8FAFC", padding="1.5rem", width="100%", cursor="pointer",
                        ),
                        # Upload 2: ASAL Putaway
                        rx.upload(
                            rx.vstack(rx.icon("upload", size=24, color="#C5A059"), rx.text("Upload ASAL BIN", font_weight="bold", color="#4A5568", size="2"), align="center"),
                            id="asal_putaway_file", max_files=1, border="2px dashed black", border_radius="8px", background="#F8FAFC", padding="1.5rem", width="100%", cursor="pointer",
                        ),
                        spacing="4", width="100%"
                    ),
                    
                    # Indikator File Terpilih & Tombol Proses
                    rx.hstack(
                        rx.hstack(
                            rx.cond(rx.selected_files("ds_putaway_file"), rx.hstack(rx.icon("check-circle", size=14, color="#38A169"), rx.text(rx.selected_files("ds_putaway_file")[0], size="1", color="#22543D", font_weight="bold", truncate=True), background="#F0FFF4", padding="4px 8px", border_radius="4px"), rx.fragment()),
                            rx.cond(rx.selected_files("asal_putaway_file"), rx.hstack(rx.icon("check-circle", size=14, color="#38A169"), rx.text(rx.selected_files("asal_putaway_file")[0], size="1", color="#22543D", font_weight="bold", truncate=True), background="#F0FFF4", padding="4px 8px", border_radius="4px"), rx.fragment()),
                            spacing="2"
                        ),
                        rx.button(
                            rx.hstack(rx.icon("play", size=16), rx.text("COMPARE PUTAWAY"), spacing="2"), 
                            # PERBAIKAN DI SINI: Masukkan kedua ID upload ke dalam 1 list/tuple
                            on_click=AppState.handle_process_putaway(
                                rx.upload_files(["ds_putaway_file", "asal_putaway_file"])
                            ), 
                            background_color="#E50914", color="white", font_weight="bold", 
                            border_radius="6px", padding="0.5rem 1.25rem", cursor="pointer"
                        ),
                        width="100%", justify="between", align="center", margin_top="1rem"
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
                
                # Metrics 4 Kotak
                rx.hstack(
                    rx.box(rx.text("Qty System Putaway", color="#A0AEC0", font_size="11px", font_weight="bold"), rx.text(AppState.putaway_qty_system, color="#E53E3E", font_size="22px", font_weight="bold"), background="#1A1A1A", padding="1rem", border_radius="8px", border_left="4px solid #E53E3E", width="100%", text_align="center"),
                    rx.box(rx.text("Total Tersetup", color="#A0AEC0", font_size="11px", font_weight="bold"), rx.text(AppState.putaway_total_setup, color="#38A169", font_size="22px", font_weight="bold"), background="#1A1A1A", padding="1rem", border_radius="8px", border_left="4px solid #38A169", width="100%", text_align="center"),
                    rx.box(rx.text("Kurang Setup", color="#A0AEC0", font_size="11px", font_weight="bold"), rx.text(AppState.putaway_kurang_setup, color="#DD6B20", font_size="22px", font_weight="bold"), background="#1A1A1A", padding="1rem", border_radius="8px", border_left="4px solid #DD6B20", width="100%", text_align="center"),
                    rx.box(rx.text("Sisa Stok Putaway", color="#A0AEC0", font_size="11px", font_weight="bold"), rx.text(AppState.putaway_sisa_stok, color="#3182CE", font_size="22px", font_weight="bold"), background="#1A1A1A", padding="1rem", border_radius="8px", border_left="4px solid #3182CE", width="100%", text_align="center"),
                    width="100%", spacing="3", margin_bottom="1.25rem",
                ),
                
                # Download Report Button (Global Download for Putaway)
                rx.flex(
                    rx.button(
                        rx.hstack(rx.icon("download", size=16), rx.text("DOWNLOAD REPORT LENGKAP"), spacing="2", align="center"),
                        on_click=AppState.download_putaway_report,
                        background_color="#10B981", color="white", font_weight="bold", border_radius="6px",
                        box_shadow="0 2px 4px rgba(0,0,0,0.1)", cursor="pointer", _hover={"background_color": "#059669"},
                    ), justify="end", width="100%", margin_bottom="0.5rem"
                ),

                # Tabs
                rx.tabs.root(
                    rx.tabs.list(
                        rx.tabs.trigger(rx.text("📋 Hasil Compare", font_weight="bold"), value="t1", color="#1A202C", _selected={"color": "#E50914", "border_bottom": "2px solid #E50914"}),
                        rx.tabs.trigger(rx.text("📝 List Setup", font_weight="bold"), value="t2", color="#1A202C", _selected={"color": "#E50914", "border_bottom": "2px solid #E50914"}),
                        rx.tabs.trigger(rx.text("⚠️ Kurang Setup", font_weight="bold"), value="t3", color="#1A202C", _selected={"color": "#E50914", "border_bottom": "2px solid #E50914"}),
                        rx.tabs.trigger(rx.text("📦 Outstanding", font_weight="bold"), value="t4", color="#1A202C", _selected={"color": "#E50914", "border_bottom": "2px solid #E50914"}),
                    ),
                    rx.tabs.content(render_clean_table(AppState.df_comp_headers, AppState.df_comp_rows), value="t1", padding="0.75rem 0"),
                    rx.tabs.content(render_clean_table(AppState.df_plist_headers, AppState.df_plist_rows), value="t2", padding="0.75rem 0"),
                    rx.tabs.content(
                        rx.cond(AppState.df_kurang_rows.length() > 0, render_clean_table(AppState.df_kurang_headers, AppState.df_kurang_rows), rx.center(rx.text("✅ Semua Tercover!", color="#38A169", font_weight="bold"), background="#C6F6D5", padding="1rem", border_radius="8px")),
                        value="t3", padding="0.75rem 0"
                    ),
                    rx.tabs.content(
                        rx.cond(AppState.df_out_rows.length() > 0, render_clean_table(AppState.df_out_headers, AppState.df_out_rows), rx.center(rx.text("✅ Tidak ada Outstanding!", color="#38A169", font_weight="bold"), background="#C6F6D5", padding="1rem", border_radius="8px")),
                        value="t4", padding="0.75rem 0"
                    ),
                    default_value="t1", width="100%",
                ),
                width="100%", spacing="0",
            ),
        ),
        width="100%", padding="1rem",
    )