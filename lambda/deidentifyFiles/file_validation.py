from pathlib import Path
import subprocess

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
    ".bam": ["application/x-gzip"],
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


def get_full_extension(local_input_path):
    return "".join(Path(local_input_path).suffixes)


def validate_genomic_file(local_input_path, extension):
    try:
        result = subprocess.run(
            ["htsfile", local_input_path], capture_output=True, text=True, check=True
        )
        output = result.stdout.strip()

        expected = HTSFILE_MAPPING.get(extension)

        if not expected:
            return False
        if expected["format"] not in output:
            return False
        if expected.get("compressed"):
            return any(
                term in output for term in ["BGZF-compressed", "gzip-compressed"]
            )

        return True

    except subprocess.CalledProcessError as e:
        print(f"Error running htsfile: {e}")
        return False


def validate_file(local_input_path):
    extension = get_full_extension(local_input_path)
    if extension not in MIME_MAPPING:
        raise Exception("File's extension is not in the list of allowed files")
    expected_mime = MIME_MAPPING[extension]

    detected_mime = Magic(mime=True).from_file(local_input_path)

    if detected_mime in expected_mime:
        if extension in GENOMIC_SUFFIXES:
            if not validate_genomic_file(local_input_path, extension):
                raise Exception(
                    f"File's extension does not match the detected format, or htsfile failed to read it"
                )
        return
    raise Exception(
        f"File's extension did not match the corresponding file signature.\nExpected signatures: {expected_mime}\nReceived: {detected_mime}"
    )
