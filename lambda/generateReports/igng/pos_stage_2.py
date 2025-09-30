import os
import uuid
from pathlib import Path
from datetime import datetime, timedelta

from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors


def _create_annotations(
    filename,
    pii_name=None,
    pii_dob=None,
    pii_gender=None,
    versions=None,
    validated_by=None,
    validated_at=None,
    project=None,
    vcf=None,
    qc_note=None,
    result_annotation=None
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
    for ra in result_annotation:
        x, y, fs, text = ra
        c.setFont("Helvetica", fs)
        c.setFillColor(colors.black)
        c.drawString(x, y, text or "")

    # TTD Pemvalidasi
    x, y, fs, text = (356, 330, 12, "")
    form.textfield(
        name="Divalidasi oleh",
        tooltip="Divalidasi oleh",
        value=f"{text}",
        x=x,
        y=y,
        width=150,
        height=80,
        fontSize=8,
        borderWidth=0,
        fillColor=colors.white,
        textColor=None,
        forceBorder=False,
        fieldFlags=1<<12,
    )

    # Nama Pemvalidasi
    x, y, fs, text = (506, 315, 12, validated_by)
    c.setFont("Helvetica", fs)
    text_width = c.stringWidth(text, "Helvetica", fs)
    c.drawString(x - text_width, y, text)

    # Date
    x, y, fs, text = (410, 294, 12, validated_at)
    c.setFont("Helvetica", fs)
    c.drawString(x, y, text)

    c.showPage()

    # Lookup Version
    x, y, fs, text = (150, 136, 11, versions["lookup_version"] or "")
    c.setFont("Helvetica", fs)
    c.drawString(x, y, text),

    c.showPage()


    c.setFont("Helvetica", 11)
    #qc_note
    c.drawString(72, 644, qc_note or "")
    #project
    c.drawString(150, 552, project or "")
    #vcf
    c.drawString(150, 565, vcf or "")

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
    versions=None,
    variant_validations=None,
    project=None,
    vcf=None,
    qc_note=None
):

    validated_by, validated_at = None, None
    result_annotation = []

    if variant_validations:

        result_annotation = [
            (76, (650 - i*13), 11, v.get("validationComment", ""))
            for i, v in enumerate(variant_validations)
        ]
        
        latest_validation = max(
            variant_validations,
            key=lambda v: v.get("validatedAt", "")
        )

        #validated_by
        user = latest_validation.get("user", {})
        full_name = f"{user.get('firstName', '')} {user.get('lastName', '')}".strip()
        validated_by = full_name
        
        #validated_at
        raw_validated_at = latest_validation.get("validatedAt")
        validated_at_str = ""
        if raw_validated_at:
            try:
                dt = datetime.fromisoformat(raw_validated_at)
                dt_local = dt + timedelta(hours=7)
                validated_at_str = dt_local.strftime("%Y-%m-%d %H:%M")
            except Exception as e:
                validated_at_str = str(raw_validated_at)

        validated_at = validated_at_str

    module_dir = Path(__file__).parent
    output_pdf_path = "/tmp/annotations.pdf"
    input_pdf_path = f"{module_dir}/body.pdf"

    _create_annotations(
        output_pdf_path,
        pii_name=pii_name,
        pii_dob=pii_dob,
        pii_gender=pii_gender,
        versions=versions,
        validated_by=validated_by,
        validated_at=validated_at,
        project=project,
        vcf=vcf,
        qc_note=qc_note,
        result_annotation=result_annotation

    )
    output_file_name = f"/tmp/{uuid.uuid4()}.pdf"
    _overlay_pdf_with_annotations(output_pdf_path, input_pdf_path, output_file_name)
    os.remove(output_pdf_path)

    print(f"Generated Stage 2 PDF: {output_file_name}")
    return output_file_name
