"""Telegram CMOS assessment-score recording handler."""

from datetime import date

from telegram import Update
from telegram.ext import ConversationHandler, ContextTypes

from models.assessment_score import AssessmentScore


ASSESSMENT_ID, MEMBERSHIP_ID, SCORE, SCORED_DATE, REMARK = range(5)


def _end_session(context: ContextTypes.DEFAULT_TYPE) -> None:
    for key in (
        "assessment_score_assessment_id",
        "assessment_score_membership_id",
        "assessment_score_score",
        "assessment_score_date",
        "assessment_score_remark",
    ):
        context.user_data.pop(key, None)


async def assessment_score(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Start the CMOS assessment-score recording conversation."""
    resolver = context.application.bot_data["get_administration_context"]
    administration_context = resolver(update, context)

    if administration_context is None:
        await update.message.reply_text(
            "Access denied: unable to resolve an authorized administration context."
        )
        return ConversationHandler.END

    await update.message.reply_text("Enter the assessment ID:")
    return ASSESSMENT_ID


async def assessment_score_assessment_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    value = update.message.text.strip()

    try:
        assessment_id = int(value)
    except ValueError:
        await update.message.reply_text(
            "Assessment ID must be a number. Enter the assessment ID:"
        )
        return ASSESSMENT_ID

    if assessment_id <= 0:
        await update.message.reply_text(
            "Assessment ID must be greater than zero. Enter the assessment ID:"
        )
        return ASSESSMENT_ID

    context.user_data["assessment_score_assessment_id"] = assessment_id
    await update.message.reply_text("Enter the membership ID:")
    return MEMBERSHIP_ID


async def assessment_score_membership_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
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

    context.user_data["assessment_score_membership_id"] = membership_id
    await update.message.reply_text("Enter the score:")
    return SCORE


async def assessment_score_value(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    value = update.message.text.strip()

    try:
        score = int(value)
    except ValueError:
        await update.message.reply_text(
            "Score must be an integer. Enter the score:"
        )
        return SCORE

    context.user_data["assessment_score_score"] = score
    await update.message.reply_text(
        "Enter the scored date (YYYY-MM-DD):"
    )
    return SCORED_DATE


async def assessment_score_date(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    value = update.message.text.strip()

    try:
        parsed_date = date.fromisoformat(value)
    except ValueError:
        await update.message.reply_text(
            "Invalid date. Use YYYY-MM-DD:"
        )
        return SCORED_DATE

    context.user_data["assessment_score_date"] = parsed_date.isoformat()
    await update.message.reply_text(
        "Enter an optional remark, or send '-' to leave it blank:"
    )
    return REMARK


async def assessment_score_remark(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    value = update.message.text.strip()
    remark = None if value == "-" else value

    assessment_id = context.user_data.get(
        "assessment_score_assessment_id"
    )
    membership_id = context.user_data.get(
        "assessment_score_membership_id"
    )
    score = context.user_data.get("assessment_score_score")
    scored_date = context.user_data.get("assessment_score_date")

    if any(
        value is None
        for value in (
            assessment_id,
            membership_id,
            score,
            scored_date,
        )
    ):
        await update.message.reply_text(
            "Assessment score recording session expired. "
            "Please use /assessment_score again."
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
    score_service = services.assessment_score(
        administration_context.tenant_id,
        user_id=administration_context.user_id,
    )

    try:
        record = score_service.record(
            AssessmentScore(
                id=None,
                tenant_id=administration_context.tenant_id,
                assessment_id=assessment_id,
                membership_id=membership_id,
                score=score,
                scored_date=scored_date,
                remark=remark,
            )
        )
    except PermissionError:
        await update.message.reply_text(
            "Access denied: assessment_score.write permission is required."
        )
        _end_session(context)
        return ConversationHandler.END
    except ValueError as exc:
        await update.message.reply_text(
            f"Assessment score could not be recorded: {exc}"
        )
        _end_session(context)
        return ConversationHandler.END
    except Exception:
        await update.message.reply_text(
            "Assessment score could not be recorded because the record "
            "conflicts with existing data."
        )
        _end_session(context)
        return ConversationHandler.END

    await update.message.reply_text(
        f"Assessment score recorded: member {record.membership_id} — "
        f"assessment {record.assessment_id} — score {record.score}"
    )
    _end_session(context)
    return ConversationHandler.END


async def cancel_assessment_score(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Cancel the CMOS assessment-score conversation."""
    _end_session(context)
    await update.message.reply_text(
        "Assessment score recording cancelled."
    )
    return ConversationHandler.END
