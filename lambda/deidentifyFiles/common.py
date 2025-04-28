import os
import re

MASK = "XXXXXXXXXX"

PII_PATTERNS = [
    r"\b[a-zA-Z0-9._%+-]{3,}@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b",  # Email
    r"^(\+62|62)?[\s-]?0?8[1-9]{1}\d{1}[\s-]?\d{4}[\s-]?\d{2,5}$",  # Phone number
    r"^(1[1-9]|21|[37][1-6]|5[1-3]|6[1-5]|[89][12])\d{2}\d{2}([04][1-9]|[1256][0-9]|[37][01])(0[1-9]|1[0-2])\d{2}\d{4}$",  # NIK
    r"\b[A-Z]{1,2} \d{1,4}( [A-Z]{1,3})?\b",  # License plate with enforced spaces
]
CASE_INSENSITIVE_PII_PATTERNS = [
    r"\b(?:(?:Jl\.|Jalan|Desa|Kelurahan|Kecamatan|Kabupaten|Provinsi|Jakarta|Kode\s?Pos)(?:\s?(?:\d{5}|RT\s?\d{1,2}/RW\s?\d{1,2}|[A-Z^RT]+[a-z]*(?:\.\s?\d+)?),?)+,?\s?)+\b",  # Address
    r"\b(?:Dr\.|Prof\.|Ir\.|Haji|Hajjah|Putra|Putri|Sri|Adi|Raden|Ny)(?:\s[A-Z][a-z]+){1,2}\b",  # Name
]
ANY_PII_PATTERN = re.compile(
    "|".join(
        f"(?:{pattern})"
        for pattern in PII_PATTERNS
        + [f"(?i:{pattern})" for pattern in CASE_INSENSITIVE_PII_PATTERNS]
    )
)

GENOMIC_SUFFIX_TYPES = {
    ".bcf": "u",
    ".bcf.gz": "b",
    ".bcf.bgz": "b",
    ".vcf": "v",
    ".vcf.gz": "z",
    ".vcf.bgz": "z",
}

# Check if the script is running in AWS Lambda.
# EC2 instances don't have as much space in tmp
WORKING_DIR = "/tmp" if ("AWS_LAMBDA_FUNCTION_NAME" in os.environ) else "."


def anonymise(input_string):
    return ANY_PII_PATTERN.sub(MASK, input_string)
