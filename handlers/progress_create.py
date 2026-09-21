"""Telegram CMOS progress recording handler."""

from datetime import date

from telegram import Update
from telegram.ext import ConversationHandler, ContextTypes

from models.progress import Progress


MEMBERSHIP_ID, TEACHING_CONTENT_ID, PROGRESS_DATE, DESCRIPTION, REMARK, STATUS = range(6)


def _end_session(context) -> None:
    for key in (
        "progress_membership_id",
        "progress_teaching_content_id",
        "progress_date",
        "progress_description",
        "progress_remark",
        "progress_status",
    ):
        context.user_data.pop(key, None)


async def progress(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the CMOS progress recording conversation."""
    resolver = context.application.bot_data["get_administration_context"]
    administration_context = resolver(update, context)

    if administration_context is None:
        await update.message.reply_text(
            "Access denied: unable to resolve an authorized administration context."
        )
        return ConversationHandler.END

    await update.message.reply_text("Enter the membership ID:")
    return MEMBERSHIP_ID


async def progress_membership_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Capture and validate the membership ID."""
    value = update.message.text.strip()

    try:
        membership_id = int(value)
    except ValueError:
        await update.message.reply_text(
            "Membership ID must be a number. Enter the membership ID:"
        )
        return MEMBERSHIP_ID

    if membership_id <= 0:
        await update.message.reply_text(
            "Membership ID must be greater than zero. Enter the membership ID:"
        )
        return MEMBERSHIP_ID

    context.user_data["progress_membership_id"] = membership_id
    await update.message.reply_text("Enter the teaching content ID:")
    return TEACHING_CONTENT_ID


async def progress_teaching_content_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Capture and validate the teaching content ID."""
    value = update.message.text.strip()

    try:
        teaching_content_id = int(value)
    except ValueError:
        await update.message.reply_text(
            "Teaching content ID must be a number. Enter the teaching content ID:"
        )
        return TEACHING_CONTENT_ID

    if teaching_content_id <= 0:
        await update.message.reply_text(
            "Teaching content ID must be greater than zero. Enter the teaching content ID:"
        )
        return TEACHING_CONTENT_ID

    context.user_data["progress_teaching_content_id"] = teaching_content_id
    await update.message.reply_text("Enter the progress date (YYYY-MM-DD):")
    return PROGRESS_DATE


async def progress_date(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Capture and validate the progress date."""
    value = update.message.text.strip()

    try:
        parsed_date = date.fromisoformat(value)
    except ValueError:
        await update.message.reply_text("Invalid date. Use YYYY-MM-DD:")
        return PROGRESS_DATE

    context.user_data["progress_date"] = parsed_date.isoformat()
    await update.message.reply_text("Describe the observable progress:")
    return DESCRIPTION


async def progress_description(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Capture the required progress description."""
    value = update.message.text.strip()

    if not value:
        await update.message.reply_text(
            "Description is required. Describe the observable progress:"
        )
        return DESCRIPTION

    context.user_data["progress_description"] = value
    await update.message.reply_text(
        "Enter an optional remark, or send '-' to leave it blank:"
    )
    return REMARK


async def progress_remark(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Capture the optional remark."""
    value = update.message.text.strip()
    context.user_data["progress_remark"] = None if value == "-" else value

    await update.message.reply_text("Enter the status (active/inactive):")
    return STATUS


async def progress_status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Capture status and record the progress."""
    value = update.message.text.strip().lower()

    if value not in {"active", "inactive"}:
        await update.message.reply_text(
            "Status must be active or inactive. Enter the status:"
        )
        return STATUS

    context.user_data["progress_status"] = value

    membership_id = context.user_data.get("progress_membership_id")
    teaching_content_id = context.user_data.get("progress_teaching_content_id")
    progress_date_value = context.user_data.get("progress_date")
    description = context.user_data.get("progress_description")
    remark = context.user_data.get("progress_remark")

    if not all(
        (
            membership_id,
            teaching_content_id,
            progress_date_value,
            description,
        )
    ):
        await update.message.reply_text(
            "Progress recording session expired. "
            "Please use /progress again."
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
    progress_service = services.progress(
        administration_context.tenant_id,
        user_id=administration_context.user_id,
    )

    try:
        record = progress_service.record(
            Progress(
                id=None,
                tenant_id=administration_context.tenant_id,
                membership_id=membership_id,
                teaching_content_id=teaching_content_id,
                progress_date=progress_date_value,
                description=description,
                remark=remark,
                status=value,
            )
        )
    except PermissionError:
        await update.message.reply_text(
            "Access denied: progress.write permission is required."
        )
        _end_session(context)
        return ConversationHandler.END
    except ValueError as exc:
        await update.message.reply_text(
            f"Progress could not be recorded: {exc}"
        )
        _end_session(context)
        return ConversationHandler.END
    except Exception:
        await update.message.reply_text(
            "Progress could not be recorded because the record "
            "conflicts with existing data."
        )
        _end_session(context)
        return ConversationHandler.END

    await update.message.reply_text(
        f"Progress recorded: member {record.membership_id} — "
        f"content {record.teaching_content_id} — {record.progress_date}"
    )

    _end_session(context)
    return ConversationHandler.END


async def cancel_progress(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Cancel the CMOS progress recording conversation."""
    _end_session(context)
    await update.message.reply_text("Progress recording cancelled.")
    return ConversationHandler.END
