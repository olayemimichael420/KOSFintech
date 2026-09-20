from models.teacher_preacher import TeacherPreacher, TeacherPreacherRole


def test_teacher_preacher_model_defaults():
    capacity = TeacherPreacher(
        id=None,
        tenant_id="church-001",
        person_id=1,
        role=TeacherPreacherRole.TEACHER,
    )

    assert capacity.id is None
    assert capacity.tenant_id == "church-001"
    assert capacity.person_id == 1
    assert capacity.role == TeacherPreacherRole.TEACHER
    assert capacity.status == "active"


def test_teacher_preacher_supports_combined_role():
    capacity = TeacherPreacher(
        id=1,
        tenant_id="church-001",
        person_id=2,
        role=TeacherPreacherRole.TEACHER_PREACHER,
        status="active",
    )

    assert capacity.role == TeacherPreacherRole.TEACHER_PREACHER
    assert capacity.status == "active"
