/* Registry Synchronization Service for MCPserver.in

Pipeline: Source → Fetch → Normalize → Validate → Attach Evidence → Verify → Publication Decision → Public Registry

Implements the Phase 1.5 registry domain classes: RegistryNormalizer, RegistryDeduplicator, RegistryValidator
Centralized isServerIndexable() consistency across packages.
*/

import { RegistryEntry, RegistryIdentity, RegistrySource, RegistryVersion, RegistryChange } from "@mcp/servers-contracts";
import { RegistryNormalizer } from "@mcp/servers-registry";
import { RegistryDeduplicator } from "@mcp/servers-registry";
import { RegistryValidator } from "@mcp/servers-registry";
import { isServerIndexable } from "@mcp/servers-evidence";
import { PublicationDecision } from "@mcp/servers-evidence";
import { z } from "zod";

// ============================
// Persistence Port (injected at runtime)
// ============================

/**
 * Read/write port for the public registry store. Implementations are
 * injected by the deployment container (e.g., the FastMCP service's
 * PostgreSQL pool adapter) rather than imported from a skill package
 * that may not be present at compile time. If no adapter is supplied,
 * the service runs in-memory and skips persistence, returning the
 * normalized/validated entries without writing them to a backing store.
 */
export interface RegistryPersistencePort {
  /** Whether the backing store currently has an open connection. */
  readonly _connected: boolean;
  /** Execute a parameterized read/write SQL statement and return rows. */
  executeRead(sql: string, params?: unknown[]): Promise<unknown[]>;
}

/** No-op default: registry runs in-memory; persistence is skipped. */
class InMemoryRegistryPersistence implements RegistryPersistencePort {
  readonly _connected = false;
  async executeRead(_sql: string, _params?: unknown[]): Promise<unknown[]> {
    throw new Error("RegistryPersistencePort is not configured");
  }
}

// ============================
// Input Validation Schemas
// ============================

/** Source registry entry ingestion validation */
const SourceEntrySchema = z.object({
  id: z.string(),
  type: z.string(),
  name: z.string(),
  slug: z.string(),
  version: z.string(),
  capabilities: z.array(z.string()).optional(),
  tags: z.array(z.string()).optional(),
  description: z.string().optional(),
  sourceType: z.enum(["official", "registry", "repository", "documentation", "package-registry", "measurement", "editorial"]),
  sourceUrl: z.string().url(),
  retrievedAt: z.string().datetime(),
  publisher: z.string().optional(),
  license: z.string().optional(),
  labels: z.array(z.string()).optional(),
});

/** Publication decision input */
const PublicationDecisionSchema = z.object({
  published: z.boolean(),
  evidenceCount: z.number().int().min(0),
  evidenceVerified: z.boolean(),
  status: z.enum(["published", "unverified", "draft", "unknown"]),
});

/** Normalized output schema */
const NormalizedEntrySchema = z.object({
  registryId: z.string(),
  displayName: z.string(),
  slug: z.string(),
  type: z.string(),
  version: z.string(),
  capabilities: z.array(z.string()).default([]),
  tags: z.array(z.string()).default([]),
  source: z.object({
    sourceType: z.enum(["official", "registry", "repository", "documentation", "package-registry", "measurement", "editorial"]),
    sourceUrl: z.string().url(),
    retrievedAt: z.string().datetime(),
  }),
  identity: z.object({
    preferred: z.string().optional(),
    fallback: z.string().optional(),
  }),
  publicationDecision: z.object({
    indexable: z.boolean(),
    reason: z.string(),
    decidedAt: z.string().datetime(),
  }),
  changeMetadata: z.object({
    changeType: z.enum(["INSERT", "UPDATE", "DELETE"]),
    source: z.string(),
    triggeredAt: z.string().datetime(),
  }),
});

// ============================
// RegistrySyncService Class
// ============================

export class RegistrySyncService {
  private db: RegistryPersistencePort;
  batchSize: number;
  sourceTimeout: number;

  constructor(
    db?: RegistryPersistencePort,
    batchSize = 10,
    sourceTimeout = 30
  ) {
    this.db = db || new InMemoryRegistryPersistence();
    this.batchSize = batchSize;
    this.sourceTimeout = sourceTimeout;
  }

