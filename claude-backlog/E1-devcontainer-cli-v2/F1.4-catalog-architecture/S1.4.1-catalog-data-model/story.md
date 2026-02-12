# [S1.4.1] Catalog Data Model

## Work Unit Metadata

| Field | Value |
|-------|-------|
| **Type** | Story |
| **Number** | S1.4.1 |
| **Status** | in-queue |
| **Parent** | F1.4 — Catalog Architecture |
| **Epic** | E1 — Caylent DevContainer CLI v2.0.0 |

## Description

Define and validate the catalog data model. No CLI code changes — this is the schema/structure definition and validation logic.

**Development Workflow (TDD):**
1. Write the test — verify it fails (red)
2. Write the code — verify the test passes (green)
3. Achieve 90%+ unit test coverage
4. Write functional tests for end-to-end behavior
5. Fix linting/formatting: `cd caylent-devcontainer-cli && make lint && make format`

## Definition of Ready

- No dependencies

## Full Requirements

### Unified Catalog Model

All devcontainer configuration sources follow the same catalog repo structure. The CLI always processes repos as catalogs — no special-casing for "default" vs "specialized."

| Source | URL | When Used |
|---|---|---|
| Default catalog (this repo) | Hardcoded as DEFAULT_CATALOG_URL | When DEVCONTAINER_CATALOG_URL not set |
| Specialized catalog (remote) | DEVCONTAINER_CATALOG_URL | When ENV var is set |

### Required Catalog Layout

```
catalog-repo/
  common/
    devcontainer-assets/
      .devcontainer.postcreate.sh      # Shared postcreate (required)
      devcontainer-functions.sh         # Shared functions (required)
      project-setup.sh                  # Template project-setup (required)
  collections/
    <collection-name>/
      catalog-entry.json                # Marker + metadata (required)
      devcontainer.json                 # DevContainer config (required)
      VERSION                           # Version identifier (required)
      ...                               # Other collection-specific files
```

Collections can be nested at any depth. CLI discovers them by recursively scanning for catalog-entry.json.

### catalog-entry.json Schema

Required fields:
- `name` (string): Lowercase, dash-separated, no spaces, min 2 chars. Pattern: `^[a-z][a-z0-9-]*[a-z0-9]$`. Must be unique across catalog.
- `description` (string): Non-empty.

Optional fields:
- `tags` (array of strings): Categories, lowercase dash-separated
- `maintainer` (string): Team or person responsible
- `min_cli_version` (string): Minimum CLI version (semver)

### Collection Rules

- Must contain catalog-entry.json and devcontainer.json and VERSION
- Must NOT contain files with same name as files in common/devcontainer-assets/ (prevents conflicts)
- postCreateCommand in devcontainer.json must call .devcontainer/.devcontainer.postcreate.sh

### ENV Var: DEVCONTAINER_CATALOG_URL

- Format: `<git-clone-url>[@<branch-or-tag>]`
- Set on developer's host machine (not inside devcontainer)
- Examples: `https://github.com/org/repo.git`, `https://github.com/org/repo.git@v2.0`, `git@github.com:org/repo.git@main`

### Key Files to Modify

- Define data classes/types in a new module like `utils/catalog.py` or `models/catalog.py`
- `caylent-devcontainer-cli/tests/unit/` — add unit tests
- `caylent-devcontainer-cli/tests/functional/` — add functional tests

## Acceptance Criteria

- [ ] Catalog data model defined (Python dataclasses or similar)
- [ ] catalog-entry.json schema validation implemented
- [ ] Name pattern regex validation: `^[a-z][a-z0-9-]*[a-z0-9]$`
- [ ] Required fields validation (name, description)
- [ ] Optional fields validation (tags format, min_cli_version semver)
- [ ] Collection structure validation (required files present)
- [ ] File conflict detection logic (collection vs common assets)
- [ ] postCreateCommand validation (must call postcreate script)
- [ ] 90% or greater unit test coverage for all new/modified code
- [ ] Functional tests verify end-to-end behavior
- [ ] All existing tests still pass after refactoring
- [ ] Linting and formatting pass (`make lint && make format`)

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
