/**
 * Authentication Primitives
 * 
 * Auth primitives for MCP server access and API protection.
 * Supports OIDC/OAuth, passkeys, and MFA.
 */

export interface AuthCredentials {
  subject: string;
  issuer: string;
  audience: string[];
  issuedAt: string;
  expiresAt: string;
}

export interface TokenPayload {
  sid: string; // Session ID
  serverId: string; // MCP server identifier
  permissions: string[];
  scopes: string[];
}

export type AuthProvider = "oidc" | "oauth" | "passkey" | "mfa";

export interface AuthError {
  code: string;
  message: string;
  retryable: boolean;
}