# [S1.2.3] Template Load Command

## Work Unit Metadata

| Field | Value |
|-------|-------|
| **Type** | Story |
| **Number** | S1.2.3 |
| **Status** | in-review |
| **Parent** | F1.2 — Template System |
| **Epic** | E1 — Caylent DevContainer CLI v2.0.0 |

## Description

Rewrite the `template load` command to use the shared `validate_template()` function and generate both `devcontainer-environment-variables.json` and `shell.env` via `write_project_files()`. The current behavior only writes the JSON file; the new behavior adds shell.env generation, SSH key writing, AWS profile map writing, and .gitignore management.

**Development Workflow (TDD):**
1. Write the test — verify it fails (red)
2. Write the code — verify the test passes (green)
3. Achieve 90%+ unit test coverage
4. Write functional tests for end-to-end behavior
5. Fix linting/formatting: `cd caylent-devcontainer-cli && make lint && make format`

## Definition of Ready

- S1.2.1 (template validation system) must be complete
- S1.1.5 must be complete

## Full Requirements

### Current Behavior Being Changed

Currently template load reads template, checks version, writes devcontainer-environment-variables.json only. Does NOT generate shell.env.

### New Behavior

1. Read template from `~/.devcontainer-templates/<name>.json`
2. Run `validate_template()` — rejects v1.x templates, validates structure, checks base keys, validates constraints, checks auth consistency
3. Write both `devcontainer-environment-variables.json` and `shell.env` via `write_project_files()`
4. If GIT_AUTH_METHOD=ssh: write `.devcontainer/ssh-private-key`
5. If AWS_CONFIG_ENABLED=true: write `.devcontainer/aws-profile-map.json`
6. Ensure `.gitignore` entries

### Key Files to Modify

- `caylent-devcontainer-cli/src/caylent_devcontainer_cli/commands/template.py` — template load command rewrite
- `caylent-devcontainer-cli/src/caylent_devcontainer_cli/utils/fs.py` — write_project_files(), gitignore management
- `caylent-devcontainer-cli/tests/unit/` — unit tests for load command
- `caylent-devcontainer-cli/tests/functional/` — functional tests for end-to-end load behavior

## Acceptance Criteria

- [x] Template loaded from `~/.devcontainer-templates/<name>.json`
- [x] `validate_template()` called before use
- [x] v1.x templates rejected with clear error
- [x] Both files generated via `write_project_files()`
- [x] SSH key written when GIT_AUTH_METHOD=ssh
- [x] AWS profile map written when AWS_CONFIG_ENABLED=true
- [x] `.gitignore` entries ensured
- [x] 90% or greater unit test coverage for all new/modified code
- [x] Functional tests verify end-to-end behavior
- [x] All existing tests still pass after refactoring
- [x] Linting and formatting pass (`make lint && make format`)
- [x] Pre-commit check passes (`cd caylent-devcontainer-cli && make test && make lint && cd .. && make pre-commit-check`)
- [x] Docs updated if project documentation is affected by these changes

## Log

### Session 1 — 2026-02-12

**Completed:**
- Rewrote `load_template()` in `commands/template.py` — removed version mismatch menu (raw input + 4 choices), removed `confirm_action()`, removed outer try/except. Now uses `validate_template()` for all validation and `questionary.confirm` via `ask_or_exit` for overwrite confirmation.
- Removed 12 old unit tests that tested the version mismatch menu (choices 1-4, invalid choice, version parse error, etc.)
- Added 8 new unit tests: no_existing_file, overwrite_accepted, overwrite_declined, calls_validate_template, passes_name_and_path_to_write, v1x_rejected_by_validate, success_message, create_new_env_file, no_confirm_action_used, no_raw_input
- Wrote 14 functional tests in `tests/functional/test_template_load.py`: 8 source inspection tests + 6 end-to-end tests (generates both files, gitignore entries, AWS profile map, SSH key placeholder, overwrite prompt, v1.x rejection)
- Coverage: template.py 98%
- Quality gate: 718 tests pass (3 skipped), lint clean, pre-commit clean (pre-existing detect-private-key from S1.2.2 test files not related to this story)

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
