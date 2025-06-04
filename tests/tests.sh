#!/usr/bin/bash

set -e

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

cd "$SCRIPT_DIR"

pytest -p no:warnings -vv ./admin/
pytest -p no:warnings -vv ./dataportal/
pytest -p no:warnings -vv ./beacon/
