from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from handlers.teaching_session_create import (
    END_DATE,
    NAME,
    START_DATE,
    cancel_teaching_session,
    teaching_session,
    teaching_session_end_date,
    teaching_session_name,
    teaching_session_start_date,
)
from models.teaching_session import TeachingSession


def _update(text=None):
    update = Mock()
    update.message = Mock()
    update.message.text = text
    update.message.reply_text = AsyncMock()
    return update


def _context():
    context = SimpleNamespace()
    context.user_data = {}
    context.application = Mock()
    context.application.bot_data = {}
    return context


def _administration_context(tenant_id="tenant-cmos", user_id="user-1"):
    return SimpleNamespace(
        tenant_id=tenant_id,
        user_id=user_id,
    )


@pytest.mark.asyncio
async def test_teaching_session_start_requires_administration_context():
    update = _update()
    context = _context()
    context.application.bot_data["get_administration_context"] = Mock(
        return_value=None
    )

    state = await teaching_session(update, context)

    assert state == -1
    update.message.reply_text.assert_awaited_once_with(
        "Access denied: unable to resolve an authorized administration context."
    )


@pytest.mark.asyncio
async def test_teaching_session_start_prompts_for_name():
    update = _update()
    context = _context()
    context.application.bot_data["get_administration_context"] = Mock(
        return_value=_administration_context()
    )

    state = await teaching_session(update, context)

    assert state == NAME
    update.message.reply_text.assert_awaited_once_with(
        "Enter the teaching session name:"
    )


@pytest.mark.asyncio
async def test_teaching_session_name_rejects_blank():
    update = _update("   ")
    context = _context()

    state = await teaching_session_name(update, context)

    assert state == NAME
    update.message.reply_text.assert_awaited_once_with(
        "Teaching session name cannot be blank. Enter the teaching session name:"
    )


@pytest.mark.asyncio
async def test_teaching_session_name_stores_value():
    update = _update("Foundations of Faith")
    context = _context()

    state = await teaching_session_name(update, context)

    assert state == START_DATE
    assert context.user_data["teaching_session_name"] == "Foundations of Faith"


@pytest.mark.asyncio
async def test_teaching_session_start_date_rejects_invalid_date():
    update = _update("2026-99-99")
    context = _context()

    state = await teaching_session_start_date(update, context)

    assert state == START_DATE
    update.message.reply_text.assert_awaited_once_with(
        "Invalid date. Use YYYY-MM-DD:"
    )


@pytest.mark.asyncio
async def test_teaching_session_start_date_stores_iso_date():
    update = _update("2026-09-21")
    context = _context()

    state = await teaching_session_start_date(update, context)

    assert state == END_DATE
    assert context.user_data["teaching_session_start_date"] == "2026-09-21"


@pytest.mark.asyncio
async def test_teaching_session_end_date_rejects_invalid_date():
    update = _update("not-a-date")
    context = _context()
    context.user_data["teaching_session_name"] = "Faith"
    context.user_data["teaching_session_start_date"] = "2026-09-21"

    state = await teaching_session_end_date(update, context)

    assert state == END_DATE
    update.message.reply_text.assert_awaited_once_with(
        "Invalid date. Use YYYY-MM-DD:"
    )


@pytest.mark.asyncio
async def test_teaching_session_end_date_requires_context_state():
    update = _update("2026-09-21")
    context = _context()

    state = await teaching_session_end_date(update, context)

    assert state == -1
    assert context.user_data == {}
    update.message.reply_text.assert_awaited_once_with(
        "Teaching session creation session expired. "
        "Please use /teaching_session again."
    )


@pytest.mark.asyncio
async def test_teaching_session_end_date_denies_missing_administration_context():
    update = _update("2026-09-21")
    context = _context()
    context.user_data["teaching_session_name"] = "Faith"
    context.user_data["teaching_session_start_date"] = "2026-09-21"
    context.application.bot_data["get_administration_context"] = Mock(
        return_value=None
    )

    state = await teaching_session_end_date(update, context)

    assert state == -1
    assert context.user_data == {}
    update.message.reply_text.assert_awaited_once_with(
        "Access denied: unable to resolve an authorized administration context."
    )


@pytest.mark.asyncio
async def test_teaching_session_end_date_records_session():
    update = _update("2026-09-22")
    context = _context()
    administration_context = _administration_context()
    resolver = Mock(return_value=administration_context)

    service = Mock()
    record = TeachingSession(
        id=17,
        tenant_id="tenant-cmos",
        name="Foundations of Faith",
        start_date="2026-09-21",
        end_date="2026-09-22",
    )
    service.create.return_value = record

    context.application.bot_data["get_administration_context"] = resolver
    context.application.bot_data["services"] = Mock()
    context.application.bot_data["services"].teaching_session.return_value = service
    context.user_data["teaching_session_name"] = "Foundations of Faith"
    context.user_data["teaching_session_start_date"] = "2026-09-21"

    state = await teaching_session_end_date(update, context)

    assert state == -1
    service.create.assert_called_once()
    created = service.create.call_args.args[0]
    assert isinstance(created, TeachingSession)
    assert created.id is None
    assert created.tenant_id == "tenant-cmos"
    assert created.name == "Foundations of Faith"
    assert created.start_date == "2026-09-21"
    assert created.end_date == "2026-09-22"
    assert context.user_data == {}
    update.message.reply_text.assert_awaited_once_with(
        "Teaching session created: Foundations of Faith — "
        "2026-09-21 to 2026-09-22"
    )


@pytest.mark.asyncio
async def test_teaching_session_end_date_handles_permission_error():
    update = _update("2026-09-22")
    context = _context()
    context.user_data["teaching_session_name"] = "Faith"
    context.user_data["teaching_session_start_date"] = "2026-09-21"
    context.application.bot_data["get_administration_context"] = Mock(
        return_value=_administration_context()
    )

    service = Mock()
    service.create.side_effect = PermissionError("missing permission")
    context.application.bot_data["services"] = Mock()
    context.application.bot_data["services"].teaching_session.return_value = service

    state = await teaching_session_end_date(update, context)

    assert state == -1
    assert context.user_data == {}
    update.message.reply_text.assert_awaited_once_with(
        "Access denied: teaching_session.write permission is required."
    )


@pytest.mark.asyncio
async def test_teaching_session_end_date_handles_validation_error():
    update = _update("2026-09-20")
    context = _context()
    context.user_data["teaching_session_name"] = "Faith"
    context.user_data["teaching_session_start_date"] = "2026-09-21"
    context.application.bot_data["get_administration_context"] = Mock(
        return_value=_administration_context()
    )

    service = Mock()
    service.create.side_effect = ValueError(
        "teaching session start date must not be after end date"
    )
    context.application.bot_data["services"] = Mock()
    context.application.bot_data["services"].teaching_session.return_value = service

    state = await teaching_session_end_date(update, context)

    assert state == -1
    assert context.user_data == {}
    update.message.reply_text.assert_awaited_once_with(
        "Teaching session could not be created: "
        "teaching session start date must not be after end date"
    )


@pytest.mark.asyncio
async def test_cancel_teaching_session_clears_state():
    update = _update()
    context = _context()
    context.user_data.update(
        {
            "teaching_session_name": "Faith",
            "teaching_session_start_date": "2026-09-21",
            "teaching_session_end_date": "2026-09-22",
        }
    )

    state = await cancel_teaching_session(update, context)

    assert state == -1
    assert context.user_data == {}
    update.message.reply_text.assert_awaited_once_with(
        "Teaching session creation cancelled."
    )
