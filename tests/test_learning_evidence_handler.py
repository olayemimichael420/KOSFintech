import asyncio
from types import SimpleNamespace

from telegram.ext import ConversationHandler

from handlers.learning_evidence_create import (
    DESCRIPTION,
    EVIDENCE_DATE,
    MEMBERSHIP_ID,
    REMARK,
    TEACHING_CONTENT_ID,
    cancel_learning_evidence,
    learning_evidence,
    learning_evidence_date,
    learning_evidence_description,
    learning_evidence_membership_id,
    learning_evidence_remark,
    learning_evidence_teaching_content_id,
)


def run(coro):
    return asyncio.run(coro)


def make_context(resolver, services=None):
    application = SimpleNamespace(
        bot_data={
            "get_administration_context": resolver,
            "services": services,
        }
    )
    return SimpleNamespace(application=application, user_data={})


def make_update(text=None):
    message = SimpleNamespace(text=text, replies=[])

    async def reply_text(value):
        message.replies.append(value)

    message.reply_text = reply_text
    return SimpleNamespace(message=message)


def test_learning_evidence_denies_without_administration_context():
    context = make_context(lambda update, context: None)
    update = make_update()

    result = run(learning_evidence(update, context))

    assert result == ConversationHandler.END
    assert "Access denied" in update.message.replies[0]


def test_learning_evidence_membership_id_accepts_positive_id():
    context = make_context(lambda update, context: None)
    update = make_update("21")

    result = run(learning_evidence_membership_id(update, context))

    assert result == TEACHING_CONTENT_ID
    assert context.user_data["learning_evidence_membership_id"] == 21


def test_learning_evidence_content_id_accepts_positive_id():
    context = make_context(lambda update, context: None)
    update = make_update("42")

    result = run(learning_evidence_teaching_content_id(update, context))

    assert result == EVIDENCE_DATE
    assert context.user_data["learning_evidence_teaching_content_id"] == 42


def test_learning_evidence_date_accepts_valid_date():
    context = make_context(lambda update, context: None)
    update = make_update("2026-09-20")

    result = run(learning_evidence_date(update, context))

    assert result == DESCRIPTION
    assert context.user_data["learning_evidence_date"] == "2026-09-20"


def test_learning_evidence_description_requires_text():
    context = make_context(lambda update, context: None)
    update = make_update("")

    result = run(learning_evidence_description(update, context))

    assert result == DESCRIPTION
    assert "Description is required" in update.message.replies[0]


def test_learning_evidence_description_accepts_text():
    context = make_context(lambda update, context: None)
    update = make_update("Member demonstrated understanding.")

    result = run(learning_evidence_description(update, context))

    assert result == REMARK
    assert context.user_data["learning_evidence_description"] == (
        "Member demonstrated understanding."
    )


def test_learning_evidence_remark_records_with_authorized_context():
    administration_context = SimpleNamespace(
        tenant_id="tenant-cmos",
        user_id=42,
    )

    class FakeEvidenceService:
        def __init__(self):
            self.recorded = None

        def record(self, record):
            self.recorded = record
            return record

    service = FakeEvidenceService()

    class FakeServices:
        def learning_evidence(self, tenant_id, user_id=None):
            assert tenant_id == "tenant-cmos"
            assert user_id == 42
            return service

    context = make_context(
        lambda update, context: administration_context,
        FakeServices(),
    )
    context.user_data.update(
        {
            "learning_evidence_membership_id": 21,
            "learning_evidence_teaching_content_id": 42,
            "learning_evidence_date": "2026-09-20",
            "learning_evidence_description": "Member demonstrated understanding.",
        }
    )
    update = make_update("Observed during teaching.")

    result = run(learning_evidence_remark(update, context))

    assert result == ConversationHandler.END
    assert service.recorded is not None
    assert service.recorded.tenant_id == "tenant-cmos"
    assert service.recorded.membership_id == 21
    assert service.recorded.teaching_content_id == 42
    assert service.recorded.evidence_date == "2026-09-20"
    assert service.recorded.description == "Member demonstrated understanding."
    assert service.recorded.remark == "Observed during teaching."
    assert "Learning evidence recorded" in update.message.replies[0]
    assert context.user_data == {}


def test_learning_evidence_remark_accepts_blank_marker():
    administration_context = SimpleNamespace(
        tenant_id="tenant-cmos",
        user_id=42,
    )

    class FakeEvidenceService:
        def __init__(self):
            self.recorded = None

        def record(self, record):
            self.recorded = record
            return record

    service = FakeEvidenceService()

    class FakeServices:
        def learning_evidence(self, tenant_id, user_id=None):
            return service

    context = make_context(
        lambda update, context: administration_context,
        FakeServices(),
    )
    context.user_data.update(
        {
            "learning_evidence_membership_id": 21,
            "learning_evidence_teaching_content_id": 42,
            "learning_evidence_date": "2026-09-20",
            "learning_evidence_description": "Observable evidence.",
        }
    )
    update = make_update("-")

    result = run(learning_evidence_remark(update, context))

    assert result == ConversationHandler.END
    assert service.recorded.remark is None


def test_cancel_learning_evidence_clears_session():
    context = make_context(lambda update, context: None)
    context.user_data.update(
        {
            "learning_evidence_membership_id": 21,
            "learning_evidence_teaching_content_id": 42,
            "learning_evidence_date": "2026-09-20",
            "learning_evidence_description": "Observable evidence.",
        }
    )
    update = make_update()

    result = run(cancel_learning_evidence(update, context))

    assert result == ConversationHandler.END
    assert context.user_data == {}
    assert "cancelled" in update.message.replies[0]
