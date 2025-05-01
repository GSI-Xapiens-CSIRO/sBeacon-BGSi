import argparse
import csv
import json
import os
import re
import subprocess

import boto3
import ijson

from file_validation import validate_file

ANNOTATION_PATH = "annotation.vcf.gz"
BGZIPPED_PATH = "bgzipped.bcf.gz"
HEADER_PATH = "header.vcf"
MAX_LINES_PER_PRINT = 100
MASK = "XXXXXXXXXX"

INFO_RESERVED_KEYS = {
    "AA",
    "AC",
    "AD",
    "ADF",
    "ADR",
    "AF",
    "AN",
    "BQ",
    "CIGAR",
    "DB",
    "DP",
    "END",
    "H2",
    "H3",
    "MQ",
    "MQ0",
    "NS",
    "SB",
    "SOMATIC",
    "VALIDATED",
    "1000G",
}

META_UNSTRUCTURED_WHITELIST = {
    "fileformat",
    "fileDate",
    "source",
    "reference",
    "assembly",
}

# Only check the Description value for these
META_STRUCTURED_WHITELIST = {
    "INFO",
    "FILTER",
    "FORMAT",
    "ALT",
    "contig",
}

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
METADATA_KEY_PII_PATTERNS = [
    r"(?i)\b(?:(?:full|first|last|middle|given|family|sur)[_ -]?name|nama(?:[_ -](?:lengkap|depan|belakang|tengah))?|nama|surname)\b",
    r"(?i)\b(?:(?:plate|license|vehicle|registration|number)_(?:plate|number|nopol|polisi|registrasi)|(?:nomor|plat)_(?:plat|nomor|polisi|registrasi)|nopol(?:_id)?|vehicle_nopol|registration_nopol|plat_number|plateno)\b",
]

GENOMIC_SUFFIX_TYPES = {
    ".bcf": "u",
    ".bcf.gz": "b",
    ".bcf.bgz": "b",
    ".vcf": "v",
    ".vcf.gz": "z",
    ".vcf.bgz": "z",
}

SAM_SUFFIXES = {
    ".bam",
    ".sam",
}

QUIETLY_SKIP_SUFFIXES = {
    # Because we'll be creating these ourselves
    # from other files, and don't want the uploaded
    # versions to squash the ones we create.
    ".bai",
    ".csi",
}

METADATA_SUFFIXES = [
    ".json",
    ".csv",
    ".tsv",
    ".txt",
]

SAM_HEADERS_WHITELIST = {
    "HD": {
        "VN",
        "SO",
        "GO",
        "SS",
    },
    "SQ": {
        "SN",
        "LN",
        "AH",
        "AN",
        "AS",
        "M5",
        "SP",
        "TP",
        "UR",
    },
    "RG": {
        "ID",
        "BC",
        "CN",
        "DT",
        "FO",
        "KS",
        "LB",
        "PG",
        "PI",
        "PL",
        "PM",
        "PU",
        "SM",
    },
    "PG": {
        "ID",
        "PN",
        "CL",
        "PP",
        "VN",
    },
}

# Check if the script is running in AWS Lambda.
# EC2 instances don't have as much space in tmp
WORKING_DIR = "/tmp" if ("AWS_LAMBDA_FUNCTION_NAME" in os.environ) else "."

dynamodb = boto3.client("dynamodb")
s3 = boto3.client("s3")


class ProcessError(Exception):
    def __init__(self, message, stdout, stderr, returncode, process_args):
        self.message = message
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode
        self.process_args = process_args
        super().__init__(message)

    def __str__(self):
        return f"{self.message}\nProcess args: {self.process_args}\nstderr:\n{self.stderr}\nreturncode: {self.returncode}"


class ParsingError(Exception):
    pass


