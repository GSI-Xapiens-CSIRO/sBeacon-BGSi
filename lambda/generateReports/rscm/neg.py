import os
from datetime import datetime
from pathlib import Path

from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors


def _create_annotations(
    date_pos,
    name_pos,
    dob_pos,
    rekam_medis_pos,
    gender_pos,
    symptoms_pos,
    footer_name_pos,
    footer_dob_pos,
    filename,
):
    c = canvas.Canvas(filename, pagesize=letter)
    form = c.acroForm

    # date
    x, y, fs, text = date_pos
    c.setFont("Helvetica-Bold", fs)
    c.drawString(x, y, text)

    # name
    x, y, fs, text = name_pos
    form.textfield(
        name="name",
        tooltip="Name",
        value=f"{text}",
        x=x,
        y=y,
        width=100,
        height=12,
        fontSize=8,
        fillColor=colors.white,
        fieldFlags=0,
    )

    # dob
    x, y, fs, text = dob_pos
    form.textfield(
        name="dob",
        tooltip="Date of Birth",
        value=f"{text}",
        x=x,
        y=y,
        width=100,
        height=12,
        fontSize=8,
        fillColor=colors.white,
        fieldFlags=0,
    )

    # rekam medis
    x, y, fs, text = rekam_medis_pos
    form.textfield(
        name="rekam",
        tooltip="Rekam Meidis",
        value="",
        x=x,
        y=y,
        width=200,
        height=12,
        fontSize=8,
        fillColor=colors.white,
        fieldFlags=0,
    )

    # gender
    x, y, fs, text = gender_pos
    form.choice(
        name="gender",
        tooltip="Gender",
        value=text,
        x=x,
        y=y,
        width=100,
        height=13,
        fontName="Helvetica",
        fontSize=8,
        options=[("Male", "male"), ("Female", "female")],
    )

    # symptoms
    x, y, fs, text = symptoms_pos
    form.textfield(
        name="symptoms",
        tooltip="Symptoms",
        value="",
        x=x,
        y=y,
        width=200,
        height=12,
        fontSize=8,
        fillColor=colors.white,
        fieldFlags=0,
    )

    for _ in range(3):
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
    assert all([pii_name, pii_dob, pii_gender]), "Missing required fields."

    module_dir = Path(__file__).parent
    output_pdf_path = "/tmp/annotations.pdf"
    input_pdf_path = f"{module_dir}/neg.pdf"

    # x, y, w, h, text
    date_pos = (72, 595, 12, f"Date: {datetime.now().strftime('%d %B %Y')}")
    name_pos = (192, 568, 12, pii_name)
    dob_pos = (192, 552, 12, pii_dob)
    rekam_medis_pos = (192, 538, 12, f"")
    gender_pos = (192, 524, 12, pii_gender)
    symptoms_pos = (192, 492, 12, f"")
    footer_name_pos = (146, 50, 12, pii_name)
    footer_dob_pos = (146, 38, 12, pii_dob)

    _create_annotations(
        date_pos,
        name_pos,
        dob_pos,
        rekam_medis_pos,
        gender_pos,
        symptoms_pos,
        footer_name_pos,
        footer_dob_pos,
        output_pdf_path,
    )
    _overlay_pdf_with_annotations(
        output_pdf_path, input_pdf_path, "/tmp/annotated_neg.pdf"
    )
    os.remove(output_pdf_path)
    print("PDF created successfully with new content drawn on it.")
    return "/tmp/annotated_neg.pdf"


if __name__ == "__main__":
    generate(pii_name="John Doe", pii_dob="01/01/1990", pii_gender="Male")
