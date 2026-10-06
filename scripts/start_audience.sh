#!/usr/bin/env bash
# All three portfolio apps share one process. Audience reports need no model download.
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ ! -x .venv/bin/python ]]; then bash scripts/setup.sh; fi
.venv/bin/python -m pip install -r requirements-membership.txt -r requirements-audience.txt
if [[ ! -f docs/audience/results.json ]]; then
  echo 'Measured snapshot missing; download and build it explicitly.' >&2
  exit 1
fi
# Optional refresh: python -m scripts.download_audience && python -m scripts.build_audience
# Optional Qwen: .venv/bin/python scripts/download_model.py
exec .venv/bin/python -m uvicorn studio.app:app --host 0.0.0.0 --port "${PORT:-8000}"
