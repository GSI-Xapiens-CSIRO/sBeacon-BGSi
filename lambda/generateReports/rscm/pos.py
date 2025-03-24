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
    pos_stage_1 = generate_pos_stage_1(variants=variants)

    # Generate the second stage of the report
    pos_stage_2 = generate_pos_stage_2(
        pii_name=pii_name, pii_dob=pii_dob, pii_gender=pii_gender
    )

    # Generate the third stage of the report
    pos_stage_3 = generate_pos_stage_3(pii_name=pii_name, pii_dob=pii_dob)

    os.remove("/tmp/annotated-RSCM_positive_int.pdf")
    os.remove("/tmp/annotated-RSCM_positive_res.pdf")
    os.remove("/tmp/annotated-RSCM_positive_vs.pdf")

    return "/tmp/annotated_pos.pdf"


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
