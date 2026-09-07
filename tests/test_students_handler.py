import asyncio
from types import SimpleNamespace
from handlers.students import students

class FakeMessage:
    def __init__(self):
        self.messages = []

    async def reply_text(self, text):
        self.messages.append(text)

def test_students_denies_missing_administration_context():
    message = FakeMessage()
    update = SimpleNamespace(message=message)
    context = SimpleNamespace(application=SimpleNamespace(bot_data={'get_administration_context': lambda u, c: None, 'services': None}))

    asyncio.run(students(update, context))

    assert message.messages == ["Access denied: unable to resolve an authorized administration context."]

def test_students_lists_authorized_students():
    message = FakeMessage()
    update = SimpleNamespace(message=message)
    admin = SimpleNamespace(tenant_id="tenant-1", user_id=7)

    student = SimpleNamespace(name="Ada", class_name="Primary 5", status="active")

    class FakeStudentService:
        def list(self):
            return [student]

    class FakeServices:
        def student(self, tenant_id, user_id=None):
            assert tenant_id == "tenant-1"
            assert user_id == 7
            return FakeStudentService()

    context = SimpleNamespace(application=SimpleNamespace(bot_data={'get_administration_context': lambda u, c: admin, 'services': FakeServices()}))

    asyncio.run(students(update, context))

    assert message.messages == ["Students:\nAda — Primary 5 — active"]
