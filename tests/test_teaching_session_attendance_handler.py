import asyncio
from types import SimpleNamespace

from telegram.ext import ConversationHandler

from handlers.teaching_session_attendance_create import (
    ATTENDANCE_DATE,
    MEMBERSHIP_ID,
    STATUS,
    TEACHING_SESSION_ID,
    cancel_teaching_attendance,
    teaching_attendance,
    teaching_attendance_date,
    teaching_attendance_membership_id,
    teaching_attendance_session_id,
    teaching_attendance_status,
)


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


def test_teaching_attendance_denies_without_administration_context():
    context = make_context(lambda update, context: None)
    update = make_update()

    result = run(teaching_attendance(update, context))

    assert result == ConversationHandler.END
    assert "Access denied" in update.message.replies[0]


def test_teaching_attendance_session_id_accepts_positive_id():
    context = make_context(lambda update, context: None)
    update = make_update("12")

    result = run(teaching_attendance_session_id(update, context))

    assert result == MEMBERSHIP_ID
    assert context.user_data["teaching_session_attendance_session_id"] == 12


def test_teaching_attendance_membership_id_accepts_positive_id():
    context = make_context(lambda update, context: None)
    update = make_update("21")

    result = run(teaching_attendance_membership_id(update, context))

    assert result == ATTENDANCE_DATE
    assert context.user_data["teaching_session_attendance_membership_id"] == 21


def test_teaching_attendance_date_accepts_valid_date():
    context = make_context(lambda update, context: None)
    update = make_update("2026-09-19")

    result = run(teaching_attendance_date(update, context))

    assert result == STATUS
    assert context.user_data["teaching_session_attendance_date"] == "2026-09-19"


def test_teaching_attendance_status_rejects_invalid_status():
    context = make_context(lambda update, context: None)
    update = make_update("holiday")

    result = run(teaching_attendance_status(update, context))

    assert result == STATUS
    assert "Invalid status" in update.message.replies[0]


def test_teaching_attendance_status_records_with_authorized_context():
    administration_context = SimpleNamespace(
        tenant_id="tenant-cmos",
        user_id=42,
    )

    class FakeAttendanceService:
        def __init__(self):
            self.recorded = None

        def record(self, record):
            self.recorded = record
            return record

    service = FakeAttendanceService()

    class FakeServices:
        def teaching_session_attendance(self, tenant_id, user_id=None):
            assert tenant_id == "tenant-cmos"
            assert user_id == 42
            return service

    context = make_context(
        lambda update, context: administration_context,
        FakeServices(),
    )
    context.user_data.update(
        {
            "teaching_session_attendance_session_id": 12,
            "teaching_session_attendance_membership_id": 21,
            "teaching_session_attendance_date": "2026-09-19",
        }
    )
    update = make_update("late")

    result = run(teaching_attendance_status(update, context))

    assert result == ConversationHandler.END
    assert service.recorded is not None
    assert service.recorded.tenant_id == "tenant-cmos"
    assert service.recorded.teaching_session_id == 12
    assert service.recorded.membership_id == 21
    assert service.recorded.attendance_date == "2026-09-19"
    assert service.recorded.status == "late"
    assert "Teaching attendance recorded" in update.message.replies[0]
    assert context.user_data == {}


def test_cancel_teaching_attendance_clears_session():
    context = make_context(lambda update, context: None)
    context.user_data.update(
        {
            "teaching_session_attendance_session_id": 12,
            "teaching_session_attendance_membership_id": 21,
            "teaching_session_attendance_date": "2026-09-19",
        }
    )
    update = make_update()

    result = run(cancel_teaching_attendance(update, context))

    assert result == ConversationHandler.END
    assert context.user_data == {}
    assert "cancelled" in update.message.replies[0]
