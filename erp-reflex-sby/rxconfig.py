import reflex as rx

config = rx.Config(
    app_name="erp_reflex_sby",
    plugins=[
        rx.plugins.RadixThemesPlugin(theme=rx.theme(appearance="dark", accent_color="red")),
    ],
)