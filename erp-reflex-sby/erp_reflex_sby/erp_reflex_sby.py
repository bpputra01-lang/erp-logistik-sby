import reflex as rx
from supabase import create_client
import pandas as pd
from datetime import datetime
import io

# ==========================================
# 1. SUPABASE CONFIG
# ==========================================
SUPABASE_URL = "https://ufhjrsxzcffdfswfqlzk.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVmaGpyc3h6Y2ZmZGZzd2ZxbHprIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYxNTI5NjgsImV4cCI6MjA5MTcyODk2OH0.DDlKkXU5-nVvNYK_uLYzXLgaj8oDT4s8vbjAoWMWacI"

def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)


# ==========================================
# 2. STATE MANAGEMENT (LOGIN & ONGKIR)
# ==========================================
class AppState(rx.State):
    # --- LOGIN STATE ---
    username: str = ""
    password: str = ""
    logged_in: bool = False
    role: str = ""
    branch: str = ""
    user_display_name: str = ""

    def set_username(self, val: str): self.username = val
    def set_password(self, val: str): self.password = val

    def handle_login(self):
        if self.username == "admin" and self.password == "sby123":
            self.logged_in = True
            self.role = "DC"
            self.branch = "SURABAYA"
            self.user_display_name = "Admin DC Surabaya"
            return rx.toast.success("Berhasil Login! Selamat datang di ERP Surabaya.", duration=4000)
        elif self.username == "toko" and self.password == "toko123":
            self.logged_in = True
            self.role = "CABANG"
            self.branch = "SURABAYA"
            self.user_display_name = "User Cabang"
            return rx.toast.success("Berhasil Login sebagai User Cabang!", duration=4000)
        else:
            return rx.toast.error("Username atau Password salah! Periksa kembali.", duration=4000)

    def logout(self):
        self.logged_in = False
        self.username = ""
        self.password = ""
        return rx.toast.info("Anda telah keluar dari sistem.")

    # --- ONGKIR DATABASE STATE ---
    data_list: list[dict] = []
    
    input_supplier: str = ""
    input_ekspedisi: str = ""
    input_koli: str = "1"
    input_ongkir: str = "0"
    input_tgl: str = datetime.now().strftime("%Y-%m-%d")
    input_jam: str = datetime.now().strftime("%H:%M:%S")

    filter_ekspedisi: str = "SEMUA"
    selected_ids: list[int] = []
    show_delete_modal: bool = False

    def set_supplier(self, val: str): self.input_supplier = val
    def set_ekspedisi(self, val: str): self.input_ekspedisi = val
    def set_koli(self, val: str): self.input_koli = val
    def set_ongkir(self, val: str): self.input_ongkir = val
    def set_tgl(self, val: str): self.input_tgl = val
    def set_filter_ekspedisi(self, val: str): self.filter_ekspedisi = val

    def load_data(self):
        """Fetch Data Realtime dari Supabase"""
        try:
            client = get_supabase()
            res = client.table("shipping_costs").select("*").execute()
            self.data_list = res.data if res.data else []
        except Exception as e:
            print("Error loading:", e)

    def save_single_data(self):
        """Simpan Input Manual"""
        if not self.input_supplier.strip():
            return rx.window_alert("Nama Supplier Wajib Diisi!")

        try:
            koli_val = int(self.input_koli) if self.input_koli else 0
            ongkir_val = int(self.input_ongkir) if self.input_ongkir else 0
        except ValueError:
            return rx.window_alert("Koli dan Ongkir harus berupa angka!")

        fix_dt = f"{self.input_tgl} {self.input_jam}"
        payload = {
            "supplier": self.input_supplier.upper(),
            "ekspedisi": self.input_ekspedisi.upper(),
            "total_koli": koli_val,
            "total_ongkir": ongkir_val,
            "created_at": fix_dt
        }
        try:
            client = get_supabase()
            client.table("shipping_costs").insert(payload).execute()
            self.load_data()
            self.input_supplier = ""
            self.input_ekspedisi = ""
            self.input_koli = "1"
            self.input_ongkir = "0"
            return rx.window_alert("✅ Data Berhasil Disimpan!")
        except Exception as e:
            return rx.window_alert(f"Gagal Simpan: {e}")

    async def handle_upload(self, files: list[rx.UploadFile]):
        """Batch Upload CSV File Processing"""
        for file in files:
            upload_data = await file.read()
            df = pd.read_csv(io.BytesIO(upload_data))
            
            required = ["SUPPLIER", "EKSPEDISI", "TOTAL KOLI", "ONGKIR", "TANGGAL_JAM"]
            if not all(col in df.columns for col in required):
                return rx.window_alert("Format CSV Salah! Wajib ada kolom template.")

            batch_data = []
            for _, row in df.iterrows():
                sup = str(row["SUPPLIER"]).upper().strip() if not pd.isna(row["SUPPLIER"]) else ""
                if not sup: continue
                
                eks = str(row["EKSPEDISI"]).upper().strip() if not pd.isna(row["EKSPEDISI"]) else ""
                try: koli = int(float(row["TOTAL KOLI"]))
                except: koli = 0
                
                try: ongkir = int(float(str(row["ONGKIR"]).replace('Rp', '').replace('.', '').replace(',', '').strip()))
                except: ongkir = 0

                tgl_raw = row["TANGGAL_JAM"]
                fix_dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S") if pd.isna(tgl_raw) else str(tgl_raw)

                batch_data.append({
                    "supplier": sup, "ekspedisi": eks, "total_koli": koli,
                    "total_ongkir": ongkir, "created_at": fix_dt
                })

            if batch_data:
                client = get_supabase()
                client.table("shipping_costs").insert(batch_data).execute()
                self.load_data()
                return rx.window_alert(f"🚀 Berhasil Upload {len(batch_data)} Data CSV!")

    # Multi Delete Logic
    def toggle_select_id(self, item_id: int):
        if item_id in self.selected_ids:
            self.selected_ids.remove(item_id)
        else:
            self.selected_ids.append(item_id)

    def open_delete_modal(self):
        if self.selected_ids:
            self.show_delete_modal = True

    def close_delete_modal(self):
        self.show_delete_modal = False

    def execute_delete(self):
        try:
            client = get_supabase()
            client.table("shipping_costs").delete().in_("id", self.selected_ids).execute()
            self.selected_ids = []
            self.show_delete_modal = False
            self.load_data()
            return rx.window_alert("🗑️ Data Berhasil Dihapus!")
        except Exception as e:
            return rx.window_alert(f"Gagal Hapus: {e}")

    # COMPUTED METRICS
    @rx.var
    def filtered_list(self) -> list[dict]:
        res = self.data_list
        if self.filter_ekspedisi != "SEMUA":
            res = [x for x in res if x.get("ekspedisi") == self.filter_ekspedisi]
        return res

    @rx.var
    def list_ekspedisi_options(self) -> list[str]:
        eksp = list(set([x.get("ekspedisi", "") for x in self.data_list if x.get("ekspedisi")]))
        return ["SEMUA"] + sorted(eksp)

    @rx.var
    def total_biaya_all(self) -> str:
        tot = sum([x.get("total_ongkir", 0) for x in self.filtered_list])
        return f"Rp {tot:,.0f}"

    @rx.var
    def total_koli_all(self) -> str:
        tot = sum([x.get("total_koli", 0) for x in self.filtered_list])
        return f"{tot:,.0f} Koli"

    @rx.var
    def avg_cost_all(self) -> str:
        biaya = sum([x.get("total_ongkir", 0) for x in self.filtered_list])
        koli = sum([x.get("total_koli", 0) for x in self.filtered_list])
        avg = biaya / koli if koli > 0 else 0
        return f"Rp {avg:,.0f}"

    @rx.var
    def biaya_datang(self) -> str:
        tot = sum([x.get("total_ongkir", 0) for x in self.filtered_list if "RTO" not in x.get("supplier", "")])
        return f"Rp {tot:,.0f}"

    @rx.var
    def koli_datang(self) -> str:
        tot = sum([x.get("total_koli", 0) for x in self.filtered_list if "RTO" not in x.get("supplier", "")])
        return f"{tot:,.0f} Koli"

    @rx.var
    def biaya_rto(self) -> str:
        tot = sum([x.get("total_ongkir", 0) for x in self.filtered_list if "RTO" in x.get("supplier", "")])
        return f"Rp {tot:,.0f}"

    @rx.var
    def koli_rto(self) -> str:
        tot = sum([x.get("total_koli", 0) for x in self.filtered_list if "RTO" in x.get("supplier", "")])
        return f"{tot:,.0f} Koli"


