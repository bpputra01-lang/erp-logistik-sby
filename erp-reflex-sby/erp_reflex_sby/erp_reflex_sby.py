import reflex as rx
from .state import AppState
from .components.login import login_page
from .components.dashboard import main_dashboard
from .components.sidebar import sidebar

def index() -> rx.Component:
    # Menggunakan rx.match untuk menghindari sama sekali error rx.cond
    return rx.match(
        AppState.logged_in,
        (
            True,
            rx.hstack(
                sidebar(),
                rx.vstack(
                    rx.match(
                        AppState.main_menu,  # <-- Diubah dari AppState.active_content_type ke AppState.main_menu
                        ("Dashboard Overview", main_dashboard()),
                        ("dashboard_ongkir", main_dashboard()),
                        (
                            "access_denied",
                            rx.vstack(
                                rx.heading("⛔ Akses Ditolak", size="7", color="#E53E3E"),
                                rx.text("Maaf, halaman Dashboard Ongkir ini khusus untuk Admin DC (Surabaya).", color="#718096"),
                                padding="3rem",
                                align_items="center",
                                justify_content="center",
                                width="100%",
                                height="80vh",
                            ),
                        ),
                        # Default / Under development
                        rx.vstack(
                            rx.heading(f"Halaman: {AppState.main_menu}", size="7", color="#1A202C"),
                            rx.text("Halaman ini sedang dalam tahap pengembangan.", color="#718096"),
                            padding="3rem",
                            align_items="center",
                            justify_content="center",
                            width="100%",
                            height="80vh",
                        ),
                    ),
                    width="100%",
                    height="100vh",
                    background_color="#F7FAFC",
                    overflow_y="auto",
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
app.add_page(index, route="/", title="ZKN ERP - Database Ongkir")