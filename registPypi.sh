#!/usr/bin/env bash
set -euo pipefail

PYTHON="${PYTHON:-python3}"
repository="${1:-}"

if [[ "${repository}" != "testpypi" && "${repository}" != "pypi" ]]; then
  echo "Usage: $0 testpypi|pypi" >&2
  exit 2
fi

if ! compgen -G "dist/*" > /dev/null; then
  echo "dist/ is empty. Run ./checkPypi.sh first." >&2
  exit 1
fi

"${PYTHON}" -m twine check dist/*
"${PYTHON}" -m twine upload --repository "${repository}" dist/*