  /** Main pipeline: ingest source entries → public registry */
  async ingest(entries: any[], sources: any[]): Promise<{
    unique: RegistryEntry[];
    duplicates: { entry: any; reason: string }[];
    publicationDecisions: Array<{ entry: any; decision: PublicationDecision; reason: string }>;
    resolutionLog: string[];
  }> {
    const log: string[] = [];
    const startTime = Date.now();

    log.push(`=== Registry Ingest Start: ${entries.length} entries from ${sources.length} sources ===`);

    // Step 1: Normalize all entries
    const normalizer = new RegistryNormalizer();
    const normalized: any[] = [];
    
    for (let i = 0; i < entries.length; i++) {
      const entry = entries[i];
      const source = sources[i] || { sourceType: "editorial", sourceUrl: '', retrievedAt: new Date().toISOString() };
      
      try {
        const parsed = SourceEntrySchema.parse(entry);
        const { identity, normalized: normalizedEntry } = normalizer.normalize(parsed, source);
        normalized.push(normalizedEntry);
        log.push(`Entry ${i}: normalized successfully, identity=${identity.registryId || 'unknown'}`);
      } catch (error) {
        log.push(`Entry ${i}: normalization failed - ${error instanceof Error ? error.message : String(error)}`);
        // Skip entries that fail schema validation
      }
    }

    // Step 2: Deduplicate using identity precedence
    const deduplicator = new RegistryDeduplicator();
    const { unique, duplicates } = deduplicator.deduplicate(normalized, sources);
    
    log.push(`Deduplication result: ${unique.length} unique, ${duplicates.length} duplicates`);

    // Step 3: Validate each unique entry
    const validator = new RegistryValidator();
    const validationResults: Array<{ entry: any; result: { valid: boolean; errors: string[] } }> = [];
    
    const validatedEntries: any[] = [];
    
    for (const entry of unique) {
      const validation = validator.validateEntry(entry);
      validationResults.push({ entry, result: validation });
      
      if (validation.valid) {
        validatedEntries.push(entry);
        log.push(`Entry ${entry.id}: validation passed`);
      } else {
        log.push(`Entry ${entry.id}: validation failed - ${validation.errors.join('; ')}`);
        // Continue - entries with missing fields may still be processed
      }
    }

    // Step 4: Publication authority decision
    const publicationDecisions: Array<{ entry: any; decision: PublicationDecision; reason: string }> = [];
    
    for (const entry of validatedEntries) {
      const { published, evidenceCount, evidenceVerified, status } = entry;
      const { indexable, reason } = isServerIndexable(
        published, evidenceCount, evidenceVerified, status as "published" | "unverified" | "draft" | "unknown"
      );
      
      const decision: PublicationDecision = {
        serverId: entry.id || '',
        published,
        indexable,
        reason,
        decidedAt: new Date().toISOString(),
      };
      
      publicationDecisions.push({
        entry,
        decision,
        reason,
      });
      
      log.push(`Entry ${entry.id}: indexable=${indexable} - ${reason}`);
    }

    // Step 5: Persist to database (if DB connector available)
    if (this.db._connected) {
      try {
        for (const decision of publicationDecisions) {
          const { entry, decision: pubDecision } = decision;
          if (pubDecision.indexable) {
            // Publish to public registry
            await this.db.executeRead(
              `INSERT INTO servers (id, name, slug, transport, status, publisher, capabilities, tags) 
               VALUES ($1, $2, $3, 'streamable-http', 'healthy', $4, $5, $6)
               ON CONFLICT (id) DO UPDATE SET
                 name = EXCLUDED.name,
                 status = EXCLUDED.status,
                 capabilities = EXCLUDED.capabilities,
                 tags = EXCLUDED.tags,
                 updated_at = NOW()`,
              [entry.id, entry.name, entry.slug, pubDecision.reason, JSON.stringify(entry.capabilities), JSON.stringify(entry.tags)]
            );
            log.push(`Published to public registry: ${entry.id}`);
          } else {
            // Quarantine - not added to public registry
            log.push(`Quarantined (not indexable): ${entry.id} - ${pubDecision.reason}`);
          }
        }
      } catch (error) {
        log.push(`Database persist error: ${error instanceof Error ? error.message : String(error)}`);
      }
    }

    const duration = Date.now() - startTime;
    
    log.push(`=== Registry Ingest Complete: ${duration}ms ===`);
    log.push(`Summary: ${entries.length} source → ${unique.length} normalized → ${validatedEntries.length} validated → ${publicationDecisions.filter(d => d.decision.indexable).length} indexable, ${publicationDecisions.filter(d => !d.decision.indexable).length} quarantined`);

    return {
      unique,
      duplicates,
      publicationDecisions,
      resolutionLog: log,
    };
  }

