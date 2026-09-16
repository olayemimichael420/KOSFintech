import pytest

from models.administration import Administration
from services.administration_provisioning_service import (
    AdministrationProvisioningService,
)


class StubAdministrationRepository:
    def __init__(self):
        self.created = []

    def create(self, administration):
        self.created.append(administration)
        return Administration(
            id=1,
            tenant_id=administration.tenant_id,
            name=administration.name,
            administration_type=administration.administration_type,
            status=administration.status,
        )


def test_create_administration_provisions_tenant_bound_administration():
    repository = StubAdministrationRepository()
    service = AdministrationProvisioningService(repository)

    created = service.create(
        tenant_id="tenant-001",
        name="Example Church",
        administration_type="church",
    )

    assert created.id == 1
    assert created.tenant_id == "tenant-001"
    assert created.name == "Example Church"
    assert created.administration_type == "church"
    assert created.status == "active"

    assert repository.created == [
        Administration(
            id=None,
            tenant_id="tenant-001",
            name="Example Church",
            administration_type="church",
        )
    ]


def test_create_administration_rejects_blank_tenant_id():
    repository = StubAdministrationRepository()
    service = AdministrationProvisioningService(repository)

    with pytest.raises(ValueError, match="tenant_id is required"):
        service.create(
            tenant_id="",
            name="Example Church",
            administration_type="church",
        )


def test_create_administration_rejects_blank_name():
    repository = StubAdministrationRepository()
    service = AdministrationProvisioningService(repository)

    with pytest.raises(ValueError, match="name is required"):
        service.create(
            tenant_id="tenant-001",
            name="   ",
            administration_type="church",
        )


def test_create_administration_rejects_blank_administration_type():
    repository = StubAdministrationRepository()
    service = AdministrationProvisioningService(repository)

    with pytest.raises(
        ValueError,
        match="administration_type is required",
    ):
        service.create(
            tenant_id="tenant-001",
            name="Example Church",
            administration_type="",
        )
