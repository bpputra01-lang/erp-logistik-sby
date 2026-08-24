import reflex as rx
import pandas as pd
from datetime import datetime
import io
import asyncio
from .database import get_supabase

class AppState(rx.State):
    # --- NAVIGATION & ROLE STATE ---
    logged_in: bool = False
    role: str = "toko"  # Contoh: "DC" (admin) atau "CABANG" (toko)
    main_menu: str = "Database Ongkir In/Out"

    def set_main_menu(self, menu: str):
        self.main_menu = menu

    # --- SIDEBAR UI & DROPDOWN STATE ---
    sidebar_open: bool = True
    dropdown_operational: bool = True
    dropdown_inventory: bool = False
    dropdown_reject: bool = False
    dropdown_extras: bool = False

    # --- STOCK MINUS STATE ---
    stock_minus_processed: bool = False
    total_qty_minus: int = 0
    total_tercover: int = 0
    total_sisa_adj: int = 0
    df_minus_awal_data: list[dict] = []
    df_set_up_data: list[dict] = []
    df_need_adj_data: list[dict] = []

    def toggle_sidebar(self):
        self.sidebar_open = not self.sidebar_open

    def toggle_dropdown(self, key: str):
        if key == "operational":
            self.dropdown_operational = not self.dropdown_operational
        elif key == "inventory":
            self.dropdown_inventory = not self.dropdown_inventory
        elif key == "reject":
            self.dropdown_reject = not self.dropdown_reject
        elif key == "extras":
            self.dropdown_extras = not self.dropdown_extras

    # --- LOGIN STATE ---
    username: str = ""
    password: str = ""
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
        self.role = "toko"
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

    # --- STOCK MINUS FILE HANDLER & LOGIC ---
    async def handle_upload_stock_minus(self, files: list[rx.UploadFile]):
        if not files:
            yield rx.toast.warning("Pilih file Excel terlebih dahulu!")
            return

        for file in files:
            upload_data = await file.read()
            try:
                df = pd.read_excel(io.BytesIO(upload_data), engine="openpyxl")
                df.columns = [str(c).strip().upper() for c in df.columns]
                
                col_sku = 'SKU'
                col_bin = 'BIN'
                col_qty = next((c for c in df.columns if 'QTY SYSTEM' in c or 'QTY SYS' in c), None)
                
                if col_qty is None:
                    yield rx.toast.error("❌ Kolom 'QTY SYSTEM' tidak ditemukan!")
                    return
                
                # 1. Persiapan Data
                df[col_qty] = pd.to_numeric(df[col_qty], errors='coerce').fillna(0)
                df[col_sku] = df[col_sku].astype(str).str.strip().str.upper()
                df[col_bin] = df[col_bin].astype(str).str.strip().str.upper()

                df_minus_awal = df[df[col_qty] < 0].copy()
                df_positif = df[df[col_qty] > 0]
                
                inventory = {}
                for _, row in df_positif.iterrows():
                    sku, bn, qt = row[col_sku], row[col_bin], row[col_qty]
                    if sku not in inventory: inventory[sku] = {}
                    inventory[sku][bn] = inventory[sku].get(bn, 0) + qt

                prior_bins = [
                    "RAK ACC LT.1", "STAGGING INBOUND", "STAGGING OUTBOUND", "KARANTINA DC",
                    "KARANTINA STORE 02", "STAGGING REFUND", "STAGING GAGAL QC", "STAGGING LT.3",
                    "STAGGING OUTBOUND SEMARANG", "STAGGING OUTBOUND SIDOARJO", "STAGGING LT.2", "LT.4"
                ]

                set_up_results = []
                df_need_adj_list = []

                # 2. Proses Alokasi & Sisa
                for _, row in df_minus_awal.iterrows():
                    sku = row[col_sku]
                    bin_asal = row[col_bin]
                    sisa_minus = abs(row[col_qty])
                    
                    if sku in inventory and any(v > 0 for v in inventory[sku].values()):
                        sku_stock = inventory[sku]
                        while sisa_minus > 0:
                            bin_solusi = ""
                            if bin_asal == "TOKO":
                                if sku_stock.get("STAGGING LT.2", 0) > 0: bin_solusi = "STAGGING LT.2"
                                elif sku_stock.get("LT.2", 0) > 0: bin_solusi = "LT.2"
                            elif bin_asal in ["STAGGING LT.2", "LT.2"] and sku_stock.get("TOKO", 0) > 0:
                                bin_solusi = "TOKO"

                            if not bin_solusi:
                                for b in prior_bins:
                                    if sku_stock.get(b, 0) > 0: bin_solusi = b; break
                            
                            if not bin_solusi:
                                for b, q in sku_stock.items():
                                    if b != "REJECT DEFECT" and q > 0: bin_solusi = b; break

                            if not bin_solusi: break
                            else:
                                qty_tersedia = sku_stock[bin_solusi]
                                ambil = min(sisa_minus, qty_tersedia)
                                set_up_results.append({
                                    "BIN AWAL": bin_solusi, "BIN TUJUAN": bin_asal,
                                    "SKU": sku, "QUANTITY": ambil, "NOTES": "STOCK MINUS"
                                })
                                sku_stock[bin_solusi] -= ambil
                                sisa_minus -= ambil

                    if sisa_minus > 0:
                        row_adj = row.to_dict()
                        row_adj[col_qty] = -sisa_minus 
                        df_need_adj_list.append(row_adj)

                df_s = pd.DataFrame(set_up_results)
                df_n = pd.DataFrame(df_need_adj_list)

                # Hitung Metrik
                self.total_qty_minus = int(abs(pd.to_numeric(df_minus_awal[col_qty], errors='coerce').sum()))
                self.total_tercover = int(df_s["QUANTITY"].sum()) if not df_s.empty else 0
                self.total_sisa_adj = int(abs(df_n[col_qty].sum())) if not df_n.empty and col_qty in df_n.columns else 0

                # Simpan ke state data list dict (diperbaiki agar tidak saling menimpa salah)
                self.df_minus_awal_data = df_minus_awal.to_dict(orient="records") if not df_minus_awal.empty else []
                self.df_set_up_data = df_s.to_dict(orient="records") if not df_s.empty else []
                self.df_need_adj_data = df_n.to_dict(orient="records") if not df_n.empty else []
                
                self.stock_minus_processed = True
                yield rx.toast.success("✅ Data Stock Minus Berhasil Diproses!")
                
            except Exception as e:
                yield rx.toast.error(f"Gagal memproses file: {e}")

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

    # --- COMPUTED ACTIVE CONTENT STATUS ---
    @rx.var
    def active_content_type(self) -> str:
        if self.main_menu == "Database Ongkir In/Out":
            if self.role == "DC":
                return "dashboard_ongkir"
            else:
                return "access_denied"
        elif self.main_menu == "Stock Minus":
            return "stock_minus"
        else:
            return "under_development"

    @rx.var
    def menu_operational(self) -> list[str]:
        if self.role == "DC":
            return ["Purchase Order Receiving", "Putaway System", "Scan Out Validation", "Refill & Overstock", "Refill & Withdraw", "Compare RTO", "Compare Penerimaan RTO", "FDR Update"]
        else:
            return ["Compare Penerimaan RTO", "Putaway System", "Purchase Order Receiving"]

    @rx.var
    def menu_inventory(self) -> list[str]:
        if self.role == "DC":
            return ["Stock Opname", "Match Real & System", "Compare System", "Cycle Count", "Putaway & Picking Audit List", "List Bin Cycle Count", "Stock Tracking Timeline", "Justification SO", "Stock Minus", "List Retur Out", "Pengajuan Mutasi Karantina", "Refill Koli to Koli/Refill", "Stock Allocation"]
        else:
            return ["Stock Minus", "Cycle Count", "Compare System", "Justification SO"]

    @rx.var
    def menu_reject(self) -> list[str]:
        return ["Pengajuan Reject/Defect", "Reject/Defect List"]

    @rx.var
    def menu_extras(self) -> list[str]:
        if self.role == "DC":
            return ["Logistic Schedule", "Balancing Stock", "Reporting & PIC", "Data Timbang Ongkir", "Database Ongkir In/Out", "Precentage Display", "Precentage Request FL to Store Stock", "Refill Toko"]
        else:
            return ["Precentage Display", "Refill Toko", "Store Leader RTO Decission"]