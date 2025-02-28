from pathlib import Path
import subprocess
import re

from magic import Magic

GENOMIC_SUFFIXES = {
    ".vcf",
    ".bcf",
    ".vcf.gz",
    ".bcf.gz",
    ".vcf.bgz",
    ".bcf.bgz",
    ".tbi",
    ".csi",
    ".bam",
    ".bai",
    ".sam",
}

MIME_MAPPING = {
    ".vcf": ["text/plain"],
    ".bcf": ["application/octet-stream"],
    ".vcf.gz": ["application/x-gzip", "application/gzip"],
    ".bcf.gz": ["application/x-gzip", "application/gzip"],
    ".vcf.bgz": ["application/x-gzip"],
    ".bcf.bgz": ["application/x-gzip"],
    ".tbi": ["application/x-gzip"],
    ".csi": ["application/x-gzip"],
    ".bam": ["application/x-gzip", "application/octet-stream"],
    ".bai": ["application/octet-stream"],
    ".sam": ["text/plain"],
    ".json": ["application/json", "text/plain"],
    ".csv": ["text/csv", "application/csv"],
    ".tsv": ["text/tab-separated-values", "text/plain"],
    ".txt": ["text/plain"],
}

HTSFILE_MAPPING = {
    ".vcf": {"format": "VCF"},
    ".bcf": {"format": "BCF"},
    ".vcf.gz": {"format": "VCF", "compressed": True},
    ".bcf.gz": {"format": "BCF", "compressed": True},
    ".vcf.bgz": {"format": "VCF", "compressed": True},
    ".bcf.bgz": {"format": "BCF", "compressed": True},
    ".tbi": {"format": "Tabix"},
    ".csi": {"format": "CSI"},
    ".bam": {"format": "BAM"},
    ".bai": {"format": "BAI"},
    ".sam": {"format": "SAM"},
}


def validate_genomic_file(local_input_path, extension):
    result = subprocess.run(
        ["htsfile", local_input_path], capture_output=True, text=True, check=True
    )
    output = result.stdout.strip()

    format_details = output.split("\t")[1] if "\t" in output else output

    expected = HTSFILE_MAPPING.get(extension)

    if not expected:
        raise Exception(
            f"File's extension is not in the list of allowed genomic files.\nAllowed file types: {', '.join(HTSFILE_MAPPING.keys())}"
        )
    if expected["format"] not in output:
        raise Exception(
            f"File's expected format did not match the format identified by htsfile.\n: {expected['format']}\nFormat identified by htsfile: {format_details}"
        )
    if expected.get("compressed"):
        if not re.search(r"\b(BGZF-compressed|gzip-compressed|compressed)\b", output):
            raise Exception(
                f"File's extension indicates that the file is compressed, but htsfile found an uncompressed format.\nFormat identified by htsfile: {format_details}"
            )

    return True


def validate_file(local_input_path):
    extension = None
    for ext in MIME_MAPPING.keys():
        if local_input_path.endswith(ext):
            extension = ext
            break
    if not extension:
        raise Exception(
            f"File's extension is not in the list of allowed files.\nAllowed file types: {', '.join(MIME_MAPPING.keys())}"
        )

    expected_mime = MIME_MAPPING[extension]

    detected_mime = Magic(mime=True).from_file(local_input_path)

    if detected_mime in expected_mime:
        if extension in GENOMIC_SUFFIXES:
            validate_genomic_file(local_input_path, extension)
        return
    raise Exception(
        f"File's expected format did not match the result of MIME type checking.\nExpected format(s): {', '.join(expected_mime)}\nFormat identified by MIME type checking: {detected_mime}"
    )
