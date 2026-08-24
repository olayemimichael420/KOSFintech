from typing import Optional

from models.verification import Verification, VerificationDecision


class VerificationRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(self, verification: Verification) -> Verification:
        cursor = self.connection.execute(
            """
            INSERT INTO verifications (
                tenant_id,
                service_act_id,
                verifier_user_id,
                decision,
                reason
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                verification.tenant_id,
                verification.service_act_id,
                verification.verifier_user_id,
                verification.decision.value,
                verification.reason,
            ),
        )

        self.connection.commit()
        verification.id = cursor.lastrowid
        return self.get(verification.tenant_id, verification.id)

    def get(
        self,
        tenant_id: str,
        verification_id: int,
    ) -> Optional[Verification]:
        row = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                service_act_id,
                verifier_user_id,
                decision,
                reason
            FROM verifications
            WHERE tenant_id = ?
              AND id = ?
            """,
            (tenant_id, verification_id),
        ).fetchone()

        return self._to_model(row) if row else None

    def list_by_act(
        self,
        tenant_id: str,
        service_act_id: int,
    ) -> list[Verification]:
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                service_act_id,
                verifier_user_id,
                decision,
                reason
            FROM verifications
            WHERE tenant_id = ?
              AND service_act_id = ?
            ORDER BY id
            """,
            (tenant_id, service_act_id),
        ).fetchall()

        return [self._to_model(row) for row in rows]

    @staticmethod
    def _to_model(row) -> Verification:
        return Verification(
            id=row["id"],
            tenant_id=row["tenant_id"],
            service_act_id=row["service_act_id"],
            verifier_user_id=row["verifier_user_id"],
            decision=VerificationDecision(row["decision"]),
            reason=row["reason"],
        )
