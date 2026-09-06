from types import SimpleNamespace

from bot import get_authenticated_identity
from models.administration_authority import (
    AdministrationAuthority,
    AdministrationAuthorityRole,
)
from models.external_identity import ExternalIdentity
from models.authority import Action
from repositories.administration_authority_repository import (
    AdministrationAuthorityRepository,
)
from repositories.external_identity_repository import (
    ExternalIdentityRepository,
)
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