class CheckedProcess:
    def __init__(self, error_message, **kwargs):
        defaults = {
            "stderr": subprocess.PIPE,
            "cwd": WORKING_DIR,
            "encoding": "utf-8",
        }
        kwargs.update({k: v for k, v in defaults.items() if k not in kwargs})
        print(
            f"Running subprocess.Popen with kwargs: {json.dumps(kwargs, default=str)}"
        )
        self.process = subprocess.Popen(**kwargs)
        self.error_message = error_message
        self.stdout = self.process.stdout
        self.stdin = self.process.stdin

    def check(self):
        stdout, stderr = self.process.communicate()
        returncode = self.process.returncode
        if returncode != 0:
            raise ProcessError(
                self.error_message, stdout, stderr, returncode, self.process.args
            )


class Viewer:
    def __init__(self, process_args, error_message):
        self.started = False
        self.process_args = process_args
        self.error_message = error_message
        self.view_process = None
        self.lines = []

    def _print(self, lines):
        if not self.started:
            self._start()
        print("\n".join(lines), file=self.view_process.stdin)

    def _start(self):
        self.view_process = CheckedProcess(
            args=self.process_args,
            stdin=subprocess.PIPE,
            error_message=self.error_message,
        )
        self.started = True

    def ingest(self, new_lines):
        self.lines.extend(new_lines)
        if len(self.lines) > MAX_LINES_PER_PRINT:
            self._print(self.lines)
            self.lines.clear()

    def close(self):
        if self.lines:
            self._print(self.lines)
        if self.started:
            self.view_process.check()


class SamReader:
    """Anonymises sam file line by line, and counts changes."""

    def __init__(self):
        self.header_lines = 0
        self.header_pii = 0
        self.record_lines = 0
        self.record_pii = 0

    def anonymise_lines(self, line_iterator):
        for line in line_iterator:
            line = line.rstrip("\r\n")
            if not line:
                continue
            if line.startswith("@"):
                self.header_lines += 1
                if new_line := anonymise_sam_header_line(line):
                    self.header_pii += 1
            else:
                self.record_lines += 1
                if new_line := anonymise_sam_record(line):
                    self.record_pii += 1
            yield new_line or line

    def get_summary_string(self):
        return (
            f"Anonymised {self.header_pii}/{self.header_lines} header lines"
            f" and {self.record_pii}/{self.record_lines} records"
        )


def anonymise(input_string):
    return ANY_PII_PATTERN.sub(MASK, input_string)


def get_structured_meta_values(value):
    if not (value.startswith("<") and value.endswith(">")):
        raise ParsingError(f"Meta information line is formatted correctly:\n{value}")
    values = {}
    current_key = []
    current_value = []
    extending = current_key
    escaped = False
    in_quotes = False
    for c in value[1:]:
        if escaped:
            extending.append(c)
            escaped = False
        elif c == "\\":
            extending.append(c)
            escaped = True
        elif c == '"':
            in_quotes = not in_quotes
            extending.append(c)
        elif in_quotes:
            extending.append(c)
        elif c in ",>":
            values["".join(current_key)] = "".join(current_value)
            current_key.clear()
            current_value.clear()
            extending = current_key
        elif c == "=":
            extending = current_value
        else:
            extending.append(c)
    return values


def anonymise_header_line(header_line):
    if header_line.startswith("##") and header_line.count("="):
        # Is a meta line
        key, value = header_line[2:].split("=", 1)
        if value.startswith("<"):
            # Structured meta line
            subkey_values = get_structured_meta_values(value)
            if key in META_STRUCTURED_WHITELIST and "Description" in subkey_values:
                subkey_values["Description"] = anonymise(subkey_values["Description"])
            else:
                subkey_values = {
                    anonymise(subkey): anonymise(subvalue)
                    for subkey, subvalue in subkey_values.items()
                }
            new_value = (
                "<"
                + ",".join(
                    f"{subkey}={subvalue}" for subkey, subvalue in subkey_values.items()
                )
                + ">"
            )
            new_line = f"##{key}={new_value}"
        elif key in META_UNSTRUCTURED_WHITELIST:
            new_line = header_line
        else:
            new_line = f"##{anonymise(key)}={anonymise(value)}"
    else:
        # Other comment line or incorrectly formatted, anonymise the whole thing
        new_line = f"#{anonymise(header_line[1:])}"
    return new_line


