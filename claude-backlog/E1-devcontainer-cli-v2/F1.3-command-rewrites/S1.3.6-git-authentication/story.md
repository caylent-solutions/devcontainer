# [S1.3.6] Git Authentication

## Work Unit Metadata

| Field | Value |
|-------|-------|
| **Type** | Story |
| **Number** | S1.3.6 |
| **Status** | in-queue |
| **Parent** | F1.3 — Command Rewrites |
| **Epic** | E1 — Caylent DevContainer CLI v2.0.0 |

## Description

Implement the two git authentication methods (token and SSH) in the postcreate script. Each method has distinct behavior for credential setup, file creation, and connectivity verification. Both methods share a common git configuration block. GIT_AUTH_METHOD must be set or the postcreate exits non-zero.

**Development Workflow (TDD):**
1. Write the test — verify it fails (red)
2. Write the code — verify the test passes (green)
3. Achieve 90%+ unit test coverage
4. Write functional tests for end-to-end behavior
5. Fix linting/formatting: `cd caylent-devcontainer-cli && make lint && make format`

## Definition of Ready

- S1.1.5 (project file generation) must be complete

## Full Requirements

### Two Methods: Token and SSH

### Token Method (GIT_AUTH_METHOD=token)

- GIT_TOKEN required in template and project files
- ssh_private_key must NOT exist in template
- .devcontainer/ssh-private-key must NOT exist in project

Postcreate behavior (token):
- Create ~/.netrc with machine <GIT_PROVIDER_URL>, login <GIT_USER>, password <GIT_TOKEN>
- Set ~/.netrc permissions to 600
- .gitconfig includes [credential] helper = store

### SSH Method (GIT_AUTH_METHOD=ssh)

- GIT_TOKEN must NOT exist in template or project files
- ssh_private_key must exist in template
- .devcontainer/ssh-private-key written to project (gitignored)

Postcreate behavior (SSH):
1. Ensure openssh-client installed (apt-get install -y openssh-client)
2. Create ~/.ssh/ with permissions 700
3. Copy .devcontainer/ssh-private-key to ~/.ssh/id_private_key
4. Set ~/.ssh/id_private_key permissions to 600
5. Run ssh-keyscan ${GIT_PROVIDER_URL} >> ~/.ssh/known_hosts
6. Create ~/.ssh/config with Host, HostName, User git, IdentityFile, IdentitiesOnly yes
7. Set ~/.ssh/config permissions to 600
8. Verify SSH connectivity: ssh -T git@${GIT_PROVIDER_URL} — exit non-zero on failure
9. Do NOT create ~/.netrc
10. .gitconfig does NOT include credential helper

### Shared Git Config (Both Methods)

```ini
[user]
    name = <GIT_USER>
    email = <GIT_USER_EMAIL>
[core]
    editor = vim
[push]
    autoSetupRemote = true
[safe]
    directory = *
[pager]
    branch = false
    config = false
    diff = false
    log = false
    show = false
    status = false
    tag = false
```

### GIT_PROVIDER_URL Usage

- Token: .netrc machine field uses bare hostname. Git credential URLs use https://<GIT_PROVIDER_URL>.
- SSH: git@<GIT_PROVIDER_URL> for SSH config and connectivity test
- User only provides hostname (e.g., github.com). Protocol never stored.

### GIT_AUTH_METHOD Unset

Exit non-zero with error: "GIT_AUTH_METHOD is required. Please regenerate project files."

### Key Files to Modify

- `.devcontainer/.devcontainer.postcreate.sh` — git authentication logic
- `.devcontainer/devcontainer-functions.sh` — git authentication functions
- `caylent-devcontainer-cli/tests/unit/` — add unit tests
- `caylent-devcontainer-cli/tests/functional/` — add functional tests

## Acceptance Criteria

- [ ] Token method: ~/.netrc created with correct format and 600 permissions
- [ ] Token method: .gitconfig includes credential helper = store
- [ ] SSH method: openssh-client installed
- [ ] SSH method: SSH key copied, permissions set to 600
- [ ] SSH method: ssh-keyscan runs for GIT_PROVIDER_URL
- [ ] SSH method: ~/.ssh/config created with correct format
- [ ] SSH method: SSH connectivity verified with ssh -T
- [ ] SSH method: no ~/.netrc, no credential helper
- [ ] Shared git config applied for both methods
- [ ] GIT_AUTH_METHOD unset produces clear error
- [ ] GIT_PROVIDER_URL used correctly for each method (hostname only)
- [ ] 90%+ unit test coverage, functional tests pass
- [ ] Linting and formatting pass (`make lint && make format`)
- [ ] Pre-commit check passes (`cd caylent-devcontainer-cli && make test && make lint && cd .. && make pre-commit-check`)

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
