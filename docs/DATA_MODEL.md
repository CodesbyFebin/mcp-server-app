# Data Model — MCPserver.in + app.mcpserver.in Shared Domain

## Evidence Model

### EvidenceRef (value type)
```typescript
interface EvidenceRef {
  id: string;            // Unique evidence identifier
  sourceUrl: string;     // URL where evidence was sourced
  sourceType: "official" | "registry" | "repository" | 
               "documentation" | "package-registry" | "measurement" | "editorial";
  status: "verified" | "unverified";  // Verification status
  lastChecked: string | null;  // ISO timestamp of last check, null if never
  supports: string[];    // Array of server IDs or fields this evidence supports
}
```

### Claim (value type)
```typescript
interface Claim {
  id: string;            // Unique claim identifier
  serverId: string;      // Associated MCP server
  field: string;         // Field being claimed (e.g., "description", "gstin")
  claimValue: string;    // The claimed value
  source: string;        // Source of the claim
  status: "verified" | "unverified" | "pending";  // Verification status
  evidenceRefIds: string[];  // IDs of EvidenceRef supporting this claim
  createdAt: string;     // ISO timestamp
  updatedAt: string;     // ISO timestamp
}
```

### ClaimEvidenceLink (value type)
```typescript
interface ClaimEvidenceLink {
  claimId: string;       // Associated claim
  evidenceRefId: string; // Supporting evidence
  linkedAt: string;      // ISO timestamp of the link
}
```

### VerificationResult (value type)
```typescript
interface VerificationResult {
  claimId: string;       // Associated claim
  verified: boolean;     // Whether the claim was verified
  reason?: string;       // Optional reason for the verdict
  verifiedAt: string;    // ISO timestamp of verification
  verifier: "human" | "system" | "engine";  // Who/what performed verification
}
```

### PublicationDecision (value type)
```typescript
interface PublicationDecision {
  serverId: string;      // Associated server
  published: boolean;    // Whether the server is published
  indexable: boolean;    // Whether the server is search-indexable
  reason: "published+evidence+verified" | "published+no-evidence" |
           "published+unverified" | "draft+evidence+verified" |
           "unknown-status";  // Deterministic reason string
  decidedAt: string;     // ISO timestamp of the decision
}
```

### isServerIndexable() — Centralized Publication Authority

**Deterministic rule** (single source of truth, used everywhere):

```typescript
function isServerIndexable(
  published: boolean,
  evidenceCount: number,
  evidenceVerified: boolean,
  status: "published" | "unverified" | "draft" | "unknown"
): { indexable: boolean; reason: string; decidedAt: string }
```

**Rules (evaluated in order)**:
1. `published && evidenceVerified && evidenceCount > 0` → `{ indexable: true, reason: "published+evidence+verified", decidedAt }`
2. `published && evidenceCount === 0` → `{ indexable: false, reason: "published+no-evidence", decidedAt }`
3. `published && !evidenceVerified` → `{ indexable: false, reason: "published+unverified", decidedAt }`
4. `status === "draft" && evidenceVerified && evidenceCount > 0` → `{ indexable: false, reason: "draft+evidence+verified", decidedAt }`
5. All other cases (including `unknown` status) → `{ indexable: false, reason: "unknown-status", decidedAt }`

**This function is the single source of truth** for indexability. Directory rendering,
static generation, sitemap generation, internal indexable links, llms.txt, llms-full.txt,
feeds and counts should consume this rule rather than duplicating it.

## Registry Model

### RegistryEntry (value type)
```typescript
interface RegistryEntry {
  id: string;            // Unique entry identifier (official registry ID preferred)
  type: "server" | "tool" | "resource" | "prompt";
  name: string;
  description: string;
  slug: string;          // URL-friendly identifier
  version: string;
  capabilities: string[];
  tags: string[];
  evidence: string[];    // Evidence reference IDs
  verificationStatus: "verified" | "unverified" | "pending";
  publicationStatus: "draft" | "published" | "archived";
  creator: string;
  createdAt: string;
  updatedAt: string;
}
```

### RegistryIdentity (value type)
```typescript
interface RegistryIdentity {
  registryId: string | null;        // Official registry-assigned ID (preferred)
  repositoryUrl: string | null;     // GitHub/GitLab URL
  packageIdentity: string | null;   // "name/version" hash
  canonicalHomepage: string | null; // Canonical homepage URL (null in current impl)
  displayName: string | null;       // Display name (least preferred for deduplication)
}
```

### RegistryNormalizer
Standardizes a raw RegistryEntry into canonical form, resolving identity based on
preferred order: registryId > repositoryUrl > packageIdentity > canonicalHomepage > displayName.

### RegistryDeduplicator
Resolves duplicate entries using identity precedence. Keeps the entry with the
highest-priority identity and most recent timestamp. Output: `{ unique, duplicates, resolutionLog }`.

### RegistryValidator
Validates registry entries and publication decisions.
- `validateEntry(entry): { valid, errors }` — checks required fields
- `validatePublicationDecision(published, evidenceCount, evidenceVerified, status): { valid, decision, reason }`

### isServerIndexable() (in registry package)
Same deterministic function as the evidence ledger version, ensuring consistency
across the system.

## Event Model (from contracts)

