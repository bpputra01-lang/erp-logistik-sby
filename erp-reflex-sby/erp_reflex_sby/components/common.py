import reflex as rx
from ..state import AppState

def metric_box(title: str, value: str, accent_color: str) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.text(title, size="1", color="#666666", weight="bold"),
            rx.heading(value, size="5", color="#111111", weight="bold"),
            align_items="start", spacing="1",
        ),
        padding="1.2rem", border_radius="12px",
        background="#FFFFFF",
        border_left=f"5px solid {accent_color}",
        border_top="1px solid #EAEAEA", border_right="1px solid #EAEAEA", border_bottom="1px solid #EAEAEA",
        box_shadow="0 4px 12px rgba(0, 0, 0, 0.05)",
        width="100%",
    )

def render_table_row(row: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.checkbox(on_change=lambda _: AppState.toggle_select_id(row["id"]))
        ),
        rx.table.cell(rx.text(row["created_at"], size="2", color="#333333")),
        rx.table.cell(rx.text(row["supplier"], weight="bold", color="#111111")),
        rx.table.cell(rx.badge(row["ekspedisi"], color_scheme="red", variant="soft")),
        rx.table.cell(rx.text(str(row["total_koli"]), color="#333333")),
        rx.table.cell(rx.text(f"Rp {row['total_ongkir']:,.0f}", weight="bold", color="#E50914")),
        style={"_hover": {"background_color": "#F8F9FA"}},
    )