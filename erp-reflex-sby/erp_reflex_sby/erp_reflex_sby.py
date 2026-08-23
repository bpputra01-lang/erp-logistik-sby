import reflex as rx
from .state import AppState
from .components.login import login_page
from .components.dashboard import main_dashboard
from .components.sidebar import sidebar

def google_sheets_viewer() -> rx.Component:
    """Komponen Google Sheets Viewer untuk Dashboard Overview."""
    
    return rx.vstack(
        rx.hstack(
            rx.vstack(
                rx.text("PILIH LAPORAN", size="2", weight="bold", color="#4A5568"),
                rx.select(
                    ["WORKING REPORT", "PERSONAL PERFORMANCE", "CYCLE COUNT DAN KERAPIHAN", "DASHBOARD MOVING STOCK"],
                    value=AppState.pilih_laporan,
                    on_change=AppState.set_pilih_laporan,
                    width="300px",
                ),
                spacing="1",
            ),
            rx.vstack(
                rx.text(
                    AppState.zoom_val.to(lambda val: f"ZOOM: {val:.2f}"), 
                    size="2", 
                    weight="bold", 
                    color="#4A5568"
                ),
                rx.slider(
                    default_value=[0.5],
                    min=0.3,
                    max=1.2,
                    step=0.05,
                    on_change=AppState.set_zoom_val,
                    width="200px",
                ),
                spacing="1",
            ),
            spacing="5",
            align_items="end",
            margin_bottom="10px",
        ),
        # Mengembalikan struktur iframe stabil yang langsung muncul
        rx.box(
            rx.html(
                f"""
                <div style="background: white; border-radius: 15px; padding: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); width: 100%; height: 75vh; overflow: auto;">
                    <iframe src="https://docs.google.com/spreadsheets/d/e/2PACX-1vRIMd-eghecjZKcOmhz0TW4f-1cG0LOWgD6X9mIK1XhiYSOx-V6xSnZQzBLfru0LhCIinIZAfbYnHv_/pubhtml?gid=864743695&single=true&rm=minimal" 
                        style="width: 100%; height: 100%; border: none;">
                    </iframe>
                </div>
                """
            ),
            width="100%",
        ),
        width="100%", spacing="4", padding="2rem",
    )

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
                        AppState.main_menu,
                        # 1. Menu Dashboard Overview (Menampilkan Google Sheets Viewer secara mandiri)
                        ("Dashboard Overview", google_sheets_viewer()),
                        
                        # 2. Menu Database Ongkir In/Out (Hanya menampilkan form input & history)
                        ("Database Ongkir In/Out", main_dashboard()),
                        ("Database Ongkir", main_dashboard()),
                        ("dashboard_ongkir", main_dashboard()),
                        
                        # 3. Handle Error Akses Ditolak
                        (
                            "access_denied",
                            rx.vstack(
                                rx.heading("⛔ Akses Ditolak", size="7", color="#E53E3E"),
                                rx.text("Maaf, halaman Database Ongkir ini khusus untuk Admin DC (Surabaya).", color="#718096"),
                                padding="3rem",
                                align_items="center",
                                justify_content="center",
                                width="100%",
                                height="80vh",
                            ),
                        ),
                        
                        # 4. Default / Under development untuk menu lain
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
app.add_page(index, route="/", title="ZKN ERP - Logistik Surabaya")