### EventEnvelope (Zod-validated schema)
```typescript
const EventEnvelopeSchema = z.object({
  eventId: z.string().uuid();
  eventType: z.string();
  aggregateId: z.string();
  aggregateType: z.string();
  sequence: z.number().int().positive();
  occurredAt: z.string().datetime();
  causedBy: z.lazy(() => z.object({
    causationId: z.string().uuid();
    correlationId: z.string().uuid().optional();
  }));
  actor: z.object({
    type: z.enum(['human', 'system', 'engine']);
    id: z.string();
  });
  payload: z.record(z.unknown());
  metadata: z.object({
    version: z.string();
    source: z.string();
    digest: z.string(); // SHA-256 hex
  });
  contractVersion: z.string();
  schemaVersion: z.string().default('1.0.0');
});
```

**Guarantees**:
- Sequence uniqueness per aggregate
- Immutable events
- Deterministic ordering
- Idempotency
- Correlation tracking

### EventStore interface
```typescript
interface EventStore {
  init(): Promise<void>;
  append(envelope: EventEnvelope | EventEnvelope[]): Promise<void>;
  getForAggregate(aggregateId: string): Promise<EventEnvelope[]>;
  getNextSequence(aggregateId: string): Promise<number>;
  getByEventId(eventId: string): Promise<EventEnvelope | null>;
  exists(eventId: string): Promise<boolean>;
  transaction(envelopes: EventEnvelope[]): Promise<void>;
}
```

**Implementations**:
- `MemoryEventStore` — in-memory, for unit tests
- `PgEventStore` — PostgreSQL, for production

### Timestamp & Digest (value types from common.ts)
```typescript
interface Timestamp {
  value: string;  // ISO 8601 datetime string
}

interface Digest {
  value: string;  // SHA-256 hex string
}
```

## Knowledge Graph Model (schema.org types)

### Entity-type mapping by route

| Route | Primary Type | Secondary Types |
|---|---|---|
| Homepage | Organization | WebSite |
| Directory /servers | CollectionPage | ItemList |
| /servers/[slug] | WebPage | SoftwareApplication |
| /glossary | DefinedTerm | — |
| /learn /docs | Article | TechArticle |
| /blog | BlogPosting | Article |
| Breadcrumbs | BreadcrumbList | — |
| FAQ | FAQPage | — only where genuine FAQ exists |

**Preservation rules**:
- Preserve Review markup only when the corresponding review exists, is visible,
  attributable, and supported by the migrated record.
- Same evidence gating applies to permissions, service specifications, price,
  ratings, compliance claims, availability, latency and other assertion-bearing fields.
- Do not automatically "give everything to every entity." Route-specific schemas only.

## Package Data Contracts

### @mcp/servers-contracts
- Shared TypeScript schemas (Phase A content contracts + Phase B registry contracts)
- EventEnvelopeSchema, EventStore interface
- Zod validators for runtime type checking
- Compiles with 0 TypeScript errors (strict mode)

### @mcp/servers-evidence
- EvidenceRef, Claim, ClaimEvidenceLink, VerificationResult, PublicationDecision
- isServerIndexable() centralized publication authority
- Compiles with 0 TypeScript errors

### @mcp/servers-registry
- RegistryEntry, RegistryEvent types
- RegistryIdentity, RegistrySource, RegistryVersion, RegistryChange
- RegistryNormalizer, RegistryDeduplicator, RegistryValidator
- isServerIndexable() — same function as evidence ledger
- Compiles with 0 TypeScript errors

### @mcp/servers-auth
- AuthCredentials, TokenPayload, AuthProvider types
- Compiles with 0 TypeScript errors

### @mcp/servers-api-client
- McpApiClient class with listServers, getServer, listTools, callTool,
  listResources, readResource, listPrompts, getPrompt methods
- StdioTransport, StreamableHttpTransport implementing McpTransport interface
- Compiles with 0 TypeScript errors

### @mcp/servers-design-tokens
- Color palette (navy, deep-navy, purple-blue, cyan, gradients)
- Typography (Inter, font sizes xs-3xl with lineHeight)
- Spacing (px-zero to 24), breakpoints (xs:320px to 2xl:1024px)
- Compiles with TypeScript strict:false (documented bounded exemption)

### @mcp/servers-mcp-server
- Production runtime baseline (FastMCP backend)
- Publication authority must be rewired to centralized Evidence Ledger

## Data Flow Summary

1. **Event sourcing**: Something happens → EventEnvelope → EventStore (Memory or Pg) →
   aggregate sequence tracking
2. **Evidence tracking**: Claim → EvidenceRef links → VerificationResult → PublicationDecision →
   isServerIndexable() → indexable / not indexable
3. **Registry tracking**: RegistryEntry → RegistryNormalizer → RegistryDeduplicator →
   identity resolution → PublicationDecision → isServerIndexable() → indexable / not indexable
4. **SEO & publication**: isServerIndexable() result → sitemap inclusion → llms.txt/ai.txt references →
   search engine discovery
5. **Knowledge graph**: Schema.org types per route → JSON-LD generation → structured data for AI agents

**Fail-closed principle**: Unknown status → not indexable. Missing evidence → not indexable.
Unverified claims → not indexable. Draft status → not indexable. This is by design, not accident.