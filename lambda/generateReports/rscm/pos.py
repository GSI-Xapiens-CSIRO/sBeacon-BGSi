import os

try:
    from .pos_stage_1 import generate as generate_pos_stage_1
    from .pos_stage_2 import generate as generate_pos_stage_2
    from .pos_stage_3 import generate as generate_pos_stage_3
except:
    # local run
    print("Running locally")
    from pos_stage_1 import generate as generate_pos_stage_1
    from pos_stage_2 import generate as generate_pos_stage_2
    from pos_stage_3 import generate as generate_pos_stage_3


def generate(*, pii_name=None, pii_dob=None, pii_gender=None, variants=None):
    assert all([pii_name, pii_dob, pii_gender, variants]), "Missing required fields"

    # Generate the first stage of the report
    res_pdf, vs_pdf = generate_pos_stage_1(variants=variants)

    # Generate the second stage of the report
    annots_pdf = generate_pos_stage_2(
        pii_name=pii_name, pii_dob=pii_dob, pii_gender=pii_gender
    )

    # Generate the third stage of the report
    report = generate_pos_stage_3(
        res_pdf, vs_pdf, annots_pdf, pii_name=pii_name, pii_dob=pii_dob
    )

    os.remove(res_pdf)
    os.remove(vs_pdf)
    os.remove(annots_pdf)

    return report


if __name__ == "__main__":
    generate(
        pii_name="John Doe",
        pii_dob="01/01/1900",
        pii_gender="Female",
        variants=[
            {
                "Alt Allele": "C1",
                "Consequence": "C2",
                "Transcript ID & Version": "C3",
                "Amino Acid Change": "C4",
                "Codon Change": "C5",
            },
            {
                "Alt Allele": "V1",
                "Consequence": "V2",
                "Transcript ID & Version": "V3",
                "Amino Acid Change": "V4",
                "Codon Change": "V5",
            },
            {
                "Alt Allele": "R1",
                "Consequence": "R2",
                "Transcript ID & Version": "R3",
                "Amino Acid Change": "R4",
                "Codon Change": "R5",
            },
        ],
    )
