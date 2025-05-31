# CHANGELOG


## Unreleased

### Breaking

* build!: fix semantic-release GH_TOKEN usage and remove invalid changelog flag to restore release automation (#25) ([`6b615f5`](https://github.com/caylent-solutions/devcontainer/commit/6b615f543ee85dd77ab7dd65f00eb865a5bd1b73))

* build!: replace semantic_release auto-push with safe version calculation to comply with branch protections (#24) ([`d18e90f`](https://github.com/caylent-solutions/devcontainer/commit/d18e90f5f0f357b6ebd1ca0fd030c8b71a802630))

### Ci

* ci: use GitHub App for semantic-release (#14) ([`1a4a481`](https://github.com/caylent-solutions/devcontainer/commit/1a4a48143b9298af303054201040c111e2363a86))

### Fix

* fix: create-release (#20) ([`f355bd7`](https://github.com/caylent-solutions/devcontainer/commit/f355bd7affa0876c2c2801b21de63465aa97bafe))

* fix: release github action (#13) ([`b6b0771`](https://github.com/caylent-solutions/devcontainer/commit/b6b0771cce323591f69d74acd47a572251755a45))

* fix: create release github action and created changelog.md (#10) ([`1026ecb`](https://github.com/caylent-solutions/devcontainer/commit/1026ecb2e21a709633d08ec75243e28c058c7600))

* fix: Resolve version conflict between setup.py and pyproject.toml and make configure (#8)

* fix: Resolve version conflict between setup.py and pyproject.toml

* fix: ensure merge pipeline and `make configure` work on subsequent runs ([`0eb1d4b`](https://github.com/caylent-solutions/devcontainer/commit/0eb1d4ba35e5425fe1a1b3f6dd9d669882937d2a))

### Test

* test: resolution to create-release with bot (#18) ([`694e1ee`](https://github.com/caylent-solutions/devcontainer/commit/694e1ee9586607e74f1a21c9963210e5ce594f7f))

### Unknown

* fix (#23)

* fix ([`249af89`](https://github.com/caylent-solutions/devcontainer/commit/249af8928741fd3fe7c0b89245bc01d6526141c2))

* Fix 2 (#22)

* fix: create-release

* BREAKING CHANGE: debugging create-release github action

* BREAKING CHANGE fix ([`bbbd9cd`](https://github.com/caylent-solutions/devcontainer/commit/bbbd9cdb3ccb6d827df9826ef881d9bf5a71f756))

* Fix (#21)

* fix: create-release

* BREAKING CHANGE: debugging create-release github action ([`980f007`](https://github.com/caylent-solutions/devcontainer/commit/980f007385bcd5d83d5af701c16143ca2951da9d))

* Test create release (#19)

* test: resolution to create-release with bot

* fix: gen token ([`261b43e`](https://github.com/caylent-solutions/devcontainer/commit/261b43e5c4412b9389ecced1cfd0a375146ac461))

* Fix error (#17)

* fix error

* fix: found and fixed issue with create-release ([`4bd5cb9`](https://github.com/caylent-solutions/devcontainer/commit/4bd5cb9be4cbc14068ca025b31e8ca60d503fa01))

* fix error (#16) ([`7440704`](https://github.com/caylent-solutions/devcontainer/commit/74407044d865d442277f2b4ca9f56670aa6f2e1e))

* remove redundant scan (#15) ([`335d46d`](https://github.com/caylent-solutions/devcontainer/commit/335d46d8a59ee208e42e168f4c8df850747ef3b9))

* Fix publish and twine (#12)

* fix: publish github action

* fix: typo

* fix: twine

* fix: add twine to devcontainer

* fix: update to actions

* fix: removed pip install twine

* fix: twine

* fix: email address ([`aa8e3e6`](https://github.com/caylent-solutions/devcontainer/commit/aa8e3e6d26f4ea5c68e0350cebc08b71e939574d))

* Fix publish (#11)

* fix: publish github action

* fix: typo ([`b075399`](https://github.com/caylent-solutions/devcontainer/commit/b0753997ed42bf12820121f2c883308c20d5acc8))

* Update code ql to v3 and fix setuptools vulnerability (#9)

* fix: Resolve version conflict between setup.py and pyproject.toml

* fix: ensure merge pipeline and `make configure` work on subsequent runs

* fix: Update semantic-release command for version 8.0.0

* fix: Update setuptools to &gt;=78.1.1 to fix path traversal vulnerability (CVE-2025-47273) ([`594a283`](https://github.com/caylent-solutions/devcontainer/commit/594a283d7750fdf22569afbbc4a0aa6d64f4d782))

* Implement CI/CD workflows, restructure project, and add setup/template CLI features (#7)

* feat: Add setup-devcontainer command with interactive template management

This commit adds a new `setup-devcontainer` command to the Caylent Devcontainer CLI,
enabling users to set up a devcontainer in their projects with either interactive
or manual configuration. The implementation includes:

- New setup command with interactive and manual modes
- Template management system for saving and reusing configurations
- Comprehensive unit and functional tests with 92% code coverage
- GitHub Actions workflows for PR validation and PyPI publishing
- Improved documentation with detailed usage examples

Key features:
- Interactive setup process with template selection
- AWS profile configuration support
- Template save/load functionality for consistent environments
- Functional tests that verify CLI behavior from a user perspective
- Manual testing guide for pre-release verification

Documentation updates:
- Added CONTRIBUTING.md with development guidelines
- Added MANUAL_TESTING.md for pre-release verification
- Updated README.md with command examples and usage instructions
- Added tests/README.md with testing guidelines

CI/CD improvements:
- Added PR validation workflow with linting and testing
- Added PyPI publishing workflow for tagged releases
- Standardized on Ubuntu 24.04 for all GitHub Actions
- Configured ASDF for consistent Python version management

This implementation satisfies the requirement to provide a simple way for users
to set up devcontainers in their projects while maintaining consistent
environments across teams.

* fixed readme

* fixed readme and gitignore

* fixed README and .gitignore files

* chore: Add CODEOWNERS file and update .gitignore to exclude coverage files

* fix: Update license from MIT to Apache 2.0

* docs: Clarify DEFAULT_PYTHON_VERSION as fallback when .tool-versions is not present

* feat: Add VERSION file and update option to setup-devcontainer command

* docs: Add instructions for committing devcontainer files

* feat: Add git hooks and pre-commit configuration

* fix: Add newline to VERSION file content

* fix: Add newlines to JSON files

* fix: Update multiline input instruction to only show &#39;Esc then Enter&#39;

* fix: Standardize on containerEnv format for environment variables

* fix: Standardize on containerEnv format for templates and add .gitignore

* added new line to the end of the file example-container-env-values.json

* fix: Improve AWS profile map input format and fix port conflicts

* feat: add template versioning and upgrade functionality

- Add template versioning to track CLI version that created templates
- Add version compatibility checking when loading templates
- Add template upgrade command to update templates to current CLI version
- Add template delete command to remove saved templates
- Add version mismatch handling with multiple options for users
- Update README with documentation for new features
- Fix unit tests and linting issues

* got unit test coverage to  88%

* unit test coverage to 90%

* linting issues fixed

* consolidated cruft test files into single files; lost some test as coverage is at 87% for now

* added blank line to end of files where missing

* changed pre-push local git hook required unit test coverage to 85%

* changed pr github action unit coverage requirement to 85%

* Move GitHub Actions workflows to repository root for proper triggering

* Fix merge simulation to properly use base branch

* Add system dependencies for Python build in GitHub Actions workflows

* Fix version handling in setup.py to ensure PEP 440 compliance

* Add Python build module to requirements and workflow

* Remove redundant build module installation step

* Add asdf reshim to Makefile install target

* Fix coverage threshold check to use coverage json command

* remove upload of coverage report as the action already publishes a summary in the stage output

* Updated Readme Contributing section with make task

* updated pre-commit hook to validate json files when commit made outside of the cli dir

* Fix end of file issues and pre-commit hook

* Add CodeQL analysis workflow

* Add main branch validation workflow

* BREAKING CHANGE: Complete CI/CD pipeline with semantic versioning and Slack notifications

This commit includes several major improvements:
1. Replace email notifications with Slack notifications for better team communication
2. Add semantic versioning based on commit messages
3. Add manual QA approval workflow with deployment environments
4. Fix code formatting and import sorting issues
5. Improve GitHub Actions workflows with proper error handling
6. Add CodeQL security scanning

This represents a stable 1.0.0 release with a complete CI/CD pipeline.

* feat: Add Slack notification for PR review requests with code owner detection

* fix: update slack messages with at here mention and find code owners ([`a618438`](https://github.com/caylent-solutions/devcontainer/commit/a6184389226c55cd80f8356e0007883630eadef8))



## v0.1.0 (2025-05-28)

### Unknown

* moved docs (#6) ([`8d2f7e6`](https://github.com/caylent-solutions/devcontainer/commit/8d2f7e689d93dbbb53f8278142e288d05e0d4668))

* Fix gitignore (#5)

* ignore *.egg-info ([`d574e99`](https://github.com/caylent-solutions/devcontainer/commit/d574e99a28d2a28379d852faa86002c7eeaaec40))

* ignore caylent-devcontainer-cli/src/caylent_devcontainer_cli.egg-info ([`1a512d7`](https://github.com/caylent-solutions/devcontainer/commit/1a512d73b61a55d1c33143d8c5f583815290da82))

* Implement cdevcontainer CLI tool and improve project structure (#3)

* Added notes to README about support for AMAZONQ even if the project does not depend AWS.
Added an ENV VAR to the devcontainer.json so that other development project build task that may automate the install of tools via ASDF can be aware it is running in a devcontainer and already had this completed so the task can skip asdf automation.

* Wrapped all env config logic into a CLI tool for better usability and maintainability.
Setup support for concurrent devcontainers to support 1 to many clients and 1 to mant project.
Setup a means to reuse project templates for devcontainers.
Added an environment variable to the devcontainer to enable other utilities that may be deployed on the container to determine its running in a devcontainer or not.

* Moved supporting docs out of repo root

* fixed amazonq

* Added info to README about when and how to rebuild the devcontainer

* fixed linting and some nit test

* fix unit test and linting

* got unit test coverage up to 91%

* fix install of asdf tools and remove launch-cli

* fix linting

* removed 502 ignore in flake

* updated isort dep ([`4a59964`](https://github.com/caylent-solutions/devcontainer/commit/4a59964e4be44e0fe09f42e068d2c474a6e268b5))

* Made AWS configuration optional (#2)

* Make configuration of AWS account access optional

* python is required when setting up devcontainer; added instructions to set it up to the README.md ([`e75e62e`](https://github.com/caylent-solutions/devcontainer/commit/e75e62e4605b24a5a09b2d52b87dd9e963faada5))

* Introduce Standardized Caylent Devcontainer for Consistent Local Development

# Refactor: Introduce Standardized Caylent Devcontainer for Consistent Local Development

## 🧰 Summary

This PR introduces a fully restructured and production-ready VS Code Devcontainer environment that enables consistent, secure, and developer-friendly local development across Caylent engineering teams.

---

## ✅ What&#39;s Included

- ✅ `devcontainer.json` rewritten for:
  - AWS SSO profile injection via `aws-profile-map.json`
  - Shell environment injection using `containerEnv` and host shell values
  - Robust set of essential development tools via Devcontainer Features (aws-cli, python, docker, etc.)
  - Amazon Q + GitHub Copilot + common extensions auto-installed
- ✅ `.devcontainer.postcreate.sh`
  - Configures AWS CLI profiles dynamically from JSON
  - Bootstraps Python with `asdf` (default version or from `.tool-versions`)
  - Injects developer Git credentials and shell aliases
  - Installs CLI tools and custom packages (`EXTRA_APT_PACKAGES`)
  - Full support for nested Docker &amp; Docker Swarm
- ✅ `.devcontainer/devcontainer-functions.sh` added with DRY logging/utilities
- ✅ `.devcontainer/example-container-env-values.json` (template for user env)
- ✅ `.devcontainer/example-aws-profile-map.json` (SSO profile mapping)
- ✅ `generate-shell-exports.py`
  - Generates `shell.env` from JSON
  - Supports both `.env` -&gt; JSON and JSON -&gt; shell export conversion
  - CLI with help, validation, and shell profile persistence

---

## 💡 Key Features

| Feature                          | Details                                                              |
|----------------------------------|----------------------------------------------------------------------|
| ✅ Cross-platform                | Works on macOS, WSL2/Windows with VS Code Devcontainers              |
| ✅ AWS SSO setup                 | Fully injected via JSON; supports multiple profiles &amp; default alias |
| ✅ GitHub Copilot + Amazon Q     | Preinstalled and ready to auth post-launch                          |
| ✅ asdf versioning               | Python installed via `.tool-versions` or fallback version           |
| ✅ Docker-in-Docker              | Supports nested containers and Docker Swarm inside the container    |
| ✅ Shell configuration           | Adds Git aliases, developer env vars, and shell PATH injections     |

---

## 🧪 How to Use

1. Copy `.devcontainer` into your app repo  
2. Copy and configure:
   ```bash
   cp .devcontainer/example-container-env-values.json devcontainer-environment-variables.json
   cp .devcontainer/example-aws-profile-map.json .devcontainer/aws-profile-map.json
   ```
3. Generate the shell config:
   ```bash
   .devcontainer/generate-shell-exports.py export devcontainer-environment-variables.json &gt; shell.env
   source shell.env
   ```
4. Open in VS Code → Reopen in container when prompted

---

## 🧼 Notes

- Does not commit any sensitive information
- Safe to use as a base for other teams with minimal customization
- `.tool-versions` is encouraged to enforce consistent tooling across teams

---

## 🧱 Future Improvements

- Optional support for GitHub Actions or pre-commit hooks
- Container image publishing (e.g. GHCR)
- JetBrains Gateway compatibility improvements ([`26eeca6`](https://github.com/caylent-solutions/devcontainer/commit/26eeca6781278dc7c728b3132de15edc92fcd439))

* Merge remote-tracking branch &#39;origin/main&#39; into first-commit ([`af7a8d5`](https://github.com/caylent-solutions/devcontainer/commit/af7a8d5b09b70ca382ecd33efb4caf59a623781a))

* Initial commit ([`4c9dc86`](https://github.com/caylent-solutions/devcontainer/commit/4c9dc86a80853a51d68d5c9e406fcd350773e3bb))

* Create .gitignore ([`adb24cd`](https://github.com/caylent-solutions/devcontainer/commit/adb24cdf49e826fc89fa44d4d32497404783e065))

* Initial commit ([`48146ef`](https://github.com/caylent-solutions/devcontainer/commit/48146efbd191f41e7effc7887e4c9c69b080af83))
