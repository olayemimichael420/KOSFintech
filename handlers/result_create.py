"""Telegram CMOS result recording handler."""

from datetime import date

from telegram import Update
from telegram.ext import ConversationHandler, ContextTypes

from models.result import Result


ASSESSMENT_ID, MEMBERSHIP_ID, GRADE_ID, RESULT, RESULT_DATE, REMARK, STATUS = range(7)


def _end_session(context: ContextTypes.DEFAULT_TYPE) -> None:
    for key in (
        "result_assessment_id",
        "result_membership_id",
        "result_grade_id",
        "result_value",
        "result_date",
        "result_remark",
        "result_status",
    ):
        context.user_data.pop(key, None)


async def result(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    resolver = context.application.bot_data["get_administration_context"]
    administration_context = resolver(update, context)

    if administration_context is None:
        await update.message.reply_text(
            "Access denied: unable to resolve an authorized administration context."
        )
        return ConversationHandler.END

    await update.message.reply_text("Enter the assessment ID:")
    return ASSESSMENT_ID


async def result_assessment_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    try:
        value = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text(
            "Assessment ID must be an integer. Enter the assessment ID:"
        )
        return ASSESSMENT_ID

    context.user_data["result_assessment_id"] = value
    await update.message.reply_text("Enter the membership ID:")
    return MEMBERSHIP_ID


async def result_membership_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    try:
        value = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text(
            "Membership ID must be an integer. Enter the membership ID:"
        )
        return MEMBERSHIP_ID

    context.user_data["result_membership_id"] = value
    await update.message.reply_text("Enter the grade ID:")
    return GRADE_ID


async def result_grade_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    try:
        value = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text(
            "Grade ID must be an integer. Enter the grade ID:"
        )
        return GRADE_ID

    context.user_data["result_grade_id"] = value
    await update.message.reply_text("Enter the result:")
    return RESULT


async def result_value(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    value = update.message.text.strip()

    if not value:
        await update.message.reply_text(
            "Result cannot be blank. Enter the result:"
        )
        return RESULT

    context.user_data["result_value"] = value
    await update.message.reply_text(
        "Enter the result date (YYYY-MM-DD):"
    )
    return RESULT_DATE


async def result_date(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    value = update.message.text.strip()

    try:
        date.fromisoformat(value)
    except ValueError:
        await update.message.reply_text(
            "Result date must be a valid ISO date (YYYY-MM-DD). "
            "Enter the result date:"
        )
        return RESULT_DATE

    context.user_data["result_date"] = value
    await update.message.reply_text(
        "Enter an optional remark, or send '-' to leave it blank:"
    )
    return REMARK


async def result_remark(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    value = update.message.text.strip()
    context.user_data["result_remark"] = None if value == "-" else value

    await update.message.reply_text(
        "Enter the status (active/inactive):"
    )
    return STATUS


async def result_status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    value = update.message.text.strip().lower()

    if value not in {"active", "inactive"}:
        await update.message.reply_text(
            "Status must be active or inactive. Enter the status:"
        )
        return STATUS

    context.user_data["result_status"] = value

    required = (
        "result_assessment_id",
        "result_membership_id",
        "result_grade_id",
        "result_value",
        "result_date",
        "result_remark",
        "result_status",
    )

    if any(key not in context.user_data for key in required):
        await update.message.reply_text(
            "Result recording session expired. Please use /result again."
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
    result_service = services.result(
        administration_context.tenant_id,
        user_id=administration_context.user_id,
    )

    try:
        record = result_service.record(
            Result(
                id=None,
                tenant_id=administration_context.tenant_id,
                assessment_id=context.user_data["result_assessment_id"],
                membership_id=context.user_data["result_membership_id"],
                grade_id=context.user_data["result_grade_id"],
                result=context.user_data["result_value"],
                result_date=context.user_data["result_date"],
                remark=context.user_data["result_remark"],
                status=context.user_data["result_status"],
            )
        )
    except PermissionError:
        await update.message.reply_text(
            "Access denied: result.write permission is required."
        )
        _end_session(context)
        return ConversationHandler.END
    except ValueError as exc:
        await update.message.reply_text(
            f"Result could not be recorded: {exc}"
        )
        _end_session(context)
        return ConversationHandler.END
    except Exception:
        await update.message.reply_text(
            "Result could not be recorded because the record conflicts "
            "with existing data."
        )
        _end_session(context)
        return ConversationHandler.END

    await update.message.reply_text(
        f"Result recorded: {record.result}"
    )
    _end_session(context)
    return ConversationHandler.END


async def cancel_result(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    _end_session(context)
    await update.message.reply_text("Result recording cancelled.")
    return ConversationHandler.END
