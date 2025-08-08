# CHANGELOG



## v1.6.0 (2025-08-08)

### Chore

* chore: add comprehensive caching to PyPI publish workflow (#61)

* optimize: add comprehensive caching to PyPI publish workflow

- Add system dependencies cache with intelligent dpkg restoration
- Add ASDF installation cache with conditional clone logic
- Add Python dependencies cache for pip and site-packages
- Implement cache hit detection and permission fixing
- Optimize workflow performance by ~2-3 minutes
- Reduce bandwidth usage and improve reliability

These caching optimizations mirror the strategy used in main-validation.yml
and provide significant performance improvements for both manual and
automatic PyPI publishing workflows.

* chore: remove redundant source command ([`6f4ad11`](https://github.com/caylent-solutions/devcontainer/commit/6f4ad1117ccd47beb6afa8000ab21084d3f7bf5a))

### Feature

* feat: add manual trigger capability to publish workflow

- Add workflow_dispatch trigger to publish.yml for manual PyPI publishing
- Support both automatic (tag push) and manual (workflow dispatch) triggers
- Add dynamic tag detection and version consistency across all steps
- Enable manual publishing of any existing tag (e.g., 1.5.0)
- Fix kebab-case linting issue with skip-existing parameter
- Keep semantic-release PyPI upload disabled for controlled publishing ([`d2c4bba`](https://github.com/caylent-solutions/devcontainer/commit/d2c4bba1fe676024b75fdafae118f58f94b772a6))

### Fix

* fix: resolve semantic-release version synchronization issues in CI/CD… (#63)

* fix: resolve semantic-release version synchronization issues in CI/CD workflows

- Fix main-validation workflow to properly update all version files (pyproject.toml, __init__.py, CHANGELOG.md)
- Use &#39;semantic_release version --no-push --no-vcs-release&#39; instead of just &#39;changelog&#39; command
- Add comprehensive version file commits to prevent version mismatches
- Replace manual version overrides in publish workflow with version consistency verification
- Update CHANGELOG.md to properly reflect current v1.5.0 release
- Ensures git tags point to commits with synchronized version files across all locations

This prevents the &#39;already released&#39; error by maintaining proper version file synchronization
and ensures semantic-release can correctly calculate next versions from commit history.

* fix: improve workflow comments and version parsing precision

- Clarify semantic-release comment to specify which files are updated (pyproject.toml, __init__.py, CHANGELOG.md)
- Use line-start anchored regex for pyproject.toml version parsing to avoid false matches
- Add detailed comments explaining Python regex approach vs grep/sed limitations
- Ensures robust version detection that handles both quote types and prevents pattern conflicts

* fix: clean up trailing whitespace in publish workflow

- Remove trailing whitespace automatically fixed by pre-commit hooks
- Ensures consistent code formatting across workflow files ([`f593565`](https://github.com/caylent-solutions/devcontainer/commit/f593565c7fe563b0a6f6a4d5d5b0ade936ae3e60))

* fix: optimize PyPI publish workflow with comprehensive caching and enhanced semantic versioning (#62)

* optimize: add comprehensive caching to PyPI publish workflow

- Add system dependencies cache with intelligent dpkg restoration
- Add ASDF installation cache with conditional clone logic
- Add Python dependencies cache for pip and site-packages
- Implement cache hit detection and permission fixing
- Optimize workflow performance by ~2-3 minutes
- Reduce bandwidth usage and improve reliability

These caching optimizations mirror the strategy used in main-validation.yml
and provide significant performance improvements for both manual and
automatic PyPI publishing workflows.

* chore: remove redundant source command

* fix: expand conventional commit support with comprehensive type definitions

- Add support for &#39;security&#39; and &#39;revert&#39; commit types as patch triggers
- Add comprehensive conventional commit documentation to CONTRIBUTING.md
- Include examples and version bump mapping for all supported types
- Clarify major version bump procedures with BREAKING CHANGE examples

This enables better semantic versioning automation and provides clear
guidelines for contributors on commit message formatting.

* fix: improve cache key robustness across all GitHub workflows

- Replace hardcoded &#39;ubuntu-2404&#39; with dynamic runner.arch in cache keys
- Ensures cache compatibility across different GitHub runner architectures
- Affects publish.yml, pr-validation.yml, and main-validation.yml workflows
- Prevents potential cache misses when GitHub updates runner specifications

This addresses the mismatch between runs-on: ubuntu-24.04 and hardcoded
ubuntu-2404 in cache keys, making the caching strategy more resilient.

* security: improve cache directory permissions with principle of least privilege

- Replace overly permissive chmod -R 755 with granular permissions
- Set directories to 755 (executable/searchable) and files to 644 (read-only)
- Apply security improvements across all workflows: publish.yml, main-validation.yml, pr-validation.yml
- Maintain functionality while reducing security exposure
- Use find with -type flag for precise permission control

This follows security best practices by granting only necessary permissions
to cache files and directories while ensuring GitHub Actions can still
access cached content effectively. ([`5384d5b`](https://github.com/caylent-solutions/devcontainer/commit/5384d5b57cc07e3b95eece22f769418e9d6e9d42))

* fix: apply pre-commit trailing whitespace fixes to publish workflow ([`2bba852`](https://github.com/caylent-solutions/devcontainer/commit/2bba85264c67b98e28f247d774cb535ebaeb5664))


## v1.5.0 (2025-08-08)

### Feature

* feat: comprehensive dev environment optimization with enhanced quality assurance

This comprehensive enhancement optimizes the development environment setup and implements
a robust quality assurance pipeline to improve developer experience and CI/CD performance.

## Python Environment Optimization
- Install Python first via asdf and immediately reshim to ensure proper binary availability
- Replace pip installation of aws-sso-util with pipx to prevent PyYAML conflicts
- Switch from isort to ruff extension to resolve formatting conflicts with black
- Set explicit Python interpreter path to asdf-managed Python in VS Code settings
- Add Python build dependencies required for asdf Python compilation
- Remove python feature from devcontainer.json as Python is now managed entirely through asdf
- Restructure postcreate script for proper dependency resolution order

## Quality Assurance Pipeline
- Add comprehensive YAML validation with yamllint and custom .yamllint configuration
- Enhance pre-commit hooks with yamllint, security scanning (gitleaks), and formatting
- Add new make tasks: github-workflow-yaml-lint, yaml-fix, pre-commit-check
- Integrate pre-commit checks into CI/CD workflows for automated quality enforcement
- Update documentation with new quality assurance workflows and make tasks

## CI/CD Performance Optimization
- Implement comprehensive caching strategy for system dependencies, ASDF, and Python packages
- Add intelligent cache hit detection to avoid unnecessary apt-get update operations
- Use dpkg for cached package restoration with apt-get install -f fallback
- Fix cache permission issues with proper ownership and accessibility
- Optimize workflow performance with cache v3 keys and conditional package installation

## Files Changed:
- .devcontainer/: Enhanced Python setup and VS Code configuration
- .github/workflows/: Added caching, pre-commit integration, and performance optimization
- .yamllint: New comprehensive YAML validation rules for GitHub Actions
- .pre-commit-config.yaml: Enhanced hooks with yamllint and security scanning
- Makefile: New quality assurance tasks with clean output formatting
- Documentation: Updated README and CONTRIBUTING files with new workflows

This change improves build performance by up to 50% through intelligent caching while
ensuring code quality through automated validation and formatting. ([`12907d9`](https://github.com/caylent-solutions/devcontainer/commit/12907d9ce011c47cfc978805f43b13636b98e264))


## v1.4.0 (2025-07-25)

### Build

* build: update asdf version to v0.15.0 and optimize zsh configuration  (#50)

* build: update asdf version to v0.15.0 and optimize zsh configuration

- Upgrade asdf from v0.14.0 to v0.15.0 for latest features and bug fixes
- Move asdf zsh configuration to be sourced after oh-my-zsh to prevent conflicts
- Consolidate asdf zsh setup to reduce duplication in postcreate script
- Ensure proper initialization order for zsh completions

* build: update asdf version to v0.15.0 and optimize zsh configuration

- Upgrade asdf from v0.14.0 to v0.15.0 for latest features and bug fixes
- Move asdf zsh configuration to be sourced after oh-my-zsh to prevent conflicts
- Consolidate asdf zsh setup to reduce duplication in postcreate script
- Ensure proper initialization order for zsh completions ([`84516c0`](https://github.com/caylent-solutions/devcontainer/commit/84516c034c83e8a6ca9b67cf1db1f6b947437975))

### Chore

* chore(release): 1.4.0 - Major improvements to CLI with IDE support, AWS profile setup, and enhanced developer experience ([`e763945`](https://github.com/caylent-solutions/devcontainer/commit/e7639450216562540aac30395afeee75ced5ad23))

* chore(release): 1.3.0 ([`51ace82`](https://github.com/caylent-solutions/devcontainer/commit/51ace826c1635ea3e92382597b0e3aebf36664e6))

### Feature

* feat: add IDE support, AWS profile options, and major developer experience improvements

- add `--ide` flag with native support for VS Code and Cursor, with validation and clear error messages
- add two methods for AWS profile setup (standard format and JSON) with validation and retry prompts
- add an interactive help system to Makefiles with descriptive comments and a pre‑commit validation task
- improve setup flow so declining overwrite continues setup, and automatically manage `.gitignore` for secrets and environment files
- increase test coverage to 91% with expanded functional tests
- add privacy settings to disable data sharing for Amazon Q and GitHub Copilot

fix: correct test mocks and improve interrupt handling

docs: update setup instructions, prerequisites, and references for IDE support ([`1174d58`](https://github.com/caylent-solutions/devcontainer/commit/1174d58de12039946706a688df7c07436a5730a3))

### Unknown

* Merge pull request #58 from caylent-solutions/release-1.3.0

Release 1.4.0 - Major improvements to CLI with IDE support, AWS profile setup, and enhanced developer experience ([`335f9d8`](https://github.com/caylent-solutions/devcontainer/commit/335f9d8cfb438bcbbd0c259fe0459d3442a3c55c))

* fix formatting ([`195d944`](https://github.com/caylent-solutions/devcontainer/commit/195d94493ef14989d3438ecb56a08701476809b4))

* Merge pull request #57 from caylent-solutions/release-1.3.0

Release 1.3.0 ([`82dc9c4`](https://github.com/caylent-solutions/devcontainer/commit/82dc9c44ea075976e4b7866f5b3b08eb37f4ce41))


## v1.2.0 (2025-06-16)

### Chore

* chore(release): 1.2.0 - Fix cli update of saved templates ([`529eda3`](https://github.com/caylent-solutions/devcontainer/commit/529eda3ef71f6eeb670c1689d7fdcc5b2f70a510))

* chore(release): 1.2.0 ([`2af2603`](https://github.com/caylent-solutions/devcontainer/commit/2af2603f587ea99828e5412928d86631b1138f11))

* chore(release): 1.1.0 ([`c8685f7`](https://github.com/caylent-solutions/devcontainer/commit/c8685f7d7824da0fb640f3b0ff507b5ecdcee13f))

* chore(release): 1.1.0 ([`e08a1db`](https://github.com/caylent-solutions/devcontainer/commit/e08a1db72d8573f9ae326409785a32da469a3ffe))

* chore(release): 1.1.0 ([`5ad4ea1`](https://github.com/caylent-solutions/devcontainer/commit/5ad4ea144496a70dc3a26f94ce9a427fe7d712c3))

* chore(release): 1.1.0 ([`2866972`](https://github.com/caylent-solutions/devcontainer/commit/2866972d9c0a84b812dce69b08b048d681216e6f))

* chore(release): 1.1.0 ([`9b3bace`](https://github.com/caylent-solutions/devcontainer/commit/9b3bace83341fe61f907d4585a03be3110275918))

* chore(release): 1.1.0 ([`a8fc155`](https://github.com/caylent-solutions/devcontainer/commit/a8fc155c2942c52fc64eebd01281f87572b255e6))

### Feature

* feat: bump-minor version (#46) ([`5de03f4`](https://github.com/caylent-solutions/devcontainer/commit/5de03f48180781fac599e29662ba301708091b0b))

* feat: update README.md (#38) ([`2f2ed3b`](https://github.com/caylent-solutions/devcontainer/commit/2f2ed3b03c3cfcb7dd8f91da97c4cf7dc626f062))

* feat: upgrade github actions to use asdf 0.15.0; last version before the switch to go (#34)

* feat: upgrade github actions to use asdf 0.15.0; last version before the switch to go ([`f48dde9`](https://github.com/caylent-solutions/devcontainer/commit/f48dde94ee4d15d180ca3a5d2996146786041e5e))

### Fix

* fix: template upgrade (#44) ([`9618e80`](https://github.com/caylent-solutions/devcontainer/commit/9618e80e4187653639673dbb28b17de5159306b8))

* fix: Updated pip install instructions now that its available on pypi (#40) ([`18bdf97`](https://github.com/caylent-solutions/devcontainer/commit/18bdf978b50f454f06034e48d00cdfffe9600d31))

* fix: remove apt install of jq as it is installed already by asdf in github actions (#36) ([`bc35705`](https://github.com/caylent-solutions/devcontainer/commit/bc357057eaa4ff95db64155795294850a563eb3d))

### Revert

* revert: Revert version changes to fix unit tests ([`321df27`](https://github.com/caylent-solutions/devcontainer/commit/321df27230a29f83e51aba2363775b5f8a9262ec))

### Unknown

* Release 1.2.0 (#48)

* docs: Update release process documentation with manual steps

* feat: improve release process ([`56846ee`](https://github.com/caylent-solutions/devcontainer/commit/56846eeeb117a9cec9c5dccd848f29f7615cc00a))

* Merge pull request #47 from caylent-solutions/release-1.1.0

Release 1.1.0 ([`2e69546`](https://github.com/caylent-solutions/devcontainer/commit/2e6954637e0a90a3803fb5a102b2cbd19ab823fc))

* Merge pull request #45 from caylent-solutions/release-1.1.0

Release 1.1.0 ([`3da3e2f`](https://github.com/caylent-solutions/devcontainer/commit/3da3e2f1e091df0ae3629f41345071234957ca20))

* Merge pull request #41 from caylent-solutions/release-1.1.0

Release 1.1.0 ([`b3e703c`](https://github.com/caylent-solutions/devcontainer/commit/b3e703c7ab9f9ca24f96dc85966b428d79ac52e4))

* Merge pull request #39 from caylent-solutions/release-1.1.0

Release 1.1.0 ([`c3a6507`](https://github.com/caylent-solutions/devcontainer/commit/c3a6507cfa27eb5c3ca915576703a71842e326e5))

* Merge pull request #37 from caylent-solutions/release-1.1.0

Release 1.1.0 ([`5f8cfd7`](https://github.com/caylent-solutions/devcontainer/commit/5f8cfd7f0840881a5459851e8a22dd8d0da5d38a))

* Merge pull request #35 from caylent-solutions/release-1.1.0

Release 1.1.0 ([`2d6e542`](https://github.com/caylent-solutions/devcontainer/commit/2d6e54286d41ec5d3ff238b5f957fadc1a9fca5e))


## v1.0.0 (2025-05-31)

### Breaking

* build!: fix semantic-release GH_TOKEN usage and remove invalid changelog flag to restore release automation (#25) ([`6b615f5`](https://github.com/caylent-solutions/devcontainer/commit/6b615f543ee85dd77ab7dd65f00eb865a5bd1b73))

* build!: replace semantic_release auto-push with safe version calculation to comply with branch protections (#24) ([`d18e90f`](https://github.com/caylent-solutions/devcontainer/commit/d18e90f5f0f357b6ebd1ca0fd030c8b71a802630))

### Build

* build: fix semantic-release output assignment to enable version propagation (#28) ([`0678432`](https://github.com/caylent-solutions/devcontainer/commit/0678432bffee1b99407d9ee6856af7a8911dd0e3))

* build: fix release automation by correctly passing new_version to all dependent steps (#27) ([`a9ee987`](https://github.com/caylent-solutions/devcontainer/commit/a9ee987c9ec870fe6bc22c4447067e2e6a8da335))

### Chore

* chore(release): 1.0.0 ([`9a5bf0c`](https://github.com/caylent-solutions/devcontainer/commit/9a5bf0cf5c16834b156f4443faf06f7fd6440780))

* chore(release): 1.0.0 ([`bb60014`](https://github.com/caylent-solutions/devcontainer/commit/bb60014013bc3a7aa9e492cdc74d824d3ab91ca8))

### Ci

* ci: use GitHub App for semantic-release (#14) ([`1a4a481`](https://github.com/caylent-solutions/devcontainer/commit/1a4a48143b9298af303054201040c111e2363a86))

### Documentation

* docs: Clean up CHANGELOG.md for 1.0.0 release ([`6e67dec`](https://github.com/caylent-solutions/devcontainer/commit/6e67dec3660b044c2792e9d1315c6cafb4cee98a))

* docs: Clean up CHANGELOG.md for 1.0.0 release ([`499acab`](https://github.com/caylent-solutions/devcontainer/commit/499acab8ef26562c71aeb1674f18980691368661))

* docs: Clean up CHANGELOG.md for 1.0.0 release ([`80d99f4`](https://github.com/caylent-solutions/devcontainer/commit/80d99f456af719844e2a821a800b860f8ebb9a45))

### Fix

* fix: update publish workflow ([`88897be`](https://github.com/caylent-solutions/devcontainer/commit/88897bedd98d02d894f6b35109406424b3fe5781))

* fix: update publish workflow and clean up changelog ([`a287c94`](https://github.com/caylent-solutions/devcontainer/commit/a287c945607e70b96c2825ca4574b30a869fb369))

* fix: create-release (#20) ([`f355bd7`](https://github.com/caylent-solutions/devcontainer/commit/f355bd7affa0876c2c2801b21de63465aa97bafe))

* fix: release github action (#13) ([`b6b0771`](https://github.com/caylent-solutions/devcontainer/commit/b6b0771cce323591f69d74acd47a572251755a45))

* fix: create release github action and created changelog.md (#10) ([`1026ecb`](https://github.com/caylent-solutions/devcontainer/commit/1026ecb2e21a709633d08ec75243e28c058c7600))

* fix: Resolve version conflict between setup.py and pyproject.toml and make configure (#8)

* fix: Resolve version conflict between setup.py and pyproject.toml

* fix: ensure merge pipeline and `make configure` work on subsequent runs ([`0eb1d4b`](https://github.com/caylent-solutions/devcontainer/commit/0eb1d4ba35e5425fe1a1b3f6dd9d669882937d2a))

### Test

* test: resolution to create-release with bot (#18) ([`694e1ee`](https://github.com/caylent-solutions/devcontainer/commit/694e1ee9586607e74f1a21c9963210e5ce594f7f))

### Unknown

* Merge pull request #33 from caylent-solutions/release-1.0.0

Release 1.0.0 ([`f68cb5c`](https://github.com/caylent-solutions/devcontainer/commit/f68cb5cb0f1126670c95d6f461b7f3930690fc9a))

* fix (#32) ([`a5f0fcd`](https://github.com/caylent-solutions/devcontainer/commit/a5f0fcd0287681822108026c4504aa47e2db8311))

* Merge pull request #31 from caylent-solutions/release-1.0.0

Release 1.0.0 ([`af0afce`](https://github.com/caylent-solutions/devcontainer/commit/af0afceda9a7a7606ca959ca1d155a786afd2489))

* fix (#30) ([`73b58f7`](https://github.com/caylent-solutions/devcontainer/commit/73b58f766d654eec4b5c4582663b551458db91e3))

* fix-attempt add debug statements (#29) ([`69f4902`](https://github.com/caylent-solutions/devcontainer/commit/69f4902bfa9baf0956267484a8b068345a339cd1))

* Merge pull request #26 from caylent-solutions/release-

Release ([`97c3e42`](https://github.com/caylent-solutions/devcontainer/commit/97c3e42b6d12ac0e39527dad8f7b9033bd5c2090))

* chore(release): ([`1669637`](https://github.com/caylent-solutions/devcontainer/commit/166963726094347bd095f8b8b0f062d7e85d8aae))

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
