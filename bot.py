#!/usr/bin/env python3
"""
KOSFintech Telegram application entry point.

PART 1 intentionally keeps the Telegram entry point minimal.
Business logic will be introduced through handlers/services in
subsequent development parts.
"""

import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

import database
from config import settings
from services.application_service_factory import ApplicationServiceFactory
from services.application_services import ApplicationServices
from handlers.students import students
from handlers.teachers import teachers
from handlers.parents import parents
from handlers.student_create import addstudent, student_name, student_class, NAME, CLASS_NAME
from handlers.attendance_create import (
    attendance,
    attendance_student_id,
    attendance_date,
    attendance_status,
    attendance_remark,
    cancel_attendance,
    STUDENT_ID,
    ATTENDANCE_DATE,
    STATUS,
    REMARK,
)
from handlers.attendance_today import attendance_today
from handlers.teaching_session_attendance_create import (
    teaching_attendance,
    teaching_attendance_session_id,
    teaching_attendance_membership_id,
    teaching_attendance_date,
    teaching_attendance_status,
    cancel_teaching_attendance,
    TEACHING_SESSION_ID,
    MEMBERSHIP_ID as TEACHING_ATTENDANCE_MEMBERSHIP_ID,
    ATTENDANCE_DATE as TEACHING_ATTENDANCE_DATE,
    STATUS as TEACHING_ATTENDANCE_STATUS,
)
from handlers.learning_evidence_create import (
    learning_evidence,
    learning_evidence_membership_id,
    learning_evidence_teaching_content_id,
    learning_evidence_date,
    learning_evidence_description,
    learning_evidence_remark,
    cancel_learning_evidence,
    MEMBERSHIP_ID as LEARNING_EVIDENCE_MEMBERSHIP_ID,
    TEACHING_CONTENT_ID as LEARNING_EVIDENCE_TEACHING_CONTENT_ID,
    EVIDENCE_DATE as LEARNING_EVIDENCE_DATE,
    DESCRIPTION as LEARNING_EVIDENCE_DESCRIPTION,
    REMARK as LEARNING_EVIDENCE_REMARK,
)
from handlers.assessment_create import (
    assessment,
    assessment_teaching_content_id,
    assessment_name,
    assessment_date,
    assessment_description,
    assessment_status,
    cancel_assessment,
    TEACHING_CONTENT_ID as ASSESSMENT_TEACHING_CONTENT_ID,
    NAME as ASSESSMENT_NAME,
    ASSESSMENT_DATE as ASSESSMENT_DATE,
    DESCRIPTION as ASSESSMENT_DESCRIPTION,
    STATUS as ASSESSMENT_STATUS,
)
from handlers.grade_create import (
    grade,
    grade_name,
    grade_description,
    grade_minimum_score,
    grade_maximum_score,
    grade_status,
    cancel_grade,
    NAME as GRADE_NAME,
    DESCRIPTION as GRADE_DESCRIPTION,
    MINIMUM_SCORE as GRADE_MINIMUM_SCORE,
    MAXIMUM_SCORE as GRADE_MAXIMUM_SCORE,
    STATUS as GRADE_STATUS,
)
from handlers.result_create import (
    result,
    result_assessment_id,
    result_membership_id,
    result_grade_id,
    result_value,
    result_date,
    result_remark,
    result_status,
    cancel_result,
    ASSESSMENT_ID as RESULT_ASSESSMENT_ID,
    MEMBERSHIP_ID as RESULT_MEMBERSHIP_ID,
    GRADE_ID as RESULT_GRADE_ID,
    RESULT as RESULT_VALUE,
    RESULT_DATE as RESULT_DATE_STATE,
    REMARK as RESULT_REMARK,
    STATUS as RESULT_STATUS,
)
from handlers.teaching_subject_create import (
    teaching_subject,
    teaching_subject_name,
    teaching_subject_status,
    cancel_teaching_subject,
    NAME as TEACHING_SUBJECT_NAME,
    STATUS as TEACHING_SUBJECT_STATUS,
)
from handlers.teaching_focus_create import (
    teaching_focus,
    teaching_focus_series_id,
    teaching_focus_name,
    teaching_focus_start_date,
    teaching_focus_end_date,
    teaching_focus_status,
    cancel_teaching_focus,
    TEACHING_SERIES_ID as TEACHING_FOCUS_SERIES_ID,
    NAME as TEACHING_FOCUS_NAME,
    START_DATE as TEACHING_FOCUS_START_DATE,
    END_DATE as TEACHING_FOCUS_END_DATE,
    STATUS as TEACHING_FOCUS_STATUS,
)
from handlers.teaching_content_create import (
    teaching_content,
    teaching_content_focus_id,
    teaching_content_name,
    teaching_content_description,
    teaching_content_sequence,
    teaching_content_status,
    cancel_teaching_content,
    TEACHING_FOCUS_ID as TEACHING_CONTENT_FOCUS_ID,
    NAME as TEACHING_CONTENT_NAME,
    DESCRIPTION as TEACHING_CONTENT_DESCRIPTION,
    SEQUENCE as TEACHING_CONTENT_SEQUENCE,
    STATUS as TEACHING_CONTENT_STATUS,
)
from handlers.teaching_content_teacher_preacher_assignment_create import (
    teaching_content_teacher_preacher_assignment,
    teaching_content_assignment_content_id,
    teaching_content_assignment_teacher_preacher_id,
    teaching_content_assignment_status,
    cancel_teaching_content_teacher_preacher_assignment,
    TEACHING_CONTENT_ID as TEACHING_CONTENT_ASSIGNMENT_CONTENT_ID,
    TEACHER_PREACHER_ID as TEACHING_CONTENT_ASSIGNMENT_TEACHER_PREACHER_ID,
    STATUS as TEACHING_CONTENT_ASSIGNMENT_STATUS,
)

