/* JSON-LD Schema Generation for MCPserver.in

Provides structured data for all public surfaces per the Phase 1.5 architecture.
Schemas are generated dynamically from the Evidence Ledger and Registry data.
*/

import { z } from "zod";

// ============================
// Schema Types
// ============================

/** Organization schema - MCPserver.in itself */
const organizationSchema = {
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "MCPserver.in",
  "description": "Model Context Protocol Server Directory and Knowledge Graph",
  "url": "https://www.mcpserver.in",
  "logo": "https://www.mcpserver.in/logo.png",
  "sameAs": [
    "https://app.mcpserver.in",
    "https://github.com/mcp-server",
  ],
};

/** WebSite schema with SearchAction */
const websiteSchema = {
  "@context": "https://schema.org",
  "@type": "WebSite",
  "name": "MCPserver.in",
  "url": "https://www.mcpserver.in",
  "description": "Model Context Protocol Server Directory and Knowledge Graph",
  "potentialAction": [
    {
      "@type": "SearchAction",
      "target": "https://www.mcpserver.in/results?q={search_term_string}",
      "query-input": "required name=search_term_string",
    }
  ],
}

/** SoftwareApplication schema for homepage */
const softwareApplicationSchema = {
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "MCPserver.in",
  "description": "Model Context Protocol Server Directory and Knowledge Graph",
  "url": "https://www.mcpserver.in",
  "operatingSystem": " agnostic",
  "softwareVersion": "5.0.0 (SAFE-DEEP OS)",
  "creator": "Organization ref: #organizationSchema",
}

/** ItemList schema for server directory */
const itemListSchemaBase = {
  "@context": "https://schema.org",
  "@type": "ItemList",
  "numberOfItems": 0,  // Dynamic - populated at runtime
  "itemListElement": [],  // Dynamic - populated at runtime
}

/** FAQPage schema */
const faqSchema = {
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "What is MCP?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Model Context Protocol - a standard for server discovery, tool access, and knowledge graph integration.",
      },
    },
    {
      "@type": "Question",
      "name": "How do I publish a server?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Servers must pass the isServerIndexable() publication authority: published + evidence + verified => indexable. Fail-closed: any missing condition remains outside the indexable knowledge graph.",
      },
    },
  ],
}

/** HowTo schema for onboarding */
const howToSchema = {
  "@context": "https://schema.org",
  "@type": "HowTo",
  "name": "Onboard to MCPserver.in",
  "description": "Guide for publishing and discovering MCP servers",
  "step": [
    {
      "text": "Register your MCP server with full metadata (identity, capabilities, tags).",
      "position": 1,
    },
    {
      "text": "Publish evidence supporting your server's claims (source URLs, verification status).",
      "position": 2,
    },
    {
      "text": "Pass the isServerIndexable() publication authority check (published + evidence + verified).",
      "position": 3,
    },
    {
      "text": "Your server appears in /servers and is indexable by AI agents.",
      "position": 4,
    },
  ],
}

/* ============================
// Export Schemas
// ============================ */

export const schemas = {
  organization: organizationSchema,
  website: websiteSchema,
  softwareApplication: softwareApplicationSchema,
  itemListBase: itemListSchemaBase,
  faq: faqSchema,
  howTo: howToSchema,
}

/* ============================
# Runtime Schema Generator
# ============================

/** Generate complete JSON-LD for homepage */
export function generateHomepageLd(
  serverCount: number,
  integrationCount: number,
  categoryCount: number,
  recentExecutions: number
) {
  return [
    // Organization schema
    { ...schemas.organization, "@type": "Organization" },

    // WebSite schema
    schemas.website,

    // SoftwareApplication schema
    { ...schemas.softwareApplication, "@type": "SoftwareApplication" },

    // ItemList for featured servers (top 8)
    {
      "@context": "https://schema.org",
      "@type": "ItemList",
      "numberOfItems": serverCount,
      "itemListElement": Array.from({ length: Math.min(8, serverCount) }, (_, i) => ({
        "@type": "ListItem",
        "position": i + 1,
        "item": {
          "@id": `https://www.mcpserver.in/servers/${String(i + 1).padStart(3, "0")}`,
          "name": `Server ${i + 1}`,
        },
      })),
    },

    // FAQ schema
    schemas.faq,

    // HowTo schema
    schemas.howTo,
  ];
}

