# VS Code Host Settings Automation

Automate validation and enforcement of required VS Code host-level settings that must be configured before opening devcontainers.

---

## Problem Statement

Several VS Code host-level settings must be configured before opening devcontainers. Without the port forwarding settings, developers hit port conflicts (tinyproxy) and stale forwarded ports that break the devcontainer environment. Without removing Copilot extensions from the auto-install list, Copilot Chat auto-installs on every launch and developers have to manually close/dismiss it each time.

Today this is a manual step documented in the README, which is easy to miss. There is no automated enforcement or validation.

## Required VS Code Host Settings

These settings must be configured in the developer's local VS Code (not in devcontainer.json):

### Port Forwarding (Required -- prevents environment breakage)

| Setting | Required Value | Default | Why |
|---------|---------------|---------|-----|
| `remote.autoForwardPorts` | `false` | `true` | Prevents VS Code from auto-forwarding internal service ports (tinyproxy, etc.) |
| `remote.restoreForwardedPorts` | `false` | `true` | Prevents VS Code from restoring previously forwarded ports on reconnect |
| `remote.otherPortsAttributes` | `{"onAutoForward": "ignore"}` | `{"onAutoForward": "notify"}` | Suppresses port forwarding notifications |

### Extension Auto-Install (Quality of life -- prevents unwanted UI)

| Setting | Required Value | Default | Why |
|---------|---------------|---------|-----|
| `remote.defaultExtensionsIfInstalledLocally` | Remove `GitHub.copilot` and `GitHub.copilot-chat` | Includes both | Copilot Chat auto-installs and must be manually dismissed each launch |

### Built-in Copilot Suppression (Quality of life -- prevents unwanted UI)

VS Code 1.96+ bundles Copilot as a built-in extension. Even after removing standalone Copilot extensions, the built-in version shows a "Finish setup" prompt and Copilot chat panel unless these settings are configured:

| Setting | Required Value | Default | Why |
|---------|---------------|---------|-----|
| `github.copilot.enable` | `{"*": false}` | `{"*": true}` | Disables Copilot completions and suggestions |
| `github.copilot.editor.enableAutoCompletions` | `false` | `true` | Disables Copilot inline auto-completions |
| `github.copilot.renameSuggestions.triggerAutomatically` | `false` | `true` | Disables Copilot rename suggestions |
| `chat.extensionUnification.enabled` | `false` | `true` | Prevents VS Code from merging Copilot functionality into the chat extension, which causes the "Finish setup" prompt |

Note: These settings are also enforced inside the devcontainer via `devcontainer.json` settings. The host-level configuration prevents the "Finish setup" prompt from appearing before the container builds.

## Implementation Phases

### Phase 1: `initializeCommand` Pre-Flight Check

A Python script that runs on the host before the container is built. If settings are misconfigured, the build fails with clear instructions.

### Phase 2: `cdevcontainer doctor` CLI Command

A CLI command that validates host settings and optionally applies fixes with `--fix`.

### Phase 3: VS Code Managed Policies (Corporate IT)

Machine-level policy files distributed via MDM that enforce settings and prevent user override.

---

## Phase 1: `initializeCommand` Pre-Flight Check

### Overview

The `initializeCommand` field in `devcontainer.json` runs on the **host machine** before the container is built. If the command exits with a non-zero exit code, VS Code halts the build and displays the error output to the developer.

We add a Python script that reads the developer's local VS Code `settings.json`, validates the required settings, and fails with actionable instructions if misconfigured.

### Settings File Locations

| Platform | Path |
|----------|------|
| macOS | `~/Library/Application Support/Code/User/settings.json` |
| Linux | `~/.config/Code/User/settings.json` |
| Windows (native) | `%APPDATA%\Code\User\settings.json` |
| WSL | `/mnt/c/Users/<username>/AppData/Roaming/Code/User/settings.json` |

For Cursor, replace `Code` with `Cursor` in all paths.
For VS Code Insiders, replace `Code` with `Code - Insiders`.

