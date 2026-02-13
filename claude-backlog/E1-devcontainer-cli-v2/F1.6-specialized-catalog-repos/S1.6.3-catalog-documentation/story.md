# [S1.6.3] Catalog Documentation

## Work Unit Metadata

| Field | Value |
|-------|-------|
| **Type** | Story |
| **Number** | S1.6.3 |
| **Status** | in-review |
| **Parent** | F1.6 — Specialized Catalog Repos |
| **Epic** | E1 — Caylent DevContainer CLI v2.0.0 |

## Description

Create comprehensive documentation for the DevContainer catalog system. Documentation lives in two places: canonical reference in the Caylent internal catalog repo (README.md and CONTRIBUTING.md), and a brief reference in this repo pointing to the catalog documentation.

**Development Workflow (TDD):**
1. Write the test — verify it fails (red)
2. Write the code — verify the test passes (green)
3. Achieve 90%+ unit test coverage
4. Write functional tests for end-to-end behavior
5. Fix linting/formatting: `cd caylent-devcontainer-cli && make lint && make format`

## Definition of Ready

- S1.6.1 (Caylent internal catalog repo) must be complete
- S1.6.2 (Smarsh client catalog repo) must be complete

## Full Requirements

### README.md Contents (Comprehensive)

The README.md must cover all of the following sections:

1. **What is a DevContainer Catalog?** — Catalog model explanation, relationship between catalogs/collections/common assets/developer templates
2. **Catalog Repo Structure** — Directory layout, `common/devcontainer-assets/` explanation, `catalog-entry.json` full schema, `devcontainer.json` requirements
3. **Creating a New Catalog Repo** — Step-by-step: create repo, create common/, create first collection, validate, push
4. **Adding a New Collection** — Step-by-step: create directory, `catalog-entry.json` with constraints, `devcontainer.json` with `postCreateCommand`, validate
5. **Modifying Common Assets** — Affects ALL collections, recommend testing, suggest versioning/tagging
6. **postCreateCommand Reference** — Exact format, non-WSL/WSL, why source `shell.env` first, why `sudo -E`
7. **Customization Model** — 3 layers: catalog collections, developer templates, `project-setup.sh`
8. **Validation Reference** — Full checks list, how to run, common failures
9. **Distributing Your Catalog** — `DEVCONTAINER_CATALOG_URL`, branch/tag support, auth requirements

### CONTRIBUTING.md

- PR process for new collections
- Required validation before merge
- Naming conventions
- Testing expectations
- Review checklist

### Documentation Locations

1. **Caylent internal catalog repo** (`caylent-solutions/caylent-devcontainer-catalog`) — README.md and CONTRIBUTING.md as canonical reference
2. **Smarsh catalog repo** (`caylent-solutions/smarsh-devcontainer-catalog`) — README.md and CONTRIBUTING.md
3. **This repo** — Brief reference pointing to catalog documentation

### Key Files

- `README.md` and `CONTRIBUTING.md` in both catalog repos
- Brief reference in this repo

## Acceptance Criteria

- [x] Comprehensive `README.md` covering all 9 documentation sections listed above
- [x] `CONTRIBUTING.md` with PR process and review checklist
- [x] Documentation in Caylent internal catalog repo (637-line README.md, 402-line CONTRIBUTING.md — pushed)
- [x] Documentation in Smarsh catalog repo (652-line README.md, 497-line CONTRIBUTING.md — pushed)
- [x] Brief reference added to this repo pointing to catalog docs (DevContainer Catalogs section in README.md)
- [x] All documentation accurate and consistent with implementation (grounded in actual catalog.py validation code)
- [x] 3-layer customization model clearly explained (catalog collections, developer templates, `project-setup.sh`)
- [x] Linting and formatting pass (`make lint && make format`)
- [x] Pre-commit check passes (`cd caylent-devcontainer-cli && make test && make lint && cd .. && make pre-commit-check`)
- [x] Docs updated if project documentation is affected by these changes (main repo README.md updated)
- [x] Removed Smarsh reference from test data in main repo (test_catalog_commands.py)

## Log

### Session 1 — 2026-02-12

**Completed:**
- Wrote comprehensive README.md (637 lines) for Caylent internal catalog covering all 9 sections: catalog concepts, repo structure, creating catalogs, adding collections, modifying common assets, postCreateCommand reference, 3-layer customization model, validation reference, and distribution guide
- Wrote comprehensive CONTRIBUTING.md (402 lines) for Caylent catalog with PR process, naming conventions, validation checks, testing expectations, review checklist
- Wrote comprehensive README.md (652 lines) for Smarsh catalog covering all 9 sections, adapted for private repo with authentication guidance
- Wrote comprehensive CONTRIBUTING.md (497 lines) for Smarsh catalog with authentication section and EKS-focused testing
- Added "DevContainer Catalogs" section to main repo README.md with key concepts, catalog commands, and pointer to catalog repo docs
- Fixed test data in test_catalog_commands.py: renamed "smarsh-java" to "acme-java" to remove Smarsh references from this repo
- All docs pushed to both external catalog repos
- All 1028 tests pass, lint clean, pre-commit clean

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
