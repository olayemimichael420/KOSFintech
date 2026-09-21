from telegram import Update
from telegram.ext import ConversationHandler, ContextTypes

from models.assessment import Assessment


TEACHING_CONTENT_ID, NAME, ASSESSMENT_DATE, DESCRIPTION, STATUS = range(5)

ALLOWED_STATUSES = {"active", "inactive"}


def _end_session(context: ContextTypes.DEFAULT_TYPE) -> None:
    for key in (
        "assessment_teaching_content_id",
        "assessment_name",
        "assessment_date",
        "assessment_description",
    ):
        context.user_data.pop(key, None)


async def assessment(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    get_administration_context = context.application.bot_data.get(
        "get_administration_context"
    )
    admin_context = (
        get_administration_context(update.effective_user.id)
        if get_administration_context
        else None
    )

    if admin_context is None:
        await update.message.reply_text(
            "Administration context required."
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "Enter the teaching content ID:"
    )
    return TEACHING_CONTENT_ID


async def assessment_teaching_content_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    try:
        teaching_content_id = int(update.message.text.strip())
        if teaching_content_id <= 0:
            raise ValueError
    except (TypeError, ValueError):
        await update.message.reply_text(
            "Teaching content ID must be a positive integer."
        )
        return TEACHING_CONTENT_ID

    context.user_data["assessment_teaching_content_id"] = teaching_content_id
    await update.message.reply_text("Enter the assessment name:")
    return NAME


async def assessment_name(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    name = update.message.text.strip()

    if not name:
        await update.message.reply_text(
            "Assessment name is required."
        )
        return NAME

    context.user_data["assessment_name"] = name
    await update.message.reply_text(
        "Enter the assessment date (YYYY-MM-DD):"
    )
    return ASSESSMENT_DATE


async def assessment_date(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    from datetime import date

    value = update.message.text.strip()

    try:
        date.fromisoformat(value)
    except ValueError:
        await update.message.reply_text(
            "Assessment date must use YYYY-MM-DD format."
        )
        return ASSESSMENT_DATE

    context.user_data["assessment_date"] = value
    await update.message.reply_text(
        "Enter a description, or - for none:"
    )
    return DESCRIPTION


async def assessment_description(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    value = update.message.text.strip()
    context.user_data["assessment_description"] = (
        None if value == "-" else value
    )

    await update.message.reply_text(
        "Enter status: active or inactive."
    )
    return STATUS


async def assessment_status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    status = update.message.text.strip().lower()

    if status not in ALLOWED_STATUSES:
        await update.message.reply_text(
            "Status must be active or inactive."
        )
        return STATUS

    get_administration_context = context.application.bot_data.get(
        "get_administration_context"
    )
    admin_context = (
        get_administration_context(update.effective_user.id)
        if get_administration_context
        else None
    )

    if admin_context is None:
        await update.message.reply_text(
            "Administration context required."
        )
        _end_session(context)
        return ConversationHandler.END

    tenant_id = admin_context.tenant_id
    user_id = admin_context.user_id
    services = context.application.bot_data["services"]

    assessment_record = Assessment(
        id=None,
        tenant_id=tenant_id,
        teaching_content_id=context.user_data[
            "assessment_teaching_content_id"
        ],
        name=context.user_data["assessment_name"],
        description=context.user_data["assessment_description"],
        assessment_date=context.user_data["assessment_date"],
        status=status,
    )

    try:
        recorded = services.assessment(
            tenant_id=tenant_id,
            user_id=user_id,
        ).record(assessment_record)
    except PermissionError as exc:
        await update.message.reply_text(str(exc))
        _end_session(context)
        return ConversationHandler.END
    except ValueError as exc:
        await update.message.reply_text(str(exc))
        _end_session(context)
        return ConversationHandler.END
    except Exception:
        await update.message.reply_text(
            "Unable to record assessment."
        )
        _end_session(context)
        return ConversationHandler.END

    await update.message.reply_text(
        f"Assessment recorded: {recorded.id}"
    )
    _end_session(context)
    return ConversationHandler.END


async def cancel_assessment(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    _end_session(context)
    await update.message.reply_text("Assessment creation cancelled.")
    return ConversationHandler.END
