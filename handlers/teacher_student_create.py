"""Telegram teacher-student relationship handlers."""

import sqlite3

from telegram import Update
from telegram.ext import ConversationHandler, ContextTypes

from models.teacher_student import TeacherStudentLink

TEACHER_ID, STUDENT_ID = range(2)


async def linkteacherstudent(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Start the teacher-student relationship workflow."""
    resolver = context.application.bot_data["get_administration_context"]
    administration_context = resolver(update, context)

    if administration_context is None:
        await update.message.reply_text(
            "Access denied: unable to resolve an authorized administration context."
        )
        return ConversationHandler.END

    await update.message.reply_text("Enter the teacher ID:")
    return TEACHER_ID


async def teacher_student_teacher_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Capture and validate the teacher ID."""
    value = update.message.text.strip()

    try:
        teacher_id = int(value)
    except ValueError:
        await update.message.reply_text(
            "Teacher ID must be a number. Enter the teacher ID:"
        )
        return TEACHER_ID

    if teacher_id <= 0:
        await update.message.reply_text(
            "Teacher ID must be greater than zero. Enter the teacher ID:"
        )
        return TEACHER_ID

    context.user_data["teacher_student_teacher_id"] = teacher_id

    await update.message.reply_text("Enter the student ID:")
    return STUDENT_ID


async def teacher_student_student_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Capture the student ID and create the relationship."""
    value = update.message.text.strip()

    try:
        student_id = int(value)
    except ValueError:
        await update.message.reply_text(
            "Student ID must be a number. Enter the student ID:"
        )
        return STUDENT_ID

    if student_id <= 0:
        await update.message.reply_text(
            "Student ID must be greater than zero. Enter the student ID:"
        )
        return STUDENT_ID

    teacher_id = context.user_data.get("teacher_student_teacher_id")

    if not teacher_id:
        await update.message.reply_text(
            "Teacher-student relationship session expired. "
            "Please use /linkteacherstudent again."
        )
        context.user_data.pop("teacher_student_teacher_id", None)
        return ConversationHandler.END

    resolver = context.application.bot_data["get_administration_context"]
    administration_context = resolver(update, context)

    if administration_context is None:
        await update.message.reply_text(
            "Access denied: unable to resolve an authorized administration context."
        )
        context.user_data.pop("teacher_student_teacher_id", None)
        return ConversationHandler.END

    services = context.application.bot_data["services"]
    teacher_student_service = services.teacher_student(
        administration_context.tenant_id,
        user_id=administration_context.user_id,
    )

    try:
        link = teacher_student_service.create(
            TeacherStudentLink(
                tenant_id=administration_context.tenant_id,
                teacher_id=teacher_id,
                student_id=student_id,
            )
        )
    except PermissionError:
        await update.message.reply_text(
            "Access denied: teacher_student.write permission is required."
        )
        context.user_data.pop("teacher_student_teacher_id", None)
        return ConversationHandler.END
    except ValueError as exc:
        await update.message.reply_text(
            f"Teacher-student relationship could not be created: {exc}"
        )
        context.user_data.pop("teacher_student_teacher_id", None)
        return ConversationHandler.END
    except sqlite3.IntegrityError:
        await update.message.reply_text(
            "Teacher-student relationship could not be created "
            "because the record conflicts with existing data."
        )
        context.user_data.pop("teacher_student_teacher_id", None)
        return ConversationHandler.END

    await update.message.reply_text(
        f"Teacher-student relationship created: "
        f"teacher {link.teacher_id} — student {link.student_id}"
    )

    context.user_data.pop("teacher_student_teacher_id", None)
    return ConversationHandler.END


async def cancel_linkteacherstudent(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Cancel the teacher-student relationship workflow."""
    context.user_data.pop("teacher_student_teacher_id", None)
    await update.message.reply_text(
        "Teacher-student relationship creation cancelled."
    )
    return ConversationHandler.END
