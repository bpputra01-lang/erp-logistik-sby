import io
import time
from datetime import datetime
import pandas as pd
from shiny import reactive
from .database import get_supabase

class AppState:
    def __init__(self):
        # --- NAVIGATION & ROLE STATE ---
        self.logged_in = reactive.Value(False)
        self.role = reactive.Value("toko")  # "DC" atau "CABANG"
        self.branch = reactive.Value("SURABAYA")
        self.user_display_name = reactive.Value("")
        self.username = reactive.Value("")
        self.password = reactive.Value("")
        self.login_timestamp_ms = reactive.Value(0)
        self.main_menu = reactive.Value("Database Ongkir In/Out")

        # --- SIDEBAR UI & DROPDOWN STATE ---
        self.sidebar_open = reactive.Value(True)
        self.dropdown_operational = reactive.Value(True)
        self.dropdown_inventory = reactive.Value(False)
        self.dropdown_reject = reactive.Value(False)
        self.dropdown_extras = reactive.Value(False)

        # --- MODAL & LOADING STATES ---
        self.is_info_open = reactive.Value(False)
        self.is_loading = reactive.Value(False)
        self.show_success_modal = reactive.Value(False)

        # --- ONGKIR DATABASE STATE ---
        self.data_list = reactive.Value([])
        self.input_supplier = reactive.Value("")
        self.input_ekspedisi = reactive.Value("")
        self.input_koli = reactive.Value("1")
        self.input_ongkir = reactive.Value("0")
        self.input_tgl = reactive.Value(datetime.now().strftime("%Y-%m-%d"))
        self.input_jam = reactive.Value(datetime.now().strftime("%H:%M:%S"))
        self.filter_ekspedisi = reactive.Value("SEMUA")
        self.selected_ids = reactive.Value([])
        self.show_delete_modal = reactive.Value(False)

        # --- STOCK MINUS STATE ---
        self.stock_minus_processed = reactive.Value(False)
        self.total_qty_minus = reactive.Value(0)
        self.total_tercover = reactive.Value(0)
        self.total_sisa_adj = reactive.Value(0)

        self.df_minus_awal_headers = reactive.Value([])
        self.df_minus_awal_rows = reactive.Value([])
        self.df_set_up_headers = reactive.Value([])
        self.df_set_up_rows = reactive.Value([])
        self.df_need_adj_headers = reactive.Value([])
        self.df_need_adj_rows = reactive.Value([])

        self._raw_df_minus_awal = pd.DataFrame()
        self._raw_df_set_up = pd.DataFrame()
        self._raw_df_need_adj = pd.DataFrame()

        # --- PUTAWAY SYSTEM STATE ---
        self.area_putaway = reactive.Value("")
        self.putaway_processed = reactive.Value(False)
        self.putaway_qty_system = reactive.Value(0)
        self.putaway_total_setup = reactive.Value(0)
        self.putaway_kurang_setup = reactive.Value(0)
        self.putaway_sisa_stok = reactive.Value(0)

        self.df_comp_headers = reactive.Value([])
        self.df_comp_rows = reactive.Value([])
        self.df_plist_headers = reactive.Value([])
        self.df_plist_rows = reactive.Value([])
        self.df_kurang_headers = reactive.Value([])
        self.df_kurang_rows = reactive.Value([])
        self.df_out_headers = reactive.Value([])
        self.df_out_rows = reactive.Value([])

        self._raw_df_comp = pd.DataFrame()
        self._raw_df_plist = pd.DataFrame()
        self._raw_df_kurang = pd.DataFrame()
        self._raw_df_out = pd.DataFrame()
        self._raw_df_updated = pd.DataFrame()

    # ==========================================
    # 1. NAVIGATION & AUTHENTICATION METHODS
    # ==========================================
    def set_main_menu(self, menu: str):
        self.main_menu.set(menu)

    def toggle_sidebar(self):
        self.sidebar_open.set(not self.sidebar_open())

    def toggle_dropdown(self, key: str):
        if key == "operational": self.dropdown_operational.set(not self.dropdown_operational())
        elif key == "inventory": self.dropdown_inventory.set(not self.dropdown_inventory())
        elif key == "reject": self.dropdown_reject.set(not self.dropdown_reject())
        elif key == "extras": self.dropdown_extras.set(not self.dropdown_extras())

    def handle_login(self, u: str, p: str):
        u = u.strip()
        p = p.strip()
        if u == "admin" and p == "sby123":
            self.logged_in.set(True)
            self.role.set("DC")
            self.branch.set("SURABAYA")
            self.user_display_name.set("Admin DC Surabaya")
            self.login_timestamp_ms.set(int(time.time() * 1000))
            return True, "Berhasil Login! Selamat datang di ERP Surabaya."
        elif u == "toko" and p == "toko123":
            self.logged_in.set(True)
            self.role.set("CABANG")
            self.branch.set("SURABAYA")
            self.user_display_name.set("User Cabang")
            self.login_timestamp_ms.set(int(time.time() * 1000))
            return True, "Berhasil Login sebagai User Cabang!"
        else:
            return False, "Username atau Password salah! Periksa kembali."

    def logout(self):
        self.logged_in.set(False)
        self.username.set("")
        self.password.set("")
        self.role.set("toko")
        self.login_timestamp_ms.set(0)

    # ==========================================
    # 2. ROLE-BASED MENUS
    # ==========================================
    def get_menu_operational(self) -> list[str]:
        if self.role() == "DC":
            return ["Purchase Order Receiving", "Putaway System", "Scan Out Validation", "Refill & Overstock", "Refill & Withdraw", "Compare RTO", "Compare Penerimaan RTO", "FDR Update"]
        else:
            return ["Compare Penerimaan RTO", "Putaway System", "Purchase Order Receiving"]

    def get_menu_inventory(self) -> list[str]:
        if self.role() == "DC":
            return ["Stock Opname", "Match Real & System", "Compare System", "Cycle Count", "Putaway & Picking Audit List", "List Bin Cycle Count", "Stock Tracking Timeline", "Justification SO", "Stock Minus", "List Retur Out", "Pengajuan Mutasi Karantina", "Refill Koli to Koli/Refill", "Stock Allocation"]
        else:
            return ["Stock Minus", "Cycle Count", "Compare System", "Justification SO"]

    def get_menu_reject(self) -> list[str]:
        return ["Pengajuan Reject/Defect", "Reject/Defect List"]

    def get_menu_extras(self) -> list[str]:
        if self.role() == "DC":
            return ["Logistic Schedule", "Balancing Stock", "Reporting & PIC", "Data Timbang Ongkir", "Database Ongkir In/Out", "Precentage Display", "Precentage Request FL to Store Stock", "Refill Toko"]
        else:
            return ["Precentage Display", "Refill Toko", "Store Leader RTO Decission"]

    def get_active_content_type(self) -> str:
        cur_menu = self.main_menu()
        if cur_menu == "Database Ongkir In/Out":
            return "dashboard_ongkir" if self.role() == "DC" else "access_denied"
        elif cur_menu == "Stock Minus":
            return "stock_minus"
        elif cur_menu == "Putaway System":
            return "putaway_system"
        else:
            return "under_development"

    # ==========================================
    # 3. ONGKIR DATABASE METHODS & METRICS
    # ==========================================
    def load_ongkir_data(self):
        try:
            client = get_supabase()
            if client:
                res = client.table("shipping_costs").select("*").execute()
                self.data_list.set(res.data if res.data else [])
        except Exception as e:
            print("Error loading Supabase data:", e)

    def save_single_ongkir(self, supp: str, eksp: str, koli_str: str, ongkir_str: str, tgl_str: str):
        if not supp.strip():
            return False, "Nama Supplier Wajib Diisi!"
        try:
            koli_val = int(koli_str) if koli_str else 0
            ongkir_val = int(ongkir_str) if ongkir_str else 0
        except ValueError:
            return False, "Koli dan Ongkir harus berupa angka!"

        fix_dt = f"{tgl_str} {datetime.now().strftime('%H:%M:%S')}"
        payload = {
            "supplier": supp.upper().strip(),
            "ekspedisi": eksp.upper().strip(),
            "total_koli": koli_val,
            "total_ongkir": ongkir_val,
            "created_at": fix_dt
        }
        try:
            client = get_supabase()
            if client:
                client.table("shipping_costs").insert(payload).execute()
            self.load_ongkir_data()
            return True, "✅ Data Berhasil Disimpan!"
        except Exception as e:
            return False, f"Gagal Simpan: {e}"

    def batch_upload_csv(self, file_bytes: bytes):
        try:
            df = pd.read_csv(io.BytesIO(file_bytes))
            required = ["SUPPLIER", "EKSPEDISI", "TOTAL KOLI", "ONGKIR", "TANGGAL_JAM"]
            if not all(col in df.columns for col in required):
                return False, "Format CSV Salah! Kolom wajib: SUPPLIER, EKSPEDISI, TOTAL KOLI, ONGKIR, TANGGAL_JAM"

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
                batch_data.append({"supplier": sup, "ekspedisi": eks, "total_koli": koli, "total_ongkir": ongkir, "created_at": fix_dt})

            if batch_data:
                client = get_supabase()
                if client:
                    client.table("shipping_costs").insert(batch_data).execute()
                self.load_ongkir_data()
                return True, f"🚀 Berhasil Upload {len(batch_data)} Data CSV!"
            return False, "Tidak ada data valid yang diupload."
        except Exception as e:
            return False, f"Gagal Upload Batch: {e}"

    def toggle_select_id(self, item_id: int):
        s = list(self.selected_ids())
        if item_id in s: s.remove(item_id)
        else: s.append(item_id)
        self.selected_ids.set(s)

    def execute_delete(self):
        s = self.selected_ids()
        try:
            client = get_supabase()
            if client:
                client.table("shipping_costs").delete().in_("id", s).execute()
            self.selected_ids.set([])
            self.show_delete_modal.set(False)
            self.load_ongkir_data()
            return True, "🗑️ Data Berhasil Dihapus!"
        except Exception as e:
            return False, f"Gagal Hapus: {e}"

    def get_filtered_ongkir(self) -> list[dict]:
        res = self.data_list()
        flt = self.filter_ekspedisi()
        if flt != "SEMUA":
            res = [x for x in res if x.get("ekspedisi") == flt]
        return res

    def get_list_ekspedisi_options(self) -> list[str]:
        eksp = list(set([x.get("ekspedisi", "") for x in self.data_list() if x.get("ekspedisi")]))
        return ["SEMUA"] + sorted(eksp)

    def metric_total_biaya_all(self) -> str:
        return f"Rp {sum([x.get('total_ongkir', 0) for x in self.get_filtered_ongkir()]):,.0f}"

    def metric_total_koli_all(self) -> str:
        return f"{sum([x.get('total_koli', 0) for x in self.get_filtered_ongkir()]):,.0f} Koli"

    def metric_avg_cost_all(self) -> str:
        data = self.get_filtered_ongkir()
        biaya = sum([x.get("total_ongkir", 0) for x in data])
        koli = sum([x.get("total_koli", 0) for x in data])
        return f"Rp {biaya / koli if koli > 0 else 0:,.0f}"

    def metric_biaya_datang(self) -> str:
        return f"Rp {sum([x.get('total_ongkir', 0) for x in self.get_filtered_ongkir() if 'RTO' not in str(x.get('supplier', ''))]):,.0f}"

    def metric_koli_datang(self) -> str:
        return f"{sum([x.get('total_koli', 0) for x in self.get_filtered_ongkir() if 'RTO' not in str(x.get('supplier', ''))]):,.0f} Koli"

    def metric_biaya_rto(self) -> str:
        return f"Rp {sum([x.get('total_ongkir', 0) for x in self.get_filtered_ongkir() if 'RTO' in str(x.get('supplier', ''))]):,.0f}"

    # ==========================================
    # 4. STOCK MINUS PROCESSING ALGORITHM
    # ==========================================
    def process_stock_minus_file(self, file_bytes: bytes, file_name: str):
        try:
            df = pd.read_excel(io.BytesIO(file_bytes), engine="openpyxl") if file_name.endswith(('.xlsx', '.xls')) else pd.read_csv(io.BytesIO(file_bytes))
            df.columns = [str(c).strip().upper() for c in df.columns]

            col_sku = 'SKU'
            col_bin = 'BIN'
            col_qty = next((c for c in df.columns if 'QTY SYSTEM' in c or 'QTY SYS' in c), None)

            if col_qty is None:
                return False, "❌ Kolom 'QTY SYSTEM' tidak ditemukan!"

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

            self.total_qty_minus.set(int(abs(pd.to_numeric(df_minus_awal[col_qty], errors='coerce').sum())))
            self.total_tercover.set(int(df_s["QUANTITY"].sum()) if not df_s.empty else 0)
            self.total_sisa_adj.set(int(abs(df_n[col_qty].sum())) if not df_n.empty and col_qty in df_n.columns else 0)

            self._raw_df_minus_awal = df_minus_awal
            self._raw_df_set_up = df_s
            self._raw_df_need_adj = df_n

            self.df_minus_awal_headers.set(df_minus_awal.columns.tolist() if not df_minus_awal.empty else [])
            self.df_minus_awal_rows.set(df_minus_awal.fillna("").astype(str).values.tolist() if not df_minus_awal.empty else [])

            self.df_set_up_headers.set(df_s.columns.tolist() if not df_s.empty else [])
            self.df_set_up_rows.set(df_s.fillna("").astype(str).values.tolist() if not df_s.empty else [])

            self.df_need_adj_headers.set(df_n.columns.tolist() if not df_n.empty else [])
            self.df_need_adj_rows.set(df_n.fillna("").astype(str).values.tolist() if not df_n.empty else [])

            self.stock_minus_processed.set(True)
            return True, "Data Stock Minus berhasil diproses!"
        except Exception as e:
            return False, f"Gagal memproses file: {e}"

    # ==========================================
    # 5. PUTAWAY COMPARE ALGORITHM
    # ==========================================
    def process_putaway_compare(self, ds_bytes: bytes, ds_name: str, asal_bytes: bytes, asal_name: str):
        try:
            df_ds = pd.read_excel(io.BytesIO(ds_bytes), engine="openpyxl") if ds_name.endswith(('.xlsx', '.xls')) else pd.read_csv(io.BytesIO(ds_bytes))
            df_asal = pd.read_excel(io.BytesIO(asal_bytes), engine="openpyxl") if asal_name.endswith(('.xlsx', '.xls')) else pd.read_csv(io.BytesIO(asal_bytes))

            df_asal_updated = df_asal.copy()
            self.putaway_qty_system.set(int(pd.to_numeric(df_asal_updated.iloc[:, 9], errors='coerce').sum()))

            def get_col_idx(df_target, keywords, default_idx):
                for i, col in enumerate(df_target.columns):
                    if any(k.lower() in str(col).lower() for k in keywords): return i
                return default_idx

            c_bin_a = get_col_idx(df_asal, ['bin', 'lokasi'], 1)
            c_sku_a = get_col_idx(df_asal, ['sku', 'item code'], 2)
            c_qty_a = get_col_idx(df_asal, ['qty system', 'quantity', 'stok'], 9)

            c_bin_d = get_col_idx(df_ds, ['bin', 'tujuan'], 0)
            c_sku_d = get_col_idx(df_ds, ['sku', 'item'], 1)
            c_qty_d = get_col_idx(df_ds, ['qty', 'jumlah'], 2)

            bin_qty_dict = {}
            for _, row in df_asal_updated.iterrows():
                try:
                    key = f"{str(row.iloc[c_bin_a])}|{str(row.iloc[c_sku_a])}"
                    qty = pd.to_numeric(row.iloc[c_qty_a], errors='coerce')
                    bin_qty_dict[key] = qty if pd.notna(qty) else 0
                except: continue

            out_data = []
            for _, row in df_ds.iterrows():
                try:
                    sku = str(row.iloc[c_sku_d])
                    diff_qty = pd.to_numeric(row.iloc[c_qty_d], errors='coerce')
                    if pd.isna(diff_qty) or diff_qty <= 0: continue

                    bin_tujuan = str(row.iloc[c_bin_d])
                    rem = int(diff_qty)

                    patterns = ["STAGING LT.3", "STAGGING LT.3", "STAGING", "STAGGING", "KARANTINA", "NORMAL"]
                    for pattern in patterns:
                        if rem <= 0: break
                        for key in list(bin_qty_dict.keys()):
                            qty_avail = bin_qty_dict[key]
                            if qty_avail <= 0: continue
                            b_name, s_name = key.split("|")
                            if s_name != sku: continue

                            match = False
                            if pattern == "NORMAL":
                                if not any(x in b_name.upper() for x in ["STAG", "KARANTINA"]): match = True
                            else:
                                if pattern in b_name.upper(): match = True

                            if match:
                                take = min(rem, qty_avail)
                                bin_qty_dict[key] -= take
                                rem -= take
                                out_data.append([bin_tujuan, sku, int(diff_qty), b_name, take, rem, "FULLY SETUP" if rem == 0 else "PARTIAL SETUP"])
                                if rem <= 0: break

                    if rem > 0:
                        out_data.append([bin_tujuan, sku, int(diff_qty), "(NO BIN)", 0, rem, "PERLU CARI STOCK MANUAL"])
                except: continue

            df_comp = pd.DataFrame(out_data, columns=["BIN ASAL", "SKU", "QTY PUTAWAY", "BIN DITEMUKAN", "QUANTITY", "DIFF", "STATUS"])

            for idx in df_asal_updated.index:
                key = f"{str(df_asal_updated.iloc[idx, c_bin_a])}|{str(df_asal_updated.iloc[idx, c_sku_a])}"
                if key in bin_qty_dict:
                    df_asal_updated.iloc[idx, c_qty_a] = bin_qty_dict[key]

            df_plist = df_comp[df_comp['STATUS'].str.contains("SETUP")].copy()
            if not df_plist.empty:
                df_plist = df_plist.rename(columns={"BIN DITEMUKAN": "BIN AWAL", "BIN ASAL": "BIN TUJUAN"})
                df_plist = df_plist[["BIN AWAL", "BIN TUJUAN", "SKU", "QUANTITY", "STATUS"]]