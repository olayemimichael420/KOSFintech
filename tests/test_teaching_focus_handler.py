import pytest
from unittest.mock import AsyncMock, MagicMock

from handlers.teaching_focus_create import (
    teaching_focus,
    teaching_focus_series_id,
    teaching_focus_name,
    teaching_focus_start_date,
    teaching_focus_end_date,
    teaching_focus_status,
    cancel_teaching_focus,
    TEACHING_SERIES_ID,
    NAME,
    START_DATE,
    END_DATE,
    STATUS,
)
from models.teaching_focus import TeachingFocus


def make_context():
    context = MagicMock()
    context.user_data = {}
    context.application.bot_data = {}
    return context


def make_update(text=""):
    update = MagicMock()
    update.message.text = text
    update.message.reply_text = AsyncMock()
    return update


def install_resolver(context, administration_context):
    context.application.bot_data["get_administration_context"] = (
        lambda update, context: administration_context
    )


@pytest.mark.asyncio
async def test_teaching_focus_starts_conversation():
    update = make_update()
    context = make_context()
    install_resolver(
        context,
        MagicMock(tenant_id="tenant-cmos", user_id="admin-1"),
    )

    result = await teaching_focus(update, context)

    assert result == TEACHING_SERIES_ID
    update.message.reply_text.assert_awaited_once_with(
        "Enter the teaching series ID for this focus:"
    )


@pytest.mark.asyncio
async def test_teaching_focus_rejects_non_integer_series_id():
    update = make_update("abc")
    context = make_context()

    result = await teaching_focus_series_id(update, context)

    assert result == TEACHING_SERIES_ID
    update.message.reply_text.assert_awaited_once_with(
        "Invalid teaching series ID. Enter an integer:"
    )


@pytest.mark.asyncio
async def test_teaching_focus_rejects_non_positive_series_id():
    update = make_update("0")
    context = make_context()

    result = await teaching_focus_series_id(update, context)

    assert result == TEACHING_SERIES_ID
    update.message.reply_text.assert_awaited_once_with(
        "Teaching series ID must be a positive integer. Enter the ID:"
    )


@pytest.mark.asyncio
async def test_teaching_focus_stores_series_id():
    update = make_update("12")
    context = make_context()

    result = await teaching_focus_series_id(update, context)

    assert result == NAME
    assert context.user_data["teaching_focus_series_id"] == 12


@pytest.mark.asyncio
async def test_teaching_focus_rejects_blank_name():
    update = make_update("   ")
    context = make_context()

    result = await teaching_focus_name(update, context)

    assert result == NAME
    update.message.reply_text.assert_awaited_once_with(
        "Teaching focus name cannot be blank. Enter the teaching focus name:"
    )


@pytest.mark.asyncio
async def test_teaching_focus_stores_name():
    update = make_update("Faith and Action")
    context = make_context()

    result = await teaching_focus_name(update, context)

    assert result == START_DATE
    assert context.user_data["teaching_focus_name"] == "Faith and Action"


@pytest.mark.asyncio
async def test_teaching_focus_rejects_invalid_start_date():
    update = make_update("2026-99-99")
    context = make_context()

    result = await teaching_focus_start_date(update, context)

    assert result == START_DATE
    update.message.reply_text.assert_awaited_once_with(
        "Invalid date. Use YYYY-MM-DD:"
    )


@pytest.mark.asyncio
async def test_teaching_focus_stores_valid_start_date():
    update = make_update("2026-09-20")
    context = make_context()

    result = await teaching_focus_start_date(update, context)

    assert result == END_DATE
    assert context.user_data["teaching_focus_start_date"] == "2026-09-20"


@pytest.mark.asyncio
async def test_teaching_focus_rejects_invalid_end_date():
    update = make_update("not-a-date")
    context = make_context()

    result = await teaching_focus_end_date(update, context)

    assert result == END_DATE
    update.message.reply_text.assert_awaited_once_with(
        "Invalid date. Use YYYY-MM-DD:"
    )


@pytest.mark.asyncio
async def test_teaching_focus_moves_to_status_after_valid_end_date():
    update = make_update("2026-09-25")
    context = make_context()
    context.user_data["teaching_focus_series_id"] = 7
    context.user_data["teaching_focus_name"] = "Faith and Action"
    context.user_data["teaching_focus_start_date"] = "2026-09-20"

    result = await teaching_focus_end_date(update, context)

    assert result == STATUS
    assert context.user_data["teaching_focus_end_date"] == "2026-09-25"


@pytest.mark.asyncio
async def test_teaching_focus_rejects_invalid_status():
    update = make_update("draft")
    context = make_context()

    result = await teaching_focus_status(update, context)

    assert result == STATUS
    update.message.reply_text.assert_awaited_once_with(
        "Invalid status. Enter active or inactive:"
    )


@pytest.mark.asyncio
async def test_teaching_focus_creates_explicit_record():
    update = make_update("active")
    context = make_context()
    context.user_data.update(
        {
            "teaching_focus_series_id": 7,
            "teaching_focus_name": "Faith and Action",
            "teaching_focus_start_date": "2026-09-20",
            "teaching_focus_end_date": "2026-09-25",
        }
    )

    administration_context = MagicMock(
        tenant_id="tenant-cmos",
        user_id="admin-1",
    )
    install_resolver(context, administration_context)

    focus_service = MagicMock()
    recorded = TeachingFocus(
        id=21,
        tenant_id="tenant-cmos",
        teaching_series_id=7,
        name="Faith and Action",
        start_date="2026-09-20",
        end_date="2026-09-25",
        status="active",
    )
    focus_service.create.return_value = recorded
    context.application.bot_data["services"] = MagicMock(
        teaching_focus=MagicMock(return_value=focus_service)
    )

    result = await teaching_focus_status(update, context)

    assert result == -1
    focus_service.create.assert_called_once_with(
        TeachingFocus(
            id=None,
            tenant_id="tenant-cmos",
            teaching_series_id=7,
            name="Faith and Action",
            start_date="2026-09-20",
            end_date="2026-09-25",
            status="active",
        )
    )
    assert context.user_data == {}


@pytest.mark.asyncio
async def test_teaching_focus_reports_service_value_error():
    update = make_update("active")
    context = make_context()
    context.user_data.update(
        {
            "teaching_focus_series_id": 7,
            "teaching_focus_name": "Faith and Action",
            "teaching_focus_start_date": "2026-09-20",
            "teaching_focus_end_date": "2026-09-25",
        }
    )

    administration_context = MagicMock(
        tenant_id="tenant-cmos",
        user_id="admin-1",
    )
    install_resolver(context, administration_context)

    focus_service = MagicMock()
    focus_service.create.side_effect = ValueError("teaching series not found")
    context.application.bot_data["services"] = MagicMock(
        teaching_focus=MagicMock(return_value=focus_service)
    )

    result = await teaching_focus_status(update, context)

    assert result == -1
    update.message.reply_text.assert_awaited_once_with(
        "Teaching focus could not be created: teaching series not found"
    )
    assert context.user_data == {}


@pytest.mark.asyncio
async def test_cancel_teaching_focus_clears_context():
    update = make_update()
    context = make_context()
    context.user_data.update(
        {
            "teaching_focus_series_id": 7,
            "teaching_focus_name": "Faith and Action",
            "teaching_focus_start_date": "2026-09-20",
            "teaching_focus_end_date": "2026-09-25",
        }
    )

    result = await cancel_teaching_focus(update, context)

    assert result == -1
    assert context.user_data == {}
    update.message.reply_text.assert_awaited_once_with(
        "Teaching focus creation cancelled."
    )