from handlers.teaching_series_create import (
    teaching_series,
    teaching_series_session_id,
    teaching_series_name,
    teaching_series_start_date,
    teaching_series_end_date,
    teaching_series_status,
    cancel_teaching_series,
    TEACHING_SESSION_ID as TEACHING_SERIES_SESSION_ID,
    NAME as TEACHING_SERIES_NAME,
    START_DATE as TEACHING_SERIES_START_DATE,
    END_DATE as TEACHING_SERIES_END_DATE,
    STATUS as TEACHING_SERIES_STATUS,
)
from handlers.teaching_session_create import (
    teaching_session,
    teaching_session_name,
    teaching_session_start_date,
    teaching_session_end_date,
    cancel_teaching_session,
    NAME as TEACHING_SESSION_NAME,
    START_DATE as TEACHING_SESSION_START_DATE,
    END_DATE as TEACHING_SESSION_END_DATE,
)
from handlers.teaching_session_member_create import (
    teaching_session_member,
    teaching_session_member_session_id,
    teaching_session_member_membership_id,
    cancel_teaching_session_member,
    TEACHING_SESSION_ID as TEACHING_SESSION_MEMBER_SESSION_ID,
    MEMBERSHIP_ID as TEACHING_SESSION_MEMBER_MEMBERSHIP_ID,
)
from handlers.teaching_session_subject_create import (
    teaching_session_subject,
    teaching_session_subject_session_id,
    teaching_session_subject_subject_id,
    cancel_teaching_session_subject,
    TEACHING_SESSION_ID as TEACHING_SESSION_SUBJECT_SESSION_ID,
    TEACHING_SUBJECT_ID as TEACHING_SESSION_SUBJECT_SUBJECT_ID,
)

