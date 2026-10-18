import io
import os
import json
import base64
from datetime import datetime
import pandas as pd

# ==============================================================================
# Konfigurasi Supabase
# ==============================================================================
SUPABASE_URL = "https://fanzsmghhbefhhaicrok.supabase.co"
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
        self.headers["Prefer"] = "return=representation"
        return self

    def update(self, payload):
        self.method = "PATCH"
        self.body = payload
        return self

    def order(self, column, desc=False):
        direction = "desc" if desc else "asc"
        self.params.append(f"order={column}.{direction}")
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

        if IS_PYODIDE:
            try:
                import pyodide.http
                data_bytes = body_str.encode("utf-8") if body_str else None
                import urllib.request
                req = urllib.request.Request(full_url, data=data_bytes, headers=self.headers, method=self.method)
                with urllib.request.urlopen(req) as resp:
                    res_text = resp.read().decode("utf-8")
                    res_json = json.loads(res_text) if res_text else []
                    return type("Response", (), {"data": res_json})()
            except Exception as e:
                print(f"❌ [Shinylive Error] Gagal eksekusi ke Supabase: {e}")
                raise Exception(f"Gagal koneksi ke database di browser: {str(e)}")
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
# GENERATOR MEMO PENGAJUAN (PDF BINER RINGAN)
# ==============================================================================
def generate_memo_pdf_bytes(memo_dict: dict) -> bytes:
    """Menghasilkan file biner PDF-1.4 asli dengan Kop JEZ, Tabel, & 3 Kotak TTD"""
    nom_val = safe_int(memo_dict.get('nominal', 0))
    items = memo_dict.get("items", [])
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
    ops.append("BT /F2 26 Tf 0.898 0.035 0.078 rg 40 790 Td (JEZ) Tj ET")
    ops.append("BT /F2 8.5 Tf 0 0 0 rg 40 776 Td (PT. ZONA KARYA NUSANTARA) Tj ET")
    ops.append("BT /F2 20 Tf 0.898 0.035 0.078 rg 370 788 Td (MEMO PENGAJUAN) Tj ET")
    ops.append("0.898 0.035 0.078 RG 1.5 w 370 782 m 555 782 l S")
    ops.append("0 0 0 RG 1.5 w 40 762 m 555 762 l S")

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

    y -= 10
    tbl_top = y
    row_h = 18
    header_h = 20
    header_y = tbl_top - header_h

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

    curr_y -= row_h
    ops.append(f"0.97 0.98 0.99 rg 40 {curr_y} 515 {row_h} re f")
    ops.append(f"0 0 0 RG 0.75 w 40 {curr_y} 515 {row_h} re S")
    ops.append(f"BT /F2 8.5 Tf 0 0 0 rg 180 {curr_y + 5} Td (TOTAL) Tj ET")
    ops.append(f"0 0 0 RG 0.5 w 440 {curr_y} m 440 {curr_y + row_h} l S")
    ops.append(f"BT /F2 8.5 Tf 0 0 0 rg 448 {curr_y + 5} Td ({tot_qty:,}) Tj ET")
    ops.append(f"0 0 0 RG 0.5 w 480 {curr_y} m 480 {curr_y + row_h} l S")
    ops.append(f"BT /F2 8.5 Tf 0.898 0.035 0.078 rg 485 {curr_y + 5} Td (Rp {nom_val:,}) Tj ET")

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


