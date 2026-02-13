# [S1.5.2] Code Command Catalog Integration

## Work Unit Metadata

| Field | Value |
|-------|-------|
| **Type** | Story |
| **Number** | S1.5.2 |
| **Status** | in-review |
| **Parent** | F1.5 — Catalog Integration |
| **Epic** | E1 — Caylent DevContainer CLI v2.0.0 |

## Description

Integrate the catalog pipeline into the code command so that when Step 5 option 1 needs to replace .devcontainer/ files, it uses catalog-entry.json to determine the catalog source and invokes the catalog pipeline for replacement. Pre-catalog projects that lack catalog-entry.json are handled by prompting the user to select a catalog source.

**Development Workflow (TDD):**
1. Write the test — verify it fails (red)
2. Write the code — verify the test passes (green)
3. Achieve 90%+ unit test coverage
4. Write functional tests for end-to-end behavior
5. Fix linting/formatting: `cd caylent-devcontainer-cli && make lint && make format`

## Definition of Ready

- S1.4.3 (catalog shared functions) must be complete
- S1.3.3 (code command validation) must be complete

## Full Requirements

### Code Command Normal Flow

No changes to code command's normal flow — it operates on existing project files regardless of catalog source.

### Step 5 Option 1: Replace .devcontainer/ Files

When code Step 5 option 1 (from S1.3.3) needs to replace .devcontainer/ files:

1. Read `.devcontainer/catalog-entry.json` to determine `catalog_url` and collection `name`
2. If `catalog-entry.json` exists: invoke catalog pipeline (`clone_catalog_repo(catalog_url)` -> find matching collection by name -> `copy_collection_to_project()`) to replace and upgrade .devcontainer/ config files
3. If `catalog-entry.json` missing (pre-catalog project): prompt user to select a catalog source using the same flow as setup-devcontainer
4. Display replacement notification (same as "User Decision: Replace")
5. Require keypress to continue

### catalog-entry.json Lifecycle

`.devcontainer/catalog-entry.json` is committed to git (NOT gitignored) by `copy_collection_to_project()` during setup-devcontainer. This file tracks which catalog and collection the project was set up from.

### Key Files

- `commands/code.py`
- `utils/catalog.py`

## Acceptance Criteria

- [x] Step 5 option 1 reads `catalog-entry.json` for `catalog_url` and `name`
- [x] Catalog pipeline invoked correctly to replace .devcontainer/
- [x] Pre-catalog projects (missing `catalog-entry.json`) prompt for catalog source
- [x] Replacement notification displayed
- [x] Keypress acknowledgement required
- [x] `catalog-entry.json` NOT in `.gitignore` (committed to repo)
- [x] 90% or greater unit test coverage for all new/modified code
- [x] Functional tests verify end-to-end behavior
- [x] All existing tests still pass after refactoring
- [x] Linting and formatting pass (`make lint && make format`)
- [x] Pre-commit check passes (`cd caylent-devcontainer-cli && make test && make lint && cd .. && make pre-commit-check`)
- [x] Docs updated if project documentation is affected by these changes

## Log

### Session 1 — 2026-02-12

**Completed:**
- Implemented `_replace_devcontainer_files(project_root)` — dispatches to catalog-entry.json path or setup-devcontainer flow
- Implemented `_replace_from_catalog_entry(project_root, catalog_entry_path)` — reads catalog-entry.json, clones catalog, finds collection, copies files with cleanup
- Updated `_handle_missing_metadata(project_root)` — "Yes" path calls `interactive_setup()` from setup.py
- Updated `_handle_missing_variables()` Option 1 — calls `_replace_devcontainer_files()` after writing project files
- Added `import json` and catalog constants to code.py imports
- Wrote 14 new unit tests: TestHandleMissingMetadataYes (3), TestReplaceDevcontainerFiles (4), TestReplaceFromCatalogEntry (7)
- Updated existing Option 1 test to mock and verify `_replace_devcontainer_files` call
- 97% unit test coverage on code.py (4 uncovered lines are pre-existing, unrelated to S1.5.2)
- Updated MANUAL_TESTING.md with Test 13 for code command catalog integration
- All 1021 tests pass, lint clean, pre-commit clean

**Remaining:**
- Human review and approval

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
