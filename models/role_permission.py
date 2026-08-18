from dataclasses import dataclass


@dataclass
class RolePermissionLink:
    tenant_id: str
    role_id: int
    permission_id: int