def anonymise_vcf_record(record, info_whitelist):
    """Anonymise the INFO column of a VCF record"""
    fields = record.split("\t")
    info_field = fields[7]
    info_fields = info_field.split(";")
    new_info_pairs = []
    for field in info_fields:
        if (key_value := field.split("=", 1))[0] not in info_whitelist:
            if len(key_value) == 1:
                # This is a flag field, it should already be in the whitelist
                info_whitelist.add(key_value[0])
            else:
                value = key_value[1]
                new_value = anonymise(value)
                if new_value != value:
                    new_info_pairs.append(f"{key_value[0]}={new_value}")
    if new_info_pairs:
        fields[7] = ";".join(new_info_pairs)
        return "\t".join(fields)
    else:
        return None


def get_output_type(file_path):
    output_type_list = [
        (suffix, output_type)
        for suffix, output_type in GENOMIC_SUFFIX_TYPES.items()
        if file_path.endswith(suffix)
    ]
    assert (
        len(output_type_list) == 1
    ), f"File path {file_path} does not have a valid suffix"
    return output_type_list[0]


def process_header(file_path):
    view_process = CheckedProcess(
        args=["bcftools", "view", "--header-only", "--no-version", file_path],
        stdout=subprocess.PIPE,
        error_message="Reading header failed",
    )
    header_changes = False
    info_whitelist = INFO_RESERVED_KEYS.copy()
    header_lines = []
    for line in view_process.stdout:
        line = line.rstrip("\r\n")
        if line.startswith("##INFO=<"):
            # INFO line, add to whitelist if Type is not "String"
            info_attributes = get_structured_meta_values(line[7:])
            if info_attributes.get("Type", "String") != "String":
                info_whitelist.add(info_attributes.get("ID"))
        new_line = anonymise_header_line(line)
        header_lines.append(new_line)
        if new_line != line:
            header_changes = True
    view_process.check()
    if header_changes:
        print("Header PII detected, creating anonymised header")
        with open(f"{WORKING_DIR}/{HEADER_PATH}", "w") as header_file:
            print("\n".join(header_lines), file=header_file)
    else:
        print("No PII detected in header")
    return info_whitelist, header_lines, header_changes


def process_records(file_path, header_lines, info_whitelist):
    view_process = CheckedProcess(
        args=["bcftools", "view", "--drop-genotypes", "--no-header", file_path],
        stdout=subprocess.PIPE,
        error_message="Reading records failed",
    )
    header_lines = header_lines.copy()
    # Remove sample columns from header
    header_lines[-1] = "\t".join(header_lines[-1].split("\t", 8)[:8])
    num_records_changed = 0
    viewer = Viewer(
        [
            "bcftools",
            "view",
            "--no-version",
            "--output-type",
            "z",
            "--output",
            ANNOTATION_PATH,
            "--write-index",
        ],
        "Creating deidentified records failed",
    )
    for line in view_process.stdout:
        line = line.rstrip("\r\n")
        new_line = anonymise_vcf_record(line, info_whitelist)
        if new_line is not None:
            if num_records_changed == 0:
                viewer.ingest(header_lines + [new_line])
            else:
                viewer.ingest([new_line])
            num_records_changed += 1
    view_process.check()
    viewer.close()
    if num_records_changed:
        print(
            f"INFO PII detected, anonymised annotation created for {num_records_changed} record(s)"
        )
    else:
        print("No PII detected in records' INFO columns")
    return num_records_changed > 0


def prepare_for_annotate(file_path):
    """Annotate is very picky, and needs a gzipped indexed file to work"""
    print("Bgzipping and indexing locally for annotation")
    view_process = CheckedProcess(
        args=[
            "bcftools",
            "view",
            "--no-version",
            "--output-type",
            "b",
            "--output",
            BGZIPPED_PATH,
            "--write-index",
            file_path,
        ],
        stdout=subprocess.PIPE,
        error_message="Bgzipping and indexing original file failed",
    )
    view_process.check()


