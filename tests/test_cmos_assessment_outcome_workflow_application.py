from services.application_services import ApplicationServices
from services.cmos_assessment_outcome_workflow_service import (
    CMOSAssessmentOutcomeWorkflowService,
)


def test_application_services_exposes_cmos_assessment_outcome_workflow():
    services = object.__new__(ApplicationServices)

    score_service = object()
    result_service = object()

    services.assessment_score = lambda tenant_id, user_id=None: score_service
    services.result = lambda tenant_id, user_id=None: result_service

    workflow = services.cmos_assessment_outcome_workflow(
        tenant_id="tenant-test",
        user_id=123,
    )

    assert isinstance(workflow, CMOSAssessmentOutcomeWorkflowService)
    assert workflow.assessment_score_service is score_service
    assert workflow.result_service is result_service
