from models.talent_point import TalentPointTransaction
from repositories.talent_point_repository import TalentPointRepository


def test_create_and_get_talent_point_transaction(db_connection):
    repository = TalentPointRepository(db_connection)

    transaction = TalentPointTransaction(
        id=None,
        tenant_id="tenant-1",
        user_id=1,
        service_act_id=1,
        amount=100,
        transaction_type="issuance",
        reference="service-act-1",
    )

    created = repository.create(transaction)

    assert created.id is not None
    assert created.tenant_id == "tenant-1"
    assert created.user_id == 1
    assert created.service_act_id == 1
    assert created.amount == 100
    assert created.transaction_type == "issuance"

    fetched = repository.get(
        "tenant-1",
        created.id,
    )

    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.amount == 100


def test_list_by_user_and_balance(db_connection):
    repository = TalentPointRepository(db_connection)

    repository.create(
        TalentPointTransaction(
            id=None,
            tenant_id="tenant-1",
            user_id=1,
            service_act_id=1,
            amount=100,
            transaction_type="issuance",
        )
    )

    repository.create(
        TalentPointTransaction(
            id=None,
            tenant_id="tenant-1",
            user_id=1,
            service_act_id=2,
            amount=50,
            transaction_type="issuance",
        )
    )

    transactions = repository.list_by_user(
        "tenant-1",
        1,
    )

    assert len(transactions) == 2
    assert repository.get_balance(
        "tenant-1",
        1,
    ) == 150


def test_list_by_service_act(db_connection):
    repository = TalentPointRepository(db_connection)

    repository.create(
        TalentPointTransaction(
            id=None,
            tenant_id="tenant-1",
            user_id=1,
            service_act_id=1,
            amount=100,
            transaction_type="issuance",
        )
    )

    transactions = repository.list_by_service_act(
        "tenant-1",
        1,
    )

    assert len(transactions) == 1
    assert transactions[0].service_act_id == 1


def test_total_issued(db_connection):
    repository = TalentPointRepository(db_connection)

    repository.create(
        TalentPointTransaction(
            id=None,
            tenant_id="tenant-1",
            user_id=1,
            service_act_id=1,
            amount=100,
            transaction_type="issuance",
        )
    )

    repository.create(
        TalentPointTransaction(
            id=None,
            tenant_id="tenant-1",
            user_id=2,
            service_act_id=2,
            amount=250,
            transaction_type="issuance",
        )
    )

    assert repository.get_total_issued("tenant-1") == 350


def test_issuance_exists_for_service_act(db_connection):
    repository = TalentPointRepository(db_connection)

    assert repository.issuance_exists_for_service_act(
        "tenant-1",
        1,
    ) is False

    repository.create(
        TalentPointTransaction(
            id=None,
            tenant_id="tenant-1",
            user_id=1,
            service_act_id=1,
            amount=100,
            transaction_type="issuance",
        )
    )

    assert repository.issuance_exists_for_service_act(
        "tenant-1",
        1,
    ) is True


def test_duplicate_issuance_for_same_service_act_is_rejected(db_connection):
    repository = TalentPointRepository(db_connection)

    transaction = TalentPointTransaction(
        id=None,
        tenant_id="tenant-1",
        user_id=1,
        service_act_id=1,
        amount=100,
        transaction_type="issuance",
    )

    repository.create(transaction)

    try:
        repository.create(
            TalentPointTransaction(
                id=None,
                tenant_id="tenant-1",
                user_id=1,
                service_act_id=1,
                amount=200,
                transaction_type="issuance",
            )
        )
    except Exception as exc:
        assert "UNIQUE" in str(exc).upper()
    else:
        raise AssertionError(
            "duplicate TP issuance should be rejected"
        )

def test_balance_is_tenant_isolated(db_connection):
    repository = TalentPointRepository(db_connection)

    tenant_2_user_id = db_connection.execute(
        "SELECT id FROM users WHERE tenant_id = ? ORDER BY id LIMIT 1",
        ("tenant-2",),
    ).fetchone()[0]

    tenant_2_service_act_id = db_connection.execute(
        "SELECT id FROM service_acts WHERE tenant_id = ? ORDER BY id LIMIT 1",
        ("tenant-2",),
    ).fetchone()[0]

    repository.create(
        TalentPointTransaction(
            id=None,
            tenant_id="tenant-1",
            user_id=1,
            service_act_id=1,
            amount=100,
            transaction_type="issuance",
        )
    )

    repository.create(
        TalentPointTransaction(
            id=None,
            tenant_id="tenant-2",
            user_id=tenant_2_user_id,
            service_act_id=tenant_2_service_act_id,
            amount=900,
            transaction_type="issuance",
        )
    )

    assert repository.get_balance("tenant-1", 1) == 100
    assert repository.get_balance(
        "tenant-2",
        tenant_2_user_id,
    ) == 900


