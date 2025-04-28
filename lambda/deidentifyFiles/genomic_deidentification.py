import json
import subprocess

from common import anonymise, GENOMIC_SUFFIX_TYPES, WORKING_DIR

ANNOTATION_PATH = "annotation.vcf.gz"
BGZIPPED_PATH = "bgzipped.bcf.gz"
HEADER_PATH = "header.vcf"
MAX_LINES_PER_PRINT = 100

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