### VS Code JSONC Parsing

VS Code `settings.json` uses JSONC (JSON with Comments) -- it allows `//` line comments, `/* */` block comments, and trailing commas. Python's `json` module cannot parse this natively. The script must strip comments before parsing. Use a regex-based approach:

```python
import re

def strip_jsonc_comments(text: str) -> str:
    """Strip // and /* */ comments from JSONC text."""
    # Remove single-line comments (but not inside strings)
    text = re.sub(r'(?<!:)//.*$', '', text, flags=re.MULTILINE)
    # Remove multi-line comments
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    # Remove trailing commas before } or ]
    text = re.sub(r',\s*([}\]])', r'\1', text)
    return text
```

Edge case: `//` inside JSON string values (e.g., URLs). The regex above handles the common case. A production implementation should use a proper JSONC tokenizer or only strip comments that start at the beginning of a line or after whitespace.

### IDE Detection

`initializeCommand` does not receive an environment variable identifying which IDE launched it. Detection strategy:

1. Check `TERM_PROGRAM` environment variable (set by some terminals but not reliably by VS Code)
2. Check `VSCODE_IPC_HOOK_CLI` or other `VSCODE_*` environment variables to confirm VS Code
3. Fall back to checking multiple paths in order: `Code`, `Cursor`, `Code - Insiders`

### WSL Username Detection

On WSL, the VS Code settings live on the Windows filesystem. To find the Windows username:

1. Check `$LOGNAME` or `$USER` (may be the WSL user, not Windows user)
2. Run `cmd.exe /C "echo %USERNAME%"` to get the Windows username
3. Scan `/mnt/c/Users/` for directories containing `AppData/Roaming/Code/User/settings.json`

### Platform Reliability Matrix

| Platform | Python Available | Settings Path Reliable | Overall |
|----------|-----------------|----------------------|---------|
| macOS | Yes (Xcode CLI tools) | Yes | Reliable |
| Linux | Yes (system package) | Yes | Reliable |
| WSL | Yes | Requires Windows path resolution | Reliable with fallback |
| Windows native | Maybe not | Yes if Python available | Fragile -- falls through to Phase 2 |

### Error Output Format

When settings are misconfigured, the script prints clear instructions and exits 1:

```
ERROR: VS Code host settings are misconfigured.

Fix these settings before opening this devcontainer:

  Open VS Code Settings (Cmd/Ctrl + ,) > Features > Remote:

  [FAIL] Auto Forward Ports -- must be disabled (currently: enabled)
  [FAIL] Restore Forwarded Ports -- must be disabled (currently: enabled)
  [FAIL] Default Extensions If Installed Locally -- remove GitHub.copilot, GitHub.copilot-chat
  [FAIL] Chat Extension Unification -- must be disabled (currently: enabled)
  [FAIL] Copilot Enable -- must be disabled for all languages (currently: enabled)
  [ OK ] Other Ports Attributes -- correctly configured

  After fixing these settings, reopen the devcontainer.
```

### Files to Create

#### `common/devcontainer-assets/check-host-settings.py`

Host-side Python script. Must use **only Python standard library** (no pip dependencies -- this runs on the host before the container exists).

**Responsibilities:**
1. Detect platform (macOS, Linux, WSL, Windows)
2. Detect IDE (VS Code, Cursor, VS Code Insiders)
3. Locate `settings.json` on disk
4. Parse JSONC content
5. Validate required settings
6. Print results and exit 0 (pass) or 1 (fail)

**Design constraints:**
- No external dependencies -- standard library only (`json`, `re`, `os`, `sys`, `platform`, `subprocess`)
- No `sleep` or time-based delays
- Fail fast with clear error messages
- Must handle missing `settings.json` gracefully (first-time VS Code installs may not have one)
- All configuration values (expected settings, paths) must be defined as constants, not hard-coded inline

#### `devcontainer.json` changes (all catalog entries + `.devcontainer/`)

