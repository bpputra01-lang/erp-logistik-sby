from shiny import reactive
from shiny.express import input, render, ui

ui.tags.style("""
    /* Full Page Background Gambar + Gradient Overlay */
    body, html {
        height: 100%;
        margin: 0;
        background-image: 
            radial-gradient(circle at center, rgba(0, 0, 0, 0.15) 0%, rgba(0, 0, 0, 0.45) 100%), 
            url('https://images.unsplash.com/photo-1553413077-190dd305871c?q=80&w=2070');
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    /* Container Tengah */
    .login-container {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 100vh;
        padding: 2rem;
        box-sizing: border-box;
    }

    /* Card Glassmorphism ala Reflex */
    .login-card {
        width: 100%;
        max-width: 520px;
        padding: 3rem 2.5rem;
        background: rgba(12, 12, 15, 0.88) !important;
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-left: 5px solid #E50914 !important;
        box-shadow: 0 25px 60px rgba(0, 0, 0, 0.85);
    }

    /* Input Styling Kustom */
    .custom-input input {
        background: rgba(0, 0, 0, 0.75) !important;
        border: 1px solid rgba(229, 9, 20, 0.4) !important;
        color: #FFFFFF !important;
        border-radius: 10px !important;
        padding: 0.8rem 1rem !important;
        height: 48px !important;
    }

    .custom-input input:focus {
        border-color: #E50914 !important;
        box-shadow: 0 0 10px rgba(229, 9, 20, 0.5) !important;
    }

    /* Gradient Button */
    .btn-login {
        background: linear-gradient(135deg, #E50914 0%, #B20710 100%) !important;
        color: #FFFFFF !important;
        font-weight: 800 !important;
        border-radius: 10px !important;
        cursor: pointer !important;
        box-shadow: 0 4px 15px rgba(229, 9, 20, 0.4) !important;
        height: 48px !important;
        width: 100% !important;
        border: none !important;
        letter-spacing: 1px;
        transition: all 0.2s ease;
    }

    .btn-login:hover {
        opacity: 0.9;
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(229, 9, 20, 0.6) !important;
    }
""")

# 2. Layout & UI Structure
with ui.div(class_="login-container"):
    with ui.div(class_="login-card"):
        
        # Header (Red Bar + Title)
        with ui.div(style="display: flex; align-items: center; gap: 12px; margin-bottom: 1.5rem;"):
            ui.div(style="width: 12px; height: 38px; background: #E50914; border-radius: 4px; flex-shrink: 0;")
            with ui.div():
                ui.div(
                    "LOGISTIC DISTRIBUTION", 
                    style="font-size: 1.25rem; font-weight: 800; color: #FFFFFF; letter-spacing: 1px; line-height: 1.2;"
                )
                ui.div(
                    "CENTER WAREHOUSE • SURABAYA", 
                    style="font-size: 0.75rem; font-weight: 700; color: #E50914; letter-spacing: 2px; margin-top: 2px;"
                )

        # Divider & Subtitle
        ui.hr(style="border-color: rgba(255, 255, 255, 0.1); margin: 1rem 0;")
        ui.div(
            "Silakan masuk dengan akun resmi gudang Anda.", 
            style="color: #B0B0B0; font-size: 0.875rem; margin-bottom: 1.5rem;"
        )

        # Form Input Username
        with ui.div(style="margin-bottom: 1rem;"):
            ui.div("USERNAME", style="font-size: 0.75rem; font-weight: 700; color: #FFFFFF; letter-spacing: 1px; margin-bottom: 0.25rem;")
            ui.div(
                ui.input_text("username", None, placeholder="Masukkan username..."),
                class_="custom-input"
            )

        # Form Input Password
        with ui.div(style="margin-bottom: 1.5rem;"):
            ui.div("PASSWORD", style="font-size: 0.75rem; font-weight: 700; color: #FFFFFF; letter-spacing: 1px; margin-bottom: 0.25rem;")
            ui.div(
                ui.input_password("password", None, placeholder="Masukkan password..."),
                class_="custom-input"
            )

        # Submit Button
        ui.input_action_button("btn_login", "SIGN IN TO SYSTEM →", class_="btn-login")

        # Footer Status
        ui.div(
            "🟢 Warehouse Supporting Tools v2.0", 
            style="text-align: center; color: #888888; font-size: 0.75rem; margin-top: 1.5rem;"
        )

# 3. Server Logic (Handling Sign In / Event)
@reactive.effect
@reactive.event(input.btn_login)
def handle_login():
    user = input.username()
    pwd = input.password()
    # Logika autentikasi kamu ke Supabase / DB bisa ditaruh di sini
    print(f"Logging in user: {user}")