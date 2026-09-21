"""Telegram CMOS grade-definition recording handler."""

from telegram import Update
from telegram.ext import ConversationHandler, ContextTypes

from models.grade import Grade


NAME, DESCRIPTION, MINIMUM_SCORE, MAXIMUM_SCORE, STATUS = range(5)


def _end_session(context: ContextTypes.DEFAULT_TYPE) -> None:
    for key in (
        "grade_name",
        "grade_description",
        "grade_minimum_score",
        "grade_maximum_score",
        "grade_status",
    ):
        context.user_data.pop(key, None)


async def grade(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Start the CMOS grade-definition recording conversation."""
    resolver = context.application.bot_data["get_administration_context"]
    administration_context = resolver(update, context)

    if administration_context is None:
        await update.message.reply_text(
            "Access denied: unable to resolve an authorized administration context."
        )
        return ConversationHandler.END

    await update.message.reply_text("Enter the grade name:")
    return NAME


async def grade_name(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    value = update.message.text.strip()

    if not value:
        await update.message.reply_text(
            "Grade name cannot be blank. Enter the grade name:"
        )
        return NAME

    context.user_data["grade_name"] = value
    await update.message.reply_text(
        "Enter an optional description, or send '-' to leave it blank:"
    )
    return DESCRIPTION


async def grade_description(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    value = update.message.text.strip()
    context.user_data["grade_description"] = None if value == "-" else value

    await update.message.reply_text("Enter the minimum score:")
    return MINIMUM_SCORE


async def grade_minimum_score(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    value = update.message.text.strip()

    try:
        minimum_score = int(value)
    except ValueError:
        await update.message.reply_text(
            "Minimum score must be an integer. Enter the minimum score:"
        )
        return MINIMUM_SCORE

    context.user_data["grade_minimum_score"] = minimum_score
    await update.message.reply_text("Enter the maximum score:")
    return MAXIMUM_SCORE


async def grade_maximum_score(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    value = update.message.text.strip()

    try:
        maximum_score = int(value)
    except ValueError:
        await update.message.reply_text(
            "Maximum score must be an integer. Enter the maximum score:"
        )
        return MAXIMUM_SCORE

    context.user_data["grade_maximum_score"] = maximum_score
    await update.message.reply_text(
        "Enter the status (active/inactive):"
    )
    return STATUS


async def grade_status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    value = update.message.text.strip().lower()

    if value not in {"active", "inactive"}:
        await update.message.reply_text(
            "Status must be active or inactive. Enter the status:"
        )
        return STATUS

    context.user_data["grade_status"] = value

    required = (
        "grade_name",
        "grade_description",
        "grade_minimum_score",
        "grade_maximum_score",
        "grade_status",
    )

    if any(key not in context.user_data for key in required):
        await update.message.reply_text(
            "Grade recording session expired. Please use /grade again."
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
    grade_service = services.grade(
        administration_context.tenant_id,
        user_id=administration_context.user_id,
    )

    try:
        record = grade_service.record(
            Grade(
                id=None,
                tenant_id=administration_context.tenant_id,
                name=context.user_data["grade_name"],
                description=context.user_data["grade_description"],
                minimum_score=context.user_data["grade_minimum_score"],
                maximum_score=context.user_data["grade_maximum_score"],
                status=context.user_data["grade_status"],
            )
        )
    except PermissionError:
        await update.message.reply_text(
            "Access denied: grade.write permission is required."
        )
        _end_session(context)
        return ConversationHandler.END
    except ValueError as exc:
        await update.message.reply_text(
            f"Grade could not be recorded: {exc}"
        )
        _end_session(context)
        return ConversationHandler.END
    except Exception:
        await update.message.reply_text(
            "Grade could not be recorded because the record conflicts "
            "with existing data."
        )
        _end_session(context)
        return ConversationHandler.END

    await update.message.reply_text(
        f"Grade recorded: {record.name} "
        f"({record.minimum_score}-{record.maximum_score})"
    )
    _end_session(context)
    return ConversationHandler.END


async def cancel_grade(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Cancel the CMOS grade-definition conversation."""
    _end_session(context)
    await update.message.reply_text("Grade recording cancelled.")
    return ConversationHandler.END
