import pytest

from models.telegram_channel_binding import TelegramChannelBinding
from repositories.telegram_channel_binding_repository import (
    TelegramChannelBindingRepository,
)


def _create_administration(connection, tenant_id="tenant-a"):
    cursor = connection.execute(
        """
        INSERT INTO administrations (
            tenant_id,
            name,
            administration_type
        )
        VALUES (?, ?, ?)
        """,
        (tenant_id, "Test Administration", "school"),
    )
    connection.commit()
    return cursor.lastrowid


def test_create_and_get_binding(db_connection):
    administration_id = _create_administration(db_connection)
    repository = TelegramChannelBindingRepository(db_connection)

    binding = TelegramChannelBinding(
        id=None,
        provider="telegram",
        chat_id="-100123456789",
        tenant_id="tenant-a",
        administration_id=administration_id,
        binding_type="supergroup",
    )

    created = repository.create(binding)

    assert created is binding
    assert created.id is not None

    loaded = repository.get(created.id)

    assert loaded is not None
    assert loaded.chat_id == "-100123456789"
    assert loaded.tenant_id == "tenant-a"
    assert loaded.administration_id == administration_id
    assert loaded.binding_type == "supergroup"
    assert loaded.status == "active"


def test_get_by_provider_chat_returns_binding(db_connection):
    administration_id = _create_administration(db_connection)
    repository = TelegramChannelBindingRepository(db_connection)

    repository.create(
        TelegramChannelBinding(
            id=None,
            provider="telegram",
            chat_id="-100987654321",
            tenant_id="tenant-a",
            administration_id=administration_id,
            binding_type="channel",
        )
    )

    loaded = repository.get_by_provider_chat(
        "telegram",
        "-100987654321",
    )

    assert loaded is not None
    assert loaded.administration_id == administration_id


def test_duplicate_provider_chat_is_rejected(db_connection):
    administration_id = _create_administration(db_connection)
    repository = TelegramChannelBindingRepository(db_connection)

    binding = TelegramChannelBinding(
        id=None,
        provider="telegram",
        chat_id="-100111222333",
        tenant_id="tenant-a",
        administration_id=administration_id,
        binding_type="group",
    )

    repository.create(binding)

    with pytest.raises(Exception):
        repository.create(
            TelegramChannelBinding(
                id=None,
                provider="telegram",
                chat_id="-100111222333",
                tenant_id="tenant-a",
                administration_id=administration_id,
                binding_type="group",
            )
        )
