# Evidence Model — Publication Authority & Indexability

## Purpose

This document defines the evidence model and publication authority for the MCPserver.in +
app.mcpserver.in dual-product system. It provides a deterministic, fail-closed mechanism
for determining whether an MCP server is indexable by search engines and AI agents.

## Core Principles

### Fail-Closed

The publication authority is fail-closed: any unknown or unverified state defaults to
"not indexable." This is by design, not accident. The system never assumes indexability.

### Centralized Authority

There is exactly one `isServerIndexable()` function. All parts of the system —
sitemap generation, llms.txt rendering, internal linking, search engine exposure —
must consume this single function rather than duplicating the logic.

### Evidence-First

Indexability requires positive evidence:
- Server must be `published`
- Server must have `qualifying evidence` (verified status)
- Server must not have `noindex` flag

### Unknown is Not Indexable

Any status not explicitly covered by the rules defaults to "not indexable."
This includes unknown publicationStatus, unknown verificationStatus, and any
future statuses not added to the enum.

## Publication Decision Rules

The `isServerIndexable()` function evaluates four parameters in order:

| Parameter | Type | Description |
|---|---|---|
| `published` | boolean | Is the server's publicationStatus "published"? |
| `evidenceCount` | number | How many qualifying EvidenceRef entries exist? |
| `evidenceVerified` | boolean | Is at least one EvidenceRef verified? |
| `status` | enum | Current status: "published" | "unverified" | "draft" | "unknown" |

### Rule Evaluation Order

```text
1. published && evidenceVerified && evidenceCount > 0
   → indexable = true
   → reason = "published+evidence+verified"

2. published && evidenceCount === 0
   → indexable = false
   → reason = "published+no-evidence"

3. published && !evidenceVerified
   → indexable = false
   → reason = "published+unverified"

4. status === "draft" && evidenceVerified && evidenceCount > 0
   → indexable = false
   → reason = "draft+evidence+verified"

5. All other cases (including status === "unknown")
   → indexable = false
   → reason = "unknown-status"
```

## Publication Cohorts

### Indexable Servers
- `published: true`
- At least one `EvidenceRef` with `status: "verified"`
- Appear in search results, AI agent indexes, directory listings
- Included in sitemap.xml, llms.txt, llms-full.txt

### Non-Indexable Servers (published but no qualifying evidence)
- `published: true`, but no verified evidence
- Do NOT appear in search results or AI agent indexes
- May still be accessible via direct URL, but not crawled/indexed
- NOT included in sitemap.xml

### Draft/Unverified/Unknown Servers
- `published: false` (draft), or `verificationStatus: "unverified"`, or `status: "unknown"`
- Do NOT appear in search results or AI agent indexes
- NOT included in sitemap.xml or llms feeds

## Evidence Ledger Workflow

### 1. Evidence Collection
- Source URLs are crawled and assessed
- EvidenceRef records are created with sourceType, status, supports fields
- `lastChecked` timestamp records when the assessment occurred

### 2. Claim Formation
- Specific field claims are made about servers (e.g., GSTIN format, capability claims)
- Claim records link to EvidenceRef via ClaimEvidenceLink
- VerificationResult records mark claims as verified/unverified/pending

### 3. Publication Decision
- All claims for a server are aggregated
- isServerIndexable() is called with the aggregated state
- Result determines whether the server appears in search indexes

### 4. Audit Trail
- Every decision logs the `decidedAt` timestamp
- The `reason` field records which rule branch was taken
- Audit events are structured JSON, no sensitive payloads

## Indexable Field Guidelines

### What makes evidence "qualifying" for indexability

Evidence is qualifying when:
- `evidence.status === "verified"` — explicitly verified by the system
- `evidence.status === "measured"` — measured/observed data that supports indexability
- The evidence `supports` field includes the server ID or relevant field

