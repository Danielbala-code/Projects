#!/usr/bin/env bash
# One process serves both portfolio projects and shares one Qwen instance.
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ ! -x .venv/bin/python ]]; then
  bash scripts/setup.sh
fi
.venv/bin/python -m pip install -r requirements-membership.txt
.venv/bin/python -m scripts.download_embeddings
.venv/bin/python scripts/download_model.py
exec .venv/bin/python -m uvicorn studio.app:app --host 0.0.0.0 --port "${PORT:-8000}"
