"""Telegram CMOS teaching-session attendance recording handler."""

from datetime import date

from telegram import Update
from telegram.ext import ConversationHandler, ContextTypes

from models.teaching_session_attendance import TeachingSessionAttendance


TEACHING_SESSION_ID, MEMBERSHIP_ID, ATTENDANCE_DATE, STATUS = range(4)

ALLOWED_STATUSES = {
    "present",
    "absent",
    "late",
    "excused",
}


def _end_session(context) -> None:
    for key in (
        "teaching_session_attendance_session_id",
        "teaching_session_attendance_membership_id",
        "teaching_session_attendance_date",
        "teaching_session_attendance_status",
    ):
        context.user_data.pop(key, None)


async def teaching_attendance(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Start the CMOS teaching-session attendance conversation."""
    resolver = context.application.bot_data["get_administration_context"]
    administration_context = resolver(update, context)

    if administration_context is None:
        await update.message.reply_text(
            "Access denied: unable to resolve an authorized administration context."
        )
        return ConversationHandler.END

    await update.message.reply_text("Enter the teaching session ID:")
    return TEACHING_SESSION_ID


async def teaching_attendance_session_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Capture and validate the teaching session ID."""
    value = update.message.text.strip()

    try:
        session_id = int(value)
    except ValueError:
        await update.message.reply_text(
            "Teaching session ID must be a number. Enter the teaching session ID:"
        )
        return TEACHING_SESSION_ID

    if session_id <= 0:
        await update.message.reply_text(
            "Teaching session ID must be greater than zero. Enter the teaching session ID:"
        )
        return TEACHING_SESSION_ID

    context.user_data["teaching_session_attendance_session_id"] = session_id
    await update.message.reply_text("Enter the membership ID:")
    return MEMBERSHIP_ID


async def teaching_attendance_membership_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Capture and validate the membership ID."""
    value = update.message.text.strip()

    try:
        membership_id = int(value)
    except ValueError:
        await update.message.reply_text(
            "Membership ID must be a number. Enter the membership ID:"
        )
        return MEMBERSHIP_ID

    if membership_id <= 0:
        await update.message.reply_text(
            "Membership ID must be greater than zero. Enter the membership ID:"
        )
        return MEMBERSHIP_ID

    context.user_data["teaching_session_attendance_membership_id"] = membership_id
    await update.message.reply_text("Enter the attendance date (YYYY-MM-DD):")
    return ATTENDANCE_DATE


async def teaching_attendance_date(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Capture and validate the attendance date."""
    value = update.message.text.strip()

    try:
        parsed_date = date.fromisoformat(value)
    except ValueError:
        await update.message.reply_text(
            "Invalid date. Use YYYY-MM-DD:"
        )
        return ATTENDANCE_DATE

    context.user_data["teaching_session_attendance_date"] = parsed_date.isoformat()
    await update.message.reply_text(
        "Enter attendance status: present, absent, late, or excused:"
    )
    return STATUS


async def teaching_attendance_status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Capture and validate the attendance status and record attendance."""
    value = update.message.text.strip().lower()

    if value not in ALLOWED_STATUSES:
        await update.message.reply_text(
            "Invalid status. Enter attendance status: present, absent, late, or excused:"
        )
        return STATUS

    session_id = context.user_data.get(
        "teaching_session_attendance_session_id"
    )
    membership_id = context.user_data.get(
        "teaching_session_attendance_membership_id"
    )
    attendance_date = context.user_data.get(
        "teaching_session_attendance_date"
    )

    if not session_id or not membership_id or not attendance_date:
        await update.message.reply_text(
            "Teaching attendance recording session expired. "
            "Please use /teaching_attendance again."
        )
        _end_session(context)
        return ConversationHandler.END

    resolver = context.application.bot_data["get_administration_context"]
    administration_context = resolver(update, context)

    if administration_context is None:
        await update.message.reply_text(
            "Access denied: unable to resolve an authorized administration context."
        )
        _end_session(context)
        return ConversationHandler.END

    services = context.application.bot_data["services"]
    attendance_service = services.teaching_session_attendance(
        administration_context.tenant_id,
        user_id=administration_context.user_id,
    )

    try:
        record = attendance_service.record(
            TeachingSessionAttendance(
                id=None,
                tenant_id=administration_context.tenant_id,
                teaching_session_id=session_id,
                membership_id=membership_id,
                attendance_date=attendance_date,
                status=value,
            )
        )
    except PermissionError:
        await update.message.reply_text(
            "Access denied: teaching_session_attendance.write permission is required."
        )
        _end_session(context)
        return ConversationHandler.END
    except ValueError as exc:
        await update.message.reply_text(
            f"Teaching attendance could not be recorded: {exc}"
        )
        _end_session(context)
        return ConversationHandler.END
    except Exception:
        await update.message.reply_text(
            "Teaching attendance could not be recorded because the record "
            "conflicts with existing data."
        )
        _end_session(context)
        return ConversationHandler.END

    await update.message.reply_text(
        f"Teaching attendance recorded: session {record.teaching_session_id} — "
        f"member {record.membership_id} — {record.attendance_date} — {record.status}"
    )

    _end_session(context)
    return ConversationHandler.END


async def cancel_teaching_attendance(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Cancel the CMOS teaching attendance conversation."""
    _end_session(context)
    await update.message.reply_text("Teaching attendance recording cancelled.")
    return ConversationHandler.END
