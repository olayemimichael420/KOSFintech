from uuid import uuid4


class TenantIdentityGenerator:
    """
    Generates opaque, unique Tenant service-boundary identifiers.

    This component does not establish institutional provenance,
    confer authority, create administration authority, or grant
    authorization.
    """

    def generate(self) -> str:
        return str(uuid4())
