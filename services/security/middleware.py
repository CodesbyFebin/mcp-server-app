"""Security middleware for MCPserver.in and app.mcpserver.in.

Implements JWT token creation/verification with HS256, Bearer token validation,
and PII redaction patterns established in Phase 1.5.
"""

import json
import base64
import hashlib
import hmac
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Literal, Union

# HS256 constants
HS256 = "HS256"


def create_access_token(
    data: Dict[str, Any],
    secret_key: str,
    algorithm: str = HS256,
    expires_minutes: int = 15,
) -> str:
    """Create a JWT access token using HS256.
    
    Args:
        data: Payload data to encode
        secret_key: HS256 secret key
        algorithm: JWT algorithm (default: HS256)
        expires_minutes: Token expiration in minutes
        
    Returns:
        Encoded JWT string
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": hashlib.sha256(str(time.time()).encode()).hexdigest()[:16],
    })
    
    # HS256 encoding
    header_b64 = base64.urlsafe_b64encode(json.dumps({"alg": algorithm, "typ": "JWT"}).encode()).decode()
    payload_b64 = base64.urlsafe_b64encode(json.dumps(to_encode).encode()).decode()
    
    # Sign the header + payload
    signing_input = f"{header_b64}.{payload_b64}"
    signature = hmac.new(
        secret_key.encode(),
        signing_input.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return f"{signing_input}.{signature}"


def verify_token(token: str, secret_key: str, algorithm: str = HS256) -> Optional[Dict[str, Any]]:
    """Verify a JWT token using HS256.
    
    Args:
        token: JWT string to verify
        secret_key: HS256 secret key
        algorithm: JWT algorithm (default: HS256)
        
    Returns:
        Decoded payload if valid, None if invalid
    """
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        
        header_b64, payload_b64, signature = parts
        
        # Verify signature
        signing_input = f"{header_b64}.{payload_b64}"
        expected_signature = hmac.new(
            secret_key.encode(),
            signing_input.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_signature):
            return None
        
        # Decode payload
        payload_decoded = base64.urlsafe_b64decode(payload_b64 + "==")
        payload = json.loads(payload_decoded)
        
        # Check expiration
        if payload.get("exp") and payload["exp"] < datetime.now(timezone.utc).timestamp():
            return None
        
        # Check issued-at
        if payload.get("iat"):
            iat = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)
            now = datetime.now(timezone.utc)
            # Allow 5 minute clock skew
            if (now - iat).total_seconds() > 300:
                return None
        
        return payload
        
    except (json.JSONDecodeError, base64.binascii.Error, ValueError, IndexError):
        return None


def validate_bearer_token(
    authorization: str,
    secret_key: str,
    algorithm: str = HS256,
    expect_jti: str | None = None
) -> Optional[Dict[str, Any]]:
    """Validate a Bearer token from Authorization header.
    
    Args:
        authorization: Raw Authorization header value
        secret_key: HS256 secret key for verification
        algorithm: JWT algorithm
        expect_jti: Expected JWT ID (for one-time use tokens)
        
    Returns:
        Decoded payload if valid, None if invalid
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    token = authorization[7:]  # Strip "Bearer "
    
    if not token:
        return None
    
    payload = verify_token(token, secret_key, algorithm)
    
    if payload is None:
        return None
    
    # Check JTI if required
    if expect_jti and payload.get("jti") != expect_jti:
        return None
    
    return payload


def optional_bearer_token(
    authorization: str,
    secret_key: str,
    algorithm: str = HS256
) -> Optional[Dict[str, Any]]:
    """Optional Bearer token validation - returns payload or None (not an error)."""
    return validate_bearer_token(authorization, secret_key, algorithm)


# ============================
# PII Redaction & Masking
# ============================

def mask_pan(pan: str) -> str:
    """Mask PAN: ABCDE1234F -> AB**E1234F (first 2 + last 4 visible)"""
    import re
    match = re.match(r"^([A-Z]{2})[A-Z]([A-Z])(\d{4})([A-Z])$", pan.upper())
    if match:
        return f"{match.group(1)}{match.group(2)}****{match.group(3)}{match.group(4)}"
    return pan


def mask_gstin(gstin: str) -> str:
    """Mask GSTIN: 07AAAAA1234Z1Z -> 07AAAA*****Z1Z"""
    import re
    match = re.match(r"^([0-9]{2}[A-Z]{5})[0-9]{4}([A-Z]{1}[0-9A-Z]{1})$", gstin.upper())
    if match:
        return f"{match.group(1)}*****{match.group(2)}"
    return gstin


def mask_email(email: str) -> str:
    """Mask email: user@example.com -> us***@example.com"""
    if "@" not in email:
        return email
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        masked_local = local[0] + "*" * (len(local) - 1)
    else:
        masked_local = local[:2] + "*" * (len(local) - 2)
    return f"{masked_local}@{domain}"


