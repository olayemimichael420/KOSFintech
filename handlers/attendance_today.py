"""Telegram attendance read handlers."""

from datetime import date

from telegram import Update
from telegram.ext import ContextTypes


async def attendance_today(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """List attendance records for the current date."""
    resolver = context.application.bot_data["get_administration_context"]
    administration_context = resolver(update, context)

    if administration_context is None:
        await update.message.reply_text(
            "Access denied: unable to resolve an authorized administration context."
        )
        return

    services = context.application.bot_data["services"]
    attendance_service = services.attendance(
        administration_context.tenant_id,
        user_id=administration_context.user_id,
    )

    try:
        records = attendance_service.list_by_date(date.today().isoformat())
    except PermissionError:
        await update.message.reply_text(
            "Access denied: attendance.read permission is required."
        )
        return

    if not records:
        await update.message.reply_text("No attendance records found for today.")
        return

    lines = [
        f"Student {record.student_id} — {record.status}"
        + (f" — {record.remark}" if record.remark else "")
        for record in records
    ]

    await update.message.reply_text(
        "Today's attendance:\n" + "\n".join(lines)
    )
