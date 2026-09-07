from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from handlers.attendance_today import attendance_today


def make_context(administration_context):
    services = Mock()
    services.attendance.return_value = Mock()

    application = SimpleNamespace(
        bot_data={
            "get_administration_context": Mock(
                return_value=administration_context
            ),
            "services": services,
        }
    )

    return SimpleNamespace(application=application), services


@pytest.mark.asyncio
async def test_attendance_today_denies_when_context_cannot_be_resolved():
    update = SimpleNamespace(
        message=SimpleNamespace(reply_text=AsyncMock())
    )

    context = SimpleNamespace(
        application=SimpleNamespace(
            bot_data={
                "get_administration_context": Mock(return_value=None),
            }
        )
    )

    await attendance_today(update, context)

    update.message.reply_text.assert_awaited_once_with(
        "Access denied: unable to resolve an authorized administration context."
    )


@pytest.mark.asyncio
async def test_attendance_today_denies_without_read_permission():
    administration_context = SimpleNamespace(
        tenant_id="tenant-1",
        user_id=10,
    )

    context, services = make_context(administration_context)
    services.attendance.return_value.list_by_date.side_effect = PermissionError(
        "missing permission: attendance.read"
    )

    update = SimpleNamespace(
        message=SimpleNamespace(reply_text=AsyncMock())
    )

    await attendance_today(update, context)

    update.message.reply_text.assert_awaited_once_with(
        "Access denied: attendance.read permission is required."
    )


@pytest.mark.asyncio
async def test_attendance_today_reports_empty_result():
    administration_context = SimpleNamespace(
        tenant_id="tenant-1",
        user_id=10,
    )

    context, services = make_context(administration_context)
    services.attendance.return_value.list_by_date.return_value = []

    update = SimpleNamespace(
        message=SimpleNamespace(reply_text=AsyncMock())
    )

    with patch(
        "handlers.attendance_today.date"
    ) as mocked_date:
        mocked_date.today.return_value = date(2026, 9, 6)

        await attendance_today(update, context)

    services.attendance.assert_called_once_with(
        "tenant-1",
        user_id=10,
    )
    services.attendance.return_value.list_by_date.assert_called_once_with(
        "2026-09-06"
    )

    update.message.reply_text.assert_awaited_once_with(
        "No attendance records found for today."
    )


@pytest.mark.asyncio
async def test_attendance_today_lists_records():
    administration_context = SimpleNamespace(
        tenant_id="tenant-1",
        user_id=10,
    )

    context, services = make_context(administration_context)

    services.attendance.return_value.list_by_date.return_value = [
        SimpleNamespace(
            student_id=101,
            status="present",
            remark=None,
        ),
        SimpleNamespace(
            student_id=102,
            status="late",
            remark="Arrived after assembly",
        ),
    ]

    update = SimpleNamespace(
        message=SimpleNamespace(reply_text=AsyncMock())
    )

    with patch(
        "handlers.attendance_today.date"
    ) as mocked_date:
        mocked_date.today.return_value = date(2026, 9, 6)

        await attendance_today(update, context)

    services.attendance.assert_called_once_with(
        "tenant-1",
        user_id=10,
    )
    services.attendance.return_value.list_by_date.assert_called_once_with(
        "2026-09-06"
    )

    update.message.reply_text.assert_awaited_once_with(
        "Today's attendance:\n"
        "Student 101 — present\n"
        "Student 102 — late — Arrived after assembly"
    )
