# MCPServer OS

Evidence-First AI Infrastructure Control Plane for Model Context Protocol

This repository is the **app.mcpserver.in control-plane application** (deploy,
govern, observe MCP workloads). The public marketing/content site
(mcpserver.in — discovery, guides, glossary, evidence pages) lives separately
in [`CodesbyFebin/Indian-MCP-Server`](https://github.com/CodesbyFebin/Indian-MCP-Server).
They share the evidence/data model conceptually (see `docs/`) but are
independently deployable, with their own dependencies and CI/CD.

> **MCPServer OS — Evidence-First Infrastructure for Model Context Protocol. Deploy verified MCP workloads, enforce zero-trust policy, observe every interaction, and produce tamper-evident operational evidence from infrastructure you control.**

## Overview

MCPServer OS is a self-hosted control plane for managing Model Context Protocol (MCP) infrastructure with an emphasis on evidence, verification, and operational integrity rather than compliance certifications.

## Core Philosophy

MCPServer OS follows an **Evidence-First** approach:
- **Discover → Verify → Approve → Deploy → Govern → Observe → Evidence → Recover**
- Focus on technical evidence and verifiable controls rather than legal compliance claims
- Immutable deployment revisions with hash-chained evidence trails
- Zero-trust architecture with tenant isolation and least-privilege access
- Observable interactions from client request to tool execution and response

## Seven Architecture Planes

1. **Trust Plane** - Provenance, artifact identity, publisher evidence via `mcpserver.in`
2. **Control Plane** - Organizations, workspaces, approvals, deployments with tenant isolation
3. **Runtime Plane** - Container/workload management, health, scaling, rollback
4. **Gateway Plane** - MCP transport, JSON-RPC validation, auth, policy, tool access
5. **Security Plane** - Isolation, secrets management, threat detection, kill switches
6. **Evidence Plane** - Technical evidence collection, control mappings, audit chain, evidence packages
7. **Intelligence Plane** - Recommendations, predictive health, MCP Doctor, bounded healing

## India-First Capabilities (Technical Evidence Focus)

- **PII Redaction Engine** - Configurable redaction of Indian PII patterns with evidence logging
- **DPDP Technical Control Profile** - Maps technical controls to DPDP Act requirements (evidence, not compliance)
- **RBI Technical Control Profile** - Maps observable technical controls to RBI Cyber Framework
- **UIDAI Authorization Tracker** - Tracks authorization status for UIDAI services (does not enable without proper credentials)
- **UPI Sandbox Adapter** - Test UPI payment flows in sandbox environments
- **Tenant Residency Policy Engine** - Configurable data residency policies (India-only, Mumbai-only, etc.)
- **IndiaAI Request Entitlement Tracker** - Tracks requests/usage for IndiaAI compute resources
- **Deployment Residency Evidence Report** - Generates evidence of deployment location for audits

## Key Features

### Deployment Lifecycle
Durable state machine with evidence collection at each transition:
```
DRAFT → SOURCE_RESOLUTION → ARTIFACT_VERIFICATION → SECURITY_SCAN → 
POLICY_EVALUATION → PENDING_APPROVAL → QUEUED → BUILDING → DEPLOYING → 
STARTING → HEALTH_CHECKING → RUNNING
```

### MCP Gateway Architecture
```
MCP CLIENT
    │
    ▼
┌──────────────────────┐
│ Authentication       │
├──────────────────────┤
│ Tenant Resolution    │
├──────────────────────┤
│ Rate Limiting        │
├──────────────────────┤
│ JSON-RPC Validation  │
├──────────────────────┤
│ Tool Policy          │
├──────────────────────┤
│ Prompt Protection    │
├──────────────────────┤
│ Secret Broker        │
├──────────────────────┤
│ Audit / Trace        │
├──────────────────────┤
│ Transport Adapter    │
└──────────┬───────────┘
           ▼
       MCP SERVER
```

### Evidence Architecture
Tamper-evident hash chain with explicit evidence types:
- CONFIG, SOURCE, SCAN, RUNTIME, LOG, APPROVAL, ATTESTATION, MANUAL
- SHA-256 artifact hashing with source revision preservation
- Tenant isolation enforced via RLS (Row Level Security)
- Evidence review and verification workflows

## Getting Started

### Prerequisites
- Node.js 18+
- Python 3.9+
- Docker & Docker Compose
- Git
- PostgreSQL 15+
- Redis 7+
- UPI sandbox access credentials (for testing)
- OVSE API key (for identity verification testing)

### Installation

```bash
# Clone the repository
git clone https://github.com/CodesbyFebin/Indian-MCP-Server.git
cd Indian-MCP-Server
git checkout kilo/orbital-eagle-zbx

# Install dependencies
npm install
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your configuration

# Initialize database
npx prisma migrate dev

# Start development environment
npm run dev
```

### Environment Variables

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `NODE_ENV` | Environment mode | `development` | Yes |
| `PORT` | Server port | `3000` | Yes |
| `MCP_SERVER_URL` | MCP server endpoint | `http://localhost:3000` | Yes |
| `UPI_SANDBOX_URL` | UPI sandbox API endpoint | `https://sandbox.upi-api.com` | Yes (for UPI features) |
| `OVSE_API_KEY` | OVSE verification API key | `your_ovse_api_key_here` | Yes (for KYC/OVSE features) |
| `DPDP_PII_ENABLED` | Enable PII redaction | `true` | Yes |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@localhost:5432/mcp` | Yes |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379` | Yes |

## Deployment

### Development
```bash
npm run dev
```

### Production (Docker Compose)
```bash
# Edit .env with production configuration
docker compose -f deploy/docker/docker-compose.yml up --build
```

### Staging Validation
Before moving to production, validate in staging:
1. Test UPI sandbox integration with test credentials
2. Verify PII redaction effectiveness with sample data
3. Check evidence ledger integrity and hash chain
4. Validate deployment lifecycle transitions
5. Test cross-tenant isolation
6. Run security scans and penetration tests

## Security Considerations

- **PII Redaction**: Automatically applied to incoming requests when enabled
- **UPI Sandbox**: Use sandbox credentials only - never production credentials
- **API Keys**: Store in environment variables or secret vault, never in code
- **Access Control**: RBAC enforced on all resources with tenant isolation
- **Secrets Management**: Integration with HashiCorp Vault or AWS Secrets Manager recommended for production
- **Transport Security**: All MCP gateway communications require mutual TLS in production

## Evidence & Audit

All significant operations generate evidence records:
- Deployment approvals and rejections
- Configuration changes
- Security events and policy violations
- Tool executions and MCP interactions
- Data access and modification events
- System health and performance metrics

Evidence is stored in an append-only, hash-chained ledger with explicit verification status.

## Development Roadmap

See [PROJECT-TRACKER.md](PROJECT-TRACKER.md) for detailed implementation progress organized by:
- **Release Trains** (R1-R4)
- **Architecture Planes** (1-7)
- **Feature Tracking** (CORE-*, DEP-*, MCP-*, etc.)
- **Status Tracking** (Design, Build, Test, Runtime, Production)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development workflow, coding standards, and pull request process.

## License

Apache 2.0 License - See [LICENSE](LICENSE) for details.

## Disclaimer

MCPServer OS provides technical evidence capabilities and configurable controls to support compliance efforts. It does not automatically confer legal or regulatory compliance. Organizations must obtain their own legal advice and compliance certifications as required by applicable laws and regulations.

**India-Specific Note**: While MCPServer OS includes India-first technical capabilities, actual compliance with DPDP Act, RBI Cyber Framework, or other Indian regulations requires appropriate organizational policies, procedures, and legal compliance efforts beyond technical controls.