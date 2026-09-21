"""Telegram CMOS teaching-subject creation handler."""

from telegram import Update
from telegram.ext import ConversationHandler, ContextTypes

from models.teaching_subject import TeachingSubject


NAME, STATUS = range(2)


def _clear_subject_context(context):
    for key in (
        "teaching_subject_name",
        "teaching_subject_status",
    ):
        context.user_data.pop(key, None)


async def teaching_subject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    resolver = context.application.bot_data["get_administration_context"]
    administration_context = resolver(update, context)

    if administration_context is None:
        await update.message.reply_text(
            "Access denied: unable to resolve an authorized administration context."
        )
        return ConversationHandler.END

    await update.message.reply_text("Enter the teaching subject name:")
    return NAME


async def teaching_subject_name(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    value = update.message.text.strip()

    if not value:
        await update.message.reply_text(
            "Teaching subject name cannot be blank. Enter the teaching subject name:"
        )
        return NAME

    context.user_data["teaching_subject_name"] = value

    await update.message.reply_text(
        "Enter the teaching subject status (active/inactive):"
    )
    return STATUS


async def teaching_subject_status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    value = update.message.text.strip().lower()

    if value not in {"active", "inactive"}:
        await update.message.reply_text(
            "Invalid status. Enter active or inactive:"
        )
        return STATUS

    name = context.user_data.get("teaching_subject_name")

    if not name:
        _clear_subject_context(context)
        await update.message.reply_text(
            "Teaching subject creation session expired. "
            "Please use /teaching_subject again."
        )
        return ConversationHandler.END

    resolver = context.application.bot_data["get_administration_context"]
    administration_context = resolver(update, context)

    if administration_context is None:
        _clear_subject_context(context)
        await update.message.reply_text(
            "Access denied: unable to resolve an authorized administration context."
        )
        return ConversationHandler.END

    services = context.application.bot_data["services"]
    subject_service = services.teaching_subject(
        administration_context.tenant_id,
        user_id=administration_context.user_id,
    )

    subject = TeachingSubject(
        id=None,
        tenant_id=administration_context.tenant_id,
        name=name,
        status=value,
    )

    try:
        record = subject_service.create(subject)
    except PermissionError:
        _clear_subject_context(context)
        await update.message.reply_text(
            "Access denied: teaching_subject.write permission is required."
        )
        return ConversationHandler.END
    except ValueError as exc:
        _clear_subject_context(context)
        await update.message.reply_text(
            f"Teaching subject could not be created: {exc}"
        )
        return ConversationHandler.END
    except Exception:
        _clear_subject_context(context)
        await update.message.reply_text(
            "Teaching subject could not be created because the record "
            "conflicts with existing data."
        )
        return ConversationHandler.END

    _clear_subject_context(context)

    await update.message.reply_text(
        f"Teaching subject created: {record.name} ({record.status})"
    )
    return ConversationHandler.END


async def cancel_teaching_subject(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    _clear_subject_context(context)
    await update.message.reply_text("Teaching subject creation cancelled.")
    return ConversationHandler.END
