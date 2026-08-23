import reflex as rx

def metric_box(title: str, value: str, accent_color: str, bg_gradient: str) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.text(title, size="1", color="#4A5568", weight="bold", style={"letter_spacing": "0.5px"}),
            rx.heading(value, size="5", color="#111111", font_weight="800"),
            align_items="start",
            spacing="1",
        ),
        padding="1.3rem",
        border_radius="14px",
        style={
            "background": bg_gradient,
            "border_left": f"6px solid {accent_color}",
            "border_top": "1.5px solid #CBD5E0",
            "border_right": "1.5px solid #CBD5E0",
            "border_bottom": "1.5px solid #CBD5E0",
            "box_shadow": "0 4px 12px rgba(0,0,0,0.06)",
            "width": "100%",
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