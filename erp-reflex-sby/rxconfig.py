import reflex as rx

config = rx.Config(
    app_name="erp_reflex_sby",
    favicon="/favicon.png",
    plugins=[
        rx.plugins.RadixThemesPlugin(
            appearance="dark", 
            accent_color="red"
        ),
    ],
)