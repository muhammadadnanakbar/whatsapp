#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if ! python3 -c "import fastapi" 2>/dev/null; then
  python3 -m pip install -r requirements.txt
fi

export PYTHONPATH="$(pwd)"
echo "Starting app at http://localhost:8001"
python3 -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8001
