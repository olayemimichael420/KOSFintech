import pytest

import database

from models.talent_point import TalentPointTransaction
from repositories.talent_point_repository import TalentPointRepository
from services.talent_point_transfer_service import TalentPointTransferService


def _setup_db(tmp_path, monkeypatch):
    db_path = tmp_path / "talent_point_transfer.db"

    monkeypatch.setattr(
        database,
        "get_db_path",
        lambda: db_path,
    )

    database.init_db()
    return database.get_connection()


def _create_user(connection, tenant_id, name):
    cursor = connection.execute(
        """
        INSERT INTO users (tenant_id, name, role)
        VALUES (?, ?, ?)
        """,
        (tenant_id, name, "member"),
    )
    connection.commit()
    return cursor.lastrowid


def _create_issuance(
    connection,
    tenant_id,
    user_id,
    amount,
    service_act_id=None,
    reference="initial-issuance",
):
    repository = TalentPointRepository(connection)

    return repository.create(
        TalentPointTransaction(
            id=None,
            tenant_id=tenant_id,
            user_id=user_id,
            service_act_id=service_act_id,
            amount=amount,
            transaction_type="issuance",
            reference=reference,
        )
    )


def test_successful_transfer_creates_debit_and_credit_without_service_act(
    tmp_path,
    monkeypatch,
):
    connection = _setup_db(tmp_path, monkeypatch)

    try:
        sender = _create_user(connection, "tenant-1", "Sender")
        recipient = _create_user(connection, "tenant-1", "Recipient")

        _create_issuance(
            connection,
            "tenant-1",
            sender,
            500,
        )

        service = TalentPointTransferService(
            TalentPointRepository(connection)
        )

        debit, credit = service.transfer(
            tenant_id="tenant-1",
            sender_user_id=sender,
            recipient_user_id=recipient,
            amount=100,
            reference="transfer-1",
        )

        assert debit.amount == -100
        assert credit.amount == 100

        assert debit.user_id == sender
        assert credit.user_id == recipient

        assert debit.transaction_type == "transfer"
        assert credit.transaction_type == "transfer"

        assert debit.service_act_id is None
        assert credit.service_act_id is None

        assert debit.reference == "transfer-1"
        assert credit.reference == "transfer-1"

    finally:
        connection.close()


def test_transfer_updates_sender_and_recipient_balances(
    tmp_path,
    monkeypatch,
):
    connection = _setup_db(tmp_path, monkeypatch)

    try:
        sender = _create_user(connection, "tenant-1", "Sender")
        recipient = _create_user(connection, "tenant-1", "Recipient")

        _create_issuance(
            connection,
            "tenant-1",
            sender,
            500,
        )

        service = TalentPointTransferService(
            TalentPointRepository(connection)
        )

        service.transfer(
            "tenant-1",
            sender,
            recipient,
            150,
        )

        repository = TalentPointRepository(connection)

        assert repository.get_balance(
            "tenant-1",
            sender,
        ) == 350

        assert repository.get_balance(
            "tenant-1",
            recipient,
        ) == 150

    finally:
        connection.close()


def test_transfer_does_not_increase_total_issued(
    tmp_path,
    monkeypatch,
):
    connection = _setup_db(tmp_path, monkeypatch)

    try:
        sender = _create_user(connection, "tenant-1", "Sender")
        recipient = _create_user(connection, "tenant-1", "Recipient")

        _create_issuance(
            connection,
            "tenant-1",
            sender,
            500,
        )

        repository = TalentPointRepository(connection)
        service = TalentPointTransferService(repository)

        assert repository.get_total_issued("tenant-1") == 500

        service.transfer(
            "tenant-1",
            sender,
            recipient,
            200,
        )

        assert repository.get_total_issued("tenant-1") == 500

    finally:
        connection.close()


