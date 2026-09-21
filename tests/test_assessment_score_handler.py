import asyncio
from types import SimpleNamespace

from handlers.assessment_score_create import (
    ASSESSMENT_ID,
    MEMBERSHIP_ID,
    SCORE,
    SCORED_DATE,
    REMARK,
    assessment_score,
    assessment_score_assessment_id,
    assessment_score_membership_id,
    assessment_score_value,
    assessment_score_date,
    assessment_score_remark,
    cancel_assessment_score,
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


class FakeScoreService:
    def __init__(self):
        self.recorded = []

    def record(self, value):
        self.recorded.append(value)
        return SimpleNamespace(
            id=31,
            membership_id=value.membership_id,
            assessment_id=value.assessment_id,
            score=value.score,
        )


class FakeServices:
    def __init__(self):
        self.score_service = FakeScoreService()

    def assessment_score(self, tenant_id, user_id=None):
        assert tenant_id == "tenant-cmos"
        assert user_id == 7
        return self.score_service


def resolver(update, context):
    return AdminContext()


def test_assessment_score_starts_conversation():
    update = _update()
    context = FakeContext(resolver=resolver)

    result = asyncio.run(assessment_score(update, context))

    assert result == ASSESSMENT_ID
    assert update.message.replies == ["Enter the assessment ID:"]


def test_assessment_id_validates_positive_integer():
    update = _update("17")
    context = FakeContext(resolver=resolver)

    result = asyncio.run(
        assessment_score_assessment_id(update, context)
    )

    assert result == MEMBERSHIP_ID
    assert context.user_data["assessment_score_assessment_id"] == 17


def test_membership_id_validates_positive_integer():
    update = _update("23")
    context = FakeContext(resolver=resolver)
    context.user_data["assessment_score_assessment_id"] = 17

    result = asyncio.run(
        assessment_score_membership_id(update, context)
    )

    assert result == SCORE
    assert context.user_data["assessment_score_membership_id"] == 23


def test_score_accepts_integer_without_inventing_range():
    update = _update("-5")
    context = FakeContext(resolver=resolver)

    result = asyncio.run(
        assessment_score_value(update, context)
    )

    assert result == SCORED_DATE
    assert context.user_data["assessment_score_score"] == -5


def test_scored_date_validates_iso_date():
    update = _update("2026-09-21")
    context = FakeContext(resolver=resolver)

    result = asyncio.run(
        assessment_score_date(update, context)
    )

    assert result == REMARK
    assert context.user_data["assessment_score_date"] == "2026-09-21"


def test_remark_records_assessment_score():
    update = _update("Observed written assessment")
    services = FakeServices()
    context = FakeContext(
        resolver=resolver,
        services=services,
    )
    context.user_data.update(
        {
            "assessment_score_assessment_id": 17,
            "assessment_score_membership_id": 23,
            "assessment_score_score": 82,
            "assessment_score_date": "2026-09-21",
        }
    )

    result = asyncio.run(
        assessment_score_remark(update, context)
    )

    assert result == -1
    assert len(services.score_service.recorded) == 1

    recorded = services.score_service.recorded[0]
    assert recorded.tenant_id == "tenant-cmos"
    assert recorded.assessment_id == 17
    assert recorded.membership_id == 23
    assert recorded.score == 82
    assert recorded.scored_date == "2026-09-21"
    assert recorded.remark == "Observed written assessment"


def test_remark_dash_records_none():
    update = _update("-")
    services = FakeServices()
    context = FakeContext(
        resolver=resolver,
        services=services,
    )
    context.user_data.update(
        {
            "assessment_score_assessment_id": 17,
            "assessment_score_membership_id": 23,
            "assessment_score_score": 82,
            "assessment_score_date": "2026-09-21",
        }
    )

    asyncio.run(
        assessment_score_remark(update, context)
    )

    assert services.score_service.recorded[0].remark is None


def test_missing_administration_context_denies_start():
    update = _update()
    context = FakeContext(resolver=lambda update, context: None)

    result = asyncio.run(assessment_score(update, context))

    assert result == -1
    assert "Access denied" in update.message.replies[0]


def test_cancel_clears_session():
    update = _update()
    context = FakeContext(resolver=resolver)
    context.user_data.update(
        {
            "assessment_score_assessment_id": 17,
            "assessment_score_membership_id": 23,
            "assessment_score_score": 82,
            "assessment_score_date": "2026-09-21",
            "assessment_score_remark": "x",
        }
    )

    result = asyncio.run(
        cancel_assessment_score(update, context)
    )

    assert result == -1
    assert context.user_data == {}
    assert update.message.replies == [
        "Assessment score recording cancelled."
    ]
