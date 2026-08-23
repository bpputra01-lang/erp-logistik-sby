import reflex as rx
from .state import AppState
from .components.login import login_page
from .components.dashboard import main_dashboard
from .components.sidebar import sidebar  # 1. Jangan lupa import sidebar-nya di sini

def index() -> rx.Component:
    return rx.cond(
        AppState.logged_in,
        # 2. Bungkus dengan hstack agar sidebar ada di kiri dan dashboard di kanan
        rx.hstack(
            sidebar(),
            rx.vstack(
                rx.match(
                    AppState.main_menu,
                    ("Database Ongkir In/Out", main_dashboard()),
                    # Jika menu lain dipilih dan belum ada halamannya, tampilkan placeholder ini:
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
app.add_page(
    index, 
    route="/", 
    title="ZKN ERP - Database Ongkir", 
    image_path="/favicon.png"  # Sesuaikan dengan nama file gambar Anda di folder assets
)