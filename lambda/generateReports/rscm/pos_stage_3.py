from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import os
from datetime import datetime
from reportlab.platypus import Table, TableStyle


def _create_annotations(filename, pages, footer_name_pos, footer_dob_pos, page_num_pos):
    c = canvas.Canvas(filename, pagesize=letter)

    for p in range(pages):
        # footer name
        x, y, fs, text = footer_name_pos
        c.setFont("Helvetica", fs)
        c.setFillColor(colors.HexColor("#156082"))
        c.drawString(x, y, text)

        # footer dob
        x, y, fs, text = footer_dob_pos
        c.setFont("Helvetica", fs)
        c.setFillColor(colors.HexColor("#156082"))
        c.drawString(x, y, text)

        # page num
        x, y = page_num_pos
        c.setFont("Helvetica", fs)
        c.setFillColor(colors.HexColor("#156082"))
        c.drawString(x, y, f"Page {p+1} of {pages}")
        c.showPage()
    c.save()


def generate(
    *,
    pii_name=None,
    pii_dob=None,
):
    assert all([pii_name, pii_dob]), "Missing required fields."

    # x, y, fs, text
    footer_name_pos = (146, 50, 12, pii_name)
    footer_dob_pos = (146, 38, 12, pii_dob)
    page_num_pos = (500, 70)

    output_pdf_path = "/tmp/annotations.pdf"
    pdf_int = PdfReader("/tmp/annotated-RSCM_positive_int.pdf")
    pdf_vs = PdfReader("/tmp/annotated-RSCM_positive_vs.pdf")
    pdf_res = PdfReader("/tmp/annotated-RSCM_positive_res.pdf")

    total_pages = len(pdf_int.pages) + len(pdf_vs.pages) + len(pdf_res.pages)

    _create_annotations(
        output_pdf_path, total_pages, footer_name_pos, footer_dob_pos, page_num_pos
    )

    writer = PdfWriter()
    pages = []

    pages.append(pdf_int.pages[0])
    pages += pdf_vs.pages
    pages.append(pdf_int.pages[1])
    pages += pdf_res.pages
    pages += pdf_int.pages[2:]

    footer_pagenum_annotations = PdfReader(output_pdf_path)

    for n, page in enumerate(pages):
        page.merge_page(footer_pagenum_annotations.pages[n])
        writer.add_page(page)

    with open("/tmp/annotated_pos.pdf", "wb") as f:
        writer.write(f)

    os.remove(output_pdf_path)
