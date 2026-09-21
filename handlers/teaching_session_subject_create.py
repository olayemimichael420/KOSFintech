"""Telegram CMOS teaching-session subject offering handler."""

from telegram import Update
from telegram.ext import ConversationHandler, ContextTypes

from models.teaching_session_subject import TeachingSessionSubject


TEACHING_SESSION_ID, TEACHING_SUBJECT_ID = range(2)


def _clear_teaching_session_subject_context(context):
    for key in (
        "teaching_session_subject_session_id",
        "teaching_session_subject_subject_id",
    ):
        context.user_data.pop(key, None)


async def teaching_session_subject(update, context):
    resolver = context.application.bot_data["get_administration_context"]
    administration_context = resolver(update, context)

    if administration_context is None:
        await update.message.reply_text(
            "Access denied: unable to resolve an authorized administration context."
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "Enter the teaching session ID for this subject offering:"
    )
    return TEACHING_SESSION_ID


async def teaching_session_subject_session_id(update, context):
    value = update.message.text.strip()

    try:
        teaching_session_id = int(value)
    except ValueError:
        await update.message.reply_text(
            "Invalid teaching session ID. Enter an integer:"
        )
        return TEACHING_SESSION_ID

    if teaching_session_id <= 0:
        await update.message.reply_text(
            "Teaching session ID must be a positive integer. Enter the ID:"
        )
        return TEACHING_SESSION_ID

    context.user_data["teaching_session_subject_session_id"] = teaching_session_id

    await update.message.reply_text(
        "Enter the teaching subject ID for this session offering:"
    )
    return TEACHING_SUBJECT_ID


async def teaching_session_subject_subject_id(update, context):
    value = update.message.text.strip()

    try:
        teaching_subject_id = int(value)
    except ValueError:
        await update.message.reply_text(
            "Invalid teaching subject ID. Enter an integer:"
        )
        return TEACHING_SUBJECT_ID

    if teaching_subject_id <= 0:
        await update.message.reply_text(
            "Teaching subject ID must be a positive integer. Enter the ID:"
        )
        return TEACHING_SUBJECT_ID

    teaching_session_id = context.user_data.get(
        "teaching_session_subject_session_id"
    )

    if teaching_session_id is None:
        _clear_teaching_session_subject_context(context)
        await update.message.reply_text(
            "Teaching session subject offering session expired. "
            "Please use /teaching_session_subject again."
        )
        return ConversationHandler.END

    resolver = context.application.bot_data["get_administration_context"]
    administration_context = resolver(update, context)

    if administration_context is None:
        _clear_teaching_session_subject_context(context)
        await update.message.reply_text(
            "Access denied: unable to resolve an authorized administration context."
        )
        return ConversationHandler.END

    services = context.application.bot_data["services"]
    subject_service = services.teaching_session_subject(
        administration_context.tenant_id,
        user_id=administration_context.user_id,
    )

    offering = TeachingSessionSubject(
        id=None,
        tenant_id=administration_context.tenant_id,
        teaching_session_id=teaching_session_id,
        teaching_subject_id=teaching_subject_id,
    )

    try:
        record = subject_service.create(offering)
    except PermissionError:
        _clear_teaching_session_subject_context(context)
        await update.message.reply_text(
            "Access denied: teaching_session_subject.write "
            "permission is required."
        )
        return ConversationHandler.END
    except ValueError as exc:
        _clear_teaching_session_subject_context(context)
        await update.message.reply_text(
            f"Teaching session subject offering could not be created: {exc}"
        )
        return ConversationHandler.END
    except Exception:
        _clear_teaching_session_subject_context(context)
        await update.message.reply_text(
            "Teaching session subject offering could not be created "
            "because the record conflicts with existing data."
        )
        return ConversationHandler.END

    _clear_teaching_session_subject_context(context)

    await update.message.reply_text(
        "Teaching session subject offering created: "
        f"session {record.teaching_session_id} — "
        f"subject {record.teaching_subject_id}"
    )
    return ConversationHandler.END


async def cancel_teaching_session_subject(update, context):
    _clear_teaching_session_subject_context(context)
    await update.message.reply_text(
        "Teaching session subject offering cancelled."
    )
    return ConversationHandler.END
