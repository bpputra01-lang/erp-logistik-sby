import reflex as rx
from .state import AppState
from .components.login import login_page
from .components.dashboard import main_dashboard
from .components.sidebar import sidebar
from .components.stock_minus import stock_minus_view

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
            # Tombol Panduan & Logic menjadi warna hitam (gray)
            rx.button(
                rx.icon("megaphone", size=18, color="#1A202C"),
                "Panduan & Logic",
                on_click=AppState.set_is_info_open(True),
                size="2",
                variant="soft",
                color_scheme="gray", 
                color="#1A202C",     
                cursor="pointer",
            ),
            rx.box(width="10px", height="10px", background="#10B981", border_radius="50%", class_name="blink-online"),
            rx.text("ONLINE", size="2", font_weight="800", color="#065F46"),
            align="center", spacing="3",
        ),
        padding="12px 20px", background="#D1FAE5", border="1.5px solid #A7F3D0", border_radius="16px", justify="between", width="100%", align="center", margin_bottom="1rem",
    )

def index() -> rx.Component:
    return rx.vstack(
        rx.html("""
            <style>
                @keyframes blinkAnimation {
                    0% { opacity: 1; transform: scale(1); }
                    50% { opacity: 0.3; transform: scale(0.8); }
                    100% { opacity: 1; transform: scale(1); }
                }
                .blink-online { animation: blinkAnimation 1.5s infinite ease-in-out; }
            </style>
        """),
        
        rx.cond(
            AppState.is_loading,
            rx.center(
                rx.vstack(
                    rx.spinner(size="3", color="red"),
                    rx.text("Sedang memproses data, mohon tunggu...", font_weight="bold", color="#1A202C", size="3"),
                    background="white", padding="2rem", border_radius="12px", box_shadow="lg", align="center", spacing="3",
                ),
                position="fixed", top="0", left="0", width="100vw", height="100vh", background="rgba(0, 0, 0, 0.5)", z_index="9999",
            ),
        ),

        # --- GLOBAL DIALOG PANDUAN & LOGIC ---
        rx.dialog.root(
            rx.dialog.content(
                rx.vstack(
                    rx.hstack(
                        rx.icon("book-open", size=20, color="#C5A059"),
                        rx.text("Panduan & Logic ERP Logistik", font_weight="bold", color="#1A202C", size="4"),
                        justify="between", width="100%", align="center"
                    ),
                    rx.divider(margin_y="0.5rem"),
                    
                    rx.accordion.root(
                        rx.accordion.item(
                            header=rx.text("📋 Informasi Format File", font_weight="bold", color="#1A202C"),
                            content=rx.box(
                                rx.text("Format yang diharapkan:", font_weight="bold", margin_bottom="6px", size="2", color="#1A202C"),
                                rx.unordered_list(
                                    rx.list_item(rx.text("Download Multiple Adjusmet dari Jezpro dan pilih ", rx.text.strong("Termasuk yang sudah habis"))),
                                    padding_left="20px", size="2", color="#4A5568"
                                ),
                                background="#F7FAFC", padding="16px", border_radius="6px"
                            ),
                            value="item-1",
                        ),
                        rx.accordion.item(
                            header=rx.text("💡 Logic Thinking", font_weight="bold", color="#1A202C"),
                            content=rx.box(
                                rx.text("Alur Process Compare Stock Minus:", font_weight="bold", margin_bottom="6px", size="2", color="#1A202C"),
                                rx.unordered_list(
                                    rx.list_item("Mengambil SKU yang memiliki Qty System minus (-)"),
                                    rx.list_item("Lalu SKU yang memiliki QTY Minus (-) tersebut akan di lakukan shuffle covering Stock"),
                                    rx.list_item("Dimana terdapat Bin prioritas untuk shuffle Covering Stock (All Stagging, Karantina)"),
                                    rx.list_item("Dan jika minus terjadi di Gudang lt.2 maka akan prioritas mengambil BIN Toko begitupun sebaliknya"),
                                    rx.list_item("Lalu jika tidak ditemukan di BIN Prioritas maka akan mengambil random BIN kecuali LIVE, Offline dan Online"),
                                    rx.list_item("Jika sudah ditemukan SKU dan Qty yang bisa covering maka akan dibuatkan list Set up"),
                                    rx.list_item("Dan jika tidak bisa diselesaikan lewat set up maka sistem akan memasukkan kedalam item need justifikasi dan perlu analisa lebih lanjut"),
                                    padding_left="20px", size="2", color="#4A5568", spacing="2"
                                ),
                                background="#F7FAFC", padding="16px", border_radius="6px"
                            ),
                            value="item-2",
                        ),
                        type="multiple", collapsible=True, width="100%", 
                        variant="ghost",      
                        color_scheme="gray",  
                    ),

                    rx.flex(
                        rx.dialog.close(
                            rx.button("Tutup", background_color="#2D3748", color="white", size="2", font_weight="bold", cursor="pointer", _hover={"background_color": "#1A202C"}, on_click=AppState.set_is_info_open(False))
                        ),
                        justify="end", width="100%", margin_top="1rem"
                    ),
                    spacing="3", align_items="start", width="100%",
                ),
                background_color="white", padding="24px", border_radius="12px", box_shadow="0 10px 25px rgba(0,0,0,0.2)", max_width="650px",
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
                        global_header(),
                        rx.match(
                            AppState.main_menu,
                            ("Database Ongkir In/Out", main_dashboard()),
                            ("Database Ongkir", main_dashboard()),
                            ("dashboard_ongkir", main_dashboard()),
                            ("Stock Minus", stock_minus_view()), 
                            (
                                "access_denied",
                                rx.vstack(
                                    rx.heading("⛔ Akses Ditolak", size="7", color="#E53E3E"),
                                    rx.text("Maaf, halaman ini dibatasi hak aksesnya.", color="#718096"),
                                    padding="3rem", align_items="center", justify_content="center", width="100%", height="70vh",
                                ),
                            ),
                            rx.vstack(
                                rx.heading(f"Halaman: {AppState.main_menu}", size="7", color="#1A202C"),
                                rx.text("Halaman ini sedang dalam tahap pengembangan.", color="#718096"),
                                padding="3rem", align_items="center", justify_content="center", width="100%", height="70vh",
                            ),
                        ),
                        width="100%", height="100vh", background_color="#F7FAFC", overflow_y="auto", padding="1.5rem",
                    ),
                    width="100vw", height="100vh", spacing="0", overflow="hidden",
                ),
            ),
            (False, login_page()),
        ),
        width="100vw", height="100vh", spacing="0",
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