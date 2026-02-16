# Manual QA Test Plan — Caylent DevContainer CLI v2.0.0

## Prerequisites

Before starting, ensure:

- [ ] CLI installed: `cdevcontainer --version` shows `2.0.0`
- [ ] Clean template state: `rm -rf ~/.devcontainer-templates/*`
- [ ] Create a scratch test directory: `mkdir -p /tmp/qa-test && cd /tmp/qa-test && git init`
- [ ] Default catalog URL is reachable: `git ls-remote https://github.com/caylent-solutions/devcontainer.git HEAD`

---

## 1. Global Options

### 1.1 Version flag

```bash
cdevcontainer --version
```

- [ ] Output: `Caylent Devcontainer CLI 2.0.0`

### 1.2 Help flag

```bash
cdevcontainer --help
```

- [ ] Shows usage with all four command groups: `catalog`, `code`, `template`, `setup-devcontainer`
- [ ] Shows `--version` and `--skip-update-check` options

### 1.3 Skip update check

```bash
cdevcontainer --skip-update-check --help
```

- [ ] No update check output, help displays normally

### 1.4 Unknown command

```bash
cdevcontainer nonexistent-command
```

- [ ] Exits non-zero with usage error

---

## 2. Catalog Commands

### 2.1 `catalog list` — default catalog

```bash
cdevcontainer catalog list
```

- [ ] Clones the default catalog repo
- [ ] Displays a table of available collections
- [ ] Shows at least the `default` collection with name and description
- [ ] Exits 0

### 2.2 `catalog list --tags` — filter by tag

```bash
cdevcontainer catalog list --tags general
```

- [ ] Shows only collections matching the `general` tag
- [ ] `default` collection appears (it has tag `general`)

```bash
cdevcontainer catalog list --tags nonexistent-tag-xyz
```

- [ ] Shows no matching collections or appropriate message
- [ ] Exits non-zero or shows empty result

### 2.3 `catalog list` — custom catalog URL

```bash
DEVCONTAINER_CATALOG_URL=https://github.com/caylent-solutions/devcontainer.git cdevcontainer catalog list
```

- [ ] Uses the environment variable URL
- [ ] Lists collections from that catalog

### 2.4 `catalog validate` — remote default

```bash
cdevcontainer catalog validate
```

- [ ] Validates the default catalog structure
- [ ] Reports number of collections found
- [ ] Exits 0

### 2.5 `catalog validate --local` — local path

```bash
cdevcontainer catalog validate --local /workspaces/devcontainer
```

- [ ] Validates the local repo as a catalog
- [ ] Reports number of collections found
- [ ] Exits 0

### 2.6 `catalog validate --local` — invalid path

```bash
cdevcontainer catalog validate --local /tmp
```

- [ ] Reports validation errors (missing common assets, collections, etc.)
- [ ] Exits non-zero

---

## 3. Template Commands

### 3.1 `template list` — empty state

```bash
cdevcontainer template list
```

- [ ] Shows message indicating no templates found
- [ ] Exits 0

### 3.2 `template create` — full interactive flow

```bash
cdevcontainer template create qa-token-test
```

Walk through all prompts with these values:

| Step | Prompt | Value |
|------|--------|-------|
| 1 | AWS config enabled | `true` |
| 2 | Default Git branch | `main` |
| 3 | Default Python version | `3.12.9` |
| 4 | Developer name | `QA Tester` |
| 5 | Git provider URL | `github.com` |
| 6 | Git authentication method | `token` |
| 7 | Git username | `qa-user` |
| 8 | Git email | `qa@example.com` |
| 9 | Git token | `ghp_testtoken123` |
| 10 | Extra APT packages | (leave empty) |
| 11 | Pager | `cat` |
| 12 | AWS output format | `json` |
| 13 | Host proxy | `false` |
| 14 | Custom env vars | (skip / done) |
| 15 | AWS profile map | (skip / done) |

- [ ] All 15 prompts appear in order (steps 10/14/15 may be skippable)
- [ ] Template saved successfully message
- [ ] File created at `~/.devcontainer-templates/qa-token-test.json`
- [ ] Exits 0

