from datetime import datetime, timezone

from audit import audit_event
from models.judicial_action import JudicialAction
from models.judicial_decision import JudicialDecision
from models.judicial_proceeding import JudicialProceeding, JudicialProceedingStatus
from services.judicial_authorization_service import (
    JudicialAuthorizationService,
)
from services.judicial_recusal_enforcement_service import (
    JudicialRecusalEnforcementService,
)


class JudicialActionsDecisionsService:
    """
    Record judicial actions and decisions within active proceedings.

    This service does not adjudicate application disputes, mutate dispute
    state, mutate Talent Point balances, create or activate judicial
    authority, close proceedings, or implement appeals.
    """

    def __init__(self, connection):
        self.connection = connection
        self.authorization_service = JudicialAuthorizationService(connection)
        self.recusal_enforcement_service = (
            JudicialRecusalEnforcementService(connection)
        )

    def record_action(
        self,
        *,
        user_id: int,
        proceeding_id: int,
        action_type: str,
        action_details: str,
    ) -> JudicialAction:
        self._require_text(action_type, "action type")
        self._require_text(action_details, "action details")

        proceeding = self._require_active_proceeding(proceeding_id)
        authority = self._require_authorized_authority(
            user_id=user_id,
            jurisdiction_id=proceeding.jurisdiction_id,
        )

        self._require_same_tenant(
            proceeding.tenant_id,
            authority["tenant_id"],
        )

        self.recusal_enforcement_service.require_not_recused(
            tenant_id=proceeding.tenant_id,
            judicial_authority_id=authority["id"],
            jurisdiction_id=proceeding.jurisdiction_id,
            proceeding_id=proceeding.id,
        )

        now = datetime.now(timezone.utc).isoformat()

        try:
            self.connection.execute("BEGIN")

            cursor = self.connection.execute(
                """
                INSERT INTO judicial_actions (
                    tenant_id,
                    proceeding_id,
                    judicial_authority_id,
                    action_type,
                    action_details,
                    acted_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    proceeding.tenant_id,
                    proceeding.id,
                    authority["id"],
                    action_type.strip(),
                    action_details.strip(),
                    now,
                ),
            )

            action = self._get_action(
                proceeding.tenant_id,
                cursor.lastrowid,
            )

            audit_event(
                event_type="judicial_action_recorded",
                actor_id=user_id,
                tenant_id=proceeding.tenant_id,
                action="record_judicial_action",
                metadata={
                    "action_id": action.id,
                    "proceeding_id": action.proceeding_id,
                    "judicial_authority_id": action.judicial_authority_id,
                    "action_type": action.action_type,
                },
                connection=self.connection,
            )

            self.connection.commit()
            return action

        except Exception:
            self.connection.rollback()
            raise

    def record_decision(
        self,
        *,
        user_id: int,
        proceeding_id: int,
        decision_type: str,
        decision_reason: str,
    ) -> JudicialDecision:
        self._require_text(decision_type, "decision type")
        self._require_text(decision_reason, "decision reason")

        proceeding = self._require_active_proceeding(proceeding_id)
        authority = self._require_authorized_authority(
            user_id=user_id,
            jurisdiction_id=proceeding.jurisdiction_id,
        )

        self._require_same_tenant(
            proceeding.tenant_id,
            authority["tenant_id"],
        )

        self.recusal_enforcement_service.require_not_recused(
            tenant_id=proceeding.tenant_id,
            judicial_authority_id=authority["id"],
            jurisdiction_id=proceeding.jurisdiction_id,
            proceeding_id=proceeding.id,
        )

        now = datetime.now(timezone.utc).isoformat()

        try:
            self.connection.execute("BEGIN")

            cursor = self.connection.execute(
                """
                INSERT INTO judicial_decisions (
                    tenant_id,
                    proceeding_id,
                    judicial_authority_id,
                    decision_type,
                    decision_reason,
                    decided_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    proceeding.tenant_id,
                    proceeding.id,
                    authority["id"],
                    decision_type.strip(),
                    decision_reason.strip(),
                    now,
                ),
            )

            decision = self._get_decision(
                proceeding.tenant_id,
                cursor.lastrowid,
            )

            audit_event(
                event_type="judicial_decision_recorded",
                actor_id=user_id,
                tenant_id=proceeding.tenant_id,
                action="record_judicial_decision",
                metadata={
                    "decision_id": decision.id,
                    "proceeding_id": decision.proceeding_id,
                    "judicial_authority_id": decision.judicial_authority_id,
                    "decision_type": decision.decision_type,
                },
                connection=self.connection,
            )

            self.connection.commit()
            return decision

        except Exception:
            self.connection.rollback()
            raise

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

    def _require_active_proceeding(
        self,
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
            WHERE id = ?
            """,
            (proceeding_id,),
        ).fetchone()

        if proceeding is None:
            raise ValueError("judicial proceeding not found")

        status = JudicialProceedingStatus(proceeding["status"])

        if status != JudicialProceedingStatus.ACTIVE:
            raise ValueError(
                "only active judicial proceedings can receive "
                "judicial actions or decisions"
            )

        return self._to_proceeding(proceeding)

    def _get_action(
        self,
        tenant_id: str,
        action_id: int,
    ) -> JudicialAction:
        row = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                proceeding_id,
                judicial_authority_id,
                action_type,
                action_details,
                acted_at
            FROM judicial_actions
            WHERE tenant_id = ?
              AND id = ?
            """,
            (tenant_id, action_id),
        ).fetchone()

        if row is None:
            raise ValueError("judicial action not found")

        return JudicialAction(
            id=row["id"],
            tenant_id=row["tenant_id"],
            proceeding_id=row["proceeding_id"],
            judicial_authority_id=row["judicial_authority_id"],
            action_type=row["action_type"],
            action_details=row["action_details"],
            acted_at=row["acted_at"],
        )

    def _get_decision(
        self,
        tenant_id: str,
        decision_id: int,
    ) -> JudicialDecision:
        row = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                proceeding_id,
                judicial_authority_id,
                decision_type,
                decision_reason,
                decided_at
            FROM judicial_decisions
            WHERE tenant_id = ?
              AND id = ?
            """,
            (tenant_id, decision_id),
        ).fetchone()

        if row is None:
            raise ValueError("judicial decision not found")

        return JudicialDecision(
            id=row["id"],
            tenant_id=row["tenant_id"],
            proceeding_id=row["proceeding_id"],
            judicial_authority_id=row["judicial_authority_id"],
            decision_type=row["decision_type"],
            decision_reason=row["decision_reason"],
            decided_at=row["decided_at"],
        )

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
    def _to_proceeding(row) -> JudicialProceeding:
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
