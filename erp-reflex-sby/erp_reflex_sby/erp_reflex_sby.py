import reflex as rx
from .state import AppState
from .components.login import login_page
from .components.sidebar import sidebar

def index() -> rx.Component:
    return rx.cond(
        AppState.logged_in,
        rx.hstack(
            sidebar(),
            rx.vstack(
                AppState.dynamic_content,
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
app.add_page(index, route="/", title="ZKN ERP - Database Ongkir")