from handlers.teacher_preacher_member_create import (
    teacher_preacher_member,
    teacher_preacher_member_teacher_preacher_id,
    teacher_preacher_member_membership_id,
    cancel_teacher_preacher_member,
    TEACHER_PREACHER_ID as TEACHER_PREACHER_MEMBER_TEACHER_PREACHER_ID,
    MEMBERSHIP_ID as TEACHER_PREACHER_MEMBER_MEMBERSHIP_ID,
)
from handlers.teacher_preacher_subject_assignment_create import (
    teacher_preacher_subject_assignment,
    teacher_preacher_subject_assignment_teacher_preacher_id,
    teacher_preacher_subject_assignment_teaching_subject_id,
    cancel_teacher_preacher_subject_assignment,
    TEACHER_PREACHER_ID as TEACHER_PREACHER_SUBJECT_ASSIGNMENT_TEACHER_PREACHER_ID,
    TEACHING_SUBJECT_ID as TEACHER_PREACHER_SUBJECT_ASSIGNMENT_TEACHING_SUBJECT_ID,
)

from handlers.progress_create import (
    progress,
    progress_membership_id,
    progress_teaching_content_id,
    progress_date,
    progress_description,
    progress_remark,
    progress_status,
    cancel_progress,
    MEMBERSHIP_ID as PROGRESS_MEMBERSHIP_ID,
    TEACHING_CONTENT_ID as PROGRESS_TEACHING_CONTENT_ID,
    PROGRESS_DATE,
    DESCRIPTION as PROGRESS_DESCRIPTION,
    REMARK as PROGRESS_REMARK,
    STATUS as PROGRESS_STATUS,
)

from handlers.assessment_score_create import (
    assessment_score,
    assessment_score_assessment_id,
    assessment_score_membership_id,
    assessment_score_value,
    assessment_score_date,
    assessment_score_remark,
    cancel_assessment_score,
    ASSESSMENT_ID as ASSESSMENT_SCORE_ASSESSMENT_ID,
    MEMBERSHIP_ID as ASSESSMENT_SCORE_MEMBERSHIP_ID,
    SCORE as ASSESSMENT_SCORE_VALUE,
    SCORED_DATE as ASSESSMENT_SCORE_DATE,
    REMARK as ASSESSMENT_SCORE_REMARK,
)
from handlers.school_student_create import (
    linkstudent,
    school_student_id,
    cancel_linkstudent,
    STUDENT_ID as SCHOOL_STUDENT_ID,
)
from handlers.teacher_student_create import (
    linkteacherstudent,
    teacher_student_teacher_id,
    teacher_student_student_id,
    cancel_linkteacherstudent,
    TEACHER_ID as TEACHER_STUDENT_TEACHER_ID,
    STUDENT_ID as TEACHER_STUDENT_STUDENT_ID,
)
from handlers.parent_student_create import (
    linkparentstudent,
    parent_student_parent_id,
    parent_student_student_id,
    cancel_linkparentstudent,
    PARENT_ID as PARENT_STUDENT_PARENT_ID,
    STUDENT_ID as PARENT_STUDENT_STUDENT_ID,
)


logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("kosfintech")


