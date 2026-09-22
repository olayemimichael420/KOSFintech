"""Telegram CMOS church-activity participation handler."""

from telegram import Update
from telegram.ext import ConversationHandler, ContextTypes

from models.church_activity_participation import ChurchActivityParticipation


CHURCH_ACTIVITY_ID, MEMBERSHIP_ID = range(2)


def _clear_church_activity_participation_context(context):
    for key in (
        "church_activity_participation_activity_id",
        "church_activity_participation_membership_id",
    ):
        context.user_data.pop(key, None)


async def church_activity_participation(
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
        "Enter the church activity ID for this participation:"
    )
    return CHURCH_ACTIVITY_ID


async def church_activity_participation_activity_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    value = update.message.text.strip()

    try:
        church_activity_id = int(value)
    except ValueError:
        await update.message.reply_text(
            "Invalid church activity ID. Enter an integer:"
        )
        return CHURCH_ACTIVITY_ID

    if church_activity_id <= 0:
        await update.message.reply_text(
            "Church activity ID must be a positive integer. Enter the ID:"
        )
        return CHURCH_ACTIVITY_ID

    context.user_data[
        "church_activity_participation_activity_id"
    ] = church_activity_id

    await update.message.reply_text(
        "Enter the membership ID to record as participating in this church activity:"
    )
    return MEMBERSHIP_ID


async def church_activity_participation_membership_id(
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

    church_activity_id = context.user_data.get(
        "church_activity_participation_activity_id"
    )

    if church_activity_id is None:
        _clear_church_activity_participation_context(context)
        await update.message.reply_text(
            "Church activity participation session expired. "
            "Please use /church_activity_participation again."
        )
        return ConversationHandler.END

    resolver = context.application.bot_data["get_administration_context"]
    administration_context = resolver(update, context)

    if administration_context is None:
        _clear_church_activity_participation_context(context)
        await update.message.reply_text(
            "Access denied: unable to resolve an authorized administration context."
        )
        return ConversationHandler.END

    services = context.application.bot_data["services"]
    participation_service = services.church_activity_participation(
        administration_context.tenant_id,
        user_id=administration_context.user_id,
    )

    participation = ChurchActivityParticipation(
        tenant_id=administration_context.tenant_id,
        church_activity_id=church_activity_id,
        membership_id=membership_id,
    )

    try:
        record = participation_service.create(participation)
    except PermissionError:
        _clear_church_activity_participation_context(context)
        await update.message.reply_text(
            "Access denied: church_activity_participation.write "
            "permission is required."
        )
        return ConversationHandler.END
    except ValueError as exc:
        _clear_church_activity_participation_context(context)
        await update.message.reply_text(
            f"Church activity participation could not be created: {exc}"
        )
        return ConversationHandler.END
    except Exception:
        _clear_church_activity_participation_context(context)
        await update.message.reply_text(
            "Church activity participation could not be created "
            "because the record conflicts with existing data."
        )
        return ConversationHandler.END

    _clear_church_activity_participation_context(context)
    await update.message.reply_text(
        "Church activity participation recorded: "
        f"activity {record.church_activity_id} — "
        f"member {record.membership_id}"
    )
    return ConversationHandler.END


async def cancel_church_activity_participation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    _clear_church_activity_participation_context(context)
    await update.message.reply_text(
        "Church activity participation cancelled."
    )
    return ConversationHandler.END
