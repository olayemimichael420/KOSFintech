import asyncio
from types import SimpleNamespace

from telegram.ext import ConversationHandler

from handlers.assessment_create import (
    ASSESSMENT_DATE,
    DESCRIPTION,
    NAME,
    STATUS,
    TEACHING_CONTENT_ID,
    assessment,
    assessment_date,
    assessment_description,
    assessment_name,
    assessment_status,
    assessment_teaching_content_id,
    cancel_assessment,
)


class FakeMessage:
    def __init__(self, text):
        self.text = text
        self.replies = []

    async def reply_text(self, text):
        self.replies.append(text)


class FakeContext:
    def __init__(self, admin_context=None):
        self.user_data = {}
        self.application = SimpleNamespace(
            bot_data={
                "get_administration_context": (
                    lambda user_id: admin_context
                ),
            }
        )


class FakeUpdate:
    def __init__(self, text="", user_id=7):
        self.message = FakeMessage(text)
        self.effective_user = SimpleNamespace(id=user_id)


class FakeAssessmentService:
    def __init__(self):
        self.created = []

    def record(self, assessment):
        self.created.append(assessment)
        return SimpleNamespace(id=42)


class FakeServices:
    def __init__(self, service):
        self.service = service

    def assessment(self, tenant_id, user_id=None):
        return self.service


def _admin_context():
    return SimpleNamespace(
        tenant_id="tenant-cmos",
        user_id=7,
    )


def test_assessment_denies_without_administration_context():
    update = FakeUpdate()
    context = FakeContext(admin_context=None)

    result = asyncio.run(assessment(update, context))

    assert result == ConversationHandler.END
    assert update.message.replies == [
        "Administration context required."
    ]


def test_assessment_prompts_for_teaching_content_id():
    update = FakeUpdate()
    context = FakeContext(admin_context=_admin_context())

    result = asyncio.run(assessment(update, context))

    assert result == TEACHING_CONTENT_ID
    assert update.message.replies == [
        "Enter the teaching content ID:"
    ]


def test_assessment_rejects_non_positive_content_id():
    update = FakeUpdate("0")
    context = FakeContext(admin_context=_admin_context())

    result = asyncio.run(
        assessment_teaching_content_id(update, context)
    )

    assert result == TEACHING_CONTENT_ID
    assert update.message.replies == [
        "Teaching content ID must be a positive integer."
    ]


def test_assessment_accepts_content_id():
    update = FakeUpdate("30")
    context = FakeContext(admin_context=_admin_context())

    result = asyncio.run(
        assessment_teaching_content_id(update, context)
    )

    assert result == NAME
    assert context.user_data["assessment_teaching_content_id"] == 30


def test_assessment_requires_name():
    update = FakeUpdate("   ")
    context = FakeContext(admin_context=_admin_context())

    result = asyncio.run(assessment_name(update, context))

    assert result == NAME
    assert update.message.replies == [
        "Assessment name is required."
    ]


def test_assessment_accepts_name():
    update = FakeUpdate("Understanding Review")
    context = FakeContext(admin_context=_admin_context())

    result = asyncio.run(assessment_name(update, context))

    assert result == ASSESSMENT_DATE
    assert context.user_data["assessment_name"] == "Understanding Review"


def test_assessment_requires_valid_date():
    update = FakeUpdate("19-09-2026")
    context = FakeContext(admin_context=_admin_context())

    result = asyncio.run(assessment_date(update, context))

    assert result == ASSESSMENT_DATE
    assert update.message.replies == [
        "Assessment date must use YYYY-MM-DD format."
    ]


def test_assessment_accepts_valid_date():
    update = FakeUpdate("2026-09-19")
    context = FakeContext(admin_context=_admin_context())

    result = asyncio.run(assessment_date(update, context))

    assert result == DESCRIPTION
    assert context.user_data["assessment_date"] == "2026-09-19"


def test_assessment_accepts_description():
    update = FakeUpdate("Observable assessment activity.")
    context = FakeContext(admin_context=_admin_context())

    result = asyncio.run(
        assessment_description(update, context)
    )

    assert result == STATUS
    assert (
        context.user_data["assessment_description"]
        == "Observable assessment activity."
    )


def test_assessment_dash_description_becomes_none():
    update = FakeUpdate("-")
    context = FakeContext(admin_context=_admin_context())

    result = asyncio.run(
        assessment_description(update, context)
    )

    assert result == STATUS
    assert context.user_data["assessment_description"] is None


def test_assessment_rejects_invalid_status():
    update = FakeUpdate("pending")
    context = FakeContext(admin_context=_admin_context())

    result = asyncio.run(assessment_status(update, context))

    assert result == STATUS
    assert update.message.replies == [
        "Status must be active or inactive."
    ]


def test_assessment_records_explicit_fields():
    service = FakeAssessmentService()
    context = FakeContext(admin_context=_admin_context())
    context.application.bot_data["services"] = FakeServices(service)

    context.user_data.update(
        {
            "assessment_teaching_content_id": 30,
            "assessment_name": "Understanding Review",
            "assessment_date": "2026-09-19",
            "assessment_description": "Observable assessment activity.",
        }
    )

    update = FakeUpdate("active")

    result = asyncio.run(assessment_status(update, context))

    assert result == ConversationHandler.END
    assert len(service.created) == 1

    assessment = service.created[0]

    assert assessment.id is None
    assert assessment.tenant_id == "tenant-cmos"
    assert assessment.teaching_content_id == 30
    assert assessment.name == "Understanding Review"
    assert assessment.description == "Observable assessment activity."
    assert assessment.assessment_date == "2026-09-19"
    assert assessment.status == "active"

    assert update.message.replies == [
        "Assessment recorded: 42"
    ]
    assert context.user_data == {}


def test_assessment_cancel_clears_session():
    context = FakeContext(admin_context=_admin_context())
    context.user_data.update(
        {
            "assessment_teaching_content_id": 30,
            "assessment_name": "Review",
            "assessment_date": "2026-09-19",
            "assessment_description": "Description",
        }
    )

    update = FakeUpdate()

    result = asyncio.run(cancel_assessment(update, context))

    assert result == ConversationHandler.END
    assert context.user_data == {}
    assert update.message.replies == [
        "Assessment creation cancelled."
    ]
