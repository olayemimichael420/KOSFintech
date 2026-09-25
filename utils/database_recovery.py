"""Operational SQLite backup and recovery helpers."""

import sqlite3
from pathlib import Path


def verify_integrity(db_path: Path) -> str:
    """Return SQLite integrity-check result for a database file."""
    db_path = Path(db_path)
    connection = sqlite3.connect(db_path)
    try:
        result = connection.execute("PRAGMA integrity_check").fetchone()
        return str(result[0]) if result else ""
    finally:
        connection.close()


def backup_database(source_path: Path, backup_path: Path) -> Path:
    """Create a consistent SQLite backup using SQLite's backup API."""
    source_path = Path(source_path)
    backup_path = Path(backup_path)
    backup_path.parent.mkdir(parents=True, exist_ok=True)

    source = sqlite3.connect(source_path)
    target = sqlite3.connect(backup_path)
    try:
        source.backup(target)
        target.commit()
    finally:
        target.close()
        source.close()

    if verify_integrity(backup_path) != "ok":
        raise RuntimeError(f"Backup integrity check failed: {backup_path}")

    return backup_path


def restore_database(backup_path: Path, restore_path: Path) -> Path:
    """Restore a backup into a separate destination and verify its integrity."""
    backup_path = Path(backup_path)
    restore_path = Path(restore_path)
    restore_path.parent.mkdir(parents=True, exist_ok=True)

    source = sqlite3.connect(backup_path)
    target = sqlite3.connect(restore_path)
    try:
        source.backup(target)
        target.commit()
    finally:
        target.close()
        source.close()

    if verify_integrity(restore_path) != "ok":
        raise RuntimeError(f"Restored database integrity check failed: {restore_path}")

    return restore_path
