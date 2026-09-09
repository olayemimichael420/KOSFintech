class JudicialRecusalEnforcementService:
    """
    J6D enforcement gate.

    This service does not create, resolve, or adjudicate recusals.
    It only determines whether an already-authorized judicial authority
    is currently recused from the requested jurisdiction or proceeding.
    """

    def __init__(self, connection):
        self.connection = connection

    def require_not_recused(
        self,
        tenant_id,
        judicial_authority_id,
        jurisdiction_id,
        proceeding_id,
    ):
        jurisdiction_recusal = self.connection.execute(
            """
            SELECT id
            FROM judicial_recusals
            WHERE tenant_id = ?
              AND judicial_authority_id = ?
              AND jurisdiction_id = ?
              AND scope = 'jurisdiction'
              AND status = 'active'
            LIMIT 1
            """,
            (
                tenant_id,
                judicial_authority_id,
                jurisdiction_id,
            ),
        ).fetchone()

        if jurisdiction_recusal is not None:
            raise ValueError(
                "judicial authority is recused from this jurisdiction"
            )

        proceeding_recusal = self.connection.execute(
            """
            SELECT id
            FROM judicial_recusals
            WHERE tenant_id = ?
              AND judicial_authority_id = ?
              AND jurisdiction_id = ?
              AND proceeding_id = ?
              AND scope = 'proceeding'
              AND status = 'active'
            LIMIT 1
            """,
            (
                tenant_id,
                judicial_authority_id,
                jurisdiction_id,
                proceeding_id,
            ),
        ).fetchone()

        if proceeding_recusal is not None:
            raise ValueError(
                "judicial authority is recused from this proceeding"
            )