def test_transfer_creates_exactly_two_transfer_entries(
    tmp_path,
    monkeypatch,
):
    connection = _setup_db(tmp_path, monkeypatch)

    try:
        sender = _create_user(connection, "tenant-1", "Sender")
        recipient = _create_user(connection, "tenant-1", "Recipient")

        _create_issuance(
            connection,
            "tenant-1",
            sender,
            500,
        )

        service = TalentPointTransferService(
            TalentPointRepository(connection)
        )

        service.transfer(
            "tenant-1",
            sender,
            recipient,
            100,
        )

        rows = connection.execute(
            """
            SELECT
                user_id,
                service_act_id,
                amount,
                transaction_type
            FROM talent_point_transactions
            WHERE tenant_id = ?
              AND transaction_type = 'transfer'
            ORDER BY id
            """,
            ("tenant-1",),
        ).fetchall()

        assert len(rows) == 2

        assert rows[0]["user_id"] == sender
        assert rows[0]["service_act_id"] is None
        assert rows[0]["amount"] == -100
        assert rows[0]["transaction_type"] == "transfer"

        assert rows[1]["user_id"] == recipient
        assert rows[1]["service_act_id"] is None
        assert rows[1]["amount"] == 100
        assert rows[1]["transaction_type"] == "transfer"

    finally:
        connection.close()


@pytest.mark.parametrize(
    "amount",
    [0, -1, -100],
)
def test_invalid_transfer_amount_is_rejected(
    tmp_path,
    monkeypatch,
    amount,
):
    connection = _setup_db(tmp_path, monkeypatch)

    try:
        sender = _create_user(connection, "tenant-1", "Sender")
        recipient = _create_user(connection, "tenant-1", "Recipient")

        _create_issuance(
            connection,
            "tenant-1",
            sender,
            500,
        )

        service = TalentPointTransferService(
            TalentPointRepository(connection)
        )

        with pytest.raises(ValueError):
            service.transfer(
                "tenant-1",
                sender,
                recipient,
                amount,
            )

    finally:
        connection.close()


def test_non_integer_transfer_amount_is_rejected(
    tmp_path,
    monkeypatch,
):
    connection = _setup_db(tmp_path, monkeypatch)

    try:
        sender = _create_user(connection, "tenant-1", "Sender")
        recipient = _create_user(connection, "tenant-1", "Recipient")

        _create_issuance(
            connection,
            "tenant-1",
            sender,
            500,
        )

        service = TalentPointTransferService(
            TalentPointRepository(connection)
        )

        with pytest.raises(
            ValueError,
            match="integer",
        ):
            service.transfer(
                "tenant-1",
                sender,
                recipient,
                10.5,
            )

    finally:
        connection.close()


def test_self_transfer_is_rejected(
    tmp_path,
    monkeypatch,
):
    connection = _setup_db(tmp_path, monkeypatch)

    try:
        sender = _create_user(connection, "tenant-1", "Sender")

        _create_issuance(
            connection,
            "tenant-1",
            sender,
            500,
        )

        service = TalentPointTransferService(
            TalentPointRepository(connection)
        )

        with pytest.raises(
            ValueError,
            match="different users",
        ):
            service.transfer(
                "tenant-1",
                sender,
                sender,
                100,
            )

    finally:
        connection.close()


def test_insufficient_balance_is_rejected(
    tmp_path,
    monkeypatch,
):
    connection = _setup_db(tmp_path, monkeypatch)

    try:
        sender = _create_user(connection, "tenant-1", "Sender")
        recipient = _create_user(connection, "tenant-1", "Recipient")

        _create_issuance(
            connection,
            "tenant-1",
            sender,
            50,
        )

        service = TalentPointTransferService(
            TalentPointRepository(connection)
        )

        with pytest.raises(
            ValueError,
            match="insufficient",
        ):
            service.transfer(
                "tenant-1",
                sender,
                recipient,
                100,
            )

    finally:
        connection.close()


def test_sender_must_exist_in_tenant(
    tmp_path,
    monkeypatch,
):
    connection = _setup_db(tmp_path, monkeypatch)

    try:
        recipient = _create_user(
            connection,
            "tenant-1",
            "Recipient",
        )

        service = TalentPointTransferService(
            TalentPointRepository(connection)
        )

        with pytest.raises(
            ValueError,
            match="sender user not found",
        ):
            service.transfer(
                "tenant-1",
                999999,
                recipient,
                100,
            )

    finally:
        connection.close()


def test_recipient_must_exist_in_tenant(
    tmp_path,
    monkeypatch,
):
    connection = _setup_db(tmp_path, monkeypatch)

    try:
        sender = _create_user(
            connection,
            "tenant-1",
            "Sender",
        )

        _create_issuance(
            connection,
            "tenant-1",
            sender,
            500,
        )

        service = TalentPointTransferService(
            TalentPointRepository(connection)
        )

        with pytest.raises(
            ValueError,
            match="recipient user not found",
        ):
            service.transfer(
                "tenant-1",
                sender,
                999999,
                100,
            )

    finally:
        connection.close()


