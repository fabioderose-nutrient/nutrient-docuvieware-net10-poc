"""Generate the fictitious sample documents of the DocuVieware backend.

Documents go to DocuViewareREST/App_Data/Documents (the document picker) and
the default document to DocuViewareREST/wwwroot/getting-started.pdf.

Every name, address and amount below is invented. Email addresses use the
reserved example.com domain.

Usage (from the repository root):
    python -m venv .venv-samples
    .venv-samples/bin/pip install reportlab openpyxl pillow pypdf
    .venv-samples/bin/python samples/generate_samples.py
"""

import io
from email import policy
from email.message import EmailMessage
from email.utils import format_datetime
from datetime import datetime, timezone
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parent.parent
DOCUMENTS = ROOT / "DocuViewareREST" / "App_Data" / "Documents"
WWWROOT = ROOT / "DocuViewareREST" / "wwwroot"
COMPANY = "Example Supplies Ltd."
CLIENT = "Sample Retail Group"


def pdf_document(title, paragraphs, pages=1):
    """A simple text PDF built with reportlab."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    c.setTitle(title)
    c.setAuthor(COMPANY)
    width, height = A4
    for page in range(1, pages + 1):
        c.setFillColorRGB(0.12, 0.23, 0.45)
        c.rect(0, height - 28 * mm, width, 28 * mm, stroke=0, fill=1)
        c.setFillColorRGB(1, 1, 1)
        c.setFont("Helvetica-Bold", 18)
        c.drawString(20 * mm, height - 17 * mm, title)
        c.setFont("Helvetica", 10)
        c.drawRightString(width - 20 * mm, height - 17 * mm, COMPANY)
        c.setFillColorRGB(0.1, 0.1, 0.1)
        y = height - 45 * mm
        for heading, body in paragraphs:
            c.setFont("Helvetica-Bold", 12)
            c.drawString(20 * mm, y, heading)
            y -= 7 * mm
            c.setFont("Helvetica", 10.5)
            for line in body:
                c.drawString(20 * mm, y, line)
                y -= 5.5 * mm
            y -= 5 * mm
        c.setFont("Helvetica", 8)
        c.setFillColorRGB(0.4, 0.4, 0.4)
        c.drawString(20 * mm, 12 * mm, "Fictitious sample document generated for a Nutrient demo.")
        c.drawRightString(width - 20 * mm, 12 * mm, f"Page {page} of {pages}")
        c.showPage()
    c.save()
    return buffer.getvalue()


def service_agreement():
    paragraphs = [
        ("1. Parties", [
            f"This agreement is made between {COMPANY} (the supplier)",
            f"and {CLIENT} (the client).",
        ]),
        ("2. Services", [
            "The supplier delivers office supplies to four stores every week.",
            "Orders placed before 2 p.m. are shipped the same working day.",
        ]),
        ("3. Prices", [
            "Prices follow the rate card attached to this PDF (rate-card.csv).",
            "Rates are reviewed once a year, in January.",
        ]),
        ("4. Term", [
            "The agreement starts on 1 March 2026 and runs for 24 months.",
            "Either party may end it with 90 days written notice.",
        ]),
    ]
    pdf = pdf_document("Service Agreement", paragraphs, pages=2)
    # Embed a CSV file: the API lists PDF embedded files as attachments.
    reader = PdfReader(io.BytesIO(pdf))
    writer = PdfWriter()
    writer.append(reader)
    writer.add_attachment("rate-card.csv", (
        "item,unit,price_usd\n"
        "Printer paper A4 (box of 5 reams),box,8.40\n"
        "Ballpoint pens (box of 50),box,6.10\n"
        "Sticky notes (pack of 12),pack,4.25\n"
    ).encode("utf-8"))
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def quote_pdf():
    return pdf_document("Quote Q-2026-0142", [
        ("Items", [
            "40 x Printer paper A4 (box of 5 reams)  336.00 USD",
            "25 x Ballpoint pens (box of 50)         152.50 USD",
            "10 x Sticky notes (pack of 12)               42.50 USD",
        ]),
        ("Total", ["531.00 USD, valid 30 days."]),
    ])


def purchase_order_xml():
    return """<?xml version="1.0" encoding="UTF-8"?>
<purchaseOrder number="PO-2026-0087" date="2026-03-12">
  <buyer>
    <name>Sample Retail Group</name>
    <email>purchasing@example.com</email>
  </buyer>
  <supplier>
    <name>Example Supplies Ltd.</name>
    <email>orders@example.com</email>
  </supplier>
  <lines>
    <line sku="PPR-005" quantity="40" unitPrice="8.40">Printer paper A4 (box of 5 reams)</line>
    <line sku="PEN-050" quantity="25" unitPrice="6.10">Ballpoint pens (box of 50)</line>
    <line sku="NTS-012" quantity="10" unitPrice="4.25">Sticky notes (pack of 12)</line>
  </lines>
  <total currency="USD">531.00</total>
