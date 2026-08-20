import sqlite3

import pytest

from models.platform_authority import (
    PlatformAuthority,
    PlatformAuthorityRole,
)
from services.super_admin_transfer_service import (
    SuperAdminTransferService,
)


def create_tables(connection):
    connection.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            name TEXT NOT NULL,
            email TEXT,
            role TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active'
        )
    """)

    connection.execute("""
        CREATE TABLE platform_authorities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('super_admin')),
            status TEXT NOT NULL DEFAULT 'active'
                CHECK(status IN ('active', 'inactive')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            transferred_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    connection.execute("""
        CREATE UNIQUE INDEX ux_platform_authorities_active_role
        ON platform_authorities(role)
        WHERE status = 'active'
    """)

    connection.execute("""
        CREATE UNIQUE INDEX ux_platform_authorities_active_user
        ON platform_authorities(user_id)
        WHERE status = 'active'
    """)

    connection.executemany(
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
        [
            (
                "platform",
                "Current Super Admin",
                "current@example.com",
                "member",
                "active",
            ),
            (
                "platform",
                "New Super Admin",
                "new@example.com",
                "member",
                "active",
            ),
            (
                "platform",
                "Inactive User",
                "inactive@example.com",
                "member",
                "inactive",
            ),
        ],
    )

    connection.commit()


def add_super_admin(connection, user_id):
    connection.execute(
        """
        INSERT INTO platform_authorities (
            user_id,
            role,
            status
        )
        VALUES (?, ?, ?)
        """,
        (
            user_id,
            "super_admin",
            "active",
        ),
    )
    connection.commit()


def test_super_admin_transfer_succeeds():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    create_tables(connection)
    add_super_admin(connection, 1)

    service = SuperAdminTransferService(connection)

    result = service.transfer(
        current_user_id=1,
        target_user_id=2,
    )

    assert result.allowed is True
    assert result.reason == "super admin transferred successfully"

    current = connection.execute(
        """
        SELECT status
        FROM platform_authorities
        WHERE user_id = 1
        """
    ).fetchone()

    new = connection.execute(
        """
        SELECT status
        FROM platform_authorities
        WHERE user_id = 2
        """
    ).fetchone()

    assert current["status"] == "inactive"
    assert new["status"] == "active"

    connection.close()


def test_non_super_admin_cannot_transfer():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    create_tables(connection)
    add_super_admin(connection, 1)

    service = SuperAdminTransferService(connection)

    result = service.transfer(
        current_user_id=2,
        target_user_id=1,
    )

    assert result.allowed is False
    assert result.reason == "current user is not the active super admin"

    connection.close()


def test_cannot_transfer_to_self():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    create_tables(connection)
    add_super_admin(connection, 1)

    service = SuperAdminTransferService(connection)

    result = service.transfer(
        current_user_id=1,
        target_user_id=1,
    )

    assert result.allowed is False
    assert result.reason == "cannot transfer super admin role to the current super admin"

    connection.close()


def test_inactive_target_is_rejected():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    create_tables(connection)
    add_super_admin(connection, 1)

    service = SuperAdminTransferService(connection)

    result = service.transfer(
        current_user_id=1,
        target_user_id=3,
    )

    assert result.allowed is False
    assert result.reason == "target user is inactive"

    connection.close()


def test_missing_target_is_rejected():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    create_tables(connection)
    add_super_admin(connection, 1)

    service = SuperAdminTransferService(connection)

    result = service.transfer(
        current_user_id=1,
        target_user_id=999,
    )

    assert result.allowed is False
    assert result.reason == "target user does not exist"

    connection.close()


def test_successful_super_admin_transfer_emits_audit_event(caplog):
    import json
    import logging

    with caplog.at_level(logging.INFO, logger="kosfintech.audit"):
        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row
        create_tables(connection)

        add_super_admin(connection, 1)
        service = SuperAdminTransferService(connection)

        decision = service.transfer(
            current_user_id=1,
            target_user_id=2,
        )

        assert decision.allowed is True

        audit_records = [
            record
            for record in caplog.records
            if record.name == "kosfintech.audit"
        ]

        assert len(audit_records) == 1

        message = audit_records[0].message
        assert message.startswith("AUDIT ")

        payload = json.loads(message[len("AUDIT "):])

        assert payload["event_type"] == "super_admin_transfer"
        assert payload["actor_id"] == 1
        assert payload["tenant_id"] == "platform"
        assert payload["action"] == "transfer_super_admin"
        assert payload["metadata"]["from_user_id"] == 1
        assert payload["metadata"]["to_user_id"] == 2

        connection.close()

def test_transfer_requires_current_authority_to_remain_active():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    create_tables(connection)
    add_super_admin(connection, 1)

    # The caller is no longer the active Super Admin.
    connection.execute("""
        UPDATE platform_authorities
        SET status = 'inactive'
        WHERE user_id = 1
    """)
    connection.commit()

    service = SuperAdminTransferService(connection)

    result = service.transfer(
        current_user_id=1,
        target_user_id=2,
    )

    assert result.allowed is False
    assert result.reason == "current user is not the active super admin"

    active = connection.execute("""
        SELECT COUNT(*) AS count
        FROM platform_authorities
        WHERE role = 'super_admin'
          AND status = 'active'
    """).fetchone()

    assert active["count"] == 0

    connection.close()
