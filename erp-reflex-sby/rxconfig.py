import reflex as rx

config = rx.Config(
    app_name="erp_reflex_sby",
    favicon="/favicon.png",
    show_reflex_badge=False,
    plugins=[
        rx.plugins.RadixThemesPlugin(
            theme=rx.theme(appearance="dark", accent_color="red")
        ),
    ],
)