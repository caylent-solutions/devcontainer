# [S1.2.4] Template Upgrade Command

## Work Unit Metadata

| Field | Value |
|-------|-------|
| **Type** | Story |
| **Number** | S1.2.4 |
| **Status** | in-review |
| **Parent** | F1.2 — Template System |
| **Epic** | E1 — Caylent DevContainer CLI v2.0.0 |

## Description

Implement the `template upgrade` command that brings an existing template up to the current CLI version's standards. Used for major version upgrades and minor version additions when new required base keys are introduced. This command modifies ONLY the template file itself — it does not modify any project files.

**Development Workflow (TDD):**
1. Write the test — verify it fails (red)
2. Write the code — verify the test passes (green)
3. Achieve 90%+ unit test coverage
4. Write functional tests for end-to-end behavior
5. Fix linting/formatting: `cd caylent-devcontainer-cli && make lint && make format`

## Definition of Ready

- S1.2.1 (template validation system) must be complete

## Full Requirements

### Purpose

Brings an existing template up to the current CLI version's standards. Used for major version upgrades and minor version additions when new required base keys are introduced.

### Scope

`template upgrade` modifies ONLY the template file itself. It does not modify any project files. Projects that reference the upgraded template detect changes on next `cdevcontainer code` run via validation steps.

### Behavior

1. Read template from `~/.devcontainer-templates/<name>.json`
2. Run `validate_template()` — detects all issues: missing base keys (prompt for value or default), invalid constraint values (prompt for correction), auth method inconsistencies (prompt to resolve), missing/outdated cli_version
3. Update cli_version to current CLI version
4. Save updated template file
5. Display: "Template '\<name\>' upgraded to CLI v\<version\>. Projects using this template will be updated on next `cdevcontainer code` run."

### Version Transitions

- **v1.x template:** Rejected by `validate_template()` with migration error
- **v2.x template with missing keys from newer v2.x CLI:** Adds missing keys, updates cli_version, saves
- **v2.x template already at current version:** No changes needed — inform user template is up to date

### Key Files to Modify

- `caylent-devcontainer-cli/src/caylent_devcontainer_cli/commands/template.py` — template upgrade command implementation
- `caylent-devcontainer-cli/tests/unit/` — unit tests for upgrade command
- `caylent-devcontainer-cli/tests/functional/` — functional tests for end-to-end upgrade behavior

## Acceptance Criteria

- [x] `template upgrade` reads and validates existing template
- [x] v1.x templates rejected with migration error
- [x] Missing base keys detected and user prompted for values
- [x] Invalid constraint values detected and user prompted for correction
- [x] Auth method inconsistencies resolved via prompts
- [x] cli_version updated to current version
- [x] Template file saved after upgrades
- [x] Already up-to-date templates handled with info message
- [x] Template file only modified (no project files touched)
- [x] 90% or greater unit test coverage for all new/modified code
- [x] Functional tests verify end-to-end behavior
- [x] All existing tests still pass after refactoring
- [x] Linting and formatting pass (`make lint && make format`)
- [x] Pre-commit check passes (`cd caylent-devcontainer-cli && make test && make lint && cd .. && make pre-commit-check`)
- [x] Docs updated if project documentation is affected by these changes

## Log

### Session 1 — 2026-02-12

**Completed:**
- Rewrote `upgrade_template_file()` in `commands/template.py` — removed `--force` flag, removed semver comparison, removed try/except wrapper, removed `upgrade_template_with_missing_vars()` and `prompt_for_missing_vars()`. Now uses `validate_template()` for all validation/fixes and checks for already-current version.
- Removed old unit tests for force flag, semver parsing, version mismatch, missing vars prompting (12 tests removed)
- Added 7 new unit tests: already_current_version, calls_validate_template, updates_cli_version, saves_template_file, success_message, v1x_rejected_by_validate, not_found
- Added 6 source inspection tests: no_force_flag, no_try_except, uses_validate_template, no_semver_in_function, no_upgrade_template_import
- Replaced `test_template_upgrade_force.py` with `test_template_upgrade.py` — 13 functional tests (8 source inspection + 5 end-to-end)
- Removed duplicate tests from `test_template_upgrade_enhancements.py` (TestPromptForMissingVars, TestUpgradeTemplateWithMissingVars classes)
- Removed duplicate tests from `test_setup.py` (test_prompt_for_missing_vars_use_defaults, test_upgrade_template_with_missing_vars)
- Updated `test_prompt_confirmation.py` to reference load_template instead of removed prompt_for_missing_vars
- Cleaned up imports: removed semver, upgrade_template from setup_interactive, get_missing_env_vars
- Coverage: template.py 99%
- Quality gate: 719 tests pass (3 skipped), lint clean, pre-commit clean

**Remaining:**
- None — all acceptance criteria met

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
