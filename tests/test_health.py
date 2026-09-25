from utils.health import health_status


def test_health_status_reports_database_ok():
    result = health_status()

    assert result["status"] == "ok"
    assert result["component"] == "kosfintech-foundation"
    assert result["database"] == "ok"


def test_health_status_closes_database_connection(monkeypatch):
    class DummyConnection:
        def __init__(self):
            self.closed = False

        def execute(self, statement):
            assert statement == "SELECT 1"
            return self

        def fetchone(self):
            return (1,)

        def close(self):
            self.closed = True

    connection = DummyConnection()
    monkeypatch.setattr("utils.health.get_connection", lambda: connection)

    result = health_status()

    assert result["database"] == "ok"
    assert connection.closed is True


def test_health_status_surfaces_database_failure(monkeypatch):
    def failing_connection():
        raise RuntimeError("database unavailable")

    monkeypatch.setattr("utils.health.get_connection", failing_connection)

    try:
        health_status()
    except RuntimeError as exc:
        assert str(exc) == "database unavailable"
    else:
        raise AssertionError("health_status() should surface database failure")
