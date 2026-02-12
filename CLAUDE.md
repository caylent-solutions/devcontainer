# Engineering and Automation Standards

This document defines the coding standards, automation principles, and operational guidelines for the ea-discovery-case-service project. Claude Code will automatically reference these rules when working on this codebase.

---

## Core Principles

### Never Assume Success - Always Verify

**All results must be verified by agents and reviewed/approved by humans.**

- **Never assume any operation succeeded** - always verify the result
- Read files after writing them to confirm content matches what was intended
- Run commands and check output to verify expected behavior
- If delegating to another agent or tool, verify the delegated work completed successfully
- Test code after writing it to ensure it works as expected
- **All results must be:**
  1. Verified by the agent through actual checks
  2. Reviewed and approved by a human developer

**Verification Requirements:**
- After writing a file, read it back to confirm contents
- After running a command, check exit codes and output
- After making changes, run tests to verify behavior
- After delegating work, verify the delegation completed
- Document verification steps in work logs

### Evidence-Based Communication

**Never make speculative claims about benefits or performance without concrete data.**

- **Never quantify benefits in percentages** without measurement data (e.g., "30% faster", "50% reduction")
- **Never estimate time improvements** without benchmarks (e.g., "reduces latency by 2 seconds", "saves 5 minutes")
- **Never claim performance gains** without profiling or testing
- **Never assert resource savings** without metrics (e.g., "uses 40% less memory")

**When discussing benefits or performance:**
- Use qualitative descriptions instead of quantitative claims
- State "can improve" rather than "improves by X%"
- Use "potentially faster" rather than "X times faster"
- Avoid numbers unless backed by actual measurements
- If you have data, cite the source and measurement conditions

**Examples:**

❌ **Speculative (Prohibited):**
- "This change will improve performance by 25%"
- "Reduces memory usage by 200MB"
- "Caching will make this 3x faster"
- "This optimization saves 10 seconds per request"

✅ **Evidence-Based (Required):**
- "This change can improve performance"
- "Caching may reduce load on the database"
- "This approach is more efficient"
- "Based on profiling data showing 2.5s average response time, reducing database calls from 10 to 3 per request improves response time to 1.2s (52% reduction)"

**Agent Responsibility:**
- Ground all technical claims in observable facts
- State what the code does, not hypothetical benefits
- When benefits are real but unmeasured, describe them qualitatively
- Only use specific numbers when you have actual data

### Fail-Fast Philosophy

All operations must adhere to strict failure handling:

- **Never introduce fallback logic** of any kind
- **Never hard code configuration values**
- **Never allow operations to fail silently**

All failures must:
- Fail fast
- Exit with a non-zero exit code
- Surface a clear, actionable error message

### SOLID Principles

**All code must follow SOLID principles:**

1. **Single Responsibility Principle (SRP)**
   - Each class should have one, and only one, reason to change
   - Each method should do one thing and do it well
   - Separate concerns into distinct classes and modules

2. **Open/Closed Principle (OCP)**
   - Classes should be open for extension but closed for modification
   - Use interfaces, abstract classes, and composition to enable extensibility
   - Avoid modifying existing code when adding new functionality

3. **Liskov Substitution Principle (LSP)**
   - Subtypes must be substitutable for their base types
   - Derived classes must not break the contract of base classes
   - Follow the principle of behavioral subtyping

4. **Interface Segregation Principle (ISP)**
   - Clients should not be forced to depend on interfaces they don't use
   - Create focused, role-specific interfaces
   - Avoid "fat" interfaces with many methods

5. **Dependency Inversion Principle (DIP)**
   - Depend on abstractions, not concretions
   - High-level modules should not depend on low-level modules
   - Use dependency injection to inject implementations

### DRY Principle (Don't Repeat Yourself)

**Never duplicate code or logic:**

- Extract common logic into reusable methods, classes, or utilities
- Use inheritance, composition, or delegation to share behavior
- Create shared libraries for cross-cutting concerns
- Avoid copy-paste programming
- If you write the same logic twice, refactor it into a shared component

**This applies to:**
- Business logic
- Data access patterns
- Validation rules
- Error handling
- Test setup and assertions
- Configuration management
- Documentation

