#!/usr/bin/env bash
# =============================================================================
# dev.sh — Local dev mode (no Docker)
# =============================================================================
# Starts backend (Spring Boot jar) + crawler (python main.py) + frontend (Vite).
# Requires: MySQL 8.0 running locally (or via docker run on $MYSQL_PORT).
#
# Usage:
#   ./scripts/dev.sh start    [backend|crawler|frontend|all]  (default: all)
#   ./scripts/dev.sh stop     [backend|crawler|frontend|all]  (default: all)
#   ./scripts/dev.sh status
#   ./scripts/dev.sh restart  [target]
#   ./scripts/dev.sh logs     [backend|crawler|frontend]
# =============================================================================
export PATH="/usr/bin:/bin:/usr/local/bin:$PATH"
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR"

LOGS_DIR="$ROOT_DIR/logs"
PIDS_DIR="$ROOT_DIR/.pids"
mkdir -p "$LOGS_DIR" "$PIDS_DIR"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
log()   { echo -e "${GREEN}[dev]${NC} $*"; }
warn()  { echo -e "${YELLOW}[dev]${NC} $*"; }

# Pick the best Java: JAVA_HOME first, then MS OpenJDK 17, then PATH.
detect_java() {
    if [ -n "$JAVA_HOME" ] && [ -x "$JAVA_HOME/bin/java" ]; then
        echo "$JAVA_HOME/bin/java"
    elif [ -x "/c/Program Files/Microsoft/jdk-17.0.19.10-hotspot/bin/java" ]; then
        echo "/c/Program Files/Microsoft/jdk-17.0.19.10-hotspot/bin/java"
    else
        command -v java
    fi
}

start_one() {
    local name="$1"
    case "$name" in
      backend)
        if [ ! -f "$ROOT_DIR/backend/target/app.jar" ]; then
            log "Building backend jar (first run)..."
            (cd "$ROOT_DIR/backend" && mvn -B clean package -DskipTests) || return 1
        fi
        log "Starting backend (Java 17) on :8080"
        (cd "$ROOT_DIR/backend" && \
            nohup "$(detect_java)" -XX:MaxRAMPercentage=75.0 \
                -jar target/app.jar --spring.profiles.active=dev \
                > "$LOGS_DIR/backend.log" 2>&1 &
            echo $! > "$PIDS_DIR/backend.pid")
        ;;
      crawler)
        log "Starting crawler"
        (cd "$ROOT_DIR/crawler" && \
            DB_HOST="${DB_HOST:-localhost}" \
            DB_PORT="${DB_PORT:-${MYSQL_PORT:-3306}}" \
            DB_USER="${DB_USER:-novel}" \
            DB_PASSWORD="${DB_PASSWORD:-novel123}" \
            DB_NAME="${DB_NAME:-novel_rank}" \
            nohup python main.py \
                > "$LOGS_DIR/crawler.log" 2>&1 &
            echo $! > "$PIDS_DIR/crawler.pid")
        ;;
      frontend)
        if [ ! -d "$ROOT_DIR/frontend/node_modules" ]; then
            log "Installing frontend deps (first run)..."
            (cd "$ROOT_DIR/frontend" && npm install) || return 1
        fi
        log "Starting Vite dev server on :5173"
        (cd "$ROOT_DIR/frontend" && \
            nohup npm run dev -- --host 0.0.0.0 --port 5173 \
                > "$LOGS_DIR/frontend.log" 2>&1 &
            echo $! > "$PIDS_DIR/frontend.pid")
        ;;
    esac
}

stop_one() {
    local name="$1" pidfile="$PIDS_DIR/$name.pid"
    if [ -f "$pidfile" ]; then
        local pid; pid=$(cat "$pidfile" 2>/dev/null || echo)
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            # Try to kill the whole process group
            kill -TERM "$pid" 2>/dev/null || true
            sleep 1
            kill -KILL "$pid" 2>/dev/null || true
            log "stopped $name (pid $pid)"
        else
            warn "$name not running (stale pid file)"
        fi
        rm -f "$pidfile"
    else
        warn "$name not running"
    fi
}

status_one() {
    local name="$1" pidfile="$PIDS_DIR/$name.pid"
    if [ -f "$pidfile" ] && kill -0 "$(cat "$pidfile" 2>/dev/null)" 2>/dev/null; then
        printf "  [OK]   %-9s pid %s\n" "$name" "$(cat "$pidfile")"
    else
        printf "  [--]   %-9s\n" "$name"
    fi
}

case "${1:-status}" in
    start)
        target="${2:-all}"
        log "starting: $target"
        for n in backend crawler frontend; do
            [ "$target" = "all" ] || [ "$target" = "$n" ] || continue
            start_one "$n"
        done
        echo
        log "Frontend:  http://localhost:5173"
        log "Backend:   http://localhost:8080/api"
        log "Swagger:   http://localhost:8080/doc.html"
        log "Logs:      $LOGS_DIR/"
        ;;
    stop)
        target="${2:-all}"
        for n in backend crawler frontend; do
            [ "$target" = "all" ] || [ "$target" = "$n" ] || continue
            stop_one "$n"
        done
        ;;
    status)
        log "status:"
        for n in backend crawler frontend; do status_one "$n"; done
        ;;
    restart)
        "$0" stop "${2:-all}"
        "$0" start "${2:-all}"
        ;;
    logs)
        target="${2:-backend}"
        pidfile="$PIDS_DIR/$target.pid"
        logfile="$LOGS_DIR/$target.log"
        if [ -f "$logfile" ]; then
            tail -f "$logfile"
        else
            warn "no log file: $logfile"
            exit 1
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop|status|restart|logs} [target]"
        echo "  target = backend|crawler|frontend|all  (default: all)"
        exit 1
        ;;
esac
