"""Bearer token validation middleware for FastMCP."""

import jwt
from datetime import datetime, timezone
from typing import Optional, Dict, Any

# In production, use a proper secret management service
SECRET_KEY = "fastmcp-production-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15


def create_access_token(data: Dict[str, Any], expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + __import__("datetime").timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None  # Token expired
    except jwt.InvalidTokenError:
        return None  # Invalid token


async def validate_bearer_token(auth_header: Optional[str]) -> bool:
    """Validate a Bearer token from the Authorization header."""
    if not auth_header:
        return False
    
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return False
    
    token = parts[1]
    payload = verify_token(token)
    return payload is not None


def optional_bearer_token(auth_header: Optional[str]) -> Optional[Dict[str, Any]]:
    """Optional Bearer token validation — returns payload or None."""
    if not auth_header:
        return None
    
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    
    token = parts[1]
    return verify_token(token)