Add `initializeCommand` field:

```json
"initializeCommand": "python3 .devcontainer/check-host-settings.py"
```

Note: The script must already be in `.devcontainer/` at the time `initializeCommand` runs. This means it is distributed as a common devcontainer asset (via `common/devcontainer-assets/`), which is copied into `.devcontainer/` during `cdevcontainer setup-devcontainer`.

For existing projects that already have `.devcontainer/` set up, the script will be copied on next catalog update (via `cdevcontainer code --regenerate-shell-env` or re-running setup).

### Files to Modify

#### `catalog/default/devcontainer.json`

Add `initializeCommand` field.

#### `catalog/test-entry/devcontainer.json`

Add `initializeCommand` field.

#### `.devcontainer/devcontainer.json`

Add `initializeCommand` field.

### Tests

#### Unit Tests: `tests/unit/test_check_host_settings.py`

The check-host-settings.py script should be importable as a module for unit testing. Structure the script with functions that can be tested individually:

| Test | Description |
|------|-------------|
| `test_strip_jsonc_comments_line_comments` | `//` comments are stripped |
| `test_strip_jsonc_comments_block_comments` | `/* */` comments are stripped |
| `test_strip_jsonc_comments_trailing_commas` | Trailing commas removed |
| `test_strip_jsonc_comments_preserves_urls` | `://` in URLs not stripped |
| `test_detect_platform_macos` | Returns `"macos"` on Darwin |
| `test_detect_platform_linux` | Returns `"linux"` on Linux (non-WSL) |
| `test_detect_platform_wsl` | Returns `"wsl"` when uname contains Microsoft |
| `test_detect_platform_windows` | Returns `"windows"` on Windows |
| `test_settings_path_macos` | Correct path for macOS |
| `test_settings_path_linux` | Correct path for Linux |
| `test_settings_path_cursor` | Uses `Cursor` instead of `Code` |
| `test_validate_settings_all_correct` | Returns no errors when all settings correct |
| `test_validate_settings_auto_forward_enabled` | Detects `autoForwardPorts: true` |
| `test_validate_settings_restore_forwarded_enabled` | Detects `restoreForwardedPorts: true` |
| `test_validate_settings_copilot_in_default_extensions` | Detects Copilot in extension list |
| `test_validate_settings_copilot_enable_default` | Detects `github.copilot.enable` not set to `{"*": false}` |
| `test_validate_settings_extension_unification_enabled` | Detects `chat.extensionUnification.enabled: true` |
| `test_validate_settings_missing_key_uses_default` | Missing key treated as VS Code default |
| `test_validate_settings_empty_file` | Empty settings.json uses all defaults |
| `test_missing_settings_file` | Missing file handled gracefully |
| `test_format_error_output` | Error message format matches spec |

#### Functional Tests: `tests/functional/test_check_host_settings.py`

| Test | Description |
|------|-------------|
| `test_script_exits_zero_on_correct_settings` | Script with correct settings exits 0 |
| `test_script_exits_one_on_bad_settings` | Script with bad settings exits 1 |
| `test_script_output_contains_instructions` | Error output includes fix instructions |
| `test_script_handles_missing_file` | Graceful handling when settings.json absent |
| `test_script_handles_jsonc_with_comments` | Parses settings.json with comments correctly |

#### Functional Tests: `tests/functional/test_catalog_structure.py`

| Test | Description |
|------|-------------|
| `test_check_host_settings_script_exists` | `common/devcontainer-assets/check-host-settings.py` exists |
| `test_check_host_settings_script_is_valid_python` | Script compiles without syntax errors |

### Verification

1. `cd caylent-devcontainer-cli && make lint` -- passes
2. `cd caylent-devcontainer-cli && make test` -- passes
3. `cd /workspaces/devcontainer && make pre-commit-check` -- passes
4. Manual: Create a temp VS Code settings.json with bad settings, run script, verify it fails with correct output
5. Manual: Create a temp VS Code settings.json with correct settings, run script, verify it passes

