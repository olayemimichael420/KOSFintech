from bot import get_telegram_binding


class FakeChat:
    def __init__(self, chat_id):
        self.id = chat_id


class FakeUpdate:
    def __init__(self, chat_id=None):
        self.effective_chat = (
            FakeChat(chat_id) if chat_id is not None else None
        )


class FakeBindingService:
    def __init__(self, binding=None):
        self.binding = binding
        self.calls = []

    def resolve_chat(self, chat_id):
        self.calls.append(chat_id)
        return self.binding


class FakeServices:
    def __init__(self, telegram_channel_binding):
        self.telegram_channel_binding = telegram_channel_binding


class FakeApplication:
    def __init__(self, binding_service):
        self.bot_data = {
            "services": FakeServices(binding_service)
        }


class FakeContext:
    def __init__(self, services):
        self.application = FakeApplication(services)


def test_get_telegram_binding_resolves_current_chat():
    binding = object()
    service = FakeBindingService(binding)
    context = FakeContext(service)

    result = get_telegram_binding(
        FakeUpdate("-100123456789"),
        context,
    )

    assert result is binding
    assert service.calls == ["-100123456789"]


def test_get_telegram_binding_returns_none_without_chat():
    service = FakeBindingService()
    context = FakeContext(service)

    assert get_telegram_binding(FakeUpdate(), context) is None
