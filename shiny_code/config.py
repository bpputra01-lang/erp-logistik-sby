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
# GENERATOR PDF MEMO PENGAJUAN (SESUAI FORMAT GAMBAR JEZ)
# ==============================================================================
def generate_memo_pdf_bytes(memo_dict: dict) -> bytes:
    """Menghasilkan file PDF Memo Pengajuan resmi dengan Kop Surat JEZ & 3 Kolom TTD"""
    import io
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    buf = io.BytesIO()
    # Menggunakan orientasi landscape atau portrait A4 (portrait pas untuk format memo)
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=30,
        bottomMargin=30
    )

    story = []
    styles = getSampleStyleSheet()

    # Style Kustom
    title_jez = ParagraphStyle(
        'JezTitle',
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=26,
        textColor=colors.HexColor('#E50914')
    )
    sub_jez = ParagraphStyle(
        'JezSub',
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.black
    )
    title_memo = ParagraphStyle(
        'MemoHeader',
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=22,
        alignment=2,  # Rata Kanan
        textColor=colors.HexColor('#E50914')
    )
    normal_bold = ParagraphStyle(
        'NormalBold',
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14
    )
    normal_text = ParagraphStyle(
        'NormalText',
        fontName='Helvetica',
        fontSize=10,
        leading=14
    )
    center_bold = ParagraphStyle(
        'CenterBold',
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        alignment=1
    )
    center_text = ParagraphStyle(
        'CenterText',
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        alignment=1
    )

    # 1. KOP SURAT (JEZ di Kiri, MEMO PENGAJUAN di Kanan)
    kop_data = [
        [
            Paragraph("<b>JEZ</b><br/><font size=8>PT. ZONA KARYA NUSANTARA</font>", title_jez),
            Paragraph("<u>MEMO PENGAJUAN</u>", title_memo)
        ]
    ]
    kop_table = Table(kop_data, colWidths=[280, 240])
    kop_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(kop_table)
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.black, spaceAfter=12))

    # 2. DETAIL INFORMASI MEMO
    nominal_str = f"Rp {memo_dict.get('nominal', 0):,}"
    info_data = [
        [Paragraph("Tanggal", normal_bold), Paragraph(":", normal_bold), Paragraph(str(memo_dict.get('tanggal', '-')), normal_text)],
        [Paragraph("Divisi", normal_bold), Paragraph(":", normal_bold), Paragraph(str(memo_dict.get('divisi', '-')), normal_text)],
        [Paragraph("Jenis Pengajuan", normal_bold), Paragraph(":", normal_bold), Paragraph(str(memo_dict.get('jenis', '-')), normal_text)],
        [Paragraph("Tujuan", normal_bold), Paragraph(":", normal_bold), Paragraph(str(memo_dict.get('tujuan', '-')), normal_text)],
        [Paragraph("Nominal Pengajuan", normal_bold), Paragraph(":", normal_bold), Paragraph(nominal_str, normal_bold)],
        [Paragraph("List Item Barang", normal_bold), Paragraph(":", normal_bold), Paragraph("Terlampir pada tabel di bawah ini :", normal_text)]
    ]
    info_table = Table(info_data, colWidths=[130, 15, 375])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 10))

    # 3. TABEL DAFTAR BARANG
    items = memo_dict.get("items", [])
    table_rows = [
        [
            Paragraph("<b>NO</b>", center_bold),
            Paragraph("<b>SKU</b>", center_bold),
            Paragraph("<b>ITEM NAME</b>", center_bold),
            Paragraph("<b>COGS (RP)</b>", center_bold),
            Paragraph("<b>QTY</b>", center_bold),
            Paragraph("<b>TOTAL (RP)</b>", center_bold)
        ]
    ]

    for idx, it in enumerate(items, start=1):
        cogs = safe_int(it.get('cogs', 0))
        qty = safe_int(it.get('qty', 0))
        subtot = cogs * qty
        table_rows.append([
            Paragraph(str(idx), center_text),
            Paragraph(str(it.get('sku', '-')), center_text),
            Paragraph(str(it.get('item_name', '-')), normal_text),
            Paragraph(f"{cogs:,}", center_text),
            Paragraph(str(qty), center_text),
            Paragraph(f"{subtot:,}", center_text)
        ])

    # Baris Total
    table_rows.append([
        Paragraph("<b>TOTAL</b>", center_bold),
        Paragraph("", center_bold),
        Paragraph("", center_bold),
        Paragraph("", center_bold),
        Paragraph(f"<b>{sum([safe_int(x.get('qty', 0)) for x in items]):,}</b>", center_bold),
        Paragraph(f"<b>Rp {memo_dict.get('nominal', 0):,}</b>", center_bold)
    ])

    items_table = Table(table_rows, colWidths=[30, 95, 185, 70, 45, 95])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
        ('GRID', (0, 0), (-1, -1), 0.8, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('SPAN', (0, -1), (3, -1)),  # Merge NO s/d COGS untuk baris total
        ('ALIGN', (0, -1), (3, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 25))

    # 4. KOTAK TANDA TANGAN (PERSIS FORMAT GAMBAR: Diajukan oleh | Diproses oleh | Diperiksa oleh)
    sign_data = [
        [
            Paragraph("<b>Diajukan oleh,</b>", center_bold),
            Paragraph("<b>Diproses oleh,</b>", center_bold),
            Paragraph("<b>Diperiksa oleh,</b>", center_bold)
        ],
        [
            Paragraph(f"<br/><br/><br/><b>({memo_dict.get('diajukan_oleh', 'Tim Pemohon')})</b><br/><font size=7 color='#666'>Tgl: {memo_dict.get('tanggal', '-')}</font>", center_text),
            Paragraph(f"<br/><br/><br/><b>({memo_dict.get('diproses_oleh', 'Tim Logistik')})</b><br/><font size=7 color='#666'>Status: {memo_dict.get('status_logistik', 'Pending')}</font>", center_text),
            Paragraph(f"<br/><br/><br/><b>({memo_dict.get('diperiksa_oleh', 'SPV / Manager')})</b><br/><font size=7 color='#666'>Status: {memo_dict.get('status_spv', 'Pending')}</font>", center_text)
        ]
    ]

    sign_table = Table(sign_data, colWidths=[173, 173, 174])
    sign_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('BOTTOMPADDING', (0, 1), (-1, 1), 10),
    ]))
    story.append(sign_table)

    doc.build(story)
    buf.seek(0)
    return buf.getvalue()