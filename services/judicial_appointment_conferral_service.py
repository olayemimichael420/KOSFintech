from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from models.judicial_appointment import JudicialAppointment
from models.judicial_authority import (
    JudicialAuthority,
    JudicialAuthorityStatus,
)
from models.judicial_conferral import JudicialConferral


@dataclass(frozen=True)
class _AppointmentContext:
    appointment: object
    tenant_id: str


class JudicialAppointmentConferralService:
    """Establish judicial appointment, conferral, and authority provenance."""

    def __init__(self, connection):
        self.connection = connection

    def create_appointment(
        self,
        *,
        candidate_user_id: int,
        jurisdiction_id: int,
        judicial_level: str,
        appointment_source: str,
        appointment_basis: str,
        qualification_record: str,
        appointed_by: int,
        appointed_at: Optional[datetime] = None,
        term_start: Optional[datetime] = None,
        term_end: Optional[datetime] = None,
    ) -> JudicialAppointment:
        candidate = self.connection.execute(
            """
            SELECT id, tenant_id, status
            FROM users
            WHERE id = ?
            """,
            (candidate_user_id,),
        ).fetchone()

        if candidate is None:
            raise ValueError("candidate user not found")

        if candidate["status"] != "active":
            raise ValueError("candidate user is inactive")

        appointing = self.connection.execute(
            """
            SELECT id, tenant_id, status
            FROM users
            WHERE id = ?
            """,
            (appointed_by,),
        ).fetchone()

        if appointing is None:
            raise ValueError("appointing user not found")

        if appointing["status"] != "active":
            raise ValueError("appointing user is inactive")

        if appointing["tenant_id"] != candidate["tenant_id"]:
            raise ValueError("tenant mismatch")

        jurisdiction = self.connection.execute(
            """
            SELECT id, tenant_id, status
            FROM judicial_jurisdictions
            WHERE id = ?
              AND tenant_id = ?
            """,
            (jurisdiction_id, candidate["tenant_id"]),
        ).fetchone()

        if jurisdiction is None:
            raise ValueError("judicial jurisdiction not found")

        if jurisdiction["status"] != "active":
            raise ValueError("judicial jurisdiction is inactive")

        self._require_text(judicial_level, "judicial level")
        self._require_text(appointment_source, "appointment source")
        self._require_text(appointment_basis, "appointment basis")
        self._require_text(qualification_record, "qualification record")
        self._validate_window(term_start, term_end, "appointment term")

        cursor = self.connection.execute(
            """
            INSERT INTO judicial_appointments (
                tenant_id,
                candidate_user_id,
                jurisdiction_id,
                judicial_level,
                appointment_source,
                appointment_basis,
                qualification_record,
                appointed_by,
                appointed_at,
                term_start,
                term_end,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'appointed')
            """,
            (
                candidate["tenant_id"],
                candidate_user_id,
                jurisdiction_id,
                judicial_level,
                appointment_source,
                appointment_basis,
                qualification_record,
                appointed_by,
                appointed_at,
                term_start,
                term_end,
            ),
        )

        self.connection.commit()

        return JudicialAppointment(
            id=cursor.lastrowid,
            candidate_user_id=candidate_user_id,
            jurisdiction_id=jurisdiction_id,
            judicial_level=judicial_level,
            appointment_source=appointment_source,
            appointment_basis=appointment_basis,
            qualification_record=qualification_record,
            appointed_by=appointed_by,
            appointed_at=appointed_at,
            term_start=term_start,
            term_end=term_end,
            status="appointed",
        )

    def create_proposed_authority(
        self,
        *,
        appointment_id: int,
        authority_type: str,
    ) -> JudicialAuthority:
        self._require_text(authority_type, "authority type")

        appointment = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                candidate_user_id,
                jurisdiction_id,
                judicial_level,
                status
            FROM judicial_appointments
            WHERE id = ?
            """,
            (appointment_id,),
        ).fetchone()

        if appointment is None:
            raise ValueError("judicial appointment not found")

        if appointment["status"] != "appointed":
            raise ValueError("judicial appointment is not active")

        user = self.connection.execute(
            """
            SELECT id, tenant_id, status
            FROM users
            WHERE id = ?
              AND tenant_id = ?
            """,
            (
                appointment["candidate_user_id"],
                appointment["tenant_id"],
            ),
        ).fetchone()

        if user is None:
            raise ValueError("appointment candidate tenant mismatch")

        if user["status"] != "active":
            raise ValueError("appointment candidate is inactive")

        jurisdiction = self.connection.execute(
            """
            SELECT id, tenant_id, status
            FROM judicial_jurisdictions
            WHERE id = ?
              AND tenant_id = ?
            """,
            (
                appointment["jurisdiction_id"],
                appointment["tenant_id"],
            ),
        ).fetchone()

        if jurisdiction is None:
            raise ValueError("judicial jurisdiction not found")

        if jurisdiction["status"] != "active":
            raise ValueError("judicial jurisdiction is inactive")

        cursor = self.connection.execute(
            """
            INSERT INTO judicial_authorities (
                tenant_id,
                user_id,
                authority_type,
                jurisdiction_id,
                judicial_level,
                appointment_id,
                conferral_id,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, 0, 'proposed')
            """,
            (
                appointment["tenant_id"],
                appointment["candidate_user_id"],
                authority_type,
                appointment["jurisdiction_id"],
                appointment["judicial_level"],
                appointment_id,
            ),
        )

        self.connection.commit()

        return JudicialAuthority(
            id=cursor.lastrowid,
            user_id=appointment["candidate_user_id"],
            authority_type=authority_type,
            jurisdiction_id=appointment["jurisdiction_id"],
            judicial_level=appointment["judicial_level"],
            appointment_id=appointment_id,
            conferral_id=0,
            status=JudicialAuthorityStatus.PROPOSED,
        )

    def create_conferral(
        self,
        *,
        appointment_id: int,
        authority_id: int,
        conferring_authority: str,
        conferral_instrument: str,
        conferral_date: Optional[datetime] = None,
        effective_from: Optional[datetime] = None,
        effective_until: Optional[datetime] = None,
    ) -> JudicialConferral:
        self._require_text(conferring_authority, "conferring authority")
        self._require_text(conferral_instrument, "conferral instrument")
        self._validate_window(
            effective_from,
            effective_until,
            "conferral effective window",
        )

        appointment = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                candidate_user_id,
                jurisdiction_id,
                judicial_level,
                status
            FROM judicial_appointments
            WHERE id = ?
            """,
            (appointment_id,),
        ).fetchone()

        if appointment is None:
            raise ValueError("judicial appointment not found")

        authority = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                user_id,
                jurisdiction_id,
                judicial_level,
                appointment_id,
                conferral_id,
                status
            FROM judicial_authorities
            WHERE id = ?
              AND tenant_id = ?
            """,
            (authority_id, appointment["tenant_id"]),
        ).fetchone()

        if authority is None:
            raise ValueError("judicial authority not found")

        if authority["status"] != "proposed":
            raise ValueError("judicial authority is not proposed")

        if authority["appointment_id"] != appointment_id:
            raise ValueError("judicial authority appointment mismatch")

        if authority["user_id"] != appointment["candidate_user_id"]:
            raise ValueError("judicial authority candidate mismatch")

        if authority["jurisdiction_id"] != appointment["jurisdiction_id"]:
            raise ValueError("judicial authority jurisdiction mismatch")

        if authority["judicial_level"] != appointment["judicial_level"]:
            raise ValueError("judicial authority level mismatch")

        cursor = self.connection.execute(
            """
            INSERT INTO judicial_conferrals (
                tenant_id,
                appointment_id,
                authority_id,
                conferring_authority,
                conferral_instrument,
                conferral_date,
                effective_from,
                effective_until,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active')
            """,
            (
                appointment["tenant_id"],
                appointment_id,
                authority_id,
                conferring_authority,
                conferral_instrument,
                conferral_date,
                effective_from,
                effective_until,
            ),
        )

        conferral_id = cursor.lastrowid

        self.connection.execute(
            """
            UPDATE judicial_authorities
            SET conferral_id = ?
            WHERE id = ?
              AND tenant_id = ?
              AND status = 'proposed'
            """,
            (
                conferral_id,
                authority_id,
                appointment["tenant_id"],
            ),
        )

        self.connection.commit()

        return JudicialConferral(
            id=conferral_id,
            appointment_id=appointment_id,
            authority_id=authority_id,
            conferring_authority=conferring_authority,
            conferral_instrument=conferral_instrument,
            conferral_date=conferral_date,
            effective_from=effective_from,
            effective_until=effective_until,
            status="active",
        )

    def activate_authority(
        self,
        *,
        authority_id: int,
        now: Optional[datetime] = None,
    ) -> JudicialAuthority:
        if now is None:
            now = datetime.now(timezone.utc)

        authority = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                user_id,
                authority_type,
                jurisdiction_id,
                judicial_level,
                appointment_id,
                conferral_id,
                status,
                effective_from,
                effective_until
            FROM judicial_authorities
            WHERE id = ?
            """,
            (authority_id,),
        ).fetchone()

        if authority is None:
            raise ValueError("judicial authority not found")

        if authority["status"] != "proposed":
            raise ValueError("judicial authority is not proposed")

        appointment = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                candidate_user_id,
                jurisdiction_id,
                judicial_level,
                status,
                term_start,
                term_end
            FROM judicial_appointments
            WHERE id = ?
              AND tenant_id = ?
            """,
            (
                authority["appointment_id"],
                authority["tenant_id"],
            ),
        ).fetchone()

        if appointment is None:
            raise ValueError("judicial appointment not found")

        if appointment["status"] != "appointed":
            raise ValueError("judicial appointment is not active")

        if authority["user_id"] != appointment["candidate_user_id"]:
            raise ValueError("judicial authority candidate mismatch")

        if authority["jurisdiction_id"] != appointment["jurisdiction_id"]:
            raise ValueError("judicial authority jurisdiction mismatch")

        if authority["judicial_level"] != appointment["judicial_level"]:
            raise ValueError("judicial authority level mismatch")

        conferral = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                appointment_id,
                authority_id,
                conferring_authority,
                conferral_instrument,
                status,
                effective_from,
                effective_until
            FROM judicial_conferrals
            WHERE authority_id = ?
              AND appointment_id = ?
              AND tenant_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (
                authority["id"],
                appointment["id"],
                authority["tenant_id"],
            ),
        ).fetchone()

        if conferral is None:
            raise ValueError("judicial conferral not found")

        if conferral["status"] != "active":
            raise ValueError("judicial conferral is inactive")

        if conferral["appointment_id"] != appointment["id"]:
            raise ValueError("judicial conferral appointment mismatch")

        if conferral["authority_id"] != authority["id"]:
            raise ValueError("judicial conferral authority mismatch")

        self._validate_effective_now(
            now,
            conferral["effective_from"],
            conferral["effective_until"],
            "judicial conferral",
        )

        self._validate_effective_now(
            now,
            appointment["term_start"],
            appointment["term_end"],
            "judicial appointment",
        )

        self.connection.execute(
            """
            UPDATE judicial_authorities
            SET status = 'active',
                effective_from = ?,
                effective_until = ?
            WHERE id = ?
              AND tenant_id = ?
              AND status = 'proposed'
            """,
            (
                conferral["effective_from"],
                conferral["effective_until"],
                authority_id,
                authority["tenant_id"],
            ),
        )

        self.connection.commit()

        return JudicialAuthority(
            id=authority["id"],
            user_id=authority["user_id"],
            authority_type=authority["authority_type"],
            jurisdiction_id=authority["jurisdiction_id"],
            judicial_level=authority["judicial_level"],
            appointment_id=authority["appointment_id"],
            conferral_id=authority["conferral_id"],
            status=JudicialAuthorityStatus.ACTIVE,
            effective_from=self._parse_datetime_or_none(
                conferral["effective_from"]
            ),
            effective_until=self._parse_datetime_or_none(
                conferral["effective_until"]
            ),
        )

    @staticmethod
    def _require_text(value: str, field: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} is required")

    @staticmethod
    def _validate_window(
        start: Optional[datetime],
        end: Optional[datetime],
        label: str,
    ) -> None:
        if start is not None and end is not None and start >= end:
            raise ValueError(f"{label} is invalid")

    @staticmethod
    def _validate_effective_now(
        now: datetime,
        start,
        end,
        label: str,
    ) -> None:
        if start is not None:
            parsed_start = JudicialAppointmentConferralService._parse_datetime(
                start
            )
            if now < parsed_start:
                raise ValueError(f"{label} is not yet effective")

        if end is not None:
            parsed_end = JudicialAppointmentConferralService._parse_datetime(
                end
            )
            if now >= parsed_end:
                raise ValueError(f"{label} has expired")

    @staticmethod
    def _parse_datetime(value: str) -> datetime:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed

    @staticmethod
    def _parse_datetime_or_none(value):
        if value is None:
            return None
        return JudicialAppointmentConferralService._parse_datetime(value)
