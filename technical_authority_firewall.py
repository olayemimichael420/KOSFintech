from dataclasses import dataclass
from enum import Enum


class FirewallResult(str, Enum):
    VALID = "VALID"
    INVALID = "INVALID"
    INDETERMINATE = "INDETERMINATE"


@dataclass(frozen=True)
class TechnicalCapability:
    actor_id: str
    capability: str


@dataclass(frozen=True)
class ConstitutionalAuthorityReference:
    authority_id: str
    holder_id: str
    status: str
    provenance: str


@dataclass(frozen=True)
class FirewallCheck:
    result: FirewallResult
    rule: str
    reason: str


class TechnicalAuthorityFirewall:
    """Developmental firewall: technical capability is not authority."""

    def validate_claim(self, capability: TechnicalCapability, authority: ConstitutionalAuthorityReference | None) -> FirewallCheck:
        if authority is None:
            return FirewallCheck(
                FirewallResult.INVALID,
                "K-TECH-AUTH-01",
                "technical capability has no independently represented constitutional authority",
            )

        if authority.holder_id != capability.actor_id:
            return FirewallCheck(
                FirewallResult.INVALID,
                "K-TECH-AUTH-02",
                "constitutional authority holder does not match technical actor",
            )

        if authority.status not in {"ESTABLISHED", "ACTIVE"}:
            return FirewallCheck(
                FirewallResult.INVALID,
                "K-TECH-AUTH-03",
                "represented constitutional authority is not established or active",
            )

        if not authority.provenance.strip():
            return FirewallCheck(
                FirewallResult.INVALID,
                "K-TECH-AUTH-04",
                "constitutional authority has no independent provenance",
            )

        return FirewallCheck(
            FirewallResult.VALID,
            "K-TECH-AUTH-01/02/03/04",
            "technical capability corresponds to a separately represented authority; capability itself did not create authority",
        )
