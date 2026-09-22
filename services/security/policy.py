"""Policy engine for MCPserver.in access control.

Deterministic evaluation order (fail-closed):
1. Organization boundary
2. Explicit deny
3. Admin override
4. Explicit allow
5. Rate/budget constraint
6. Approval requirement
7. Default deny
"""

from typing import Dict, Any


class PolicyEngine:
    """Policy engine with deterministic fail-closed evaluation."""

    def __init__(
        self,
        org_boundary: bool = True,
        explicit_deny: bool = False,
        admin_override: bool = False,
        explicit_allow: bool = False,
        rate_constraint: bool = True,
        approval_requirement: bool = True,
        default_deny: bool = True,
    ):
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
        """Evaluate access policy.

        Returns:
            {"allowed": bool, "reason": str, "stage": str}
        """

        # Stage 1: Organization boundary (fail-closed)
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

        # Stage 7: Default deny (fail-closed)
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