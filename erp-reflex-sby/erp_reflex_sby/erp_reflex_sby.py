import reflex as rx
from .state import AppState
from .components.login import login_page
from .components.dashboard import main_dashboard
from .components.sidebar import sidebar
from .components.stock_minus import stock_minus_view

# --- KOMPONEN HEADER GLOBAL (ONLINE & USER INFO) ---
def global_header() -> rx.Component:
    return rx.hstack(
        rx.hstack(
            rx.box(width="10px", height="32px", background="#E50914", border_radius="4px"),
            rx.vstack(
                rx.heading(AppState.main_menu, size="5", color="#111111", font_weight="800"),
                rx.text(f"Logged in as: {AppState.user_display_name} ({AppState.role})", size="2", color="#4A5568"),
                align_items="start", spacing="0",
            ),
            align="center", spacing="3",
        ),
        rx.hstack(
            # Tombol Informasi Format & Logic (Megaphone Icon) - Membuka Global Modal Info
            rx.button(
                rx.icon("megaphone", size=18),
                "Panduan & Logic",
                on_click=AppState.set_is_info_open(True),
                size="2",
                variant="soft",
                color_scheme="orange",
                cursor="pointer",
            ),
            # Titik Hijau Berkedip
            rx.box(
                width="10px", height="10px", background="#10B981", 
                border_radius="50%", class_name="blink-online"
            ),
            rx.text("ONLINE", size="2", font_weight="800", color="#065F46"),
            align="center", spacing="3",
        ),
        padding="12px 20px",
        background="#D1FAE5",
        border="1.5px solid #A7F3D0",
        border_radius="16px",
        justify="between", width="100%", align="center",
        margin_bottom="1rem",
    )


def index() -> rx.Component:
    return rx.vstack(
        # --- CSS ANIMASI BLINK ---
        rx.html("""
            <style>
                @keyframes blinkAnimation {
                    0% { opacity: 1; transform: scale(1); }
                    50% { opacity: 0.3; transform: scale(0.8); }
                    100% { opacity: 1; transform: scale(1); }
                }
                .blink-online {
                    animation: blinkAnimation 1.5s infinite ease-in-out;
                }
            </style>
        """),
        
        # --- GLOBAL LOADING OVERLAY ---
        rx.cond(
            AppState.is_loading,
            rx.center(
                rx.vstack(
                    rx.spinner(size="3", color="red"),
                    rx.text("Sedang memproses data, mohon tunggu...", font_weight="bold", color="#1A202C", size="3"),
                    background="white",
                    padding="2rem",
                    border_radius="12px",
                    box_shadow="lg",
                    align="center",
                    spacing="3",
                ),
                position="fixed",
                top="0",
                left="0",
                width="100vw",
                height="100vh",
                background="rgba(0, 0, 0, 0.5)",
                z_index="9999",
            ),
        ),

        # --- GLOBAL DIALOG PANDUAN & LOGIC (Dikontrol oleh AppState.is_info_open) ---
        rx.dialog.root(
            rx.dialog.content(
                rx.vstack(
                    rx.hstack(
                        rx.icon("book-open", size=20, color="#C5A059"),
                        rx.text("Panduan & Logic ERP Logistik Surabaya", font_weight="bold", color="#1A202C", size="4"),
                        justify="between", width="100%", align="center"
                    ),
                    rx.divider(margin_y="0.5rem"),
                    rx.text("1. Modul Stock Minus: Digunakan untuk mencocokkan Qty System vs Qty Stock Opname (SO) aktual gudang.", color="#4A5568", size="2"),
                    rx.text("2. Template Set Up: Menghasilkan format baris otomatis untuk proses penyesuaian database.", color="#4A5568", size="2"),
                    rx.text("3. Justifikasi: Menyaring item selisih yang memerlukan approval atau investigasi lanjut oleh PIC.", color="#4A5568", size="2"),
                    rx.flex(
                        rx.dialog.close(
                            rx.button("Tutup", background_color="#2D3748", color="white", size="2", font_weight="bold", cursor="pointer", on_click=AppState.set_is_info_open(False))
                        ),
                        justify="end", width="100%", margin_top="1rem"
                    ),
                    spacing="3", align_items="start", width="100%",
                ),
            ),
            open=AppState.is_info_open,
            on_open_change=AppState.set_is_info_open,
        ),

        rx.match(
            AppState.logged_in,
            (
                True,
                rx.hstack(
                    sidebar(),
                    rx.vstack(
                        # --- HEADER GLOBAL ---
                        global_header(),

                        rx.match(
                            AppState.main_menu,
                            ("Database Ongkir In/Out", main_dashboard()),
                            ("Database Ongkir", main_dashboard()),
                            ("dashboard_ongkir", main_dashboard()),
                            ("Stock Minus", stock_minus_view()), 

                            # Handle Error Akses Ditolak
                            (
                                "access_denied",
                                rx.vstack(
                                    rx.heading("⛔ Akses Ditolak", size="7", color="#E53E3E"),
                                    rx.text("Maaf, halaman ini dibatasi hak aksesnya.", color="#718096"),
                                    padding="3rem", align_items="center", justify_content="center",
                                    width="100%", height="70vh",
                                ),
                            ),

                            # Default / Under development untuk menu lain
                            rx.vstack(
                                rx.heading(f"Halaman: {AppState.main_menu}", size="7", color="#1A202C"),
                                rx.text("Halaman ini sedang dalam tahap pengembangan.", color="#718096"),
                                padding="3rem", align_items="center", justify_content="center",
                                width="100%", height="70vh",
                            ),
                        ),
                        width="100%",
                        height="100vh",
                        background_color="#F7FAFC",
                        overflow_y="auto",
                        padding="1.5rem",
                    ),
                    width="100vw",
                    height="100vh",
                    spacing="0",
                    overflow="hidden",
                ),
            ),
            (
                False,
                login_page(),
            ),
        ),
        width="100vw",
        height="100vh",
        spacing="0",
    )


app = rx.App(
    theme=rx.theme(appearance="light", accent_color="red"),
    style={
        "[data-sonner-toaster]": {
            "top": "20px !important",
            "right": "20px !important",
            "bottom": "auto !important",
            "left": "auto !important",
        }
    }
)
app.add_page(index, route="/", title="ZKN ERP - Logistik Surabaya")