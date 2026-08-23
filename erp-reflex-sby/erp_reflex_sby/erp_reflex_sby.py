import reflex as rx
from .state import AppState
from .components.login import login_page
from .components.dashboard import main_dashboard
from .components.sidebar import sidebar

def index() -> rx.Component:
    return rx.cond(
        AppState.logged_in,
        rx.hstack(
            sidebar(),
            rx.vstack(
                rx.match(
                    AppState.main_menu,
                    # Karena role admin bernilai "DC", cek kondisinya dengan "DC"
                    ("Dashboard Overview", rx.cond(AppState.role == "DC", main_dashboard(), rx.text("Akses Ditolak: Khusus Admin DC", color="red", font_size="1.5rem"))),
                    # Jika ada menu lain, tambahkan di bawah sini...
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