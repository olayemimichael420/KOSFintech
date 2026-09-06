from models.telegram_channel_binding import TelegramChannelBinding


class TelegramChannelBindingRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(self, binding: TelegramChannelBinding) -> TelegramChannelBinding:
        cursor = self.connection.execute(
            """
            INSERT INTO telegram_channel_bindings (
                provider,
                chat_id,
                tenant_id,
                administration_id,
                binding_type,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                binding.provider,
                binding.chat_id,
                binding.tenant_id,
                binding.administration_id,
                binding.binding_type,
                binding.status,
            ),
        )

        self.connection.commit()
        binding.id = cursor.lastrowid
        return binding

    def get(self, binding_id: int):
        row = self.connection.execute(
            """
            SELECT
                id,
                provider,
                chat_id,
                tenant_id,
                administration_id,
                binding_type,
                status,
                created_at
            FROM telegram_channel_bindings
            WHERE id = ?
            """,
            (binding_id,),
        ).fetchone()

        if row is None:
            return None

        return TelegramChannelBinding(
            id=row["id"],
            provider=row["provider"],
            chat_id=row["chat_id"],
            tenant_id=row["tenant_id"],
            administration_id=row["administration_id"],
            binding_type=row["binding_type"],
            status=row["status"],
            created_at=row["created_at"],
        )

    def get_by_provider_chat(self, provider: str, chat_id: str):
        row = self.connection.execute(
            """
            SELECT
                id,
                provider,
                chat_id,
                tenant_id,
                administration_id,
                binding_type,
                status,
                created_at
            FROM telegram_channel_bindings
            WHERE provider = ?
              AND chat_id = ?
            """,
            (provider, chat_id),
        ).fetchone()

        if row is None:
            return None

        return TelegramChannelBinding(
            id=row["id"],
            provider=row["provider"],
            chat_id=row["chat_id"],
            tenant_id=row["tenant_id"],
            administration_id=row["administration_id"],
            binding_type=row["binding_type"],
            status=row["status"],
            created_at=row["created_at"],
        )
