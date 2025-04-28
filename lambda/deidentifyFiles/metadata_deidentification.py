import csv
import json
import re

import ijson

from common import anonymise

METADATA_KEY_PII_PATTERNS = [
    r"(?i)\b(?:(?:full|first|last|middle|given|family|sur)[_ -]?name|nama(?:[_ -](?:lengkap|depan|belakang|tengah))?|name|nama|surname)\b",
    r"(?i)\b(?:(?:plate|license|vehicle|registration|number)_(?:plate|number|nopol|polisi|registrasi)|(?:nomor|plat)_(?:plat|nomor|polisi|registrasi)|nopol(?:_id)?|vehicle_nopol|registration_nopol|plat_number|plateno)\b",
]


def anonymise_json(input_path, output_path):
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


def anonymise_tabular(input_path, output_path, delimiter):
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


def anonymise_txt(input_path, output_path):
    """Processes TXT files to deidentify PII, writing results line-by-line."""
    with open(input_path, "r") as infile, open(output_path, "w") as outfile:
        for line in infile:
            deidentified_line = anonymise(line)
            outfile.write(deidentified_line)
