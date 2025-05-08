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


def _generate_row_data(
    headers: List[str], rows: List[Tuple[str]]
) -> List[List[Paragraph]]:
    """Generate sample data for our table with some longer text entries"""
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
        wordWrap="CJK",
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#156082"),
    )

    # Format headers as Paragraph objects
    header_row = [Paragraph(header, header_style) for header in headers]
    data = [header_row]

    # Generate rows
    for row in rows:
        row_data = []
        for text in row:
            p = Paragraph(text, cell_style)
            row_data.append(p)

        data.append(row_data)

    return data


def _create_pdf_with_table_vs(
    filename: str, headers: List[str], rows: List[Tuple[str]]
):
    """Create a PDF with a table that has wrapped text"""
    # Create a document template with specified margins
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=70,
        leftMargin=70,
        topMargin=195,  # 195 pts top margin as requested
        bottomMargin=70,  # 70 pts bottom margin as requested
    )

    styles = getSampleStyleSheet()
    # Container for the 'flowable' elements
    elements = []

    # Add a title
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Normal"],
        alignment=TA_LEFT,
        fontName="Helvetica-Bold",
    )
    title = Paragraph("VARIANT SUMMARY FOR FH", style=title_style)
    elements.append(title)
    elements.append(Spacer(1, 5))

    # Generate table data
    data = _generate_row_data(headers, rows)

    # Calculate equal column widths based on available page width
    page_width = letter[0] - doc.leftMargin - doc.rightMargin
    col_width = page_width / len(headers)

    # Create the table with specified column widths
    table = Table(data, colWidths=[col_width] * len(headers))

    # Style the table
    style = TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#a5d6db")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#156082")),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),  # Vertical alignment
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#a5d6db")),
        ]
    )
    table.setStyle(style)

    # Add alternating row colors
    for i in range(1, len(data)):
        if i % 2 == 0:
            bc = colors.whitesmoke
        else:
            bc = colors.white
        style = TableStyle([("BACKGROUND", (0, i), (-1, i), bc)])
        table.setStyle(style)

    elements.append(table)

    # Build the PDF
    doc.build(elements)


def _create_pdf_with_table_res(
    filename: str, headers: List[str], rows: List[Tuple[str]]
):
    """Create a PDF with a table that has wrapped text"""
    # Create a document template with specified margins
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=70,
        leftMargin=70,
        topMargin=195,  # 195 pts top margin as requested
        bottomMargin=70,  # 70 pts bottom margin as requested
    )

    styles = getSampleStyleSheet()
    # Container for the 'flowable' elements
    elements = []

    # Add a title
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Normal"],
        alignment=TA_LEFT,
        fontName="Helvetica-Bold",
    )
    title = Paragraph("RESULTS INTERPRETATION", style=title_style)
    elements.append(title)
    elements.append(Spacer(1, 5))

    # Generate table data
    data = _generate_row_data(headers, rows)

    # Calculate equal column widths based on available page width
    page_width = letter[0] - doc.leftMargin - doc.rightMargin

    # Create the table with specified column widths
    table = Table(data, colWidths=[page_width / 5, 4 * page_width / 5] * len(headers))

    # Style the table
    style = TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#a5d6db")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#156082")),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),  # Vertical alignment
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#a5d6db")),
        ]
    )
    table.setStyle(style)

    # Add alternating row colors
    for i in range(1, len(data)):
        if i % 2 == 0:
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


def generate(*, variants=None):
    assert all([variants]), "Missing required fields"
    module_dir = Path(__file__).parent

    output_pdf_annotations = "/tmp/annotations.pdf"
    input_pdf_path = f"{module_dir}/blank.pdf"

    column_mapping = {
        "Gene/Variant": "Alt Allele",
        "Genotype": "Consequence",
        "Assesment": "Transcript ID & Version",
        "Mode of Inheritance": "Amino Acid Change",
        "Phenotype": "Codon Change",
    }

    rows = []
    headers = [
        "Gene/Variant",
        "Genotype",
        "Assesment",
        "Mode of Inheritance",
        "Phenotype",
    ]

    output_file_name_res = f"/tmp/{str(uuid.uuid4())}-res.pdf"
    output_file_name_vs = f"/tmp/{str(uuid.uuid4())}-vs.pdf"

    for variant in variants:
        row = []
        for header in headers:
            row.append(variant[column_mapping[header]])
        rows.append(row)

    _create_pdf_with_table_vs(output_pdf_annotations, headers, rows)
    _overlay_template_with_table(
        output_pdf_annotations, input_pdf_path, output_file_name_vs
    )

    rows = []

    headers = [
        "Gene/Variant",
        "Interpretation of your genetic result",
    ]

    for variant in variants:
        row = []
        row.append(variant[column_mapping[headers[0]]])
        row.append(
            """Your genetic profile have indicated that you have the variant that is certain/probable to be the cause FH. 
Familial hypercholesterolemia-1 (FHCL1) can be caused by heterozygous, compound heterozygous, or homozygous mutation in the low density lipoprotein receptor gene (LDLR; 606945) on chromosome 19p13
Familial hypercholesterolemia is characterized by elevation of serum cholesterol bound to low density lipoprotein (LDL), which promotes deposition of cholesterol in the skin (xanthelasma), tendons (xanthomas), and coronary arteries (atherosclerosis). The disorder occurs in 2 clinical forms: homozygous and heterozygous.
"""
        )
        rows.append(row)

    _create_pdf_with_table_res(output_pdf_annotations, headers, rows)
    _overlay_template_with_table(
        output_pdf_annotations, input_pdf_path, output_file_name_res
    )
    os.remove(output_pdf_annotations)

    print(
        f"Generated Stage 1 PDFs: vs = {output_file_name_vs} res = {output_file_name_res}"
    )

    return output_file_name_vs, output_file_name_res
