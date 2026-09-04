import pytest

from models.external_identity import ExternalIdentity
from models.permission import Permission
from models.role import Role
from models.role_permission import RolePermissionLink
from models.user import User
from models.user_role import UserRoleLink

from repositories.external_identity_repository import ExternalIdentityRepository
from repositories.permission_repository import PermissionRepository
from repositories.role_permission_repository import RolePermissionRepository
from repositories.role_repository import RoleRepository
from repositories.user_repository import UserRepository
from repositories.user_role_repository import UserRoleRepository

from services.external_identity_service import ExternalIdentityService
from services.permission_resolution_service import PermissionResolutionService


LINK_PERMISSION = "external_identity.link"
READ_PERMISSION = "external_identity.read"


def build_service(connection):
    return ExternalIdentityService(
        external_identity_repository=ExternalIdentityRepository(connection),
        user_repository=UserRepository(connection),
        permission_service=PermissionResolutionService(connection),
    )


def create_user(
    connection,
    tenant_id,
    name="Test User",
    email="user@example.com",
    status="active",
):
    return UserRepository(connection).create(
        User(
            id=None,
            tenant_id=tenant_id,
            name=name,
            email=email,
            role="member",
            status=status,
        )
    )


def grant_permission(
    connection,
    user,
    permission_name,
    description,
    role_name,
):
    role = RoleRepository(connection).create(
        Role(
            None,
            user.tenant_id,
            role_name,
            description,
        )
    )

    permission = PermissionRepository(connection).create(
        Permission(
            None,
            user.tenant_id,
            permission_name,
            description,
        )
    )

    UserRoleRepository(connection).create(
        UserRoleLink(
            user.tenant_id,
            user.id,
            role.id,
        )
    )

    RolePermissionRepository(connection).create(
        RolePermissionLink(
            user.tenant_id,
            role.id,
            permission.id,
        )
    )


def grant_link_permission(connection, user, role_name="identity_linker"):
    grant_permission(
        connection,
        user,
        LINK_PERMISSION,
        "Link an external identity to an existing canonical user",
        role_name,
    )


def grant_read_permission(connection, user, role_name="identity_reader"):
    grant_permission(
        connection,
        user,
        READ_PERMISSION,
        "Read external identities linked to canonical users",
        role_name,
    )


def test_link_binds_external_identity_to_existing_active_user(db_connection):
    actor = create_user(
        db_connection,
        "school-001",
        name="Authorized Actor",
        email="actor@example.com",
    )
    target = create_user(
        db_connection,
        "school-001",
        name="Target User",
        email="target@example.com",
    )
    grant_link_permission(db_connection, actor)

    service = build_service(db_connection)

    identity = service.link(
        provider="telegram",
        subject="telegram-001",
        tenant_id="school-001",
        user_id=target.id,
        actor_user_id=actor.id,
    )

    assert isinstance(identity, ExternalIdentity)
    assert identity.id is not None
    assert identity.provider == "telegram"
    assert identity.subject == "telegram-001"
    assert identity.tenant_id == "school-001"
    assert identity.user_id == target.id


def test_link_rejects_actor_without_link_permission(db_connection):
    actor = create_user(
        db_connection,
        "school-001",
        name="Unauthorized Actor",
        email="unauthorized@example.com",
    )
    target = create_user(
        db_connection,
        "school-001",
        name="Target User",
        email="target@example.com",
    )

    service = build_service(db_connection)

    with pytest.raises(
        PermissionError,
        match="external identity link permission denied",
    ):
        service.link(
            provider="telegram",
            subject="telegram-denied",
            tenant_id="school-001",
            user_id=target.id,
            actor_user_id=actor.id,
        )


def test_link_rejects_unknown_actor(db_connection):
    target = create_user(
        db_connection,
        "school-001",
        name="Target User",
        email="target@example.com",
    )

    service = build_service(db_connection)

    with pytest.raises(
        PermissionError,
        match="external identity link permission denied",
    ):
        service.link(
            provider="telegram",
            subject="telegram-unknown-actor",
            tenant_id="school-001",
            user_id=target.id,
            actor_user_id=999999,
        )


