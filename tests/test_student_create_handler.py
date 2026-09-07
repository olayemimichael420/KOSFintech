import asyncio
from types import SimpleNamespace

from handlers.student_create import (
    NAME,
    CLASS_NAME,
    addstudent,
    student_name,
    student_class,
)
from telegram.ext import ConversationHandler


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


def test_addstudent_denies_without_administration_context():
    resolver = lambda update, context: None
    context = make_context(resolver, None)
    update = make_update()

    result = run(addstudent(update, context))

    assert result == ConversationHandler.END
    assert "Access denied" in update.message.replies[0]


def test_student_name_rejects_empty_name():
    context = make_context(lambda update, context: None, None)
    update = make_update("   ")

    result = run(student_name(update, context))

    assert result == NAME
    assert "cannot be empty" in update.message.replies[0]


def test_student_name_accepts_name_and_requests_class():
    context = make_context(lambda update, context: None, None)
    update = make_update("Ada Lovelace")

    result = run(student_name(update, context))

    assert result == CLASS_NAME
    assert context.user_data["student_name"] == "Ada Lovelace"
    assert "class" in update.message.replies[0]


def test_student_class_rejects_empty_class():
    context = make_context(lambda update, context: None, None)
    context.user_data["student_name"] = "Ada Lovelace"
    update = make_update("   ")

    result = run(student_class(update, context))

    assert result == CLASS_NAME
    assert "cannot be empty" in update.message.replies[0]


def test_student_class_creates_student_with_authorized_context():
    administration_context = SimpleNamespace(
        tenant_id="tenant-a",
        user_id=42,
    )

    class FakeStudentService:
        def __init__(self):
            self.created = None

        def create(self, student):
            self.created = student
            student.id = 17
            return student

    service = FakeStudentService()

    class FakeServices:
        def student(self, tenant_id, user_id=None):
            assert tenant_id == "tenant-a"
            assert user_id == 42
            return service

    context = make_context(
        lambda update, context: administration_context,
        FakeServices(),
    )
    context.user_data["student_name"] = "Ada Lovelace"
    update = make_update("Primary 5")

    result = run(student_class(update, context))

    assert result == ConversationHandler.END
    assert service.created is not None
    assert service.created.tenant_id == "tenant-a"
    assert service.created.name == "Ada Lovelace"
    assert service.created.class_name == "Primary 5"
    assert service.created.user_id is None
    assert service.created.age is None
    assert service.created.guardian_id is None
    assert service.created.id == 17
    assert "Student created" in update.message.replies[0]
    assert "17" in update.message.replies[0]
    assert "student_name" not in context.user_data