---

## Phase 2: `cdevcontainer doctor` CLI Command

### Overview

A new top-level CLI command that validates VS Code host settings and optionally applies fixes. This covers platforms where the `initializeCommand` pre-flight check cannot run (Windows native without Python, Cursor, VS Code Insiders) and provides a self-service troubleshooting tool.

### Command Interface

```bash
# Check host settings (read-only, report issues)
cdevcontainer doctor

# Check and fix host settings
cdevcontainer doctor --fix

# Check settings for a specific IDE
cdevcontainer doctor --ide cursor
cdevcontainer doctor --ide vscode-insiders

# Check all detected IDEs
cdevcontainer doctor --all-ides
```

### Supported IDEs

| IDE | Argument | Settings Directory Name |
|-----|----------|------------------------|
| VS Code | `vscode` (default) | `Code` |
| Cursor | `cursor` | `Cursor` |
| VS Code Insiders | `vscode-insiders` | `Code - Insiders` |

### Command Behavior

**Read-only mode (default):**
1. Detect OS
2. Detect IDE (from `--ide` argument or default to VS Code)
3. Locate settings.json
4. Parse JSONC
5. Validate settings
6. Print report (pass/fail per setting)
7. Exit 0 if all pass, exit 1 if any fail

**Fix mode (`--fix`):**
1. Same as read-only steps 1-6
2. For each failing setting, update the parsed JSON
3. Write the updated settings.json back to disk
4. Re-validate to confirm fixes applied
5. Print summary of changes made

**Fix mode constraints:**
- Must preserve existing settings (only add/modify the specific keys)
- Must preserve JSONC comments (read as JSONC, write as standard JSON with a note that comments were stripped, OR implement comment-preserving write)
- Must create a backup of the original file before modifying (e.g., `settings.json.bak`)
- Must prompt for confirmation before writing (unless `--yes` flag is passed)

### Files to Create

#### `caylent-devcontainer-cli/src/caylent_devcontainer_cli/commands/doctor.py`

CLI command module following the existing command pattern.

**Functions:**
- `register_command(subparsers)` -- register the `doctor` command with argparse
- `handle_doctor(args)` -- main handler
- Uses lazy imports for doctor-specific utilities

#### `caylent-devcontainer-cli/src/caylent_devcontainer_cli/utils/host_settings.py`

Utility module containing the core logic (shared between the CLI command and the initializeCommand script).

**Functions:**
- `detect_platform() -> str` -- returns `"macos"`, `"linux"`, `"wsl"`, or `"windows"`
- `get_settings_path(platform: str, ide: str) -> str` -- returns the full path to settings.json
- `parse_jsonc(content: str) -> dict` -- parse JSONC content to a Python dict
- `validate_host_settings(settings: dict) -> list[HostSettingIssue]` -- validate and return issues
- `apply_fixes(settings: dict, issues: list[HostSettingIssue]) -> dict` -- return fixed settings dict
- `format_report(issues: list[HostSettingIssue]) -> str` -- format human-readable report

**Dataclass:**
```python
@dataclass
class HostSettingIssue:
    setting_key: str
    display_name: str
    expected: Any
    actual: Any
    severity: str  # "required" or "recommended"
    fix_description: str
```

### Files to Modify

#### `caylent-devcontainer-cli/src/caylent_devcontainer_cli/cli.py`

- Add `doctor` to the imports (line 7)
- Add `doctor.register_command(subparsers)` in `build_parser()` (after line 65)

#### `caylent-devcontainer-cli/src/caylent_devcontainer_cli/utils/constants.py`

Add constants:
- `VSCODE_SETTINGS_DIR_NAMES` -- mapping of IDE identifiers to directory names
- `VSCODE_SETTINGS_PATHS` -- mapping of platform to base path patterns
- `REQUIRED_HOST_SETTINGS` -- dict of required settings with expected values and defaults
- `RECOMMENDED_HOST_SETTINGS` -- dict of recommended settings