def test_link_rejects_inactive_actor(db_connection):
    actor = create_user(
        db_connection,
        "school-001",
        name="Inactive Actor",
        email="inactive-actor@example.com",
        status="inactive",
    )
    target = create_user(
        db_connection,
        "school-001",
        name="Target User",
        email="target@example.com",
    )

    service = build_service(db_connection)

    with pytest.raises(
        PermissionError,
        match="external identity link permission denied",
    ):
        service.link(
            provider="telegram",
            subject="telegram-inactive-actor",
            tenant_id="school-001",
            user_id=target.id,
            actor_user_id=actor.id,
        )


def test_link_rejects_cross_tenant_actor(db_connection):
    actor = create_user(
        db_connection,
        "school-001",
        name="Tenant One Actor",
        email="actor@school1.example.com",
    )
    target = create_user(
        db_connection,
        "school-002",
        name="Tenant Two Target",
        email="target@school2.example.com",
    )
    grant_link_permission(db_connection, actor)

    service = build_service(db_connection)

    with pytest.raises(
        PermissionError,
        match="external identity link permission denied",
    ):
        service.link(
            provider="telegram",
            subject="telegram-cross-tenant",
            tenant_id="school-002",
            user_id=target.id,
            actor_user_id=actor.id,
        )


def test_link_rejects_missing_canonical_user(db_connection):
    actor = create_user(
        db_connection,
        "school-001",
        name="Authorized Actor",
        email="actor@example.com",
    )
    grant_link_permission(db_connection, actor)

    service = build_service(db_connection)

    with pytest.raises(ValueError, match="canonical user not found"):
        service.link(
            provider="telegram",
            subject="telegram-002",
            tenant_id="school-001",
            user_id=999999,
            actor_user_id=actor.id,
        )


def test_link_rejects_inactive_canonical_user(db_connection):
    actor = create_user(
        db_connection,
        "school-001",
        name="Authorized Actor",
        email="actor@example.com",
    )
    target = create_user(
        db_connection,
        "school-001",
        name="Inactive User",
        email="inactive@example.com",
        status="inactive",
    )
    grant_link_permission(db_connection, actor)

    service = build_service(db_connection)

    with pytest.raises(ValueError, match="canonical user is not active"):
        service.link(
            provider="telegram",
            subject="telegram-003",
            tenant_id="school-001",
            user_id=target.id,
            actor_user_id=actor.id,
        )


def test_link_rejects_duplicate_external_identity(db_connection):
    actor = create_user(
        db_connection,
        "school-001",
        name="Authorized Actor",
        email="actor@example.com",
    )
    user_one = create_user(
        db_connection,
        "school-001",
        name="User One",
        email="one@example.com",
    )
    user_two = create_user(
        db_connection,
        "school-001",
        name="User Two",
        email="two@example.com",
    )
    grant_link_permission(db_connection, actor)

    service = build_service(db_connection)

    service.link(
        provider="telegram",
        subject="telegram-duplicate",
        tenant_id="school-001",
        user_id=user_one.id,
        actor_user_id=actor.id,
    )

    with pytest.raises(
        ValueError,
        match="external identity already linked",
    ):
        service.link(
            provider="telegram",
            subject="telegram-duplicate",
            tenant_id="school-001",
            user_id=user_two.id,
            actor_user_id=actor.id,
        )


def test_resolve_returns_canonical_external_identity_binding(db_connection):
    actor = create_user(
        db_connection,
        "school-001",
        name="Authorized Actor",
        email="actor@example.com",
    )
    user = create_user(
        db_connection,
        "school-001",
        name="Resolvable User",
        email="resolve@example.com",
    )
    grant_link_permission(db_connection, actor)

    service = build_service(db_connection)

    created = service.link(
        provider="telegram",
        subject="telegram-resolve",
        tenant_id="school-001",
        user_id=user.id,
        actor_user_id=actor.id,
    )

    resolved = service.resolve(
        provider="telegram",
        subject="telegram-resolve",
    )

    assert resolved is not None
    assert resolved.id == created.id
    assert resolved.user_id == user.id
    assert resolved.tenant_id == "school-001"


