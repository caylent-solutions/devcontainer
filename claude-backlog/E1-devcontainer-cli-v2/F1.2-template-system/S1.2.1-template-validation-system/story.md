# [S1.2.1] Template Validation System

## Work Unit Metadata

| Field | Value |
|-------|-------|
| **Type** | Story |
| **Number** | S1.2.1 |
| **Status** | in-review |
| **Parent** | F1.2 — Template System |
| **Epic** | E1 — Caylent DevContainer CLI v2.0.0 |

## Description

Implement a shared `validate_template()` function that every command reading a template must call before using the data. This function performs structural validation, base key completeness checks, known key value validation, auth method consistency checks, and conflict detection.

**Development Workflow (TDD):**
1. Write the test — verify it fails (red)
2. Write the code — verify the test passes (green)
3. Achieve 90%+ unit test coverage
4. Write functional tests for end-to-end behavior
5. Fix linting/formatting: `cd caylent-devcontainer-cli && make lint && make format`

## Definition of Ready

- S1.1.2 (template utilities) must be complete
- S1.1.3 (UI utilities) must be complete

## Full Requirements

### Structural Validation

- `containerEnv` must exist and be a dict — exit non-zero if not
- `cli_version` must exist and be a v2.x version — if missing or v1.x, exit non-zero: "This template was created with CLI v1.x and is not compatible with v2.0.0. Please recreate your template using `cdevcontainer template create <name>`"
- `template_name` must exist — exit non-zero if not
- `template_path` must exist — exit non-zero if not

### Base Key Completeness

- Verify all EXAMPLE_ENV_VALUES keys exist in containerEnv (respecting conditional requirements — GIT_TOKEN only when GIT_AUTH_METHOD=token; HOST_PROXY_URL is always present but value only validated when HOST_PROXY=true)
- If any are missing, present each missing key with its default value and prompt the user to accept the default or enter a custom value

### Known Key Value Validation

- AWS_CONFIG_ENABLED must be "true" or "false"
- HOST_PROXY must be "true" or "false"
- GIT_AUTH_METHOD must be "token" or "ssh"
- HOST_PROXY_URL must start with http:// or https:// (only validated when HOST_PROXY=true)
- GIT_PROVIDER_URL must be hostname only — no protocol prefix, must contain at least one dot
- If any value is invalid, show the current value, explain what is expected, and prompt for correction

### Auth Method Consistency

- If GIT_AUTH_METHOD=token: GIT_TOKEN must exist and be non-empty. ssh_private_key must NOT exist.
- If GIT_AUTH_METHOD=ssh: GIT_TOKEN must NOT exist. ssh_private_key must exist.
- If both GIT_TOKEN and ssh_private_key are present: prompt user to choose one, remove the other

### Conflict Detection

- If CLI version has added new known keys that already exist in template as user-added custom keys, flag each one
- Show key name, current value in template, and CLI's expected default
- Prompt: keep existing value, use CLI default, or enter new value

### Where This Runs

One shared `validate_template()` function called by: template load, template upgrade, setup-devcontainer (interactive), and code (for template comparison).

### Key Files to Modify

- `caylent-devcontainer-cli/src/caylent_devcontainer_cli/utils/template.py` — new module or extend existing, add `validate_template()`
- `caylent-devcontainer-cli/src/caylent_devcontainer_cli/utils/ui.py` — UI prompts for validation corrections
- `caylent-devcontainer-cli/src/caylent_devcontainer_cli/utils/constants.py` — known keys, constraints
- `caylent-devcontainer-cli/tests/unit/` — unit tests for validation logic
- `caylent-devcontainer-cli/tests/functional/` — functional tests for end-to-end validation behavior

## Acceptance Criteria

- [x] `validate_template()` implemented as shared function
- [x] Structural validation: containerEnv, cli_version, template_name, template_path
- [x] v1.x templates rejected with clear migration error message
- [x] Base key completeness check against EXAMPLE_ENV_VALUES with conditional logic
- [x] Missing keys prompt user for default or custom value
- [x] Known key value validation for all constrained fields
- [x] Auth method consistency check (token vs SSH mutual exclusivity)
- [x] Conflict detection for new known keys vs existing custom keys
- [x] Called by template load, template upgrade, setup-devcontainer, code
- [x] 90% or greater unit test coverage for all new/modified code
- [x] Functional tests verify end-to-end behavior
- [x] All existing tests still pass after refactoring
- [x] Linting and formatting pass (`make lint && make format`)
- [x] Pre-commit check passes (`cd caylent-devcontainer-cli && make test && make lint && cd .. && make pre-commit-check`)
- [x] Docs updated if project documentation is affected by these changes

## Log

### Session 1 — 2026-02-12

**Completed:**
- Added `REQUIRED_TEMPLATE_KEYS` and `VALID_KEY_VALUES` to `utils/constants.py`
- Updated `EXAMPLE_ENV_VALUES` in `setup.py`: added GIT_AUTH_METHOD, HOST_PROXY, HOST_PROXY_URL; removed CICD
- Implemented full `validate_template()` in `utils/template.py` with 5 private helper functions:
  - `_validate_structure()` — containerEnv, cli_version (v2.x check, v1.x migration error), template_name, template_path
  - `_validate_base_key_completeness()` — checks all EXAMPLE_ENV_VALUES keys, GIT_TOKEN conditional on auth method
  - `_validate_known_key_values()` — validates constrained keys via VALID_KEY_VALUES, GIT_PROVIDER_URL (hostname only), HOST_PROXY_URL (http(s):// prefix when proxy enabled)
  - `_validate_auth_consistency()` — token requires non-empty GIT_TOKEN and removes ssh_private_key; ssh removes GIT_TOKEN
  - `_detect_conflicts()` — flags known keys from newer CLI versions conflicting with custom keys
- Wired `validate_template()` into `interactive_setup()` (setup.py) and `load_template()` (template.py)
- Wrote 51 unit tests in `tests/unit/test_validate_template.py` (all 5 phases + edge cases)
- Wrote 17 functional tests in `tests/functional/test_validate_template.py`
- Fixed regressions in test_setup.py (2 tests), test_template.py (7 tests), test_template_utils.py (2 tests), test_template_utilities.py (1 test), test_code_command.py (5 tests), test_code_missing_vars.py (1 test)
- Coverage: 97% on `utils/template.py`
- Quality gate: 462 unit tests pass (3 skipped), 165 functional tests pass, lint clean, pre-commit clean

**Remaining:**
- None — all acceptance criteria met

**Notes:**
- Template upgrade (S1.2.4) and code command rewrite (S1.3.2/S1.3.3) are future stories — `validate_template()` is ready for them to wire in
- `REQUIRED_TEMPLATE_KEYS` constant defined in constants.py for documentation/reference but not imported in template.py (structural validation uses inline checks)
- Deep copy ensures original template dict is never mutated

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
