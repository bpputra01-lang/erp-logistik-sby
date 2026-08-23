import reflex as rx
from .state import AppState
from .components.login import login_page
from .components.dashboard import main_dashboard

def index() -> rx.Component:
    return rx.cond(
        AppState.logged_in,
        main_dashboard(),
        login_page()
    )

app = rx.App(
    theme=rx.theme(appearance="dark", accent_color="gold"),
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