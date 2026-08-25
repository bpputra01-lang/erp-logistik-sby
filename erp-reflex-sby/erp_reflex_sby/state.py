import reflex as rx
import pandas as pd
from datetime import datetime
import io
import asyncio
import time
from .database import get_supabase

class AppState(rx.State):
    # --- NAVIGATION & ROLE STATE ---
    logged_in: bool = False
    role: str = "toko"
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
    is_info_open: bool = False  
    is_loading: bool = False
    show_success_modal: bool = False    
    
    total_qty_minus: int = 0
    total_tercover: int = 0
    total_sisa_adj: int = 0
    
    df_minus_awal_headers: list[str] = []
    df_minus_awal_rows: list[list[str]] = []
    
    df_set_up_headers: list[str] = []
    df_set_up_rows: list[list[str]] = []
    
    df_need_adj_headers: list[str] = []
    df_need_adj_rows: list[list[str]] = []

    def set_is_info_open(self, val: bool):
        self.is_info_open = val

    def set_show_success_modal(self, val: bool):
        self.show_success_modal = val

    def toggle_sidebar(self):
        self.sidebar_open = not self.sidebar_open

    def toggle_dropdown(self, key: str):
        if key == "operational": self.dropdown_operational = not self.dropdown_operational
        elif key == "inventory": self.dropdown_inventory = not self.dropdown_inventory
        elif key == "reject": self.dropdown_reject = not self.dropdown_reject
        elif key == "extras": self.dropdown_extras = not self.dropdown_extras

    # --- LOGIN STATE ---
    username: str = ""
    password: str = ""
    branch: str = ""
    user_display_name: str = ""
    login_timestamp_ms: int = 0 

    def set_username(self, val: str): self.username = val
    def set_password(self, val: str): self.password = val

    def handle_login(self):
        if self.username == "admin" and self.password == "sby123":
            self.logged_in = True; self.role = "DC"; self.branch = "SURABAYA"; self.user_display_name = "Admin DC Surabaya"
            self.login_timestamp_ms = int(time.time() * 1000)
            return rx.toast.success("Berhasil Login! Selamat datang di ERP Surabaya.", duration=4000, position="top-right")
        
        elif self.username == "toko" and self.password == "toko123":
            self.logged_in = True; self.role = "CABANG"; self.branch = "SURABAYA"; self.user_display_name = "User Cabang"
            self.login_timestamp_ms = int(time.time() * 1000)
            return rx.toast.success("Berhasil Login sebagai User Cabang!", duration=4000, position="top-right")
        
        else:
            return rx.toast.error("Username atau Password salah! Periksa kembali.", duration=4000, position="top-right")

    def handle_key_down(self, key: str):
        if key == "Enter": return self.handle_login()

    def logout(self):
        self.logged_in = False; self.username = ""; self.password = ""; self.role = "toko"
        self.login_timestamp_ms = 0
        return rx.toast.info("Anda telah keluar dari sistem.")

    # --- FITUR DOWNLOAD EXCEL ---
    async def download_excel_data(self, tab_name: str):
        output = io.BytesIO()
        df = pd.DataFrame()
        filename = "download.xlsx"

        if tab_name == "minus_awal" and self.df_minus_awal_headers:
            df = pd.DataFrame(self.df_minus_awal_rows, columns=self.df_minus_awal_headers)
            filename = "Data_Minus_Awal.xlsx"
        elif tab_name == "set_up" and self.df_set_up_headers:
            df = pd.DataFrame(self.df_set_up_rows, columns=self.df_set_up_headers)
            filename = "Template_Set_Up.xlsx"
        elif tab_name == "justifikasi" and self.df_need_adj_headers:
            df = pd.DataFrame(self.df_need_adj_rows, columns=self.df_need_adj_headers)
            filename = "Data_Justifikasi.xlsx"
        else:
            return rx.toast.warning("Data kosong, tidak ada yang didownload.", position="top-center")

        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        
        return rx.download(data=output.getvalue(), filename=filename)

    # --- ONGKIR DATABASE STATE ---
    data_list: list[dict] = []
    input_supplier: str = ""; input_ekspedisi: str = ""; input_koli: str = "1"; input_ongkir: str = "0"
    input_tgl: str = datetime.now().strftime("%Y-%m-%d"); input_jam: str = datetime.now().strftime("%H:%M:%S")
    filter_ekspedisi: str = "SEMUA"; selected_ids: list[int] = []; show_delete_modal: bool = False

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
        payload = {"supplier": self.input_supplier.upper().strip(), "ekspedisi": self.input_ekspedisi.upper().strip(), "total_koli": koli_val, "total_ongkir": ongkir_val, "created_at": fix_dt}
        try:
            client = get_supabase()
            await asyncio.to_thread(lambda: client.table("shipping_costs").insert(payload).execute())
            self.input_supplier = ""; self.input_ekspedisi = ""; self.input_koli = "1"; self.input_ongkir = "0"
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
                batch_data.append({"supplier": sup, "ekspedisi": eks, "total_koli": koli, "total_ongkir": ongkir, "created_at": fix_dt})
            if batch_data:
                try:
                    client = get_supabase()
                    await asyncio.to_thread(lambda: client.table("shipping_costs").insert(batch_data).execute())
                    yield rx.toast.success(f"🚀 Berhasil Upload {len(batch_data)} Data CSV!")
                    yield AppState.load_data()
                except Exception as e:
                    yield rx.toast.error(f"Gagal Upload Batch: {e}")

    def toggle_select_id(self, item_id: int):
        if item_id in self.selected_ids: self.selected_ids.remove(item_id)
        else: self.selected_ids.append(item_id)

    def open_delete_modal(self):
        if self.selected_ids: self.show_delete_modal = True

    def close_delete_modal(self):
        self.show_delete_modal = False

    async def execute_delete(self):
        try:
            client = get_supabase()
            await asyncio.to_thread(lambda: client.table("shipping_costs").delete().in_("id", self.selected_ids).execute())
            self.selected_ids = []; self.show_delete_modal = False
            yield rx.toast.success("🗑️ Data Berhasil Dihapus!")
            yield AppState.load_data()
        except Exception as e:
            yield rx.toast.error(f"Gagal Hapus: {e}")

    # --- STOCK MINUS FILE HANDLER & LOGIC ---
    async def handle_upload_stock_minus(self, files: list[rx.UploadFile]):
        if not files:
            yield rx.toast.warning("Pilih file Excel terlebih dahulu!")
            return

        self.is_loading = True
        yield

        try:
            for file in files:
                upload_data = await file.read()
                df = pd.read_excel(io.BytesIO(upload_data), engine="openpyxl")
                df.columns = [str(c).strip().upper() for c in df.columns]
                
                col_sku = 'SKU'
                col_bin = 'BIN'
                col_qty = next((c for c in df.columns if 'QTY SYSTEM' in c or 'QTY SYS' in c), None)
                
                if col_qty is None:
                    self.is_loading = False
                    yield rx.toast.error("❌ Kolom 'QTY SYSTEM' tidak ditemukan!")
                    return
                
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

                self.total_qty_minus = int(abs(pd.to_numeric(df_minus_awal[col_qty], errors='coerce').sum()))
                self.total_tercover = int(df_s["QUANTITY"].sum()) if not df_s.empty else 0
                self.total_sisa_adj = int(abs(df_n[col_qty].sum())) if not df_n.empty and col_qty in df_n.columns else 0
                
                if not df_minus_awal.empty:
                    df_m_clean = df_minus_awal.fillna("").astype(str)
                    self.df_minus_awal_headers = df_m_clean.columns.tolist()
                    self.df_minus_awal_rows = df_m_clean.values.tolist()
                else:
                    self.df_minus_awal_headers = []; self.df_minus_awal_rows = []

                if not df_s.empty:
                    df_s_clean = df_s.fillna("").astype(str)
                    self.df_set_up_headers = df_s_clean.columns.tolist()
                    self.df_set_up_rows = df_s_clean.values.tolist()
                else:
                    self.df_set_up_headers = []; self.df_set_up_rows = []

                if not df_n.empty:
                    df_n_clean = df_n.fillna("").astype(str)
                    self.df_need_adj_headers = df_n_clean.columns.tolist()
                    self.df_need_adj_rows = df_n_clean.values.tolist()
                else:
                    self.df_need_adj_headers = []; self.df_need_adj_rows = []
                
                self.stock_minus_processed = True

            self.is_loading = False
            self.show_success_modal = True
            yield
            
            await asyncio.sleep(2.5)
            self.show_success_modal = False
            yield
            
        except Exception as e:
            self.is_loading = False
            yield rx.toast.error(f"Gagal memproses file: {e}", position="top-center")

    # ==========================================
    # --- PUTAWAY SYSTEM STATE & LOGIC ---
    # ==========================================
    area_putaway: str = ""
    putaway_processed: bool = False

    # Variabel Internal Server untuk menampung data file sementara
    _ds_file_data: bytes = b""
    _ds_file_name: str = ""
    _asal_file_data: bytes = b""
    _asal_file_name: str = ""
    
    # Metrics Putaway
    putaway_qty_system: int = 0
    putaway_total_setup: int = 0
    putaway_kurang_setup: int = 0
    putaway_sisa_stok: int = 0
    
    # Data DataFrames (Headers & Rows)
    df_comp_headers: list[str] = []
    df_comp_rows: list[list[str]] = []
    df_plist_headers: list[str] = []
    df_plist_rows: list[list[str]] = []
    df_kurang_headers: list[str] = []
    df_kurang_rows: list[list[str]] = []
    df_out_headers: list[str] = []
    df_out_rows: list[list[str]] = []
    
    # Variabel internal untuk keperluan Download Excel
    _raw_df_comp: pd.DataFrame = pd.DataFrame()
    _raw_df_plist: pd.DataFrame = pd.DataFrame()
    _raw_df_kurang: pd.DataFrame = pd.DataFrame()
    _raw_df_out: pd.DataFrame = pd.DataFrame()
    _raw_df_updated: pd.DataFrame = pd.DataFrame()

    def set_area_putaway(self, val: str):
        self.area_putaway = val

    # 🔥 FUNGSI BARU: Mereset buffer/memori sebelum proses berjalan
    def reset_buffers(self):
        self._ds_file_data = b""
        self._asal_file_data = b""
        self._ds_file_name = ""
        self._asal_file_name = ""

    # 🔥 FUNGSI BARU: Tangkap File DS Putaway
    async def handle_upload_ds(self, files: list[rx.UploadFile]):
        if files:
            self._ds_file_data = await files[0].read()
            self._ds_file_name = files[0].filename

    # 🔥 FUNGSI BARU: Tangkap File Asal Bin
    async def handle_upload_asal(self, files: list[rx.UploadFile]):
        if files:
            self._asal_file_data = await files[0].read()
            self._asal_file_name = files[0].filename

    # 🔥 PERBAIKAN: Fungsi Utama, menggunakan wait-loop agar tidak error saat klik pertama
    async def handle_process_putaway(self):
        if not self.area_putaway:
            yield rx.toast.warning("Silakan pilih Area Putaway terlebih dahulu!", position="top-center")
            return
        
        self.is_loading = True
        yield

        # WAIT-LOOP: Sistem sabar menunggu maksimal 2 detik hingga file ter-upload
        for _ in range(20): 
            if self._ds_file_data and self._asal_file_data:
                break
            await asyncio.sleep(0.1)

        # Validasi akhir: Jika tetap kosong setelah ditunggu, munculkan peringatan
        if not self._ds_file_data or not self._asal_file_data:
            self.is_loading = False
            yield rx.toast.warning("Harap upload KEDUA file (DS Putaway & Asal Bin)!", position="top-center")
            return

        try:
            # 1. Baca Data dari Memori Server
            ds_data = self._ds_file_data
            df_ds = pd.read_csv(io.BytesIO(ds_data)) if self._ds_file_name.endswith('.csv') else pd.read_excel(io.BytesIO(ds_data), engine="openpyxl")
            
            asal_data = self._asal_file_data
            df_asal = pd.read_csv(io.BytesIO(asal_data)) if self._asal_file_name.endswith('.csv') else pd.read_excel(io.BytesIO(asal_data), engine="openpyxl")

            df_asal_updated = df_asal.copy()
            self.putaway_qty_system = int(pd.to_numeric(df_asal_updated.iloc[:, 9], errors='coerce').sum())

            # Helper Kolom Dinamis
            def get_col_idx(df, keywords, default_idx):
                for i, col in enumerate(df.columns):
                    if any(k.lower() in str(col).lower() for k in keywords): return i
                return default_idx

            c_bin_a = get_col_idx(df_asal, ['bin', 'lokasi'], 1)
            c_sku_a = get_col_idx(df_asal, ['sku', 'item code'], 2)
            c_qty_a = get_col_idx(df_asal, ['qty system', 'quantity', 'stok'], 9)

            c_bin_d = get_col_idx(df_ds, ['bin', 'tujuan'], 0)
            c_sku_d = get_col_idx(df_ds, ['sku', 'item'], 1)
            c_qty_d = get_col_idx(df_ds, ['qty', 'jumlah'], 2)

            # Dictionary Mapping
            bin_qty_dict = {}
            for _, row in df_asal_updated.iterrows():
                try:
                    key = f"{str(row.iloc[c_bin_a])}|{str(row.iloc[c_sku_a])}"
                    qty = pd.to_numeric(row.iloc[c_qty_a], errors='coerce')
                    bin_qty_dict[key] = qty if pd.notna(qty) else 0
                except: continue

            # Main Logic (Covering Stock)
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

            # Extract DataFrames
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
            
            # Logic Filter Keyword
            if self.area_putaway == "DC LANTAI 1": kw_out = ["GL1-DC-PUTAWAY", "STAG"]
            elif self.area_putaway == "DC LANTAI 2": kw_out = ["GL2-DC-PUTAWAY", "STAG"]
            elif self.area_putaway == "DC LANTAI 3": kw_out = ["GL3-DC-PUTAWAY", "STAG"]
            elif self.area_putaway == "JERSEY ZONE": kw_out = ["JZ-PUTAWAY", "STAG"]
            else: kw_out = ["STAG", "PUTAWAY"]

            bin_series = df_asal_updated.iloc[:, c_bin_a].astype(str).str.upper()
            mask_kw = bin_series.str.contains(kw_out[0], na=False)
            for kw in kw_out[1:]:
                mask_kw = mask_kw | bin_series.str.contains(kw, na=False)

            mask_out = (pd.to_numeric(df_asal_updated.iloc[:, c_qty_a], errors='coerce') > 0) & mask_kw
            df_outstanding = df_asal_updated[mask_out].copy()

            # Assign Metrics
            self.putaway_total_setup = int(df_plist['QUANTITY'].sum()) if not df_plist.empty else 0
            self.putaway_kurang_setup = int(df_kurang['DIFF'].sum()) if not df_kurang.empty else 0
            
            self.putaway_sisa_stok = 0
            if not df_outstanding.empty:
                qty_col = [c for c in df_outstanding.columns if 'qty' in str(c).lower()]
                if qty_col: self.putaway_sisa_stok = int(pd.to_numeric(df_outstanding[qty_col[0]], errors='coerce').sum())

            # Convert to State Headers & Rows
            def to_state(df):
                if df.empty: return [], []
                clean = df.fillna("").astype(str)
                return clean.columns.tolist(), clean.values.tolist()

            self.df_comp_headers, self.df_comp_rows = to_state(df_comp)
            self.df_plist_headers, self.df_plist_rows = to_state(df_plist)
            self.df_kurang_headers, self.df_kurang_rows = to_state(df_kurang)
            self.df_out_headers, self.df_out_rows = to_state(df_outstanding)
            
            # Save Raw for Export
            self._raw_df_comp = df_comp
            self._raw_df_plist = df_plist
            self._raw_df_kurang = df_kurang
            self._raw_df_out = df_outstanding
            self._raw_df_updated = df_asal_updated
            
            self.putaway_processed = True
            
            self.is_loading = False
            self.show_success_modal = True
            yield
            
            await asyncio.sleep(2.5)
            self.show_success_modal = False
            yield
            
        except Exception as e:
            self.is_loading = False
            yield rx.toast.error(f"Gagal memproses file: {e}", position="top-center")
            
    async def download_putaway_report(self):
        if not self.putaway_processed:
            return rx.toast.warning("Belum ada data untuk didownload!", position="top-center")
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            self._raw_df_comp.to_excel(writer, sheet_name='COMPARE', index=False)
            self._raw_df_plist.to_excel(writer, sheet_name='PUTAWAY_LIST', index=False)
            self._raw_df_kurang.to_excel(writer, sheet_name='KURANG_SETUP', index=False)
            self._raw_df_out.to_excel(writer, sheet_name='OUTSTANDING', index=False)
            self._raw_df_updated.to_excel(writer, sheet_name='SISA_STOK_SYSTEM', index=False)
        
        return rx.download(data=output.getvalue(), filename="REPORT_PUTAWAY_SYSTEM.xlsx")

    # --- COMPUTED METRICS ---
    @rx.var
    def filtered_list(self) -> list[dict]:
        res = self.data_list
        if self.filter_ekspedisi != "SEMUA": res = [x for x in res if x.get("ekspedisi") == self.filter_ekspedisi]
        return res

    @rx.var
    def list_ekspedisi_options(self) -> list[str]:
        eksp = list(set([x.get("ekspedisi", "") for x in self.data_list if x.get("ekspedisi")]))
        return ["SEMUA"] + sorted(eksp)

    @rx.var
    def total_biaya_all(self) -> str:
        return f"Rp {sum([x.get('total_ongkir', 0) for x in self.filtered_list]):,.0f}"

    @rx.var
    def total_koli_all(self) -> str:
        return f"{sum([x.get('total_koli', 0) for x in self.filtered_list]):,.0f} Koli"

    @rx.var
    def avg_cost_all(self) -> str:
        biaya = sum([x.get("total_ongkir", 0) for x in self.filtered_list])
        koli = sum([x.get("total_koli", 0) for x in self.filtered_list])
        return f"Rp {biaya / koli if koli > 0 else 0:,.0f}"

    @rx.var
    def biaya_datang(self) -> str:
        return f"Rp {sum([x.get('total_ongkir', 0) for x in self.filtered_list if 'RTO' not in str(x.get('supplier', ''))]):,.0f}"

    @rx.var
    def koli_datang(self) -> str:
        return f"{sum([x.get('total_koli', 0) for x in self.filtered_list if 'RTO' not in str(x.get('supplier', ''))]):,.0f} Koli"

    @rx.var
    def biaya_rto(self) -> str:
        return f"Rp {sum([x.get('total_ongkir', 0) for x in self.filtered_list if 'RTO' in str(x.get('supplier', ''))]):,.0f}"

    @rx.var
    def koli_rto(self) -> str:
        return f"{sum([x.get('total_koli', 0) for x in self.filtered_list if 'RTO' in str(x.get('supplier', ''))]):,.0f} Koli"

    @rx.var
    def active_content_type(self) -> str:
        if self.main_menu == "Database Ongkir In/Out":
            return "dashboard_ongkir" if self.role == "DC" else "access_denied"
        elif self.main_menu == "Stock Minus":
            return "stock_minus"
        else:
            return "under_development"

    @rx.var
    def menu_operational(self) -> list[str]:
        if self.role == "DC": return ["Purchase Order Receiving", "Putaway System", "Scan Out Validation", "Refill & Overstock", "Refill & Withdraw", "Compare RTO", "Compare Penerimaan RTO", "FDR Update"]
        else: return ["Compare Penerimaan RTO", "Putaway System", "Purchase Order Receiving"]

    @rx.var
    def menu_inventory(self) -> list[str]:
        if self.role == "DC": return ["Stock Opname", "Match Real & System", "Compare System", "Cycle Count", "Putaway & Picking Audit List", "List Bin Cycle Count", "Stock Tracking Timeline", "Justification SO", "Stock Minus", "List Retur Out", "Pengajuan Mutasi Karantina", "Refill Koli to Koli/Refill", "Stock Allocation"]
        else: return ["Stock Minus", "Cycle Count", "Compare System", "Justification SO"]

    @rx.var
    def menu_reject(self) -> list[str]: return ["Pengajuan Reject/Defect", "Reject/Defect List"]

    @rx.var
    def menu_extras(self) -> list[str]:
        if self.role == "DC": return ["Logistic Schedule", "Balancing Stock", "Reporting & PIC", "Data Timbang Ongkir", "Database Ongkir In/Out", "Precentage Display", "Precentage Request FL to Store Stock", "Refill Toko"]
        else: return ["Precentage Display", "Refill Toko", "Store Leader RTO Decission"]