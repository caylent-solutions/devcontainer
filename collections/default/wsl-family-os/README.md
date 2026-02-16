# Proxy Configuration for Windows/WSL

This directory contains documentation and utilities for configuring host proxy support when running devcontainers on Windows with WSL (Windows Subsystem for Linux).

## Overview

When using a corporate proxy (e.g., SurePath AI) on a Windows machine with WSL, the devcontainer needs to route traffic through the host's proxy. The proxy runs on the Windows host and the devcontainer connects to it via the WSL network interface.

## Prerequisites

1. **Windows with WSL 2** installed and configured
2. **A proxy server** running on the Windows host (e.g., tinyproxy, Squid, or corporate proxy)
3. **Docker Desktop for Windows** with WSL 2 backend enabled

## Configuration

### Environment Variables

Set the following in your `devcontainer-environment-variables.json`:

```json
{
  "containerEnv": {
    "HOST_PROXY": "true",
    "HOST_PROXY_URL": "http://host.docker.internal:3128"
  }
}
```

### How It Works

1. The `postCreateCommand` sources `shell.env` which contains proxy environment variables
2. The postcreate script detects WSL via `uname -r | grep -i microsoft`
3. When `HOST_PROXY=true`, the script validates that the proxy is reachable at the configured `HOST_PROXY_URL`
4. Proxy environment variables (`HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY`) are set in `shell.env`

### WSL Network Access

In WSL 2, the Windows host is accessible from within containers via `host.docker.internal`. This is the default hostname used to reach proxy services running on the Windows host.

## Troubleshooting

### Cannot reach host proxy

**Verify the proxy is running on the Windows host:**
```powershell
# PowerShell on Windows host
netstat -an | findstr :3128
```

**Test connectivity from inside the devcontainer:**
```bash
nc -zv host.docker.internal 3128
```

**Check WSL networking:**
```bash
# From WSL terminal
ping host.docker.internal
```

### Line ending issues

WSL may introduce Windows-style line endings (CRLF) into files. The devcontainer setup automatically handles this by:
1. Running `sed` to strip carriage returns from `.devcontainer/` files
2. Running `fix-line-endings.py` to convert all workspace files

### Proxy authentication failures

If your corporate proxy requires authentication:
1. Ensure credentials are configured in the proxy client on the Windows host
2. The devcontainer connects to the local proxy (no direct authentication needed)
3. The local proxy handles upstream authentication

## Support

If you encounter issues:
1. Check the devcontainer setup log: `cat /tmp/devcontainer-setup.log`
2. Verify proxy accessibility: `nc -zv host.docker.internal 3128`
3. Check environment variables: `env | grep -i proxy`