def test_list_for_user_is_tenant_scoped(db_connection):
    actor = create_user(
        db_connection,
        "school-001",
        name="Authorized Actor",
        email="actor@example.com",
    )
    user = create_user(
        db_connection,
        "school-001",
        name="Linked User",
        email="linked@example.com",
    )
    grant_link_permission(db_connection, actor)
    grant_read_permission(db_connection, actor)

    service = build_service(db_connection)

    service.link(
        provider="telegram",
        subject="telegram-list",
        tenant_id="school-001",
        user_id=user.id,
        actor_user_id=actor.id,
    )

    identities = service.list_for_user(
        tenant_id="school-001",
        user_id=user.id,
        actor_user_id=actor.id,
    )

    assert len(identities) == 1
    assert identities[0].provider == "telegram"
    assert identities[0].subject == "telegram-list"
    assert identities[0].tenant_id == "school-001"


def test_list_for_user_rejects_actor_without_read_permission(db_connection):
    actor = create_user(
        db_connection,
        "school-001",
        name="Unauthorized Actor",
        email="unauthorized@example.com",
    )
    user = create_user(
        db_connection,
        "school-001",
        name="Target User",
        email="target@example.com",
    )

    service = build_service(db_connection)

    with pytest.raises(
        PermissionError,
        match="external identity read permission denied",
    ):
        service.list_for_user(
            tenant_id="school-001",
            user_id=user.id,
            actor_user_id=actor.id,
        )


def test_list_for_user_rejects_unknown_actor(db_connection):
    user = create_user(
        db_connection,
        "school-001",
        name="Target User",
        email="target@example.com",
    )

    service = build_service(db_connection)

    with pytest.raises(
        PermissionError,
        match="external identity read permission denied",
    ):
        service.list_for_user(
            tenant_id="school-001",
            user_id=user.id,
            actor_user_id=999999,
        )


def test_list_for_user_rejects_inactive_actor(db_connection):
    actor = create_user(
        db_connection,
        "school-001",
        name="Inactive Actor",
        email="inactive@example.com",
        status="inactive",
    )
    user = create_user(
        db_connection,
        "school-001",
        name="Target User",
        email="target@example.com",
    )
    grant_read_permission(db_connection, actor)

    service = build_service(db_connection)

    with pytest.raises(
        PermissionError,
        match="external identity read permission denied",
    ):
        service.list_for_user(
            tenant_id="school-001",
            user_id=user.id,
            actor_user_id=actor.id,
        )


def test_list_for_user_rejects_cross_tenant_actor(db_connection):
    actor = create_user(
        db_connection,
        "school-002",
        name="Other Tenant Actor",
        email="other@example.com",
    )
    user = create_user(
        db_connection,
        "school-001",
        name="Target User",
        email="target@example.com",
    )
    grant_read_permission(db_connection, actor)

    service = build_service(db_connection)

    with pytest.raises(
        PermissionError,
        match="external identity read permission denied",
    ):
        service.list_for_user(
            tenant_id="school-001",
            user_id=user.id,
            actor_user_id=actor.id,
        )


def test_list_for_user_rejects_wrong_tenant(db_connection):
    actor = create_user(
        db_connection,
        "school-001",
        name="Authorized Actor",
        email="actor@example.com",
    )
    user = create_user(
        db_connection,
        "school-001",
        name="Tenant User",
        email="tenant@example.com",
    )
    grant_read_permission(db_connection, actor)

    service = build_service(db_connection)

    with pytest.raises(
        PermissionError,
        match="external identity read permission denied",
    ):
        service.list_for_user(
            tenant_id="school-002",
            user_id=user.id,
            actor_user_id=actor.id,
        )
