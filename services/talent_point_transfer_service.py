from audit import audit_event
from models.talent_point import TalentPointTransaction
from services.talent_point_policy import TalentPointPolicy
from services.permission_resolution_service import PermissionResolutionService


class TalentPointTransferService:
    """
    Application service responsible for transferring Talent Points
    between users within the same tenant.

    Economic rules:
    - Transfer amount must be a positive integer.
    - Sender and recipient must belong to the same tenant.
    - Sender and recipient must be different users.
    - Sender must have sufficient TP balance.
    - Transfers do not create new TP.
    - Transfers are represented as two immutable ledger entries:
        sender    -> negative amount
        recipient -> positive amount
    - A transfer has no Service Act.
    - Debit, credit, and audit event are one atomic transaction.
    - Failed audit persistence rolls back the entire transfer.
    """

    def __init__(
        self,
        repository,
        permission_service: PermissionResolutionService,
    ):
        self.repository = repository
        self.permission_service = permission_service

    def transfer(
        self,
        tenant_id: str,
        actor_user_id: int,
        sender_user_id: int,
        recipient_user_id: int,
        amount: int,
        reference: str | None = None,
    ) -> tuple[
        TalentPointTransaction,
        TalentPointTransaction,
    ]:

        # ---------------------------------------------------------
        # 1. Authorize authenticated actor
        # ---------------------------------------------------------
        if not self.permission_service.has_permission(
            user_id=actor_user_id,
            permission_name="talent_point.transfer",
            tenant_id=tenant_id,
        ):
            raise PermissionError("talent point transfer permission denied")

        if actor_user_id != sender_user_id:
            raise PermissionError("transfer actor must be the sender")

        # ---------------------------------------------------------
        # 2. Validate amount
        # ---------------------------------------------------------
        TalentPointPolicy.validate_amount(amount)

        # ---------------------------------------------------------
        # 2. Validate sender / recipient
        # ---------------------------------------------------------
        if sender_user_id == recipient_user_id:
            raise ValueError("sender and recipient must be different users")

        connection = self.repository.connection

        # ---------------------------------------------------------
        # 3. Verify both users exist inside the tenant
        # ---------------------------------------------------------
        sender = connection.execute(
            """
            SELECT id
            FROM users
            WHERE tenant_id = ?
              AND id = ?
            """,
            (tenant_id, sender_user_id),
        ).fetchone()

        if sender is None:
            raise ValueError("sender user not found")

        recipient = connection.execute(
            """
            SELECT id
            FROM users
            WHERE tenant_id = ?
              AND id = ?
            """,
            (tenant_id, recipient_user_id),
        ).fetchone()

        if recipient is None:
            raise ValueError("recipient user not found")

        # ---------------------------------------------------------
        # 4. Verify sufficient balance
        # ---------------------------------------------------------
        sender_balance = self.repository.get_balance(
            tenant_id,
            sender_user_id,
        )

        if sender_balance < amount:
            raise ValueError("insufficient Talent Point balance")

        # ---------------------------------------------------------
        # 5. Create atomic ledger entries
        # ---------------------------------------------------------
        debit = TalentPointTransaction(
            id=None,
            tenant_id=tenant_id,
            user_id=sender_user_id,
            service_act_id=None,
            amount=-amount,
            transaction_type="transfer",
            reference=reference,
            created_at=None,
        )

        credit = TalentPointTransaction(
            id=None,
            tenant_id=tenant_id,
            user_id=recipient_user_id,
            service_act_id=None,
            amount=amount,
            transaction_type="transfer",
            reference=reference,
            created_at=None,
        )

        try:
            if connection.in_transaction:
                connection.commit()

            connection.execute("BEGIN")

            debit = self.repository.create(debit)
            credit = self.repository.create(credit)

            # -----------------------------------------------------
            # 6. Audit the complete economic operation
            # -----------------------------------------------------
            audit_event(
                event_type="talent_point_transfer",
                actor_id=actor_user_id,
                tenant_id=tenant_id,
                action="transfer_talent_points",
                metadata={
                    "debit_transaction_id": debit.id,
                    "credit_transaction_id": credit.id,
                    "sender_user_id": sender_user_id,
                    "recipient_user_id": recipient_user_id,
                    "amount": amount,
                    "transaction_type": "transfer",
                    "reference": reference,
                },
                connection=connection,
            )

            connection.commit()

            return debit, credit

        except Exception:
            connection.rollback()
            raise
