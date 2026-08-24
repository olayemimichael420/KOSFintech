from datetime import datetime, timezone
from typing import Optional

from models.talent_point import TalentPointTransaction


class TalentPointRepository:
    """Persistence layer for the Talent Points ledger."""

    def __init__(self, connection):
        self.connection = connection

    def create(
        self,
        transaction: TalentPointTransaction,
    ) -> TalentPointTransaction:
        cursor = self.connection.execute(
            """
            INSERT INTO talent_point_transactions (
                tenant_id,
                user_id,
                service_act_id,
                amount,
                transaction_type,
                reference
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                transaction.tenant_id,
                transaction.user_id,
                transaction.service_act_id,
                transaction.amount,
                transaction.transaction_type,
                transaction.reference,
            ),
        )

        self.connection.commit()

        transaction.id = cursor.lastrowid

        return self.get(
            transaction.tenant_id,
            transaction.id,
        )

    def get(
        self,
        tenant_id: str,
        transaction_id: int,
    ) -> Optional[TalentPointTransaction]:
        row = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                user_id,
                service_act_id,
                amount,
                transaction_type,
                reference,
                created_at
            FROM talent_point_transactions
            WHERE tenant_id = ?
              AND id = ?
            """,
            (
                tenant_id,
                transaction_id,
            ),
        ).fetchone()

        return self._to_model(row) if row else None

    def list_by_user(
        self,
        tenant_id: str,
        user_id: int,
    ) -> list[TalentPointTransaction]:
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                user_id,
                service_act_id,
                amount,
                transaction_type,
                reference,
                created_at
            FROM talent_point_transactions
            WHERE tenant_id = ?
              AND user_id = ?
            ORDER BY id
            """,
            (
                tenant_id,
                user_id,
            ),
        ).fetchall()

        return [self._to_model(row) for row in rows]

    def list_by_service_act(
        self,
        tenant_id: str,
        service_act_id: int,
    ) -> list[TalentPointTransaction]:
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                user_id,
                service_act_id,
                amount,
                transaction_type,
                reference,
                created_at
            FROM talent_point_transactions
            WHERE tenant_id = ?
              AND service_act_id = ?
            ORDER BY id
            """,
            (
                tenant_id,
                service_act_id,
            ),
        ).fetchall()

        return [self._to_model(row) for row in rows]

    def get_balance(
        self,
        tenant_id: str,
        user_id: int,
    ) -> int:
        row = self.connection.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS balance
            FROM talent_point_transactions
            WHERE tenant_id = ?
              AND user_id = ?
            """,
            (
                tenant_id,
                user_id,
            ),
        ).fetchone()

        return int(row["balance"])

    def get_total_issued(
        self,
        tenant_id: str,
    ) -> int:
        row = self.connection.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS total
            FROM talent_point_transactions
            WHERE tenant_id = ?
              AND transaction_type = 'issuance'
            """,
            (tenant_id,),
        ).fetchone()

        return int(row["total"])

        # Normalize UTC timestamps to SQLite CURRENT_TIMESTAMP format.
    def get_issued_since(
        self,
        tenant_id: str,
        start_time: datetime,
    ) -> int:
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)

        start_time = start_time.astimezone(timezone.utc)

        timestamp = start_time.strftime("%Y-%m-%d %H:%M:%S")

        row = self.connection.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS total
            FROM talent_point_transactions
            WHERE tenant_id = ?
              AND transaction_type = 'issuance'
              AND created_at >= ?
            """,
            (
                tenant_id,
                timestamp,
            ),
        ).fetchone()

        return int(row["total"])

    def issuance_exists_for_service_act(

        self,
        tenant_id: str,
        service_act_id: int,
    ) -> bool:
        row = self.connection.execute(
            """
            SELECT 1
            FROM talent_point_transactions
            WHERE tenant_id = ?
              AND service_act_id = ?
              AND transaction_type = 'issuance'
            LIMIT 1
            """,
            (
                tenant_id,
                service_act_id,
            ),
        ).fetchone()

        return row is not None

    @staticmethod
    def _to_model(row) -> TalentPointTransaction:
        return TalentPointTransaction(
            id=row["id"],
            tenant_id=row["tenant_id"],
            user_id=row["user_id"],
            service_act_id=row["service_act_id"],
            amount=row["amount"],
            transaction_type=row["transaction_type"],
            reference=row["reference"],
            created_at=row["created_at"],
        )
