import os
import uuid
from pathlib import Path
from datetime import datetime

from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors


def _create_annotations(
    filename, pii_name=None, pii_dob=None, pii_gender=None, versions=None
):
    c = canvas.Canvas(filename, pagesize=A4)
    form = c.acroForm

    # INFORMASI KLINIS
    x, y, fs, text = (68, 538, 12, "")
    form.textfield(
        name="INFORMASI KLINIS",
        tooltip="INFORMASI KLINIS",
        value=f"{text}",
        x=x,
        y=y,
        width=463,
        height=129,
        fontSize=8,
        borderWidth=0,
        fillColor=colors.white,
        textColor=None,
        forceBorder=False,
        fieldFlags=1<<12,
    )
    c.showPage()

    # REKOMENDASI PRESKRIPSI
    x, y, fs, text = (68, 446, 12, "")
    form.textfield(
        name="REKOMENDASI PRESKRIPSI",
        tooltip="REKOMENDASI PRESKRIPSI",
        value=f"{text}",
        x=x,
        y=y,
        width=463,
        height=222,
        fontSize=8,
        borderWidth=0,
        fillColor=colors.white,
        textColor=None,
        forceBorder=False,
        fieldFlags=1<<12,
    )

    # Divalidasi oleh
    x, y, fs, text = (275, 214, 12, "")
    form.textfield(
        name="Divalidasi oleh",
        tooltip="Divalidasi oleh",
        value=f"{text}",
        x=x,
        y=y,
        width=254,
        height=208,
        fontSize=8,
        borderWidth=0,
        fillColor=colors.white,
        textColor=None,
        forceBorder=False,
        fieldFlags=1<<12,
    )

    # Date
    x, y, fs, text = (365, 197, 12, datetime.now().strftime("%d/%m/%Y"))
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


def generate(*, pii_name=None, pii_dob=None, pii_gender=None, versions=None):
    module_dir = Path(__file__).parent
    output_pdf_path = "/tmp/annotations.pdf"
    input_pdf_path = f"{module_dir}/body.pdf"

    _create_annotations(
        output_pdf_path,
        pii_name=pii_name,
        pii_dob=pii_dob,
        pii_gender=pii_gender,
        versions=versions,
    )
    output_file_name = f"/tmp/{uuid.uuid4()}.pdf"
    _overlay_pdf_with_annotations(output_pdf_path, input_pdf_path, output_file_name)
    os.remove(output_pdf_path)

    print(f"Generated Stage 2 PDF: {output_file_name}")
    return output_file_name
