import bot
from types import SimpleNamespace

from bot import get_authenticated_identity
from models.administration_authority import (
    AdministrationAuthority,
    AdministrationAuthorityRole,
)
from models.external_identity import ExternalIdentity
from models.student import Student
from models.authority import Action
from repositories.administration_authority_repository import (
    AdministrationAuthorityRepository,
)
from repositories.external_identity_repository import (
    ExternalIdentityRepository,
)
from repositories.student_repository import StudentRepository
from services.application_service_factory import ApplicationServiceFactory
from services.application_services import ApplicationServices


def test_telegram_identity_flows_into_governance_authorization(db_connection):
    administration_id = db_connection.execute(
        """
        INSERT INTO administrations (
            tenant_id,
            name,
            administration_type
        )
        VALUES (?, ?, ?)
        """,
        ("tenant-1", "Integration Administration", "school"),
    ).lastrowid

    user_id = 1

    AdministrationAuthorityRepository(db_connection).create(
        AdministrationAuthority(
            id=None,
            tenant_id="tenant-1",
            administration_id=administration_id,
            user_id=user_id,
            role=AdministrationAuthorityRole.OWNER,
        )
    )

    ExternalIdentityRepository(db_connection).create(
        ExternalIdentity(
            id=None,
            provider="telegram",
            subject="123456789",
            tenant_id="tenant-1",
            user_id=user_id,
        )
    )

    services = ApplicationServices(
        ApplicationServiceFactory(db_connection)
    )

    update = SimpleNamespace(
        effective_user=SimpleNamespace(id=123456789)
    )

    application = SimpleNamespace(
        bot_data={"services": services}
    )
    context = SimpleNamespace(application=application)

    identity = get_authenticated_identity(update, context)

    assert identity is not None
    assert identity.user_id == user_id
    assert identity.tenant_id == "tenant-1"
    assert identity.is_authenticated is True

    authorization_context = services.authorization_context.resolve(
        user_id=identity.user_id,
        administration_id=administration_id,
        tenant_id=identity.tenant_id,
    )

    decision = services.authorization.authorize_context(
        context=authorization_context,
        administration_id=administration_id,
        action=Action.REMOVE_ADMIN,
    )

    assert decision.allowed is True
    assert decision.reason == "owner authorized within administration"

def test_telegram_identity_and_binding_flow_into_smos_student_read(db_connection):
    administration_id = db_connection.execute(
        """
        INSERT INTO administrations (
            tenant_id,
            name,
            administration_type
        )
        VALUES (?, ?, ?)
        """,
        ("tenant-1", "SMOS Integration Administration", "school"),
    ).lastrowid

    # Grant the existing tenant-1 test user the ordinary SMOS
    # application permission required to read student records.
    role_id = db_connection.execute(
        """
        INSERT INTO roles (
            tenant_id,
            name,
            status
        )
        VALUES (?, ?, ?)
        """,
        ("tenant-1", "smos_reader", "active"),
    ).lastrowid

    permission_id = db_connection.execute(
        """
        INSERT INTO permissions (
            tenant_id,
            name,
            status
        )
        VALUES (?, ?, ?)
        """,
        ("tenant-1", "student.read", "active"),
    ).lastrowid

    db_connection.execute(
        """
        INSERT INTO user_roles (
            tenant_id,
            user_id,
            role_id
        )
        VALUES (?, ?, ?)
        """,
        ("tenant-1", 1, role_id),
    )

    db_connection.execute(
        """
        INSERT INTO role_permissions (
            tenant_id,
            role_id,
            permission_id
        )
        VALUES (?, ?, ?)
        """,
        ("tenant-1", role_id, permission_id),
    )

    db_connection.execute(
        """
        INSERT INTO telegram_channel_bindings (
            provider,
            chat_id,
            tenant_id,
            administration_id,
            binding_type
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            "telegram",
            "-100987654321",
            "tenant-1",
            administration_id,
            "group",
        ),
    )

    db_connection.commit()

    ExternalIdentityRepository(db_connection).create(
        ExternalIdentity(
            id=None,
            provider="telegram",
            subject="123456789",
            tenant_id="tenant-1",
            user_id=1,
        )
    )

    student = StudentRepository(db_connection).create(
        Student(
            id=None,
            tenant_id="tenant-1",
            user_id=None,
            name="SMOS Learner",
            class_name="JSS 1",
            age=12,
            guardian_id=None,
            enrollment_date="2026-09-06",
        )
    )

    services = ApplicationServices(
        ApplicationServiceFactory(db_connection)
    )

    update = SimpleNamespace(
        effective_user=SimpleNamespace(id=123456789),
        effective_chat=SimpleNamespace(id=-100987654321),
    )

    application = SimpleNamespace(
        bot_data={"services": services}
    )
    context = SimpleNamespace(application=application)

    administration_context = bot.get_administration_context(
        update,
        context,
    )

    assert administration_context is not None
    assert administration_context.user_id == 1
    assert administration_context.tenant_id == "tenant-1"
    assert administration_context.administration_id == administration_id

    student_service = services.student(
        administration_context.tenant_id,
        user_id=administration_context.user_id,
    )

    result = student_service.get(student.id)

    assert result is not None
    assert result.id == student.id
    assert result.tenant_id == "tenant-1"
