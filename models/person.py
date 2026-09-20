from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Person:
    """
    KOSFintech-wide human identity.

    Person identifies the human being. It does not establish
    application authentication, institutional membership,
    capacity, authority, assignment, participation, or permission.
    """

    id: Optional[int]
    name: str
    status: str = "active"
