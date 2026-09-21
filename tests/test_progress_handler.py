import asyncio
from types import SimpleNamespace

from handlers.progress_create import (
    MEMBERSHIP_ID,
    TEACHING_CONTENT_ID,
    PROGRESS_DATE,
    DESCRIPTION,
    REMARK,
    STATUS,
    progress,
    progress_membership_id,
    progress_teaching_content_id,
    progress_date,
    progress_description,
    progress_remark,
    progress_status,
    cancel_progress,
)


class FakeMessage:
    def __init__(self, text=""):
        self.text = text
        self.replies = []

    async def reply_text(self, message):
        self.replies.append(message)


def _update(text="", user_id=1):
    return SimpleNamespace(
        message=FakeMessage(text),
        effective_user=SimpleNamespace(id=user_id),
    )


class FakeContext:
    def __init__(self, resolver=None, services=None):
        self.user_data = {}
        self.application = SimpleNamespace(
            bot_data={
                "get_administration_context": resolver,
                "services": services,
            }
        )


class AdminContext:
    tenant_id = "tenant-cmos"
    user_id = 7


class FakeProgressService:
    def __init__(self):
        self.recorded = []

    def record(self, value):
        self.recorded.append(value)
        return value


class FakeServices:
    def __init__(self):
        self.progress_service = FakeProgressService()

    def progress(self, tenant_id, user_id=None):
        assert tenant_id == "tenant-cmos"
        assert user_id == 7
        return self.progress_service


def resolver(update, context):
    return AdminContext()


def test_progress_starts_conversation():
    update = _update()
    context = FakeContext(resolver=resolver)

    state = asyncio.run(progress(update, context))

    assert state == MEMBERSHIP_ID
    assert update.message.replies == ["Enter the membership ID:"]


def test_progress_ids_accept_positive_integers():
    context = FakeContext(resolver=resolver)

    membership = asyncio.run(progress_membership_id(_update("11"), context))
    content = asyncio.run(progress_teaching_content_id(_update("22"), context))

    assert membership == TEACHING_CONTENT_ID
    assert content == PROGRESS_DATE
    assert context.user_data["progress_membership_id"] == 11
    assert context.user_data["progress_teaching_content_id"] == 22


def test_progress_rejects_non_integer_membership_id():
    update = _update("not-an-id")
    context = FakeContext(resolver=resolver)

    state = asyncio.run(progress_membership_id(update, context))

    assert state == MEMBERSHIP_ID
    assert "must be a number" in update.message.replies[0]


def test_progress_rejects_non_positive_content_id():
    update = _update("0")
    context = FakeContext(resolver=resolver)

    state = asyncio.run(progress_teaching_content_id(update, context))

    assert state == TEACHING_CONTENT_ID
    assert "greater than zero" in update.message.replies[0]


def test_progress_date_requires_iso_date():
    update = _update("19-09-2026")
    context = FakeContext(resolver=resolver)

    state = asyncio.run(progress_date(update, context))

    assert state == PROGRESS_DATE


def test_progress_description_requires_value():
    update = _update(" ")
    context = FakeContext(resolver=resolver)

    state = asyncio.run(progress_description(update, context))

    assert state == DESCRIPTION


def test_progress_remark_dash_becomes_none():
    update = _update("-")
    context = FakeContext(resolver=resolver)

    state = asyncio.run(progress_remark(update, context))

    assert state == STATUS
    assert context.user_data["progress_remark"] is None


def test_progress_status_records_explicit_progress():
    update = _update("active")
    services = FakeServices()
    context = FakeContext(resolver=resolver, services=services)

    context.user_data.update({
        "progress_membership_id": 11,
        "progress_teaching_content_id": 22,
        "progress_date": "2026-09-19",
        "progress_description": "Observed continued participation and development",
        "progress_remark": "Good progress",
    })

    state = asyncio.run(progress_status(update, context))

    assert state == -1

    recorded = services.progress_service.recorded[0]
    assert recorded.tenant_id == "tenant-cmos"
    assert recorded.membership_id == 11
    assert recorded.teaching_content_id == 22
    assert recorded.progress_date == "2026-09-19"
    assert recorded.description == "Observed continued participation and development"
    assert recorded.remark == "Good progress"
    assert recorded.status == "active"
    assert context.user_data == {}


def test_progress_status_rejects_invalid_status():
    update = _update("pending")
    context = FakeContext(resolver=resolver)

    state = asyncio.run(progress_status(update, context))

    assert state == STATUS


def test_missing_administration_context_denies_start():
    update = _update()
    context = FakeContext(
        resolver=lambda update, context: None
    )

    state = asyncio.run(progress(update, context))

    assert state == -1
    assert "Access denied" in update.message.replies[0]


def test_cancel_progress_clears_session():
    update = _update()
    context = FakeContext(resolver=resolver)

    context.user_data.update({
        "progress_membership_id": 11,
        "progress_teaching_content_id": 22,
        "progress_date": "2026-09-19",
        "progress_description": "Observed progress",
        "progress_remark": None,
        "progress_status": "active",
    })

    state = asyncio.run(cancel_progress(update, context))

    assert state == -1
    assert context.user_data == {}
    assert update.message.replies == ["Progress recording cancelled."]
