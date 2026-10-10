import io
import json
import pandas as pd

# ==============================================================================
# Konfigurasi Supabase
# ==============================================================================
SUPABASE_URL = "https://fanzsmghhbefhhaicrok.supabase.co"

# Gunakan JWT Anon Key resmi
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZhbnpzbWdoaGJlZmhoYWljcm9rIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODgxNTQzNDgsImV4cCI6MjEwMzczMDM0OH0.brCSOO9nHAUK8CxDWPperpJ--_NA_nwy5cO9OqGv3I0"

# Deteksi apakah kode berjalan di browser (Shinylive / Pyodide)
IS_PYODIDE = False
try:
    import pyodide.http
    IS_PYODIDE = True
except ImportError:
    import urllib.request
    import urllib.error
    IS_PYODIDE = False


class SimpleSupabaseTable:
    def __init__(self, base_url, key, table_name):
        self.url = f"{base_url}/rest/v1/{table_name}"
        self.headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        self.params = []
        self.method = "GET"
        self.body = None

    def select(self, columns="*"):
        self.params.append(f"select={columns}")
        return self

    def insert(self, payload):
        self.method = "POST"
        self.body = payload if isinstance(payload, list) else [payload]
        return self

    def delete(self):
        self.method = "DELETE"
        return self

    def in_(self, column, values):
        val_str = ",".join(map(str, values))
        self.params.append(f"{column}=in.({val_str})")
        return self

    def execute(self):
        full_url = self.url
        if self.params:
            full_url += "?" + "&".join(self.params)

        body_str = json.dumps(self.body) if self.body else None

        # ----------------------------------------------------------------------
        # Jalur 1: Jika berjalan di Shinylive / Hugging Face Static (Browser WASM)
        # ----------------------------------------------------------------------
        if IS_PYODIDE:
            try:
                import pyodide.http
                # Menggunakan synchronous open_url yang didukung Web Worker Pyodide
                data_bytes = body_str.encode("utf-8") if body_str else None
                
                # Gunakan urllib open_url bawaan Pyodide yang sudah dipatch
                import urllib.request
                req = urllib.request.Request(full_url, data=data_bytes, headers=self.headers, method=self.method)
                with urllib.request.urlopen(req) as resp:
                    res_text = resp.read().decode("utf-8")
                    res_json = json.loads(res_text) if res_text else []
                    return type("Response", (), {"data": res_json})()
            except Exception as e:
                print(f"❌ [Shinylive Error] Gagal eksekusi ke Supabase: {e}")
                raise Exception(f"Gagal koneksi ke database di browser: {str(e)}")

        # ----------------------------------------------------------------------
        # Jalur 2: Jika berjalan di Python biasa (Local Laptop / Server)
        # ----------------------------------------------------------------------
        else:
            import urllib.request
            import urllib.error

            data_bytes = body_str.encode("utf-8") if body_str else None
            req = urllib.request.Request(full_url, data=data_bytes, headers=self.headers, method=self.method)

            try:
                with urllib.request.urlopen(req) as resp:
                    res_data = resp.read().decode("utf-8")
                    return type("Response", (), {"data": json.loads(res_data) if res_data else []})()
            except urllib.error.HTTPError as e:
                err_msg = e.read().decode("utf-8") if e.fp else ""
                print(f"❌ Supabase REST HTTPError [{e.code}]: {err_msg}")
                raise Exception(f"Ditolak Supabase [{e.code}]: {err_msg}")
            except Exception as e:
                print(f"❌ Supabase REST error: {e}")
                raise e


class SimpleSupabaseClient:
    def __init__(self, url, key):
        self.url = url
        self.key = key

    def table(self, table_name):
        return SimpleSupabaseTable(self.url, self.key, table_name)


def get_supabase():
    return SimpleSupabaseClient(SUPABASE_URL, SUPABASE_KEY)


def safe_int(val, default=0) -> int:
    try:
        if pd.isna(val) or val is None:
            return default
        cleaned = str(val).replace("Rp", "").replace(".", "").replace(",", "").strip()
        return int(float(cleaned))
    except Exception:
        return default


def load_data_from_info(file_info) -> pd.DataFrame:
    if not file_info or len(file_info) == 0:
        return pd.DataFrame()
    path = file_info[0]["datapath"]
    name = str(file_info[0]["name"]).lower()
    try:
        if name.endswith('.csv'):
            df = pd.read_csv(path)
            return df if not df.empty else pd.DataFrame()
        else:
            return pd.read_excel(path, engine="openpyxl")
    except Exception as e:
        print(f"Error loading {name}: {e}")
        return pd.DataFrame()


# ==============================================================================
# Helper Format Tanggal WIB
# ==============================================================================
def format_datetime_wib(df: pd.DataFrame, kolom: str, format_tampilan: str = "%d-%m-%Y %H:%M") -> pd.DataFrame:
    if df is not None and not df.empty and kolom in df.columns:
        try:
            converted = pd.to_datetime(df[kolom], errors="coerce")
            if converted.dt.tz is not None:
                converted = converted.dt.tz_convert("Asia/Jakarta")
            else:
                converted = converted.dt.tz_localize("UTC").dt.tz_convert("Asia/Jakarta")
            df[kolom] = converted.dt.strftime(format_tampilan)
        except Exception as e:
            print(f"Error saat memformat tanggal kolom '{kolom}': {e}")
    return df


