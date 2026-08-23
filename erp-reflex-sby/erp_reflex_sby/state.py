import reflex as rx
import pandas as pd
from datetime import datetime
import io
import asyncio
from .database import get_supabase

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
            return rx.toast.success("Berhasil Login! Selamat datang di ERP Surabaya.", duration=4000, position="top-right")
            
        elif self.username == "toko" and self.password == "toko123":
            self.logged_in = True
            self.role = "CABANG"
            self.branch = "SURABAYA"
            self.user_display_name = "User Cabang"
            return rx.toast.success("Berhasil Login sebagai User Cabang!", duration=4000, position="top-right")
            
        else:
            return rx.toast.error("Username atau Password salah! Periksa kembali.", duration=4000, position="top-right")

    def handle_key_down(self, key: str):
        if key == "Enter":
            return self.handle_login()

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

    async def load_data(self):
        try:
            client = get_supabase()
            res = await asyncio.to_thread(lambda: client.table("shipping_costs").select("*").execute())
            self.data_list = res.data if res.data else []
        except Exception as e:
            print("Error loading:", e)

    async def save_single_data(self):
        if not self.input_supplier.strip():
            yield rx.toast.warning("Nama Supplier Wajib Diisi!")
            return

        try:
            koli_val = int(self.input_koli) if self.input_koli else 0
            ongkir_val = int(self.input_ongkir) if self.input_ongkir else 0
        except ValueError:
            yield rx.toast.warning("Koli dan Ongkir harus berupa angka!")
            return

        fix_dt = f"{self.input_tgl} {self.input_jam}"
        payload = {
            "supplier": self.input_supplier.upper().strip(),
            "ekspedisi": self.input_ekspedisi.upper().strip(),
            "total_koli": koli_val,
            "total_ongkir": ongkir_val,
            "created_at": fix_dt
        }
        try:
            client = get_supabase()
            await asyncio.to_thread(lambda: client.table("shipping_costs").insert(payload).execute())
            self.input_supplier = ""
            self.input_ekspedisi = ""
            self.input_koli = "1"
            self.input_ongkir = "0"
            yield rx.toast.success("✅ Data Berhasil Disimpan!")
            yield AppState.load_data()
        except Exception as e:
            yield rx.toast.error(f"Gagal Simpan: {e}")

    async def handle_upload(self, files: list[rx.UploadFile]):
        if not files:
            yield rx.toast.warning("Pilih file CSV terlebih dahulu!")
            return

        for file in files:
            upload_data = await file.read()
            df = pd.read_csv(io.BytesIO(upload_data))

            required = ["SUPPLIER", "EKSPEDISI", "TOTAL KOLI", "ONGKIR", "TANGGAL_JAM"]
            if not all(col in df.columns for col in required):
                yield rx.toast.error("Format CSV Salah! Kolom wajib: SUPPLIER, EKSPEDISI, TOTAL KOLI, ONGKIR, TANGGAL_JAM")
                return

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
                    "supplier": sup, 
                    "ekspedisi": eks, 
                    "total_koli": koli,
                    "total_ongkir": ongkir, 
                    "created_at": fix_dt
                })

            if batch_data:
                try:
                    client = get_supabase()
                    await asyncio.to_thread(lambda: client.table("shipping_costs").insert(batch_data).execute())
                    yield rx.toast.success(f"🚀 Berhasil Upload {len(batch_data)} Data CSV!")
                    yield AppState.load_data()
                except Exception as e:
                    yield rx.toast.error(f"Gagal Upload Batch: {e}")

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

    async def execute_delete(self):
        try:
            client = get_supabase()
            await asyncio.to_thread(lambda: client.table("shipping_costs").delete().in_("id", self.selected_ids).execute())
            self.selected_ids = []
            self.show_delete_modal = False
            yield rx.toast.success("🗑️ Data Berhasil Dihapus!")
            yield AppState.load_data()
        except Exception as e:
            yield rx.toast.error(f"Gagal Hapus: {e}")

    # --- COMPUTED METRICS ---
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
        tot = sum([x.get("total_ongkir", 0) for x in self.filtered_list if "RTO" not in str(x.get("supplier", ""))])
        return f"Rp {tot:,.0f}"

    @rx.var
    def koli_datang(self) -> str:
        tot = sum([x.get("total_koli", 0) for x in self.filtered_list if "RTO" not in str(x.get("supplier", ""))])
        return f"{tot:,.0f} Koli"

    @rx.var
    def biaya_rto(self) -> str:
        tot = sum([x.get("total_ongkir", 0) for x in self.filtered_list if "RTO" in str(x.get("supplier", ""))])
        return f"Rp {tot:,.0f}"

    @rx.var
    def koli_rto(self) -> str:
        tot = sum([x.get("total_koli", 0) for x in self.filtered_list if "RTO" in str(x.get("supplier", ""))])
        return f"{tot:,.0f} Koli"