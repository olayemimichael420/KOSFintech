"""
Authentication and authorization foundation.

Full RBAC and tenant isolation will be implemented in the
authentication phase.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class UserContext:
    """Security context for an authenticated user."""

    user_id: int
    tenant_id: Optional[str]
    role: str
    is_authenticated: bool = True


def authorize(
    user: UserContext,
    permission: str,
) -> bool:
    """
    Foundation authorization hook.

    The complete permission matrix will be implemented later.
    """

    if not user.is_authenticated:
        return False

    if user.role == "super_admin":
        return True

    return permission == "public.read"
