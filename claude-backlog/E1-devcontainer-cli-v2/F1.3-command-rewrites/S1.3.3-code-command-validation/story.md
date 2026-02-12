# [S1.3.3] Code Command Validation (Steps 0-5)

## Work Unit Metadata

| Field | Value |
|-------|-------|
| **Type** | Story |
| **Number** | S1.3.3 |
| **Status** | in-queue |
| **Parent** | F1.3 — Command Rewrites |
| **Epic** | E1 — Caylent DevContainer CLI v2.0.0 |

## Description

Implement the two-stage environment variable validation for the code command (Steps 0-5). When both project files exist, perform validation before launching the IDE. The validation detection logic (Steps 0-3) is shared with setup-devcontainer via a single shared function. The code command diverges on the response by prompting the user to fix issues (Steps 4-5).

**Development Workflow (TDD):**
1. Write the test — verify it fails (red)
2. Write the code — verify the test passes (green)
3. Achieve 90%+ unit test coverage
4. Write functional tests for end-to-end behavior
5. Fix linting/formatting: `cd caylent-devcontainer-cli && make lint && make format`

## Definition of Ready

- S1.3.2 (code command rewrite) must be complete
- S1.2.1 (template validation) must be complete

## Full Requirements

### Shared Validation Detection (Steps 0-3)

Both code and setup-devcontainer share the same validation detection logic via a single shared function. They diverge on the response: code prompts the user to fix (Steps 4-5), setup-devcontainer displays informational only.

#### Step 0 — Check Base Keys

- Verify all EXAMPLE_ENV_VALUES keys exist in both files (respecting conditional requirements)
- If any base keys missing, flag them — project files out of date with current CLI version

#### Step 1 — Validate Required Metadata

- Check both files for required metadata (template_name, template_path, cli_version)
- If metadata missing: notify user, prompt Yes (default, green) to select/create template and regenerate, or No (red) with warning and launch without changes

#### Step 2 — Locate and Validate Template

- Using template_name and template_path from metadata, locate developer template
- If template not found: exit non-zero with error and remediation instructions
- Run validate_template() on loaded template

#### Step 3 — Compare Against Template

- Compare project files against containerEnv values in developer template
- Identify key/value pairs from template missing from either file

### Code Command Response (Steps 4-5)

#### Step 4 — Handle Missing Variables

- Notify user, display which variables are missing, from which files, what values would be added
- Warn about potential build issues

#### Step 5 — User Confirmation

- Option 1 (default): Update config and add missing variables via write_project_files(), read catalog-entry.json for catalog_url and collection name, invoke catalog pipeline to replace .devcontainer/ files (or prompt for catalog source if catalog-entry.json missing)
- Option 2: Only add missing variables to existing files, do not modify .devcontainer/

After either option: launch IDE.

### Two-Stage Environment Variable Validation

- Stage 1: Base Keys (EXAMPLE_ENV_VALUES) — check both files
- Stage 2: Developer Template — locate template, compare all containerEnv keys
- Both stages feed into Steps 4-5

### Key Files to Modify

- `caylent-devcontainer-cli/src/caylent_devcontainer_cli/commands/code.py` — Steps 4-5 response logic
- `caylent-devcontainer-cli/src/caylent_devcontainer_cli/utils/validation.py` — new shared module for Steps 0-3
- `caylent-devcontainer-cli/tests/unit/` — add unit tests
- `caylent-devcontainer-cli/tests/functional/` — add functional tests

## Acceptance Criteria

- [ ] Shared validation detection function (Steps 0-3) implemented
- [ ] Step 0: base key check against EXAMPLE_ENV_VALUES with conditional logic
- [ ] Step 1: metadata validation with prompt for regeneration
- [ ] Step 2: template location and validation
- [ ] Step 3: template comparison detecting missing keys
- [ ] Step 4: clear display of missing variables with file sources
- [ ] Step 5: two-option prompt (update config + catalog, or just add variables)
- [ ] Two-stage validation (base keys + template comparison) working
- [ ] Shared function reusable by setup-devcontainer (informational mode)
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
