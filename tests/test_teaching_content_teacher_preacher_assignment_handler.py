import pytest
from unittest.mock import AsyncMock, MagicMock

from handlers.teaching_content_teacher_preacher_assignment_create import (
    TEACHING_CONTENT_ID,
    TEACHER_PREACHER_ID,
    STATUS,
    teaching_content_teacher_preacher_assignment,
    teaching_content_assignment_content_id,
    teaching_content_assignment_teacher_preacher_id,
    teaching_content_assignment_status,
    cancel_teaching_content_teacher_preacher_assignment,
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
    administration_context = MagicMock()
    administration_context.tenant_id = tenant_id
    administration_context.user_id = user_id

    context.application.bot_data[
        "get_administration_context"
    ] = MagicMock(return_value=administration_context)

    return administration_context


@pytest.mark.asyncio
async def test_assignment_starts_conversation():
    context = make_context()
    set_admin_context(context)
    update = make_update()

    result = await teaching_content_teacher_preacher_assignment(
        update,
        context,
    )

    assert result == TEACHING_CONTENT_ID
    update.message.reply_text.assert_awaited_once_with(
        "Enter the teaching content ID for this assignment:"
    )


@pytest.mark.asyncio
async def test_assignment_rejects_invalid_content_id():
    context = make_context()
    update = make_update("abc")

    result = await teaching_content_assignment_content_id(
        update,
        context,
    )

    assert result == TEACHING_CONTENT_ID


@pytest.mark.asyncio
async def test_assignment_rejects_non_positive_content_id():
    context = make_context()
    update = make_update("0")

    result = await teaching_content_assignment_content_id(
        update,
        context,
    )

    assert result == TEACHING_CONTENT_ID


@pytest.mark.asyncio
async def test_assignment_accepts_content_id():
    context = make_context()
    update = make_update("7")

    result = await teaching_content_assignment_content_id(
        update,
        context,
    )

    assert result == TEACHER_PREACHER_ID
    assert context.user_data[
        "teaching_content_assignment_content_id"
    ] == 7


@pytest.mark.asyncio
async def test_assignment_rejects_invalid_teacher_preacher_id():
    context = make_context()
    update = make_update("abc")

    result = await teaching_content_assignment_teacher_preacher_id(
        update,
        context,
    )

    assert result == TEACHER_PREACHER_ID


@pytest.mark.asyncio
async def test_assignment_rejects_non_positive_teacher_preacher_id():
    context = make_context()
    update = make_update("0")

    result = await teaching_content_assignment_teacher_preacher_id(
        update,
        context,
    )

    assert result == TEACHER_PREACHER_ID


@pytest.mark.asyncio
async def test_assignment_accepts_teacher_preacher_id():
    context = make_context()
    update = make_update("11")

    result = await teaching_content_assignment_teacher_preacher_id(
        update,
        context,
    )

    assert result == STATUS
    assert context.user_data[
        "teaching_content_assignment_teacher_preacher_id"
    ] == 11


@pytest.mark.asyncio
async def test_assignment_rejects_invalid_status():
    context = make_context()
    context.user_data.update(
        teaching_content_assignment_content_id=7,
        teaching_content_assignment_teacher_preacher_id=11,
    )
    update = make_update("draft")

    result = await teaching_content_assignment_status(
        update,
        context,
    )

    assert result == STATUS


@pytest.mark.asyncio
async def test_assignment_creates_record():
    context = make_context()
    administration_context = set_admin_context(context)

    service = MagicMock()
    record = MagicMock()
    record.teaching_content_id = 7
    record.teacher_preacher_id = 11
    record.status = "active"
    service.create.return_value = record

    context.application.bot_data["services"] = MagicMock()
    context.application.bot_data[
        "services"
    ].teaching_content_teacher_preacher_assignment.return_value = service

    context.user_data.update(
        teaching_content_assignment_content_id=7,
        teaching_content_assignment_teacher_preacher_id=11,
    )

    update = make_update("active")

    result = await teaching_content_assignment_status(
        update,
        context,
    )

    assert result == -1

    service.create.assert_called_once()
    assignment = service.create.call_args.args[0]

    assert assignment.tenant_id == administration_context.tenant_id
    assert assignment.teaching_content_id == 7
    assert assignment.teacher_preacher_id == 11
    assert assignment.status == "active"
    assert context.user_data == {}


@pytest.mark.asyncio
async def test_cancel_assignment_clears_context():
    context = make_context()
    context.user_data.update(
        teaching_content_assignment_content_id=7,
        teaching_content_assignment_teacher_preacher_id=11,
    )

    update = make_update()

    result = await cancel_teaching_content_teacher_preacher_assignment(
        update,
        context,
    )

    assert result == -1
    assert context.user_data == {}