/** Generate JSON-LD for /servers page */
export function generateServersLd(serverEntries: Array<{
  slug: string;
  name: string;
  description?: string;
  publisher: string;
  status: "healthy" | "degraded" | "unknown";
  capabilities: string[];
}>) {
  return [
    schemas.website,

    {
      "@context": "https://schema.org",
      "@type": "ItemList",
      "numberOfItems": serverEntries.length,
      "itemListElement": serverEntries.map((entry, i) => ({
        "@type": "ListItem",
        "position": i + 1,
        "item": {
          "@id": `https://www.mcpserver.in/servers/${entry.slug}`,
          "name": entry.name,
          "description": entry.description || `${entry.publisher} server`,
          "url": `https://www.mcpserver.in/servers/${entry.slug}`,
        },
      })),
    },
  ];
}

/** Generate JSON-LD for individual server page */
export function generateServerLd(
  server: {
    slug: string;
    name: string;
    description: string;
    publisher: string;
    status: "healthy" | "degraded" | "unknown";
    capabilities: string[];
    version?: string;
    evidence: Array<{ type: string; sourceUrl: string; verified: boolean }>;
  },
  publicationDecision: { indexable: boolean; reason: string }
) {
  const base: Record<string, any> = {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    "name": server.name,
    "description": server.description,
    "url": `https://www.mcpserver.in/servers/${server.slug}`,
    "operatingSystem": "agnostic",
    "softwareVersion": server.version || "5.0.0",
  };

  // Add evidence-backed properties
  if (server.evidence && server.evidence.length > 0) {
    base["audit"] = server.evidence.map((ev) => ({
      "@type": "Audit",
      "name": ev.type,
      "subject": `https://www.mcpserver.in/servers/${server.slug}`,
      "entity": {
        "@type": "Organization",
        "name": server.publisher,
      },
      "result": ev.verified ? "http://schema.org/VerifyAction" : "unverified",
      "source": ev.sourceUrl,
    }));
  }

  // Publication decision
  if (publicationDecision.indexable) {
    base["isBasedOnUrl"] = `https://www.mcpserver.in/servers/${server.slug}`;
    base["datePublished"] = new Date().toISOString().split("T")[0];
  }

  return base;
}

/** Generate JSON-LD for /integrations page */
export function generateIntegrationsLd(integrationEntries: Array<{
  name: string;
  description: string;
  url: string;
  category: string;
}>) {
  return [
    schemas.website,

    {
      "@context": "https://schema.org",
      "@type": "ItemList",
      "numberOfItems": integrationEntries.length,
      "itemListElement": integrationEntries.map((entry, i) => ({
        "@type": "ListItem",
        "position": i + 1,
        "item": {
          "@id": entry.url,
          "name": entry.name,
          "description": entry.description,
          "url": entry.url,
        },
      })),
    },
  ];
}

/** Generate JSON-LD for /clients page */
export function generateClientsLd(clientEntries: Array<{
  name: string;
  description: string;
  type: string;
  url: string;
}>) {
  return [
    schemas.website,

    {
      "@context": "https://schema.org",
      "@type": "ItemList",
      "numberOfItems": clientEntries.length,
      "itemListElement": clientEntries.map((entry, i) => ({
        "@type": "ListItem",
        "position": i + 1,
        "item": {
          "@id": entry.url,
          "name": entry.name,
          "description": entry.description,
          "url": entry.url,
        },
      })),
    },
  ];
}

