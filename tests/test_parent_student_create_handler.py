import sqlite3
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from telegram.ext import ConversationHandler

from handlers.parent_student_create import (
    PARENT_ID,
    STUDENT_ID,
    cancel_linkparentstudent,
    linkparentstudent,
    parent_student_parent_id,
    parent_student_student_id,
)


def make_context(resolver=None, service=None):
    context = MagicMock()
    context.user_data = {}

    context.application.bot_data = {
        "get_administration_context": resolver or MagicMock(),
        "services": MagicMock(),
    }

    if service is not None:
        context.application.bot_data["services"].parent_student.return_value = service

    return context


def make_update(text=None):
    update = MagicMock()
    update.message.text = text
    update.message.reply_text = AsyncMock()
    return update


def make_admin_context():
    return SimpleNamespace(
        tenant_id="tenant-1",
        user_id=42,
    )


@pytest.mark.asyncio
async def test_linkparentstudent_denies_without_administration_context():
    update = make_update()
    context = make_context(resolver=MagicMock(return_value=None))

    result = await linkparentstudent(update, context)

    assert result == ConversationHandler.END
    update.message.reply_text.assert_awaited_once_with(
        "Access denied: unable to resolve an authorized administration context."
    )


@pytest.mark.asyncio
async def test_linkparentstudent_asks_for_parent_id():
    update = make_update()
    context = make_context(
        resolver=MagicMock(return_value=make_admin_context())
    )

    result = await linkparentstudent(update, context)

    assert result == PARENT_ID
    update.message.reply_text.assert_awaited_once_with(
        "Enter the parent ID:"
    )


@pytest.mark.asyncio
async def test_invalid_parent_id_is_rejected():
    update = make_update("abc")
    context = make_context()

    result = await parent_student_parent_id(update, context)

    assert result == PARENT_ID
    update.message.reply_text.assert_awaited_once_with(
        "Parent ID must be a number. Enter the parent ID:"
    )


@pytest.mark.asyncio
async def test_valid_parent_id_moves_to_student_id_and_stores_state():
    update = make_update("12")
    context = make_context()

    result = await parent_student_parent_id(update, context)

    assert result == STUDENT_ID
    assert context.user_data["parent_student_parent_id"] == 12
    update.message.reply_text.assert_awaited_once_with(
        "Enter the student ID:"
    )


@pytest.mark.asyncio
async def test_valid_parent_and_student_create_relationship():
    update = make_update("7")
    resolver = MagicMock(return_value=make_admin_context())

    service = MagicMock()
    service.create.return_value = SimpleNamespace(
        parent_id=12,
        student_id=7,
    )

    context = make_context(
        resolver=resolver,
        service=service,
    )
    context.user_data["parent_student_parent_id"] = 12

    result = await parent_student_student_id(update, context)

    assert result == ConversationHandler.END
    service.create.assert_called_once()

    link = service.create.call_args.args[0]
    assert link.tenant_id == "tenant-1"
    assert link.parent_id == 12
    assert link.student_id == 7
    assert "parent_student_parent_id" not in context.user_data

    update.message.reply_text.assert_awaited_once_with(
        "Parent-student relationship created: parent 12 — student 7"
    )


@pytest.mark.asyncio
async def test_permission_error_is_handled():
    update = make_update("7")
    resolver = MagicMock(return_value=make_admin_context())

    service = MagicMock()
    service.create.side_effect = PermissionError(
        "missing permission: parent_student.write"
    )

    context = make_context(
        resolver=resolver,
        service=service,
    )
    context.user_data["parent_student_parent_id"] = 12

    result = await parent_student_student_id(update, context)

    assert result == ConversationHandler.END
    assert "parent_student_parent_id" not in context.user_data
    update.message.reply_text.assert_awaited_once_with(
        "Access denied: parent_student.write permission is required."
    )


@pytest.mark.asyncio
async def test_integrity_error_is_handled():
    update = make_update("7")
    resolver = MagicMock(return_value=make_admin_context())

    service = MagicMock()
    service.create.side_effect = sqlite3.IntegrityError()

    context = make_context(
        resolver=resolver,
        service=service,
    )
    context.user_data["parent_student_parent_id"] = 12

    result = await parent_student_student_id(update, context)

    assert result == ConversationHandler.END
    assert "parent_student_parent_id" not in context.user_data
    update.message.reply_text.assert_awaited_once_with(
        "Parent-student relationship could not be created "
        "because the record conflicts with existing data."
    )


@pytest.mark.asyncio
async def test_cancel_ends_workflow_and_clears_state():
    update = make_update()
    context = make_context()
    context.user_data["parent_student_parent_id"] = 12

    result = await cancel_linkparentstudent(update, context)

    assert result == ConversationHandler.END
    assert "parent_student_parent_id" not in context.user_data
    update.message.reply_text.assert_awaited_once_with(
        "Parent-student relationship creation cancelled."
    )
