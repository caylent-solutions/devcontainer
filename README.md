# Caylent Devcontainer Base

## 🚀 Overview

This repository provides the **base development container** configuration used across Caylent engineering projects. It is designed to be:

- ✅ **Cross-platform**: macOS and Windows (WSL2) compatible using VS Code  
- 🧱 **Reusable**: drop into any repo to enable consistent local dev experience  
- 🔐 **Secure and configurable**: injects secrets via environment, not committed  
- 🧩 **Smart defaults**: tools, AWS profiles, aliases, Python setup, Git config, and more  
- 🧪 **Consistent environments**: ensures identical local dev setups across teams using `asdf` to pin and manage exact binary versions  

📦 Repo URL: [`https://github.com/caylent-solutions/devcontainer`](https://github.com/caylent-solutions/devcontainer)

---

## 🧰 What’s Included

- `devcontainer.json` — VS Code container definition
- `.devcontainer.postcreate.sh` — container setup script
- `generate-shell-exports.sh` / `generate-shell-exports.py` — transforms env JSON into shell exports
- `example-aws-profile-map.json` — declarative AWS SSO profile config template
- Git, AWS CLI, Docker, Python, `asdf`, aliases, shell profile injection
- Extension support for Amazon Q and GitHub Copilot

---

## 💡 Built-In Tooling

The devcontainer installs:

- ✅ Amazon Q VS Code extension
- ✅ GitHub Copilot + Copilot Chat
- ✅ GitLens, YAML, Python, Docker, Makefile Tools
- ✅ Jinja, spell checking

These extensions are auto-installed on container start.

---

## 🖥 Prerequisites

### For macOS
- [VS Code](https://code.visualstudio.com/Download)
- [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop)
- [Homebrew](https://brew.sh/) — optional
- Python 3.12.9 - [Installation Guide](PYTHON_INSTALL.md#for-macos-using-asdf)

### For Windows
- [WSL2](https://learn.microsoft.com/en-us/windows/wsl/install)
- [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)
- [VS Code](https://code.visualstudio.com/Download)
- Python 3.12.9 - [Installation Guide](PYTHON_INSTALL.md#for-windows-using-windows-store-or-official-installer)

---

## 🪄 Quick Start

### 1. Copy Devcontainer Into Your Project
```bash
git clone https://github.com/caylent-solutions/devcontainer.git
cd devcontainer
cp -r .devcontainer ../your-project-dir/
cd ../your-project-dir
```

---

### 2a. Customize Your Developer Environment

```bash
cp .devcontainer/example-container-env-values.json devcontainer-environment-variables.json
```

Update `devcontainer-environment-variables.json` with your values:
- `AWS_CONFIG_ENABLED` (default: `true`) - Set to `false` to disable AWS configuration
- `DEFAULT_GIT_BRANCH` (e.g. `main`)
- `DEFAULT_PYTHON_VERSION` (e.g. `3.12.9`)
- Git credentials: `GIT_USER`, `GIT_USER_EMAIL`, `GIT_TOKEN`
- AWS SSO and account information (required if `AWS_CONFIG_ENABLED=true`)
- Extra packages: `EXTRA_APT_PACKAGES`

---

### 2b. Configure AWS Profile Map (Optional)

By default, AWS configuration is enabled. If you don't need AWS access, you can disable it by setting `AWS_CONFIG_ENABLED=false` in your `devcontainer-environment-variables.json`.

If AWS configuration is enabled, copy the example:
```bash
cp .devcontainer/example-aws-profile-map.json .devcontainer/aws-profile-map.json
```

Edit `.devcontainer/aws-profile-map.json` to define your AWS SSO accounts:

```json
{
  "default": {
    "region": "us-east-2",
    "sso_start_url": "https://your-org.awsapps.com/start",
    "sso_region": "us-east-1",
    "account_name": "your-default-account",
    "account_id": "123456789012",
    "role_name": "AdministratorAccess"
  },
  ...
}
```

> ⚠️ This file is required only when AWS configuration is enabled (`AWS_CONFIG_ENABLED=true`).

---

### 3. Generate `shell.env`

```bash
.devcontainer/generate-shell-exports.py export devcontainer-environment-variables.json --output shell.env
source shell.env
```

To persist:
```bash
echo "source $(pwd)/shell.env" >> ~/.zshrc
```

---

### 4. Launch in VS Code

```bash
code .
```

Accept the prompt to reopen in container.

---

## 🧩 Post-Launch Setup

### 🧠 GitHub Copilot

- Auto-installed
- Login prompt appears if not authenticated
- To verify: open any `.py` file and type a comment — suggestions will appear

### 🤖 Amazon Q

- Open the Amazon Q sidebar (left bar in VS Code)
- Click **Sign in** and follow the browser flow using your **AWS Builder ID** or **IAM Identity Center**
- You must have authenticated to the CLI via `aws sso login` first

---

### 🔐 Connect to AWS via SSO

From the container:
```bash
aws sso login --profile your-profile-name
```

- Omitting `--profile` uses the `"default"` profile from your `~/.aws/config`.

---

### ✅ Confirm Git Auth

```bash
git config --get user.email
git config --get user.name
git ls-remote https://github.com/your-org/your-repo.git
```

Or open the Source Control tab in VS Code to confirm the repo is accessible.

---

## 🐍 Python Install Logic

- `.tool-versions` present? → installs pinned Python version
- Not present? → installs version from:
```json
"DEFAULT_PYTHON_VERSION": "3.12.9"
```

> ✅ Best practice: commit `.tool-versions` to your repo:
```bash
echo "python 3.12.9" > .tool-versions
git add .tool-versions
git commit -m "Add Python version pin for devcontainer"
```

Then rebuild the container.

---

## 🐳 Docker-in-Docker Support

The devcontainer supports **nested Docker** with `docker-in-docker`.

To enable Docker Swarm inside the container:
```bash
docker swarm init
```

> You can now run full containerized workflows inside the devcontainer itself.

---

## 📡 Debug Ports

| Port      | Purpose                  |
|-----------|--------------------------|
| 5678      | Python debug (debugpy)   |
| 9229      | Node.js inspector        |
| 5005      | Java debug (JDWP)        |
| 4020      | Custom web app / tools   |
| 4711      | Internal dev tools       |
| 8080      | Web servers (HTTP)       |
| 5050      | WebSocket / APIs         |

---

## 🧩 JetBrains Compatibility

JetBrains IDEs (like PyCharm) support Devcontainers via [JetBrains Gateway](https://www.jetbrains.com/remote-development/gateway/), but:

- Post-create hooks, VS Code extensions, and shell customization are **not** guaranteed
- VS Code is **strongly recommended** for full compatibility

---

## 📁 File Reference

| File | Purpose |
|------|---------|
| `.devcontainer/devcontainer.json` | VS Code container setup |
| `.devcontainer/.devcontainer.postcreate.sh` | Container provisioning logic |
| `.devcontainer/example-aws-profile-map.json` | AWS profile template |
| `.devcontainer/aws-profile-map.json` | Your active AWS profiles |
| `.devcontainer/example-container-env-values.json` | Developer config example |
| `.devcontainer/generate-shell-exports.sh|.py` | Converts JSON to shell env exports |

---

## 🧪 Validate Your Config

```bash
.devcontainer/generate-shell-exports.sh devcontainer-environment-variables.json
```

Or using Python:
```bash
python .devcontainer/generate-shell-exports.py export devcontainer-environment-variables.json
```

---

## 🧼 Git Hygiene

- ❌ Never commit `shell.env` or `devcontainer-environment-variables.json`
- ✅ Use `.tool-versions` to ensure reproducibility
- ✅ Use `aws-profile-map.json` to declare AWS SSO profiles
- `.gitignore` excludes common temp files, IDE config, and secrets

---

## 🤝 Contributing

### If Public (Open Source)

1. Fork the repo on GitHub
2. Create a feature branch: `git checkout -b feat/my-change`
3. Push and open a Pull Request

### If Caylent Internal

1. Pull `main`: `git checkout main && git pull`
2. Create a new branch: `git checkout -b feat/thing`
3. Commit and push: `git add . && git commit -m "feat: update thing" && git push`
4. Open a PR to `main` and request review

> All PRs must pass CI and be reviewed before merge.