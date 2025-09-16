import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple
from copy import deepcopy

from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT


def _write_header_footer(filename, pages, pii_name, pii_dob, pii_gender, report_id):
    c = canvas.Canvas(filename, pagesize=letter)
    form = c.acroForm
    fields = [
        # Name
        (150, 670, 135, 12, 12, pii_name, 0),
        # Lab number
        (150, 670 - 14, 135, 12, 12, "", 0),
        # gender
        (150, 670 - 14 * 2, 135, 12, 12, pii_gender, 0),
        # DOB
        (150, 670 - 14 * 3, 135, 12, 12, pii_dob, 0),
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
        (438, 670 - 14 * 3, 135, 12, 12, datetime.now().strftime("%d/%m/%Y"), 0),
        # Referring institution
        (438, 670 - 14 * 4, 135, 12, 12, "", 0),
        # Testing lab
        (438, 670 - 14 * 5, 135, 12, 12, "", 0),
    ]

    c.setFont("Helvetica", 12)
    form.textfield(
        name=f"clinical-info",
        tooltip="",
        value=f"",
        x=150,
        y=540,
        width=400,
        height=35,
        fontSize=12 - 2,
        borderWidth=0,
        fillColor=colors.white,
        textColor=None,
        borderColor=None,
        forceBorder=False,
        fieldFlags=1 << 12,
    )

    for page in range(pages):
        x, y, fs, text = (5, 780, 12, report_id)
        c.setFont("Helvetica", fs)
        c.drawString(x, y, text)
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
                fillColor=colors.white,
                textColor=None,
                borderColor=None,
                forceBorder=False,
                fieldFlags=flags,
            )
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.HexColor("#808080"))
        c.drawString(270, 40, f"Halaman {page+1} dari {pages}")
        c.showPage()
    c.save()


def _generate_row_data(
    header_rows: List[List[str]], rows: List[Tuple[str]]
) -> List[List[Paragraph]]:
    styles = getSampleStyleSheet()
    # Create a paragraph style for table cells with wrapping text
    cell_style = ParagraphStyle(
        "CellStyle",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        wordWrap="CJK",
    )
    header_style = ParagraphStyle(
        "CellStyle",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        # wordWrap="CJK",
        fontName="Helvetica-Bold",
        textColor=colors.black,
    )

    # Format headers as Paragraph objects
    header_rows = [
        [Paragraph(header, header_style) for header in headers]
        for headers in header_rows
    ]
    data = [*header_rows]

    # Generate rows
    for row in rows:
        row_data = []
        for text in row:
            p = Paragraph(text, cell_style)
            row_data.append(p)

        data.append(row_data)

    return data


def _create_pdf_with_table(
    filename: str, header_rows: List[str], col_widths: List[int], rows: List[Tuple[str]]
):
    """Create a PDF with a table that has wrapped text"""
    # Create a document template with specified margins
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=70,
        leftMargin=70,
        topMargin=210,
        bottomMargin=70,  # 70 pts bottom margin as requested
    )

    styles = getSampleStyleSheet()
    # Container for the 'flowable' elements
    elements = []

    # Add a title
    title_style = ParagraphStyle(
        "Title",
        parent=styles["h2"],
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
    )
    title = Paragraph("HASIL PEMERIKSAAN GENOMIK", style=title_style)
    elements.append(Spacer(2, 25))
    elements.append(title)
    elements.append(Spacer(2, 10))
    sub_title_style = ParagraphStyle(
        "SubTitle",
        parent=styles["Normal"],
        alignment=TA_LEFT,
        fontName="Helvetica-Bold",
        fontSize=14,
    )
    sub_title = Paragraph("HASIL", style=sub_title_style)
    elements.append(sub_title)
    elements.append(Spacer(2, 10))

    # Generate table data
    data = _generate_row_data(header_rows, rows)

    # Create the table with specified column widths
    table = Table(data, colWidths=col_widths)

    # Style the table
    style = TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDF180")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ]
    )
    table.setStyle(style)

    # Add alternating row colors
    for i in range(2, len(data)):
        if i % 2 == 1:
            bc = colors.whitesmoke
        else:
            bc = colors.white
        style = TableStyle([("BACKGROUND", (0, i), (-1, i), bc)])
        table.setStyle(style)

    elements.append(table)

    # Build the PDF
    doc.build(elements)


