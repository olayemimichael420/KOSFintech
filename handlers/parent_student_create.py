"""Telegram parent-student relationship handlers."""

import sqlite3

from telegram import Update
from telegram.ext import ConversationHandler, ContextTypes

from models.parent_student import ParentStudentLink

PARENT_ID, STUDENT_ID = range(2)


async def linkparentstudent(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Start the parent-student relationship workflow."""
    resolver = context.application.bot_data["get_administration_context"]
    administration_context = resolver(update, context)

    if administration_context is None:
        await update.message.reply_text(
            "Access denied: unable to resolve an authorized administration context."
        )
        return ConversationHandler.END

    await update.message.reply_text("Enter the parent ID:")
    return PARENT_ID


async def parent_student_parent_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Capture and validate the parent ID."""
    value = update.message.text.strip()

    try:
        parent_id = int(value)
    except ValueError:
        await update.message.reply_text(
            "Parent ID must be a number. Enter the parent ID:"
        )
        return PARENT_ID

    if parent_id <= 0:
        await update.message.reply_text(
            "Parent ID must be greater than zero. Enter the parent ID:"
        )
        return PARENT_ID

    context.user_data["parent_student_parent_id"] = parent_id

    await update.message.reply_text("Enter the student ID:")
    return STUDENT_ID


async def parent_student_student_id(
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

    parent_id = context.user_data.get("parent_student_parent_id")

    if not parent_id:
        await update.message.reply_text(
            "Parent-student relationship session expired. "
            "Please use /linkparentstudent again."
        )
        context.user_data.pop("parent_student_parent_id", None)
        return ConversationHandler.END

    resolver = context.application.bot_data["get_administration_context"]
    administration_context = resolver(update, context)

    if administration_context is None:
        await update.message.reply_text(
            "Access denied: unable to resolve an authorized administration context."
        )
        context.user_data.pop("parent_student_parent_id", None)
        return ConversationHandler.END

    services = context.application.bot_data["services"]
    parent_student_service = services.parent_student(
        administration_context.tenant_id,
        user_id=administration_context.user_id,
    )

    try:
        link = parent_student_service.create(
            ParentStudentLink(
                tenant_id=administration_context.tenant_id,
                parent_id=parent_id,
                student_id=student_id,
            )
        )
    except PermissionError:
        await update.message.reply_text(
            "Access denied: parent_student.write permission is required."
        )
        context.user_data.pop("parent_student_parent_id", None)
        return ConversationHandler.END
    except ValueError as exc:
        await update.message.reply_text(
            f"Parent-student relationship could not be created: {exc}"
        )
        context.user_data.pop("parent_student_parent_id", None)
        return ConversationHandler.END
    except sqlite3.IntegrityError:
        await update.message.reply_text(
            "Parent-student relationship could not be created "
            "because the record conflicts with existing data."
        )
        context.user_data.pop("parent_student_parent_id", None)
        return ConversationHandler.END

    await update.message.reply_text(
        f"Parent-student relationship created: "
        f"parent {link.parent_id} — student {link.student_id}"
    )

    context.user_data.pop("parent_student_parent_id", None)
    return ConversationHandler.END


async def cancel_linkparentstudent(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Cancel the parent-student relationship workflow."""
    context.user_data.pop("parent_student_parent_id", None)
    await update.message.reply_text(
        "Parent-student relationship creation cancelled."
    )
    return ConversationHandler.END