### 3.3 `template create` — SSH auth variant

```bash
cdevcontainer template create qa-ssh-test
```

Use these values (differences from token flow):

| Step | Prompt | Value |
|------|--------|-------|
| 1 | AWS config enabled | `false` |
| 6 | Git authentication method | `ssh` |
| 9 | Git token | *(should NOT be prompted)* |
| 10 | SSH private key | Provide a path to a valid SSH key |

- [ ] Git token prompt is **skipped** (token prompt should not appear)
- [ ] SSH private key prompt appears instead
- [ ] AWS output format prompt is **skipped** (AWS disabled)
- [ ] AWS profile map prompt is **skipped** (AWS disabled)
- [ ] Template saved successfully
- [ ] Exits 0

### 3.4 `template create` — duplicate name

```bash
cdevcontainer template create qa-token-test
```

- [ ] Warns that template already exists
- [ ] Prompts for overwrite confirmation
- [ ] If declined: exits without overwriting
- [ ] If accepted: overwrites and saves

### 3.5 `template list` — populated state

```bash
cdevcontainer template list
```

- [ ] Shows `qa-token-test` with CLI version `2.0.0`
- [ ] Shows `qa-ssh-test` with CLI version `2.0.0`
- [ ] Exits 0

### 3.6 `template save` — from existing project

First, set up a project with config files:

```bash
mkdir -p /tmp/qa-save-test
cp /workspaces/devcontainer/collections/default/example-container-env-values.json /tmp/qa-save-test/devcontainer-environment-variables.json
```

```bash
cdevcontainer template save qa-saved -p /tmp/qa-save-test
```

- [ ] Prompts for confirmation
- [ ] Saves template to `~/.devcontainer-templates/qa-saved.json`
- [ ] Exits 0

### 3.7 `template save` — missing JSON file

```bash
mkdir -p /tmp/qa-empty
cdevcontainer template save qa-missing -p /tmp/qa-empty
```

- [ ] Reports error: `devcontainer-environment-variables.json` not found
- [ ] Exits non-zero

### 3.8 `template load` — into a project

```bash
mkdir -p /tmp/qa-load-test
cdevcontainer template load qa-token-test -p /tmp/qa-load-test
```

- [ ] Loads template and validates it
- [ ] Generates `devcontainer-environment-variables.json` in target directory
- [ ] Generates `shell.env` in target directory
- [ ] Updates `.gitignore` with secret file entries
- [ ] If AWS enabled: creates `.devcontainer/aws-profile-map.json`
- [ ] Exits 0

Verify generated files:

```bash
ls -la /tmp/qa-load-test/devcontainer-environment-variables.json
ls -la /tmp/qa-load-test/shell.env
cat /tmp/qa-load-test/.gitignore
```

- [ ] JSON file exists and contains `containerEnv` key
- [ ] `shell.env` exists and contains `export` statements
- [ ] `.gitignore` contains `devcontainer-environment-variables.json` and `shell.env`

### 3.9 `template load` — nonexistent template

```bash
cdevcontainer template load nonexistent-template
```

- [ ] Reports error: template not found
- [ ] Exits non-zero

### 3.10 `template load` — overwrite confirmation

```bash
cdevcontainer template load qa-token-test -p /tmp/qa-load-test
```

- [ ] Prompts for overwrite confirmation (files already exist from 3.8)
- [ ] If accepted: regenerates files
- [ ] If declined: exits without changes

### 3.11 `template upgrade`

```bash
cdevcontainer template upgrade qa-token-test
```

- [ ] Reports template is already at current version (since it was created with v2.0.0)
- [ ] Exits 0

### 3.12 `template delete` — single template

```bash
cdevcontainer template delete qa-saved
```

- [ ] Prompts for confirmation
- [ ] If accepted: deletes template, confirms deletion
- [ ] Exits 0

```bash
cdevcontainer template list
```

- [ ] `qa-saved` no longer appears

### 3.13 `template delete` — multiple templates

```bash
cdevcontainer template delete qa-token-test qa-ssh-test
```

- [ ] Prompts for confirmation for each template
- [ ] Deletes both if confirmed
- [ ] Exits 0

