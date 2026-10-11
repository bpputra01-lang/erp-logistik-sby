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
def generate_audit_pack_pdf_bytes(audit_data: dict) -> bytes:
    """Menghasilkan PDF resmi External Audit Pack dengan proteksi anti-blank & anti-0 bytes"""
    try:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib import colors
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, Image
        )
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    except ImportError as e:
        print(f"⚠️ ReportLab error: {e}")
        return b""

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        rightMargin=30, leftMargin=30,
        topMargin=30, bottomMargin=30
    )

    styles = getSampleStyleSheet()
    
    # Kustomisasi Style agar aman dari error teks meluber
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=13,
        textColor=colors.HexColor('#1A365D'),
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        textColor=colors.HexColor('#4A5568'),
        spaceAfter=8
    )
    th_style = ParagraphStyle(
        'TableHeader',
        fontName='Helvetica-Bold',
        fontSize=7,
        textColor=colors.white,
        alignment=1
    )
    tb_style = ParagraphStyle(
        'TableCell',
        fontName='Helvetica',
        fontSize=7,
        textColor=colors.HexColor('#1A202C')
    )
    tb_bold = ParagraphStyle(
        'TableCellBold',
        fontName='Helvetica-Bold',
        fontSize=7,
        textColor=colors.HexColor('#1A202C')
    )
    tb_red = ParagraphStyle(
        'TableCellRed',
        fontName='Helvetica-Bold',
        fontSize=7,
        textColor=colors.HexColor('#E53E3E'),
        alignment=2
    )
    tb_green = ParagraphStyle(
        'TableCellGreen',
        fontName='Helvetica-Bold',
        fontSize=7,
        textColor=colors.HexColor('#22543D'),
        alignment=2
    )

    elements = []

    # 1. Judul Dokumen & Identitas
    elements.append(Paragraph(f"<b>STOCK OPNAME OFFICIAL AUDIT REPORT – {audit_data.get('id', 'AUDIT')}</b>", title_style))
    elements.append(Paragraph(
        f"Company: {audit_data.get('company', '-')} | Branch: {audit_data.get('branch', '-')} | "
        f"Count Date: {audit_data.get('count_date', '-')} ({audit_data.get('start_time', '08:00')} - {audit_data.get('end_time', '17:00')}) | "
        f"Method: {audit_data.get('count_method', 'Full Count')} | Standard: ISA 501 / PSAK 14",
        subtitle_style
    ))

    # 2. Ringkasan Metrik Utama
    tot_sku = safe_int(audit_data.get('total_sku', 0))
    tot_sys = safe_int(audit_data.get('total_qty_system', 0))
    tot_phys = safe_int(audit_data.get('total_qty_physical', 0))
    tot_var = safe_int(audit_data.get('total_variance_qty', 0))

    summary_data = [
        ["Total SKU Checked", "Total Qty System", "Total Physical Count", "Net Variance Qty", "Lead Auditor"],
        [
            f"{tot_sku:,} SKU",
            f"{tot_sys:,} PCS",
            f"{tot_phys:,} PCS",
            f"{tot_var:,} PCS",
            str(audit_data.get('lead_auditor', '-'))
        ]
    ]
    t_sum = Table(summary_data, colWidths=[155, 155, 155, 155, 215])
    t_sum.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1A365D')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E0')),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#F8FAFC')),
    ]))
    elements.append(t_sum)
    elements.append(Spacer(1, 10))

    # 3. TABEL ITEM SELISIH (VARIANCE DISCREPANCIES)
    elements.append(Paragraph("<b>DAFTAR ITEM SELISIH FISIK VS SISTEM (VARIANCE DISCREPANCIES):</b>", styles['Heading4']))

    diff_items = []
    total_qty_diff = 0
    total_val_diff = 0

    for it in audit_data.get("items", []):
        phys_raw = str(it.get("Physical Count", it.get("qty_physical", ""))).strip()
        if phys_raw == "" or phys_raw.lower() in ["none", "nan"]:
            continue

        try:
            sys_q = int(float(it.get("Qty System", it.get("qty_system", 0))))
        except:
            sys_q = 0

        try:
            phys_q = int(float(phys_raw))
        except:
            phys_q = 0

        diff_q = phys_q - sys_q

        try:
            hb = int(float(it.get("Harga Beli", it.get("cogs", 0))))
        except:
            hb = 0

        var_val_raw = it.get("Variance Value", it.get("variance_value", ""))
        try:
            var_val = int(float(var_val_raw)) if str(var_val_raw).strip() not in ["", "-", "None", "nan"] else diff_q * hb
        except:
            var_val = diff_q * hb

        if diff_q != 0 or var_val != 0:
            diff_items.append({
                "bin": str(it.get("Bin Location", it.get("bin", "-"))),
                "sku": str(it.get("SKU", it.get("sku", "-"))),
                "desc": str(it.get("Description", it.get("item_name", "-"))),
                "uom": str(it.get("UoM (PAIR / PCS)", it.get("uom", "PCS"))),
                "sys": sys_q,
                "phys": phys_q,
                "diff": diff_q,
                "val": var_val,
                "remarks": str(it.get("Remarks", it.get("remarks", ""))) if str(it.get("Remarks", it.get("remarks", ""))).lower() not in ["none", "nan"] else ""
            })
            total_qty_diff += diff_q
            total_val_diff += var_val

    if diff_items:
        col_w_diff = [25, 80, 110, 200, 36, 50, 50, 50, 90, 144]
        t_diff_data = [[
            Paragraph("<b>No</b>", th_style),
            Paragraph("<b>Bin Location</b>", th_style),
            Paragraph("<b>SKU</b>", th_style),
            Paragraph("<b>Description</b>", th_style),
            Paragraph("<b>UoM</b>", th_style),
            Paragraph("<b>Qty Sys</b>", th_style),
            Paragraph("<b>Physical</b>", th_style),
            Paragraph("<b>Diff Qty</b>", th_style),
            Paragraph("<b>Nilai Selisih (Rp)</b>", th_style),
            Paragraph("<b>Catatan / Remarks</b>", th_style)
        ]]

        for d_i, d_row in enumerate(diff_items, start=1):
            diff_str = f"{d_row['diff']:+d}"
            diff_style = tb_green if d_row['diff'] > 0 else tb_red
            val_formatted = (f"+Rp {d_row['val']:,}" if d_row['val'] > 0 else f"-Rp {abs(d_row['val']):,}") if d_row['val'] != 0 else "Rp 0"

            t_diff_data.append([
                Paragraph(str(d_i), tb_style),
                Paragraph(d_row["bin"], tb_bold),
                Paragraph(d_row["sku"], tb_bold),
                Paragraph(d_row["desc"], tb_style),
                Paragraph(d_row["uom"], tb_style),
                Paragraph(str(d_row["sys"]), tb_style),
                Paragraph(str(d_row["phys"]), tb_style),
                Paragraph(diff_str, diff_style),
                Paragraph(val_formatted, diff_style),
                Paragraph(d_row["remarks"], tb_style)
            ])

        total_val_str = (f"+Rp {total_val_diff:,}" if total_val_diff > 0 else f"-Rp {abs(total_val_diff):,}") if total_val_diff != 0 else "Rp 0"
        t_diff_data.append([
            Paragraph("<b>TOTAL</b>", tb_bold),
            Paragraph("", tb_style),
            Paragraph(f"<b>{len(diff_items)} SKU Selisih</b>", tb_bold),
            Paragraph("", tb_style),
            Paragraph("", tb_style),
            Paragraph("", tb_style),
            Paragraph("", tb_style),
            Paragraph(f"<b>{total_qty_diff:+d}</b>", tb_bold),
            Paragraph(f"<b>{total_val_str}</b>", tb_bold),
            Paragraph("", tb_style)
        ])

        t_diff = Table(t_diff_data, colWidths=col_w_diff, repeatRows=1)
        t_diff.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#C53030')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E0')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (8, 0), (8, -1), 'RIGHT'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#EDF2F7')),
            ('SPAN', (0, -1), (1, -1)),
        ]))
        elements.append(t_diff)
    else:
        elements.append(Paragraph("<i>✅ Tidak ada perbedaan kuantitas (0 Selisih). Seluruh hasil hitung fisik cocok 100% dengan data sistem.</i>", subtitle_style))

    elements.append(Spacer(1, 10))

    # 4. OBSERVASI & TEMUAN AUDITOR
    findings = audit_data.get("findings", [])
    if findings:
        elements.append(Paragraph("<b>AUDITOR OBSERVATIONS & FINDINGS:</b>", styles['Heading4']))
        f_table_data = [[
            Paragraph("<b>No</b>", th_style),
            Paragraph("<b>Area</b>", th_style),
            Paragraph("<b>Temuan / Case</b>", th_style),
            Paragraph("<b>Risk</b>", th_style),
            Paragraph("<b>Rekomendasi Auditor</b>", th_style),
            Paragraph("<b>Status</b>", th_style)
        ]]
        for f_i, fd in enumerate(findings, start=1):
            risk_color = colors.HexColor('#E53E3E') if fd.get("risk") == "High" else colors.HexColor('#DD6B20')
            f_table_data.append([
                Paragraph(str(f_i), tb_style),
                Paragraph(str(fd.get("area", "-")), tb_style),
                Paragraph(str(fd.get("case", "-")), tb_style),
                Paragraph(f"<b>{fd.get('risk', '-')}</b>", ParagraphStyle('Rk', parent=tb_style, textColor=risk_color, alignment=1)),
                Paragraph(str(fd.get("recom", "-")), tb_style),
                Paragraph(f"<b>{fd.get('status', 'Open')}</b>", tb_style)
            ])
        t_find = Table(f_table_data, colWidths=[25, 120, 265, 55, 335, 95], repeatRows=1)
        t_find.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2D3748')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E0')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ]))
        elements.append(t_find)
        elements.append(Spacer(1, 10))

    # 5. TANDA TANGAN DIGITAL (AMAN DARI CRASH BASE64)
    elements.append(Paragraph("<b>STOCK COUNT SIGN-OFF (DIGITAL SIGNATURES):</b>", styles['Heading4']))

    def safe_img_flowable(data_url):
        try:
            if not data_url or not isinstance(data_url, str):
                return Paragraph("<i>(Belum TTD)</i>", tb_style)
            if "base64," in data_url:
                data_url = data_url.split("base64,")[1]
            img_bytes = base64.b64decode(data_url)
            if len(img_bytes) < 100:
                return Paragraph("<i>(Belum TTD)</i>", tb_style)
            return Image(io.BytesIO(img_bytes), width=110, height=35)
        except:
            return Paragraph("<i>(Belum TTD)</i>", tb_style)

    img_counter = safe_img_flowable(audit_data.get("sign_counter_img"))
    img_spv = safe_img_flowable(audit_data.get("sign_supervisor_img"))
    img_mgr = safe_img_flowable(audit_data.get("sign_manager_img"))
    img_lead = safe_img_flowable(audit_data.get("sign_lead_img"))

    ctr_name = str(audit_data.get('sign_counter_name') or audit_data.get('counter_name') or '-')
    spv_name = str(audit_data.get('sign_supervisor_name') or audit_data.get('supervisor') or '-')
    mgr_name = str(audit_data.get('sign_manager_name') or audit_data.get('manager') or '-')
    lead_name = str(audit_data.get('sign_lead_name') or audit_data.get('lead_auditor') or '-')

    sign_table_data = [
        [
            Paragraph("<b>Count Team (Counter)</b>", th_style),
            Paragraph("<b>Count Team Supervisor</b>", th_style),
            Paragraph("<b>Warehouse/Ops. Manager</b>", th_style),
            Paragraph("<b>Lead External Auditor</b>", th_style)
        ],
        [img_counter, img_spv, img_mgr, img_lead],
        [
            Paragraph(f"Nama: {ctr_name}", tb_style),
            Paragraph(f"Nama: {spv_name}", tb_style),
            Paragraph(f"Nama: {mgr_name}", tb_style),
            Paragraph(f"Nama: {lead_name}", tb_style)
        ]
    ]

    t_sign = Table(sign_table_data, colWidths=[223, 223, 223, 224])
    t_sign.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2D3748')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E0')),
        ('BOTTOMPADDING', (0, 1), (-1, 1), 4),
        ('TOPPADDING', (0, 1), (-1, 1), 4),
    ]))

    elements.append(KeepTogether([t_sign]))

    # Eksekusi Build Document ReportLab
    try:
        doc.build(elements)
        buf.seek(0)
        return buf.getvalue()
    except Exception as e:
        print(f"❌ Gagal Build PDF ReportLab: {e}")
        return b""