#### `caylent-devcontainer-cli/README.md`

- Add `doctor` to the Commands list
- Add usage examples
- Document the `--fix` flag

### Tests

#### Unit Tests: `tests/unit/test_doctor.py`

| Test | Description |
|------|-------------|
| `TestRegisterCommand::test_registers_doctor_command` | `doctor` subcommand registered in argparse |
| `TestRegisterCommand::test_fix_flag_registered` | `--fix` flag available |
| `TestRegisterCommand::test_ide_flag_registered` | `--ide` flag with choices |
| `TestHandleDoctor::test_all_settings_correct_exits_zero` | Exit 0 when no issues |
| `TestHandleDoctor::test_bad_settings_exits_one` | Exit 1 when issues found |
| `TestHandleDoctor::test_fix_mode_writes_settings` | `--fix` updates settings.json |
| `TestHandleDoctor::test_fix_mode_creates_backup` | `--fix` creates .bak file |
| `TestHandleDoctor::test_missing_settings_file_reports_error` | Clear error for missing file |

#### Unit Tests: `tests/unit/test_host_settings.py`

| Test | Description |
|------|-------------|
| `TestDetectPlatform::test_macos` | `platform.system() == "Darwin"` returns `"macos"` |
| `TestDetectPlatform::test_linux` | Non-WSL Linux returns `"linux"` |
| `TestDetectPlatform::test_wsl` | WSL uname returns `"wsl"` |
| `TestGetSettingsPath::test_macos_vscode` | Correct path |
| `TestGetSettingsPath::test_linux_cursor` | Uses `Cursor` dir |
| `TestGetSettingsPath::test_wsl_resolves_windows_user` | Finds Windows username |
| `TestParseJsonc::test_line_comments` | Strips `//` comments |
| `TestParseJsonc::test_block_comments` | Strips `/* */` comments |
| `TestParseJsonc::test_trailing_commas` | Removes trailing commas |
| `TestParseJsonc::test_preserves_url_strings` | `://` in values preserved |
| `TestValidateHostSettings::test_all_correct` | No issues returned |
| `TestValidateHostSettings::test_auto_forward_default` | Missing key uses VS Code default (true) -> issue |
| `TestValidateHostSettings::test_copilot_in_extensions` | Copilot detected in list |
| `TestValidateHostSettings::test_empty_settings` | All defaults -> multiple issues |
| `TestApplyFixes::test_adds_missing_settings` | Missing keys added |
| `TestApplyFixes::test_corrects_wrong_values` | Wrong values corrected |
| `TestApplyFixes::test_removes_copilot_from_list` | Copilot entries removed |
| `TestApplyFixes::test_preserves_existing_settings` | Unrelated settings untouched |
| `TestFormatReport::test_all_pass` | "All settings OK" message |
| `TestFormatReport::test_failures_shown` | Each failure listed with instructions |
| `TestFormatReport::test_severity_indicated` | Required vs recommended distinction |

#### Functional Tests: `tests/functional/test_doctor_command.py`

| Test | Description |
|------|-------------|
| `test_doctor_help` | `cdevcontainer doctor --help` exits 0 with usage info |
| `test_doctor_in_main_help` | `cdevcontainer --help` lists `doctor` command |
| `test_doctor_reads_settings_file` | With a temp settings.json, validates correctly |
| `test_doctor_fix_creates_backup` | `--fix` creates settings.json.bak |
| `test_doctor_fix_corrects_settings` | `--fix` writes correct values |
| `test_doctor_reports_missing_file` | Reports error when settings.json not found |

### Verification

1. `cd caylent-devcontainer-cli && make lint` -- passes
2. `cd caylent-devcontainer-cli && make test` -- passes (90%+ unit test coverage)
3. `cd /workspaces/devcontainer && make pre-commit-check` -- passes
4. Manual: `cdevcontainer doctor` on a fresh VS Code install shows failures
5. Manual: `cdevcontainer doctor --fix` corrects settings and re-check passes
6. Manual: `cdevcontainer doctor --ide cursor` targets Cursor settings

