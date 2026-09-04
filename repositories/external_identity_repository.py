from models.external_identity import ExternalIdentity


class ExternalIdentityRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(self, identity: ExternalIdentity) -> ExternalIdentity:
        cursor = self.connection.execute(
            """
            INSERT INTO external_identities (
                provider,
                subject,
                tenant_id,
                user_id
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                identity.provider,
                identity.subject,
                identity.tenant_id,
                identity.user_id,
            ),
        )

        self.connection.commit()

        identity.id = cursor.lastrowid
        return identity

    def get(self, identity_id: int):
        row = self.connection.execute(
            """
            SELECT
                id,
                provider,
                subject,
                tenant_id,
                user_id,
                created_at
            FROM external_identities
            WHERE id = ?
            """,
            (identity_id,),
        ).fetchone()

        if row is None:
            return None

        return ExternalIdentity(
            id=row["id"],
            provider=row["provider"],
            subject=row["subject"],
            tenant_id=row["tenant_id"],
            user_id=row["user_id"],
            created_at=row["created_at"],
        )

    def get_by_provider_subject(
        self,
        provider: str,
        subject: str,
    ):
        row = self.connection.execute(
            """
            SELECT
                id,
                provider,
                subject,
                tenant_id,
                user_id,
                created_at
            FROM external_identities
            WHERE provider = ?
              AND subject = ?
            """,
            (provider, subject),
        ).fetchone()

        if row is None:
            return None

        return ExternalIdentity(
            id=row["id"],
            provider=row["provider"],
            subject=row["subject"],
            tenant_id=row["tenant_id"],
            user_id=row["user_id"],
            created_at=row["created_at"],
        )

    def list_by_user(
        self,
        tenant_id: str,
        user_id: int,
    ):
        rows = self.connection.execute(
            """
            SELECT
                id,
                provider,
                subject,
                tenant_id,
                user_id,
                created_at
            FROM external_identities
            WHERE tenant_id = ?
              AND user_id = ?
            ORDER BY id
            """,
            (tenant_id, user_id),
        ).fetchall()

        return [
            ExternalIdentity(
                id=row["id"],
                provider=row["provider"],
                subject=row["subject"],
                tenant_id=row["tenant_id"],
                user_id=row["user_id"],
                created_at=row["created_at"],
            )
            for row in rows
        ]
