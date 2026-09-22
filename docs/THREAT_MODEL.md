# Threat Model — MCPserver.in + app.mcpserver.in

## Purpose

This document identifies potential security threats, vulnerabilities, and attack vectors
for the MCPserver.in + app.mcpserver.in dual-product system, and defines mitigation
strategies for each.

## Threat Classification

### 1. Authentication Threats

| Threat | Description | Mitigation |
|---|---|---|
| Credential stuffing | Attackers use leaked password/username combos from other breaches | Rate-limiting on auth endpoints, MFA required for sensitive actions, passwordless authentication (passkeys), anomalous pattern detection |
| Password brute force | Repeated login attempts with different passwords | Account lockout after N failures, exponential backoff on delays, CAPTCHA for repeated failures, IP-based throttling |
| Token replay | Stolen bearer tokens reused in different sessions | One-time use tokens, session binding to IP/device, short token TTL (15min), rotation on use, fingerprinting |
| Session fixation | Attacker sets victim's session ID before login | Regenerate session ID on authentication, use server-generated session IDs only, HttpOnly Secure cookies |

### 2. Authorization Threats

| Threat | Description | Mitigation |
|---|---|---|
| Privilege escalation | User gains higher-role capabilities than assigned | RBAC with explicit deny, organization boundaries, admin override only via MFA, audit all role changes |
| Cross-user data access | User reads/writes another user's data | Organization boundaries as first policy layer, explicit allow only, resource-level ownership checks, never trust client-reported user IDs |
| Privilege creep | Users accumulate roles beyond need | Regular access reviews (quarterly), explicit deny as default, just-in-time role assignment, maximum role retention period |

### 3. Injection Threats

| Threat | Description | Mitigation |
|---|---|---|
| SQL injection | Malicious SQL in user input to database | Parameterized queries, ORM with typed queries, input validation, ORACLE sanitization, query whitelisting |
| Cross-site scripting (XSS) | Script injection into web pages viewed by others | Content Security Policy, HTML escaping on output, DOMPurify for rich text, sanitize all user-generated content, CSP nonces |
| Command injection | OS commands injected via user input | Avoid shell execution, use child_process with arg arrays not strings, input validation, allowlist permitted commands |
| SQLi via API params | SQL injection through API client parameters | Parameterized queries in all database access, ORM type safety, input schema validation (Zod), prepared statements |

### 4. Data Threats

| Threat | Description | Mitigation |
|---|---|---|
| PII exposure | Personally identifiable information leaked in logs/response | PII never logged raw, data masking at display (PAN: `**** **** **** 1234`, email masking), redaction middleware, structured audit fields only |
| Unauthorized data modification | Write access to data user shouldn't modify | Write-only endpoints where needed, version concurrency controls, optimistic locking, change audit trail |
| Confidential data leak | GSTIN, PAN, Aadhaar, financial data exposed | Encryption at rest (AES-256), encryption in transit (TLS 1.3+), secret management (Vault/Secrets Manager), field-level encryption for highest-sensitivity data |
| Schema pollution | Malicious schema injection via API | Zod schema validation on all inbound, never trust client-schema, generate server schemas, reject unknown fields |

### 5. Network Threats

| Threat | Description | Mitigation |
|---|---|---|
| SSRF | Server-side request injection to internal resources | Protocol validation (allowlist http/https), hostname validation, private IP blocking (10.x, 172.x, 192.168.x, 127.x), DNS rebinding prevention, request timeout (30s max), outbound firewall rules |
| Open redirect | Redirect to arbitrary attacker-controlled site | Strict redirect validation, allowlist-only destinations, no relative redirects without validation, CAPTCHA for sensitive redirects |
| Man-in-the-middle | Traffic intercepted between client and server | TLS 1.3+ everywhere, certificate pinning, HSTS (max-age=31536000; includeSubDomains; preload), validate certs, no public CAs for internal endpoints |
| Port scanning | Attacker probes open ports on host | Rate limiting on all endpoints, fail-closed ports (only documented services), network segmentation, host-level firewall |

### 6. Application Threats

