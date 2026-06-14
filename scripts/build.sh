#!/usr/bin/env bash
# =============================================================================
# build.sh — Build Docker images (does not start them)
# =============================================================================
# Usage:
#   ./scripts/build.sh                  # build all services
#   ./scripts/build.sh backend frontend # build specific services
#   ./scripts/build.sh --no-cache       # pass through extra flags
# =============================================================================
export PATH="/usr/bin:/bin:/usr/local/bin:$PATH"
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR"

GREEN='\033[0;32m'
log() { echo -e "${GREEN}[build]${NC} $*"; }

if ! command -v docker >/dev/null 2>&1; then
    echo "Error: docker not found. Install Docker first."
    exit 1
fi

log "Building images: $*"
docker compose build "$@"
log "Done. Run ./scripts/start.sh to deploy."
