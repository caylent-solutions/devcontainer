# [S1.2.2] Template Create Command

## Work Unit Metadata

| Field | Value |
|-------|-------|
| **Type** | Story |
| **Number** | S1.2.2 |
| **Status** | in-queue |
| **Parent** | F1.2 — Template System |
| **Epic** | E1 — Caylent DevContainer CLI v2.0.0 |

## Description

Implement the `template create` command with a full 17-step interactive creation flow. All prompts use the universal input confirmation pattern (display value, "Is this correct?", re-prompt if no). The command collects all environment configuration, validates inputs, handles conditional prompts based on auth method and proxy settings, and saves the resulting template.

**Development Workflow (TDD):**
1. Write the test — verify it fails (red)
2. Write the code — verify the test passes (green)
3. Achieve 90%+ unit test coverage
4. Write functional tests for end-to-end behavior
5. Fix linting/formatting: `cd caylent-devcontainer-cli && make lint && make format`

## Definition of Ready

- S1.2.1 (template validation system) must be complete
- S1.1.6 must be complete
- S1.3.1 must be complete

## Full Requirements

### Interactive Creation Flow — Full Prompt Sequence (17 Steps)

All prompts use the universal input confirmation pattern (display value, "Is this correct?", re-prompt if no).

1. **AWS config enabled** — Select: true, false. Default: true
2. **Default Git branch** — Text, default: main, non-empty
3. **Default Python version** — Text, default: 3.12.9, non-empty
4. **Developer name** — Text, no default, non-empty
5. **Git provider URL** — Text, default: github.com, hostname only (no protocol prefix, must contain at least one dot)
6. **Git authentication method** — Select: Personal Access Token (default), SSH Key
7. **Git username** — Text, no default, non-empty
8. **Git email** — Text, no default, non-empty
9. **Git token** — Password field, no default, non-empty — only if token method
10. **SSH private key path** — File path with full validation (see SSH Key Input constraints). On success, read file contents and store as ssh_private_key in template. — only if SSH method
11. **Extra APT packages** — Text, default: "", may be empty
12. **Pager** — Select: cat, less, more, most. Default: cat
13. **AWS output format** — Select: json, table, text, yaml. Default: json — only if AWS enabled
14. **Host proxy** — Select: true, false. Default: false
15. **Host proxy URL** — Text, no default, must start with http:// or https:// — only if host proxy is true
16. **Additional custom environment variables** (free-form loop with conflict detection)
17. **AWS profile map** — existing AWS profile config flow — only if AWS enabled

### SSH Key Input Validation

- Prompt: "Enter the path to your SSH private key file"
- File exists and is readable — error and re-prompt if not
- Normalize line endings — strip \r, ensure trailing newline
- Format check — starts with `-----BEGIN` and contains `-----END`
- Real key validation — run `ssh-keygen -y -f <keyfile>`. If passphrase required: error with guidance. If invalid: show ssh-keygen error. Re-prompt both cases.
- On success: display fingerprint from `ssh-keygen -l -f <keyfile>`, ask "Is this correct?"

### Host Proxy Configuration

- If true: prompt for full URL with example `http://host.docker.internal:3128`, validate starts with http:// or https://, add HOST_PROXY=true and HOST_PROXY_URL=\<input\>
- If false: add HOST_PROXY=false and HOST_PROXY_URL="" (empty string)

### Custom Environment Variables (Free-Form Loop)

- Prompt for key (non-empty), validate no conflict with KNOWN_KEYS, built-in keys, or already-entered custom keys
- On conflict: "The key '\<key\>' already exists (\<source\>). Please enter a different key name."
- Prompt for value (no constraints)
- Display key/value, "Is this correct?" loop
- "Add another?" loop

### Key Files to Modify

- `caylent-devcontainer-cli/src/caylent_devcontainer_cli/commands/template.py` — template create command implementation
- `caylent-devcontainer-cli/src/caylent_devcontainer_cli/utils/ui.py` — UI prompts and input confirmation
- `caylent-devcontainer-cli/src/caylent_devcontainer_cli/utils/template.py` — template saving logic
- `caylent-devcontainer-cli/src/caylent_devcontainer_cli/utils/constants.py` — KNOWN_KEYS, defaults
- `caylent-devcontainer-cli/tests/unit/` — unit tests for creation flow
- `caylent-devcontainer-cli/tests/functional/` — functional tests for end-to-end creation

## Acceptance Criteria

- [ ] Full 17-step interactive creation flow implemented
- [ ] All input constraints enforced (select fields, text fields, password fields)
- [ ] Universal input confirmation pattern on every prompt
- [ ] SSH key validation with all checks (exists, format, ssh-keygen, fingerprint)
- [ ] Host proxy configuration with URL validation
- [ ] Custom environment variable loop with conflict detection against KNOWN_KEYS
- [ ] Template saved with all metadata (template_name, template_path, cli_version)
- [ ] AWS profile map flow working when AWS enabled
- [ ] 90% or greater unit test coverage for all new/modified code
- [ ] Functional tests verify end-to-end behavior
- [ ] All existing tests still pass after refactoring
- [ ] Linting and formatting pass (`make lint && make format`)

## Log

_(No work has been done yet — this story is in-queue)_

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
