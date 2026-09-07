"""Telegram attendance recording handlers."""

from datetime import date
from types import SimpleNamespace

from telegram import Update
from telegram.ext import ConversationHandler, ContextTypes

from models.attendance import Attendance


STUDENT_ID, ATTENDANCE_DATE, STATUS, REMARK = range(4)

ALLOWED_STATUSES = {
    "present",
    "absent",
    "late",
    "excused",
}


def _end_session(context) -> None:
    for key in (
        "attendance_student_id",
        "attendance_date",
        "attendance_status",
    ):
        context.user_data.pop(key, None)


async def attendance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the attendance recording conversation."""
    resolver = context.application.bot_data["get_administration_context"]
    administration_context = resolver(update, context)

    if administration_context is None:
        await update.message.reply_text(
            "Access denied: unable to resolve an authorized administration context."
        )
        return ConversationHandler.END

    await update.message.reply_text("Enter the student ID:")
    return STUDENT_ID


async def attendance_student_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Capture and validate the student ID."""
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

    context.user_data["attendance_student_id"] = student_id
    await update.message.reply_text("Enter the attendance date (YYYY-MM-DD):")
    return ATTENDANCE_DATE


async def attendance_date(
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

    context.user_data["attendance_date"] = parsed_date.isoformat()
    await update.message.reply_text(
        "Enter attendance status: present, absent, late, or excused:"
    )
    return STATUS


async def attendance_status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Capture and validate the attendance status."""
    value = update.message.text.strip().lower()

    if value not in ALLOWED_STATUSES:
        await update.message.reply_text(
            "Invalid status. Enter present, absent, late, or excused:"
        )
        return STATUS

    context.user_data["attendance_status"] = value
    await update.message.reply_text(
        "Enter an optional remark, or type none:"
    )
    return REMARK


async def attendance_remark(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Create the attendance record."""
    remark = update.message.text.strip()

    if remark.lower() == "none":
        remark = None

    student_id = context.user_data.get("attendance_student_id")
    attendance_date_value = context.user_data.get("attendance_date")
    status = context.user_data.get("attendance_status")

    if not student_id or not attendance_date_value or not status:
        await update.message.reply_text(
            "Attendance recording session expired. Please use /attendance again."
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
    attendance_service = services.attendance(
        administration_context.tenant_id,
        user_id=administration_context.user_id,
    )

    try:
        record = attendance_service.record(
            Attendance(
                id=None,
                tenant_id=administration_context.tenant_id,
                student_id=student_id,
                attendance_date=attendance_date_value,
                status=status,
                remark=remark,
            )
        )
    except PermissionError:
        await update.message.reply_text(
            "Access denied: attendance.write permission is required."
        )
        _end_session(context)
        return ConversationHandler.END
    except ValueError as exc:
        await update.message.reply_text(
            f"Attendance could not be recorded: {exc}"
        )
        _end_session(context)
        return ConversationHandler.END
    except Exception:
        await update.message.reply_text(
            "Attendance could not be recorded because the record conflicts with existing data."
        )
        _end_session(context)
        return ConversationHandler.END

    await update.message.reply_text(
        f"Attendance recorded: student {record.student_id} — "
        f"{record.attendance_date} — {record.status}"
    )

    _end_session(context)
    return ConversationHandler.END


async def cancel_attendance(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Cancel the attendance recording conversation."""
    _end_session(context)
    await update.message.reply_text("Attendance recording cancelled.")
    return ConversationHandler.END
