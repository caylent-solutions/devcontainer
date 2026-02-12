# [S2.2.1] GitHub Actions Mirror Workflow

## Work Unit Metadata

| Field | Value |
|-------|-------|
| **Type** | Story |
| **Number** | S2.2.1 |
| **Status** | in-queue |
| **Parent** | F2.2 — Mirror Automation |
| **Epic** | E2 — ECR Public Image Mirror |

## Description

Create a GitHub Actions workflow that mirrors the Microsoft DevContainer base image from MCR to ECR Public on a semi-monthly schedule. The workflow checks for upstream changes, authenticates via OIDC, pushes updated images, updates devcontainer.json files, and creates a pull request when changes are detected.

## Definition of Ready

- S2.1.2 must be complete (need IAM role ARN)

## Full Requirements

### Workflow File

**`.github/workflows/mirror-devcontainer-image.yml`**

Trigger: Scheduled cron semi-monthly (1st and 15th) + manual workflow_dispatch

```yaml
name: Mirror DevContainer Base Image
on:
  schedule:
    - cron: '0 6 1,15 * *'  # 6 AM UTC on 1st and 15th
  workflow_dispatch:
permissions:
  id-token: write    # Required for OIDC
  contents: write    # Required for PR creation
  pull-requests: write
```

### Step 1: Check for Upstream Image Update

- Pull manifest digest from `mcr.microsoft.com/devcontainers/base:noble` (using `docker manifest inspect` or `crane digest`)
- Compare against digest currently in ECR Public (using `crane digest`)
- If digests match: skip, exit successfully
- If differ or ECR image doesn't exist: continue

### Step 2: Authenticate to ECR Public via OIDC

- Use `aws-actions/configure-aws-credentials` with IAM role ARN
- Authenticate Docker: `aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin public.ecr.aws`

### Step 3: Pull, Tag, and Push

- Pull `mcr.microsoft.com/devcontainers/base:noble`
- Tag as `public.ecr.aws/<ALIAS>/devcontainer-base:noble`
- Also tag with upstream digest as version tag (e.g., `noble-<short-sha>`)
- Push both tags

### Step 4: Update devcontainer.json Files

- Update image field in both `.devcontainer/devcontainer.json` and `collections/default/devcontainer.json`
- Only update if image reference has changed

### Step 5: Create Pull Request

- If either devcontainer.json updated, create PR with title "chore: update devcontainer base image to latest mirror" and body with upstream digest, date, release notes link
- If no changes: no PR

### Tools

- `crane` (google/go-containerregistry) for digest comparison
- Docker for pull/tag/push
- `gh` CLI for PR creation

### Key Files

- `.github/workflows/mirror-devcontainer-image.yml` (new)

### Shell Requirements

- All `run` steps must use `shell: bash`

## Acceptance Criteria

- [ ] Workflow file created at `.github/workflows/mirror-devcontainer-image.yml`
- [ ] Cron schedule: 1st and 15th of month at 6 AM UTC
- [ ] Manual workflow_dispatch trigger available
- [ ] OIDC permissions configured (id-token, contents, pull-requests)
- [ ] Digest comparison correctly detects upstream changes
- [ ] Skips push when digests match
- [ ] OIDC authentication to ECR Public works
- [ ] Image pulled, tagged (noble + version tag), and pushed
- [ ] devcontainer.json files updated only when changed
- [ ] PR created automatically with correct title and body
- [ ] All run steps use `shell: bash`
- [ ] `crane` installed for digest comparison
- [ ] 90%+ test coverage where applicable (workflow testing may be limited)
- [ ] Linting/formatting pass
- [ ] Pre-commit check passes (`cd caylent-devcontainer-cli && make test && make lint && cd .. && make pre-commit-check`)
- [ ] Docs updated if project documentation is affected by these changes

## Log

_(No work has been done yet)_

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
