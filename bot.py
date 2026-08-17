#!/usr/bin/env python3
"""
KOSFintech Telegram application entry point.

PART 1 intentionally keeps the Telegram entry point minimal.
Business logic will be introduced through handlers/services in
subsequent development parts.
"""

import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from config import settings


logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("kosfintech")


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Basic health/start command."""

    await update.message.reply_text(
        "🚀 KOSFintech Global Community Operations Platform\n\n"
        "Foundation layer is online.\n"
        "The modular system is being assembled incrementally.\n\n"
        "Use /health to verify the application."
    )


async def health(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Basic application health response."""

    await update.message.reply_text(
        "✅ KOSFintech application is responding.\n"
        f"Environment: {settings.app_env}"
    )


def build_application() -> Application:
    """Construct the Telegram application."""

    if not settings.bot_token:
        raise RuntimeError(
            "BOT_TOKEN is not configured. "
            "Set it in the environment or .env file."
        )

    application = (
        Application.builder()
        .token(settings.bot_token)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("health", health)
    )

    return application


def main() -> None:
    """Application entry point."""

    logger.info("Starting KOSFintech foundation...")

    application = build_application()

    logger.info(
        "KOSFintech Telegram application started."
    )

    application.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
