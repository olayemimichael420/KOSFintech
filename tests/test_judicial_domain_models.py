from dataclasses import FrozenInstanceError

import pytest

from models.judicial_appointment import JudicialAppointment
from models.judicial_authority import (
    JudicialAuthority,
    JudicialAuthorityStatus,
)
from models.judicial_conferral import JudicialConferral
from models.judicial_jurisdiction import (
    JudicialJurisdiction,
    JudicialJurisdictionStatus,
)


def test_judicial_jurisdiction_defaults_to_active():
    jurisdiction = JudicialJurisdiction(
        id=None,
        tenant_id="tenant-001",
        jurisdiction_type="community",
        jurisdiction_scope="tenant-001",
        judicial_level="first_instance",
        case_types="service_act_dispute",
    )

    assert jurisdiction.id is None
    assert jurisdiction.status == JudicialJurisdictionStatus.ACTIVE
    assert jurisdiction.parent_jurisdiction_id is None


def test_judicial_jurisdiction_status_values_are_stable():
    assert JudicialJurisdictionStatus.ACTIVE.value == "active"
    assert JudicialJurisdictionStatus.INACTIVE.value == "inactive"


def test_judicial_appointment_preserves_constitutional_provenance():
    appointment = JudicialAppointment(
        id=None,
        candidate_user_id=10,
        jurisdiction_id=20,
        judicial_level="first_instance",
        appointment_source="constitutional_appointment",
        appointment_basis="approved qualification and appointment process",
        qualification_record="qualification-record-001",
        appointed_by=30,
    )

    assert appointment.candidate_user_id == 10
    assert appointment.jurisdiction_id == 20
    assert appointment.appointed_by == 30
    assert appointment.status == "appointed"
    assert appointment.appointed_at is None
    assert appointment.term_start is None
    assert appointment.term_end is None


def test_judicial_conferral_preserves_appointment_and_instrument():
    conferral = JudicialConferral(
        id=None,
        appointment_id=40,
        authority_id=50,
        conferring_authority="constitutional_conferring_authority",
        conferral_instrument="conferral-instrument-001",
    )

    assert conferral.appointment_id == 40
    assert conferral.authority_id == 50
    assert conferral.conferring_authority == (
        "constitutional_conferring_authority"
    )
    assert conferral.conferral_instrument == "conferral-instrument-001"
    assert conferral.status == "active"


def test_judicial_authority_defaults_to_proposed():
    authority = JudicialAuthority(
        id=None,
        user_id=10,
        authority_type="first_instance_judicial",
        jurisdiction_id=20,
        judicial_level="first_instance",
        appointment_id=30,
        conferral_id=40,
    )

    assert authority.id is None
    assert authority.status == JudicialAuthorityStatus.PROPOSED
    assert authority.effective_from is None
    assert authority.effective_until is None


def test_judicial_authority_status_values_are_stable():
    assert JudicialAuthorityStatus.PROPOSED.value == "proposed"
    assert JudicialAuthorityStatus.VETTED.value == "vetted"
    assert JudicialAuthorityStatus.APPOINTED.value == "appointed"
    assert JudicialAuthorityStatus.ACTIVE.value == "active"
    assert JudicialAuthorityStatus.SUSPENDED.value == "suspended"
    assert JudicialAuthorityStatus.INACTIVE.value == "inactive"
    assert JudicialAuthorityStatus.REVOKED.value == "revoked"
    assert JudicialAuthorityStatus.EXPIRED.value == "expired"


@pytest.mark.parametrize(
    "factory",
    [
        lambda: JudicialJurisdiction(
            id=None,
            tenant_id="tenant-001",
            jurisdiction_type="community",
            jurisdiction_scope="tenant-001",
            judicial_level="first_instance",
            case_types="service_act_dispute",
        ),
        lambda: JudicialAppointment(
            id=None,
            candidate_user_id=10,
            jurisdiction_id=20,
            judicial_level="first_instance",
            appointment_source="constitutional_appointment",
            appointment_basis="approved basis",
            qualification_record="record-001",
            appointed_by=30,
        ),
        lambda: JudicialConferral(
            id=None,
            appointment_id=40,
            authority_id=50,
            conferring_authority="constitutional_authority",
            conferral_instrument="instrument-001",
        ),
        lambda: JudicialAuthority(
            id=None,
            user_id=10,
            authority_type="first_instance_judicial",
            jurisdiction_id=20,
            judicial_level="first_instance",
            appointment_id=30,
            conferral_id=40,
        ),
    ],
)
def test_judicial_domain_models_are_immutable(factory):
    model = factory()

    with pytest.raises(FrozenInstanceError):
        model.id = 999
