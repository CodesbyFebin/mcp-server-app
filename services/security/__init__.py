"""Security & Compliance Service for MCPserver.in and app.mcpserver.in.

Exports:
- JWT token creation/verification (HS256)
- Bearer token validation (optional/required)
- PII redaction/masking (PAN, GSTIN, email, phone)
- Policy engine (deterministic fail-closed evaluation)
- Network security (SSRF, protocol validation, DNS rebinding)
"""

# PII Reddaction
from .middleware import (
    create_access_token,
    verify_token,
    validate_bearer_token,
    optional_bearer_token,
    mask_pan,
    mask_gstin,
    mask_email,
    mask_phone,
    redact_sensitive_text,
)

# Policy Engine
from .policy import PolicyEngine

# Network Security
from .network import (
    SSRFProtection,
    ProtocolValidator,
    DNSRebindingPrevention,
    ssrf_protection,
    protocol_validator,
    dns_rebinding_prevention,
    is_safe_url,
    validate_url_protocol,
    check_dns_rebinding,
)

__all__ = [
    # Token management
    "create_access_token",
    "verify_token",
    "validate_bearer_token",
    "optional_bearer_token",
    # PII redaction
    "mask_pan",
    "mask_gstin",
    "mask_email",
    "mask_phone",
    "redact_sensitive_text",
    # Policy engine
    "PolicyEngine",
    # Network security
    "SSRFProtection",
    "ProtocolValidator",
    "DNSRebindingPrevention",
    "ssrf_protection",
    "protocol_validator",
    "dns_rebinding_prevention",
    "is_safe_url",
    "validate_url_protocol",
    "check_dns_rebinding",
]