from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import TableStyle
from reportlab.lib.units import inch
import os


def create_invoice(name, installment, total_paid, total_amount,
                   balance, reference, bill_no,
                   submitted_at, verified_at):

    os.makedirs("invoices", exist_ok=True)

    filename = f"invoice_{name}_{bill_no}.pdf"
    filepath = os.path.join("invoices", filename)

    doc = SimpleDocTemplate(filepath)
    elements = []
    styles = getSampleStyleSheet()

    # Title
    elements.append(Paragraph("<b>COLLEGE TOUR PAYMENT RECEIPT</b>", styles["Title"]))
    elements.append(Spacer(1, 0.4 * inch))

    # Invoice Data Table
    data = [
        ["Bill No", bill_no],
        ["Member Name", name],
        ["Installment Paid", f"₹ {installment}"],
        ["Total Paid So Far", f"₹ {total_paid}"],
        ["Total Amount", f"₹ {total_amount}"],
        ["Remaining Balance", f"₹ {balance}"],
        ["Reference Number", reference],
        ["Payment Submitted At", submitted_at],
        ["Payment Verified At", verified_at],
    ]

    table = Table(data, colWidths=[2.5 * inch, 3 * inch])
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 0.5 * inch))

    # Verified Seal
    seal_style = ParagraphStyle(
        name="SealStyle",
        fontSize=16,
        textColor=colors.green
    )

    elements.append(Paragraph("<b>✔ PAYMENT VERIFIED</b>", seal_style))
    elements.append(Spacer(1, 0.3 * inch))

    elements.append(Paragraph(
        "This is a system-generated receipt. No signature required.",
        styles["Normal"]
    ))

    doc.build(elements)

    return filepath