"""Telegram CMOS teaching-focus creation handler."""

from datetime import date

from telegram import Update
from telegram.ext import ConversationHandler, ContextTypes

from models.teaching_focus import TeachingFocus


TEACHING_SERIES_ID, NAME, START_DATE, END_DATE, STATUS = range(5)


def _clear_focus_context(context):
    for key in (
        "teaching_focus_series_id",
        "teaching_focus_name",
        "teaching_focus_start_date",
        "teaching_focus_end_date",
    ):
        context.user_data.pop(key, None)


async def teaching_focus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    resolver = context.application.bot_data["get_administration_context"]
    administration_context = resolver(update, context)

    if administration_context is None:
        await update.message.reply_text(
            "Access denied: unable to resolve an authorized administration context."
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "Enter the teaching series ID for this focus:"
    )
    return TEACHING_SERIES_ID


async def teaching_focus_series_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    value = update.message.text.strip()

    try:
        series_id = int(value)
    except ValueError:
        await update.message.reply_text(
            "Invalid teaching series ID. Enter an integer:"
        )
        return TEACHING_SERIES_ID

    if series_id <= 0:
        await update.message.reply_text(
            "Teaching series ID must be a positive integer. Enter the ID:"
        )
        return TEACHING_SERIES_ID

    context.user_data["teaching_focus_series_id"] = series_id

    await update.message.reply_text("Enter the teaching focus name:")
    return NAME


async def teaching_focus_name(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    value = update.message.text.strip()

    if not value:
        await update.message.reply_text(
            "Teaching focus name cannot be blank. Enter the teaching focus name:"
        )
        return NAME

    context.user_data["teaching_focus_name"] = value

    await update.message.reply_text(
        "Enter the teaching focus start date (YYYY-MM-DD):"
    )
    return START_DATE


async def teaching_focus_start_date(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    value = update.message.text.strip()

    try:
        parsed_date = date.fromisoformat(value)
    except ValueError:
        await update.message.reply_text(
            "Invalid date. Use YYYY-MM-DD:"
        )
        return START_DATE

    context.user_data["teaching_focus_start_date"] = parsed_date.isoformat()

    await update.message.reply_text(
        "Enter the teaching focus end date (YYYY-MM-DD):"
    )
    return END_DATE


async def teaching_focus_end_date(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    value = update.message.text.strip()

    try:
        parsed_date = date.fromisoformat(value)
    except ValueError:
        await update.message.reply_text(
            "Invalid date. Use YYYY-MM-DD:"
        )
        return END_DATE

    if "teaching_focus_series_id" not in context.user_data:
        _clear_focus_context(context)
        await update.message.reply_text(
            "Teaching focus creation session expired. "
            "Please use /teaching_focus again."
        )
        return ConversationHandler.END

    context.user_data["teaching_focus_end_date"] = parsed_date.isoformat()

    await update.message.reply_text(
        "Enter the teaching focus status (active/inactive):"
    )
    return STATUS


async def teaching_focus_status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    value = update.message.text.strip().lower()

    if value not in {"active", "inactive"}:
        await update.message.reply_text(
            "Invalid status. Enter active or inactive:"
        )
        return STATUS

    series_id = context.user_data.get("teaching_focus_series_id")
    name = context.user_data.get("teaching_focus_name")
    start_date = context.user_data.get("teaching_focus_start_date")
    end_date = context.user_data.get("teaching_focus_end_date")

    if series_id is None or not name or not start_date or not end_date:
        _clear_focus_context(context)
        await update.message.reply_text(
            "Teaching focus creation session expired. "
            "Please use /teaching_focus again."
        )
        return ConversationHandler.END

    resolver = context.application.bot_data["get_administration_context"]
    administration_context = resolver(update, context)

    if administration_context is None:
        _clear_focus_context(context)
        await update.message.reply_text(
            "Access denied: unable to resolve an authorized administration context."
        )
        return ConversationHandler.END

    services = context.application.bot_data["services"]
    focus_service = services.teaching_focus(
        administration_context.tenant_id,
        user_id=administration_context.user_id,
    )

    focus = TeachingFocus(
        id=None,
        tenant_id=administration_context.tenant_id,
        teaching_series_id=series_id,
        name=name,
        start_date=start_date,
        end_date=end_date,
        status=value,
    )

    try:
        record = focus_service.create(focus)
    except PermissionError:
        _clear_focus_context(context)
        await update.message.reply_text(
            "Access denied: teaching_focus.write permission is required."
        )
        return ConversationHandler.END
    except ValueError as exc:
        _clear_focus_context(context)
        await update.message.reply_text(
            f"Teaching focus could not be created: {exc}"
        )
        return ConversationHandler.END
    except Exception:
        _clear_focus_context(context)
        await update.message.reply_text(
            "Teaching focus could not be created because the record "
            "conflicts with existing data."
        )
        return ConversationHandler.END

    _clear_focus_context(context)

    await update.message.reply_text(
        f"Teaching focus created: {record.name} — "
        f"{record.start_date} to {record.end_date} ({record.status})"
    )
    return ConversationHandler.END


async def cancel_teaching_focus(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    _clear_focus_context(context)
    await update.message.reply_text("Teaching focus creation cancelled.")
    return ConversationHandler.END
