import sqlite3

import pytest

from database import init_db
from models.reputation import ReputationEvent
from models.reputation_profile import ReputationProfile
from repositories.reputation_repository import ReputationRepository
from services.reputation_profile_service import ReputationProfileService


def _setup(tmp_path):
    db_path = tmp_path / "reputation_profile.db"

    import config

    original_db_file = config.settings.db_file

    object.__setattr__(config.settings, "db_file", db_path)

    try:
        init_db()
    finally:
        object.__setattr__(config.settings, "db_file", original_db_file)

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    user_ids = []

    for name in ("Provider", "Reviewer"):
        cursor = connection.execute(
            """
            INSERT INTO users
                (tenant_id, name, email, role, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "tenant-001",
                name,
                f"{name.lower()}@example.com",
                "member",
                "active",
            ),
        )
        user_ids.append(cursor.lastrowid)

    connection.commit()

    repository = ReputationRepository(connection)
    service = ReputationProfileService(repository)

    return connection, repository, service, user_ids


def _create_event(
    connection,
    repository,
    service_act_id,
    subject_user_id,
    reviewer_user_id,
    score,
    tenant_id="tenant-001",
):
    connection.execute(
        """
        INSERT INTO service_acts (
            tenant_id,
            provider_user_id,
            recipient_user_id,
            title,
            description,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            tenant_id,
            subject_user_id,
            reviewer_user_id,
            f"Service Act {service_act_id}",
            "Completed test service.",
            "completed",
        ),
    )
    connection.commit()

    event = ReputationEvent(
        id=None,
        tenant_id=tenant_id,
        service_act_id=service_act_id,
        subject_user_id=subject_user_id,
        reviewer_user_id=reviewer_user_id,
        score=score,
        comment=None,
        created_at=None,
    )

    return repository.create(event)


def test_empty_profile_returns_zero_values(tmp_path):
    connection, _, service, user_ids = _setup(tmp_path)

    provider_id, _ = user_ids

    profile = service.get_profile(
        "tenant-001",
        provider_id,
    )

    assert isinstance(profile, ReputationProfile)
    assert profile.tenant_id == "tenant-001"
    assert profile.user_id == provider_id
    assert profile.average_score == 0.0
    assert profile.total_reviews == 0
    assert profile.score_5_count == 0
    assert profile.score_4_count == 0
    assert profile.score_3_count == 0
    assert profile.score_2_count == 0
    assert profile.score_1_count == 0

    connection.close()


def test_single_five_star_review(tmp_path):
    connection, repository, service, user_ids = _setup(tmp_path)

    provider_id, reviewer_id = user_ids

    _create_event(
        connection,
        repository,
        service_act_id=1,
        subject_user_id=provider_id,
        reviewer_user_id=reviewer_id,
        score=5,
    )

    profile = service.get_profile(
        "tenant-001",
        provider_id,
    )

    assert profile.average_score == 5.0
    assert profile.total_reviews == 1
    assert profile.score_5_count == 1
    assert profile.score_4_count == 0
    assert profile.score_3_count == 0
    assert profile.score_2_count == 0
    assert profile.score_1_count == 0

    connection.close()


def test_mixed_scores_produce_correct_distribution_and_average(tmp_path):
    connection, repository, service, user_ids = _setup(tmp_path)

    provider_id, reviewer_id = user_ids

    for service_act_id, score in enumerate(
        [5, 5, 4, 3, 2, 1],
        start=1,
    ):
        _create_event(
            connection,
            repository,
            service_act_id=service_act_id,
            subject_user_id=provider_id,
            reviewer_user_id=reviewer_id,
            score=score,
        )

    profile = service.get_profile(
        "tenant-001",
        provider_id,
    )

    assert profile.total_reviews == 6
    assert profile.average_score == pytest.approx(20 / 6)
    assert profile.score_5_count == 2
    assert profile.score_4_count == 1
    assert profile.score_3_count == 1
    assert profile.score_2_count == 1
    assert profile.score_1_count == 1

    connection.close()


def test_profile_is_tenant_scoped(tmp_path):
    connection, repository, service, user_ids = _setup(tmp_path)

    provider_id, reviewer_id = user_ids

    _create_event(
        connection,
        repository,
        service_act_id=1,
        subject_user_id=provider_id,
        reviewer_user_id=reviewer_id,
        score=5,
        tenant_id="tenant-001",
    )

    profile = service.get_profile(
        "tenant-002",
        provider_id,
    )

    assert profile.tenant_id == "tenant-002"
    assert profile.total_reviews == 0
    assert profile.average_score == 0.0

    connection.close()


def test_profile_is_immutable(tmp_path):
    connection, _, service, user_ids = _setup(tmp_path)

    provider_id, _ = user_ids

    profile = service.get_profile(
        "tenant-001",
        provider_id,
    )

    with pytest.raises(AttributeError):
        profile.average_score = 5.0

    connection.close()
