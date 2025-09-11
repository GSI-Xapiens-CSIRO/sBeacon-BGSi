import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors

def clear_area(c, x, y, width=200, height=15, color=colors.white):
    c.setFillColor(color)
    c.rect(x, y, width, height, fill=1, stroke=0)
    c.setFillColor(colors.black)

def _create_annotations(
    date_pos,
    name_pos,
    dob_pos,
    rekam_medis_pos,
    gender_pos,
    symptoms_pos,
    clinical_diagnosis_pos,
    physician_pos,
    genetic_counselor_pos,
    footer_name_pos,
    footer_dob_pos,
    filename,
    versions,
    report_id,
    validated_at,
    validated_by,
    project_value,
    vcf_value,
    validated_comment,
):
    c = canvas.Canvas(filename, pagesize=letter)
    form = c.acroForm
    text_color = colors.HexColor("#156082")

    print("validated_comment:", validated_comment)
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

    for n in range(4):
        x, y, fs, text = (5, 780, 12, report_id)
        c.setFont("Helvetica", fs)
        c.drawString(x, y, text)
        
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
        x, y, fs, text = date_pos
        c.setFont("Helvetica", fs)
        c.setFillColor(text_color)
        c.drawString(x, y, text or "")
        
        if n == 2:
            versions_pos = [
                # left col
                (180, 570 + 15, 11, versions["clinvar_version"]),
                (180, 556 + 15, 11, versions["gnomad_version"]),
                # right col
                (450 - 20, 570 + 15, 11, versions["dbsnp_version"]),
                (450 - 20, 556 + 15, 11, versions["sift_version"]),
            ]
            for pos in versions_pos:
                x, y, fs, text = pos
                c.setFont("Helvetica", fs)
                c.setFillColor(colors.black)
                c.drawString(x, y, text)
            
            x, y, fs, text = validated_at
            c.setFont("Helvetica", fs)
            c.setFillColor(colors.black)
            c.drawString(x, y, text or "")

            x, y, fs, text = validated_by
            c.setFont("Helvetica", fs)
            c.setFillColor(colors.black)
            c.drawString(x, y, text or "")

        if n == 3:
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

            x, y, fs, text = validated_comment
            c.setFont("Helvetica", fs)
            c.setFillColor(colors.black)
            c.drawString(x, y, text or "")

        # page num
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.HexColor("#156082"))
        c.drawString(490, 68, f"Page {n+1} of 4")

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


def generate_neg(
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
    user=None,
    validated_at=None,
    validated_comment=None
):
    module_dir = Path(__file__).parent
    output_pdf_path = "/tmp/annotations.pdf"
    input_pdf_path = f"{module_dir}/neg.pdf"

    # x, y, h, text
    date_pos = (158, 47, 10, datetime.now().strftime('%Y-%m-%d'))
    name_pos = (192, 566, 12, "")
    dob_pos = (192, 552, 12, "")
    rekam_medis_pos = (192, 538, 12, "")
    gender_pos = (192, 524, 12, "Male")
    clinical_diagnosis_pos = (192, 510, 12, "Familial Hypercholesterolemia (FH)")
    symptoms_pos = (192, 494, 12, "")
    physician_pos = (192, 480, 12, "dr. Dicky Tahapary, SpPD-KEMD., PhD")
    genetic_counselor_pos = (192, 464, 12, "dr. Widya Eka Nugraha, M.Si. Med.")
    
    footer_name_pos = (148, 72, 10, "")
    footer_dob_pos = (148, 58, 10, "")
    footer_date_pos = (158, 47, 10, datetime.now().strftime('%Y-%m-%d'))
    
    project_value = (72, 505, 12, project or "")
    vcf_value = (72, 550, 12, vcf or "")
    validated_by = (205, 175, 11, f"{user.get('firstName', '')} {user.get('lastName', '')}".strip())

    try:
        dt = datetime.fromisoformat(validated_at)
        dt_wib = dt + timedelta(hours=7)
        validated_at_str = dt_wib.strftime("%Y-%m-%d %H:%M")
    except Exception as e:
        print("Parse error:", e)
        validated_at_str = validated_at

    validated_at = (205, 161, 11, validated_at_str)
    validated_comment= (72, 442, 11, validated_comment or "")

    _create_annotations(
        date_pos,
        name_pos,
        dob_pos,
        rekam_medis_pos,
        gender_pos,
        symptoms_pos,
        clinical_diagnosis_pos,
        physician_pos,
        genetic_counselor_pos,
        footer_name_pos,
        footer_dob_pos,
        output_pdf_path,
        versions,
        report_id,
        validated_at,
        validated_by,
        project_value,
        vcf_value,
        validated_comment,
    )
    output_file_name = f"/tmp/{str(uuid.uuid4())}.pdf"
    _overlay_pdf_with_annotations(output_pdf_path, input_pdf_path, output_file_name)
    os.remove(output_pdf_path)

    print(f"Generated report: {output_file_name}")
    return output_file_name


if __name__ == "__main__":
    generate_neg(
        pii_name="John Doe",
        pii_dob="01/01/1990",
        pii_gender="Male",
        versions={
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
        },
        report_id=str(uuid.uuid4()),
    )
