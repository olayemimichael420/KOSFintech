class TalentPointPolicy:
    """Economic policy governing Talent Point issuance."""

    DAILY_MINT_CAP = 50_000
    TOTAL_SUPPLY_CAP = 100_000_000

    @classmethod
    def validate_amount(cls, amount: int) -> None:
        if not isinstance(amount, int):
            raise ValueError("Talent Point amount must be an integer")

        if amount <= 0:
            raise ValueError("Talent Point amount must be greater than zero")

    @classmethod
    def validate_daily_cap(
        cls,
        current_daily_issued: int,
        amount: int,
    ) -> None:
        if current_daily_issued + amount > cls.DAILY_MINT_CAP:
            raise ValueError("daily Talent Point issuance cap exceeded")

    @classmethod
    def validate_total_supply(
        cls,
        current_total_issued: int,
        amount: int,
    ) -> None:
        if current_total_issued + amount > cls.TOTAL_SUPPLY_CAP:
            raise ValueError("total Talent Point supply cap exceeded")