def get_authenticated_identity(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """Resolve a Telegram update to a canonical authenticated identity."""

    services = context.application.bot_data["services"]

    return services.telegram_identity.authenticate_update(update)


def get_telegram_binding(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """Resolve the current Telegram chat to its KOSFintech binding."""

    chat = getattr(update, "effective_chat", None)
    if chat is None:
        return None

    services = context.application.bot_data["services"]

    return services.telegram_channel_binding.resolve_chat(
        str(chat.id)
    )


def get_administration_context(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """Compose authenticated Telegram identity and administration context."""

    identity = get_authenticated_identity(update, context)
    if identity is None:
        return None

    binding = get_telegram_binding(update, context)
    if binding is None:
        return None

    services = context.application.bot_data["services"]

    return services.administration_context.resolve(
        user_id=identity.user_id,
        administration_id=binding.administration_id,
        tenant_id=binding.tenant_id,
    )


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Basic health/start command."""

    await update.message.reply_text(
        "🚀 KOSFintech Global Community Operations Platform\n\n"
        "Foundation layer is online.\n"
        "The modular system is being assembled incrementally.\n\n"
        "Use /health to verify the application."
    )


async def health(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Basic application health response."""

    await update.message.reply_text(
        "✅ KOSFintech application is responding.\n"
        f"Environment: {settings.app_env}"
    )


def build_application() -> Application:
    """Construct the Telegram application."""

    if not settings.bot_token:
        raise RuntimeError(
            "BOT_TOKEN is not configured. "
            "Set it in the environment or .env file."
        )

    application = (
        Application.builder()
        .token(settings.bot_token)
        .build()
    )

    # Application-scoped dependency composition.
    # The database connection is supplied to the service factory once,
    # keeping repository/service construction out of Telegram handlers.
    connection = database.get_connection()
    application.bot_data["db_connection"] = connection
    service_factory = ApplicationServiceFactory(connection)
    application.bot_data["service_factory"] = service_factory
    application.bot_data["services"] = ApplicationServices(service_factory)
    application.bot_data["get_administration_context"] = get_administration_context

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("health", health)
    )

    application.add_handler(
        CommandHandler("students", students)
    )

    application.add_handler(
        CommandHandler("teachers", teachers)
    )

    application.add_handler(
        CommandHandler("parents", parents)
    )

    application.add_handler(
        ConversationHandler(
            entry_points=[CommandHandler("addstudent", addstudent)],
            states={
                NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, student_name)
                ],
                CLASS_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, student_class)
                ],
            },
            fallbacks=[],
        )
    )
    application.add_handler(
        CommandHandler("attendance_today", attendance_today)
    )

    application.add_handler(
        ConversationHandler(
            entry_points=[
                CommandHandler("teaching_attendance", teaching_attendance)
            ],
            states={
                TEACHING_SESSION_ID: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        teaching_attendance_session_id,
                    )
                ],
                TEACHING_ATTENDANCE_MEMBERSHIP_ID: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        teaching_attendance_membership_id,
                    )
                ],
                TEACHING_ATTENDANCE_DATE: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        teaching_attendance_date,
                    )
                ],
                TEACHING_ATTENDANCE_STATUS: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        teaching_attendance_status,
                    )
                ],
            },
            fallbacks=[
                CommandHandler(
                    "cancel_teaching_attendance",
                    cancel_teaching_attendance,
                ),
            ],
        )
    )
    application.add_handler(
        ConversationHandler(
            entry_points=[
                CommandHandler("learning_evidence", learning_evidence)
            ],
            states={
                LEARNING_EVIDENCE_MEMBERSHIP_ID: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        learning_evidence_membership_id,
                    )
                ],
                LEARNING_EVIDENCE_TEACHING_CONTENT_ID: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        learning_evidence_teaching_content_id,
                    )
                ],
                LEARNING_EVIDENCE_DATE: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        learning_evidence_date,
                    )
                ],
                LEARNING_EVIDENCE_DESCRIPTION: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        learning_evidence_description,
                    )
                ],
                LEARNING_EVIDENCE_REMARK: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        learning_evidence_remark,
                    )
                ],
            },
            fallbacks=[
                CommandHandler(
                    "cancel_learning_evidence",
                    cancel_learning_evidence,
                ),
            ],
        )
    )

    application.add_handler(
        ConversationHandler(
            entry_points=[
                CommandHandler("assessment", assessment)
            ],
            states={
                ASSESSMENT_TEACHING_CONTENT_ID: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        assessment_teaching_content_id,
                    )
                ],
                ASSESSMENT_NAME: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        assessment_name,
                    )
                ],
                ASSESSMENT_DATE: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        assessment_date,
                    )
                ],
                ASSESSMENT_DESCRIPTION: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        assessment_description,
                    )
                ],
                ASSESSMENT_STATUS: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        assessment_status,
                    )
                ],
            },
            fallbacks=[
                CommandHandler(
                    "cancel_assessment",
                    cancel_assessment,
                ),
            ],
        )
    )

    application.add_handler(
        ConversationHandler(
            entry_points=[
                CommandHandler("assessment_score", assessment_score)
            ],
            states={
                ASSESSMENT_SCORE_ASSESSMENT_ID: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        assessment_score_assessment_id,
                    )
                ],
                ASSESSMENT_SCORE_MEMBERSHIP_ID: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        assessment_score_membership_id,
                    )
                ],
                ASSESSMENT_SCORE_VALUE: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        assessment_score_value,
                    )
                ],
                ASSESSMENT_SCORE_DATE: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        assessment_score_date,
                    )
                ],
                ASSESSMENT_SCORE_REMARK: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        assessment_score_remark,
                    )
                ],
            },
            fallbacks=[
                CommandHandler(
                    "cancel_assessment_score",
                    cancel_assessment_score,
                ),
            ],
        )
    )

    application.add_handler(
        ConversationHandler(
            entry_points=[
                CommandHandler("grade", grade)
            ],
            states={
                GRADE_NAME: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        grade_name,
                    )
                ],
                GRADE_DESCRIPTION: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        grade_description,
                    )
                ],
                GRADE_MINIMUM_SCORE: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        grade_minimum_score,
                    )
                ],
                GRADE_MAXIMUM_SCORE: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        grade_maximum_score,
                    )
                ],
                GRADE_STATUS: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        grade_status,
                    )
                ],
            },
            fallbacks=[
                CommandHandler(
                    "cancel_grade",
                    cancel_grade,
                ),
            ],
        )
    )

    application.add_handler(
        ConversationHandler(
            entry_points=[
                CommandHandler("result", result)
            ],
            states={
                RESULT_ASSESSMENT_ID: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        result_assessment_id,
                    )
                ],
                RESULT_MEMBERSHIP_ID: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        result_membership_id,
                    )
                ],
                RESULT_GRADE_ID: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        result_grade_id,
                    )
                ],
                RESULT_VALUE: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        result_value,
                    )
                ],
                RESULT_DATE_STATE: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        result_date,
                    )
                ],
                RESULT_REMARK: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        result_remark,
                    )
                ],
                RESULT_STATUS: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        result_status,
                    )
                ],
            },
            fallbacks=[
                CommandHandler(
                    "cancel_result",
                    cancel_result,
                ),
            ],
        )
    )

    application.add_handler(
        ConversationHandler(
            entry_points=[
                CommandHandler("teaching_focus", teaching_focus)
            ],
            states={
                TEACHING_FOCUS_SERIES_ID: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        teaching_focus_series_id,
                    )
                ],
                TEACHING_FOCUS_NAME: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        teaching_focus_name,
                    )
                ],
                TEACHING_FOCUS_START_DATE: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        teaching_focus_start_date,
                    )
                ],
                TEACHING_FOCUS_END_DATE: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        teaching_focus_end_date,
                    )
                ],
                TEACHING_FOCUS_STATUS: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        teaching_focus_status,
                    )
                ],
            },
            fallbacks=[
                CommandHandler(
                    "cancel_teaching_focus",
                    cancel_teaching_focus,
                ),
            ],
        )
    )

    application.add_handler(
        ConversationHandler(
            entry_points=[
                CommandHandler("teaching_content", teaching_content)
            ],
            states={
                TEACHING_CONTENT_FOCUS_ID: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        teaching_content_focus_id,
                    )
                ],
                TEACHING_CONTENT_NAME: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        teaching_content_name,
                    )
                ],
                TEACHING_CONTENT_DESCRIPTION: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        teaching_content_description,
                    )
                ],
                TEACHING_CONTENT_SEQUENCE: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        teaching_content_sequence,
                    )
                ],
                TEACHING_CONTENT_STATUS: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        teaching_content_status,
                    )
                ],
            },
            fallbacks=[
                CommandHandler(
                    "cancel_teaching_content",
                    cancel_teaching_content,
                ),
            ],
        )
    )

    application.add_handler(
        ConversationHandler(
            entry_points=[
                CommandHandler(
                    "content_tp_assign",
                    teaching_content_teacher_preacher_assignment,
                )
            ],
            states={
                TEACHING_CONTENT_ASSIGNMENT_CONTENT_ID: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        teaching_content_assignment_content_id,
                    )
                ],
                TEACHING_CONTENT_ASSIGNMENT_TEACHER_PREACHER_ID: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        teaching_content_assignment_teacher_preacher_id,
                    )
                ],
                TEACHING_CONTENT_ASSIGNMENT_STATUS: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        teaching_content_assignment_status,
                    )
                ],
            },
            fallbacks=[
                CommandHandler(
                    "cancel_content_tp_assign",
                    cancel_teaching_content_teacher_preacher_assignment,
                ),
            ],
        )
    )

    application.add_handler(
        ConversationHandler(
            entry_points=[
                CommandHandler("teaching_series", teaching_series)
            ],
            states={
                TEACHING_SERIES_SESSION_ID: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        teaching_series_session_id,
                    )
                ],
                TEACHING_SERIES_NAME: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        teaching_series_name,
                    )
                ],
                TEACHING_SERIES_START_DATE: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        teaching_series_start_date,
                    )
                ],
                TEACHING_SERIES_END_DATE: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        teaching_series_end_date,
                    )
                ],
                TEACHING_SERIES_STATUS: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        teaching_series_status,
                    )
                ],
            },
            fallbacks=[
                CommandHandler(
                    "cancel_teaching_series",
                    cancel_teaching_series,
                ),
            ],
        )
    )

    application.add_handler(
        ConversationHandler(
            entry_points=[
                CommandHandler("teaching_subject", teaching_subject)
            ],
            states={
                TEACHING_SUBJECT_NAME: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        teaching_subject_name,
                    )
                ],
                TEACHING_SUBJECT_STATUS: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        teaching_subject_status,
                    )
                ],
            },
            fallbacks=[
                CommandHandler(
                    "cancel_teaching_subject",
                    cancel_teaching_subject,
                ),
            ],
        )
    )

    application.add_handler(
        ConversationHandler(
            entry_points=[
                CommandHandler("teaching_session", teaching_session)
            ],
            states={
                TEACHING_SESSION_NAME: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        teaching_session_name,
                    )
                ],
                TEACHING_SESSION_START_DATE: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        teaching_session_start_date,
                    )
                ],
                TEACHING_SESSION_END_DATE: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        teaching_session_end_date,
                    )
                ],
            },
            fallbacks=[
                CommandHandler(
                    "cancel_teaching_session",
                    cancel_teaching_session,
                ),
            ],
        )
    )

    application.add_handler(
        ConversationHandler(
            entry_points=[
                CommandHandler(
                    "teaching_session_member",
                    teaching_session_member,
                )
            ],
            states={
                TEACHING_SESSION_MEMBER_SESSION_ID: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        teaching_session_member_session_id,
                    )
                ],
                TEACHING_SESSION_MEMBER_MEMBERSHIP_ID: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        teaching_session_member_membership_id,
                    )
                ],
            },
            fallbacks=[
                CommandHandler(
                    "cancel_teaching_session_member",
                    cancel_teaching_session_member,
                ),
            ],
        )
    )

    application.add_handler(
        ConversationHandler(
            entry_points=[
                CommandHandler(
                    "teaching_session_subject",
                    teaching_session_subject,
                )
            ],
            states={
                TEACHING_SESSION_SUBJECT_SESSION_ID: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        teaching_session_subject_session_id,
                    )
                ],
                TEACHING_SESSION_SUBJECT_SUBJECT_ID: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        teaching_session_subject_subject_id,
                    )
                ],
            },
            fallbacks=[
                CommandHandler(
                    "cancel_teaching_session_subject",
                    cancel_teaching_session_subject,
                ),
            ],
        )
    )

    application.add_handler(
        ConversationHandler(
            entry_points=[
                CommandHandler(
                    "teacher_preacher_member",
                    teacher_preacher_member,
                )
            ],
            states={
                TEACHER_PREACHER_MEMBER_TEACHER_PREACHER_ID: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        teacher_preacher_member_teacher_preacher_id,
                    )
                ],
                TEACHER_PREACHER_MEMBER_MEMBERSHIP_ID: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        teacher_preacher_member_membership_id,
                    )
                ],
            },
            fallbacks=[
                CommandHandler(
                    "cancel_teacher_preacher_member",
                    cancel_teacher_preacher_member,
                ),
            ],
        )
    )

    application.add_handler(
        ConversationHandler(
            entry_points=[
                CommandHandler(
                    "teacher_preacher_subject_assignment",
                    teacher_preacher_subject_assignment,
                )
            ],
            states={
                TEACHER_PREACHER_SUBJECT_ASSIGNMENT_TEACHER_PREACHER_ID: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        teacher_preacher_subject_assignment_teacher_preacher_id,
                    )
                ],
                TEACHER_PREACHER_SUBJECT_ASSIGNMENT_TEACHING_SUBJECT_ID: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        teacher_preacher_subject_assignment_teaching_subject_id,
                    )
                ],
            },
            fallbacks=[
                CommandHandler(
                    "cancel_teacher_preacher_subject_assignment",
                    cancel_teacher_preacher_subject_assignment,
                ),
            ],
        )
    )

    application.add_handler(
        ConversationHandler(
            entry_points=[
                CommandHandler("progress", progress)
            ],
            states={
                PROGRESS_MEMBERSHIP_ID: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        progress_membership_id,
                    )
                ],
                PROGRESS_TEACHING_CONTENT_ID: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        progress_teaching_content_id,
                    )
                ],
                PROGRESS_DATE: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        progress_date,
                    )
                ],
                PROGRESS_DESCRIPTION: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        progress_description,
                    )
                ],
                PROGRESS_REMARK: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        progress_remark,
                    )
                ],
                PROGRESS_STATUS: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        progress_status,
                    )
                ],
            },
            fallbacks=[
                CommandHandler(
                    "cancel_progress",
                    cancel_progress,
                ),
            ],
        )
    )

    application.add_handler(
        ConversationHandler(
            entry_points=[CommandHandler("linkstudent", linkstudent)],
            states={
                SCHOOL_STUDENT_ID: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        school_student_id,
                    )
                ],
            },
            fallbacks=[
                CommandHandler("cancel", cancel_linkstudent),
            ],
        )
    )

    application.add_handler(
        ConversationHandler(
            entry_points=[
                CommandHandler("linkteacherstudent", linkteacherstudent)
            ],
            states={
                TEACHER_STUDENT_TEACHER_ID: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        teacher_student_teacher_id,
                    )
                ],
                TEACHER_STUDENT_STUDENT_ID: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        teacher_student_student_id,
                    )
                ],
            },
            fallbacks=[
                CommandHandler("cancel", cancel_linkteacherstudent),
            ],
        )
    )

    application.add_handler(
        ConversationHandler(
            entry_points=[
                CommandHandler("linkparentstudent", linkparentstudent)
            ],
            states={
                PARENT_STUDENT_PARENT_ID: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        parent_student_parent_id,
                    )
                ],
                PARENT_STUDENT_STUDENT_ID: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        parent_student_student_id,
                    )
                ],
            },
            fallbacks=[
                CommandHandler("cancel", cancel_linkparentstudent),
            ],
        )
    )

    application.add_handler(
        ConversationHandler(
            entry_points=[CommandHandler("attendance", attendance)],
            states={
                STUDENT_ID: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        attendance_student_id,
                    )
                ],
                ATTENDANCE_DATE: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        attendance_date,
                    )
                ],
                STATUS: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        attendance_status,
                    )
                ],
                REMARK: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        attendance_remark,
                    )
                ],
            },
            fallbacks=[
                CommandHandler("cancel", cancel_attendance),
            ],
        )
    )

    return application


def main() -> None:
    """Application entry point."""

    logger.info("Starting KOSFintech foundation...")

    logger.info("Initializing production database...")
    database.init_db()

    logger.info("Production database initialized.")

    application = build_application()

    logger.info(
        "KOSFintech Telegram application started."
    )

    application.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
