#!/usr/bin/env bash
# =============================================================================
# stop.sh — Stop the Docker stack
# =============================================================================
# Usage:
#   ./scripts/stop.sh           # docker compose down (keeps volumes)
#   ./scripts/stop.sh --volumes # also delete MySQL data (DANGEROUS)
#   ./scripts/stop.sh --orphans # also remove orphan containers
# =============================================================================
export PATH="/usr/bin:/bin:/usr/local/bin:$PATH"
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR"

GREEN='\033[0;32m'
log() { echo -e "${GREEN}[stop]${NC} $*"; }

if [ "$1" = "--volumes" ] || [ "$1" = "-v" ]; then
    echo
    echo "WARNING: --volumes will DELETE the MySQL data volume."
    echo "         All crawled rankings will be lost."
    echo
    read -p "Type 'yes' to confirm: " ans
    if [ "$ans" != "yes" ]; then
        echo "Aborted."
        exit 1
    fi
fi

log "Stopping services..."
docker compose down "$@"
log "Done. Run ./scripts/start.sh to bring the stack back up."
