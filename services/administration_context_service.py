from dataclasses import dataclass
from typing import Optional

from repositories.administration_repository import AdministrationRepository


@dataclass(frozen=True)
class AdministrationContext:
    """
    Explicitly established administration context for an authenticated user.

    This identifies WHERE the user is operating.
    It does not grant authority or permissions.
    """

    user_id: int
    tenant_id: str
    administration_id: int


class AdministrationContextService:
    """
    Establish an explicit administration context for an authenticated user.

    Authentication establishes WHO.
    Administration context establishes WHERE.
    Authorization determines WHAT the user may do.

    This service deliberately does not:
    - infer administration from tenant alone;
    - infer authority from users.role;
    - use Telegram metadata;
    - grant permissions or governance authority.
    """

    def __init__(self, connection):
        self.connection = connection
        self.administration_repository = AdministrationRepository(connection)

    def resolve(
        self,
        user_id: int,
        administration_id: int,
        tenant_id: Optional[str] = None,
    ) -> Optional[AdministrationContext]:
        user_row = self.connection.execute(
            """
            SELECT tenant_id, status
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()

        if user_row is None or user_row["status"] != "active":
            return None

        authenticated_tenant_id = user_row["tenant_id"]

        # A caller-supplied tenant may confirm identity context,
        # but must never override the authenticated tenant.
        if (
            tenant_id is not None
            and tenant_id != authenticated_tenant_id
        ):
            return None

        administration = self.administration_repository.get_by_id(
            administration_id
        )

        if administration is None:
            return None

        if administration.status != "active":
            return None

        if administration.tenant_id != authenticated_tenant_id:
            return None

        return AdministrationContext(
            user_id=user_id,
            tenant_id=authenticated_tenant_id,
            administration_id=administration.id,
        )
