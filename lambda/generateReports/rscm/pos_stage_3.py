import os
import uuid

from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from datetime import datetime, timedelta


def _create_annotations(
    filename,
    pages,
    footer_name_pos,
    footer_dob_pos,
    footer_date_pos,
    page_num_pos,
    report_id=None,
    versions_pos=None,
    validated_at=None,
    validated_by=None,
    project_value=None,
    vcf_value=None,
    result_annotation=None,
):
    c = canvas.Canvas(filename, pagesize=letter)
    text_color = colors.HexColor("#156082")
    form = c.acroForm
    
    for p in range(pages):
        # report_id di header
        x, y, fs, text = (5, 778, 11, report_id or "")
        c.setFont("Helvetica", fs)
        c.drawString(x, y, text)

        if p == pages - 2:
            for pos in versions_pos:
                x, y, fs, text = pos
                c.setFont("Helvetica", fs)
                c.drawString(x, y, text or "")
            
            x, y, fs, text = validated_at
            c.setFont("Helvetica", fs)
            c.setFillColor(colors.black)
            c.drawString(x, y, text or "")

            x, y, fs, text = validated_by
            c.setFont("Helvetica", fs)
            c.setFillColor(colors.black)
            c.drawString(x, y, text or "")

        if p == pages - 1:
            #project
            x, y, fs, text = project_value
            c.setFont("Helvetica", fs)
            c.setFillColor(colors.black)
            c.drawString(x, y, text or "")

            #vcf
            x, y, fs, text = vcf_value
            c.setFont("Helvetica", fs)
            c.setFillColor(colors.black)
            c.drawString(x, y, text or "")

            for ra in result_annotation:
                x, y, fs, text = ra
                c.setFont("Helvetica", fs)
                c.setFillColor(colors.black)
                c.drawString(x, y, text or "")

        # footer name
        x, y, fs, text = footer_name_pos
        form.textfield(
            name="name",
            tooltip="Name",
            value=f"{text}",
            x=x,
            y=y,
            width=160,
            height=11,
            fontSize=fs,
            borderWidth=0,
            fillColor=colors.white,
            textColor=text_color,
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
            width=160,
            height=11,
            fontSize=fs,
            borderWidth=0,
            fillColor=colors.white,
            textColor=text_color,
            forceBorder=False,
            fieldFlags=0,
        )

        # footer date
        x, y, fs, text = footer_date_pos
        c.setFont("Helvetica", fs)
        c.setFillColor(text_color)
        c.drawString(x, y, text or "")

        # page num
        x, y = page_num_pos
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.HexColor("#156082"))
        c.drawString(x, y, f"Page {p+1} of {pages}")

        c.showPage()
    c.save()


def generate(
    summary_pdf,
    results_pdf,
    annots_pdf,
    *,
    pii_name=None,
    pii_dob=None,
    report_id=None,
    versions=None,
    variant_validations=None,
    project=None,
    vcf=None,
    user=None
):
    validated_by, validated_at = None, None
    result_annotation = []


    #validated_by
    full_name = f"{user.get('firstName', '')} {user.get('lastName', '')}".strip()
    validated_by = (205, 150, 11, full_name)

    if variant_validations:

        result_annotation = [
            (72, (442 - i*13), 11, v.get("validationComment", ""))
            for i, v in enumerate(variant_validations)
            if v.get("validationComment")
        ]
        
        latest_validation = max(
            variant_validations,
            key=lambda v: v.get("validatedAt", "")
        )
        
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

        validated_at = (205, 136, 11, validated_at_str)


    # x, y, fs, text
    footer_name_pos = (148, 72, 10, "")
    footer_dob_pos = (148, 58, 10, "")
    footer_date_pos = (158, 47, 10, datetime.now().strftime('%Y-%m-%d'))
    page_num_pos = (490, 70)

    output_pdf_path = "/tmp/annotations.pdf"
    pdf_int = PdfReader(annots_pdf)
    pdf_summary = PdfReader(summary_pdf)
    pdf_results = PdfReader(results_pdf)

    total_pages = len(pdf_int.pages) + len(pdf_results.pages) + len(pdf_summary.pages)

    versions_pos = [
        (184, 353, 11, versions["clinvar_version"]),
        (184, 339, 11, versions["gnomad_version"]),
        (184, 325, 11, versions["dbsnp_version"]),
        (184, 311, 11, versions["sift_version"]),
    ]

    vcf_value = (72, 550, 12, vcf)
    project_value = (72, 505, 12, project)

    _create_annotations(
        output_pdf_path,
        total_pages,
        footer_name_pos,
        footer_dob_pos,
        footer_date_pos,
        page_num_pos,
        report_id,
        versions_pos,
        validated_at,
        validated_by,
        project_value,
        vcf_value,
        result_annotation,
    )

    writer = PdfWriter()
    pages = []

    # urutan pages
    pages.append(pdf_int.pages[0])
    pages += pdf_summary.pages
    pages.append(pdf_int.pages[1])
    pages += pdf_results.pages
    pages += pdf_int.pages[2:]

    # merge annotations (footer & pagenum)
    footer_pagenum_annotations = PdfReader(output_pdf_path)

    for n, page in enumerate(pages):
        page.merge_page(footer_pagenum_annotations.pages[n])
        writer.add_page(page)

    output_file_name = f"/tmp/{str(uuid.uuid4())}.pdf"
    with open(output_file_name, "wb") as f:
        writer.write(f)

    os.remove(output_pdf_path)
    print(f"Generated Stage 3 PDF: {output_file_name}")
    return output_file_name