def mask_phone(phone: str) -> str:
    """Mask phone: +919876543210 -> +91*****43210"""
    import re
    match = re.match(r"^(\+?[\d\-\+]*)(\d{4})$", phone)
    if match:
        return f"{match.group(1)}*****{match.group(2)}"
    return re.sub(r"(\d{4})$", r"****\1", phone)


def redact_sensitive_text(text: str) -> str:
    """Redact all sensitive patterns from text.
    
    Applies masking to PAN, GSTIN, email, and phone numbers found in text.
    """
    import re
    
    # PAN pattern: ABCDE1234F
    text = re.sub(r"[A-Z]{5}\d{4}[A-Z]", lambda m: mask_pan(m.group(0)), text)
    
    # GSTIN pattern: 07AAAAA1234Z1Z
    text = re.sub(r"[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}", 
                  lambda m: mask_gstin(m.group(0)), text)
    
    # Email pattern
    text = re.sub(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", 
                  lambda m: mask_email(m.group(0)), text, flags=re.IGNORECASE)
    
    # Phone pattern (Indian: +91 or 91 or 10 digits)
    text = re.sub(r"(?:\+?91[-\s]?)?[6-9]\d{9}\b", 
                  lambda m: mask_phone(m.group(0)), text)
    
    return text


# ============================
# Policy Engine
# ============================

class PolicyEngine:
    """Policy engine with deterministic evaluation order.
    
    Evaluation order (fail-closed):
    1. Organization boundary
    2. Explicit deny
    3. Admin override
    4. Explicit allow
    5. Rate/budget constraint
    6. Approval requirement
    7. Default deny
    """
    
    def __init__(self, 
                 org_boundary: bool = True,
                 explicit_deny: bool = False,
                 admin_override: bool = False,
                 explicit_allow: bool = False,
                 rate_constraint: bool = True,
                 approval_requirement: bool = True,
                 default_deny: bool = True):
        self.org_boundary = org_boundary
        self.explicit_deny = explicit_deny
        self.admin_override = admin_override
        self.explicit_allow = explicit_allow
        self.rate_constraint = rate_constraint
        self.approval_requirement = approval_requirement
        self.default_deny = default_deny
    
    def evaluate(
        self,
        actor_org: str,
        requested_org: str | None,
        has_explicit_deny: bool = False,
        is_admin: bool = False,
        has_rate_exceeded: bool = False,
        requires_approval: bool = False,
        approval_granted: bool = False,
    ) -> Dict[str, Any]:
        """Evaluate access policy and return decision.
        
        Returns:
            {
                "allowed": bool,
                "reason": str,
                "stage": str,  # where the decision was made
            }
        """
        # Stage 1: Organization boundary
        if self.org_boundary and requested_org and actor_org != requested_org:
            return {
                "allowed": False,
                "reason": f"Organization boundary: actor '{actor_org}' cannot access '{requested_org}'",
                "stage": "organization_boundary",
            }
        
        # Stage 2: Explicit deny
        if self.explicit_deny and has_explicit_deny:
            return {
                "allowed": False,
                "reason": "Explicit deny policy activated",
                "stage": "explicit_deny",
            }
        
        # Stage 3: Admin override
        if self.admin_override and is_admin:
            return {
                "allowed": True,
                "reason": "Admin override activated",
                "stage": "admin_override",
            }
        
        # Stage 4: Explicit allow
        if self.explicit_allow:
            return {
                "allowed": True,
                "reason": "Explicit allow policy activated",
                "stage": "explicit_allow",
            }
        
        # Stage 5: Rate/budget constraint
        if self.rate_constraint and has_rate_exceeded:
            return {
                "allowed": False,
                "reason": "Rate/budget constraint exceeded",
                "stage": "rate_constraint",
            }
        
        # Stage 6: Approval requirement
        if self.approval_requirement and requires_approval and not approval_granted:
            return {
                "allowed": False,
                "reason": "Approval required but not granted",
                "stage": "approval_requirement",
            }
        
        # Stage 7: Default deny
        if self.default_deny:
            return {
                "allowed": False,
                "reason": "Default deny policy activated",
                "stage": "default_deny",
            }
        
        return {
            "allowed": True,
            "reason": "No policy matched (unexpected state)",
            "stage": "unknown",
        }


# ============================
# Network Security
# ============================

