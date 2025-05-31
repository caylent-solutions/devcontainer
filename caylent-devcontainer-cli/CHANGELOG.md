# CHANGELOG

## 1.0.0 (2025-05-31)

The `1.0.0` release of the **Caylent Devcontainer** introduces a robust foundation for managing local development environments at scale. This version includes a powerful CLI, environment templating, AWS integration, and a full CI/CD pipeline built on GitHub Actions.

---

### 🚀 Highlights

- **One-line environment setup** via `cdevcontainer setup-devcontainer`
- **Interactive template management** with save, load, and upgrade capabilities
- **Declarative AWS SSO support** with `aws-profile-map.json`
- **Cross-platform compatibility** (macOS, WSL2) using VS Code
- **CI/CD automation** with semantic versioning, Slack notifications, and QA workflows

---

### ✨ Features

- CLI command: `setup-devcontainer` for guided interactive setup
- Reusable template system: `save`, `load`, `upgrade`, `delete`
- JSON-driven configuration with `devcontainer-environment-variables.json`
- Optional AWS SSO injection using `example-aws-profile-map.json`
- Docker-in-Docker + Docker Swarm support
- Pre-installed extensions: GitHub Copilot, Amazon Q, GitLens, Python, YAML, Docker
- JetBrains Gateway support (beta)

---

### 🛠 CLI Improvements

- Installable via pip:
  ```bash
  pip install caylent-devcontainer-cli==1.0.0
