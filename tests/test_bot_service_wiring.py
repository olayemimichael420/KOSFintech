import sqlite3

import bot

from services.application_service_factory import ApplicationServiceFactory
from services.application_services import ApplicationServices


def test_build_application_wires_service_factory(monkeypatch):
    connection = sqlite3.connect(":memory:")

    class DummySettings:
        bot_token = "test-token"
        log_level = "INFO"
        app_env = "test"

    monkeypatch.setattr(bot, "settings", DummySettings())
    monkeypatch.setattr(bot.database, "get_connection", lambda: connection)

    application = bot.build_application()

    try:
        assert application.bot_data["db_connection"] is connection
        assert isinstance(
            application.bot_data["service_factory"],
            ApplicationServiceFactory,
        )
        assert application.bot_data["service_factory"].connection is connection
        assert isinstance(
            application.bot_data["services"],
            ApplicationServices,
        )
        assert application.bot_data["services"].factory is application.bot_data["service_factory"]
    finally:
        connection.close()
