from models.telegram_channel_binding import TelegramChannelBinding
from services.telegram_channel_binding_service import (
    TelegramChannelBindingService,
)


class FakeRepository:
    def __init__(self, binding=None):
        self.binding = binding
        self.calls = []

    def get_by_provider_chat(self, provider, chat_id):
        self.calls.append((provider, chat_id))
        return self.binding


def test_resolve_active_binding():
    binding = TelegramChannelBinding(
        id=1,
        provider="telegram",
        chat_id="-100123456789",
        tenant_id="tenant-a",
        administration_id=42,
        binding_type="supergroup",
        status="active",
    )

    repository = FakeRepository(binding)
    service = TelegramChannelBindingService(repository)

    result = service.resolve_chat("-100123456789")

    assert result == binding
    assert repository.calls == [
        ("telegram", "-100123456789")
    ]


def test_inactive_binding_does_not_resolve():
    binding = TelegramChannelBinding(
        id=1,
        provider="telegram",
        chat_id="-100123456789",
        tenant_id="tenant-a",
        administration_id=42,
        binding_type="supergroup",
        status="inactive",
    )

    service = TelegramChannelBindingService(FakeRepository(binding))

    assert service.resolve_chat("-100123456789") is None


def test_unknown_chat_does_not_resolve():
    service = TelegramChannelBindingService(FakeRepository())

    assert service.resolve_chat("-100999999999") is None