### Shared Code Between Phase 1 and Phase 2

The `host_settings.py` utility module in the CLI contains the core logic. The `check-host-settings.py` initializeCommand script should import from this module if the CLI is installed on the host, or contain a standalone copy of the essential logic (platform detection, JSONC parsing, validation) for environments where the CLI is not installed.

Recommended approach: `check-host-settings.py` is a standalone script with zero dependencies (not even the CLI package). It duplicates the core validation logic from `host_settings.py`. This is an acceptable DRY exception because:
- The initializeCommand script runs on the host where the CLI may not be installed
- The script must use only Python standard library
- The duplication is limited to ~100 lines of platform detection and JSONC parsing

A comment at the top of both files should reference the other to keep them in sync:
```python
# NOTE: Core validation logic is duplicated in:
#   - common/devcontainer-assets/check-host-settings.py (standalone, initializeCommand)
#   - caylent-devcontainer-cli/src/.../utils/host_settings.py (CLI module)
# Changes to validation rules must be applied to both files.
```

---

## Phase 3: VS Code Managed Policies (Corporate IT)

### Overview

VS Code supports machine-level policy files that enforce settings and prevent users from overriding them. This is the standard enterprise approach. Implementation is owned by Corporate IT since it requires admin access and MDM infrastructure.

### Policy File Locations

| Platform | Path |
|----------|------|
| macOS | `/Library/Application Support/Microsoft/vscode/policy.json` |
| Linux | `/etc/vscode/policy.json` |
| Windows | Registry: `HKLM\SOFTWARE\Policies\Microsoft\VSCode` or `%ProgramFiles%\Microsoft VS Code\policy.json` |

### Policy File Content

```json
{
  "remote.autoForwardPorts": false,
  "remote.restoreForwardedPorts": false,
  "remote.otherPortsAttributes": {
    "onAutoForward": "ignore"
  },
  "github.copilot.enable": {
    "*": false
  },
  "github.copilot.editor.enableAutoCompletions": false,
  "github.copilot.renameSuggestions.triggerAutomatically": false,
  "chat.extensionUnification.enabled": false
}
```

Note: `remote.defaultExtensionsIfInstalledLocally` may not be policy-capable. The `github.copilot.*` and `chat.extensionUnification.*` settings need verification against the VS Code policy documentation for policy-capability.

### Distribution Methods

| Method | Platforms | Tool |
|--------|-----------|------|
| Jamf | macOS | Profile or script |
| Intune | Windows, macOS | Configuration profile |
| Ansible | Linux, macOS | Playbook |
| Group Policy | Windows | GPO template |
| Chef/Puppet | All | Recipe/manifest |

### Dev Team Deliverables for Corporate IT

1. **Policy file content** -- the JSON above
2. **Documentation** -- which settings, why they're required, what breaks without them
3. **Validation script** -- a script IT can run to verify the policy is applied (reuse `cdevcontainer doctor`)
4. **Rollout plan** -- recommended phased rollout (pilot group -> team -> org)

### Tests

No automated tests for Phase 3 -- this is an IT infrastructure deliverable. Validation is manual or via `cdevcontainer doctor`.

---

## Implementation Order

| Order | Work Item | Dependencies | Estimated Scope |
|-------|-----------|-------------|-----------------|
| 1 | Create `host_settings.py` utility module | None | New file + unit tests |
| 2 | Create `check-host-settings.py` standalone script | None (duplicates core logic) | New file + unit tests |
| 3 | Add `initializeCommand` to all devcontainer.json files | Work item 2 | Modify 3 local + 2 remote devcontainer.json files |
| 4 | Create `doctor.py` command module | Work item 1 | New file + unit tests |
| 5 | Register `doctor` command in CLI | Work item 4 | Modify cli.py |
| 6 | Add functional tests for doctor command | Work items 4, 5 | New test file |
| 7 | Add functional tests for check-host-settings script | Work item 2 | New test file |
| 8 | Update documentation (README, CLI README) | Work items 3, 5 | Modify 2 files |
| 9 | Update remote catalog repos | Work items 2, 3 | Push via gh api |
| 10 | Deliver policy file spec to Corporate IT | None | Documentation only |

