"""Telegram CMOS teaching-series creation handler."""

from datetime import date

from telegram import Update
from telegram.ext import ConversationHandler, ContextTypes

from models.teaching_series import TeachingSeries


TEACHING_SESSION_ID, NAME, START_DATE, END_DATE, STATUS = range(5)


def _clear_series_context(context):
    for key in (
        "teaching_series_session_id",
        "teaching_series_name",
        "teaching_series_start_date",
        "teaching_series_end_date",
    ):
        context.user_data.pop(key, None)


async def teaching_series(update: Update, context: ContextTypes.DEFAULT_TYPE):
    resolver = context.application.bot_data["get_administration_context"]
    administration_context = resolver(update, context)

    if administration_context is None:
        await update.message.reply_text(
            "Access denied: unable to resolve an authorized administration context."
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "Enter the teaching session ID for this series:"
    )
    return TEACHING_SESSION_ID


async def teaching_series_session_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    value = update.message.text.strip()

    try:
        session_id = int(value)
    except ValueError:
        await update.message.reply_text(
            "Invalid teaching session ID. Enter an integer:"
        )
        return TEACHING_SESSION_ID

    if session_id <= 0:
        await update.message.reply_text(
            "Teaching session ID must be a positive integer. Enter the ID:"
        )
        return TEACHING_SESSION_ID

    context.user_data["teaching_series_session_id"] = session_id

    await update.message.reply_text("Enter the teaching series name:")
    return NAME


async def teaching_series_name(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    value = update.message.text.strip()

    if not value:
        await update.message.reply_text(
            "Teaching series name cannot be blank. Enter the teaching series name:"
        )
        return NAME

    context.user_data["teaching_series_name"] = value

    await update.message.reply_text(
        "Enter the teaching series start date (YYYY-MM-DD):"
    )
    return START_DATE


async def teaching_series_start_date(
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

    context.user_data["teaching_series_start_date"] = parsed_date.isoformat()

    await update.message.reply_text(
        "Enter the teaching series end date (YYYY-MM-DD):"
    )
    return END_DATE


async def teaching_series_end_date(
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

    if "teaching_series_session_id" not in context.user_data:
        _clear_series_context(context)
        await update.message.reply_text(
            "Teaching series creation session expired. "
            "Please use /teaching_series again."
        )
        return ConversationHandler.END

    context.user_data["teaching_series_end_date"] = parsed_date.isoformat()

    await update.message.reply_text(
        "Enter the teaching series status (active/inactive):"
    )
    return STATUS


async def teaching_series_status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    value = update.message.text.strip().lower()

    if value not in {"active", "inactive"}:
        await update.message.reply_text(
            "Invalid status. Enter active or inactive:"
        )
        return STATUS

    session_id = context.user_data.get("teaching_series_session_id")
    name = context.user_data.get("teaching_series_name")
    start_date = context.user_data.get("teaching_series_start_date")
    end_date = context.user_data.get("teaching_series_end_date")

    if session_id is None or not name or not start_date or not end_date:
        _clear_series_context(context)
        await update.message.reply_text(
            "Teaching series creation session expired. "
            "Please use /teaching_series again."
        )
        return ConversationHandler.END

    resolver = context.application.bot_data["get_administration_context"]
    administration_context = resolver(update, context)

    if administration_context is None:
        _clear_series_context(context)
        await update.message.reply_text(
            "Access denied: unable to resolve an authorized administration context."
        )
        return ConversationHandler.END

    services = context.application.bot_data["services"]
    series_service = services.teaching_series(
        administration_context.tenant_id,
        user_id=administration_context.user_id,
    )

    series = TeachingSeries(
        id=None,
        tenant_id=administration_context.tenant_id,
        teaching_session_id=session_id,
        name=name,
        start_date=start_date,
        end_date=end_date,
        status=value,
    )

    try:
        record = series_service.create(series)
    except PermissionError:
        _clear_series_context(context)
        await update.message.reply_text(
            "Access denied: teaching_series.write permission is required."
        )
        return ConversationHandler.END
    except ValueError as exc:
        _clear_series_context(context)
        await update.message.reply_text(
            f"Teaching series could not be created: {exc}"
        )
        return ConversationHandler.END
    except Exception:
        _clear_series_context(context)
        await update.message.reply_text(
            "Teaching series could not be created because the record "
            "conflicts with existing data."
        )
        return ConversationHandler.END

    _clear_series_context(context)

    await update.message.reply_text(
        f"Teaching series created: {record.name} — "
        f"{record.start_date} to {record.end_date} ({record.status})"
    )
    return ConversationHandler.END


async def cancel_teaching_series(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    _clear_series_context(context)
    await update.message.reply_text("Teaching series creation cancelled.")
    return ConversationHandler.END
