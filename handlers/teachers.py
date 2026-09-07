"""Telegram teacher handlers."""

from telegram import Update
from telegram.ext import ContextTypes


async def teachers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List teachers for the authorized administration context."""
    resolver = context.application.bot_data["get_administration_context"]
    administration_context = resolver(update, context)
    if administration_context is None:
        await update.message.reply_text("Access denied: unable to resolve an authorized administration context.")
        return

    services = context.application.bot_data["services"]
    teacher_service = services.teacher(
        administration_context.tenant_id,
        user_id=administration_context.user_id,
    )

    try:
        records = teacher_service.list()
    except PermissionError:
        await update.message.reply_text("Access denied: teacher.read permission is required.")
        return

    if not records:
        await update.message.reply_text("No teachers found.")
        return

    lines = [f"{teacher.name} — {teacher.subject} — {teacher.status}" for teacher in records]
    await update.message.reply_text("Teachers:\n" + "\n".join(lines))