# ==============================================================================
# GENERATOR RESMI PDF BINER %PDF-1.4 (ANTI-CORRUPT & MURNI TANPA ERROR)
# ==============================================================================
def generate_memo_pdf_bytes(memo_dict: dict) -> bytes:
    """Menghasilkan file biner PDF-1.4 asli dengan Kop JEZ, Tabel, & 3 Kotak TTD"""
    nom_val = safe_int(memo_dict.get('nominal', 0))
    items = memo_dict.get("items", [])
    memo_no = str(memo_dict.get('id', '-'))
    tgl_val = str(memo_dict.get('tanggal', '-'))
    div_val = str(memo_dict.get('divisi', '-'))
    jen_val = str(memo_dict.get('jenis', '-'))
    tuj_val = str(memo_dict.get('tujuan', '-'))
    pemohon = str(memo_dict.get('diajukan_oleh', 'Tim Pemohon'))
    logistik = str(memo_dict.get('diproses_oleh', 'Tim Logistik'))
    spv = str(memo_dict.get('diperiksa_oleh', 'SPV Warehouse'))
    st_log = str(memo_dict.get('status_logistik', 'Belum Diproses'))
    st_spv = str(memo_dict.get('status_spv', 'Belum Diperiksa'))

    def esc(text):
        if not text: return ""
        s = str(text).replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
        return s.encode('latin-1', 'replace').decode('latin-1')

    ops = []
    # 1. KOP SURAT (JEZ Merah & MEMO PENGAJUAN)
    ops.append("BT /F2 26 Tf 0.898 0.035 0.078 rg 40 790 Td (JEZ) Tj ET")
    ops.append("BT /F2 8.5 Tf 0 0 0 rg 40 776 Td (PT. ZONA KARYA NUSANTARA) Tj ET")
    ops.append("BT /F2 20 Tf 0.898 0.035 0.078 rg 370 788 Td (MEMO PENGAJUAN) Tj ET")
    ops.append("0.898 0.035 0.078 RG 1.5 w 370 782 m 555 782 l S")
    ops.append("0 0 0 RG 1.5 w 40 762 m 555 762 l S")

    # 2. DETAIL INFORMASI MEMO
    y = 742
    metadata = [
        ("Tanggal", tgl_val),
        ("Divisi", div_val),
        ("Jenis Pengajuan", jen_val),
        ("Tujuan", tuj_val),
        ("Nominal Pengajuan", f"Rp {nom_val:,}"),
        ("List Item Barang", "Terlampir pada tabel berikut :"),
    ]
    for lbl, val in metadata:
        ops.append(f"BT /F2 9.5 Tf 0 0 0 rg 40 {y} Td ({esc(lbl)}) Tj ET")
        ops.append(f"BT /F2 9.5 Tf 0 0 0 rg 140 {y} Td (:) Tj ET")
        f_val = "/F2" if "Nominal" in lbl else "/F1"
        ops.append(f"BT {f_val} 9.5 Tf 0 0 0 rg 150 {y} Td ({esc(val)}) Tj ET")
        y -= 15

    # 3. TABEL BARANG
    y -= 10
    tbl_top = y
    row_h = 18
    header_h = 20
    header_y = tbl_top - header_h

    # Header Background & Border
    ops.append(f"0.945 0.96 0.976 rg 40 {header_y} 515 {header_h} re f")
    ops.append(f"0 0 0 RG 0.75 w 40 {header_y} 515 {header_h} re S")

    cols = [
        ("NO", 40, 30),
        ("SKU", 70, 110),
        ("ITEM NAME", 180, 185),
        ("COGS (RP)", 365, 75),
        ("QTY", 440, 40),
        ("TOTAL (RP)", 480, 75)
    ]
    for name, cx, _ in cols:
        ops.append(f"0 0 0 RG 0.75 w {cx} {header_y} m {cx} {tbl_top} l S")
        ops.append(f"BT /F2 8.5 Tf 0 0 0 rg {cx + 4} {header_y + 6} Td ({esc(name)}) Tj ET")
    ops.append(f"0 0 0 RG 0.75 w 555 {header_y} m 555 {tbl_top} l S")

    # Baris Data Barang
    curr_y = header_y
    tot_qty = 0
    for idx, it in enumerate(items, start=1):
        curr_y -= row_h
        c_val = safe_int(it.get('cogs', 0))
        q_val = safe_int(it.get('qty', 0))
        sub_val = c_val * q_val
        tot_qty += q_val

        ops.append(f"0 0 0 RG 0.5 w 40 {curr_y} 515 {row_h} re S")
        for _, cx, _ in cols:
            ops.append(f"0 0 0 RG 0.5 w {cx} {curr_y} m {cx} {curr_y + row_h} l S")
        ops.append(f"0 0 0 RG 0.5 w 555 {curr_y} m 555 {curr_y + row_h} l S")

        ops.append(f"BT /F1 8 Tf 0 0 0 rg 50 {curr_y + 5} Td ({idx}) Tj ET")
        ops.append(f"BT /F2 8 Tf 0 0 0 rg 74 {curr_y + 5} Td ({esc(it.get('sku', '-'))}) Tj ET")
        name_txt = esc(it.get('item_name', '-'))
        if len(name_txt) > 35: name_txt = name_txt[:32] + "..."
        ops.append(f"BT /F1 8 Tf 0 0 0 rg 184 {curr_y + 5} Td ({name_txt}) Tj ET")
        ops.append(f"BT /F1 8 Tf 0 0 0 rg 370 {curr_y + 5} Td ({c_val:,}) Tj ET")
        ops.append(f"BT /F2 8 Tf 0 0 0 rg 450 {curr_y + 5} Td ({q_val}) Tj ET")
        ops.append(f"BT /F2 8 Tf 0 0 0 rg 485 {curr_y + 5} Td ({sub_val:,}) Tj ET")

    # Baris Total
    curr_y -= row_h
    ops.append(f"0.97 0.98 0.99 rg 40 {curr_y} 515 {row_h} re f")
    ops.append(f"0 0 0 RG 0.75 w 40 {curr_y} 515 {row_h} re S")
    ops.append(f"BT /F2 8.5 Tf 0 0 0 rg 180 {curr_y + 5} Td (TOTAL) Tj ET")
    ops.append(f"0 0 0 RG 0.5 w 440 {curr_y} m 440 {curr_y + row_h} l S")
    ops.append(f"BT /F2 8.5 Tf 0 0 0 rg 448 {curr_y + 5} Td ({tot_qty:,}) Tj ET")
    ops.append(f"0 0 0 RG 0.5 w 480 {curr_y} m 480 {curr_y + row_h} l S")
    ops.append(f"BT /F2 8.5 Tf 0.898 0.035 0.078 rg 485 {curr_y + 5} Td (Rp {nom_val:,}) Tj ET")

    # 4. KOTAK TANDA TANGAN (3 KOLOM PERSIS TEMPLATE)
    curr_y -= 30
    sign_w = 515 / 3
    sign_h = 75
    header_sign_h = 18
    sign_box_top = curr_y

    sign_headers = [("Diajukan oleh,", 40), ("Diproses oleh,", 40 + sign_w), ("Diperiksa oleh,", 40 + 2 * sign_w)]
    sign_bodies = [
        (f"({pemohon})", f"Tgl: {tgl_val}", 40),
        (f"({logistik})", f"Status: {st_log}", 40 + sign_w),
        (f"({spv})", f"Status: {st_spv}", 40 + 2 * sign_w)
    ]

    for idx, (sh, bx) in enumerate(sign_headers):
        ops.append(f"0.95 0.96 0.97 rg {bx} {sign_box_top - header_sign_h} {sign_w} {header_sign_h} re f")
        ops.append(f"0 0 0 RG 0.75 w {bx} {sign_box_top - header_sign_h} {sign_w} {header_sign_h} re S")
        ops.append(f"BT /F2 8.5 Tf 0 0 0 rg {bx + 40} {sign_box_top - 13} Td ({esc(sh)}) Tj ET")

        body_y = sign_box_top - sign_h
        ops.append(f"0 0 0 RG 0.75 w {bx} {body_y} {sign_w} {sign_h - header_sign_h} re S")
        nm, nt, _ = sign_bodies[idx]
        ops.append(f"BT /F2 8.5 Tf 0 0 0 rg {bx + 20} {body_y + 18} Td ({esc(nm)}) Tj ET")
        ops.append(f"BT /F1 7.5 Tf 0.3 0.3 0.3 rg {bx + 20} {body_y + 6} Td ({esc(nt)}) Tj ET")

    # 5. RAKIT BINARY PDF 1.4 RESMI
    content_stream = "\n".join(ops).encode('latin-1')
    stream_len = len(content_stream)

    objects = {
        1: b"<< /Type /Catalog /Pages 2 0 R >>",
        2: b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        3: b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595.28 841.89] /Contents 4 0 R /Resources << /Font << /F1 5 0 R /F2 6 0 R >> >> >>",
        4: f"<< /Length {stream_len} >>\nstream\n".encode('latin-1') + content_stream + b"\nendstream",
        5: b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
        6: b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>"
    }

    buf = bytearray()
    buf.extend(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = {}

    for obj_id in sorted(objects.keys()):
        offsets[obj_id] = len(buf)
        buf.extend(f"{obj_id} 0 obj\n".encode('latin-1'))
        buf.extend(objects[obj_id])
        buf.extend(b"\nendobj\n")

    xref_offset = len(buf)
    buf.extend(f"xref\n0 {len(objects) + 1}\n".encode('latin-1'))
    buf.extend(b"0000000000 65535 f \n")
    for obj_id in sorted(objects.keys()):
        buf.extend(f"{offsets[obj_id]:010d} 00000 n \n".encode('latin-1'))

    buf.extend(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode('latin-1'))
    return bytes(buf)