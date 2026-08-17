"""Basic application health helpers."""


def health_status() -> dict:
    """Return basic application health information."""

    return {
        "status": "ok",
        "component": "kosfintech-foundation",
    }
