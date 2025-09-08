import os
import uuid
from pathlib import Path
from datetime import datetime

from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors


def clear_area(c, x, y, width=200, height=15, color=colors.white):
    c.setFillColor(color)
    c.rect(x, y, width, height, fill=1, stroke=0)
    c.setFillColor(colors.black)

def _create_annotations(
    filename,
    date_pos,
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

    # Date (tetap ada label)
    x, y, fs, text = date_pos
    c.setFont("Helvetica-Bold", fs)
    c.drawString(x, y, text or "")

    # Clinical Diagnosis
    x, y, fs, text = clinical_diagnosis_pos
    clear_area(c, x, y - 2, width=250, height=16)
    c.setFont("Helvetica", fs)
    c.setFillColor(colors.black)
    c.drawString(x, y, text or "")

    # Physician
    x, y, fs, text = physician_pos
    clear_area(c, x, y - 2, width=250, height=16)
    c.setFont("Helvetica", fs)
    c.setFillColor(colors.black)
    c.drawString(x, y, text or "")

    # Genetic Counselor
    x, y, fs, text = genetic_counselor_pos
    clear_area(c, x, y - 2, width=250, height=16)
    c.setFont("Helvetica", fs)
    c.setFillColor(colors.black)
    c.drawString(x, y, text or "")

    # Name (hanya value)
    x, y, fs, text = name_pos
    c.setFont("Helvetica", fs)
    c.drawString(x, y, text or "")

    # DOB
    x, y, fs, text = dob_pos
    c.setFont("Helvetica", fs)
    c.drawString(x, y, text or "")

    # Rekam Medis
    x, y, fs, text = rekam_medis_pos
    c.setFont("Helvetica", fs)
    c.drawString(x, y, text or "")

    # Gender
    x, y, fs, text = gender_pos
    c.setFont("Helvetica", fs)
    c.drawString(x, y, text or "")

    # Symptoms
    x, y, fs, text = symptoms_pos
    c.setFont("Helvetica", fs)
    c.drawString(x, y, text or "")

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
    date_pos = (72, 595, 12, f"Date: {datetime.now().strftime('%d %B %Y')}")
    name_pos = (192, 568, 12, pii_name)
    dob_pos = (192, 552, 12, pii_dob)
    rekam_medis_pos = (192, 538, 12, pii_rekam_medis)
    gender_pos = (192, 524, 12, pii_gender)
    clinical_diagnosis_pos = (192, 510, 12, pii_clinical_diagnosis)
    symptoms_pos = (192, 494, 12, pii_symptoms)
    physician_pos = (192, 480, 12, pii_physician)
    genetic_counselor_pos = (192, 464, 12, pii_genetic_counselor)

    _create_annotations(
        output_pdf_path,
        date_pos,
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
