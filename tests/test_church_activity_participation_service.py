from unittest.mock import Mock

import pytest

from models.church_activity_participation import ChurchActivityParticipation
from services.church_activity_participation_service import (
    ChurchActivityParticipationService,
)


def test_create_enforces_tenant_and_delegates():
    repository = Mock()
    participation = ChurchActivityParticipation(
        tenant_id="tenant-1",
        church_activity_id=10,
        membership_id=20,
    )
    repository.create.return_value = participation

    service = ChurchActivityParticipationService(
        repository=repository,
        tenant_id="tenant-1",
    )

    assert service.create(participation) == participation
    repository.create.assert_called_once_with(participation)


def test_create_rejects_tenant_mismatch():
    repository = Mock()

    service = ChurchActivityParticipationService(
        repository=repository,
        tenant_id="tenant-1",
    )

    participation = ChurchActivityParticipation(
        tenant_id="tenant-2",
        church_activity_id=10,
        membership_id=20,
    )

    with pytest.raises(
        ValueError,
        match="church activity participation tenant mismatch",
    ):
        service.create(participation)

    repository.create.assert_not_called()


def test_get_uses_service_tenant():
    repository = Mock()
    expected = ChurchActivityParticipation(
        tenant_id="tenant-1",
        church_activity_id=10,
        membership_id=20,
    )
    repository.get.return_value = expected

    service = ChurchActivityParticipationService(
        repository=repository,
        tenant_id="tenant-1",
    )

    assert service.get(10, 20) == expected
    repository.get.assert_called_once_with(
        "tenant-1",
        10,
        20,
    )


def test_list_by_activity_uses_service_tenant():
    repository = Mock()
    expected = [
        ChurchActivityParticipation(
            tenant_id="tenant-1",
            church_activity_id=10,
            membership_id=20,
        )
    ]
    repository.list_by_activity.return_value = expected

    service = ChurchActivityParticipationService(
        repository=repository,
        tenant_id="tenant-1",
    )

    assert service.list_by_activity(10) == expected
    repository.list_by_activity.assert_called_once_with(
        "tenant-1",
        10,
    )


def test_list_by_member_uses_service_tenant():
    repository = Mock()
    expected = [
        ChurchActivityParticipation(
            tenant_id="tenant-1",
            church_activity_id=10,
            membership_id=20,
        )
    ]
    repository.list_by_member.return_value = expected

    service = ChurchActivityParticipationService(
        repository=repository,
        tenant_id="tenant-1",
    )

    assert service.list_by_member(20) == expected
    repository.list_by_member.assert_called_once_with(
        "tenant-1",
        20,
    )


def test_missing_write_permission_rejected(db_connection):
    tenant_id = "tenant-cmos"

    db_connection.execute(
        "INSERT INTO tenants (tenant_id, status) VALUES (?, 'active')",
        (tenant_id,),
    )
    db_connection.commit()

    repository = Mock()
    service = ChurchActivityParticipationService(
        repository=repository,
        tenant_id=tenant_id,
        connection=db_connection,
        user_id="user-without-permission",
    )

    participation = ChurchActivityParticipation(
        tenant_id=tenant_id,
        church_activity_id=10,
        membership_id=20,
    )

    with pytest.raises(
        PermissionError,
        match="church_activity_participation.write",
    ):
        service.create(participation)

    repository.create.assert_not_called()


def test_granted_write_permission_allows_create(db_connection):
    tenant_id = "tenant-cmos"

    db_connection.execute(
        "INSERT INTO tenants (tenant_id, status) VALUES (?, 'active')",
        (tenant_id,),
    )

    user_id = db_connection.execute(
        """
        INSERT INTO users (tenant_id, name, role)
        VALUES (?, ?, ?)
        """,
        (tenant_id, "CMOS Writer", "member"),
    ).lastrowid

    role_id = db_connection.execute(
        """
        INSERT INTO roles (tenant_id, name, status)
        VALUES (?, ?, 'active')
        """,
        (tenant_id, "cmos_participation_writer"),
    ).lastrowid

    permission_id = db_connection.execute(
        """
        INSERT INTO permissions (tenant_id, name, status)
        VALUES (?, ?, 'active')
        """,
        (tenant_id, "church_activity_participation.write"),
    ).lastrowid

    db_connection.execute(
        """
        INSERT INTO user_roles (tenant_id, user_id, role_id)
        VALUES (?, ?, ?)
        """,
        (tenant_id, user_id, role_id),
    )

    db_connection.execute(
        """
        INSERT INTO role_permissions (
            tenant_id,
            role_id,
            permission_id
        )
        VALUES (?, ?, ?)
        """,
        (tenant_id, role_id, permission_id),
    )

    db_connection.commit()

    repository = Mock()
    participation = ChurchActivityParticipation(
        tenant_id=tenant_id,
        church_activity_id=10,
        membership_id=20,
    )
    repository.create.return_value = participation

    service = ChurchActivityParticipationService(
        repository=repository,
        tenant_id=tenant_id,
        connection=db_connection,
        user_id=user_id,
    )

    assert service.create(participation) == participation
    repository.create.assert_called_once_with(participation)


def test_granted_read_permission_allows_get(db_connection):
    tenant_id = "tenant-cmos"

    db_connection.execute(
        "INSERT INTO tenants (tenant_id, status) VALUES (?, 'active')",
        (tenant_id,),
    )

    user_id = db_connection.execute(
        """
        INSERT INTO users (tenant_id, name, role)
        VALUES (?, ?, ?)
        """,
        (tenant_id, "CMOS Reader", "member"),
    ).lastrowid

    role_id = db_connection.execute(
        """
        INSERT INTO roles (tenant_id, name, status)
        VALUES (?, ?, 'active')
        """,
        (tenant_id, "cmos_participation_reader"),
    ).lastrowid

    permission_id = db_connection.execute(
        """
        INSERT INTO permissions (tenant_id, name, status)
        VALUES (?, ?, 'active')
        """,
        (tenant_id, "church_activity_participation.read"),
    ).lastrowid

    db_connection.execute(
        """
        INSERT INTO user_roles (tenant_id, user_id, role_id)
        VALUES (?, ?, ?)
        """,
        (tenant_id, user_id, role_id),
    )

    db_connection.execute(
        """
        INSERT INTO role_permissions (
            tenant_id,
            role_id,
            permission_id
        )
        VALUES (?, ?, ?)
        """,
        (tenant_id, role_id, permission_id),
    )

    db_connection.commit()

    repository = Mock()
    expected = ChurchActivityParticipation(
        tenant_id=tenant_id,
        church_activity_id=10,
        membership_id=20,
    )
    repository.get.return_value = expected

    service = ChurchActivityParticipationService(
        repository=repository,
        tenant_id=tenant_id,
        connection=db_connection,
        user_id=user_id,
    )

    assert service.get(10, 20) == expected
    repository.get.assert_called_once_with(
        tenant_id,
        10,
        20,
    )


def test_missing_read_permission_rejected(db_connection):
    tenant_id = "tenant-cmos"

    db_connection.execute(
        "INSERT INTO tenants (tenant_id, status) VALUES (?, 'active')",
        (tenant_id,),
    )
    db_connection.commit()

    repository = Mock()
    service = ChurchActivityParticipationService(
        repository=repository,
        tenant_id=tenant_id,
        connection=db_connection,
        user_id="user-without-permission",
    )

    with pytest.raises(
        PermissionError,
        match="church_activity_participation.read",
    ):
        service.get(10, 20)

    repository.get.assert_not_called()
