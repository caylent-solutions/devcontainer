# tinyproxy Daemon for macOS

This directory contains scripts for managing tinyproxy as a background daemon on your Mac host, required for devcontainer proxy support with SurePath AI.

## Overview

The devcontainer needs to access external resources through the SurePath AI proxy. Since SurePath uses IP-based authentication, the proxy must run on your Mac (with the authenticated IP) and the devcontainer connects to it via `host.docker.internal:3128`.

## Prerequisites

**Install tinyproxy** on your Mac:

```bash
brew install tinyproxy
```

Verify installation:
```bash
tinyproxy -h
```

## Quick Start

### Make the script executable (first time only)
```bash
chmod +x .devcontainer/macOS/tinyproxy-daemon.sh
```

### Start the proxy
```bash
./.devcontainer/macOS/tinyproxy-daemon.sh start
```

### Check status
```bash
./.devcontainer/macOS/tinyproxy-daemon.sh status
```

### Stop the proxy
```bash
./.devcontainer/macOS/tinyproxy-daemon.sh stop
```

### Restart the proxy
```bash
./.devcontainer/macOS/tinyproxy-daemon.sh restart
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

### Examples

**Start the proxy:**
```bash
./tinyproxy-daemon.sh start
```

**Check status:**
```bash
./tinyproxy-daemon.sh status
```

**Restart the proxy:**
```bash
./tinyproxy-daemon.sh restart
```

## Log Files

All logs are stored in `~/.devcontainer-proxy/`:

| File | Purpose | Location |
|------|---------|----------|
| **Output Log** | Standard tinyproxy output | `~/.devcontainer-proxy/tinyproxy.log` |
| **PID File** | Process ID of running daemon | `~/.devcontainer-proxy/tinyproxy.pid` |

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

The proxy is configured with:

| Setting | Value | Description |
|---------|-------|-------------|
| **Upstream Proxy** | `edge.surepath.ai:8080` | SurePath AI proxy server |
| **Listen Address** | `0.0.0.0` | Binds to all interfaces (accessible from Docker) |
| **Port** | `3128` | Standard proxy port |
| **Container Access** | `host.docker.internal:3128` | How devcontainer reaches the proxy |

## Troubleshooting

### Proxy won't start

**Check if tinyproxy is installed:**
```bash
which tinyproxy
tinyproxy -h
```

If not installed, see [Prerequisites](#prerequisites).

**Check if another process is using port 3128:**
```bash
lsof -i :3128
```

If port is in use, stop the other process or change the port in the script.

**Check error logs:**
```bash
cat ~/.devcontainer-proxy/tinyproxy.log
```

### Proxy starts but devcontainer can't connect

**Verify proxy is listening on all interfaces:**
```bash
./tinyproxy-daemon.sh status
```

Look for: `Listening on port 3128`

**Test from host:**
```bash
curl -x http://localhost:3128 -I https://claude.ai/install.sh
```

Should return HTTP 302 (redirect to installer).

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

### devcontainer build fails with "Cannot reach Mac host proxy"

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
        <string>/full/path/to/your/project/.devcontainer/macOS/tinyproxy-daemon.sh</string>
        <string>start</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/YOUR_USERNAME/.devcontainer-proxy/launchd-stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/YOUR_USERNAME/.devcontainer-proxy/launchd-stderr.log</string>
</dict>
</plist>
```

**Important:** Replace `/full/path/to/your/project` and `YOUR_USERNAME` with your actual paths.

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
- ✅ **No silent failures** - all errors are reported
- ✅ **Non-zero exit codes** - proper exit codes on failure
- ✅ **No fallbacks** - fails fast if requirements aren't met
- ✅ **Detailed error messages** - explains what went wrong
- ✅ **Log file references** - directs you to logs for debugging

### Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | General error (missing command, invalid arguments, operation failed) |

## Support

### Get Help

```bash
# Show usage
./tinyproxy-daemon.sh

# Check status and logs
./tinyproxy-daemon.sh status
```

### Common Issues

1. **"tinyproxy is not installed"**
   - Install tinyproxy: `brew install tinyproxy`

2. **"tinyproxy is already running"**
   - Stop first: `./tinyproxy-daemon.sh stop`
   - Or restart: `./tinyproxy-daemon.sh restart`

3. **"Failed to start proxy"**
   - Check logs: `cat ~/.devcontainer-proxy/tinyproxy.log`
   - Verify upstream proxy is accessible: `curl -I http://edge.surepath.ai:8080`

4. **"Port 3128 is NOT LISTENING"**
   - Check logs for port conflicts
   - Verify no firewall is blocking the port
   - Ensure no other process is using port 3128

## Security Notes

- The proxy binds to `0.0.0.0` (all interfaces) to be accessible from Docker containers
- Only accessible from your local machine and Docker containers
- Upstream proxy uses SurePath AI authentication - traffic is monitored
- Logs may contain proxy traffic - protect log directory

## Developer Notes

### Script Architecture
- Written in Bash with `set -euo pipefail` for strict error handling
- Uses PID file for process management
- Validates proxy accessibility after start
- Color-coded output for better visibility
- Comprehensive status reporting

### Customization
Edit `tinyproxy.conf` to customize:
- `Port` - Change proxy port (default: 3128)
- `Bind` - Change bind address (default: 0.0.0.0)
- `Upstream` - Change upstream proxy server
- `LogFile` - Change log location
- `LogLevel` - Change verbosity (Info, Connect, Notice, Warning, Error, Critical)
