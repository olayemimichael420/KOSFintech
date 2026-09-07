"""Telegram student handlers."""

from telegram import Update
from telegram.ext import ContextTypes


async def students(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List students for the authorized administration context."""
    resolver = context.application.bot_data["get_administration_context"]
    administration_context = resolver(update, context)
    if administration_context is None:
        await update.message.reply_text("Access denied: unable to resolve an authorized administration context.")
        return

    services = context.application.bot_data["services"]
    student_service = services.student(
        administration_context.tenant_id,
        user_id=administration_context.user_id,
    )

    try:
        records = student_service.list()
    except PermissionError:
        await update.message.reply_text("Access denied: student.read permission is required.")
        return

    if not records:
        await update.message.reply_text("No students found.")
        return

    lines = [f"{student.name} — {student.class_name} — {student.status}" for student in records]
    await update.message.reply_text("Students:\n" + "\n".join(lines))
