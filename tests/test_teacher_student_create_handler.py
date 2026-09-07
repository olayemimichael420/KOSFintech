import asyncio
import sqlite3
from types import SimpleNamespace

from telegram.ext import ConversationHandler

from handlers.teacher_student_create import (
    TEACHER_ID,
    STUDENT_ID,
    linkteacherstudent,
    teacher_student_teacher_id,
    teacher_student_student_id,
    cancel_linkteacherstudent,
)


def run(coro):
    return asyncio.run(coro)


def make_context(resolver, services):
    application = SimpleNamespace(
        bot_data={
            "get_administration_context": resolver,
            "services": services,
        }
    )
    return SimpleNamespace(application=application, user_data={})


def make_update(text=None):
    message = SimpleNamespace(
        text=text,
        replies=[],
    )

    async def reply_text(value):
        message.replies.append(value)

    message.reply_text = reply_text
    return SimpleNamespace(message=message)


def test_linkteacherstudent_denies_without_administration_context():
    context = make_context(lambda update, context: None, None)
    update = make_update()

    result = run(linkteacherstudent(update, context))

    assert result == ConversationHandler.END
    assert "Access denied" in update.message.replies[0]


def test_linkteacherstudent_requests_teacher_id():
    administration_context = SimpleNamespace(
        tenant_id="tenant-a",
        user_id=42,
    )
    context = make_context(
        lambda update, context: administration_context,
        None,
    )
    update = make_update()

    result = run(linkteacherstudent(update, context))

    assert result == TEACHER_ID
    assert "teacher ID" in update.message.replies[0]


def test_teacher_student_teacher_id_rejects_invalid_value():
    context = make_context(lambda update, context: None, None)
    update = make_update("abc")

    result = run(teacher_student_teacher_id(update, context))

    assert result == TEACHER_ID
    assert "must be a number" in update.message.replies[0]


def test_teacher_student_teacher_id_accepts_teacher_id():
    context = make_context(lambda update, context: None, None)
    update = make_update("12")

    result = run(teacher_student_teacher_id(update, context))

    assert result == STUDENT_ID
    assert context.user_data["teacher_student_teacher_id"] == 12
    assert "student ID" in update.message.replies[0]


def test_teacher_student_student_id_creates_relationship():
    administration_context = SimpleNamespace(
        tenant_id="tenant-a",
        user_id=42,
    )

    class FakeTeacherStudentService:
        def __init__(self):
            self.created = None

        def create(self, link):
            self.created = link
            return link

    service = FakeTeacherStudentService()

    class FakeServices:
        def teacher_student(self, tenant_id, user_id=None):
            assert tenant_id == "tenant-a"
            assert user_id == 42
            return service

    context = make_context(
        lambda update, context: administration_context,
        FakeServices(),
    )
    context.user_data["teacher_student_teacher_id"] = 12
    update = make_update("17")

    result = run(teacher_student_student_id(update, context))

    assert result == ConversationHandler.END
    assert service.created is not None
    assert service.created.tenant_id == "tenant-a"
    assert service.created.teacher_id == 12
    assert service.created.student_id == 17
    assert "relationship created" in update.message.replies[0]
    assert "teacher_student_teacher_id" not in context.user_data


def test_teacher_student_student_id_denies_without_write_permission():
    administration_context = SimpleNamespace(
        tenant_id="tenant-a",
        user_id=42,
    )

    class FakeTeacherStudentService:
        def create(self, link):
            raise PermissionError("missing permission")

    class FakeServices:
        def teacher_student(self, tenant_id, user_id=None):
            return FakeTeacherStudentService()

    context = make_context(
        lambda update, context: administration_context,
        FakeServices(),
    )
    context.user_data["teacher_student_teacher_id"] = 12
    update = make_update("17")

    result = run(teacher_student_student_id(update, context))

    assert result == ConversationHandler.END
    assert "teacher_student.write" in update.message.replies[0]


def test_teacher_student_student_id_handles_integrity_conflict():
    administration_context = SimpleNamespace(
        tenant_id="tenant-a",
        user_id=42,
    )

    class FakeTeacherStudentService:
        def create(self, link):
            raise sqlite3.IntegrityError("duplicate")

    class FakeServices:
        def teacher_student(self, tenant_id, user_id=None):
            return FakeTeacherStudentService()

    context = make_context(
        lambda update, context: administration_context,
        FakeServices(),
    )
    context.user_data["teacher_student_teacher_id"] = 12
    update = make_update("17")

    result = run(teacher_student_student_id(update, context))

    assert result == ConversationHandler.END
    assert "conflicts with existing data" in update.message.replies[0]


def test_cancel_linkteacherstudent_ends_workflow():
    context = make_context(lambda update, context: None, None)
    context.user_data["teacher_student_teacher_id"] = 12
    update = make_update()

    result = run(cancel_linkteacherstudent(update, context))

    assert result == ConversationHandler.END
    assert "cancelled" in update.message.replies[0]
    assert "teacher_student_teacher_id" not in context.user_data
