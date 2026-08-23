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
    is_dc = AppState.role == "DC"
    
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
                    rx.icon("panel-left-close", size=18),
                    on_click=AppState.toggle_sidebar,
                    variant="ghost",
                    color="#CBD5E0",
                    _hover={"color": "#FFFFFF", "background": "rgba(255,255,255,0.1)"},
                ),
                justify="between",
                width="100%",
                margin_bottom="1rem",
                align="center",
            ),
            
            # --- KELOMPOK 1: DASHBOARD SUMMARY (Hanya DC) ---
            rx.cond(
                is_dc,
                rx.vstack(
                    rx.text("MAIN MENU", size="1", weight="bold", color="#A0AEC0", margin_top="5px"),
                    rx.text("DASHBOARD SUMMARY", size="1", weight="bold", color="#A0AEC0", margin_bottom="3px"),
                    menu_item("Dashboard Overview", "Dashboard Overview"),
                    menu_item("Database Master", "Database Master"),
                    width="100%", spacing="1", align_items="start",
                ),
            ),
            
            # --- KELOMPOK 2: OPERATIONAL (DROPDOWN) ---
            rx.vstack(
                section_dropdown_header("OPERATIONAL", "operational", AppState.dropdown_operational),
                rx.cond(
                    AppState.dropdown_operational,
                    rx.cond(
                        is_dc,
                        rx.vstack(
                            menu_item("Purchase Order Receiving", "Purchase Order Receiving"),
                            menu_item("Putaway System", "Putaway System"),
                            menu_item("Scan Out Validation", "Scan Out Validation"),
                            menu_item("Refill & Overstock", "Refill & Overstock"),
                            menu_item("Refill & Withdraw", "Refill & Withdraw"),
                            menu_item("Compare RTO", "Compare RTO"),
                            menu_item("Compare Penerimaan RTO", "Compare Penerimaan RTO"),
                            menu_item("FDR Update", "FDR Update"),
                            width="100%", spacing="1", padding_left="0.5rem",
                        ),
                        rx.vstack(
                            menu_item("Compare Penerimaan RTO", "Compare Penerimaan RTO"),
                            menu_item("Putaway System", "Putaway System"),
                            menu_item("Purchase Order Receiving", "Purchase Order Receiving"),
                            width="100%", spacing="1", padding_left="0.5rem",
                        ),
                    ),
                ),
                width="100%", align_items="start",
            ),

            # --- KELOMPOK 3: INVENTORY (DROPDOWN) ---
            rx.vstack(
                section_dropdown_header("INVENTORY", "inventory", AppState.dropdown_inventory),
                rx.cond(
                    AppState.dropdown_inventory,
                    rx.cond(
                        is_dc,
                        rx.vstack(
                            menu_item("Stock Opname", "Stock Opname"),
                            menu_item("Match Real & System", "Match Real & System"),
                            menu_item("Compare System", "Compare System"),
                            menu_item("Cycle Count", "Cycle Count"),
                            menu_item("Putaway & Picking Audit List", "Putaway & Picking Audit List"),
                            menu_item("List Bin Cycle Count", "List Bin Cycle Count"),
                            menu_item("Stock Tracking Timeline", "Stock Tracking Timeline"),
                            menu_item("Justification SO", "Justification SO"),
                            menu_item("Stock Minus", "Stock Minus"),
                            menu_item("List Retur Out", "List Retur Out"),
                            menu_item("Pengajuan Mutasi Karantina", "Pengajuan Mutasi Karantina"),
                            menu_item("Refill Koli to Koli/Refill", "Refill Koli to Koli/Refill"),
                            menu_item("Stock Allocation", "Stock Allocation"),
                            width="100%", spacing="1", padding_left="0.5rem",
                        ),
                        rx.vstack(
                            menu_item("Stock Minus", "Stock Minus"),
                            menu_item("Cycle Count", "Cycle Count"),
                            menu_item("Compare System", "Compare System"),
                            menu_item("Justification SO", "Justification SO"),
                            width="100%", spacing="1", padding_left="0.5rem",
                        ),
                    ),
                ),
                width="100%", align_items="start",
            ),

            # --- KELOMPOK 4: REJECT & DEFECT (DROPDOWN) ---
            rx.vstack(
                section_dropdown_header("REJECT & DEFECT", "reject", AppState.dropdown_reject),
                rx.cond(
                    AppState.dropdown_reject,
                    rx.vstack(
                        menu_item("Pengajuan Reject/Defect", "Pengajuan Reject/Defect"),
                        menu_item("Reject/Defect List", "Reject/Defect List"),
                        width="100%", spacing="1", padding_left="0.5rem",
                    ),
                ),
                width="100%", align_items="start",
            ),

            # --- KELOMPOK 5: EXTRAS (DROPDOWN) ---
            rx.vstack(
                section_dropdown_header("EXTRAS", "extras", AppState.dropdown_extras),
                rx.cond(
                    AppState.dropdown_extras,
                    rx.cond(
                        is_dc,
                        rx.vstack(
                            menu_item("Logistic Schedule", "Logistic Schedule"),
                            menu_item("Balancing Stock", "Balancing Stock"),
                            menu_item("Reporting & PIC", "Reporting & PIC"),
                            menu_item("Data Timbang Ongkir", "Data Timbang Ongkir"),
                            menu_item("Database Ongkir In/Out", "Database Ongkir In/Out"),
                            menu_item("Precentage Display", "Precentage Display"),
                            menu_item("Precentage Request FL to Store Stock", "Precentage Request FL to Store Stock"),
                            menu_item("Refill Toko", "Refill Toko"),
                            width="100%", spacing="1", padding_left="0.5rem",
                        ),
                        rx.vstack(
                            menu_item("Precentage Display", "Precentage Display"),
                            menu_item("Refill Toko", "Refill Toko"),
                            menu_item("Store Leader RTO Decission", "Store Leader RTO Decission"),
                            width="100%", spacing="1", padding_left="0.5rem",
                        ),
                    ),
                ),
                width="100%", align_items="start",
            ),

            width="280px",
            padding="1rem",
            background="linear-gradient(180deg, #111318 0%, #1A1D24 50%, #0D0F12 100%)",
            border_right="1px solid #2D3748",
            height="100vh",
            overflow_y="auto",
            align_items="start",
            transition="width 0.3s ease",
        ),
        # KONDISI SAAT SIDEBAR DITUTUP (Hanya menampilkan tombol buka)
        rx.vstack(
            rx.button(
                rx.icon("panel-left-open", size=20),
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