from dataclasses import dataclass


@dataclass(frozen=True)
class PersonUserLink:
    """
    Associates a global KOSFintech Person with a tenant-scoped User.

    A Person may have multiple Users.
    A User may be associated with only one Person.
    """

    person_id: int
    tenant_id: str
    user_id: int
