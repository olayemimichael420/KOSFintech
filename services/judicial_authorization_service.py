from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass(frozen=True)
class JudicialAuthorizationDecision:
    allowed: bool
    reason: str


class JudicialAuthorizationService:
    def __init__(self, connection):
        self.connection = connection

    def authorize_decision(
        self,
        *,
        user_id: int,
        jurisdiction_id: int,
        now: Optional[datetime] = None,
    ) -> JudicialAuthorizationDecision:
        if now is None:
            now = datetime.now(timezone.utc)

        user = self.connection.execute(
            """
            SELECT id, tenant_id, status
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()

        if user is None:
            return JudicialAuthorizationDecision(
                False,
                "authenticated user not found",
            )

        if user["status"] != "active":
            return JudicialAuthorizationDecision(
                False,
                "authenticated user is inactive",
            )

        active_authority = self.connection.execute(
            """
            SELECT id
            FROM judicial_authorities
            WHERE user_id = ?
              AND tenant_id = ?
              AND status = 'active'
            LIMIT 1
            """,
            (user_id, user["tenant_id"]),
        ).fetchone()

        if active_authority is None:
            return JudicialAuthorizationDecision(
                False,
                "no active judicial authority",
            )

        authority = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                user_id,
                jurisdiction_id,
                status,
                effective_from,
                effective_until
            FROM judicial_authorities
            WHERE user_id = ?
              AND tenant_id = ?
              AND status = 'active'
              AND jurisdiction_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (user_id, user["tenant_id"], jurisdiction_id),
        ).fetchone()

        if authority is None:
            return JudicialAuthorizationDecision(
                False,
                "judicial authority jurisdiction mismatch",
            )

        if authority["effective_from"] is not None:
            effective_from = self._parse_datetime(
                authority["effective_from"]
            )
            if now < effective_from:
                return JudicialAuthorizationDecision(
                    False,
                    "judicial authority is not yet effective",
                )

        if authority["effective_until"] is not None:
            effective_until = self._parse_datetime(
                authority["effective_until"]
            )
            if now >= effective_until:
                return JudicialAuthorizationDecision(
                    False,
                    "judicial authority has expired",
                )

        jurisdiction = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                status
            FROM judicial_jurisdictions
            WHERE id = ?
              AND tenant_id = ?
            """,
            (authority["jurisdiction_id"], user["tenant_id"]),
        ).fetchone()

        if jurisdiction is None:
            return JudicialAuthorizationDecision(
                False,
                "judicial jurisdiction not found",
            )

        if jurisdiction["status"] != "active":
            return JudicialAuthorizationDecision(
                False,
                "judicial jurisdiction is inactive",
            )

        if authority["jurisdiction_id"] != jurisdiction_id:
            return JudicialAuthorizationDecision(
                False,
                "judicial authority jurisdiction mismatch",
            )

        requested_jurisdiction = self.connection.execute(
            """
            SELECT id
            FROM judicial_jurisdictions
            WHERE id = ?
              AND tenant_id = ?
            """,
            (jurisdiction_id, user["tenant_id"]),
        ).fetchone()

        if requested_jurisdiction is None:
            return JudicialAuthorizationDecision(
                False,
                "judicial jurisdiction not found",
            )

        return JudicialAuthorizationDecision(
            True,
            "active judicial authority authorized",
        )

    def authorize(
        self,
        *,
        user_id: int,
        jurisdiction_id: int,
        now: Optional[datetime] = None,
    ) -> bool:
        return self.authorize_decision(
            user_id=user_id,
            jurisdiction_id=jurisdiction_id,
            now=now,
        ).allowed

    @staticmethod
    def _parse_datetime(value: str) -> datetime:
        parsed = datetime.fromisoformat(value)

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        return parsed
