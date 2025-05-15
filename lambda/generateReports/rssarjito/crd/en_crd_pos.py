import os
import uuid
from datetime import datetime
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


def _write_header_footer(filename, pages, pii_name, pii_dob, pii_gender):
    c = canvas.Canvas(filename, pagesize=letter)
    form = c.acroForm
    fields = [
        # Name
        (186, 670, 135, 12, 12, pii_name, 0),
        # Lab number
        (186, 670 - 14, 135, 12, 12, "", 0),
        # gender
        (186, 670 - 14 * 2, 135, 12, 12, pii_gender, 0),
        # DOB
        (186, 670 - 14 * 3, 135, 12, 12, pii_dob, 0),
        # Race
        (186, 670 - 14 * 4, 135, 12, 12, "", 0),
        # Specimen type
        (186, 670 - 14 * 5, 135, 12, 12, "", 0),
        # Sample Id
        (186, 670 - 14 * 6, 135, 12, 12, "", 0),
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
    c.drawString(72, 551, f"Clinical Information:")
    form.textfield(
        name=f"clinical-info",
        tooltip="",
        value=f"",
        x=188,
        y=540,
        width=372,
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
                borderWidth=0,
                fillColor=colors.white,
                textColor=None,
                borderColor=None,
                forceBorder=False,
                fieldFlags=flags,
            )
        c.setFont("Helvetica", fs)
        c.setFillColor(colors.HexColor("#808080"))
        c.drawString(290, 30, f"Page {page+1} of {pages}")
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
    title = Paragraph("GENOMIC TESTING RESULTS", style=title_style)
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
    sub_title = Paragraph("RESULTS", style=sub_title_style)
    elements.append(sub_title)
    elements.append(Spacer(2, 10))

    # Generate table data
    data = _generate_row_data(header_rows, rows)

    # Create the table with specified column widths
    table = Table(data, colWidths=col_widths)

    # Style the table
    style = TableStyle(
        [
            ("SPAN", (0, 0), (0, 1)),  # Col 1 header spans 2 rows
            ("SPAN", (1, 0), (1, 1)),  # Col 2 header spans 2 rows
            ("SPAN", (2, 0), (2, 1)),  # Col 3 header spans 2 rows
            ("SPAN", (3, 0), (3, 1)),  # Col 4 header spans 2 rows
            ("SPAN", (4, 0), (4, 1)),  # Col 5 header spans 2 rows
            ("SPAN", (5, 0), (6, 0)),  # Col 6 header spans 1 row
            ("SPAN", (7, 0), (7, 1)),  # Col 7 header spans 2 rows
            ("BACKGROUND", (0, 0), (-1, 2), colors.HexColor("#EDF180")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),  # Vertical alignment
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
):
    _text_field_positions_page_1 = [
        # Results Interpretation
        (69, 328, 472, 155, 12, "", 1 << 12),
        # Conclusion
        (69, 190, 472, 61, 12, "", 1 << 12),
        # Recommendation
        (69, 50, 472, 120, 12, "", 1 << 12),
    ]
    _text_field_positions_page_2 = [
        # additional information
        (69, 337, 472, 207, 12, "", 1 << 12),
        # validated by
        (420, 207, 118, 82, 12, "", 0),
    ]
    _text_field_positions_page_3 = []
    _text_field_positions_page_4 = [
        # References
        (91, 63, 445, 330, 12, "", 1 << 12),
    ]
    # static text
    _static_text_page_1 = []
    _static_text_page_2 = []
    _static_text_page_3 = []
    _static_text_page_4 = [
        # OMIM
        (170, 479 - 15, 11, "vOMIM"),
        # ClinVar
        (170, 467 - 15, 11, "vClinvar"),
        # gnomAD
        (170, 455 - 15, 11, "vgnomAD"),
        # dbSNP
        (170, 443 - 15, 11, "vdbSNP"),
        # SIFT
        (170, 431 - 15, 11, "vSIFT"),
        # PolyPhen2
        (170, 419 - 15, 11, "vPolyPhen2"),
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
                borderWidth=0,
                fillColor=colors.white,
                textColor=None,
                forceBorder=False,
                borderColor=None,
                fieldFlags=flags,
            )
        for n, pos in enumerate(page_poses_st):
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


def generate(*, pii_name=None, pii_dob=None, pii_gender=None, variants=None):
    header_rows = [
        [
            "Gene/ Transcript",
            "Variants/ Protein Change",
            "AF",
            "Zygosity",
            "Inheritance/ Associated Phenotype",
            "Computational Prediction",
            "",
            "Variant Classification",
        ],
        ["", "", "", "", "" "", "SIFT", "PP2"],
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
                variant["SIFT (max)"],
                "NA",
                variant["clinSig"],
            ]
        )
    module_dir = Path(__file__).parent
    output_pdf_annotations = "/tmp/annotations.pdf"
    input_pdf_path = f"{module_dir}/EN_Genome Report_Positive_CRD-TABLE.pdf"

    _create_pdf_with_table(
        output_pdf_annotations, header_rows, [80, 68, 60, 55, 93, 37, 37, 83], data
    )
    _overlay_template_with_table(
        output_pdf_annotations, input_pdf_path, "/tmp/overlayed-table.pdf"
    )

    _create_annotations(output_pdf_annotations)
    _overlay_pdf_with_annotations(
        output_pdf_annotations,
        f"{module_dir}/EN_Genome Report_Positive_CRD-REST.pdf",
        "/tmp/overlayed-annot.pdf",
    )

    pdf_table = PdfReader("/tmp/overlayed-table.pdf")
    pdf_rest = PdfReader("/tmp/overlayed-annot.pdf")

    total_pages = len(pdf_table.pages) + len(pdf_rest.pages)

    _write_header_footer(
        output_pdf_annotations, total_pages, pii_name, pii_dob, pii_gender
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
    generate(variants=data, **pii_data)
