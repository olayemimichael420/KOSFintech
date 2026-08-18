from dataclasses import dataclass


@dataclass
class UserRoleLink:
    tenant_id: str
    user_id: int
    role_id: int