### 3.14 `template delete` — nonexistent template

```bash
cdevcontainer template delete nonexistent-template
```

- [ ] Reports error: template not found
- [ ] Exits non-zero

---

## 4. Setup-Devcontainer Command

### 4.1 Fresh project setup — interactive flow

```bash
mkdir -p /tmp/qa-setup-test && cd /tmp/qa-setup-test && git init
cdevcontainer setup-devcontainer /tmp/qa-setup-test
```

- [ ] Creates `.tool-versions` if missing
- [ ] Since no `.devcontainer/` exists, proceeds to catalog selection
- [ ] Copies the `default` collection (or prompts if multiple collections)
- [ ] Runs informational validation (displays any issues)
- [ ] Enters interactive setup flow (17-step prompts)
- [ ] After completing prompts, generates project files

Verify results:

```bash
ls -la /tmp/qa-setup-test/.devcontainer/
ls -la /tmp/qa-setup-test/devcontainer-environment-variables.json
ls -la /tmp/qa-setup-test/shell.env
ls -la /tmp/qa-setup-test/.tool-versions
cat /tmp/qa-setup-test/.gitignore
```

- [ ] `.devcontainer/` directory exists with: `devcontainer.json`, `catalog-entry.json`, `VERSION`, `.devcontainer.postcreate.sh`, `devcontainer-functions.sh`, `project-setup.sh`
- [ ] `devcontainer-environment-variables.json` exists with valid JSON
- [ ] `shell.env` exists with `export` statements
- [ ] `.tool-versions` exists
- [ ] `.gitignore` updated with secret file entries

### 4.2 Setup with existing `.devcontainer/` — replacement prompt

```bash
cdevcontainer setup-devcontainer /tmp/qa-setup-test
```

- [ ] Detects existing `.devcontainer/` directory
- [ ] Shows VERSION file content
- [ ] Shows catalog-entry.json info
- [ ] Prompts: "Replace existing files?"
- [ ] If declined: skips catalog replacement, proceeds to interactive setup
- [ ] If accepted: replaces `.devcontainer/` from catalog, then proceeds to interactive setup

### 4.3 Setup with `--catalog-entry` flag

```bash
mkdir -p /tmp/qa-catalog-entry-test && cd /tmp/qa-catalog-entry-test && git init
cdevcontainer setup-devcontainer /tmp/qa-catalog-entry-test --catalog-entry default
```

- [ ] Automatically selects the `default` collection without browsing
- [ ] Proceeds with the rest of the setup flow
- [ ] Exits 0

### 4.4 Setup with custom catalog URL

```bash
mkdir -p /tmp/qa-custom-catalog-test && cd /tmp/qa-custom-catalog-test && git init
DEVCONTAINER_CATALOG_URL=https://github.com/caylent-solutions/devcontainer.git \
  cdevcontainer setup-devcontainer /tmp/qa-custom-catalog-test
```

- [ ] Uses the custom catalog URL
- [ ] Lists collections from that catalog
- [ ] Proceeds with normal flow

### 4.5 Setup with invalid path

```bash
cdevcontainer setup-devcontainer /nonexistent/path
```

- [ ] Reports error: path does not exist or is not a directory
- [ ] Exits non-zero

### 4.6 Setup — template save prompt

During the interactive setup (4.1), at the end of the flow:

- [ ] Asks if you want to save the configuration as a template
- [ ] If yes: asks for template name, saves to `~/.devcontainer-templates/`
- [ ] If no: proceeds without saving

---

## 5. Code Command

### 5.1 `code` — with valid project

First, ensure a project is set up (use output from test 4.1):

```bash
cdevcontainer code /tmp/qa-setup-test
```

- [ ] Loads `devcontainer-environment-variables.json`
- [ ] Runs validation steps
- [ ] Attempts to launch VS Code (`code` command)
- [ ] If VS Code is installed: opens the project
- [ ] If VS Code is not installed: shows install instructions and exits non-zero

### 5.2 `code --ide cursor`

```bash
cdevcontainer code /tmp/qa-setup-test --ide cursor
```

