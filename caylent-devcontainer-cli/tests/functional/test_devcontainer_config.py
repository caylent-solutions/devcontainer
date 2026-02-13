"""Functional tests validating devcontainer configuration file patterns.

These tests read the actual .devcontainer/ files in the repository and validate
that they conform to the S1.3.5 requirements: no containerEnv, shell.env sourced
first, sudo -E used, proxy validation with active polling, no sleep commands.
"""

import json
import os
from unittest import TestCase


def _repo_root():
    """Return the repository root directory."""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def _devcontainer_dir():
    """Return the .devcontainer directory path."""
    return os.path.join(_repo_root(), ".devcontainer")


def _read_file(filename):
    """Read a file from .devcontainer/ and return its contents."""
    path = os.path.join(_devcontainer_dir(), filename)
    with open(path) as f:
        return f.read()


class TestDevcontainerJson(TestCase):
    """Validate devcontainer.json structure and content."""

    @classmethod
    def setUpClass(cls):
        path = os.path.join(_devcontainer_dir(), "devcontainer.json")
        with open(path) as f:
            cls.config = json.load(f)
        with open(path) as f:
            cls.raw = f.read()

    def test_no_container_env_block(self):
        """containerEnv block must be removed — all env vars come from shell.env."""
        self.assertNotIn("containerEnv", self.config)

    def test_post_create_command_sources_shell_env_first(self):
        """postCreateCommand must source shell.env before all other operations."""
        cmd = self.config["postCreateCommand"]
        # After the log tee redirect, shell.env must be sourced before apt-get
        self.assertIn("source shell.env", cmd)
        shell_env_pos = cmd.index("source shell.env")
        apt_get_pos = cmd.index("apt-get")
        self.assertLess(shell_env_pos, apt_get_pos)

    def test_post_create_command_uses_sudo_e(self):
        """postCreateCommand must use sudo -E to preserve environment variables."""
        cmd = self.config["postCreateCommand"]
        # Every sudo in the command should be sudo -E
        self.assertNotIn("sudo apt-get", cmd)
        self.assertNotIn("sudo bash", cmd)
        self.assertIn("sudo -E apt-get", cmd)
        self.assertIn("sudo -E bash", cmd)

    def test_post_create_command_has_wsl_and_non_wsl_paths(self):
        """postCreateCommand must handle both WSL and non-WSL environments."""
        cmd = self.config["postCreateCommand"]
        self.assertIn("uname -r | grep -i microsoft", cmd)

    def test_post_create_command_has_log_tee(self):
        """postCreateCommand must tee output to setup log file."""
        cmd = self.config["postCreateCommand"]
        self.assertIn("tee /tmp/devcontainer-setup.log", cmd)


