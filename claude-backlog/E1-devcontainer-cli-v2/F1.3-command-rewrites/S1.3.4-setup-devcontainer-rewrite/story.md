# [S1.3.4] Setup-DevContainer Rewrite

## Work Unit Metadata

| Field | Value |
|-------|-------|
| **Type** | Story |
| **Number** | S1.3.4 |
| **Status** | in-review |
| **Parent** | F1.3 — Command Rewrites |
| **Epic** | E1 — Caylent DevContainer CLI v2.0.0 |

## Description

Rewrite the setup-devcontainer command for v2.0.0. The "clone repo, copy .devcontainer/" step is replaced by the unified catalog pipeline (catalog integration is S1.5.1). This story implements the setup-devcontainer logic WITHOUT the catalog integration, focusing on configuration detection, replace/no-replace flow, validation, and interactive setup.

**Development Workflow (TDD):**
1. Write the test — verify it fails (red)
2. Write the code — verify the test passes (green)
3. Achieve 90%+ unit test coverage
4. Write functional tests for end-to-end behavior
5. Fix linting/formatting: `cd caylent-devcontainer-cli && make lint && make format`

## Definition of Ready

- S1.1.5 (project file generation) must be complete
- S1.1.6 must be complete
- S1.3.1 (universal UI requirements) must be complete

## Full Requirements

### .tool-versions

- Create .tool-versions as empty file if it does not already exist
- Do not add any runtime entries

### Existing Configuration Detection

When .devcontainer/ already exists:
- Inform user that devcontainer config files already exist
- Show current version from VERSION file (if exists; if not, "version unknown")
- If .devcontainer/catalog-entry.json exists, show collection name and catalog URL
- Inform user they will be asked whether to replace

### Python Notice

If .tool-versions exists AND contains a Python entry:
- Append to replacement prompt: recommended config manages Python through features in devcontainer.json, .devcontainer/.devcontainer.postcreate.sh, and devcontainer-functions.sh
- If they want to follow recommendation, choose yes when prompted to replace

### User Decision: Replace

- Display notification explaining: existing files overwritten, review git changes before building, close remote connection if project auto-starts devcontainer, open from OS file explorer not recent folders, merge back customizations, test before pushing, rebuild devcontainer (possibly without cache)
- Require explicit keypress acknowledgement
- Proceed with catalog selection and setup

### User Decision: Do Not Replace

- Leave all .devcontainer/ files unchanged
- Continue with interactive setup for environment files only

### File Validation (Both Paths) — Informational Only

After replace/no-replace, if both project files exist, run shared validation (Steps 0-3). Unlike code command, setup-devcontainer does NOT prompt to fix. Instead displays issues as informational: "The following configuration issues were detected... Completing this setup will regenerate your project configuration from the selected template and resolve these issues."

### File Generation

After interactive setup completes, write_project_files() generates both files.

### Key Files to Modify

- `caylent-devcontainer-cli/src/caylent_devcontainer_cli/commands/setup.py` — setup-devcontainer command logic
- `caylent-devcontainer-cli/src/caylent_devcontainer_cli/commands/setup_interactive.py` — interactive setup flow
- `caylent-devcontainer-cli/tests/unit/` — add unit tests
- `caylent-devcontainer-cli/tests/functional/` — add functional tests

## Acceptance Criteria

- [x] .tool-versions created as empty file when missing
- [x] Existing config detection shows version and catalog entry info
- [x] Python notice displayed when .tool-versions contains Python entry
- [x] Replace flow with full notification and keypress acknowledgement
- [x] No-replace flow continues with env files only
- [x] Shared validation (Steps 0-3) runs in informational-only mode
- [x] File generation via write_project_files() after interactive setup
- [x] 90%+ unit test coverage, functional tests pass
- [x] Linting and formatting pass (`make lint && make format`)
- [x] Pre-commit check passes (`cd caylent-devcontainer-cli && make test && make lint && cd .. && make pre-commit-check`)
- [x] Docs updated if project documentation is affected by these changes

## Log

### Session 1 — 2026-02-12

**Completed:**
- Rewrote setup.py with new flow: config detection, replace/no-replace, .tool-versions as empty file, informational validation, Python notice
- Removed clone/copy logic (REPO_URL, clone_repo, copy_devcontainer_files, show_manual_instructions, ensure_gitignore_entries, check_and_create_tool_versions)
- Removed --manual and --ref flags from register_command
- Updated setup_interactive.py to remove check_and_create_tool_versions reference from apply_template
- Wrote 32 unit tests for new setup functions (TestRegisterCommand, TestEnsureToolVersions, TestHasPythonEntry, TestShowExistingConfig, TestShowPythonNotice, TestPromptReplaceDecision, TestShowReplaceNotification, TestRunInformationalValidation, TestHandleSetup)
- Updated test_apply_template.py and test_json_newlines.py to remove check_and_create_tool_versions patches
- Rewrote functional tests (test_setup_command.py, test_setup_version.py, test_cli.py) to test new behavior
- Updated README.md to remove --manual and --ref documentation
- Quality gate: 477 unit + 219 functional = 696 total, 0 failures, 96% coverage, lint clean, pre-commit clean

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
