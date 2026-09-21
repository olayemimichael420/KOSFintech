"""Telegram CMOS teaching-content Teacher/Preacher assignment handler."""

from telegram import Update
from telegram.ext import ConversationHandler, ContextTypes

from models.teaching_content_teacher_preacher_assignment import (
    TeachingContentTeacherPreacherAssignment,
)


TEACHING_CONTENT_ID, TEACHER_PREACHER_ID, STATUS = range(3)


def _clear_assignment_context(context):
    for key in (
        "teaching_content_assignment_content_id",
        "teaching_content_assignment_teacher_preacher_id",
    ):
        context.user_data.pop(key, None)


async def teaching_content_teacher_preacher_assignment(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    resolver = context.application.bot_data["get_administration_context"]
    administration_context = resolver(update, context)

    if administration_context is None:
        await update.message.reply_text(
            "Access denied: unable to resolve an authorized administration context."
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "Enter the teaching content ID for this assignment:"
    )
    return TEACHING_CONTENT_ID


async def teaching_content_assignment_content_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    value = update.message.text.strip()

    try:
        content_id = int(value)
    except ValueError:
        await update.message.reply_text(
            "Invalid teaching content ID. Enter an integer:"
        )
        return TEACHING_CONTENT_ID

    if content_id <= 0:
        await update.message.reply_text(
            "Teaching content ID must be a positive integer. Enter the ID:"
        )
        return TEACHING_CONTENT_ID

    context.user_data["teaching_content_assignment_content_id"] = content_id

    await update.message.reply_text(
        "Enter the Teacher/Preacher ID for this assignment:"
    )
    return TEACHER_PREACHER_ID


async def teaching_content_assignment_teacher_preacher_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    value = update.message.text.strip()

    try:
        teacher_preacher_id = int(value)
    except ValueError:
        await update.message.reply_text(
            "Invalid Teacher/Preacher ID. Enter an integer:"
        )
        return TEACHER_PREACHER_ID

    if teacher_preacher_id <= 0:
        await update.message.reply_text(
            "Teacher/Preacher ID must be a positive integer. Enter the ID:"
        )
        return TEACHER_PREACHER_ID

    context.user_data[
        "teaching_content_assignment_teacher_preacher_id"
    ] = teacher_preacher_id

    await update.message.reply_text(
        "Enter the assignment status (active/inactive):"
    )
    return STATUS


async def teaching_content_assignment_status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    value = update.message.text.strip().lower()

    if value not in {"active", "inactive"}:
        await update.message.reply_text(
            "Invalid status. Enter active or inactive:"
        )
        return STATUS

    content_id = context.user_data.get(
        "teaching_content_assignment_content_id"
    )
    teacher_preacher_id = context.user_data.get(
        "teaching_content_assignment_teacher_preacher_id"
    )

    if content_id is None or teacher_preacher_id is None:
        _clear_assignment_context(context)
        await update.message.reply_text(
            "Teaching content assignment session expired. "
            "Please use /teaching_content_teacher_preacher_assignment again."
        )
        return ConversationHandler.END

    resolver = context.application.bot_data["get_administration_context"]
    administration_context = resolver(update, context)

    if administration_context is None:
        _clear_assignment_context(context)
        await update.message.reply_text(
            "Access denied: unable to resolve an authorized administration context."
        )
        return ConversationHandler.END

    services = context.application.bot_data["services"]
    assignment_service = services.teaching_content_teacher_preacher_assignment(
        administration_context.tenant_id,
        user_id=administration_context.user_id,
    )

    assignment = TeachingContentTeacherPreacherAssignment(
        id=None,
        tenant_id=administration_context.tenant_id,
        teaching_content_id=content_id,
        teacher_preacher_id=teacher_preacher_id,
        status=value,
    )

    try:
        record = assignment_service.create(assignment)
    except PermissionError:
        _clear_assignment_context(context)
        await update.message.reply_text(
            "Access denied: "
            "teaching_content_teacher_preacher_assignment.write "
            "permission is required."
        )
        return ConversationHandler.END
    except ValueError as exc:
        _clear_assignment_context(context)
        await update.message.reply_text(
            f"Teaching content Teacher/Preacher assignment could not be "
            f"created: {exc}"
        )
        return ConversationHandler.END
    except Exception:
        _clear_assignment_context(context)
        await update.message.reply_text(
            "Teaching content Teacher/Preacher assignment could not be "
            "created because the record conflicts with existing data."
        )
        return ConversationHandler.END

    _clear_assignment_context(context)

    await update.message.reply_text(
        "Teaching content Teacher/Preacher assignment created: "
        f"content {record.teaching_content_id} — "
        f"Teacher/Preacher {record.teacher_preacher_id} "
        f"({record.status})"
    )
    return ConversationHandler.END


async def cancel_teaching_content_teacher_preacher_assignment(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    _clear_assignment_context(context)
    await update.message.reply_text(
        "Teaching content Teacher/Preacher assignment cancelled."
    )
    return ConversationHandler.END
