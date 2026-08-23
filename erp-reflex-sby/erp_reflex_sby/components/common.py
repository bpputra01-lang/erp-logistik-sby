import reflex as rx
from ..state import AppState

def metric_box(title: str, value: str, accent_color: str, bg_gradient: str) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.text(title, size="1", color="#1A202C", weight="bold", style={"letter_spacing": "0.5px"}),
            rx.heading(value, size="5", color="#111111", font_weight="800"),
            align_items="start",
            spacing="1",
        ),
        padding="1.3rem",
        border_radius="14px",
        style={
            "background": bg_gradient + " !important",
            "border-left": f"7px solid {accent_color} !important",
            "border-top": "2px solid #718096 !important",
            "border-right": "2px solid #718096 !important",
            "border-bottom": "2px solid #718096 !important",
            "box-shadow": "0 6px 15px rgba(0,0,0,0.1) !important",
            "width": "100% !important",
        }
    )

def render_table_row(row: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.checkbox(on_change=lambda _: AppState.toggle_select_id(row["id"]))
        ),
        rx.table.cell(rx.text(row["created_at"], size="2", color="#2D3748", font_weight="500")),
        rx.table.cell(rx.text(row["supplier"], weight="bold", color="#111111")),
        rx.table.cell(rx.badge(row["ekspedisi"], color_scheme="red", variant="soft")),
        rx.table.cell(rx.text(str(row["total_koli"]), color="#2D3748", font_weight="600")),
        rx.table.cell(rx.text(f"Rp {row['total_ongkir']:,.0f}", weight="bold", color="#E50914")),
        style={"_hover": {"background_color": "#EDF2F7"}},
    )