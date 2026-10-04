#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
CC=gcc CXX=g++ CMAKE_BUILD_PARALLEL_LEVEL=2 CMAKE_ARGS='-DGGML_NATIVE=OFF -DGGML_CUDA=OFF' .venv/bin/python -m pip install -r requirements.txt
echo 'Setup complete. Optional: .venv/bin/python scripts/download_model.py'
echo 'Start: .venv/bin/python -m uvicorn studio.app:app --host 0.0.0.0 --port 8000'
