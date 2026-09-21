from unittest.mock import Mock

from services.cmos_assessment_outcome_workflow_service import (
    CMOSAssessmentOutcomeWorkflowService,
)


def test_record_score_and_result_delegates_explicitly():
    assessment_score_service = Mock()
    result_service = Mock()

    assessment_score = object()
    result = object()

    assessment_score_service.record.return_value = "recorded-score"
    result_service.record.return_value = "recorded-result"

    workflow = CMOSAssessmentOutcomeWorkflowService(
        assessment_score_service=assessment_score_service,
        result_service=result_service,
    )

    returned_score, returned_result = workflow.record_score_and_result(
        assessment_score=assessment_score,
        result=result,
    )

    assessment_score_service.record.assert_called_once_with(
        assessment_score
    )
    result_service.record.assert_called_once_with(result)

    assert returned_score == "recorded-score"
    assert returned_result == "recorded-result"