**Acceptable repetition:**
- Test cases with different data (use parameterized tests instead)
- Independent implementations with similar structure but different concerns
- When abstraction would increase complexity more than it reduces duplication

### Complete Replacement of Superseded Code

**When replacing old functionality with new functionality, all consumers must be updated in the same change.**

When a function, class, or pattern is replaced by a new implementation:

1. **Find all references** — search the entire codebase for every call site, import, test, and documentation reference to the old code
2. **Update all consumers** — every caller, test, and reference must be migrated to the new implementation in the same story/commit
3. **Remove the old code** — delete the superseded function/class entirely; do not leave dead code behind
4. **Update all tests** — tests for the old function must be replaced with tests for the new function; never patch tests to work around removed code
5. **Verify no orphaned references** — run a final grep to confirm zero remaining references to the old function name

**This applies to:**
- Replaced utility functions (e.g., old validation replaced by new shared validation)
- Renamed or restructured APIs
- Deprecated patterns superseded by new patterns
- Refactored test helpers and fixtures

**Anti-patterns to avoid:**
- Mocking/patching tests to work around removed functions instead of updating them
- Leaving old imports that cause ImportError at collection time
- Keeping "backward compatibility" tests for deleted code
- Fixing tests file-by-file reactively instead of proactively finding all references upfront

**Required approach:**
- Before writing the new implementation, search for all references to the old code
- Plan the full set of files that need updating
- After writing the new code, update ALL consumers in one pass
- Run the full test suite to verify zero breakage

### 12-Factor App Principles

**All code must adhere to the 12-factor app methodology:**

1. **Codebase**
   - One codebase tracked in version control, many deploys
   - Never maintain multiple codebases for the same application

2. **Dependencies**
   - Explicitly declare and isolate dependencies
   - Use `build.gradle` for all dependencies
   - Never rely on implicit system-wide packages

3. **Config**
   - Store config in environment variables, never in code
   - Config varies between deploys (dev, staging, production)
   - No credentials, URLs, or environment-specific values in code or git

4. **Backing Services**
   - Treat backing services (databases, queues, APIs) as attached resources
   - Connect via URL or credentials from environment
   - Must be swappable without code changes

5. **Build, Release, Run**
   - Strictly separate build, release, and run stages
   - Build creates deployment artifact
   - Release combines artifact with config
   - Run executes the application

6. **Processes**
   - Execute the app as one or more stateless processes
   - Never store session state in application memory
   - Use backing services (Redis, database) for persistent state

7. **Port Binding**
   - Export services via port binding
   - Application is completely self-contained
   - Port numbers must be configurable via environment variables

8. **Concurrency**
   - Scale out via the process model
   - Design for horizontal scaling
   - Processes are disposable and can be started/stopped rapidly

9. **Disposability**
   - Maximize robustness with fast startup and graceful shutdown
   - Processes should be disposable (can be started or stopped at any time)
   - Handle SIGTERM gracefully
   - Ensure idempotent operations

10. **Dev/Prod Parity**
    - Keep development, staging, and production as similar as possible
    - Minimize time gap between development and deployment
    - Use same backing services across environments (containerized databases, etc.)
    - Same deployment process for all environments

11. **Logs**
    - Treat logs as event streams
    - Application writes unbuffered to stdout/stderr
    - Never manage log files or log rotation in application code
    - Let execution environment handle log aggregation

12. **Admin Processes**
    - Run admin/management tasks as one-off processes
    - Use same codebase and config as application
    - Admin code ships with application code
    - Use same dependency isolation

### Idiomatic Code

**All code must be idiomatic to its language and framework.**

Write code that follows the conventions, patterns, and best practices of the specific technology:

**Java/Spring Boot:**
- Use Spring's dependency injection annotations (`@Autowired`, `@Component`, `@Service`)
- Follow JavaBeans conventions for getters/setters
- Use Optional for nullable return values
- Leverage Java 17+ features (records, pattern matching, text blocks)
- Follow Spring Boot conventions for configuration and auto-configuration
- Use Spring's stereotype annotations appropriately