def test_total_issued_is_tenant_isolated(db_connection):
    repository = TalentPointRepository(db_connection)

    tenant_2_user_id = db_connection.execute(
        "SELECT id FROM users WHERE tenant_id = ? ORDER BY id LIMIT 1",
        ("tenant-2",),
    ).fetchone()[0]

    tenant_2_service_act_id = db_connection.execute(
        "SELECT id FROM service_acts WHERE tenant_id = ? ORDER BY id LIMIT 1",
        ("tenant-2",),
    ).fetchone()[0]

    repository.create(
        TalentPointTransaction(
            id=None,
            tenant_id="tenant-1",
            user_id=1,
            service_act_id=1,
            amount=100,
            transaction_type="issuance",
        )
    )

    repository.create(
        TalentPointTransaction(
            id=None,
            tenant_id="tenant-2",
            user_id=tenant_2_user_id,
            service_act_id=tenant_2_service_act_id,
            amount=900,
            transaction_type="issuance",
        )
    )

    assert repository.get_total_issued("tenant-1") == 100
    assert repository.get_total_issued("tenant-2") == 900


def test_total_issued_ignores_non_issuance_transactions(db_connection):
    repository = TalentPointRepository(db_connection)

    repository.create(
        TalentPointTransaction(
            id=None,
            tenant_id="tenant-1",
            user_id=1,
            service_act_id=1,
            amount=100,
            transaction_type="issuance",
        )
    )

    repository.create(
        TalentPointTransaction(
            id=None,
            tenant_id="tenant-1",
            user_id=1,
            service_act_id=2,
            amount=50,
            transaction_type="transfer",
        )
    )

    assert repository.get_total_issued("tenant-1") == 100


def test_list_by_user_is_tenant_isolated(db_connection):
    repository = TalentPointRepository(db_connection)

    tenant_2_user_id = db_connection.execute(
        "SELECT id FROM users WHERE tenant_id = ? ORDER BY id LIMIT 1",
        ("tenant-2",),
    ).fetchone()[0]

    tenant_2_service_act_id = db_connection.execute(
        "SELECT id FROM service_acts WHERE tenant_id = ? ORDER BY id LIMIT 1",
        ("tenant-2",),
    ).fetchone()[0]

    repository.create(
        TalentPointTransaction(
            id=None,
            tenant_id="tenant-1",
            user_id=1,
            service_act_id=1,
            amount=100,
            transaction_type="issuance",
        )
    )

    repository.create(
        TalentPointTransaction(
            id=None,
            tenant_id="tenant-2",
            user_id=tenant_2_user_id,
            service_act_id=tenant_2_service_act_id,
            amount=900,
            transaction_type="issuance",
        )
    )

    tenant_1_transactions = repository.list_by_user(
        "tenant-1",
        1,
    )

    tenant_2_transactions = repository.list_by_user(
        "tenant-2",
        tenant_2_user_id,
    )

    assert len(tenant_1_transactions) == 1
    assert tenant_1_transactions[0].amount == 100

    assert len(tenant_2_transactions) == 1
    assert tenant_2_transactions[0].amount == 900


def test_list_by_service_act_is_tenant_isolated(db_connection):
    repository = TalentPointRepository(db_connection)

    tenant_2_user_id = db_connection.execute(
        "SELECT id FROM users WHERE tenant_id = ? ORDER BY id LIMIT 1",
        ("tenant-2",),
    ).fetchone()[0]

    tenant_2_service_act_id = db_connection.execute(
        "SELECT id FROM service_acts WHERE tenant_id = ? ORDER BY id LIMIT 1",
        ("tenant-2",),
    ).fetchone()[0]

    repository.create(
        TalentPointTransaction(
            id=None,
            tenant_id="tenant-1",
            user_id=1,
            service_act_id=1,
            amount=100,
            transaction_type="issuance",
        )
    )

    repository.create(
        TalentPointTransaction(
            id=None,
            tenant_id="tenant-2",
            user_id=tenant_2_user_id,
            service_act_id=tenant_2_service_act_id,
            amount=900,
            transaction_type="issuance",
        )
    )

    tenant_1_transactions = repository.list_by_service_act(
        "tenant-1",
        1,
    )

    tenant_2_transactions = repository.list_by_service_act(
        "tenant-2",
        tenant_2_service_act_id,
    )

    assert len(tenant_1_transactions) == 1
    assert tenant_1_transactions[0].amount == 100

    assert len(tenant_2_transactions) == 1
    assert tenant_2_transactions[0].amount == 900
