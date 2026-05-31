#!/usr/bin/env bash
set -euo pipefail

PYTHON="${PYTHON:-python3}"

rm -rf build dist astars.egg-info

"${PYTHON}" -m build --sdist --wheel
"${PYTHON}" -m twine check dist/*
