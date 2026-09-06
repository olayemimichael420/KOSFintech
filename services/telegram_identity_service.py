from services.authentication_service import AuthenticatedIdentity


class TelegramIdentityService:
    """
    Adapt a Telegram external identity into a canonical authenticated
    KOSFintech identity.

    This service establishes identity only. It does not assign authority,
    permissions, roles, or tenant membership.
    """

    PROVIDER = "telegram"

    def __init__(
        self,
        external_identity_service,
        authentication_service,
    ):
        self.external_identity_service = external_identity_service
        self.authentication_service = authentication_service

    def authenticate_update(self, update) -> AuthenticatedIdentity | None:
        """
        Resolve the Telegram user represented by an update into a
        currently authenticated canonical KOSFintech identity.
        """

        telegram_user = getattr(update, "effective_user", None)

        if telegram_user is None:
            return None

        subject = str(telegram_user.id)

        external_identity = self.external_identity_service.resolve(
            provider=self.PROVIDER,
            subject=subject,
        )

        if external_identity is None:
            return None

        return self.authentication_service.authenticate(
            user_id=external_identity.user_id,
        )
