from datetime import datetime, timezone
from typing import Optional

from audit import audit_event
from models.judicial_recusal import (
    JudicialRecusal,
    JudicialRecusalScope,
    JudicialRecusalStatus,
)
from services.judicial_authorization_service import (
    JudicialAuthorizationService,
)


class JudicialRecusalService:
    """
    Record and resolve judicial recusal records.

    This service does not adjudicate recusal grounds, deactivate judicial
    authority, suspend proceedings, alter disputes, mutate Talent Points,
    appoint replacement authority, or implement appeals/enforcement.
    """

    def __init__(self, connection):
        self.connection = connection
        self.authorization_service = JudicialAuthorizationService(connection)

    def record_recusal(
        self,
        *,
        user_id: int,
        judicial_authority_id: int,
        jurisdiction_id: int,
        scope: JudicialRecusalScope,
        reason: str,
        proceeding_id: Optional[int] = None,
    ) -> JudicialRecusal:
        self._require_text(reason, "recusal reason")
        scope = self._coerce_scope(scope)

        authority = self._require_authority(
            judicial_authority_id=judicial_authority_id,
            jurisdiction_id=jurisdiction_id,
        )

        user = self._require_active_user(user_id)

        self._require_same_tenant(
            authority["tenant_id"],
            user["tenant_id"],
        )

        self._require_authorized_jurisdiction(
            user_id=user_id,
            jurisdiction_id=jurisdiction_id,
        )

        if scope == JudicialRecusalScope.JURISDICTION:
            if proceeding_id is not None:
                raise ValueError(
                    "jurisdiction recusal cannot specify a proceeding"
                )
        else:
            if proceeding_id is None:
                raise ValueError(
                    "proceeding recusal requires a proceeding"
                )

            self._require_proceeding(
                proceeding_id=proceeding_id,
                tenant_id=authority["tenant_id"],
                jurisdiction_id=jurisdiction_id,
            )

        now = datetime.now(timezone.utc).isoformat()

        try:
            self.connection.execute("BEGIN")

            cursor = self.connection.execute(
                """
                INSERT INTO judicial_recusals (
                    tenant_id,
                    judicial_authority_id,
                    jurisdiction_id,
                    proceeding_id,
                    scope,
                    reason,
                    initiated_by,
                    recorded_at,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active')
                """,
                (
                    authority["tenant_id"],
                    authority["id"],
                    jurisdiction_id,
                    proceeding_id,
                    scope.value,
                    reason.strip(),
                    user_id,
                    now,
                ),
            )

            recusal = self._get(
                tenant_id=authority["tenant_id"],
                recusal_id=cursor.lastrowid,
            )

            audit_event(
                event_type="judicial_recusal_recorded",
                actor_id=user_id,
                tenant_id=authority["tenant_id"],
                action="record_judicial_recusal",
                metadata={
                    "recusal_id": recusal.id,
                    "judicial_authority_id": recusal.judicial_authority_id,
                    "jurisdiction_id": recusal.jurisdiction_id,
                    "proceeding_id": recusal.proceeding_id,
                    "scope": recusal.scope.value,
                },
                connection=self.connection,
            )

            self.connection.commit()
            return recusal

        except Exception:
            self.connection.rollback()
            raise

    def resolve_recusal(
        self,
        *,
        user_id: int,
        recusal_id: int,
    ) -> JudicialRecusal:
        recusal = self._require_recusal(recusal_id)

        self._require_active_user(user_id)
        self._require_authorized_jurisdiction(
            user_id=user_id,
            jurisdiction_id=recusal.jurisdiction_id,
        )

        if recusal.status != JudicialRecusalStatus.ACTIVE:
            raise ValueError(
                "only active judicial recusals can be resolved"
            )

        now = datetime.now(timezone.utc).isoformat()

        try:
            self.connection.execute("BEGIN")

            self.connection.execute(
                """
                UPDATE judicial_recusals
                SET status = 'resolved',
                    resolved_at = ?
                WHERE id = ?
                  AND tenant_id = ?
                  AND status = 'active'
                """,
                (
                    now,
                    recusal.id,
                    recusal.tenant_id,
                ),
            )

            resolved = self._get(
                tenant_id=recusal.tenant_id,
                recusal_id=recusal.id,
            )

            audit_event(
                event_type="judicial_recusal_resolved",
                actor_id=user_id,
                tenant_id=recusal.tenant_id,
                action="resolve_judicial_recusal",
                metadata={
                    "recusal_id": resolved.id,
                    "judicial_authority_id": (
                        resolved.judicial_authority_id
                    ),
                    "jurisdiction_id": resolved.jurisdiction_id,
                    "proceeding_id": resolved.proceeding_id,
                },
                connection=self.connection,
            )

            self.connection.commit()
            return resolved

        except Exception:
            self.connection.rollback()
            raise

    def _require_authority(
        self,
        *,
        judicial_authority_id: int,
        jurisdiction_id: int,
    ):
        authority = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                user_id,
                jurisdiction_id,
                status
            FROM judicial_authorities
            WHERE id = ?
            """,
            (judicial_authority_id,),
        ).fetchone()

        if authority is None:
            raise ValueError("judicial authority not found")

        if authority["jurisdiction_id"] != jurisdiction_id:
            raise ValueError(
                "judicial authority jurisdiction mismatch"
            )

        if authority["status"] != "active":
            raise ValueError("judicial authority is inactive")

        return authority

    def _require_active_user(self, user_id: int):
        user = self.connection.execute(
            """
            SELECT id, tenant_id, status
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()

        if user is None:
            raise ValueError("authenticated user not found")

        if user["status"] != "active":
            raise ValueError("authenticated user is inactive")

        return user

    def _require_authorized_jurisdiction(
        self,
        *,
        user_id: int,
        jurisdiction_id: int,
    ) -> None:
        decision = self.authorization_service.authorize_decision(
            user_id=user_id,
            jurisdiction_id=jurisdiction_id,
        )

        if not decision.allowed:
            raise ValueError(decision.reason)

    def _require_proceeding(
        self,
        *,
        proceeding_id: int,
        tenant_id: str,
        jurisdiction_id: int,
    ) -> None:
        proceeding = self.connection.execute(
            """
            SELECT id, tenant_id, jurisdiction_id
            FROM judicial_proceedings
            WHERE id = ?
              AND tenant_id = ?
            """,
            (proceeding_id, tenant_id),
        ).fetchone()

        if proceeding is None:
            raise ValueError("judicial proceeding not found")

        if proceeding["jurisdiction_id"] != jurisdiction_id:
            raise ValueError(
                "judicial proceeding jurisdiction mismatch"
            )

    def _require_recusal(self, recusal_id: int) -> JudicialRecusal:
        recusal = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                judicial_authority_id,
                jurisdiction_id,
                proceeding_id,
                scope,
                reason,
                initiated_by,
                recorded_at,
                resolved_at,
                status
            FROM judicial_recusals
            WHERE id = ?
            """,
            (recusal_id,),
        ).fetchone()

        if recusal is None:
            raise ValueError("judicial recusal not found")

        return self._to_model(recusal)

    def _get(
        self,
        *,
        tenant_id: str,
        recusal_id: int,
    ) -> JudicialRecusal:
        recusal = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                judicial_authority_id,
                jurisdiction_id,
                proceeding_id,
                scope,
                reason,
                initiated_by,
                recorded_at,
                resolved_at,
                status
            FROM judicial_recusals
            WHERE id = ?
              AND tenant_id = ?
            """,
            (recusal_id, tenant_id),
        ).fetchone()

        if recusal is None:
            raise ValueError("judicial recusal not found")

        return self._to_model(recusal)

    @staticmethod
    def _coerce_scope(scope) -> JudicialRecusalScope:
        try:
            return JudicialRecusalScope(scope)
        except (TypeError, ValueError):
            raise ValueError("invalid judicial recusal scope")

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
    def _to_model(row) -> JudicialRecusal:
        return JudicialRecusal(
            id=row["id"],
            tenant_id=row["tenant_id"],
            judicial_authority_id=row["judicial_authority_id"],
            jurisdiction_id=row["jurisdiction_id"],
            proceeding_id=row["proceeding_id"],
            scope=JudicialRecusalScope(row["scope"]),
            reason=row["reason"],
            initiated_by=row["initiated_by"],
            recorded_at=row["recorded_at"],
            resolved_at=row["resolved_at"],
            status=JudicialRecusalStatus(row["status"]),
        )
