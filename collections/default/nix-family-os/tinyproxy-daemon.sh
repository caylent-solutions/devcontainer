#!/usr/bin/env bash
# tinyproxy daemon management script for macOS
# Manages tinyproxy as a background daemon for devcontainer proxy support
#
# Usage: ./tinyproxy-daemon.sh {start|stop|restart|status}

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/tinyproxy.conf"
LOG_DIR="${HOME}/.devcontainer-proxy"
PID_FILE="${LOG_DIR}/tinyproxy.pid"
LOG_FILE="${LOG_DIR}/tinyproxy.log"
PROXY_PORT=3128

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ${NC}  $1"
}

log_success() {
    echo -e "${GREEN}✓${NC}  $1"
}

log_warn() {
    echo -e "${YELLOW}⚠${NC}  $1"
}

log_error() {
    echo -e "${RED}✗${NC}  $1" >&2
}

exit_with_error() {
    log_error "$1"
    exit 1
}

# Create log directory if it doesn't exist
mkdir -p "${LOG_DIR}"

# Check if tinyproxy is installed
check_tinyproxy() {
    if ! command -v tinyproxy &> /dev/null; then
        exit_with_error "tinyproxy is not installed. Install it with: brew install tinyproxy"
    fi
}

# Get PID if running
get_pid() {
    if [[ -f "${PID_FILE}" ]]; then
        local pid=$(cat "${PID_FILE}")
        if ps -p "${pid}" > /dev/null 2>&1; then
            echo "${pid}"
            return 0
        else
            # Stale PID file
            rm -f "${PID_FILE}"
        fi
    fi
    return 1
}

# Start tinyproxy
start_proxy() {
    log_info "Starting tinyproxy daemon..."

    check_tinyproxy

    # Check if already running
    if get_pid > /dev/null 2>&1; then
        local pid=$(get_pid)
        log_warn "tinyproxy is already running (PID: ${pid})"
        return 0
    fi

    # Check if config file exists
    if [[ ! -f "${CONFIG_FILE}" ]]; then
        exit_with_error "Config file not found: ${CONFIG_FILE}"
    fi

    log_info "Config file: ${CONFIG_FILE}"
    log_info "Listening on: 0.0.0.0:${PROXY_PORT}"
    log_info "Upstream proxy: edge.surepath.ai:8080"
    log_info "Log file: ${LOG_FILE}"

    # Start tinyproxy
    tinyproxy -c "${CONFIG_FILE}"

    # Wait a moment and verify it started
    sleep 2

    if get_pid > /dev/null 2>&1; then
        local pid=$(get_pid)
        log_success "tinyproxy started successfully (PID: ${pid})"

        # Test if port is accessible
        if lsof -iTCP:${PROXY_PORT} -sTCP:LISTEN > /dev/null 2>&1; then
            log_success "Proxy is listening on port ${PROXY_PORT}"
        else
            log_warn "Proxy started but port ${PROXY_PORT} may not be accessible"
        fi

        log_info ""
        log_info "To view logs in real-time:"
        log_info "  tail -f ${LOG_FILE}"
        log_info ""
        log_info "To check status:"
        log_info "  ./tinyproxy-daemon.sh status"
    else
        exit_with_error "Failed to start tinyproxy. Check logs: ${LOG_FILE}"
    fi
}

# Stop tinyproxy
stop_proxy() {
    log_info "Stopping tinyproxy daemon..."

    if ! get_pid > /dev/null 2>&1; then
        log_warn "tinyproxy is not running"
        return 0
    fi

    local pid=$(get_pid)
    log_info "Sending TERM signal to PID ${pid}..."

    kill "${pid}" 2>/dev/null || true

    # Wait for process to stop
    local count=0
    while ps -p "${pid}" > /dev/null 2>&1 && [[ ${count} -lt 10 ]]; do
        sleep 0.5
        count=$((count + 1))
    done

    if ps -p "${pid}" > /dev/null 2>&1; then
        log_warn "Process didn't stop gracefully, sending KILL signal..."
        kill -9 "${pid}" 2>/dev/null || true
        sleep 1
    fi

    rm -f "${PID_FILE}"
    log_success "tinyproxy stopped"
}

# Restart tinyproxy
restart_proxy() {
    log_info "Restarting tinyproxy daemon..."
    stop_proxy
    sleep 1
    start_proxy
}

# Show status
show_status() {
    log_info "Checking tinyproxy daemon status..."
    echo ""

    if get_pid > /dev/null 2>&1; then
        local pid=$(get_pid)
        log_success "tinyproxy is RUNNING (PID: ${pid})"

        # Check if port is listening
        if lsof -iTCP:${PROXY_PORT} -sTCP:LISTEN -P | grep -q "${pid}"; then
            log_success "Listening on port ${PROXY_PORT}"
        else
            log_warn "Process running but not listening on port ${PROXY_PORT}"
        fi

        # Show recent logs
        if [[ -f "${LOG_FILE}" ]]; then
            echo ""
            log_info "Last log entries (last 20 lines):"
            echo "────────────────────────────────────────"
            tail -20 "${LOG_FILE}"
            echo "────────────────────────────────────────"
        fi
    else
        log_warn "tinyproxy is NOT RUNNING"

        # Show last log entries if available
        if [[ -f "${LOG_FILE}" ]]; then
            echo ""
            log_info "Last run log entries (last 20 lines):"
            echo "────────────────────────────────────────"
            tail -20 "${LOG_FILE}" 2>/dev/null || echo "(no logs)"
            echo "────────────────────────────────────────"
        fi

        echo ""
        log_info "To start the proxy:"
        log_info "  ./tinyproxy-daemon.sh start"
    fi
}

# Main command handler
case "${1:-}" in
    start)
        start_proxy
        ;;
    stop)
        stop_proxy
        ;;
    restart)
        restart_proxy
        ;;
    status)
        show_status
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        echo ""
        echo "Commands:"
        echo "  start    Start tinyproxy daemon"
        echo "  stop     Stop tinyproxy daemon"
        echo "  restart  Restart tinyproxy daemon"
        echo "  status   Show daemon status and logs"
        exit 1
        ;;
esac
