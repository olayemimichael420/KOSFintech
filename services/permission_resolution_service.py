from typing import Optional, Set


class PermissionResolutionService:
    """
    Resolves effective application permissions for a user.

    Tenant identity is always taken from the authenticated user's
    database record. A caller-supplied tenant can only confirm that
    identity; it can never override it.

    Governance authority (super_admin, owner, admin1, admin2) is
    deliberately separate from application RBAC permissions.
    """

    def __init__(self, connection):
        self.connection = connection

    def has_permission(
        self,
        user_id: int,
        permission_name: str,
        tenant_id: Optional[str] = None,
    ) -> bool:
        """
        Return True when the user has the requested active permission
        within the user's authenticated tenant.
        """

        user_row = self.connection.execute(
            """
            SELECT tenant_id, status
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()

        if user_row is None or user_row["status"] != "active":
            return False

        authenticated_tenant_id = user_row["tenant_id"]

        if (
            tenant_id is not None
            and tenant_id != authenticated_tenant_id
        ):
            return False

        row = self.connection.execute(
            """
            SELECT 1
            FROM user_roles AS ur
            JOIN roles AS r
              ON r.id = ur.role_id
             AND r.tenant_id = ur.tenant_id
            JOIN role_permissions AS rp
              ON rp.role_id = r.id
             AND rp.tenant_id = r.tenant_id
            JOIN permissions AS p
              ON p.id = rp.permission_id
             AND p.tenant_id = rp.tenant_id
            WHERE ur.tenant_id = ?
              AND ur.user_id = ?
              AND r.status = 'active'
              AND p.name = ?
              AND p.status = 'active'
            LIMIT 1
            """,
            (
                authenticated_tenant_id,
                user_id,
                permission_name,
            ),
        ).fetchone()

        return row is not None

    def get_permissions(
        self,
        user_id: int,
        tenant_id: Optional[str] = None,
    ) -> Set[str]:
        """
        Return all active permission names assigned to the user.

        The user's authenticated tenant is authoritative.
        """

        user_row = self.connection.execute(
            """
            SELECT tenant_id, status
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()

        if user_row is None or user_row["status"] != "active":
            return set()

        authenticated_tenant_id = user_row["tenant_id"]

        if (
            tenant_id is not None
            and tenant_id != authenticated_tenant_id
        ):
            return set()

        rows = self.connection.execute(
            """
            SELECT DISTINCT p.name
            FROM user_roles AS ur
            JOIN roles AS r
              ON r.id = ur.role_id
             AND r.tenant_id = ur.tenant_id
            JOIN role_permissions AS rp
              ON rp.role_id = r.id
             AND rp.tenant_id = r.tenant_id
            JOIN permissions AS p
              ON p.id = rp.permission_id
             AND p.tenant_id = rp.tenant_id
            WHERE ur.tenant_id = ?
              AND ur.user_id = ?
              AND r.status = 'active'
              AND p.status = 'active'
            ORDER BY p.name
            """,
            (
                authenticated_tenant_id,
                user_id,
            ),
        ).fetchall()

        return {row["name"] for row in rows}
