# [S1.3.1] Universal UI Requirements

## Work Unit Metadata

| Field | Value |
|-------|-------|
| **Type** | Story |
| **Number** | S1.3.1 |
| **Status** | complete |
| **Parent** | F1.3 — Command Rewrites |
| **Epic** | E1 — Caylent DevContainer CLI v2.0.0 |

## Description

Implement universal UI patterns for input confirmation and questionary null handling across all interactive commands. Every command that accepts user input must give the user the opportunity to review and re-enter their input. All questionary prompts must use the shared ask_or_exit() wrapper.

**Development Workflow (TDD):**
1. Write the test — verify it fails (red)
2. Write the code — verify the test passes (green)
3. Achieve 90%+ unit test coverage
4. Write functional tests for end-to-end behavior
5. Fix linting/formatting: `cd caylent-devcontainer-cli && make lint && make format`

## Definition of Ready

- S1.1.3 must be complete (depends on ask_or_exit, exit_cancelled)

## Full Requirements

### Input Confirmation

Every command that accepts user input must give the user the opportunity to review and re-enter their input.

After each input is received:
1. Display the entered value back to the user:
   - Single-line text: Show the value as entered
   - Password fields (e.g., GIT_TOKEN): Show masked value (e.g., `****...****`) or length
   - Select fields: Show the selected option
   - Multi-line text (AWS profiles): Show the parsed/formatted result, not raw input
   - File path inputs (SSH key): Show the key fingerprint from `ssh-keygen -l -f <keyfile>`
2. Ask: "Is this correct?" (yes/no)
3. If no: re-prompt for the same input
4. If yes: proceed to the next prompt

This should be implemented as a reusable pattern/wrapper that all interactive commands use. The pattern should be easy to apply to any questionary prompt type (text, select, password, etc.).

### Questionary Null Handling

All questionary prompts must use the shared ask_or_exit() wrapper. If user cancels (Ctrl+C or null return), exit cleanly with exit_cancelled().

### Key Files to Modify

- `caylent-devcontainer-cli/src/caylent_devcontainer_cli/utils/ui.py` — input confirmation pattern, reusable wrappers
- `caylent-devcontainer-cli/src/caylent_devcontainer_cli/commands/setup_interactive.py` — apply universal UI patterns
- `caylent-devcontainer-cli/tests/unit/` — add unit tests
- `caylent-devcontainer-cli/tests/functional/` — add functional tests

## Acceptance Criteria

- [x] Input confirmation pattern implemented as reusable utility
- [x] Handles all input types: text, password, select, multi-line, file path
- [x] Password fields display masked value
- [x] File path inputs display SSH key fingerprint
- [x] "Is this correct?" re-prompt loop works correctly
- [x] All questionary prompts use ask_or_exit() wrapper
- [x] Ctrl+C and null returns handled with exit_cancelled()
- [x] 90%+ unit test coverage, functional tests pass
- [x] Linting and formatting pass (`make lint && make format`)
- [x] Pre-commit check passes (`cd caylent-devcontainer-cli && make test && make lint && cd .. && make pre-commit-check`)
- [x] Docs updated if project documentation is affected by these changes

## Log

### Session 1 — 2026-02-12

**Completed:**
- Implemented `prompt_with_confirmation(prompt_fn, display_fn)` in `utils/ui.py` — reusable confirmation loop for any questionary prompt type
- Implemented `mask_password(value)` — masks password for safe display, shows length only
- Implemented `ssh_fingerprint(key_path)` — calls `ssh-keygen -l -f` to get fingerprint for display
- Standardized 13 inconsistent `.ask()` calls to use `ask_or_exit()`:
  - `utils/template.py`: 5 calls in validation functions (removed manual None checks)
  - `commands/setup_interactive.py`: 7 calls in `prompt_aws_profile_map()` and `load_template_from_file()`
  - `commands/code.py`: 1 call in `prompt_upgrade_or_continue()`
  - `commands/template.py`: 2 calls in `prompt_for_missing_vars()`
- Wrote 19 unit tests in `tests/unit/test_prompt_confirmation.py`
- Wrote 13 functional tests in `tests/functional/test_prompt_confirmation.py` (including source inspection tests)
- Coverage: 95% on `utils/ui.py`
- Quality gate: 481 unit tests (3 skipped), 178 functional tests, lint clean, pre-commit clean

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
