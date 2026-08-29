import io
import time
from datetime import datetime
import pandas as pd
from shiny import reactive
from config import get_supabase, safe_int, load_data_from_info

class AppState:
    def __init__(self):
        # Navigation & Role
        self.logged_in = reactive.Value(False)
        self.role = reactive.Value("DC")
        self.branch = reactive.Value("SURABAYA")
        self.user_display_name = reactive.Value("")
        self.username = reactive.Value("")
        self.password = reactive.Value("")
        self.login_timestamp_ms = reactive.Value(0)
        self.main_menu = reactive.Value("Database Ongkir In/Out")
        

        # Sidebar Dropdowns
        self.sidebar_open = reactive.Value(True)
        self.dropdown_operational = reactive.Value(True)
        self.dropdown_inventory = reactive.Value(False)
        self.dropdown_reject = reactive.Value(False)
        self.dropdown_extras = reactive.Value(False)

        # Modals
        self.is_info_open = reactive.Value(False)
        self.show_success_modal = reactive.Value(False)
        self.show_error_modal = reactive.Value(False)
        self.error_modal_message = reactive.Value("")

        # Database Ongkir
        self.data_list = reactive.Value([])
        self.input_supplier = reactive.Value("")
        self.input_ekspedisi = reactive.Value("")
        self.input_koli = reactive.Value("1")
        self.input_ongkir = reactive.Value("0")
        self.input_tgl = reactive.Value(datetime.now().strftime("%Y-%m-%d"))
        self.filter_ekspedisi = reactive.Value("SEMUA")
        self.selected_ids = reactive.Value([])
        self.show_delete_modal = reactive.Value(False)

        # Stock Minus
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

        # Putaway System
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

        # Compare System
        self.compare_sys_processed = reactive.Value(False)
        self.cs_total_checked = reactive.Value(0)
        self.cs_total_diff = reactive.Value(0)
        self.cs_match_count = reactive.Value(0)
        self.cs_unmatch_count = reactive.Value(0)
        self.cs_no_sales_count = reactive.Value(0)
        self.df_cs_headers = reactive.Value([])
        self.df_cs_rows = reactive.Value([])
        self._raw_df_cs_all = pd.DataFrame()
        self._raw_df_cs_diff = pd.DataFrame()

        #list bin cycle count
        # --- CYCLE COUNT STATE ---
        self.cc_processed = reactive.Value(False)
        self.cc_list_sub = reactive.Value([])
        self.cc_list_brand = reactive.Value([])
        self.cc_list_tier = reactive.Value([])
        self.cc_total_bin = reactive.Value(0)
        self.cc_total_sku = reactive.Value(0)
        self.cc_total_qty = reactive.Value(0)
        self.df_cc_headers = reactive.Value([])
        self.df_cc_rows = reactive.Value([])
        self._raw_df_cc_base = pd.DataFrame()
        self._raw_df_cc_filtered = pd.DataFrame()
        self._cc_col_mapping = {}

        # --- PUTAWAY & PICKING AUDIT STATE ---
        self.ppa_processed = reactive.Value(False)
        self.ppa_total_picking_qty = reactive.Value(0)
        self.ppa_unique_picking_bin = reactive.Value(0)
        self.ppa_unique_putaway_bin = reactive.Value(0)
        self.ppa_final_matching_bin = reactive.Value(0)

        self.df_ppa_picking_headers = reactive.Value([])
        self.df_ppa_picking_rows = reactive.Value([])
        self.df_ppa_upicking_headers = reactive.Value([])
        self.df_ppa_upicking_rows = reactive.Value([])
        self.df_ppa_putaway_headers = reactive.Value([])
        self.df_ppa_putaway_rows = reactive.Value([])
        self.df_ppa_uputaway_headers = reactive.Value([])
        self.df_ppa_uputaway_rows = reactive.Value([])
        self.df_ppa_final_headers = reactive.Value([])
        self.df_ppa_final_rows = reactive.Value([])

        self._raw_df_ppa_picking = pd.DataFrame()
        self._raw_df_ppa_upicking = pd.DataFrame()
        self._raw_df_ppa_putaway = pd.DataFrame()
        self._raw_df_ppa_uputaway = pd.DataFrame()
        self._raw_df_ppa_final = pd.DataFrame()

    def set_main_menu(self, menu: str): self.main_menu.set(menu)
    def toggle_sidebar(self): self.sidebar_open.set(not self.sidebar_open())
    def toggle_dropdown(self, key: str):
        if key == "operational": self.dropdown_operational.set(not self.dropdown_operational())
        elif key == "inventory": self.dropdown_inventory.set(not self.dropdown_inventory())
        elif key == "reject": self.dropdown_reject.set(not self.dropdown_reject())
        elif key == "extras": self.dropdown_extras.set(not self.dropdown_extras())

    def handle_login(self, u: str, p: str):
        u, p = u.strip(), p.strip()
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
        return False, "Username atau Password salah! Periksa kembali."

    def logout(self):
        self.logged_in.set(False)
        self.username.set("")
        self.password.set("")
        self.role.set("DC")
        self.login_timestamp_ms.set(0)

    def get_menu_operational(self) -> list[str]:
        if self.role() == "DC":
            return ["Purchase Order Receiving", "Putaway System", "Scan Out Validation", "Refill & Overstock", "Refill & Withdraw", "Compare RTO", "Compare Penerimaan RTO", "FDR Update"]
        return ["Compare Penerimaan RTO", "Putaway System", "Purchase Order Receiving"]

    def get_menu_inventory(self) -> list[str]:
        if self.role() == "DC":
            return ["Stock Opname", "Match Real & System", "Compare System", "Cycle Count", "Putaway & Picking Audit List", "List Bin Cycle Count", "Stock Tracking Timeline", "Justification SO", "Stock Minus", "List Retur Out", "Pengajuan Mutasi Karantina", "Refill Koli to Koli/Refill", "Stock Allocation"]
        return ["Stock Minus", "Cycle Count", "Compare System", "Justification SO"]

    def get_menu_reject(self) -> list[str]:
        return ["Pengajuan Reject/Defect", "Reject/Defect List"]

    def get_menu_extras(self) -> list[str]:
        if self.role() == "DC":
            return ["Logistic Schedule", "Balancing Stock", "Reporting & PIC", "Data Timbang Ongkir", "Database Ongkir In/Out", "Precentage Display", "Precentage Request FL to Store Stock", "Refill Toko"]
        return ["Precentage Display", "Refill Toko", "Store Leader RTO Decission"]

    def get_active_content_type(self) -> str:
        cur_menu = self.main_menu()
        if cur_menu in ["Database Ongkir In/Out", "Database Ongkir", "dashboard_ongkir"]:
            return "dashboard_ongkir"
        elif cur_menu == "Stock Minus": return "stock_minus"
        elif cur_menu == "Putaway System": return "putaway_system"
        elif cur_menu == "Compare System": return "compare_system"
        elif cur_menu == "List Bin Cycle Count": return "cycle_count"
        elif cur_menu in ["Putaway & Picking Audit List", "Putaway & Picking Audit"]: return "ppa_audit"
        return "under_development"

    # --- Ongkir Methods ---
    def load_ongkir_data(self):
        try:
            client = get_supabase()
            if client:
                res = client.table("shipping_costs").select("*").execute()
                self.data_list.set(res.data if res.data else [])
        except Exception as e: print("Supabase load error:", e)

    def save_single_ongkir(self, supp: str, eksp: str, koli_str: str, ongkir_str: str, tgl_str: str):
        if not supp.strip(): return False, "Nama Supplier Wajib Diisi!"
        payload = {
            "supplier": supp.upper().strip(), "ekspedisi": eksp.upper().strip(),
            "total_koli": safe_int(koli_str, 0), "total_ongkir": safe_int(ongkir_str, 0),
            "created_at": f"{tgl_str} {datetime.now().strftime('%H:%M:%S')}"
        }
        try:
            client = get_supabase()
            if client: client.table("shipping_costs").insert(payload).execute()
            self.load_ongkir_data()
            return True, "✅ Data Berhasil Disimpan!"
        except Exception as e: return False, f"Gagal Simpan: {e}"

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
                tgl_raw = row["TANGGAL_JAM"]
                fix_dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S") if pd.isna(tgl_raw) else str(tgl_raw)
                batch_data.append({"supplier": sup, "ekspedisi": eks, "total_koli": safe_int(row.get("TOTAL KOLI", 0)), "total_ongkir": safe_int(row.get("ONGKIR", 0)), "created_at": fix_dt})
            if batch_data:
                client = get_supabase()
                if client: client.table("shipping_costs").insert(batch_data).execute()
                self.load_ongkir_data()
                return True, f"🚀 Berhasil Upload {len(batch_data)} Data CSV!"
            return False, "Tidak ada data valid yang diupload."
        except Exception as e: return False, f"Gagal Upload Batch: {e}"

    def toggle_select_id(self, item_id: str):
        s = list(self.selected_ids())
        if item_id in s: s.remove(item_id)
        else: s.append(item_id)
        self.selected_ids.set(s)

    def execute_delete(self):
        s = self.selected_ids()
        try:
            client = get_supabase()
            if client: client.table("shipping_costs").delete().in_("id", s).execute()
            self.selected_ids.set([])
            self.show_delete_modal.set(False)
            self.load_ongkir_data()
            return True, "🗑️ Data Berhasil Dihapus!"
        except Exception as e: return False, f"Gagal Hapus: {e}"

    def get_filtered_ongkir(self) -> list[dict]:
        res = self.data_list()
        flt = self.filter_ekspedisi()
        if flt != "SEMUA":
            res = [x for x in res if str(x.get("ekspedisi", "")).upper() == flt.upper()]
        return res

    def get_list_ekspedisi_options(self) -> list[str]:
        eksp = list(set([str(x.get("ekspedisi", "")).upper() for x in self.data_list() if x.get("ekspedisi")]))
        return ["SEMUA"] + sorted(eksp)

    def metric_total_biaya_all(self) -> str: return f"Rp {sum([safe_int(x.get('total_ongkir', 0)) for x in self.get_filtered_ongkir()]):,.0f}"
    def metric_total_koli_all(self) -> str: return f"{sum([safe_int(x.get('total_koli', x.get('koli', 0))) for x in self.get_filtered_ongkir()]):,.0f} Koli"
    def metric_avg_cost_all(self) -> str:
        data = self.get_filtered_ongkir()
        biaya = sum([safe_int(x.get("total_ongkir", 0)) for x in data])
        koli = sum([safe_int(x.get("total_koli", x.get("koli", 0))) for x in data])
        return f"Rp {(biaya / koli) if koli > 0 else 0:,.0f}"
    def metric_biaya_datang(self) -> str: return f"Rp {sum([safe_int(x.get('total_ongkir', 0)) for x in self.get_filtered_ongkir() if 'RTO' not in str(x.get('supplier', ''))]):,.0f}"
    def metric_koli_datang(self) -> str: return f"{sum([safe_int(x.get('total_koli', x.get('koli', 0))) for x in self.get_filtered_ongkir() if 'RTO' not in str(x.get('supplier', ''))]):,.0f} Koli"
    def metric_biaya_rto(self) -> str: return f"Rp {sum([safe_int(x.get('total_ongkir', 0)) for x in self.get_filtered_ongkir() if 'RTO' in str(x.get('supplier', ''))]):,.0f}"

    # --- Stock Minus Processing ---
    def process_stock_minus_file(self, file_bytes: bytes, file_name: str):
        try:
            df = pd.read_excel(io.BytesIO(file_bytes), engine="openpyxl") if file_name.endswith(('.xlsx', '.xls')) else pd.read_csv(io.BytesIO(file_bytes))
            df.columns = [str(c).strip().upper() for c in df.columns]
            col_sku, col_bin = 'SKU', 'BIN'
            col_qty = next((c for c in df.columns if 'QTY SYSTEM' in c or 'QTY SYS' in c), None)
            if col_qty is None: return False, "Kolom 'QTY SYSTEM' tidak ditemukan!"

            df[col_qty] = pd.to_numeric(df[col_qty], errors='coerce').fillna(0)
            df[col_sku] = df[col_sku].astype(str).str.strip().str.upper()
            df[col_bin] = df[col_bin].astype(str).str.strip().str.upper()

            df_minus_awal, df_positif = df[df[col_qty] < 0].copy(), df[df[col_qty] > 0]
            inventory = {}
            for _, row in df_positif.iterrows():
                sku, bn, qt = row[col_sku], row[col_bin], row[col_qty]
                if sku not in inventory: inventory[sku] = {}
                inventory[sku][bn] = inventory[sku].get(bn, 0) + qt

            prior_bins = ["RAK ACC LT.1", "STAGGING INBOUND", "STAGGING OUTBOUND", "KARANTINA DC", "KARANTINA STORE 02", "STAGGING REFUND", "STAGING GAGAL QC", "STAGGING LT.3", "STAGGING OUTBOUND SEMARANG", "STAGGING OUTBOUND SIDOARJO", "STAGGING LT.2", "LT.4"]
            set_up_results, df_need_adj_list = [], []

            for _, row in df_minus_awal.iterrows():
                sku, bin_asal = row[col_sku], row[col_bin]
                sisa_minus = abs(row[col_qty])
                if sku in inventory and any(v > 0 for v in inventory[sku].values()):
                    sku_stock = inventory[sku]
                    while sisa_minus > 0:
                        bin_solusi = ""
                        if bin_asal == "TOKO":
                            if sku_stock.get("STAGGING LT.2", 0) > 0: bin_solusi = "STAGGING LT.2"
                            elif sku_stock.get("LT.2", 0) > 0: bin_solusi = "LT.2"
                        elif bin_asal in ["STAGGING LT.2", "LT.2"] and sku_stock.get("TOKO", 0) > 0: bin_solusi = "TOKO"
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
                            set_up_results.append({"BIN AWAL": bin_solusi, "BIN TUJUAN": bin_asal, "SKU": sku, "QUANTITY": ambil, "NOTES": "STOCK MINUS"})
                            sku_stock[bin_solusi] -= ambil
                            sisa_minus -= ambil
                if sisa_minus > 0:
                    row_adj = row.to_dict()
                    row_adj[col_qty] = -sisa_minus
                    df_need_adj_list.append(row_adj)

            df_s, df_n = pd.DataFrame(set_up_results), pd.DataFrame(df_need_adj_list)
            self.total_qty_minus.set(int(abs(pd.to_numeric(df_minus_awal[col_qty], errors='coerce').sum())))
            self.total_tercover.set(int(df_s["QUANTITY"].sum()) if not df_s.empty else 0)
            self.total_sisa_adj.set(int(abs(df_n[col_qty].sum())) if not df_n.empty and col_qty in df_n.columns else 0)
            self._raw_df_minus_awal, self._raw_df_set_up, self._raw_df_need_adj = df_minus_awal, df_s, df_n
            self.df_minus_awal_headers.set(df_minus_awal.columns.tolist() if not df_minus_awal.empty else [])
            self.df_minus_awal_rows.set(df_minus_awal.fillna("").astype(str).values.tolist() if not df_minus_awal.empty else [])
            self.df_set_up_headers.set(df_s.columns.tolist() if not df_s.empty else [])
            self.df_set_up_rows.set(df_s.fillna("").astype(str).values.tolist() if not df_s.empty else [])
            self.df_need_adj_headers.set(df_n.columns.tolist() if not df_n.empty else [])
            self.df_need_adj_rows.set(df_n.fillna("").astype(str).values.tolist() if not df_n.empty else [])
            self.stock_minus_processed.set(True)
            return True, "Data Stock Minus berhasil diproses!"
        except Exception as e: return False, f"Gagal memproses file: {e}"

    # --- Putaway Compare Processing ---
    def process_putaway_compare(self, ds_bytes: bytes, ds_name: str, asal_bytes: bytes, asal_name: str):
        try:
            df_ds = pd.read_excel(io.BytesIO(ds_bytes), engine="openpyxl") if ds_name.endswith(('.xlsx', '.xls')) else pd.read_csv(io.BytesIO(ds_bytes))
            df_asal = pd.read_excel(io.BytesIO(asal_bytes), engine="openpyxl") if asal_name.endswith(('.xlsx', '.xls')) else pd.read_csv(io.BytesIO(ds_bytes))
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
                    bin_tujuan, rem = str(row.iloc[c_bin_d]), int(diff_qty)
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
                    if rem > 0: out_data.append([bin_tujuan, sku, int(diff_qty), "(NO BIN)", 0, rem, "PERLU CARI STOCK MANUAL"])
                except: continue

            df_comp = pd.DataFrame(out_data, columns=["BIN ASAL", "SKU", "QTY PUTAWAY", "BIN DITEMUKAN", "QUANTITY", "DIFF", "STATUS"])
            for idx in df_asal_updated.index:
                key = f"{str(df_asal_updated.iloc[idx, c_bin_a])}|{str(df_asal_updated.iloc[idx, c_sku_a])}"
                if key in bin_qty_dict: df_asal_updated.iloc[idx, c_qty_a] = bin_qty_dict[key]

            df_plist = df_comp[df_comp['STATUS'].str.contains("SETUP")].copy()
            if not df_plist.empty:
                df_plist = df_plist.rename(columns={"BIN DITEMUKAN": "BIN AWAL", "BIN ASAL": "BIN TUJUAN"})
                df_plist = df_plist[["BIN AWAL", "BIN TUJUAN", "SKU", "QUANTITY", "STATUS"]]
                df_plist.columns = ["BIN AWAL", "BIN TUJUAN", "SKU", "QUANTITY", "NOTES"]
                df_plist['NOTES'] = "PUTAWAY"
            else: df_plist = pd.DataFrame(columns=["BIN AWAL", "BIN TUJUAN", "SKU", "QUANTITY", "NOTES"])

            df_kurang = df_comp[df_comp['STATUS'] == "PERLU CARI STOCK MANUAL"].copy()
            area = self.area_putaway()
            if area == "DC LANTAI 1": kw_out = ["GL1-DC-PUTAWAY", "STAG"]
            elif area == "DC LANTAI 2": kw_out = ["GL2-DC-PUTAWAY", "STAG"]
            elif area == "DC LANTAI 3": kw_out = ["GL3-DC-PUTAWAY", "STAG"]
            elif area == "JERSEY ZONE": kw_out = ["JZ-PUTAWAY", "STAG"]
            else: kw_out = ["STAG", "PUTAWAY"]

            bin_series = df_asal_updated.iloc[:, c_bin_a].astype(str).str.upper()
            mask_kw = bin_series.str.contains(kw_out[0], na=False)
            for kw in kw_out[1:]: mask_kw = mask_kw | bin_series.str.contains(kw, na=False)
            mask_out = (pd.to_numeric(df_asal_updated.iloc[:, c_qty_a], errors='coerce') > 0) & mask_kw
            df_outstanding = df_asal_updated[mask_out].copy()

            self.putaway_total_setup.set(int(df_plist['QUANTITY'].sum()) if not df_plist.empty else 0)
            self.putaway_kurang_setup.set(int(df_kurang['DIFF'].sum()) if not df_kurang.empty else 0)
            sisa = 0
            if not df_outstanding.empty:
                qty_col = [c for c in df_outstanding.columns if 'qty' in str(c).lower()]
                if qty_col: sisa = int(pd.to_numeric(df_outstanding[qty_col[0]], errors='coerce').sum())
            self.putaway_sisa_stok.set(sisa)

            self._raw_df_comp, self._raw_df_plist = df_comp, df_plist
            self._raw_df_kurang, self._raw_df_out, self._raw_df_updated = df_kurang, df_outstanding, df_asal_updated
            self.df_comp_headers.set(df_comp.columns.tolist() if not df_comp.empty else [])
            self.df_comp_rows.set(df_comp.fillna("").astype(str).values.tolist() if not df_comp.empty else [])
            self.df_plist_headers.set(df_plist.columns.tolist() if not df_plist.empty else [])
            self.df_plist_rows.set(df_plist.fillna("").astype(str).values.tolist() if not df_plist.empty else [])
            self.df_kurang_headers.set(df_kurang.columns.tolist() if not df_kurang.empty else [])
            self.df_kurang_rows.set(df_kurang.fillna("").astype(str).values.tolist() if not df_kurang.empty else [])
            self.df_out_headers.set(df_outstanding.columns.tolist() if not df_outstanding.empty else [])
            self.df_out_rows.set(df_outstanding.fillna("").astype(str).values.tolist() if not df_outstanding.empty else [])
            self.putaway_processed.set(True)
            return True, "Compare Putaway berhasil diproses!"
        except Exception as e: return False, f"Gagal memproses file Putaway: {e}"

    # --- Compare System Processing (Streamlit Logic) ---
    def process_compare_system(self, f_sys1, f_sys2, f_track=None, f_po=None, f_rto_in=None, f_rto_out=None, f_refund=None):
        try:
            df1, df2 = load_data_from_info(f_sys1), load_data_from_info(f_sys2)
            if df1.empty or df2.empty: return False, "File Stock System Start Shift atau End Shift tidak boleh kosong!"

            def prepare_sku_totals(df):
                if df.empty: return pd.DataFrame(columns=['SKU', 'QTY'])
                df_clean = df.copy()
                if df_clean.shape[1] < 10: raise ValueError("File System kurang dari 10 kolom (Kolom J tidak ada).")
                df_mapped = pd.DataFrame({
                    'SKU': df_clean.iloc[:, 2].astype(str).str.strip().str.upper(),
                    'QTY': pd.to_numeric(df_clean.iloc[:, 9], errors='coerce').fillna(0)
                })
                return df_mapped.groupby('SKU', as_index=False)['QTY'].sum()

            data1, data2 = prepare_sku_totals(df1), prepare_sku_totals(df2)
            if data1.empty or data2.empty: return False, "Data SKU di File Utama kosong setelah diparsing!"

            data1['SKU'] = data1['SKU'].astype(str).str.strip().str.upper()
            data2['SKU'] = data2['SKU'].astype(str).str.strip().str.upper()
            comparison = pd.merge(data1, data2, on='SKU', how='outer', suffixes=('_Sys1', '_Sys2')).fillna(0)
            comparison = comparison[(comparison['QTY_Sys1'] >= 0) & (comparison['QTY_Sys2'] >= 0)].copy()
            comparison['DIFF'] = comparison['QTY_Sys1'] - comparison['QTY_Sys2']
            discrepancies = comparison[comparison['DIFF'] != 0].copy()

            df_track_clean = pd.DataFrame(columns=['INVOICE', 'SKU', 'BIN', 'QTY'])
            if f_track and not discrepancies.empty:
                df_track = load_data_from_info(f_track)
                if not df_track.empty and df_track.shape[1] >= 11:
                    df_track_clean = pd.DataFrame({
                        'INVOICE': df_track.iloc[:, 0].astype(str).str.strip(),
                        'SKU': df_track.iloc[:, 1].astype(str).str.strip().str.upper(),
                        'BIN': df_track.iloc[:, 6].astype(str).str.strip().str.upper(),
                        'QTY': pd.to_numeric(df_track.iloc[:, 10], errors='coerce').fillna(0)
                    })

            df_rto_out_clean = pd.DataFrame(columns=['NO_TF', 'SKU', 'QTY'])
            if f_rto_out and not discrepancies.empty:
                df_rto_out_df = load_data_from_info(f_rto_out)
                if not df_rto_out_df.empty and df_rto_out_df.shape[1] >= 8:
                    df_rto_out_clean = pd.DataFrame({
                        'NO_TF': df_rto_out_df.iloc[:, 0].astype(str).str.strip(),
                        'SKU': df_rto_out_df.iloc[:, 3].astype(str).str.strip().str.upper(),
                        'QTY': pd.to_numeric(df_rto_out_df.iloc[:, 7], errors='coerce').fillna(0)
                    })

            df_po_clean = pd.DataFrame(columns=['NO_PO', 'SKU', 'QTY'])
            if f_po and not discrepancies.empty:
                df_po = load_data_from_info(f_po)
                if not df_po.empty and df_po.shape[1] >= 13:
                    df_po_clean = pd.DataFrame({
                        'NO_PO': df_po.iloc[:, 0].astype(str).str.strip(),
                        'SKU': df_po.iloc[:, 4].astype(str).str.strip().str.upper(),
                        'QTY': pd.to_numeric(df_po.iloc[:, 12], errors='coerce').fillna(0)
                    })

            df_rto_in_clean = pd.DataFrame(columns=['NO_TF', 'SKU', 'QTY'])
            if f_rto_in and not discrepancies.empty:
                df_rto_in_df = load_data_from_info(f_rto_in)
                if not df_rto_in_df.empty and df_rto_in_df.shape[1] >= 8:
                    df_rto_in_clean = pd.DataFrame({
                        'NO_TF': df_rto_in_df.iloc[:, 0].astype(str).str.strip(),
                        'SKU': df_rto_in_df.iloc[:, 3].astype(str).str.strip().str.upper(),
                        'QTY': pd.to_numeric(df_rto_in_df.iloc[:, 7], errors='coerce').fillna(0)
                    })

            df_refund_clean = pd.DataFrame(columns=['SKU', 'QTY'])
            if f_refund and not discrepancies.empty:
                df_refund_df = load_data_from_info(f_refund)
                if not df_refund_df.empty and df_refund_df.shape[1] >= 11:
                    df_refund_clean = pd.DataFrame({
                        'SKU': df_refund_df.iloc[:, 3].astype(str).str.strip().str.upper(),
                        'QTY': pd.to_numeric(df_refund_df.iloc[:, 10], errors='coerce').fillna(0)
                    })

            status_list, doc_reference_list, track_bin_list, total_found_qty_list = [], [], [], []

            for idx, row in discrepancies.iterrows():
                target_sku, actual_diff = str(row['SKU']).strip().upper(), row['DIFF']
                needed_qty = abs(actual_diff)
                docs_found, bins_found, accumulated_qty = [], [], 0

                if actual_diff < 0:
                    if not df_po_clean.empty:
                        match_po = df_po_clean[df_po_clean['SKU'] == target_sku]
                        if not match_po.empty:
                            docs_found.append(f"PO:{'/'.join(map(str, match_po['NO_PO'].unique()))}")
                            accumulated_qty += match_po['QTY'].sum()
                    if not df_rto_in_clean.empty:
                        match_rto_in = df_rto_in_clean[df_rto_in_clean['SKU'] == target_sku]
                        if not match_rto_in.empty:
                            docs_found.append(f"RTO_IN:{'/'.join(map(str, match_rto_in['NO_TF'].unique()))}")
                            accumulated_qty += match_rto_in['QTY'].sum()
                    if not df_refund_clean.empty:
                        match_refund = df_refund_clean[df_refund_clean['SKU'] == target_sku]
                        if not match_refund.empty:
                            docs_found.append("REFUND:Found")
                            accumulated_qty += match_refund['QTY'].sum()

                    if accumulated_qty == 0: final_status = "PENAMBAHAN STOK (NO HISTORY)"
                    elif accumulated_qty >= needed_qty: final_status = "DONE MASUK"
                    else: final_status = "MASUK QTY MISSMATCH"
                    track_bin_list.append("-")
                else:
                    if not df_track_clean.empty:
                        match_track = df_track_clean[df_track_clean['SKU'] == target_sku]
                        if not match_track.empty:
                            docs_found.append(f"TRACK:{'/'.join(map(str, match_track['INVOICE'].unique()))}")
                            if match_track['BIN'].any(): bins_found.append("/".join(map(str, match_track['BIN'].unique())))
                            accumulated_qty += match_track['QTY'].sum()
                    if not df_rto_out_clean.empty:
                        match_rto_out = df_rto_out_clean[df_rto_out_clean['SKU'] == target_sku]
                        if not match_rto_out.empty:
                            docs_found.append(f"RTO_OUT:{'/'.join(map(str, match_rto_out['NO_TF'].unique()))}")
                            bins_found.append("RTO_OUT")
                            accumulated_qty += match_rto_out['QTY'].sum()

                    if accumulated_qty == 0: final_status = "NO SALES (PERLU CEK ADJ)"
                    elif accumulated_qty >= needed_qty: final_status = "DONE TERJUAL"
                    else: final_status = "KELUAR QTY MISSMATCH"
                    track_bin_list.append(", ".join(bins_found) if bins_found else "-")

                status_list.append(final_status)
                doc_reference_list.append(", ".join(docs_found) if docs_found else "-")
                total_found_qty_list.append(accumulated_qty)

            discrepancies['TRACK_INVOICE'] = doc_reference_list
            discrepancies['TRACK_BIN'] = track_bin_list
            discrepancies['TRACK_QTY'] = total_found_qty_list
            discrepancies['STATUS_CHECK'] = status_list

            self.cs_total_checked.set(len(comparison))
            self.cs_total_diff.set(len(discrepancies))
            if not discrepancies.empty and 'STATUS_CHECK' in discrepancies.columns:
                self.cs_match_count.set(len(discrepancies[discrepancies['STATUS_CHECK'].isin(["DONE MASUK", "DONE TERJUAL"])]))
                self.cs_unmatch_count.set(len(discrepancies[discrepancies['STATUS_CHECK'].isin(["MASUK QTY MISSMATCH", "KELUAR QTY MISSMATCH"])]))
                self.cs_no_sales_count.set(len(discrepancies[discrepancies['STATUS_CHECK'].isin(["PENAMBAHAN STOK (NO HISTORY)", "NO SALES (PERLU CEK ADJ)"])]))
            else:
                self.cs_match_count.set(0)
                self.cs_unmatch_count.set(0)
                self.cs_no_sales_count.set(0)
