#!/usr/bin/env bash
set -euo pipefail

PYTHON="${PYTHON:-python3}"

usage_release_env() {
  cat >&2 <<EOF
Install release dependencies with:
  ${PYTHON} -m pip install -e ".[release]"

Or run this script with a Python that already has release tools:
  PYTHON=/path/to/python $0
EOF
}

require_python() {
  if ! command -v "${PYTHON}" >/dev/null 2>&1; then
    echo "error: Python executable not found: ${PYTHON}" >&2
    echo "Set PYTHON=/path/to/python or install python3." >&2
    exit 127
  fi
}

require_module() {
  local module="$1"

  if ! "${PYTHON}" -c "import ${module}" >/dev/null 2>&1; then
    echo "error: missing Python module: ${module}" >&2
    usage_release_env
    exit 1
  fi
}

require_python
require_module build
require_module twine

rm -rf build dist astars.egg-info

"${PYTHON}" -m build --sdist --wheel
"${PYTHON}" -m twine check dist/*
