from models.telegram_channel_binding import TelegramChannelBinding


def test_binding_model_holds_explicit_telegram_administration_mapping():
    binding = TelegramChannelBinding(
        id=None,
        provider="telegram",
        chat_id="-100123456789",
        tenant_id="tenant-001",
        administration_id=42,
        binding_type="supergroup",
        status="active",
    )

    assert binding.provider == "telegram"
    assert binding.chat_id == "-100123456789"
    assert binding.tenant_id == "tenant-001"
    assert binding.administration_id == 42
    assert binding.binding_type == "supergroup"
    assert binding.status == "active"
