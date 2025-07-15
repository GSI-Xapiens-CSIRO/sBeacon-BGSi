import os
import uuid
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
    versions,
    report_id,
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
        width=200,
        height=12,
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
        value="",
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
        value="",
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

    for n in range(3):
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
        if n == 2:
            versions_pos = [
                # left col
                (180, 570 + 15, 11, versions["snp_eff_version"]),
                (180, 556 + 15, 11, versions["snp_sift_version"]),
                (180, 542 + 15, 11, versions["clinvar_version"]),
                (180, 528 + 15, 11, versions["omim_version"]),
                # right col
                (450 - 20, 570 + 15, 11, versions["gnomad_version"]),
                (450 - 20, 556 + 15, 11, versions["dbsnp_version"]),
                (450 - 20, 542 + 15, 11, versions["sift_version"]),
                (450 - 20, 528 + 15, 11, versions["polyphen2_version"]),
            ]
            for pos in versions_pos:
                x, y, fs, text = pos
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
    *, pii_name=None, pii_dob=None, pii_gender=None, versions=None, report_id=None
):
    module_dir = Path(__file__).parent
    output_pdf_path = "/tmp/annotations.pdf"
    input_pdf_path = f"{module_dir}/neg.pdf"

    # x, y, h, text
    date_pos = (72, 595, 12, f"Date: {datetime.now().strftime('%d %B %Y')}")
    name_pos = (192, 564, 12, pii_name)
    dob_pos = (192, 550, 12, pii_dob)
    rekam_medis_pos = (192, 538, 12, f"")
    gender_pos = (192, 524, 12, pii_gender)
    symptoms_pos = (192, 492, 12, f"")
    footer_name_pos = (146, 48, 12, pii_name)
    footer_dob_pos = (146, 36, 12, pii_dob)

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
        versions,
        report_id,
    )
    output_file_name = f"/tmp/{str(uuid.uuid4())}.pdf"
    _overlay_pdf_with_annotations(output_pdf_path, input_pdf_path, output_file_name)
    os.remove(output_pdf_path)

    print(f"Generated report: {output_file_name}")
    return output_file_name


if __name__ == "__main__":
    generate(
        pii_name="John Doe",
        pii_dob="01/01/1990",
        pii_gender="Male",
        versions={
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
        report_id=str(uuid.uuid4()),
    )
