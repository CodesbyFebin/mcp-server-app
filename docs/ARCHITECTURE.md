# Architecture — MCPserver.in + app.mcpserver.in Dual-Product System

## Executive Summary

Build two coordinated products over a shared domain model:
- **Product A**: MCPserver.in (public authority website for discovery, SEO/AEO/GEO)
- **Product B**: app.mcpserver.in (mobile-first MCP workspace app)

Both products share contracts, evidence model, registry schemas, but remain independently deployable.

## Phase 1: Foundation & Monorepo Setup (Complete)

### 1.1 Repository Structure
Monorepo at `app-mcpserver-in/` with turbo workspaces config, 7 `@mcp/servers-*` packages,
3 apps (web, app), and 8 services.

### 1.2 Shared Contracts Package
File: `packages/contracts/src/`
- MCP domain types
- Evidence model (EvidenceRef interface → upgraded full domain)
- Registry schemas (upgraded with identity resolution)
- Authentication primitives
- API schemas
- Server/Tool/Resource/Prompt types

### 1.3 Evidence Ledger Core
File: `packages/evidence/src/`
- EvidenceRef, Claim, ClaimEvidenceLink, VerificationResult, PublicationDecision
- Centralized isServerIndexable() publication authority function
- Deterministic fail-closed rule: published && verified && qualifyingEvidence && !noindex

### 1.4 Registry Domain
File: `packages/registry/src/`
- RegistryEntry, RegistryEvent, Blueprint/Generator/Section/Engine Entry types
- RegistryIdentity with preferred→fallback resolution order
- RegistryNormalizer, RegistryDeduplicator, RegistryValidator
- Centralized isServerIndexable() function

## Phase 2: MCPserver.in Public Website (Planned)

### 2.1 Next.js 14 App Router Setup
File: `apps/web/app/`
- App Router with SSR/SSG
- Deep navy/black canvas design
- Purple-blue-cyan gradient system
- Glass morphism effects

### 2.2 Core Routes
- `/` - Homepage with HERO, Evidence Ledger, Server Discovery
- `/servers/` - AI-indexed directory with ItemList schema
- `/servers/[slug]/` - Individual server pages
- `/integrations/` - Integration directory
- `/clients/` - Client libraries
- `/learn/` - Documentation
- `/docs/` - Technical docs
- `/glossary/` - Glossary with DefinedTerm schema (post-pruning)
- `/blog/` - Blog with Article schema
- `/state-of-mcp/` - Research
- `/about/` / `/security/` / `/editorial-policy/`

### 2.3 AI Search Readiness Files (root directory)
1. `llms.txt` - AI agent guide with key pages and topics
2. `ai.txt` - Crawler permissions (opt-in)
3. `security.txt` - Security contact
4. `humans.txt` - Team attribution

### 2.4 Structured Data (JSON-LD)
- Homepage: SoftwareApplication schema
- Registry: ItemList schema for servers
- Server pages: SoftwareApplication + Evidence
- FAQs: FAQPage schema
- Blog: Article schema

### 2.5 robots.txt
```
User-agent: *
Allow: /
Disallow: /api/
Disallow: /drafts/
Disallow: /internal/

User-agent: GPTBot
Allow: /
User-agent: ClaudeBot
Allow: /
User-agent: PerplexityBot
Allow: /
Sitemap: https://www.mcpserver.in/sitemap.xml
```

### 2.6 llms.txt
```
## MCPserver.in — AI Agent Guide

This is the official MCPserver.in domain. Key pages:
- /servers — AI-indexed server directory
- /servers/[slug] — Individual server pages
- /glossary — Core glossary (post-pruning)
- /learn — Documentation and research
- /state-of-mcp — MCP research overview
- /docs — Technical documentation
- /blog — Blog posts and articles

Crawler permissions: ai.txt allows indexing. security.txt on file.
```

## Phase 3: FastMCP Backend Service (Planned)

### 3.1 FastMCP Structure
Python MCP server with India tools (GST, UPI, PAN/CIN, IFSC) and multi-LLM gateway.

### 3.2 India Enterprise Tools
- GST Validation: 15-char regex pattern
- UPI Validation: VPA syntax user@handle
- PAN/CIN: 5L+4D+1L pattern, 21-char CIN decoder
- IFSC: 11-char alphanumeric, bank + branch extraction

### 3.3 Multi-LLM Gateway
Provider abstraction with auto-fallback cascade:
1. Preferred provider (Gemini/Nvidia/Cloudflare)
2. Compatible fallback
3. Local Ollama/vLLM
4. Explicit failure

### 3.4 Skill Bridges
Web search bridge, document parser, database connector.

## Phase 4: app.mcpserver.in Mobile App (Planned)

### 4.1 Next.js App Router Mobile-First
File: `apps/app/app/`
- Mobile-first breakpoints: 320, 375, 390, 414, 768
- Bottom navigation, touch targets ≥44px, safe area support

### 4.2 Navigation Structure
Primary (bottom nav): Home, Servers, Playground, Skills, Activity
Secondary (hamburger): Gateway, Models, Workflows, Settings

