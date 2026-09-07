"""Telegram student write handlers."""

from telegram import Update
from telegram.ext import ConversationHandler, ContextTypes

from models.student import Student

NAME, CLASS_NAME = range(2)

async def addstudent(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the student creation conversation."""
    resolver = context.application.bot_data["get_administration_context"]
    administration_context = resolver(update, context)

    if administration_context is None:
        await update.message.reply_text(
            "Access denied: unable to resolve an authorized administration context."
        )
        return ConversationHandler.END

    await update.message.reply_text("Enter the student's full name:")
    return NAME


async def student_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Capture the student's name."""
    name = update.message.text.strip()

    if not name:
        await update.message.reply_text("Student name cannot be empty. Enter the student's full name:")
        return NAME

    context.user_data["student_name"] = name

    await update.message.reply_text("Enter the student's class:")
    return CLASS_NAME


async def student_class(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Capture the student's class and create the student."""
    class_name = update.message.text.strip()

    if not class_name:
        await update.message.reply_text(
            "Class cannot be empty. Enter the student's class:"
        )
        return CLASS_NAME

    name = context.user_data.get("student_name")

    if not name:
        await update.message.reply_text(
            "Student creation session expired. Please use /addstudent again."
        )
        context.user_data.pop("student_name", None)
        return ConversationHandler.END

    resolver = context.application.bot_data["get_administration_context"]
    administration_context = resolver(update, context)

    if administration_context is None:
        await update.message.reply_text(
            "Access denied: unable to resolve an authorized administration context."
        )
        context.user_data.pop("student_name", None)
        return ConversationHandler.END

    services = context.application.bot_data["services"]
    student_service = services.student(
        administration_context.tenant_id,
        user_id=administration_context.user_id,
    )

    try:
        student = Student(
            id=None,
            tenant_id=administration_context.tenant_id,
            user_id=None,
            name=name,
            class_name=class_name,
            age=None,
            guardian_id=None,
            enrollment_date=None,
        )
        created = student_service.create(student)
    except PermissionError:
        await update.message.reply_text(
            "Access denied: student.write permission is required."
        )
        context.user_data.pop("student_name", None)
        return ConversationHandler.END

    await update.message.reply_text(
        f"Student created: {created.name} — {created.class_name} — ID {created.id}"
    )

    context.user_data.pop("student_name", None)
    return ConversationHandler.END
