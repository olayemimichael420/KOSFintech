import asyncio
import sqlite3
from types import SimpleNamespace

from telegram.ext import ConversationHandler

from handlers.school_student_create import (
    STUDENT_ID,
    linkstudent,
    school_student_id,
    cancel_linkstudent,
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


def test_linkstudent_denies_without_administration_context():
    context = make_context(lambda update, context: None, None)
    update = make_update()

    result = run(linkstudent(update, context))

    assert result == ConversationHandler.END
    assert "Access denied" in update.message.replies[0]


def test_linkstudent_requests_student_id():
    administration_context = SimpleNamespace(
        tenant_id="tenant-a",
        user_id=42,
    )
    context = make_context(
        lambda update, context: administration_context,
        None,
    )
    update = make_update()

    result = run(linkstudent(update, context))

    assert result == STUDENT_ID
    assert "student ID" in update.message.replies[0]


def test_school_student_id_rejects_non_numeric_value():
    context = make_context(lambda update, context: None, None)
    update = make_update("abc")

    result = run(school_student_id(update, context))

    assert result == STUDENT_ID
    assert "must be a number" in update.message.replies[0]


def test_school_student_id_rejects_non_positive_value():
    context = make_context(lambda update, context: None, None)
    update = make_update("0")

    result = run(school_student_id(update, context))

    assert result == STUDENT_ID
    assert "greater than zero" in update.message.replies[0]


def test_school_student_id_creates_relationship_with_authorized_context():
    administration_context = SimpleNamespace(
        tenant_id="tenant-a",
        user_id=42,
    )

    class FakeSchoolStudentService:
        def __init__(self):
            self.created = None

        def create(self, link):
            self.created = link
            return link

    service = FakeSchoolStudentService()

    class FakeServices:
        def school_student(self, tenant_id, user_id=None):
            assert tenant_id == "tenant-a"
            assert user_id == 42
            return service

    context = make_context(
        lambda update, context: administration_context,
        FakeServices(),
    )
    update = make_update("17")

    result = run(school_student_id(update, context))

    assert result == ConversationHandler.END
    assert service.created is not None
    assert service.created.tenant_id == "tenant-a"
    assert service.created.student_id == 17
    assert "relationship created" in update.message.replies[0]


def test_school_student_id_denies_without_write_permission():
    administration_context = SimpleNamespace(
        tenant_id="tenant-a",
        user_id=42,
    )

    class FakeSchoolStudentService:
        def create(self, link):
            raise PermissionError("missing permission")

    class FakeServices:
        def school_student(self, tenant_id, user_id=None):
            return FakeSchoolStudentService()

    context = make_context(
        lambda update, context: administration_context,
        FakeServices(),
    )
    update = make_update("17")

    result = run(school_student_id(update, context))

    assert result == ConversationHandler.END
    assert "school_student.write" in update.message.replies[0]


def test_school_student_id_handles_integrity_conflict():
    administration_context = SimpleNamespace(
        tenant_id="tenant-a",
        user_id=42,
    )

    class FakeSchoolStudentService:
        def create(self, link):
            raise sqlite3.IntegrityError("duplicate")

    class FakeServices:
        def school_student(self, tenant_id, user_id=None):
            return FakeSchoolStudentService()

    context = make_context(
        lambda update, context: administration_context,
        FakeServices(),
    )
    update = make_update("17")

    result = run(school_student_id(update, context))

    assert result == ConversationHandler.END
    assert "conflicts with existing data" in update.message.replies[0]


def test_cancel_linkstudent_ends_workflow():
    context = make_context(lambda update, context: None, None)
    update = make_update()

    result = run(cancel_linkstudent(update, context))

    assert result == ConversationHandler.END
    assert "cancelled" in update.message.replies[0]
