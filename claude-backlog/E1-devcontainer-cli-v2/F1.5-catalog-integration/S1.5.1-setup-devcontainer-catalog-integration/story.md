# [S1.5.1] Setup-DevContainer Catalog Integration

## Work Unit Metadata

| Field | Value |
|-------|-------|
| **Type** | Story |
| **Number** | S1.5.1 |
| **Status** | in-queue |
| **Parent** | F1.5 — Catalog Integration |
| **Epic** | E1 — Caylent DevContainer CLI v2.0.0 |

## Description

Integrate the catalog pipeline into setup-devcontainer so that all setup paths use catalog-based collection discovery, selection, and file copying. Whether or not a specialized catalog URL is configured, setup-devcontainer always flows through the catalog pipeline — there is no separate "copy .devcontainer/" path.

**Development Workflow (TDD):**
1. Write the test — verify it fails (red)
2. Write the code — verify the test passes (green)
3. Achieve 90%+ unit test coverage
4. Write functional tests for end-to-end behavior
5. Fix linting/formatting: `cd caylent-devcontainer-cli && make lint && make format`

## Definition of Ready

- S1.4.3 (catalog shared functions) must be complete
- S1.3.4 (setup-devcontainer rewrite) must be complete

## Full Requirements

### When DEVCONTAINER_CATALOG_URL is NOT Set

1. Clone default catalog (this repo) using DEFAULT_CATALOG_URL
2. Discover collections — default catalog has one collection: default
3. Since only one collection, select automatically (no browsing UI)
4. Copy collection files + common assets to project's .devcontainer/
5. Continue with interactive setup (template selection/creation, env var prompts)

### When DEVCONTAINER_CATALOG_URL IS Set

1. Present source selection prompt:
```
DevContainer configuration sources available:

> Default Caylent General DevContainer
  Browse specialized configurations from catalog
```
2. If "Default" selected: clone default catalog, auto-select default, copy and continue
3. If "Browse catalog" selected:
   a. Clone specialized catalog from DEVCONTAINER_CATALOG_URL
   b. Validate catalog structure
   c. Discover collections, parse metadata
   d. Build flat list sorted A-Z with default first
   e. Present searchable/scrollable selection list using questionary
   f. Display full metadata and ask "Is this correct?"
   g. Copy collection + common assets
   h. Continue with interactive setup
4. Clean up temp directory (all paths)

### `--catalog-entry <name>` Flag

1. Requires DEVCONTAINER_CATALOG_URL set — exit non-zero if not
2. Clone specialized catalog
3. Find collection by name — exit non-zero if not found
4. Skip source selection and browsing UI
5. Display metadata, "Is this correct?"
6. Copy and continue

### File Copy (All Paths)

Same function used for all paths: `copy_collection_to_project(collection_path, common_assets_path, target_path, catalog_url)`

### Key Files

- `commands/setup.py`
- `commands/setup_interactive.py`
- `utils/catalog.py`

## Acceptance Criteria

- [ ] Without DEVCONTAINER_CATALOG_URL: auto-clones this repo, auto-selects default
- [ ] With DEVCONTAINER_CATALOG_URL: source selection prompt works
- [ ] "Default" selection clones default catalog correctly
- [ ] "Browse catalog" shows searchable selection list
- [ ] Selected collection metadata displayed with confirmation
- [ ] `--catalog-entry` flag skips browsing, selects directly
- [ ] `--catalog-entry` requires DEVCONTAINER_CATALOG_URL (error if not set)
- [ ] `copy_collection_to_project()` used for all paths
- [ ] Temp directories cleaned up in all paths
- [ ] 90% or greater unit test coverage for all new/modified code
- [ ] Functional tests verify end-to-end behavior
- [ ] All existing tests still pass after refactoring
- [ ] Linting and formatting pass (`make lint && make format`)
- [ ] Pre-commit check passes (`cd caylent-devcontainer-cli && make test && make lint && cd .. && make pre-commit-check`)
- [ ] Docs updated if project documentation is affected by these changes

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
