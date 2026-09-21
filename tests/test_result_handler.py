import asyncio
from types import SimpleNamespace

from handlers.result_create import (
    ASSESSMENT_ID,
    MEMBERSHIP_ID,
    GRADE_ID,
    RESULT,
    RESULT_DATE,
    REMARK,
    STATUS,
    result,
    result_assessment_id,
    result_membership_id,
    result_grade_id,
    result_value,
    result_date,
    result_remark,
    result_status,
    cancel_result,
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


class FakeResultService:
    def __init__(self):
        self.recorded = []

    def record(self, value):
        self.recorded.append(value)
        return value


class FakeServices:
    def __init__(self):
        self.result_service = FakeResultService()

    def result(self, tenant_id, user_id=None):
        assert tenant_id == "tenant-cmos"
        assert user_id == 7
        return self.result_service


def resolver(update, context):
    return AdminContext()


def test_result_starts_conversation():
    update = _update()
    context = FakeContext(resolver=resolver)

    result_state = asyncio.run(result(update, context))

    assert result_state == ASSESSMENT_ID
    assert update.message.replies == ["Enter the assessment ID:"]


def test_result_ids_accept_integer_values():
    context = FakeContext(resolver=resolver)

    assessment = asyncio.run(
        result_assessment_id(_update("11"), context)
    )
    membership = asyncio.run(
        result_membership_id(_update("22"), context)
    )
    grade = asyncio.run(
        result_grade_id(_update("33"), context)
    )

    assert assessment == MEMBERSHIP_ID
    assert membership == GRADE_ID
    assert grade == RESULT
    assert context.user_data["result_assessment_id"] == 11
    assert context.user_data["result_membership_id"] == 22
    assert context.user_data["result_grade_id"] == 33


def test_result_rejects_non_integer_assessment_id():
    update = _update("not-an-id")
    context = FakeContext(resolver=resolver)

    result_state = asyncio.run(
        result_assessment_id(update, context)
    )

    assert result_state == ASSESSMENT_ID
    assert "must be an integer" in update.message.replies[0]


def test_result_value_rejects_blank():
    update = _update(" ")
    context = FakeContext(resolver=resolver)

    result_state = asyncio.run(
        result_value(update, context)
    )

    assert result_state == RESULT


def test_result_date_requires_iso_date():
    update = _update("19-09-2026")
    context = FakeContext(resolver=resolver)

    result_state = asyncio.run(
        result_date(update, context)
    )

    assert result_state == RESULT_DATE


def test_result_remark_dash_becomes_none():
    update = _update("-")
    context = FakeContext(resolver=resolver)

    result_state = asyncio.run(
        result_remark(update, context)
    )

    assert result_state == STATUS
    assert context.user_data["result_remark"] is None


def test_result_status_records_explicit_result():
    update = _update("active")
    services = FakeServices()
    context = FakeContext(resolver=resolver, services=services)

    context.user_data.update({
        "result_assessment_id": 11,
        "result_membership_id": 22,
        "result_grade_id": 33,
        "result_value": "Completed the assessment requirements",
        "result_date": "2026-09-19",
        "result_remark": "Good progress",
    })

    result_state = asyncio.run(
        result_status(update, context)
    )

    assert result_state == -1

    recorded = services.result_service.recorded[0]

    assert recorded.tenant_id == "tenant-cmos"
    assert recorded.assessment_id == 11
    assert recorded.membership_id == 22
    assert recorded.grade_id == 33
    assert recorded.result == "Completed the assessment requirements"
    assert recorded.result_date == "2026-09-19"
    assert recorded.remark == "Good progress"
    assert recorded.status == "active"
    assert context.user_data == {}


def test_result_status_rejects_invalid_status():
    update = _update("pending")
    context = FakeContext(resolver=resolver)

    context.user_data.update({
        "result_assessment_id": 11,
        "result_membership_id": 22,
        "result_grade_id": 33,
        "result_value": "Completed",
        "result_date": "2026-09-19",
        "result_remark": None,
    })

    result_state = asyncio.run(
        result_status(update, context)
    )

    assert result_state == STATUS


def test_missing_administration_context_denies_start():
    update = _update()
    context = FakeContext(
        resolver=lambda update, context: None
    )

    result_state = asyncio.run(
        result(update, context)
    )

    assert result_state == -1
    assert "Access denied" in update.message.replies[0]


def test_cancel_result_clears_session():
    update = _update()
    context = FakeContext(resolver=resolver)

    context.user_data.update({
        "result_assessment_id": 11,
        "result_membership_id": 22,
        "result_grade_id": 33,
        "result_value": "Completed",
        "result_date": "2026-09-19",
        "result_remark": None,
        "result_status": "active",
    })

    result_state = asyncio.run(
        cancel_result(update, context)
    )

    assert result_state == -1
    assert context.user_data == {}
    assert update.message.replies == ["Result recording cancelled."]
