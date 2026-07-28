import os
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def create_invoice_pdf(invoice_data, business_info, items_data):
    """
    Generates a professional PDF GST Invoice for Astha Builders & Hardware using ReportLab.
    Returns bytes buffer.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    header_style = ParagraphStyle(
        'InvHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#1E3A8A')
    )

    sub_style = ParagraphStyle(
        'InvSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#475569')
    )

    title_style = ParagraphStyle(
        'InvTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=16,
        textColor=colors.HexColor('#0D9488'),
        alignment=2
    )

    cell_style = ParagraphStyle(
        'CellText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#1E293B')
    )

    cell_bold = ParagraphStyle(
        'CellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#1E293B')
    )

    cell_header = ParagraphStyle(
        'CellHdr',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white
    )

    story = []

    # 1. Top Business Header & Title
    b_name = business_info.get("business_name", "ASTHA BUILDERS & HARDWARE")
    b_gst = business_info.get("gst", "21AAAAA0000A1Z5")
    b_phone = business_info.get("phone", "+91 98765 43210")
    b_addr = business_info.get("address", "Hardware Yard, Bhubaneswar, Odisha")

    left_info = f"<b>{b_name}</b><br/>{b_addr}<br/>GSTIN: {b_gst} | Phone: {b_phone}"
    right_info = f"<b>TAX INVOICE</b><br/>Invoice No: <b>{invoice_data.get('invoice_no', 'INV-001')}</b><br/>Date: {invoice_data.get('date', datetime.now().strftime('%Y-%m-%d'))}"

    header_table = Table(
        [[Paragraph(left_info, header_style), Paragraph(right_info, title_style)]],
        colWidths=[320, 202]
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10))

    # Divider line
    div_table = Table([[""]], colWidths=[522])
    div_table.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (-1, -1), 1.5, colors.HexColor('#0D9488')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(div_table)
    story.append(Spacer(1, 10))

    # 2. Bill To / Party Details
    cust_name = invoice_data.get("customer", "Cash Customer")
    cust_mobile = invoice_data.get("mobile", "N/A")
    bill_to_text = f"<b>Billed To:</b><br/><b>{cust_name}</b><br/>Mobile: {cust_mobile}<br/>Payment Mode: {invoice_data.get('payment_mode', 'CASH')}"

    pay_status = invoice_data.get("payment_status", "Paid").upper()
    status_color = "#10B981" if pay_status == "PAID" else "#F59E0B"
    status_text = f"<br/><br/>Status: <font color='{status_color}'><b>{pay_status}</b></font>"

    party_table = Table(
        [[Paragraph(bill_to_text, sub_style), Paragraph(status_text, ParagraphStyle('RStatus', parent=sub_style, alignment=2))]],
        colWidths=[350, 172]
    )
    party_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
    story.append(party_table)
    story.append(Spacer(1, 12))

    # 3. Item Table
    table_data = [[
        Paragraph("S.No", cell_header),
        Paragraph("Product Description", cell_header),
        Paragraph("Qty", cell_header),
        Paragraph("Unit", cell_header),
        Paragraph("Rate (₹)", cell_header),
        Paragraph("GST %", cell_header),
        Paragraph("Total (₹)", cell_header)
    ]]

    for i, item in enumerate(items_data, 1):
        table_data.append([
            Paragraph(str(i), cell_style),
            Paragraph(str(item.get("product", "Item")), cell_style),
            Paragraph(str(item.get("quantity", 1)), cell_style),
            Paragraph(str(item.get("unit", "Pcs")), cell_style),
            Paragraph(f"{float(item.get('price', 0)):,.2f}", cell_style),
            Paragraph(f"{float(item.get('gst', 0)):.1f}%", cell_style),
            Paragraph(f"{float(item.get('total', 0)):,.2f}", cell_bold)
        ])

    items_table = Table(table_data, colWidths=[35, 207, 45, 45, 65, 50, 75])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A8A')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
        ('TOPPADDING', (0, 0), (-1, 0), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 12))

    # 4. Total Summary
    total_val = float(invoice_data.get("total", 0))
    paid_val = float(invoice_data.get("amount_paid", total_val))
    bal_val = float(invoice_data.get("balance", 0))

    summary_text = f"Grand Total: <b>₹ {total_val:,.2f}</b><br/>Amount Paid: ₹ {paid_val:,.2f}<br/>Balance Due: <b>₹ {bal_val:,.2f}</b>"

    sum_table = Table(
        [["", Paragraph(summary_text, ParagraphStyle('SumR', parent=sub_style, alignment=2))]],
        colWidths=[320, 202]
    )
    story.append(sum_table)
    story.append(Spacer(1, 20))

    # 5. Terms & Footer
    terms_text = "<b>Terms & Conditions:</b><br/>1. Goods once sold will not be taken back without valid invoice.<br/>2. Subject to Bhubaneswar Jurisdiction."
    story.append(Paragraph(terms_text, sub_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

def generate_invoice_pdf(invoice_obj, party_obj, items_list):
    """Wrapper mapping SalesInvoiceModel objects into ReportLab generator."""
    inv_dict = {
        "invoice_no": getattr(invoice_obj, "invoice_no", "INV-001"),
        "date": str(getattr(invoice_obj, "invoice_date", datetime.now().date())),
        "customer": getattr(party_obj, "business_name", "Cash Customer"),
        "mobile": getattr(party_obj, "mobile", "N/A"),
        "payment_mode": getattr(invoice_obj, "payment_mode", "CASH"),
        "payment_status": getattr(invoice_obj, "payment_status", "PAID"),
        "total": float(getattr(invoice_obj, "grand_total", 0.0)),
        "amount_paid": float(getattr(invoice_obj, "amount_paid", 0.0)),
        "balance": float(getattr(invoice_obj, "balance_due", 0.0))
    }

    biz_dict = {
        "business_name": "ASTHA BUILDERS & HARDWARE",
        "gst": "21AAAAA0000A1Z5",
        "phone": "+91 98765 43210",
        "address": "Hardware Yard, Bhubaneswar, Odisha"
    }

    items_dicts = []
    for it in items_list:
        p_name = it.product.product_name if hasattr(it, "product") and it.product else "Item"
        items_dicts.append({
            "product": p_name,
            "quantity": float(it.quantity),
            "unit": getattr(it, "unit_name", "Pcs"),
            "price": float(it.unit_price),
            "gst": float(it.gst_rate),
            "total": float(it.line_total)
        })

    return create_invoice_pdf(inv_dict, biz_dict, items_dicts)
