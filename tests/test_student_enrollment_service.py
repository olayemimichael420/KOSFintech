from models.student_enrollment import StudentEnrollment
from services.student_enrollment_service import StudentEnrollmentService


class FakeRepository:
    def __init__(self):
        self.created = []
        self.items = {}

    def create(self, enrollment):
        enrollment.id = len(self.created) + 1
        self.created.append(enrollment)
        self.items[enrollment.id] = enrollment
        return enrollment

    def get(self, tenant_id, enrollment_id):
        enrollment = self.items.get(enrollment_id)
        if enrollment is None or enrollment.tenant_id != tenant_id:
            return None
        return enrollment

    def list(self, tenant_id, student_id):
        return [
            enrollment
            for enrollment in self.created
            if enrollment.tenant_id == tenant_id
            and enrollment.student_id == student_id
        ]


def make_enrollment(tenant_id):
    return StudentEnrollment(
        id=None,
        tenant_id=tenant_id,
        student_id=101,
        academic_class_id=201,
        academic_session_id=301,
        academic_term_id=401,
        enrollment_date="2026-09-01",
    )


def test_create_enforces_tenant_scope():
    repository = FakeRepository()
    service = StudentEnrollmentService(
        repository=repository,
        tenant_id="school-a",
    )

    enrollment = service.create(make_enrollment("school-a"))

    assert enrollment.id == 1
    assert enrollment.tenant_id == "school-a"


def test_create_rejects_tenant_mismatch():
    repository = FakeRepository()
    service = StudentEnrollmentService(
        repository=repository,
        tenant_id="school-a",
    )

    try:
        service.create(make_enrollment("school-b"))
    except ValueError as exc:
        assert str(exc) == "student enrollment tenant mismatch"
    else:
        raise AssertionError("expected tenant mismatch")


def test_list_is_tenant_scoped():
    repository = FakeRepository()
    repository.create(make_enrollment("school-a"))
    repository.create(make_enrollment("school-b"))

    service = StudentEnrollmentService(
        repository=repository,
        tenant_id="school-a",
    )

    result = service.list(101)

    assert len(result) == 1
    assert result[0].tenant_id == "school-a"


def test_get_is_tenant_scoped():
    repository = FakeRepository()

    school_a = repository.create(make_enrollment("school-a"))
    school_b = repository.create(make_enrollment("school-b"))

    service = StudentEnrollmentService(
        repository=repository,
        tenant_id="school-a",
    )

    assert service.get(school_a.id) is school_a
    assert service.get(school_b.id) is None


def test_permission_constants_defined():
    assert StudentEnrollmentService.READ_PERMISSION == "student_enrollment.read"
    assert StudentEnrollmentService.WRITE_PERMISSION == "student_enrollment.write"
