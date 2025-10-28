#!/usr/bin/env bash
set -euo pipefail

python -m venv .venv
source .venv/bin/activate

# Ensure modern build tooling (fixes 'setuptools.build_meta' errors on Py3.12)
python -m pip install --upgrade pip setuptools wheel

PYV=$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "Detected Python ${PYV}"

if python - <<'PYCHK'
import sys
print(int((sys.version_info.major, sys.version_info.minor) >= (3,12)))
PYCHK
then
  echo "Using requirements-py312.txt"
  pip install -r requirements-py312.txt
pip install -e .
else
  echo "Using requirements.txt"
  pip install -r requirements.txt
pip install -e .
fi

mkdir -p .data/msmarco configs/generated results/raw results/agg results/figures tables
cp .env.example .env || true
echo "Environment ready. Activate with: source .venv/bin/activate"
