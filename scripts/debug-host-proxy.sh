#!/usr/bin/env bash
set -uo pipefail

# Host-side proxy and network diagnostic script
# Run on macOS host: bash scripts/debug-host-proxy.sh

PROXY_DIR="$HOME/.devcontainer-proxy"
PROXY_PORT="${PROXY_PORT:-3128}"
UPSTREAM_HOST="${UPSTREAM_HOST:-edge.surepath.ai}"
UPSTREAM_PORT="${UPSTREAM_PORT:-8080}"

divider() { echo; echo "======== $1 ========"; }
info()    { echo "  $1"; }
check()   { echo "  [CHECK] $1"; }
warn()    { echo "  [WARN] $1"; }

# macOS doesn't have timeout; use perl fallback
_timeout() {
    local secs="$1"; shift
    perl -e "alarm $secs; exec @ARGV" -- "$@" 2>/dev/null
}

echo "====================================================="
echo "  HOST PROXY & NETWORK DIAGNOSTICS"
echo "  $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo "  Host: $(hostname)"
echo "  macOS: $(sw_vers -productVersion 2>/dev/null || echo 'unknown')"
echo "  Arch: $(uname -m)"
echo "====================================================="

# ── 1. TINYPROXY PROCESS ──
divider "TINYPROXY PROCESS"

if pgrep -x tinyproxy > /dev/null 2>&1; then
    check "tinyproxy is RUNNING"
    ps aux | grep '[t]inyproxy' | while read -r line; do info "$line"; done
    TPROXY_PID=$(pgrep -x tinyproxy | head -1)
    info "PID: $TPROXY_PID"
    if [ -n "$TPROXY_PID" ]; then
        info "Open files (lsof):"
        lsof -p "$TPROXY_PID" 2>/dev/null | head -30 | while read -r line; do info "  $line"; done
    fi
else
    check "tinyproxy is NOT RUNNING"
    info "Check if it was recently killed:"
    ls -la "$PROXY_DIR"/tinyproxy.pid 2>/dev/null || info "  No PID file found at $PROXY_DIR/tinyproxy.pid"
fi

# ── 2. TINYPROXY CONFIG ──
divider "TINYPROXY CONFIG"

CONF_FILE="$PROXY_DIR/tinyproxy.conf"
if [ -f "$CONF_FILE" ]; then
    check "Config file exists: $CONF_FILE"
    info "Contents:"
    cat "$CONF_FILE" | while read -r line; do info "  $line"; done
else
    check "Config file NOT FOUND at $CONF_FILE"
    info "Searching for tinyproxy.conf elsewhere:"
    find /usr/local/etc /opt/homebrew/etc "$HOME" -name "tinyproxy.conf" 2>/dev/null | while read -r f; do info "  Found: $f"; done
fi

# ── 3. TINYPROXY LOG ──
divider "TINYPROXY LOG (last 50 lines)"

LOG_FILE="$PROXY_DIR/tinyproxy.log"
if [ -f "$LOG_FILE" ]; then
    LOG_SIZE=$(wc -c < "$LOG_FILE" | tr -d ' ')
    check "Log file exists: $LOG_FILE ($LOG_SIZE bytes)"
    if [ "$LOG_SIZE" -eq 0 ]; then
        warn "LOG IS EMPTY - tinyproxy has processed ZERO requests"
        warn "This suggests traffic is NOT reaching tinyproxy"
    fi
    info "Last 50 lines:"
    tail -50 "$LOG_FILE" | while read -r line; do info "  $line"; done
else
    check "Log file NOT FOUND at $LOG_FILE"
fi

# ── 4. TINYPROXY BINARY ──
divider "TINYPROXY BINARY"

TPROXY_BIN=$(which tinyproxy 2>/dev/null)
if [ -n "$TPROXY_BIN" ]; then
    check "Binary: $TPROXY_BIN"
    info "Version: $(tinyproxy -v 2>&1 || echo 'unknown')"
    info "Installed via: $(brew list --formula 2>/dev/null | grep tinyproxy && echo 'homebrew' || echo 'unknown')"
else
    check "tinyproxy binary NOT FOUND in PATH"
fi

# ── 5. LOCAL PORT LISTENING - PORT CONFLICT DETECTION ──
divider "PORT $PROXY_PORT LISTENER (conflict detection)"