**General Guidelines:**
- Write code that looks natural to experienced developers in that language
- Use language-specific idioms and patterns
- Follow framework conventions and best practices
- Prefer framework-provided solutions over custom implementations
- Use standard library functions over custom implementations

### Declarative vs Imperative Code

**State descriptions must be declarative, not imperative.**

**Declarative (Required):**
- Describe **what** the desired state should be
- Infrastructure as Code: Kubernetes manifests, Terraform configurations
- Configuration files: application.yml, properties files
- Database schemas: migration scripts describe end state
- Build configurations: declare dependencies and outputs

**Imperative (Avoid for State):**
- Do not describe **how** to reach the state through step-by-step instructions
- Avoid procedural scripts for infrastructure changes
- Don't use manual setup instructions in documentation

**Examples:**

✅ **Declarative (Correct):**
```yaml
# Kubernetes deployment
replicas: 3
resources:
  limits:
    memory: "512Mi"
    cpu: "500m"
```

❌ **Imperative (Incorrect):**
```bash
# Script that modifies state
kubectl scale deployment myapp --replicas=3
kubectl set resources deployment myapp --limits=memory=512Mi,cpu=500m
```

✅ **Declarative (Correct):**
```java
@Configuration
public class DatabaseConfig {
    @Bean
    public DataSource dataSource() {
        // Declare desired configuration
        return DataSourceBuilder.create()
            .url(environment.getProperty("database.url"))
            .build();
    }
}
```

### Environment-Agnostic Artifacts

**All build artifacts must be environment-agnostic.**

**Required:**
- Build once, deploy anywhere
- No environment-specific code or configuration baked into artifacts
- JAR/WAR files must be identical across all environments
- Container images must be environment-neutral
- All environment-specific configuration injected at runtime

**Implementation:**
- Use environment variables for all environment-specific values
- Externalize configuration using Spring profiles and property sources
- Container images should not contain environment-specific config
- Build artifacts reference configuration templates, not actual values
- Use ConfigMaps and Secrets in Kubernetes for runtime configuration

**Anti-patterns to avoid:**
- Building separate artifacts for dev/staging/production
- Environment-specific property files baked into JAR
- Hard-coded environment detection logic
- Different Docker images per environment

**Example:**

✅ **Correct (Environment-Agnostic):**
```dockerfile
FROM openjdk:17-jre-slim
COPY target/app.jar /app.jar
# Configuration injected at runtime via environment variables
ENTRYPOINT ["java", "-jar", "/app.jar"]
```

❌ **Incorrect (Environment-Specific):**
```dockerfile
FROM openjdk:17-jre-slim
COPY target/app.jar /app.jar
COPY config/production.properties /config/application.properties
ENTRYPOINT ["java", "-jar", "/app.jar"]
```

### Immutable Deployments

**Deployments should be immutable wherever possible.**

**Immutable Deployment Principles:**
- Deploy new versions by replacing entire instances, not updating existing ones
- Never modify running containers or application code in place
- Configuration changes trigger new deployments
- Rollbacks are achieved by deploying previous version, not reverting changes
- Infrastructure is replaced, not modified

**Benefits:**
- Predictable, reproducible deployments
- Easy rollback to previous versions
- No configuration drift
- Easier debugging and troubleshooting
- Better disaster recovery

**Required Approach:**
- Use immutable container images with version tags
- Deploy new pods/containers rather than modifying existing ones
- Configuration changes create new deployment revisions
- Database migrations are forward-only, versioned
- Never SSH into containers to make changes

**When to Flag Mutable Deployments:**

If you encounter any of these patterns, **flag them and recommend immutable alternatives:**

❌ **Mutable Anti-patterns:**
- Scripts that modify files on running servers
- In-place updates to running containers
- Manual configuration changes via SSH/kubectl exec
- Hot-swapping configuration files
- Patching running applications
- Directly modifying Kubernetes resources with `kubectl edit`

**Agent Responsibility:**

When you detect mutable deployment patterns:
1. **Flag the issue** - Clearly identify the mutable pattern
2. **Explain the risk** - Why immutability is preferred
3. **Recommend immutable alternative** - Provide specific guidance
4. **Assess impact** - Note if change requires architecture modification

**Exception:**

