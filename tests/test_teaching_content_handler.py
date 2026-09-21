import pytest
from unittest.mock import AsyncMock, MagicMock

from handlers.teaching_content_create import (
    TEACHING_FOCUS_ID,
    NAME,
    DESCRIPTION,
    SEQUENCE,
    STATUS,
    teaching_content,
    teaching_content_focus_id,
    teaching_content_name,
    teaching_content_description,
    teaching_content_sequence,
    teaching_content_status,
    cancel_teaching_content,
)


def make_context():
    context = MagicMock()
    context.user_data = {}
    context.application.bot_data = {}
    return context


def make_update(text=None):
    update = MagicMock()
    update.message.text = text
    update.message.reply_text = AsyncMock()
    return update


def set_admin_context(context, tenant_id="tenant-cmos", user_id=1):
    admin = MagicMock()
    admin.tenant_id = tenant_id
    admin.user_id = user_id
    context.application.bot_data["get_administration_context"] = MagicMock(
        return_value=admin
    )
    return admin


@pytest.mark.asyncio
async def test_teaching_content_starts_conversation():
    context = make_context()
    set_admin_context(context)
    update = make_update()

    result = await teaching_content(update, context)

    assert result == TEACHING_FOCUS_ID
    update.message.reply_text.assert_awaited_once_with(
        "Enter the teaching focus ID for this content:"
    )


@pytest.mark.asyncio
async def test_teaching_content_rejects_invalid_focus_id():
    context = make_context()
    update = make_update("abc")

    result = await teaching_content_focus_id(update, context)

    assert result == TEACHING_FOCUS_ID
    update.message.reply_text.assert_awaited_once_with(
        "Invalid teaching focus ID. Enter an integer:"
    )


@pytest.mark.asyncio
async def test_teaching_content_rejects_non_positive_focus_id():
    context = make_context()
    update = make_update("0")

    result = await teaching_content_focus_id(update, context)

    assert result == TEACHING_FOCUS_ID


@pytest.mark.asyncio
async def test_teaching_content_accepts_focus_id():
    context = make_context()
    update = make_update("7")

    result = await teaching_content_focus_id(update, context)

    assert result == NAME
    assert context.user_data["teaching_content_focus_id"] == 7


@pytest.mark.asyncio
async def test_teaching_content_rejects_blank_name():
    context = make_context()
    update = make_update("   ")

    result = await teaching_content_name(update, context)

    assert result == NAME


@pytest.mark.asyncio
async def test_teaching_content_accepts_name():
    context = make_context()
    update = make_update("Faith Demonstrated")

    result = await teaching_content_name(update, context)

    assert result == DESCRIPTION
    assert context.user_data["teaching_content_name"] == "Faith Demonstrated"


@pytest.mark.asyncio
async def test_teaching_content_accepts_optional_description():
    context = make_context()
    update = make_update("-")

    result = await teaching_content_description(update, context)

    assert result == SEQUENCE
    assert context.user_data["teaching_content_description"] is None


@pytest.mark.asyncio
async def test_teaching_content_rejects_invalid_sequence():
    context = make_context()
    update = make_update("abc")

    result = await teaching_content_sequence(update, context)

    assert result == SEQUENCE


@pytest.mark.asyncio
async def test_teaching_content_accepts_optional_sequence():
    context = make_context()
    update = make_update("-")

    result = await teaching_content_sequence(update, context)

    assert result == STATUS
    assert context.user_data["teaching_content_sequence"] is None


@pytest.mark.asyncio
async def test_teaching_content_rejects_invalid_status():
    context = make_context()
    update = make_update("draft")

    result = await teaching_content_status(update, context)

    assert result == STATUS


@pytest.mark.asyncio
async def test_teaching_content_creates_record():
    context = make_context()
    set_admin_context(context)

    service = MagicMock()
    record = MagicMock()
    record.name = "Faith Demonstrated"
    record.status = "active"
    service.create.return_value = record

    context.application.bot_data["services"] = MagicMock()
    context.application.bot_data["services"].teaching_content.return_value = service

    context.user_data.update(
        teaching_content_focus_id=7,
        teaching_content_name="Faith Demonstrated",
        teaching_content_description="Faith in action",
        teaching_content_sequence=1,
    )

    update = make_update("active")

    result = await teaching_content_status(update, context)

    assert result == -1
    service.create.assert_called_once()

    content = service.create.call_args.args[0]
    assert content.tenant_id == "tenant-cmos"
    assert content.teaching_focus_id == 7
    assert content.name == "Faith Demonstrated"
    assert content.description == "Faith in action"
    assert content.sequence == 1
    assert content.status == "active"
    assert context.user_data == {}


@pytest.mark.asyncio
async def test_cancel_teaching_content_clears_context():
    context = make_context()
    context.user_data["teaching_content_focus_id"] = 7

    update = make_update()

    result = await cancel_teaching_content(update, context)

    assert result == -1
    assert context.user_data == {}
