import os
import uuid

from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors


def _create_annotations(
    filename, pages, footer_name_pos, footer_dob_pos, page_num_pos, report_id=None, versions_pos=None
):
    c = canvas.Canvas(filename, pagesize=letter)
    text_color = colors.HexColor("#156082")
    
    for p in range(pages):
        # report_id di header
        x, y, fs, text = (5, 780, 12, report_id or "")
        c.setFont("Helvetica", fs)
        c.drawString(x, y, text)

        if p == pages - 1:
            for pos in versions_pos:
                x, y, fs, text = pos
                c.setFont("Helvetica", fs)
                c.drawString(x, y, text or "")

        # footer name
        x, y, fs, text = footer_name_pos
        c.setFont("Helvetica", fs)
        c.setFillColor(text_color)
        c.drawString(x, y, text or "")

        # footer dob
        x, y, fs, text = footer_dob_pos
        c.setFont("Helvetica", fs)
        c.setFillColor(text_color)
        c.drawString(x, y, text or "")

        # page num
        x, y = page_num_pos
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.HexColor("#156082"))
        c.drawString(x, y, f"Page {p+1} of {pages}")

        c.showPage()
    c.save()


def generate(
    summary_pdf, results_pdf, annots_pdf, *, pii_name=None, pii_dob=None, report_id=None, 
    versions=None,
):
    # x, y, fs, text
    footer_name_pos = (146, 50, 12, pii_name)
    footer_dob_pos = (146, 38, 12, pii_dob)
    page_num_pos = (500, 70)

    output_pdf_path = "/tmp/annotations.pdf"
    pdf_int = PdfReader(annots_pdf)
    pdf_summary = PdfReader(summary_pdf)
    pdf_results = PdfReader(results_pdf)

    total_pages = len(pdf_int.pages) + len(pdf_results.pages) + len(pdf_summary.pages)


    versions_pos = [
        (180, 570, 11, versions["snp_eff_version"]),
        (180, 555, 11, versions["snp_sift_version"]),
        (180, 541, 11, versions["clinvar_version"]),
        (180, 527, 11, versions["omim_version"]),
        (470, 570, 11, versions["gnomad_version"]),
        (470, 555, 11, versions["dbsnp_version"]),
        (470, 541, 11, versions["sift_version"]),
        (470, 527, 11, versions["polyphen2_version"]),
    ]

    _create_annotations(
        output_pdf_path,
        total_pages,
        footer_name_pos,
        footer_dob_pos,
        page_num_pos,
        report_id,
        versions_pos
    )

    writer = PdfWriter()
    pages = []

    # urutan pages
    pages.append(pdf_int.pages[0])
    pages += pdf_summary.pages
    pages.append(pdf_int.pages[1])
    pages += pdf_results.pages
    pages += pdf_int.pages[2:]

    # merge annotations (footer & pagenum)
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
