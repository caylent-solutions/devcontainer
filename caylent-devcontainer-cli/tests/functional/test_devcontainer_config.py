"""Functional tests validating devcontainer configuration file patterns.

These tests read the actual .devcontainer/ files in the repository and validate
that they conform to the S1.3.5 and S1.3.6 requirements: no containerEnv, shell.env
sourced first, sudo -E used, proxy validation with active polling, no sleep commands,
git authentication with token/SSH branching.
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

    def test_post_create_command_calls_postcreate_wrapper(self):
        """postCreateCommand must call postcreate-wrapper.sh."""
        cmd = self.config["postCreateCommand"]
        self.assertIn("postcreate-wrapper.sh", cmd)

    def test_postcreate_wrapper_sources_shell_env_first(self):
        """postcreate-wrapper.sh must source shell.env before all other operations."""
        wrapper = _read_file("postcreate-wrapper.sh")
        self.assertIn("source shell.env", wrapper)
        shell_env_pos = wrapper.index("source shell.env")
        apt_get_pos = wrapper.index("apt-get")
        self.assertLess(shell_env_pos, apt_get_pos)

    def test_postcreate_wrapper_configures_apt_proxy(self):
        """postcreate-wrapper.sh must configure apt proxy via apt.conf.d before apt-get."""
        wrapper = _read_file("postcreate-wrapper.sh")
        self.assertIn("/etc/apt/apt.conf.d/99proxy", wrapper)
        proxy_conf_pos = wrapper.index("/etc/apt/apt.conf.d/99proxy")
        apt_get_pos = wrapper.index("apt-get update")
        self.assertLess(proxy_conf_pos, apt_get_pos)

    def test_postcreate_wrapper_adds_no_proxy_direct_overrides(self):
        """postcreate-wrapper.sh must add DIRECT overrides for NO_PROXY domains."""
        wrapper = _read_file("postcreate-wrapper.sh")
        self.assertIn("NO_PROXY", wrapper)
        self.assertIn("DIRECT", wrapper)

    def test_postcreate_wrapper_uses_sudo_e_for_postcreate(self):
        """postcreate-wrapper.sh must use sudo -E for postcreate.sh to pass env vars."""
        wrapper = _read_file("postcreate-wrapper.sh")
        self.assertIn("sudo -E bash", wrapper)

    def test_postcreate_wrapper_has_wsl_and_non_wsl_paths(self):
        """postcreate-wrapper.sh must handle both WSL and non-WSL environments."""
        wrapper = _read_file("postcreate-wrapper.sh")
        self.assertIn("microsoft", wrapper)

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

    def test_apt_uses_sudo_without_e(self):
        """Postcreate apt-get must use sudo (not sudo -E) since proxy comes from apt.conf.d."""
        for i, line in enumerate(self.content.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if "apt-get" in stripped and "sudo -E" in stripped:
                self.fail(f"Line {i} uses sudo -E for apt-get (proxy comes from apt.conf.d, not env): {stripped}")

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

    def test_configure_apt_proxy_function_exists(self):
        """devcontainer-functions.sh must define configure_apt_proxy function."""
        self.assertIn("configure_apt_proxy()", self.content)

    def test_configure_apt_proxy_writes_apt_conf(self):
        """configure_apt_proxy must write to /etc/apt/apt.conf.d/99proxy."""
        self.assertIn("/etc/apt/apt.conf.d/99proxy", self.content)

    def test_configure_apt_proxy_handles_no_proxy(self):
        """configure_apt_proxy must parse NO_PROXY and add DIRECT overrides."""
        self.assertIn("NO_PROXY", self.content)
        self.assertIn('"DIRECT"', self.content)

    def test_configure_git_shared_function_exists(self):
        """devcontainer-functions.sh must define configure_git_shared function."""
        self.assertIn("configure_git_shared()", self.content)

    def test_configure_git_token_function_exists(self):
        """devcontainer-functions.sh must define configure_git_token function."""
        self.assertIn("configure_git_token()", self.content)

    def test_configure_git_ssh_function_exists(self):
        """devcontainer-functions.sh must define configure_git_ssh function."""
        self.assertIn("configure_git_ssh()", self.content)

    def test_git_shared_config_has_user_section(self):
        """Shared git config must include [user] section with name and email."""
        self.assertIn("[user]", self.content)
        self.assertIn("name = ${git_user}", self.content)
        self.assertIn("email = ${git_user_email}", self.content)

    def test_git_shared_config_has_pager_section(self):
        """Shared git config must disable pager for common commands."""
        self.assertIn("[pager]", self.content)
        self.assertIn("branch = false", self.content)
        self.assertIn("diff = false", self.content)
        self.assertIn("log = false", self.content)

    def test_git_shared_config_has_safe_directory(self):
        """Shared git config must set safe.directory = *."""
        self.assertIn("[safe]", self.content)
        self.assertIn("directory = *", self.content)

    def test_git_shared_config_has_push_auto_setup(self):
        """Shared git config must set push.autoSetupRemote = true."""
        self.assertIn("[push]", self.content)
        self.assertIn("autoSetupRemote = true", self.content)

    def test_git_token_creates_netrc(self):
        """Token method must create .netrc with machine, login, password."""
        self.assertIn("machine ${git_provider_url}", self.content)
        self.assertIn("login ${git_user}", self.content)
        self.assertIn("password ${git_token}", self.content)

    def test_git_token_sets_netrc_permissions(self):
        """Token method must set .netrc permissions to 600."""
        self.assertIn('chmod 600 "${netrc}"', self.content)

    def test_git_token_adds_credential_helper(self):
        """Token method must add credential helper = store to .gitconfig."""
        self.assertIn("[credential]", self.content)
        self.assertIn("helper = store", self.content)

    def test_git_ssh_installs_openssh(self):
        """SSH method must ensure openssh-client is installed."""
        self.assertIn("openssh-client", self.content)

    def test_git_ssh_creates_ssh_dir(self):
        """SSH method must create .ssh directory with 700 permissions."""
        self.assertIn('mkdir -p "${ssh_dir}"', self.content)
        self.assertIn('chmod 700 "${ssh_dir}"', self.content)

    def test_git_ssh_copies_private_key(self):
        """SSH method must copy ssh-private-key with 600 permissions."""
        self.assertIn("ssh-private-key", self.content)
        self.assertIn('chmod 600 "${ssh_key_dest}"', self.content)

    def test_git_ssh_runs_keyscan(self):
        """SSH method must run ssh-keyscan for GIT_PROVIDER_URL."""
        self.assertIn("ssh-keyscan", self.content)
        self.assertIn("known_hosts", self.content)

    def test_git_ssh_creates_config(self):
        """SSH method must create ~/.ssh/config with correct entries."""
        self.assertIn("Host ${git_provider_url}", self.content)
        self.assertIn("HostName ${git_provider_url}", self.content)
        self.assertIn("User git", self.content)
        self.assertIn("IdentityFile ${ssh_key_dest}", self.content)
        self.assertIn("IdentitiesOnly yes", self.content)

    def test_git_ssh_sets_config_permissions(self):
        """SSH method must set ~/.ssh/config permissions to 600."""
        self.assertIn('chmod 600 "${ssh_dir}/config"', self.content)

    def test_git_ssh_verifies_connectivity(self):
        """SSH method must verify SSH connectivity with ssh -T."""
        self.assertIn("ssh -T", self.content)

    def test_git_ssh_checks_permission_denied(self):
        """SSH method must detect permission denied errors."""
        self.assertIn("permission denied", self.content)


class TestPostcreateGitAuth(TestCase):
    """Validate git authentication patterns in postcreate.sh."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read_file(".devcontainer.postcreate.sh")

    def test_git_auth_method_required(self):
        """Postcreate must exit with error when GIT_AUTH_METHOD is unset."""
        self.assertIn("GIT_AUTH_METHOD is required", self.content)

    def test_git_auth_method_branching(self):
        """Postcreate must branch on GIT_AUTH_METHOD value."""
        self.assertIn('case "${GIT_AUTH_METHOD}"', self.content)
        self.assertIn("token)", self.content)
        self.assertIn("ssh)", self.content)

    def test_invalid_git_auth_method_rejected(self):
        """Postcreate must reject invalid GIT_AUTH_METHOD values."""
        self.assertIn("Invalid GIT_AUTH_METHOD", self.content)

    def test_shared_git_config_called(self):
        """Postcreate must call configure_git_shared for both methods."""
        self.assertIn("configure_git_shared", self.content)

    def test_token_method_calls_configure_git_token(self):
        """Postcreate must call configure_git_token for token method."""
        self.assertIn("configure_git_token", self.content)

    def test_ssh_method_calls_configure_git_ssh(self):
        """Postcreate must call configure_git_ssh for SSH method."""
        self.assertIn("configure_git_ssh", self.content)

    def test_cicd_skips_git_configuration(self):
        """CICD mode must skip git configuration."""
        self.assertIn("CICD mode enabled - skipping Git configuration", self.content)

    def test_no_hardcoded_netrc_outside_function(self):
        """Postcreate must not create .netrc directly — delegated to function."""
        lines = self.content.splitlines()
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            # .netrc should only appear in the function call, not inline cat heredoc
            if "cat <<EOF > " in stripped and ".netrc" in stripped:
                self.fail(f"Line {i} creates .netrc directly instead of using function: {stripped}")