- [ ] Attempts to launch Cursor instead of VS Code
- [ ] If Cursor is installed: opens the project
- [ ] If Cursor is not installed: shows install instructions and exits non-zero

### 5.3 `code` — missing configuration files

```bash
mkdir -p /tmp/qa-no-config
cdevcontainer code /tmp/qa-no-config
```

- [ ] Reports error: `devcontainer-environment-variables.json` not found
- [ ] Exits non-zero

### 5.4 `code --regenerate-shell-env`

```bash
cdevcontainer code /tmp/qa-setup-test --regenerate-shell-env
```

- [ ] Reads existing JSON configuration
- [ ] Regenerates only `shell.env` (does not prompt for anything)
- [ ] Does NOT launch an IDE
- [ ] Exits 0

Verify:

```bash
cat /tmp/qa-setup-test/shell.env
```

- [ ] `shell.env` contains updated `export` statements matching JSON config

### 5.5 `code` — validation detects missing variables

If the template or CLI was upgraded and new required variables were added, the `code` command should detect them. To simulate:

1. Edit `/tmp/qa-setup-test/devcontainer-environment-variables.json` and remove a key (e.g., delete `PAGER`)
2. Run:

```bash
cdevcontainer code /tmp/qa-setup-test
```

- [ ] Detects missing variable(s)
- [ ] Displays which variables are missing
- [ ] Offers options to fix (update devcontainer config or add missing variables only)
- [ ] After fixing, proceeds to launch IDE

### 5.6 `code` — default project root (current directory)

```bash
cd /tmp/qa-setup-test
cdevcontainer code
```

- [ ] Uses current directory as project root
- [ ] Behaves the same as `cdevcontainer code /tmp/qa-setup-test`

---

## 6. Validation Behavior (Cross-Cutting)

### 6.1 Template constraint validation

Create a template with an invalid constraint value:

```bash
# Create a valid template first
cdevcontainer template create qa-constraint-test
# Then manually edit it to have an invalid value
```

Edit `~/.devcontainer-templates/qa-constraint-test.json` and change `GIT_AUTH_METHOD` to `"invalid"`.

```bash
cdevcontainer template load qa-constraint-test -p /tmp/qa-constraint-validate
```

- [ ] Validation catches the invalid `GIT_AUTH_METHOD` value
- [ ] Reports the error with valid options (`token`, `ssh`)
- [ ] Exits non-zero or prompts for correction

### 6.2 Auth consistency — token method

Verify that when `GIT_AUTH_METHOD=token`:
- [ ] `GIT_TOKEN` is required and prompted
- [ ] `ssh-private-key` file is NOT created
- [ ] Template load/create enforces this

### 6.3 Auth consistency — SSH method

Verify that when `GIT_AUTH_METHOD=ssh`:
- [ ] SSH private key is required and prompted
- [ ] `GIT_TOKEN` is removed or not required
- [ ] `.devcontainer/ssh-private-key` file IS created
- [ ] Template load/create enforces this

### 6.4 Host proxy consistency

When `HOST_PROXY=true`:
- [ ] `HOST_PROXY_URL` is required
- [ ] Must start with `http://` or `https://`

When `HOST_PROXY=false`:
- [ ] `HOST_PROXY_URL` is not prompted

### 6.5 AWS consistency

When `AWS_CONFIG_ENABLED=true`:
- [ ] `AWS_DEFAULT_OUTPUT` is prompted
- [ ] AWS profile map prompt appears

When `AWS_CONFIG_ENABLED=false`:
- [ ] `AWS_DEFAULT_OUTPUT` is skipped
- [ ] AWS profile map is skipped
- [ ] No `aws-profile-map.json` created

---

## 7. Edge Cases

### 7.1 Git provider URL validation

During `template create`, for the git provider URL prompt:

- [ ] `github.com` — accepted
- [ ] `gitlab.example.com` — accepted
- [ ] `https://github.com` — rejected (has protocol prefix)
- [ ] `github` — rejected (no dot)
- [ ] Empty — rejected

### 7.2 Custom environment variables — conflict detection

During `template create`, at the custom env vars step:

