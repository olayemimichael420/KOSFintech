from bot import get_telegram_binding
from models.administration import Administration
from models.administration_authority import AdministrationAuthority
from models.authority import AuthorityRole
from models.user import User
from models.telegram_channel_binding import TelegramChannelBinding
from repositories.administration_authority_repository import AdministrationAuthorityRepository
from repositories.administration_repository import AdministrationRepository
from repositories.telegram_channel_binding_repository import TelegramChannelBindingRepository
from repositories.user_repository import UserRepository
from services.administration_context_service import AdministrationContextService
from services.authorization_service import AuthorizationService
from services.telegram_channel_binding_service import TelegramChannelBindingService


class FakeChat:
    def __init__(self, chat_id):
        self.id = chat_id


class FakeUpdate:
    def __init__(self, chat_id):
        self.effective_chat = FakeChat(chat_id)


class FakeTelegramBindingService:
    def __init__(self, binding):
        self.binding = binding

    def resolve_chat(self, chat_id):
        assert chat_id == self.binding.chat_id
        return self.binding


class FakeServices:
    def __init__(self, binding_service):
        self.telegram_channel_binding = binding_service


class FakeApplication:
    def __init__(self, services):
        self.bot_data = {"services": services}


class FakeContext:
    def __init__(self, services):
        self.application = FakeApplication(services)


def test_telegram_binding_resolves_to_authorized_administration(
    db_connection,
):
    user = UserRepository(db_connection).create(
        User(
            id=None,
            tenant_id="tenant-e2e",
            name="E2E Owner",
            email="e2e@example.com",
            role="member",
            status="active",
        )
    )

    administration = AdministrationRepository(db_connection).create(
        Administration(
            id=None,
            tenant_id="tenant-e2e",
            name="E2E School",
            administration_type="school",
        )
    )

    AdministrationAuthorityRepository(db_connection).create(
        AdministrationAuthority(
            id=None,
            tenant_id="tenant-e2e",
            administration_id=administration.id,
            user_id=user.id,
            role=AuthorityRole.OWNER,
            status="active",
        )
    )

    binding = TelegramChannelBinding(
        id=None,
        provider="telegram",
        chat_id="-100987654321",
        tenant_id="tenant-e2e",
        administration_id=administration.id,
        binding_type="operations",
    )

    binding = TelegramChannelBindingRepository(db_connection).create(binding)

    binding_service = FakeTelegramBindingService(binding)
    context = FakeContext(FakeServices(binding_service))

    resolved_binding = get_telegram_binding(
        FakeUpdate("-100987654321"),
        context,
    )

    assert resolved_binding is not None
    assert resolved_binding.administration_id == administration.id

    administration_context = AdministrationContextService(
        db_connection
    ).resolve(
        user_id=user.id,
        administration_id=resolved_binding.administration_id,
        tenant_id=resolved_binding.tenant_id,
    )

    assert administration_context is not None
    assert administration_context.administration_id == administration.id

    decision = AuthorizationService(db_connection).authorize(
        user_id=user.id,
        administration_id=administration_context.administration_id,
        action="manage_administration",
    )

    assert decision is True


def test_telegram_binding_cannot_cross_tenant_authorization(
    db_connection,
):
    user = UserRepository(db_connection).create(
        User(
            id=None,
            tenant_id="tenant-user",
            name="Wrong Tenant User",
            email="wrong@example.com",
            role="member",
            status="active",
        )
    )

    administration = AdministrationRepository(db_connection).create(
        Administration(
            id=None,
            tenant_id="tenant-school",
            name="School Administration",
            administration_type="school",
        )
    )

    binding = TelegramChannelBindingRepository(db_connection).create(
        TelegramChannelBinding(
            id=None,
            provider="telegram",
            chat_id="-100555555555",
            tenant_id="tenant-school",
            administration_id=administration.id,
            binding_type="operations",
        )
    )

    binding_service = FakeTelegramBindingService(binding)
    context = FakeContext(FakeServices(binding_service))

    resolved_binding = get_telegram_binding(
        FakeUpdate("-100555555555"),
        context,
    )

    assert resolved_binding is not None

    administration_context = AdministrationContextService(
        db_connection
    ).resolve(
        user_id=user.id,
        administration_id=resolved_binding.administration_id,
        tenant_id=resolved_binding.tenant_id,
    )

    assert administration_context is None


def test_inactive_telegram_binding_cannot_enter_administration_context(
    db_connection,
):
    user = UserRepository(db_connection).create(
        User(
            id=None,
            tenant_id="tenant-inactive",
            name="Inactive Binding User",
            email="inactive@example.com",
            role="member",
            status="active",
        )
    )

    administration = AdministrationRepository(db_connection).create(
        Administration(
            id=None,
            tenant_id="tenant-inactive",
            name="Inactive Interface School",
            administration_type="school",
        )
    )

    binding = TelegramChannelBindingRepository(db_connection).create(
        TelegramChannelBinding(
            id=None,
            provider="telegram",
            chat_id="-100666666666",
            tenant_id="tenant-inactive",
            administration_id=administration.id,
            binding_type="operations",
            status="inactive",
        )
    )

    binding_service = TelegramChannelBindingService(
        TelegramChannelBindingRepository(db_connection)
    )
    context = FakeContext(FakeServices(binding_service))

    resolved_binding = get_telegram_binding(
        FakeUpdate("-100666666666"),
        context,
    )

    # The bot-level boundary delegates to the binding service.
    # The real service must reject inactive bindings.
    assert resolved_binding is None


def test_unknown_telegram_chat_cannot_enter_administration_context(
    db_connection,
):
    user = UserRepository(db_connection).create(
        User(
            id=None,
            tenant_id="tenant-unknown",
            name="Unknown Chat User",
            email="unknown@example.com",
            role="member",
            status="active",
        )
    )

    administration = AdministrationRepository(db_connection).create(
        Administration(
            id=None,
            tenant_id="tenant-unknown",
            name="Unknown Chat School",
            administration_type="school",
        )
    )

    binding_service = TelegramChannelBindingService(
        TelegramChannelBindingRepository(db_connection)
    )
    context = FakeContext(FakeServices(binding_service))

    resolved_binding = get_telegram_binding(
        FakeUpdate("-100777777777"),
        context,
    )

    assert resolved_binding is None

    administration_context = AdministrationContextService(
        db_connection
    ).resolve(
        user_id=user.id,
        administration_id=administration.id,
        tenant_id=administration.tenant_id,
    )

    assert administration_context is not None
