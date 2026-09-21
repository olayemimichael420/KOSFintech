"""Telegram CMOS teaching-session member/enrollment handler."""

from telegram import Update
from telegram.ext import ConversationHandler, ContextTypes

from models.teaching_session_member import TeachingSessionMemberLink


TEACHING_SESSION_ID, MEMBERSHIP_ID = range(2)


def _clear_teaching_session_member_context(context):
    for key in (
        "teaching_session_member_session_id",
        "teaching_session_member_membership_id",
    ):
        context.user_data.pop(key, None)


async def teaching_session_member(
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
        "Enter the teaching session ID for this member enrollment:"
    )
    return TEACHING_SESSION_ID


async def teaching_session_member_session_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    value = update.message.text.strip()

    try:
        teaching_session_id = int(value)
    except ValueError:
        await update.message.reply_text(
            "Invalid teaching session ID. Enter an integer:"
        )
        return TEACHING_SESSION_ID

    if teaching_session_id <= 0:
        await update.message.reply_text(
            "Teaching session ID must be a positive integer. Enter the ID:"
        )
        return TEACHING_SESSION_ID

    context.user_data["teaching_session_member_session_id"] = teaching_session_id

    await update.message.reply_text(
        "Enter the membership ID to enroll in this teaching session:"
    )
    return MEMBERSHIP_ID


async def teaching_session_member_membership_id(
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

    teaching_session_id = context.user_data.get(
        "teaching_session_member_session_id"
    )

    if teaching_session_id is None:
        _clear_teaching_session_member_context(context)
        await update.message.reply_text(
            "Teaching session member enrollment session expired. "
            "Please use /teaching_session_member again."
        )
        return ConversationHandler.END

    resolver = context.application.bot_data["get_administration_context"]
    administration_context = resolver(update, context)

    if administration_context is None:
        _clear_teaching_session_member_context(context)
        await update.message.reply_text(
            "Access denied: unable to resolve an authorized administration context."
        )
        return ConversationHandler.END

    services = context.application.bot_data["services"]
    member_service = services.teaching_session_member(
        administration_context.tenant_id,
        user_id=administration_context.user_id,
    )

    link = TeachingSessionMemberLink(
        tenant_id=administration_context.tenant_id,
        teaching_session_id=teaching_session_id,
        membership_id=membership_id,
    )

    try:
        record = member_service.create(link)
    except PermissionError:
        _clear_teaching_session_member_context(context)
        await update.message.reply_text(
            "Access denied: teaching_session_member.write "
            "permission is required."
        )
        return ConversationHandler.END
    except ValueError as exc:
        _clear_teaching_session_member_context(context)
        await update.message.reply_text(
            f"Teaching session member enrollment could not be created: {exc}"
        )
        return ConversationHandler.END
    except Exception:
        _clear_teaching_session_member_context(context)
        await update.message.reply_text(
            "Teaching session member enrollment could not be created "
            "because the record conflicts with existing data."
        )
        return ConversationHandler.END

    _clear_teaching_session_member_context(context)

    await update.message.reply_text(
        "Teaching session member enrollment created: "
        f"session {record.teaching_session_id} — "
        f"member {record.membership_id}"
    )
    return ConversationHandler.END


async def cancel_teaching_session_member(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    _clear_teaching_session_member_context(context)
    await update.message.reply_text(
        "Teaching session member enrollment cancelled."
    )
    return ConversationHandler.END
