"""Telegram CMOS teaching-session creation handler."""

from datetime import date

from telegram import Update
from telegram.ext import ConversationHandler, ContextTypes

from models.teaching_session import TeachingSession


NAME, START_DATE, END_DATE = range(3)


def _end_session(context) -> None:
    for key in (
        "teaching_session_name",
        "teaching_session_start_date",
        "teaching_session_end_date",
    ):
        context.user_data.pop(key, None)


async def teaching_session(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Start the CMOS teaching-session creation conversation."""
    resolver = context.application.bot_data["get_administration_context"]
    administration_context = resolver(update, context)

    if administration_context is None:
        await update.message.reply_text(
            "Access denied: unable to resolve an authorized administration context."
        )
        return ConversationHandler.END

    await update.message.reply_text("Enter the teaching session name:")
    return NAME


async def teaching_session_name(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Capture and validate the teaching session name."""
    value = update.message.text.strip()

    if not value:
        await update.message.reply_text(
            "Teaching session name cannot be blank. Enter the teaching session name:"
        )
        return NAME

    context.user_data["teaching_session_name"] = value
    await update.message.reply_text(
        "Enter the teaching session start date (YYYY-MM-DD):"
    )
    return START_DATE


async def teaching_session_start_date(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Capture and validate the teaching session start date."""
    value = update.message.text.strip()

    try:
        parsed_date = date.fromisoformat(value)
    except ValueError:
        await update.message.reply_text(
            "Invalid date. Use YYYY-MM-DD:"
        )
        return START_DATE

    context.user_data["teaching_session_start_date"] = parsed_date.isoformat()
    await update.message.reply_text(
        "Enter the teaching session end date (YYYY-MM-DD):"
    )
    return END_DATE


async def teaching_session_end_date(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Capture the end date and create the teaching session."""
    value = update.message.text.strip()

    try:
        parsed_date = date.fromisoformat(value)
    except ValueError:
        await update.message.reply_text(
            "Invalid date. Use YYYY-MM-DD:"
        )
        return END_DATE

    name = context.user_data.get("teaching_session_name")
    start_date = context.user_data.get("teaching_session_start_date")

    if not name or not start_date:
        await update.message.reply_text(
            "Teaching session creation session expired. "
            "Please use /teaching_session again."
        )
        _end_session(context)
        return ConversationHandler.END

    resolver = context.application.bot_data["get_administration_context"]
    administration_context = resolver(update, context)

    if administration_context is None:
        await update.message.reply_text(
            "Access denied: unable to resolve an authorized administration context."
        )
        _end_session(context)
        return ConversationHandler.END

    services = context.application.bot_data["services"]
    session_service = services.teaching_session(
        administration_context.tenant_id,
        user_id=administration_context.user_id,
    )

    session = TeachingSession(
        id=None,
        tenant_id=administration_context.tenant_id,
        name=name,
        start_date=start_date,
        end_date=parsed_date.isoformat(),
    )

    try:
        record = session_service.create(session)
    except PermissionError:
        await update.message.reply_text(
            "Access denied: teaching_session.write permission is required."
        )
        _end_session(context)
        return ConversationHandler.END
    except ValueError as exc:
        await update.message.reply_text(
            f"Teaching session could not be created: {exc}"
        )
        _end_session(context)
        return ConversationHandler.END
    except Exception:
        await update.message.reply_text(
            "Teaching session could not be created because the record "
            "conflicts with existing data."
        )
        _end_session(context)
        return ConversationHandler.END

    await update.message.reply_text(
        f"Teaching session created: {record.name} — "
        f"{record.start_date} to {record.end_date}"
    )
    _end_session(context)
    return ConversationHandler.END


async def cancel_teaching_session(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Cancel the CMOS teaching-session creation conversation."""
    _end_session(context)
    await update.message.reply_text(
        "Teaching session creation cancelled."
    )
    return ConversationHandler.END
