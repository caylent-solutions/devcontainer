# [S1.1.5] Project File Generation

## Work Unit Metadata

| Field | Value |
|-------|-------|
| **Type** | Story |
| **Number** | S1.1.5 |
| **Status** | in-queue |
| **Parent** | F1.1 — Core DRY Refactoring & Removals |
| **Epic** | E1 — Caylent DevContainer CLI v2.0.0 |

## Description

Implement the unified `write_project_files()` function that generates all project configuration files from template data. This single function replaces all scattered file generation logic and ensures devcontainer-environment-variables.json and shell.env are always generated together with consistent metadata, sorted keys, and sensitive file protection.

**Development Workflow (TDD):**
1. Write the test — verify it fails (red)
2. Write the code — verify the test passes (green)
3. Achieve 90%+ unit test coverage
4. Write functional tests for end-to-end behavior
5. Fix linting/formatting: `cd caylent-devcontainer-cli && make lint && make format`

## Definition of Ready

- S1.1.1 must be complete (depends on write_json_file, file path constants)

## Full Requirements

### B. Project File Generation (Spec Section B)

**`write_project_files(project_root, template_data, template_name, template_path)`** — Single function in `utils/fs.py` that:

1. Writes `devcontainer-environment-variables.json` with metadata and sorted keys
2. Immediately generates `shell.env` with metadata comment header and sorted exports
3. Writes `.devcontainer/aws-profile-map.json` if AWS is enabled
4. Writes `.devcontainer/ssh-private-key` if GIT_AUTH_METHOD=ssh
5. Ensures .gitignore entries for all sensitive files

Every command that produces project files must call this one function: setup-devcontainer, template load, and any validation flow that regenerates files.

### Metadata Requirements

**shell.env header:**
```bash
# Template: <template_name>
# Template Path: <template_path>
# CLI Version: <cli_version>
# Generated: <ISO 8601 timestamp>
```

**devcontainer-environment-variables.json:**
```json
{
  "template_name": "<template_name>",
  "template_path": "<template_path>",
  "cli_version": "<cli_version>",
  "containerEnv": { ... }
}
```

### Sorting Requirements

- In `shell.env`: all export lines sorted ascending alphabetically (A-Z) by variable name
- In `devcontainer-environment-variables.json`: all keys under containerEnv sorted ascending alphabetically (A-Z)

### Static Container Values

Generated into `shell.env`, NOT stored in templates:

- `DEVCONTAINER=true`
- `BASH_ENV=${containerWorkspaceFolder}/shell.env`
- `NO_PROXY=localhost,127.0.0.1,.local`
- `no_proxy=localhost,127.0.0.1,.local`
- Dynamic PATH with asdf shims and .localscripts
- `unset GIT_EDITOR`

When `HOST_PROXY=true`, also generate:

- `HTTP_PROXY=${HOST_PROXY_URL}`
- `HTTPS_PROXY=${HOST_PROXY_URL}`
- `http_proxy=${HOST_PROXY_URL}`
- `https_proxy=${HOST_PROXY_URL}`

### Sensitive File Protection (.gitignore entries)

The function must ensure the following entries exist in the project's `.gitignore`:

- `shell.env`
- `devcontainer-environment-variables.json`
- `.devcontainer/aws-profile-map.json`
- `.devcontainer/ssh-private-key`

### Key Files to Modify

- `caylent-devcontainer-cli/src/caylent_devcontainer_cli/utils/fs.py` — add `write_project_files()`
- All commands that currently generate project files — refactor to call `write_project_files()`
- `caylent-devcontainer-cli/tests/unit/test_fs.py` — add unit tests
- `caylent-devcontainer-cli/tests/functional/` — add functional tests

## Acceptance Criteria

- [ ] `write_project_files()` implemented in `utils/fs.py`
- [ ] Generates `devcontainer-environment-variables.json` with metadata and sorted containerEnv keys
- [ ] Generates `shell.env` with metadata comment header and sorted exports
- [ ] Writes `aws-profile-map.json` when `AWS_CONFIG_ENABLED=true`
- [ ] Writes `ssh-private-key` when `GIT_AUTH_METHOD=ssh`
- [ ] Ensures .gitignore entries for all 4 sensitive files
- [ ] Static container values generated correctly in `shell.env`
- [ ] Proxy variables generated when `HOST_PROXY=true`
- [ ] Both files always generated together (never one without the other)
- [ ] All commands that produce project files call `write_project_files()`
- [ ] 90% or greater unit test coverage for all new/modified code
- [ ] Functional tests verify end-to-end behavior
- [ ] All existing tests still pass after refactoring
- [ ] Linting and formatting pass (`make lint && make format`)
- [ ] Pre-commit check passes (`cd caylent-devcontainer-cli && make test && make lint && cd .. && make pre-commit-check`)
- [ ] Docs updated if project documentation is affected by these changes

## Log

_(No work has been done yet — this is the first session)_

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
