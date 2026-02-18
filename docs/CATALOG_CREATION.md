# Creating a DevContainer Catalog Repository

This guide covers how to create, structure, validate, and distribute a custom devcontainer catalog repository for use with the Caylent Devcontainer CLI (`cdevcontainer`).

## What Is a Catalog?

A catalog is a Git repository that contains one or more devcontainer configurations (entries) along with shared assets. The CLI clones a catalog, discovers its entries, and copies the selected entry's files into a project's `.devcontainer/` directory.

### Example Catalogs

For working examples, see the Caylent DevOps Platform repositories:

- [Browse all Caylent DevOps Platform catalogs](https://github.com/search?q=topic%3Acaylent-devops-platform+org%3Acaylent-solutions&type=Repositories)
- This repository (`caylent-solutions/devcontainer`) serves as the **default catalog**

## Repository Structure

A catalog repository must follow this layout:

```
catalog-repo/
  common/
    devcontainer-assets/                   # Shared files copied into every project's .devcontainer/
      .devcontainer.postcreate.sh          # Main postcreate hook (required)
      devcontainer-functions.sh            # Shared shell functions (required)
      postcreate-wrapper.sh               # Postcreate wrapper script (required)
      project-setup.sh                     # Project-specific setup template (required)
      nix-family-os/                       # Host proxy toolkit for macOS/Linux (required subdir)
        README.md                          #   Documentation (required)
        tinyproxy.conf.template            #   Proxy config template (required)
        tinyproxy-daemon.sh                #   Daemon management script (required)
      wsl-family-os/                       # Host proxy toolkit for Windows/WSL (required subdir)
        README.md                          #   Documentation (required)
        tinyproxy.conf.template            #   Proxy config template (required)
        tinyproxy-daemon.sh                #   Daemon management script (required)
    root-project-assets/                   # Files copied into the project root (optional)
      CLAUDE.md                            #   AI coding standards (example)
      .claude/                             #   Claude Code configuration (example)
  catalog/
    <entry-name>/                          # One directory per entry
      catalog-entry.json                   #   Entry metadata (required)
      devcontainer.json                    #   DevContainer configuration (required)
      VERSION                              #   Semver version string (required)
      <additional files>                   #   Any other files needed by this entry
```

## Step-by-Step: Creating a New Catalog

### 1. Initialize the Repository

```bash
mkdir my-devcontainer-catalog
cd my-devcontainer-catalog
git init
```

### 2. Create the Common Assets Directory

Common assets are **automatically copied into every project's `.devcontainer/`** regardless of which entry is selected. This is how shared scripts and proxy toolkits are distributed.

```bash
mkdir -p common/devcontainer-assets
mkdir -p common/devcontainer-assets/nix-family-os
mkdir -p common/devcontainer-assets/wsl-family-os
```

#### Required Common Asset Files

You must provide these four files in `common/devcontainer-assets/`:

| File | Purpose |
|------|---------|
| `.devcontainer.postcreate.sh` | Main postcreate hook — runs after the container is created |
| `devcontainer-functions.sh` | Shared shell functions used by postcreate and project-setup |
| `postcreate-wrapper.sh` | Wrapper that orchestrates the postcreate lifecycle |
| `project-setup.sh` | Template for project-specific setup commands |

All four must have the **executable bit set**:

```bash
chmod +x common/devcontainer-assets/.devcontainer.postcreate.sh
chmod +x common/devcontainer-assets/devcontainer-functions.sh
chmod +x common/devcontainer-assets/postcreate-wrapper.sh
chmod +x common/devcontainer-assets/project-setup.sh
```

#### Required Subdirectories

Each subdirectory (`nix-family-os/`, `wsl-family-os/`) must contain:

| File | Purpose |
|------|---------|
| `README.md` | Documentation for the proxy toolkit |
| `tinyproxy.conf.template` | Proxy configuration template with environment variable placeholders |
| `tinyproxy-daemon.sh` | Daemon management script (must be executable) |

```bash
chmod +x common/devcontainer-assets/nix-family-os/tinyproxy-daemon.sh
chmod +x common/devcontainer-assets/wsl-family-os/tinyproxy-daemon.sh
```

> **Tip**: Copy these files from the [default catalog](https://github.com/caylent-solutions/devcontainer/tree/main/common/devcontainer-assets) as a starting point, then customize as needed.

### 3. Create Root Project Assets (Optional)

Files in `common/root-project-assets/` are copied into the **project root** (not `.devcontainer/`) when an entry is installed. This is useful for distributing standardized root-level files.

```bash
mkdir -p common/root-project-assets
```

Common uses:
- `CLAUDE.md` — AI coding standards
- `.claude/` — Claude Code configuration directory
- Any other root-level files your organization needs in every project

All `.json` files in this directory must be valid JSON (the validator checks this).

### 4. Create Your First Catalog Entry

Each entry lives in its own directory under `catalog/`:

```bash
mkdir -p catalog/my-entry
```

#### catalog-entry.json

This file defines the entry's metadata:

```json
{
  "name": "my-entry",
  "description": "A devcontainer configuration for my team's projects",
  "tags": ["python", "aws"],
  "maintainer": "team@example.com",
  "min_cli_version": "2.0.0"
}
```

**Field reference:**

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Entry name — must match the directory name. Lowercase, dash-separated, min 2 chars. Pattern: `^[a-z][a-z0-9-]*[a-z0-9]$` |
| `description` | Yes | Human-readable description shown in `catalog list` |
| `tags` | No | Array of lowercase, dash-separated tags for filtering (`catalog list --tags`) |
| `maintainer` | No | Contact information for the entry maintainer |
| `min_cli_version` | No | Minimum CLI version required to use this entry (semver X.Y.Z). Entries with a higher min version than the user's CLI are skipped. |

**No additional fields are allowed** — the validator rejects unknown fields.

#### devcontainer.json

Your standard VS Code devcontainer configuration. Requirements:

1. Must have a `name` field (non-empty string)
2. Must have at least one container source: `image`, `build`, `dockerFile`, or `dockerComposeFile`
3. `postCreateCommand` must reference `.devcontainer/.devcontainer.postcreate.sh` or `.devcontainer/postcreate-wrapper.sh`

Example:

```json
{
  "name": "My Entry DevContainer",
  "image": "mcr.microsoft.com/devcontainers/base:noble",
  "postCreateCommand": "bash .devcontainer/postcreate-wrapper.sh 2>&1 | tee /tmp/postcreate.log",
  "customizations": {
    "vscode": {
      "extensions": [
        "anthropic.claude-code",
        "amazonwebservices.aws-toolkit-vscode"
      ],
      "settings": {
        "github.copilot.enable": { "*": false },
        "chat.extensionUnification.enabled": false
      }
    }
  }
}
```

#### VERSION

A file containing a single semver string (X.Y.Z):

```
2.0.0
```

### 5. Naming the Default Entry

If your catalog has an entry named `default`, it will be auto-selected when:
- The user sets `DEVCONTAINER_CATALOG_URL` and chooses "Default Caylent General DevContainer" from the source selection prompt
- The catalog has exactly one entry (auto-selected regardless of name)

For catalogs with multiple entries, the CLI presents a browsable selection list.

### 6. File Conflict Rules

Entry directories must **not** contain files with the same name as files in `common/devcontainer-assets/`. During installation, common assets are copied after entry files — common assets take precedence on name collisions.

The validator detects conflicts between:
- Entry files and common asset files (top-level)
- Entry files and common asset subdirectories

If your entry needs a file that has the same name as a common asset, rename the entry's file to avoid the collision.

## Validating Your Catalog

### Local Validation

Run the CLI's validation command against your local catalog:

```bash
cdevcontainer catalog validate --local /path/to/your/catalog
```

This performs comprehensive checks:

| Area | Check |
|------|-------|
| Common assets | All four required files present |
| Common assets | `nix-family-os/` and `wsl-family-os/` subdirectories with required files |
| Common assets | Shell scripts have executable permission |
| Common assets | All `.json` files in `root-project-assets/` are valid JSON |
| Per-entry | Required files present (`catalog-entry.json`, `devcontainer.json`, `VERSION`) |
| Per-entry | `VERSION` contains valid semver (X.Y.Z) |
| Per-entry | `devcontainer.json` has `name` field and a container source |
| Per-entry | `postCreateCommand` references postcreate scripts |
| Per-entry | Directory name matches `catalog-entry.json` `name` field |
| Per-entry | `catalog-entry.json` has valid name pattern, description, and no unknown fields |
| Per-entry | No file conflicts with common assets |
| Cross-entry | No duplicate entry names |

### Remote Validation

After pushing, validate the remote catalog:

```bash
# Using the default catalog URL
cdevcontainer catalog validate

# Using a custom URL
cdevcontainer catalog validate --catalog-url "https://github.com/your-org/your-catalog.git@main"
```

## Tagging and Releases

The CLI relies on semver tags for deterministic, reproducible behavior.

### How Tag Resolution Works

When `DEVCONTAINER_CATALOG_URL` is **not set**, the CLI:
1. Runs `git ls-remote --tags` against the default catalog
2. Finds all tags matching semver format (X.Y.Z)
3. Filters for tags >= `2.0.0`
4. Selects the highest version
5. Clones that specific tag

When `DEVCONTAINER_CATALOG_URL` **is set**:
- With `@tag` suffix (e.g., `https://github.com/org/catalog.git@1.2.0`): clones that specific tag/branch
- Without suffix: clones the default branch

### Tagging Best Practices

```bash
# Create an annotated tag
git tag -a 2.0.0 -m "Release 2.0.0"
git push origin 2.0.0
```

- Tag every release with a semver version (MAJOR.MINOR.PATCH)
- Use annotated tags for provenance (`git tag -a`, not lightweight tags)
- Do not rely on the default branch for production use
- Increment the version when changing common assets, entry files, or adding entries

## Distribution

### Setting Up for Users

Users consume your catalog by setting the `DEVCONTAINER_CATALOG_URL` environment variable:

```bash
# Pin to a specific tag (recommended)
export DEVCONTAINER_CATALOG_URL="https://github.com/your-org/your-catalog.git@2.0.0"

# Use the default branch (not recommended for production)
export DEVCONTAINER_CATALOG_URL="https://github.com/your-org/your-catalog.git"
```

Then users run:

```bash
cdevcontainer setup-devcontainer /path/to/project
```

### Direct Entry Selection

Users can skip the interactive selection by specifying an entry name:

```bash
export DEVCONTAINER_CATALOG_URL="https://github.com/your-org/your-catalog.git@2.0.0"
cdevcontainer setup-devcontainer --catalog-entry java-backend /path/to/project
```

### Catalog URL Override

The `--catalog-url` flag bypasses both tag resolution and the `DEVCONTAINER_CATALOG_URL` environment variable. This is useful for testing branches:

```bash
cdevcontainer setup-devcontainer --catalog-url "https://github.com/your-org/your-catalog.git@feature/new-entry" /path/to/project
```

## Browsing Catalog Entries

Users can list available entries without setting up a project:

```bash
# List all entries
cdevcontainer catalog list

# Filter by tags (ANY match)
cdevcontainer catalog list --tags python,aws

# List from a specific catalog
cdevcontainer catalog list --catalog-url "https://github.com/your-org/your-catalog.git@2.0.0"
```

## The 3-Layer Customization Model

The devcontainer system uses three layers of customization:

1. **Catalog entries** — The base devcontainer configuration (devcontainer.json, scripts, extensions). Maintained by the catalog owner. Provides the foundation.

2. **Developer templates** — Per-developer settings (Git credentials, AWS profiles, proxy configuration). Created via `cdevcontainer template create` or during interactive setup. Stored in `~/.devcontainer-templates/`.

3. **Project setup** — Project-specific initialization (installing dependencies, running build tools). Defined in `.devcontainer/project-setup.sh`. Maintained by the project team.

This separation ensures:
- Catalog updates don't break developer settings
- Developer settings are portable across projects
- Project teams can customize without modifying the catalog

## Adding Entries to an Existing Catalog

1. Create a new directory under `catalog/`:
   ```bash
   mkdir catalog/new-entry
   ```

2. Add the required files:
   - `catalog-entry.json` (name must match directory name)
   - `devcontainer.json`
   - `VERSION`

3. Validate locally:
   ```bash
   cdevcontainer catalog validate --local .
   ```

4. Tag and release:
   ```bash
   git add catalog/new-entry/
   git commit -m "feat: add new-entry devcontainer configuration"
   git tag -a 2.1.0 -m "Release 2.1.0"
   git push origin main 2.1.0
   ```

## Troubleshooting

### "No catalog tags >= 2.0.0 found"

The CLI could not find any semver tags in the catalog repository. Ensure you have pushed at least one tag >= `2.0.0`:

```bash
git tag -a 2.0.0 -m "Initial release"
git push origin 2.0.0
```

### "Entry 'name' not found"

The `--catalog-entry` name does not match any entry in the catalog. List available entries:

```bash
cdevcontainer catalog list
```

### Validation errors on common assets

Ensure all required files exist and shell scripts have the executable bit set:

```bash
chmod +x common/devcontainer-assets/*.sh
chmod +x common/devcontainer-assets/nix-family-os/tinyproxy-daemon.sh
chmod +x common/devcontainer-assets/wsl-family-os/tinyproxy-daemon.sh
```

### File conflict errors

An entry contains a file with the same name as a common asset. Rename the conflicting file in the entry directory — common assets always take precedence during copy.

### "DEVCONTAINER_CATALOG_URL is not set"

The `--catalog-entry` flag requires `DEVCONTAINER_CATALOG_URL` to be set:

```bash
export DEVCONTAINER_CATALOG_URL="https://github.com/your-org/your-catalog.git@2.0.0"
```

### Git authentication failures

For HTTPS repos, verify a valid token or credential helper is configured. For SSH repos, verify your SSH key is loaded and the host is in `known_hosts`. Test access:

```bash
git ls-remote https://github.com/your-org/your-catalog.git
```