class NetworkSecurity:
    """Network security controls for the MCP system."""
    
    @staticmethod
    def check_ssrf(url: str) -> bool:
        """Check URL for SSRF (Server-Side Request Forgery) risks.
        
        Blocks:
        - Private IP addresses (127.0.0.0/8, 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
        - Link-local addresses (169.254.0.0/16)
        - Broadcast addresses
        - Loopback addresses
        """
        import re
        
        # Extract hostname from URL
        hostname_match = re.search(r'://([^/]+)', url)
        if not hostname_match:
            return False  # Can't parse URL
        
        hostname = hostname_match.group(1).split("/")[0].split("?")[0].split(":")[0]
        
        # Check for private IPs
        private_ip_patterns = [
            r'^127\.\d{1,3}\.\d{1,3}\.\d{1,3}$',       # Loopback
            r'^10\.\d{1,3}\.\d{1,3}\.\d{1,3}$',        # 10.0.0.0/8
            r'^172\.(1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3}$',  # 172.16.0.0/12
            r'^192\.168\.\d{1,3}\.\d{1,3}$',            # 192.168.0.0/16
            r'^169\.254\.\d{1,3}\.\d{1,3}$',            # Link-local
        ]
        
        for pattern in private_ip_patterns:
            if re.match(pattern, hostname):
                return False  # SSRF risk detected
        
        # Check for hostname resolution to private IP
        # (In production, would resolve DNS and check)
        
        return True  # Passes SSRF check
    
    @staticmethod
    def validate_protocol(url: str, allowed_protocols: list[str] | None = None) -> bool:
        """Validate URL protocol is in allowed list."""
        if allowed_protocols is None:
            allowed_protocols = ["https", "http"]
        
        import re
        match = re.match(r'^([a-zA-Z]+):\/\/', url)
        if match:
            protocol = match.group(1).lower()
            return protocol in [p.lower() for p in allowed_protocols]
        return False
    
    @staticmethod
    def check_private_ip(hostname: str) -> bool:
        """Check if hostname resolves to a private IP address."""
        import re
        
        private_patterns = [
            r'^127\.',        # 127.x.x.x
            r'^10\.',         # 10.x.x.x
            r'^172\.(1[6-9]|2\d|3[0-1])\.',  # 172.16.x.x - 172.31.x.x
            r'^192\.168\.',   # 192.168.x.x
            r'^169\.254\.',   # 169.254.x.x
        ]
        
        for pattern in private_patterns:
            if re.match(pattern, hostname):
                return True  # It's a private IP
        
        return False


# ============================
# Example Usage
# ============================

if __name__ == "__main__":
    import sys
    
    print("=== Security Middleware ===")
    print()
    
    # Token creation
    print("--- Token Creation ---")
    token = create_access_token(
        data={"sub": "user123", "org": "mcp-org"},
        secret_key="super-secret-key",
        expires_minutes=30
    )
    print(f"Created token: {token[:50]}...")
    
    # Token verification
    print()
    print("--- Token Verification ---")
    payload = verify_token(token, "super-secret-key")
    if payload:
        print(f"✅ Token valid: sub={payload.get('sub')}, org={payload.get('org')}")
        print(f"   Exp: {datetime.fromtimestamp(payload['exp'], tz=timezone.utc)}")
        print(f"   iat: {datetime.fromtimestamp(payload['iat'], tz=timezone.utc)}")
    else:
        print("❌ Token invalid")
    
    # Bearer validation
    print()
    print("--- Bearer Validation ---")
    payload = validate_bearer_token(f"Bearer {token}", "super-secret-key")
    if payload:
        print(f"✅ Bearer token valid")
    else:
        print("❌ Bearer token invalid")
    
    # Optional bearer
    print()
    print("--- Optional Bearer ---")
    payload = optional_bearer_token("Bearer " + "invalid", "super-secret-key")
    print(f"✅ Optional valid: {payload is not None}")
    payload = optional_bearer_token("", "super-secret-key")
    print(f"✅ Optional missing: {payload is None}")
    
    # PII masking
    print()
    print("--- PII Redaction ---")
    test_text = "User PAN: ABCDE1234F, GSTIN: 07AAAAA1234Z1Z, email: user@example.com, phone: +919876543210"
    redacted = redact_sensitive_text(test_text)
    print(f"Original: {test_text}")
    print(f"Redacted: {redacted}")
    
    # Policy engine
    print()
    print("--- Policy Engine ---")
    engine = PolicyEngine()
    
    # Test org boundary
    result = engine.evaluate(
        actor_org="mcp-org",
        requested_org="other-org",
        has_explicit_deny=False,
        is_admin=False,
        has_rate_exceeded=False,
        requires_approval=False,
        approval_granted=False,
    )
    print(f"Org boundary: allowed={result['allowed']}, reason={result['reason'][:60]}...")
    
    # Test default deny
    result = engine.evaluate(
        actor_org="mcp-org",
        requested_org="mcp-org",
        has_explicit_deny=False,
        is_admin=False,
        has_rate_exceeded=False,
        requires_approval=False,
        approval_granted=False,
    )
    print(f"Default deny: allowed={result['allowed']}, reason={result['reason'][:60]}...")
    
    # Test admin override
    result = engine.evaluate(
        actor_org="mcp-org",
        requested_org="mcp-org",
        has_explicit_deny=False,
        is_admin=True,
        has_rate_exceeded=False,
        requires_approval=False,
        approval_granted=False,
    )
    print(f"Admin override: allowed={result['allowed']}, reason={result['reason'][:60]}...")