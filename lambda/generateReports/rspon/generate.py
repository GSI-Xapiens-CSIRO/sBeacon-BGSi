import os
from pathlib import Path

from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.pdfbase.pdfmetrics import stringWidth


def _create_annotations(
    filename, pii_name, pii_dob, pii_gender, diplotype, phenotype, pk_v, pkdb_v
):
    YT = 695
    # x, y, w, h, flags, text
    common_text_fields = [
        (150, YT, 120, 10, 0, ""),
        (150, YT - 11, 120, 10, 0, pii_name),
        (150, YT - 11 * 2, 120, 10, 0, pii_dob),
        (150, YT - 11 * 3, 120, 10, 0, pii_gender),
        (150, YT - 11 * 4, 120, 10, 0, ""),
        (150, YT - 11 * 5, 120, 10, 0, ""),
        (150, YT - 11 * 6, 120, 10, 0, ""),
        (405, YT, 120, 10, 0, ""),
        (405, YT - 11, 120, 10, 0, ""),
        (405, YT - 11 * 2, 120, 10, 0, ""),
        (405, YT - 11 * 3, 120, 10, 0, ""),
        (405, YT - 11 * 4, 120, 10, 0, ""),
        (405, YT - 11 * 5, 120, 10, 0, ""),
    ]
    pg_1_text_fields = [
        # patient clinical info
        (73, 510, 470, 65, 1 << 12, ""),
    ]
    pg_2_text_fields = []
    pg_3_text_fields = [
        # names in last page
        (188, 280, 350, 15, 0, ""),
        (188, 255, 350, 15, 0, ""),
        (188, 230, 350, 15, 0, ""),
    ]

    pg_1_text_boxes = [
        # examination details
        (260, 454, 11, diplotype),
        (400, 454, 11, phenotype),
    ]
    pg_2_text_boxes = [
        # versions
        (200, 300, 10, pk_v),
        (200, 284, 10, pkdb_v),
    ]
    pg_3_text_boxes = []
    c = canvas.Canvas(filename, pagesize=letter)
    form = c.acroForm

    for page_text_fields, page_text_boxes in zip(
        [pg_1_text_fields, pg_2_text_fields, pg_3_text_fields],
        [pg_1_text_boxes, pg_2_text_boxes, pg_3_text_boxes],
    ):
        for n, (x, y, w, h, flags, text) in enumerate(
            common_text_fields + page_text_fields
        ):
            form.textfield(
                name=f"text_field_{n}",
                tooltip="Text Field",
                value=text,
                x=x,
                y=y,
                width=w,
                height=h,
                fontSize=8,
                fillColor=colors.white,
                fieldFlags=flags,
            )
        for n, (x, y, fs, text) in enumerate(page_text_boxes):
            c.setFont("Helvetica", fs)
            c.drawString(x, y, text)

        c.showPage()
    c.save()


def _overlay_pdf_with_annotations(src, dest, output):
    # Open the existing PDF and the newly created PDF
    annotations_pdf = PdfReader(src)
    template_pdf = PdfReader(dest)

    # Create a PDF writer for the output PDF
    writer = PdfWriter()

    # Add pages from the existing PDF and overlay them with new content
    for page_number in range(len(template_pdf.pages)):
        page = template_pdf.pages[page_number]
        if page_number < len(annotations_pdf.pages):
            overlay_page = annotations_pdf.pages[page_number]
            page.merge_page(overlay_page)
        writer.add_page(page)

    # Write the merged PDF to a file
    with open(output, "wb") as f:
        writer.write(f)


def _get_details(variants):
    # TODO update this logic
    match len(variants):
        case 1:
            return "NM", "Test Diplotype", "Test Phenotype", "PK V1", "PGKB DB VX"
        case 2:
            return "IM", "Test Diplotype", "Test Phenotype", "PK V1", "PGKB DB VX"
        case 3:
            return "PoorM", "Test Diplotype", "Test Phenotype", "PK V1", "PGKB DB VX"
        case _:
            return "RapidM", "Test Diplotype", "Test Phenotype", "PK V1", "PGKB DB VX"


def generate(*, pii_name=None, pii_dob=None, pii_gender=None, variants=None):
    assert all([pii_name, pii_dob, pii_gender]), "Missing required fields"
    module_dir = Path(__file__).parent
    kind, diplotype, phenotype, pk_v, pkdb_v = _get_details(variants)
    annotated = "/tmp/annotations.pdf"
    template = f"{module_dir}/{kind}.pdf"

    _create_annotations(
        annotated, pii_name, pii_dob, pii_gender, diplotype, phenotype, pk_v, pkdb_v
    )
    _overlay_pdf_with_annotations(annotated, template, "/tmp/annotated_m.pdf")
    os.remove(annotated)
    return "/tmp/annotated_m.pdf"


if __name__ == "__main__":
    generate(pii_name="John Doe", pii_dob="01/01/1900", pii_gender="Male", variants=[1])
