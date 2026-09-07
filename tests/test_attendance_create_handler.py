import asyncio
from types import SimpleNamespace

from handlers.attendance_create import (
    ATTENDANCE_DATE,
    REMARK,
    STATUS,
    STUDENT_ID,
    attendance,
    attendance_date,
    attendance_remark,
    attendance_status,
    attendance_student_id,
    cancel_attendance,
)
from telegram.ext import ConversationHandler


def run(coro):
    return asyncio.run(coro)


def make_context(resolver, services=None):
    application = SimpleNamespace(
        bot_data={
            "get_administration_context": resolver,
            "services": services,
        }
    )
    return SimpleNamespace(application=application, user_data={})


def make_update(text=None):
    message = SimpleNamespace(text=text, replies=[])

    async def reply_text(value):
        message.replies.append(value)

    message.reply_text = reply_text
    return SimpleNamespace(message=message)


def test_attendance_denies_without_administration_context():
    context = make_context(lambda update, context: None)
    update = make_update()

    result = run(attendance(update, context))

    assert result == ConversationHandler.END
    assert "Access denied" in update.message.replies[0]


def test_attendance_student_id_rejects_invalid_value():
    context = make_context(lambda update, context: None)
    update = make_update("abc")

    result = run(attendance_student_id(update, context))

    assert result == STUDENT_ID
    assert "must be a number" in update.message.replies[0]


def test_attendance_student_id_accepts_positive_id():
    context = make_context(lambda update, context: None)
    update = make_update("12")

    result = run(attendance_student_id(update, context))

    assert result == ATTENDANCE_DATE
    assert context.user_data["attendance_student_id"] == 12


def test_attendance_date_rejects_invalid_date():
    context = make_context(lambda update, context: None)
    update = make_update("2026-99-99")

    result = run(attendance_date(update, context))

    assert result == ATTENDANCE_DATE
    assert "Invalid date" in update.message.replies[0]


def test_attendance_date_accepts_valid_date():
    context = make_context(lambda update, context: None)
    update = make_update("2026-09-06")

    result = run(attendance_date(update, context))

    assert result == STATUS
    assert context.user_data["attendance_date"] == "2026-09-06"


def test_attendance_status_rejects_invalid_status():
    context = make_context(lambda update, context: None)
    update = make_update("holiday")

    result = run(attendance_status(update, context))

    assert result == STATUS
    assert "Invalid status" in update.message.replies[0]


def test_attendance_status_accepts_valid_status():
    context = make_context(lambda update, context: None)
    update = make_update("Late")

    result = run(attendance_status(update, context))

    assert result == REMARK
    assert context.user_data["attendance_status"] == "late"


def test_attendance_remark_records_with_authorized_context():
    administration_context = SimpleNamespace(
        tenant_id="tenant-a",
        user_id=42,
    )

    class FakeAttendanceService:
        def __init__(self):
            self.recorded = None

        def record(self, record):
            self.recorded = record
            record.id = 7
            return record

    service = FakeAttendanceService()

    class FakeServices:
        def attendance(self, tenant_id, user_id=None):
            assert tenant_id == "tenant-a"
            assert user_id == 42
            return service

    context = make_context(
        lambda update, context: administration_context,
        FakeServices(),
    )
    context.user_data.update(
        {
            "attendance_student_id": 12,
            "attendance_date": "2026-09-06",
            "attendance_status": "late",
        }
    )
    update = make_update("Arrived after first period")

    result = run(attendance_remark(update, context))

    assert result == ConversationHandler.END
    assert service.recorded is not None
    assert service.recorded.tenant_id == "tenant-a"
    assert service.recorded.student_id == 12
    assert service.recorded.attendance_date == "2026-09-06"
    assert service.recorded.status == "late"
    assert service.recorded.remark == "Arrived after first period"
    assert "Attendance recorded" in update.message.replies[0]
    assert "12" in update.message.replies[0]
    assert "attendance_student_id" not in context.user_data


def test_attendance_remark_converts_none_to_null_remark():
    administration_context = SimpleNamespace(
        tenant_id="tenant-a",
        user_id=42,
    )

    class FakeAttendanceService:
        def record(self, record):
            assert record.remark is None
            record.id = 8
            return record

    class FakeServices:
        def attendance(self, tenant_id, user_id=None):
            return FakeAttendanceService()

    context = make_context(
        lambda update, context: administration_context,
        FakeServices(),
    )
    context.user_data.update(
        {
            "attendance_student_id": 12,
            "attendance_date": "2026-09-06",
            "attendance_status": "present",
        }
    )
    update = make_update("none")

    result = run(attendance_remark(update, context))

    assert result == ConversationHandler.END
    assert "Attendance recorded" in update.message.replies[0]


def test_attendance_remark_denies_unauthorized_write():
    administration_context = SimpleNamespace(
        tenant_id="tenant-a",
        user_id=42,
    )

    class FakeAttendanceService:
        def record(self, record):
            raise PermissionError("missing permission: attendance.write")

    class FakeServices:
        def attendance(self, tenant_id, user_id=None):
            return FakeAttendanceService()

    context = make_context(
        lambda update, context: administration_context,
        FakeServices(),
    )
    context.user_data.update(
        {
            "attendance_student_id": 12,
            "attendance_date": "2026-09-06",
            "attendance_status": "present",
        }
    )
    update = make_update("none")

    result = run(attendance_remark(update, context))

    assert result == ConversationHandler.END
    assert "attendance.write" in update.message.replies[0]
    assert "attendance_student_id" not in context.user_data


def test_cancel_attendance_clears_session():
    context = make_context(lambda update, context: None)
    context.user_data.update(
        {
            "attendance_student_id": 12,
            "attendance_date": "2026-09-06",
            "attendance_status": "present",
        }
    )
    update = make_update()

    result = run(cancel_attendance(update, context))

    assert result == ConversationHandler.END
    assert context.user_data == {}
    assert "cancelled" in update.message.replies[0]
