import io
import time
from datetime import datetime
import numpy as np       
import pandas as pd
from shiny import reactive
from config import get_supabase, safe_int, load_data_from_info, format_datetime_wib


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
        self.filter_periode = reactive.Value("SEMUA")
        self.active_ongkir_tab = reactive.Value("tab_input")
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

        # --- CYCLE COUNT ANALYZER STATE ---
        self.cca_branch = reactive.Value("SURABAYA")
        self.cca_step1_done = reactive.Value(False)
        self.cca_qty_real_plus = reactive.Value(0)
        self.cca_qty_sys_plus = reactive.Value(0)

        self.df_cca_scan_headers = reactive.Value([])
        self.df_cca_scan_rows = reactive.Value([])
        self.df_cca_stock_headers = reactive.Value([])
        self.df_cca_stock_rows = reactive.Value([])
        self.df_cca_real_headers = reactive.Value([])
        self.df_cca_real_rows = reactive.Value([])
        self.df_cca_sys_headers = reactive.Value([])
        self.df_cca_sys_rows = reactive.Value([])

        self._raw_df_cca_scan = pd.DataFrame()
        self._raw_df_cca_stock = pd.DataFrame()
        self._raw_df_cca_real_plus = pd.DataFrame()
        self._raw_df_cca_sys_plus = pd.DataFrame()
        self._cca_map_dict = {}

        # Step 2: Allocation
        self.cca_step2_done = reactive.Value(False)
        self.df_cca_alloc_headers = reactive.Value([])
        self.df_cca_alloc_rows = reactive.Value([])
        self.df_cca_sys_upd_headers = reactive.Value([])
        self.df_cca_sys_upd_rows = reactive.Value([])
        self.df_cca_setup_real_headers = reactive.Value([])
        self.df_cca_setup_real_rows = reactive.Value([])

        self._raw_df_cca_alloc = pd.DataFrame()
        self._raw_df_cca_sys_upd = pd.DataFrame()
        self._raw_df_cca_setup_real = pd.DataFrame()

        # Step 3: Recon Reports
        self.cca_step3_done = reactive.Value(False)
        self.df_cca_rec_real_headers = reactive.Value([])
        self.df_cca_rec_real_rows = reactive.Value([])
        self.df_cca_rec_sys_headers = reactive.Value([])
        self.df_cca_rec_sys_rows = reactive.Value([])

        self._raw_df_cca_rec_real = pd.DataFrame()
        self._raw_df_cca_rec_sys = pd.DataFrame()

        # Step 4: Recon Real + Analysis
        self.cca_step4_done = reactive.Value(False)
        self.cca_qty_need_adj = reactive.Value(0)
        self.cca_sku_need_adj = reactive.Value(0)
        self.df_cca_adj4_headers = reactive.Value([])
        self.df_cca_adj4_rows = reactive.Value([])
        self._raw_df_cca_adj4 = pd.DataFrame()

        # Step 5: Karantina Generator
        self.cca_step5_done = reactive.Value(False)
        self.cca_qty_karantina = reactive.Value(0)
        self.cca_sku_karantina = reactive.Value(0)
        self.df_cca_karantina_headers = reactive.Value([])
        self.df_cca_karantina_rows = reactive.Value([])
        self.df_cca_check5_headers = reactive.Value([])
        self.df_cca_check5_rows = reactive.Value([])

        self._raw_df_cca_karantina = pd.DataFrame()
        self._raw_df_cca_check5 = pd.DataFrame()

        # Step 6: Miss Location Report
        self.cca_step6_done = reactive.Value(False)
        self.cca_sku_miss_loc = reactive.Value(0)
        self.cca_qty_miss_loc = reactive.Value(0)
        self.df_cca_miss_loc_headers = reactive.Value([])
        self.df_cca_miss_loc_rows = reactive.Value([])
        self.df_cca_sum_miss_headers = reactive.Value([])
        self.df_cca_sum_miss_rows = reactive.Value([])

        self._raw_df_cca_miss_loc = pd.DataFrame()
        self._raw_df_cca_sum_miss = pd.DataFrame()

        # --- COMPARE RTO STATE ---
        self.rto_step1_done = reactive.Value(False)
        self.rto_q_total = reactive.Value(0)
        self.rto_q_sesuai = reactive.Value(0)
        self.rto_q_lebih = reactive.Value(0)
        self.rto_q_kurang = reactive.Value(0)
        self.df_rto_ds_headers = reactive.Value([])
        self.df_rto_ds_rows = reactive.Value([])
        self.df_rto_selisih_headers = reactive.Value([])
        self.df_rto_selisih_rows = reactive.Value([])
        self._raw_df_rto_ds = pd.DataFrame()
        self._raw_df_rto_selisih = pd.DataFrame()
        self._raw_df_rto_app = pd.DataFrame()

        # Step 2 & 3: Draft Compared
        self.rto_draft_done = reactive.Value(False)
        self.rto_q_draft_total = reactive.Value(0)
        self.rto_q_ok = reactive.Value(0)
        self.rto_q_edit = reactive.Value(0)
        self.rto_q_del = reactive.Value(0)
        self.df_rto_draft_comp_headers = reactive.Value([])
        self.df_rto_draft_comp_rows = reactive.Value([])
        self._raw_df_rto_draft_comp = pd.DataFrame()

        # Step 4: New Draft
        self.rto_new_draft_done = reactive.Value(False)
        self.rto_q_new_draft_total = reactive.Value(0)
        self.df_rto_new_draft_headers = reactive.Value([])
        self.df_rto_new_draft_rows = reactive.Value([])
        self._raw_df_rto_new_draft = pd.DataFrame()

        # --- STOCK OPNAME ANALYZER STATE ---
        self.so_step1_done = reactive.Value(False)
        self.so_qty_real_plus = reactive.Value(0)
        self.so_qty_sys_plus = reactive.Value(0)

        self.df_so_scan_headers = reactive.Value([])
        self.df_so_scan_rows = reactive.Value([])
        self.df_so_stock_headers = reactive.Value([])
        self.df_so_stock_rows = reactive.Value([])
        self.df_so_real_headers = reactive.Value([])
        self.df_so_real_rows = reactive.Value([])
        self.df_so_sys_headers = reactive.Value([])
        self.df_so_sys_rows = reactive.Value([])

        self._raw_df_so_scan = pd.DataFrame()
        self._raw_df_so_stock = pd.DataFrame()
        self._raw_df_so_real_plus = pd.DataFrame()
        self._raw_df_so_sys_plus = pd.DataFrame()
        self._so_map_dict = {}

        # Step 2 & 3: Allocation & Recon
        self.so_step2_done = reactive.Value(False)
        self.df_so_alloc_headers = reactive.Value([])
        self.df_so_alloc_rows = reactive.Value([])
        self.df_so_sys_upd_headers = reactive.Value([])
        self.df_so_sys_upd_rows = reactive.Value([])
        self.df_so_setup_real_headers = reactive.Value([])
        self.df_so_setup_real_rows = reactive.Value([])
        self.df_so_rec_real_headers = reactive.Value([])
        self.df_so_rec_real_rows = reactive.Value([])
        self.df_so_rec_sys_headers = reactive.Value([])
        self.df_so_rec_sys_rows = reactive.Value([])

        self._raw_df_so_alloc = pd.DataFrame()
        self._raw_df_so_sys_upd = pd.DataFrame()
        self._raw_df_so_setup_real = pd.DataFrame()
        self._raw_df_so_rec_real = pd.DataFrame()
        self._raw_df_so_rec_sys = pd.DataFrame()

        # Step 4: Final Adjustment + Process
        self.so_step4_done = reactive.Value(False)
        self.so_step4_setup_done = reactive.Value(False)
        self.df_so_mult_headers = reactive.Value([])
        self.df_so_mult_rows = reactive.Value([])
        self.df_so_sing_headers = reactive.Value([])
        self.df_so_sing_rows = reactive.Value([])
        self.df_so_res4_headers = reactive.Value([])
        self.df_so_res4_rows = reactive.Value([])
        self.df_so_setup4_headers = reactive.Value([])
        self.df_so_setup4_rows = reactive.Value([])
        self.df_so_miss4_headers = reactive.Value([])
        self.df_so_miss4_rows = reactive.Value([])

        self._raw_df_so_mult = pd.DataFrame()
        self._raw_df_so_sing = pd.DataFrame()
        self._raw_df_so_res4 = pd.DataFrame()
        self._raw_df_so_setup4 = pd.DataFrame()
        self._raw_df_so_miss4 = pd.DataFrame()

        # Step 5: Karantina Generator
        self.so_step5_done = reactive.Value(False)
        self.so_qty_karantina = reactive.Value(0)
        self.so_sku_karantina = reactive.Value(0)
        self.df_so_karantina_headers = reactive.Value([])
        self.df_so_karantina_rows = reactive.Value([])
        self.df_so_check5_headers = reactive.Value([])
        self.df_so_check5_rows = reactive.Value([])

        self._raw_df_so_karantina = pd.DataFrame()
        self._raw_df_so_check5 = pd.DataFrame()

        # Step 6A: Miss Location Report
        self.so_step6a_done = reactive.Value(False)
        self.so_sku_miss_loc = reactive.Value(0)
        self.so_qty_miss_loc = reactive.Value(0)
        self.df_so_miss_loc_headers = reactive.Value([])
        self.df_so_miss_loc_rows = reactive.Value([])
        self.df_so_sum_miss_headers = reactive.Value([])
        self.df_so_sum_miss_rows = reactive.Value([])

        self._raw_df_so_miss_loc = pd.DataFrame()
        self._raw_df_so_sum_miss = pd.DataFrame()

        # Step 6B: Summary Adjustment Report
        self.so_step6b_done = reactive.Value(False)
        self.so_adj_val_p = reactive.Value(0)
        self.so_adj_val_m = reactive.Value(0)
        self.so_adj_val_net = reactive.Value(0)
        self.so_adj_qty_p = reactive.Value(0)
        self.so_adj_qty_m = reactive.Value(0)
        self.so_adj_sku_tot = reactive.Value(0)
        self.df_so_adj_detail_headers = reactive.Value([])
        self.df_so_adj_detail_rows = reactive.Value([])
        self.df_so_adj_sum_headers = reactive.Value([])
        self.df_so_adj_sum_rows = reactive.Value([])

        self._raw_df_so_adj_detail = pd.DataFrame()
        self._raw_df_so_adj_sum = pd.DataFrame()

        # --- JUSTIFICATION SO STATE ---
        self.jso_processed = reactive.Value(False)
        self.jso_c_undef = reactive.Value(0)
        self.jso_c_sys = reactive.Value(0)
        self.jso_c_adj = reactive.Value(0)
        self.jso_c_rto = reactive.Value(0)
        self.jso_c_rekon = reactive.Value(0)
        self.df_jso_headers = reactive.Value([])
        self.df_jso_rows = reactive.Value([])
        self._raw_df_jso_res = pd.DataFrame()

        # --- CROSS CHECK REAL & SYSTEM (MATCHING KARANTINA) ---
        self.crs_processed = reactive.Value(False)
        self.crs_total_real = reactive.Value(0)
        self.crs_total_matched = reactive.Value(0)
        self.crs_total_unmatched = reactive.Value(0)
        self.crs_system_left = reactive.Value(0)
        self.crs_status_choices = reactive.Value([])

        self.df_crs_headers = reactive.Value([])
        self.df_crs_rows = reactive.Value([])
        self._raw_df_crs_all = pd.DataFrame()
        self._raw_df_crs_filtered = pd.DataFrame()

        # --- BALANCING STOCK & DYNAMIC ALLOCATION STATE ---
        self.bs_processed = reactive.Value(False)
        self.bs_total_sku = reactive.Value(0)
        self.bs_total_stock = reactive.Value(0)
        self.bs_sku_need_off = reactive.Value(0)
        self.bs_sku_need_on = reactive.Value(0)
        self.bs_qty_refill_total = reactive.Value(0)
        self.bs_perc_offline = reactive.Value(0.0)
        self.bs_perc_online = reactive.Value(0.0)

        self.df_bs_refill_headers = reactive.Value([])
        self.df_bs_refill_rows = reactive.Value([])
        self.df_bs_alloc_headers = reactive.Value([])
        self.df_bs_alloc_rows = reactive.Value([])
        self.df_bs_off_missing_headers = reactive.Value([])
        self.df_bs_off_missing_rows = reactive.Value([])
        self.df_bs_on_missing_headers = reactive.Value([])
        self.df_bs_on_missing_rows = reactive.Value([])

        self._raw_df_bs_refill = pd.DataFrame()
        self._raw_df_bs_alloc = pd.DataFrame()
        self._raw_df_bs_off_missing = pd.DataFrame()
        self._raw_df_bs_on_missing = pd.DataFrame()

        # --- PHYSICAL INVENTORY LIST STATE (UNIFIED) ---
        self.pil_mode = reactive.Value("")

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
            return ["Putaway System", "Compare RTO", "Purchase Order Receiving", "Instock Validation", "Compare Penerimaan RTO"]
        return ["Compare Penerimaan RTO", "Putaway System", "Purchase Order Receiving"]

    def get_menu_inventory(self) -> list[str]:
        if self.role() == "DC":
            return ["Stock Opname", "Cycle Count", "Justification SO", "Stock Minus", "Compare System", "Physical Inventory List", "Cross Check Real & System", "List Retur Out", "Reloc Koli to Koli"]
        return ["Stock Minus", "Cycle Count", "Compare System", "Justification SO"]

    def get_menu_reject(self) -> list[str]:
        return ["Defect & Reject Database"]

    def get_menu_extras(self) -> list[str]:
        if self.role() == "DC":
            return ["Balancing Stock", "Data Timbang Ongkir", "Database Ongkir In/Out", "Precentage Display", "Refill Toko"]
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
        elif cur_menu == "Cycle Count": return "cycle_count_analyzer"
        elif cur_menu == "Compare RTO": return "compare_rto"
        elif cur_menu == "Stock Opname": return "stock_opname"
        elif cur_menu == "Justification SO": return "justification_so"
        elif cur_menu in ["Cross Check Real & System", "Match Real & System"]: return "cross_check_real_sys"
        elif cur_menu == "Balancing Stock": return "balancing_stock"
        elif cur_menu == "Physical Inventory List": return "physical_inventory_list"
        return "under_development"


    # --- Ongkir Methods ---
    def load_ongkir_data(self):
        try:
            client = get_supabase()
            if client:
                res = client.table("shipping_costs").select("*").execute()
                if res.data:
                    df = pd.DataFrame(res.data)
                    # Otomatis ubah tanggal ISO Supabase ke format WIB
                    if "created_at" in df.columns:
                        df = format_datetime_wib(df, "created_at")
                    self.data_list.set(df.to_dict(orient="records"))
                else:
                    self.data_list.set([])
        except Exception as e:
            print("Supabase load error:", e)

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
        
        # 1. Filter Ekspedisi
        flt_eks = self.filter_ekspedisi()
        if flt_eks != "SEMUA":
            res = [x for x in res if str(x.get("ekspedisi", "")).upper() == flt_eks.upper()]
            
        # 2. Filter Periode Waktu
        flt_waktu = self.filter_periode()
        if flt_waktu != "SEMUA" and res:
            now = datetime.now()
            filtered_res = []
            for x in res:
                tgl_str = str(x.get("created_at", "")).strip()
                try:
                    # Parse format tanggal DD-MM-YYYY HH:MM
                    dt = pd.to_datetime(tgl_str, dayfirst=True)
                    if flt_waktu == "HARI INI":
                        if dt.date() == now.date():
                            filtered_res.append(x)
                    elif flt_waktu == "7 HARI TERAKHIR":
                        if (now - dt).days <= 7 and dt <= now:
                            filtered_res.append(x)
                    elif flt_waktu == "BULAN INI":
                        if dt.year == now.year and dt.month == now.month:
                            filtered_res.append(x)
                    elif flt_waktu == "BULAN LALU":
                        # Hitung bulan lalu
                        first_day_cur = now.replace(day=1)
                        last_month = first_day_cur - pd.Timedelta(days=1)
                        if dt.year == last_month.year and dt.month == last_month.month:
                            filtered_res.append(x)
                except Exception:
                    filtered_res.append(x)
            res = filtered_res

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
        
    def trigger_pc_sync_and_load(self):
        try:
            import urllib.request
            import json
            import time
            from config import SUPABASE_URL, SUPABASE_KEY

            # 1. Kirim Sinyal PENDING ke Supabase
            insert_url = f"{SUPABASE_URL}/rest/v1/sync_queue"
            req_ins = urllib.request.Request(
                insert_url,
                data=json.dumps({"status": "PENDING"}).encode('utf-8'),
                headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json", "Prefer": "return=representation"},
                method="POST"
            )
            with urllib.request.urlopen(req_ins, timeout=10) as resp:
                created_task = json.loads(resp.read().decode('utf-8'))
                task_id = created_task[0]["id"]

            # 2. Tunggu PC Kantor Menyelesaikan Download (Polling maksimal 25 detik)
            for _ in range(12):
                time.sleep(2)
                check_url = f"{SUPABASE_URL}/rest/v1/sync_queue?id=eq.{task_id}"
                req_chk = urllib.request.Request(check_url, headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"})
                with urllib.request.urlopen(req_chk, timeout=10) as resp_chk:
                    t_data = json.loads(resp_chk.read().decode('utf-8'))
                    if t_data and t_data[0]["status"] == "DONE":
                        break
            else:
                return False, "Timeout: PC Kantor belum menyala atau proses terlalu lama."

            # 3. Setelah PC Kantor Selesai, Baca File dari Supabase Storage
            return self.load_stock_minus_from_supabase()

        except Exception as e:
            return False, f"Gagal trigger PC kantor: {e}"
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

# ==========================================================================
    # CYCLE COUNT ANALYZER LOGIC & ALGORITHMS (LENGKAP STEP 1 - 6)
    # ==========================================================================

    # --- STEP 1: COMPARE SCAN VS STOCK ---
    def run_cca_step1(self, f_scan, f_stock, sub_sel, brand_sel, bin_sys_sel):
        try:
            df_s_raw = load_data_from_info(f_scan)
            df_t_raw = load_data_from_info(f_stock)

            if df_s_raw.empty or df_t_raw.empty:
                return False, "File Data Scan dan Stock System tidak boleh kosong!"

            # 1. Bersihkan Data Scan
            ds = df_s_raw.iloc[:, [0, 1, 2]].copy()
            ds.columns = ['BIN', 'SKU', 'QTY_SCAN']
            ds['BIN'] = ds['BIN'].astype(str).str.strip().str.upper()
            ds['SKU'] = ds['SKU'].astype(str).str.strip().str.upper()
            ds['QTY_SCAN'] = pd.to_numeric(ds['QTY_SCAN'], errors='coerce').fillna(0)

            # 2. Bersihkan & Filter Stock System
            dt = df_t_raw.copy()
            col_b, col_s, col_q_sys = dt.columns[1], dt.columns[2], dt.columns[9]

            if sub_sel and len(sub_sel) > 0 and dt.shape[1] > 6:
                dt = dt[dt.iloc[:, 6].astype(str).str.upper().isin([x.upper() for x in sub_sel])]
            if brand_sel and len(brand_sel) > 0 and dt.shape[1] > 3:
                dt = dt[dt.iloc[:, 3].astype(str).str.upper().isin([x.upper() for x in brand_sel])]
            if bin_sys_sel and len(bin_sys_sel) > 0 and dt.shape[1] > 1:
                dt = dt[dt.iloc[:, 1].astype(str).str.upper().apply(lambda x: any(c.upper() in x for c in bin_sys_sel))]

            dt[col_b] = dt[col_b].astype(str).str.strip().str.upper()
            dt[col_s] = dt[col_s].astype(str).str.strip().str.upper()
            dt[col_q_sys] = pd.to_numeric(dt[col_q_sys], errors='coerce').fillna(0)

            # 3. Compare Scan to Stock
            dt_sub = dt[[col_b, col_s, col_q_sys]].copy()
            dt_sub.columns = ['BIN', 'SKU', 'QTY_SYSTEM']
            dt_grouped = dt_sub.groupby(['BIN', 'SKU'], as_index=False)['QTY_SYSTEM'].sum()

            res_scan = ds.merge(dt_grouped, on=['BIN', 'SKU'], how='left').fillna(0)
            res_scan['DIFF'] = res_scan['QTY_SCAN'] - res_scan['QTY_SYSTEM']
            res_scan['NOTE'] = np.where(res_scan['DIFF'] > 0, "REAL +", np.where(res_scan['DIFF'] < 0, "SYSTEM +", "OK"))

            # 4. Compare Stock to Scan
            ds_g = ds.groupby(['BIN', 'SKU'], as_index=False)['QTY_SCAN'].sum()
            ds_g.columns = ['BIN_SCAN', 'SKU_SCAN', 'QTY_TOTAL_SCAN']

            dt_merged = dt.merge(ds_g, left_on=[col_b, col_s], right_on=['BIN_SCAN', 'SKU_SCAN'], how='left')
            dt_merged['QTY SO'] = dt_merged['QTY_TOTAL_SCAN'].fillna(0)
            dt_merged['DIFF'] = dt_merged[col_q_sys] - dt_merged['QTY SO']
            dt_merged['NOTE'] = np.where(dt_merged['DIFF'] > 0, "SYSTEM +", np.where(dt_merged['DIFF'] < 0, "REAL +", "OK"))
            res_stock = dt_merged.drop(columns=['BIN_SCAN', 'SKU_SCAN', 'QTY_TOTAL_SCAN'], errors='ignore')

            # 5. Mapping Nama Item
            item_map = dt.iloc[:, [2, 4]].dropna().astype(str)
            item_map.columns = ['SKU', 'NAME']
            item_map['SKU'] = item_map['SKU'].str.strip().str.upper()
            map_dict = item_map.drop_duplicates('SKU').set_index('SKU')['NAME'].to_dict()

            res_scan['ITEM NAME'] = res_scan['SKU'].map(map_dict).fillna("-")
            res_stock['ITEM NAME'] = res_stock.iloc[:, 2].astype(str).str.upper().map(map_dict).fillna("-")

            real_plus = res_scan[res_scan['NOTE'] == "REAL +"].copy()
            system_plus = res_stock[res_stock['NOTE'] == "SYSTEM +"].copy()

            self.cca_qty_real_plus.set(int(real_plus['DIFF'].sum()) if not real_plus.empty else 0)
            self.cca_qty_sys_plus.set(int(system_plus['DIFF'].sum()) if not system_plus.empty else 0)

            # Simpan 100% Data Utuh
            self._raw_df_cca_scan = res_scan.copy()
            self._raw_df_cca_stock = res_stock.copy()
            self._raw_df_cca_real_plus = real_plus.copy()
            self._raw_df_cca_sys_plus = system_plus.copy()
            self._cca_map_dict = map_dict

            # Format Angka Bersih untuk Tampilan
            def clean_num_str(val):
                try:
                    if pd.isna(val) or val == "" or val is None: return ""
                    f = float(val)
                    return str(int(f)) if f.is_integer() else f"{f:g}"
                except: return str(val)

            disp_scan, disp_stock = res_scan.copy(), res_stock.copy()
            disp_real, disp_sys = real_plus.copy(), system_plus.copy()

            for c in ['QTY_SCAN', 'QTY_SYSTEM', 'DIFF']:
                if c in disp_scan.columns: disp_scan[c] = disp_scan[c].apply(clean_num_str)
                if c in disp_real.columns: disp_real[c] = disp_real[c].apply(clean_num_str)

            for c in ['QTY_SYSTEM', 'QTY SO', 'DIFF']:
                if c in disp_stock.columns: disp_stock[c] = disp_stock[c].apply(clean_num_str)
                if c in disp_sys.columns: disp_sys[c] = disp_sys[c].apply(clean_num_str)

            self.df_cca_scan_headers.set(disp_scan.columns.tolist())
            self.df_cca_scan_rows.set(disp_scan.fillna("").astype(str).values.tolist())
            self.df_cca_stock_headers.set(disp_stock.columns.tolist())
            self.df_cca_stock_rows.set(disp_stock.fillna("").astype(str).values.tolist())
            self.df_cca_real_headers.set(disp_real.columns.tolist())
            self.df_cca_real_rows.set(disp_real.fillna("").astype(str).values.tolist())
            self.df_cca_sys_headers.set(disp_sys.columns.tolist())
            self.df_cca_sys_rows.set(disp_sys.fillna("").astype(str).values.tolist())

            self.cca_step1_done.set(True)
            return True, "Compare Step 1 Berhasil!"
        except Exception as e:
            return False, f"Gagal Compare Step 1: {e}"

    # --- STEP 2 & 3: ALLOCATION & RECON REPORTS ---
    def run_cca_step2(self, f_bin_cov, selected_bin_cov):
        try:
            if self._raw_df_cca_real_plus.empty or self._raw_df_cca_sys_plus.empty:
                return False, "Jalankan Step 1 terlebih dahulu!"

            df_cov_raw = load_data_from_info(f_bin_cov)
            if df_cov_raw.empty:
                return False, "File BIN Coverage kosong!"

            import re
            if selected_bin_cov and len(selected_bin_cov) > 0:
                pattern = "|".join([re.escape(str(b).strip().upper()) for b in selected_bin_cov])
                mask = df_cov_raw.iloc[:, 1].astype(str).str.strip().str.upper().str.contains(pattern, na=False)
                df_cov = df_cov_raw[mask].copy()
            else:
                df_cov = df_cov_raw.copy()

            # Indexing Dictionary per SKU O(1)
            system_by_sku = {}
            for _, row in self._raw_df_cca_sys_plus.iterrows():
                b, s = str(row['BIN']).strip().upper(), str(row['SKU']).strip().upper()
                q = float(row.get('DIFF', 0))
                if q > 0:
                    if s not in system_by_sku: system_by_sku[s] = {}
                    system_by_sku[s][b] = system_by_sku[s].get(b, 0) + q

            selected_bins = set(df_cov.iloc[:, 1].astype(str).str.strip().str.upper().unique())
            coverage_by_sku = {}
            for _, row in df_cov.iterrows():
                b_val, s_val = str(row.iloc[1]).strip().upper(), str(row.iloc[2]).strip().upper()
                if b_val in selected_bins:
                    try: val = float(row.iloc[9])
                    except: val = 0
                    if val > 0:
                        if s_val not in coverage_by_sku: coverage_by_sku[s_val] = {}
                        coverage_by_sku[s_val][b_val] = coverage_by_sku[s_val].get(b_val, 0) + val

            new_rows = []
            df_sys_updated = self._raw_df_cca_sys_plus.copy()
            sys_reduction = {}

            for _, row in self._raw_df_cca_real_plus.iterrows():
                sku = str(row['SKU']).strip().upper()
                diff_needed = float(row['DIFF'])
                if diff_needed <= 0:
                    r_copy = row.to_dict()
                    r_copy.update({'BIN ALOKASI': '', 'QTY ALLOCATION': 0, 'STATUS': 'NO DIFF'})
                    new_rows.append(r_copy)
                    continue

                remaining = diff_needed
                if sku in system_by_sku:
                    for bin_src, qty_avail in list(system_by_sku[sku].items()):
                        if remaining <= 0: break
                        if qty_avail > 0:
                            alloc = min(qty_avail, remaining)
                            r_alloc = row.to_dict()
                            r_alloc.update({'BIN ALOKASI': bin_src, 'QTY ALLOCATION': alloc, 'STATUS': 'FULL ALLOCATION' if alloc == remaining else 'PARTIAL ALLOCATION'})
                            new_rows.append(r_alloc)
                            system_by_sku[sku][bin_src] -= alloc
                            sys_reduction[(bin_src, sku)] = sys_reduction.get((bin_src, sku), 0) + alloc
                            remaining -= alloc

                if remaining > 0 and sku in coverage_by_sku:
                    for bin_src, qty_avail in list(coverage_by_sku[sku].items()):
                        if remaining <= 0: break
                        if qty_avail > 0:
                            alloc = min(qty_avail, remaining)
                            r_alloc = row.to_dict()
                            r_alloc.update({'BIN ALOKASI': bin_src, 'QTY ALLOCATION': alloc, 'STATUS': 'FULL ALLOCATION' if alloc == remaining else 'PARTIAL ALLOCATION'})
                            new_rows.append(r_alloc)
                            coverage_by_sku[sku][bin_src] -= alloc
                            remaining -= alloc

                if remaining > 0:
                    r_no = row.to_dict()
                    r_no.update({'DIFF': remaining, 'BIN ALOKASI': '', 'QTY ALLOCATION': 0, 'STATUS': 'NO ALLOCATION'})
                    new_rows.append(r_no)

            allocated = pd.DataFrame(new_rows)
            for (b, s), q in sys_reduction.items():
                mask = (df_sys_updated['BIN'].astype(str).str.upper() == b) & (df_sys_updated['SKU'].astype(str).str.upper() == s)
                if mask.any():
                    df_sys_updated.loc[mask, 'DIFF'] -= q

            allocated['ITEM NAME'] = allocated['SKU'].map(self._cca_map_dict)

            # Generate Set Up Real +
            filtered_setup = allocated[allocated['STATUS'].isin(['FULL ALLOCATION', 'PARTIAL ALLOCATION'])].copy()
            if not filtered_setup.empty:
                filtered_setup['BIN AWAL'] = filtered_setup['BIN ALOKASI']
                filtered_setup['BIN TUJUAN'] = filtered_setup['BIN']
                filtered_setup['QUANTITY'] = filtered_setup['QTY ALLOCATION']
                filtered_setup['NOTES'] = "MISS LOCATION"
                df_setup_real = filtered_setup[['BIN AWAL', 'BIN TUJUAN', 'SKU', 'QUANTITY', 'NOTES']].copy()
            else:
                df_setup_real = pd.DataFrame(columns=['BIN AWAL', 'BIN TUJUAN', 'SKU', 'QUANTITY', 'NOTES'])

            # Otomatis Buat Recon Reports (Step 3)
            filtered_no_alloc = allocated[allocated['STATUS'] == "NO ALLOCATION"].copy()
            if not filtered_no_alloc.empty:
                cols_r = [c for c in ['BIN', 'SKU', 'ITEM NAME', 'QTY_SCAN', 'QTY_SYSTEM', 'DIFF'] if c in filtered_no_alloc.columns]
                recon_real = filtered_no_alloc[cols_r].copy()
                recon_real['HASIL RECONCILIATION'] = ""
            else:
                recon_real = pd.DataFrame(columns=['BIN', 'SKU', 'ITEM NAME', 'QTY_SCAN', 'QTY_SYSTEM', 'DIFF', 'HASIL RECONCILIATION'])

            outstanding = df_sys_updated[df_sys_updated['DIFF'] != 0].copy()
            outstanding['HASIL REKONSILIASI'] = ""

            self._raw_df_cca_alloc = allocated.copy()
            self._raw_df_cca_sys_upd = df_sys_updated.copy()
            self._raw_df_cca_setup_real = df_setup_real.copy()
            self._raw_df_cca_rec_real = recon_real.copy()
            self._raw_df_cca_rec_sys = outstanding.copy()

            self.df_cca_alloc_headers.set(allocated.columns.tolist())
            self.df_cca_alloc_rows.set(allocated.fillna("").astype(str).values.tolist())
            self.df_cca_sys_upd_headers.set(df_sys_updated.columns.tolist())
            self.df_cca_sys_upd_rows.set(df_sys_updated.fillna("").astype(str).values.tolist())
            self.df_cca_setup_real_headers.set(df_setup_real.columns.tolist())
            self.df_cca_setup_real_rows.set(df_setup_real.fillna("").astype(str).values.tolist())
            self.df_cca_rec_real_headers.set(recon_real.columns.tolist())
            self.df_cca_rec_real_rows.set(recon_real.fillna("").astype(str).values.tolist())
            self.df_cca_rec_sys_headers.set(outstanding.columns.tolist())
            self.df_cca_rec_sys_rows.set(outstanding.fillna("").astype(str).values.tolist())

            self.cca_step2_done.set(True)
            self.cca_step3_done.set(True)
            return True, "Allocation Step 2 & Recon Step 3 Selesai!"
        except Exception as e:
            return False, f"Gagal Allocation Step 2: {e}"

    # --- STEP 4: RECON REAL + ANALYSIS ---
    def run_cca_step4(self, f_recon_real):
        try:
            df_r = load_data_from_info(f_recon_real)
            if df_r.empty or df_r.shape[1] < 7:
                return False, "File Recon Real + kurang kolom (butuh minimal 7 kolom)!"

            q_recon = np.nan_to_num(pd.to_numeric(df_r.iloc[:, 6], errors='coerce').values, nan=0.0)
            q_sys = np.nan_to_num(pd.to_numeric(df_r.iloc[:, 4], errors='coerce').values, nan=0.0)
            
            diff = q_recon - q_sys
            mask = diff != 0

            df_res = df_r[mask].copy()
            df_res['NEED_ADJ'] = diff[mask]

            self.cca_qty_need_adj.set(int(np.sum(diff[mask])))
            self.cca_sku_need_adj.set(len(df_res))

            self._raw_df_cca_adj4 = df_res.copy()
            self.df_cca_adj4_headers.set(df_res.columns.tolist())
            self.df_cca_adj4_rows.set(df_res.fillna("").astype(str).values.tolist())

            self.cca_step4_done.set(True)
            return True, "Analisis Step 4 Berhasil!"
        except Exception as e:
            return False, f"Gagal Step 4: {e}"

    # --- STEP 5: RECON SYSTEM + (SET UP KARANTINA) ---
    def run_cca_step5(self, f_recon_sys):
        try:
            df_raw6 = load_data_from_info(f_recon_sys)
            if df_raw6.empty:
                return False, "File System + Recon kosong!"

            df_raw6.columns = df_raw6.columns.astype(str).str.strip().str.upper()
            audit_results, karantina_results = [], []

            for _, row in df_raw6.iterrows():
                try:
                    bin_raw, sku_raw = row.get('BIN'), row.get('SKU')
                    if pd.isna(bin_raw) and pd.isna(sku_raw): continue

                    bin_val = str(bin_raw).strip().upper()
                    sku_val = str(sku_raw).strip().upper()
                    if bin_val.endswith('.0'): bin_val = bin_val[:-2]
                    if sku_val.endswith('.0'): sku_val = sku_val[:-2]

                    q_sys_num = pd.to_numeric(row.get('QTY SYSTEM', '0'), errors='coerce') or 0
                    q_rec_num = pd.to_numeric(row.get('HASIL REKONSILIASI', '0'), errors='coerce') or 0
                    diff = q_sys_num - q_rec_num

                    if diff != 0:
                        audit_results.append({'BIN': bin_val, 'SKU': sku_val, 'QTY_SYSTEM_J': q_sys_num, 'QTY_RECON_N': q_rec_num, 'SELISIH': diff})
                        karantina_results.append({"BIN AWAL": bin_val, "BIN TUJUAN": "KARANTINA", "SKU": sku_val, "QUANTITY": int(abs(diff)), "NOTES": "MISS LOCATION"})
                except: continue

            df_karantina = pd.DataFrame(karantina_results) if karantina_results else pd.DataFrame(columns=['BIN AWAL', 'BIN TUJUAN', 'SKU', 'QUANTITY', 'NOTES'])
            df_check = pd.DataFrame(audit_results) if audit_results else pd.DataFrame(columns=['BIN', 'SKU', 'QTY_SYSTEM_J', 'QTY_RECON_N', 'SELISIH'])

            self.cca_qty_karantina.set(int(df_karantina['QUANTITY'].sum()) if not df_karantina.empty and 'QUANTITY' in df_karantina.columns else 0)
            self.cca_sku_karantina.set(df_karantina['SKU'].nunique() if not df_karantina.empty and 'SKU' in df_karantina.columns else 0)

            self._raw_df_cca_karantina = df_karantina.copy()
            self._raw_df_cca_check5 = df_check.copy()

            self.df_cca_karantina_headers.set(df_karantina.columns.tolist())
            self.df_cca_karantina_rows.set(df_karantina.fillna("").astype(str).values.tolist())
            self.df_cca_check5_headers.set(df_check.columns.tolist())
            self.df_cca_check5_rows.set(df_check.fillna("").astype(str).values.tolist())

            self.cca_step5_done.set(True)
            return True, "Analisis Karantina Step 5 Selesai!"
        except Exception as e:
            return False, f"Gagal Step 5: {e}"

    # --- STEP 6: MISS LOCATION REPORT ---
    def run_cca_step6(self):
        try:
            if self._raw_df_cca_setup_real.empty:
                return False, "Data Set Up Real + kosong! Jalankan Step 2 terlebih dahulu."

            columns_ref = ["BIN SYSTEM +", "BIN REAL +", "SKU", "QTY MISS LOC."]
            df_out = self._raw_df_cca_setup_real.iloc[:, 0:4].copy()
            df_out.columns = columns_ref
            df_out["QTY MISS LOC."] = pd.to_numeric(df_out["QTY MISS LOC."], errors='coerce').fillna(0)

            count_sku = df_out["SKU"].nunique()
            count_qty = int(df_out["QTY MISS LOC."].sum())

            df_sum = pd.DataFrame({
                "METRIC": ["Total SKU Miss Loc", "Total Qty Miss Loc"],
                "VALUE": [count_sku, count_qty]
            })

            self.cca_sku_miss_loc.set(count_sku)
            self.cca_qty_miss_loc.set(count_qty)

            self._raw_df_cca_miss_loc = df_out.copy()
            self._raw_df_cca_sum_miss = df_sum.copy()

            self.df_cca_miss_loc_headers.set(df_out.columns.tolist())
            self.df_cca_miss_loc_rows.set(df_out.fillna("").astype(str).values.tolist())
            self.df_cca_sum_miss_headers.set(df_sum.columns.tolist())
            self.df_cca_sum_miss_rows.set(df_sum.fillna("").astype(str).values.tolist())

            self.cca_step6_done.set(True)
            return True, "Miss Location Report Berhasil Dibuat!"
        except Exception as e:
            return False, f"Gagal Step 6: {e}"

# ==========================================================================
    # COMPARE RTO ALGORITHMS (PORTED FROM STREAMLIT)
    # ==========================================================================
    def run_rto_step1(self, f_ds, f_app):
        try:
            df_ds_raw = load_data_from_info(f_ds)
            df_app_raw = load_data_from_info(f_app)

            if df_ds_raw.empty or df_app_raw.empty:
                return False, "File DS RTO dan AppSheet RTO tidak boleh kosong!"

            def clean_sku(val):
                if pd.isna(val): return ""
                if isinstance(val, float) and val.is_integer():
                    s = str(int(val)).strip().upper()
                else:
                    s = str(val).strip().upper()
                if s.endswith('.0'): s = s[:-2]
                if s in ["NAN", "0", "NONE", ""]: return ""
                return s

            df_a = df_app_raw.copy()
            df_a.columns = [str(i) for i in range(1, len(df_a.columns) + 1)]
            
            mask_status = df_a['2'].astype(str).str.strip().str.upper().isin(['DONE', 'KURANG AMBIL'])
            df_filtered = df_a[mask_status].copy()

            dict_qty_total = {}
            for _, row in df_filtered.iterrows():
                sku1 = clean_sku(row.get('9', ''))
                qty1 = pd.to_numeric(row.get('13', 0), errors='coerce') or 0
                if sku1: dict_qty_total[sku1] = dict_qty_total.get(sku1, 0) + qty1

                sku2 = clean_sku(row.get('15', ''))
                qty2 = pd.to_numeric(row.get('17', 0), errors='coerce') or 0
                if sku2: dict_qty_total[sku2] = dict_qty_total.get(sku2, 0) + qty2

            res_ds = df_ds_raw.copy()
            cols = list(res_ds.columns)
            sku_col, scan_col = cols[0], cols[1]

            res_ds['SKU_UPPER'] = res_ds[sku_col].apply(clean_sku)
            res_ds['QTY AMBIL'] = res_ds['SKU_UPPER'].map(dict_qty_total).fillna(0).astype(int)

            def check_note(row):
                scan = pd.to_numeric(row[scan_col], errors='coerce') or 0
                ambil = row['QTY AMBIL']
                if scan > ambil: return "KELEBIHAN AMBIL"
                elif scan < ambil: return "KURANG AMBIL"
                else: return "SESUAI"

            res_ds['NOTE'] = res_ds.apply(check_note, axis=1)

            results_selisih = []
            mismatch_ds = res_ds[res_ds['NOTE'] != 'SESUAI'].copy()

            for _, row in mismatch_ds.iterrows():
                sku = row['SKU_UPPER']
                mask_app = (df_a['9'].apply(clean_sku) == sku) | (df_a['15'].apply(clean_sku) == sku)
                found_rows = df_a[mask_app]
                if not found_rows.empty:
                    for _, r_app in found_rows.iterrows():
                        if clean_sku(r_app.get('9')) == sku:
                            results_selisih.append([sku, row[scan_col], row['QTY AMBIL'], row['NOTE'], r_app.get('12', '-'), r_app.get('13', 0), 0])
                        if clean_sku(r_app.get('15')) == sku:
                            results_selisih.append([sku, row[scan_col], row['QTY AMBIL'], row['NOTE'], r_app.get('16', '-'), r_app.get('17', 0), 0])
                else:
                    results_selisih.append([sku, row[scan_col], row['QTY AMBIL'], row['NOTE'], "-", 0, 0])

            skus_in_ds = set(res_ds['SKU_UPPER'].unique())
            for sku_app, total_qty in dict_qty_total.items():
                if sku_app and sku_app not in skus_in_ds:
                    mask_app = (df_a['9'].apply(clean_sku) == sku_app) | (df_a['15'].apply(clean_sku) == sku_app)
                    found_rows = df_a[mask_app]
                    for _, r_app in found_rows.iterrows():
                        note_khusus = "DI APPSHEET DIAMBIL DI DS TIDAK ADA"
                        if clean_sku(r_app.get('9')) == sku_app:
                            results_selisih.append([sku_app, 0, total_qty, note_khusus, r_app.get('12', '-'), r_app.get('13', 0), 0])
                        if clean_sku(r_app.get('15')) == sku_app:
                            results_selisih.append([sku_app, 0, total_qty, note_khusus, r_app.get('16', '-'), r_app.get('17', 0), 0])

            res_selisih = pd.DataFrame(results_selisih, columns=['SKU','QTY SCAN','QTY AMBIL','NOTE','BIN','QTY AMBIL BIN','HASIL CEK REAL'])
            res_selisih = res_selisih.drop_duplicates(subset=['SKU', 'BIN', 'QTY AMBIL BIN', 'NOTE'], keep='first')
            res_selisih['SKU'] = res_selisih['SKU'].apply(clean_sku)
            res_ds.drop(columns=['SKU_UPPER'], inplace=True, errors='ignore')

            # Kalkulasi Metrik
            v_scan = pd.to_numeric(res_selisih['QTY SCAN'], errors='coerce').fillna(0)
            v_ambil = pd.to_numeric(res_selisih['QTY AMBIL BIN'], errors='coerce').fillna(0)
            v_notes = res_selisih['NOTE'].astype(str).str.strip().str.upper()

            q_tot = int(pd.to_numeric(res_ds[scan_col], errors='coerce').sum())
            q_ses = int(pd.to_numeric(res_ds[res_ds['NOTE'] == 'SESUAI'][scan_col], errors='coerce').sum())
            
            mask_l = v_notes == 'KELEBIHAN AMBIL'
            q_leb = int((v_scan[mask_l] - res_selisih.loc[mask_l, 'QTY AMBIL']).sum()) if mask_l.any() else 0

            mask_k = v_notes == 'KURANG AMBIL'
            mask_m = v_notes == 'DI APPSHEET DIAMBIL DI DS TIDAK ADA'
            selisih_k = (res_selisih.loc[mask_k, 'QTY AMBIL'] - v_scan[mask_k]).sum() if mask_k.any() else 0
            total_m = v_ambil[mask_m].sum() if mask_m.any() else 0
            q_kur = int(selisih_k + total_m)

            self.rto_q_total.set(q_tot)
            self.rto_q_sesuai.set(q_ses)
            self.rto_q_lebih.set(q_leb)
            self.rto_q_kurang.set(q_kur)

            self._raw_df_rto_ds = res_ds.copy()
            self._raw_df_rto_selisih = res_selisih.copy()
            self._raw_df_rto_app = df_app_raw.copy()

            self.df_rto_ds_headers.set(res_ds.columns.tolist())
            self.df_rto_ds_rows.set(res_ds.fillna("").astype(str).values.tolist())
            self.df_rto_selisih_headers.set(res_selisih.columns.tolist())
            self.df_rto_selisih_rows.set(res_selisih.fillna("").astype(str).values.tolist())

            self.rto_step1_done.set(True)
            return True, "Compare DS vs AppSheet Selesai!"
        except Exception as e:
            return False, f"Gagal Compare RTO Step 1: {e}"

    def run_rto_step2_refresh(self, f_cek):
        try:
            if self._raw_df_rto_app.empty or self._raw_df_rto_ds.empty:
                return False, "Jalankan Step 1 terlebih dahulu!"

            df_selisih = load_data_from_info(f_cek)
            if df_selisih.empty:
                return False, "File Hasil Cek Real kosong!"

            df_app_res = self._raw_df_rto_app.copy()
            df_ds_res = self._raw_df_rto_ds.copy()

            real_map = {}
            for _, row in df_selisih.iterrows():
                sku_real = str(row.iloc[0]).strip().upper()
                bin_real = str(row.iloc[4]).strip().upper()
                qty_real = pd.to_numeric(row.iloc[6], errors='coerce') or 0
                if sku_real not in ["", "NAN", "NONE"]:
                    real_map[f"{sku_real}|{bin_real}"] = qty_real

            for idx in df_app_res.index:
                try:
                    sku = str(df_app_res.iloc[idx, 8]).strip().upper()
                    if sku in ["", "NAN", "0", "NONE"]: sku = str(df_app_res.iloc[idx, 14]).strip().upper()
                    b1, b2 = str(df_app_res.iloc[idx, 11]).strip().upper(), str(df_app_res.iloc[idx, 15]).strip().upper()
                    target_qty = real_map.get(f"{sku}|{b1}") if f"{sku}|{b1}" in real_map else real_map.get(f"{sku}|{b2}")
                    if target_qty is not None:
                        val_n = str(df_app_res.iloc[idx, 13]).strip()
                        if val_n == "" or val_n.lower() == "nan": df_app_res.iloc[idx, 12] = target_qty
                        else: df_app_res.iloc[idx, 16] = target_qty
                except: continue

            if not df_ds_res.empty:
                df_app_res['TMP_SKU'] = df_app_res.apply(lambda r: str(r.iloc[8]).strip().upper() if str(r.iloc[8]).strip() not in ["","0","nan"] else str(r.iloc[14]).strip().upper(), axis=1)
                df_app_res['TMP_QTY'] = df_app_res.apply(lambda r: (pd.to_numeric(r.iloc[12], errors='coerce') or 0) + (pd.to_numeric(r.iloc[16], errors='coerce') or 0), axis=1)
                summary_map = df_app_res.groupby('TMP_SKU')['TMP_QTY'].sum().to_dict()
                sku_col, scan_col, ambil_col = df_ds_res.columns[0], df_ds_res.columns[1], df_ds_res.columns[2]
                df_ds_res[ambil_col] = df_ds_res[sku_col].astype(str).str.strip().str.upper().map(summary_map).fillna(0)
                df_ds_res[scan_col] = df_ds_res[ambil_col]
                if 'NOTE' in df_ds_res.columns: df_ds_res['NOTE'] = "SESUAI"
                df_app_res.drop(columns=['TMP_SKU', 'TMP_QTY'], inplace=True, errors='ignore')

            self._raw_df_rto_ds = df_ds_res.copy()
            self._raw_df_rto_app = df_app_res.copy()
            self.df_rto_ds_rows.set(df_ds_res.fillna("").astype(str).values.tolist())

            return True, "Data RTO Berhasil Di-refresh!"
        except Exception as e:
            return False, f"Gagal Refresh RTO: {e}"

    def run_rto_step3_draft(self, f_draft):
        try:
            if self._raw_df_rto_app.empty:
                return False, "Jalankan Step 1 terlebih dahulu!"

            df_draft = load_data_from_info(f_draft)
            if df_draft.empty:
                return False, "File Draft Jezpro kosong!"

            df_res = df_draft.copy()
            df_a = self._raw_df_rto_app.copy()
            df_a.columns = [str(i) for i in range(1, len(df_a.columns) + 1)]

            def clean_sku(val):
                if pd.isna(val): return ""
                s = str(val).strip().upper()
                if s.endswith('.0'): s = s[:-2]
                return s if s not in ["NAN", "0", "NONE"] else ""

            app_summary = {}
            for _, r in df_a.iterrows():
                pairs = [(clean_sku(r.get('9')), str(r.get('12','')).strip().upper(), pd.to_numeric(r.get('13',0), errors='coerce') or 0),
                         (clean_sku(r.get('15')) or clean_sku(r.get('9')), str(r.get('16','')).strip().upper(), pd.to_numeric(r.get('17',0), errors='coerce') or 0)]
                for s, b, q in pairs:
                    if s and b not in ["", "0", "NAN"]:
                        app_summary[(s, b)] = app_summary.get((s, b), 0) + q

            rem_app = app_summary.copy()
            processed_indices = set()

            for idx, row in df_res.iterrows():
                sku_d = clean_sku(row.iloc[3])
                bin_d = str(row.iloc[8]).strip().upper()
                qty_h = pd.to_numeric(row.iloc[7], errors='coerce') or 0
                key_d = (sku_d, bin_d)

                if rem_app.get(key_d, 0) > 0:
                    qty_j = rem_app[key_d]
                    rem_app[key_d] = 0
                    note = "DRAFT SESUAI" if qty_j == qty_h else "BEDA QTY"
                    status = "OK" if qty_j == qty_h else "PERLU EDIT QTY DRAFT"
                    df_res.loc[idx, ['QTY AMBIL', 'NOTE', 'BIN AMBIL LAIN', 'QTY BIN LAIN', 'STATUS']] = [qty_j, note, "", 0, status]
                    processed_indices.add(idx)

            for idx, row in df_res.iterrows():
                if idx in processed_indices: continue
                sku_d = clean_sku(row.iloc[3])
                possible_bins = [k for k, v in rem_app.items() if k[0] == sku_d and v > 0]
                if possible_bins:
                    bin_lain = ", ".join([b[1] for b in possible_bins])
                    qty_lain = sum([rem_app[b] for b in possible_bins])
                    df_res.loc[idx, ['QTY AMBIL', 'NOTE', 'BIN AMBIL LAIN', 'QTY BIN LAIN', 'STATUS']] = [0, "PINDAH BIN", bin_lain, qty_lain, "PERLU EDIT BIN DRAFT"]
                else:
                    df_res.loc[idx, ['QTY AMBIL', 'NOTE', 'BIN AMBIL LAIN', 'QTY BIN LAIN', 'STATUS']] = [0, "HAPUS ITEM INI", "", 0, "DELETE ITEM"]

            sku_in_draft = set(df_draft.iloc[:, 3].apply(clean_sku).unique())
            new_rows = []
            for (sku_a, bin_a), qty_a in rem_app.items():
                if qty_a > 0 and sku_a not in sku_in_draft:
                    new_entry = {col: "" for col in df_res.columns}
                    new_entry[df_res.columns[0]] = "-"
                    new_entry[df_res.columns[3]] = sku_a
                    new_entry[df_res.columns[7]] = 0
                    new_entry[df_res.columns[8]] = bin_a
                    new_entry['QTY AMBIL'] = qty_a
                    new_entry['NOTE'] = "TAMBAH ITEM BARU"
                    new_entry['STATUS'] = "ADD NEW"
                    new_rows.append(new_entry)
                    rem_app[(sku_a, bin_a)] = 0

            if new_rows:
                df_res = pd.concat([df_res, pd.DataFrame(new_rows)], ignore_index=True)

            for col in ['QTY AMBIL', 'QTY BIN LAIN', df_res.columns[7]]:
                if col in df_res.columns:
                    df_res[col] = pd.to_numeric(df_res[col], errors='coerce').fillna(0).astype(int)

            # Hitung Metrik Final
            qty_ambil = pd.to_numeric(df_res['QTY AMBIL'], errors='coerce').fillna(0)
            qty_lain = pd.to_numeric(df_res['QTY BIN LAIN'], errors='coerce').fillna(0)

            q_draft_tot = int((qty_ambil + qty_lain).sum())
            mask_ok = (df_res['STATUS'] == 'OK')
            q_ok = int((qty_ambil[mask_ok] + qty_lain[mask_ok]).sum())
            mask_edit = df_res['STATUS'].str.contains('EDIT', na=False)
            q_edit = int((qty_ambil[mask_edit] + qty_lain[mask_edit]).sum())
            
            qty_col_name = df_draft.columns[7]
            q_del = int(pd.to_numeric(df_res[df_res['STATUS'] == 'DELETE ITEM'][qty_col_name], errors='coerce').sum()) if 'DELETE ITEM' in df_res['STATUS'].values else 0

            self.rto_q_draft_total.set(q_draft_tot)
            self.rto_q_ok.set(q_ok)
            self.rto_q_edit.set(q_edit)
            self.rto_q_del.set(q_del)

            self._raw_df_rto_draft_comp = df_res.copy()
            self.df_rto_draft_comp_headers.set(df_res.columns.tolist())
            self.df_rto_draft_comp_rows.set(df_res.fillna("").astype(str).values.tolist())

            self.rto_draft_done.set(True)
            return True, "Compare Draft Jezpro Berhasil!"
        except Exception as e:
            return False, f"Gagal Compare Draft: {e}"

    def run_rto_step4_new_draft(self):
        try:
            if self._raw_df_rto_draft_comp.empty:
                return False, "Jalankan Compare Draft Jezpro terlebih dahulu!"

            dict_final = {}
            for _, row in self._raw_df_rto_draft_comp.iterrows():
                sku = str(row.iloc[3]).strip().upper()
                bin_i = str(row.iloc[8]).strip().upper()
                bin_l = str(row.iloc[11]).strip().upper() if not pd.isna(row.iloc[11]) else ""
                q_j = pd.to_numeric(row['QTY AMBIL'], errors='coerce') or 0
                q_m = pd.to_numeric(row['QTY BIN LAIN'], errors='coerce') or 0
                if q_j > 0:
                    k = f"{bin_i}|{sku}"
                    dict_final[k] = dict_final.get(k, 0) + q_j
                if q_m > 0 and bin_l not in ["", "-", "NAN"]:
                    k_l = f"{bin_l}|{sku}"
                    dict_final[k_l] = dict_final.get(k_l, 0) + q_m

            res = pd.DataFrame([{'BIN': k.split('|')[0], 'SKU': k.split('|')[1], 'QUANTITY': int(v)} for k, v in dict_final.items()])
            if not res.empty:
                res = res.sort_values(['BIN', 'SKU']).reset_index(drop=True)

            self.rto_q_new_draft_total.set(int(res['QUANTITY'].sum()) if not res.empty else 0)
            self._raw_df_rto_new_draft = res.copy()
            self.df_rto_new_draft_headers.set(res.columns.tolist() if not res.empty else [])
            self.df_rto_new_draft_rows.set(res.fillna("").astype(str).values.tolist() if not res.empty else [])

            self.rto_new_draft_done.set(True)
            return True, f"Generate New Draft Selesai! Total: {self.rto_q_new_draft_total()} Pcs"
        except Exception as e:
            return False, f"Gagal Generate New Draft: {e}"

# ==========================================================================
    # STOCK OPNAME ANALYZER LOGIC & ALGORITHMS (LENGKAP STEP 1 - 6)
    # ==========================================================================
    def run_so_step1(self, f_scan, f_stock, sub_sel, bin_sys_sel):
        try:
            df_s_raw = load_data_from_info(f_scan)
            df_t_raw = load_data_from_info(f_stock)
            if df_s_raw.empty or df_t_raw.empty:
                return False, "File Data Scan dan Stock System tidak boleh kosong!"

            ds = df_s_raw.iloc[:, [0, 1, 2]].copy()
            ds.columns = ['BIN', 'SKU', 'QTY_SCAN']
            ds['BIN'] = ds['BIN'].astype(str).str.strip().str.upper()
            ds['SKU'] = ds['SKU'].astype(str).str.strip().str.upper()
            ds['QTY_SCAN'] = pd.to_numeric(ds['QTY_SCAN'], errors='coerce').fillna(0)

            dt = df_t_raw.copy()
            col_b, col_s, col_q_sys = dt.columns[1], dt.columns[2], dt.columns[9]

            if sub_sel and len(sub_sel) > 0 and dt.shape[1] > 6:
                dt = dt[dt.iloc[:, 6].astype(str).str.upper().isin([x.upper() for x in sub_sel])]
            if bin_sys_sel and len(bin_sys_sel) > 0 and dt.shape[1] > 1:
                dt = dt[dt.iloc[:, 1].astype(str).str.upper().apply(lambda x: any(c.upper() in x for c in bin_sys_sel))]

            dt[col_b] = dt[col_b].astype(str).str.strip().str.upper()
            dt[col_s] = dt[col_s].astype(str).str.strip().str.upper()
            dt[col_q_sys] = pd.to_numeric(dt[col_q_sys], errors='coerce').fillna(0)

            dt_sub = dt[[col_b, col_s, col_q_sys]].copy()
            dt_sub.columns = ['BIN', 'SKU', 'QTY_SYSTEM']
            dt_grouped = dt_sub.groupby(['BIN', 'SKU'], as_index=False)['QTY_SYSTEM'].sum()

            res_scan = ds.merge(dt_grouped, on=['BIN', 'SKU'], how='left').fillna(0)
            res_scan['DIFF'] = res_scan['QTY_SCAN'] - res_scan['QTY_SYSTEM']
            res_scan['NOTE'] = np.where(res_scan['DIFF'] > 0, "REAL +", np.where(res_scan['DIFF'] < 0, "SYSTEM +", "OK"))

            ds_g = ds.groupby(['BIN', 'SKU'], as_index=False)['QTY_SCAN'].sum()
            ds_g.columns = ['BIN_SCAN', 'SKU_SCAN', 'QTY_TOTAL_SCAN']

            dt_merged = dt.merge(ds_g, left_on=[col_b, col_s], right_on=['BIN_SCAN', 'SKU_SCAN'], how='left')
            dt_merged['QTY SO'] = dt_merged['QTY_TOTAL_SCAN'].fillna(0)
            dt_merged['DIFF'] = dt_merged[col_q_sys] - dt_merged['QTY SO']
            dt_merged['NOTE'] = np.where(dt_merged['DIFF'] > 0, "SYSTEM +", np.where(dt_merged['DIFF'] < 0, "REAL +", "OK"))
            res_stock = dt_merged.drop(columns=['BIN_SCAN', 'SKU_SCAN', 'QTY_TOTAL_SCAN'], errors='ignore')

            item_map = dt.iloc[:, [2, 4]].dropna().astype(str)
            item_map.columns = ['SKU', 'NAME']
            item_map['SKU'] = item_map['SKU'].str.strip().str.upper()
            map_dict = item_map.drop_duplicates('SKU').set_index('SKU')['NAME'].to_dict()

            res_scan['ITEM NAME'] = res_scan['SKU'].map(map_dict).fillna("-")
            res_stock['ITEM NAME'] = res_stock.iloc[:, 2].astype(str).str.upper().map(map_dict).fillna("-")

            real_plus = res_scan[res_scan['NOTE'] == "REAL +"].copy()
            system_plus = res_stock[res_stock['NOTE'] == "SYSTEM +"].copy()

            self.so_qty_real_plus.set(int(real_plus['DIFF'].sum()) if not real_plus.empty else 0)
            self.so_qty_sys_plus.set(int(system_plus['DIFF'].sum()) if not system_plus.empty else 0)

            self._raw_df_so_scan = res_scan.copy()
            self._raw_df_so_stock = res_stock.copy()
            self._raw_df_so_real_plus = real_plus.copy()
            self._raw_df_so_sys_plus = system_plus.copy()
            self._so_map_dict = map_dict

            self.df_so_scan_headers.set(res_scan.columns.tolist())
            self.df_so_scan_rows.set(res_scan.fillna("").astype(str).values.tolist())
            self.df_so_stock_headers.set(res_stock.columns.tolist())
            self.df_so_stock_rows.set(res_stock.fillna("").astype(str).values.tolist())
            self.df_so_real_headers.set(real_plus.columns.tolist())
            self.df_so_real_rows.set(real_plus.fillna("").astype(str).values.tolist())
            self.df_so_sys_headers.set(system_plus.columns.tolist())
            self.df_so_sys_rows.set(system_plus.fillna("").astype(str).values.tolist())

            self.so_step1_done.set(True)
            return True, "Compare Step 1 Berhasil!"
        except Exception as e:
            return False, f"Gagal Compare Step 1: {e}"

    def run_so_step2(self, f_bin_cov, selected_bin_cov):
        try:
            if self._raw_df_so_real_plus.empty or self._raw_df_so_sys_plus.empty:
                return False, "Jalankan Step 1 terlebih dahulu!"

            df_cov_raw = load_data_from_info(f_bin_cov)
            if df_cov_raw.empty: return False, "File BIN Coverage kosong!"

            import re
            if selected_bin_cov and len(selected_bin_cov) > 0:
                pattern = "|".join([re.escape(str(b).strip().upper()) for b in selected_bin_cov])
                mask = df_cov_raw.iloc[:, 1].astype(str).str.strip().str.upper().str.contains(pattern, na=False)
                df_cov = df_cov_raw[mask].copy()
            else:
                df_cov = df_cov_raw.copy()

            system_by_sku = {}
            for _, row in self._raw_df_so_sys_plus.iterrows():
                b, s = str(row['BIN']).strip().upper(), str(row['SKU']).strip().upper()
                q = float(row.get('DIFF', 0))
                if q > 0:
                    if s not in system_by_sku: system_by_sku[s] = {}
                    system_by_sku[s][b] = system_by_sku[s].get(b, 0) + q

            selected_bins = set(df_cov.iloc[:, 1].astype(str).str.strip().str.upper().unique())
            coverage_by_sku = {}
            for _, row in df_cov.iterrows():
                b_val, s_val = str(row.iloc[1]).strip().upper(), str(row.iloc[2]).strip().upper()
                if b_val in selected_bins:
                    try: val = float(row.iloc[9])
                    except: val = 0
                    if val > 0:
                        if s_val not in coverage_by_sku: coverage_by_sku[s_val] = {}
                        coverage_by_sku[s_val][b_val] = coverage_by_sku[s_val].get(b_val, 0) + val

            new_rows = []
            df_sys_updated = self._raw_df_so_sys_plus.copy()
            sys_reduction = {}

            for _, row in self._raw_df_so_real_plus.iterrows():
                sku = str(row['SKU']).strip().upper()
                diff_needed = float(row['DIFF'])
                if diff_needed <= 0:
                    r_copy = row.to_dict()
                    r_copy.update({'BIN ALOKASI': '', 'QTY ALLOCATION': 0, 'STATUS': 'NO DIFF'})
                    new_rows.append(r_copy)
                    continue

                remaining = diff_needed
                if sku in system_by_sku:
                    for bin_src, qty_avail in list(system_by_sku[sku].items()):
                        if remaining <= 0: break
                        if qty_avail > 0:
                            alloc = min(qty_avail, remaining)
                            r_alloc = row.to_dict()
                            r_alloc.update({'BIN ALOKASI': bin_src, 'QTY ALLOCATION': alloc, 'STATUS': 'FULL ALLOCATION' if alloc == remaining else 'PARTIAL ALLOCATION'})
                            new_rows.append(r_alloc)
                            system_by_sku[sku][bin_src] -= alloc
                            sys_reduction[(bin_src, sku)] = sys_reduction.get((bin_src, sku), 0) + alloc
                            remaining -= alloc

                if remaining > 0 and sku in coverage_by_sku:
                    for bin_src, qty_avail in list(coverage_by_sku[sku].items()):
                        if remaining <= 0: break
                        if qty_avail > 0:
                            alloc = min(qty_avail, remaining)
                            r_alloc = row.to_dict()
                            r_alloc.update({'BIN ALOKASI': bin_src, 'QTY ALLOCATION': alloc, 'STATUS': 'FULL ALLOCATION' if alloc == remaining else 'PARTIAL ALLOCATION'})
                            new_rows.append(r_alloc)
                            coverage_by_sku[sku][bin_src] -= alloc
                            remaining -= alloc

                if remaining > 0:
                    r_no = row.to_dict()
                    r_no.update({'DIFF': remaining, 'BIN ALOKASI': '', 'QTY ALLOCATION': 0, 'STATUS': 'NO ALLOCATION'})
                    new_rows.append(r_no)

            allocated = pd.DataFrame(new_rows)
            for (b, s), q in sys_reduction.items():
                mask = (df_sys_updated['BIN'].astype(str).str.upper() == b) & (df_sys_updated['SKU'].astype(str).str.upper() == s)
                if mask.any(): df_sys_updated.loc[mask, 'DIFF'] -= q

            allocated['ITEM NAME'] = allocated['SKU'].map(self._so_map_dict)

            filtered_setup = allocated[allocated['STATUS'].isin(['FULL ALLOCATION', 'PARTIAL ALLOCATION'])].copy()
            if not filtered_setup.empty:
                filtered_setup['BIN AWAL'] = filtered_setup['BIN ALOKASI']
                filtered_setup['BIN TUJUAN'] = filtered_setup['BIN']
                filtered_setup['QUANTITY'] = filtered_setup['QTY ALLOCATION']
                filtered_setup['NOTES'] = "MISS LOCATION"
                df_setup_real = filtered_setup[['BIN AWAL', 'BIN TUJUAN', 'SKU', 'QUANTITY', 'NOTES']].copy()
            else:
                df_setup_real = pd.DataFrame(columns=['BIN AWAL', 'BIN TUJUAN', 'SKU', 'QUANTITY', 'NOTES'])

            # Step 3 Auto-Gen
            filtered_no_alloc = allocated[allocated['STATUS'] == "NO ALLOCATION"].copy()
            if not filtered_no_alloc.empty:
                cols_r = [c for c in ['BIN', 'SKU', 'ITEM NAME', 'QTY_SCAN', 'QTY_SYSTEM', 'DIFF'] if c in filtered_no_alloc.columns]
                recon_real = filtered_no_alloc[cols_r].copy()
                recon_real['HASIL RECONCILIATION'] = ""
            else:
                recon_real = pd.DataFrame(columns=['BIN', 'SKU', 'ITEM NAME', 'QTY_SCAN', 'QTY_SYSTEM', 'DIFF', 'HASIL RECONCILIATION'])

            outstanding = df_sys_updated[df_sys_updated['DIFF'] != 0].copy()
            outstanding['HASIL REKONSILIASI'] = ""

            self._raw_df_so_alloc = allocated.copy()
            self._raw_df_so_sys_upd = df_sys_updated.copy()
            self._raw_df_so_setup_real = df_setup_real.copy()
            self._raw_df_so_rec_real = recon_real.copy()
            self._raw_df_so_rec_sys = outstanding.copy()

            self.df_so_alloc_headers.set(allocated.columns.tolist())
            self.df_so_alloc_rows.set(allocated.fillna("").astype(str).values.tolist())
            self.df_so_sys_upd_headers.set(df_sys_updated.columns.tolist())
            self.df_so_sys_upd_rows.set(df_sys_updated.fillna("").astype(str).values.tolist())
            self.df_so_setup_real_headers.set(df_setup_real.columns.tolist())
            self.df_so_setup_real_rows.set(df_setup_real.fillna("").astype(str).values.tolist())
            self.df_so_rec_real_headers.set(recon_real.columns.tolist())
            self.df_so_rec_real_rows.set(recon_real.fillna("").astype(str).values.tolist())
            self.df_so_rec_sys_headers.set(outstanding.columns.tolist())
            self.df_so_rec_sys_rows.set(outstanding.fillna("").astype(str).values.tolist())

            self.so_step2_done.set(True)
            return True, "Allocation & Recon Selesai!"
        except Exception as e:
            return False, f"Gagal Allocation Step 2: {e}"

    def run_so_step4(self, f_r4, f_s4, f_m5):
        try:
            df_r4 = load_data_from_info(f_r4)
            df_s4 = load_data_from_info(f_s4)
            df_m5 = load_data_from_info(f_m5)

            if df_r4.empty or df_s4.empty or df_m5.empty:
                return False, "Ketiga file (Real+ Recon, Cek Stock Adj+, Staging Inbound) wajib diupload!"

            def super_clean(val):
                if pd.isna(val) or str(val).strip().lower() in ['nan', 'null', '']: return ""
                s = str(val).strip().upper()
                if s.endswith('.0'): s = s[:-2]
                return s

            df_s = df_s4.copy()
            df_r = df_r4.copy()

            df_s['JOIN_KEY'] = df_s.iloc[:, 1].fillna('').astype(str).apply(super_clean) + "|" + df_s.iloc[:, 2].fillna('').astype(str).apply(super_clean)
            df_r['JOIN_KEY'] = df_r.iloc[:, 0].fillna('').astype(str).apply(super_clean) + "|" + df_r.iloc[:, 1].fillna('').astype(str).apply(super_clean)

            recon_map = {}
            for _, row in df_r.iterrows():
                b, s = super_clean(row.iloc[0]), super_clean(row.iloc[1])
                q = pd.to_numeric(row.iloc[6], errors='coerce') or 0
                if b and s: recon_map[f"{b}|{s}"] = q

            new_qty_so = df_s['JOIN_KEY'].map(recon_map)
            sys_qty = pd.to_numeric(df_s.iloc[:, 9], errors='coerce').fillna(0)
            new_diff = np.where(new_qty_so.notna(), (sys_qty - new_qty_so.fillna(0)).abs(), np.nan)

            cols_to_keep = [i for i in range(len(df_s.columns)) if i not in [10, 11]]
            df_final_stock = df_s.iloc[:, cols_to_keep].copy()
            df_final_stock.insert(10, "QTY SO", new_qty_so.fillna(0))
            df_final_stock.insert(11, "DIFF", new_diff)

            matched_keys = set(df_s[new_qty_so.notna()]['JOIN_KEY'])
            df_missing_raw = df_r[~df_r['JOIN_KEY'].isin(matched_keys)].copy()

            valid_missing_rows = []
            for _, row in df_missing_raw.iterrows():
                q_rec_val = pd.to_numeric(row.iloc[6], errors='coerce') or 0
                if q_rec_val > 0: valid_missing_rows.append(row)

            if valid_missing_rows:
                df_missing = pd.DataFrame(valid_missing_rows)
                df_missing['FINAL_RECON_QTY'] = pd.to_numeric(df_missing.iloc[:, 6], errors='coerce').fillna(0)
                df_missing['QTY_SYSTEM'] = 0
            else:
                df_missing = pd.DataFrame(columns=df_r.columns.tolist() + ['FINAL_RECON_QTY', 'QTY_SYSTEM'])

            df_final_stock.drop(columns=['JOIN_KEY'], errors='ignore', inplace=True)
            df_missing.drop(columns=['JOIN_KEY'], errors='ignore', inplace=True)

            # Logic Pivot Adjustment
            pivot_list, single_list = [], []
            col_sku_stock = next((c for c in df_final_stock.columns if 'SKU' in c.upper()), df_final_stock.columns[2])
            q_so_v = pd.to_numeric(df_final_stock["QTY SO"], errors='coerce').fillna(0)
            q_sys_v = pd.to_numeric(df_final_stock.iloc[:, 9], errors='coerce').fillna(0)
            mask_plus = (q_so_v > q_sys_v) & (df_final_stock["DIFF"].notna())

            if mask_plus.any():
                for _, r in df_final_stock[mask_plus].iterrows():
                    pivot_list.append({'SKU_KEY_TEMP': super_clean(r[col_sku_stock]), 'QTY_TOTAL': pd.to_numeric(r["DIFF"], errors='coerce')})

            inbound_master = df_m5.copy()
            col_sku_inb = next((c for c in inbound_master.columns if 'SKU' in c.upper()), inbound_master.columns[2])
            inbound_master['SKU_JOIN'] = inbound_master[col_sku_inb].apply(super_clean)
            m_clean = inbound_master.drop_duplicates(subset=['SKU_JOIN'])
            inbound_skus_set = set(m_clean['SKU_JOIN'].unique())

            if not df_missing.empty:
                col_b_m = df_missing.columns[0]
                col_s_m = df_missing.columns[1]
                col_q_r = 'FINAL_RECON_QTY' if 'FINAL_RECON_QTY' in df_missing.columns else df_missing.columns[6]
                col_q_s = 'QTY_SYSTEM' if 'QTY_SYSTEM' in df_missing.columns else None

                for _, row in df_missing.iterrows():
                    s_rec = super_clean(row[col_s_m])
                    if not s_rec: continue
                    q_r_v = pd.to_numeric(row[col_q_r], errors='coerce') or 0
                    q_s_v = pd.to_numeric(row[col_q_s], errors='coerce') if col_q_s else 0
                    q_calc = q_r_v - q_s_v
                    if q_calc <= 0: continue

                    if s_rec in inbound_skus_set:
                        pivot_list.append({'SKU_KEY_TEMP': s_rec, 'QTY_TOTAL': q_calc})
                    else:
                        single_list.append({'BIN': row[col_b_m], 'SKU': row[col_s_m], 'QTY ADJ': q_calc})

            df_mult_res = pd.DataFrame()
            if pivot_list:
                df_p = pd.DataFrame(pivot_list)
                df_p_g = df_p.groupby('SKU_KEY_TEMP')['QTY_TOTAL'].sum().reset_index()
                mask_has_m = df_p_g['SKU_KEY_TEMP'].isin(inbound_skus_set)

                for _, row in df_p_g[~mask_has_m].iterrows():
                    single_list.append({'BIN': 'STAGING INBOUND (MISS MASTER)', 'SKU': row['SKU_KEY_TEMP'], 'QTY ADJ': row['QTY_TOTAL']})

                df_p_val = df_p_g[mask_has_m]
                if not df_p_val.empty:
                    df_mult_res = df_p_val.merge(m_clean, left_on='SKU_KEY_TEMP', right_on='SKU_JOIN', how='inner')
                    col_t_so = next((c for c in df_mult_res.columns if 'QTY SO' in c.upper() or 'SO' in c.upper()), None)
                    if col_t_so: df_mult_res[col_t_so] = df_mult_res['QTY_TOTAL']
                    else: df_mult_res['QTY SO'] = df_mult_res['QTY_TOTAL']
                    df_mult_res.drop(columns=['SKU_KEY_TEMP', 'QTY_TOTAL', 'SKU_JOIN'], errors='ignore', inplace=True)

            df_sing_res = pd.DataFrame(single_list) if single_list else pd.DataFrame(columns=['BIN', 'SKU', 'QTY ADJ'])

            if not df_mult_res.empty:
                last_col = df_mult_res.columns[-1]
                df_mult_res[last_col] = pd.to_numeric(df_mult_res[last_col], errors='coerce').fillna(0)
                df_mult_res = df_mult_res[df_mult_res[last_col] > 0].reset_index(drop=True)

            if not df_sing_res.empty:
                last_c = df_sing_res.columns[-1]
                df_sing_res[last_c] = pd.to_numeric(df_sing_res[last_c], errors='coerce').fillna(0)
                df_sing_res = df_sing_res[df_sing_res[last_c] > 0].reset_index(drop=True)

            self._raw_df_so_mult = df_mult_res.copy()
            self._raw_df_so_sing = df_sing_res.copy()
            self._raw_df_so_res4 = df_final_stock.copy()
            self._raw_df_so_miss4 = df_missing.copy()

            self.df_so_mult_headers.set(df_mult_res.columns.tolist() if not df_mult_res.empty else [])
            self.df_so_mult_rows.set(df_mult_res.fillna("").astype(str).values.tolist() if not df_mult_res.empty else [])
            self.df_so_sing_headers.set(df_sing_res.columns.tolist() if not df_sing_res.empty else [])
            self.df_so_sing_rows.set(df_sing_res.fillna("").astype(str).values.tolist() if not df_sing_res.empty else [])
            self.df_so_res4_headers.set(df_final_stock.columns.tolist() if not df_final_stock.empty else [])
            self.df_so_res4_rows.set(df_final_stock.fillna("").astype(str).values.tolist() if not df_final_stock.empty else [])
            self.df_so_miss4_headers.set(df_missing.columns.tolist() if not df_missing.empty else [])
            self.df_so_miss4_rows.set(df_missing.fillna("").astype(str).values.tolist() if not df_missing.empty else [])

            self.so_step4_done.set(True)
            return True, "Final Adjustment Step 4 Selesai!"
        except Exception as e:
            return False, f"Gagal Step 4: {e}"

    def run_so_step4_setup_real(self):
        try:
            if self._raw_df_so_res4.empty or self._raw_df_so_mult.empty:
                return False, "Jalankan Step 4 terlebih dahulu!"

            def clean_val(x):
                if pd.isna(x): return ""
                s = str(x).strip().upper()
                if s.startswith("SPE"): s = s[3:]
                if s.endswith('.0'): s = s[:-2]
                return s

            allowed_skus = set()
            col_s_m = self._raw_df_so_mult.columns[2] if len(self._raw_df_so_mult.columns) > 2 else self._raw_df_so_mult.columns[0]
            allowed_skus = set(self._raw_df_so_mult[col_s_m].apply(clean_val).unique())

            setup_real_data = []
            seen_entry = set()

            df_stock = self._raw_df_so_res4.copy()
            qty_system = pd.to_numeric(df_stock.iloc[:, 9], errors='coerce').fillna(0)
            qty_so = pd.to_numeric(df_stock.iloc[:, 10], errors='coerce').fillna(0)
            diff_val = pd.to_numeric(df_stock.iloc[:, 11], errors='coerce').fillna(0)

            for i in range(len(df_stock)):
                if qty_so.iloc[i] > qty_system.iloc[i]:
                    sku_key = clean_val(df_stock.iloc[i, 2])
                    bin_tujuan = df_stock.iloc[i, 1]
                    qty_mutasi = diff_val.iloc[i]
                    if sku_key in allowed_skus:
                        setup_real_data.append({"BIN AWAL": "STAGING INBOUND", "BIN TUJUAN": bin_tujuan, "SKU": sku_key, "QUANTITY": qty_mutasi, "NOTES": "MISS LOCATION"})
                        seen_entry.add(f"{sku_key}|{bin_tujuan}")

            if not self._raw_df_so_miss4.empty:
                for _, row_m in self._raw_df_so_miss4.iterrows():
                    bin_t_m = row_m.iloc[0]
                    sku_k_m = clean_val(row_m.iloc[1])
                    qty_m = pd.to_numeric(row_m.iloc[6], errors='coerce') or 0
                    if sku_k_m in allowed_skus and f"{sku_k_m}|{bin_t_m}" not in seen_entry:
                        setup_real_data.append({"BIN AWAL": "STAGING INBOUND", "BIN TUJUAN": bin_t_m, "SKU": sku_k_m, "QUANTITY": qty_m, "NOTES": "RELOCATION (MISSING)"})

            df_real = pd.DataFrame(setup_real_data) if setup_real_data else pd.DataFrame(columns=["BIN AWAL", "BIN TUJUAN", "SKU", "QUANTITY", "NOTES"])
            self._raw_df_so_setup4 = df_real.copy()
            self.df_so_setup4_headers.set(df_real.columns.tolist())
            self.df_so_setup4_rows.set(df_real.fillna("").astype(str).values.tolist())

            self.so_step4_setup_done.set(True)
            return True, "Set Up Real + Berhasil Dibuat!"
        except Exception as e:
            return False, f"Gagal Set Up Real +: {e}"

    def run_so_step5(self, f_k6, f_adj6):
        try:
            df_outstanding = load_data_from_info(f_k6)
            df_recon = load_data_from_info(f_adj6)

            if df_outstanding.empty or df_recon.empty:
                return False, "File System+ Recon & Stock Cek Adj- tidak boleh kosong!"

            def clean_val(x):
                if pd.isna(x): return ""
                s = str(x).strip().upper()
                if s.startswith("SPE"): s = s[3:].strip()
                if s.endswith('.0'): s = s[:-2]
                return s

            sys_map = {}
            for _, row in df_recon.iterrows():
                try:
                    k_sys = f"{clean_val(row.iloc[1])}|{clean_val(row.iloc[2])}"
                    val_sys = pd.to_numeric(row.iloc[9], errors='coerce')
                    sys_map[k_sys] = val_sys if not pd.isna(val_sys) else 0
                except: continue

            recon_map = {}
            for _, row in df_outstanding.iterrows():
                try:
                    k_rec = f"{clean_val(row.iloc[1])}|{clean_val(row.iloc[2])}"
                    val_rec = pd.to_numeric(row.iloc[13], errors='coerce')
                    recon_map[k_rec] = val_rec if not pd.isna(val_rec) else 0
                except: continue

            audit_results, karantina_results = [], []
            for _, row in df_outstanding.iterrows():
                bin_val, sku_val = row.iloc[1], row.iloc[2]
                key = f"{clean_val(bin_val)}|{clean_val(sku_val)}"
                q_sys = sys_map.get(key, 0)
                q_rec = recon_map.get(key, 0)
                diff = q_sys - q_rec

                if diff != 0:
                    audit_results.append({'BIN': bin_val, 'SKU': sku_val, 'QTY_SYSTEM_J': q_sys, 'QTY_RECON_N': q_rec, 'SELISIH': diff})
                    if diff > 0:
                        karantina_results.append({"BIN AWAL": bin_val, "BIN TUJUAN": "KARANTINA", "SKU": sku_val, "QUANTITY": diff, "NOTES": "NOT FOUND"})

            df_karantina = pd.DataFrame(karantina_results) if karantina_results else pd.DataFrame(columns=['BIN AWAL', 'BIN TUJUAN', 'SKU', 'QUANTITY', 'NOTES'])
            df_check = pd.DataFrame(audit_results) if audit_results else pd.DataFrame(columns=['BIN','SKU','QTY_SYSTEM_J','QTY_RECON_N','SELISIH'])

            self.so_qty_karantina.set(int(df_karantina['QUANTITY'].sum()) if not df_karantina.empty and 'QUANTITY' in df_karantina.columns else 0)
            self.so_sku_karantina.set(df_karantina['SKU'].nunique() if not df_karantina.empty and 'SKU' in df_karantina.columns else 0)

            self._raw_df_so_karantina = df_karantina.copy()
            self._raw_df_so_check5 = df_check.copy()

            self.df_so_karantina_headers.set(df_karantina.columns.tolist())
            self.df_so_karantina_rows.set(df_karantina.fillna("").astype(str).values.tolist())
            self.df_so_check5_headers.set(df_check.columns.tolist())
            self.df_so_check5_rows.set(df_check.fillna("").astype(str).values.tolist())

            self.so_step5_done.set(True)
            return True, "Analisis Karantina Step 5 Selesai!"
        except Exception as e:
            return False, f"Gagal Step 5: {e}"

    def run_so_step6_miss_loc(self):
        try:
            data_src = self._raw_df_so_setup_real if not self._raw_df_so_setup_real.empty else self._raw_df_so_setup4
            if data_src.empty: return False, "Data Set Up Real + belum tersedia!"

            columns_ref = ["BIN SYSTEM +", "BIN REAL +", "SKU", "QTY MISS LOC."]
            df_out = data_src.iloc[:, 0:4].copy()
            df_out.columns = columns_ref
            df_out["QTY MISS LOC."] = pd.to_numeric(df_out["QTY MISS LOC."], errors='coerce').fillna(0)

            count_sku = df_out["SKU"].nunique()
            count_qty = int(df_out["QTY MISS LOC."].sum())
            df_sum = pd.DataFrame({"METRIC": ["Total SKU Miss Loc", "Total Qty Miss Loc"], "VALUE": [count_sku, count_qty]})

            self.so_sku_miss_loc.set(count_sku)
            self.so_qty_miss_loc.set(count_qty)

            self._raw_df_so_miss_loc = df_out.copy()
            self._raw_df_so_sum_miss = df_sum.copy()

            self.df_so_miss_loc_headers.set(df_out.columns.tolist())
            self.df_so_miss_loc_rows.set(df_out.fillna("").astype(str).values.tolist())
            self.df_so_sum_miss_headers.set(df_sum.columns.tolist())
            self.df_so_sum_miss_rows.set(df_sum.fillna("").astype(str).values.tolist())

            self.so_step6a_done.set(True)
            return True, "Miss Location Report Berhasil Dibuat!"
        except Exception as e:
            return False, f"Gagal Miss Location: {e}"

    def run_so_step6_summary_adj(self, f_plus=None, f_minus=None):
        try:
            cols_header = ["BIN", "SKU", "BRAND", "ITEM NAME", "VARIANT", "SUB KATEGORI", "HARGA BELI", "HARGA JUAL", "QTY SYSTEM", "QTY SO", "VALUE ADJ", "STATUS ADJ"]

            active_plus = load_data_from_info(f_plus) if f_plus else self._raw_df_so_mult
            active_minus = load_data_from_info(f_minus) if f_minus else None

            if active_plus.empty:
                return False, "Data Stock Adj + tidak ditemukan!"

            def process_data(df, status):
                if df is None or (isinstance(df, pd.DataFrame) and df.empty):
                    return pd.DataFrame(columns=cols_header)
                temp = df.iloc[:, 1:11].copy()
                temp.columns = cols_header[:10]
                for col in ["HARGA BELI", "QTY SO", "QTY SYSTEM"]:
                    temp[col] = pd.to_numeric(temp[col], errors='coerce').fillna(0)
                temp["VALUE ADJ"] = (temp["QTY SO"] - temp["QTY SYSTEM"]) * temp["HARGA BELI"]
                temp["STATUS ADJ"] = status
                return temp

            df_adj_plus = process_data(active_plus, "ADJ +")
            df_adj_minus = process_data(active_minus, "ADJ -")
            df_final = pd.concat([df_adj_plus, df_adj_minus], ignore_index=True)

            val_plus = df_adj_plus["VALUE ADJ"].sum() if not df_adj_plus.empty else 0
            val_minus = df_adj_minus["VALUE ADJ"].sum() if not df_adj_minus.empty else 0
            qty_plus = (df_adj_plus["QTY SO"] - df_adj_plus["QTY SYSTEM"]).abs().sum() if not df_adj_plus.empty else 0
            qty_minus = -(df_adj_minus["QTY SO"] - df_adj_minus["QTY SYSTEM"]).abs().sum() if not df_adj_minus.empty else 0

            df_sum = pd.DataFrame({
                "METRIC": ["Total SKU Adj.", "Total Value Adj. +", "Total Value Adj. -", "Total QTY Adj. +", "Total QTY Adj. -", "Total Value", "Total QTY"],
                "VALUE": [len(df_final[df_final["SKU"].astype(str).str.strip() != ""]), val_plus, val_minus, qty_plus, qty_minus, val_plus + val_minus, qty_plus + qty_minus]
            })

            self.so_adj_val_p.set(val_plus)
            self.so_adj_val_m.set(val_minus)
            self.so_adj_val_net.set(val_plus + val_minus)
            self.so_adj_qty_p.set(int(qty_plus))
            self.so_adj_qty_m.set(int(qty_minus))
            self.so_adj_sku_tot.set(len(df_final))

            self._raw_df_so_adj_detail = df_final.copy()
            self._raw_df_so_adj_sum = df_sum.copy()

            self.df_so_adj_detail_headers.set(df_final.columns.tolist())
            self.df_so_adj_detail_rows.set(df_final.fillna("").astype(str).values.tolist())
            self.df_so_adj_sum_headers.set(df_sum.columns.tolist())
            self.df_so_adj_sum_rows.set(df_sum.fillna("").astype(str).values.tolist())

            self.so_step6b_done.set(True)
            return True, "Summary Adjustment Berhasil Dibuat!"
        except Exception as e:
            return False, f"Gagal Summary Adjustment: {e}"

# ==========================================================================
    # JUSTIFICATION SO ALGORITHM (PORTED FROM STREAMLIT)
    # ==========================================================================
    def process_justification_so(self, f_case, f_track, f_all_stock, f_scan=None):
        try:
            df_case = load_data_from_info(f_case)
            df_tracking = load_data_from_info(f_track)
            df_all_stock = load_data_from_info(f_all_stock)
            df_scan = load_data_from_info(f_scan) if f_scan else None

            if df_case.empty or df_tracking.empty or df_all_stock.empty:
                return False, "File Adjustment, Summary Stock, dan All Data Stock wajib diupload!"

            res = df_case.copy()
            res.columns = [str(c).upper().strip() for c in res.columns]

            df_tracking = df_tracking.copy()
            df_tracking.columns = [str(c).upper().strip() for c in df_tracking.columns]

            df_all_stock = df_all_stock.copy()
            df_all_stock.columns = [str(c).upper().strip() for c in df_all_stock.columns]

            sku_col_case = 'SKU'
            qty_sys_col_case = 'QTY SYSTEM'
            qty_so_col_case = 'QTY SO'

            res['SKU_KEY_JOIN'] = res[sku_col_case].astype(str).str.split('.').str[0].str.strip().str.upper()

            # 2. Aggregasi Tracking (Kolom A-O)
            sku_col_track = df_tracking.columns[2]
            track_agg = df_tracking.groupby(sku_col_track).agg({
                df_tracking.columns[4]: 'sum',
                df_tracking.columns[5]: 'sum',
                df_tracking.columns[6]: 'sum',
                df_tracking.columns[7]: 'sum',
                df_tracking.columns[8]: 'sum',
                df_tracking.columns[9]: 'sum',
                df_tracking.columns[10]: 'sum',
                df_tracking.columns[11]: 'sum',
                df_tracking.columns[12]: 'sum',
                df_tracking.columns[13]: 'sum',
                df_tracking.columns[14]: 'sum'
            }).reset_index()

            track_agg.columns = [
                'SKU_KEY', 'BEGINNING STOCK', '_F_STOCK_IN', '_G_ADJ_IN', '_H_TRF_IN',
                '_I_DRAFT_IN', '_J_SALES', '_K_ADJ_OUT', '_L_DRAFT_OUT', '_M_TRF_OUT',
                '_N_ENDING_STOCK', '_O_CURR_STOCK'
            ]
            track_agg['SKU_KEY'] = track_agg['SKU_KEY'].astype(str).str.split('.').str[0].str.strip().str.upper()

            # 3. Aggregasi All Data Stock
            sku_col_all = df_all_stock.columns[2]
            qty_sys_col_all = df_all_stock.columns[9]

            all_stock_agg = df_all_stock.groupby(sku_col_all).agg({
                qty_sys_col_all: 'sum'
            }).reset_index()

            all_stock_agg.columns = ['SKU_KEY_ALL', '_QTY_SYS_ALL']
            all_stock_agg['SKU_KEY_ALL'] = all_stock_agg['SKU_KEY_ALL'].astype(str).str.split('.').str[0].str.strip().str.upper()

            # 4. Merge Data
            res = res.merge(track_agg, left_on='SKU_KEY_JOIN', right_on='SKU_KEY', how='left').fillna(0)
            res = res.merge(all_stock_agg, left_on='SKU_KEY_JOIN', right_on='SKU_KEY_ALL', how='left').fillna(0)

            # 5. Mapping Kolom Final
            res['BEGINNING STOCK'] = res['BEGINNING STOCK']
            res['ENDING STOCK'] = res['_N_ENDING_STOCK']
            res['CURRENT STOCK'] = res['_O_CURR_STOCK']
            res['TOTAL_STOCKIN'] = res['_F_STOCK_IN']
            res['TOTAL_ADJ_PLUS'] = res['_G_ADJ_IN']
            res['TOTAL TRF_IN'] = res['_H_TRF_IN']
            res['TOTAL DRAFT_TRF_IN'] = res['_I_DRAFT_IN']
            res['TOTAL SALES'] = res['_J_SALES']
            res['TOTAL_ADJ_MINUS'] = res['_K_ADJ_OUT']
            res['TOTAL DRAFT_TRF_OUT'] = res['_L_DRAFT_OUT']
            res['TOTAL TRF_OUT'] = res['_M_TRF_OUT']
            res['QTY SYSTEM ALL'] = res['_QTY_SYS_ALL']
            res['GAP ADJUSMENT'] = res['TOTAL_ADJ_PLUS'] - res['TOTAL_ADJ_MINUS']

            # Real QTY Calculation
            if df_scan is not None and not df_scan.empty:
                df_scan_copy = df_scan.copy()
                sku_col_scan = df_scan_copy.columns[1]
                qty_col_scan = df_scan_copy.columns[2]

                scan_agg = df_scan_copy.groupby(sku_col_scan).agg({qty_col_scan: 'sum'}).reset_index()
                scan_agg.columns = ['SKU_KEY_SCAN', 'REAL_QTY_SCAN']
                scan_agg['SKU_KEY_SCAN'] = scan_agg['SKU_KEY_SCAN'].astype(str).str.split('.').str[0].str.strip().str.upper()

                res = res.merge(scan_agg, left_on='SKU_KEY_JOIN', right_on='SKU_KEY_SCAN', how='left').fillna(0)
                res['REAL QTY'] = res['REAL_QTY_SCAN']
                res = res.drop(columns=['SKU_KEY_SCAN', 'REAL_QTY_SCAN'], errors='ignore')
            else:
                res['REAL QTY'] = (
                    res['BEGINNING STOCK'] + res['TOTAL_STOCKIN'] + res['TOTAL TRF_IN']
                    - res['TOTAL SALES'] - res['TOTAL TRF_OUT'] - res['TOTAL DRAFT_TRF_OUT']
                )

            # 6. Formula Justifikasi Otomatis
            def run_formula(row):
                try:
                    qty_sys_row = round(float(row[qty_sys_col_case]), 2)
                    qty_so_row = round(float(row[qty_so_col_case]), 2)
                    begin_stock = round(float(row['BEGINNING STOCK']), 2)
                    stock_in = round(float(row['TOTAL_STOCKIN']), 2)
                    trf_in = round(float(row['TOTAL TRF_IN']), 2)
                    sales = round(float(row['TOTAL SALES']), 2)
                    trf_out = round(float(row['TOTAL TRF_OUT']), 2)
                    gap_adj = round(float(row['GAP ADJUSMENT']), 2)
                    curr_stock = round(float(row['CURRENT STOCK']), 2)
                    qty_sys_all = round(float(row['QTY SYSTEM ALL']), 2)
                    draft_in = round(float(row['TOTAL DRAFT_TRF_IN']), 2)
                    draft_out = round(float(row['TOTAL DRAFT_TRF_OUT']), 2)
                    ending_stock = round(float(row['ENDING STOCK']), 2)
                    real_qty = round(float(row['REAL QTY']), 2)

                    if qty_so_row > qty_sys_row and begin_stock < 0:
                        if gap_adj > 0 and gap_adj < abs(begin_stock): return "KESALAHAN SYSTEM (BEGIN STOCK -)"
                        elif gap_adj == 0: return "KESALAHAN SYSTEM (BEGIN STOCK -)"

                    if gap_adj == 0 and begin_stock == 0:
                        if ending_stock == real_qty == curr_stock:
                            if qty_sys_all < ending_stock: return "KESALAHAN SYSTEM"

                    if qty_sys_row > qty_so_row and gap_adj > 0: return "KESALAHAN ADJUSMENT +"
                    elif qty_sys_row < qty_so_row and gap_adj < 0: return "KESALAHAN ADJUSMENT -"

                    if qty_so_row > qty_sys_row and begin_stock >= 0 and gap_adj == 0 and draft_in == 0 and draft_out == 0:
                        mutasi_bersih = round(begin_stock + (stock_in + trf_in) - (sales + trf_out), 2)
                        if mutasi_bersih != ending_stock: return "KESALAHAN SYSTEM"

                    if gap_adj == 0:
                        if qty_sys_row > qty_so_row:
                            diff = qty_sys_row - qty_so_row
                            if round(qty_sys_all - diff, 2) == curr_stock: return "KESALAHAN SYSTEM"
                        elif qty_sys_row < qty_so_row:
                            diff = qty_so_row - qty_sys_row
                            if round(qty_sys_all + diff, 2) == curr_stock: return "KESALAHAN SYSTEM"

                    if draft_in > 0 or draft_out > 0: return "KESALAHAN RTO"
                    if qty_sys_all == curr_stock: return "CEK HASIL REKONSILIASI"

                    return "UNDEFINED"
                except:
                    return "ERROR DATA"

            res['JUSTIFICATION'] = res.apply(run_formula, axis=1)

            ordered_headers = [
                'IDENTIFY', 'BIN', 'SKU', 'BRAND', 'ITEM NAME', 'VARIANT', 'SUB KATEGORI',
                'HARGA BELI', 'HARGA JUAL', 'QTY SYSTEM', 'QTY SO',
                'BEGINNING STOCK', 'TOTAL_STOCKIN', 'TOTAL_ADJ_PLUS', 'TOTAL TRF_IN',
                'TOTAL DRAFT_TRF_IN', 'TOTAL SALES', 'TOTAL_ADJ_MINUS', 'TOTAL DRAFT_TRF_OUT',
                'TOTAL TRF_OUT', 'ENDING STOCK', 'REAL QTY', 'CURRENT STOCK',
                'QTY SYSTEM ALL', 'GAP ADJUSMENT', 'JUSTIFICATION'
            ]

            drop_cols = ['SKU_KEY_JOIN', 'SKU_KEY', 'SKU_KEY_ALL', '_F_STOCK_IN', '_G_ADJ_IN', '_H_TRF_IN', '_I_DRAFT_IN', '_J_SALES', '_K_ADJ_OUT', '_L_DRAFT_OUT', '_M_TRF_OUT', '_N_ENDING_STOCK', '_O_CURR_STOCK', '_QTY_SYS_ALL']
            res = res.drop(columns=[c for c in drop_cols if c in res.columns], errors='ignore')
            final_df = res[[c for c in ordered_headers if c in res.columns]].copy()

            # Hitung Metrik
            c_undef = len(final_df[final_df['JUSTIFICATION'] == "UNDEFINED"])
            c_sys = len(final_df[final_df['JUSTIFICATION'].isin(["KESALAHAN SYSTEM", "KESALAHAN SYSTEM (BEGIN STOCK -)"])])
            c_adj = len(final_df[final_df['JUSTIFICATION'].isin(["KESALAHAN ADJUSMENT +", "KESALAHAN ADJUSMENT -"])])
            c_rto = len(final_df[final_df['JUSTIFICATION'] == "KESALAHAN RTO"])
            c_rekon = len(final_df[final_df['JUSTIFICATION'] == "CEK HASIL REKONSILIASI"])

            self.jso_c_undef.set(c_undef)
            self.jso_c_sys.set(c_sys)
            self.jso_c_adj.set(c_adj)
            self.jso_c_rto.set(c_rto)
            self.jso_c_rekon.set(c_rekon)

            self._raw_df_jso_res = final_df.copy()
            self.df_jso_headers.set(final_df.columns.tolist())
            self.df_jso_rows.set(final_df.fillna("").astype(str).values.tolist())

            self.jso_processed.set(True)
            return True, f"Justifikasi Selesai! ({len(final_df):,} Baris Diproses)"
        except Exception as e:
            return False, f"Gagal Justifikasi SO: {e}"

# ==========================================================================
    # CROSS CHECK REAL & SYSTEM (INSTANT ENGINE)
    # ==========================================================================
    def process_cross_check_real_system(self, f_sys, f_real):
        try:
            df_sys_raw = load_data_from_info(f_sys)
            df_real_raw = load_data_from_info(f_real)

            if df_sys_raw.empty or df_real_raw.empty:
                return False, "Kedua file (Laporan System & Real) wajib diupload!"

            if df_sys_raw.shape[1] < 11:
                return False, "File System kurang dari 11 kolom (Kolom A=Cabang, D=SKU, K=Qty)!"
            if df_real_raw.shape[1] < 13:
                return False, "File Real kurang dari 13 kolom (Kolom A=Cabang, E=SKU, M=Qty)!"

            cab_sys_arr = df_sys_raw.iloc[:, 0].astype(str).str.strip().str.upper().to_numpy()
            sku_sys_arr = df_sys_raw.iloc[:, 3].astype(str).str.strip().str.upper().to_numpy()
            qty_sys_arr = pd.to_numeric(df_sys_raw.iloc[:, 10], errors='coerce').fillna(0).to_numpy()

            cab_real_arr = df_real_raw.iloc[:, 0].astype(str).str.strip().str.upper().to_numpy()
            sku_real_arr = df_real_raw.iloc[:, 4].astype(str).str.strip().str.upper().to_numpy()
            qty_real_arr = pd.to_numeric(df_real_raw.iloc[:, 12], errors='coerce').fillna(0).to_numpy()

            # Hash Map O(1) Lookup: {SKU: {CABANG: QTY}}
            system_pool = {}
            for i in range(len(sku_sys_arr)):
                s, q, c = sku_sys_arr[i], qty_sys_arr[i], cab_sys_arr[i]
                if q > 0 and s not in ("", "NAN", "NONE"):
                    if s not in system_pool:
                        system_pool[s] = {}
                    system_pool[s][c] = system_pool[s].get(c, 0.0) + q

            matched_records = []
            total_real_qty = 0
            total_allocated_qty = 0

            for i in range(len(sku_real_arr)):
                sku_r, qty_r, cab_r = sku_real_arr[i], qty_real_arr[i], cab_real_arr[i]
                if not sku_r or sku_r in ("", "NAN", "NONE") or qty_r <= 0:
                    continue

                total_real_qty += qty_r
                qty_sisa = qty_r
                pool_sku = system_pool.get(sku_r)

                if pool_sku:
                    # 1. Cabang Sendiri (Match Perfect)
                    avail_home = pool_sku.get(cab_r, 0.0)
                    if avail_home > 0:
                        take = avail_home if avail_home < qty_sisa else qty_sisa
                        pool_sku[cab_r] -= take
                        qty_sisa -= take
                        total_allocated_qty += take
                        matched_records.append((sku_r, cab_r, cab_r, int(take), "MATCH PERFECT"))

                    # 2. Lintas Cabang (Cross-Branch)
                    if qty_sisa > 0:
                        for cab_other, avail_other in pool_sku.items():
                            if avail_other > 0:
                                take = avail_other if avail_other < qty_sisa else qty_sisa
                                pool_sku[cab_other] -= take
                                qty_sisa -= take
                                total_allocated_qty += take
                                matched_records.append((sku_r, cab_r, cab_other, int(take), "MATCH CROSS-BRANCH"))
                                if qty_sisa <= 0:
                                    break

                # 3. Unmatched
                if qty_sisa > 0:
                    matched_records.append((sku_r, cab_r, "TIDAK KETEMU / SYSTEM HABIS", int(qty_sisa), "UNMATCHED / NO SYSTEM QTY"))

            total_system_left = sum(sum(branches.values()) for branches in system_pool.values())

            headers = ["SKU", "Cabang Real", "Cabang System", "Qty Match", "Status"]
            df_res = pd.DataFrame(matched_records, columns=headers) if matched_records else pd.DataFrame(columns=headers)

            self.crs_total_real.set(int(total_real_qty))
            self.crs_total_matched.set(int(total_allocated_qty))
            self.crs_total_unmatched.set(int(total_real_qty - total_allocated_qty))
            self.crs_system_left.set(int(total_system_left))

            self._raw_df_crs_all = df_res.copy()
            self.df_crs_headers.set(headers)
            self.df_crs_rows.set(df_res.fillna("").astype(str).values.tolist())

            self.crs_processed.set(True)
            return True, "Matching Selesai!"
        except Exception as e:
            return False, f"Gagal Match Real & System: {e}"

# ==========================================================================
    # BALANCING STOCK & DYNAMIC ALLOCATION HYBRID ENGINE (FIXED)
    # ==========================================================================
    def process_balancing_stock(self, f_stock, f_sales):
        try:
            # 1. Helper Pembaca File Bersih & Cepat
            def fast_read(file_info):
                if not file_info: return pd.DataFrame()
                path = file_info[0]["datapath"]
                name = file_info[0]["name"].lower()
                if name.endswith(('.xlsx', '.xls')):
                    try:
                        return pd.read_excel(path, engine='calamine')
                    except Exception:
                        return pd.read_excel(path, engine='openpyxl')
                elif name.endswith('.csv'):
                    return pd.read_csv(path)
                return pd.DataFrame()

            df_stk_raw = fast_read(f_stock)
            df_sls_raw = fast_read(f_sales)

            if df_stk_raw.empty or df_sls_raw.empty:
                return False, "Kedua file (All Stock & Laporan Sales) wajib diupload!"

            if df_stk_raw.shape[1] < 10:
                return False, "File All Stock minimal harus 10 kolom (Kolom B=BIN, C=SKU, E=Nama, J=Qty)!"

            # 2. Proses Data Sales (Histori Online vs Offline)
            col_store_idx = 0
            col_qty_sls_idx = 18 if df_sls_raw.shape[1] > 18 else df_sls_raw.shape[1] - 1
            col_sku_sls_idx = 26 if df_sls_raw.shape[1] > 26 else (1 if df_sls_raw.shape[1] > 1 else 0)

            store_series = df_sls_raw.iloc[:, col_store_idx].astype(str).str.upper()
            sku_sls_series = df_sls_raw.iloc[:, col_sku_sls_idx].astype(str).str.strip().str.upper()
            qty_sls_series = pd.to_numeric(df_sls_raw.iloc[:, col_qty_sls_idx], errors='coerce').fillna(0)

            df_sls_clean = pd.DataFrame({
                'SKU': sku_sls_series,
                'SALES_ONLINE': np.where(store_series.str.contains('ONLINE|ONL|WEB|SHOPEE|TOKOPEDIA|TIKTOK|LAZADA', na=False), qty_sls_series, 0),
                'SALES_OFFLINE': np.where(store_series.str.contains('JEZ|STORE|TOKO|OFFLINE|SURABAYA|MALANG|JEMBER|KEDIRI|SIDOARJO|SEMARANG', na=False), qty_sls_series, 0)
            })
            df_sls_clean = df_sls_clean[(df_sls_clean['SKU'] != '') & (df_sls_clean['SKU'] != 'NAN')]
            sales_summary = df_sls_clean.groupby('SKU', as_index=False).agg({'SALES_ONLINE': 'sum', 'SALES_OFFLINE': 'sum'})
            sales_summary['TOTAL_SALES'] = sales_summary['SALES_ONLINE'] + sales_summary['SALES_OFFLINE']
            sales_dict = sales_summary.set_index('SKU').to_dict(orient='index')

            # 3. Proses Data Stock Aktual per BIN
            col_bin_raw = df_stk_raw.iloc[:, 1].astype(str).str.strip().str.upper()
            col_sku_raw = df_stk_raw.iloc[:, 2].astype(str).str.strip().str.upper()
            col_name_raw = df_stk_raw.iloc[:, 4].astype(str).str.strip() if df_stk_raw.shape[1] > 4 else df_stk_raw.iloc[:, 2]
            col_qty_raw = pd.to_numeric(df_stk_raw.iloc[:, 9], errors='coerce').fillna(0)

            # Filter Eksklusi Global
            excl_kw = "DEFECT|REJECT|KARANTINA|MARKOM|AMP|LIVE|RUSAK"
            mask_valid = ~col_bin_raw.str.contains(excl_kw, na=False) & (col_sku_raw != "") & (col_sku_raw != "NAN")

            df_valid_stk = pd.DataFrame({
                'BIN': col_bin_raw[mask_valid],
                'SKU': col_sku_raw[mask_valid],
                'NAMA': col_name_raw[mask_valid],
                'QTY': col_qty_raw[mask_valid]
            })

            # Mapping Deskripsi Item
            sku_name_map = df_valid_stk.drop_duplicates('SKU').set_index('SKU')['NAMA'].to_dict()

            # Kategorisasi BIN:
            # - SOURCE: mengandung LOG / INB / GL4
            # - TARGET OFFLINE: mengandung OFF / TOKO / STORE / GL2-STORE / GUDANG LT.2
            # - TARGET ONLINE: mengandung ONL / ONLINE / HUB
            is_source = df_valid_stk['BIN'].str.contains('LOG|INB|GL4|GL1-DC|GL3-DC', na=False) & ~df_valid_stk['BIN'].str.contains('OFF|ONL|TOKO|STORE', na=False)
            is_target_off = df_valid_stk['BIN'].str.contains('OFF|TOKO|STORE|GL2-STORE|GUDANG LT.2|OUT', na=False)
            is_target_on = df_valid_stk['BIN'].str.contains('ONL|ONLINE|HUB', na=False)

            df_valid_stk['IS_SOURCE'] = is_source
            df_valid_stk['IS_OFF'] = is_target_off
            df_valid_stk['IS_ON'] = is_target_on

            # 4. Agregasi Stok per SKU
            sku_agg = df_valid_stk.groupby('SKU').agg(
                TOTAL_STOCK=('QTY', lambda x: x[x > 0].sum()),
                STOCK_SOURCE=('QTY', lambda x: x[df_valid_stk.loc[x.index, 'IS_SOURCE'] & (x > 0)].sum()),
                STOCK_OFF_ACTUAL=('QTY', lambda x: x[df_valid_stk.loc[x.index, 'IS_OFF'] & (x > 0)].sum()),
                STOCK_ON_ACTUAL=('QTY', lambda x: x[df_valid_stk.loc[x.index, 'IS_ON'] & (x > 0)].sum())
            ).reset_index()

            # Simpan detail lokasi BIN asal
            source_bins_detail = df_valid_stk[df_valid_stk['IS_SOURCE'] & (df_valid_stk['QTY'] > 0)].groupby(['SKU', 'BIN'])['QTY'].sum().to_dict()

            allocation_rows = []
            refill_instructions = []
            off_missing_list = []
            on_missing_list = []

            for _, row in sku_agg.iterrows():
                sku = row['SKU']
                tot_stk = int(row['TOTAL_STOCK'])
                stk_src = int(row['STOCK_SOURCE'])
                act_off = int(row['STOCK_OFF_ACTUAL'])
                act_on = int(row['STOCK_ON_ACTUAL'])

                if tot_stk <= 0:
                    continue

                # Ambil Histori Sales
                sls_info = sales_dict.get(sku, {'SALES_ONLINE': 0, 'SALES_OFFLINE': 0, 'TOTAL_SALES': 0})
                s_on = sls_info['SALES_ONLINE']
                s_off = sls_info['SALES_OFFLINE']
                s_tot = sls_info['TOTAL_SALES']

                # Hitung Rasio & Target Ideal Alokasi
                if s_tot == 0:
                    pct_on, pct_off, pct_log = 0.10, 0.10, 0.80
                    kategori = "NO SALES HISTORY (80% LOGISTIK)"
                else:
                    ratio_on = s_on / s_tot
                    ratio_off = s_off / s_tot
                    if ratio_on > 0.70:
                        pct_on, pct_off, pct_log = 0.70, 0.15, 0.15
                        kategori = "DOMINAN ONLINE (>70%)"
                    elif ratio_off > 0.70:
                        pct_on, pct_off, pct_log = 0.15, 0.70, 0.15
                        kategori = "DOMINAN OFFLINE (>70%)"
                    else:
                        pct_on, pct_off, pct_log = 0.40, 0.40, 0.20
                        kategori = "BALANCED (40:40:20)"

                # Hitung Qty Ideal Target
                target_on = int(np.ceil(tot_stk * pct_on))
                target_off = int(np.ceil(tot_stk * pct_off))
                target_log = tot_stk - target_on - target_off

                # Penyesuaian Proteksi Ceil
                if target_log < 0:
                    excess = abs(target_log)
                    target_log = 0
                    if target_on > target_off:
                        target_on = max(0, target_on - excess)
                    else:
                        target_off = max(0, target_off - excess)

                item_desc = sku_name_map.get(sku, "-")

                allocation_rows.append({
                    "SKU": sku,
                    "ITEM NAME": item_desc,
                    "TOTAL STOCK": tot_stk,
                    "SALES ONL": int(s_on),
                    "SALES OFF": int(s_off),
                    "KLASIFIKASI": kategori,
                    "IDEAL ONL": target_on,
                    "IDEAL OFF": target_off,
                    "IDEAL LOG": target_log,
                    "ACTUAL ONL": act_on,
                    "ACTUAL OFF": act_off,
                    "ACTUAL SOURCE": stk_src
                })

                # Logika Balancing & Refill dari BIN Acuan (LOG / INB)
                sisa_source_refill = stk_src
                available_bins = [b for (s, b), q in source_bins_detail.items() if s == sku and q > 0]
                bin_asal_utama = available_bins[0] if available_bins else "LOGISTIK / INBOUND"

                # 1. Cek Kebutuhan Refill Offline
                if act_off < target_off:
                    defisit_off = target_off - act_off
                    qty_refill_off = min(defisit_off, sisa_source_refill)
                    status_off = "HABIS DI STORE (0 QTY)" if act_off == 0 else "KURANG DARI TARGET IDEAL"

                    off_missing_list.append({
                        "SKU": sku,
                        "ITEM NAME": item_desc,
                        "STOK OFFLINE SAAT INI": act_off,
                        "TARGET IDEAL OFFLINE": target_off,
                        "DEFISIT QTY": defisit_off,
                        "STOK SUMBER (LOG/INB)": stk_src,
                        "QTY DAPAT DI-REFILL": qty_refill_off,
                        "STATUS": status_off
                    })

                    if qty_refill_off > 0:
                        refill_instructions.append({
                            "BIN AWAL": bin_asal_utama,
                            "BIN TUJUAN": "TOKO / OFFLINE ZONE",
                            "SKU": sku,
                            "ITEM NAME": item_desc,
                            "QTY REFILL": qty_refill_off,
                            "NOTES": f"BALANCING OFFLINE ({status_off})"
                        })
                        sisa_source_refill -= qty_refill_off

                # 2. Cek Kebutuhan Refill Online
                if act_on < target_on:
                    defisit_on = target_on - act_on
                    qty_refill_on = min(defisit_on, sisa_source_refill)
                    status_on = "HABIS DI ONLINE (0 QTY)" if act_on == 0 else "KURANG DARI TARGET IDEAL"

                    on_missing_list.append({
                        "SKU": sku,
                        "ITEM NAME": item_desc,
                        "STOK ONLINE SAAT INI": act_on,
                        "TARGET IDEAL ONLINE": target_on,
                        "DEFISIT QTY": defisit_on,
                        "STOK SUMBER (LOG/INB)": stk_src,
                        "QTY DAPAT DI-REFILL": qty_refill_on,
                        "STATUS": status_on
                    })

                    if qty_refill_on > 0:
                        refill_instructions.append({
                            "BIN AWAL": bin_asal_utama,
                            "BIN TUJUAN": "ONLINE / HUB ZONE",
                            "SKU": sku,
                            "ITEM NAME": item_desc,
                            "QTY REFILL": qty_refill_on,
                            "NOTES": f"BALANCING ONLINE ({status_on})"
                        })

            # DataFrames
            df_alloc = pd.DataFrame(allocation_rows)
            df_refill = pd.DataFrame(refill_instructions)
            df_off_miss = pd.DataFrame(off_missing_list)
            df_on_miss = pd.DataFrame(on_missing_list)

            # Hitung Metrik Dashboard
            tot_sku_count = len(df_alloc)
            tot_stock_pcs = int(df_alloc['TOTAL STOCK'].sum()) if not df_alloc.empty else 0
            need_off_sku = len(df_off_miss)
            need_on_sku = len(df_on_miss)
            total_refill_qty = int(df_refill['QTY REFILL'].sum()) if not df_refill.empty else 0

            ready_off = tot_sku_count - need_off_sku
            ready_on = tot_sku_count - need_on_sku
            perc_off = (ready_off / tot_sku_count * 100) if tot_sku_count > 0 else 0.0
            perc_on = (ready_on / tot_sku_count * 100) if tot_sku_count > 0 else 0.0

            # Set Reactive Values
            self.bs_total_sku.set(tot_sku_count)
            self.bs_total_stock.set(tot_stock_pcs)
            self.bs_sku_need_off.set(need_off_sku)
            self.bs_sku_need_on.set(need_on_sku)
            self.bs_qty_refill_total.set(total_refill_qty)
            self.bs_perc_offline.set(perc_off)
            self.bs_perc_online.set(perc_on)

            self._raw_df_bs_refill = df_refill
            self._raw_df_bs_alloc = df_alloc
            self._raw_df_bs_off_missing = df_off_miss
            self._raw_df_bs_on_missing = df_on_miss

            self.df_bs_refill_headers.set(df_refill.columns.tolist() if not df_refill.empty else [])
            self.df_bs_refill_rows.set(df_refill.fillna("").astype(str).values.tolist() if not df_refill.empty else [])

            self.df_bs_alloc_headers.set(df_alloc.columns.tolist() if not df_alloc.empty else [])
            self.df_bs_alloc_rows.set(df_alloc.fillna("").astype(str).values.tolist() if not df_alloc.empty else [])

            self.df_bs_off_missing_headers.set(df_off_miss.columns.tolist() if not df_off_miss.empty else [])
            self.df_bs_off_missing_rows.set(df_off_miss.fillna("").astype(str).values.tolist() if not df_off_miss.empty else [])

            self.df_bs_on_missing_headers.set(df_on_miss.columns.tolist() if not df_on_miss.empty else [])
            self.df_bs_on_missing_rows.set(df_on_miss.fillna("").astype(str).values.tolist() if not df_on_miss.empty else [])

            self.bs_processed.set(True)
            return True, f"Balancing Stock Selesai! ({len(df_refill):,} instruksi mutasi refill dibuat)"
        except Exception as e:
            return False, f"Gagal memproses Balancing Stock: {e}"