- [ ] Entering `GIT_TOKEN` as a custom var key — rejected (conflicts with known key)
- [ ] Entering `AWS_CONFIG_ENABLED` — rejected (conflicts with known key)
- [ ] Entering `MY_CUSTOM_VAR` — accepted
- [ ] Entering `MY_CUSTOM_VAR` again — rejected (duplicate)

### 7.3 SSH key validation

During `template create` with SSH auth:

- [ ] Invalid file path — rejected with error
- [ ] Non-existent file — rejected with error
- [ ] Valid SSH private key — accepted, fingerprint displayed

### 7.4 AWS profile map — standard format

During interactive setup or template create with AWS enabled:

- [ ] Adding a profile prompts for: sso_start_url, sso_region, sso_account_name, sso_account_id, sso_role_name, region
- [ ] All fields are required (empty values rejected)
- [ ] Can add multiple profiles
- [ ] Can finish with "done"

### 7.5 AWS profile map — JSON format

- [ ] Option to paste JSON directly is offered
- [ ] Valid JSON with correct structure is accepted
- [ ] Invalid JSON is rejected

---

## 8. Generated File Verification

After completing a full `setup-devcontainer` flow, verify all files:

### 8.1 `devcontainer-environment-variables.json`

```bash
python3 -c "import json; d=json.load(open('/tmp/qa-setup-test/devcontainer-environment-variables.json')); print(json.dumps(d, indent=2))"
```

- [ ] Valid JSON
- [ ] Contains `containerEnv` dict with all expected keys
- [ ] Contains `cli_version: "2.0.0"`
- [ ] Contains `template_name` and `template_path`
- [ ] If AWS enabled: contains `aws_profile_map`
- [ ] If SSH auth: contains `ssh_private_key`

### 8.2 `shell.env`

```bash
cat /tmp/qa-setup-test/shell.env
```

- [ ] Contains `export` statements for each environment variable
- [ ] Values match JSON configuration
- [ ] Has metadata header comment
- [ ] Variables are sorted alphabetically

### 8.3 `.devcontainer/devcontainer.json`

```bash
python3 -c "import json; json.load(open('/tmp/qa-setup-test/.devcontainer/devcontainer.json')); print('valid')"
```

- [ ] Valid JSON
- [ ] Contains `image`, `features`, `customizations` keys
- [ ] `postCreateCommand` references `shell.env`

### 8.4 `.devcontainer/catalog-entry.json`

```bash
cat /tmp/qa-setup-test/.devcontainer/catalog-entry.json
```

- [ ] Contains `name`, `description`, `tags`, `maintainer`
- [ ] `name` matches the collection used

### 8.5 `.devcontainer/VERSION`

```bash
cat /tmp/qa-setup-test/.devcontainer/VERSION
```

- [ ] Contains a version string

### 8.6 `.gitignore` entries

```bash
grep -E '(devcontainer-environment-variables|shell\.env|aws-profile-map|ssh-private-key)' /tmp/qa-setup-test/.gitignore
```

- [ ] `devcontainer-environment-variables.json` listed
- [ ] `shell.env` listed
- [ ] `.devcontainer/aws-profile-map.json` listed
- [ ] `.devcontainer/ssh-private-key` listed

---

## 9. Cleanup

After testing, clean up all test artifacts:

```bash
rm -rf /tmp/qa-test /tmp/qa-save-test /tmp/qa-load-test /tmp/qa-setup-test
rm -rf /tmp/qa-catalog-entry-test /tmp/qa-custom-catalog-test /tmp/qa-no-config
rm -rf /tmp/qa-empty /tmp/qa-constraint-validate
rm -rf ~/.devcontainer-templates/qa-*
```

---

## Test Summary

| Section | Command | Tests |
|---------|---------|-------|
| 1 | Global options | 4 |
| 2 | `catalog list` / `catalog validate` | 6 |
| 3 | `template create/save/load/list/delete/upgrade` | 14 |
| 4 | `setup-devcontainer` | 6 |
| 5 | `code` | 6 |
| 6 | Validation behavior | 5 |
| 7 | Edge cases | 5 |
| 8 | Generated file verification | 6 |
| **Total** | | **52** |
