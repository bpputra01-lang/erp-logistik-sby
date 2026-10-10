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
# GENERATOR PDF & DOKUMEN CETAK RESMI MEMO PENGAJUAN JEZ
# ==============================================================================
def generate_memo_pdf_bytes(memo_dict: dict) -> bytes:
    """Menghasilkan file PDF Memo Pengajuan resmi tanpa risiko crash 1-byte"""
    import io
    
    # Ambil data aman dengan safe_int
    nom_val = safe_int(memo_dict.get('nominal', 0))
    items = memo_dict.get("items", [])
    tgl_val = str(memo_dict.get('tanggal', '-'))
    div_val = str(memo_dict.get('divisi', '-'))
    jen_val = str(memo_dict.get('jenis', '-'))
    tuj_val = str(memo_dict.get('tujuan', '-'))
    pemohon = str(memo_dict.get('diajukan_oleh', 'Tim Pemohon'))
    logistik = str(memo_dict.get('diproses_oleh', 'Tim Logistik'))
    spv = str(memo_dict.get('diperiksa_oleh', 'SPV Warehouse'))
    st_log = str(memo_dict.get('status_logistik', 'Pending'))
    st_spv = str(memo_dict.get('status_spv', 'Pending'))

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=30, bottomMargin=30)
        story = []

        title_jez = ParagraphStyle('JezTitle', fontName='Helvetica-Bold', fontSize=22, leading=24, textColor=colors.HexColor('#E50914'))
        title_memo = ParagraphStyle('MemoHeader', fontName='Helvetica-Bold', fontSize=18, leading=20, alignment=2, textColor=colors.HexColor('#E50914'))
        normal_bold = ParagraphStyle('NormalBold', fontName='Helvetica-Bold', fontSize=9, leading=13)
        normal_text = ParagraphStyle('NormalText', fontName='Helvetica', fontSize=9, leading=13)
        center_bold = ParagraphStyle('CenterBold', fontName='Helvetica-Bold', fontSize=9, leading=12, alignment=1)
        center_text = ParagraphStyle('CenterText', fontName='Helvetica', fontSize=9, leading=12, alignment=1)

        # 1. KOP SURAT
        kop_table = Table([
            [Paragraph("<b>JEZ</b><br/><font size=7>PT. ZONA KARYA NUSANTARA</font>", title_jez),
             Paragraph("<u>MEMO PENGAJUAN</u>", title_memo)]
        ], colWidths=[280, 240])
        kop_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
        story.append(kop_table)
        story.append(Spacer(1, 4))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.black, spaceAfter=10))

        # 2. DETAIL INFORMASI MEMO
        info_data = [
            [Paragraph("Tanggal", normal_bold), Paragraph(":", normal_bold), Paragraph(tgl_val, normal_text)],
            [Paragraph("Divisi", normal_bold), Paragraph(":", normal_bold), Paragraph(div_val, normal_text)],
            [Paragraph("Jenis Pengajuan", normal_bold), Paragraph(":", normal_bold), Paragraph(jen_val, normal_text)],
            [Paragraph("Tujuan", normal_bold), Paragraph(":", normal_bold), Paragraph(tuj_val, normal_text)],
            [Paragraph("Nominal Pengajuan", normal_bold), Paragraph(":", normal_bold), Paragraph(f"Rp {nom_val:,}", normal_bold)],
            [Paragraph("List Item Barang", normal_bold), Paragraph(":", normal_bold), Paragraph("Terlampir pada tabel berikut :", normal_text)]
        ]
        info_tbl = Table(info_data, colWidths=[120, 15, 385])
        info_tbl.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('BOTTOMPADDING', (0,0), (-1,-1), 2)]))
        story.append(info_tbl)
        story.append(Spacer(1, 8))

        # 3. TABEL BARANG
        table_rows = [[
            Paragraph("<b>NO</b>", center_bold),
            Paragraph("<b>SKU</b>", center_bold),
            Paragraph("<b>ITEM NAME</b>", center_bold),
            Paragraph("<b>COGS (RP)</b>", center_bold),
            Paragraph("<b>QTY</b>", center_bold),
            Paragraph("<b>TOTAL (RP)</b>", center_bold)
        ]]

        tot_qty = 0
        for idx, it in enumerate(items, start=1):
            c_val = safe_int(it.get('cogs', 0))
            q_val = safe_int(it.get('qty', 0))
            sub_val = c_val * q_val
            tot_qty += q_val
            table_rows.append([
                Paragraph(str(idx), center_text),
                Paragraph(str(it.get('sku', '-')), center_text),
                Paragraph(str(it.get('item_name', '-')), normal_text),
                Paragraph(f"{c_val:,}", center_text),
                Paragraph(str(q_val), center_text),
                Paragraph(f"{sub_val:,}", center_text)
            ])

        table_rows.append([
            Paragraph("<b>TOTAL</b>", center_bold),
            Paragraph("", center_bold), Paragraph("", center_bold), Paragraph("", center_bold),
            Paragraph(f"<b>{tot_qty:,}</b>", center_bold),
            Paragraph(f"<b>Rp {nom_val:,}</b>", center_bold)
        ])

        items_table = Table(table_rows, colWidths=[28, 92, 190, 70, 45, 95])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
            ('GRID', (0, 0), (-1, -1), 0.8, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('SPAN', (0, -1), (3, -1)),
            ('ALIGN', (0, -1), (3, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(items_table)
        story.append(Spacer(1, 20))

        # 4. KOTAK TANDA TANGAN
        sign_data = [
            [Paragraph("<b>Diajukan oleh,</b>", center_bold),
             Paragraph("<b>Diproses oleh,</b>", center_bold),
             Paragraph("<b>Diperiksa oleh,</b>", center_bold)],
            [Paragraph(f"<br/><br/><br/><b>({pemohon})</b><br/><font size=7 color='#666'>Tgl: {tgl_val}</font>", center_text),
             Paragraph(f"<br/><br/><br/><b>({logistik})</b><br/><font size=7 color='#666'>Status: {st_log}</font>", center_text),
             Paragraph(f"<br/><br/><br/><b>({spv})</b><br/><font size=7 color='#666'>Status: {st_spv}</font>", center_text)]
        ]
        sign_tbl = Table(sign_data, colWidths=[173, 173, 174])
        sign_tbl.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 1), (-1, 1), 8),
        ]))
        story.append(sign_tbl)

        doc.build(story)
        buf.seek(0)
        res_bytes = buf.getvalue()
        if len(res_bytes) > 100:
            return res_bytes
    except Exception as e:
        print(f"Reportlab failed: {e}")

    # FALLBACK ENGINE HTML RESMI: Menjamin file tidak pernah kosong / 1 byte
    html_content = generate_memo_html_document(memo_dict)
    return html_content.encode("utf-8")


