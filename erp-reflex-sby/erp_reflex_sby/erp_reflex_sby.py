import reflex as rx
from .state import AppState
from .components.login import login_page
from .components.dashboard import main_dashboard
from .components.sidebar import sidebar

# --- KOMPONEN HEADER GLOBAL (ONLINE & USER INFO) ---
def global_header() -> rx.Component:
    return rx.hstack(
        # --- CSS ANIMASI BLINK UNTUK TITIK ONLINE ---
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
            # --- TITIK HIJAU DENGAN KELAS CSS BERKEDIP (BLINK) ---
            rx.box(
                width="10px", 
                height="10px", 
                background="#10B981", 
                border_radius="50%",
                class_name="blink-online"
            ),
            rx.text("ONLINE", size="2", font_weight="800", color="#065F46"),
            align="center", spacing="2",
        ),
        padding="12px 20px",
        background="#D1FAE5",
        border="1.5px solid #A7F3D0",
        border_radius="16px",
        justify="between", width="100%", align="center",
        margin_bottom="1rem",
    )

def index() -> rx.Component:
    return rx.match(
        AppState.logged_in,
        (
            True,
            rx.hstack(
                sidebar(),
                rx.vstack(
                    # --- HEADER GLOBAL DIPASANG DI SINI AGAR MUNCUL DI SEMUA MENU ---
                    global_header(),

                    rx.match(
                        AppState.main_menu,
                        ("Database Ongkir In/Out", main_dashboard()),
                        ("Database Ongkir", main_dashboard()),
                        ("dashboard_ongkir", main_dashboard()),

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