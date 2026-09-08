from datetime import datetime, timezone
from typing import Optional

from audit import audit_event
from models.judicial_proceeding import (
    JudicialProceeding,
    JudicialProceedingStatus,
)
from services.judicial_authorization_service import (
    JudicialAuthorizationService,
)


class JudicialProceedingsService:
    """
    Manage the lifecycle of judicial proceedings.

    This service does not adjudicate disputes, resolve application disputes,
    mutate Talent Point balances, create judicial authority, or implement
    appeals.
    """

    def __init__(self, connection):
        self.connection = connection
        self.authorization_service = JudicialAuthorizationService(connection)

    def create_proceeding(
        self,
        *,
        user_id: int,
        dispute_id: int,
        jurisdiction_id: int,
        proceeding_type: str,
    ) -> JudicialProceeding:
        self._require_text(proceeding_type, "proceeding type")

        authority = self._require_authorized_authority(
            user_id=user_id,
            jurisdiction_id=jurisdiction_id,
        )

        dispute = self.connection.execute(
            """
            SELECT id, tenant_id
            FROM disputes
            WHERE id = ?
              AND tenant_id = ?
            """,
            (dispute_id, authority["tenant_id"]),
        ).fetchone()

        if dispute is None:
            raise ValueError("judicial dispute not found")

        jurisdiction = self.connection.execute(
            """
            SELECT id, tenant_id, status
            FROM judicial_jurisdictions
            WHERE id = ?
              AND tenant_id = ?
            """,
            (jurisdiction_id, authority["tenant_id"]),
        ).fetchone()

        if jurisdiction is None:
            raise ValueError("judicial jurisdiction not found")

        if jurisdiction["status"] != "active":
            raise ValueError("judicial jurisdiction is inactive")

        connection = self.connection

        try:
            connection.execute("BEGIN")

            cursor = connection.execute(
                """
                INSERT INTO judicial_proceedings (
                    tenant_id,
                    dispute_id,
                    jurisdiction_id,
                    proceeding_type,
                    status,
                    opened_by_authority_id
                )
                VALUES (?, ?, ?, ?, 'proposed', ?)
                """,
                (
                    authority["tenant_id"],
                    dispute_id,
                    jurisdiction_id,
                    proceeding_type.strip(),
                    authority["id"],
                ),
            )

            proceeding = self._get(
                authority["tenant_id"],
                cursor.lastrowid,
            )

            audit_event(
                event_type="judicial_proceeding_created",
                actor_id=user_id,
                tenant_id=authority["tenant_id"],
                action="create_judicial_proceeding",
                metadata={
                    "proceeding_id": proceeding.id,
                    "dispute_id": proceeding.dispute_id,
                    "jurisdiction_id": proceeding.jurisdiction_id,
                    "judicial_authority_id": authority["id"],
                },
                connection=connection,
            )

            connection.commit()
            return proceeding

        except Exception:
            connection.rollback()
            raise

    def open_proceeding(
        self,
        *,
        user_id: int,
        proceeding_id: int,
    ) -> JudicialProceeding:
        proceeding = self._require_proceeding(proceeding_id)
        authority = self._require_authorized_authority(
            user_id=user_id,
            jurisdiction_id=proceeding.jurisdiction_id,
        )

        self._require_same_tenant(proceeding.tenant_id, authority["tenant_id"])

        if proceeding.status != JudicialProceedingStatus.PROPOSED:
            raise ValueError(
                "only proposed judicial proceedings can be opened"
            )

        if proceeding.opened_by_authority_id != authority["id"]:
            raise ValueError("judicial proceeding opening authority mismatch")

        now = datetime.now(timezone.utc).isoformat()

        return self._transition(
            proceeding=proceeding,
            authority=authority,
            user_id=user_id,
            new_status=JudicialProceedingStatus.OPEN,
            timestamp_field="opened_at",
            timestamp=now,
            event_type="judicial_proceeding_opened",
            action="open_judicial_proceeding",
        )

    def activate_proceeding(
        self,
        *,
        user_id: int,
        proceeding_id: int,
    ) -> JudicialProceeding:
        proceeding = self._require_proceeding(proceeding_id)
        authority = self._require_authorized_authority(
            user_id=user_id,
            jurisdiction_id=proceeding.jurisdiction_id,
        )

        self._require_same_tenant(proceeding.tenant_id, authority["tenant_id"])

        if proceeding.status != JudicialProceedingStatus.OPEN:
            raise ValueError(
                "only open judicial proceedings can be activated"
            )

        return self._transition(
            proceeding=proceeding,
            authority=authority,
            user_id=user_id,
            new_status=JudicialProceedingStatus.ACTIVE,
            event_type="judicial_proceeding_activated",
            action="activate_judicial_proceeding",
        )

    def close_proceeding(
        self,
        *,
        user_id: int,
        proceeding_id: int,
        closure_reason: str,
    ) -> JudicialProceeding:
        self._require_text(closure_reason, "closure reason")

        proceeding = self._require_proceeding(proceeding_id)
        authority = self._require_authorized_authority(
            user_id=user_id,
            jurisdiction_id=proceeding.jurisdiction_id,
        )

        self._require_same_tenant(proceeding.tenant_id, authority["tenant_id"])

        if proceeding.status != JudicialProceedingStatus.ACTIVE:
            raise ValueError(
                "only active judicial proceedings can be closed"
            )

        now = datetime.now(timezone.utc).isoformat()

        return self._transition(
            proceeding=proceeding,
            authority=authority,
            user_id=user_id,
            new_status=JudicialProceedingStatus.CLOSED,
            timestamp_field="closed_at",
            timestamp=now,
            closure_reason=closure_reason.strip(),
            event_type="judicial_proceeding_closed",
            action="close_judicial_proceeding",
        )

    def terminate_proceeding(
        self,
        *,
        user_id: int,
        proceeding_id: int,
        termination_reason: str,
    ) -> JudicialProceeding:
        self._require_text(termination_reason, "termination reason")

        proceeding = self._require_proceeding(proceeding_id)
        authority = self._require_authorized_authority(
            user_id=user_id,
            jurisdiction_id=proceeding.jurisdiction_id,
        )

        self._require_same_tenant(proceeding.tenant_id, authority["tenant_id"])

        allowed_statuses = {
            JudicialProceedingStatus.PROPOSED,
            JudicialProceedingStatus.OPEN,
            JudicialProceedingStatus.ACTIVE,
        }

        if proceeding.status not in allowed_statuses:
            raise ValueError(
                "only proposed, open, or active judicial proceedings "
                "can be terminated"
            )

        now = datetime.now(timezone.utc).isoformat()

        return self._transition(
            proceeding=proceeding,
            authority=authority,
            user_id=user_id,
            new_status=JudicialProceedingStatus.TERMINATED,
            timestamp_field="closed_at",
            timestamp=now,
            closure_reason=termination_reason.strip(),
            event_type="judicial_proceeding_terminated",
            action="terminate_judicial_proceeding",
        )

    def _require_authorized_authority(
        self,
        *,
        user_id: int,
        jurisdiction_id: int,
    ):
        decision = self.authorization_service.authorize_decision(
            user_id=user_id,
            jurisdiction_id=jurisdiction_id,
        )

        if not decision.allowed:
            raise ValueError(decision.reason)

        user = self.connection.execute(
            """
            SELECT id, tenant_id
            FROM users
            WHERE id = ?
              AND status = 'active'
            """,
            (user_id,),
        ).fetchone()

        if user is None:
            raise ValueError("authenticated user not found")

        authority = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                user_id,
                jurisdiction_id,
                status
            FROM judicial_authorities
            WHERE user_id = ?
              AND tenant_id = ?
              AND jurisdiction_id = ?
              AND status = 'active'
            ORDER BY id DESC
            LIMIT 1
            """,
            (user_id, user["tenant_id"], jurisdiction_id),
        ).fetchone()

        if authority is None:
            raise ValueError("active judicial authority not found")

        return authority

    def _require_proceeding(self, proceeding_id: int) -> JudicialProceeding:
        proceeding = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                dispute_id,
                jurisdiction_id,
                proceeding_type,
                status,
                opened_by_authority_id,
                opened_at,
                closed_at,
                closure_reason
            FROM judicial_proceedings
            WHERE id = ?
            """,
            (proceeding_id,),
        ).fetchone()

        if proceeding is None:
            raise ValueError("judicial proceeding not found")

        return self._to_model(proceeding)

    def _get(
        self,
        tenant_id: str,
        proceeding_id: int,
    ) -> JudicialProceeding:
        proceeding = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                dispute_id,
                jurisdiction_id,
                proceeding_type,
                status,
                opened_by_authority_id,
                opened_at,
                closed_at,
                closure_reason
            FROM judicial_proceedings
            WHERE tenant_id = ?
              AND id = ?
            """,
            (tenant_id, proceeding_id),
        ).fetchone()

        if proceeding is None:
            raise ValueError("judicial proceeding not found")

        return self._to_model(proceeding)

    def _transition(
        self,
        *,
        proceeding: JudicialProceeding,
        authority,
        user_id: int,
        new_status: JudicialProceedingStatus,
        timestamp_field: Optional[str] = None,
        timestamp: Optional[str] = None,
        closure_reason: Optional[str] = None,
        event_type: str,
        action: str,
    ) -> JudicialProceeding:
        assignments = ["status = ?"]
        values = [new_status.value]

        if timestamp_field is not None:
            assignments.append(f"{timestamp_field} = ?")
            values.append(timestamp)

        if closure_reason is not None:
            assignments.append("closure_reason = ?")
            values.append(closure_reason)

        values.extend([proceeding.tenant_id, proceeding.id])

        try:
            self.connection.execute("BEGIN")

            self.connection.execute(
                f"""
                UPDATE judicial_proceedings
                SET {", ".join(assignments)}
                WHERE tenant_id = ?
                  AND id = ?
                """,
                tuple(values),
            )

            updated = self._get(
                proceeding.tenant_id,
                proceeding.id,
            )

            audit_event(
                event_type=event_type,
                actor_id=user_id,
                tenant_id=proceeding.tenant_id,
                action=action,
                metadata={
                    "proceeding_id": updated.id,
                    "dispute_id": updated.dispute_id,
                    "jurisdiction_id": updated.jurisdiction_id,
                    "judicial_authority_id": authority["id"],
                    "status": updated.status.value,
                },
                connection=self.connection,
            )

            self.connection.commit()
            return updated

        except Exception:
            self.connection.rollback()
            raise

    @staticmethod
    def _require_text(value: str, field: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} is required")

    @staticmethod
    def _require_same_tenant(
        expected_tenant: str,
        actual_tenant: str,
    ) -> None:
        if expected_tenant != actual_tenant:
            raise ValueError("tenant mismatch")

    @staticmethod
    def _to_model(row) -> JudicialProceeding:
        return JudicialProceeding(
            id=row["id"],
            tenant_id=row["tenant_id"],
            dispute_id=row["dispute_id"],
            jurisdiction_id=row["jurisdiction_id"],
            proceeding_type=row["proceeding_type"],
            status=JudicialProceedingStatus(row["status"]),
            opened_by_authority_id=row["opened_by_authority_id"],
            opened_at=row["opened_at"],
            closed_at=row["closed_at"],
            closure_reason=row["closure_reason"],
        )