| Threat | Description | Mitigation |
|---|---|---|
| Deserialization | Malicious data deserialization executing code | Use safe deserialization libraries, avoid native deserialization, schema validation before deserialization, consider JSON only |
| Path traversal | `../` sequences access files outside web root | Path validation, allowlisted path prefixes, resolve() and verify within base dir, deny `..` components, chroot for containerized services |
| File inclusion | Remote/ local file inclusion via parameter | File path allowlisting, reject absolute paths, sandbox file access, content security on included files |
| Prototype pollution | JavaScript prototype polluted via JSON | Use Object.create(null), frozen objects, schema validation before object merge, avoid deep merges from untrusted sources |
| Denial of service | Resource exhaustion (CPU, memory, connections) | Rate limiting per endpoint/ip/token, connection pooling with max limits, request size limits, CPU/memory quotas, auto-scaling with limits, circuit breakers |

### 7. Supply Chain Threats

| Threat | Description | Mitigation |
|---|---|---|
| Dependency compromise | Malicious code in npm/pip/go dependencies | Regular dependency audits (`npm audit`, Snyk), pin dependency versions, use lockfiles (`package-lock.json`), monitor CVE feeds, SBOM generation, verify signatures |
| Build compromise | CI/CD pipeline injected with malicious code | Signed commits, git commit verification, pipeline as code in repo, approve all changes, immutable build artifacts, air-gapped build where possible |
| Dependency confusion | Internal packages overtaken by malicious npm packages | Private package indices, explicit package names in imports, version pinning, detect when internal package versions are "helpfully" overridden |

### 8. Configuration Threats

| Threat | Description | Mitigation |
|---|---|---|
| Secrets in source | API keys, passwords, tokens committed to repo | Secret scanning (git-secrets, truffleHog), secret rotation policy, environment variable only, no .env in repo, secret management service, rotate immediately if committed |
| Overly permissive IAM | Roles/policies with too broad permissions | Principle of least privilege, regular IAM audits, automated policy review, just-in-time access, deny-by-default |
| Default credentials | Devices/services with factory defaults | Change all defaults on provisioning, documented default-change process, credential inventory, rotate after any exposure |
| Feature creep | Disabled features left enabled | Feature flags with expiration, regular feature flag audit, remove unused code, feature flag governance process |

## Incident Response

### 1. Detection

- anomalous auth failure rate spike
- unexpected outbound network traffic
- PII in logs (monitoring alert)
- rate limit exceeded responses increasing
- TLS certificate expiration warnings
- dependency vulnerability alerts

### 2. Containment

- revoke compromised tokens/sessions
- isolate affected service/instances
- block attacker IP at WAF/nateway
- rotate secrets (API keys, DB passwords, JWT secrets)
- enable read-only mode as default
- enable maintenance mode if needed

### 3. Eradication

- remove attacker access (SS keys, tokens, sessions)
- patch vulnerable code/dependencies
- rotate all credentials in affected scope
- rebuild compromised containers/images
- verify integrity of all affected artifacts

### 4. Recovery

- restore from known-good backup (pre-compromise)
- monitor for re-indication of compromise
- gradually restore normal operations
- communicate with affected users if PII was exposed
- post-incident review and process improvement

### 5. Post-Incident Review

- timeline of events (what, when, how long)
- what worked well in response
- what could be improved
- process changes to prevent recurrence
- updated threat model entries if new vectors discovered
- documentation updates
- stakeholder communication plan review

## Security Headers (CSP, HSTS, etc.)

All responses should include these security headers:

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 0
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=()
Cache-Control: no-cache, no-store, must-revalidate (for /api/* routes)
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline' https:; style-src 'self' 'unsafe-inline' https:; img-src 'self' data: https:; connect-src 'self'; font-src 'self; object-src 'none; frame-ancestors 'none; base-uri 'self;
```

## Compliance Mapping

| Framework | Controls Mapped | Status |
|---|---|---|
| OWASP Top 10 | All 10 categories | Addressed |
| ISO 27001 | A.9, A.12, A.13, A.14 | In progress |
| SOC 2 | CC6.1, CC6.2, CC6.3, CC7.2 | In progress |
| GDPR | Art. 32 (security of processing) | Addressed (PII protection) |
| India IT Act 2000 | Section 43A, 72A | Addressed (financial PII) |
| India DPDP Act | Consent, data minimization | Addressed |

## Threat Model Maintenance

- Review quarterly or after any significant change
- Update after any incident or near-miss
- Incorporate new threat intelligence (CVE, exploit trends)
- Incorporate feedback from pentest/red-team exercises
- Maintain mapping to compliance frameworks
- Keep incident response plan current and tested (tabletop exercise annually)

## End of Document