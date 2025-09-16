import os
import uuid
from datetime import datetime

from PyPDF2 import PdfReader, PdfWriter
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors


def _write_header(c, form, pii_name, pii_dob, pii_gender):
    fields = [
        # Name
        (186, 670, 135, 12, 12, pii_name, 0),
        # Lab number
        (186, 670 - 14, 135, 12, 12, "", 0),
        # gender
        (186, 670 - 14 * 2, 135, 12, 12, pii_gender, 0),
        # DOB
        (186, 670 - 14 * 3, 135, 12, 12, pii_dob, 0),
        # Race
        (186, 670 - 14 * 4, 135, 12, 12, "", 0),
        # Specimen type
        (186, 670 - 14 * 5, 135, 12, 12, "", 0),
        # Sample Id
        (186, 670 - 14 * 6, 135, 12, 12, "", 0),
        # Referring clinician
        (438, 670, 135, 12, 12, "", 0),
        # Sampling date
        (438, 670 - 14, 135, 12, 12, "", 0),
        # Testing Date
        (438, 670 - 14 * 2, 135, 12, 12, "", 0),
        # Reporting Date
        (438, 670 - 14 * 3, 135, 12, 12, datetime.now().strftime("%d/%m/%Y"), 0),
        # Referring institution
        (438, 670 - 14 * 4, 135, 12, 12, "", 0),
        # Testing lab
        (438, 670 - 14 * 5, 135, 12, 12, "", 0),
    ]

    for n, pos in enumerate(fields):
        x, y, w, h, fs, text, flags = pos
        c.setFont("Helvetica", fs)
        form.textfield(
            name=f"header-{n}",
            tooltip="",
            value=f"{text}",
            x=x,
            y=y,
            width=w,
            height=h,
            fontSize=fs - 2,
            borderWidth=0,
            borderColor=None,
            fillColor=colors.white,
            textColor=None,
            forceBorder=False,
            fieldFlags=flags,
        )


def _create_annotations(
    pii_name,
    pii_dob,
    pii_gender,
    versions,
    report_id,
    filename,
):
    _text_field_positions_page_1 = [
        # Clinical Information
        (186, 526, 375, 35, 12, "", 1 << 12),
        # Results interpretation
        (70, 152, 490, 170, 12, "", 1 << 12),
    ]
    _text_field_positions_page_2 = [
        # recommendation
        (70, 460, 490, 85, 12, "", 1 << 12),
        # additional information
        (70, 221, 490, 216, 12, "", 1 << 12),
        # validated by
        (442, 120, 118, 82, 12, "", 0),
    ]
    _text_field_positions_page_3 = []
    _text_field_positions_page_4 = [
        # References
        (91, 63, 445, 345, 12, "", 1 << 12),
    ]
    # static text
    _static_text_page_1 = []
    _static_text_page_2 = []
    _static_text_page_3 = []
    _static_text_page_4 = [
        # OMIM
        (170, 479, 11, versions["omim_version"]),
        # ClinVar
        (170, 467, 11, versions["clinvar_version"]),
        # gnomAD
        (170, 455, 11, versions["gnomad_version"]),
        # dbSNP
        (170, 443, 11, versions["dbsnp_version"]),
        # SIFT
        (170, 431, 11, versions["sift_version"]),
        # PolyPhen2
        (170, 419, 11, versions["polyphen2_version"]),
    ]

    c = canvas.Canvas(filename, pagesize=letter)
    form = c.acroForm
    unique_counter = 0

    for page_poses_tf, page_poses_st in [
        (_text_field_positions_page_1, _static_text_page_1),
        (_text_field_positions_page_2, _static_text_page_2),
        (_text_field_positions_page_3, _static_text_page_3),
        (_text_field_positions_page_4, _static_text_page_4),
    ]:
        x, y, fs, text = (5, 780, 12, report_id)
        c.setFont("Helvetica", fs)
        c.drawString(x, y, text)
        for n, pos in enumerate(page_poses_tf):
            x, y, w, h, fs, text, flags = pos
            c.setFont("Helvetica", fs)
            form.textfield(
                name=f"name-{unique_counter}",
                tooltip="",
                value=f"{text}",
                x=x,
                y=y,
                width=w,
                height=h,
                fontSize=fs - 2,
                borderWidth=0,
                borderColor=None,
                fillColor=colors.white,
                textColor=None,
                forceBorder=False,
                fieldFlags=flags,
            )
            unique_counter += 1
        for n, pos in enumerate(page_poses_st):
            x, y, fs, text = pos
            c.setFont("Helvetica", fs)
            c.drawString(x, y, text)
        _write_header(c, form, pii_name, pii_dob, pii_gender)
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
    *, pii_name=None, pii_dob=None, pii_gender=None, versions=None, report_id=None
):
    module_dir = Path(__file__).parent
    output_file_name = f"/tmp/{uuid.uuid4()}.pdf"
    _create_annotations(
        pii_name, pii_dob, pii_gender, versions, report_id, "/tmp/annotations.pdf"
    )
    _overlay_pdf_with_annotations(
        "/tmp/annotations.pdf",
        f"{module_dir}/EN_Genome Report_No Finding_CRD.pdf",
        output_file_name,
    )
    os.remove("/tmp/annotations.pdf")

    print(f"Generated report: {output_file_name}")
    return output_file_name


if __name__ == "__main__":
    data = {
        "pii_name": "John Doe",
        "pii_dob": "01/01/2000",
        "pii_gender": "Male",
        "versions": {
            "clinvar_version": "2025-0504",
            "ensembl_version": "114",
            "gnomad_version": "v4.1.0",
            "sift_version": "5.2.2",
            "dbsnp_version": "b156",
            "gnomad_1KG_version": "v3.1.2",
            "gnomad_constraints_version": "v3.1.2",
            "snp_eff_version": "N/A",
            "snp_sift_version": "N/A",
            "polyphen2_version": "N/A",
            "omim_version": "N/A",
        },
        "report_id": str(uuid.uuid4()),
    }

    generate(**data)