def anonymise_sam_header_line(header_line):
    assert header_line.startswith("@")
    contains_pii = False
    if (
        header_tags_whitelist := SAM_HEADERS_WHITELIST.get(header_line[1:3])
    ) is not None:
        new_tags = []
        for tag in header_line[4:].split("\t"):
            key, value = tag.split(":", 1)
            if key in header_tags_whitelist:
                new_tags.append(f"{key}:{value}")
            else:
                if (new_value := anonymise(value)) != value:
                    contains_pii = True
                    new_tags.append(f"{key}:{new_value}")
                else:
                    new_tags.append(tag)
        if not contains_pii:
            return None
        header_content = "\t".join(new_tags)
    else:
        # Should be a @CO header
        header_content = anonymise(header_line[4:])
        if header_content == header_line[4:]:
            return None
    return f"{header_line[:4]}{header_content}"


def anonymise_sam_record(record):
    all_fields = record.split("\t")
    contains_pii = False
    for idx, field in enumerate(all_fields):
        if idx < 11:
            continue
        tag, tag_type, value = field.split(":", 2)
        if tag_type == "Z":
            if (new_value := anonymise(value)) != value:
                contains_pii = True
                all_fields[idx] = f"{tag}:{tag_type}:{new_value}"
    return "\t".join(all_fields) if contains_pii else None


def anonymise_bam(input_path, output_path):
    # We need to write out the whole bam file as we go anyway,
    # So we might as well always send the created files
    output_index = f"{output_path}.bai"
    in_samtools_process = CheckedProcess(
        args=["samtools", "view", "--no-PG", "-h", input_path],
        stdout=subprocess.PIPE,
        error_message="Reading bam file failed",
    )
    out_samtools_viewer = Viewer(
        [
            "samtools",
            "view",
            "-h",
            "-b",
            "--no-PG",
            "--write-index",
            "-o",
            f"{output_path}##idx##{output_index}",
        ],
        "Creating deidentified bam file failed",
    )
    reader = SamReader()
    for line in reader.anonymise_lines(in_samtools_process.stdout):
        out_samtools_viewer.ingest([line])
    print(reader.get_summary_string())
    in_samtools_process.check()
    out_samtools_viewer.close()
    return [output_path, output_index]


def anonymise_sam(input_path, output_path):
    # In this case we can just read it as a flat file
    # With special handling of the relevant parts.
    with open(input_path, "r") as infile, open(output_path, "w") as outfile:
        reader = SamReader()
        for line in reader.anonymise_lines(infile):
            print(line, file=outfile)
    print(reader.get_summary_string())
    return [output_path]


def anonymise_vcf(input_path, output_path):
    output_type = get_output_type(input_path)[1]
    info_whitelist, header_lines, header_changes = process_header(input_path)
    info_changes = process_records(input_path, header_lines, info_whitelist)
    base_reheader_args = [
        "bcftools",
        "reheader",
        "--header",
        HEADER_PATH,
        "--output",
        output_path,
    ]
    base_annotate_args = [
        "bcftools",
        "annotate",
        "--no-version",
        "--annotations",
        ANNOTATION_PATH,
        "--columns",
        "INFO",
        "--pair-logic",
        "exact",
        "--output-type",
        output_type,
        BGZIPPED_PATH,
    ]
    files_to_move = [output_path]
    if output_type in "zb":
        files_to_move.append(f"{output_path}.csi")
    if header_changes:
        if info_changes:
            prepare_for_annotate(input_path)
            reheader_process = CheckedProcess(
                args=base_reheader_args,
                stdin=subprocess.PIPE,
                error_message="Updating header failed",
            )
            annotate_process = CheckedProcess(
                args=base_annotate_args,
                stdout=reheader_process.stdin,
                error_message="Updating INFO column failed",
            )
            reheader_process.check()
            annotate_process.check()
        else:
            reheader_process = CheckedProcess(
                args=base_reheader_args + [input_path],
                error_message="Updating header failed",
            )
            reheader_process.check()
        if output_type in "zb":
            index_process = CheckedProcess(
                args=["bcftools", "index", output_path],
                error_message="Indexing anonymised file failed",
            )
            index_process.check()
    elif info_changes:
        prepare_for_annotate(input_path)
        annotate_process = CheckedProcess(
            args=base_annotate_args
            + ["--output", output_path]
            + (["--write-index"] if output_type in "zb" else []),
            error_message="Updating INFO column failed",
        )
        annotate_process.check()
    else:
        print("No PII detected in VCF file, copying verbatim")
        files_to_move = [input_path]
        if output_type in "zb":
            index_process = CheckedProcess(
                args=["bcftools", "index", input_path],
                error_message="Indexing original file failed",
            )
            index_process.check()
            files_to_move.append(f"{input_path}.csi")
    return files_to_move


