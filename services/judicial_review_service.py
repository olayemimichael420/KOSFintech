from datetime import datetime, timezone

from audit import audit_event
from models.judicial_review import (
    JudicialReview,
    JudicialReviewStatus,
    JudicialReviewType,
)
from services.judicial_authorization_service import (
    JudicialAuthorizationService,
)


class JudicialReviewService:
    """
    Record proposed judicial review or appeal relationships.

    This service does not determine admissibility, appellate jurisdiction,
    merits, finality, reversal, invalidation, reopening, stays, remedies,
    or execution. It records only a proposed review or appeal.
    """

    def __init__(self, connection):
        self.connection = connection
        self.authorization_service = JudicialAuthorizationService(connection)

    def record_review(
        self,
        *,
        user_id: int,
        proceeding_id: int,
        decision_id: int,
        review_type,
        grounds: str,
    ) -> JudicialReview:
        self._require_text(grounds, "review grounds")

        try:
            review_type = JudicialReviewType(review_type)
        except (ValueError, TypeError):
            raise ValueError("invalid judicial review type")

        proceeding = self._require_active_proceeding(proceeding_id)
        decision = self._get_decision(
            proceeding["tenant_id"],
            decision_id,
        )

        if decision["proceeding_id"] != proceeding["id"]:
            raise ValueError("judicial decision does not belong to proceeding")

        decision_authority = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                jurisdiction_id,
                status
            FROM judicial_authorities
            WHERE id = ?
              AND tenant_id = ?
            """,
            (
                decision["judicial_authority_id"],
                proceeding["tenant_id"],
            ),
        ).fetchone()

        if decision_authority is None:
            raise ValueError("judicial decision authority not found")

        if decision_authority["jurisdiction_id"] != proceeding["jurisdiction_id"]:
            raise ValueError(
                "judicial decision authority jurisdiction mismatch"
            )

        authority = self._require_authorized_authority(
            user_id=user_id,
            jurisdiction_id=proceeding["jurisdiction_id"],
        )

        self._require_same_tenant(
            proceeding["tenant_id"],
            authority["tenant_id"],
        )

        now = datetime.now(timezone.utc).isoformat()

        try:
            self.connection.execute("BEGIN")

            cursor = self.connection.execute(
                """
                INSERT INTO judicial_reviews (
                    tenant_id,
                    proceeding_id,
                    decision_id,
                    originating_judicial_authority_id,
                    jurisdiction_id,
                    review_type,
                    initiated_by,
                    grounds,
                    status,
                    recorded_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    proceeding["tenant_id"],
                    proceeding["id"],
                    decision["id"],
                    decision["judicial_authority_id"],
                    proceeding["jurisdiction_id"],
                    review_type.value,
                    user_id,
                    grounds.strip(),
                    JudicialReviewStatus.PROPOSED.value,
                    now,
                ),
            )

            review = self._get_review(
                proceeding["tenant_id"],
                cursor.lastrowid,
            )

            audit_event(
                event_type="judicial_review_recorded",
                actor_id=user_id,
                tenant_id=proceeding["tenant_id"],
                action="record_judicial_review",
                metadata={
                    "review_id": review.id,
                    "proceeding_id": review.proceeding_id,
                    "decision_id": review.decision_id,
                    "originating_judicial_authority_id": (
                        review.originating_judicial_authority_id
                    ),
                    "jurisdiction_id": review.jurisdiction_id,
                    "review_type": review.review_type.value,
                    "status": review.status.value,
                },
                connection=self.connection,
            )

            self.connection.commit()
            return review

        except Exception:
            self.connection.rollback()
            raise

    def _require_authorized_authority(
        self,
        *,
        user_id: int,
        jurisdiction_id: int,
    ):
        authorization = self.authorization_service.authorize_decision(
            user_id=user_id,
            jurisdiction_id=jurisdiction_id,
        )

        if not authorization.allowed:
            raise ValueError(authorization.reason)

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
            (
                user_id,
                user["tenant_id"],
                jurisdiction_id,
            ),
        ).fetchone()

        if authority is None:
            raise ValueError("active judicial authority not found")

        return authority

    def _require_active_proceeding(self, proceeding_id: int):
        row = self.connection.execute(
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

        if row is None:
            raise ValueError("judicial proceeding not found")

        if row["status"] != "active":
            raise ValueError(
                "only active judicial proceedings can receive "
                "judicial review records"
            )

        return row

    def _get_decision(self, tenant_id: str, decision_id: int):
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

        return row

    def _get_review(
        self,
        tenant_id: str,
        review_id: int,
    ) -> JudicialReview:
        row = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                proceeding_id,
                decision_id,
                originating_judicial_authority_id,
                jurisdiction_id,
                review_type,
                initiated_by,
                grounds,
                status,
                recorded_at
            FROM judicial_reviews
            WHERE tenant_id = ?
              AND id = ?
            """,
            (tenant_id, review_id),
        ).fetchone()

        if row is None:
            raise ValueError("judicial review not found")

        return JudicialReview(
            id=row["id"],
            tenant_id=row["tenant_id"],
            proceeding_id=row["proceeding_id"],
            decision_id=row["decision_id"],
            originating_judicial_authority_id=(
                row["originating_judicial_authority_id"]
            ),
            jurisdiction_id=row["jurisdiction_id"],
            review_type=JudicialReviewType(row["review_type"]),
            initiated_by=row["initiated_by"],
            grounds=row["grounds"],
            status=JudicialReviewStatus(row["status"]),
            recorded_at=row["recorded_at"],
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
