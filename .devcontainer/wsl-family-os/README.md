# tinyproxy Daemon for Windows / WSL Host

> **Important:** This script runs on your **Windows host via WSL** (Windows Subsystem for Linux), **not** inside the devcontainer. The devcontainer connects to this proxy via `host.docker.internal`.
>
> For macOS or native Linux hosts, see the [nix-family-os](../nix-family-os/README.md) directory instead.

This directory contains scripts for managing tinyproxy as a background daemon on your Windows/WSL host, required for devcontainer proxy support with an upstream corporate proxy.

## Overview

The devcontainer needs to access external resources through an upstream proxy. Since the upstream proxy uses IP-based authentication, the proxy must run on your **host machine** (with the authenticated IP) and the devcontainer connects to it via `host.docker.internal`.

On Windows, you run tinyproxy inside a WSL distribution (e.g., Ubuntu). Docker Desktop for Windows with the WSL 2 backend makes the WSL network accessible to containers via `host.docker.internal`.

## Prerequisites

1. **Windows with WSL 2** installed and configured
2. **Docker Desktop for Windows** with WSL 2 backend enabled
3. **tinyproxy** installed inside your WSL distribution

**Install tinyproxy** inside your WSL terminal:

```bash
sudo apt-get update && sudo apt-get install -y tinyproxy
```

Verify installation:
```bash
tinyproxy -h
```

## Environment Variables

All environment variables are **required**. The script will exit with an error if any are missing, and will recommend adding them to your shell rc file.

| Variable | Description | Example |
|----------|-------------|---------|
| `TINYPROXY_UPSTREAM_HOST` | Upstream proxy hostname | `edge.surepath.ai` |
| `TINYPROXY_UPSTREAM_PORT` | Upstream proxy port | `8080` |
| `TINYPROXY_PORT` | Listen port | `3128` |
| `TINYPROXY_READINESS_TIMEOUT` | Startup readiness timeout (seconds) | `10` |
| `TINYPROXY_STOP_TIMEOUT` | Graceful stop timeout (seconds) | `10` |

Set these in your WSL shell profile (`~/.bashrc` or `~/.zshrc`) or export them before running the script:

```bash
export TINYPROXY_UPSTREAM_HOST=edge.surepath.ai
export TINYPROXY_UPSTREAM_PORT=8080
export TINYPROXY_PORT=3128
export TINYPROXY_READINESS_TIMEOUT=10
export TINYPROXY_STOP_TIMEOUT=10
```

## Quick Start

All commands below are run **inside your WSL terminal**, not in PowerShell or the devcontainer.

### Make the script executable (first time only)
```bash
chmod +x .devcontainer/wsl-family-os/tinyproxy-daemon.sh
```

### Start the proxy
```bash
./.devcontainer/wsl-family-os/tinyproxy-daemon.sh start
```

### Check status
```bash
./.devcontainer/wsl-family-os/tinyproxy-daemon.sh status
```

### Stop the proxy
```bash
./.devcontainer/wsl-family-os/tinyproxy-daemon.sh stop
```

### Restart the proxy
```bash
./.devcontainer/wsl-family-os/tinyproxy-daemon.sh restart
```

## Usage

### Command Syntax
```bash
./tinyproxy-daemon.sh {start|stop|restart|status}
```

### Commands

| Command | Description |
|---------|-------------|
| `start` | Start tinyproxy daemon |
| `stop` | Stop tinyproxy daemon |
| `restart` | Restart tinyproxy daemon |
| `status` | Show daemon status and recent logs |

## How It Works

The daemon script uses a **template-based config generation** approach:

1. `tinyproxy.conf.template` — checked into the repo with placeholders (`__USER__`, `__UPSTREAM_HOST__`, etc.)
2. On `start`, the script resolves all placeholders using environment variables and OS-detected values (user, group)
3. A runtime config is written to `~/.devcontainer-proxy/tinyproxy.conf`
4. tinyproxy runs against the generated runtime config

This ensures no hardcoded values in the repo and the config works for any user or upstream proxy.

## Log Files

All logs are stored in `~/.devcontainer-proxy/`:

| File | Purpose | Location |
|------|---------|----------|
| **Output Log** | Standard tinyproxy output | `~/.devcontainer-proxy/tinyproxy.log` |
| **PID File** | Process ID of running daemon | `~/.devcontainer-proxy/tinyproxy.pid` |
| **Runtime Config** | Generated config from template | `~/.devcontainer-proxy/tinyproxy.conf` |

### View logs in real-time

**Watch output log:**
```bash
tail -f ~/.devcontainer-proxy/tinyproxy.log
```

**View last 50 lines:**
```bash
tail -50 ~/.devcontainer-proxy/tinyproxy.log
```

### Clear logs

```bash
# Clear all logs
rm ~/.devcontainer-proxy/*.log

# Clear just output log
rm ~/.devcontainer-proxy/tinyproxy.log
```

## Configuration

The proxy is configured via environment variables:

| Setting | Source | Description |
|---------|--------|-------------|
| **Upstream Proxy** | `TINYPROXY_UPSTREAM_HOST:TINYPROXY_UPSTREAM_PORT` | Upstream proxy server |
| **Listen Address** | `0.0.0.0` (template) | Binds to all interfaces (accessible from Docker) |
| **Port** | `TINYPROXY_PORT` | Listen port |
| **Container Access** | `host.docker.internal:<TINYPROXY_PORT>` | How devcontainer reaches the proxy |

