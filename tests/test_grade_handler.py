import asyncio
from types import SimpleNamespace

from handlers.grade_create import (
    NAME,
    DESCRIPTION,
    MINIMUM_SCORE,
    MAXIMUM_SCORE,
    STATUS,
    grade,
    grade_name,
    grade_description,
    grade_minimum_score,
    grade_maximum_score,
    grade_status,
    cancel_grade,
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


class FakeGradeService:
    def __init__(self):
        self.recorded = []

    def record(self, value):
        self.recorded.append(value)
        return value


class FakeServices:
    def __init__(self):
        self.grade_service = FakeGradeService()

    def grade(self, tenant_id, user_id=None):
        assert tenant_id == "tenant-cmos"
        assert user_id == 7
        return self.grade_service


def resolver(update, context):
    return AdminContext()


def test_grade_starts_conversation():
    update = _update()
    context = FakeContext(resolver=resolver)

    result = asyncio.run(grade(update, context))

    assert result == NAME
    assert update.message.replies == ["Enter the grade name:"]


def test_grade_name_rejects_blank():
    update = _update(" ")
    context = FakeContext(resolver=resolver)

    result = asyncio.run(grade_name(update, context))

    assert result == NAME


def test_grade_name_accepts_name():
    update = _update("A")
    context = FakeContext(resolver=resolver)

    result = asyncio.run(grade_name(update, context))

    assert result == DESCRIPTION
    assert context.user_data["grade_name"] == "A"


def test_grade_description_dash_becomes_none():
    update = _update("-")
    context = FakeContext(resolver=resolver)
    context.user_data["grade_name"] = "A"

    result = asyncio.run(grade_description(update, context))

    assert result == MINIMUM_SCORE
    assert context.user_data["grade_description"] is None


def test_grade_scores_accept_integer_values():
    context = FakeContext(resolver=resolver)

    minimum = asyncio.run(grade_minimum_score(_update("80"), context))
    maximum = asyncio.run(grade_maximum_score(_update("100"), context))

    assert minimum == MAXIMUM_SCORE
    assert maximum == STATUS
    assert context.user_data["grade_minimum_score"] == 80
    assert context.user_data["grade_maximum_score"] == 100


def test_grade_status_records_explicit_grade():
    update = _update("active")
    services = FakeServices()
    context = FakeContext(resolver=resolver, services=services)
    context.user_data.update(
        {
            "grade_name": "A",
            "grade_description": "Excellent",
            "grade_minimum_score": 80,
            "grade_maximum_score": 100,
        }
    )

    result = asyncio.run(grade_status(update, context))

    assert result == -1
    recorded = services.grade_service.recorded[0]
    assert recorded.tenant_id == "tenant-cmos"
    assert recorded.name == "A"
    assert recorded.description == "Excellent"
    assert recorded.minimum_score == 80
    assert recorded.maximum_score == 100
    assert recorded.status == "active"
    assert context.user_data == {}


def test_grade_status_rejects_invalid_status():
    update = _update("pending")
    context = FakeContext(resolver=resolver)
    context.user_data.update(
        {
            "grade_name": "A",
            "grade_description": None,
            "grade_minimum_score": 80,
            "grade_maximum_score": 100,
        }
    )

    result = asyncio.run(grade_status(update, context))

    assert result == STATUS


def test_missing_administration_context_denies_start():
    update = _update()
    context = FakeContext(
        resolver=lambda update, context: None
    )

    result = asyncio.run(grade(update, context))

    assert result == -1
    assert "Access denied" in update.message.replies[0]


def test_cancel_grade_clears_session():
    update = _update()
    context = FakeContext(resolver=resolver)
    context.user_data.update(
        {
            "grade_name": "A",
            "grade_description": "x",
            "grade_minimum_score": 80,
            "grade_maximum_score": 100,
            "grade_status": "active",
        }
    )

    result = asyncio.run(cancel_grade(update, context))

    assert result == -1
    assert context.user_data == {}
    assert update.message.replies == ["Grade recording cancelled."]
