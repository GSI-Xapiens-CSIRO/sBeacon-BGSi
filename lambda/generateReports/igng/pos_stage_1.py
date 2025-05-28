import os
import uuid
from pathlib import Path
from typing import List, Tuple
from copy import deepcopy

from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
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
        textColor=colors.black,
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
        pagesize=A4,
        rightMargin=65,
        leftMargin=65,
        topMargin=156,
        bottomMargin=75,
    )

    # Container for the 'flowable' elements
    elements = []

    # Generate table data
    data = _generate_row_data(headers, rows)

    # Calculate equal column widths based on available page width
    page_width = A4[0] - doc.leftMargin - doc.rightMargin
    col_width = page_width / len(headers)

    # Create the table with specified column widths
    table = Table(data, colWidths=[col_width] * len(headers))

    # Style the table
    style = TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#cadeb7")),
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


def generate(*, variants=[]):
    module_dir = Path(__file__).parent
    output_pdf_annotations = "/tmp/annotations.pdf"
    input_pdf_path = f"{module_dir}/blank.pdf"

    rows = []
    headers = [
        "Obat",
        "Gen yang dianalisis",
        "Genotipe",
        "rsIDs",
        "Kategori Metabolisme",
        "Rekomendasi Klinis",
    ]

    output_file_name = f"/tmp/{str(uuid.uuid4())}.pdf"

    for variant in variants:

        row = [variant["Drugs"]]
        row.append(variant["Gene"])
        # row.append(variant="Genotype"])
        row.append("N/A")
        row.append(variant["Variant"])
        row.append(variant["Phenotype Categories"])
        row.append(variant.get("Recommendation", "N/A"))
        rows.append(row)

    _create_pdf_with_table_vs(output_pdf_annotations, headers, rows)
    _overlay_template_with_table(
        output_pdf_annotations, input_pdf_path, output_file_name
    )

    print(f"Generated Stage 1 PDFs: {output_file_name}")

    return output_file_name
