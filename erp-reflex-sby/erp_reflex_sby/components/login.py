import reflex as rx
from ..state import AppState

def login_page() -> rx.Component:
    return rx.flex(
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.box(width="12px", height="38px", background="#E50914", border_radius="4px"),
                    rx.vstack(
                        rx.heading("LOGISTIC DISTRIBUTION", size="6", color="#FFFFFF", font_weight="800", letter_spacing="1px"),
                        rx.text("CENTER WAREHOUSE • SURABAYA", size="1", color="#E50914", font_weight="700", letter_spacing="2px"),
                        spacing="0",
                    ),
                    align="center", spacing="3",
                ),
                rx.divider(border_color="rgba(255, 255, 255, 0.1)"),
                rx.text("Silakan masuk dengan akun resmi gudang Anda.", size="2", color="#B0B0B0"),

                rx.vstack(
                    rx.text("USERNAME", size="1", font_weight="700", color="#FFFFFF", letter_spacing="1px"),
                    rx.input(
                        placeholder="Masukkan username...",
                        value=AppState.username,
                        on_change=AppState.set_username,
                        on_key_down=AppState.handle_key_down,
                        size="3", variant="surface", color_scheme="red", width="100%",
                        style={
                            "background": "rgba(0, 0, 0, 0.75)", 
                            "border": "1px solid rgba(229, 9, 20, 0.4)", 
                            "color": "#FFFFFF", "border-radius": "10px", "padding": "0.8rem 1rem",
                        },
                    ),
                    spacing="1", width="100%",
                ),

                rx.vstack(
                    rx.text("PASSWORD", size="1", font_weight="700", color="#FFFFFF", letter_spacing="1px"),
                    rx.input(
                        type="password",
                        placeholder="Masukkan password...",
                        value=AppState.password,
                        on_change=AppState.set_password,
                        on_key_down=AppState.handle_key_down,
                        size="3", variant="surface", color_scheme="gray", width="100%",
                        style={
                            "background": "rgba(0, 0, 0, 0.75)", 
                            "border": "1px solid rgba(229, 9, 20, 0.4)", 
                            "color": "#FFFFFF", "border-radius": "10px", "padding": "0.8rem 1rem",
                        },
                    ),
                    spacing="1", width="100%",
                ),

                rx.box(height="10px"),

                rx.button(
                    "SIGN IN TO SYSTEM →",
                    on_click=AppState.handle_login,
                    size="3", width="100%",
                    style={
                        "background": "linear-gradient(135deg, #E50914 0%, #B20710 100%)", 
                        "color": "#FFFFFF", "font-weight": "800", "border-radius": "10px", 
                        "cursor": "pointer", "box-shadow": "0 4px 15px rgba(229, 9, 20, 0.4)", "height": "48px",
                    },
                ),

                rx.center(
                    rx.text("🟢 Warehouse Supporting Tools v2.0", size="1", color="#888888"),
                    margin_top="10px",
                ),
                spacing="5", align="stretch", width="100%",
            ),
            width="100%", max_width="520px", padding="3rem 2.5rem",
            background="rgba(12, 12, 15, 0.88)", backdrop_filter="blur(20px)",
            border_radius="20px", border="1px solid rgba(255, 255, 255, 0.12)",
            border_left="5px solid #E50914", box_shadow="0 25px 60px rgba(0, 0, 0, 0.85)",
        ),
        background_image="radial-gradient(circle at center, rgba(0, 0, 0, 0.15) 0%, rgba(0, 0, 0, 0.45) 100%), url('https://images.unsplash.com/photo-1553413077-190dd305871c?q=80&w=2070')",
        background_size="cover", background_position="center", background_repeat="no-repeat",
        width="100vw", height="100vh", align="center", justify="center", padding="2rem",
    )