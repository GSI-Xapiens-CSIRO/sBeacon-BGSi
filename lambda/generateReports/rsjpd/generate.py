import os
import uuid

from PyPDF2 import PdfReader, PdfWriter
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors


_text_field_positions_page_1 = [
    # -----
    # Nama lengkap
    (135, 685, 130, 12, 12, "", 0),
    # Tanggal lahir
    (135, 660, 130, 12, 12, "", 0),
    # Usia
    (135, 635, 130, 12, 12, "", 0),
    # Jenis kelamin
    (135, 608, 130, 12, 12, "", 0),
    # Berat badan
    (135, 578, 120, 12, 12, "", 0),
    # Tinggi badan
    (135, 545, 120, 12, 12, "", 0),
    # No rekam medis
    (145, 515, 120, 12, 12, "", 0),
    # -----
    # Dokter pengirim
    (396, 690, 150, 12, 12, "", 0),
    # Tipe spesimen
    (396, 662, 150, 12, 12, "", 0),
    # Waktu pengambilan
    (420, 605, 130, 12, 12, "", 0),
    # Waktu penerimaan
    (420, 560, 130, 12, 12, "", 0),
    # Diagnosa
    (120, 420, 400, 24, 12, "", 1 << 12),
    # -----
    # statins
    # Atorvastatin
    (190, 195, 100, 12, 12, "", 0),
    (320, 195, 100, 12, 12, "", 0),
    (455, 195, 100, 12, 12, "", 0),
    # Lovastatin
    (190, 171, 100, 12, 12, "", 0),
    (320, 171, 100, 12, 12, "", 0),
    (455, 171, 100, 12, 12, "", 0),
    # Pitavastatin
    (190, 147, 100, 12, 12, "", 0),
    (320, 147, 100, 12, 12, "", 0),
    (455, 147, 100, 12, 12, "", 0),
    # Pravastatin
    (190, 123, 100, 12, 12, "", 0),
    (320, 123, 100, 12, 12, "", 0),
    (455, 123, 100, 12, 12, "", 0),
    # Rosuvastatin
    (190, 99, 100, 12, 12, "", 0),
    (320, 99, 100, 12, 12, "", 0),
    (455, 99, 100, 12, 12, "", 0),
    # Simvastatin
    (190, 75, 100, 12, 12, "", 0),
    (320, 75, 100, 12, 12, "", 0),
    (455, 75, 100, 12, 12, "", 0),
]
_checkbox_positions_page_1 = [
    # -----
    # APOE
    (400, 630, 12, "", 0),
    # SLCO1B1
    (470, 630, 12, "", 0),
    # -----
    # Diabetes Militus
    (80, 380, 12, "", 0),
    # Hipertensi
    (80, 355, 12, "", 0),
    # Dislipidemia
    (80, 330, 12, "", 0),
    # -----
    # Perokok Aktif
    (298, 380, 12, "", 0),
    # Perokok Pasif
    (298, 355, 12, "", 0),
    # PJK keluarga usia muda
    (298, 330, 12, "", 0),
    # -----
    # Atorvastatin
    (57, 191, 12, "", 0),
    # Lovastatin
    (57, 167, 12, "", 0),
    # Pitavastatin
    (57, 141, 12, "", 0),
    # Pravastatin
    (57, 119, 12, "", 0),
    # Rosuvastatin
    (57, 95, 12, "", 0),
    # Simvastatin
    (57, 70, 12, "", 0),
]

_text_field_positions_page_2 = [
    # -----
    # SLCO1B1
    (190, 690, 100, 12, 12, "", 0),
    (305, 690, 100, 12, 12, "", 0),
    (420, 690, 100, 12, 12, "", 0),
    # APOE
    (190, 660, 100, 12, 12, "", 0),
    (305, 660, 100, 12, 12, "", 0),
    (420, 660, 100, 12, 12, "", 0),
    # ----
    # 1
    (290, 577, 45, 12, 12, "", 0),
    (341, 577, 45, 12, 12, "", 0),
    # 2
    (190, 548, 35, 12, 12, "", 0),
    # 3
    (190, 513, 35, 12, 12, "", 0),
    # 4
    (190, 480, 35, 12, 12, "", 0),
    # 5
    (166, 446, 45, 12, 12, "", 0),
    # ------
    # Kesimpulan
    (57, 293, 470, 69, 12, "", 1 << 12),
    # Tindak Lanjut Pengobatan
    (57, 55, 470, 210, 12, "", 1 << 12),
]

_text_field_positions_page_3 = [
    # -----
    # Metode Uji
    (57, 718, 470, 52, 12, "", 0),
    # Sumber
    (57, 25, 470, 200, 12, "", 0),
]


def _create_annotations(
    filename,
):
    c = canvas.Canvas(filename, pagesize=letter)
    c.showPage()
    form = c.acroForm

    for n, pos in enumerate(_text_field_positions_page_1):
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
            fillColor=colors.white,
            fieldFlags=flags,
        )
    for n, pos in enumerate(_checkbox_positions_page_1):
        x, y, fs, text, flags = pos
        c.setFont("Helvetica", fs)
        form.checkbox(
            name=f"checkbox-{n}",
            tooltip="",
            x=x,
            y=y,
            buttonStyle="check",
            shape="square",
            borderStyle="solid",
            borderWidth=1,
            fillColor=colors.white,
            borderColor=colors.black,
            fieldFlags=flags,
        )

    c.showPage()

    for n, pos in enumerate(_text_field_positions_page_2):
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
            fillColor=colors.white,
            fieldFlags=flags,
        )
    c.showPage()
    for n, pos in enumerate(_text_field_positions_page_3):
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
            fillColor=colors.white,
            fieldFlags=flags,
        )
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


def generate(*, pii_name=None, pii_dob=None, pii_gender=None):
    module_dir = Path(__file__).parent
    output_file_name = f"/tmp/{uuid.uuid4()}.pdf"
    _create_annotations("/tmp/annotations.pdf")
    _overlay_pdf_with_annotations(
        "/tmp/annotations.pdf",
        f"{module_dir}/template.pdf",
        output_file_name,
    )
    os.remove("/tmp/annotations.pdf")

    print(f"Generated report: {output_file_name}")
    return output_file_name


if __name__ == "__main__":
    generate()
