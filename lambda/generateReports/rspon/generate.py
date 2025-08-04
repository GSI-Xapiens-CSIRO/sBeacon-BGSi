import os
from pathlib import Path
from typing import Dict
import uuid

from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.pdfbase.pdfmetrics import stringWidth


def _create_annotations(
    filename,
    pii_name,
    pii_dob,
    pii_gender,
    diplotype,
    phenotype,
    pharmcat_version,
    pharmgkb_version,
    report_id,
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
    pg_2_text_fields = [
        # clinical notes
        (69, 68, 470, 100, 1 << 12, ""),
    ]
    pg_3_text_fields = [
        # names in last page
        (188, 280, 350, 15, 0, ""),
        (188, 255, 350, 15, 0, ""),
        (188, 230, 350, 15, 0, ""),
    ]

    pg_1_text_boxes = [
        # examination details
        (280, 454, 11, diplotype),
        (380, 454, 11, phenotype),
    ]
    pg_2_text_boxes = [
        # versions
        (200, 300, 10, pharmcat_version),
        (200, 284, 10, pharmgkb_version),
        # clinical notes
        (69, 180, 13, "Clinical Notes"),
    ]
    pg_3_text_boxes = []
    c = canvas.Canvas(filename, pagesize=letter)
    form = c.acroForm
    unique_counter = 0

    for page_text_fields, page_text_boxes in zip(
        [pg_1_text_fields, pg_2_text_fields, pg_3_text_fields],
        [pg_1_text_boxes, pg_2_text_boxes, pg_3_text_boxes],
    ):
        x, y, fs, text = (5, 780, 12, report_id)
        c.setFont("Helvetica", fs)
        c.drawString(x, y, text)
        for n, (x, y, w, h, flags, text) in enumerate(common_text_fields):
            form.textfield(
                name=f"header_{n}",
                tooltip="Text Field",
                value=text,
                x=x,
                y=y,
                width=w,
                height=h,
                fontSize=8,
                borderWidth=0,
                fillColor=colors.white,
                textColor=None,
                forceBorder=False,
                fieldFlags=flags,
            )
        for n, (x, y, w, h, flags, text) in enumerate(page_text_fields):
            form.textfield(
                name=f"text_field_{unique_counter}",
                tooltip="Text Field",
                value=text,
                x=x,
                y=y,
                width=w,
                height=h,
                fontSize=8,
                borderWidth=0,
                fillColor=colors.white,
                textColor=None,
                forceBorder=False,
                fieldFlags=flags,
            )
            unique_counter += 1
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


def generate(
    *,
    pii_name=None,
    pii_dob=None,
    pii_gender=None,
    phenotype=None,
    alleles=None,
    versions=None,
    report_id=None,
):
    module_dir = Path(__file__).parent
    kind = "".join([x[0] for x in phenotype.split(" ")])

    # diplotype, phenotype = _get_details(phenotype,alleles)
    annotated = "/tmp/annotations.pdf"
    template = f"{module_dir}/{kind}.pdf"
    output_file_name = f"/tmp/{uuid.uuid4()}.pdf"

    _create_annotations(
        annotated,
        pii_name,
        pii_dob,
        pii_gender,
        alleles,
        phenotype,
        versions["pharmcat_version"],
        versions["pharmgkb_version"],
        report_id,
    )
    _overlay_pdf_with_annotations(annotated, template, output_file_name)
    os.remove(annotated)

    print(f"Generated report: {output_file_name}")
    return output_file_name


if __name__ == "__main__":
    alleles = "*38,*38"
    phenotype = "Normal Metabolizer"
    versions = {
        "gnomad_version": "v4.1.0",
        "sift_version": "5.2.2",
        "dbsnp_version": "b156",
        "gnomad_1KG_version": "v3.1.2",
        "gnomad_constraints_version": "v3.1.2",
        "snp_eff_version": "N/A",
        "snp_sift_version": "N/A",
        "polyphen2_version": "N/A",
        "omim_version": "N/A",
        "pharmcat_version": "3.0.0",
        "pharmgkb_version": "2025-03-07-16-38",
    }
    generate(
        pii_name="John Doe",
        pii_dob="01/01/1900",
        pii_gender="Male",
        phenotype=phenotype,
        alleles=alleles,
        versions=versions,
        report_id=str(uuid.uuid4()),
    )
