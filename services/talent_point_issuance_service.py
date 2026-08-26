from datetime import datetime, timezone

from audit import audit_event
from models.service_act import ServiceActStatus
from models.talent_point import TalentPointTransaction
from services.talent_point_policy import TalentPointPolicy


class TalentPointIssuanceService:
    """
    Application service responsible for issuing Talent Points
    for completed Service Acts.

    Economic rules:
    - Only completed Service Acts may receive TP.
    - Provider receives the TP.
    - Amount must be a positive integer.
    - A Service Act may receive only one issuance.
    - Daily issuance is capped at 50,000 TP.
    - Total TP supply is capped at 100,000,000 TP.
    - Tenant boundaries must be respected.
    - Successful issuance emits a structured audit event.
    """

    def __init__(self, repository):
        self.repository = repository

    def issue_for_service_act(
        self,
        tenant_id: str,
        service_act,
        amount: int,
        reference: str | None = None,
    ) -> TalentPointTransaction:

        # ---------------------------------------------------------
        # 1. Tenant integrity
        # ---------------------------------------------------------
        if service_act.tenant_id != tenant_id:
            raise ValueError("tenant mismatch")

        # ---------------------------------------------------------
        # 2. Service Act must be completed
        # ---------------------------------------------------------
        if service_act.status != ServiceActStatus.COMPLETED:
            raise ValueError(
                "Talent Points can only be issued for completed Service Acts"
            )

        # ---------------------------------------------------------
        # 3. Validate TP amount
        # ---------------------------------------------------------
        TalentPointPolicy.validate_amount(amount)

        # ---------------------------------------------------------
        # 4. Prevent duplicate issuance
        # ---------------------------------------------------------
        if self.repository.issuance_exists_for_service_act(
            tenant_id,
            service_act.id,
        ):
            raise ValueError(
                "Talent Point issuance already exists for service act"
            )

        # ---------------------------------------------------------
        # 5. Determine current UTC day
        # ---------------------------------------------------------
        now = datetime.now(timezone.utc)
        start_of_day = now.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        # ---------------------------------------------------------
        # 6. Enforce total supply cap
        # ---------------------------------------------------------
        current_total_issued = self.repository.get_total_issued(
            tenant_id,
        )

        TalentPointPolicy.validate_total_supply(
            current_total_issued,
            amount,
        )

        # ---------------------------------------------------------
        # 7. Enforce daily minting cap
        # ---------------------------------------------------------
        current_daily_issued = self.repository.get_issued_since(
            tenant_id,
            start_of_day,
        )

        TalentPointPolicy.validate_daily_cap(
            current_daily_issued,
            amount,
        )

        # ---------------------------------------------------------
        # 8. Create immutable issuance ledger transaction
        # ---------------------------------------------------------
        transaction = TalentPointTransaction(
            id=None,
            tenant_id=tenant_id,
            user_id=service_act.provider_user_id,
            service_act_id=service_act.id,
            amount=amount,
            transaction_type="issuance",
            reference=reference,
            created_at=None,
        )

        connection = self.repository.connection

        try:
            connection.execute("BEGIN")

            transaction = self.repository.create(transaction)

            # ---------------------------------------------------------
            # 9. Emit audit event using the SAME transaction
            # ---------------------------------------------------------
            audit_event(
                event_type="talent_point_issuance",
                actor_id=transaction.user_id,
                tenant_id=transaction.tenant_id,
                action="issue_talent_points",
                metadata={
                    "transaction_id": transaction.id,
                    "service_act_id": transaction.service_act_id,
                    "user_id": transaction.user_id,
                    "amount": transaction.amount,
                    "transaction_type": transaction.transaction_type,
                    "reference": transaction.reference,
                },
                connection=connection,
            )

            connection.commit()

            # ---------------------------------------------------------
            # 10. Return committed transaction
            # ---------------------------------------------------------
            return transaction

        except Exception:
            connection.rollback()
            raise
