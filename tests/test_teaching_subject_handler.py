from types import SimpleNamespace

import pytest

from handlers.teaching_subject_create import (
    NAME,
    STATUS,
    cancel_teaching_subject,
    teaching_subject,
    teaching_subject_name,
    teaching_subject_status,
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


class FakeAdministrationContext:
    tenant_id = "tenant-cmos"
    user_id = "user-1"


class FakeSubjectService:
    def __init__(self, record=None, error=None):
        self.record_value = record
        self.error = error
        self.created = []

    def create(self, subject):
        self.created.append(subject)
        if self.error:
            raise self.error
        return self.record_value


class FakeServices:
    def __init__(self, subject_service):
        self.subject_service = subject_service

    def teaching_subject(self, tenant_id, user_id=None):
        assert tenant_id == "tenant-cmos"
        assert user_id == "user-1"
        return self.subject_service


class FakeBotData(dict):
    pass


class FakeApplication:
    def __init__(self, bot_data):
        self.bot_data = bot_data


class FakeContext:
    def __init__(self, bot_data):
        self.application = FakeApplication(bot_data)
        self.user_data = {}


def make_context(subject_service):
    bot_data = FakeBotData(
        get_administration_context=lambda update, context: FakeAdministrationContext(),
        services=FakeServices(subject_service),
    )
    return FakeContext(bot_data)


@pytest.mark.asyncio
async def test_teaching_subject_starts_conversation():
    update = FakeUpdate()
    context = make_context(FakeSubjectService())

    result = await teaching_subject(update, context)

    assert result == NAME
    assert update.message.replies == [
        "Enter the teaching subject name:"
    ]


@pytest.mark.asyncio
async def test_teaching_subject_denies_when_context_unavailable():
    update = FakeUpdate()
    context = make_context(FakeSubjectService())
    context.application.bot_data["get_administration_context"] = (
        lambda update, context: None
    )

    result = await teaching_subject(update, context)

    assert result == -1
    assert "Access denied" in update.message.replies[0]


@pytest.mark.asyncio
async def test_blank_name_is_rejected():
    update = FakeUpdate("   ")
    context = make_context(FakeSubjectService())

    result = await teaching_subject_name(update, context)

    assert result == NAME
    assert "cannot be blank" in update.message.replies[0]


@pytest.mark.asyncio
async def test_name_is_stored():
    update = FakeUpdate("Faith")
    context = make_context(FakeSubjectService())

    result = await teaching_subject_name(update, context)

    assert result == STATUS
    assert context.user_data["teaching_subject_name"] == "Faith"


@pytest.mark.asyncio
async def test_invalid_status_is_rejected():
    update = FakeUpdate("draft")
    context = make_context(FakeSubjectService())

    result = await teaching_subject_status(update, context)

    assert result == STATUS
    assert "Invalid status" in update.message.replies[0]


@pytest.mark.asyncio
async def test_subject_is_created_with_explicit_status():
    from models.teaching_subject import TeachingSubject

    record = TeachingSubject(
        id=7,
        tenant_id="tenant-cmos",
        name="Faith",
        status="active",
    )
    service = FakeSubjectService(record=record)
    context = make_context(service)
    context.user_data["teaching_subject_name"] = "Faith"

    update = FakeUpdate("active")

    result = await teaching_subject_status(update, context)

    assert result == -1
    assert len(service.created) == 1
    assert service.created[0].name == "Faith"
    assert service.created[0].tenant_id == "tenant-cmos"
    assert service.created[0].status == "active"
    assert "Teaching subject created: Faith (active)" in update.message.replies[0]


@pytest.mark.asyncio
async def test_permission_error_is_handled():
    service = FakeSubjectService(error=PermissionError("missing permission"))
    context = make_context(service)
    context.user_data["teaching_subject_name"] = "Faith"

    update = FakeUpdate("active")

    result = await teaching_subject_status(update, context)

    assert result == -1
    assert "teaching_subject.write" in update.message.replies[0]


@pytest.mark.asyncio
async def test_value_error_is_handled():
    service = FakeSubjectService(error=ValueError("tenant mismatch"))
    context = make_context(service)
    context.user_data["teaching_subject_name"] = "Faith"

    update = FakeUpdate("active")

    result = await teaching_subject_status(update, context)

    assert result == -1
    assert "tenant mismatch" in update.message.replies[0]


@pytest.mark.asyncio
async def test_missing_name_ends_expired_conversation():
    context = make_context(FakeSubjectService())
    update = FakeUpdate("active")

    result = await teaching_subject_status(update, context)

    assert result == -1
    assert "session expired" in update.message.replies[0]


@pytest.mark.asyncio
async def test_cancel_clears_context():
    context = make_context(FakeSubjectService())
    context.user_data["teaching_subject_name"] = "Faith"
    context.user_data["teaching_subject_status"] = "active"

    update = FakeUpdate()

    result = await cancel_teaching_subject(update, context)

    assert result == -1
    assert context.user_data == {}
    assert update.message.replies == ["Teaching subject creation cancelled."]


@pytest.mark.asyncio
async def test_inactive_subject_is_supported():
    from models.teaching_subject import TeachingSubject

    record = TeachingSubject(
        id=8,
        tenant_id="tenant-cmos",
        name="Old Testament",
        status="inactive",
    )
    service = FakeSubjectService(record=record)
    context = make_context(service)
    context.user_data["teaching_subject_name"] = "Old Testament"

    update = FakeUpdate("inactive")

    result = await teaching_subject_status(update, context)

    assert result == -1
    assert service.created[0].status == "inactive"
    assert "Old Testament (inactive)" in update.message.replies[0]
