"""Telegram school-student relationship handlers."""

import sqlite3

from telegram import Update
from telegram.ext import ConversationHandler, ContextTypes

from models.school_student import SchoolStudentLink

STUDENT_ID = 0


async def linkstudent(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Start the school-student relationship workflow."""
    resolver = context.application.bot_data["get_administration_context"]
    administration_context = resolver(update, context)

    if administration_context is None:
        await update.message.reply_text(
            "Access denied: unable to resolve an authorized administration context."
        )
        return ConversationHandler.END

    await update.message.reply_text("Enter the student ID:")
    return STUDENT_ID


async def school_student_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Capture the student ID and create the school-student relationship."""
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

    resolver = context.application.bot_data["get_administration_context"]
    administration_context = resolver(update, context)

    if administration_context is None:
        await update.message.reply_text(
            "Access denied: unable to resolve an authorized administration context."
        )
        return ConversationHandler.END

    services = context.application.bot_data["services"]
    school_student_service = services.school_student(
        administration_context.tenant_id,
        user_id=administration_context.user_id,
    )

    try:
        link = school_student_service.create(
            SchoolStudentLink(
                tenant_id=administration_context.tenant_id,
                student_id=student_id,
            )
        )
    except PermissionError:
        await update.message.reply_text(
            "Access denied: school_student.write permission is required."
        )
        return ConversationHandler.END
    except ValueError as exc:
        await update.message.reply_text(
            f"Student relationship could not be created: {exc}"
        )
        return ConversationHandler.END
    except sqlite3.IntegrityError:
        await update.message.reply_text(
            "Student relationship could not be created because the record conflicts with existing data."
        )
        return ConversationHandler.END

    await update.message.reply_text(
        f"Student relationship created: student {link.student_id}"
    )
    return ConversationHandler.END


async def cancel_linkstudent(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Cancel the school-student relationship workflow."""
    await update.message.reply_text("Student relationship creation cancelled.")
    return ConversationHandler.END
