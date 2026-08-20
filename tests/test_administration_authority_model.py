from models.administration_authority import (
    AdministrationAuthority,
    AdministrationAuthorityRole,
)


def test_owner_authority():
    authority = AdministrationAuthority(
        id=None,
        tenant_id="tenant-001",
        administration_id=1,
        user_id=10,
        role=AdministrationAuthorityRole.OWNER,
    )

    assert authority.role == AdministrationAuthorityRole.OWNER
    assert authority.status == "active"


def test_admin_roles():
    for role in (
        AdministrationAuthorityRole.ADMIN_1,
        AdministrationAuthorityRole.ADMIN_2,
    ):
        authority = AdministrationAuthority(
            id=None,
            tenant_id="tenant-001",
            administration_id=1,
            user_id=10,
            role=role,
        )

        assert authority.role == role
        assert authority.status == "active"
