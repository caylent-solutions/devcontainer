# [S1.3.3] Code Command Validation (Steps 0-5)

## Work Unit Metadata

| Field | Value |
|-------|-------|
| **Type** | Story |
| **Number** | S1.3.3 |
| **Status** | in-review |
| **Parent** | F1.3 — Command Rewrites |
| **Epic** | E1 — Caylent DevContainer CLI v2.0.0 |

## Description

Implement the two-stage environment variable validation for the code command (Steps 0-5). When both project files exist, perform validation before launching the IDE. The validation detection logic (Steps 0-3) is shared with setup-devcontainer via a single shared function. The code command diverges on the response by prompting the user to fix issues (Steps 4-5).

**Development Workflow (TDD):**
1. Write the test — verify it fails (red)
2. Write the code — verify the test passes (green)
3. Achieve 90%+ unit test coverage
4. Write functional tests for end-to-end behavior
5. Fix linting/formatting: `cd caylent-devcontainer-cli && make lint && make format`

## Definition of Ready

- S1.3.2 (code command rewrite) must be complete
- S1.2.1 (template validation) must be complete

## Full Requirements

### Shared Validation Detection (Steps 0-3)

Both code and setup-devcontainer share the same validation detection logic via a single shared function. They diverge on the response: code prompts the user to fix (Steps 4-5), setup-devcontainer displays informational only.

#### Step 0 — Check Base Keys

- Verify all EXAMPLE_ENV_VALUES keys exist in both files (respecting conditional requirements)
- If any base keys missing, flag them — project files out of date with current CLI version

#### Step 1 — Validate Required Metadata

- Check both files for required metadata (template_name, template_path, cli_version)
- If metadata missing: notify user, prompt Yes (default, green) to select/create template and regenerate, or No (red) with warning and launch without changes

#### Step 2 — Locate and Validate Template

- Using template_name and template_path from metadata, locate developer template
- If template not found: exit non-zero with error and remediation instructions
- Run validate_template() on loaded template

#### Step 3 — Compare Against Template

- Compare project files against containerEnv values in developer template
- Identify key/value pairs from template missing from either file

### Code Command Response (Steps 4-5)

#### Step 4 — Handle Missing Variables

- Notify user, display which variables are missing, from which files, what values would be added
- Warn about potential build issues

#### Step 5 — User Confirmation

- Option 1 (default): Update config and add missing variables via write_project_files(), read catalog-entry.json for catalog_url and collection name, invoke catalog pipeline to replace .devcontainer/ files (or prompt for catalog source if catalog-entry.json missing)
- Option 2: Only add missing variables to existing files, do not modify .devcontainer/

After either option: launch IDE.

### Two-Stage Environment Variable Validation

- Stage 1: Base Keys (EXAMPLE_ENV_VALUES) — check both files
- Stage 2: Developer Template — locate template, compare all containerEnv keys
- Both stages feed into Steps 4-5

### Key Files to Modify

- `caylent-devcontainer-cli/src/caylent_devcontainer_cli/commands/code.py` — Steps 4-5 response logic
- `caylent-devcontainer-cli/src/caylent_devcontainer_cli/utils/validation.py` — new shared module for Steps 0-3
- `caylent-devcontainer-cli/tests/unit/` — add unit tests
- `caylent-devcontainer-cli/tests/functional/` — add functional tests

## Acceptance Criteria

- [x] Shared validation detection function (Steps 0-3) implemented — `detect_validation_issues()` in `utils/validation.py:146`
- [x] Step 0: base key check against EXAMPLE_ENV_VALUES with conditional logic — lines 166-178, GIT_TOKEN/ssh conditional at line 171; 4 unit tests in `TestStep0BaseKeyCheck`
- [x] Step 1: metadata validation with prompt for regeneration — detection in `validation.py:180-190`, prompt in `code.py:131-157`; 4 unit tests in `TestStep1MetadataValidation`
- [x] Step 2: template location and validation — `_step2_locate_template()` at `validation.py:128-143`; 4 unit tests (2 mocked + 2 real file I/O)
- [x] Step 3: template comparison detecting missing keys — `validation.py:200-204`; 3 unit tests in `TestStep3TemplateComparison`
- [x] Step 4: clear display of missing variables with file sources — `code.py:170-179` with "base keys" vs "template" source attribution; `test_step4_displays_missing_variables` test
- [x] Step 5: two-option prompt (update config + catalog, or just add variables) — `code.py:181-217` with two questionary choices; `test_step5_option1_updates_project_files` and `test_step5_option2_adds_vars_only` tests
- [x] Two-stage validation (base keys + template comparison) working — `ValidationResult.all_missing_keys` merges both; `test_all_missing_keys_combines_stages` test
- [x] Shared function reusable by setup-devcontainer (informational mode) — `detect_validation_issues` in shared `utils/validation.py`, returns `ValidationResult` dataclass; caller decides response
- [x] 90%+ unit test coverage, functional tests pass — code.py 93%, validation.py 100%; 232 tests pass
- [x] Linting and formatting pass (`make lint && make format`) — verified clean
- [x] Pre-commit check passes (`cd caylent-devcontainer-cli && make test && make lint && cd .. && make pre-commit-check`) — verified clean
- [x] Docs updated if project documentation is affected by these changes — no existing docs reference code command validation behavior; no updates needed

