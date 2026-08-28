import sqlite3

import database
import pytest


def _setup_fresh_db(tmp_path, monkeypatch):
    db_path = tmp_path / "governance_schema.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)
    database.init_db()

    connection = database.get_connection()
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _seed_users_and_proposal(connection):
    users = []

    for name, tenant_id in (
        ("Alice", "tenant-001"),
        ("Bob", "tenant-001"),
    ):
        cursor = connection.execute(
            """
            INSERT INTO users (
                tenant_id,
                name,
                email,
                role,
                status
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                tenant_id,
                name,
                f"{name.lower()}@example.com",
                "member",
                "active",
            ),
        )
        users.append(cursor.lastrowid)

    cursor = connection.execute(
        """
        INSERT INTO governance_proposals (
            tenant_id,
            proposer_user_id,
            title,
            description,
            status
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            "tenant-001",
            users[0],
            "Test Proposal",
            "Schema test proposal.",
            "draft",
        ),
    )

    connection.commit()

    return users[0], users[1], cursor.lastrowid


def test_governance_proposal_table_exists(tmp_path, monkeypatch):
    connection = _setup_fresh_db(tmp_path, monkeypatch)

    try:
        row = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'governance_proposals'
            """
        ).fetchone()

        assert row is not None
    finally:
        connection.close()


def test_governance_vote_table_exists(tmp_path, monkeypatch):
    connection = _setup_fresh_db(tmp_path, monkeypatch)

    try:
        row = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'governance_votes'
            """
        ).fetchone()

        assert row is not None
    finally:
        connection.close()


def test_governance_proposal_status_constraint(tmp_path, monkeypatch):
    connection = _setup_fresh_db(tmp_path, monkeypatch)

    try:
        proposer_id, _, _ = _seed_users_and_proposal(connection)

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO governance_proposals (
                    tenant_id,
                    proposer_user_id,
                    title,
                    description,
                    status
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "tenant-001",
                    proposer_id,
                    "Invalid Status",
                    "Should be rejected.",
                    "invalid",
                ),
            )
    finally:
        connection.close()


def test_governance_vote_choice_constraint(tmp_path, monkeypatch):
    connection = _setup_fresh_db(tmp_path, monkeypatch)

    try:
        proposer_id, voter_id, proposal_id = _seed_users_and_proposal(
            connection
        )

        connection.execute(
            """
            UPDATE governance_proposals
            SET status = 'open'
            WHERE tenant_id = ?
              AND id = ?
            """,
            ("tenant-001", proposal_id),
        )
        connection.commit()

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO governance_votes (
                    tenant_id,
                    proposal_id,
                    voter_user_id,
                    choice
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    "tenant-001",
                    proposal_id,
                    voter_id,
                    "invalid",
                ),
            )
    finally:
        connection.close()


def test_governance_vote_requires_valid_proposal(tmp_path, monkeypatch):
    connection = _setup_fresh_db(tmp_path, monkeypatch)

    try:
        _, voter_id, _ = _seed_users_and_proposal(connection)

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO governance_votes (
                    tenant_id,
                    proposal_id,
                    voter_user_id,
                    choice
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    "tenant-001",
                    999999,
                    voter_id,
                    "yes",
                ),
            )
    finally:
        connection.close()


def test_governance_vote_requires_valid_voter(tmp_path, monkeypatch):
    connection = _setup_fresh_db(tmp_path, monkeypatch)

    try:
        _, _, proposal_id = _seed_users_and_proposal(connection)

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO governance_votes (
                    tenant_id,
                    proposal_id,
                    voter_user_id,
                    choice
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    "tenant-001",
                    proposal_id,
                    999999,
                    "yes",
                ),
            )
    finally:
        connection.close()


def test_governance_vote_rejects_duplicate_voter(tmp_path, monkeypatch):
    connection = _setup_fresh_db(tmp_path, monkeypatch)

    try:
        _, voter_id, proposal_id = _seed_users_and_proposal(connection)

        connection.execute(
            """
            UPDATE governance_proposals
            SET status = 'open'
            WHERE tenant_id = ?
              AND id = ?
            """,
            ("tenant-001", proposal_id),
        )

        connection.execute(
            """
            INSERT INTO governance_votes (
                tenant_id,
                proposal_id,
                voter_user_id,
                choice
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                "tenant-001",
                proposal_id,
                voter_id,
                "yes",
            ),
        )
        connection.commit()

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO governance_votes (
                    tenant_id,
                    proposal_id,
                    voter_user_id,
                    choice
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    "tenant-001",
                    proposal_id,
                    voter_id,
                    "no",
                ),
            )
    finally:
        connection.close()
