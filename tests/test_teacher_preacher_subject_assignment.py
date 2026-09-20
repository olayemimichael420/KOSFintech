from models.teacher_preacher_subject_assignment import TeacherPreacherSubjectAssignment


def test_teacher_preacher_subject_assignment_defaults_to_active():
    assignment = TeacherPreacherSubjectAssignment(
        id=None,
        tenant_id="tenant-cmos",
        teacher_preacher_id=1,
        teaching_subject_id=2,
    )

    assert assignment.status == "active"


def test_teacher_preacher_subject_assignment_preserves_values():
    assignment = TeacherPreacherSubjectAssignment(
        id=7,
        tenant_id="tenant-cmos",
        teacher_preacher_id=3,
        teaching_subject_id=5,
        status="inactive",
    )

    assert assignment.id == 7
    assert assignment.tenant_id == "tenant-cmos"
    assert assignment.teacher_preacher_id == 3
    assert assignment.teaching_subject_id == 5
    assert assignment.status == "inactive"