def process_tabular(input_path, output_path, delimiter):
    """Processes CSV/TSV files to deidentify PII and drop sensitive columns."""
    with open(input_path, "r", newline="", encoding="utf-8") as infile:
        reader = csv.reader(infile, delimiter=delimiter)
        header = next(reader)
        columns_to_keep = [
            idx
            for idx, col_name in enumerate(header)
            if not any(
                re.match(pattern, col_name) for pattern in METADATA_KEY_PII_PATTERNS
            )
        ]
        with open(output_path, "w", newline="", encoding="utf-8") as outfile:
            writer = csv.writer(outfile, delimiter=delimiter)

            filtered_header = [header[idx] for idx in columns_to_keep]
            writer.writerow(filtered_header)
            for row in reader:
                filtered_row = [anonymise(row[idx]) for idx in columns_to_keep]
                writer.writerow(filtered_row)


def process_json(input_path, output_path):
    """Process JSON files to deidentify PII, writing results line-by-line and omitting sensitive keys"""
    with open(input_path, "r") as infile, open(output_path, "w") as outfile:
        parser = ijson.parse(infile)
        # The stack holds a dictionary for each container with keys:
        #  'type': "object" or "array"
        #  'first': boolean flag, True if no item has been written yet.
        #  'pending_key': for objects, True if a key was written but its value not has not yet been written.
        stack = []
        keybuffer = None  # When set, skip all subelements

        for prefix, event, value in parser:
            if keybuffer and not prefix.startswith(keybuffer):
                keybuffer = None
            if keybuffer:
                continue

            if event == "start_map":
                if stack:
                    if stack[-1]["type"] == "object" and stack[-1].get("pending_key"):
                        outfile.write(":")
                        stack[-1]["pending_key"] = False
                    elif stack[-1]["type"] == "array" and not stack[-1]["first"]:
                        outfile.write(",")
                outfile.write("{")
                stack.append({"type": "object", "first": True, "pending_key": False})

            elif event == "end_map":
                outfile.write("}")
                stack.pop()
                if stack:
                    stack[-1]["first"] = False

            elif event == "start_array":
                if stack:
                    if stack[-1]["type"] == "object" and stack[-1].get("pending_key"):
                        outfile.write(":")
                        stack[-1]["pending_key"] = False
                    elif stack[-1]["type"] == "array" and not stack[-1]["first"]:
                        outfile.write(",")
                outfile.write("[")
                stack.append({"type": "array", "first": True})

            elif event == "end_array":
                outfile.write("]")
                stack.pop()
                if stack:
                    stack[-1]["first"] = False

            elif event == "map_key":
                # If the key matches a PII pattern, set the keybuffer to skip its subtree.
                if any(
                    re.match(pattern, value) for pattern in METADATA_KEY_PII_PATTERNS
                ):
                    keybuffer = f"{prefix}.{value}"
                    continue
                if stack and stack[-1]["type"] == "object":
                    if not stack[-1]["first"]:
                        outfile.write(",")
                    else:
                        stack[-1]["first"] = False
                    outfile.write(json.dumps(value))
                    stack[-1]["pending_key"] = True

            elif event in ("string", "number", "boolean", "null"):
                if stack:
                    if stack[-1]["type"] == "object" and stack[-1].get("pending_key"):
                        outfile.write(":")
                        stack[-1]["pending_key"] = False
                    elif stack[-1]["type"] == "array":
                        if not stack[-1]["first"]:
                            outfile.write(",")
                        else:
                            stack[-1]["first"] = False
                if event == "string":
                    outfile.write(json.dumps(anonymise(value)))
                else:
                    outfile.write(json.dumps(value))

        outfile.write("\n")