  /** Ingest from a single source URL */
  async ingestFromSource(sourceUrl: string, entryType: "registry" | "evidence" = "registry"): Promise<{
    success: boolean;
    entriesProcessed: number;
    uniqueCount: number;
    indexableCount: number;
    quarantinedCount: number;
    resolutionLog: string[];
  }> {
    // Fetch entries from source (mock - integrate with real source)
    let entries: any[];
    let sources: any[];
    
    if (entryType === "registry") {
      // Mock registry source fetch
      entries = [
        {
          id: "server-001",
          type: "mcp-server",
          name: "Sample Server",
          slug: "sample-server",
          version: "1.0.0",
          capabilities: ["tool-calling", "resource-access"],
          tags: ["example", "demo"],
          description: "A sample MCP server for demonstration",
          sourceType: "registry",
          sourceUrl,
          retrievedAt: new Date().toISOString(),
          publisher: "MCP Organization",
          license: "MIT",
        },
      ];
      sources = [{ sourceType: "registry", sourceUrl, retrievedAt: new Date().toISOString() }];
    } else {
      entries = [];
      sources = [];
    }

    const result = await this.ingest(entries, sources);
    
    const indexableCount = result.publicationDecisions.filter(d => d.decision.indexable).length;
    const quarantinedCount = result.publicationDecisions.filter(d => !d.decision.indexable).length;
    
    return {
      success: true,
      entriesProcessed: entries.length,
      uniqueCount: result.unique.length,
      indexableCount,
      quarantinedCount,
      resolutionLog: result.resolutionLog,
    };
  }

  /** Generate sitemap entries for indexable servers */
  async generateSitemapEntries(): Promise<Array<{slug: string; lastmod: string; changefreq: string; priority: string}>> {
    const sitemapEntries: Array<{slug: string; lastmod: string; changefreq: string; priority: string}> = [];
    
    // In production, query the database for all indexable servers
    // For now, return mock entries based on the 400 KEEP classification
    const mockSlugs = [
      "math-solver", "text-generator", "image-analyzer", "code-assistant",
      "data-insight", "knowledge-base", "workflow-automation", "api-gateway",
    ];
    
    const now = new Date().toISOString().split("T")[0];
    
    for (const slug of mockSlugs) {
      sitemapEntries.push({
        slug,
        lastmod: now,
        changefreq: "weekly",
        priority: "0.8",
      });
    }
    
    return sitemapEntries;
  }

  /** Generate robots.txt content */
  generateRobotsTxt(): string {
    return `
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
`.trim();
  }

  /** Health check */
  async healthCheck(): Promise<{healthy: boolean; entriesProcessed: number; indexableCount: number; quarantinedCount: number}> {
    const log = await this.ingest([], []);
    
    return {
      healthy: true,
      entriesProcessed: 0,
      indexableCount: 0,
      quarantinedCount: 0,
    };
  }
}

// ============================
// Convenience Functions
// ============================

/** Quick registry sync from a source URL */
export async function quickSync(sourceUrl: string, batchSize = 10): Promise<{
  success: boolean;
  entriesProcessed: number;
  uniqueCount: number;
  indexableCount: number;
  quarantinedCount: number;
  resolutionLog: string[];
}> {
  const service = new RegistrySyncService(undefined, batchSize);
  return service.ingestFromSource(sourceUrl);
}

/** Generate sitemap XML for indexable servers */
export function generateSitemapXml(entries: Array<{slug: string; lastmod: string; changefreq: string; priority: string}>): string {
  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  ${entries.map(e => `
    <url>
      <loc>https://www.mcpserver.in/servers/${e.slug}</loc>
      <lastmod>${e.lastmod}</lastmod>
      <changefreq>${e.changefreq}</changefreq>
      <priority>${e.priority}</priority>
    </url>`).join("")}
</urlset>`;
  
  return xml;
}

// ============================
// Example Usage
// ============================

if (require.main === module) {
  console.log("Registry Sync Service — Example Usage");
  console.log("");
  console.log("This module provides the RegistrySyncService class for");
  console.log("MCP registry synchronization and publication authority enforcement.");
  console.log("");
  console.log("Key functions:");
  console.log("  - ingest(entries, sources): Full pipeline execution");
  console.log("  - ingestFromSource(sourceUrl): Single source ingestion");
  console.log("  - generateSitemapEntries(): Sitemap generation for indexable servers");
  console.log("  - generateRobotsTxt(): Crawl controls robots.txt");
  console.log("");
  console.log("Publication authority rules (deterministic, fail-closed):");
  console.log("  • published + evidence + verified + published => indexable");
  console.log("  • published + no evidence => not indexable");
  console.log("  • published + unverified => not indexable");
  console.log("  • draft + evidence + verified => not indexable");
  console.log("  • unknown status => not indexable");
}