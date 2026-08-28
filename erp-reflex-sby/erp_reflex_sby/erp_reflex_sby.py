import io
import time
import asyncio
from datetime import datetime
import pandas as pd
from supabase import create_client, Client
from shiny import App, Inputs, Outputs, Session, reactive, render, ui

# ==============================================================================
# 1. KONFIGURASI SUPABASE
# ==============================================================================
SUPABASE_URL = "https://ufhjrsxzcffdfswfqlzk.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVmaGpyc3h6Y2ZmZGZzd2ZxbHprIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYxNTI5NjgsImV4cCI6MjA5MTcyODk2OH0.DDlKkXU5-nVvNYK_uLYzXLgaj8oDT4s8vbjAoWMWacI"

def get_supabase() -> Client:
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print("Supabase Init Error:", e)
        return None

def safe_int(val, default=0) -> int:
    try:
        if pd.isna(val) or val is None: return default
        cleaned = str(val).replace("Rp", "").replace(".", "").replace(",", "").strip()
        return int(float(cleaned))
    except Exception:
        return default

# ==============================================================================
# 2. APP STATE & LOGIKA UTAMA
# ==============================================================================
class AppState:
    def __init__(self):
        # --- NAVIGATION & ROLE STATE ---
        self.logged_in = reactive.Value(False)
        self.role = reactive.Value("DC")
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

        # --- GLOBAL MODAL & LOADING STATES ---
        self.is_loading = reactive.Value(False)
        self.show_success_modal = reactive.Value(False)
        self.show_error_modal = reactive.Value(False)
        self.error_modal_message = reactive.Value("")

        # --- ONGKIR DATABASE STATE ---
        self.data_list = reactive.Value([])
        self.input_supplier = reactive.Value("")
        self.input_ekspedisi = reactive.Value("")
        self.input_koli = reactive.Value("1")
        self.input_ongkir = reactive.Value("0")
        self.input_tgl = reactive.Value(datetime.now().strftime("%Y-%m-%d"))
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

    # --- GLOBAL POPUP TRIGGER HELPERS ---
    def trigger_success(self):
        self.show_error_modal.set(False)
        self.show_success_modal.set(True)

    def trigger_error(self, message: str = ""):
        self.show_success_modal.set(False)
        self.error_modal_message.set(message if message else "Terjadi kesalahan saat memproses data!")
        self.show_error_modal.set(True)

    def set_loading(self, status: bool):
        self.is_loading.set(status)

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
        self.role.set("DC")
        self.login_timestamp_ms.set(0)

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
        if cur_menu in ["Database Ongkir In/Out", "Database Ongkir", "dashboard_ongkir"]:
            return "dashboard_ongkir"
        elif cur_menu == "Stock Minus":
            return "stock_minus"
        elif cur_menu == "Putaway System":
            return "putaway_system"
        else:
            return "under_development"

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
        koli_val = safe_int(koli_str, 0)
        ongkir_val = safe_int(ongkir_str, 0)

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
                koli = safe_int(row.get("TOTAL KOLI", 0))
                ongkir = safe_int(row.get("ONGKIR", 0))
                tgl_raw = row["TANGGAL_JAM"]
                fix_dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S") if pd.isna(tgl_raw) else str(tgl_raw)
                batch_data.append({"supplier": sup, "ekspedisi": eksp, "total_koli": koli, "total_ongkir": ongkir, "created_at": fix_dt})

            if batch_data:
                client = get_supabase()
                if client:
                    client.table("shipping_costs").insert(batch_data).execute()
                self.load_ongkir_data()
                return True, f"🚀 Berhasil Upload {len(batch_data)} Data CSV!"
            return False, "Tidak ada data valid yang diupload."
        except Exception as e:
            return False, f"Gagal Upload Batch: {e}"

    def toggle_select_id(self, item_id: str):
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
            res = [x for x in res if str(x.get("ekspedisi", "")).upper() == flt.upper()]
        return res

    def get_list_ekspedisi_options(self) -> list[str]:
        eksp = list(set([str(x.get("ekspedisi", "")).upper() for x in self.data_list() if x.get("ekspedisi")]))
        return ["SEMUA"] + sorted(eksp)

    def metric_total_biaya_all(self) -> str:
        total = sum([safe_int(x.get('total_ongkir', 0)) for x in self.get_filtered_ongkir()])
        return f"Rp {total:,.0f}"

    def metric_total_koli_all(self) -> str:
        total = sum([safe_int(x.get('total_koli', x.get('koli', 0))) for x in self.get_filtered_ongkir()])
        return f"{total:,.0f} Koli"

    def metric_avg_cost_all(self) -> str:
        data = self.get_filtered_ongkir()
        biaya = sum([safe_int(x.get("total_ongkir", 0)) for x in data])
        koli = sum([safe_int(x.get("total_koli", x.get("koli", 0))) for x in data])
        avg = (biaya / koli) if koli > 0 else 0
        return f"Rp {avg:,.0f}"

    def metric_biaya_datang(self) -> str:
        total = sum([safe_int(x.get('total_ongkir', 0)) for x in self.get_filtered_ongkir() if 'RTO' not in str(x.get('supplier', ''))])
        return f"Rp {total:,.0f}"

    def metric_koli_datang(self) -> str:
        total = sum([safe_int(x.get('total_koli', x.get('koli', 0))) for x in self.get_filtered_ongkir() if 'RTO' not in str(x.get('supplier', ''))])
        return f"{total:,.0f} Koli"

    def metric_biaya_rto(self) -> str:
        total = sum([safe_int(x.get('total_ongkir', 0)) for x in self.get_filtered_ongkir() if 'RTO' in str(x.get('supplier', ''))])
        return f"Rp {total:,.0f}"

    def process_stock_minus_file(self, file_bytes: bytes, file_name: str):
        try:
            df = pd.read_excel(io.BytesIO(file_bytes), engine="openpyxl") if file_name.endswith(('.xlsx', '.xls')) else pd.read_csv(io.BytesIO(file_bytes))
            df.columns = [str(c).strip().upper() for c in df.columns]

            col_sku = 'SKU'
            col_bin = 'BIN'
            col_qty = next((c for c in df.columns if 'QTY SYSTEM' in c or 'QTY SYS' in c), None)

            if col_qty is None:
                return False, "Kolom 'QTY SYSTEM' tidak ditemukan pada file!"

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
                df_plist.columns = ["BIN AWAL", "BIN TUJUAN", "SKU", "QUANTITY", "NOTES"]
                df_plist['NOTES'] = "PUTAWAY"
            else:
                df_plist = pd.DataFrame(columns=["BIN AWAL", "BIN TUJUAN", "SKU", "QUANTITY", "NOTES"])

            df_kurang = df_comp[df_comp['STATUS'] == "PERLU CARI STOCK MANUAL"].copy()

            area = self.area_putaway()
            if area == "DC LANTAI 1": kw_out = ["GL1-DC-PUTAWAY", "STAG"]
            elif area == "DC LANTAI 2": kw_out = ["GL2-DC-PUTAWAY", "STAG"]
            elif area == "DC LANTAI 3": kw_out = ["GL3-DC-PUTAWAY", "STAG"]
            elif area == "JERSEY ZONE": kw_out = ["JZ-PUTAWAY", "STAG"]
            else: kw_out = ["STAG", "PUTAWAY"]

            bin_series = df_asal_updated.iloc[:, c_bin_a].astype(str).str.upper()
            mask_kw = bin_series.str.contains(kw_out[0], na=False)
            for kw in kw_out[1:]:
                mask_kw = mask_kw | bin_series.str.contains(kw, na=False)

            mask_out = (pd.to_numeric(df_asal_updated.iloc[:, c_qty_a], errors='coerce') > 0) & mask_kw
            df_outstanding = df_asal_updated[mask_out].copy()

            self.putaway_total_setup.set(int(df_plist['QUANTITY'].sum()) if not df_plist.empty else 0)
            self.putaway_kurang_setup.set(int(df_kurang['DIFF'].sum()) if not df_kurang.empty else 0)

            sisa = 0
            if not df_outstanding.empty:
                qty_col = [c for c in df_outstanding.columns if 'qty' in str(c).lower()]
                if qty_col: sisa = int(pd.to_numeric(df_outstanding[qty_col[0]], errors='coerce').sum())
            self.putaway_sisa_stok.set(sisa)

            self._raw_df_comp = df_comp
            self._raw_df_plist = df_plist
            self._raw_df_kurang = df_kurang
            self._raw_df_out = df_outstanding
            self._raw_df_updated = df_asal_updated

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
        except Exception as e:
            return False, f"Gagal memproses file Putaway: {e}"

