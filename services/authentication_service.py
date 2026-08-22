from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class AuthenticatedIdentity:
    """Canonical identity established by the authentication layer."""

    user_id: int
    tenant_id: str
    is_authenticated: bool = True


class AuthenticationService:
    """
    Resolves an authenticated internal KOSFintech identity.

    Authentication establishes WHO the user is.
    It does not assign platform or administration authority.
    """

    def __init__(self, connection):
        self.connection = connection

    def authenticate(self, user_id: int) -> Optional[AuthenticatedIdentity]:
        row = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                status
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()

        if row is None:
            return None

        if row["status"] != "active":
            return None

        return AuthenticatedIdentity(
            user_id=row["id"],
            tenant_id=row["tenant_id"],
        )
