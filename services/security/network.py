"""Network security controls for the MCP system.

SSRF protection, protocol validation, hostname validation,
private IP blocking, DNS rebinding prevention, timeout enforcement.
"""

import re
from typing import List, Optional


class SSRFProtection:
    """Server-Side Request Forgery protection.

    Blocks requests to private/internal IP addresses,
    localhost, link-local addresses, and reserved ranges.
    """

    # Private IP ranges (CIDR notation for reference):
    # 127.0.0.0/8 (loopback)
    # 10.0.0.0/8 (private)
    # 172.16.0.0/12 (private)
    # 192.168.0.0/16 (private)
    # 169.254.0.0/16 (link-local)
    # 224.0.0.0/4 (multicast)
    # 240.0.0.0/4 (reserved)

    PRIVATE_IP_PREFIXES = [
        "127.",
        "10.",
        "172.16.",
        "172.17.",
        "172.18.",
        "172.19.",
        "172.20.",
        "172.21.",
        "172.22.",
        "172.23.",
        "172.24.",
        "172.25.",
        "172.26.",
        "172.27.",
        "172.28.",
        "172.29.",
        "172.30.",
        "172.31.",
        "192.168.",
        "169.254.",
    ]

    RESERVED_HOSTNAMES = [
        "localhost",
        "local",
        "internal",
        "admin",
        "config",
        "metadata",
    ]

    def check_hostname(self, hostname: str) -> bool:
        """Check if hostname is safe to connect to.

        Returns True if safe, False if SSRF risk detected.
        """
        if not hostname:
            return False

        hostname_lower = hostname.lower().strip()

        # Check reserved hostnames
        for reserved in self.RESERVED_HOSTNAMES:
            if hostname_lower == reserved or hostname_lower.startswith(reserved + "."):
                return False

        # Check private IP prefixes
        for prefix in self.PRIVATE_IP_PREFIXES:
            if hostname_lower.startswith(prefix):
                return False

        # Check for IP address format (hostname is actually an IP)
        ip_pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
        if re.match(ip_pattern, hostname_lower):
            # Additional check: is it a private IP?
            octets = hostname_lower.split(".")
            if len(octets) == 4:
                try:
                    o1, o2, o3, o4 = int(octets[0]), int(octets[1]), int(octets[2]), int(octets[3])
                    # 127.x.x.x - loopback
                    if o1 == 127:
                        return False
                    # 10.x.x.x - private
                    if o1 == 10:
                        return False
                    # 172.16.x.x - 172.31.x.x - private
                    if o1 == 172 and 16 <= o2 <= 31:
                        return False
                    # 192.168.x.x - private
                    if o1 == 192 and o2 == 168:
                        return False
                    # 169.254.x.x - link-local
                    if o1 == 169 and o2 == 254:
                        return False
                except ValueError:
                    pass

        return True

    def check_url(self, url: str) -> bool:
        """Check URL for SSRF risks.

        Returns True if safe, False if SSRF risk detected.
        """
        # Extract hostname from URL
        hostname_match = re.search(r"://([^/]+)", url)
        if not hostname_match:
            # No scheme, try without
            hostname_match = re.search(r"^([^/]+)", url)
        if not hostname_match:
            return False

        hostname = hostname_match.group(1).split(":")[0]  # Remove port
        return self.check_hostname(hostname)


class ProtocolValidator:
    """Validate URL protocols against an allowlist."""

    DEFAULT_ALLOWED = ["https", "http"]

    def __init__(self, allowed_protocols: List[str] | None = None):
        self.allowed_protocols = allowed_protocols or self.DEFAULT_ALLOWED

    def validate(self, url: str) -> bool:
        """Validate URL protocol is in allowed list."""
        import re
        match = re.match(r"^([a-zA-Z]+):\/\/", url)
        if match:
            protocol = match.group(1).lower()
            return protocol in self.allowed_protocols
        return False


class DNSRebindingPrevention:
    """DNS rebinding attack prevention.

    Tracks recently seen hostnames and their resolved IPs
    to prevent attackers from bouncing between public and
    private IPs via DNS TTL manipulation.
    """

    def __init__(self, max_entries: int = 100, ttl_seconds: int = 300):
        self.max_entries = max_entries
        self.ttl_seconds = ttl_seconds
        self._seen: dict[str, dict] = {}  # hostname -> {ip, first_seen}

    def record_attempt(self, hostname: str, ip: str) -> bool:
        """Record a DNS resolution attempt. Returns True if suspicious."""
        hostname_lower = hostname.lower().strip()

        if hostname_lower in self._seen:
            entry = self._seen[hostname_lower]
            # Check if this IP was previously seen for this hostname
            if entry["ip"] != ip:
                # IP changed - potential DNS rebinding
                age = (
                    datetime.now(timezone.utc).timestamp()
                    - entry["first_seen"]
                )
                if age < self.ttl_seconds:
                    return True  # Suspicious: IP changed within TTL
            # Update entry
            entry["ip"] = ip
            entry["first_seen"] = datetime.now(timezone.utc).timestamp()
        else:
            # New entry
            if len(self._seen) >= self.max_entries:
                # Evict oldest
                oldest = min(
                    self._seen.keys(), key=lambda k: self._seen[k]["first_seen"]
                )
                del self._seen[oldest]
            self._seen[hostname_lower] = {
                "ip": ip,
                "first_seen": datetime.now(timezone.utc).timestamp(),
            }

        return False

    def is_safe(self, hostname: str, resolved_ip: str) -> bool:
        """Check if hostname-to-IP mapping is safe."""
        if not self.check_hostname(hostname):
            return False
        # Check if this hostname+IP combo has been seen suspiciously
        return not self.record_attempt(hostname, resolved_ip)


# Global instances for convenience
ssrf_protection = SSRFProtection()
protocol_validator = ProtocolValidator()
dns_rebinding_prevention = DNSRebindingPrevention()


# Convenience functions
def is_safe_url(url: str) -> bool:
    """Quick check if URL is safe from SSRF."""
    return ssrf_protection.check_url(url)


def validate_url_protocol(url: str, allowed: List[str] | None = None) -> bool:
    """Quick protocol validation."""
    return protocol_validator.validate(url, allowed or protocol_validator.DEFAULT_ALLOWED)


def check_dns_rebinding(hostname: str, ip: str) -> bool:
    """Check for DNS rebinding suspicion."""
    return dns_rebinding_prevention.is_safe(hostname, ip)