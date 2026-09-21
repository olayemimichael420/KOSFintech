class CMOSAssessmentOutcomeWorkflowService:
    """
    Orchestrate explicit CMOS assessment score and result recording.

    This workflow does not calculate grades, infer results, establish
    learning, or advance progress. The caller supplies the explicit
    Result, including its grade_id and result value.
    """

    def __init__(
        self,
        assessment_score_service,
        result_service,
    ):
        self.assessment_score_service = assessment_score_service
        self.result_service = result_service

    def record_score_and_result(
        self,
        assessment_score,
        result,
    ):
        score = self.assessment_score_service.record(
            assessment_score
        )

        recorded_result = self.result_service.record(
            result
        )

        return score, recorded_result
