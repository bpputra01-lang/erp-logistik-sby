import reflex as rx
from ..state import AppState

def menu_item(label: str, target_menu: str) -> rx.Component:
    is_active = AppState.main_menu == target_menu
    
    return rx.button(
        label,
        on_click=lambda: AppState.set_main_menu(target_menu),
        width="100%",
        justify="start",
        variant="solid",
        style={
            "background": rx.cond(
                is_active, 
                "linear-gradient(135deg, #E50914 0%, #B20710 100%)", 
                "transparent"
            ),
            "color": rx.cond(is_active, "#FFFFFF", "#CBD5E0"),
            "font-weight": rx.cond(is_active, "700", "500"),
            "padding": "0.5rem 0.75rem",
            "margin-bottom": "3px",
            "border-radius": "6px",
            "text-align": "left",
            "justify-content": "flex-start",
            "font-size": "0.85rem",
            "box-shadow": rx.cond(is_active, "0 4px 12px rgba(229, 9, 20, 0.4)", "none"),
            "_hover": {
                "background": rx.cond(
                    is_active, 
                    "linear-gradient(135deg, #E50914 0%, #B20710 100%)", 
                    "rgba(255, 255, 255, 0.08)"
                ),
                "color": "#FFFFFF",
            }
        }
    )

def section_dropdown_header(title: str, dropdown_key: str, is_open: bool) -> rx.Component:
    return rx.hstack(
        rx.text(title, size="1", weight="bold", color="#FFFFFF", letter_spacing="0.05em"),
        rx.icon(
            tag=rx.cond(is_open, "chevron-down", "chevron-right"),
            size=16,
            color="#FFFFFF",
        ),
        justify="between",
        width="100%",
        padding="0.5rem 0.6rem",
        border_radius="6px",
        cursor="pointer",
        background="rgba(255, 255, 255, 0.05)",
        margin_top="0.8rem",
        margin_bottom="0.3rem",
        on_click=lambda: AppState.toggle_dropdown(dropdown_key),
        _hover={"background": "rgba(255, 255, 255, 0.1)"}
    )

def sidebar() -> rx.Component:
    return rx.cond(
        AppState.sidebar_open,
        # KONDISI SAAT SIDEBAR TERBUKA
        rx.vstack(
            # --- HEADER & TOMBOL CLOSE SIDEBAR ---
            rx.hstack(
                rx.hstack(
                    rx.heading("JEZ", color="#E50914", font_weight="900", size="5"),
                    rx.heading("PRO", color="#FFFFFF", font_weight="900", size="5"),
                    spacing="1",
                ),
                rx.button(
                    rx.icon("panel_left_close", size=18),
                    on_click=AppState.toggle_sidebar,
                    variant="ghost",
                    color="#CBD5E0",
                    _hover={"color": "#FFFFFF", "background": "rgba(255,255,255,0.1)"},
                ),
                justify="between",
                width="100%",
                margin_bottom="0.5rem",
                align="center",
            ),
            
            # Area Menu yang bisa di-scroll
            rx.vstack(
                # --- KELOMPOK 1: OPERATIONAL ---
                rx.vstack(
                    section_dropdown_header("OPERATIONAL", "operational", AppState.dropdown_operational),
                    rx.cond(
                        AppState.dropdown_operational,
                        rx.vstack(
                            rx.foreach(
                                AppState.menu_operational,
                                lambda item: menu_item(item, item)
                            ),
                            width="100%", spacing="1", padding_left="0.5rem",
                        ),
                        rx.fragment()
                    ),
                    width="100%", align_items="start",
                ),

                # --- KELOMPOK 2: INVENTORY ---
                rx.vstack(
                    section_dropdown_header("INVENTORY", "inventory", AppState.dropdown_inventory),
                    rx.cond(
                        AppState.dropdown_inventory,
                        rx.vstack(
                            rx.foreach(
                                AppState.menu_inventory,
                                lambda item: menu_item(item, item)
                            ),
                            width="100%", spacing="1", padding_left="0.5rem",
                        ),
                        rx.fragment()
                    ),
                    width="100%", align_items="start",
                ),

                # --- KELOMPOK 3: REJECT & DEFECT ---
                rx.vstack(
                    section_dropdown_header("REJECT & DEFECT", "reject", AppState.dropdown_reject),
                    rx.cond(
                        AppState.dropdown_reject,
                        rx.vstack(
                            rx.foreach(
                                AppState.menu_reject,
                                lambda item: menu_item(item, item)
                            ),
                            width="100%", spacing="1", padding_left="0.5rem",
                        ),
                        rx.fragment()
                    ),
                    width="100%", align_items="start",
                ),

                # --- KELOMPOK 4: EXTRAS ---
                rx.vstack(
                    section_dropdown_header("EXTRAS", "extras", AppState.dropdown_extras),
                    rx.cond(
                        AppState.dropdown_extras,
                        rx.vstack(
                            rx.foreach(
                                AppState.menu_extras,
                                lambda item: menu_item(item, item)
                            ),
                            width="100%", spacing="1", padding_left="0.5rem",
                        ),
                        rx.fragment()
                    ),
                    width="100%", align_items="start",
                ),
                
                width="100%",
                flex="1",
                overflow_y="auto",
                spacing="2",
            ),

            # --- TOMBOL LOGOUT ---
            rx.box(
                rx.button(
                    rx.hstack(
                        rx.icon("log-out", size=16),
                        rx.text("Logout Sistem", size="2", weight="bold"),
                        spacing="2",
                        align="center",
                    ),
                    on_click=AppState.logout,
                    width="100%",
                    color="#FFFFFF",
                    background="linear-gradient(135deg, #E50914 0%, #B20710 100%)",
                    padding="0.5rem",
                    border_radius="6px",
                    cursor="pointer",
                    _hover={"background": "linear-gradient(135deg, #FF1924 0%, #C20710 100%)"},
                ),
                width="100%",
                padding_top="0.8rem",
                border_top="1px solid rgba(255, 255, 255, 0.1)",
                margin_top="auto",
            ),

            width="280px",
            padding="1rem",
            background="linear-gradient(180deg, #111318 0%, #1A1D24 50%, #0D0F12 100%)",
            border_right="1px solid #2D3748",
            height="100vh",
            align_items="start",
            transition="width 0.3s ease",
        ),
        # KONDISI SAAT SIDEBAR DITUTUP
        rx.vstack(
            rx.button(
                rx.icon("panel_left_open", size=20),
                on_click=AppState.toggle_sidebar,
                variant="ghost",
                color="#FFFFFF",
                padding="0.5rem",
                _hover={"background": "rgba(255,255,255,0.1)"},
            ),
            width="60px",
            padding="1rem 0.5rem",
            background="#111318",
            border_right="1px solid #2D3748",
            height="100vh",
            align_items="center",
        ),
    )