# ==========================================
# 3. UI COMPONENTS
# ==========================================
def login_page() -> rx.Component:
    return rx.flex(
        rx.box(
            rx.vstack(
                # Header Logo / Title
                rx.hstack(
                    rx.box(width="12px", height="35px", background="#E50914", border_radius="4px"),
                    rx.vstack(
                        rx.heading("LOGISTIC DISTRIBUTION", size="6", color="#FFFFFF", font_weight="800", letter_spacing="1px"),
                        rx.text("CENTER WAREHOUSE • SURABAYA", size="1", color="#E50914", font_weight="700", letter_spacing="2px"),
                        spacing="0",
                    ),
                    align="center",
                    spacing="3",
                ),
                rx.divider(border_color="rgba(255, 255, 255, 0.1)"),
                rx.text("Silakan masuk dengan akun resmi gudang Anda.", size="2", color="#B0B0B0"),

                # Input Username
                rx.vstack(
                    rx.text("USERNAME", size="1", font_weight="700", color="#FFFFFF", letter_spacing="1px"),
                    rx.input(
                        placeholder="Masukkan username...",
                        value=AppState.username,
                        on_change=AppState.set_username,
                        size="3",
                        variant="surface",
                        color_scheme="red",
                        style={
                            "background": "rgba(0, 0, 0, 0.75)", 
                            "border": "1px solid rgba(229, 9, 20, 0.4)", 
                            "color": "#FFFFFF", 
                            "border-radius": "10px"
                        },
                    ),
                    spacing="1", width="100%",
                ),

                # Input Password
                rx.vstack(
                    rx.text("PASSWORD", size="1", font_weight="700", color="#FFFFFF", letter_spacing="1px"),
                    rx.input(
                        type="password",
                        placeholder="Masukkan password...",
                        value=AppState.password,
                        on_change=AppState.set_password,
                        size="3",
                        variant="surface",
                        color_scheme="red",
                        style={
                            "background": "rgba(0, 0, 0, 0.75)", 
                            "border": "1px solid rgba(229, 9, 20, 0.4)", 
                            "color": "#FFFFFF", 
                            "border-radius": "10px"
                        },
                    ),
                    spacing="1", width="100%",
                ),

                rx.box(height="10px"),

                # Button Submit
                rx.button(
                    "SIGN IN TO SYSTEM →",
                    on_click=AppState.handle_login,
                    size="3",
                    width="100%",
                    style={
                        "background": "linear-gradient(135deg, #E50914 0%, #B20710 100%)", 
                        "color": "#FFFFFF", 
                        "font-weight": "800", 
                        "border-radius": "10px", 
                        "cursor": "pointer",
                        "box-shadow": "0 4px 15px rgba(229, 9, 20, 0.4)"
                    },
                ),

                rx.center(
                    rx.text("🟢 Warehouse Supporting Tools v2.0", size="1", color="#888888"),
                    margin_top="10px",
                ),
                spacing="5",
                align="stretch",
            ),
            width="100%",
            max_width="440px",
            padding="2.5rem",
            background="rgba(10, 10, 14, 0.88)", # Pekat transparan agar kontras dengan background terang
            backdrop_filter="blur(20px)",
            border_radius="20px",
            border="1px solid rgba(255, 255, 255, 0.12)",
            border_left="5px solid #E50914",
            box_shadow="0 20px 50px rgba(0, 0, 0, 0.6)",
        ),
        # GAMBAR GUDANG TERANG BERSIH + OVERLAY GRADIENT
        background_image="linear-gradient(to right, rgba(5, 5, 8, 0.95) 0%, rgba(5, 5, 8, 0.60) 35%, rgba(255, 255, 255, 0.05) 100%), url('https://images.unsplash.com/photo-1553413077-190dd305871c?q=80&w=2070')",
        background_size="cover",
        background_position="center",
        background_repeat="no-repeat",
        width="100vw",
        height="100vh",
        align="center",
        justify="start",
        padding_left=["2rem", "5rem", "8rem"],
        padding_right="2rem",
    )
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

