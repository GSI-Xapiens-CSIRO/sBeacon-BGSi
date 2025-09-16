import os
import uuid
from pathlib import Path

from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors


def clear_area(c, x, y, width=220, height=15, color=colors.white):
    c.setFillColor(color)
    c.rect(x, y, width, height, fill=1, stroke=0)
    c.setFillColor(colors.black)

def _create_annotations(
    filename,
    name_pos,
    dob_pos,
    rekam_medis_pos,
    gender_pos,
    symptoms_pos,
    clinical_diagnosis_pos,
    physician_pos,
    genetic_counselor_pos
):
    c = canvas.Canvas(filename, pagesize=letter)
    form = c.acroForm

    # Clinical Diagnosis
    x, y, fs, text = clinical_diagnosis_pos
    c.setFont("Helvetica", fs)
    c.setFillColor(colors.black)
    c.drawString(x, y, text or "")

    # Physician
    x, y, fs, text = physician_pos
    c.setFont("Helvetica", fs)
    c.setFillColor(colors.black)
    c.drawString(x, y, text or "")

    # Genetic Counselor
    x, y, fs, text = genetic_counselor_pos
    c.setFont("Helvetica", fs)
    c.setFillColor(colors.black)
    c.drawString(x, y, text or "")

    # name
    x, y, fs, text = name_pos
    form.textfield(
        name="name",
        tooltip="Name",
        value=f"{text}",
        x=x,
        y=y,
        width=220,
        height=13,
        fontSize=fs,
        borderWidth=0,
        fillColor=colors.white,
        textColor=None,
        forceBorder=False,
        fieldFlags=0,
    )

    #dob
    x, y, fs, text = dob_pos
    form.textfield(
        name="dob",
        tooltip="Date of Birth",
        value=f"{text}",
        x=x,
        y=y,
        width=220,
        height=13,
        fontSize=fs,
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
        width=220,
        height=13,
        fontSize=fs,
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
        width=220,
        height=13,
        fontName="Helvetica",
        fontSize=fs,
        options=["Male", "Female"],
        borderWidth=0,
        fillColor=colors.white,
        textColor=None,
        forceBorder=False,
        fieldFlags=0,
    )

    # symptoms
    x, y, fs, text = symptoms_pos
    form.textfield(
        name="symptoms",
        tooltip="Symptoms",
        value=text,
        x=x,
        y=y,
        width=220,
        height=13,
        fontSize=fs,
        fieldFlags=0,
        borderWidth=0,
        fillColor=colors.white,
        textColor=None,
        forceBorder=False,
    )

    c.save()


def _overlay_pdf_with_annotations(src, dest, output):
    annotations_pdf = PdfReader(src)
    template_pdf = PdfReader(dest)

    writer = PdfWriter()
    for page_number in range(len(template_pdf.pages)):
        page = template_pdf.pages[page_number]
        if page_number < len(annotations_pdf.pages):
            overlay_page = annotations_pdf.pages[page_number]
            page.merge_page(overlay_page)
        writer.add_page(page)

    with open(output, "wb") as f:
        writer.write(f)


def generate(
    *,
    pii_name=None,
    pii_dob=None,
    pii_gender=None,
    pii_rekam_medis=None,
    pii_symptoms=None,
    pii_clinical_diagnosis=None,
    pii_physician=None,
    pii_genetic_counselor=None
):
    module_dir = Path(__file__).parent
    output_pdf_path = "/tmp/annotations.pdf"
    input_pdf_path = f"{module_dir}/pos.pdf"

    # positions
    name_pos = (192, 568, 12, "")
    dob_pos = (192, 552, 12, "")
    rekam_medis_pos = (192, 538, 12, "")
    gender_pos = (192, 524, 12, "Male")
    clinical_diagnosis_pos = (192, 510, 12, "Familial Hypercholesterolemia (FH)")
    symptoms_pos = (192, 494, 12, "")
    physician_pos = (192, 480, 12, "dr. Dicky Tahapary, SpPD-KEMD., PhD")
    genetic_counselor_pos = (192, 464, 12, "dr. Widya Eka Nugraha, M.Si. Med.")

    _create_annotations(
        output_pdf_path,
        name_pos,
        dob_pos,
        rekam_medis_pos,
        gender_pos,
        symptoms_pos,
        clinical_diagnosis_pos,
        physician_pos,
        genetic_counselor_pos
    )

    output_file_name = f"/tmp/{uuid.uuid4()}.pdf"
    _overlay_pdf_with_annotations(output_pdf_path, input_pdf_path, output_file_name)
    os.remove(output_pdf_path)

    print(f"Generated Stage 2 PDF: {output_file_name}")
    return output_file_name
