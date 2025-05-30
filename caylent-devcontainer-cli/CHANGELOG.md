# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

_No unreleased changes yet._

## [1.0.0] - 2025-05-30

### Added
- Core CLI (`cdevcontainer`) with support for:
  - `setup-devcontainer` for interactive and manual configuration
  - `code` command to launch VS Code with loaded environment
  - `template` management (save, load, delete, upgrade)
  - `env export/load` for validating and exporting shell-compatible config
- Devcontainer bootstrap files:
  - `.devcontainer/devcontainer.json`
  - `.devcontainer.postcreate.sh`
  - `example-aws-profile-map.json`
  - `example-container-env-values.json`
- Support for automatic Python version management using `.tool-versions`
- JetBrains compatibility (partial), with Docker-in-Docker and debug port mappings
- GitHub Actions:
  - `pr-validation.yml` with lint/test/coverage and Slack notification
  - `publish.yml` with trusted publisher integration for PyPI
- Pre-commit and pre-push Git hooks via `make configure`
- Python package metadata and semantic versioning via tags
- Documentation:
  - Comprehensive `README.md` with install, config, and usage
  - Python install guide (`supplemental-docs/PYTHON_INSTALL.md`)
  - Contribution guide (`CONTRIBUTING.md`)
