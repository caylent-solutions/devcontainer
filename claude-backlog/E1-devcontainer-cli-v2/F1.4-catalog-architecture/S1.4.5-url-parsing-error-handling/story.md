# [S1.4.5] URL Parsing & Error Handling

## Work Unit Metadata

| Field | Value |
|-------|-------|
| **Type** | Story |
| **Number** | S1.4.5 |
| **Status** | in-review |
| **Parent** | F1.4 — Catalog Architecture |
| **Epic** | E1 — Caylent DevContainer CLI v2.0.0 |

## Description

Implement URL parsing logic for DEVCONTAINER_CATALOG_URL and comprehensive error handling for all catalog operations.

**Development Workflow (TDD):**
1. Write the test — verify it fails (red)
2. Write the code — verify the test passes (green)
3. Achieve 90%+ unit test coverage
4. Write functional tests for end-to-end behavior
5. Fix linting/formatting: `cd caylent-devcontainer-cli && make lint && make format`

## Definition of Ready

- S1.4.3 must be complete

## Full Requirements

### URL Parsing Rules

DEVCONTAINER_CATALOG_URL format: `<clone-url>[@<ref>]`

Parsing rules:
- If URL ends with `.git@<ref>`: split on last @ after .git
- If URL ends with `.git`: no ref, use default branch
- If URL has no .git suffix: split on last @ if present, otherwise default branch
- Must distinguish SSH user `git@` from ref delimiter `@v2.0` in URLs like `git@github.com:org/repo.git@v2.0`

Examples:

| Input | Clone URL | Ref |
|---|---|---|
| `https://github.com/org/repo.git` | `https://github.com/org/repo.git` | (default) |
| `https://github.com/org/repo.git@v2.0` | `https://github.com/org/repo.git` | `v2.0` |
| `git@github.com:org/repo.git` | `git@github.com:org/repo.git` | (default) |
| `git@github.com:org/repo.git@v2.0` | `git@github.com:org/repo.git` | `v2.0` |

### Error Handling Table

| Scenario | Behavior |
|---|---|
| DEVCONTAINER_CATALOG_URL not set + --catalog-entry | Exit non-zero: "DEVCONTAINER_CATALOG_URL is not set. The --catalog-entry flag requires a specialized catalog." |
| Clone fails (auth, network, invalid URL) | Exit non-zero with actionable auth failure message |
| No common/devcontainer-assets/ | Exit non-zero: "Catalog repo is missing required directory..." |
| No collections found | Exit non-zero: "No devcontainer collections found..." |
| --catalog-entry name not found | Exit non-zero: "Collection '<name>' not found. Run 'cdevcontainer catalog list'" |
| Collection missing devcontainer.json | Skip in list/browse, report in validate |
| min_cli_version higher than current | Warn and skip in list/browse unless forced |

### Key Files to Modify

- `caylent-devcontainer-cli/src/caylent_devcontainer_cli/utils/catalog.py`
- `caylent-devcontainer-cli/tests/unit/` — add unit tests
- `caylent-devcontainer-cli/tests/functional/` — add functional tests

## Acceptance Criteria

- [x] URL parsing handles all 4 example formats correctly
- [x] SSH git@ prefix distinguished from @ref delimiter
- [x] .git suffix detection works correctly
- [x] Default branch used when no @ref specified
- [x] All 7 error scenarios produce correct error messages
- [x] Errors exit non-zero with actionable messages
- [x] No silent fallbacks on any error
- [x] Edge cases: empty URL, malformed URL, multiple @ signs
- [x] 90% or greater unit test coverage with all URL format edge cases
- [x] Functional tests verify end-to-end behavior
- [x] All existing tests still pass after refactoring
- [x] Linting and formatting pass (`make lint && make format`)
- [x] Pre-commit check passes (`cd caylent-devcontainer-cli && make test && make lint && cd .. && make pre-commit-check`)
- [x] Docs updated if project documentation is affected by these changes

## Log

### Session 1 — 2026-02-12

**Completed:**

URL parsing (all 4 formats) and clone error handling were already implemented in S1.4.3. This story added the remaining error handling functions and catalog list improvements:

**New functions in `utils/catalog.py`:**
- `compare_semver(a, b)` — compare two semver strings, returns -1/0/1
- `check_min_cli_version(min_version, current_version=None)` — check if CLI meets minimum version
- `find_collection_by_name(entries, name)` — look up collection by name, raises SystemExit with actionable message if not found
- `validate_catalog_entry_env(catalog_entry_name)` — validate DEVCONTAINER_CATALOG_URL is set when `--catalog-entry` is used
- Updated `discover_collection_entries()` with `skip_incomplete` parameter to filter out collections missing devcontainer.json

**Updated `commands/catalog.py`:**
- `handle_catalog_list()` now validates common assets (exits non-zero if missing)
- `handle_catalog_list()` now exits non-zero when no collections found
- `handle_catalog_list()` now uses `skip_incomplete=True` to skip collections missing devcontainer.json
- `handle_catalog_list()` now filters by min_cli_version — warns and skips incompatible entries

**All 7 error scenarios covered:**
1. `DEVCONTAINER_CATALOG_URL not set + --catalog-entry` → `validate_catalog_entry_env()` exits with actionable message
2. Clone fails → already handled in S1.4.3 with actionable auth messages
3. No common/devcontainer-assets/ → `handle_catalog_list()` exits non-zero with specific message
4. No collections found → `handle_catalog_list()` exits non-zero with specific message
5. `--catalog-entry` name not found → `find_collection_by_name()` exits with "Run 'cdevcontainer catalog list'"
6. Collection missing devcontainer.json → skipped in list (via `skip_incomplete=True`), reported in validate
7. min_cli_version higher than current → warned and skipped in list

**Tests:**
- Added 11 new unit tests in `test_catalog_commands.py` (TestCompareSemver, TestCheckMinCliVersion, TestFindCollectionByName, TestValidateCatalogEntryEnv)
- Added 3 new unit tests for min_cli_version/common assets in TestHandleCatalogList
- Added 2 new unit tests for `skip_incomplete` in `test_catalog.py`
- Added 9 new functional tests in `test_catalog_commands.py` (TestErrorHandlingEndToEnd)
- Updated all existing tests to mock `validate_common_assets` for new catalog list flow

**Quality gate:** 625 unit + 354 functional = 979 total, 0 failures, 100% coverage on commands/catalog.py, 97% on catalog.py, 96% overall, lint clean, pre-commit clean

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
