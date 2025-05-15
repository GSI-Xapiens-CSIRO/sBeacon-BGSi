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
    summary_pdf, results_pdf = generate_pos_stage_1(variants=variants)

    # Generate the second stage of the report
    annots_pdf = generate_pos_stage_2(
        pii_name=pii_name, pii_dob=pii_dob, pii_gender=pii_gender
    )

    # Generate the third stage of the report
    report = generate_pos_stage_3(
        summary_pdf, results_pdf, annots_pdf, pii_name=pii_name, pii_dob=pii_dob
    )

    os.remove(summary_pdf)
    os.remove(results_pdf)
    os.remove(annots_pdf)

    return report


if __name__ == "__main__":
    # Example usage - for testing includes made up data
    generate(
        pii_name="John Doe",
        pii_dob="01/01/1900",
        pii_gender="Female",
        variants=[
            {
                "Gene Name": "TPMT",
                "Variant Name": "NM_000367.5(TPMT):c.719A>G (p.Tyr240Cys)",
                "gt": "0/0",
                "clinSig": "Benign",
                "conditions": "ABCG2-related disorder",
            },
            {
                "Gene Name": "TPMT",
                "Variant Name": "NM_000367.5(TPMT):c.719A>G (p.Tyr240Cys)",
                "gt": "0/0",
                "clinSig": "association",
                "conditions": "BLOOD GROUP, JUNIOR SYSTEM",
            },
            {
                "Gene Name": "TPMT",
                "Variant Name": "NM_000367.5(TPMT):c.626-1G>A",
                "gt": "0/0",
                "clinSig": "drug response",
                "conditions": "Gemcitabine response",
            },
            {
                "Gene Name": "TPMT",
                "Variant Name": "NM_000367.5(TPMT):c.500C>G (p.Ala167Gly)",
                "gt": "0/0",
                "clinSig": "association",
                "conditions": "Uric acid concentration, serum, quantitative trait locus 1",
            },
            {
                "Gene Name": "TPMT",
                "Variant Name": "NM_000367.5(TPMT):c.460G>A (p.Ala154Thr)",
                "gt": "0/0",
                "clinSig": "drug response",
                "conditions": "rosuvastatin response - Efficacy",
            },
            {
                "Gene Name": "-",
                "Variant Name": "NM_000367.5(TPMT):c.497A>G (p.Tyr166Cys)",
                "gt": "0/0",
                "clinSig": "drug response",
                "conditions": "rosuvastatin response - Metabolism/PK",
            },
        ],
    )