LISTENER=$(lsof -i ":$PROXY_PORT" -sTCP:LISTEN 2>/dev/null)
if [ -n "$LISTENER" ]; then
    check "Processes listening on port $PROXY_PORT:"
    echo "$LISTENER" | while read -r line; do info "  $line"; done

    # Count distinct PIDs (excluding header)
    LISTENER_PIDS=$(echo "$LISTENER" | tail -n +2 | awk '{print $2}' | sort -u)
    PID_COUNT=$(echo "$LISTENER_PIDS" | wc -l | tr -d ' ')
    if [ "$PID_COUNT" -gt 1 ]; then
        warn "PORT CONFLICT DETECTED: $PID_COUNT different processes on port $PROXY_PORT"
        echo "$LISTENER_PIDS" | while read -r pid; do
            PNAME=$(ps -p "$pid" -o comm= 2>/dev/null)
            PADDR=$(echo "$LISTENER" | grep "$pid" | awk '{print $9}' | head -1)
            warn "  PID $pid ($PNAME) bound to $PADDR"
        done
        warn "If VS Code is bound to 127.0.0.1:$PROXY_PORT, it may intercept"
        warn "container traffic routed via host.docker.internal (loopback)"
    fi
else
    check "NOTHING listening on port $PROXY_PORT"
fi

info "netstat check:"
netstat -an 2>/dev/null | grep "\.$PROXY_PORT " | grep -i listen | while read -r line; do info "  $line"; done

# ── 6. VS CODE PORT FORWARDING ──
divider "VS CODE PORT FORWARDING"

VSCODE_ON_PORT=$(lsof -i ":$PROXY_PORT" -sTCP:LISTEN 2>/dev/null | grep -i "code")
if [ -n "$VSCODE_ON_PORT" ]; then
    warn "VS Code is listening on port $PROXY_PORT:"
    echo "$VSCODE_ON_PORT" | while read -r line; do warn "  $line"; done
    warn "This is VS Code's automatic port forwarding."
    warn "Container traffic to host.docker.internal:$PROXY_PORT may be"
    warn "intercepted by VS Code instead of reaching tinyproxy."
    warn ""
    warn "FIX: Add to devcontainer.json:"
    warn '  "portsAttributes": { "3128": { "onAutoForward": "ignore" } }'
    warn "OR change tinyproxy to a different port."
else
    check "VS Code is NOT listening on port $PROXY_PORT (good)"
fi

# ── 7. LOCAL PROXY CONNECTIVITY ──
divider "LOCAL PROXY CONNECTIVITY (localhost:$PROXY_PORT)"

check "TCP connect to localhost:$PROXY_PORT:"
if nc -z -w5 localhost "$PROXY_PORT" 2>/dev/null; then
    info "  SUCCESS"
else
    info "  FAILED"
fi

check "TCP connect to 0.0.0.0:$PROXY_PORT:"
if nc -z -w5 0.0.0.0 "$PROXY_PORT" 2>/dev/null; then
    info "  SUCCESS"
else
    info "  FAILED"
fi

check "HTTP PROXY test via curl (localhost -> http://httpbin.org/ip):"
CURL_RESULT=$(_timeout 15 curl -s -o /dev/null -w "HTTP %{http_code} in %{time_total}s" \
    --proxy "http://localhost:$PROXY_PORT" "http://httpbin.org/ip" 2>&1) || CURL_RESULT="TIMEOUT or error"
info "  $CURL_RESULT"

check "HTTP PROXY test via curl (localhost -> http://ports.ubuntu.com/):"
CURL_RESULT2=$(_timeout 15 curl -s -o /dev/null -w "HTTP %{http_code} in %{time_total}s" \
    --proxy "http://localhost:$PROXY_PORT" "http://ports.ubuntu.com/ubuntu-ports/dists/noble/InRelease" 2>&1) || CURL_RESULT2="TIMEOUT or error"
info "  $CURL_RESULT2"

check "HTTPS CONNECT test via curl (localhost -> https://registry.npmjs.org/):"
CURL_RESULT3=$(_timeout 15 curl -s -o /dev/null -w "HTTP %{http_code} in %{time_total}s" \
    --proxy "http://localhost:$PROXY_PORT" "https://registry.npmjs.org/" 2>&1) || CURL_RESULT3="TIMEOUT or error"
info "  $CURL_RESULT3"

# ── 8. UPSTREAM PROXY (SUREPATH) ──
divider "UPSTREAM PROXY ($UPSTREAM_HOST:$UPSTREAM_PORT)"

check "DNS resolution of $UPSTREAM_HOST:"
DNS_RESULT=$(host "$UPSTREAM_HOST" 2>&1)
info "  $DNS_RESULT"

check "dig $UPSTREAM_HOST:"
DIG_RESULT=$(dig +short "$UPSTREAM_HOST" 2>&1)
info "  $DIG_RESULT"