def _overlay_template_with_table(src, dest, output):
    # Open the existing PDF and the newly created PDF
    annotations_pdf = PdfReader(src)
    template_pdf = PdfReader(dest)

    # Create a PDF writer for the output PDF
    writer = PdfWriter()

    # Get page from template, and overlay with table
    for page_number in range(len(annotations_pdf.pages)):
        page = deepcopy(template_pdf.pages[0])
        overlay_page = annotations_pdf.pages[page_number]
        page.merge_page(overlay_page)
        writer.add_page(page)

    # Write the merged PDF to a file
    with open(output, "wb") as f:
        writer.write(f)


def _create_annotations(
    filename,
    versions,
    project,
    vcf,
    validated_by,
    validated_at,
    qc_note,
    result_annotation
):
    _text_field_positions_page_1 = [
        # Recommendation
        (69, 110, 472, 120, 12, "", 1 << 12),
    ]
    _text_field_positions_page_2 = [
        # validated by
        (420, 206, 118, 82, 12, "", 0),
    ]
    _text_field_positions_page_3 = []
    _text_field_positions_page_4 = [
        # References
        (91, 63, 445, 290, 12, "", 1 << 12),
    ]
    _text_field_positions_page_5 = [
    ]

    # static text
    _static_text_page_1 = [
        (x, y, fs,align_right, text)
        for x, y, fs, align_right, text in result_annotation
    ]
    _static_text_page_2 = [
        (74, 486, 11, False, qc_note),
        (538, 193, 11, True, validated_by),
        (538, 161, 11, True,  validated_at),
    ]
    _static_text_page_3 = []
    _static_text_page_4 = [
        # ClinVar
        (170, 479 - 53, 11, False, versions["clinvar_version"]),
        # gnomAD
        (170, 467 - 53, 11, False, versions["gnomad_version"]),
        # dbSNP
        (170, 455 - 53, 11, False, versions["dbsnp_version"]),
        # SIFT
        (170, 443 - 53, 11, False, versions["sift_version"]),
    ]
    _static_text_page_5 = [
        (170, 538, 11, False, vcf),
        (170, 526, 11, False, project),
    ]

    c = canvas.Canvas(filename, pagesize=letter)
    form = c.acroForm
    unique_counter = 0

    for page_poses_tf, page_poses_st in [
        (_text_field_positions_page_1, _static_text_page_1),
        (_text_field_positions_page_2, _static_text_page_2),
        (_text_field_positions_page_3, _static_text_page_3),
        (_text_field_positions_page_4, _static_text_page_4),
        (_text_field_positions_page_5, _static_text_page_5),
    ]:
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
                fillColor=colors.white,
                textColor=None,
                forceBorder=False,
                borderColor=None,
                fieldFlags=flags,
            )
            unique_counter += 1
        for n, pos in enumerate(page_poses_st):
            x, y, fs, align_right, text = pos
            c.setFont("Helvetica", fs)
            if align_right:
                if text is None:
                    text = ""
                text_width = c.stringWidth(str(text), "Helvetica", fs)
                c.drawString(x - text_width, y, str(text))
            else:
                if text is None:
                    text = ""
                c.drawString(x, y, str(text))

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
    *,
    pii_name=None,
    pii_dob=None,
    pii_gender=None,
    pii_rekam_medis=None,
    pii_clinical_diagnosis=None,
    pii_symptoms=None,
    pii_physician=None,
    pii_genetic_counselor=None,
    variants=None,
    versions=None,
    report_id=None,
    project=None,
    vcf=None,
    variant_validations=None,
    qc_note=None
):
    header_rows = [
        [
            "Gen/ Transkrip",
            "Varian/ Protein",
            "AF",
            "Zigositas",
            "Pewarisan/ Fenotipe Terkait",
            "Prediksi Komputasi(SIFT)",
            "Klasifikasi Varian",
        ],
    ]

    data = []
    for variant in variants:
        variant_protein_change = variant["Variant Name"]
        gene_transcript = (
            variant["Gene Name"] + "/ " + variant["Transcript ID & Version"]
        )
        gt = variant["gt"]
        if gt == "0/0":
            genotype = "Hom(ref)"
        elif gt == "1/1":
            genotype = "Hom(alt)"
        else:
            genotype = "Het"
        data.append(
            [
                gene_transcript,
                variant_protein_change,
                variant["Allele Frequency (Global)"],
                genotype,
                "-/ " + variant["conditions"],
                variant["SIFT (max)"],  # langsung masuk ke kolom Computational Prediction (SIFT)
                variant["clinSig"],
            ]
        )
    
    validated_by, validated_at = None, None
    result_annotation = []

    if variant_validations:

        result_annotation = [
            (74, (472 - i*13), 11, False, v.get("validationComment", ""))
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
    output_pdf_annotations = "/tmp/annotations.pdf"
    input_pdf_path = f"{module_dir}/ID_Genome Report_Positive-TABLE.pdf"

    _create_pdf_with_table(
        output_pdf_annotations, header_rows, [80, 68, 60, 55, 93, 60, 83], data
    )
    _overlay_template_with_table(
        output_pdf_annotations, input_pdf_path, "/tmp/overlayed-table.pdf"
    )

    _create_annotations(output_pdf_annotations, versions, project, vcf, validated_by, validated_at, qc_note, result_annotation)
    _overlay_pdf_with_annotations(
        output_pdf_annotations,
        f"{module_dir}/ID_Genome Report_Positive-REST.pdf",
        "/tmp/overlayed-annot.pdf",
    )

    pdf_table = PdfReader("/tmp/overlayed-table.pdf")
    pdf_rest = PdfReader("/tmp/overlayed-annot.pdf")

    total_pages = len(pdf_table.pages) + len(pdf_rest.pages)

    _write_header_footer(
        output_pdf_annotations, total_pages, pii_name, pii_dob, pii_gender, report_id
    )

    footer_pagenum_annotations = PdfReader(output_pdf_annotations)

    pages = []
    pages += pdf_table.pages
    pages += pdf_rest.pages

    writer = PdfWriter()

    for n, page in enumerate(pages):
        page.merge_page(footer_pagenum_annotations.pages[n])
        writer.add_page(page)

    output_file_name = f"/tmp/{uuid.uuid4()}.pdf"
    with open(output_file_name, "wb") as f:
        writer.write(f)

    os.remove("/tmp/overlayed-table.pdf")
    os.remove("/tmp/overlayed-annot.pdf")
    os.remove(output_pdf_annotations)

    print(f"Generated report: {output_file_name}")
    return output_file_name


if __name__ == "__main__":
    data = [
        {
            "Variant Name": "NM_000367.5(TPMT):c.719A>G (p.Tyr240Cys)",
            "gt": "0/0",
            "clinSig": "drug response",
            "conditions": "Thiopurine S-methyltransferase deficiency",
            "SIFT (max)": "0",
            "Allele Frequency (Global)": "0.0431942",
            "Gene Name": "TPMT",
            "Transcript ID & Version": "ENST00000309983.5",
            "Amino Acid Change": "Y/C",
        },
        {
            "Variant Name": "NM_000367.5(TPMT):c.719A>G (p.Tyr240Cys)",
            "gt": "0/0",
            "clinSig": "Likely benign; other",
            "conditions": "not provided",
            "SIFT (max)": "0",
            "Allele Frequency (Global)": "0.0431942",
            "Gene Name": "TPMT",
            "Transcript ID & Version": "ENST00000309983.5",
            "Amino Acid Change": "Y/C",
        },
        {
            "Variant Name": "NM_000367.5(TPMT):c.719A>G (p.Tyr240Cys)",
            "gt": "0/0",
            "clinSig": "drug response",
            "conditions": "Thiopurine S-methyltransferase deficiency",
            "SIFT (max)": "0",
            "Allele Frequency (Global)": "0.0431942",
            "Gene Name": "-",
            "Transcript ID & Version": "ENST00000830125.1",
            "Amino Acid Change": "-",
        },
    ]
    pii_data = {"pii_name": "John Doe", "pii_dob": "01/01/2000", "pii_gender": "Male"}
    versions = {
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
    }

    generate(variants=data, **pii_data, versions=versions, report_id=str(uuid.uuid4()))
