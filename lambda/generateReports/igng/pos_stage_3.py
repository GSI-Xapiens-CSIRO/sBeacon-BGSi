import os
import uuid
from datetime import datetime

from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors


def _create_annotations(filename, pages, page_num_pos, report_id=None):
    c = canvas.Canvas(filename, pagesize=A4)
    form = c.acroForm

    text_boxes = [
        # ---left side---
        # Nama Pasien :
        (147, 768, 134, 12),
        # ID Pasien :
        (147, 755, 134, 12),
        # Jenis Kelamin :
        (147, 742, 134, 12),
        # Tanggal Lahir :
        (147, 729, 134, 12),
        # Ras :
        (147, 716, 134, 12),
        # Jenis Sampel :
        (147, 703, 134, 12),
        # ---right side---
        # Dokter Pengirim :
        (435, 768, 90, 12),
        # Tanggal Pengambilan sampel :
        (435, 755, 90, 12),
        # Tanggal Pemeriksaan :
        (435, 742, 90, 12),
        # Institusi Pengirim :
        (435, 716, 90, 12),
        # Laboratorium Penguji :
        (435, 703, 90, 12),
    ]
    # Tanggal Pelaporan :
    date_pos = (435, 731, 12)

    for p in range(pages):
        # page num
        x, y = page_num_pos
        c.setFont("Helvetica", 11)
        c.setFillColor(colors.HexColor("#828282"))
        c.drawString(x, y, f"Halaman  {p+1} dari {pages}")
        x, y, fs, text = (5, 830, 12, report_id)
        c.setFont("Helvetica", fs)
        c.drawString(x, y, text)

        for n, (x, y, w, fs) in enumerate(text_boxes):
            form.textfield(
                name=f"header-{n}",
                tooltip="",
                value=f"",
                x=x,
                y=y,
                width=w,
                height=fs + 5,
                fontSize=fs - 2,
                borderWidth=0,
                fillColor=colors.transparent,
                textColor=None,
                forceBorder=False,
                fieldFlags=1 << 12,
            )
        # Tanggal Pelaporan :
        x, y, fs = date_pos
        c.setFont("Helvetica", fs - 2)
        c.setFillColor(colors.black)
        c.drawString(x, y, str(datetime.now().strftime("%d/%m/%Y")))
        c.showPage()
    c.save()


def generate(
    table_pdf,
    annots_pdf,
    *,
    pii_name=None,
    pii_dob=None,
    pii_gender=None,
    report_id=None,
):
    # x, y, fs, text
    page_num_pos = (500, 50)

    output_pdf_path = "/tmp/annotations.pdf"
    pdf_body = PdfReader(annots_pdf)
    pdf_table = PdfReader(table_pdf)

    total_pages = len(pdf_body.pages) + len(pdf_table.pages)

    _create_annotations(output_pdf_path, total_pages, page_num_pos, report_id)

    writer = PdfWriter()
    pages = []

    pages.append(pdf_body.pages[0])
    pages += pdf_table.pages
    pages += pdf_body.pages[1:]

    footer_pagenum_annotations = PdfReader(output_pdf_path)

    for n, page in enumerate(pages):
        page.merge_page(footer_pagenum_annotations.pages[n])
        writer.add_page(page)

    output_file_name = f"/tmp/{str(uuid.uuid4())}.pdf"
    with open(output_file_name, "wb") as f:
        writer.write(f)

    os.remove(output_pdf_path)
    print(f"Generated Stage 3 PDF: {output_file_name}")
    return output_file_name
