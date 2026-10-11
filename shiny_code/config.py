import os
import io
import base64
from datetime import datetime
import pandas as pd

# (PENTING: Jangan hapus fungsi bawaan config.py Anda yang lain seperti:
# get_supabase, safe_int, load_data_from_info, format_datetime_wib!)

def get_reportlab_image_from_base64(data_url, width=120, height=45):
    """Mengubah base64 canvas URL menjadi Image Flowable ReportLab"""
    try:
        from reportlab.platypus import Image  # ✅ WAJIB DIIMPORT DI SINI
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

def generate_audit_pack_pdf_bytes(audit_data: dict) -> bytes:
    """Menghasilkan PDF resmi External Audit Pack lengkap dengan tabel selisih & TTD digital"""
    try:
        # ✅ WAJIB DIIMPORT DI SINI AGAR TIDAK 'NameError: SimpleDocTemplate is not defined'
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib import colors
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
        )
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    except ImportError as e:
        print("⚠️ ReportLab / Pillow belum terpasang:", e)
        return b""

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        rightMargin=25, leftMargin=25,
        topMargin=25, bottomMargin=25
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=colors.HexColor('#1A365D'),
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        textColor=colors.HexColor('#4A5568'),
        spaceAfter=10
    )
    th_style = ParagraphStyle(
        'TableHeader',
        fontName='Helvetica-Bold',
        fontSize=7.5,
        textColor=colors.white,
        alignment=1
    )
    tb_style = ParagraphStyle(
        'TableCell',
        fontName='Helvetica',
        fontSize=7.5,
        textColor=colors.HexColor('#1A202C')
    )
    tb_bold = ParagraphStyle(
        'TableCellBold',
        fontName='Helvetica-Bold',
        fontSize=7.5,
        textColor=colors.HexColor('#1A202C')
    )
    tb_red = ParagraphStyle(
        'TableCellRed',
        fontName='Helvetica-Bold',
        fontSize=7.5,
        textColor=colors.HexColor('#E53E3E'),
        alignment=2
    )
    tb_green = ParagraphStyle(
        'TableCellGreen',
        fontName='Helvetica-Bold',
        fontSize=7.5,
        textColor=colors.HexColor('#22543D'),
        alignment=2
    )

    elements = []

    # 1. Judul Dokumen & Identitas
    elements.append(Paragraph(f"STOCK OPNAME OFFICIAL AUDIT REPORT – {audit_data.get('id', 'AUDIT')}", title_style))
    elements.append(Paragraph(
        f"Company: {audit_data.get('company')} | Branch: {audit_data.get('branch')} | Count Date: {audit_data.get('count_date')} ({audit_data.get('start_time')} - {audit_data.get('end_time')}) | Method: {audit_data.get('count_method')} | Standard: ISA 501 / PSAK 14",
        subtitle_style
    ))

    # 2. Ringkasan Metrik Utama
    summary_data = [
        ["Total SKU Checked", "Total Qty System", "Total Physical Count", "Net Variance Qty", "Lead Auditor"],
        [
            f"{audit_data.get('total_sku', 0):,} SKU",
            f"{audit_data.get('total_qty_system', 0):,} PCS",
            f"{audit_data.get('total_qty_physical', 0):,} PCS",
            f"{audit_data.get('total_variance_qty', 0):,} PCS",
            str(audit_data.get('lead_auditor', '-'))
        ]
    ]
    t_sum = Table(summary_data, colWidths=[150, 150, 150, 150, 191])
    t_sum.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1A365D')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#CBD5E0')),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#F8FAFC')),
    ]))
    elements.append(t_sum)
    elements.append(Spacer(1, 12))

    # =========================================================================
    # 3. TABEL COUNT SHEET YANG SELISIH SAJA (VARIANCE / DISCREPANCY ITEMS)
    # =========================================================================
    elements.append(Paragraph("<b>DAFTAR ITEM SELISIH FISIK VS SISTEM (VARIANCE DISCREPANCIES):</b>", styles['Heading4']))

    diff_items = []
    total_qty_diff = 0
    total_val_diff = 0

    for it in audit_data.get("items", []):
        phys_raw = str(it.get("Physical Count", "")).strip()
        if phys_raw == "" or phys_raw.lower() in ["none", "nan"]:
            continue

        try:
            sys_q = int(float(it.get("Qty System", 0)))
        except:
            sys_q = 0

        try:
            phys_q = int(float(phys_raw))
        except:
            phys_q = 0

        diff_q = phys_q - sys_q

        try:
            hb = int(float(it.get("Harga Beli", 0)))
        except:
            hb = 0

        var_val_raw = it.get("Variance Value", "")
        if str(var_val_raw).strip() not in ["", "-", "None", "nan"]:
            try:
                var_val = int(float(var_val_raw))
            except:
                var_val = diff_q * hb
        else:
            var_val = diff_q * hb

        # Filter HANYA yang mengalami selisih
        if diff_q != 0 or var_val != 0:
            diff_items.append({
                "bin": str(it.get("Bin Location", "-")),
                "sku": str(it.get("SKU", "-")),
                "desc": str(it.get("Description", "-")),
                "uom": str(it.get("UoM (PAIR / PCS)", it.get("UoM", "PCS"))),
                "sys": sys_q,
                "phys": phys_q,
                "diff": diff_q,
                "val": var_val,
                "remarks": str(it.get("Remarks", "")) if str(it.get("Remarks", "")).lower() not in ["none", "nan"] else ""
            })
            total_qty_diff += diff_q
            total_val_diff += var_val

    if diff_items:
        col_w_diff = [25, 75, 105, 185, 36, 50, 50, 50, 85, 130]
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
            ('ALIGN', (4, 0), (4, -1), 'CENTER'),
            ('ALIGN', (5, 0), (7, -1), 'CENTER'),
            ('ALIGN', (8, 0), (8, -1), 'RIGHT'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#EDF2F7')),
            ('SPAN', (0, -1), (1, -1)),
        ]))
        elements.append(t_diff)
    else:
        elements.append(Paragraph(
            "<i>✅ Tidak ada perbedaan kuantitas (0 Selisih). Seluruh hasil hitung fisik cocok 100% dengan data sistem.</i>",
            subtitle_style
        ))

    elements.append(Spacer(1, 14))

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
        t_find = Table(f_table_data, colWidths=[25, 120, 225, 55, 290, 76], repeatRows=1)
        t_find.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2D3748')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E0')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (5, 0), (5, -1), 'CENTER'),
        ]))
        elements.append(t_find)
        elements.append(Spacer(1, 14))

    # 5. TABEL TANDA TANGAN DIGITAL
    elements.append(Paragraph("<b>STOCK COUNT SIGN-OFF (DIGITAL SIGNATURES):</b>", styles['Heading4']))

    img_counter = get_reportlab_image_from_base64(audit_data.get("sign_counter_img"), width=130, height=45)
    img_spv = get_reportlab_image_from_base64(audit_data.get("sign_supervisor_img"), width=130, height=45)
    img_mgr = get_reportlab_image_from_base64(audit_data.get("sign_manager_img"), width=130, height=45)
    img_lead = get_reportlab_image_from_base64(audit_data.get("sign_lead_img"), width=130, height=45)

    sign_table_data = [
        [
            Paragraph("<b>Count Team (Counter)</b>", tb_style),
            Paragraph("<b>Count Team Supervisor</b>", tb_style),
            Paragraph("<b>Warehouse/Ops. Manager</b>", tb_style),
            Paragraph("<b>Lead External Auditor</b>", tb_style)
        ],
        [
            img_counter if img_counter != "" else Paragraph("<br/><br/><i>(Tanda Tangan)</i>", tb_style),
            img_spv if img_spv != "" else Paragraph("<br/><br/><i>(Tanda Tangan)</i>", tb_style),
            img_mgr if img_mgr != "" else Paragraph("<br/><br/><i>(Tanda Tangan)</i>", tb_style),
            img_lead if img_lead != "" else Paragraph("<br/><br/><i>(Tanda Tangan)</i>", tb_style)
        ],
        [
            Paragraph(f"Nama: {audit_data.get('sign_counter_name') or '-'}", tb_style),
            Paragraph(f"Nama: {audit_data.get('sign_supervisor_name') or '-'}", tb_style),
            Paragraph(f"Nama: {audit_data.get('sign_manager_name') or '-'}", tb_style),
            Paragraph(f"Nama: {audit_data.get('sign_lead_name') or '-'}", tb_style)
        ]
    ]

    t_sign = Table(sign_table_data, colWidths=[197, 197, 197, 200])
    t_sign.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EDF2F7')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#CBD5E0')),
        ('BOTTOMPADDING', (0, 1), (-1, 1), 6),
        ('TOPPADDING', (0, 1), (-1, 1), 6),
    ]))

    elements.append(KeepTogether([t_sign]))

    doc.build(elements)
    buf.seek(0)
    return buf.getvalue()