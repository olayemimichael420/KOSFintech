from technical_authority_firewall import (
    ConstitutionalAuthorityReference,
    FirewallResult,
    TechnicalAuthorityFirewall,
    TechnicalCapability,
)


def capability():
    return TechnicalCapability("ACTOR-001", "SUPER_ADMIN")


def authority(**overrides):
    values = {
        "authority_id": "AUTH-001",
        "holder_id": "ACTOR-001",
        "status": "ACTIVE",
        "provenance": "INDEPENDENT-AUTHORITY-BASIS",
    }
    values.update(overrides)
    return ConstitutionalAuthorityReference(**values)


def test_super_admin_without_authority_is_rejected():
    result = TechnicalAuthorityFirewall().validate_claim(capability(), None)
    assert result.result is FirewallResult.INVALID


def test_super_admin_cannot_create_authority_by_capability():
    result = TechnicalAuthorityFirewall().validate_claim(
        capability(),
        authority(status="PROPOSED"),
    )
    assert result.result is FirewallResult.INVALID


def test_mismatched_authority_holder_is_rejected():
    result = TechnicalAuthorityFirewall().validate_claim(
        capability(),
        authority(holder_id="OTHER-ACTOR"),
    )
    assert result.result is FirewallResult.INVALID


def test_authority_without_provenance_is_rejected():
    result = TechnicalAuthorityFirewall().validate_claim(
        capability(),
        authority(provenance=""),
    )
    assert result.result is FirewallResult.INVALID


def test_technical_capability_may_correspond_to_independent_authority():
    result = TechnicalAuthorityFirewall().validate_claim(capability(), authority())
    assert result.result is FirewallResult.VALID