check "TCP connect to $UPSTREAM_HOST:$UPSTREAM_PORT:"
if nc -z -w10 "$UPSTREAM_HOST" "$UPSTREAM_PORT" 2>/dev/null; then
    info "  SUCCESS"
else
    info "  FAILED (timeout or refused)"
fi

check "Direct curl to $UPSTREAM_HOST:$UPSTREAM_PORT (as HTTP proxy -> httpbin.org):"
UPSTREAM_CURL=$(_timeout 15 curl -s -o /dev/null -w "HTTP %{http_code} in %{time_total}s" \
    --proxy "http://$UPSTREAM_HOST:$UPSTREAM_PORT" "http://httpbin.org/ip" 2>&1) || UPSTREAM_CURL="TIMEOUT or error"
info "  $UPSTREAM_CURL"

check "Direct curl to $UPSTREAM_HOST:$UPSTREAM_PORT (as HTTP proxy -> ports.ubuntu.com):"
UPSTREAM_CURL2=$(_timeout 15 curl -s -o /dev/null -w "HTTP %{http_code} in %{time_total}s" \
    --proxy "http://$UPSTREAM_HOST:$UPSTREAM_PORT" "http://ports.ubuntu.com/ubuntu-ports/dists/noble/InRelease" 2>&1) || UPSTREAM_CURL2="TIMEOUT or error"
info "  $UPSTREAM_CURL2"

check "Direct HTTPS CONNECT via upstream ($UPSTREAM_HOST:$UPSTREAM_PORT -> https://httpbin.org):"
UPSTREAM_CURL3=$(_timeout 15 curl -s -o /dev/null -w "HTTP %{http_code} in %{time_total}s" \
    --proxy "http://$UPSTREAM_HOST:$UPSTREAM_PORT" "https://httpbin.org/ip" 2>&1) || UPSTREAM_CURL3="TIMEOUT or error"
info "  $UPSTREAM_CURL3"

# ── 9. DIRECT INTERNET CONNECTIVITY (no proxy) ──
divider "DIRECT INTERNET (bypassing all proxies)"

check "DNS resolution of ports.ubuntu.com:"
info "  $(host ports.ubuntu.com 2>&1 | head -3)"

check "Direct curl to https://httpbin.org/ip (no proxy):"
DIRECT=$(_timeout 10 curl -s --noproxy '*' "https://httpbin.org/ip" 2>&1) || DIRECT="TIMEOUT or error"
info "  $DIRECT"

check "Direct curl to http://ports.ubuntu.com/ (no proxy):"
DIRECT2=$(_timeout 10 curl -s -o /dev/null -w "HTTP %{http_code} in %{time_total}s" \
    --noproxy '*' "http://ports.ubuntu.com/ubuntu-ports/dists/noble/InRelease" 2>&1) || DIRECT2="TIMEOUT or error"
info "  $DIRECT2"

# ── 10. DOCKER DESKTOP ──
divider "DOCKER DESKTOP"

check "Docker version:"
info "  $(docker version --format '{{.Client.Version}}' 2>/dev/null || echo 'docker not found')"

check "Docker Desktop running:"
if pgrep -f "Docker Desktop" > /dev/null 2>&1; then
    info "  YES"
else
    info "  NOT DETECTED"
fi

check "Docker network inspect bridge:"
docker network inspect bridge 2>/dev/null | grep -E '"Subnet"|"Gateway"' | while read -r line; do info "  $line"; done

check "Docker proxy settings (from daemon config):"
DOCKER_DAEMON="$HOME/.docker/daemon.json"
if [ -f "$DOCKER_DAEMON" ]; then
    cat "$DOCKER_DAEMON" | while read -r line; do info "  $line"; done
else
    info "  No daemon.json found"
fi

check "Docker Desktop settings (proxy section):"
DOCKER_SETTINGS="$HOME/Library/Group Containers/group.com.docker/settings-store.json"
if [ -f "$DOCKER_SETTINGS" ]; then
    grep -iE 'proxy|forward' "$DOCKER_SETTINGS" 2>/dev/null | while read -r line; do info "  $line"; done
else
    DOCKER_SETTINGS2="$HOME/Library/Group Containers/group.com.docker/settings.json"
    if [ -f "$DOCKER_SETTINGS2" ]; then
        grep -iE 'proxy|forward' "$DOCKER_SETTINGS2" 2>/dev/null | while read -r line; do info "  $line"; done
    else
        info "  Docker Desktop settings file not found"
    fi
fi

# ── 11. NETWORK INTERFACES & ROUTING ──
divider "NETWORK INTERFACES & ROUTING"