Only allow mutable deployments when:
- It represents a major architectural change that's been explicitly approved
- The project explicitly uses a mutable deployment model (rare, should be documented)
- Immediate hotfix is required (but follow up with immutable deployment)

### Input-Driven and Dynamic Configuration

**All code must be input-driven and dynamically configured, not static.**

This principle applies to:
- Application code
- Test code (unit, integration, end-to-end)
- Scripts and automation
- CI/CD pipelines
- Infrastructure configuration

**Never use static values or hard-coded data:**
- No hard-coded URLs, endpoints, or hostnames
- No hard-coded credentials or API keys
- No hard-coded timeouts or retry counts
- No hard-coded file paths or directory locations
- No hard-coded environment-specific settings
- No hard-coded feature flags or toggles
- No hard-coded test data or mock responses
- No hard-coded port numbers or connection strings
- No hard-coded dates, times, or temporal values
- No hard-coded identifiers (user IDs, account IDs, etc.)

**Required approach:**
- Externalize all configuration via environment variables or configuration files
- Use configuration properties from `application.yml` or `application.properties`
- Inject dependencies and configuration through Spring's dependency injection
- Load test data from external files or configuration
- Use parameterized tests with data providers
- Make all thresholds, limits, and boundaries configurable
- Support runtime reconfiguration where appropriate

**Test code requirements:**
- Test fixtures must be configurable via test properties
- Mock data must be loaded from test resources or generated dynamically
- Test timeouts must be configurable
- Test endpoints and URLs must be injectable
- Integration test configuration must be externalized
- No hard-coded assertions on specific values (use relative comparisons or configured expected values)

---

---

## Testing Standards

### Real Tests Only - No Stubs

**When writing or fixing tests, NEVER create stub tests.**

❌ **Prohibited Test Patterns:**
```java
@Test
public void testSomething() {
    // TODO: Implement test
    assertTrue(true); // NEVER DO THIS
}

@Test
public void testFeature() {
    // Stub test that always passes
    assertNotNull(new Object()); // NEVER DO THIS
}
```

✅ **Required Test Patterns:**
```java
@Test
public void testUserCreation() {
    // Real test with actual behavior validation
    User user = userService.createUser("test@example.com");
    assertNotNull(user);
    assertEquals("test@example.com", user.getEmail());
    verify(userRepository).save(any(User.class));
}
```

**Requirements:**
- Tests must validate actual behavior, not mock success
- Tests must be able to actually fail if the code is wrong
- No placeholder tests that always pass
- No stub tests marked with TODO
- Tests must include meaningful assertions
- Integration tests must test real integrations (with test containers/test databases)

---

## Security Standards

**All code must meet the security requirements for highly regulated financial services.**

This application operates in a highly regulated financial environment and must comply with strict security standards including SOC 2, PCI DSS, FINRA, SEC regulations, and data privacy laws.

### Security Scans - Never Bypass Without Permission

**When running security scans, NEVER add code exceptions to bypass failures without explicit human permission.**

❌ **Prohibited Security Bypass Patterns:**
```java
// NEVER DO THIS without explicit human permission
String password = getPassword(); // nosec
executeCommand(userInput); // nosemgrep
```

```python
# NEVER DO THIS without explicit human permission
# nosec B501
password = "hardcoded"  # noqa: S105
```

```yaml
# NEVER DO THIS without explicit human permission
rules:
  - id: sql-injection
    severity: error
    exclude:
      - "src/main/java/UserService.java"  # NEVER ignore findings this way
```

**Required Approach:**
1. If a security scan fails, document the failure
2. Analyze the finding - is it a real vulnerability?
3. If it's a real issue, fix the code (don't suppress the warning)
4. If you believe it's a false positive, ask human for guidance
5. Only add suppressions with explicit human approval AND documentation of why

**Never:**
- Add `// nosec` comments to bypass security tools
- Add `# noqa` comments to bypass linters
- Modify security tool configurations to ignore findings
- Use `@SuppressWarnings("security")` without approval
- Disable security rules or checks

### Core Security Principles

**Defense in Depth:**
- Implement multiple layers of security controls
- Never rely on a single security mechanism
- Assume every layer can be breached and plan accordingly