## Troubleshooting

### Proxy won't start

**Check if tinyproxy is installed:**
```bash
which tinyproxy
tinyproxy -h
```

If not installed:
```bash
sudo apt-get update && sudo apt-get install -y tinyproxy
```

**Check environment variables are set:**
```bash
echo $TINYPROXY_UPSTREAM_HOST
echo $TINYPROXY_UPSTREAM_PORT
echo $TINYPROXY_PORT
echo $TINYPROXY_READINESS_TIMEOUT
echo $TINYPROXY_STOP_TIMEOUT
```

If any are not set, export them (see [Environment Variables](#environment-variables)).

**Check if another process is using the listen port:**
```bash
ss -tlnp | grep :3128
```

If port is in use, stop the other process or set `TINYPROXY_PORT` to a different value.

**Check error logs:**
```bash
cat ~/.devcontainer-proxy/tinyproxy.log
```

### Proxy starts but devcontainer can't connect

**Verify proxy is listening on all interfaces:**
```bash
./tinyproxy-daemon.sh status
```

Look for: `Listening on port <port>`

**Test from WSL:**
```bash
curl -x http://localhost:3128 -I https://example.com
```

**From devcontainer, test host connectivity:**
```bash
nc -zv host.docker.internal 3128
```

Should show: `Connection to host.docker.internal port 3128 [tcp/*] succeeded!`

### Proxy stops unexpectedly

**Check system logs:**
```bash
tail -100 ~/.devcontainer-proxy/tinyproxy.log
```

**Check if process was killed:**
```bash
./tinyproxy-daemon.sh status
```

**Restart the proxy:**
```bash
./tinyproxy-daemon.sh restart
```

### devcontainer build fails with "Cannot reach host proxy"

**Ensure proxy is running (in WSL terminal):**
```bash
./tinyproxy-daemon.sh status
```

**Restart the proxy:**
```bash
./tinyproxy-daemon.sh restart
```

**Rebuild devcontainer:**
In VS Code: `Ctrl+Shift+P` → "Dev Containers: Rebuild Container"

### WSL-specific issues

**WSL networking not bridged properly:**
```bash
# Verify host.docker.internal resolves from WSL
ping -c 1 host.docker.internal
```

**Windows firewall blocking connections:**
Ensure Windows Firewall allows inbound connections on the tinyproxy listen port from the WSL and Docker networks.

**Line ending issues:**
WSL may introduce Windows-style line endings (CRLF). If scripts fail with `\r` errors:
```bash
sed -i 's/\r$//' .devcontainer/wsl-family-os/tinyproxy-daemon.sh
```

## Auto-Start on WSL Login (Optional)

To automatically start tinyproxy when your WSL session starts, add the following to your `~/.bashrc` or `~/.profile`:

```bash
# Auto-start tinyproxy daemon if not already running
if ! pgrep -x tinyproxy > /dev/null 2>&1; then
    /full/path/to/your/project/.devcontainer/wsl-family-os/tinyproxy-daemon.sh start
fi
```

**Important:** Replace `/full/path/to/your/project` with your actual project path, and ensure all required environment variables are exported above this line in your rc file.

## Error Handling

The script follows strict error handling:
- **No silent failures** — all errors are reported
- **Non-zero exit codes** — proper exit codes on failure
- **No fallbacks** — fails fast if requirements aren't met (missing env vars, missing tinyproxy)
- **Readiness polling** — verifies port is listening after start instead of blind delays
- **Detailed error messages** — explains what went wrong
- **Log file references** — directs you to logs for debugging

### Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | General error (missing env var, missing command, invalid arguments, operation failed) |

## Support

### Get Help

```bash
# Show usage and environment variable documentation
./tinyproxy-daemon.sh

# Check status and logs
./tinyproxy-daemon.sh status
```

### Common Issues

1. **"TINYPROXY_UPSTREAM_HOST is not set"**
   - Export the variable: `export TINYPROXY_UPSTREAM_HOST=edge.surepath.ai`
   - Add to `~/.bashrc` for persistence

2. **"tinyproxy is not installed"**
   - Install tinyproxy: `sudo apt-get install tinyproxy`

3. **"tinyproxy is already running"**
   - Stop first: `./tinyproxy-daemon.sh stop`
   - Or restart: `./tinyproxy-daemon.sh restart`

4. **"Failed to start proxy"**
   - Check logs: `cat ~/.devcontainer-proxy/tinyproxy.log`
   - Verify upstream proxy is accessible: `nc -zv $TINYPROXY_UPSTREAM_HOST $TINYPROXY_UPSTREAM_PORT`

5. **"Port is NOT LISTENING"**
   - Check logs for port conflicts
   - Verify no firewall is blocking the port
   - Ensure no other process is using the port: `ss -tlnp | grep :3128`

## Security Notes

- The proxy binds to `0.0.0.0` (all interfaces) to be accessible from Docker containers
- Only accessible from your local machine and Docker containers
- Upstream proxy traffic may be monitored by the upstream provider
- Logs may contain proxy traffic — protect log directory
- The generated runtime config is stored in `~/.devcontainer-proxy/` (not in the repo)
