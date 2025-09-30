# CHANGELOG



## v1.8.0 (2025-09-30)

### Feature

* feat: remove workflow cancellation logic from release process (#85)

- Simplify release workflow by removing GitHub job cancellation code
- Reduces complexity and potential race conditions during PR creation/merge
- Allows natural workflow execution without interference ([`18b5511`](https://github.com/caylent-solutions/devcontainer/commit/18b5511a4d3889047467d412f51ebcf75f2ebcfa))


## v1.7.1 (2025-09-30)

### Chore

* chore(release): 1.7.1 ([`be3334a`](https://github.com/caylent-solutions/devcontainer/commit/be3334a981146bcdff11eba177194673e88f0569))

### Fix

* fix: fix wf (#83) ([`ca15a19`](https://github.com/caylent-solutions/devcontainer/commit/ca15a19ed5bb39a1ad44b06942d9da730f03e5d3))

### Unknown

* Merge pull request #84 from caylent-solutions/release-1.7.1

Release 1.7.1 ([`205cc74`](https://github.com/caylent-solutions/devcontainer/commit/205cc747dbbb4abbbe10c29e007dabb7192fc1da))

* Feat/trigger publish workflow (#82)

* feat: auto-trigger publish workflow from release process

- Add step to trigger publish.yml workflow after tag creation in main-validation.yml
- Remove push trigger on tags from publish.yml to prevent duplicate runs
- Publish workflow now only runs on manual dispatch or automated trigger

* fix: provide required tag input to publish workflow trigger

- Use -f flag to pass tag parameter to workflow_dispatch
- Fixes HTTP 422 error about missing required input

* refactor: eliminate duplicate version extraction in workflow

- Store version in step output to avoid duplication
- Use stored version in trigger step for consistency
- Improves maintainability and reduces potential inconsistencies ([`6c51176`](https://github.com/caylent-solutions/devcontainer/commit/6c5117612d7c72ab09be1de1a4f22c25b12941de))


## v1.7.0 (2025-09-30)

### Chore

* chore(release): 1.7.0 ([`92568bf`](https://github.com/caylent-solutions/devcontainer/commit/92568bf883e74c0adf819183b825f6ca68e6a239))

### Feature

* feat: auto-trigger publish workflow from release process (#80)

- Add step to trigger publish.yml workflow after tag creation in main-validation.yml
- Remove push trigger on tags from publish.yml to prevent duplicate runs
- Publish workflow now only runs on manual dispatch or automated trigger ([`9aaec70`](https://github.com/caylent-solutions/devcontainer/commit/9aaec708aaff16d8e1377df2396ed2572ecaed20))

### Unknown

* Merge pull request #81 from caylent-solutions/release-1.7.0

Release 1.7.0 ([`ae15da7`](https://github.com/caylent-solutions/devcontainer/commit/ae15da72938d3696d4146eaee6f79a70d521fc98))


## v1.6.5 (2025-09-30)

### Chore

* chore(release): 1.6.5 ([`c578f8b`](https://github.com/caylent-solutions/devcontainer/commit/c578f8bf0254cddc17a6b6ab391db58b624e12a1))

### Fix

* fix: workflow ([`0001826`](https://github.com/caylent-solutions/devcontainer/commit/0001826d011a363fd77b06a860b6a8f71949d9e5))

### Unknown

* Merge pull request #79 from caylent-solutions/release-1.6.5

Release 1.6.5 ([`3663c45`](https://github.com/caylent-solutions/devcontainer/commit/3663c452e569f2f8019dc979455f6f978bc2338e))

* Merge pull request #78 from caylent-solutions/fix-workflow

fix: workflow ([`85113e6`](https://github.com/caylent-solutions/devcontainer/commit/85113e6fc15f51c58520910d1e667afe96b8953c))


## v1.6.4 (2025-09-30)

### Chore

* chore(release): 1.6.4 ([`1cf1770`](https://github.com/caylent-solutions/devcontainer/commit/1cf17701c0ff08cd457a2a58e95452cec4ea32bc))

### Fix

* fix: Cancel workflows triggered by intermediate PR operations

- Add event-driven workflow cancellation after PR creation and merge
- Use 30-second timeout instead of fixed sleep delays
- Prevent unwanted workflow runs from PR operations
- Only allow tag push to trigger publish workflow
- Resolves issue where GitHub App token prevents publish workflow triggering ([`5b8fca8`](https://github.com/caylent-solutions/devcontainer/commit/5b8fca8ecada735deeac4a359819883c84e22493))

### Unknown

* Merge pull request #77 from caylent-solutions/release-1.6.4

Release 1.6.4 ([`4ee289a`](https://github.com/caylent-solutions/devcontainer/commit/4ee289a235c24c6741ed1ac111852a56d32388bd))

* Merge pull request #76 from caylent-solutions/fix/cancel-intermediate-workflows

fix: Cancel workflows triggered by intermediate PR operations ([`7a48c05`](https://github.com/caylent-solutions/devcontainer/commit/7a48c0510414dc049a20be7f5d8b67473f02c38f))


## v1.6.3 (2025-09-30)

### Chore

* chore(release): 1.6.3 ([`c9f320e`](https://github.com/caylent-solutions/devcontainer/commit/c9f320eb6726fc9330b60d219cfa6c70262aeb7c))

### Fix

* fix: sync ver ([`9800e8a`](https://github.com/caylent-solutions/devcontainer/commit/9800e8a175c1066e4051164fbb55eb68dabc5a39))

* fix: whitespace ([`54e841c`](https://github.com/caylent-solutions/devcontainer/commit/54e841c9976aad824d0f981d4a585838d0aa8f03))

* fix: Ensure __init__.py version stays in sync with pyproject.toml during releases

- Add manual update of __init__.py after semantic-release
- Include __init__.py in whitespace cleanup
- Stage __init__.py file for commit with other version files
- Resolves version mismatch issues that prevent PyPI publishing ([`8499676`](https://github.com/caylent-solutions/devcontainer/commit/8499676975087e84e350cfa802223124ad4e5447))

* fix: Sync __init__.py version to match pyproject.toml (1.6.2) ([`c5ce5f8`](https://github.com/caylent-solutions/devcontainer/commit/c5ce5f8ba7dbd62b37cca30ee38acd1250adfd7b))

### Unknown

* Merge pull request #75 from caylent-solutions/release-1.6.3

Release 1.6.3 ([`1e3bd51`](https://github.com/caylent-solutions/devcontainer/commit/1e3bd51f511f33451b99decf1ab6bc327001d5d1))

* Merge pull request #74 from caylent-solutions/fix/semantic-release-init-version-sync

Fix create release GitHub action and fix: make CLI version dynamic to match package metadata  - Replace hardcoded version in __init__.py with dynamic version reading - Version now automatically syncs with pyproject.toml - Fixes issue where CLI showed 1.0.0 instead of actual package version&#34; ([`7f0915e`](https://github.com/caylent-solutions/devcontainer/commit/7f0915e4b0b37cf73c431526e1a800b5b956d3df))

* fix: ([`086dc83`](https://github.com/caylent-solutions/devcontainer/commit/086dc835df0eb3a7e6442974b53652742aded52a))


## v1.6.2 (2025-09-30)

### Chore

* chore(release): 1.6.2 ([`01c3c57`](https://github.com/caylent-solutions/devcontainer/commit/01c3c57050d09af6c02975d394f1e19d19a9a4b3))

### Fix

* fix: lint ([`934171e`](https://github.com/caylent-solutions/devcontainer/commit/934171ee63041da4883da9bd49d2d764d981bce7))

* fix: lint ([`5cb80a6`](https://github.com/caylent-solutions/devcontainer/commit/5cb80a6e0f41b7aef7fc18c7ba33f3657b620579))

* fix: format ([`7aedde7`](https://github.com/caylent-solutions/devcontainer/commit/7aedde741866bb3608801f3662d7135b3a3bb1c9))

* fix: white space ([`ac62849`](https://github.com/caylent-solutions/devcontainer/commit/ac6284985f13f2235a44ffc86a353d46675d7eb9))

* fix: Replace dynamic version loading with hardcoded version for semantic-release compatibility ([`e42484c`](https://github.com/caylent-solutions/devcontainer/commit/e42484cf10d8d8b8f85dd325a01be412b4b1dfef))

### Unknown

* Merge pull request #73 from caylent-solutions/release-1.6.2

Release 1.6.2 ([`63f3167`](https://github.com/caylent-solutions/devcontainer/commit/63f3167f9ba122880bac907707f195a7b2491861))

* Merge pull request #72 from caylent-solutions/fix/version-handling-semantic-release

fix: Replace dynamic version loading with hardcoded version for seman… ([`164918b`](https://github.com/caylent-solutions/devcontainer/commit/164918b2a73c4ceff9a49edc28700c431ba784d0))


## v1.6.1 (2025-09-30)

### Chore

* chore(release): 1.6.1 ([`ed20b0e`](https://github.com/caylent-solutions/devcontainer/commit/ed20b0ef894d656f4f2ea5dc248a1b60aa4db870))

* chore: revert CHANGELOG.md to remove unwanted changes ([`72fb727`](https://github.com/caylent-solutions/devcontainer/commit/72fb7272b17c77f9cb210ac7557010807ebd086c))

### Fix

* fix: revert caylent-devcontainer-cli/CHANGELOG.md to main ([`9164634`](https://github.com/caylent-solutions/devcontainer/commit/91646345b236462a866eab083968a65aa1d9f7a0))

* fix: format ([`4db0745`](https://github.com/caylent-solutions/devcontainer/commit/4db0745d69166389ea470d25bb9d5a9946ef3d99))

* fix: make CLI version dynamic to match package metadata

- Replace hardcoded version in __init__.py with dynamic version reading
- Version now automatically syncs with pyproject.toml
- Fixes issue where CLI showed 1.0.0 instead of actual package version ([`464caf9`](https://github.com/caylent-solutions/devcontainer/commit/464caf9d7626bb3996ded0b8f16b0a6e981f70de))

### Test

* test: fix version test for dynamic version loading

- Mock importlib_metadata module to avoid import errors during testing
- Ensures test passes when package metadata is not available ([`dd2f626`](https://github.com/caylent-solutions/devcontainer/commit/dd2f626ce4e907e903616fa06f47b08b746a0401))

### Unknown

* Merge pull request #71 from caylent-solutions/release-1.6.1

Release 1.6.1 ([`5188c6e`](https://github.com/caylent-solutions/devcontainer/commit/5188c6eff5d02a8e86cbf4cf22c74cc50308207e))

* Fix issues with Github Action Create Release and dynamic cli release version

Fix issues with Github Action Create Release and dynamic cli release version ([`2e57c87`](https://github.com/caylent-solutions/devcontainer/commit/2e57c87b332cbdd6bff5eb1b907e8da0709f1703))

* fix: ([`8485264`](https://github.com/caylent-solutions/devcontainer/commit/84852649f5d6e9ddd49ecaec24248aa94abb4a35))


## v1.6.0 (2025-09-30)

### Chore

* chore(release): 1.6.0 ([`ba3101e`](https://github.com/caylent-solutions/devcontainer/commit/ba3101ecdd8d3008bacc18ef2b028d00e748c960))

* chore(release): 1.6.0 ([`53403a8`](https://github.com/caylent-solutions/devcontainer/commit/53403a8e14d5b05e2aac86fe91d9b6e0f08b9798))

* chore(release): 1.6.0 ([`8d74dc0`](https://github.com/caylent-solutions/devcontainer/commit/8d74dc0404f8395cb827548a6c3708a07ae9aec7))

* chore(release): 1.6.0 ([`258e7cc`](https://github.com/caylent-solutions/devcontainer/commit/258e7ccf1d0f64ff04bf7b9420b127ec12ec365f))

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

* fix: fix ([`cacb04a`](https://github.com/caylent-solutions/devcontainer/commit/cacb04acedb50880ea155c36cd14cdafee05101a))

* fix: fix ([`54db91f`](https://github.com/caylent-solutions/devcontainer/commit/54db91f6c83fe07df6d133817b445bb877484b28))

* fix: fix ([`2f44215`](https://github.com/caylent-solutions/devcontainer/commit/2f44215fc5fbdb04b8c7be06bf3e727c73ace2c8))

* fix: fix ([`4514c73`](https://github.com/caylent-solutions/devcontainer/commit/4514c73c4d198d0b5f87f67852f32667047a2400))

* fix: fix ([`e428180`](https://github.com/caylent-solutions/devcontainer/commit/e428180b303b674dfcb1b552408b336ef29a71db))

* fix: fix ([`8238efd`](https://github.com/caylent-solutions/devcontainer/commit/8238efd825154ef4f385d0b21276fe86d8cef6f9))

* fix: fix ([`ad39e96`](https://github.com/caylent-solutions/devcontainer/commit/ad39e969f82957fc5a039fa3bdba03e9bdbc300c))

* fix(workflow): use temporary file approach for __init__.py update

- Replace problematic inline Python with temporary file approach
- Avoids complex shell quoting and f-string issues in GitHub Actions
- Creates temporary Python script, executes it, then removes it
- More reliable across different shell environments ([`90dcb2e`](https://github.com/caylent-solutions/devcontainer/commit/90dcb2eaf60d68209cd752cc1e662571cec6127c))

* fix: sed ([`3515848`](https://github.com/caylent-solutions/devcontainer/commit/35158485806e5b0b2c6daeacab3c6473bb44bec4))

* fix(workflow): fix sed quoting issue for __init__.py update

- Change sed command to use single quotes to avoid shell quoting issues
- This fixes the &#39;unterminated s command&#39; error in GitHub Actions ([`9334f22`](https://github.com/caylent-solutions/devcontainer/commit/9334f22e0efbec0952e978484de05b6eceb659d4))

* fix: white space ([`f9a19a4`](https://github.com/caylent-solutions/devcontainer/commit/f9a19a40d7a6c612f98d2035eccc540bf79bc88b))

* fix(workflow): fix semantic-release version file synchronization

- Use semantic-release with --no-commit flag to update pyproject.toml and CHANGELOG.md
- Manually update __init__.py since semantic-release version_variable isn&#39;t working properly
- Add build artifact cleanup to prevent git workflow interference
- Fix version extraction to use pyproject.toml directly instead of step outputs
- Ensures all three version files (pyproject.toml, __init__.py, CHANGELOG.md) are synchronized

This resolves the &#39;nothing to commit, working tree clean&#39; errors and ensures proper
branch → PR → merge → tag workflow for releases. ([`229d0a7`](https://github.com/caylent-solutions/devcontainer/commit/229d0a7867d00b6a558094d291fb0706e0a1e362))

* fix: reset version files to 1.5.0 to sync with latest git tag

- Reset pyproject.toml version from 1.6.0 to 1.5.0
- Reset __init__.py __version__ from 1.6.0 to 1.5.0
- Reset CHANGELOG.md to start with v1.5.0 as latest version
- This resolves the mismatch between git tags (1.5.0) and version files (1.6.0)
- Now semantic-release can properly calculate 1.6.0 based on commits since 1.5.0 tag ([`7655573`](https://github.com/caylent-solutions/devcontainer/commit/765557359ac75ab66236ac01ddba511441aa688e))

* fix: semantic release ([`9fd8b8a`](https://github.com/caylent-solutions/devcontainer/commit/9fd8b8ac00e27b16ca25b26310c48cf22b334b5c))

* fix: semantic release v8 config (#64)

* 1.6.0

Automatically generated by python-semantic-release

* fix: update semantic-release to v8 configuration format and sync version files

- Update semantic-release config to use v8.x format with proper sections
- Fix version_variable -&gt; version_variables (array format required in v8)
- Add proper branch, changelog, remote, and publish configurations
- Sync __init__.py version to 1.6.0 to match pyproject.toml
- Include CHANGELOG.md formatting updates from semantic-release

This ensures semantic-release will update all three files (pyproject.toml, __init__.py, CHANGELOG.md)
atomically in future releases, preventing &#39;nothing to commit&#39; issues in CI/CD workflows.

* fix: correct semantic-release v8 configuration syntax

- Use version_variable (singular) not version_variables (plural)
- Use version_toml as string not array
- Restore branch config at top level
- Remove over-complex nested sections that aren&#39;t needed
- Keep the essential configuration for updating all 3 files atomically

---------

Co-authored-by: semantic-release &lt;semantic-release&gt; ([`1ea7bce`](https://github.com/caylent-solutions/devcontainer/commit/1ea7bcece8536dd661d0640c66ce376ce448c100))

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

### Unknown

* Merge pull request #69 from caylent-solutions/release-1.6.0

Release 1.6.0 ([`070a40b`](https://github.com/caylent-solutions/devcontainer/commit/070a40be443dd8abcb5fabef391d4440a26a4624))

* Expand devcontainer validation, CICD toggle, tooling improvements, and WSL support (#68)

feat: expand devcontainer validation, CICD toggle, tooling, and WSL support

- **Validation**
  - Ensure every project has a `.tool-versions` file at launch when using `cdevcontainer code &lt;project&gt;`
  - Require that `.tool-versions` contains a `python` entry, enforcing consistency in runtime management

- **CICD Mode**
  - Add toggle in the container post-create script to enable or disable AWS and Git config
  - Allows the devcontainer to run as a CICD build agent without applying developer-specific setup
  - CICD mode detection persists into shell environments for consistent behavior

- **Shell &amp; AWS CLI Options**
  - Ensures default pager goes to stdout to enable agentic agents to run commands and parse output
  - Add configuration options to customize the default shell pager
  - Add options to adjust AWS CLI output formatting for readability and consistency

- **Tooling Enhancements**
  - Add GitHub CLI (`gh`) to the default set of installed tools
  - Recommend installation of Caylent Devcontainer CLI via `pipx` to isolate from system Python packages

- **Line Endings**
  - Ensure projects can be launched from WSL under Windows
  - Add a high-performance script to recursively convert all files from Windows CRLF to Unix LF line endings
  - Set Git defaults to always clone repositories with Unix line endings

- **Setup-devcontainer Improvements**
  - Add feature to override the default devcontainer template files during `setup-devcontainer` by providing git ref with arg `--ref`
    - Enables testing and iteration on templates before a semantic release is published
  - Remove fallback logic where `setup-devcontainer` would silently ignore missing semantic releases of the CLI
    - Enforces explicit release workflow and removes hidden paths

- **WSL Support**
  - Add comprehensive support for running devcontainer under Windows Subsystem for Linux (WSL)
  - `devcontainer.json` now launches the post-create command ensuring all files have Unix line endings
  - Post-create script enhancements:
    - Ensure shell environment variables load across Bash, Zsh, and other shells
    - Normalize commands to work seamlessly in WSL environments
  - Update `setup-container` workflow for WSL compatibility ([`d35ce6e`](https://github.com/caylent-solutions/devcontainer/commit/d35ce6e7e8d95b9dd73dd0d790c89dcd9e2178a1))


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
