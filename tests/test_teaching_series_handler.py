import pytest

from handlers.teaching_series_create import (
    END_DATE,
    NAME,
    START_DATE,
    STATUS,
    TEACHING_SESSION_ID,
    cancel_teaching_series,
    teaching_series,
    teaching_series_end_date,
    teaching_series_name,
    teaching_series_session_id,
    teaching_series_start_date,
    teaching_series_status,
)
from models.teaching_series import TeachingSeries


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


class FakeSeriesService:
    def __init__(self, record=None, error=None):
        self.record_value = record
        self.error = error
        self.created = []

    def create(self, series):
        self.created.append(series)
        if self.error:
            raise self.error
        return self.record_value


class FakeServices:
    def __init__(self, series_service):
        self.series_service = series_service

    def teaching_series(self, tenant_id, user_id=None):
        assert tenant_id == "tenant-cmos"
        assert user_id == "user-1"
        return self.series_service


class FakeApplication:
    def __init__(self, bot_data):
        self.bot_data = bot_data


class FakeContext:
    def __init__(self, series_service):
        self.application = FakeApplication(
            {
                "get_administration_context": (
                    lambda update, context: FakeAdministrationContext()
                ),
                "services": FakeServices(series_service),
            }
        )
        self.user_data = {}


@pytest.mark.asyncio
async def test_teaching_series_starts_conversation():
    update = FakeUpdate()
    context = FakeContext(FakeSeriesService())

    result = await teaching_series(update, context)

    assert result == TEACHING_SESSION_ID
    assert update.message.replies == [
        "Enter the teaching session ID for this series:"
    ]


@pytest.mark.asyncio
async def test_invalid_session_id_is_rejected():
    update = FakeUpdate("abc")
    context = FakeContext(FakeSeriesService())

    result = await teaching_series_session_id(update, context)

    assert result == TEACHING_SESSION_ID
    assert "Invalid teaching session ID" in update.message.replies[0]


@pytest.mark.asyncio
async def test_non_positive_session_id_is_rejected():
    update = FakeUpdate("0")
    context = FakeContext(FakeSeriesService())

    result = await teaching_series_session_id(update, context)

    assert result == TEACHING_SESSION_ID
    assert "positive integer" in update.message.replies[0]


@pytest.mark.asyncio
async def test_session_id_is_stored():
    update = FakeUpdate("7")
    context = FakeContext(FakeSeriesService())

    result = await teaching_series_session_id(update, context)

    assert result == NAME
    assert context.user_data["teaching_series_session_id"] == 7


@pytest.mark.asyncio
async def test_blank_name_is_rejected():
    update = FakeUpdate("   ")
    context = FakeContext(FakeSeriesService())

    result = await teaching_series_name(update, context)

    assert result == NAME
    assert "cannot be blank" in update.message.replies[0]


@pytest.mark.asyncio
async def test_invalid_start_date_is_rejected():
    update = FakeUpdate("not-a-date")
    context = FakeContext(FakeSeriesService())

    result = await teaching_series_start_date(update, context)

    assert result == START_DATE
    assert "Invalid date" in update.message.replies[0]


@pytest.mark.asyncio
async def test_invalid_end_date_is_rejected():
    context = FakeContext(FakeSeriesService())
    context.user_data["teaching_series_session_id"] = 1
    context.user_data["teaching_series_name"] = "Faith Foundations"
    context.user_data["teaching_series_start_date"] = "2026-01-01"

    update = FakeUpdate("bad-date")

    result = await teaching_series_end_date(update, context)

    assert result == END_DATE
    assert "Invalid date" in update.message.replies[0]


@pytest.mark.asyncio
async def test_valid_end_date_moves_to_status():
    context = FakeContext(FakeSeriesService())
    context.user_data["teaching_series_session_id"] = 1
    context.user_data["teaching_series_name"] = "Faith Foundations"
    context.user_data["teaching_series_start_date"] = "2026-01-01"

    update = FakeUpdate("2026-01-31")

    result = await teaching_series_end_date(update, context)

    assert result == STATUS
    assert context.user_data["teaching_series_end_date"] == "2026-01-31"


@pytest.mark.asyncio
async def test_invalid_status_is_rejected():
    context = FakeContext(FakeSeriesService())
    context.user_data.update(
        {
            "teaching_series_session_id": 1,
            "teaching_series_name": "Faith Foundations",
            "teaching_series_start_date": "2026-01-01",
            "teaching_series_end_date": "2026-01-31",
        }
    )

    update = FakeUpdate("draft")

    result = await teaching_series_status(update, context)

    assert result == STATUS
    assert "Invalid status" in update.message.replies[0]


@pytest.mark.asyncio
async def test_series_is_created_with_explicit_fields():
    record = TeachingSeries(
        id=9,
        tenant_id="tenant-cmos",
        teaching_session_id=3,
        name="Faith Foundations",
        start_date="2026-01-01",
        end_date="2026-01-31",
        status="active",
    )
    service = FakeSeriesService(record=record)
    context = FakeContext(service)
    context.user_data.update(
        {
            "teaching_series_session_id": 3,
            "teaching_series_name": "Faith Foundations",
            "teaching_series_start_date": "2026-01-01",
            "teaching_series_end_date": "2026-01-31",
        }
    )

    update = FakeUpdate("active")

    result = await teaching_series_status(update, context)

    assert result == -1
    assert len(service.created) == 1
    created = service.created[0]
    assert created.tenant_id == "tenant-cmos"
    assert created.teaching_session_id == 3
    assert created.name == "Faith Foundations"
    assert created.start_date == "2026-01-01"
    assert created.end_date == "2026-01-31"
    assert created.status == "active"


@pytest.mark.asyncio
async def test_service_value_error_is_reported():
    service = FakeSeriesService(
        error=ValueError("teaching session not found")
    )
    context = FakeContext(service)
    context.user_data.update(
        {
            "teaching_series_session_id": 99,
            "teaching_series_name": "Faith Foundations",
            "teaching_series_start_date": "2026-01-01",
            "teaching_series_end_date": "2026-01-31",
        }
    )

    update = FakeUpdate("active")

    result = await teaching_series_status(update, context)

    assert result == -1
    assert "teaching session not found" in update.message.replies[0]


@pytest.mark.asyncio
async def test_cancel_clears_context():
    context = FakeContext(FakeSeriesService())
    context.user_data.update(
        {
            "teaching_series_session_id": 3,
            "teaching_series_name": "Faith Foundations",
            "teaching_series_start_date": "2026-01-01",
            "teaching_series_end_date": "2026-01-31",
        }
    )

    update = FakeUpdate()

    result = await cancel_teaching_series(update, context)

    assert result == -1
    assert context.user_data == {}
    assert update.message.replies == [
        "Teaching series creation cancelled."
    ]
