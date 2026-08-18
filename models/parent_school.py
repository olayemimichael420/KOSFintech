from dataclasses import dataclass


@dataclass
class ParentSchoolLink:
    tenant_id: str
    parent_id: int