def process_flatfile(input_path, output_path):
    """Processes TXT files to deidentify PII, writing results line-by-line."""
    with open(input_path, "r") as infile, open(output_path, "w") as outfile:
        for line in infile:
            deidentified_line = anonymise(line)
            outfile.write(deidentified_line)


def deidentify_metadata(local_input_path, local_output_path):
    """Main function to process file from S3, deidentify, and upload back to S3."""

    if local_input_path.endswith(".json"):
        process_json(local_input_path, local_output_path)
    elif local_input_path.endswith(".txt"):
        process_flatfile(local_input_path, local_output_path)
    elif local_input_path.endswith(".csv"):
        process_tabular(local_input_path, local_output_path, delimiter=",")
    elif local_input_path.endswith(".tsv"):
        process_tabular(local_input_path, local_output_path, delimiter="\t")

    return True


def dynamodb_update_item(table_name, location, update_fields: dict):
    update_expression = "SET " + ", ".join(f"{k} = :{k}" for k in update_fields.keys())
    if "error_message" not in update_fields:
        update_expression += " REMOVE error_message"
    kwargs = {
        "TableName": table_name,
        "Key": {
            "vcfLocation": {"S": location},
        },
        "UpdateExpression": update_expression,
        "ExpressionAttributeValues": {f":{k}": v for k, v in update_fields.items()},
    }
    print(f"Calling dynamodb.update_item with kwargs: {json.dumps(kwargs)}")
    response = dynamodb.update_item(**kwargs)
    print(f"Received response: {json.dumps(response, default=str)}")


def update_deidentification_status(files_table, location, status):
    update_fields = {
        "deidentificationStatus": {
            "S": status,
        }
    }
    dynamodb_update_item(files_table, location, update_fields)


def log_error(files_table, location, error_message):
    update_fields = {
        "deidentificationStatus": {
            "S": "Error",
        },
        "error_message": {
            "S": error_message,
        },
    }
    dynamodb_update_item(files_table, location, update_fields)


def log_deidentification_status(
    projects_table: str, project_name: str, file_name: str, status: str
):
    if status == "Pending":
        update_expression = """
        ADD pending_files :file_name
        """
    else:
        update_expression = """
        DELETE pending_files :file_name
        """
    kwargs = {
        "TableName": projects_table,
        "Key": {
            "name": {"S": project_name},
        },
        "UpdateExpression": update_expression,
        "ExpressionAttributeValues": {
            ":file_name": {"SS": [file_name]},
        },
    }
    print(f"Calling dynamodb.update_item with kwargs: {json.dumps(kwargs)}")
    response = dynamodb.update_item(**kwargs)
    print(f"Received response: {json.dumps(response, default=str)}")


def log_projects_error(
    projects_table: str, project_name: str, file_name: str, error_message: str
):
    update_expression = """
    SET error_messages = list_append(if_not_exists(error_messages, :empty_list), :error_message)
    DELETE files :file_name
    """
    kwargs = {
        "TableName": projects_table,
        "Key": {
            "name": {"S": project_name},
        },
        "UpdateExpression": update_expression,
        "ExpressionAttributeValues": {
            ":error_message": {
                "L": [
                    {
                        "M": {
                            "file": {"S": file_name},
                            "error": {"S": error_message},
                        }
                    }
                ]
            },
            ":empty_list": {"L": []},
            ":file_name": {"SS": [file_name]},
        },
    }
    print(f"Calling dynamodb.update_item with kwargs: {json.dumps(kwargs)}")
    response = dynamodb.update_item(**kwargs)
    print(f"Received response: {json.dumps(response, default=str)}")


def s3_download(**kwargs: dict):
    print(f"Calling s3.download_file with kwargs: {json.dumps(kwargs)}")
    response = s3.download_file(**kwargs)
    print(f"Received response: {json.dumps(response, default=str)}")


def s3_upload(**kwargs: dict):
    print(f"Calling s3.upload_file with kwargs: {json.dumps(kwargs)}")
    response = s3.upload_file(**kwargs)
    print(f"Received response: {json.dumps(response, default=str)}")


