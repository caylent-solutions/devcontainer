# [S1.6.2] Smarsh Client Catalog Repo

## Work Unit Metadata

| Field | Value |
|-------|-------|
| **Type** | Story |
| **Number** | S1.6.2 |
| **Status** | in-review |
| **Parent** | F1.6 — Specialized Catalog Repos |
| **Epic** | E1 — Caylent DevContainer CLI v2.0.0 |

## Description

Create the Smarsh client DevContainer catalog repository with two collections: smarsh-java-backend and smarsh-angular-fullstack. Both target Amazon EKS and share the same common/devcontainer-assets/. The catalog is self-contained and independent of the default catalog.

**Development Workflow (TDD):**
1. Write the test — verify it fails (red)
2. Write the code — verify the test passes (green)
3. Achieve 90%+ unit test coverage
4. Write functional tests for end-to-end behavior
5. Fix linting/formatting: `cd caylent-devcontainer-cli && make lint && make format`

## Definition of Ready

- S1.4.2 must be complete
- **Manual prerequisite: human must create `caylent-solutions/smarsh-devcontainer-catalog` GitHub repo before this story can start**

## Full Requirements

### Catalog Structure

```
smarsh-devcontainer-catalog/
  README.md
  CONTRIBUTING.md
  common/
    devcontainer-assets/
      .devcontainer.postcreate.sh
      devcontainer-functions.sh
      project-setup.sh
  collections/
    smarsh-java-backend/
      catalog-entry.json
      devcontainer.json
      VERSION
      ...
    smarsh-angular-fullstack/
      catalog-entry.json
      devcontainer.json
      VERSION
      ...
```

### smarsh-java-backend Collection

**catalog-entry.json:**
```json
{
  "name": "smarsh-java-backend",
  "description": "Java 21 with Spring Boot 3.x, Gradle, and Checkstyle for Smarsh backend services. Targets EKS deployment.",
  "tags": ["java", "spring-boot", "gradle", "backend", "eks", "smarsh"],
  "maintainer": "Caylent Platform Team",
  "min_cli_version": "2.0.0"
}
```

**Scope:** Java 21, Spring Boot 3.x, Gradle, Checkstyle, Spring VS Code extensions, Kubernetes/Helm for EKS, AWS CLI, backend-only.

### smarsh-angular-fullstack Collection

**catalog-entry.json:**
```json
{
  "name": "smarsh-angular-fullstack",
  "description": "Angular 19 with Node.js 22, Java 21, and Spring Boot 3.x for Smarsh fullstack services. Targets EKS deployment.",
  "tags": ["angular", "node", "java", "spring-boot", "fullstack", "eks", "smarsh"],
  "maintainer": "Caylent Platform Team",
  "min_cli_version": "2.0.0"
}
```

**Scope:** Everything in smarsh-java-backend PLUS Node.js 22/npm, Angular CLI, Angular VS Code extensions, ESLint, frontend debug port forwarding (4200, 9229).

### Shared Characteristics

- Both collections target Amazon EKS
- Both are Smarsh-specific
- Both use the same `common/devcontainer-assets/`
- Both devcontainer.json files must have compliant `postCreateCommand`

### Key Output

Files prepared locally, pushed to the external repo after human creates it.

## Acceptance Criteria

- [x] Manual prereq verified: GitHub repo `caylent-solutions/smarsh-devcontainer-catalog` exists (private repo created with matching settings)
- [x] `common/devcontainer-assets/` created with 3 required files (`.devcontainer.postcreate.sh`, `devcontainer-functions.sh`, `project-setup.sh`)
- [N/A] `smarsh-java-backend` collection — **deferred per user instruction** ("just make a default one for now; not the brownfield or greenfield")
- [N/A] `smarsh-angular-fullstack` collection — **deferred per user instruction**
- [x] `collections/default/` collection created with `catalog-entry.json`, `devcontainer.json`, `VERSION` (Smarsh-specific defaults targeting EKS)
- [x] `devcontainer.json` has compliant `postCreateCommand`
- [x] `README.md` and `CONTRIBUTING.md` created (Smarsh-specific)
- [x] Catalog passes `cdevcontainer catalog validate --local .` (1 collection found)
- [x] All files committed and pushed to external repo
- [N/A] 90% or greater unit test coverage — no CLI code changes, external repo only
- [N/A] Linting and formatting — no CLI code changes
- [N/A] Pre-commit check — no CLI code changes
- [N/A] Docs updated — external repo has its own README.md and CONTRIBUTING.md

## Log

### Session 1 — 2026-02-12

**Completed:**
- Created private GitHub repo `caylent-solutions/smarsh-devcontainer-catalog` via `gh repo create`
- Configured repo settings to match source repo: squash-only merges, branch ruleset on main (1 approval, dismiss stale reviews, code owner review, last push approval, thread resolution, non-fast-forward, copilot code review), secret scanning with push protection
- Exception: no required status checks (no GitHub Actions yet), no Integration bypass actor
- Created `common/devcontainer-assets/` with 3 shared files (postcreate, functions, project-setup) — copied from Caylent internal catalog
- Created `collections/default/` with Smarsh-specific catalog-entry.json (EKS/Smarsh tags), devcontainer.json (name: smarsh-devcontainer), VERSION (1.0.0)
- Created README.md and CONTRIBUTING.md with Smarsh-specific documentation
- Validated catalog: `cdevcontainer catalog validate --local .` passes (1 collection)
- Committed and pushed to main

**Scope Change:**
- User instructed "just make a default one for now; not the brownfield or greenfield" — smarsh-java-backend and smarsh-angular-fullstack collections deferred to future work

**Remaining:**
- Specialized collections (smarsh-java-backend, smarsh-angular-fullstack) to be created as separate future stories when Smarsh team requirements are finalized

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
