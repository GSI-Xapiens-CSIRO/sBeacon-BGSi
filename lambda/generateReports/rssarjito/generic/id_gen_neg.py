import os
import uuid

from PyPDF2 import PdfReader, PdfWriter
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors


def _write_header(c, form):
    fields = [
        # Name
        (150, 670, 135, 12, 12, "", 0),
        # Lab number
        (150, 670 - 14, 135, 12, 12, "", 0),
        # gender
        (150, 670 - 14 * 2, 135, 12, 12, "", 0),
        # DOB
        (150, 670 - 14 * 3, 135, 12, 12, "", 0),
        # Race
        (150, 670 - 14 * 4, 135, 12, 12, "", 0),
        # Specimen type
        (150, 670 - 14 * 5, 135, 12, 12, "", 0),
        # Sample Id
        (150, 670 - 14 * 6, 135, 12, 12, "", 0),
        # Referring clinician
        (438, 670, 135, 12, 12, "", 0),
        # Sampling date
        (438, 670 - 14, 135, 12, 12, "", 0),
        # Testing Date
        (438, 670 - 14 * 2, 135, 12, 12, "", 0),
        # Reporting Date
        (438, 670 - 14 * 3, 135, 12, 12, "", 0),
        # Referring institution
        (438, 670 - 14 * 4, 135, 12, 12, "", 0),
        # Testing lab
        (438, 670 - 14 * 5, 135, 12, 12, "", 0),
    ]

    for n, pos in enumerate(fields):
        x, y, w, h, fs, text, flags = pos
        c.setFont("Helvetica", fs)
        form.textfield(
            name=f"name-{n}",
            tooltip="",
            value=f"{text}",
            x=x,
            y=y,
            width=w,
            height=h,
            fontSize=fs - 2,
            fillColor=colors.white,
            fieldFlags=flags,
        )


def _create_annotations(
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
        (91, 63, 445, 300, 12, "", 1 << 12),
    ]
    # static text
    _static_text_page_1 = []
    _static_text_page_2 = []
    _static_text_page_3 = []
    _static_text_page_4 = [
        # OMIM
        (170, 479 - 52, 11, "vOMIM"),
        # ClinVar
        (170, 467 - 52, 11, "vClinvar"),
        # gnomAD
        (170, 455 - 52, 11, "vgnomAD"),
        # dbSNP
        (170, 443 - 52, 11, "vdbSNP"),
        # SIFT
        (170, 431 - 52, 11, "vSIFT"),
        # PolyPhen2
        (170, 419 - 52, 11, "vPolyPhen2"),
    ]

    c = canvas.Canvas(filename, pagesize=letter)
    form = c.acroForm

    for page_poses_tf, page_poses_st in [
        (_text_field_positions_page_1, _static_text_page_1),
        (_text_field_positions_page_2, _static_text_page_2),
        (_text_field_positions_page_3, _static_text_page_3),
        (_text_field_positions_page_4, _static_text_page_4),
    ]:
        for n, pos in enumerate(page_poses_tf):
            x, y, w, h, fs, text, flags = pos
            c.setFont("Helvetica", fs)
            form.textfield(
                name=f"name-{n}",
                tooltip="",
                value=f"{text}",
                x=x,
                y=y,
                width=w,
                height=h,
                fontSize=fs - 2,
                fillColor=colors.white,
                fieldFlags=flags,
            )
        for n, pos in enumerate(page_poses_st):
            x, y, fs, text = pos
            c.setFont("Helvetica", fs)
            c.drawString(x, y, text)
        _write_header(c, form)
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


def generate(*, pii_name=None, pii_dob=None, pii_gender=None):
    module_dir = Path(__file__).parent
    output_file_name = f"/tmp/{uuid.uuid4()}.pdf"
    _create_annotations("/tmp/annotations.pdf")
    _overlay_pdf_with_annotations(
        "/tmp/annotations.pdf",
        f"{module_dir}/ID_Genome Report_No Finding-GENERIC.pdf",
        output_file_name,
    )
    os.remove("/tmp/annotations.pdf")

    print(f"Generated report: {output_file_name}")
    return output_file_name


if __name__ == "__main__":
    generate()
