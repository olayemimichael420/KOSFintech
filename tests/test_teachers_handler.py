import asyncio
from types import SimpleNamespace
from handlers.teachers import teachers


class FakeMessage:
    def __init__(self):
        self.messages = []

    async def reply_text(self, text):
        self.messages.append(text)


def test_teachers_denies_missing_administration_context():
    message = FakeMessage()
    update = SimpleNamespace(message=message)
    context = SimpleNamespace(application=SimpleNamespace(bot_data={"get_administration_context": lambda u, c: None, "services": None}))

    asyncio.run(teachers(update, context))

    assert message.messages == ["Access denied: unable to resolve an authorized administration context."]


def test_teachers_lists_authorized_teachers():
    message = FakeMessage()
    update = SimpleNamespace(message=message)
    admin = SimpleNamespace(tenant_id="tenant-1", user_id=7)
    teacher = SimpleNamespace(name="Ada", subject="Mathematics", status="active")

    class FakeTeacherService:
        def list(self):
            return [teacher]

    class FakeServices:
        def teacher(self, tenant_id, user_id=None):
            assert tenant_id == "tenant-1"
            assert user_id == 7
            return FakeTeacherService()

    context = SimpleNamespace(application=SimpleNamespace(bot_data={"get_administration_context": lambda u, c: admin, "services": FakeServices()}))

    asyncio.run(teachers(update, context))

    assert message.messages == ["Teachers:\nAda — Mathematics — active"]