class TestPostcreateScript(TestCase):
    """Validate .devcontainer.postcreate.sh content and patterns."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read_file(".devcontainer.postcreate.sh")

    def test_sources_devcontainer_functions(self):
        """Postcreate must source devcontainer-functions.sh."""
        self.assertIn('source "${WORK_DIR}/.devcontainer/devcontainer-functions.sh"', self.content)

    def test_shell_env_sourced_in_bashrc(self):
        """Postcreate must configure shell.env sourcing in .bashrc."""
        self.assertIn('source \\"${WORK_DIR}/shell.env\\"', self.content)

    def test_bash_env_set_in_bashrc(self):
        """Postcreate must set BASH_ENV to shell.env in .bashrc."""
        self.assertIn('BASH_ENV=\\"${WORK_DIR}/shell.env\\"', self.content)

    def test_shell_env_sourced_in_zshenv(self):
        """Postcreate must configure shell.env sourcing in .zshenv."""
        self.assertIn(".zshenv", self.content)
        self.assertIn('source \\"${WORK_DIR}/shell.env\\"', self.content)

    def test_cicd_read_from_runtime_environment(self):
        """CICD must be read from runtime environment, not shell.env."""
        self.assertIn('CICD_VALUE="${CICD:-false}"', self.content)

    def test_no_sleep_commands(self):
        """Postcreate must not contain any sleep commands."""
        for i, line in enumerate(self.content.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            self.assertNotRegex(
                stripped,
                r"\bsleep\b",
                f"Line {i} contains 'sleep': {stripped}",
            )

    def test_proxy_validation_uses_validate_host_proxy(self):
        """Proxy validation must call validate_host_proxy function."""
        self.assertIn("validate_host_proxy", self.content)

    def test_proxy_host_port_parsed_from_env(self):
        """Proxy host and port must be parsed from HOST_PROXY_URL, not hardcoded."""
        self.assertIn("parse_proxy_host_port", self.content)
        self.assertIn("PROXY_PARSED_HOST", self.content)
        self.assertIn("PROXY_PARSED_PORT", self.content)

    def test_proxy_url_required_when_proxy_enabled(self):
        """HOST_PROXY_URL must be validated as non-empty when HOST_PROXY=true."""
        self.assertIn("HOST_PROXY_URL", self.content)

    def test_proxy_timeout_configurable(self):
        """Proxy validation timeout must be configurable via HOST_PROXY_TIMEOUT."""
        self.assertIn("HOST_PROXY_TIMEOUT", self.content)

    def test_proxy_readme_references(self):
        """Proxy validation must reference correct README for WSL vs non-WSL."""
        self.assertIn("wsl-family-os/README.md", self.content)
        self.assertIn("nix-family-os/README.md", self.content)

    def test_set_euo_pipefail(self):
        """Postcreate must use strict error handling."""
        self.assertIn("set -euo pipefail", self.content)


class TestDevcontainerFunctions(TestCase):
    """Validate devcontainer-functions.sh content and patterns."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read_file("devcontainer-functions.sh")

    def test_validate_host_proxy_function_exists(self):
        """devcontainer-functions.sh must define validate_host_proxy function."""
        self.assertIn("validate_host_proxy()", self.content)

    def test_parse_proxy_host_port_function_exists(self):
        """devcontainer-functions.sh must define parse_proxy_host_port function."""
        self.assertIn("parse_proxy_host_port()", self.content)

    def test_validate_host_proxy_uses_nc(self):
        """validate_host_proxy must use nc for active port checking."""
        self.assertIn("nc -z -w 1", self.content)

    def test_no_sleep_commands(self):
        """devcontainer-functions.sh must not contain any sleep commands."""
        for i, line in enumerate(self.content.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            self.assertNotRegex(
                stripped,
                r"\bsleep\b",
                f"Line {i} contains 'sleep': {stripped}",
            )

    def test_validate_host_proxy_has_timeout_loop(self):
        """validate_host_proxy must implement timeout-based polling loop."""
        self.assertIn("elapsed", self.content)
        self.assertIn("timeout", self.content)

    def test_parse_proxy_strips_protocol(self):
        """parse_proxy_host_port must strip protocol prefix."""
        self.assertIn("#*://", self.content)

    def test_parse_proxy_validates_port_present(self):
        """parse_proxy_host_port must validate that port is present in URL."""
        self.assertIn("does not contain a port", self.content)

    def test_is_wsl_function_exists(self):
        """devcontainer-functions.sh must define is_wsl function."""
        self.assertIn("is_wsl()", self.content)

    def test_logging_functions_exist(self):
        """devcontainer-functions.sh must define standard logging functions."""
        self.assertIn("log_info()", self.content)
        self.assertIn("log_success()", self.content)
        self.assertIn("log_warn()", self.content)
        self.assertIn("log_error()", self.content)

    def test_exit_with_error_function_exists(self):
        """devcontainer-functions.sh must define exit_with_error function."""
        self.assertIn("exit_with_error()", self.content)
        self.assertIn("exit 1", self.content)