check "Active interfaces with IPs:"
ifconfig | grep -E '^[a-z]|inet ' | grep -B1 'inet ' | while read -r line; do info "  $line"; done

check "Default route:"
info "  $(netstat -rn 2>/dev/null | grep '^default' | head -3)"

check "DNS servers:"
scutil --dns 2>/dev/null | grep 'nameserver' | sort -u | while read -r line; do info "  $line"; done

# ── 12. PROXY ENV VARS ON HOST ──
divider "HOST PROXY ENVIRONMENT VARIABLES"

for var in HTTP_PROXY HTTPS_PROXY http_proxy https_proxy NO_PROXY no_proxy ALL_PROXY all_proxy; do
    val="${!var:-}"
    if [ -n "$val" ]; then
        check "$var=$val"
    else
        check "$var=(unset)"
    fi
done

# ── 13. shell.env CONTENTS ──
divider "shell.env PROXY SETTINGS"

SHELL_ENV_CANDIDATES=(
    "$HOME/.devcontainer-proxy/shell.env"
    "$(pwd)/shell.env"
)
for f in "${SHELL_ENV_CANDIDATES[@]}"; do
    if [ -f "$f" ]; then
        check "Found: $f"
        grep -iE 'proxy|host_proxy' "$f" 2>/dev/null | while read -r line; do info "  $line"; done
    fi
done

# ── 14. NETWORK LATENCY & REACHABILITY ──
divider "NETWORK LATENCY"

check "Ping $UPSTREAM_HOST (3 packets):"
ping -c 3 -W 5 "$UPSTREAM_HOST" 2>&1 | tail -3 | while read -r line; do info "  $line"; done

check "Traceroute to $UPSTREAM_HOST (max 10 hops):"
traceroute -m 10 -w 3 "$UPSTREAM_HOST" 2>&1 | while read -r line; do info "  $line"; done

# ── 15. TINYPROXY END-TO-END CHAIN TEST ──
divider "END-TO-END CHAIN TEST (client -> tinyproxy -> upstream -> internet)"

check "Step 1: Client -> tinyproxy (localhost:$PROXY_PORT) TCP:"
if nc -z -w5 localhost "$PROXY_PORT" 2>/dev/null; then
    info "  OK"
else
    info "  FAILED - tinyproxy not reachable"
fi

check "Step 2: tinyproxy -> upstream ($UPSTREAM_HOST:$UPSTREAM_PORT) TCP:"
if nc -z -w10 "$UPSTREAM_HOST" "$UPSTREAM_PORT" 2>/dev/null; then
    info "  OK"
else
    info "  FAILED - upstream not reachable"
fi

check "Step 3: Full chain - curl via tinyproxy (HTTP):"
CHAIN_RESULT=$(_timeout 20 curl -v -s -w "\nHTTP %{http_code} total=%{time_total}s connect=%{time_connect}s starttransfer=%{time_starttransfer}s" \
    --proxy "http://localhost:$PROXY_PORT" "http://httpbin.org/ip" 2>&1) || CHAIN_RESULT="TIMEOUT - full chain failed"
echo "$CHAIN_RESULT" | while read -r line; do info "  $line"; done

check "Step 4: Full chain - curl via tinyproxy (HTTPS CONNECT):"
CHAIN_RESULT2=$(_timeout 20 curl -v -s -w "\nHTTP %{http_code} total=%{time_total}s connect=%{time_connect}s starttransfer=%{time_starttransfer}s" \
    --proxy "http://localhost:$PROXY_PORT" "https://httpbin.org/ip" 2>&1) || CHAIN_RESULT2="TIMEOUT - full chain HTTPS failed"
echo "$CHAIN_RESULT2" | while read -r line; do info "  $line"; done

# ── 16. TINYPROXY LOG AFTER TESTS ──
divider "TINYPROXY LOG AFTER TESTS"

if [ -f "$LOG_FILE" ]; then
    LOG_SIZE_AFTER=$(wc -c < "$LOG_FILE" | tr -d ' ')
    check "Log file size after tests: $LOG_SIZE_AFTER bytes"
    if [ "$LOG_SIZE_AFTER" -eq 0 ]; then
        warn "STILL EMPTY - tinyproxy never received any of our test requests"
        warn "Traffic is being intercepted before reaching tinyproxy"
    else
        info "Last 20 lines after tests:"
        tail -20 "$LOG_FILE" | while read -r line; do info "  $line"; done
    fi
fi

divider "DIAGNOSTICS COMPLETE"
echo
echo "Copy all output above and provide to your debugging session."
