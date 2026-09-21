import asyncio
from types import SimpleNamespace

from handlers.teaching_session_member_create import (
    MEMBERSHIP_ID,
    TEACHING_SESSION_ID,
    cancel_teaching_session_member,
    teaching_session_member,
    teaching_session_member_membership_id,
    teaching_session_member_session_id,
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
    context = FakeContext(resolver=lambda update, context: None)

    result = asyncio.run(teaching_session_member(update, context))

    assert result == -1
    assert update.message.replies == [
        "Access denied: unable to resolve an authorized administration context."
    ]


def test_start_prompts_for_teaching_session_id():
    update = FakeUpdate()
    context = FakeContext(
        resolver=lambda update, context: administration_context()
    )

    result = asyncio.run(teaching_session_member(update, context))

    assert result == TEACHING_SESSION_ID
    assert update.message.replies == [
        "Enter the teaching session ID for this member enrollment:"
    ]


def test_invalid_teaching_session_id_rejected():
    update = FakeUpdate("abc")
    context = FakeContext()

    result = asyncio.run(
        teaching_session_member_session_id(update, context)
    )

    assert result == TEACHING_SESSION_ID
    assert update.message.replies == [
        "Invalid teaching session ID. Enter an integer:"
    ]


def test_non_positive_teaching_session_id_rejected():
    update = FakeUpdate("0")
    context = FakeContext()

    result = asyncio.run(
        teaching_session_member_session_id(update, context)
    )

    assert result == TEACHING_SESSION_ID
    assert update.message.replies == [
        "Teaching session ID must be a positive integer. Enter the ID:"
    ]


def test_valid_teaching_session_id_stored():
    update = FakeUpdate("101")
    context = FakeContext()

    result = asyncio.run(
        teaching_session_member_session_id(update, context)
    )

    assert result == MEMBERSHIP_ID
    assert context.user_data["teaching_session_member_session_id"] == 101
    assert update.message.replies == [
        "Enter the membership ID to enroll in this teaching session:"
    ]


def test_invalid_membership_id_rejected():
    update = FakeUpdate("abc")
    context = FakeContext()
    context.user_data["teaching_session_member_session_id"] = 101

    result = asyncio.run(
        teaching_session_member_membership_id(update, context)
    )

    assert result == MEMBERSHIP_ID
    assert update.message.replies == [
        "Invalid membership ID. Enter an integer:"
    ]


def test_non_positive_membership_id_rejected():
    update = FakeUpdate("0")
    context = FakeContext()
    context.user_data["teaching_session_member_session_id"] = 101

    result = asyncio.run(
        teaching_session_member_membership_id(update, context)
    )

    assert result == MEMBERSHIP_ID
    assert update.message.replies == [
        "Membership ID must be a positive integer. Enter the ID:"
    ]


class FakeMemberService:
    def __init__(self):
        self.created = []

    def create(self, link):
        self.created.append(link)
        return link


class FakeServices:
    def __init__(self):
        self.member_service = FakeMemberService()

    def teaching_session_member(self, tenant_id, user_id=None):
        assert tenant_id == "tenant-a"
        assert user_id == 77
        return self.member_service


def test_authorized_context_creates_member_link():
    update = FakeUpdate("201")
    services = FakeServices()
    context = FakeContext(
        resolver=lambda update, context: administration_context(),
        services=services,
    )
    context.user_data["teaching_session_member_session_id"] = 101

    result = asyncio.run(
        teaching_session_member_membership_id(update, context)
    )

    assert result == -1
    record = services.member_service.created[0]
    assert record.tenant_id == "tenant-a"
    assert record.teaching_session_id == 101
    assert record.membership_id == 201
    assert context.user_data == {}
    assert update.message.replies == [
        "Teaching session member enrollment created: "
        "session 101 — member 201"
    ]


def test_missing_administration_context_at_final_step_denies_and_clears():
    update = FakeUpdate("201")
    context = FakeContext(
        resolver=lambda update, context: None,
        services=FakeServices(),
    )
    context.user_data["teaching_session_member_session_id"] = 101

    result = asyncio.run(
        teaching_session_member_membership_id(update, context)
    )

    assert result == -1
    assert context.user_data == {}
    assert update.message.replies == [
        "Access denied: unable to resolve an authorized administration context."
    ]


def test_missing_session_state_clears_and_ends():
    update = FakeUpdate("201")
    context = FakeContext(
        resolver=lambda update, context: administration_context(),
        services=FakeServices(),
    )

    result = asyncio.run(
        teaching_session_member_membership_id(update, context)
    )

    assert result == -1
    assert context.user_data == {}
    assert update.message.replies == [
        "Teaching session member enrollment session expired. "
        "Please use /teaching_session_member again."
    ]


def test_cancel_clears_state():
    update = FakeUpdate()
    context = FakeContext()
    context.user_data["teaching_session_member_session_id"] = 101
    context.user_data["teaching_session_member_membership_id"] = 201

    result = asyncio.run(cancel_teaching_session_member(update, context))

    assert result == -1
    assert context.user_data == {}
    assert update.message.replies == [
        "Teaching session member enrollment cancelled."
    ]
