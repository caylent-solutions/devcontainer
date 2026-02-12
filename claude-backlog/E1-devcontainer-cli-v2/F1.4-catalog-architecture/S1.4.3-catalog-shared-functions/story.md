# [S1.4.3] Catalog Shared Functions

## Work Unit Metadata

| Field | Value |
|-------|-------|
| **Type** | Story |
| **Number** | S1.4.3 |
| **Status** | in-queue |
| **Parent** | F1.4 — Catalog Architecture |
| **Epic** | E1 — Caylent DevContainer CLI v2.0.0 |

## Description

Implement all shared catalog functions as reusable by all consumers (DRY).

**Development Workflow (TDD):**
1. Write the test — verify it fails (red)
2. Write the code — verify the test passes (green)
3. Achieve 90%+ unit test coverage
4. Write functional tests for end-to-end behavior
5. Fix linting/formatting: `cd caylent-devcontainer-cli && make lint && make format`

## Definition of Ready

- S1.4.1 must be complete
- S1.1.1 must be complete

## Full Requirements

### Shared Catalog Functions

Implement all shared catalog functions as reusable by all consumers (DRY).

**`parse_catalog_url(url_with_ref) -> (clone_url, ref)`** — Parses URL + optional ref. See URL Parsing rules in S1.4.5 for full parsing logic.

**`clone_catalog_repo(url_with_ref) -> temp_path`** — Calls parse_catalog_url(), performs shallow clone (`git clone --depth 1 --branch <ref>` or `git clone --depth 1` for default branch) to temp dir, returns path. Handles auth errors with actionable messages.

**`validate_catalog_structure(repo_path) -> list[ValidationError]`** — Validates common assets directory exists with required files.

**`discover_collections(repo_path) -> list[CollectionEntry]`** — Recursively scans for catalog-entry.json, parses metadata, returns sorted list with `default` first then A-Z.

**`validate_collection(collection_path, common_assets_path) -> list[ValidationError]`** — Validates single collection: metadata, file conflicts with common assets, postCreateCommand compliance.

**`validate_catalog(repo_path) -> list[ValidationError]`** — Full validation: structure + all collections + name uniqueness.

**`copy_collection_to_project(collection_path, common_assets_path, target_path, catalog_url)`** — Copies collection files + common assets into target .devcontainer/. Augments catalog-entry.json with catalog_url field before writing. Calls remove_example_files().

### Authentication Failure Handling

If cloning fails, exit non-zero with:
- "Failed to clone the devcontainer catalog from '<url>'"
- "For HTTPS repos: verify a valid token or credential helper is configured."
- "For SSH repos: verify your SSH key is loaded and the host is in known_hosts."
- "You can test access by running: `git ls-remote <url>`"
- Do NOT fall back silently to a different source.

### Key Files to Modify

- `caylent-devcontainer-cli/src/caylent_devcontainer_cli/utils/catalog.py` (new module)
- `caylent-devcontainer-cli/src/caylent_devcontainer_cli/utils/fs.py`
- `caylent-devcontainer-cli/tests/unit/` — add unit tests
- `caylent-devcontainer-cli/tests/functional/` — add functional tests

## Acceptance Criteria

- [ ] parse_catalog_url() correctly parses all URL formats
- [ ] clone_catalog_repo() performs shallow clone to temp dir
- [ ] clone_catalog_repo() handles auth failures with actionable messages
- [ ] validate_catalog_structure() checks common assets exist
- [ ] discover_collections() recursively finds catalog-entry.json files
- [ ] discover_collections() sorts with default first, then A-Z
- [ ] validate_collection() checks metadata, conflicts, postCreateCommand
- [ ] validate_catalog() runs full validation including uniqueness
- [ ] copy_collection_to_project() merges collection + common assets
- [ ] copy_collection_to_project() augments catalog-entry.json with catalog_url
- [ ] Temp directories cleaned up properly
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
