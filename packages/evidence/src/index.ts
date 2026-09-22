/**
 * Evidence Ledger Core
 * 
 * Domain model for field-level evidence tracking and publication authority.
 * 
 * Publication authority rule (deterministic):
 *   published + evidence + verified       => indexable
 *   published + no evidence              => not indexable
 *   published + unverified               => not indexable
 *   draft + evidence + verified          => not indexable
 *   unknown status                       => not indexable
 */

// --- Value types ---

export interface EvidenceRef {
  id: string;
  sourceUrl: string;
  sourceType: "official" | "registry" | "repository" | "documentation" |
           "package-registry" | "measurement" | "editorial";
  status: "verified" | "unverified";
  lastChecked: string | null;
  supports: string[];
}

export interface Claim {
  id: string;
  serverId: string;
  field: string;
  claimValue: string;
  source: string;
  status: "verified" | "unverified" | "pending";
  evidenceRefIds: string[];
  createdAt: string;
  updatedAt: string;
}

export interface ClaimEvidenceLink {
  claimId: string;
  evidenceRefId: string;
  linkedAt: string;
}

export interface VerificationResult {
  claimId: string;
  verified: boolean;
  reason?: string;
  verifiedAt: string;
  verifier: "human" | "system" | "engine";
}

export interface PublicationDecision {
  serverId: string;
  published: boolean;
  indexable: boolean;
  reason: "published+evidence+verified" | "published+no-evidence" | 
          "published+unverified" | "draft+evidence+verified" | "unknown-status";
  decidedAt: string;
}

// --- Publication authority ---

/**
 * Publication authority: deterministic isServerIndexable() rule
 * 
 * Rules (all evaluated against a server's evidence ledger):
 *   - published + evidence + verified       => indexable
 *   - published + no evidence              => not indexable
 *   - published + unverified               => not indexable
 *   - draft + evidence + verified          => not indexable
 *   - unknown status                       => not indexable
 */
export function isServerIndexable(
  published: boolean,
  evidenceCount: number,
  evidenceVerified: boolean,
  status: "published" | "unverified" | "draft" | "unknown"
): PublicationDecision {
  if (status === "published" && evidenceVerified && evidenceCount > 0) {
    return {
      serverId: "",
      published: true,
      indexable: true,
      reason: "published+evidence+verified",
      decidedAt: new Date().toISOString()
    };
  }
  if (status === "published" && evidenceCount === 0) {
    return {
      serverId: "",
      published: true,
      indexable: false,
      reason: "published+no-evidence",
      decidedAt: new Date().toISOString()
    };
  }
  if (status === "published" && !evidenceVerified) {
    return {
      serverId: "",
      published: true,
      indexable: false,
      reason: "published+unverified",
      decidedAt: new Date().toISOString()
    };
  }
  if (status === "published" && evidenceVerified && evidenceCount > 0) {
    // This branch is technically unreachable due to above, but kept for completeness
    return {
      serverId: "",
      published: true,
      indexable: true,
      reason: "published+evidence+verified",
      decidedAt: new Date().toISOString()
    };
  }
  if (status === "draft" && evidenceVerified && evidenceCount > 0) {
    return {
      serverId: "",
      published: false,
      indexable: false,
      reason: "draft+evidence+verified",
      decidedAt: new Date().toISOString()
    };
  }
  // unknown status or any other case
  return {
    serverId: "",
    published: false,
    indexable: false,
    reason: "unknown-status",
    decidedAt: new Date().toISOString()
  };
}