</purchaseOrder>
"""


def email(subject, body_text, body_html, attachments=(), day=10):
    message = EmailMessage()
    message["From"] = f"{COMPANY} <orders@example.com>"
    message["To"] = f"{CLIENT} <purchasing@example.com>"
    message["Subject"] = subject
    message["Date"] = format_datetime(datetime(2026, 3, day, 9, 30, tzinfo=timezone.utc))
    message["Message-ID"] = f"<sample-{day}@example.com>"
    message.set_content(body_text)
    # One tag per line keeps the HTML part short-lined (7bit, no quoted-printable).
    message.add_alternative(body_html.replace("><", ">\n<"), subtype="html")
    for name, data, maintype, subtype in attachments:
        message.add_attachment(data, maintype=maintype, subtype=subtype, filename=name)
    # CRLF line endings, as in real mail files.
    return message.as_bytes(policy=policy.SMTP)


def delivery_update_eml():
    return email(
        "Delivery update for PO-2026-0087",
        "Hello,\n\nYour order PO-2026-0087 left our warehouse this morning.\n"
        "Expected delivery: Friday 13 March, before noon.\n\nKind regards,\nCustomer Service",
        "<html><body style='font-family: Arial, sans-serif'>"
        "<h2 style='color:#1e3a73'>Delivery update</h2>"
        "<p>Hello,</p><p>Your order <strong>PO-2026-0087</strong>\nleft our warehouse this morning.</p>"
        "<table border='1' cellpadding='6' cellspacing='0'>"
        "<tr><th>Item</th><th>Quantity</th></tr>"
        "<tr><td>Printer paper A4 (box of 5 reams)</td><td>40</td></tr>"
        "<tr><td>Ballpoint pens (box of 50)</td><td>25</td></tr>"
        "<tr><td>Sticky notes (pack of 12)</td><td>10</td></tr></table>"
        "<p>Expected delivery: Friday 13 March, before noon.</p>"
        "<p>Kind regards,<br>Customer Service</p></body></html>",
        day=11,
    )


def quote_eml():
    notes = (
        "Notes for the quote Q-2026-0142\n"
        "- Prices include delivery to the four sites.\n"
        "- Payment terms: 30 days.\n"
    ).encode("utf-8")
    return email(
        "Quote Q-2026-0142 with attachments",
        "Hello,\n\nPlease find our quote and a few notes attached.\n\nKind regards,\nSales Team",
        "<html><body style='font-family: Arial, sans-serif'>"
        "<h2 style='color:#1e3a73'>Quote Q-2026-0142</h2>"
        "<p>Hello,</p><p>Please find our quote and a few notes attached.</p>"
        "<p>Kind regards,<br>Sales Team</p></body></html>",
        attachments=[
            ("quote-Q-2026-0142.pdf", quote_pdf(), "application", "pdf"),
            ("quote-notes.txt", notes, "text", "plain"),
        ],
        day=9,
    )


def monthly_figures_xlsx():
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Q1 2026"
    sheet.append(["Month", "Orders", "Revenue (USD)", "Returns"])
    for row in [("January", 112, 18450.00, 3), ("February", 98, 16120.50, 1), ("March", 121, 20310.75, 2)]:
        sheet.append(row)
    sheet.append(["Total", 331, 54881.25, 6])
    for cell in sheet[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="1E3A73")
    for column, width in zip("ABCD", (14, 10, 16, 10)):
        sheet.column_dimensions[column].width = width
    out = io.BytesIO()
    workbook.save(out)
    return out.getvalue()


def font(size, bold=False):
    names = ["Arial Bold.ttf", "DejaVuSans-Bold.ttf"] if bold else ["Arial.ttf", "DejaVuSans.ttf"]
    for name in names:
        for folder in ["/System/Library/Fonts/Supplemental", "/Library/Fonts", "/usr/share/fonts/truetype/dejavu"]:
            path = Path(folder) / name
            if path.exists():
                return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def receipt_png():
    image = Image.new("RGB", (600, 800), "white")
    draw = ImageDraw.Draw(image)
    draw.text((40, 40), "EXAMPLE SUPPLIES LTD.", fill="black", font=font(30, True))
    draw.text((40, 85), "Receipt R-55210  -  12 March 2026", fill="black", font=font(20))
    y = 150
    for item, price in [("Printer paper x 2", "16.80"), ("Ballpoint pens x 1", "6.10"), ("Sticky notes x 3", "12.75")]:
        draw.text((40, y), item, fill="black", font=font(22))
        draw.text((460, y), price, fill="black", font=font(22))
        y += 40
    draw.line((40, y + 10, 560, y + 10), fill="black", width=2)
    draw.text((40, y + 30), "TOTAL USD", fill="black", font=font(24, True))
    draw.text((460, y + 30), "35.65", fill="black", font=font(24, True))
    draw.text((40, 720), "Thank you. Fictitious sample.", fill="gray", font=font(18))
    out = io.BytesIO()
    image.save(out, "PNG", optimize=True)
    return out.getvalue()




def getting_started_pdf():
    return pdf_document("Getting Started", [
        ("Default document", [
            "This PDF is loaded into every new viewer session from a URL",
            "(DefaultDocumentUri in DocuViewareREST/appsettings.json).",
        ]),
        ("Server documents", [
            "Pick a file in the top bar and click Load in viewer. The DocuVieware",
            "server reads it, renders the pages and sends only images to the browser.",
        ]),
        ("Formats", [
            "PDF, Office, images, emails (EML, MSG) and text render natively.",
            "XML goes through a small custom action and is rendered as text.",
        ]),
    ])


def main():
    DOCUMENTS.mkdir(parents=True, exist_ok=True)
    WWWROOT.mkdir(parents=True, exist_ok=True)
    files = {
        DOCUMENTS / "service-agreement.pdf": service_agreement(),
        DOCUMENTS / "purchase-order.xml": purchase_order_xml().encode("utf-8"),
        DOCUMENTS / "delivery-update.eml": delivery_update_eml(),
        DOCUMENTS / "quote-with-attachments.eml": quote_eml(),
        DOCUMENTS / "monthly-figures.xlsx": monthly_figures_xlsx(),
        DOCUMENTS / "scanned-receipt.png": receipt_png(),
        WWWROOT / "getting-started.pdf": getting_started_pdf(),
    }
    for path, data in files.items():
        path.write_bytes(data)
        print(f"{path.relative_to(ROOT)}  {len(data)} bytes")


if __name__ == "__main__":
    main()
