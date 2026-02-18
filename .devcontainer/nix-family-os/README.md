# tinyproxy Daemon for macOS / Linux Host

> **Important:** This script runs on your **host operating system** (macOS or Linux), **not** inside the devcontainer. The devcontainer connects to this proxy via `host.docker.internal`.
>
> For Windows/WSL hosts, see the [wsl-family-os](../wsl-family-os/README.md) directory instead.

This directory is a **common catalog asset** — it is automatically copied into every project's `.devcontainer/nix-family-os/` when a devcontainer is set up via `cdevcontainer setup-devcontainer`. It contains scripts for managing tinyproxy as a background daemon on your macOS or Linux host, required for devcontainer proxy support with an upstream corporate proxy.

## Overview

The devcontainer needs to access external resources through an upstream proxy. Since the upstream proxy uses IP-based authentication, the proxy must run on your **host machine** (with the authenticated IP) and the devcontainer connects to it via `host.docker.internal`.

## Prerequisites

**Install tinyproxy** on your host machine:

```bash
# macOS
brew install tinyproxy

# Linux (Debian/Ubuntu)
sudo apt-get install tinyproxy
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

Set these in your shell profile (`~/.zshrc`, `~/.bashrc`) or export them before running the script:

```bash
export TINYPROXY_UPSTREAM_HOST=edge.surepath.ai
export TINYPROXY_UPSTREAM_PORT=8080
export TINYPROXY_PORT=3128
export TINYPROXY_READINESS_TIMEOUT=10
export TINYPROXY_STOP_TIMEOUT=10
```

## Quick Start

### Make the script executable (first time only)
```bash
chmod +x .devcontainer/nix-family-os/tinyproxy-daemon.sh
```

### Start the proxy
```bash
./.devcontainer/nix-family-os/tinyproxy-daemon.sh start
```

### Check status
```bash
./.devcontainer/nix-family-os/tinyproxy-daemon.sh status
```

### Stop the proxy
```bash
./.devcontainer/nix-family-os/tinyproxy-daemon.sh stop
```

### Restart the proxy
```bash
./.devcontainer/nix-family-os/tinyproxy-daemon.sh restart
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

If not installed, see [Prerequisites](#prerequisites).

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
lsof -i :3128
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

**Test from host:**
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

**Ensure proxy is running:**
```bash
./tinyproxy-daemon.sh status
```

**Restart the proxy:**
```bash
./tinyproxy-daemon.sh restart
```

**Rebuild devcontainer:**
In VS Code: `Cmd+Shift+P` → "Dev Containers: Rebuild Container"

## Auto-Start on Mac Boot (Optional)

To automatically start tinyproxy when your Mac boots, create a LaunchAgent.

### Create LaunchAgent plist

Create file: `~/Library/LaunchAgents/com.devcontainer.tinyproxy.plist`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.devcontainer.tinyproxy</string>
    <key>ProgramArguments</key>
    <array>
        <string>/full/path/to/your/project/.devcontainer/nix-family-os/tinyproxy-daemon.sh</string>
        <string>start</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>EnvironmentVariables</key>
    <dict>
        <key>TINYPROXY_UPSTREAM_HOST</key>
        <string>edge.surepath.ai</string>
        <key>TINYPROXY_UPSTREAM_PORT</key>
        <string>8080</string>
        <key>TINYPROXY_PORT</key>
        <string>3128</string>
        <key>TINYPROXY_READINESS_TIMEOUT</key>
        <string>10</string>
        <key>TINYPROXY_STOP_TIMEOUT</key>
        <string>10</string>
    </dict>
    <key>StandardOutPath</key>
    <string>/Users/YOUR_USERNAME/.devcontainer-proxy/launchd-stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/YOUR_USERNAME/.devcontainer-proxy/launchd-stderr.log</string>
</dict>
</plist>
```

**Important:** Replace `/full/path/to/your/project`, `YOUR_USERNAME`, and the environment variable values with your actual values.

### Load the LaunchAgent

```bash
# Load and start immediately
launchctl load ~/Library/LaunchAgents/com.devcontainer.tinyproxy.plist

# Check if loaded
launchctl list | grep tinyproxy
```

### Manage LaunchAgent

```bash
# Unload (stop auto-start)
launchctl unload ~/Library/LaunchAgents/com.devcontainer.tinyproxy.plist

# Start manually
launchctl start com.devcontainer.tinyproxy

# Stop manually
launchctl stop com.devcontainer.tinyproxy
```

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
   - Add to `~/.zshrc` or `~/.bashrc` for persistence

2. **"tinyproxy is not installed"**
   - Install tinyproxy: `brew install tinyproxy`

3. **"tinyproxy is already running"**
   - Stop first: `./tinyproxy-daemon.sh stop`
   - Or restart: `./tinyproxy-daemon.sh restart`

4. **"Failed to start proxy"**
   - Check logs: `cat ~/.devcontainer-proxy/tinyproxy.log`
   - Verify upstream proxy is accessible: `nc -zv $TINYPROXY_UPSTREAM_HOST $TINYPROXY_UPSTREAM_PORT`

5. **"Port is NOT LISTENING"**
   - Check logs for port conflicts
   - Verify no firewall is blocking the port
   - Ensure no other process is using the port: `lsof -i :3128`

## Security Notes

- The proxy binds to `0.0.0.0` (all interfaces) to be accessible from Docker containers
- Only accessible from your local machine and Docker containers
- Upstream proxy traffic may be monitored by the upstream provider
- Logs may contain proxy traffic — protect log directory
- The generated runtime config is stored in `~/.devcontainer-proxy/` (not in the repo)
