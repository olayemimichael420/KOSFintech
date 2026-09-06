class TelegramChannelBindingService:
    """
    Resolve an active Telegram chat binding to its KOSFintech
    administration context.

    This service does not authenticate users or grant authority.
    """

    PROVIDER = "telegram"

    def __init__(self, repository):
        self.repository = repository

    def resolve_chat(self, chat_id):
        binding = self.repository.get_by_provider_chat(
            self.PROVIDER,
            str(chat_id),
        )

        if binding is None or binding.status != "active":
            return None

        return binding
