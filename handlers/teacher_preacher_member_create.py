"""Telegram CMOS Teacher/Preacher-member relationship handler."""

from telegram import Update
from telegram.ext import ConversationHandler, ContextTypes

from models.teacher_preacher_member import TeacherPreacherMemberLink


TEACHER_PREACHER_ID, MEMBERSHIP_ID = range(2)


def _clear_teacher_preacher_member_context(context):
    for key in (
        "teacher_preacher_member_teacher_preacher_id",
        "teacher_preacher_member_membership_id",
    ):
        context.user_data.pop(key, None)


async def teacher_preacher_member(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    resolver = context.application.bot_data["get_administration_context"]
    administration_context = resolver(update, context)

    if administration_context is None:
        await update.message.reply_text(
            "Access denied: unable to resolve an authorized administration context."
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "Enter the Teacher/Preacher capacity ID for this member relationship:"
    )
    return TEACHER_PREACHER_ID


async def teacher_preacher_member_teacher_preacher_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    value = update.message.text.strip()

    try:
        teacher_preacher_id = int(value)
    except ValueError:
        await update.message.reply_text(
            "Invalid Teacher/Preacher capacity ID. Enter an integer:"
        )
        return TEACHER_PREACHER_ID

    if teacher_preacher_id <= 0:
        await update.message.reply_text(
            "Teacher/Preacher capacity ID must be a positive integer. Enter the ID:"
        )
        return TEACHER_PREACHER_ID

    context.user_data[
        "teacher_preacher_member_teacher_preacher_id"
    ] = teacher_preacher_id

    await update.message.reply_text(
        "Enter the membership ID for this Teacher/Preacher-member relationship:"
    )
    return MEMBERSHIP_ID


async def teacher_preacher_member_membership_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    value = update.message.text.strip()

    try:
        membership_id = int(value)
    except ValueError:
        await update.message.reply_text(
            "Invalid membership ID. Enter an integer:"
        )
        return MEMBERSHIP_ID

    if membership_id <= 0:
        await update.message.reply_text(
            "Membership ID must be a positive integer. Enter the ID:"
        )
        return MEMBERSHIP_ID

    teacher_preacher_id = context.user_data.get(
        "teacher_preacher_member_teacher_preacher_id"
    )

    if teacher_preacher_id is None:
        _clear_teacher_preacher_member_context(context)
        await update.message.reply_text(
            "Teacher/Preacher-member relationship session expired. "
            "Please use /teacher_preacher_member again."
        )
        return ConversationHandler.END

    resolver = context.application.bot_data["get_administration_context"]
    administration_context = resolver(update, context)

    if administration_context is None:
        _clear_teacher_preacher_member_context(context)
        await update.message.reply_text(
            "Access denied: unable to resolve an authorized administration context."
        )
        return ConversationHandler.END

    services = context.application.bot_data["services"]

    member_service = services.teacher_preacher_member(
        administration_context.tenant_id,
        user_id=administration_context.user_id,
    )

    link = TeacherPreacherMemberLink(
        tenant_id=administration_context.tenant_id,
        teacher_preacher_id=teacher_preacher_id,
        membership_id=membership_id,
    )

    try:
        record = member_service.create(link)
    except PermissionError:
        _clear_teacher_preacher_member_context(context)
        await update.message.reply_text(
            "Access denied: teacher_preacher_member.write "
            "permission is required."
        )
        return ConversationHandler.END
    except ValueError as exc:
        _clear_teacher_preacher_member_context(context)
        await update.message.reply_text(
            f"Teacher/Preacher-member relationship could not be created: {exc}"
        )
        return ConversationHandler.END
    except Exception:
        _clear_teacher_preacher_member_context(context)
        await update.message.reply_text(
            "Teacher/Preacher-member relationship could not be created "
            "because the record conflicts with existing data."
        )
        return ConversationHandler.END

    _clear_teacher_preacher_member_context(context)

    await update.message.reply_text(
        "Teacher/Preacher-member relationship created: "
        f"Teacher/Preacher {record.teacher_preacher_id} — "
        f"member {record.membership_id}"
    )
    return ConversationHandler.END


async def cancel_teacher_preacher_member(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    _clear_teacher_preacher_member_context(context)

    await update.message.reply_text(
        "Teacher/Preacher-member relationship cancelled."
    )
    return ConversationHandler.END