def test_cross_tenant_sender_is_rejected(
    tmp_path,
    monkeypatch,
):
    connection = _setup_db(tmp_path, monkeypatch)

    try:
        tenant_2_sender = _create_user(
            connection,
            "tenant-2",
            "Tenant 2 Sender",
        )

        tenant_1_recipient = _create_user(
            connection,
            "tenant-1",
            "Tenant 1 Recipient",
        )

        _create_issuance(
            connection,
            "tenant-2",
            tenant_2_sender,
            500,
        )

        service = TalentPointTransferService(
            TalentPointRepository(connection)
        )

        with pytest.raises(
            ValueError,
            match="sender user not found",
        ):
            service.transfer(
                "tenant-1",
                tenant_2_sender,
                tenant_1_recipient,
                100,
            )

    finally:
        connection.close()


def test_cross_tenant_recipient_is_rejected(
    tmp_path,
    monkeypatch,
):
    connection = _setup_db(tmp_path, monkeypatch)

    try:
        tenant_1_sender = _create_user(
            connection,
            "tenant-1",
            "Tenant 1 Sender",
        )

        tenant_2_recipient = _create_user(
            connection,
            "tenant-2",
            "Tenant 2 Recipient",
        )

        _create_issuance(
            connection,
            "tenant-1",
            tenant_1_sender,
            500,
        )

        service = TalentPointTransferService(
            TalentPointRepository(connection)
        )

        with pytest.raises(
            ValueError,
            match="recipient user not found",
        ):
            service.transfer(
                "tenant-1",
                tenant_1_sender,
                tenant_2_recipient,
                100,
            )

    finally:
        connection.close()


def test_transfer_is_tenant_isolated(
    tmp_path,
    monkeypatch,
):
    connection = _setup_db(tmp_path, monkeypatch)

    try:
        tenant_1_sender = _create_user(
            connection,
            "tenant-1",
            "Tenant 1 Sender",
        )

        tenant_1_recipient = _create_user(
            connection,
            "tenant-1",
            "Tenant 1 Recipient",
        )

        tenant_2_user = _create_user(
            connection,
            "tenant-2",
            "Tenant 2 User",
        )

        _create_issuance(
            connection,
            "tenant-1",
            tenant_1_sender,
            500,
        )

        _create_issuance(
            connection,
            "tenant-2",
            tenant_2_user,
            900,
            service_act_id=None,
        )

        service = TalentPointTransferService(
            TalentPointRepository(connection)
        )

        service.transfer(
            "tenant-1",
            tenant_1_sender,
            tenant_1_recipient,
            100,
        )

        repository = TalentPointRepository(connection)

        assert repository.get_balance(
            "tenant-1",
            tenant_1_sender,
        ) == 400

        assert repository.get_balance(
            "tenant-1",
            tenant_1_recipient,
        ) == 100

        assert repository.get_balance(
            "tenant-2",
            tenant_2_user,
        ) == 900

        assert repository.get_total_issued(
            "tenant-1",
        ) == 500

        assert repository.get_total_issued(
            "tenant-2",
        ) == 900

    finally:
        connection.close()


def test_failed_transfer_leaves_ledger_unchanged(
    tmp_path,
    monkeypatch,
):
    connection = _setup_db(tmp_path, monkeypatch)

    try:
        sender = _create_user(connection, "tenant-1", "Sender")
        recipient = _create_user(connection, "tenant-1", "Recipient")

        _create_issuance(
            connection,
            "tenant-1",
            sender,
            500,
        )

        repository = TalentPointRepository(connection)
        service = TalentPointTransferService(repository)

        with pytest.raises(ValueError):
            service.transfer(
                "tenant-1",
                sender,
                recipient,
                1000,
            )

        transfer_rows = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM talent_point_transactions
            WHERE tenant_id = ?
              AND transaction_type = 'transfer'
            """,
            ("tenant-1",),
        ).fetchone()

        assert transfer_rows["count"] == 0

        assert repository.get_balance(
            "tenant-1",
            sender,
        ) == 500

        assert repository.get_balance(
            "tenant-1",
            recipient,
        ) == 0

    finally:
        connection.close()
