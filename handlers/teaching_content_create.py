"""Telegram CMOS teaching-content creation handler."""

from telegram import Update
from telegram.ext import ConversationHandler, ContextTypes

from models.teaching_content import TeachingContent


TEACHING_FOCUS_ID, NAME, DESCRIPTION, SEQUENCE, STATUS = range(5)


def _clear_content_context(context):
    for key in (
        "teaching_content_focus_id",
        "teaching_content_name",
        "teaching_content_description",
        "teaching_content_sequence",
    ):
        context.user_data.pop(key, None)


async def teaching_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    resolver = context.application.bot_data["get_administration_context"]
    administration_context = resolver(update, context)

    if administration_context is None:
        await update.message.reply_text(
            "Access denied: unable to resolve an authorized administration context."
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "Enter the teaching focus ID for this content:"
    )
    return TEACHING_FOCUS_ID


async def teaching_content_focus_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    value = update.message.text.strip()

    try:
        focus_id = int(value)
    except ValueError:
        await update.message.reply_text(
            "Invalid teaching focus ID. Enter an integer:"
        )
        return TEACHING_FOCUS_ID

    if focus_id <= 0:
        await update.message.reply_text(
            "Teaching focus ID must be a positive integer. Enter the ID:"
        )
        return TEACHING_FOCUS_ID

    context.user_data["teaching_content_focus_id"] = focus_id

    await update.message.reply_text("Enter the teaching content name:")
    return NAME


async def teaching_content_name(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    value = update.message.text.strip()

    if not value:
        await update.message.reply_text(
            "Teaching content name cannot be blank. Enter the teaching content name:"
        )
        return NAME

    context.user_data["teaching_content_name"] = value

    await update.message.reply_text(
        "Enter the teaching content description, or - for none:"
    )
    return DESCRIPTION


async def teaching_content_description(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    value = update.message.text.strip()

    context.user_data["teaching_content_description"] = (
        None if value == "-" else value
    )

    await update.message.reply_text(
        "Enter the teaching content sequence number, or - for none:"
    )
    return SEQUENCE


async def teaching_content_sequence(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    value = update.message.text.strip()

    if value == "-":
        sequence = None
    else:
        try:
            sequence = int(value)
        except ValueError:
            await update.message.reply_text(
                "Invalid sequence. Enter an integer or - for none:"
            )
            return SEQUENCE

    context.user_data["teaching_content_sequence"] = sequence

    await update.message.reply_text(
        "Enter the teaching content status (active/inactive):"
    )
    return STATUS


async def teaching_content_status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    value = update.message.text.strip().lower()

    if value not in {"active", "inactive"}:
        await update.message.reply_text(
            "Invalid status. Enter active or inactive:"
        )
        return STATUS

    focus_id = context.user_data.get("teaching_content_focus_id")
    name = context.user_data.get("teaching_content_name")
    description = context.user_data.get("teaching_content_description")
    sequence = context.user_data.get("teaching_content_sequence")

    if focus_id is None or not name:
        _clear_content_context(context)
        await update.message.reply_text(
            "Teaching content creation session expired. "
            "Please use /teaching_content again."
        )
        return ConversationHandler.END

    resolver = context.application.bot_data["get_administration_context"]
    administration_context = resolver(update, context)

    if administration_context is None:
        _clear_content_context(context)
        await update.message.reply_text(
            "Access denied: unable to resolve an authorized administration context."
        )
        return ConversationHandler.END

    services = context.application.bot_data["services"]
    content_service = services.teaching_content(
        administration_context.tenant_id,
        user_id=administration_context.user_id,
    )

    content = TeachingContent(
        id=None,
        tenant_id=administration_context.tenant_id,
        teaching_focus_id=focus_id,
        name=name,
        description=description,
        sequence=sequence,
        status=value,
    )

    try:
        record = content_service.create(content)
    except PermissionError:
        _clear_content_context(context)
        await update.message.reply_text(
            "Access denied: teaching_content.write permission is required."
        )
        return ConversationHandler.END
    except ValueError as exc:
        _clear_content_context(context)
        await update.message.reply_text(
            f"Teaching content could not be created: {exc}"
        )
        return ConversationHandler.END
    except Exception:
        _clear_content_context(context)
        await update.message.reply_text(
            "Teaching content could not be created because the record "
            "conflicts with existing data."
        )
        return ConversationHandler.END

    _clear_content_context(context)

    await update.message.reply_text(
        f"Teaching content created: {record.name} ({record.status})"
    )
    return ConversationHandler.END


async def cancel_teaching_content(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    _clear_content_context(context)
    await update.message.reply_text("Teaching content creation cancelled.")
    return ConversationHandler.END