### 4.3 Key Pages
- Home: Search bar (priority), system status, quick actions, recent activity
- Servers: Card layout with icon, name, publisher, verification, connect button
- Playground: Server selector, session management, tool execution, JSON-RPC inspector
- Skills: Skill selection, input configuration, preview actions, run→progress→result→history

### 4.4 MCP Client Library
File: `apps/app/lib/mcp-client.ts`
```typescript
interface McpTransport {
  connect(): Promise<void>;
  request<T>(method: string, params?: unknown): Promise<T>;
  close(): Promise<void>;
}
```

### 4.5 JSON-RPC Inspector
Initialize, tools/list, tools/call, resources/list, resources/read,
prompts/list, prompts/get, request/response viewer, latency tracking.

## Phase 5: API Service & Database (Planned)

### 5.1 API Service
File: `services/api/`
- Authentication (OIDC/OAuth, passkeys, MFA)
- Organizations/Teams/Users, Servers/Tools/Resources/Prompts
- Execution history, Skills/Workflows, Model providers, User preferences

### 5.2 Database Schema (PostgreSQL + Drizzle)
Core Entities: User, Organization, Team, Server, Tool, Resource, Prompt,
Evidence, Policy, Approval, Execution, Workflow, Skill, ModelProvider, AuditEvent.

### 5.3 Evidence Ledger
- Field-level evidence tracking
- Source validation
- Publication decision logic
- Audit trails

## Phase 6: Registry Service (Planned)

### 6.1 Registry Sync Service
File: `services/registry-sync/`
- Official registry ingestion
- Source normalization
- Deduplication (via RegistryDeduplicator)
- Provenance tracking
- Capability normalization
- Evidence linking
- Publication review (via isServerIndexable())

### 6.2 Pipeline
Source → Fetch → Normalize → Validate → Attach Evidence → Verify → Publication Decision → Public Registry

## Phase 7: Security & Compliance (Planned)

### 7.1 Sensitive Data Protection
Client-side masking (PAN, GSTIN, Aadhaar, email, phone), server-side redaction,
hashing for audit, PII never logged raw, structured audit fields.

### 7.2 Authentication & Authorization
OIDC/OAuth with passkeys, MFA support, bearer tokens, JWT validation,
RBAC: Admin/Developer/Read-Only, organization boundaries.

### 7.3 Policy Engine
Order: 1. Organization boundary 2. Explicit deny 3. Admin override
4. Explicit allow 5. Rate/budget constraint 6. Approval requirement
7. Default deny

### 7.4 Approvals
One-shot approvals, expiring, auditable, non-replayable, bound to:
actor, org, server, tool, argumentsHash, risk, expiration.

### 7.5 Network Security
SSRF protection, protocol validation, hostname validation, private IP blocking,
DNS rebinding prevention, timeout enforcement.

## Phase 8: Deployment & Infrastructure (Planned)

### 8.1 Docker Compose
8 services: web, app, api, mcp-server, gateway, redis, postgres, caddy.

### 8.2 Caddy Configuration
Reverse proxy with websocket upgrade for /v1/mcp*, noindex headers for drafts.

### 8.3 Environment
.env.example with all variables, no secrets committed, dev/staging/prod separation.

## Phase 9: Observability & Testing (Planned)

### 9.1 Observability
Structured JSON logs (no sensitive payloads), request count/latency/errors,
MCP tool latency, model latency, provider fallback events, workflow execution,
skill execution, database health, cache health, container health.

### 9.2 Testing
Frontend: unit tests, component tests, E2E tests, MCP protocol tests.
Backend: Pytest, integration tests, policy tests (ALLOW/DENY/REQUIRE_APPROVAL).

## Phase 10: SEO/AEO/GEO & Launch (Planned)

### 10.1 Performance
MCPserver.in: LCP <2.5s, CLS <0.1, INP <200ms
app.mcpserver.in: Fast first render, minimal JS

### 10.2 Accessibility
Semantic HTML, keyboard support, focus states, screen reader labels,
contrast, touch targets ≥ appropriate size.

### 10.3 Publication Verification
Verify: indexableServers = /servers, sitemap correctness, llms feeds,
JSON feeds, JSON-LD, search consistency, related servers.
No drift allowed between systems.

## Deliverables

**Product A - MCPserver.in**: Public authority website, evidence-backed discovery,
AI-indexed registry, SEO/AEO/GEO optimized, llms.txt/ai.txt/security.txt/humans.txt,
JSON-LD schemas.

**Product B - app.mcpserver.in**: Mobile-first workspace, MCP playground,
multi-LLM gateway, skills automation, workflow builder, execution history.

**Shared**: Contracts package, Evidence ledger, Registry domain,
Authentication contracts, Design tokens.

## Success Criteria

Both products deployed independently with shared contracts, no fabricated data,
verified runtime, production monitoring.

**Timeline**: 12 weeks (Phase 1 complete, Phase 2-10 planned)
**Status**: Foundation hardened, ready for Phase 2 implementation.