/** Generate JSON-LD for /evidence page */
export function generateEvidenceLd(evidenceEntries: Array<{
  id: string;
  sourceUrl: string;
  sourceType: "official" | "registry" | "repository" | "documentation" | "package-registry" | "measurement" | "editorial";
  status: "verified" | "unverified";
  supports: string[];
}>) {
  return [
    schemas.website,

    {
      "@context": "https://schema.org",
      "@type": "DefinedTerm",
      "termCode": "MCP-evidence",
      "alternateName": "evidence-ledger",
      "description": "Publication authority and evidence ledger for MCPserver.in",
      "termStatus": "active",
      "providedBy": {
        "@type": "Organization",
        "name": "MCPserver.in",
      },
    },
    // Evidence entries as structured list
    {
      "@context": "https://schema.org",
      "@type": "ItemList",
      "numberOfItems": evidenceEntries.length,
      "itemListElement": evidenceEntries.map((entry) => ({
        "@type": "DefinedTerm",
        "termCode": entry.id,
        "description": `${entry.sourceType} evidence: ${entry.sourceUrl}`,
        "termStatus": entry.status ? "verified" : "unverified",
        "supplementalProperty": {
          "supports": entry.supports,
        },
      })),
    },
  ];
}

/** Generate JSON-LD for /methodology page */
export function generateMethodologyLd() {
  return [
    schemas.website,

    {
      "@context": "https://schema.org",
      "@type": "DefinedTerm",
      "termCode": "MCP-methodology",
      "description": "SAFE-DEEP OS v5 architecture with Phase A (Content contracts) and Phase B (Registry contracts)",
      "termStatus": "active",
      "alternateName": "SAFE-DEEP OS v5",
      "providedBy": {
        "@type": "Organization",
        "name": "MCPserver.in",
      },
      "exampleOfUsage": "Full lifecycle: content-addressed artifacts → event sourcing → publication authority → knowledge graph indexing",
    },
  ];
}

/** Generate JSON-LD for /docs page */
export function generateDocsLd(docsEntries: Array<{
  title: string;
  description: string;
  url: string;
  type: "article" | "faq" | "how-to";
}>) {
  const items = docsEntries.map((entry) => {
    if (entry.type === "faq") {
      return {
        "@type": "FAQPage",
        "mainEntity": [
          {
            "@type": "Question",
            "name": entry.title.split("?").pop() || entry.title,
            "acceptedAnswer": {
              "@type": "Answer",
              "text": entry.description,
            },
          },
        ],
      };
    } else if (entry.type === "how-to") {
      return {
        "@context": "https://schema.org",
        "@type": "HowTo",
        "name": entry.title,
        "description": entry.description,
        "step": Array.from({ length: 3 }, (_, j) => ({
          "position": j + 1,
          "text": `Step ${j + 1}: ${entry.description}`,
        })),
      };
    } else {
      // Default to Article
      return {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": entry.title,
        "description": entry.description,
        "url": entry.url,
      };
    }
  });

  return [
    schemas.website,

    {
      "@context": "https://schema.org",
      "@type": "ItemList",
      "numberOfItems": items.length,
      "itemListElement": items,
    },
  ];
}

/** Generate JSON-LD for /glossary page */
export function generateGlossaryLd(termEntries: Array<{
  term: string;
  definition: string;
  definedTerm: string;
  category: string;
}>) {
  return [
    schemas.website,

    {
      "@context": "https://schema.org",
      "@type": "DefinedTerm",
      "termCode": "glossary",
      "alternateName": "defined-term",
      "description": "SAFE-DEEP OS v5 glossary of terms and concepts",
      "termStatus": "active",
      "providedBy": {
        "@type": "Organization",
        "name": "MCPserver.in",
      },
      "exampleOfUsage": "Used across all knowledge graph surfaces for schema.org type consistency",
    },
    // Terms as list
    {
      "@context": "https://schema.org",
      "@type": "ItemList",
      "numberOfItems": termEntries.length,
      "itemListElement": termEntries.map((entry) => ({
        "@type": "DefinedTerm",
        "termCode": entry.term,
        "description": entry.definition,
        "termStatus": "active",
      })),
    },
  ];
}