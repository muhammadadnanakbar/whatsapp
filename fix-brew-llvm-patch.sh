#!/usr/bin/env bash
# Fixes: ENOENT patch file when installing qemu (via gnutls -> llvm)
set -euo pipefail

PATCH_URL="https://github.com/llvm/llvm-project/compare/1381ad497b9a6d3da630cbef53cbfa9ddf117bb6...40a8c7c0ff3f688b690e4c74db734de67f0f89e9.diff"
CACHE_DIR="${HOME}/Library/Caches/Homebrew/downloads"
PATCH_FILE="${CACHE_DIR}/373708817c634b56c0b875aba22b6d707aa53a17bb24ea9850a44bf2e00907a5--1381ad497b9a6d3da630cbef53cbfa9ddf117bb6...40a8c7c0ff3f688b690e4c74db734de67f0f89e9.diff"

mkdir -p "$CACHE_DIR"
echo "Downloading LLVM patch file..."
curl -fsSL "$PATCH_URL" -o "$PATCH_FILE"
ls -la "$PATCH_FILE"

rm -f /usr/local/var/homebrew/locks/*.lock 2>/dev/null || true

export HOMEBREW_NO_AUTO_UPDATE=1
echo ""
echo "Installing qemu (LLVM build can take 1-2+ hours on macOS 12)..."
brew install qemu

echo ""
qemu-img --version
echo "Success! Next:"
echo "  cd $(dirname "$0")"
echo "  colima start --cpu 2 --memory 4"
echo "  ./setup-waha.sh"
