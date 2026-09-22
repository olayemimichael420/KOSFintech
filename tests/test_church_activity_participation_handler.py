import asyncio
from types import SimpleNamespace

from handlers.church_activity_participation_create import (
    CHURCH_ACTIVITY_ID,
    MEMBERSHIP_ID,
    cancel_church_activity_participation,
    church_activity_participation,
    church_activity_participation_activity_id,
    church_activity_participation_membership_id,
)


class FakeMessage:
    def __init__(self, text=None):
        self.text = text
        self.replies = []

    async def reply_text(self, text):
        self.replies.append(text)


class FakeUpdate:
    def __init__(self, text=None):
        self.message = FakeMessage(text)


class FakeContext:
    def __init__(self, resolver=None, services=None):
        self.user_data = {}
        self.application = SimpleNamespace(
            bot_data={
                "get_administration_context": resolver,
                "services": services,
            }
        )


def administration_context():
    return SimpleNamespace(
        tenant_id="tenant-a",
        user_id=77,
    )


def test_start_requires_administration_context():
    update = FakeUpdate()
    context = FakeContext(
        resolver=lambda update, context: None,
    )

    result = asyncio.run(
        church_activity_participation(update, context)
    )

    assert result == -1
    assert update.message.replies == [
        "Access denied: unable to resolve an authorized administration context."
    ]


def test_start_prompts_for_church_activity_id():
    update = FakeUpdate()
    context = FakeContext(
        resolver=lambda update, context: administration_context(),
    )

    result = asyncio.run(
        church_activity_participation(update, context)
    )

    assert result == CHURCH_ACTIVITY_ID
    assert update.message.replies == [
        "Enter the church activity ID for this participation:"
    ]


def test_invalid_church_activity_id_rejected():
    update = FakeUpdate("abc")
    context = FakeContext()

    result = asyncio.run(
        church_activity_participation_activity_id(update, context)
    )

    assert result == CHURCH_ACTIVITY_ID
    assert update.message.replies == [
        "Invalid church activity ID. Enter an integer:"
    ]


def test_non_positive_church_activity_id_rejected():
    update = FakeUpdate("0")
    context = FakeContext()

    result = asyncio.run(
        church_activity_participation_activity_id(update, context)
    )

    assert result == CHURCH_ACTIVITY_ID
    assert update.message.replies == [
        "Church activity ID must be a positive integer. Enter the ID:"
    ]


def test_valid_church_activity_id_stored():
    update = FakeUpdate("101")
    context = FakeContext()

    result = asyncio.run(
        church_activity_participation_activity_id(update, context)
    )

    assert result == MEMBERSHIP_ID
    assert (
        context.user_data["church_activity_participation_activity_id"]
        == 101
    )
    assert update.message.replies == [
        "Enter the membership ID to record as participating in this church activity:"
    ]


def test_invalid_membership_id_rejected():
    update = FakeUpdate("abc")
    context = FakeContext()
    context.user_data[
        "church_activity_participation_activity_id"
    ] = 101

    result = asyncio.run(
        church_activity_participation_membership_id(update, context)
    )

    assert result == MEMBERSHIP_ID
    assert update.message.replies == [
        "Invalid membership ID. Enter an integer:"
    ]


def test_non_positive_membership_id_rejected():
    update = FakeUpdate("0")
    context = FakeContext()
    context.user_data[
        "church_activity_participation_activity_id"
    ] = 101

    result = asyncio.run(
        church_activity_participation_membership_id(update, context)
    )

    assert result == MEMBERSHIP_ID
    assert update.message.replies == [
        "Membership ID must be a positive integer. Enter the ID:"
    ]


class FakeParticipationService:
    def __init__(self):
        self.created = []

    def create(self, participation):
        self.created.append(participation)
        return participation


class FakeServices:
    def __init__(self):
        self.participation_service = FakeParticipationService()

    def church_activity_participation(self, tenant_id, user_id=None):
        assert tenant_id == "tenant-a"
        assert user_id == 77
        return self.participation_service


def test_authorized_context_creates_participation():
    update = FakeUpdate("201")
    services = FakeServices()
    context = FakeContext(
        resolver=lambda update, context: administration_context(),
        services=services,
    )
    context.user_data[
        "church_activity_participation_activity_id"
    ] = 101

    result = asyncio.run(
        church_activity_participation_membership_id(update, context)
    )

    assert result == -1

    record = services.participation_service.created[0]
    assert record.tenant_id == "tenant-a"
    assert record.church_activity_id == 101
    assert record.membership_id == 201
    assert context.user_data == {}
    assert update.message.replies == [
        "Church activity participation recorded: activity 101 — member 201"
    ]


def test_missing_administration_context_at_final_step_denies_and_clears():
    update = FakeUpdate("201")
    context = FakeContext(
        resolver=lambda update, context: None,
        services=FakeServices(),
    )
    context.user_data[
        "church_activity_participation_activity_id"
    ] = 101

    result = asyncio.run(
        church_activity_participation_membership_id(update, context)
    )

    assert result == -1
    assert context.user_data == {}
    assert update.message.replies == [
        "Access denied: unable to resolve an authorized administration context."
    ]


def test_missing_activity_state_clears_and_ends():
    update = FakeUpdate("201")
    context = FakeContext(
        resolver=lambda update, context: administration_context(),
        services=FakeServices(),
    )

    result = asyncio.run(
        church_activity_participation_membership_id(update, context)
    )

    assert result == -1
    assert context.user_data == {}
    assert update.message.replies == [
        "Church activity participation session expired. "
        "Please use /church_activity_participation again."
    ]


def test_cancel_clears_state():
    update = FakeUpdate()
    context = FakeContext()
    context.user_data[
        "church_activity_participation_activity_id"
    ] = 101
    context.user_data[
        "church_activity_participation_membership_id"
    ] = 201

    result = asyncio.run(
        cancel_church_activity_participation(update, context)
    )

    assert result == -1
    assert context.user_data == {}
    assert update.message.replies == [
        "Church activity participation cancelled."
    ]