# Tambahkan fungsi format angka pintar:
            def format_smart_num(val):
                try:
                    if pd.isna(val) or val is None or val == "":
                        return ""
                    f_val = float(val)
                    # Jika angka bulat (misal 1.0, 25.0) -> ubah jadi integer '1', '25'
                    if f_val.is_integer():
                        return str(int(f_val))
                    # Jika ada komanya (misal 1.5, 2.75) -> pertahankan komanya
                    return f"{f_val:g}"
                except (ValueError, TypeError):
                    return str(val)

            ordered_cols = ['SKU', 'QTY_Sys1', 'QTY_Sys2', 'DIFF', 'TRACK_INVOICE', 'TRACK_BIN', 'TRACK_QTY', 'STATUS_CHECK']
            display_df = discrepancies[[c for c in ordered_cols if c in discrepancies.columns]].copy()

            # Bersihkan angka .0 di kolom QTY dan DIFF
            for col in ['QTY_Sys1', 'QTY_Sys2', 'DIFF', 'TRACK_QTY']:
                if col in display_df.columns:
                    display_df[col] = display_df[col].apply(format_smart_num)

            self._raw_df_cs_all = comparison
            self._raw_df_cs_diff = display_df
            self.df_cs_headers.set(display_df.columns.tolist() if not display_df.empty else [])
            self.df_cs_rows.set(display_df.fillna("").astype(str).values.tolist() if not display_df.empty else [])
            self.compare_sys_processed.set(True)
            return True, "Comparison Selesai!"
            
        except Exception as e: return False, f"Terjadi Kesalahan: {e}"


    # --- LIST BIN CYCLE COUNT ---
    def process_cycle_count_file(self, file_bytes: bytes, file_name: str):
        try:
            df_raw = pd.read_excel(io.BytesIO(file_bytes), engine="openpyxl") if file_name.endswith(('.xlsx', '.xls')) else pd.read_csv(io.BytesIO(file_bytes))
            if df_raw.shape[1] < 10:
                return False, "⚠️ File kurang dari 10 kolom! Pastikan format file sesuai (Kolom B, C, G, J)."

            df_scan = df_raw.copy()
            col_bin = df_raw.columns[1]
            col_sku = df_raw.columns[2]
            col_item = df_raw.columns[4]
            col_variant = df_raw.columns[5]
            col_sub = df_raw.columns[6]
            col_harga = df_raw.columns[7]
            col_qty = df_raw.columns[9]

            brand_col = [col for col in df_raw.columns if 'BRAND' in str(col).upper()]
            col_brand = brand_col[0] if brand_col else "BRAND"
            if not brand_col:
                df_scan["BRAND"] = "UNKNOWN"

            df_scan[col_bin] = df_scan[col_bin].astype(str).str.strip()
            df_scan[col_sku] = df_scan[col_sku].astype(str).str.strip()
            df_scan[col_item] = df_scan[col_item].astype(str).str.strip().str.upper()
            df_scan[col_variant] = df_scan[col_variant].astype(str).str.strip().str.upper()
            df_scan[col_sub] = df_scan[col_sub].astype(str).str.strip().str.upper()
            df_scan[col_brand] = df_scan[col_brand].astype(str).str.strip().str.upper()
            df_scan[col_qty] = pd.to_numeric(df_scan[col_qty], errors='coerce').fillna(0).astype(int)
            df_scan["HARGA_NUMERIC"] = pd.to_numeric(df_scan[col_harga], errors='coerce').fillna(0)

            # Tiering Harga
            kondisi = [
                (df_scan["HARGA_NUMERIC"] >= 1000000),
                (df_scan["HARGA_NUMERIC"] >= 700000) & (df_scan["HARGA_NUMERIC"] < 1000000),
                (df_scan["HARGA_NUMERIC"] >= 400000) & (df_scan["HARGA_NUMERIC"] < 700000),
                (df_scan["HARGA_NUMERIC"] >= 100000) & (df_scan["HARGA_NUMERIC"] < 400000),
                (df_scan["HARGA_NUMERIC"] >= 0) & (df_scan["HARGA_NUMERIC"] < 100000)
            ]
            pilihan_tier = [
                "LUXURY TIER (>= 1 JUTA)",
                "TOP TIER (700 RIBU - < 1 JUTA)",
                "MID TIER (400 RIBU - < 700 RIBU)",
                "ENTRY TIER (100 RIBU - < 400 RIBU)",
                "MASS MARKET TIER (0 - < 100 RIBU)"
            ]
            df_scan["TIER_HARGA"] = np.select(kondisi, pilihan_tier, default="Tidak Terdefinisi")

            # Filter Block Bin
            kata_kunci_block = "DEFECT|REJECT|KARANTINA|STAG|INB|OUT|PUTAWAY"
            df_scan = df_scan[~df_scan[col_bin].str.contains(kata_kunci_block, case=False, na=False)]

            # Simpan Opsi Filter
            list_sub = sorted([str(x).strip().upper() for x in df_scan[col_sub].unique() if pd.notna(x) and str(x).strip() != '' and str(x).upper() != 'NAN'])
            list_brand = sorted([str(x).strip().upper() for x in df_scan[col_brand].unique() if pd.notna(x) and str(x).strip() != '' and str(x).upper() != 'NAN'])
            tier_unik = df_scan["TIER_HARGA"].unique()
            list_tier = [t for t in pilihan_tier if t in tier_unik]

            self.cc_list_sub.set(list_sub)
            self.cc_list_brand.set(list_brand)
            self.cc_list_tier.set(list_tier)

            self._cc_col_mapping = {
                "bin": col_bin, "sku": col_sku, "qty": col_qty,
                "sub": col_sub, "brand": col_brand, "cols_asli": list(df_raw.columns)
            }
            self._raw_df_cc_base = df_scan
            self.apply_cc_filters([], [], [])
            self.cc_processed.set(True)
            return True, "Data Cycle Count Berhasil Diproses!"
        except Exception as e:
            return False, f"Terjadi kesalahan saat memproses data: {e}"

    def apply_cc_filters(self, selected_sub, selected_brand, selected_tier):
        if self._raw_df_cc_base.empty:
            return
        df = self._raw_df_cc_base.copy()
        cols = self._cc_col_mapping

        if selected_sub and len(selected_sub) > 0:
            df = df[df[cols["sub"]].isin(selected_sub)]
        if selected_brand and len(selected_brand) > 0:
            df = df[df[cols["brand"]].isin(selected_brand)]
        if selected_tier and len(selected_tier) > 0:
            df = df[df["TIER_HARGA"].isin(selected_tier)]

        total_bin = df[cols["bin"]].nunique() if not df.empty else 0
        unique_sku = df[cols["sku"]].nunique() if not df.empty else 0
        total_qty = int(df[cols["qty"]].sum()) if not df.empty else 0

        self.cc_total_bin.set(total_bin)
        self.cc_total_sku.set(unique_sku)
        self.cc_total_qty.set(total_qty)

        cols_asli = [c for c in cols["cols_asli"] if c in df.columns]
        display_df = df[cols_asli].copy()

        self._raw_df_cc_filtered = display_df
        self.df_cc_headers.set(display_df.columns.tolist() if not display_df.empty else [])
        self.df_cc_rows.set(display_df.fillna("").astype(str).values.tolist() if not display_df.empty else [])

        # --- PUTAWAY & PICKING AUDIT ALGORITHM ---
    def process_ppa_audit(self, f_sales, f_rto, f_mutasi):
        try:
            if not f_sales and not f_rto and not f_mutasi:
                return False, "Harap upload setidaknya salah satu file (Sales, RTO, atau Mutasi)!"

            # 1. Olah Data Picking (Sales & RTO)
            combined_list = []
            if f_sales:
                df_s = load_data_from_info(f_sales)
                if not df_s.empty and df_s.shape[1] > 10:
                    df_sales = df_s.iloc[:, [1, 6, 10]].copy()
                    df_sales.columns = ['SKU', 'BIN', 'QTY']
                    df_sales['SKU'] = df_sales['SKU'].astype(str).str.strip().str.upper()
                    df_sales['BIN'] = df_sales['BIN'].astype(str).str.strip().str.upper()
                    df_sales['QTY'] = pd.to_numeric(df_sales['QTY'], errors='coerce').fillna(0).astype(int)
                    df_sales = df_sales[(df_sales['SKU'] != '') & (df_sales['BIN'] != '') & (df_sales['SKU'] != 'SKU')]
                    df_sales = df_sales.groupby(['SKU', 'BIN'], as_index=False)['QTY'].sum()
                    df_sales['SOURCE'] = 'SALES'
                    combined_list.append(df_sales)

            if f_rto:
                df_r = load_data_from_info(f_rto)
                if not df_r.empty and df_r.shape[1] > 8:
                    df_rto = df_r.iloc[:, [3, 8, 7]].copy()
                    df_rto.columns = ['SKU', 'BIN', 'QTY']
                    df_rto['SKU'] = df_rto['SKU'].astype(str).str.strip().str.upper()
                    df_rto['BIN'] = df_rto['BIN'].astype(str).str.strip().str.upper()
                    df_rto['QTY'] = pd.to_numeric(df_rto['QTY'], errors='coerce').fillna(0).astype(int)
                    df_rto = df_rto[(df_rto['SKU'] != '') & (df_rto['BIN'] != '') & (df_rto['SKU'] != 'SKU')]
                    df_rto = df_rto.groupby(['SKU', 'BIN'], as_index=False)['QTY'].sum()
                    df_rto['SOURCE'] = 'RTO'
                    combined_list.append(df_rto)

            if combined_list:
                df_picking = pd.concat(combined_list, ignore_index=True)
                df_picking = df_picking[df_picking['QTY'] > 0].reset_index(drop=True)
            else:
                df_picking = pd.DataFrame(columns=['SKU', 'BIN', 'QTY', 'SOURCE'])

            # 2. Olah Data Putaway (Rantai Mutasi)
            if f_mutasi:
                df_m = load_data_from_info(f_mutasi)
                if not df_m.empty and df_m.shape[1] >= 13:
                    df_mutasi = df_m.iloc[:, [0, 3, 8, 12]].copy()
                    df_mutasi.columns = ['WAKTU', 'SKU', 'BIN AWAL', 'BIN TUJUAN']
                    df_mutasi['WAKTU'] = pd.to_datetime(df_mutasi['WAKTU'], errors='coerce')
                    df_mutasi['SKU'] = df_mutasi['SKU'].astype(str).str.strip().str.upper()
                    df_mutasi['BIN AWAL'] = df_mutasi['BIN AWAL'].astype(str).str.strip().str.upper()
                    df_mutasi['BIN TUJUAN'] = df_mutasi['BIN TUJUAN'].astype(str).str.strip().str.upper()
                    df_mutasi = df_mutasi.dropna(subset=['SKU'])
                    df_mutasi = df_mutasi[(df_mutasi['BIN AWAL'] != '') & (df_mutasi['BIN TUJUAN'] != '') & (df_mutasi['BIN AWAL'] != 'NAN') & (df_mutasi['BIN TUJUAN'] != 'NAN')]

                    # Process Mutation Chain
                    records = []
                    for sku, group in df_mutasi.groupby('SKU', sort=False):
                        group_sorted = group.sort_values(by='WAKTU', ascending=True)
                        active_chains = []
                        for idx, row in group_sorted.iterrows():
                            bin_awal, bin_tujuan = row['BIN AWAL'], row['BIN TUJUAN']
                            matched = False
                            for chain in active_chains:
                                if chain['current_bin'] == bin_awal:
                                    chain['current_bin'] = bin_tujuan
                                    chain['history'].append(bin_tujuan)
                                    matched = True
                                    break
                            if not matched:
                                active_chains.append({'current_bin': bin_tujuan, 'history': [bin_awal, bin_tujuan]})
                        for chain in active_chains:
                            records.append({
                                'SKU': sku,
                                'BIN AWAL': chain['history'][0],
                                'LAST BIN MUTASI': chain['current_bin'],
                                'TOTAL PERJALANAN': len(chain['history']) - 1,
                                'ALUR MUTASI': " ➔ ".join(chain['history'])
                            })
                    df_putaway = pd.DataFrame(records).drop_duplicates().reset_index(drop=True) if records else pd.DataFrame(columns=['SKU', 'BIN AWAL', 'LAST BIN MUTASI', 'TOTAL PERJALANAN', 'ALUR MUTASI'])
                else:
                    df_putaway = pd.DataFrame(columns=['SKU', 'BIN AWAL', 'LAST BIN MUTASI', 'TOTAL PERJALANAN', 'ALUR MUTASI'])
            else:
                df_putaway = pd.DataFrame(columns=['SKU', 'BIN AWAL', 'LAST BIN MUTASI', 'TOTAL PERJALANAN', 'ALUR MUTASI'])

            # 3. Unique BIN DataFrames
            df_upicking = pd.DataFrame({'BIN': sorted(df_picking['BIN'].unique())}) if not df_picking.empty else pd.DataFrame(columns=['BIN'])
            df_uputaway = pd.DataFrame({'LAST BIN MUTASI': sorted(df_putaway['LAST BIN MUTASI'].unique())}) if not df_putaway.empty else pd.DataFrame(columns=['LAST BIN MUTASI'])

            # 4. Final Matching List (Irisan)
            if not df_picking.empty and not df_putaway.empty:
                set_p = set(df_picking['BIN'].astype(str).str.strip())
                set_m = set(df_putaway['LAST BIN MUTASI'].astype(str).str.strip())
                match_bins = sorted(list(set_p.intersection(set_m)))
                df_final = pd.DataFrame({'NO': range(1, len(match_bins) + 1), 'BIN AUDIT FINAL': match_bins}) if match_bins else pd.DataFrame(columns=['NO', 'BIN AUDIT FINAL'])
            else:
                df_final = pd.DataFrame(columns=['NO', 'BIN AUDIT FINAL'])

            # Set Metrik
            self.ppa_total_picking_qty.set(int(df_picking['QTY'].sum()) if not df_picking.empty else 0)
            self.ppa_unique_picking_bin.set(len(df_upicking))
            self.ppa_unique_putaway_bin.set(len(df_uputaway))
            self.ppa_final_matching_bin.set(len(df_final))

            # Set Data Tabel
            self._raw_df_ppa_picking = df_picking
            self._raw_df_ppa_upicking = df_upicking
            self._raw_df_ppa_putaway = df_putaway
            self._raw_df_ppa_uputaway = df_uputaway
            self._raw_df_ppa_final = df_final

            self.df_ppa_picking_headers.set(df_picking.columns.tolist() if not df_picking.empty else [])
            self.df_ppa_picking_rows.set(df_picking.fillna("").astype(str).values.tolist() if not df_picking.empty else [])

            self.df_ppa_upicking_headers.set(df_upicking.columns.tolist() if not df_upicking.empty else [])
            self.df_ppa_upicking_rows.set(df_upicking.fillna("").astype(str).values.tolist() if not df_upicking.empty else [])

            self.df_ppa_putaway_headers.set(df_putaway.columns.tolist() if not df_putaway.empty else [])
            self.df_ppa_putaway_rows.set(df_putaway.fillna("").astype(str).values.tolist() if not df_putaway.empty else [])

            self.df_ppa_uputaway_headers.set(df_uputaway.columns.tolist() if not df_uputaway.empty else [])
            self.df_ppa_uputaway_rows.set(df_uputaway.fillna("").astype(str).values.tolist() if not df_uputaway.empty else [])

            self.df_ppa_final_headers.set(df_final.columns.tolist() if not df_final.empty else [])
            self.df_ppa_final_rows.set(df_final.fillna("").astype(str).values.tolist() if not df_final.empty else [])

            self.ppa_processed.set(True)
            return True, "Seluruh proses audit berhasil dijalankan!"
        except Exception as e:
            return False, f"Terjadi kesalahan saat memproses data: {e}"