## Log

### Session 1 — 2026-02-12

**Completed:**
- Created `src/caylent_devcontainer_cli/utils/validation.py` with shared validation detection (Steps 0-3)
  - `ValidationResult` dataclass with `has_issues` and `all_missing_keys` properties
  - `parse_shell_env()` for extracting keys and metadata from shell.env
  - `_read_shell_env()` and `_step2_locate_template()` helper functions
  - `detect_validation_issues()` main entry point implementing Steps 0-3
- Integrated Steps 4-5 into `code.py`:
  - `_handle_missing_metadata()` for Step 1 user prompt
  - `_handle_missing_variables()` for Steps 4-5 display and two-option prompt
  - Connected validation flow between file checks and IDE launch
- Wrote 30 unit tests in `test_validation.py` (100% coverage)
- Wrote 22 unit tests in `test_code.py` (93% coverage) including 8 new validation-specific tests
- Updated ALL consumers of old code (replaced functions): test_cdevcontainer.py, test_code_missing_vars.py, test_code_command.py, test_prompt_confirmation.py, test_template_upgrade_enhancements.py
- Created `_setup_validation_env()` helper in test_code_command.py for subprocess functional tests
- Created `REVIEW-SUPERSEDED-CODE.md` review prompt for pre-merge review
- Updated `CLAUDE.md` with "Complete Replacement of Superseded Code" standard
- Updated `AGENT-PROMPT.md` with "Complete Replacement of Superseded Code" section

**Debugging Notes:**
- Subprocess functional tests require HOME override so TEMPLATES_DIR resolves inside temp directory
- Template JSON must include `containerEnv`, `cli_version`, `template_name`, `template_path` for `validate_template()` to pass
- Source inspection tests break when black reformats imports to multi-line — use `hasattr(module, "name")` instead of scanning source lines
- `_NO_ISSUES` helper (pre-built ValidationResult with no issues) is essential for tests that don't care about validation

---

## General Code Requirements

### Core Coding Principles

#### Fail-Fast Philosophy

- Never introduce fallback logic of any kind
- Never hard code configuration values
- Never allow operations to fail silently
- All failures must fail fast, exit with non-zero exit code, and surface clear, actionable error messages

#### SOLID Principles

- **Single Responsibility Principle (SRP):** Each class/method should have one reason to change
- **Open/Closed Principle (OCP):** Open for extension, closed for modification
- **Liskov Substitution Principle (LSP):** Subtypes must be substitutable for base types
- **Interface Segregation Principle (ISP):** Create focused, role-specific interfaces
- **Dependency Inversion Principle (DIP):** Depend on abstractions, not concretions

#### DRY Principle (Don't Repeat Yourself)

- Never duplicate code or logic
- Extract common logic into reusable methods, classes, or utilities
- Use inheritance, composition, or delegation to share behavior
- If you write the same logic twice, refactor it into a shared component

#### 12-Factor App Principles

- **Codebase:** One codebase in version control, many deploys
- **Dependencies:** Explicitly declare and isolate all dependencies
- **Config:** Store config in environment variables, never in code
- **Backing Services:** Treat as attached resources, swappable without code changes
- **Build, Release, Run:** Strictly separate stages
- **Processes:** Execute as stateless processes
- **Port Binding:** Export services via port binding (configurable via env vars)
- **Concurrency:** Scale out via process model
- **Disposability:** Fast startup, graceful shutdown
- **Dev/Prod Parity:** Keep environments similar
- **Logs:** Treat as event streams to stdout/stderr
- **Admin Processes:** Run as one-off processes with same codebase

