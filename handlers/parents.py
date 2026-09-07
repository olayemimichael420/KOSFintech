"""Telegram parent handlers."""

from telegram import Update
from telegram.ext import ContextTypes


async def parents(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List parents for the authorized administration context."""
    resolver = context.application.bot_data["get_administration_context"]
    administration_context = resolver(update, context)
    if administration_context is None:
        await update.message.reply_text("Access denied: unable to resolve an authorized administration context.")
        return

    services = context.application.bot_data["services"]
    parent_service = services.parent(
        administration_context.tenant_id,
        user_id=administration_context.user_id,
    )

    try:
        records = parent_service.list()
    except PermissionError:
        await update.message.reply_text("Access denied: parent.read permission is required.")
        return

    if not records:
        await update.message.reply_text("No parents found.")
        return

    lines = [f"{parent.name} — {parent.phone or 'No phone'} — {parent.status}" for parent in records]
    await update.message.reply_text("Parents:\n" + "\n".join(lines))
