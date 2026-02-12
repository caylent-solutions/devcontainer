# [S1.1.3] UI & Prompt Utilities

## Work Unit Metadata

| Field | Value |
|-------|-------|
| **Type** | Story |
| **Number** | S1.1.3 |
| **Status** | in-review |
| **Parent** | F1.1 — Core DRY Refactoring & Removals |
| **Epic** | E1 — Caylent DevContainer CLI v2.0.0 |

## Description

Implement shared UI and prompt utilities including ask_or_exit(), exit_cancelled(), and exit_with_error(). Remove deprecated AUTO_YES/set_auto_yes() and confirm_overwrite() patterns. This story consolidates scattered inline exit and confirmation patterns into single shared implementations.

**Development Workflow (TDD):**
1. Write the test — verify it fails (red)
2. Write the code — verify the test passes (green)
3. Achieve 90%+ unit test coverage
4. Write functional tests for end-to-end behavior
5. Fix linting/formatting: `cd caylent-devcontainer-cli && make lint && make format`

## Definition of Ready

- No dependencies

## Full Requirements

### G. Confirmation and Prompt Utilities (Spec Section G)

**Remove `setup.py:confirm_overwrite()`:**
- All confirmation prompts must use `ui.py:confirm_action()`
- Remove the duplicate confirm_overwrite() function from setup.py

**Remove `AUTO_YES` / `set_auto_yes()`:**
- The -y/--yes flag is removed entirely in v2.0.0
- All prompts require explicit user interaction
- Remove all AUTO_YES checks and the set_auto_yes() function from utils/ui.py

**`ask_or_exit(questionary_question)`** — Wrapper utility in `utils/ui.py`:
- Calls `.ask()` on the provided questionary question
- Checks for None return value (user cancelled)
- Calls `exit_cancelled()` if None
- Returns the answer if not None
- Replaces 14 inline null-check patterns in setup_interactive.py

**`exit_cancelled(message="Operation cancelled by user")`** — Single function in `utils/ui.py`:
- Logs the cancellation message
- Exits with appropriate exit code
- Replaces ~20 scattered cancellation exit patterns throughout the codebase

**`exit_with_error(message)`** — Single function in `utils/ui.py`:
- Logs the error message
- Calls `sys.exit(1)`
- Replaces ~40 inline `import sys; sys.exit(1)` patterns throughout the codebase

### Key Files to Modify

- `caylent-devcontainer-cli/src/caylent_devcontainer_cli/utils/ui.py` — add ask_or_exit(), exit_cancelled(), exit_with_error(); remove AUTO_YES/set_auto_yes()
- `caylent-devcontainer-cli/src/caylent_devcontainer_cli/commands/setup.py` — remove confirm_overwrite(), use confirm_action()
- `caylent-devcontainer-cli/src/caylent_devcontainer_cli/commands/setup_interactive.py` — replace 14 inline null-check patterns with ask_or_exit()
- All files with inline `sys.exit(1)` — replace with exit_with_error()
- All files with cancellation exit patterns — replace with exit_cancelled()
- `caylent-devcontainer-cli/tests/unit/` — add unit tests
- `caylent-devcontainer-cli/tests/functional/` — add functional tests

## Acceptance Criteria

- [ ] `ask_or_exit()` implemented in `utils/ui.py`, replaces 14 inline null-check patterns
- [ ] `exit_cancelled()` implemented in `utils/ui.py`, replaces ~20 cancellation exit patterns
- [ ] `exit_with_error()` implemented in `utils/ui.py`, replaces ~40 inline `sys.exit(1)` patterns
- [ ] `confirm_overwrite()` removed from `setup.py`, all callers use `confirm_action()`
- [ ] `AUTO_YES` and `set_auto_yes()` removed from `utils/ui.py`
- [ ] All AUTO_YES checks removed throughout the codebase
- [ ] 90% or greater unit test coverage for all new/modified code
- [ ] Functional tests verify end-to-end behavior
- [ ] All existing tests still pass after refactoring
- [ ] Linting and formatting pass (`make lint && make format`)
- [ ] Docs updated if project documentation is affected by these changes

## Log

### Session 1 — 2026-02-12

**Completed:**
- Added `exit_with_error(message)`, `exit_cancelled(message)`, and `ask_or_exit(question)` to `utils/ui.py`
- Removed `AUTO_YES` global variable and `set_auto_yes()` function from `utils/ui.py`
- Removed `confirm_overwrite()` from `commands/setup.py`, replaced callers with `confirm_action()`
- Removed AUTO_YES setter block from `cli.py`
- Replaced 14 inline questionary null-check patterns in `setup_interactive.py` with `ask_or_exit()`
- Replaced ~20 cancellation exit patterns across setup.py, template.py, code.py, install.py, fs.py with `exit_cancelled()`
- Replaced ~25 inline `log("ERR")+import sys+sys.exit(1)` patterns across all command/utility files with `exit_with_error()`
- Eliminated all inline `import sys` patterns from command and utility modules
- Created `tests/unit/test_ui_utilities.py` with 19 tests (100% coverage on ui.py)
- Fixed 18 broken tests from AUTO_YES/confirm_overwrite removals
- Fixed functional tests to use stdin input instead of `-y` flag
- All 512 tests pass, lint clean, 100% coverage on ui.py

**Remaining:** None — ready for human review

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