def main_dashboard() -> rx.Component:
    return rx.box(
        rx.vstack(
            # TOP BAR / HEADER LOGOUT
            rx.hstack(
                rx.vstack(
                    rx.heading("🛻 DATABASE ONGKIR IN/OUT", size="6", color="white"),
                    rx.text(f"Logged in as: {AppState.user_display_name} ({AppState.role})", size="2", color="#8F95B2"),
                    align_items="start", spacing="1",
                ),
                rx.hstack(
                    rx.badge("● SUPABASE CONNECTED", color_scheme="green", variant="soft", size="3"),
                    rx.button("Logout", on_click=AppState.logout, color_scheme="red", variant="soft", size="2"),
                    spacing="3",
                ),
                justify="between", width="100%", padding_bottom="1rem", border_bottom="1px solid #232738",
            ),

            # TABS CONTROL
            rx.tabs.root(
                rx.tabs.list(
                    rx.tabs.trigger("📥 INPUT & BATCH DATA", value="tab1"),
                    rx.tabs.trigger("📊 SUMMARY & HISTORY", value="tab2"),
                    background="#141724", padding="4px", border_radius="8px",
                ),
                
                # TAB 1: INPUT FORM
                rx.tabs.content(
                    rx.grid(
                        rx.box(
                            rx.vstack(
                                rx.heading("📝 Input Transaksi Manual", size="4", color="#FFD700"),
                                rx.input(placeholder="Nama Supplier...", value=AppState.input_supplier, on_change=AppState.set_supplier, width="100%"),
                                rx.hstack(
                                    rx.input(placeholder="Ekspedisi...", value=AppState.input_ekspedisi, on_change=AppState.set_ekspedisi, width="100%"),
                                    rx.input(type="number", placeholder="Total Koli", value=AppState.input_koli, on_change=AppState.set_koli, width="100%"),
                                    width="100%",
                                ),
                                rx.hstack(
                                    rx.input(type="number", placeholder="Total Ongkir (Rp)", value=AppState.input_ongkir, on_change=AppState.set_ongkir, width="100%"),
                                    rx.input(type="date", value=AppState.input_tgl, on_change=AppState.set_tgl, width="100%"),
                                    width="100%",
                                ),
                                rx.button("🚀 SIMPAN DATA ONGKIR", on_click=AppState.save_single_data, color_scheme="gold", width="100%", size="3"),
                                spacing="3",
                            ),
                            padding="1.5rem", background="#141724", border_radius="12px", border="1px solid #232738",
                        ),
                        rx.box(
                            rx.vstack(
                                rx.heading("📁 Batch CSV Upload", size="4", color="#00EB93"),
                                rx.upload(
                                    rx.vstack(
                                        rx.button("Pilih File CSV", color_scheme="gray", variant="outline"),
                                        rx.text("Drag and drop file CSV di sini", size="2", color="#8F95B2"),
                                    ),
                                    id="upload_csv", border="1px dashed #FFD700", padding="2rem", border_radius="10px", width="100%",
                                ),
                                rx.button("⚡ EXECUTE BATCH UPLOAD", on_click=AppState.handle_upload(rx.upload_files(upload_id="upload_csv")), color_scheme="green", width="100%", size="3"),
                                spacing="3",
                            ),
                            padding="1.5rem", background="#141724", border_radius="12px", border="1px solid #232738",
                        ),
                        columns=rx.breakpoints(initial="1", sm="2"), spacing="4", width="100%", margin_top="1rem",
                    ),
                    value="tab1",
                ),

                # TAB 2: SUMMARY & HISTORY
                rx.tabs.content(
                    rx.vstack(
                        rx.hstack(
                            rx.select(AppState.list_ekspedisi_options, value=AppState.filter_ekspedisi, on_change=AppState.set_filter_ekspedisi, width="200px"),
                            rx.cond(
                                AppState.selected_ids.length() > 0,
                                rx.button(f"🗑️ HAPUS ({AppState.selected_ids.length()}) DATA", on_click=AppState.open_delete_modal, color_scheme="red", variant="solid"),
                            ),
                            justify="between", width="100%", margin_top="1rem",
                        ),
                        rx.grid(
                            metric_box("💰 BIAYA ALL", AppState.total_biaya_all, "#FFD700"),
                            metric_box("📦 KOLI ALL", AppState.total_koli_all, "#FFD700"),
                            metric_box("📊 AVG COST ALL", AppState.avg_cost_all, "#FFD700"),
                            metric_box("🚚 BIAYA DATANG", AppState.biaya_datang, "#00EB93"),
                            metric_box("📦 KOLI DATANG", AppState.koli_datang, "#00EB93"),
                            metric_box("🔄 BIAYA RTO", AppState.biaya_rto, "#FF4B4B"),
                            columns=rx.breakpoints(initial="1", sm="3"), spacing="3", width="100%",
                        ),
                        rx.box(
                            rx.table.root(
                                rx.table.header(
                                    rx.table.row(
                                        rx.table.column_header_cell("SELECT"),
                                        rx.table.column_header_cell("TANGGAL"),
                                        rx.table.column_header_cell("SUPPLIER"),
                                        rx.table.column_header_cell("EKSPEDISI"),
                                        rx.table.column_header_cell("KOLI"),
                                        rx.table.column_header_cell("TOTAL ONGKIR"),
                                    ),
                                ),
                                rx.table.body(rx.foreach(AppState.filtered_list, render_table_row)),
                                width="100%",
                            ),
                            background="#141724", border_radius="12px", border="1px solid #232738", padding="1rem", width="100%",
                        ),
                        spacing="4", width="100%",
                    ),
                    value="tab2",
                ),
                width="100%",
            ),

            # POPUP MODAL DELETE
            rx.dialog.root(
                rx.dialog.content(
                    rx.dialog.title("⚠️ Konfirmasi Delete"),
                    rx.dialog.description("Yakin mau menghapus data dari Supabase secara permanen?"),
                    rx.hstack(
                        rx.button("Batal", on_click=AppState.close_delete_modal, variant="soft"),
                        rx.button("Ya, Hapus!", on_click=AppState.execute_delete, color_scheme="red"),
                        justify="end", spacing="3", margin_top="1rem",
                    ),
                    background="#141724", border="1px solid #232738",
                ),
                open=AppState.show_delete_modal,
            ),
            spacing="4", padding="2rem", max_width="1200px", margin="0 auto", on_mount=AppState.load_data,
        ),
        background_color="#0d0f17", min_height="100vh",
    )

# ==========================================
# 4. ROUTER & MAIN ENTRY POINT
# ==========================================
def index() -> rx.Component:
    return rx.cond(
        AppState.logged_in,
        main_dashboard(),
        login_page()
    )

# MENGATUR TOAST KE POJOK KANAN ATAS (top-right)
app = rx.App(
    theme=rx.theme(appearance="dark", accent_color="gold"),
    style={
        "[data-sonner-toaster]": {
            "top": "20px !important",
            "right": "20px !important",
            "bottom": "auto !important",
            "left": "auto !important",
        }
    }
)
app.add_page(index, route="/", title="ZKN ERP - Database Ongkir")