Evidence is NOT qualifying when:
- `evidence.status === "unverified"` — disputed or unconfirmed
- `evidence.status` is any other future enum value not listed above
- The evidence `supports` field does not include the relevant server/field
- No evidence exists (evidenceCount === 0)

### noindex Flag

If a server record has `noindex: true` (set via meta tag, HTTP header, or
explicit PublicationDecision), the server is never indexable regardless of
other conditions. This is an explicit opt-out mechanism.

## Deterministic Guarantees

Given the same input parameters, `isServerIndexable()` always returns the same
output. There is no hidden state, no configuration, no runtime dependencies.

The function is pure — given `(published, evidenceCount, evidenceVerified, status)`,
it returns `({indexable, reason, decidedAt})`. This enables:
- Caching at CDN edge
- Static generation at build time
- Consistency across all deployment environments
- Static analysis and verification

## Integration Points

### Sitemap Generation
```typescript
// Only include servers where isServerIndexable() returns true
sitemap.entries = filter(
  allServers,
  server => isServerIndexable(
    server.publicationStatus === "published",
    server.evidence.filter(e => e.status === "verified").length,
    server.evidence.some(e => e.status === "verified" || e.status === "measured") > 0,
    server.verificationStatus // or derive from evidence
  )
)
```

### llms.txt / llms-full.txt
```typescript
// Only reference indexable servers
llmsEntries = filter(
  allServers,
  server => isServerIndexable(...)
)
```

### Internal Linking
Navigation, related-server suggestions, and "discoverable" links should only
connect to servers where isServerIndexable() = true.

### AI Agent Exposure
AI citation and attribution should only reference indexable servers. The
publication authority function is the gate.

### SEO Audit
Regular audits should verify that isServerIndexable() results are consistent
across all systems. Any drift should be flagged and investigated.

## API Contract

```typescript
// from packages/evidence/src/index.ts
export function isServerIndexable(
  published: boolean,
  evidenceCount: number,
  evidenceVerified: boolean,
  status: "published" | "unverified" | "draft" | "unknown"
): { indexable: boolean; reason: string; decidedAt: string }
```

```typescript
// from packages/registry/src/index.ts
export { isServerIndexable };
// Same function, same implementation, in both packages
```

Both the evidence and registry packages export the identical `isServerIndexable()`
function. They must remain in sync — any change to one must be reflected in the other.

## Unknown State Handling

The function explicitly handles four status values:

| status value | indexable | reason |
|---|---|---|
| "published" | depends on evidence | branch 1, 2, or 3 above |
| "unverified" | false | "published+unverified" (branch 3) |
| "draft" | depends on evidence | branch 4 or 5 above |
| "unknown" | false | "unknown-status" (branch 5) |

Any future enum values added to the status field must be handled explicitly —
the function is not exhaustive in a way that would allow fallthrough. This is
enforced by TypeScript's exhaustiveness checking on the union type.

## Fail-Closed In Practice

| Scenario | publicationStatus | verificationStatus | evidenceCount | evidenceVerified | indexable |
|---|---|---|---|---|---|
| Verified server | "published" | "verified" | 3 | true | true |
| Unverified server | "published" | "unverified" | 5 | false | false |
| No evidence | "published" | "verified" | 0 | false | false |
| Draft server | "draft" | "verified" | 5 | true | false |
| Unknown status | "published" | "verified" | 3 | true | false (unknown-status) |
| Noindex server | "published" | "verified" | 3 | true | false (noindex override) |

This table demonstrates the fail-closed behavior: the last row shows that even with
all-positive evidence, an explicit noindex override prevents indexability.

## Future Extensions

The function is designed to be extended while maintaining backward compatibility:

1. New `status` enum values must be handled explicitly (TypeScript exhaustiveness check)
2. New evidence status values require a decision in the rule evaluation order
3. The `reason` string can be extended but should follow the established pattern
4. The `decidedAt` timestamp should always be set to `new Date().toISOString()`

No removal or change of existing branches is permitted without a version bump
to the function's contract and a review of all integration points.