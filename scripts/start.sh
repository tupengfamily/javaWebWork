#!/usr/bin/env bash
# =============================================================================
# start.sh — Deploy the full stack with Docker Compose
# =============================================================================
# Usage:
#   ./scripts/start.sh                  # docker compose up -d
#   ./scripts/start.sh --build          # build first, then up
#   ./scripts/start.sh --no-cache       # build with no cache, then up
#   ./scripts/start.sh [service...]     # up only specific service(s)
# =============================================================================
export PATH="/usr/bin:/bin:/usr/local/bin:$PATH"
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'
log()   { echo -e "${GREEN}[start]${NC} $*"; }
warn()  { echo -e "${YELLOW}[start]${NC} $*"; }

# --- preflight ---
if ! command -v docker >/dev/null 2>&1; then
    echo "Error: docker not found. Install Docker first."; exit 1
fi
if ! docker compose version >/dev/null 2>&1; then
    echo "Error: docker compose v2 not installed."; exit 1
fi
if [ ! -f "$ROOT_DIR/.env" ]; then
    warn ".env not found. Copying from .env.example (edit it first for prod!)"
    cp "$ROOT_DIR/.env.example" "$ROOT_DIR/.env"
fi

# --- build if requested ---
build_first=0
for arg in "$@"; do
    case "$arg" in
        --build|--rebuild|--no-cache) build_first=1 ;;
    esac
done
if [ "$build_first" = "1" ]; then
    log "Building images first..."
    docker compose build "$@"
fi

# --- up ---
log "Starting services..."
docker compose up -d "$@"

echo
log "Waiting for MySQL healthcheck (up to 60s)..."
for i in $(seq 1 30); do
    if docker compose exec -T mysql mysqladmin ping -h 127.0.0.1 -uroot \
            -p"$(grep '^MYSQL_ROOT_PASSWORD=' .env | cut -d= -f2-)" \
            --silent 2>/dev/null; then
        log "MySQL ready."
        break
    fi
    sleep 2
done

echo
echo "=========================================="
echo "  Services started!"
echo "=========================================="
echo "  Frontend:   http://localhost"
echo "  Backend:    http://localhost:8080/api"
echo "  Swagger:    http://localhost:8080/doc.html"
echo "  MySQL:      localhost:\$(grep ^MYSQL_PORT= .env | cut -d= -f2)"
echo "  Login:      admin / admin123"
echo "=========================================="
echo "  Logs:       ./scripts/build.sh --no-cache && docker compose logs -f"
echo "  Stop:       ./scripts/stop.sh"
echo "=========================================="
