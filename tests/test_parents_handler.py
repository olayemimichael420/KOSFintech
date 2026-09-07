import asyncio
from types import SimpleNamespace
from handlers.parents import parents


class FakeMessage:
    def __init__(self):
        self.messages = []

    async def reply_text(self, text):
        self.messages.append(text)


def test_parents_denies_missing_administration_context():
    message = FakeMessage()
    update = SimpleNamespace(message=message)
    context = SimpleNamespace(application=SimpleNamespace(bot_data={"get_administration_context": lambda u, c: None, "services": None}))

    asyncio.run(parents(update, context))

    assert message.messages == ["Access denied: unable to resolve an authorized administration context."]

def test_parents_lists_authorized_parents():
    message = FakeMessage()
    update = SimpleNamespace(message=message)
    admin = SimpleNamespace(tenant_id="tenant-1", user_id=7)
    parent = SimpleNamespace(name="Grace", phone="08012345678", status="active")

    class FakeParentService:
        def list(self):
            return [parent]

    class FakeServices:
        def parent(self, tenant_id, user_id=None):
            assert tenant_id == "tenant-1"
            assert user_id == 7
            return FakeParentService()

    context = SimpleNamespace(application=SimpleNamespace(bot_data={"get_administration_context": lambda u, c: admin, "services": FakeServices()}))

    asyncio.run(parents(update, context))

    assert message.messages == ["Parents:\nGrace — 08012345678 — active"]
