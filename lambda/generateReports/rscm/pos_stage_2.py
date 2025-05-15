import os
import uuid
from pathlib import Path
from datetime import datetime

from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors


def _create_annotations(
    filename,
    date_pos,
    name_pos,
    dob_pos,
    rekam_medis_pos,
    gender_pos,
    symptoms_pos,
    versions_pos,
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
        height=fs,
        fontSize=8,
        borderWidth=0,
        fillColor=colors.white,
        textColor=None,
        forceBorder=False,
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
        borderWidth=0,
        fillColor=colors.white,
        textColor=None,
        forceBorder=False,
        fieldFlags=0,
    )

    # rekam medis
    x, y, fs, text = rekam_medis_pos
    form.textfield(
        name="rekam",
        tooltip="Rekam Meidis",
        value=text,
        x=x,
        y=y,
        width=200,
        height=fs,
        fontSize=8,
        borderWidth=0,
        fillColor=colors.white,
        textColor=None,
        forceBorder=False,
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
        borderWidth=0,
        fillColor=colors.white,
        textColor=None,
        forceBorder=False,
    )

    # symptoms
    x, y, fs, text = symptoms_pos
    form.textfield(
        name="symptoms",
        tooltip="Symptoms",
        value=text,
        x=x,
        y=y,
        width=200,
        height=fs,
        fontSize=8,
        fieldFlags=0,
        borderWidth=0,
        fillColor=colors.white,
        textColor=None,
        forceBorder=False,
    )
    c.showPage()
    c.showPage()
    c.showPage()

    for pos in versions_pos:
        x, y, fs, text = pos
        c.setFont("Helvetica", fs)
        c.drawString(x, y, text)

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


def generate(*, pii_name=None, pii_dob=None, pii_gender=None, versions=None):
    assert all([pii_name, pii_dob, pii_gender]), "Missing required fields."

    module_dir = Path(__file__).parent
    output_pdf_path = "/tmp/annotations.pdf"
    input_pdf_path = f"{module_dir}/pos.pdf"

    # x, y, fs, text
    date_pos = (72, 595, 12, f"Date: {datetime.now().strftime('%d %B %Y')}")
    name_pos = (192, 568, 12, pii_name)
    dob_pos = (192, 552, 12, pii_dob)
    rekam_medis_pos = (192, 538, 12, f"")
    gender_pos = (192, 524, 12, pii_gender)
    symptoms_pos = (192, 492, 12, f"")

    # TODO get versions

    versions_pos = [
        # left col
        (180, 570, 12, versions["snp_eff_version"]),
        (180, 556, 12, versions["snp_sift_version"]),
        (180, 542, 12, versions["clinvar_version"]),
        (180, 528, 12, versions["omim_version"]),
        # right col
        (480, 570, 12, versions["gnomad_version"]),
        (480, 556, 12, versions["dbsnp_version"]),
        (480, 542, 12, versions["sift_version"]),
        (480, 528, 12, versions["polyphen2_version"]),
    ]

    _create_annotations(
        output_pdf_path,
        date_pos,
        name_pos,
        dob_pos,
        rekam_medis_pos,
        gender_pos,
        symptoms_pos,
        versions_pos,
    )
    output_file_name = f"/tmp/{uuid.uuid4()}.pdf"
    _overlay_pdf_with_annotations(output_pdf_path, input_pdf_path, output_file_name)
    os.remove(output_pdf_path)

    print(f"Generated Stage 2 PDF: {output_file_name}")
    return output_file_name
