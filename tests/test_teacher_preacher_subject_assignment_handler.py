import pytest

from handlers.teacher_preacher_subject_assignment_create import (
    TEACHER_PREACHER_ID,
    TEACHING_SUBJECT_ID,
    cancel_teacher_preacher_subject_assignment,
    teacher_preacher_subject_assignment,
    teacher_preacher_subject_assignment_teacher_preacher_id,
    teacher_preacher_subject_assignment_teaching_subject_id,
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


class FakeApplication:
    def __init__(self, bot_data):
        self.bot_data = bot_data


class FakeContext:
    def __init__(self, bot_data):
        self.application = FakeApplication(bot_data)
        self.user_data = {}


class FakeAdministrationContext:
    def __init__(self, tenant_id="tenant-a", user_id="user-a"):
        self.tenant_id = tenant_id
        self.user_id = user_id


class FakeAssignmentService:
    def __init__(self):
        self.created = []

    def create(self, assignment):
        self.created.append(assignment)
        return assignment


class FakeServices:
    def __init__(self, assignment_service):
        self._assignment_service = assignment_service

    def teacher_preacher_subject_assignment(self, tenant_id, user_id=None):
        return self._assignment_service


def make_context(resolver=None, service=None):
    if resolver is None:
        resolver = lambda update, context: FakeAdministrationContext()

    if service is None:
        service = FakeAssignmentService()

    return FakeContext(
        {
            "get_administration_context": resolver,
            "services": FakeServices(service),
        }
    )


@pytest.mark.asyncio
async def test_start_denies_without_administration_context():
    update = FakeUpdate()
    context = make_context(lambda update, context: None)

    result = await teacher_preacher_subject_assignment(update, context)

    assert result == -1
    assert "Access denied" in update.message.replies[-1]


@pytest.mark.asyncio
async def test_start_prompts_for_teacher_preacher_id():
    update = FakeUpdate()
    context = make_context()

    result = await teacher_preacher_subject_assignment(update, context)

    assert result == TEACHER_PREACHER_ID
    assert "Teacher/Preacher capacity ID" in update.message.replies[-1]


@pytest.mark.asyncio
async def test_teacher_preacher_id_must_be_integer():
    update = FakeUpdate("abc")
    context = make_context()

    result = await teacher_preacher_subject_assignment_teacher_preacher_id(
        update, context
    )

    assert result == TEACHER_PREACHER_ID
    assert "Invalid Teacher/Preacher capacity ID" in update.message.replies[-1]


@pytest.mark.asyncio
async def test_teacher_preacher_id_must_be_positive():
    update = FakeUpdate("0")
    context = make_context()

    result = await teacher_preacher_subject_assignment_teacher_preacher_id(
        update, context
    )

    assert result == TEACHER_PREACHER_ID
    assert "positive integer" in update.message.replies[-1]


@pytest.mark.asyncio
async def test_valid_teacher_preacher_id_prompts_for_subject_id():
    update = FakeUpdate("12")
    context = make_context()

    result = await teacher_preacher_subject_assignment_teacher_preacher_id(
        update, context
    )

    assert result == TEACHING_SUBJECT_ID
    assert (
        context.user_data[
            "teacher_preacher_subject_assignment_teacher_preacher_id"
        ]
        == 12
    )


@pytest.mark.asyncio
async def test_subject_id_must_be_integer():
    update = FakeUpdate("abc")
    context = make_context()
    context.user_data[
        "teacher_preacher_subject_assignment_teacher_preacher_id"
    ] = 12

    result = await teacher_preacher_subject_assignment_teaching_subject_id(
        update, context
    )

    assert result == TEACHING_SUBJECT_ID
    assert "Invalid teaching subject ID" in update.message.replies[-1]


@pytest.mark.asyncio
async def test_subject_id_must_be_positive():
    update = FakeUpdate("0")
    context = make_context()
    context.user_data[
        "teacher_preacher_subject_assignment_teacher_preacher_id"
    ] = 12

    result = await teacher_preacher_subject_assignment_teaching_subject_id(
        update, context
    )

    assert result == TEACHING_SUBJECT_ID
    assert "positive integer" in update.message.replies[-1]


@pytest.mark.asyncio
async def test_expired_session_is_rejected():
    update = FakeUpdate("7")
    context = make_context()

    result = await teacher_preacher_subject_assignment_teaching_subject_id(
        update, context
    )

    assert result == -1
    assert "session expired" in update.message.replies[-1]


@pytest.mark.asyncio
async def test_authorized_assignment_is_created():
    update = FakeUpdate("21")
    service = FakeAssignmentService()
    context = make_context(service=service)
    context.user_data[
        "teacher_preacher_subject_assignment_teacher_preacher_id"
    ] = 12

    result = await teacher_preacher_subject_assignment_teaching_subject_id(
        update, context
    )

    assert result == -1
    assert len(service.created) == 1

    assignment = service.created[0]
    assert assignment.tenant_id == "tenant-a"
    assert assignment.teacher_preacher_id == 12
    assert assignment.teaching_subject_id == 21
    assert "assignment created" in update.message.replies[-1]


@pytest.mark.asyncio
async def test_permission_error_is_handled():
    class DeniedService:
        def create(self, assignment):
            raise PermissionError("denied")

    update = FakeUpdate("21")
    context = make_context(service=DeniedService())
    context.user_data[
        "teacher_preacher_subject_assignment_teacher_preacher_id"
    ] = 12

    result = await teacher_preacher_subject_assignment_teaching_subject_id(
        update, context
    )

    assert result == -1
    assert "permission is required" in update.message.replies[-1]


@pytest.mark.asyncio
async def test_cancel_clears_context():
    update = FakeUpdate()
    context = make_context()
    context.user_data[
        "teacher_preacher_subject_assignment_teacher_preacher_id"
    ] = 12
    context.user_data[
        "teacher_preacher_subject_assignment_teaching_subject_id"
    ] = 21

    result = await cancel_teacher_preacher_subject_assignment(update, context)

    assert result == -1
    assert context.user_data == {}
    assert "cancelled" in update.message.replies[-1]
