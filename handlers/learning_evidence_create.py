"""Telegram CMOS learning-evidence recording handler."""

from datetime import date

from telegram import Update
from telegram.ext import ConversationHandler, ContextTypes

from models.learning_evidence import LearningEvidence


MEMBERSHIP_ID, TEACHING_CONTENT_ID, EVIDENCE_DATE, DESCRIPTION, REMARK = range(5)


def _end_session(context) -> None:
    for key in (
        "learning_evidence_membership_id",
        "learning_evidence_teaching_content_id",
        "learning_evidence_date",
        "learning_evidence_description",
        "learning_evidence_remark",
    ):
        context.user_data.pop(key, None)


async def learning_evidence(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the CMOS learning-evidence recording conversation."""
    resolver = context.application.bot_data["get_administration_context"]
    administration_context = resolver(update, context)

    if administration_context is None:
        await update.message.reply_text(
            "Access denied: unable to resolve an authorized administration context."
        )
        return ConversationHandler.END

    await update.message.reply_text("Enter the membership ID:")
    return MEMBERSHIP_ID


async def learning_evidence_membership_id(
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

    context.user_data["learning_evidence_membership_id"] = membership_id
    await update.message.reply_text("Enter the teaching content ID:")
    return TEACHING_CONTENT_ID


async def learning_evidence_teaching_content_id(
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

    context.user_data["learning_evidence_teaching_content_id"] = teaching_content_id
    await update.message.reply_text("Enter the evidence date (YYYY-MM-DD):")
    return EVIDENCE_DATE


async def learning_evidence_date(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Capture and validate the evidence date."""
    value = update.message.text.strip()

    try:
        parsed_date = date.fromisoformat(value)
    except ValueError:
        await update.message.reply_text(
            "Invalid date. Use YYYY-MM-DD:"
        )
        return EVIDENCE_DATE

    context.user_data["learning_evidence_date"] = parsed_date.isoformat()
    await update.message.reply_text("Describe the observable learning evidence:")
    return DESCRIPTION


async def learning_evidence_description(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Capture the required learning-evidence description."""
    value = update.message.text.strip()

    if not value:
        await update.message.reply_text(
            "Description is required. Describe the observable learning evidence:"
        )
        return DESCRIPTION

    context.user_data["learning_evidence_description"] = value
    await update.message.reply_text(
        "Enter an optional remark, or send '-' to leave it blank:"
    )
    return REMARK


async def learning_evidence_remark(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Capture the optional remark and record learning evidence."""
    value = update.message.text.strip()
    remark = None if value == "-" else value

    membership_id = context.user_data.get("learning_evidence_membership_id")
    teaching_content_id = context.user_data.get(
        "learning_evidence_teaching_content_id"
    )
    evidence_date = context.user_data.get("learning_evidence_date")
    description = context.user_data.get("learning_evidence_description")

    if not all(
        (
            membership_id,
            teaching_content_id,
            evidence_date,
            description,
        )
    ):
        await update.message.reply_text(
            "Learning evidence recording session expired. "
            "Please use /learning_evidence again."
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
    evidence_service = services.learning_evidence(
        administration_context.tenant_id,
        user_id=administration_context.user_id,
    )

    try:
        record = evidence_service.record(
            LearningEvidence(
                id=None,
                tenant_id=administration_context.tenant_id,
                membership_id=membership_id,
                teaching_content_id=teaching_content_id,
                evidence_date=evidence_date,
                description=description,
                remark=remark,
            )
        )
    except PermissionError:
        await update.message.reply_text(
            "Access denied: learning_evidence.write permission is required."
        )
        _end_session(context)
        return ConversationHandler.END
    except ValueError as exc:
        await update.message.reply_text(
            f"Learning evidence could not be recorded: {exc}"
        )
        _end_session(context)
        return ConversationHandler.END
    except Exception:
        await update.message.reply_text(
            "Learning evidence could not be recorded because the record "
            "conflicts with existing data."
        )
        _end_session(context)
        return ConversationHandler.END

    await update.message.reply_text(
        f"Learning evidence recorded: member {record.membership_id} — "
        f"content {record.teaching_content_id} — {record.evidence_date}"
    )

    _end_session(context)
    return ConversationHandler.END


async def cancel_learning_evidence(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Cancel the CMOS learning-evidence conversation."""
    _end_session(context)
    await update.message.reply_text(
        "Learning evidence recording cancelled."
    )
    return ConversationHandler.END