def deidentify(
    input_bucket,
    output_bucket,
    projects_table,
    files_table,
    project,
    file_name,
    object_key,
):
    update_deidentification_status(
        files_table, f"{project}/project-files/{file_name}", "Pending"
    )
    log_deidentification_status(projects_table, project, file_name, "Pending")

    local_input_path = f"{WORKING_DIR}/input_{file_name}"
    local_output_path = f"{WORKING_DIR}/deidentified_{file_name}"

    s3.download_file(Bucket=input_bucket, Key=object_key, Filename=local_input_path)

    try:
        validate_file(local_input_path)
        print(f"Validation passed for {local_input_path}")
    except Exception as e:
        print(f"An error occurred when validating {object_key}: {e}")
        log_error(files_table, f"{project}/project-files/{file_name}", str(e))
        log_projects_error(projects_table, project, file_name, anonymise(str(e)))
        log_deidentification_status(projects_table, project, file_name, "Error")
        s3.delete_object(Bucket=input_bucket, Key=object_key)
        print("Exiting")
        return
    if any(
        object_key.endswith(suffix)
        for suffix in set(GENOMIC_SUFFIX_TYPES.keys()) | SAM_SUFFIXES
    ):
        try:
            if any(object_key.endswith(suffix) for suffix in SAM_SUFFIXES):
                if object_key.endswith(".bam"):
                    output_paths = anonymise_bam(local_input_path, local_output_path)
                elif object_key.endswith(".sam"):
                    output_paths = anonymise_sam(local_input_path, local_output_path)
                else:
                    raise (Exception("Unexpected SAM file suffix"))
            else:
                output_paths = anonymise_vcf(local_input_path, local_output_path)
        except (ProcessError, ParsingError) as e:
            print(f"An error occurred while deidentifying {object_key}: {e}")
            log_error(files_table, f"{project}/project-files/{file_name}", str(e))
            log_projects_error(projects_table, project, file_name, anonymise(str(e)))
            log_deidentification_status(projects_table, project, file_name, "Error")
            s3.delete_object(Bucket=input_bucket, Key=object_key)
            print("Exiting")
            return
    elif any(object_key.endswith(suffix) for suffix in QUIETLY_SKIP_SUFFIXES):
        print("We'd rather create this file again from the source file, skipping")
        return
    elif any(object_key.endswith(suffix) for suffix in METADATA_SUFFIXES):
        try:
            deidentify_metadata(local_input_path, local_output_path)
        except Exception as e:
            print(f"An error occurred while deidentifying {object_key}: {e}")
            log_error(files_table, f"{project}/project-files/{file_name}", str(e))
            log_projects_error(projects_table, project, file_name, anonymise(str(e)))
            log_deidentification_status(projects_table, project, file_name, "Error")
            s3.delete_object(Bucket=input_bucket, Key=object_key)
            print("Exiting")
            return
        output_paths = [local_output_path]
    else:
        raise ValueError(f"File {object_key} does not have a recognised suffix")

    output_key = object_key.split("/", 1)[1]
    base_path = output_paths[0]
    s3.upload_file(Bucket=output_bucket, Key=output_key, Filename=output_paths[0])
    for extra_file in output_paths[1:]:
        assert extra_file.startswith(
            base_path
        ), f"Extra file {extra_file} does not match output path {base_path}"
        s3.upload_file(
            Bucket=output_bucket,
            Key=f"{output_key}{extra_file[len(base_path):]}",
            Filename=extra_file,
        )
    s3.delete_object(Bucket=input_bucket, Key=object_key)

    update_deidentification_status(
        files_table, f"{project}/project-files/{file_name}", "Anonymised"
    )
    log_deidentification_status(projects_table, project, file_name, "Anonymised")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-bucket", required=True)
    parser.add_argument("--output-bucket", required=True)
    parser.add_argument("--projects-table", required=True)
    parser.add_argument("--files-table", required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--file-name", required=True)
    parser.add_argument("--object-key", required=True)
    args = parser.parse_args()
    deidentify(
        args.input_bucket,
        args.output_bucket,
        args.projects_table,
        args.files_table,
        args.project,
        args.file_name,
        args.object_key,
    )
