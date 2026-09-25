import sqlite3

from utils.database_recovery import (
    backup_database,
    restore_database,
    verify_integrity,
)


def test_backup_database_creates_verified_copy(tmp_path):
    source = tmp_path / "source.db"
    backup = tmp_path / "backup.db"

    connection = sqlite3.connect(source)
    connection.execute(
        "CREATE TABLE recovery_probe (id INTEGER PRIMARY KEY, value TEXT NOT NULL)"
    )
    connection.execute(
        "INSERT INTO recovery_probe (value) VALUES (?)",
        ("backup-test",),
    )
    connection.commit()
    connection.close()

    result = backup_database(source, backup)

    assert result == backup
    assert backup.exists()
    assert verify_integrity(backup) == "ok"


def test_restore_database_preserves_data_and_integrity(tmp_path):
    source = tmp_path / "source.db"
    backup = tmp_path / "backup.db"
    restored = tmp_path / "restored.db"

    connection = sqlite3.connect(source)
    connection.execute(
        "CREATE TABLE recovery_probe (id INTEGER PRIMARY KEY, value TEXT NOT NULL)"
    )
    connection.execute(
        "INSERT INTO recovery_probe (value) VALUES (?)",
        ("restore-test",),
    )
    connection.commit()
    connection.close()

    backup_database(source, backup)
    result = restore_database(backup, restored)

    connection = sqlite3.connect(restored)
    value = connection.execute(
        "SELECT value FROM recovery_probe WHERE id = 1"
    ).fetchone()[0]
    connection.close()

    assert result == restored
    assert value == "restore-test"
    assert verify_integrity(restored) == "ok"
