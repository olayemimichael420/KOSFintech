import pytest

from handlers.session_teacher_preacher_assignment_create import (
    TEACHER_PREACHER_ID,
    TEACHING_SESSION_ID,
    cancel_session_teacher_preacher_assignment,
    session_teacher_preacher_assignment,
    session_teacher_preacher_assignment_teacher_preacher_id,
    session_teacher_preacher_assignment_teaching_session_id,
)


class FakeMessage:
    def __init__(self, text=""):
        self.text = text
        self.replies = []

    async def reply_text(self, text):
        self.replies.append(text)


class FakeUpdate:
    def __init__(self, text=""):
        self.message = FakeMessage(text)
        self.effective_user = type("User", (), {"id": 77})()


class FakeAdministrationContext:
    tenant_id = "tenant-a"
    user_id = 77


class FakeContext:
    def __init__(self, resolver=None, service=None):
        self.user_data = {}

        async def default_resolver(update, context):
            return FakeAdministrationContext()

        self.application = type(
            "Application",
            (),
            {
                "bot_data": {
                    "get_administration_context": (
                        resolver or default_resolver
                    ),
                    "services": type(
                        "Services",
                        (),
                        {
                            "session_teacher_preacher_assignment":
                                lambda self, tenant_id, user_id=None: service,
                        },
                    )(),
                }
            },
        )()


class FakeAssignmentService:
    def __init__(self):
        self.created = []

    def create(self, assignment):
        self.created.append(assignment)
        return assignment


@pytest.mark.asyncio
async def test_start_denies_without_administration_context():
    update = FakeUpdate()
    async def denied_resolver(update, context):
        return None

    context = FakeContext(resolver=denied_resolver)

    result = await session_teacher_preacher_assignment(update, context)

    assert result == -1
    assert "Access denied" in update.message.replies[-1]


@pytest.mark.asyncio
async def test_start_prompts_for_teacher_preacher_id():
    update = FakeUpdate()
    context = FakeContext()

    result = await session_teacher_preacher_assignment(update, context)

    assert result == TEACHER_PREACHER_ID
    assert "Teacher/Preacher capacity ID" in update.message.replies[-1]


@pytest.mark.asyncio
async def test_teacher_preacher_id_must_be_integer():
    update = FakeUpdate("abc")
    context = FakeContext()

    result = await session_teacher_preacher_assignment_teacher_preacher_id(
        update, context
    )

    assert result == TEACHER_PREACHER_ID
    assert "valid positive" in update.message.replies[-1]


@pytest.mark.asyncio
async def test_valid_teacher_preacher_id_prompts_for_session_id():
    update = FakeUpdate("12")
    context = FakeContext()

    result = await session_teacher_preacher_assignment_teacher_preacher_id(
        update, context
    )

    assert result == TEACHING_SESSION_ID
    assert context.user_data[
        "session_teacher_preacher_assignment_teacher_preacher_id"
    ] == 12


@pytest.mark.asyncio
async def test_session_id_must_be_positive():
    update = FakeUpdate("0")
    context = FakeContext()
    context.user_data[
        "session_teacher_preacher_assignment_teacher_preacher_id"
    ] = 12

    result = await session_teacher_preacher_assignment_teaching_session_id(
        update, context
    )

    assert result == TEACHING_SESSION_ID
    assert "positive" in update.message.replies[-1]


@pytest.mark.asyncio
async def test_authorized_assignment_is_created():
    update = FakeUpdate("21")
    service = FakeAssignmentService()
    context = FakeContext(service=service)

    context.user_data[
        "session_teacher_preacher_assignment_teacher_preacher_id"
    ] = 12

    result = await session_teacher_preacher_assignment_teaching_session_id(
        update, context
    )

    assert result == -1
    assert len(service.created) == 1

    assignment = service.created[0]
    assert assignment.tenant_id == "tenant-a"
    assert assignment.teacher_preacher_id == 12
    assert assignment.teaching_session_id == 21
    assert context.user_data == {}


@pytest.mark.asyncio
async def test_permission_error_is_handled():
    class DeniedService:
        def create(self, assignment):
            raise PermissionError("denied")

    update = FakeUpdate("21")
    context = FakeContext(service=DeniedService())
    context.user_data[
        "session_teacher_preacher_assignment_teacher_preacher_id"
    ] = 12

    result = await session_teacher_preacher_assignment_teaching_session_id(
        update, context
    )

    assert result == -1
    assert "permission is required" in update.message.replies[-1]
    assert context.user_data == {}


@pytest.mark.asyncio
async def test_expired_session_is_rejected_and_cleared():
    update = FakeUpdate("21")
    context = FakeContext()

    result = await session_teacher_preacher_assignment_teaching_session_id(
        update, context
    )

    assert result == -1
    assert context.user_data == {}
    assert "Unable to create" not in update.message.replies[-1]


@pytest.mark.asyncio
async def test_cancel_clears_context():
    update = FakeUpdate()
    context = FakeContext()
    context.user_data[
        "session_teacher_preacher_assignment_teacher_preacher_id"
    ] = 12
    context.user_data[
        "session_teacher_preacher_assignment_teaching_session_id"
    ] = 21

    result = await cancel_session_teacher_preacher_assignment(
        update, context
    )

    assert result == -1
    assert context.user_data == {}
    assert "cancelled" in update.message.replies[-1]
