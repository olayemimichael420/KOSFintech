import pytest

from models.session_teacher_preacher_assignment import (
    SessionTeacherPreacherAssignment,
)
from services.session_teacher_preacher_assignment_service import (
    SessionTeacherPreacherAssignmentService,
)


class FakeRepository:
    def __init__(self):
        self.created = []
        self.items = {}

    def create(self, assignment):
        created = SessionTeacherPreacherAssignment(
            id=1,
            tenant_id=assignment.tenant_id,
            teacher_preacher_id=assignment.teacher_preacher_id,
            teaching_session_id=assignment.teaching_session_id,
            status=assignment.status,
        )
        self.created.append(created)
        self.items[created.id] = created
        return created

    def get(self, tenant_id, assignment_id):
        assignment = self.items.get(assignment_id)
        if assignment is None or assignment.tenant_id != tenant_id:
            return None
        return assignment

    def list(self, tenant_id):
        return [
            assignment
            for assignment in self.items.values()
            if assignment.tenant_id == tenant_id
        ]


def test_create_delegates_with_matching_tenant():
    repository = FakeRepository()

    service = SessionTeacherPreacherAssignmentService(
        repository=repository,
        tenant_id="tenant-001",
    )

    assignment = SessionTeacherPreacherAssignment(
        id=None,
        tenant_id="tenant-001",
        teacher_preacher_id=10,
        teaching_session_id=20,
    )

    created = service.create(assignment)

    assert created.id == 1
    assert created.tenant_id == "tenant-001"
    assert created.teacher_preacher_id == 10
    assert created.teaching_session_id == 20


def test_create_rejects_tenant_mismatch():
    repository = FakeRepository()

    service = SessionTeacherPreacherAssignmentService(
        repository=repository,
        tenant_id="tenant-001",
    )

    assignment = SessionTeacherPreacherAssignment(
        id=None,
        tenant_id="tenant-002",
        teacher_preacher_id=10,
        teaching_session_id=20,
    )

    with pytest.raises(ValueError, match="tenant mismatch"):
        service.create(assignment)

    assert repository.created == []


def test_get_and_list_are_tenant_scoped():
    repository = FakeRepository()

    service = SessionTeacherPreacherAssignmentService(
        repository=repository,
        tenant_id="tenant-001",
    )

    created = service.create(
        SessionTeacherPreacherAssignment(
            id=None,
            tenant_id="tenant-001",
            teacher_preacher_id=10,
            teaching_session_id=20,
        )
    )

    assert service.get(created.id) == created
    assert service.list() == [created]


def test_permissions_are_explicit():
    assert (
        SessionTeacherPreacherAssignmentService.READ_PERMISSION
        == "session_teacher_preacher_assignment.read"
    )
    assert (
        SessionTeacherPreacherAssignmentService.WRITE_PERMISSION
        == "session_teacher_preacher_assignment.write"
    )
