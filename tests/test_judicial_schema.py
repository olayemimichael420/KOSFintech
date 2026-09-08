import sqlite3

import pytest

import database


def test_judicial_schema(tmp_path, monkeypatch):
    db_path = tmp_path / "judicial.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)

    database.init_db()
    connection = database.get_connection()

    try:
        expected_tables = {
            "judicial_jurisdictions",
            "judicial_appointments",
            "judicial_conferrals",
            "judicial_authorities",
        }

        tables = {
            row["name"]
            for row in connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                """
            ).fetchall()
        }

        assert expected_tables.issubset(tables)

        expected_columns = {
            "judicial_jurisdictions": {
                "id",
                "tenant_id",
                "jurisdiction_type",
                "jurisdiction_scope",
                "judicial_level",
                "case_types",
                "parent_jurisdiction_id",
                "status",
            },
            "judicial_appointments": {
                "id",
                "tenant_id",
                "candidate_user_id",
                "jurisdiction_id",
                "judicial_level",
                "appointment_source",
                "appointment_basis",
                "qualification_record",
                "appointed_by",
                "appointed_at",
                "term_start",
                "term_end",
                "status",
            },
            "judicial_conferrals": {
                "id",
                "tenant_id",
                "appointment_id",
                "authority_id",
                "conferring_authority",
                "conferral_instrument",
                "conferral_date",
                "effective_from",
                "effective_until",
                "status",
            },
            "judicial_authorities": {
                "id",
                "tenant_id",
                "user_id",
                "authority_type",
                "jurisdiction_id",
                "judicial_level",
                "appointment_id",
                "conferral_id",
                "status",
                "effective_from",
                "effective_until",
            },
        }

        for table, columns in expected_columns.items():
            actual_columns = {
                row["name"]
                for row in connection.execute(
                    f"PRAGMA table_info({table})"
                ).fetchall()
            }
            assert actual_columns == columns

        expected_fk_targets = {
            "judicial_jurisdictions": {
                "judicial_jurisdictions",
            },
            "judicial_appointments": {
                "users",
                "judicial_jurisdictions",
            },
            "judicial_conferrals": {
                "judicial_appointments",
                "judicial_authorities",
            },
            "judicial_authorities": {
                "users",
                "judicial_jurisdictions",
                "judicial_appointments",
            },
        }

        for table, expected_targets in expected_fk_targets.items():
            foreign_keys = connection.execute(
                f"PRAGMA foreign_key_list({table})"
            ).fetchall()

            actual_targets = {
                row["table"]
                for row in foreign_keys
            }

            assert expected_targets.issubset(actual_targets)

        # Seed users in separate tenants.
        connection.execute(
            """
            INSERT INTO users (tenant_id, name, role)
            VALUES (?, ?, ?)
            """,
            ("tenant-001", "User One", "member"),
        )

        user_one = connection.execute(
            """
            SELECT id
            FROM users
            WHERE tenant_id = ?
            """,
            ("tenant-001",),
        ).fetchone()["id"]

        connection.execute(
            """
            INSERT INTO users (tenant_id, name, role)
            VALUES (?, ?, ?)
            """,
            ("tenant-002", "User Two", "member"),
        )

        user_two = connection.execute(
            """
            SELECT id
            FROM users
            WHERE tenant_id = ?
            """,
            ("tenant-002",),
        ).fetchone()["id"]

        # Tenant 001 jurisdiction.
        connection.execute(
            """
            INSERT INTO judicial_jurisdictions (
                tenant_id,
                jurisdiction_type,
                jurisdiction_scope,
                judicial_level,
                case_types
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "tenant-001",
                "school",
                "school-001",
                "local",
                "service_act",
            ),
        )

        jurisdiction_id = connection.execute(
            """
            SELECT id
            FROM judicial_jurisdictions
            WHERE tenant_id = ?
            """,
            ("tenant-001",),
        ).fetchone()["id"]

        connection.commit()

        # Tenant boundary must reject a jurisdiction from another tenant.
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO judicial_appointments (
                    tenant_id,
                    candidate_user_id,
                    jurisdiction_id,
                    judicial_level,
                    appointment_source,
                    appointment_basis,
                    qualification_record,
                    appointed_by
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "tenant-002",
                    user_two,
                    jurisdiction_id,
                    "local",
                    "test",
                    "test",
                    "test",
                    user_two,
                ),
            )

        # Same-tenant appointment must succeed.
        connection.execute(
            """
            INSERT INTO judicial_appointments (
                tenant_id,
                candidate_user_id,
                jurisdiction_id,
                judicial_level,
                appointment_source,
                appointment_basis,
                qualification_record,
                appointed_by
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "tenant-001",
                user_one,
                jurisdiction_id,
                "local",
                "test",
                "test",
                "test",
                user_one,
            ),
        )

        connection.commit()

        appointment_id = connection.execute(
            """
            SELECT id
            FROM judicial_appointments
            WHERE tenant_id = ?
            """,
            ("tenant-001",),
        ).fetchone()["id"]

        assert appointment_id is not None

        # Judicial authority status CHECK must reject invalid values.
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
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
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "tenant-001",
                    user_one,
                    "judge",
                    jurisdiction_id,
                    "local",
                    appointment_id,
                    999999,
                    "invalid-status",
                ),
            )

    finally:
        connection.close()
