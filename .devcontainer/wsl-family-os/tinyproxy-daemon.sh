#!/usr/bin/env bash
# tinyproxy daemon management script for Windows / WSL host
# Manages tinyproxy as a background daemon on the HOST OS (WSL) for devcontainer proxy support
#
# Required environment variables:
#   TINYPROXY_UPSTREAM_HOST       - Upstream proxy hostname (e.g., edge.surepath.ai)
#   TINYPROXY_UPSTREAM_PORT       - Upstream proxy port (e.g., 8080)
#   TINYPROXY_PORT                - Listen port (e.g., 3128)
#   TINYPROXY_READINESS_TIMEOUT   - Startup readiness timeout in seconds (e.g., 10)
#   TINYPROXY_STOP_TIMEOUT        - Graceful stop timeout in seconds (e.g., 10)
#
# Usage: ./tinyproxy-daemon.sh {start|stop|restart|status}

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_FILE="${SCRIPT_DIR}/tinyproxy.conf.template"
LOG_DIR="${HOME}/.devcontainer-proxy"
RUNTIME_CONFIG="${LOG_DIR}/tinyproxy.conf"
PID_FILE="${LOG_DIR}/tinyproxy.pid"
LOG_FILE="${LOG_DIR}/tinyproxy.log"

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

# Detect the user's shell rc file for guidance
detect_shell_rc() {
    local current_shell="${SHELL:-}"
    case "${current_shell}" in
        */zsh)  echo "${HOME}/.zshrc" ;;
        */bash) echo "${HOME}/.bashrc" ;;
        *)      echo "" ;;
    esac
}

# Print guidance for setting a missing environment variable
print_env_guidance() {
    local var_name="$1"
    local example_value="$2"
    local rc_file
    rc_file="$(detect_shell_rc)"

    log_error "${var_name} is not set."
    echo "" >&2
    echo "  Export it before running this script:" >&2
    echo "    export ${var_name}=${example_value}" >&2
    echo "" >&2
    if [[ -n "${rc_file}" ]]; then
        echo "  For persistence, add it to ${rc_file}:" >&2
        echo "    echo 'export ${var_name}=${example_value}' >> ${rc_file}" >&2
    else
        echo "  For persistence, add it to your shell rc file (~/.bashrc or ~/.zshrc):" >&2
        echo "    echo 'export ${var_name}=${example_value}' >> ~/.bashrc  # or ~/.zshrc" >&2
    fi
}

# Validate all required environment variables are set
validate_required_env() {
    local missing=0

    if [[ -z "${TINYPROXY_UPSTREAM_HOST:-}" ]]; then
        print_env_guidance "TINYPROXY_UPSTREAM_HOST" "edge.surepath.ai"
        missing=1
    fi

    if [[ -z "${TINYPROXY_UPSTREAM_PORT:-}" ]]; then
        print_env_guidance "TINYPROXY_UPSTREAM_PORT" "8080"
        missing=1
    fi

    if [[ -z "${TINYPROXY_PORT:-}" ]]; then
        print_env_guidance "TINYPROXY_PORT" "3128"
        missing=1
    fi

    if [[ -z "${TINYPROXY_READINESS_TIMEOUT:-}" ]]; then
        print_env_guidance "TINYPROXY_READINESS_TIMEOUT" "10"
        missing=1
    fi

    if [[ -z "${TINYPROXY_STOP_TIMEOUT:-}" ]]; then
        print_env_guidance "TINYPROXY_STOP_TIMEOUT" "10"
        missing=1
    fi

    if [[ ${missing} -ne 0 ]]; then
        exit 1
    fi
}

# Detect if running inside a Docker container and warn the user
warn_if_in_container() {
    local in_container=false

    if [[ -f "/.dockerenv" ]]; then
        in_container=true
    elif grep -qE '(/docker/|/lxc/)' /proc/1/cgroup 2>/dev/null; then
        in_container=true
    fi

    if [[ "${in_container}" == "true" ]]; then
        log_warn "It looks like you are running inside a Docker container."
        log_warn "This script is intended to run on the HOST operating system (Windows/WSL),"
        log_warn "not inside the devcontainer. The devcontainer connects to this proxy via host.docker.internal."
        echo ""
        read -rp "Do you still want to continue? [y/N] " response
        case "${response}" in
            [yY][eE][sS]|[yY])
                log_info "Continuing inside container as requested..."
                ;;
            *)
                exit_with_error "Aborted. Run this script on your WSL host instead."
                ;;
        esac
    fi
}

# Create log directory if it doesn't exist
mkdir -p "${LOG_DIR}"

# Check if tinyproxy is installed
check_tinyproxy() {
    if ! command -v tinyproxy &> /dev/null; then
        exit_with_error "tinyproxy is not installed. Install it with: sudo apt-get install tinyproxy"
    fi
}

# Resolve the current user's primary group
resolve_group() {
    id -gn 2>/dev/null || exit_with_error "Failed to resolve primary group for user '${USER}'"
}

# Generate runtime config from template
generate_config() {
    if [[ ! -f "${TEMPLATE_FILE}" ]]; then
        exit_with_error "Template file not found: ${TEMPLATE_FILE}"
    fi

    local group
    group="$(resolve_group)"

    sed \
        -e "s|__USER__|${USER}|g" \
        -e "s|__GROUP__|${group}|g" \
        -e "s|__LOG_DIR__|${LOG_DIR}|g" \
        -e "s|__UPSTREAM_HOST__|${TINYPROXY_UPSTREAM_HOST}|g" \
        -e "s|__UPSTREAM_PORT__|${TINYPROXY_UPSTREAM_PORT}|g" \
        -e "s|__LISTEN_PORT__|${TINYPROXY_PORT}|g" \
        "${TEMPLATE_FILE}" > "${RUNTIME_CONFIG}"

    log_info "Generated runtime config: ${RUNTIME_CONFIG}"
}