---

## Acceptance Criteria

### Phase 1
- [ ] `check-host-settings.py` exists in `common/devcontainer-assets/`
- [ ] Script uses only Python standard library (no pip dependencies)
- [ ] Script detects macOS, Linux, and WSL platforms
- [ ] Script locates VS Code and Cursor settings.json paths
- [ ] Script parses JSONC (handles comments and trailing commas)
- [ ] Script validates all required host settings
- [ ] Script exits 0 when all settings correct
- [ ] Script exits 1 with actionable error message when settings misconfigured
- [ ] Script handles missing settings.json gracefully (treats as all-defaults)
- [ ] `initializeCommand` added to all devcontainer.json files (local + remote catalogs)
- [ ] All unit tests pass with 90%+ coverage
- [ ] All functional tests pass
- [ ] `make lint` passes
- [ ] `make pre-commit-check` passes

### Phase 2
- [ ] `cdevcontainer doctor` command registered and functional
- [ ] `--fix` flag applies corrections to settings.json
- [ ] `--fix` creates backup before modifying
- [ ] `--ide` flag supports `vscode`, `cursor`, `vscode-insiders`
- [ ] Read-only mode exits 0 (pass) or 1 (fail)
- [ ] Report clearly distinguishes required vs recommended settings
- [ ] Documentation updated (CLI README, main README)
- [ ] All unit tests pass with 90%+ coverage
- [ ] All functional tests pass
- [ ] `make lint` passes
- [ ] `make pre-commit-check` passes

### Phase 3
- [ ] Policy file content documented
- [ ] Distribution methods documented per platform
- [ ] Validation approach documented (using `cdevcontainer doctor`)
- [ ] Deliverable handed to Corporate IT

---

## Claude Code Implementation Prompt

Use this prompt to implement the work items. Provide it as context when starting implementation.

```
Implement the VS Code host settings automation feature for the caylent-devcontainer-cli project.

Reference the backlog spec at: /workspaces/devcontainer/backlog/vscode-host-settings-automation.md

Key constraints from CLAUDE.md that apply:
- Never hard-code configuration values -- use constants
- Fail fast with clear, actionable error messages
- No sleep or time-based delays
- No fallback logic -- fail clearly
- All code must be idiomatic Python
- SOLID and DRY principles (with documented exception for standalone script duplication)
- Tests must validate actual behavior, not mock success
- Tests must maintain 90%+ unit test coverage
- Update all documentation in sync with code changes
- Never bypass linters or security checks
- Never add inline suppression comments (noqa, nosec, etc.)
- Evidence-based communication -- no speculative performance claims

Development workflow:
1. Install: cd caylent-devcontainer-cli && make install
2. Lint: cd caylent-devcontainer-cli && make lint
3. Unit tests: cd caylent-devcontainer-cli && make unit-test
4. Functional tests: cd caylent-devcontainer-cli && make functional-test
5. Pre-commit: cd /workspaces/devcontainer && make pre-commit-check

Existing patterns to follow:
- Command registration: see commands/catalog.py register_command()
- CLI entry point: see cli.py build_parser()
- Validation pattern: see utils/validation.py ValidationResult dataclass
- Error handling: use utils/ui.py log(), exit_with_error()
- Constants: add to utils/constants.py
- Unit tests: unittest.TestCase with @patch, in tests/unit/
- Functional tests: subprocess.run() against CLI, in tests/functional/
- Code style: black (120 chars), isort, flake8

Start with Phase 1 (initializeCommand script), then Phase 2 (doctor command).
Push changes to remote catalogs via gh api after all local tests pass.
```
