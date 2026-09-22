# API Model — MCPserver.in + app.mcpserver.in

## McpApiClient — Typed API Client

### Class: McpApiClient

The `McpApiClient` is the typed API client for interacting with MCP server services.
It implements the `McpTransport` interface and supports both transport types:
- `StdioTransport` — standard input/output communication
- `StreamableHttpTransport` — HTTP with streaming support

### Constructor

```typescript
new McpApiClient(transport: McpTransport, options?: {
  timeoutMs?: number;     // Default: 30000
  headers?: Record<string, string>;
  timeout?: number;       // Alias for timeoutMs
})
```

### Transport Types

#### McpTransport Interface
```typescript
interface McpTransport {
  connect(): Promise<void>;
  request<T>(method: string, params?: unknown): Promise<T>;
  close(): Promise<void>;
}
```

#### StdioTransport
```typescript
class StdioTransport implements McpTransport {
  connect(): Promise<void>;     // Initialize stdio subprocess
  request<T>(method: string, params?: unknown): Promise<T>;  // Send JSON-RPC request
  close(): Promise<void>;       // Terminate stdio subprocess
}
```

#### StreamableHttpTransport
```typescript
class StreamableHttpTransport implements McpTransport {
  constructor(baseUrl: string, options?: { timeoutMs?: number });
  connect(): Promise<void>;     // Establish HTTP connection
  request<T>(method: string, params?: unknown): Promise<T>;  // POST to /v1/mcp
  close(): Promise<void>;       // Close HTTP connection
}
```

### Core Methods

| Method | Parameters | Returns | Description |
|---|---|---|---|
| `listServers()` | none | `Server[]` | List all available MCP servers |
| `getServer(slug: string)` | server slug | `Server | null` | Get server details by slug |
| `listTools(serverId?: string)` | optional server filter | `Tool[]` | List tools, optionally filtered by server |
| `callTool(method: string, params?: unknown)` | method name + optional params | `any` | Execute a tool with given params |
| `listResources(serverId?: string)` | optional server filter | `Resource[]` | List resources, optionally filtered by server |
| `readResource(uri: string)` | resource URI | `any` | Read a resource by URI |
| `listPrompts(serverId?: string)` | optional server filter | `Prompt[]` | List prompts, optionally filtered by server |
| `getPrompt(name: string)` | prompt name | `Prompt | null` | Get a prompt by name |

### Error Handling

All methods throw `ApiError` on failure with structured error information:

```typescript
interface ApiError {
  message: string;       // Human-readable error message
  code: number;        // Error code (e.g., 404, 500)
  status: string;      // HTTP status string
  requestId?: string;  // Request identifier for debugging
  retryable: boolean;  // Whether the error can be retried
  timeout: boolean;    // Whether the error was timeout-related
}
```

### Example Usage

```typescript
import { McpApiClient, StdioTransport } from '@mcp/servers-api-client';

// Initialize with stdio transport
const transport = new StdioTransport();
const client = new McpApiClient(transport);

// Connect and list servers
await transport.connect();
const servers = await client.listServers();

// Call a tool
const result = await client.callTool('gst.validate', {
  gstin: '07AAAPS1234C1Z5'
});

// Close when done
await transport.close();
```

### API Endpoints (StreamableHttpTransport)

| Endpoint | Method | Description |
|---|---|---|
| `POST /v1/mcp/initialize` | initialize | Initialize MCP session |
| `POST /v1/mcp/tools/list` | tools/list | List available tools |
| `POST /v1/mcp/tools/call` | tools/call | Execute a tool |
| `POST /v1/mcp/resources/list` | resources/list | List resources |
| `POST /v1/mcp/resources/read` | resources/read | Read a resource |
| `POST /v1/mcp/prompts/list` | prompts/list | List prompts |
| `POST /v1/mcp/prompts/get` | prompts/get | Get a prompt |

### Timeout Configuration