# ==============================================================================
# DEKODER TANDA TANGAN CANVAS (PURE PYTHON - TANPA PERLU DEPENDENSI EKSTERNAL)
# ==============================================================================
def process_signature_canvas(base64_str):
    """
    Mendekode canvas PNG transparan menjadi stream Flate/RGB murni untuk PDF.
    Mendeteksi coretan pena secara otomatis dan meratakannya ke latar putih.
    Returns: (compressed_bytes, width, height) jika ada coretan, atau None jika kosong.
    """
    if not base64_str or not isinstance(base64_str, str) or len(base64_str) < 100:
        return None
    try:
        import zlib
        import struct
        
        raw_b64 = base64_str.split("base64,")[1] if "base64," in base64_str else base64_str
        png_bytes = base64.b64decode(raw_b64)
        if len(png_bytes) < 30 or png_bytes[:8] != b'\x89PNG\r\n\x1a\n':
            return None

        # 1. Parse Chunk PNG
        idx = 8
        idat_list = []
        w, h = 0, 0
        color_type = 6

        while idx < len(png_bytes):
            if idx + 8 > len(png_bytes): break
            length = struct.unpack(">I", png_bytes[idx:idx+4])[0]
            ctype = png_bytes[idx+4:idx+8]
            data = png_bytes[idx+8:idx+8+length]
            idx += 12 + length

            if ctype == b'IHDR':
                w, h = struct.unpack(">II", data[:8])
                color_type = data[9]
            elif ctype == b'IDAT':
                idat_list.append(data)
            elif ctype == b'IEND':
                break

        if not idat_list or w == 0 or h == 0:
            return None

        # 2. Dekompresi IDAT
        raw_decomp = zlib.decompress(b"".join(idat_list))
        bpp = 4 if color_type == 6 else (3 if color_type == 2 else 1)
        stride = 1 + w * bpp
        if len(raw_decomp) < h * stride:
            return None

        # 3. Un-filtering PNG & Deteksi Coretan TTD
        out_rgb = bytearray(w * h * 3)
        prior_row = bytearray(w * bpp)
        has_ink = False

        def paeth_predict(a, b, c):
            p = a + b - c
            pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
            if pa <= pb and pa <= pc: return a
            elif pb <= pc: return b
            return c

        for y_i in range(h):
            offset = y_i * stride
            ftype = raw_decomp[offset]
            row_raw = raw_decomp[offset+1:offset+stride]
            curr_row = bytearray(w * bpp)

            if ftype == 0:
                curr_row[:] = row_raw
            elif ftype == 1:
                for x in range(len(row_raw)):
                    left = curr_row[x - bpp] if x >= bpp else 0
                    curr_row[x] = (row_raw[x] + left) & 0xFF
            elif ftype == 2:
                for x in range(len(row_raw)):
                    curr_row[x] = (row_raw[x] + prior_row[x]) & 0xFF
            elif ftype == 3:
                for x in range(len(row_raw)):
                    left = curr_row[x - bpp] if x >= bpp else 0
                    curr_row[x] = (row_raw[x] + (left + prior_row[x]) // 2) & 0xFF
            elif ftype == 4:
                for x in range(len(row_raw)):
                    left = curr_row[x - bpp] if x >= bpp else 0
                    up = prior_row[x]
                    up_left = prior_row[x - bpp] if x >= bpp else 0
                    curr_row[x] = (row_raw[x] + paeth_predict(left, up, up_left)) & 0xFF
            else:
                curr_row[:] = row_raw

            prior_row = curr_row
            row_out_off = y_i * w * 3

            for x_i in range(w):
                if color_type == 6:
                    r, g, b, a = curr_row[x_i*4], curr_row[x_i*4+1], curr_row[x_i*4+2], curr_row[x_i*4+3]
                elif color_type == 2:
                    r, g, b, a = curr_row[x_i*3], curr_row[x_i*3+1], curr_row[x_i*3+2], 255
                else:
                    v = curr_row[x_i]
                    r, g, b, a = v, v, v, 255

                # Jika ada piksel gelap / goresan pena
                if a > 30 and (r < 235 or g < 235 or b < 235):
                    has_ink = True

                alpha = a / 255.0
                out_rgb[row_out_off + x_i*3]     = int(r * alpha + 255 * (1.0 - alpha))
                out_rgb[row_out_off + x_i*3 + 1] = int(g * alpha + 255 * (1.0 - alpha))
                out_rgb[row_out_off + x_i*3 + 2] = int(b * alpha + 255 * (1.0 - alpha))

        if not has_ink:
            return None

        # Return data terkompresi FlateDecode untuk PDF
        return (zlib.compress(bytes(out_rgb)), w, h)

    except Exception as e:
        print("Signature decoder notice:", e)
        return None


# ==============================================================================
# GENERATOR RESMI AUDIT PACK (DENGAN TAMPILAN ASLI GAMBAR TTD)
# ==============================================================================
def generate_audit_pack_pdf_bytes(audit_data: dict) -> bytes:
    """
    Menghasilkan Dokumen PDF Portrait A4 Resmi ZKN:
    Kop Surat, Summary Box, Tabel Count Sheet (Selisih Saja), Findings, dan TTD Digital Asli.
    """
    
    # --------------------------------------------------------------------------
    # 1. PARSING ITEM SELISIH DENGAN NILAI VALUASI LENGKAP
    # --------------------------------------------------------------------------
    diff_items = []
    tot_diff_qty = 0
    tot_diff_val = 0

    for it in audit_data.get("items", []):
        p_raw = it.get("Physical Count", it.get("qty_physical", it.get("physical", "")))
        p_str = str(p_raw).strip() if p_raw is not None else ""
        if p_str == "" or p_str.lower() in ["none", "nan"]: 
            continue
        
        s_q = safe_int(it.get("Qty System", it.get("qty_system", it.get("system", 0))))
        p_q = safe_int(p_str)
        d_q = p_q - s_q

        cogs_val = safe_int(it.get("Harga Beli", it.get("cogs", it.get("COGS", it.get("price", it.get("harga", 0))))))
        var_raw = it.get("Variance Value", it.get("variance_value", it.get("Nilai Selisih", it.get("nilai_selisih", None))))
        if var_raw is not None and str(var_raw).strip() not in ["", "none", "nan"]:
            v_val = safe_int(var_raw)
        else:
            v_val = d_q * cogs_val

        if d_q != 0 or v_val != 0:
            diff_items.append({
                "sku": str(it.get("SKU", it.get("sku", "-"))),
                "desc": str(it.get("Description", it.get("item_name", it.get("description", "-")))),
                "sys": s_q,
                "phys": p_q,
                "diff": d_q,
                "val": v_val
            })
            tot_diff_qty += d_q
            tot_diff_val += v_val

    # Helper pencarian key TTD
    def get_sig_val(prefix):
        for k in [f"sign_{prefix}_img", f"sign_{prefix}", f"signature_{prefix}", f"ttd_{prefix}", f"{prefix}_signature", f"{prefix}_sign"]:
            val = audit_data.get(k)
            if val and isinstance(val, str) and len(val) > 100:
                return val
        return None

    sig_counter_data = get_sig_val("counter")
    sig_spv_data     = get_sig_val("supervisor")
    sig_mgr_data     = get_sig_val("manager")
    sig_lead_data    = get_sig_val("lead")

    # --------------------------------------------------------------------------
    # 2. REPORTLAB ENGINE (JIKA TERSEDIA DI ENVIRONMENT)
    # --------------------------------------------------------------------------
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, Image
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        
        def esc_pdf(text):
            if text is None: return ""
            return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=26, bottomMargin=26)
        styles = getSampleStyleSheet()

        COLOR_PRIMARY_RED = colors.HexColor('#C5161D')
        COLOR_NAVY_DARK   = colors.HexColor('#1A365D')
        COLOR_BOX_BG      = colors.HexColor('#EBF3F8')
        COLOR_BORDER      = colors.HexColor('#B8D0E0')
        COLOR_TEXT_MUTED  = colors.HexColor('#4A5568')

        h_left_title  = ParagraphStyle('HLTitle', fontName='Helvetica-Bold', fontSize=15, leading=17, textColor=COLOR_PRIMARY_RED)
        h_left_sub    = ParagraphStyle('HLSub', fontName='Helvetica-Bold', fontSize=7.5, leading=10, textColor=colors.HexColor('#2D3748'))
        h_right_title = ParagraphStyle('HRTitle', fontName='Helvetica-Bold', fontSize=11, leading=13, textColor=COLOR_NAVY_DARK, alignment=2)
        h_right_sub   = ParagraphStyle('HRSub', fontName='Helvetica', fontSize=7.5, leading=10, textColor=COLOR_TEXT_MUTED, alignment=2)
        
        meta_label = ParagraphStyle('MLabel', fontName='Helvetica-Bold', fontSize=7.5, leading=10, textColor=colors.black)
        meta_val   = ParagraphStyle('MVal', fontName='Helvetica', fontSize=7.5, leading=10, textColor=colors.black)
        
        section_h = ParagraphStyle('SecHead', fontName='Helvetica-Bold', fontSize=8.5, leading=11, textColor=colors.black, spaceBefore=4, spaceAfter=4)
        th_style  = ParagraphStyle('TH', fontName='Helvetica-Bold', fontSize=7, leading=8.5, textColor=colors.white, alignment=1)
        tb_style  = ParagraphStyle('TB', fontName='Helvetica', fontSize=7, leading=8.5, textColor=colors.HexColor('#1A202C'))
        tb_bold   = ParagraphStyle('TBBold', fontName='Helvetica-Bold', fontSize=7, leading=8.5, textColor=colors.HexColor('#1A202C'))
        tb_center = ParagraphStyle('TBCenter', fontName='Helvetica', fontSize=7, leading=8.5, textColor=colors.HexColor('#1A202C'), alignment=1)
        tb_red    = ParagraphStyle('TBRed', fontName='Helvetica-Bold', fontSize=7, leading=8.5, textColor=COLOR_PRIMARY_RED, alignment=1)
        tb_green  = ParagraphStyle('TBGreen', fontName='Helvetica-Bold', fontSize=7, leading=8.5, textColor=colors.HexColor('#2F855A'), alignment=1)
        tb_right_red = ParagraphStyle('TRed', fontName='Helvetica-Bold', fontSize=7, leading=8.5, textColor=COLOR_PRIMARY_RED, alignment=2)
        tb_right_green = ParagraphStyle('TGrn', fontName='Helvetica-Bold', fontSize=7, leading=8.5, textColor=colors.HexColor('#2F855A'), alignment=2)

        elements = []

        comp_str = str(audit_data.get('company', 'PT ZONA KARYA NUSANTARA')).upper()
        branch_str = str(audit_data.get('branch', 'SZ SURABAYA')).upper()
        audit_id = str(audit_data.get('id', 'AUD/SZ /20261011/178'))

        header_table_data = [
            [Paragraph("<b>ZKN WAREHOUSE AUDIT</b>", h_left_title), Paragraph("<b>AUDIT SIGN-OFF REPORT</b>", h_right_title)],
            [Paragraph(f"<b>{esc_pdf(comp_str)} - {esc_pdf(branch_str)}</b>", h_left_sub), Paragraph(f"No: {esc_pdf(audit_id)}", h_right_sub)]
        ]
        t_header = Table(header_table_data, colWidths=[315, 220])
        t_header.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('BOTTOMPADDING', (0,0), (-1,-1), 0), ('TOPPADDING', (0,0), (-1,-1), 0)]))
        elements.append(t_header)
        elements.append(Spacer(1, 4))

        red_bar = Table([[""]], colWidths=[535], rowHeights=[1.6])
        red_bar.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), COLOR_PRIMARY_RED), ('TOPPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 0)]))
        elements.append(red_bar)
        elements.append(Spacer(1, 6))

        count_date = str(audit_data.get('count_date', '11 OCTOBER 2026')).upper()
        count_method = str(audit_data.get('count_method', 'Full count (wall-to-wall)'))
        counter_name = str(audit_data.get('sign_counter_name') or audit_data.get('counter_name') or 'RAMITA').upper()
        time_range = f"{audit_data.get('start_time', '08:00')} - {audit_data.get('end_time', '17:00')}"
        lead_auditor = str(audit_data.get('sign_lead_name') or audit_data.get('lead_auditor') or 'EKO').upper()
        ops_manager = str(audit_data.get('sign_manager_name') or audit_data.get('manager') or 'ZAKKI').upper()
        supervisor = str(audit_data.get('sign_supervisor_name') or audit_data.get('supervisor') or 'BARA').upper()
        currency = str(audit_data.get('currency', 'IDR'))

        meta_data = [
            [Paragraph("Tanggal Pelaksanaan:", meta_label), Paragraph(count_date, meta_val), Paragraph("Lead Auditor:", meta_label), Paragraph(lead_auditor, meta_val)],
            [Paragraph("Metode Perhitungan:", meta_label), Paragraph(count_method, meta_val), Paragraph("Ops Manager:", meta_label), Paragraph(ops_manager, meta_val)],
            [Paragraph("Team Counter:", meta_label), Paragraph(counter_name, meta_val), Paragraph("Supervisor:", meta_label), Paragraph(supervisor, meta_val)],
            [Paragraph("Jam Pelaksanaan:", meta_label), Paragraph(time_range, meta_val), Paragraph("Mata Uang:", meta_label), Paragraph(currency, meta_val)],
        ]
        t_meta = Table(meta_data, colWidths=[105, 175, 85, 170])
        t_meta.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('TOPPADDING', (0,0), (-1,-1), 1.2), ('BOTTOMPADDING', (0,0), (-1,-1), 1.2)]))
        elements.append(t_meta)
        elements.append(Spacer(1, 8))

        tot_sku = safe_int(audit_data.get('total_sku', 0))
        tot_sys = safe_int(audit_data.get('total_qty_system', 0))
        tot_phys = safe_int(audit_data.get('total_qty_physical', 0))
        tot_var = safe_int(audit_data.get('total_variance_qty', 0))

        metric_data = [[
            Paragraph(f"<b>TOTAL SKU: {tot_sku:,}</b>", ParagraphStyle('M1', fontName='Helvetica-Bold', fontSize=7.5, textColor=COLOR_NAVY_DARK, alignment=1)),
            Paragraph(f"<b>QTY SYSTEM: {tot_sys:,}</b>", ParagraphStyle('M2', fontName='Helvetica-Bold', fontSize=7.5, textColor=colors.HexColor('#007A78'), alignment=1)),
            Paragraph(f"<b>PHYSICAL COUNT: {tot_phys:,}</b>", ParagraphStyle('M3', fontName='Helvetica-Bold', fontSize=7.5, textColor=colors.HexColor('#2B6CB0'), alignment=1)),
            Paragraph(f"<b>NET VARIANCE: {tot_var:+,}</b>", ParagraphStyle('M4', fontName='Helvetica-Bold', fontSize=7.5, textColor=COLOR_PRIMARY_RED, alignment=1)),
        ]]
        t_metric = Table(metric_data, colWidths=[130, 130, 135, 140])
        t_metric.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), COLOR_BOX_BG), ('BOX', (0,0), (-1,-1), 1, COLOR_BORDER),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('TOPPADDING', (0,0), (-1,-1), 5), ('BOTTOMPADDING', (0,0), (-1,-1), 5)
        ]))
        elements.append(t_metric)
        elements.append(Spacer(1, 9))

        elements.append(Paragraph("<b>DAFTAR ITEM SELISIH (VARIANCE COUNT SHEET)</b>", section_h))
        col_w_diff = [20, 95, 175, 45, 45, 55, 100]
        t_diff_data = [[Paragraph(h, th_style) for h in ["NO", "SKU", "DESCRIPTION", "SYS", "PHYS", "DIFF", "NILAI SELISIH"]]]

        for idx_d, d_row in enumerate(diff_items, start=1):
            d_color = tb_green if d_row["diff"] > 0 else tb_red
            d_val_style = tb_right_green if d_row["val"] > 0 else tb_right_red
            diff_str = f"{d_row['diff']:+d}"
            val_str = (f"+Rp {d_row['val']:,}" if d_row['val'] > 0 else f"-Rp {abs(d_row['val']):,}") if d_row['val'] != 0 else "Rp 0"
            t_diff_data.append([
                Paragraph(str(idx_d), tb_center), Paragraph(esc_pdf(d_row["sku"]), tb_bold),
                Paragraph(esc_pdf(d_row["desc"][:40]), tb_style), Paragraph(str(d_row["sys"]), tb_center),
                Paragraph(str(d_row["phys"]), tb_center), Paragraph(diff_str, d_color), Paragraph(val_str, d_val_style)
            ])

        tot_val_text = (f"+Rp {tot_diff_val:,}" if tot_diff_val > 0 else f"-Rp {abs(tot_diff_val):,}") if tot_diff_val != 0 else "Rp 0"
        t_diff_data.append([
            Paragraph("<b>TOTAL</b>", tb_bold), Paragraph(f"<b>{len(diff_items)} SKU</b>", tb_bold), Paragraph("", tb_style),
            Paragraph("", tb_style), Paragraph("", tb_style),
            Paragraph(f"<b>{tot_diff_qty:+d}</b>", tb_red if tot_diff_qty < 0 else tb_green),
            Paragraph(f"<b>{tot_val_text}</b>", tb_right_red if tot_diff_val < 0 else tb_right_green)
        ])

        t_diff = Table(t_diff_data, colWidths=col_w_diff, repeatRows=1)
        t_diff.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), COLOR_NAVY_DARK), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('TOPPADDING', (0,0), (-1,-1), 2.5), ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
            ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#F7FAFC'))
        ]))
        elements.append(t_diff)
        elements.append(Spacer(1, 10))

        elements.append(Paragraph("<b>AUDITOR OBSERVATIONS & FINDINGS</b>", section_h))
        findings = audit_data.get("findings", [])
        f_cols = [20, 75, 185, 45, 145, 65]
        t_find_data = [[Paragraph(h, th_style) for h in ["NO", "AREA", "TEMUAN / CASE", "RISK", "REKOMENDASI", "STATUS"]]]

        if findings:
            for f_i, fd in enumerate(findings, start=1):
                risk_txt = str(fd.get("risk", "Low")).strip()
                r_col = tb_red if risk_txt.lower() == "high" else (tb_right_red if risk_txt.lower() == "medium" else tb_green)
                st_val = str(fd.get('status', 'Open')).strip()
                t_find_data.append([
                    Paragraph(str(f_i), tb_center), Paragraph(esc_pdf(fd.get("area", "-")), tb_style),
                    Paragraph(esc_pdf(fd.get("case", "-")), tb_style), Paragraph(f"<b>{esc_pdf(risk_txt)}</b>", r_col),
                    Paragraph(esc_pdf(fd.get("recom", "-")), tb_style), Paragraph(f"<b>{esc_pdf(st_val)}</b>", tb_green if st_val.lower() == 'closed' else tb_red)
                ])
        else:
            t_find_data.append([Paragraph("-", tb_center), Paragraph("-", tb_style), Paragraph("Tidak ada catatan temuan fisik khusus.", tb_style), Paragraph("-", tb_center), Paragraph("-", tb_style), Paragraph("-", tb_center)])

        t_find = Table(t_find_data, colWidths=f_cols, repeatRows=1)
        t_find.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), COLOR_NAVY_DARK), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('TOPPADDING', (0,0), (-1,-1), 2.5), ('BOTTOMPADDING', (0,0), (-1,-1), 2.5)
        ]))
        elements.append(t_find)
        elements.append(Spacer(1, 10))

        elements.append(Paragraph("<b>STOCK COUNT SIGN-OFF</b>", section_h))

        def make_sig_cell_rl(base64_data):
            if base64_data:
                try:
                    raw_b64 = base64_data.split("base64,")[1] if "base64," in base64_data else base64_data
                    img_bytes = base64.b64decode(raw_b64)
                    img = Image(io.BytesIO(img_bytes), width=105, height=36)
                    img.hAlign = 'CENTER'
                    return img
                except Exception:
                    pass
            return Paragraph("<i>[Signed via System]</i>", ParagraphStyle('SM', fontName='Helvetica-Oblique', fontSize=7, textColor=COLOR_TEXT_MUTED, alignment=1))

        col_w_sign = [133.75, 133.75, 133.75, 133.75]
        sign_table_data = [
            [Paragraph("<b>Counter</b>", tb_bold), Paragraph("<b>Supervisor</b>", tb_bold), Paragraph("<b>Manager Ops</b>", tb_bold), Paragraph("<b>Lead Auditor</b>", tb_bold)],
            [make_sig_cell_rl(sig_counter_data), make_sig_cell_rl(sig_spv_data), make_sig_cell_rl(sig_mgr_data), make_sig_cell_rl(sig_lead_data)],
            [Paragraph(f"<b>{esc_pdf(counter_name)}</b>", tb_bold), Paragraph(f"<b>{esc_pdf(supervisor)}</b>", tb_bold), Paragraph(f"<b>{esc_pdf(ops_manager)}</b>", tb_bold), Paragraph(f"<b>{esc_pdf(lead_auditor)}</b>", tb_bold)]
        ]

        t_sign = Table(sign_table_data, colWidths=col_w_sign)
        t_sign.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#718096')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('ALIGN', (0,0), (-1,0), 'LEFT'), ('ALIGN', (0,2), (-1,2), 'LEFT'), ('ALIGN', (0,1), (-1,1), 'CENTER'),
            ('TOPPADDING', (0,0), (-1,0), 3), ('BOTTOMPADDING', (0,0), (-1,0), 2),
            ('TOPPADDING', (0,1), (-1,1), 2), ('BOTTOMPADDING', (0,1), (-1,1), 2),
            ('TOPPADDING', (0,2), (-1,2), 2), ('BOTTOMPADDING', (0,2), (-1,2), 3),
        ]))
        elements.append(KeepTogether([t_sign]))

        doc.build(elements)
        buf.seek(0)
        res_bytes = buf.getvalue()
        if len(res_bytes) > 200:
            return res_bytes

    except Exception:
        pass

    # --------------------------------------------------------------------------
    # HELPER: WRAP TEXT UNTUK PDF NATIVE (MENCEGAH POTONGAN TEKS)
    # --------------------------------------------------------------------------
    def wrap_text(text, max_chars=30):
        if not text: return [""]
        words = str(text).split(' ')
        lines = []
        current_line = ""
        for word in words:
            if current_line == "":
                current_line = word
            elif len(current_line) + 1 + len(word) <= max_chars:
                current_line += " " + word
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        return lines if lines else [""]

    # --------------------------------------------------------------------------
    # 3. NATIVE BINARY PDF ENGINE (DENGAN AUTO-WRAP TEKS & MULTI-LINE)
    # --------------------------------------------------------------------------
    comp = str(audit_data.get('company', 'PT ZONA KARYA NUSANTARA')).upper()
    br = str(audit_data.get('branch', 'SZ SURABAYA')).upper()
    dt = str(audit_data.get('count_date', '11 OCTOBER 2026')).upper()
    audit_id_str = str(audit_data.get('id', 'AUD/SZ /20261011/178'))
    lead = str(audit_data.get('sign_lead_name') or audit_data.get('lead_auditor') or 'EKO').upper()
    mgr = str(audit_data.get('sign_manager_name') or audit_data.get('manager') or 'ZAKKI').upper()
    spv = str(audit_data.get('sign_supervisor_name') or audit_data.get('supervisor') or 'BARA').upper()
    ctr = str(audit_data.get('sign_counter_name') or audit_data.get('counter_name') or 'RAMITA').upper()

    tot_sku_n = safe_int(audit_data.get('total_sku', 0))
    tot_sys_n = safe_int(audit_data.get('total_qty_system', 0))
    tot_phys_n = safe_int(audit_data.get('total_qty_physical', 0))
    tot_var_n = safe_int(audit_data.get('total_variance_qty', 0))
    findings_list = audit_data.get('findings', [])

    def esc_native(text):
        if not text: return ""
        s = str(text).replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
        return s.encode('latin-1', 'replace').decode('latin-1')

    ops = []
    # Kop Surat
    ops.append("BT /F2 16 Tf 0.77 0.08 0.11 rg 40 805 Td (ZKN WAREHOUSE AUDIT) Tj ET")
    ops.append("BT /F2 11 Tf 0.1 0.2 0.35 rg 380 805 Td (AUDIT SIGN-OFF REPORT) Tj ET")
    ops.append(f"BT /F2 8 Tf 0.2 0.2 0.2 rg 40 792 Td ({esc_native(comp)} - {esc_native(br)}) Tj ET")
    ops.append(f"BT /F1 8 Tf 0.3 0.3 0.3 rg 380 792 Td (No: {esc_native(audit_id_str)}) Tj ET")
    ops.append("0.77 0.08 0.11 RG 1.5 w 40 782 m 555 782 l S")

    # Meta Data
    y = 765
    meta_pairs = [
        ("Tanggal Pelaksanaan", dt, "Lead Auditor", lead),
        ("Metode Perhitungan", "Full count (wall-to-wall)", "Ops Manager", mgr),
        ("Team Counter", ctr, "Supervisor", spv),
        ("Jam Pelaksanaan", "08:00 - 17:00", "Mata Uang", "IDR")
    ]
    for l1, v1, l2, v2 in meta_pairs:
        ops.append(f"BT /F2 8 Tf 0 0 0 rg 40 {y} Td ({esc_native(l1)}:) Tj ET")
        ops.append(f"BT /F1 8 Tf 0 0 0 rg 140 {y} Td ({esc_native(v1)}) Tj ET")
        ops.append(f"BT /F2 8 Tf 0 0 0 rg 330 {y} Td ({esc_native(l2)}:) Tj ET")
        ops.append(f"BT /F1 8 Tf 0 0 0 rg 410 {y} Td ({esc_native(v2)}) Tj ET")
        y -= 13

    # Kotak Ringkasan Metrik
    y -= 5
    ops.append(f"0.92 0.95 0.97 rg 40 {y-18} 515 22 re f")
    ops.append(f"0.72 0.81 0.88 RG 0.75 w 40 {y-18} 515 22 re S")
    ops.append(f"BT /F2 8 Tf 0.1 0.2 0.35 rg 48 {y-11} Td (TOTAL SKU: {tot_sku_n:,}) Tj ET")
    ops.append(f"BT /F2 8 Tf 0 0.47 0.47 rg 170 {y-11} Td (QTY SYSTEM: {tot_sys_n:,}) Tj ET")
    ops.append(f"BT /F2 8 Tf 0.17 0.42 0.69 rg 295 {y-11} Td (PHYSICAL COUNT: {tot_phys_n:,}) Tj ET")
    ops.append(f"BT /F2 8 Tf 0.77 0.08 0.11 rg 420 {y-11} Td (NET VARIANCE: {tot_var_n:+,}) Tj ET")
    y -= 25

    # Count Sheet (Detail Selisih & Nilai Rupiah)
    y -= 12
    ops.append(f"BT /F2 9 Tf 0 0 0 rg 40 {y} Td (DAFTAR ITEM SELISIH (VARIANCE COUNT SHEET)) Tj ET")
    y -= 18
    ops.append(f"0.1 0.2 0.35 rg 40 {y} 515 15 re f")
    ops.append(f"BT /F2 7.5 Tf 1 1 1 rg 45 {y+4} Td (NO) Tj ET")
    ops.append(f"BT /F2 7.5 Tf 1 1 1 rg 70 {y+4} Td (SKU) Tj ET")
    ops.append(f"BT /F2 7.5 Tf 1 1 1 rg 170 {y+4} Td (DESCRIPTION) Tj ET")
    ops.append(f"BT /F2 7.5 Tf 1 1 1 rg 330 {y+4} Td (SYS) Tj ET")
    ops.append(f"BT /F2 7.5 Tf 1 1 1 rg 365 {y+4} Td (PHYS) Tj ET")
    ops.append(f"BT /F2 7.5 Tf 1 1 1 rg 400 {y+4} Td (DIFF) Tj ET")
    ops.append(f"BT /F2 7.5 Tf 1 1 1 rg 455 {y+4} Td (NILAI SELISIH) Tj ET")

    if not diff_items:
        y -= 15
        ops.append(f"0.98 0.98 0.98 rg 40 {y} 515 15 re f")
        ops.append(f"BT /F1 7.5 Tf 0.3 0.3 0.3 rg 45 {y+4} Td (Tidak ada selisih stok / 100% Cocok.) Tj ET")
    else:
        for idx_dn, itm in enumerate(diff_items, start=1):
            desc_lines = wrap_text(itm['desc'], 26)
            num_l = len(desc_lines)
            r_h = max(15, num_l * 10)
            y -= r_h

            ops.append(f"0.85 0.85 0.85 RG 0.5 w 40 {y} 515 {r_h} re S")
            ops.append(f"BT /F1 7.5 Tf 0 0 0 rg 45 {y + r_h - 10} Td ({idx_dn}) Tj ET")
            ops.append(f"BT /F2 7.5 Tf 0 0 0 rg 70 {y + r_h - 10} Td ({esc_native(itm['sku'][:16])}) Tj ET")
            
            line_y = y + r_h - 10
            for l_txt in desc_lines:
                ops.append(f"BT /F1 7.5 Tf 0 0 0 rg 170 {line_y} Td ({esc_native(l_txt)}) Tj ET")
                line_y -= 9

            ops.append(f"BT /F1 7.5 Tf 0 0 0 rg 335 {y + r_h - 10} Td ({itm['sys']}) Tj ET")
            ops.append(f"BT /F1 7.5 Tf 0 0 0 rg 370 {y + r_h - 10} Td ({itm['phys']}) Tj ET")
            
            d_col = "0 0.5 0.2" if itm['diff'] > 0 else "0.8 0.1 0.1"
            ops.append(f"BT /F2 7.5 Tf {d_col} rg 405 {y + r_h - 10} Td ({itm['diff']:+d}) Tj ET")
            v_str = (f"+Rp {itm['val']:,}" if itm['val'] > 0 else f"-Rp {abs(itm['val']):,}") if itm['val'] != 0 else "Rp 0"
            ops.append(f"BT /F2 7.5 Tf {d_col} rg 455 {y + r_h - 10} Td ({v_str}) Tj ET")

        y -= 15
        ops.append(f"0.94 0.95 0.96 rg 40 {y} 515 15 re f")
        ops.append(f"0.7 0.7 0.7 RG 0.5 w 40 {y} 515 15 re S")
        ops.append(f"BT /F2 7.5 Tf 0 0 0 rg 70 {y+4} Td (TOTAL) Tj ET")
        ops.append(f"BT /F2 7.5 Tf 0 0 0 rg 170 {y+4} Td ({len(diff_items)} SKU) Tj ET")
        tot_d_col = "0 0.5 0.2" if tot_diff_qty >= 0 else "0.8 0.1 0.1"
        ops.append(f"BT /F2 7.5 Tf {tot_d_col} rg 405 {y+4} Td ({tot_diff_qty:+d}) Tj ET")
        tot_val_s = (f"+Rp {tot_diff_val:,}" if tot_diff_val > 0 else f"-Rp {abs(tot_diff_val):,}") if tot_diff_val != 0 else "Rp 0"
        ops.append(f"BT /F2 7.5 Tf {tot_d_col} rg 455 {y+4} Td ({tot_val_s}) Tj ET")

    # Temuan Auditor (Observations & Findings dengan Auto-Wrap)
    y -= 25
    ops.append(f"BT /F2 9 Tf 0 0 0 rg 40 {y} Td (AUDITOR OBSERVATIONS & FINDINGS) Tj ET")
    y -= 18
    ops.append(f"0.1 0.2 0.35 rg 40 {y} 515 15 re f")
    ops.append(f"BT /F2 7.5 Tf 1 1 1 rg 45 {y+4} Td (NO) Tj ET")
    ops.append(f"BT /F2 7.5 Tf 1 1 1 rg 70 {y+4} Td (AREA) Tj ET")
    ops.append(f"BT /F2 7.5 Tf 1 1 1 rg 150 {y+4} Td (TEMUAN / CASE) Tj ET")
    ops.append(f"BT /F2 7.5 Tf 1 1 1 rg 340 {y+4} Td (RISK) Tj ET")
    ops.append(f"BT /F2 7.5 Tf 1 1 1 rg 400 {y+4} Td (REKOMENDASI) Tj ET")
    ops.append(f"BT /F2 7.5 Tf 1 1 1 rg 505 {y+4} Td (STATUS) Tj ET")

    if findings_list:
        for f_idx, fd in enumerate(findings_list, start=1):
            area_lines = wrap_text(str(fd.get('area', '-')), 12)
            case_lines = wrap_text(str(fd.get('case', '-')), 28)
            recom_lines = wrap_text(str(fd.get('recom', '-')), 20)
            num_l = max(len(area_lines), len(case_lines), len(recom_lines), 1)
            r_h = max(15, num_l * 10)
            y -= r_h

            ops.append(f"0.85 0.85 0.85 RG 0.5 w 40 {y} 515 {r_h} re S")
            ops.append(f"BT /F1 7.5 Tf 0 0 0 rg 45 {y + r_h - 10} Td ({f_idx}) Tj ET")

            line_y = y + r_h - 10
            for l_txt in area_lines:
                ops.append(f"BT /F1 7.5 Tf 0 0 0 rg 70 {line_y} Td ({esc_native(l_txt)}) Tj ET")
                line_y -= 9

            line_y = y + r_h - 10
            for l_txt in case_lines:
                ops.append(f"BT /F1 7.5 Tf 0 0 0 rg 150 {line_y} Td ({esc_native(l_txt)}) Tj ET")
                line_y -= 9

            risk_txt = str(fd.get('risk', 'Low'))
            ops.append(f"BT /F2 7.5 Tf 0.8 0.1 0.1 rg 340 {y + r_h - 10} Td ({esc_native(risk_txt)}) Tj ET")

            line_y = y + r_h - 10
            for l_txt in recom_lines:
                ops.append(f"BT /F1 7.5 Tf 0 0 0 rg 400 {line_y} Td ({esc_native(l_txt)}) Tj ET")
                line_y -= 9

            st_val = str(fd.get('status', 'Closed'))
            st_col = "0.1 0.5 0.2" if st_val.lower() == 'closed' else "0.8 0.1 0.1"
            ops.append(f"BT /F2 7.5 Tf {st_col} rg 505 {y + r_h - 10} Td ({esc_native(st_val)}) Tj ET")
    else:
        y -= 15
        ops.append(f"0.85 0.85 0.85 RG 0.5 w 40 {y} 515 15 re S")
        ops.append(f"BT /F1 7.5 Tf 0.3 0.3 0.3 rg 45 {y+4} Td (Tidak ada catatan temuan fisik khusus.) Tj ET")

    # --------------------------------------------------------------------------
    # KOTAK SIGN-OFF DENGAN DUKUNGAN RENDERING GAMBAR TTD ASLI
    # --------------------------------------------------------------------------
    y -= 25
    ops.append(f"BT /F2 9 Tf 0 0 0 rg 40 {y} Td (STOCK COUNT SIGN-OFF) Tj ET")
    y -= 62
    sign_w = 515 / 4
    sign_boxes = [
        ("Counter", ctr, sig_counter_data),
        ("Supervisor", spv, sig_spv_data),
        ("Manager Ops", mgr, sig_mgr_data),
        ("Lead Auditor", lead, sig_lead_data)
    ]

    native_img_objects = {}
    xobj_entries = []

    for s_i, (s_title, s_name, s_b64) in enumerate(sign_boxes, start=1):
        bx = 40 + (s_i - 1) * sign_w
        ops.append(f"0.5 0.5 0.5 RG 0.5 w {bx} {y} {sign_w} 56 re S")
        ops.append(f"BT /F2 8 Tf 0 0 0 rg {bx+8} {y+45} Td ({esc_native(s_title)}) Tj ET")
        ops.append(f"BT /F2 8 Tf 0 0 0 rg {bx+8} {y+7} Td ({esc_native(s_name)}) Tj ET")

        sig_parsed = process_signature_canvas(s_b64)
        if sig_parsed:
            comp_flate, iw, ih = sig_parsed
            obj_id = 6 + len(native_img_objects) + 1
            native_img_objects[obj_id] = (comp_flate, iw, ih)
            img_ref = f"/Sig{s_i}"
            xobj_entries.append(f"{img_ref} {obj_id} 0 R")

            img_w = sign_w - 20
            img_h = 28
            img_x = bx + 10
            img_y = y + 16
            ops.append(f"q {img_w} 0 0 {img_h} {img_x} {img_y} cm {img_ref} Do Q")
        else:
            ops.append(f"BT /F1 7.5 Tf 0.45 0.45 0.45 rg {bx+10} {y+25} Td ([Signed via System]) Tj ET")

    # Gabungkan Stream & XObject
    content_stream = "\n".join(ops).encode('latin-1')
    stream_len = len(content_stream)

    xobj_str = " ".join(xobj_entries)
    resources_xobj = f"/XObject << {xobj_str} >>" if xobj_entries else ""

    objects = {
        1: b"<< /Type /Catalog /Pages 2 0 R >>",
        2: b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        3: f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595.28 841.89] /Contents 4 0 R /Resources << /Font << /F1 5 0 R /F2 6 0 R >> {resources_xobj} >> >>".encode('latin-1'),
        4: f"<< /Length {stream_len} >>\nstream\n".encode('latin-1') + content_stream + b"\nendstream",
        5: b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
        6: b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>"
    }

    for o_id, (comp_bytes, iw, ih) in native_img_objects.items():
        header_img = f"<< /Type /XObject /Subtype /Image /Width {iw} /Height {ih} /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /FlateDecode /Length {len(comp_bytes)} >>\nstream\n".encode('latin-1')
        objects[o_id] = header_img + comp_bytes + b"\nendstream"

    buf_native = bytearray()
    buf_native.extend(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = {}
    for obj_id in sorted(objects.keys()):
        offsets[obj_id] = len(buf_native)
        buf_native.extend(f"{obj_id} 0 obj\n".encode('latin-1'))
        buf_native.extend(objects[obj_id])
        buf_native.extend(b"\nendobj\n")

    xref_offset = len(buf_native)
    buf_native.extend(f"xref\n0 {len(objects) + 1}\n".encode('latin-1'))
    buf_native.extend(b"0000000000 65535 f \n")
    for obj_id in sorted(objects.keys()):
        buf_native.extend(f"{offsets[obj_id]:010d} 00000 n \n".encode('latin-1'))

    buf_native.extend(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode('latin-1'))
    return bytes(buf_native)

    # ==============================================================================
# [BARU] GENERATOR MODEL 2: MEMO KAS ADJUSTMENT (PERSIS SEPERTI GAMBAR)
# ==============================================================================
def generate_memo_kas_pdf_bytes(memo_dict: dict) -> bytes:
    import io
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    buffer = io.BytesIO()
    # Format Landscape (Mendatar) sesuai gambar acuan
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=36,
        rightMargin=36,
        topMargin=25,
        bottomMargin=25
    )
    elements = []

    styles = getSampleStyleSheet()
    style_normal = ParagraphStyle('KasNormal', parent=styles['Normal'], fontSize=9, leading=11, fontName='Helvetica')
    style_bold = ParagraphStyle('KasBold', parent=styles['Normal'], fontSize=9, leading=11, fontName='Helvetica-Bold')

    # 1. HEADER (Kiri: JEZ Merah, Kanan: MEMO KAS ADJUSTMENT Merah)
    header_data = [
        [
            Paragraph("<font size=24 color='#D32F2F'><b><i>JEZ</i></b></font><br/><font size=8 color='#000000'><b>PT. ZONA KARYA NUSANTARA</b></font>", style_normal),
            Paragraph("<font size=15 color='#D32F2F'><b>MEMO KAS ADJUSTMENT</b></font><br/><font size=8 color='#000000'>PT ZONA KARYA NUSANTARA</font>", ParagraphStyle('HRight', parent=style_normal, alignment=2))
        ]
    ]
    t_header = Table(header_data, colWidths=[380, 390])
    t_header.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LINEBELOW', (0, 0), (-1, -1), 1.5, colors.black),
    ]))
    elements.append(t_header)
    elements.append(Spacer(1, 10))

    # Helper Tanggal Indonesia
    raw_tgl = memo_dict.get("tanggal", "")
    try:
        dt = pd.to_datetime(raw_tgl)
        bln = ["", "Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
        tgl_str = f"{dt.day} {bln[dt.month]} {dt.year}"
    except Exception:
        tgl_str = str(raw_tgl)

    nama_pengaju = str(memo_dict.get("diajukan_oleh", "Markom")).strip()
    divisi_txt = str(memo_dict.get("divisi", "Markom SBY")).strip()
    ket_adj = str(memo_dict.get("tujuan", memo_dict.get("jenis", "-"))).strip().upper()

    # 2. METADATA DETAIL (No. Adjustment dikosongkan)
    meta_rows = [
        [Paragraph("Tanggal", style_normal), Paragraph(f": {tgl_str}", style_normal)],
        [Paragraph("Nama Pengaju", style_normal), Paragraph(f": {nama_pengaju}", style_normal)],
        [Paragraph("Divisi", style_normal), Paragraph(f": : {divisi_txt}", style_normal)],
        [Paragraph("Keterangan Adjustment", style_normal), Paragraph(f": {ket_adj}", style_normal)],
        [Paragraph("No. Adjustment", style_normal), Paragraph(": ", style_normal)], # Dikosongkan sesuai poin 9
        [Paragraph("Detail Adjustment", style_normal), Paragraph(":", style_normal)]
    ]
    t_meta = Table(meta_rows, colWidths=[150, 620])
    t_meta.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(t_meta)
    elements.append(Spacer(1, 6))

    # 3. TABEL 4 KOLOM: BIN | SKU | ITEM NAME | HARGA BELI
    items = memo_dict.get("items", [])
    table_content = [
        [
            Paragraph("<b>BIN</b>", ParagraphStyle('TH', parent=style_bold, alignment=1)),
            Paragraph("<b>SKU</b>", ParagraphStyle('TH', parent=style_bold, alignment=1)),
            Paragraph("<b>ITEM NAME</b>", ParagraphStyle('TH', parent=style_bold, alignment=1)),
            Paragraph("<b>HARGA BELI</b>", ParagraphStyle('TH', parent=style_bold, alignment=1))
        ]
    ]

    total_beli = 0
    for it in items:
        bin_val = str(it.get("bin", "-")).strip()
        sku_val = str(it.get("sku", "-")).strip()
        item_val = str(it.get("item_name", "-")).strip()
        cogs_val = safe_int(it.get("cogs", 0), 0)
        total_beli += cogs_val

        table_content.append([
            Paragraph(bin_val, ParagraphStyle('TC', parent=style_normal, alignment=1)),
            Paragraph(sku_val, ParagraphStyle('TC', parent=style_normal, alignment=1)),
            Paragraph(item_val, style_normal),
            Paragraph(f"Rp.{cogs_val:,}", ParagraphStyle('TR', parent=style_normal, alignment=2))
        ])

    while len(table_content) < 4:
        table_content.append(["", "", "", ""])

    # Baris Total
    table_content.append(["Total", "", "", f"Rp.{total_beli:,}"])

    t_detail = Table(table_content, colWidths=[130, 160, 330, 150])
    t_detail.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -2), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('SPAN', (0, -1), (2, -1)),
        ('ALIGN', (0, -1), (2, -1), 'RIGHT'),
        ('ALIGN', (3, -1), (3, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 9),
        ('GRID', (0, -1), (-1, -1), 1, colors.black),
    ]))
    elements.append(t_detail)
    elements.append(Spacer(1, 15))

    # 4. KOTAK TANDA TANGAN (Diajukan oleh | Diproses oleh | Diperiksa oleh)
    sign_data = [
        [
            Paragraph("<b>Diajukan oleh,</b>", style_bold),
            Paragraph("<b>Diproses oleh,</b>", style_bold),
            Paragraph("<b>Diperiksa oleh,</b>", style_bold)
        ],
        ["\n\n\n", "\n\n\n", "\n\n\n"],
        [
            Paragraph(nama_pengaju, style_normal),
            Paragraph("Tim Purchasing", style_normal),
            Paragraph("Tim Finance", style_normal)
        ]
    ]
    t_sign = Table(sign_data, colWidths=[256, 257, 257])
    t_sign.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(t_sign)

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()