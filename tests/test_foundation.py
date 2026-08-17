from pathlib import Path

from config import settings
from database import get_db_path, init_db
from utils.health import health_status


def test_settings_load():
    assert settings.app_name.startswith("KOSFintech")
    assert settings.default_country
    assert settings.default_currency


def test_database_path():
    path = get_db_path()

    assert isinstance(path, Path)
    assert path.parent.exists()


def test_database_initialization():
    init_db()

    assert get_db_path().exists()


def test_health():
    result = health_status()

    assert result["status"] == "ok"
