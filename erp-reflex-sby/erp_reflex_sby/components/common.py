import reflex as rx
from ..state import AppState

def metric_box(title: str, value: str, accent_color: str) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.text(title, size="1", color="#8F95B2", weight="bold"),
            rx.heading(value, size="5", color=accent_color, weight="bold"),
            align_items="start", spacing="1",
        ),
        padding="1rem", border_radius="10px",
        background="linear-gradient(135deg, #181b28 0%, #11131f 100%)",
        border_left=f"4px solid {accent_color}",
        border_top="1px solid #232738", border_right="1px solid #232738", border_bottom="1px solid #232738",
        width="100%",
    )

def render_table_row(row: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.checkbox(on_change=lambda _: AppState.toggle_select_id(row["id"]))
        ),
        rx.table.cell(rx.text(row["created_at"], size="2")),
        rx.table.cell(rx.text(row["supplier"], weight="bold", color="#FFD700")),
        rx.table.cell(rx.badge(row["ekspedisi"], color_scheme="gold", variant="solid")),
        rx.table.cell(str(row["total_koli"])),
        rx.table.cell(f"Rp {row['total_ongkir']:,.0f}"),
    )