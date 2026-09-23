from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from models.session_teacher_preacher_assignment import (
    SessionTeacherPreacherAssignment,
)

TEACHER_PREACHER_ID, TEACHING_SESSION_ID = range(2)

_CONTEXT_TP_ID = "session_teacher_preacher_assignment_teacher_preacher_id"
_CONTEXT_SESSION_ID = "session_teacher_preacher_assignment_teaching_session_id"


def _cleanup(context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.pop(_CONTEXT_TP_ID, None)
    context.user_data.pop(_CONTEXT_SESSION_ID, None)


async def session_teacher_preacher_assignment(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    _cleanup(context)

    get_administration_context = context.application.bot_data.get(
        "get_administration_context"
    )

    if get_administration_context is None:
        await update.message.reply_text("Access denied.")
        return ConversationHandler.END

    administration_context = await get_administration_context(update, context)

    if administration_context is None:
        await update.message.reply_text("Access denied.")
        return ConversationHandler.END

    await update.message.reply_text(
        "Enter Teacher/Preacher capacity ID:"
    )
    return TEACHER_PREACHER_ID


async def session_teacher_preacher_assignment_teacher_preacher_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    try:
        teacher_preacher_id = int(update.message.text.strip())
        if teacher_preacher_id <= 0:
            raise ValueError
    except (TypeError, ValueError):
        await update.message.reply_text(
            "Please enter a valid positive Teacher/Preacher capacity ID."
        )
        return TEACHER_PREACHER_ID

    context.user_data[_CONTEXT_TP_ID] = teacher_preacher_id

    await update.message.reply_text(
        "Enter Teaching Session ID:"
    )
    return TEACHING_SESSION_ID


async def session_teacher_preacher_assignment_teaching_session_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    try:
        teaching_session_id = int(update.message.text.strip())
        if teaching_session_id <= 0:
            raise ValueError
    except (TypeError, ValueError):
        await update.message.reply_text(
            "Please enter a valid positive Teaching Session ID."
        )
        return TEACHING_SESSION_ID

    teacher_preacher_id = context.user_data.get(_CONTEXT_TP_ID)

    if teacher_preacher_id is None:
        _cleanup(context)
        await update.message.reply_text(
            "Session Teacher/Preacher assignment session expired. "
            "Please use /tp_session_assignment again."
        )
        return ConversationHandler.END

    context.user_data[_CONTEXT_SESSION_ID] = teaching_session_id

    get_administration_context = context.application.bot_data.get(
        "get_administration_context"
    )

    if get_administration_context is None:
        _cleanup(context)
        await update.message.reply_text("Access denied.")
        return ConversationHandler.END

    administration_context = await get_administration_context(update, context)

    if administration_context is None:
        _cleanup(context)
        await update.message.reply_text("Access denied.")
        return ConversationHandler.END

    teaching_session_id = context.user_data.get(_CONTEXT_SESSION_ID)

    if teaching_session_id is None:
        _cleanup(context)
        await update.message.reply_text(
            "Session Teacher/Preacher assignment session expired. "
            "Please use /tp_session_assignment again."
        )
        return ConversationHandler.END

    services = context.application.bot_data["services"]

    assignment = SessionTeacherPreacherAssignment(
        id=None,
        tenant_id=administration_context.tenant_id,
        teacher_preacher_id=teacher_preacher_id,
        teaching_session_id=teaching_session_id,
    )

    try:
        service = services.session_teacher_preacher_assignment(
            administration_context.tenant_id,
            user_id=administration_context.user_id,
        )
        service.create(assignment)

    except PermissionError:
        _cleanup(context)
        await update.message.reply_text(
            "session_teacher_preacher_assignment.write permission is required."
        )
        return ConversationHandler.END

    except ValueError as exc:
        _cleanup(context)
        await update.message.reply_text(str(exc))
        return ConversationHandler.END

    except Exception:
        _cleanup(context)
        await update.message.reply_text(
            "Unable to create the session Teacher/Preacher assignment."
        )
        return ConversationHandler.END

    _cleanup(context)

    await update.message.reply_text(
        "Session Teacher/Preacher assignment created successfully."
    )
    return ConversationHandler.END


async def cancel_session_teacher_preacher_assignment(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    _cleanup(context)
    await update.message.reply_text(
        "Session Teacher/Preacher assignment cancelled."
    )
    return ConversationHandler.END
