"""Telegram CMOS Teacher/Preacher subject assignment handler."""

from telegram import Update
from telegram.ext import ConversationHandler, ContextTypes

from models.teacher_preacher_subject_assignment import (
    TeacherPreacherSubjectAssignment,
)


TEACHER_PREACHER_ID, TEACHING_SUBJECT_ID = range(2)


def _clear_teacher_preacher_subject_assignment_context(context):
    for key in (
        "teacher_preacher_subject_assignment_teacher_preacher_id",
        "teacher_preacher_subject_assignment_teaching_subject_id",
    ):
        context.user_data.pop(key, None)


async def teacher_preacher_subject_assignment(update, context):
    resolver = context.application.bot_data["get_administration_context"]
    administration_context = resolver(update, context)
    if administration_context is None:
        await update.message.reply_text(
            "Access denied: unable to resolve an authorized administration context."
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "Enter the Teacher/Preacher capacity ID for this subject assignment:"
    )
    return TEACHER_PREACHER_ID


async def teacher_preacher_subject_assignment_teacher_preacher_id(
    update, context
):
    value = update.message.text.strip()
    try:
        teacher_preacher_id = int(value)
    except ValueError:
        await update.message.reply_text(
            "Invalid Teacher/Preacher capacity ID. Enter an integer:"
        )
        return TEACHER_PREACHER_ID

    if teacher_preacher_id <= 0:
        await update.message.reply_text(
            "Teacher/Preacher capacity ID must be a positive integer. Enter the ID:"
        )
        return TEACHER_PREACHER_ID

    context.user_data[
        "teacher_preacher_subject_assignment_teacher_preacher_id"
    ] = teacher_preacher_id

    await update.message.reply_text(
        "Enter the teaching subject ID for this Teacher/Preacher assignment:"
    )
    return TEACHING_SUBJECT_ID


async def teacher_preacher_subject_assignment_teaching_subject_id(
    update, context
):
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

    teacher_preacher_id = context.user_data.get(
        "teacher_preacher_subject_assignment_teacher_preacher_id"
    )
    if teacher_preacher_id is None:
        _clear_teacher_preacher_subject_assignment_context(context)
        await update.message.reply_text(
            "Teacher/Preacher subject assignment session expired. "
            "Please use /teacher_preacher_subject_assignment again."
        )
        return ConversationHandler.END

    resolver = context.application.bot_data["get_administration_context"]
    administration_context = resolver(update, context)
    if administration_context is None:
        _clear_teacher_preacher_subject_assignment_context(context)
        await update.message.reply_text(
            "Access denied: unable to resolve an authorized administration context."
        )
        return ConversationHandler.END

    services = context.application.bot_data["services"]
    assignment_service = services.teacher_preacher_subject_assignment(
        administration_context.tenant_id,
        user_id=administration_context.user_id,
    )

    assignment = TeacherPreacherSubjectAssignment(
        id=None,
        tenant_id=administration_context.tenant_id,
        teacher_preacher_id=teacher_preacher_id,
        teaching_subject_id=teaching_subject_id,
    )

    try:
        record = assignment_service.create(assignment)
    except PermissionError:
        _clear_teacher_preacher_subject_assignment_context(context)
        await update.message.reply_text(
            "Access denied: teacher_preacher_subject_assignment.write "
            "permission is required."
        )
        return ConversationHandler.END
    except ValueError as exc:
        _clear_teacher_preacher_subject_assignment_context(context)
        await update.message.reply_text(
            f"Teacher/Preacher subject assignment could not be created: {exc}"
        )
        return ConversationHandler.END
    except Exception:
        _clear_teacher_preacher_subject_assignment_context(context)
        await update.message.reply_text(
            "Teacher/Preacher subject assignment could not be created "
            "because the record conflicts with existing data."
        )
        return ConversationHandler.END

    _clear_teacher_preacher_subject_assignment_context(context)
    await update.message.reply_text(
        "Teacher/Preacher subject assignment created: "
        f"Teacher/Preacher {record.teacher_preacher_id} — "
        f"subject {record.teaching_subject_id}"
    )
    return ConversationHandler.END


async def cancel_teacher_preacher_subject_assignment(update, context):
    _clear_teacher_preacher_subject_assignment_context(context)
    await update.message.reply_text(
        "Teacher/Preacher subject assignment cancelled."
    )
    return ConversationHandler.END
