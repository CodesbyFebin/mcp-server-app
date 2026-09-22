/* Multi-LLM Gateway Client for MCPserver.in

The provider routing logic ("ProviderRouter") lives in the FastMCP Python
service at `services/mcp-server/gateway/router.py` and is exposed over HTTP
by that backend. Caddy routes `/v1/mcp*` directly to FastMCP (Phase 8.2),
so this package does not re-implement routing — it provides a typed client
for the gateway's admin/health surface and a deterministic forwarder for
completion requests.

This keeps a single source of truth for routing (the Python router) while
giving the TypeScript workspace a compile-time-checked adapter.
*/

import { z } from "zod";

// ============================
// Provider Types (mirror services/mcp-server/gateway/router.py)
// ============================

/** LLM provider identifiers, kept in sync with the Python `Provider` enum. */
export type ProviderName =
  | "gemini"
  | "nvidia"
  | "cloudflare"
  | "ollama"
  | "vllm"
  | "another";

/** Provider health status, mirroring the Python `HealthStatus` enum. */
export type HealthStatus = "healthy" | "degraded" | "unhealthy" | "unknown";

/** Health snapshot for a single provider, returned by `healthCheckAll`. */
export interface ProviderHealth {
  status: HealthStatus;
  successCount: number;
  errorCount: number;
  lastHealthCheck: number;
}

/** Result of a routed completion request, mirroring `route_complete`. */
export interface CompletionResult {
  provider: ProviderName;
  model: string;
  result: string;
  latencyMs: number;
  fallback: boolean;
}

/** Failure envelope returned when every provider in the cascade is down. */
export interface CompletionFailure {
  error: string;
  lastError: string | null;
  fallback: false;
}

// ============================
// Response Schemas (runtime validation of upstream responses)
// ============================

const ProviderHealthSchema = z.object({
  status: z.enum(["healthy", "degraded", "unhealthy", "unknown"]),
  successCount: z.number().int().min(0),
  errorCount: z.number().int().min(0),
  lastHealthCheck: z.number(),
});

const CompletionResultSchema = z.object({
  provider: z.enum(["gemini", "nvidia", "cloudflare", "ollama", "vllm", "another"]),
  model: z.string(),
  result: z.string(),
  latencyMs: z.number().min(0),
  fallback: z.boolean(),
});

const CompletionFailureSchema = z.object({
  error: z.string(),
  lastError: z.string().nullable(),
  fallback: z.literal(false),
});

// ============================
// GatewayClient
// ============================

/**
 * Typed client for the FastMCP gateway. Forwards completion requests and
 * reads health snapshots from the Python `ProviderRouter` over HTTP.
 */
export class GatewayClient {
  private readonly baseUrl: string;
  private readonly timeoutMs: number;

  constructor(options: { baseUrl?: string; timeoutMs?: number } = {}) {
    this.baseUrl = (options.baseUrl ?? process.env.MCP_GATEWAY_URL ?? "http://localhost:8000").replace(/\/$/, "");
    this.timeoutMs = options.timeoutMs ?? 30_000;
  }

  /** Forward a completion request to the gateway's fallback cascade. */
  async complete(prompt: string, params?: Record<string, unknown>): Promise<CompletionResult | CompletionFailure> {
    const url = `${this.baseUrl}/v1/gateway/complete`;
    const body = JSON.stringify({ prompt, ...(params ?? {}) });

    const res = await this.fetchWithTimeout(url, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body,
    });

    if (!res.ok) {
      return {
        error: `Gateway HTTP ${res.status}`,
        lastError: await res.text().catch(() => null),
        fallback: false,
      };
    }

    const data = await res.json();
    const parsed = CompletionResultSchema.safeParse(data);
    if (parsed.success) return parsed.data;

    const failure = CompletionFailureSchema.safeParse(data);
    if (failure.success) return failure.data;

    return {
      error: "Gateway returned an unrecognized response shape",
      lastError: JSON.stringify(data),
      fallback: false,
    };
  }

  /** Read health snapshots for all configured providers. */
  async healthCheckAll(): Promise<Record<ProviderName, ProviderHealth>> {
    const url = `${this.baseUrl}/v1/gateway/health`;
    const res = await this.fetchWithTimeout(url, { method: "GET" });

    if (!res.ok) {
      throw new Error(`Gateway health HTTP ${res.status}`);
    }

    const data = (await res.json()) as Record<string, unknown>;
    const out: Record<string, ProviderHealth> = {};
    for (const [name, value] of Object.entries(data)) {
      const parsed = ProviderHealthSchema.safeParse(value);
      if (parsed.success) {
        out[name] = parsed.data as ProviderHealth;
      }
    }
    return out as Record<ProviderName, ProviderHealth>;
  }

  private async fetchWithTimeout(url: string, init: RequestInit): Promise<Response> {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeoutMs);
    try {
      return await fetch(url, { ...init, signal: controller.signal });
    } finally {
      clearTimeout(timer);
    }
  }
}

// ============================
// Convenience factory
// ============================

/** Create a gateway client bound to the configured backend URL. */
export function createGatewayClient(options?: ConstructorParameters<typeof GatewayClient>[0]): GatewayClient {
  return new GatewayClient(options);
}