# Get PID if running
get_pid() {
    if [[ -f "${PID_FILE}" ]]; then
        local pid
        pid=$(cat "${PID_FILE}")
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

# Check if a port is listening using ss (available by default on WSL/Ubuntu)
check_port_listening() {
    local port="$1"
    ss -tlnp 2>/dev/null | grep -q ":${port} " 2>/dev/null
}

# Wait for process to be ready (PID file exists and port is listening)
wait_for_ready() {
    local port="$1"
    local elapsed=0

    while [[ ${elapsed} -lt ${TINYPROXY_READINESS_TIMEOUT} ]]; do
        if get_pid > /dev/null 2>&1 && check_port_listening "${port}"; then
            return 0
        fi
        sleep 0.5
        elapsed=$((elapsed + 1))
    done
    return 1
}

# Wait for process to stop
wait_for_stop() {
    local pid="$1"
    local elapsed=0

    while ps -p "${pid}" > /dev/null 2>&1 && [[ ${elapsed} -lt ${TINYPROXY_STOP_TIMEOUT} ]]; do
        sleep 0.5
        elapsed=$((elapsed + 1))
    done

    # Return whether process is still running
    ps -p "${pid}" > /dev/null 2>&1
}

# Start tinyproxy
start_proxy() {
    warn_if_in_container
    log_info "Starting tinyproxy daemon..."

    check_tinyproxy
    validate_required_env

    # Check if already running
    if get_pid > /dev/null 2>&1; then
        local pid
        pid=$(get_pid)
        log_warn "tinyproxy is already running (PID: ${pid})"
        return 0
    fi

    # Generate runtime config from template
    generate_config

    log_info "Config file: ${RUNTIME_CONFIG}"
    log_info "Listening on: 0.0.0.0:${TINYPROXY_PORT}"
    log_info "Upstream proxy: ${TINYPROXY_UPSTREAM_HOST}:${TINYPROXY_UPSTREAM_PORT}"
    log_info "Log file: ${LOG_FILE}"

    # Start tinyproxy with generated runtime config
    tinyproxy -c "${RUNTIME_CONFIG}"

    # Wait for readiness
    if wait_for_ready "${TINYPROXY_PORT}"; then
        local pid
        pid=$(get_pid)
        log_success "tinyproxy started successfully (PID: ${pid})"
        log_success "Proxy is listening on port ${TINYPROXY_PORT}"

        echo ""
        log_info "To view logs in real-time:"
        log_info "  tail -f ${LOG_FILE}"
        echo ""
        log_info "To check status:"
        log_info "  ./tinyproxy-daemon.sh status"
    else
        exit_with_error "Failed to start tinyproxy within ${TINYPROXY_READINESS_TIMEOUT}s. Check logs: ${LOG_FILE}"
    fi
}

# Stop tinyproxy
stop_proxy() {
    log_info "Stopping tinyproxy daemon..."

    validate_required_env

    if ! get_pid > /dev/null 2>&1; then
        log_warn "tinyproxy is not running"
        return 0
    fi

    local pid
    pid=$(get_pid)
    log_info "Sending TERM signal to PID ${pid}..."

    kill "${pid}" 2>/dev/null || true

    # Wait for process to stop
    if wait_for_stop "${pid}"; then
        log_warn "Process didn't stop gracefully, sending KILL signal..."
        kill -9 "${pid}" 2>/dev/null || true

        # Poll until confirmed dead
        local elapsed=0
        while ps -p "${pid}" > /dev/null 2>&1 && [[ ${elapsed} -lt ${TINYPROXY_STOP_TIMEOUT} ]]; do
            sleep 0.5
            elapsed=$((elapsed + 1))
        done
    fi

    rm -f "${PID_FILE}"
    log_success "tinyproxy stopped"
}

# Restart tinyproxy
restart_proxy() {
    log_info "Restarting tinyproxy daemon..."
    stop_proxy
    start_proxy
}

# Show status
show_status() {
    log_info "Checking tinyproxy daemon status..."
    echo ""

    validate_required_env

    if get_pid > /dev/null 2>&1; then
        local pid
        pid=$(get_pid)
        log_success "tinyproxy is RUNNING (PID: ${pid})"

        # Check if port is listening
        if check_port_listening "${TINYPROXY_PORT}"; then
            log_success "Listening on port ${TINYPROXY_PORT}"
        else
            log_warn "Process running but not listening on port ${TINYPROXY_PORT}"
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
            tail -20 "${LOG_FILE}"
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
        echo "  status   Show daemon status and recent logs"
        echo ""
        echo "Required environment variables:"
        echo "  TINYPROXY_UPSTREAM_HOST       Upstream proxy hostname (e.g., edge.surepath.ai)"
        echo "  TINYPROXY_UPSTREAM_PORT       Upstream proxy port (e.g., 8080)"
        echo "  TINYPROXY_PORT                Listen port (e.g., 3128)"
        echo "  TINYPROXY_READINESS_TIMEOUT   Startup readiness timeout in seconds (e.g., 10)"
        echo "  TINYPROXY_STOP_TIMEOUT        Graceful stop timeout in seconds (e.g., 10)"
        exit 1
        ;;
esac
