import os
import uuid

from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors


def _create_annotations(
    filename, pages, footer_name_pos, footer_dob_pos, page_num_pos, report_id=None
):
    c = canvas.Canvas(filename, pagesize=letter)
    form = c.acroForm

    for p in range(pages):
        x, y, fs, text = (5, 780, 12, report_id)
        c.setFont("Helvetica", fs)
        c.drawString(x, y, text)
        # footer name
        x, y, fs, text = footer_name_pos
        form.textfield(
            name="name",
            tooltip="Name",
            value=f"{text}",
            x=x,
            y=y,
            width=200,
            height=12,
            fontSize=8,
            borderWidth=0,
            fillColor=colors.white,
            textColor=None,
            forceBorder=False,
            fieldFlags=0,
        )

        # footer dob
        x, y, fs, text = footer_dob_pos
        form.textfield(
            name="dob",
            tooltip="Date of Birth",
            value=f"{text}",
            x=x,
            y=y,
            width=100,
            height=12,
            fontSize=8,
            borderWidth=0,
            fillColor=colors.white,
            textColor=None,
            forceBorder=False,
            fieldFlags=0,
        )

        # page num
        x, y = page_num_pos
        c.setFont("Helvetica", fs)
        c.setFillColor(colors.HexColor("#156082"))
        c.drawString(x, y, f"Page {p+1} of {pages}")
        c.showPage()
    c.save()


def generate(
    summary_pdf, results_pdf, annots_pdf, *, pii_name=None, pii_dob=None, report_id=None
):
    # x, y, fs, text
    footer_name_pos = (146, 48, 12, pii_name)
    footer_dob_pos = (146, 36, 12, pii_dob)
    page_num_pos = (500, 70)

    output_pdf_path = "/tmp/annotations.pdf"
    pdf_int = PdfReader(annots_pdf)
    pdf_summary = PdfReader(summary_pdf)
    pdf_results = PdfReader(results_pdf)

    total_pages = len(pdf_int.pages) + len(pdf_results.pages) + len(pdf_summary.pages)

    _create_annotations(
        output_pdf_path,
        total_pages,
        footer_name_pos,
        footer_dob_pos,
        page_num_pos,
        report_id,
    )

    writer = PdfWriter()
    pages = []

    pages.append(pdf_int.pages[0])
    pages += pdf_summary.pages
    pages.append(pdf_int.pages[1])
    pages += pdf_results.pages
    pages += pdf_int.pages[2:]

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
