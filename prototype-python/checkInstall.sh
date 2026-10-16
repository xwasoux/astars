#!/usr/bin/env bash
set -euo pipefail

PYTHON="${PYTHON:-python3}"
MODE="${1:-dist}"
VENV_DIR="${VENV_DIR:-/private/tmp/astars-clean-install}"
PACKAGE_NAME="${PACKAGE_NAME:-astars}"
ASTARS_VERSION="${ASTARS_VERSION:-}"
WHEEL_PATH=""

usage() {
  cat >&2 <<EOF
Usage: $0 dist|pypi|testpypi

Modes:
  dist      Install the single wheel in dist/ into a clean venv.
  pypi      Install ${PACKAGE_NAME}==ASTARS_VERSION from PyPI.
  testpypi  Install ${PACKAGE_NAME}==ASTARS_VERSION from TestPyPI, using PyPI for dependencies.

Environment:
  PYTHON          Python executable used to create the clean venv. Default: python3
  VENV_DIR        Clean venv path. Default: /private/tmp/astars-clean-install
  ASTARS_VERSION  Required for pypi and testpypi modes. Also asserted by the smoke test when set.
EOF
}

require_python() {
  if ! command -v "${PYTHON}" >/dev/null 2>&1; then
    echo "error: Python executable not found: ${PYTHON}" >&2
    echo "Set PYTHON=/path/to/python or install python3." >&2
    exit 127
  fi
}

require_version() {
  if [[ -z "${ASTARS_VERSION}" ]]; then
    echo "error: ASTARS_VERSION is required for ${MODE} mode." >&2
    echo "Example: ASTARS_VERSION=0.1.0 $0 ${MODE}" >&2
    exit 2
  fi
}

require_safe_venv_dir() {
  case "${VENV_DIR}" in
    ""|"/"|"/tmp"|"/private"|"/private/tmp")
      echo "error: unsafe VENV_DIR: ${VENV_DIR}" >&2
      exit 2
      ;;
  esac

  if [[ -n "${HOME:-}" && "${VENV_DIR}" == "${HOME}" ]]; then
    echo "error: unsafe VENV_DIR: ${VENV_DIR}" >&2
    exit 2
  fi

  if [[ "${VENV_DIR}" == "${PWD}" ]]; then
    echo "error: unsafe VENV_DIR: ${VENV_DIR}" >&2
    exit 2
  fi
}

require_dist_wheel() {
  shopt -s nullglob
  local wheels=(dist/*.whl)
  shopt -u nullglob

  if (( ${#wheels[@]} == 0 )); then
    echo "error: dist/ has no wheel. Run ./checkPypi.sh first." >&2
    exit 1
  fi

  if (( ${#wheels[@]} > 1 )); then
    echo "error: dist/ has multiple wheels. Remove stale artifacts and run ./checkPypi.sh again." >&2
    printf 'found: %s\n' "${wheels[@]}" >&2
    exit 1
  fi

  WHEEL_PATH="${wheels[0]}"
}

prepare_venv() {
  rm -rf "${VENV_DIR}"
  "${PYTHON}" -m venv "${VENV_DIR}"
  VENV_PYTHON="${VENV_DIR}/bin/python"
  "${VENV_PYTHON}" -m pip install --upgrade pip
}

install_from_dist() {
  "${VENV_PYTHON}" -m pip install --no-cache-dir "${WHEEL_PATH}"
}

install_from_pypi() {
  require_version
  "${VENV_PYTHON}" -m pip install --no-cache-dir "${PACKAGE_NAME}==${ASTARS_VERSION}"
}

install_from_testpypi() {
  require_version
  "${VENV_PYTHON}" -m pip install \
    --no-cache-dir \
    --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    "${PACKAGE_NAME}==${ASTARS_VERSION}"
}

run_smoke_test() {
  ASTARS_EXPECTED_VERSION="${ASTARS_VERSION}" "${VENV_PYTHON}" - <<'PY'
import os

import astars

unit = astars.parse_str("def hello(name):\n    return name\n", lang="python")
function = unit.find(kind="FunctionDef")[0]

assert unit.root.kind == "Module"
assert function.kind == "FunctionDef"
assert unit.source_of(function).startswith("def hello")

expected_version = os.environ.get("ASTARS_EXPECTED_VERSION")
if expected_version:
    assert astars.__version__ == expected_version, (
        f"expected astars {expected_version}, got {astars.__version__}"
    )

print(astars.__version__)
print(unit.root.kind)
print(function.kind)
PY
}

if [[ "${MODE}" != "dist" && "${MODE}" != "pypi" && "${MODE}" != "testpypi" ]]; then
  usage
  exit 2
fi

require_python

case "${MODE}" in
  dist)
    require_dist_wheel
    ;;
  pypi|testpypi)
    require_version
    ;;
esac

require_safe_venv_dir
prepare_venv

case "${MODE}" in
  dist)
    install_from_dist
    ;;
  pypi)
    install_from_pypi
    ;;
  testpypi)
    install_from_testpypi
    ;;
esac

run_smoke_test
