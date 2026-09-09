from services.judicial_authorization_service import (
    JudicialAuthorizationService,
)
from services.judicial_proceedings_service import (
    JudicialProceedingsService,
)


class JudicialDecisionClosureService:
    """
    Link an existing judicial decision to the canonical proceeding closure.

    This service does not implement the proceeding lifecycle itself.
    JudicialProceedingsService remains the sole owner of closure mutation.
    """

    def __init__(self, connection):
        self.connection = connection
        self.authorization_service = JudicialAuthorizationService(connection)
        self.proceedings_service = JudicialProceedingsService(connection)

    def close_proceeding_from_decision(
        self,
        *,
        user_id: int,
        proceeding_id: int,
        decision_id: int,
        closure_reason: str,
    ):
        self._require_text(closure_reason, "closure reason")

        proceeding = self.connection.execute(
            """
            SELECT id, tenant_id, jurisdiction_id, status
            FROM judicial_proceedings
            WHERE id = ?
            """,
            (proceeding_id,),
        ).fetchone()

        if proceeding is None:
            raise ValueError("judicial proceeding not found")

        if proceeding["status"] != "active":
            raise ValueError("only active judicial proceedings can be closed")

        decision = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                proceeding_id,
                judicial_authority_id
            FROM judicial_decisions
            WHERE id = ?
              AND tenant_id = ?
            """,
            (decision_id, proceeding["tenant_id"]),
        ).fetchone()

        if decision is None:
            raise ValueError("judicial decision not found")

        if decision["proceeding_id"] != proceeding["id"]:
            raise ValueError("decision does not belong to proceeding")

        self.authorization_service.authorize_decision(
            user_id=user_id,
            jurisdiction_id=proceeding["jurisdiction_id"],
        )

        authority = self.connection.execute(
            """
            SELECT id, tenant_id, jurisdiction_id
            FROM judicial_authorities
            WHERE user_id = ?
              AND tenant_id = ?
              AND jurisdiction_id = ?
              AND status = 'active'
            ORDER BY id DESC
            LIMIT 1
            """,
            (
                user_id,
                proceeding["tenant_id"],
                proceeding["jurisdiction_id"],
            ),
        ).fetchone()

        if authority is None:
            raise ValueError("no active judicial authority")

        if decision["judicial_authority_id"] != authority["id"]:
            raise ValueError("decision authority does not match authorized judicial authority")

        return self.proceedings_service.close_proceeding(
            user_id=user_id,
            proceeding_id=proceeding_id,
            closure_reason=closure_reason,
        )

    @staticmethod
    def _require_text(value: str, label: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{label} is required")