def generate_memo_html_document(memo_dict: dict) -> str:
    """Template Dokumen Resmi Memo JEZ Siap Cetak A4 / Save PDF dari Browser"""
    nom_val = safe_int(memo_dict.get('nominal', 0))
    items = memo_dict.get("items", [])
    
    rows_html = ""
    tot_qty = 0
    for idx, it in enumerate(items, start=1):
        c_val = safe_int(it.get('cogs', 0))
        q_val = safe_int(it.get('qty', 0))
        sub_val = c_val * q_val
        tot_qty += q_val
        rows_html += f"""
        <tr>
            <td style="text-align: center;">{idx}</td>
            <td style="text-align: center; font-weight: bold;">{it.get('sku', '-')}</td>
            <td>{it.get('item_name', '-')}</td>
            <td style="text-align: center;">Rp {c_val:,}</td>
            <td style="text-align: center; font-weight: bold;">{q_val}</td>
            <td style="text-align: center; font-weight: bold;">Rp {sub_val:,}</td>
        </tr>
        """

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>MEMO_{memo_dict.get('id', 'PENGAJUAN').replace('/', '_')}</title>
    <style>
        @page {{ size: A4; margin: 15mm; }}
        body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #000; margin: 0; padding: 20px; }}
        .kop {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #000; padding-bottom: 8px; margin-bottom: 15px; }}
        .kop-jez {{ color: #E50914; font-size: 32px; font-weight: 900; line-height: 1; }}
        .kop-sub {{ font-size: 11px; font-weight: bold; color: #000; letter-spacing: 0.5px; }}
        .kop-memo {{ color: #E50914; font-size: 24px; font-weight: bold; text-decoration: underline; text-align: right; }}
        .meta-table {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; font-size: 13px; }}
        .meta-table td {{ padding: 3px 0; vertical-align: top; }}
        .meta-table td.label {{ width: 150px; font-weight: bold; }}
        .meta-table td.colon {{ width: 20px; font-weight: bold; }}
        .items-table {{ width: 100%; border-collapse: collapse; margin-bottom: 25px; font-size: 12px; }}
        .items-table th, .items-table td {{ border: 1px solid #000; padding: 6px 8px; }}
        .items-table th {{ background-color: #F1F5F9; font-weight: bold; text-align: center; }}
        .sign-table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
        .sign-table td {{ border: 1px solid #000; width: 33.33%; text-align: center; vertical-align: top; padding: 8px; }}
        .sign-box {{ height: 75px; display: flex; align-items: flex-end; justify-content: center; font-weight: bold; }}
        @media print {{
            .no-print {{ display: none; }}
            body {{ padding: 0; }}
        }}
    </style>
</head>
<body>
    <div class="no-print" style="margin-bottom: 15px; text-align: right;">
        <button onclick="window.print()" style="background: #10B981; color: white; border: none; padding: 8px 16px; border-radius: 6px; font-weight: bold; cursor: pointer;">🖨️ Cetak / Simpan PDF</button>
    </div>
    <div class="kop">
        <div>
            <div class="kop-jez">JEZ</div>
            <div class="kop-sub">PT. ZONA KARYA NUSANTARA</div>
        </div>
        <div class="kop-memo">MEMO PENGAJUAN</div>
    </div>
    <table class="meta-table">
        <tr><td class="label">Tanggal</td><td class="colon">:</td><td>{memo_dict.get('tanggal', '-')}</td></tr>
        <tr><td class="label">Divisi</td><td class="colon">:</td><td>{memo_dict.get('divisi', '-')}</td></tr>
        <tr><td class="label">Jenis Pengajuan</td><td class="colon">:</td><td>{memo_dict.get('jenis', '-')}</td></tr>
        <tr><td class="label">Tujuan</td><td class="colon">:</td><td>{memo_dict.get('tujuan', '-')}</td></tr>
        <tr><td class="label">Nominal Pengajuan</td><td class="colon">:</td><td><b>Rp {nom_val:,}</b></td></tr>
        <tr><td class="label">List Item Barang</td><td class="colon">:</td><td>Terlampir pada tabel berikut :</td></tr>
    </table>
    <table class="items-table">
        <thead>
            <tr>
                <th style="width: 30px;">NO</th>
                <th style="width: 120px;">SKU</th>
                <th>ITEM NAME</th>
                <th style="width: 100px;">COGS</th>
                <th style="width: 50px;">QTY</th>
                <th style="width: 110px;">TOTAL</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
            <tr style="background: #F8FAFC; font-weight: bold;">
                <td colspan="4" style="text-align: center;">TOTAL</td>
                <td style="text-align: center;">{tot_qty}</td>
                <td style="text-align: center; color: #E50914;">Rp {nom_val:,}</td>
            </tr>
        </tbody>
    </table>
    <table class="sign-table">
        <tr style="font-weight: bold; background: #F8FAFC;">
            <td>Diajukan oleh,</td>
            <td>Diproses oleh,</td>
            <td>Diperiksa oleh,</td>
        </tr>
        <tr>
            <td><div class="sign-box">({memo_dict.get('diajukan_oleh', 'Tim Pemohon')})</div><div style="font-size: 10px; color: #666; margin-top: 4px;">Tgl: {memo_dict.get('tanggal', '-')}</div></td>
            <td><div class="sign-box">({memo_dict.get('diproses_oleh', 'Tim Logistik')})</div><div style="font-size: 10px; color: #666; margin-top: 4px;">Status: {memo_dict.get('status_logistik', 'Pending')}</div></td>
            <td><div class="sign-box">({memo_dict.get('diperiksa_oleh', 'SPV Warehouse')})</div><div style="font-size: 10px; color: #666; margin-top: 4px;">Status: {memo_dict.get('status_spv', 'Pending')}</div></td>
        </tr>
    </table>
</body>
</html>"""