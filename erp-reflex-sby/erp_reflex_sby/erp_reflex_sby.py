import reflex as rx
from .state import AppState
from .components.login import login_page
from .components.dashboard import main_dashboard
from .components.sidebar import sidebar  # 1. Jangan lupa import sidebar-nya di sini

def index() -> rx.Component:
    return rx.cond(
        AppState.logged_in,
        rx.hstack(
            sidebar(), # Sidebar otomatis menyembunyikan menu dashboard jika bukan admin
            rx.vstack(
                rx.match(
                    AppState.main_menu,
                    # Validasi ganda: Pastikan hanya admin yang bisa membuka halaman ini
                    ("Dashboard Overview", rx.cond(AppState.role == "admin", main_dashboard(), rx.text("Akses Ditolak: Khusus Admin", color="red", font_size="1.5rem"))),
                    # Menu lainnya...
                ),
                width="100%",
                height="100vh",
                background_color="#F7FAFC",
                overflow_y="auto",
            ),
            width="100vw",
            height="100vh",
            spacing="0",
        ),
        login_page()
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