# ==============================================================================
# 3. CSS & JAVASCRIPT ASSETS
# ==============================================================================
CUSTOM_HEAD = ui.head_content(
    ui.tags.link(rel="stylesheet", href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"),
    ui.tags.style("""
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
        body, html { height: 100%; width: 100%; overflow-x: hidden; background-color: #111318; margin: 0; padding: 0; }
        
        /* --- RADIX / REFLEX RED SPINNER --- */
        .reflex-spinner-red {
            width: 38px;
            height: 38px;
            border: 3.5px solid rgba(229, 9, 20, 0.2);
            border-top-color: #E50914;
            border-radius: 50%;
            animation: reflexSpin 0.75s linear infinite;
        }
        @keyframes reflexSpin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        @keyframes blinkAnimation {
            0% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.3; transform: scale(0.8); }
            100% { opacity: 1; transform: scale(1); }
        }
        .blink-online { animation: blinkAnimation 1.5s infinite ease-in-out; }
        
        @keyframes popIn {
            0% { transform: scale(0.5); opacity: 0; }
            70% { transform: scale(1.15); opacity: 1; }
            100% { transform: scale(1); opacity: 1; }
        }
        .animate-pop { animation: popIn 0.45s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards; }
        
        /* Notifikasi Toast */
        #shiny-notification-panel {
            top: 25px !important;
            right: 25px !important;
            bottom: auto !important;
            left: auto !important;
            position: fixed !important;
            z-index: 999999 !important;
            width: 360px !important;
        }
        .shiny-notification {
            border-radius: 10px !important;
            box-shadow: 0 10px 25px rgba(0,0,0,0.18) !important;
            font-weight: 700 !important;
            font-size: 13px !important;
            padding: 14px 18px !important;
            margin-bottom: 10px !important;
        }
        .shiny-notification-message {
            background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
            color: #FFFFFF !important;
            border: none !important;
        }
        .shiny-notification-error {
            background: linear-gradient(135deg, #E50914 0%, #B20710 100%) !important;
            color: #FFFFFF !important;
            border: none !important;
        }
        .shiny-notification-warning {
            background: linear-gradient(135deg, #DD6B20 0%, #C05621 100%) !important;
            color: #FFFFFF !important;
            border: none !important;
        }

        .custom-clean-table { width: 100%; border-collapse: collapse; font-size: 13px; text-align: left; }
        .custom-clean-table th { background: #EDF2F7; color: #1A202C; font-weight: bold; font-size: 12px; padding: 10px; white-space: nowrap; border-bottom: 1px solid #CBD5E0; }
        .custom-clean-table td { color: #2D3748; padding: 8px 10px; white-space: nowrap; border-bottom: 1px solid #EDF2F7; }
        .custom-clean-table tr:hover { background-color: #F8FAFC; }
        
        .btn-red-gradient {
            background: linear-gradient(135deg, #E50914 0%, #B20710 100%) !important;
            color: #FFFFFF !important;
            font-weight: 800 !important;
            border-radius: 8px !important;
            border: none !important;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(229, 9, 20, 0.4);
            transition: all 0.2s ease;
        }
        .btn-red-gradient:hover { filter: brightness(1.1); }
        .btn-locked {
            background-color: #E50914 !important;
            opacity: 0.5 !important;
            color: white !important;
            font-weight: bold !important;
            border-radius: 6px !important;
            cursor: not-allowed !important;
            border: none !important;
        }

        /* --- UPLOADER BOX STYLING & PERBAIKAN TEXT INPUT NAMA FILE --- */
        .uploader-box {
            border: 2px dashed #718096 !important;
            border-radius: 10px;
            background: #F8FAFC;
            padding: 1rem 1.25rem;
            width: 100%;
            display: flex;
            align-items: center;
            transition: all 0.2s ease;
        }
        .uploader-box:hover {
            border-color: #1A202C !important;
            background-color: #F1F5F9;
        }
        .uploader-box .shiny-input-container {
            margin-bottom: 0 !important;
            width: 100%;
        }
        .uploader-box .input-group {
            display: flex !important;
            align-items: center !important;
            width: 100% !important;
            margin-bottom: 0 !important;
        }
        .uploader-box .btn-file {
            background-color: #C5A059 !important;
            color: #FFFFFF !important;
            font-weight: bold !important;
            border-radius: 6px !important;
            border: none !important;
            padding: 8px 18px !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
            display: inline-flex;
            align-items: center;
            margin-right: 10px !important;
        }
        .uploader-box .btn-file:hover {
            filter: brightness(1.08);
        }
        .uploader-box input[type="text"].form-control {
            background-color: #FFFFFF !important;
            border: 1.5px solid #CBD5E0 !important;
            border-radius: 6px !important;
            color: #1A202C !important;
            font-weight: 700 !important;
            font-size: 13px !important;
            box-shadow: none !important;
            padding: 8px 12px !important;
            height: 40px !important;
            width: 100% !important;
            flex: 1 1 auto !important;
            display: block !important;
            text-overflow: ellipsis !important;
            overflow: hidden !important;
            white-space: nowrap !important;
            opacity: 1 !important;
        }

        /* --- BATCH CSV UPLOADER BOX --- */
        .csv-batch-box {
            border: 2px dashed #718096 !important;
            border-radius: 12px;
            background: #FAFAFA;
            padding: 1.5rem 1.25rem;
            width: 100%;
            text-align: center;
            margin-bottom: 1.25rem;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            transition: all 0.2s ease;
        }
        .csv-batch-box:hover {
            border-color: #1A202C !important;
            background-color: #F4F4F5;
        }
        .csv-batch-box .shiny-input-container {
            margin-bottom: 0 !important;
            width: 100%;
        }
        .csv-batch-box .input-group {
            display: flex !important;
            align-items: center !important;
            width: 100% !important;
            margin-bottom: 0 !important;
        }
        .csv-batch-box .btn-file {
            background-color: #1A202C !important;
            color: #FFFFFF !important;
            font-weight: 700 !important;
            border-radius: 6px !important;
            border: none !important;
            padding: 8px 16px !important;
            margin-right: 10px !important;
        }
        .csv-batch-box .btn-file:hover {
            background-color: #2D3748 !important;
        }
        .csv-batch-box input[type="text"].form-control {
            background-color: #FFFFFF !important;
            border: 1.5px solid #CBD5E0 !important;
            border-radius: 6px !important;
            color: #1A202C !important;
            font-weight: 700 !important;
            font-size: 13px !important;
            box-shadow: none !important;
            padding: 8px 12px !important;
            height: 40px !important;
            width: 100% !important;
            flex: 1 1 auto !important;
            display: block !important;
            text-overflow: ellipsis !important;
            overflow: hidden !important;
            white-space: nowrap !important;
            opacity: 1 !important;
        }

        details { border: 1px solid #E2E8F0; border-radius: 6px; margin-bottom: 8px; background: #FFFFFF; }
        summary { font-weight: bold; padding: 10px 14px; cursor: pointer; color: #1A202C; background: #F8FAFC; border-radius: 6px; }
        details[open] summary { border-bottom: 1px solid #E2E8F0; border-radius: 6px 6px 0 0; }
        .accordion-content { padding: 14px; font-size: 13px; color: #4A5568; background: #F7FAFC; }
    """),
    ui.tags.script("""
        setInterval(function() {
            let elStore = document.getElementById('login-time-store');
            let elTimer = document.getElementById('live-timer');
            if (elStore && elTimer) {
                let loginTime = parseInt(elStore.innerText);
                if (loginTime && loginTime > 0) {
                    let now = new Date().getTime();
                    let diff = Math.floor((now - loginTime) / 1000);
                    let h = String(Math.floor(diff / 3600)).padStart(2, '0');
                    let m = String(Math.floor((diff % 3600) / 60)).padStart(2, '0');
                    let s = String(diff % 60).padStart(2, '0');
                    elTimer.innerText = h + ':' + m + ':' + s;
                } else {
                    elTimer.innerText = "00:00:00";
                }
            }
        }, 1000);
    """)
)

# ==============================================================================
# 4. HELPER KOMPONEN METRICS & MODAL
# ==============================================================================
def metric_box(title: str, val_str: str, text_color: str, bg_gradient: str):
    return ui.div(
        ui.div(title, style="color: #4A5568; font-size: 11px; font-weight: 800; text-transform: uppercase; margin-bottom: 4px;"),
        ui.div(val_str, style=f"color: {text_color}; font-size: 20px; font-weight: 800;"),
        style=f"background: {bg_gradient}; padding: 1rem; border-radius: 12px; border: 1px solid rgba(0,0,0,0.06); text-align: center; width: 100%; box-shadow: 0 2px 6px rgba(0,0,0,0.03);"
    )

def dark_metric_box(title: str, val_str: str, border_color: str):
    return ui.div(
        ui.div(title, style="color: #A0AEC0; font-size: 11px; font-weight: bold; margin-bottom: 4px;"),
        ui.div(val_str, style=f"color: {border_color}; font-size: 22px; font-weight: bold;"),
        style=f"background: #1A1A1A; padding: 1rem; border-radius: 8px; border-left: 4px solid {border_color}; width: 100%; text-align: center;"
    )

def render_clean_table(headers: list, rows: list):
    if not rows or len(rows) == 0:
        return ui.div(
            ui.div("Tidak ada data untuk ditampilkan.", style="color: #718096; padding: 1.5rem; font-style: italic; text-align: center;"),
            style="background: white; border-radius: 8px; border: 1px solid #E2E8F0; width: 100%;"
        )
    
    th_cells = [ui.tags.th(str(h)) for h in headers]
    tr_rows = []
    for r in rows:
        td_cells = [ui.tags.td(str(c)) for c in r]
        tr_rows.append(ui.tags.tr(*td_cells))
        
    return ui.div(
        ui.tags.table(
            ui.tags.thead(ui.tags.tr(*th_cells)),
            ui.tags.tbody(*tr_rows),
            class_="custom-clean-table"
        ),
        style="overflow-x: auto; width: 100%; background: white; border-radius: 8px; padding: 0.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05); border: 1px solid #E2E8F0;"
    )

# --- SUCCESS MODAL ---
def success_modal(show: bool):
    if not show:
        return ui.div()
    return ui.div(
        ui.div(
            ui.div(
                ui.tags.i(class_="fa-solid fa-check", style="font-size: 55px; color: white;"),
                class_="animate-pop",
                style="background: linear-gradient(135deg, #4ade80 0%, #16a34a 100%); border-radius: 50%; width: 95px; height: 95px; box-shadow: 0 10px 30px rgba(74, 222, 128, 0.5); margin-bottom: 10px; display: flex; align-items: center; justify-content: center;"
            ),
            ui.h2("Success!", style="font-size: 32px; color: #1A202C; font-weight: 800; margin: 0;"),
            style="display: flex; flex-direction: column; align-items: center; justify-content: center; background: transparent;"
        ),
        ui.tags.script("""
            setTimeout(function() {
                let el = document.getElementById('success-modal-overlay');
                if (el) {
                    el.remove();
                    Shiny.setInputValue('close_success_modal_event', Math.random(), {priority: 'event'});
                }
            }, 1800);
        """),
        id="success-modal-overlay",
        onclick="this.remove(); Shiny.setInputValue('close_success_modal_event', Math.random(), {priority: 'event'});",
        style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: 99999; background: rgba(255, 255, 255, 0.65); backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center; cursor: pointer;"
    )

# --- ERROR MODAL ---
def error_modal(show: bool, message: str = ""):
    if not show:
        return ui.div()
    return ui.div(
        ui.div(
            ui.div(
                ui.tags.i(class_="fa-solid fa-xmark", style="font-size: 55px; color: white;"),
                class_="animate-pop",
                style="background: linear-gradient(135deg, #EF4444 0%, #B91C1C 100%); border-radius: 50%; width: 95px; height: 95px; box-shadow: 0 10px 30px rgba(239, 68, 68, 0.5); margin-bottom: 10px; display: flex; align-items: center; justify-content: center;"
            ),
            ui.h2("Gagal / Error!", style="font-size: 30px; color: #E53E3E; font-weight: 800; margin: 0 0 6px 0;"),
            ui.p(message if message else "Terjadi kesalahan saat memproses data!", style="color: #2D3748; font-size: 15px; font-weight: 700; text-align: center; max-width: 450px; margin: 0;"),
            style="display: flex; flex-direction: column; align-items: center; justify-content: center; background: transparent;"
        ),
        ui.tags.script("""
            setTimeout(function() {
                let el = document.getElementById('error-modal-overlay');
                if (el) {
                    el.remove();
                    Shiny.setInputValue('close_error_modal_event', Math.random(), {priority: 'event'});
                }
            }, 2600);
        """),
        id="error-modal-overlay",
        onclick="this.remove(); Shiny.setInputValue('close_error_modal_event', Math.random(), {priority: 'event'});",
        style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: 99999; background: rgba(255, 255, 255, 0.65); backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center; cursor: pointer;"
    )

# --- GLOBAL LOADING OVERLAY (CONVERTED DARI REFLEX) ---
def render_reflex_loading_overlay(is_loading: bool):
    if not is_loading:
        return ui.div()
    return ui.div(
        ui.div(
            ui.div(class_="reflex-spinner-red"),
            ui.span(
                "Sedang memproses data, mohon tunggu...",
                style="font-weight: bold; color: #1A202C; font-size: 14px; text-align: center;"
            ),
            style="""
                background: white;
                padding: 2rem;
                border-radius: 12px;
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.25);
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 1rem;
                min-width: 280px;
            """
        ),
        style="""
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(0, 0, 0, 0.5);
            z-index: 99999;
            display: flex;
            align-items: center;
            justify-content: center;
        """
    )

# ==============================================================================
# 5. VIEW STOCK MINUS
# ==============================================================================
def stock_minus_view(state: AppState):
    uploader_ui = ui.div(
        ui.span("Upload File STOCK MINUS", style="font-weight: bold; color: #1A202C; font-size: 14px; margin-bottom: 0.25rem; display: block;"),
        ui.div(
            ui.input_file(
                "upload_stock_file",
                None,
                accept=[".xlsx", ".xls"],
                multiple=False,
                button_label=ui.tags.span(ui.tags.i(class_="fa-solid fa-upload", style="margin-right: 6px; font-size: 14px;"), "Upload"),
                placeholder="200MB per file • XLSX, XLS"
            ),
            class_="uploader-box"
        ),
        ui.output_ui("stock_minus_action_btn_ui"),
        style="width: 100%; background: white; padding: 1.25rem; border-radius: 10px; border: 1px solid #E2E8F0; margin-bottom: 1.25rem;"
    )

    results_ui = ui.output_ui("stock_minus_results_container")

    return ui.div(uploader_ui, results_ui, style="width: 100%; padding: 1rem;")

# ==============================================================================
# 6. VIEW PUTAWAY SYSTEM
# ==============================================================================
def custom_uploader_box(id_str: str, title: str):
    return ui.div(
        ui.span(title, style="font-weight: bold; color: #1A202C; font-size: 14px; margin-bottom: 0.25rem; display: block;"),
        ui.div(
            ui.input_file(
                id_str,
                None,
                accept=[".xlsx", ".xls", ".csv"],
                multiple=False,
                button_label=ui.tags.span(ui.tags.i(class_="fa-solid fa-upload", style="margin-right: 6px; font-size: 14px;"), "Upload"),
                placeholder="200MB per file • XLSX, XLS, CSV"
            ),
            class_="uploader-box"
        ),
        style="flex: 1; min-width: 280px; margin-bottom: 0.5rem;"
    )

def putaway_view(state: AppState):
    cur_area = state.area_putaway()

    if cur_area != "":
        area_content = ui.div(
            ui.div(
                ui.tags.i(class_="fa-solid fa-map-pin", style="color: #3182ce; font-size: 18px; margin-right: 8px;"),
                ui.span("Area Terpilih: ", style="font-weight: normal; color: #2c5282; font-size: 13px;"),
                ui.span(cur_area, style="font-weight: bold; color: #2c5282; font-size: 13px;"),
                style="background: #ebf8ff; border-left: 4px solid #3182ce; padding: 10px 16px; border-radius: 6px; width: 100%; display: flex; align-items: center; margin-bottom: 1rem;"
            ),
            ui.div(
                custom_uploader_box("ds_putaway_file", "Upload DS PUTAWAY"),
                custom_uploader_box("asal_putaway_file", "Upload ASAL BIN"),
                style="display: flex; gap: 1rem; width: 100%; margin-bottom: 1rem; flex-wrap: wrap;"
            ),
            ui.output_ui("putaway_action_btn_ui"),
            style="width: 100%;"
        )
    else:
        area_content = ui.div(
            "⚠️ Silakan pilih Area Putaway di atas terlebih dahulu.",
            style="color: #DD6B20; font-weight: bold; font-style: italic; background: #FFFFF0; border: 1px solid #F6E05E; padding: 1rem; border-radius: 8px; width: 100%; text-align: center;"
        )

    top_section = ui.div(
        ui.span("📍 Pilih Area Putaway", style="font-weight: bold; color: #1A202C; font-size: 14px; margin-bottom: 0.5rem; display: block;"),
        ui.tags.select(
            ui.tags.option("-- Pilih Area Putaway --", value=""),
            ui.tags.option("DC LANTAI 1", value="DC LANTAI 1"),
            ui.tags.option("DC LANTAI 2", value="DC LANTAI 2"),
            ui.tags.option("DC LANTAI 3", value="DC LANTAI 3"),
            ui.tags.option("JERSEY ZONE", value="JERSEY ZONE"),
            id="area_putaway_select",
            onchange="Shiny.setInputValue('select_area_putaway', this.value, {priority: 'event'})",
            style="""
                width: 100%; padding: 10px 14px; background-color: #FFFFFF; color: #000000;
                font-weight: bold; font-size: 14px; border: 1.5px solid #CBD5E0;
                border-radius: 8px; outline: none; cursor: pointer; margin-bottom: 1rem;
            """
        ),
        area_content,
        style="width: 100%; background: white; padding: 1.25rem; border-radius: 10px; border: 1px solid #E2E8F0; margin-bottom: 1.25rem;"
    )

    results_ui = ui.output_ui("putaway_results_container")

    return ui.div(top_section, results_ui, style="width: 100%; padding: 1rem;")

# ==============================================================================
# 7. VIEW DATABASE ONGKIR (MAIN DASHBOARD)
# ==============================================================================
def main_dashboard_view(state: AppState):
    STYLE_LABEL_CSS = "font-size: 11px; font-weight: 800; color: #1A202C; margin-bottom: 2px; letter-spacing: 0.5px; display: block;"

    tab1_content = ui.div(
        ui.div(
            ui.div(
                ui.span("📝", style="font-size: 20px; margin-right: 8px;"),
                ui.h4("Input Transaksi Manual", style="font-size: 16px; font-weight: bold; color: #1A202C; margin: 0;"),
                style="display: flex; align-items: center; margin-bottom: 0.75rem;"
            ),
            ui.hr(style="border-color: #CBD5E0; margin-bottom: 1rem;"),
            ui.div(
                ui.span("NAMA SUPPLIER", style=STYLE_LABEL_CSS),
                ui.tags.input(id="input_supplier", type="text", placeholder="Masukkan Nama Supplier...", style="background-color: #FFFFFF; color: #111111; border: 2px solid #4A5568; border-radius: 8px; font-weight: 600; padding: 0.6rem 0.8rem; width: 100%; outline: none;"),
                style="margin-bottom: 0.75rem; width: 100%;"
            ),
            ui.div(
                ui.div(
                    ui.span("EKSPEDISI", style=STYLE_LABEL_CSS),
                    ui.tags.input(id="input_ekspedisi", type="text", placeholder="Nama Ekspedisi...", style="background-color: #FFFFFF; color: #111111; border: 2px solid #4A5568; border-radius: 8px; font-weight: 600; padding: 0.6rem 0.8rem; width: 100%; outline: none;"),
                    style="flex: 1; margin-right: 8px;"
                ),
                ui.div(
                    ui.span("TOTAL KOLI", style=STYLE_LABEL_CSS),
                    ui.tags.input(id="input_koli", type="number", value="1", placeholder="Jumlah Koli", style="background-color: #FFFFFF; color: #111111; border: 2px solid #4A5568; border-radius: 8px; font-weight: 600; padding: 0.6rem 0.8rem; width: 100%; outline: none;"),
                    style="flex: 1;"
                ),
                style="display: flex; width: 100%; margin-bottom: 0.75rem;"
            ),
            ui.div(
                ui.div(
                    ui.span("TOTAL ONGKIR (RP)", style=STYLE_LABEL_CSS),
                    ui.tags.input(id="input_ongkir", type="number", value="0", placeholder="Rp 0", style="background-color: #FFFFFF; color: #111111; border: 2px solid #4A5568; border-radius: 8px; font-weight: 600; padding: 0.6rem 0.8rem; width: 100%; outline: none;"),
                    style="flex: 1; margin-right: 8px;"
                ),
                ui.div(
                    ui.span("TANGGAL", style=STYLE_LABEL_CSS),
                    ui.tags.input(id="input_tgl", type="date", value=datetime.now().strftime("%Y-%m-%d"), style="background-color: #FFFFFF; color: #111111; border: 2px solid #4A5568; border-radius: 8px; font-weight: 600; padding: 0.6rem 0.8rem; width: 100%; outline: none;"),
                    style="flex: 1;"
                ),
                style="display: flex; width: 100%; margin-bottom: 1.25rem;"
            ),
            ui.tags.button(
                "🚀 SIMPAN DATA ONGKIR",
                onclick="""
                    Shiny.setInputValue('btn_save_ongkir_manual', {
                        supplier: document.getElementById('input_supplier').value,
                        ekspedisi: document.getElementById('input_ekspedisi').value,
                        koli: document.getElementById('input_koli').value,
                        ongkir: document.getElementById('input_ongkir').value,
                        tgl: document.getElementById('input_tgl').value
                    }, {priority: 'event'})
                """,
                class_="btn-red-gradient",
                style="width: 100%; height: 48px; font-size: 14px;"
            ),
            style="background: #FFFFFF; border-radius: 16px; border: 2px solid #CBD5E0; box-shadow: 0 10px 25px rgba(0,0,0,0.03); padding: 1.8rem; flex: 1; min-width: 320px;"
        ),
        ui.div(
            ui.div(
                ui.span("📁", style="font-size: 20px; margin-right: 8px;"),
                ui.h4("Batch CSV Upload", style="font-size: 16px; font-weight: bold; color: #1A202C; margin: 0;"),
                style="display: flex; align-items: center; margin-bottom: 0.75rem;"
            ),
            ui.hr(style="border-color: #CBD5E0; margin-bottom: 1rem;"),
            ui.div(
                ui.div(
                    ui.span("☁️", style="font-size: 24px;"),
                    style="padding: 10px; background: #E2E8F0; border-radius: 50%; width: 50px; height: 50px; display: flex; align-items: center; justify-content: center; margin-bottom: 8px;"
                ),
                ui.span("Tarik & lepaskan file CSV di sini atau klik Pilih File:", style="font-size: 13px; color: #4A5568; font-weight: bold; margin-bottom: 10px;"),
                ui.input_file(
                    "upload_csv_batch",
                    None,
                    accept=[".csv"],
                    multiple=False,
                    button_label="Pilih File CSV",
                    placeholder="Pilih file CSV..."
                ),
                class_="csv-batch-box"
            ),
            ui.output_ui("batch_csv_action_btn_ui"),
            style="background: #FFFFFF; border-radius: 16px; border: 2px solid #CBD5E0; box-shadow: 0 10px 25px rgba(0,0,0,0.03); padding: 1.8rem; flex: 1; min-width: 320px;"
        ),
        style="display: flex; flex-wrap: wrap; gap: 1.25rem; width: 100%; margin-top: 1.5rem;"
    )

    selected_count = len(state.selected_ids())
    del_btn_ui = ui.tags.button(
        f"🗑️ HAPUS ({selected_count}) DATA",
        onclick="Shiny.setInputValue('btn_open_delete_modal', Math.random(), {priority: 'event'})",
        style="background: #E53E3E; color: white; border: none; padding: 6px 14px; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 13px;"
    ) if selected_count > 0 else ui.div()

    eksp_options = state.get_list_ekspedisi_options()
    select_options = [ui.tags.option(opt, value=opt, selected=(opt == state.filter_ekspedisi())) for opt in eksp_options]

    filtered_data = state.get_filtered_ongkir()
    table_rows = []
    sel_set = set(state.selected_ids())

    for row in filtered_data:
        r_id = str(row.get("id", ""))
        is_chk = r_id in sel_set
        chk = ui.tags.input(
            type="checkbox",
            checked=is_chk,
            onchange=f"Shiny.setInputValue('toggle_row_id', '{r_id}', {{priority: 'event'}})"
        )
        tgl_display = str(row.get("created_at", row.get("tanggal", "")))
        supp_display = str(row.get("supplier", ""))
        eksp_display = str(row.get("ekspedisi", ""))
        koli_display = safe_int(row.get("total_koli", row.get("koli", 0)))
        ongkir_display = safe_int(row.get("total_ongkir", 0))

        table_rows.append(ui.tags.tr(
            ui.tags.td(chk, style="text-align: center; width: 60px;"),
            ui.tags.td(tgl_display),
            ui.tags.td(supp_display),
            ui.tags.td(eksp_display),
            ui.tags.td(str(koli_display)),
            ui.tags.td(f"Rp {ongkir_display:,}")
        ))

    tab2_content = ui.div(
        ui.div(
            ui.div(
                ui.span("FILTER EKSPEDISI:", style="font-size: 12px; font-weight: 800; color: #111111; margin-right: 8px;"),
                ui.tags.select(
                    *select_options,
                    id="select_filter_ekspedisi",
                    onchange="Shiny.setInputValue('change_filter_ekspedisi', this.value, {priority: 'event'})",
                    style="background-color: #FFFFFF !important; color: #000000 !important; border: 2.5px solid #1A202C !important; border-radius: 8px !important; font-weight: 800 !important; box-shadow: 0 2px 5px rgba(0,0,0,0.05); width: 220px; padding: 6px 10px; outline: none; cursor: pointer;"
                ),
                style="display: flex; align-items: center;"
            ),
            del_btn_ui,
            style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin-top: 1.5rem; margin-bottom: 0.5rem;"
        ),
        ui.div(
            metric_box("💰 BIAYA ALL", state.metric_total_biaya_all(), "#C53030", "linear-gradient(135deg, #FED7D7 0%, #FEB2B2 100%)"),
            metric_box("📦 KOLI ALL", state.metric_total_koli_all(), "#1A202C", "linear-gradient(135deg, #E2E8F0 0%, #CBD5E0 100%)"),
            metric_box("📊 AVG COST ALL", state.metric_avg_cost_all(), "#C53030", "linear-gradient(135deg, #FED7D7 0%, #FEB2B2 100%)"),
            metric_box("🚚 BIAYA DATANG", state.metric_biaya_datang(), "#276749", "linear-gradient(135deg, #C6F6D5 0%, #9AE6B4 100%)"),
            metric_box("📦 KOLI DATANG", state.metric_koli_datang(), "#276749", "linear-gradient(135deg, #C6F6D5 0%, #9AE6B4 100%)"),
            metric_box("🔄 BIAYA RTO", state.metric_biaya_rto(), "#9B2C2C", "linear-gradient(135deg, #FED7D7 0%, #FEB2B2 100%)"),
            style="display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 1rem; width: 100%; margin-bottom: 1.5rem;"
        ),
        ui.div(
            ui.tags.table(
                ui.tags.thead(
                    ui.tags.tr(
                        ui.tags.th("SELECT", style="text-align: center; color: #1A202C; font-weight: bold;"),
                        ui.tags.th("TANGGAL", style="color: #1A202C; font-weight: bold;"),
                        ui.tags.th("SUPPLIER", style="color: #1A202C; font-weight: bold;"),
                        ui.tags.th("EKSPEDISI", style="color: #1A202C; font-weight: bold;"),
                        ui.tags.th("KOLI", style="color: #1A202C; font-weight: bold;"),
                        ui.tags.th("TOTAL ONGKIR", style="color: #1A202C; font-weight: bold;"),
                    ),
                    style="background-color: #CBD5E0 !important;"
                ),
                ui.tags.tbody(*table_rows) if len(table_rows) > 0 else ui.tags.tr(ui.tags.td("Tidak ada transaksi ongkir.", colspan="6", style="text-align: center; color: #718096; padding: 2rem;")),
                class_="custom-clean-table"
            ),
            style="background: #FFFFFF; border-radius: 16px; border: 2.5px solid #1A202C; padding: 1rem; width: 100%; box-shadow: 0 10px 25px rgba(0,0,0,0.04); overflow-x: auto;"
        ),
        style="width: 100%;"
    )

    return ui.div(
        ui.navset_card_tab(
            ui.nav_panel("📥 INPUT & BATCH DATA", tab1_content),
            ui.nav_panel("📊 SUMMARY & HISTORY", tab2_content)
        ),
        style="width: 100%; background-color: #F7FAFC; min-height: 100vh; padding: 1rem;"
    )

# ==============================================================================
# 8. VIEW SIDEBAR, HEADER & LOGIN PAGE
# ==============================================================================
def menu_item(label: str, target_menu: str, current_menu: str):
    is_active = (current_menu == target_menu)
    bg_style = "background: linear-gradient(135deg, #E50914 0%, #B20710 100%); color: #FFFFFF; font-weight: 700; box-shadow: 0 4px 12px rgba(229, 9, 20, 0.4);" if is_active else "background: transparent; color: #CBD5E0; font-weight: 500;"

    return ui.tags.button(
        label,
        onclick=f"Shiny.setInputValue('select_menu_item', '{target_menu}', {{priority: 'event'}})",
        style=f"""
            width: 100%; text-align: left; padding: 0.5rem 0.75rem; margin-bottom: 3px;
            border-radius: 6px; font-size: 0.85rem; border: none; cursor: pointer;
            justify-content: flex-start; transition: all 0.2s ease; {bg_style}
        """
    )

def section_dropdown_header(title: str, dropdown_key: str, is_open: bool):
    icon_tag = "fa-chevron-down" if is_open else "fa-chevron-right"
    return ui.tags.div(
        ui.tags.span(title, style="font-size: 11px; font-weight: bold; color: #FFFFFF; letter-spacing: 0.05em;"),
        ui.tags.i(class_=f"fa-solid {icon_tag}", style="font-size: 12px; color: #FFFFFF;"),
        onclick=f"Shiny.setInputValue('toggle_dropdown_section', '{dropdown_key}', {{priority: 'event'}})",
        style="""
            display: flex; justify-content: space-between; align-items: center; width: 100%;
            padding: 0.5rem 0.6rem; border-radius: 6px; cursor: pointer;
            background: rgba(255, 255, 255, 0.05); margin-top: 0.8rem; margin-bottom: 0.3rem;
            transition: background 0.2s ease;
        """
    )

def sidebar(state: AppState):
    cur_menu = state.main_menu()

    if not state.sidebar_open():
        return ui.div(
            ui.tags.button(
                ui.tags.i(class_="fa-solid fa-bars", style="font-size: 18px; color: #FFFFFF;"),
                onclick="Shiny.setInputValue('btn_toggle_sidebar', Math.random(), {priority: 'event'})",
                style="background: transparent; border: none; cursor: pointer; padding: 0.5rem; border-radius: 6px;"
            ),
            style="width: 60px; min-width: 60px; padding: 1rem 0.5rem; background: #111318; border-right: 1px solid #2D3748; height: 100vh; display: flex; flex-direction: column; align-items: center;"
        )

    op_menus = state.get_menu_operational()
    inv_menus = state.get_menu_inventory()
    rej_menus = state.get_menu_reject()
    ext_menus = state.get_menu_extras()

    return ui.div(
        ui.div(
            ui.div(
                ui.span("JEZ", style="color: #E50914; font-weight: 900; font-size: 20px;"),
                ui.span("PRO", style="color: #FFFFFF; font-weight: 900; font-size: 20px;"),
                style="display: flex; gap: 2px; align-items: center;"
            ),
            ui.tags.button(
                ui.tags.i(class_="fa-solid fa-angles-left", style="font-size: 16px; color: #CBD5E0;"),
                onclick="Shiny.setInputValue('btn_toggle_sidebar', Math.random(), {priority: 'event'})",
                style="background: transparent; border: none; cursor: pointer; padding: 4px 8px; border-radius: 4px;"
            ),
            style="display: flex; justify-content: space-between; width: 100%; align-items: center; margin-bottom: 0.5rem;"
        ),
        ui.div(
            ui.div(
                section_dropdown_header("OPERATIONAL", "operational", state.dropdown_operational()),
                ui.div(
                    *[menu_item(item, item, cur_menu) for item in op_menus],
                    style="width: 100%; padding-left: 0.5rem; display: flex; flex-direction: column;" if state.dropdown_operational() else "display: none;"
                ),
                style="width: 100%;"
            ),
            ui.div(
                section_dropdown_header("INVENTORY", "inventory", state.dropdown_inventory()),
                ui.div(
                    *[menu_item(item, item, cur_menu) for item in inv_menus],
                    style="width: 100%; padding-left: 0.5rem; display: flex; flex-direction: column;" if state.dropdown_inventory() else "display: none;"
                ),
                style="width: 100%;"
            ),
            ui.div(
                section_dropdown_header("REJECT & DEFECT", "reject", state.dropdown_reject()),
                ui.div(
                    *[menu_item(item, item, cur_menu) for item in rej_menus],
                    style="width: 100%; padding-left: 0.5rem; display: flex; flex-direction: column;" if state.dropdown_reject() else "display: none;"
                ),
                style="width: 100%;"
            ),
            ui.div(
                section_dropdown_header("EXTRAS", "extras", state.dropdown_extras()),
                ui.div(
                    *[menu_item(item, item, cur_menu) for item in ext_menus],
                    style="width: 100%; padding-left: 0.5rem; display: flex; flex-direction: column;" if state.dropdown_extras() else "display: none;"
                ),
                style="width: 100%;"
            ),
            style="width: 100%; flex: 1; overflow-y: auto; padding-right: 4px;"
        ),
        ui.div(
            ui.tags.button(
                ui.tags.span(
                    ui.tags.i(class_="fa-solid fa-right-from-bracket", style="margin-right: 8px; font-size: 14px;"),
                    ui.span("Logout Sistem", style="font-weight: bold; font-size: 13px;")
                ),
                onclick="Shiny.setInputValue('btn_execute_logout', Math.random(), {priority: 'event'})",
                class_="btn-red-gradient",
                style="width: 100%; padding: 0.5rem; border-radius: 6px; display: flex; align-items: center; justify-content: center;"
            ),
            style="width: 100%; padding-top: 0.8rem; border-top: 1px solid rgba(255, 255, 255, 0.1); margin-top: auto;"
        ),
        style="""
            width: 280px; min-width: 280px; padding: 1rem;
            background: linear-gradient(180deg, #111318 0%, #1A1D24 50%, #0D0F12 100%);
            border-right: 1px solid #2D3748; height: 100vh; display: flex; flex-direction: column;
            align-items: flex-start; transition: width 0.3s ease;
        """
    )

def login_page():
    return ui.div(
        ui.div(
            ui.div(
                ui.div(
                    ui.div(style="width: 12px; height: 38px; background: #E50914; border-radius: 4px; margin-right: 12px;"),
                    ui.div(
                        ui.h2("LOGISTIC DISTRIBUTION", style="color: #FFFFFF; font-size: 22px; font-weight: 800; letter-spacing: 1px; margin: 0; line-height: 1.1;"),
                        ui.span("CENTER WAREHOUSE • SURABAYA", style="color: #E50914; font-size: 11px; font-weight: 700; letter-spacing: 2px;"),
                        style="display: flex; flex-direction: column;"
                    ),
                    style="display: flex; align-items: center; margin-bottom: 1.25rem;"
                ),
                ui.hr(style="border-color: rgba(255, 255, 255, 0.1); margin-bottom: 1.25rem;"),
                ui.p("Silakan masuk dengan akun resmi gudang Anda.", style="color: #B0B0B0; font-size: 13px; margin-bottom: 1.5rem;"),
                ui.div(
                    ui.span("USERNAME", style="font-size: 11px; font-weight: 700; color: #FFFFFF; letter-spacing: 1px; margin-bottom: 4px; display: block;"),
                    ui.tags.input(
                        id="login_username_field", type="text", placeholder="Masukkan username...",
                        onkeydown="if (event.key === 'Enter') document.getElementById('btn_sign_in').click();",
                        style="background: rgba(0, 0, 0, 0.75); border: 1px solid rgba(229, 9, 20, 0.4); color: #FFFFFF; border-radius: 10px; padding: 0.8rem 1rem; width: 100%; outline: none;"
                    ),
                    style="margin-bottom: 1rem;"
                ),
                ui.div(
                    ui.span("PASSWORD", style="font-size: 11px; font-weight: 700; color: #FFFFFF; letter-spacing: 1px; margin-bottom: 4px; display: block;"),
                    ui.tags.input(
                        id="login_password_field", type="password", placeholder="Masukkan password...",
                        onkeydown="if (event.key === 'Enter') document.getElementById('btn_sign_in').click();",
                        style="background: rgba(0, 0, 0, 0.75); border: 1px solid rgba(229, 9, 20, 0.4); color: #FFFFFF; border-radius: 10px; padding: 0.8rem 1rem; width: 100%; outline: none;"
                    ),
                    style="margin-bottom: 1.5rem;"
                ),
                ui.div(style="height: 10px;"),
                ui.tags.button(
                    "SIGN IN TO SYSTEM →",
                    id="btn_sign_in",
                    onclick="""
                        Shiny.setInputValue('btn_submit_login', {
                            user: document.getElementById('login_username_field').value,
                            pass: document.getElementById('login_password_field').value
                        }, {priority: 'event'})
                    """,
                    class_="btn-red-gradient",
                    style="width: 100%; height: 48px; font-size: 14px; font-weight: 800; border-radius: 10px; cursor: pointer; box-shadow: 0 4px 15px rgba(229, 9, 20, 0.4);"
                ),
                ui.div(
                    "🟢 Warehouse Supporting Tools v2.0",
                    style="color: #888888; font-size: 12px; text-align: center; margin-top: 10px;"
                ),
                style="display: flex; flex-direction: column; width: 100%;"
            ),
            style="""
                width: 100%; max-width: 520px; padding: 3rem 2.5rem;
                background: rgba(12, 12, 15, 0.88); backdrop-filter: blur(20px);
                border-radius: 20px; border: 1px solid rgba(255, 255, 255, 0.12);
                border-left: 5px solid #E50914; box-shadow: 0 25px 60px rgba(0, 0, 0, 0.85);
            """
        ),
        style="""
            background-image: radial-gradient(circle at center, rgba(0, 0, 0, 0.15) 0%, rgba(0, 0, 0, 0.45) 100%), url('https://images.unsplash.com/photo-1553413077-190dd305871c?q=80&w=2070');
            background-size: cover; background-position: center; background-repeat: no-repeat;
            width: 100vw; height: 100vh; display: flex; align-items: center; justify-content: center; padding: 2rem;
        """
    )

def global_header(state: AppState):
    return ui.div(
        ui.div(
            ui.div(style="width: 10px; height: 32px; background: #E50914; border-radius: 4px; margin-right: 12px;"),
            ui.div(
                ui.h3(state.main_menu(), style="font-size: 18px; color: #111111; font-weight: 800; margin: 0; line-height: 1.2;"),
                ui.span(f"Logged in as: {state.user_display_name()} ({state.role()})", style="font-size: 12px; color: #4A5568;"),
                style="display: flex; flex-direction: column; align-items: flex-start;"
            ),
            style="display: flex; align-items: center;"
        ),
        ui.div(
            ui.tags.button(
                ui.tags.i(class_="fa-solid fa-bullhorn", style="margin-right: 6px; color: #1A202C; font-size: 14px;"),
                "Panduan & Logic",
                onclick="Shiny.setInputValue('btn_open_panduan_modal', Math.random(), {priority: 'event'})",
                style="background: #E2E8F0; color: #1A202C; border: none; padding: 6px 14px; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 13px;"
            ),
            ui.div(
                ui.div(
                    ui.div(style="width: 8px; height: 8px; background: #10B981; border-radius: 50%; margin-right: 6px;", class_="blink-online"),
                    ui.span("ONLINE", style="font-size: 12px; font-weight: 800; color: #065F46;"),
                    style="display: flex; align-items: center;"
                ),
                ui.div(
                    ui.span(str(state.login_timestamp_ms()), id="login-time-store", style="display: none;"),
                    ui.tags.i(class_="fa-regular fa-clock", style="font-size: 12px; color: #4A5568; margin-right: 4px;"),
                    ui.span("00:00:00", id="live-timer", style="color: #4A5568; font-weight: bold; font-size: 12px; font-family: monospace;"),
                    style="display: flex; align-items: center; justify-content: center;"
                ),
                style="display: flex; flex-direction: column; align-items: center; gap: 2px;"
            ),
            style="display: flex; align-items: center; gap: 1.25rem;"
        ),
        style="padding: 12px 20px; background: #D1FAE5; border: 1.5px solid #A7F3D0; border-radius: 16px; display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 1rem;"
    )

# ==============================================================================
# 9. ROOT UI & SERVER CONTROLLER
# ==============================================================================
app_ui = ui.page_fluid(
    CUSTOM_HEAD,
    ui.output_ui("global_loading_overlay_ui"),
    ui.output_ui("global_success_modal_ui"),
    ui.output_ui("global_error_modal_ui"),
    ui.output_ui("main_root_container"),
    style="padding: 0; margin: 0; background-color: #111318;"
)

def server(input: Inputs, output: Outputs, session: Session):
    state = AppState()

    # --- MODAL DISMISS EVENTS ---
    @reactive.Effect
    @reactive.event(input.close_success_modal_event)
    def _on_close_success_modal():
        state.show_success_modal.set(False)

    @reactive.Effect
    @reactive.event(input.close_error_modal_event)
    def _on_close_error_modal():
        state.show_error_modal.set(False)
        state.error_modal_message.set("")

    # --- UNIVERSAL RENDER MODALS & SPINNER ---
    @render.ui
    def global_success_modal_ui():
        return success_modal(state.show_success_modal())

    @render.ui
    def global_error_modal_ui():
        return error_modal(state.show_error_modal(), state.error_modal_message())

    @render.ui
    def global_loading_overlay_ui():
        return render_reflex_loading_overlay(state.is_loading())

    # --- LOGIN & LOGOUT ACTIONS ---
    @reactive.Effect
    @reactive.event(input.btn_submit_login)
    def _login_event():
        data = input.btn_submit_login()
        u = data.get("user", "")
        p = data.get("pass", "")
        success, msg = state.handle_login(u, p)
        if success:
            state.load_ongkir_data()
            ui.notification_show(msg, type="message", duration=4)
        else:
            state.trigger_error(msg)
            ui.notification_show(msg, type="error", duration=4)

    @reactive.Effect
    @reactive.event(input.btn_execute_logout)
    def _logout_event():
        state.logout()
        ui.notification_show("Anda telah keluar dari sistem.", type="warning", duration=4)

    # --- SIDEBAR & NAVIGATION ---
    @reactive.Effect
    @reactive.event(input.select_menu_item)
    def _nav_event():
        state.set_main_menu(input.select_menu_item())

    @reactive.Effect
    @reactive.event(input.btn_toggle_sidebar)
    def _side_toggle():
        state.toggle_sidebar()

    @reactive.Effect
    @reactive.event(input.toggle_dropdown_section)
    def _drop_toggle():
        state.toggle_dropdown(input.toggle_dropdown_section())

    @reactive.Effect
    @reactive.event(input.btn_open_panduan_modal)
    def _panduan_modal():
        cur = state.main_menu()
        if cur == "Stock Minus":
            guide_body = ui.div(
                ui.tags.details(
                    ui.tags.summary("📋 Informasi Format File"),
                    ui.div(
                        ui.tags.strong("Format yang diharapkan:"),
                        ui.tags.ul(ui.tags.li("Download Multiple Adjusmet dari Jezpro dan pilih ", ui.tags.strong("Termasuk yang sudah habis"))),
                        class_="accordion-content"
                    ),
                    open=True
                ),
                ui.tags.details(
                    ui.tags.summary("💡 Logic Thinking"),
                    ui.div(
                        ui.tags.strong("Alur Process Compare Stock Minus:"),
                        ui.tags.ol(
                            ui.tags.li("Mengambil SKU yang memiliki Qty System minus (-)"),
                            ui.tags.li("Lalu SKU yang memiliki QTY Minus (-) tersebut akan di lakukan shuffle covering Stock"),
                            ui.tags.li("Dimana terdapat Bin prioritas untuk shuffle Covering Stock (All Stagging, Karantina)"),
                            ui.tags.li("Dan jika minus terjadi di Gudang lt.2 maka akan prioritas mengambil BIN Toko begitupun sebaliknya"),
                            ui.tags.li("Lalu jika tidak ditemukan di BIN Prioritas maka akan mengambil random BIN kecuali LIVE, Offline dan Online"),
                            ui.tags.li("Jika sudah ditemukan SKU dan Qty yang bisa covering maka akan dibuatkan list Set up"),
                            ui.tags.li("Dan jika tidak bisa diselesaikan lewat set up maka sistem akan memasukkan kedalam item need justifikasi dan perlu analisa lebih lanjut")
                        ),
                        class_="accordion-content"
                    ),
                    open=True
                )
            )
        elif cur == "Putaway System":
            guide_body = ui.div(
                ui.tags.details(
                    ui.tags.summary("📋 Informasi Format File"),
                    ui.div(
                        ui.tags.strong("Format yang diharapkan:"),
                        ui.tags.ul(
                            ui.tags.li(ui.tags.strong("DATA SCAN PUTAWAY: "), "Kolom A = BIN, Kolom B = SKU, Kolom C = QTY SCAN"),
                            ui.tags.li(ui.tags.strong("DATA PUTAWAY: "), "Sesuai yang ada pada template Jezpro.")
                        ),
                        class_="accordion-content"
                    ),
                    open=True
                ),
                ui.tags.details(
                    ui.tags.summary("💡 Logic Thinking"),
                    ui.div(
                        ui.tags.strong("Alur Compare Putaway:"),
                        ui.tags.ol(
                            ui.tags.li("SKU di file data scan akan dicompare dengan SKU yang ada di FIle data BIN Putaway"),
                            ui.tags.li("Tiap unique SKU teratas di File data scan akan mendapatkan alokasi penuh"),
                            ui.tags.li("Untuk SKU yang tidak mendapatkan alokasi maka akan ditulis dengan note ", ui.tags.strong("PERLU CEK MANUAL"), " untuk mengetahui apakah ada double data scan atau item belum terset up di BIN PUTAWAY"),
                            ui.tags.li("List Set up akan dibuatkan otomatis oleh system dengan BIN awal diambil dari BIN di file Putaway dan BIN tujuan disesuaikan dengan BIN yang ada di data scan")
                        ),
                        class_="accordion-content"
                    ),
                    open=True
                )
            )
        else:
            guide_body = ui.div(
                ui.tags.i(class_="fa-regular fa-folder-open", style="font-size: 40px; color: #CBD5E0; margin-bottom: 8px;"),
                ui.p(f"Panduan dan Logic untuk halaman '{cur}' belum tersedia.", style="color: #718096; font-style: italic;"),
                style="text-align: center; padding: 2rem;"
            )

        modal = ui.modal(
            guide_body,
            title=ui.div(ui.tags.i(class_="fa-solid fa-book-open", style="color: #C5A059; margin-right: 8px;"), "Panduan & Logic ERP Logistik"),
            easy_close=True,
            footer=ui.modal_button("Tutup", class_="btn-red-gradient")
        )
        ui.modal_show(modal)

    # --- DYNAMIC ACTION BUTTONS & FILE BADGES (NO RE-RENDER UPLOADER) ---
    @render.ui
    def stock_minus_action_btn_ui():
        f = input.upload_stock_file() if "upload_stock_file" in input else None
        if f and len(f) > 0:
            file_name = f[0]["name"]
            size_kb = round(f[0]["size"] / 1024, 1) if "size" in f[0] else 0
            return ui.div(
                ui.div(
                    ui.tags.i(class_="fa-solid fa-file-excel", style="color: #10B981; font-size: 16px; margin-right: 8px;"),
                    ui.span("File Terpilih: ", style="color: #4A5568; font-size: 13px; font-weight: bold;"),
                    ui.span(f"{file_name} ({size_kb} KB)", style="color: #10B981; font-size: 13px; font-weight: 800;"),
                    style="display: flex; align-items: center;"
                ),
                ui.input_action_button(
                    "btn_process_stock_minus",
                    ui.tags.span(ui.tags.i(class_="fa-solid fa-play", style="margin-right: 6px; font-size: 14px;"), "PROSES DATA"),
                    class_="btn-red-gradient",
                    style="padding: 0.75rem 1.5rem; font-weight: bold; border-radius: 6px;"
                ),
                style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin-top: 1rem;"
            )
        else:
            return ui.div(
                ui.tags.button(
                    ui.tags.i(class_="fa-solid fa-lock", style="margin-right: 6px; font-size: 14px;"),
                    "PILIH FILE UNTUK MEMULAI",
                    disabled=True,
                    class_="btn-locked",
                    style="padding: 0.75rem 1.5rem;"
                ),
                style="display: flex; justify-content: flex-end; width: 100%; margin-top: 1rem;"
            )

    @render.ui
    def putaway_action_btn_ui():
        f_ds = input.ds_putaway_file() if "ds_putaway_file" in input else None
        f_as = input.asal_putaway_file() if "asal_putaway_file" in input else None
        has_ds = f_ds is not None and len(f_ds) > 0
        has_as = f_as is not None and len(f_as) > 0

        if has_ds and has_as:
            return ui.div(
                ui.div(
                    ui.div(
                        ui.tags.i(class_="fa-solid fa-check-circle", style="color: #10B981; margin-right: 6px;"),
                        ui.span(f"DS: {f_ds[0]['name']}", style="color: #2D3748; font-size: 12px; font-weight: bold; margin-right: 12px;"),
                        ui.tags.i(class_="fa-solid fa-check-circle", style="color: #10B981; margin-right: 6px;"),
                        ui.span(f"ASAL: {f_as[0]['name']}", style="color: #2D3748; font-size: 12px; font-weight: bold;"),
                        style="display: flex; align-items: center;"
                    )
                ),
                ui.input_action_button(
                    "btn_compare_putaway",
                    ui.tags.span(ui.tags.i(class_="fa-solid fa-play", style="margin-right: 6px; font-size: 14px;"), "COMPARE PUTAWAY"),
                    class_="btn-red-gradient",
                    style="padding: 0.75rem 1.5rem; font-weight: bold; border-radius: 6px;"
                ),
                style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin-top: 0.5rem;"
            )
        else:
            return ui.div(
                ui.tags.button(
                    ui.tags.i(class_="fa-solid fa-lock", style="margin-right: 6px; font-size: 14px;"),
                    "PILIH KEDUA FILE UNTUK MEMULAI",
                    disabled=True,
                    class_="btn-locked",
                    style="padding: 0.75rem 1.5rem;"
                ),
                style="display: flex; justify-content: flex-end; width: 100%; margin-top: 0.5rem;"
            )

    @render.ui
    def batch_csv_action_btn_ui():
        f = input.upload_csv_batch() if "upload_csv_batch" in input else None
        if f and len(f) > 0:
            return ui.div(
                ui.div(
                    ui.tags.i(class_="fa-solid fa-file-csv", style="color: #10B981; font-size: 16px; margin-right: 6px;"),
                    ui.span(f"File: {f[0]['name']}", style="color: #276749; font-weight: bold; font-size: 13px;"),
                    style="margin-bottom: 8px; display: flex; align-items: center; justify-content: center;"
                ),
                ui.input_action_button(
                    "btn_execute_batch_upload",
                    "⚡ EXECUTE BATCH UPLOAD",
                    style="background: #1A202C; color: #FFFFFF !important; font-weight: 800; border-radius: 10px; cursor: pointer; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15); width: 100%; height: 48px; border: none; font-size: 14px;"
                )
            )
        else:
            return ui.input_action_button(
                "btn_execute_batch_upload",
                "⚡ EXECUTE BATCH UPLOAD",
                style="background: #1A202C; color: #FFFFFF !important; font-weight: 800; border-radius: 10px; cursor: pointer; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15); width: 100%; height: 48px; border: none; font-size: 14px;"
            )

    # --- RENDER HASIL STOCK MINUS & PUTAWAY ---
    @render.ui
    def stock_minus_results_container():
        if not state.stock_minus_processed():
            return ui.div()
        return ui.div(
            ui.div(
                dark_metric_box("TOTAL QTY MINUS", f"{state.total_qty_minus()}", "#E53E3E"),
                dark_metric_box("TERCOVER", f"{state.total_tercover()}", "#38A169"),
                dark_metric_box("SISA ADJ", f"{state.total_sisa_adj()}", "#DD6B20"),
                style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 0.75rem; width: 100%; margin-bottom: 1.25rem;"
            ),
            ui.navset_card_tab(
                ui.nav_panel(
                    "MINUS AWAL",
                    ui.div(
                        ui.div(
                            ui.download_button(
                                "btn_dl_minus_awal",
                                ui.tags.span(ui.tags.i(class_="fa-solid fa-download", style="margin-right: 6px; font-size: 14px;"), "Download Excel"),
                                style="background-color: #10B981; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 6px 14px; cursor: pointer; box-shadow: 0 2px 4px rgba(0,0,0,0.1);"
                            ),
                            style="display: flex; justify-content: flex-end; width: 100%; margin-bottom: 0.5rem;"
                        ),
                        render_clean_table(state.df_minus_awal_headers(), state.df_minus_awal_rows()),
                        style="padding: 0.75rem 0;"
                    )
                ),
                ui.nav_panel(
                    "TEMPLATE SET UP",
                    ui.div(
                        ui.div(
                            ui.download_button(
                                "btn_dl_set_up",
                                ui.tags.span(ui.tags.i(class_="fa-solid fa-download", style="margin-right: 6px; font-size: 14px;"), "Download Excel"),
                                style="background-color: #10B981; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 6px 14px; cursor: pointer; box-shadow: 0 2px 4px rgba(0,0,0,0.1);"
                            ),
                            style="display: flex; justify-content: flex-end; width: 100%; margin-bottom: 0.5rem;"
                        ),
                        render_clean_table(state.df_set_up_headers(), state.df_set_up_rows()),
                        style="padding: 0.75rem 0;"
                    )
                ),
                ui.nav_panel(
                    "JUSTIFIKASI",
                    ui.div(
                        ui.div(
                            ui.download_button(
                                "btn_dl_justifikasi",
                                ui.tags.span(ui.tags.i(class_="fa-solid fa-download", style="margin-right: 6px; font-size: 14px;"), "Download Excel"),
                                style="background-color: #10B981; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 6px 14px; cursor: pointer; box-shadow: 0 2px 4px rgba(0,0,0,0.1);"
                            ),
                            style="display: flex; justify-content: flex-end; width: 100%; margin-bottom: 0.5rem;"
                        ),
                        render_clean_table(state.df_need_adj_headers(), state.df_need_adj_rows()),
                        style="padding: 0.75rem 0;"
                    )
                )
            ),
            style="width: 100%;"
        )

    @render.ui
    def putaway_results_container():
        if not state.putaway_processed():
            return ui.div()

        kurang_rows = state.df_kurang_rows()
        if kurang_rows and len(kurang_rows) > 0:
            kurang_content = render_clean_table(state.df_kurang_headers(), kurang_rows)
        else:
            kurang_content = ui.div("✅ Semua Tercover!", style="background: #C6F6D5; color: #38A169; font-weight: bold; padding: 1rem; border-radius: 8px; text-align: center;")

        out_rows = state.df_out_rows()
        if out_rows and len(out_rows) > 0:
            out_content = render_clean_table(state.df_out_headers(), out_rows)
        else:
            out_content = ui.div("✅ Tidak ada Outstanding!", style="background: #C6F6D5; color: #38A169; font-weight: bold; padding: 1rem; border-radius: 8px; text-align: center;")

        return ui.div(
            ui.hr(style="margin: 1.5rem 0 1rem 0; border-color: #E2E8F0;"),
            ui.h4("📋 RINGKASAN HASIL", style="font-size: 16px; color: #010B13; font-weight: 800; margin: 1rem 0;"),
            ui.div(
                dark_metric_box("Qty System Putaway", f"{state.putaway_qty_system()}", "#E53E3E"),
                dark_metric_box("Total Tersetup", f"{state.putaway_total_setup()}", "#38A169"),
                dark_metric_box("Kurang Setup", f"{state.putaway_kurang_setup()}", "#DD6B20"),
                dark_metric_box("Sisa Stok Putaway", f"{state.putaway_sisa_stok()}", "#3182CE"),
                style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 0.75rem; width: 100%; margin-bottom: 1.25rem;"
            ),
            ui.div(
                ui.download_button(
                    "btn_dl_putaway_report",
                    ui.tags.span(ui.tags.i(class_="fa-solid fa-download", style="margin-right: 6px; font-size: 14px;"), "DOWNLOAD REPORT LENGKAP"),
                    style="background-color: #10B981; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 8px 16px; cursor: pointer; box-shadow: 0 2px 4px rgba(0,0,0,0.1);"
                ),
                style="display: flex; justify-content: flex-end; width: 100%; margin-bottom: 0.5rem;"
            ),
            ui.navset_card_tab(
                ui.nav_panel("Hasil Compare", ui.div(render_clean_table(state.df_comp_headers(), state.df_comp_rows()), style="padding: 0.75rem 0;")),
                ui.nav_panel("List Setup", ui.div(render_clean_table(state.df_plist_headers(), state.df_plist_rows()), style="padding: 0.75rem 0;")),
                ui.nav_panel("Kurang Setup", ui.div(kurang_content, style="padding: 0.75rem 0;")),
                ui.nav_panel("Outstanding", ui.div(out_content, style="padding: 0.75rem 0;"))
            ),
            style="width: 100%;"
        )

    # --- ASYNC PROCESS HANDLERS ---
    @reactive.Effect
    @reactive.event(input.btn_save_ongkir_manual)
    async def _save_manual():
        d = input.btn_save_ongkir_manual()
        state.set_loading(True)
        await asyncio.sleep(0.05)
        succ, msg = state.save_single_ongkir(d.get("supplier", ""), d.get("ekspedisi", ""), d.get("koli", "1"), d.get("ongkir", "0"), d.get("tgl", ""))
        state.set_loading(False)
        if succ:
            state.trigger_success()
        else:
            state.trigger_error(msg)

    @reactive.Effect
    @reactive.event(input.btn_execute_batch_upload)
    async def _save_batch():
        f = input.upload_csv_batch()
        if not f:
            state.trigger_error("Pilih file CSV terlebih dahulu!")
            return
        state.set_loading(True)
        await asyncio.sleep(0.05)
        with open(f[0]["datapath"], "rb") as fp:
            succ, msg = state.batch_upload_csv(fp.read())
        state.set_loading(False)
        if succ:
            state.trigger_success()
        else:
            state.trigger_error(msg)

    @reactive.Effect
    @reactive.event(input.toggle_row_id)
    def _toggle_chk():
        state.toggle_select_id(str(input.toggle_row_id()))

    @reactive.Effect
    @reactive.event(input.change_filter_ekspedisi)
    def _filter_chg():
        state.filter_ekspedisi.set(input.change_filter_ekspedisi())

    @reactive.Effect
    @reactive.event(input.btn_open_delete_modal)
    def _del_modal():
        modal = ui.modal(
            ui.p("Apakah Anda yakin ingin menghapus data terpilih secara permanen dari database Supabase?"),
            title="⚠️ Konfirmasi Hapus Data",
            easy_close=True,
            footer=ui.div(
                ui.modal_button("Batal"),
                ui.tags.button("Ya, Hapus Permanen", onclick="Shiny.setInputValue('btn_confirm_delete_permanent', Math.random(), {priority: 'event'})", style="background: #E53E3E; color: white; border: none; padding: 6px 12px; border-radius: 6px; margin-left: 8px; font-weight: bold; cursor: pointer;"),
                style="display: flex; justify-content: flex-end;"
            )
        )
        ui.modal_show(modal)

    @reactive.Effect
    @reactive.event(input.btn_confirm_delete_permanent)
    async def _del_exec():
        state.set_loading(True)
        await asyncio.sleep(0.05)
        succ, msg = state.execute_delete()
        state.set_loading(False)
        ui.modal_remove()
        if succ:
            state.trigger_success()
            ui.notification_show(msg, type="message", duration=4)
        else:
            state.trigger_error(msg)
            ui.notification_show(msg, type="error", duration=4)

    @reactive.Effect
    @reactive.event(input.btn_process_stock_minus)
    async def _proc_stock_file():
        f = input.upload_stock_file()
        if not f:
            state.trigger_error("Pilih file Stock Minus terlebih dahulu!")
            return
        state.set_loading(True)
        await asyncio.sleep(0.05)
        with open(f[0]["datapath"], "rb") as fp:
            succ, msg = state.process_stock_minus_file(fp.read(), f[0]["name"])
        state.set_loading(False)
        if succ:
            state.trigger_success()
        else:
            state.trigger_error(msg)

    @render.download(filename="Data_Minus_Awal.xlsx")
    def btn_dl_minus_awal():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            state._raw_df_minus_awal.to_excel(writer, index=False)
        buf.seek(0)
        return buf.getvalue()

    @render.download(filename="Template_Set_Up.xlsx")
    def btn_dl_set_up():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            state._raw_df_set_up.to_excel(writer, index=False)
        buf.seek(0)
        return buf.getvalue()

    @render.download(filename="Data_Justifikasi.xlsx")
    def btn_dl_justifikasi():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            state._raw_df_need_adj.to_excel(writer, index=False)
        buf.seek(0)
        return buf.getvalue()

    @reactive.Effect
    @reactive.event(input.select_area_putaway)
    def _area_sel():
        state.area_putaway.set(input.select_area_putaway())

    @reactive.Effect
    @reactive.event(input.btn_compare_putaway)
    async def _proc_putaway_files():
        f_ds = input.ds_putaway_file()
        f_as = input.asal_putaway_file()
        if not f_ds or not f_as:
            state.trigger_error("Kedua file (DS Putaway & Asal Bin) wajib diupload!")
            return
        state.set_loading(True)
        await asyncio.sleep(0.05)
        with open(f_ds[0]["datapath"], "rb") as fp_ds, open(f_as[0]["datapath"], "rb") as fp_as:
            succ, msg = state.process_putaway_compare(fp_ds.read(), f_ds[0]["name"], fp_as.read(), f_as[0]["name"])
        state.set_loading(False)
        if succ:
            state.trigger_success()
        else:
            state.trigger_error(msg)

    @render.download(filename="REPORT_PUTAWAY_SYSTEM.xlsx")
    def btn_dl_putaway_report():
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            state._raw_df_comp.to_excel(writer, sheet_name='COMPARE', index=False)
            state._raw_df_plist.to_excel(writer, sheet_name='PUTAWAY_LIST', index=False)
            state._raw_df_kurang.to_excel(writer, sheet_name='KURANG_SETUP', index=False)
            state._raw_df_out.to_excel(writer, sheet_name='OUTSTANDING', index=False)
            state._raw_df_updated.to_excel(writer, sheet_name='SISA_STOK_SYSTEM', index=False)
        buf.seek(0)
        return buf.getvalue()

    # --- ROOT CONTAINER ROUTER (HANYA REAKTIF PADA MENU & LOGIN) ---
    @render.ui
    def main_root_container():
        if not state.logged_in():
            return login_page()

        content_type = state.get_active_content_type()

        if content_type == "dashboard_ongkir":
            page_content = main_dashboard_view(state)
        elif content_type == "stock_minus":
            page_content = stock_minus_view(state)
        elif content_type == "putaway_system":
            page_content = putaway_view(state)
        elif content_type == "access_denied":
            page_content = ui.div(
                ui.h2("⛔ Akses Ditolak", style="font-size: 28px; color: #E53E3E; font-weight: bold; margin-bottom: 0.5rem;"),
                ui.p("Maaf, halaman ini dibatasi hak aksesnya.", style="color: #718096; font-size: 15px;"),
                style="padding: 3rem; text-align: center; height: 70vh; display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%;"
            )
        else:
            page_content = ui.div(
                ui.h2(f"Halaman: {state.main_menu()}", style="font-size: 28px; color: #1A202C; font-weight: bold; margin-bottom: 0.5rem;"),
                ui.p("Halaman ini sedang dalam tahap pengembangan.", style="color: #718096; font-size: 15px;"),
                style="padding: 3rem; text-align: center; height: 70vh; display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%;"
            )

        return ui.div(
            sidebar(state),
            ui.div(
                global_header(state),
                page_content,
                style="flex: 1; height: 100vh; overflow-y: auto; padding: 1.5rem; background-color: #F7FAFC;"
            ),
            style="display: flex; width: 100vw; height: 100vh; overflow: hidden; background-color: #111318;"
        )

# ==============================================================================
# 10. INISIALISASI APLIKASI
# ==============================================================================
app = App(app_ui, server)