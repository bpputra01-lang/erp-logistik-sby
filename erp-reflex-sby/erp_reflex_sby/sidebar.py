import reflex as rx
from ..state import AppState

def menu_item(label: str, target_menu: str) -> rx.Component:
    is_active = AppState.main_menu == target_menu
    return rx.button(
        label,
        on_click=lambda: AppState.set_main_menu(target_menu),
        width="100%",
        justify="start",
        variant="soft" if is_active else "ghost",
        color_scheme="red" if is_active else "gray",
        style={
            "font-weight": "700" if is_active else "500",
            "padding": "0.5rem 0.75rem",
            "margin-bottom": "2px",
            "border-radius": "8px",
            "text-align": "left",
        }
    )

def sidebar() -> rx.Component:
    is_dc = AppState.role == "DC"
    
    return rx.vstack(
        # --- LOGO / HEADER ELEGAN ---
        rx.hstack(
            rx.heading("JEZ", color="#E50914", font_weight="900", size="6"),
            rx.heading("PRO", color="#111111", font_weight="900", size="6"),
            align="center",
            spacing="1",
            margin_bottom="1rem",
        ),
        
        # --- KELOMPOK 1: DASHBOARD SUMMARY (Hanya DC) ---
        rx.cond(
            is_dc,
            rx.vstack(
                rx.text("MAIN MENU", size="1", weight="bold", color="#808495", margin_top="10px"),
                rx.text("DASHBOARD SUMMARY", size="1", weight="bold", color="#808495", margin_bottom="5px"),
                menu_item("Dashboard Overview", "Dashboard Overview"),
                menu_item("Database Master", "Database Master"),
                width="100%",
                spacing="1",
                align_items="start",
            ),
        ),
        
        # --- KELOMPOK 2: OPERATIONAL ---
        rx.vstack(
            rx.text("OPERATIONAL", size="1", weight="bold", color="#808495", margin_top="20px", margin_bottom="5px"),
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
                    width="100%", spacing="1",
                ),
                rx.vstack(
                    menu_item("Compare Penerimaan RTO", "Compare Penerimaan RTO"),
                    menu_item("Putaway System", "Putaway System"),
                    menu_item("Purchase Order Receiving", "Purchase Order Receiving"),
                    width="100%", spacing="1",
                ),
            ),
            width="100%", align_items="start",
        ),

        # --- KELOMPOK 3: INVENTORY ---
        rx.vstack(
            rx.text("INVENTORY", size="1", weight="bold", color="#808495", margin_top="20px", margin_bottom="5px"),
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
                    width="100%", spacing="1",
                ),
                rx.vstack(
                    menu_item("Stock Minus", "Stock Minus"),
                    menu_item("Cycle Count", "Cycle Count"),
                    menu_item("Compare System", "Compare System"),
                    menu_item("Justification SO", "Justification SO"),
                    width="100%", spacing="1",
                ),
            ),
            width="100%", align_items="start",
        ),

        # --- KELOMPOK 4: REJECT & DEFECT ---
        rx.vstack(
            rx.text("REJECT & DEFECT", size="1", weight="bold", color="#808495", margin_top="20px", margin_bottom="5px"),
            menu_item("Pengajuan Reject/Defect", "Pengajuan Reject/Defect"),
            menu_item("Reject/Defect List", "Reject/Defect List"),
            width="100%", spacing="1", align_items="start",
        ),

        # --- KELOMPOK 5: EXTRAS ---
        rx.vstack(
            rx.text("EXTRAS", size="1", weight="bold", color="#808495", margin_top="20px", margin_bottom="5px"),
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
                    width="100%", spacing="1",
                ),
                rx.vstack(
                    menu_item("Precentage Display", "Precentage Display"),
                    menu_item("Refill Toko", "Refill Toko"),
                    menu_item("Store Leader RTO Decission", "Store Leader RTO Decission"),
                    width="100%", spacing="1",
                ),
            ),
            width="100%", align_items="start",
        ),

        width="280px",
        padding="1.5rem",
        background_color="#FFFFFF",
        border_right="2px solid #E2E8F0",
        height="100vh",
        overflow_y="auto",
    )