#### Idiomatic Code

- Follow conventions, patterns, and best practices of the specific technology
- Use language-specific idioms and patterns
- Prefer framework-provided solutions over custom implementations

#### Declarative vs Imperative Code

- State descriptions must be declarative (describe **what**), not imperative (describe **how**)
- Use declarative configuration files, IaC, database schemas
- Avoid procedural scripts for infrastructure changes

#### Environment-Agnostic Artifacts

- Build once, deploy anywhere
- No environment-specific code or configuration in artifacts
- All environment-specific configuration injected at runtime
- Never build separate artifacts per environment

#### Input-Driven and Dynamic Configuration

- All code must be input-driven and dynamically configured, not static
- Never use hard-coded values for: URLs, credentials, timeouts, file paths, environment settings, feature flags, test data, port numbers, dates, identifiers
- Externalize all configuration via environment variables or configuration files
- Make all thresholds, limits, and boundaries configurable

### Testing Standards

#### Real Tests Only — No Stubs

- Never create stub tests that always pass
- Tests must validate actual behavior, not mock success
- Tests must be able to fail if code is wrong
- No placeholder tests marked with TODO
- Integration tests must test real integrations (test containers/databases)

### Security Standards

#### Security Scans

- Never add code exceptions to bypass security scan failures without explicit human permission
- Never use `// nosec`, `# noqa`, or `@SuppressWarnings("security")` without approval
- If scan fails: document, analyze, fix code (don't suppress), ask human if false positive

#### Sensitive Data Handling

- Never log, display, or expose: passwords, API keys, SSN, credit cards, PII, tokens, encryption keys
- Use AWS Secrets Manager/Parameter Store for secrets
- Never commit secrets to git
- Mask/redact sensitive data in logs
- Encrypt sensitive data at rest and in transit

#### Input Validation and Sanitization

- Validate all user input: type, length, format, range
- Use allowlists, not denylists
- Reject invalid input, don't fix it
- Sanitize for SQL injection, XSS, command injection
- Use parameterized queries for all database operations
- Never trust any input from users, APIs, or external systems

#### Authentication and Authorization

- Implement proper session management with secure cookies
- Use strong password policies
- Use OAuth 2.0/OpenID Connect for API auth
- Implement RBAC
- JWT: short expiration, refresh mechanisms, RS256 signing
- Regenerate session IDs after auth, implement timeout, secure HTTP-only cookies

#### Cryptography

- Use TLS 1.2+ for all network communication
- Use AES-256 for data at rest
- Use bcrypt, scrypt, or Argon2 for password hashing (never MD5, SHA1, plain SHA256)
- Never implement custom crypto algorithms
- Never store encryption keys in code

#### API Security

- Implement rate limiting
- Validate Content-Type headers
- Implement CORS policies (never wildcard origins in production)
- Return generic error messages
- Implement request size limits
- Required response headers: `Strict-Transport-Security`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Content-Security-Policy`

#### SQL Injection Prevention

- Use parameterized queries exclusively
- Never concatenate user input into SQL queries
- Use named parameters in native queries

#### XSS Prevention

- Escape all output by default
- Use templating engines with auto-escaping
- Implement Content Security Policy headers
- Use context-aware encoding

#### Container Security

- Run containers as non-root user
- Use minimal base images (distroless when possible)
- Implement resource limits
- Use read-only file systems where possible
- Drop unnecessary Linux capabilities

#### Error Handling and Logging

- Log security-relevant events with timestamps, user IDs, actions
- Never log sensitive data
- Never return stack traces or detailed errors to clients
- Use generic error messages for authentication failures

### Waiting and Readiness Detection

#### Time-Based Delays Are Prohibited

- Never use `sleep` to wait for anything
- Never use time-based delays as synchronization

#### Required: Active Readiness Detection

- Use health check endpoints, port availability checks, file existence, API status polling, process state monitoring, container readiness probes
- All waits must support variable-driven timeouts (no hard-coded values)
- On timeout: fail fast, non-zero exit code, clear diagnostic message

### Shell and Scripting Standards

#### Script Creation Policy

- Never create shell scripts unless explicitly requested by the prompt
- Shell code must not be embedded in application code, CI/CD pipelines, or build logic

#### Prohibited Patterns

- Never use `sleep` commands or sleep-based methods
- Prefer event-driven logic, state polling with conditions, lifecycle hooks, built-in readiness mechanisms