**Least Privilege:**
- Grant minimum permissions necessary for functionality
- Apply to users, services, containers, and processes
- Never use root or admin privileges unless absolutely required

**Zero Trust:**
- Never trust, always verify
- Authenticate and authorize every request
- No implicit trust based on network location

### Sensitive Data Handling

**Never log, display, or expose:**
- Passwords or authentication credentials
- API keys, access tokens, or secrets
- Social Security Numbers (SSN)
- Credit card numbers (PAN)
- Bank account numbers
- Personal Identifiable Information (PII): names with SSN, email with financial data
- Authentication tokens or session identifiers
- Encryption keys or certificates

**Required Practices:**
- Use AWS Secrets Manager or Parameter Store for all secrets
- Never commit secrets to git repositories
- Mask or redact sensitive data in logs
- Encrypt sensitive data at rest and in transit
- Use secure token storage mechanisms
- Implement proper key rotation

**Data Classification:**
- Public: No restrictions
- Internal: Access controlled to employees
- Confidential: Access controlled to specific roles
- Restricted: Highest sensitivity, strict access controls (PII, financial data)

### Input Validation and Sanitization

**All user input must be validated and sanitized:**
- Validate input type, length, format, and range
- Use allowlists, not denylists
- Reject invalid input, don't try to fix it
- Sanitize for SQL injection, XSS, command injection
- Validate file uploads: type, size, content
- Use parameterized queries for all database operations

**Never:**
- Trust any input from users, APIs, or external systems
- Concatenate user input directly into SQL queries
- Execute user input as code or commands
- Render user input directly into HTML without escaping

### Authentication and Authorization

**Required:**
- Use Spring Security for all authentication and authorization
- Implement proper session management with secure cookies
- Use strong password policies (complexity, rotation)
- Implement multi-factor authentication (MFA) where required
- Use OAuth 2.0 / OpenID Connect for API authentication
- Implement proper role-based access control (RBAC)
- Log all authentication events (success and failure)

**JWT Tokens:**
- Use short expiration times (15-30 minutes for access tokens)
- Implement token refresh mechanisms
- Sign tokens with strong algorithms (RS256, not HS256)
- Validate signature, expiration, and issuer on every request
- Store tokens securely (secure HTTP-only cookies or secure storage)

**Session Management:**
- Regenerate session IDs after authentication
- Implement session timeout (15-30 minutes of inactivity)
- Invalidate sessions on logout
- Use secure, HTTP-only, SameSite cookies

### Cryptography

**Required:**
- Use TLS 1.2 or higher for all network communication
- Use AES-256 for data at rest encryption
- Use bcrypt, scrypt, or Argon2 for password hashing (never MD5, SHA1, or plain SHA256)
- Use cryptographically secure random number generators
- Implement certificate validation and pinning where appropriate

**Never:**
- Implement custom cryptographic algorithms
- Use deprecated or weak algorithms (DES, 3DES, RC4, MD5, SHA1)
- Store encryption keys in code or configuration files
- Reuse initialization vectors (IVs) or nonces

### API Security

