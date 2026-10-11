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
# HELPER PARSER TANDA TANGAN BASE64 KE REPORTLAB IMAGE
# ==============================================================================
def get_reportlab_image_from_base64(data_url, width=120, height=45):
    """Mengubah base64 canvas URL menjadi Image Flowable ReportLab"""
    try:
        from reportlab.platypus import Image
        if not data_url or not isinstance(data_url, str):
            return ""
        if "base64," in data_url:
            data_url = data_url.split("base64,")[1]
        img_bytes = base64.b64decode(data_url)
        if len(img_bytes) < 300:
            return ""
        buf = io.BytesIO(img_bytes)
        return Image(buf, width=width, height=height)
    except Exception as e:
        print("Error parsing signature image for PDF:", e)
        return ""


# ==============================================================================
# GENERATOR RESMI AUDIT PACK (LENGKAP: TABEL SELISIH + TTD DIGITAL CANVAS)
# ==============================================================================
# ==============================================================================
# GENERATOR RESMI AUDIT PACK (LAYOUT PORTRAIT SESUAI REFERENSI ZKN)
# ==============================================================================
def generate_audit_pack_pdf_bytes(audit_data: dict) -> bytes:
    """
    Menghasilkan PDF Stock Opname Resmi berorientasi Portrait A4
    sesuai format ZKN Warehouse Audit (Kop, Summary Box, Tabel Selisih, Findings, & TTD Digital).
    """
    
    # --------------------------------------------------------------------------
    # 1. ENGINE UTAMA: REPORTLAB (PORTRAIT A4)
    # --------------------------------------------------------------------------
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, Image, HRFlowable
        )
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        
        def esc_pdf(text):
            if text is None: return ""
            return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        buf = io.BytesIO()
        # A4 Portrait: lebar 595.28 pt, margin 30 pt kiri-kanan -> lebar efektif tabel = 535.28 pt
        doc = SimpleDocTemplate(
            buf, pagesize=A4,
            rightMargin=30, leftMargin=30, topMargin=28, bottomMargin=28
        )

        styles = getSampleStyleSheet()
        
        # Palet Warna Sesuai Referensi Gambar
        COLOR_PRIMARY_RED = colors.HexColor('#C5161D')    # Merah judul ZKN
        COLOR_NAVY_DARK   = colors.HexColor('#1A365D')    # Navy heading
        COLOR_BOX_BG      = colors.HexColor('#EBF3F8')    # Biru muda kotak metrik
        COLOR_BORDER      = colors.HexColor('#B8D0E0')    # Garis tepi metrik
        COLOR_TEXT_MUTED  = colors.HexColor('#4A5568')

        # Gaya Teks
        h_left_title = ParagraphStyle('HLeftTitle', fontName='Helvetica-Bold', fontSize=15, leading=17, textColor=COLOR_PRIMARY_RED)
        h_left_sub   = ParagraphStyle('HLeftSub', fontName='Helvetica-Bold', fontSize=7.5, leading=10, textColor=colors.HexColor('#2D3748'))
        h_right_title = ParagraphStyle('HRightTitle', fontName='Helvetica-Bold', fontSize=11, leading=13, textColor=COLOR_NAVY_DARK, alignment=2)
        h_right_sub   = ParagraphStyle('HRightSub', fontName='Helvetica', fontSize=7.5, leading=10, textColor=COLOR_TEXT_MUTED, alignment=2)
        
        meta_label = ParagraphStyle('MetaLabel', fontName='Helvetica-Bold', fontSize=7.5, leading=10, textColor=colors.black)
        meta_val   = ParagraphStyle('MetaVal', fontName='Helvetica', fontSize=7.5, leading=10, textColor=colors.black)
        
        section_h = ParagraphStyle('SecHead', fontName='Helvetica-Bold', fontSize=8.5, leading=11, textColor=colors.black, spaceBefore=4, spaceAfter=3)
        th_style  = ParagraphStyle('TH', fontName='Helvetica-Bold', fontSize=7, leading=8.5, textColor=colors.white, alignment=1)
        tb_style  = ParagraphStyle('TB', fontName='Helvetica', fontSize=7, leading=8.5, textColor=colors.HexColor('#1A202C'))
        tb_bold   = ParagraphStyle('TBBold', fontName='Helvetica-Bold', fontSize=7, leading=8.5, textColor=colors.HexColor('#1A202C'))
        tb_center = ParagraphStyle('TBCenter', fontName='Helvetica', fontSize=7, leading=8.5, textColor=colors.HexColor('#1A202C'), alignment=1)
        tb_red    = ParagraphStyle('TBRed', fontName='Helvetica-Bold', fontSize=7, leading=8.5, textColor=COLOR_PRIMARY_RED, alignment=1)
        tb_green  = ParagraphStyle('TBGreen', fontName='Helvetica-Bold', fontSize=7, leading=8.5, textColor=colors.HexColor('#2F855A'), alignment=1)

        elements = []

        # ----------------------------------------------------------------------
        # A. KOP SURAT (HEADER ATAS)
        # ----------------------------------------------------------------------
        comp_str = str(audit_data.get('company', 'PT ZONA KARYA NUSANTARA')).upper()
        branch_str = str(audit_data.get('branch', 'SZ SURABAYA')).upper()
        audit_id = str(audit_data.get('id', 'AUD/SZ /20261011/814'))

        header_table_data = [
            [
                Paragraph("<b>ZKN WAREHOUSE AUDIT</b>", h_left_title),
                Paragraph("<b>AUDIT SIGN-OFF REPORT</b>", h_right_title)
            ],
            [
                Paragraph(f"<b>{esc_pdf(comp_str)} - {esc_pdf(branch_str)}</b>", h_left_sub),
                Paragraph(f"No: {esc_pdf(audit_id)}", h_right_sub)
            ]
        ]
        t_header = Table(header_table_data, colWidths=[315, 220])
        t_header.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(t_header)
        elements.append(Spacer(1, 4))
        # Garis horizontal merah persis gambar referensi
        elements.append(HRFlowable(width="100%", thickness=1.8, color=COLOR_PRIMARY_RED, spaceAfter=6, spaceBefore=2))

        # ----------------------------------------------------------------------
        # B. TABEL META INFORMASI (2 KOLOM RAPI)
        # ----------------------------------------------------------------------
        count_date = str(audit_data.get('count_date', '11 OCTOBER 2026')).upper()
        count_method = str(audit_data.get('count_method', 'Full count (wall-to-wall)'))
        counter_name = str(audit_data.get('sign_counter_name') or audit_data.get('counter_name') or 'RAMITA').upper()
        time_range = f"{audit_data.get('start_time', '08:00')} - {audit_data.get('end_time', '17:00')}"
        lead_auditor = str(audit_data.get('sign_lead_name') or audit_data.get('lead_auditor') or 'EKO').upper()
        ops_manager = str(audit_data.get('sign_manager_name') or audit_data.get('manager') or 'ZAKKI').upper()
        supervisor = str(audit_data.get('sign_supervisor_name') or audit_data.get('supervisor') or 'BARA').upper()
        currency = str(audit_data.get('currency', 'IDR'))

        meta_data = [
            [Paragraph("Tanggal Pelaksanaan:", meta_label), Paragraph(count_date, meta_val),
             Paragraph("Lead Auditor:", meta_label), Paragraph(lead_auditor, meta_val)],
            [Paragraph("Metode Perhitungan:", meta_label), Paragraph(count_method, meta_val),
             Paragraph("Ops Manager:", meta_label), Paragraph(ops_manager, meta_val)],
            [Paragraph("Team Counter:", meta_label), Paragraph(counter_name, meta_val),
             Paragraph("Supervisor:", meta_label), Paragraph(supervisor, meta_val)],
            [Paragraph("Jam Pelaksanaan:", meta_label), Paragraph(time_range, meta_val),
             Paragraph("Mata Uang:", meta_label), Paragraph(currency, meta_val)],
        ]
        t_meta = Table(meta_data, colWidths=[105, 175, 85, 170])
        t_meta.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 1.2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1.2),
        ]))
        elements.append(t_meta)
        elements.append(Spacer(1, 7))

        # ----------------------------------------------------------------------
        # C. KOTAK METRIK UTAMA (BACKGROUND BIRU MUDA SESUAI GAMBAR)
        # ----------------------------------------------------------------------
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
            ('BACKGROUND', (0, 0), (-1, -1), COLOR_BOX_BG),
            ('BOX', (0, 0), (-1, -1), 1, COLOR_BORDER),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(t_metric)
        elements.append(Spacer(1, 9))

        # ----------------------------------------------------------------------
        # D. TABEL COUNT SHEET (HANYA ITEM YANG SELISIH FISIK VS SISTEM)
        # ----------------------------------------------------------------------
        elements.append(Paragraph("<b>DAFTAR ITEM SELISIH (VARIANCE COUNT SHEET)</b>", section_h))

        diff_items = []
        tot_diff_qty = 0
        tot_diff_val = 0

        for it in audit_data.get("items", []):
            phys_raw = str(it.get("Physical Count", it.get("qty_physical", ""))).strip()
            if phys_raw == "" or phys_raw.lower() in ["none", "nan"]: continue
            sys_q = safe_int(it.get("Qty System", it.get("qty_system", 0)))
            phys_q = safe_int(phys_raw)
            diff_q = phys_q - sys_q
            hb = safe_int(it.get("Harga Beli", it.get("cogs", 0)))
            var_val = safe_int(it.get("Variance Value", it.get("variance_value", diff_q * hb)))

            # Filter hanya item yang ada selisih
            if diff_q != 0 or var_val != 0:
                diff_items.append({
                    "sku": str(it.get("SKU", it.get("sku", "-"))),
                    "desc": str(it.get("Description", it.get("item_name", "-"))),
                    "sys": sys_q,
                    "phys": phys_q,
                    "diff": diff_q,
                    "val": var_val
                })
                tot_diff_qty += diff_q
                tot_diff_val += var_val

        if diff_items:
            # Lebar total = 20 + 95 + 170 + 55 + 55 + 60 + 80 = 535 pt
            col_w_diff = [20, 95, 170, 55, 55, 60, 80]
            t_diff_data = [[
                Paragraph("NO", th_style), Paragraph("SKU", th_style), Paragraph("DESCRIPTION", th_style),
                Paragraph("SYS", th_style), Paragraph("PHYS", th_style), Paragraph("DIFF", th_style), Paragraph("NILAI SELISIH", th_style)
            ]]

            for idx_d, d_row in enumerate(diff_items, start=1):
                d_color = tb_green if d_row["diff"] > 0 else tb_red
                diff_str = f"{d_row['diff']:+d}"
                val_str = (f"+Rp {d_row['val']:,}" if d_row['val'] > 0 else f"-Rp {abs(d_row['val']):,}") if d_row['val'] != 0 else "Rp 0"
                
                t_diff_data.append([
                    Paragraph(str(idx_d), tb_center),
                    Paragraph(esc_pdf(d_row["sku"]), tb_bold),
                    Paragraph(esc_pdf(d_row["desc"][:42]), tb_style),
                    Paragraph(str(d_row["sys"]), tb_center),
                    Paragraph(str(d_row["phys"]), tb_center),
                    Paragraph(diff_str, d_color),
                    Paragraph(val_str, d_color)
                ])

            tot_val_text = (f"+Rp {tot_diff_val:,}" if tot_diff_val > 0 else f"-Rp {abs(tot_diff_val):,}") if tot_diff_val != 0 else "Rp 0"
            t_diff_data.append([
                Paragraph("<b>TOTAL</b>", tb_bold),
                Paragraph(f"<b>{len(diff_items)} SKU</b>", tb_bold),
                Paragraph("", tb_style),
                Paragraph("", tb_style),
                Paragraph("", tb_style),
                Paragraph(f"<b>{tot_diff_qty:+d}</b>", tb_bold),
                Paragraph(f"<b>{tot_val_text}</b>", tb_bold)
            ])

            t_diff = Table(t_diff_data, colWidths=col_w_diff, repeatRows=1)
            t_diff.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), COLOR_NAVY_DARK),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E0')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 2.5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#F7FAFC')),
                ('ALIGN', (-1, 1), (-1, -1), 'RIGHT'),
            ]))
            elements.append(t_diff)
        else:
            elements.append(Paragraph("<i>✅ Tidak ada selisih kuantitas. Seluruh stok fisik 100% cocok dengan data sistem.</i>", meta_val))

        elements.append(Spacer(1, 9))

        # ----------------------------------------------------------------------
        # E. TABEL TEMUAN AUDITOR (AUDITOR OBSERVATIONS & FINDINGS)
        # ----------------------------------------------------------------------
        elements.append(Paragraph("<b>AUDITOR OBSERVATIONS & FINDINGS</b>", section_h))
        findings = audit_data.get("findings", [])
        
        # Lebar total: 20 + 75 + 185 + 45 + 145 + 65 = 535 pt
        f_cols = [20, 75, 185, 45, 145, 65]
        t_find_data = [[
            Paragraph("NO", th_style), Paragraph("AREA", th_style), Paragraph("TEMUAN / CASE", th_style),
            Paragraph("RISK", th_style), Paragraph("REKOMENDASI", th_style), Paragraph("STATUS", th_style)
        ]]

        if findings:
            for f_i, fd in enumerate(findings, start=1):
                risk_txt = str(fd.get("risk", "Low")).strip()
                r_col = tb_red if risk_txt.lower() == "high" else (tb_green if risk_txt.lower() == "low" else tb_center)
                t_find_data.append([
                    Paragraph(str(f_i), tb_center),
                    Paragraph(esc_pdf(fd.get("area", "-")), tb_style),
                    Paragraph(esc_pdf(fd.get("case", "-")), tb_style),
                    Paragraph(f"<b>{esc_pdf(risk_txt)}</b>", r_col),
                    Paragraph(esc_pdf(fd.get("recom", "-")), tb_style),
                    Paragraph(f"<b>{esc_pdf(fd.get('status', 'Open'))}</b>", tb_green if str(fd.get('status','')).lower() == 'open' else tb_style)
                ])
        else:
            t_find_data.append([
                Paragraph("-", tb_center), Paragraph("-", tb_style),
                Paragraph("Tidak ada catatan temuan fisik khusus.", tb_style),
                Paragraph("-", tb_center), Paragraph("-", tb_style), Paragraph("-", tb_center)
            ])

        t_find = Table(t_find_data, colWidths=f_cols, repeatRows=1)
        t_find.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), COLOR_NAVY_DARK),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E0')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 2.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ]))
        elements.append(t_find)
        elements.append(Spacer(1, 10))

        # ----------------------------------------------------------------------
        # F. STOCK COUNT SIGN-OFF (4 KOTAK DENGAN TTD DIGITAL GAMBAR ASLI)
        # ----------------------------------------------------------------------
        elements.append(Paragraph("<b>STOCK COUNT SIGN-OFF</b>", section_h))

        def make_signature_cell(data_url):
            """Mengekstrak gambar base64 canvas; jika kosong kembalikan teks [Signed via System]"""
            try:
                if data_url and isinstance(data_url, str) and len(data_url) > 200:
                    raw_b64 = data_url.split("base64,")[1] if "base64," in data_url else data_url
                    img_bytes = base64.b64decode(raw_b64)
                    if len(img_bytes) > 200:
                        return Image(io.BytesIO(img_bytes), width=105, height=35)
            except Exception as e:
                print("Gagal render gambar TTD:", e)
            return Paragraph("<i>[Signed via System]</i>", ParagraphStyle('SignedSys', fontName='Helvetica-Oblique', fontSize=7, textColor=COLOR_TEXT_MUTED, alignment=1))

        # Kolom TTD: 535 / 4 = 133.75 pt masing-masing
        col_w_sign = [133.75, 133.75, 133.75, 133.75]
        sign_table_data = [
            # Baris 1: Jabatan / Role
            [Paragraph("<b>Counter</b>", tb_bold), Paragraph("<b>Supervisor</b>", tb_bold),
             Paragraph("<b>Manager Ops</b>", tb_bold), Paragraph("<b>Lead Auditor</b>", tb_bold)],
            # Baris 2: Canvas TTD Digital
            [make_signature_cell(audit_data.get("sign_counter_img")),
             make_signature_cell(audit_data.get("sign_supervisor_img")),
             make_signature_cell(audit_data.get("sign_manager_img")),
             make_signature_cell(audit_data.get("sign_lead_img"))],
            # Baris 3: Nama Lengkap
            [Paragraph(f"<b>{esc_pdf(counter_name)}</b>", tb_bold),
             Paragraph(f"<b>{esc_pdf(supervisor)}</b>", tb_bold),
             Paragraph(f"<b>{esc_pdf(ops_manager)}</b>", tb_bold),
             Paragraph(f"<b>{esc_pdf(lead_auditor)}</b>", tb_bold)]
        ]

        t_sign = Table(sign_table_data, colWidths=col_w_sign)
        t_sign.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#718096')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 1), (-1, 1), 1),
            ('TOPPADDING', (0, 1), (-1, 1), 1),
        ]))
        elements.append(KeepTogether([t_sign]))

        # Render file PDF
        doc.build(elements)
        buf.seek(0)
        res_bytes = buf.getvalue()
        if len(res_bytes) > 200:
            return res_bytes

    except Exception as e:
        print(f"⚠️ ReportLab Error, beralih ke Native PDF Portrait Fallback: {e}")

    # --------------------------------------------------------------------------
    # 2. ENGINE CADANGAN: NATIVE PDF BINER (PORTRAIT A4 TAHAN BANTING)
    # --------------------------------------------------------------------------
    comp = str(audit_data.get('company', 'PT ZONA KARYA NUSANTARA')).upper()
    br = str(audit_data.get('branch', 'SZ SURABAYA')).upper()
    dt = str(audit_data.get('count_date', '11 OCTOBER 2026')).upper()
    audit_id_str = str(audit_data.get('id', 'AUD/SZ /20261011/814'))
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
    # KOP PORTRAIT A4 (Mulai dari Y = 800)
    ops.append("BT /F2 16 Tf 0.77 0.08 0.11 rg 40 805 Td (ZKN WAREHOUSE AUDIT) Tj ET")
    ops.append("BT /F2 11 Tf 0.1 0.2 0.35 rg 380 805 Td (AUDIT SIGN-OFF REPORT) Tj ET")
    ops.append(f"BT /F2 8 Tf 0.2 0.2 0.2 rg 40 792 Td ({esc_native(comp)} - {esc_native(br)}) Tj ET")
    ops.append(f"BT /F1 8 Tf 0.3 0.3 0.3 rg 380 792 Td (No: {esc_native(audit_id_str)}) Tj ET")
    ops.append("0.77 0.08 0.11 RG 1.5 w 40 782 m 555 782 l S")

    # Meta Data 2 Kolom
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

    # Kotak Ringkasan Metrik Biru Muda
    y -= 5
    ops.append(f"0.92 0.95 0.97 rg 40 {y-18} 515 22 re f")
    ops.append(f"0.72 0.81 0.88 RG 0.75 w 40 {y-18} 515 22 re S")
    ops.append(f"BT /F2 8 Tf 0.1 0.2 0.35 rg 48 {y-11} Td (TOTAL SKU: {tot_sku_n:,}) Tj ET")
    ops.append(f"BT /F2 8 Tf 0 0.47 0.47 rg 170 {y-11} Td (QTY SYSTEM: {tot_sys_n:,}) Tj ET")
    ops.append(f"BT /F2 8 Tf 0.17 0.42 0.69 rg 295 {y-11} Td (PHYSICAL COUNT: {tot_phys_n:,}) Tj ET")
    ops.append(f"BT /F2 8 Tf 0.77 0.08 0.11 rg 420 {y-11} Td (NET VARIANCE: {tot_var_n:+,}) Tj ET")

    # Temuan Auditor
    y -= 38
    ops.append(f"BT /F2 9 Tf 0 0 0 rg 40 {y} Td (AUDITOR OBSERVATIONS & FINDINGS) Tj ET")
    y -= 14
    ops.append(f"0.1 0.2 0.35 rg 40 {y} 515 15 re f")
    ops.append(f"BT /F2 7.5 Tf 1 1 1 rg 45 {y+4} Td (NO) Tj ET")
    ops.append(f"BT /F2 7.5 Tf 1 1 1 rg 70 {y+4} Td (AREA) Tj ET")
    ops.append(f"BT /F2 7.5 Tf 1 1 1 rg 150 {y+4} Td (TEMUAN / CASE) Tj ET")
    ops.append(f"BT /F2 7.5 Tf 1 1 1 rg 340 {y+4} Td (RISK) Tj ET")
    ops.append(f"BT /F2 7.5 Tf 1 1 1 rg 400 {y+4} Td (REKOMENDASI) Tj ET")
    ops.append(f"BT /F2 7.5 Tf 1 1 1 rg 505 {y+4} Td (STATUS) Tj ET")

    for f_idx, fd in enumerate(findings_list[:4], start=1):
        y -= 15
        ops.append(f"0.85 0.85 0.85 RG 0.5 w 40 {y} 515 15 re S")
        ops.append(f"BT /F1 7.5 Tf 0 0 0 rg 45 {y+4} Td ({f_idx}) Tj ET")
        ops.append(f"BT /F1 7.5 Tf 0 0 0 rg 70 {y+4} Td ({esc_native(str(fd.get('area','-'))[:12])}) Tj ET")
        ops.append(f"BT /F1 7.5 Tf 0 0 0 rg 150 {y+4} Td ({esc_native(str(fd.get('case','-'))[:32])}) Tj ET")
        ops.append(f"BT /F2 7.5 Tf 0.8 0.1 0.1 rg 340 {y+4} Td ({esc_native(str(fd.get('risk','Low')))}) Tj ET")
        ops.append(f"BT /F1 7.5 Tf 0 0 0 rg 400 {y+4} Td ({esc_native(str(fd.get('recom','-'))[:20])}) Tj ET")
        ops.append(f"BT /F2 7.5 Tf 0.1 0.5 0.2 rg 505 {y+4} Td ({esc_native(str(fd.get('status','Open')))}) Tj ET")

    # Kotak Sign-Off (4 Kotak TTD)
    y -= 25
    ops.append(f"BT /F2 9 Tf 0 0 0 rg 40 {y} Td (STOCK COUNT SIGN-OFF) Tj ET")
    y -= 58
    sign_w = 515 / 4
    sign_boxes = [("Counter", ctr), ("Supervisor", spv), ("Manager Ops", mgr), ("Lead Auditor", lead)]
    for s_i, (s_title, s_name) in enumerate(sign_boxes):
        bx = 40 + s_i * sign_w
        ops.append(f"0.5 0.5 0.5 RG 0.5 w {bx} {y} {sign_w} 52 re S")
        ops.append(f"BT /F2 8 Tf 0 0 0 rg {bx+8} {y+42} Td ({esc_native(s_title)}) Tj ET")
        ops.append(f"BT /F1 7.5 Tf 0.4 0.4 0.4 rg {bx+8} {y+24} Td ([Signed via System]) Tj ET")
        ops.append(f"BT /F2 8 Tf 0 0 0 rg {bx+8} {y+7} Td ({esc_native(s_name)}) Tj ET")

    content_stream = "\n".join(ops).encode('latin-1')
    stream_len = len(content_stream)

    # Portrait A4: MediaBox [0 0 595.28 841.89]
    objects = {
        1: b"<< /Type /Catalog /Pages 2 0 R >>",
        2: b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        3: b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595.28 841.89] /Contents 4 0 R /Resources << /Font << /F1 5 0 R /F2 6 0 R >> >> >>",
        4: f"<< /Length {stream_len} >>\nstream\n".encode('latin-1') + content_stream + b"\nendstream",
        5: b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
        6: b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>"
    }

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