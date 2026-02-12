# [S1.1.2] Template Utility Functions

## Work Unit Metadata

| Field | Value |
|-------|-------|
| **Type** | Story |
| **Number** | S1.1.2 |
| **Status** | complete |
| **Parent** | F1.1 — Core DRY Refactoring & Removals |
| **Epic** | E1 — Caylent DevContainer CLI v2.0.0 |

## Description

Implement shared template utilities, missing variable detection, version compatibility checks, CLI_NAME constant consolidation, and project root resolution. This story consolidates scattered inline patterns into single shared implementations.

**Development Workflow (TDD):**
1. Write the test — verify it fails (red)
2. Write the code — verify the test passes (green)
3. Achieve 90%+ unit test coverage
4. Write functional tests for end-to-end behavior
5. Fix linting/formatting: `cd caylent-devcontainer-cli && make lint && make format`

## Definition of Ready

- No dependencies

## Full Requirements

### D. Template Utilities (Spec Section D)

**`get_template_path(name) -> str`** — Single function for `os.path.join(TEMPLATES_DIR, f"{name}.json")`:
- Replaces 7 inline template path constructions throughout the codebase
- Must use the TEMPLATES_DIR constant

**`get_template_names() -> list[str]`** — Single function that scans TEMPLATES_DIR and returns template names:
- `template list` calls it for display
- `setup_interactive` calls it for selection choices
- Replaces all template name scanning logic

**`ensure_templates_dir()`** — Single function in a shared utility:
- Replaces 3 implementations currently in the codebase
- Creates the templates directory if it does not exist

**`validate_template(template_data) -> template_data`** — Single validation function:
- Called on every template load
- Full implementation is in S1.2.1; this story creates the function signature/stub location

### E. Missing Variable Detection (Spec Section E)

**`get_missing_env_vars(container_env: dict) -> dict`** — Single function that checks against EXAMPLE_ENV_VALUES:
- Replaces `code.py:check_missing_env_vars()`
- Replaces `template.py:get_missing_single_line_vars()`
- Returns a dict of missing environment variables

### F. Version Compatibility (Spec Section F)

**`check_template_version(template_data)`** — Single function that validates cli_version matches current CLI major version:
- For v2.0.0, rejects any template without cli_version or with a v1.x version
- Replaces 3 separate semver comparison implementations

### I. CLI_NAME Constant (Spec Section I)

- Remove CLI_NAME from `cli.py`
- Import from `utils/constants.py` where it already exists
- Ensure all references throughout codebase use the constant from `utils/constants.py`

### K. Project Root Resolution (Spec Section K)

**`resolve_project_root(path=None) -> str`** — Single function that:
- Defaults to `os.getcwd()` when path is None
- Validates `.devcontainer/` exists in the resolved path
- Replaces `find_project_root()` and 3 inline `args.project_root or os.getcwd()` patterns

### Key Files to Modify

- `caylent-devcontainer-cli/src/caylent_devcontainer_cli/utils/template.py` — new or extended with template utilities
- `caylent-devcontainer-cli/src/caylent_devcontainer_cli/utils/constants.py` — CLI_NAME consolidation
- `caylent-devcontainer-cli/src/caylent_devcontainer_cli/utils/fs.py` — resolve_project_root()
- `caylent-devcontainer-cli/src/caylent_devcontainer_cli/commands/code.py` — replace check_missing_env_vars()
- `caylent-devcontainer-cli/src/caylent_devcontainer_cli/commands/template.py` — replace get_missing_single_line_vars()
- `caylent-devcontainer-cli/src/caylent_devcontainer_cli/commands/setup.py` — replace inline patterns
- `caylent-devcontainer-cli/src/caylent_devcontainer_cli/cli.py` — remove CLI_NAME definition
- `caylent-devcontainer-cli/tests/unit/` — add unit tests
- `caylent-devcontainer-cli/tests/functional/` — add functional tests

## Acceptance Criteria

- [x] `get_template_path()` replaces all 7 inline template path constructions
- [x] `get_template_names()` replaces all template name scanning logic
- [x] `ensure_templates_dir()` replaces all 3 implementations
- [x] `get_missing_env_vars()` replaces `check_missing_env_vars()` and `get_missing_single_line_vars()`
- [x] `check_template_version()` replaces 3 separate semver comparison implementations
- [x] CLI_NAME imported from `utils/constants.py` everywhere (removed from `cli.py`)
- [x] `resolve_project_root()` replaces `find_project_root()` and 3 inline patterns
- [x] 90% or greater unit test coverage for all new/modified code
- [x] Functional tests verify end-to-end behavior
- [x] All existing tests still pass after refactoring
- [x] Linting and formatting pass (`make lint && make format`)
- [x] Docs updated if project documentation is affected by these changes

## Log

Completed and pushed on 2026-02-12. All acceptance criteria met. 502 tests pass, lint clean, 91% coverage.

### Retroactive AC Validation — 2026-02-12

All 12 acceptance criteria validated one by one with concrete evidence:
- `get_template_path` at template.py:13, 8 callers, no inline path constructions remain
- `get_template_names` at template.py:25, used by template.py and setup_interactive.py
- `ensure_templates_dir` at template.py:43, 4 callers, no inline makedirs for templates
- `get_missing_env_vars` at env.py:13, replaces old check_missing_env_vars/get_missing_single_line_vars (grep: 0 matches for old names)
- `check_template_version` at template.py:62, 6 tests covering version validation
- CLI_NAME defined in constants.py:9, imported in cli.py:8, no local definition in cli.py
- `resolve_project_root` at fs.py:114, no inline `args.project_root or os.getcwd()` patterns remain
- Coverage: template.py 95%, env.py 100%, fs.py 93%
- 393 unit tests pass, 98 functional tests pass
- Lint clean
- No documentation affected (internal utility functions only, no user-facing changes)

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