**Required:**
- Implement rate limiting to prevent abuse
- Use API gateways for centralized security controls
- Validate Content-Type headers
- Implement CORS policies appropriately (never use wildcard origins in production)
- Return generic error messages (don't leak implementation details)
- Implement request size limits
- Use versioned APIs to maintain security controls during updates

**Response Headers:**
- `Strict-Transport-Security` for HTTPS enforcement
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY` or `SAMEORIGIN`
- `Content-Security-Policy` to prevent XSS
- Remove `X-Powered-By` and other identifying headers

### Dependency Management

**Required:**
- Keep all dependencies up to date
- Scan dependencies for known vulnerabilities (Snyk, OWASP Dependency-Check)
- Use only trusted, well-maintained libraries
- Review dependency licenses for compliance
- Monitor security advisories for used dependencies

**Never:**
- Use dependencies with known critical vulnerabilities
- Use unmaintained or abandoned libraries
- Ignore security scan findings

### Error Handling and Logging

**Required:**
- Log all security-relevant events (authentication, authorization, data access)
- Include timestamps, user IDs, and actions in audit logs
- Use structured logging for easier analysis
- Implement log integrity controls
- Send logs to centralized logging system

**Never:**
- Log sensitive data (passwords, tokens, PII, financial data)
- Return stack traces or detailed error messages to clients
- Log data that can be used to compromise security

**Error Messages:**
- Generic for authentication failures ("Invalid credentials", not "User not found")
- No stack traces in production
- No database error details exposed
- No file system paths revealed

### SQL Injection Prevention

**Required:**
- Use JPA/Hibernate or parameterized queries exclusively
- Never concatenate user input into SQL queries
- Use named parameters in native queries
- Validate all input before database operations

**Prohibited:**
```java
// NEVER do this
String query = "SELECT * FROM users WHERE username = '" + username + "'";
```

**Required:**
```java
// ALWAYS do this
@Query("SELECT u FROM User u WHERE u.username = :username")
User findByUsername(@Param("username") String username);
```

### Cross-Site Scripting (XSS) Prevention

**Required:**
- Escape all output by default
- Use templating engines with auto-escaping (Thymeleaf)
- Implement Content Security Policy headers
- Validate and sanitize all user input
- Use context-aware encoding (HTML, JavaScript, URL, CSS)

### Container Security

**Required:**
- Run containers as non-root user
- Use minimal base images (distroless when possible)
- Scan images for vulnerabilities
- Implement resource limits (CPU, memory)
- Use read-only file systems where possible
- Drop unnecessary Linux capabilities

**Dockerfile Requirements:**
```dockerfile
# Use non-root user
USER nonroot:nonroot

# Read-only root filesystem
RUN chmod -R 555 /app

# No secrets in images
# Environment variables for runtime config only
```

### Kubernetes Security

**Required:**
- Use Network Policies to restrict pod-to-pod communication
- Implement Pod Security Standards (restricted)
- Use Secrets for sensitive data (never ConfigMaps)
- Enable RBAC with least privilege
- Implement resource quotas and limits
- Use separate namespaces for environment isolation

### Compliance Requirements

**Must comply with:**
- **SOC 2 Type II** - Security, availability, confidentiality controls
- **PCI DSS** - If handling payment card data
- **FINRA** - Financial industry regulatory requirements
- **SEC Regulations** - Securities and Exchange Commission rules
- **GDPR** - If handling EU citizen data
- **CCPA** - If handling California resident data
- **SOX** - Sarbanes-Oxley for financial reporting

**Required Controls:**
- Audit logging of all data access
- Data retention and deletion policies
- Access control and review procedures
- Change management and approval processes
- Incident response procedures
- Regular security assessments and penetration testing

### Security Testing

**Required:**
- Static Application Security Testing (SAST) in CI/CD pipeline
- Dynamic Application Security Testing (DAST) for running applications
- Software Composition Analysis (SCA) for dependencies
- Security code reviews for all changes
- Penetration testing before major releases

### Agent Responsibility for Security

When writing code:
1. **Identify security risks** - Consider what could go wrong
2. **Apply security controls** - Implement appropriate safeguards
3. **Validate assumptions** - Don't assume inputs are safe
4. **Follow secure patterns** - Use framework security features
5. **Flag security concerns** - Highlight potential vulnerabilities for review

**When in doubt:**
- Choose the more secure option
- Ask for security review
- Document security decisions
- Err on the side of caution

### Security Anti-Patterns to Avoid

❌ **Never:**
- Hard-code credentials or secrets
- Disable security features "temporarily"
- Use `eval()` or similar code execution functions
- Trust client-side validation alone
- Use `SELECT *` in queries
- Expose internal IDs or implementation details
- Use default or weak passwords
- Skip input validation "just this once"
- Store passwords in plain text or reversible encryption
- Use `@SuppressWarnings` on security findings without review
- Disable TLS certificate validation
- Use `chmod 777` or equivalent overly permissive settings

## Waiting and Readiness Detection

### Time-Based Delays Are Prohibited

**Never use time-based synchronization:**
- Never use `sleep` to wait for anything
- Never use time-based delays as a synchronization mechanism

### Required Approach: Active Readiness Detection

All waiting must be implemented using **readiness detection**, not time.

**Acceptable readiness mechanisms:**
- Health check endpoints
- Port availability checks
- File existence verification
- API status polling
- Process state monitoring
- Container readiness probes

### Timeout Requirements

All waits must support **variable-driven timeouts**:
- No hard-coded timeout values
- Timeout values must be configurable via environment variables

**On timeout:**
- Fail fast
- Exit with non-zero exit code
- Emit a clear diagnostic message explaining what timed out and how to investigate

---

## Shell and Scripting Standards

### Script Creation Policy

**Never create shell scripts unless explicitly requested by the prompt**

- Shell code must not be embedded inside:
  - Application code
  - CI/CD pipelines
  - Build logic
- Exception: When the user explicitly requests shell script creation

### Prohibited Patterns

**Never use `sleep` commands or sleep-based methods in any form**

Prefer instead:
- Event-driven logic
- State polling with conditions
- Proper lifecycle hooks
- Built-in readiness mechanisms

---

## GitHub Workflows

### Shell Configuration

When creating or editing GitHub Actions workflows:

**Required:**
- Always use `shell: bash` for all `run` steps that execute shell commands
- Never use `sh`
- Never rely on implicit shell defaults

### Error Handling

**Required:**
- All commands must fail on error
- Use `set -euo pipefail` where appropriate
- No silent failures allowed
- All critical steps must validate their own success

---

## Git Usage Standards

### Selective File Addition

When adding files with git:

**Only add:**
- Files modified in the current prompt, or
- Files explicitly requested by the developer

**Never add:**
- Unrelated files
- Generated artifacts (unless explicitly requested)
- Formatting or cleanup changes outside the scope of the prompt
- Files that were not part of the current work

### Never Bypass Hooks, Linters, or Security Checks

**Never use flags, options, inline comments, configuration changes, or any other mechanism that causes quality tools to skip or ignore findings:**

**Prohibited command-line flags:**
- `--no-verify` on any git command
- `--no-gpg-sign` or other hook-skipping flags
- `--skip-checks`, `--force`, or equivalent flags to bypass CI/CD quality gates

**Prohibited inline code annotations (these tell tools to ignore findings):**
- `# noqa` (flake8/ruff ignore)
- `# nosec` (bandit security ignore)
- `// nosec` (gosec ignore)
- `# type: ignore` (mypy ignore)
- `@SuppressWarnings` (Java ignore)
- `// nolint` (golangci-lint ignore)
- `// eslint-disable` or `/* eslint-disable */` (ESLint ignore)
- `# pragma: no cover` (coverage ignore)
- `# skipcq` (DeepSource ignore)
- Any similar annotation in any language that suppresses a linter, formatter, type checker, or security scanner finding

**Prohibited configuration changes:**
- Adding files or patterns to `.flake8`, `.eslintignore`, `.banditrc`, or similar ignore lists to hide findings
- Adding `exclude` rules to security scanner configs
- Modifying tool configurations to raise thresholds or disable rules

**If a hook, linter, or security check fails:**
1. Investigate and fix the root cause
2. If you believe it's a false positive, ask the human for guidance
3. Never work around the check — fix the code or fix the check

**No exceptions.** If a pre-commit or pre-push hook is failing, the correct response is to fix the issue it found, not to bypass it.

### Commit and PR Messages

When creating commit messages or pull request descriptions:

**Never include:**
- `Co-Authored-By: Claude <noreply@anthropic.com>`
- `Co-Authored-By: Anthropic`
- Any similar co-authorship attribution to Claude or Anthropic

**Rationale:**
- Commits should reflect human authorship and accountability
- AI assistance is a tool, not a co-author
- Attribution should be to the developer making the commit

---

## Documentation Standards

### Documentation Synchronization

**Documentation must always be kept in sync with code changes.**

**Required:**
- Update relevant documentation in the same commit as code changes
- Never leave documentation outdated after code modifications
- Documentation updates are part of "done", not optional follow-up work

**This applies to:**
- README files
- API documentation
- Architecture diagrams
- Configuration guides
- Deployment instructions
- User guides
- Developer guides
- Code comments and docstrings

**When to Update Documentation:**

1. **API Changes** - Update API documentation immediately
   - REST endpoint changes → Update API docs
   - Request/response format changes → Update examples
   - New endpoints → Document parameters, responses, errors

2. **Configuration Changes** - Update configuration guides
   - New environment variables → Document in README or config docs
   - Changed property names → Update all references
   - New configuration files → Document purpose and format

3. **Architecture Changes** - Update architecture documentation
   - New components → Update architecture diagrams
   - Changed patterns → Update design documentation
   - Removed components → Remove from all documentation

4. **Deployment Changes** - Update deployment instructions
   - New deployment steps → Update runbooks
   - Changed infrastructure → Update IaC documentation
   - New dependencies → Update installation guides

5. **Behavior Changes** - Update user-facing documentation
   - Changed functionality → Update user guides
   - New features → Add to feature documentation
   - Deprecated features → Mark as deprecated, document migration

**Documentation Debt is Technical Debt:**
- Outdated documentation is worse than no documentation
- Misleading docs cause more problems than missing docs
- Documentation must be treated as first-class deliverable

**Agent Responsibility:**

When making code changes:
1. **Identify affected documentation** - Determine which docs need updates
2. **Update documentation** - Make changes in the same commit
3. **Verify completeness** - Ensure all references are updated
4. **Flag missing docs** - If documentation doesn't exist but should, create it

### Documentation Creation Policy

**Do not create summary documents unless explicitly requested**

**Never generate:**
- Design documents
- Summaries
- Checklists
- Reports
- Executive summaries
- Overview documents

**Exception:** Only when the user directly requests them OR when explicitly required in backlog specifications or prompts

**Required documentation creation:**
- When code changes affect existing documentation (updates required)
- When new features/APIs require user-facing documentation (part of the feature)
- When configuration changes require documentation (part of the change)
- When backlog work units explicitly specify output documents in "Output Location" section

### Completion Criteria

A prompt is complete when:
- The requested changes are implemented
- Tests pass (if applicable)
- All affected documentation is updated in sync with code changes
- No summary documentation is created (unless requested)
- Only relevant files are staged for commit

---

## Project-Specific Context

### Technology Stack

- **Language:** Java 17
- **Framework:** Spring Boot 3.x
- **Build Tool:** Gradle
- **Container:** Docker with DevContainer support
- **CI/CD:** GitHub Actions
- **Deployment:** Kubernetes with ArgoCD

### Critical Files (Require Manual Review)

These files should be modified with care and reviewed before changes:

**Build & Configuration:**
- `build.gradle`, `settings.gradle`, `gradle.properties`
- `.devcontainer/**`
- `.tool-versions`
- `shell.env`
- `config/checkstyle/*.xml`
- `src/main/resources/application*.yml`

**CI/CD & Deployment:**
- `.github/workflows/*.yml`
- `cd/k8s/**/*.yaml`

**Version Control:**
- `.git/**`
- `.vscode/*.json`

---

## Summary

These standards ensure:
- **Security:** Defense in depth, least privilege, zero trust, compliance with financial regulations
- **Reliability:** Fail-fast behavior prevents silent failures
- **Maintainability:** No hard-coded values or time-based waits
- **Consistency:** Standardized approaches across all automation
- **Safety:** Protected files require manual review, secure coding practices
- **Clarity:** Clear error messages for troubleshooting (without leaking sensitive information)
- **Quality:** SOLID and DRY principles, idiomatic code
- **Scalability:** 12-factor app methodology, immutable deployments
- **Portability:** Environment-agnostic artifacts, declarative state
- **Deployability:** Immutable infrastructure, predictable releases
- **Documentation:** Always in sync with code, never outdated
- **Compliance:** SOC 2, PCI DSS, FINRA, SEC, GDPR, CCPA, SOX
- **Accuracy:** Evidence-based claims, no speculative performance numbers

When in doubt, follow these principles in order:
1. Security first - validate input, protect sensitive data, follow secure patterns
2. Fail fast with clear errors (without exposing implementation details)
3. Use active detection, not time delays
4. Externalize all configuration (especially secrets and credentials)
5. Write idiomatic, declarative code
6. Ensure artifacts are environment-agnostic
7. Design for immutable deployments
8. Update documentation with every code change
9. Make evidence-based claims, avoid speculative numbers
10. Only create what was explicitly requested
