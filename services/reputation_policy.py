class ReputationPolicy:
    MIN_SCORE = 1
    MAX_SCORE = 5

    @classmethod
    def validate_score(cls, score: int) -> None:
        if not isinstance(score, int) or isinstance(score, bool):
            raise ValueError("reputation score must be an integer")

        if not cls.MIN_SCORE <= score <= cls.MAX_SCORE:
            raise ValueError(
                "reputation score must be between 1 and 5"
            )
