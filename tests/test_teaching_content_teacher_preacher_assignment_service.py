from unittest.mock import Mock

import pytest

from models.teaching_content_teacher_preacher_assignment import (
    TeachingContentTeacherPreacherAssignment,
)
from services.teaching_content_teacher_preacher_assignment_service import (
    TeachingContentTeacherPreacherAssignmentService,
)


def _assignment(tenant_id="tenant-cmos"):
    return TeachingContentTeacherPreacherAssignment(
        id=None,
        tenant_id=tenant_id,
        teaching_content_id=10,
        teacher_preacher_id=20,
    )


def test_create_delegates_to_repository():
    repository = Mock()
    expected = _assignment()
    repository.create.return_value = expected

    service = TeachingContentTeacherPreacherAssignmentService(
        repository=repository,
        tenant_id="tenant-cmos",
    )

    result = service.create(expected)

    assert result is expected
    repository.create.assert_called_once_with(expected)


def test_create_rejects_tenant_mismatch():
    repository = Mock()

    service = TeachingContentTeacherPreacherAssignmentService(
        repository=repository,
        tenant_id="tenant-cmos",
    )

    with pytest.raises(ValueError, match="tenant mismatch"):
        service.create(_assignment("tenant-other"))

    repository.create.assert_not_called()


def test_list_uses_service_tenant():
    repository = Mock()
    repository.list.return_value = []

    service = TeachingContentTeacherPreacherAssignmentService(
        repository=repository,
        tenant_id="tenant-cmos",
    )

    result = service.list(10)

    assert result == []
    repository.list.assert_called_once_with(
        "tenant-cmos",
        10,
    )


def test_get_uses_service_tenant():
    repository = Mock()
    repository.get.return_value = None

    service = TeachingContentTeacherPreacherAssignmentService(
        repository=repository,
        tenant_id="tenant-cmos",
    )

    result = service.get(7)

    assert result is None
    repository.get.assert_called_once_with(
        "tenant-cmos",
        7,
    )


def test_create_requires_write_permission():
    repository = Mock()
    connection = Mock()
    permission_service = Mock()
    permission_service.has_permission.return_value = False

    service = TeachingContentTeacherPreacherAssignmentService(
        repository=repository,
        tenant_id="tenant-cmos",
        connection=connection,
        user_id=1,
    )
    service.permission_service = permission_service

    with pytest.raises(PermissionError):
        service.create(_assignment())

    permission_service.has_permission.assert_called_once_with(
        user_id=1,
        permission_name="teaching_content_teacher_preacher_assignment.write",
        tenant_id="tenant-cmos",
    )
    repository.create.assert_not_called()


def test_list_requires_read_permission():
    repository = Mock()
    connection = Mock()
    permission_service = Mock()
    permission_service.has_permission.return_value = False

    service = TeachingContentTeacherPreacherAssignmentService(
        repository=repository,
        tenant_id="tenant-cmos",
        connection=connection,
        user_id=1,
    )
    service.permission_service = permission_service

    with pytest.raises(PermissionError):
        service.list(10)

    permission_service.has_permission.assert_called_once_with(
        user_id=1,
        permission_name="teaching_content_teacher_preacher_assignment.read",
        tenant_id="tenant-cmos",
    )
    repository.list.assert_not_called()


def test_get_requires_read_permission():
    repository = Mock()
    connection = Mock()
    permission_service = Mock()
    permission_service.has_permission.return_value = False

    service = TeachingContentTeacherPreacherAssignmentService(
        repository=repository,
        tenant_id="tenant-cmos",
        connection=connection,
        user_id=1,
    )
    service.permission_service = permission_service

    with pytest.raises(PermissionError):
        service.get(7)

    permission_service.has_permission.assert_called_once_with(
        user_id=1,
        permission_name="teaching_content_teacher_preacher_assignment.read",
        tenant_id="tenant-cmos",
    )
    repository.get.assert_not_called()