Default timeout: 30000ms (30 seconds)
- Configurable per client instance
- Applied at transport level (connect + request)
- Non-retryable errors marked as timeout automatically
- Configurable per-request override possible

### Transport Health

- `connect()` must succeed before any `request()` calls
- `close()` idempotent — safe to call multiple times
- Automatic reconnect not built-in; callers manage reconnection
- Transport state tracked internally, `connect()` idempotent on success
- Error events emitted on transport failure

### Example: Full Lifecycle

```typescript
import { McpApiClient, StreamableHttpTransport } from '@mcp/servers-api-client';

const client = new McpApiClient(
  new StreamableHttpTransport('https://api.mcpserver.in/v1')
);

// 1. Initialize
await client.callTool('initialize', {});

// 2. List tools
const tools = await client.listTools();

// 3. Call a tool with params
const result = await client.callTool('gst.validate', {
  gstin: '07AAAPS1234C1Z5'
});

// 4. List resources
const resources = await client.listResources();

// 5. Read a resource
const resource = await client.readResource('server://mcp-server-123');

// 6. List prompts
const prompts = await client.listPrompts();

// 7. Get a specific prompt
const prompt = await client.getPrompt('gst-validation');

// 8. Close transport
await client.close();
```

### API Error Codes

| Code | Meaning | Retryable |
|---|---|---|
| 1001 | Method not found | no |
| 1002 | Invalid parameters | no |
| 1003 | Server error | yes |
| 1004 | Transport error | yes |
| 1005 | Timeout | yes |
| 1006 | Unauthorized | no |
| 1007 | Forbidden | no |
| 1008 | Not found | no |
| 1009 | Rate limited | yes (back off) |
| 1101 | Connection refused | yes |
| 1102 | Host unreachable | yes |
| 1103 | Network timeout | yes |

### Rate Limiting

- Global rate limit: 100 requests/minute per client
- Per-endpoint limits: vary by method
- 429 responses with `Retry-After` header
- Exponential backoff on retry: 1s, 2s, 4s, 8s, 16s max
- Burst allowance: 10 requests burst, then 10/min sustained

### Idempotency

- `initialize` is idempotent (safe to call multiple times)
- `tools/list` is idempotent
- `tools/call` with same params returns same result (server-dependent)
- Non-idempotent methods explicitly documented
- Clients should handle non-idempotent rejections gracefully

### Security Sanitization

Client-side sanitization on incoming data:
- PAN: validated as `[A-Z]{5}[0-9]{4}[A-Z]{1}`
- GSTIN: validated against `^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$`
- Email: masked display (first 2 + last 2 chars + ...)
- Phone: formatted per region, never stored raw
- Never log raw PII (PAN, GSTIN, Aadhaar, email, phone)
- Structured audit fields only in logs

### API Versioning

Current version: `v1`
- URL path includes version: `/v1/mcp/...`
- Major versions have breaking changes; minor are additive
- `X-API-Version` header supported for explicit versioning
- Deprecation policy: 6-month notice before major version deprecation

### Compatibility

- TypeScript strict mode compatible
- All packages compile with `tsc --noEmit` exit code 0
- Zod validators for runtime type checking
- ESM module resolution with NodeNext
- No circular dependencies between packages

### Package Boundary

`@mcp/servers-api-client` depends on:
- `@mcp/servers-contracts` (for shared schemas/types)
- No direct dependency on runtime or service implementations

`@mcp/servers-api-client` is used by:
- `apps/web/` (MCPserver.in web app)
- `apps/app/` (app.mcpserver.in mobile app)
- Any consumer of the MCP JSON-RPC protocol

### Type Guarantees

All API methods return statically typed results where possible. Zod schemas
validate payloads at runtime. TypeScript types align with Zod schemas so that
type errors catch issues before runtime. The `listTools`, `listResources`, and
`listPrompts` methods return arrays typed to their respective Zod-validated schemas.