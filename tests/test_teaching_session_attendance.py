from models.teaching_session_attendance import TeachingSessionAttendance


def test_teaching_session_attendance_defaults():
    attendance = TeachingSessionAttendance(
        id=None,
        tenant_id="tenant-cmos",
        teaching_session_id=1,
        membership_id=2,
        attendance_date="2026-01-15",
    )

    assert attendance.status == "present"
    assert attendance.remark is None


def test_teaching_session_attendance_preserves_explicit_values():
    attendance = TeachingSessionAttendance(
        id=7,
        tenant_id="tenant-cmos",
        teaching_session_id=3,
        membership_id=4,
        attendance_date="2026-02-20",
        status="late",
        remark="Arrived after commencement",
    )

    assert attendance.id == 7
    assert attendance.tenant_id == "tenant-cmos"
    assert attendance.teaching_session_id == 3
    assert attendance.membership_id == 4
    assert attendance.attendance_date == "2026-02-20"
    assert attendance.status == "late"
    assert attendance.remark == "Arrived after commencement"


def test_teaching_session_attendance_is_immutable():
    attendance = TeachingSessionAttendance(
        id=None,
        tenant_id="tenant-cmos",
        teaching_session_id=1,
        membership_id=2,
        attendance_date="2026-01-15",
    )

    try:
        attendance.status = "absent"
        assert False, "expected frozen dataclass to reject mutation"
    except AttributeError:
        pass
