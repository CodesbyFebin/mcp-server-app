/**
 * Typed API Client for MCP Server Interaction
 * 
 * Client-side library for interacting with MCP server APIs.
 * Handles transport, sanitization, and error handling.
 */

import { McpTransport } from "./transport.js";

export interface ServerInfo {
  id: string;
  name: string;
  slug: string;
  verificationStatus: "verified" | "unverified" | "pending";
  publicationStatus: "draft" | "published" | "archived";
  capabilities: string[];
}

export interface ToolInfo {
  name: string;
  description: string;
  parameters: Record<string, unknown>;
}

export interface ResourceInfo {
  uri: string;
  description: string;
  mimeType: string;
}

export interface PromptInfo {
  name: string;
  description: string;
  arguments: Record<string, unknown>;
}

export class McpApiClient {
  constructor(private transport: McpTransport) {}

  async listServers(): Promise<ServerInfo[]> {
    return this.transport.request<ServerInfo[]>("/servers/list", {});
  }

  async getServer(slug: string): Promise<ServerInfo> {
    return this.transport.request<ServerInfo>(`/servers/${slug}`, {});
  }

  async listTools(): Promise<ToolInfo[]> {
    return this.transport.request<ToolInfo[]>("/tools/list", {});
  }

  async callTool(name: string, arguments_: Record<string, unknown>): Promise<any> {
    return this.transport.request(`/tools/call`, { name, arguments: arguments_ });
  }

  async listResources(): Promise<ResourceInfo[]> {
    return this.transport.request<ResourceInfo[]>("/resources/list", {});
  }

  async readResource(uri: string): Promise<any> {
    return this.transport.request(`/resources/read`, { uri });
  }

  async listPrompts(): Promise<PromptInfo[]> {
    return this.transport.request<PromptInfo[]>("/prompts/list", {});
  }

  async getPrompt(name: string): Promise<any> {
    return this.transport.request(`/prompts/get`, { name });
  }
}