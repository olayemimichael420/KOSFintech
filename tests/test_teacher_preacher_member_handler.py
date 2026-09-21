import asyncio
from types import SimpleNamespace

from handlers.teacher_preacher_member_create import (
    MEMBERSHIP_ID,
    TEACHER_PREACHER_ID,
    cancel_teacher_preacher_member,
    teacher_preacher_member,
    teacher_preacher_member_membership_id,
    teacher_preacher_member_teacher_preacher_id,
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

    result = asyncio.run(teacher_preacher_member(update, context))

    assert result == -1
    assert update.message.replies == [
        "Access denied: unable to resolve an authorized administration context."
    ]


def test_start_prompts_for_teacher_preacher_id():
    update = FakeUpdate()
    context = FakeContext(
        resolver=lambda update, context: administration_context()
    )

    result = asyncio.run(teacher_preacher_member(update, context))

    assert result == TEACHER_PREACHER_ID
    assert update.message.replies == [
        "Enter the Teacher/Preacher capacity ID for this member relationship:"
    ]


def test_invalid_teacher_preacher_id_rejected():
    update = FakeUpdate("abc")
    context = FakeContext()

    result = asyncio.run(
        teacher_preacher_member_teacher_preacher_id(update, context)
    )

    assert result == TEACHER_PREACHER_ID
    assert update.message.replies == [
        "Invalid Teacher/Preacher capacity ID. Enter an integer:"
    ]


def test_non_positive_teacher_preacher_id_rejected():
    update = FakeUpdate("0")
    context = FakeContext()

    result = asyncio.run(
        teacher_preacher_member_teacher_preacher_id(update, context)
    )

    assert result == TEACHER_PREACHER_ID
    assert update.message.replies == [
        "Teacher/Preacher capacity ID must be a positive integer. Enter the ID:"
    ]


def test_valid_teacher_preacher_id_stored():
    update = FakeUpdate("101")
    context = FakeContext()

    result = asyncio.run(
        teacher_preacher_member_teacher_preacher_id(update, context)
    )

    assert result == MEMBERSHIP_ID
    assert (
        context.user_data["teacher_preacher_member_teacher_preacher_id"]
        == 101
    )
    assert update.message.replies == [
        "Enter the membership ID for this Teacher/Preacher-member relationship:"
    ]


def test_invalid_membership_id_rejected():
    update = FakeUpdate("abc")
    context = FakeContext()
    context.user_data["teacher_preacher_member_teacher_preacher_id"] = 101

    result = asyncio.run(
        teacher_preacher_member_membership_id(update, context)
    )

    assert result == MEMBERSHIP_ID
    assert update.message.replies == [
        "Invalid membership ID. Enter an integer:"
    ]


def test_non_positive_membership_id_rejected():
    update = FakeUpdate("0")
    context = FakeContext()
    context.user_data["teacher_preacher_member_teacher_preacher_id"] = 101

    result = asyncio.run(
        teacher_preacher_member_membership_id(update, context)
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

    def teacher_preacher_member(self, tenant_id, user_id=None):
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
    context.user_data["teacher_preacher_member_teacher_preacher_id"] = 101

    result = asyncio.run(
        teacher_preacher_member_membership_id(update, context)
    )

    assert result == -1
    record = services.member_service.created[0]
    assert record.tenant_id == "tenant-a"
    assert record.teacher_preacher_id == 101
    assert record.membership_id == 201
    assert context.user_data == {}
    assert update.message.replies == [
        "Teacher/Preacher-member relationship created: "
        "Teacher/Preacher 101 — member 201"
    ]


def test_missing_administration_context_at_final_step_denies_and_clears():
    update = FakeUpdate("201")
    context = FakeContext(
        resolver=lambda update, context: None,
        services=FakeServices(),
    )
    context.user_data["teacher_preacher_member_teacher_preacher_id"] = 101

    result = asyncio.run(
        teacher_preacher_member_membership_id(update, context)
    )

    assert result == -1
    assert context.user_data == {}
    assert update.message.replies == [
        "Access denied: unable to resolve an authorized administration context."
    ]


def test_missing_teacher_preacher_state_clears_and_ends():
    update = FakeUpdate("201")
    context = FakeContext(
        resolver=lambda update, context: administration_context(),
        services=FakeServices(),
    )

    result = asyncio.run(
        teacher_preacher_member_membership_id(update, context)
    )

    assert result == -1
    assert context.user_data == {}
    assert update.message.replies == [
        "Teacher/Preacher-member relationship session expired. "
        "Please use /teacher_preacher_member again."
    ]


def test_cancel_clears_state():
    update = FakeUpdate()
    context = FakeContext()
    context.user_data["teacher_preacher_member_teacher_preacher_id"] = 101
    context.user_data["teacher_preacher_member_membership_id"] = 201

    result = asyncio.run(cancel_teacher_preacher_member(update, context))

    assert result == -1
    assert context.user_data == {}
    assert update.message.replies == [
        "Teacher/Preacher-member relationship cancelled."
    ]
