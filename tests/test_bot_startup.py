import bot


class DummyApplication:
    def __init__(self):
        self.polling_started = False
        self.polling_kwargs = None

    def run_polling(self, **kwargs):
        self.polling_started = True
        self.polling_kwargs = kwargs


def test_main_initializes_database_before_application(monkeypatch):
    calls = []

    def fake_init_db():
        calls.append("database.init_db")

    application = DummyApplication()

    def fake_build_application():
        calls.append("build_application")
        return application

    monkeypatch.setattr(
        bot.database,
        "init_db",
        fake_init_db,
    )

    monkeypatch.setattr(
        bot,
        "build_application",
        fake_build_application,
    )

    bot.main()

    assert calls == [
        "database.init_db",
        "build_application",
    ]

    assert application.polling_started is True
    assert application.polling_kwargs == {
        "drop_pending_updates": True,
    }


def test_build_application_requires_bot_token(monkeypatch):
    class DummySettings:
        bot_token = None

    monkeypatch.setattr(
        bot,
        "settings",
        DummySettings(),
    )

    try:
        bot.build_application()
    except RuntimeError as exc:
        assert "BOT_TOKEN is not configured" in str(exc)
    else:
        raise AssertionError(
            "build_application() should reject missing BOT_TOKEN"
        )
