#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
PROJECT_DIR="$(pwd)"

echo "=== WhatsApp Group Copier — WAHA setup ==="

# 1. QEMU (required for Colima on macOS 12)
if ! command -v qemu-img &>/dev/null; then
  echo "Installing QEMU (required — first time can take 30–60 min on macOS 12)..."
  echo "Leave this terminal open until it finishes."
  brew install qemu
fi

# 2. Docker via Colima (macOS 12 cannot use latest Docker Desktop)
if ! command -v docker &>/dev/null; then
  echo "Installing Colima + Docker..."
  brew install colima docker docker-compose
fi

if ! colima status 2>/dev/null | grep -q "Running"; then
  echo "Starting Colima (first time may take a few minutes)..."
  colima start --cpu 2 --memory 4
fi

echo "Docker: $(docker --version)"

# 2. Generate WAHA credentials
mkdir -p waha-env sessions
if [[ ! -f waha-env/.env ]]; then
  echo "Generating WAHA API key and dashboard password..."
  docker pull devlikeapro/waha:latest
  docker run --rm -v "${PROJECT_DIR}/waha-env:/app/env" devlikeapro/waha:latest init-waha /app/env
fi

WAHA_KEY="$(grep '^WAHA_API_KEY=' waha-env/.env | cut -d= -f2- | tr -d '"' | tr -d "'")"
if [[ -z "${WAHA_KEY}" ]]; then
  WAHA_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(16))')"
  echo "WAHA_API_KEY=${WAHA_KEY}" >> waha-env/.env
fi

# 3. Sync app .env
grep -q '^WAHA_API_KEY=' .env && sed -i.bak "s|^WAHA_API_KEY=.*|WAHA_API_KEY=${WAHA_KEY}|" .env || echo "WAHA_API_KEY=${WAHA_KEY}" >> .env
rm -f .env.bak

# 4. Start WAHA
echo "Starting WAHA on http://localhost:3000 ..."
docker compose up -d waha

echo ""
echo "=== Done ==="
echo "WAHA_API_KEY=${WAHA_KEY}"
echo ""
echo "Next steps:"
echo "  1. Open http://localhost:3000/dashboard"
echo "  2. Connect with API key above"
echo "  3. Start session 'default' and scan QR with WhatsApp (+923034992699)"
echo "  4. Run: ./start-app.sh"
echo "  5. Open http://localhost:8001"
