from models.assessment import Assessment
from models.assessment_score import AssessmentScore
from models.church_anchor import ChurchAnchor
from models.learning_evidence import LearningEvidence
from models.membership import Membership
from models.person import Person
from models.progress import Progress
from models.result import Result
from models.teaching_content import TeachingContent
from models.teaching_focus import TeachingFocus
from models.teaching_series import TeachingSeries
from models.teaching_session import TeachingSession
from models.teaching_session_attendance import TeachingSessionAttendance
from models.teaching_session_member import TeachingSessionMemberLink
from models.teaching_session_subject import TeachingSessionSubject
from models.teaching_subject import TeachingSubject
from models.teacher_preacher import TeacherPreacher, TeacherPreacherRole
from models.teacher_preacher_subject_assignment import (
    TeacherPreacherSubjectAssignment,
)
from models.teaching_content_teacher_preacher_assignment import (
    TeachingContentTeacherPreacherAssignment,
)
from models.grade import Grade
from repositories.church_anchor_repository import ChurchAnchorRepository
from repositories.person_repository import PersonRepository
from repositories.teacher_preacher_repository import TeacherPreacherRepository
from services.application_service_factory import ApplicationServiceFactory
from services.application_services import ApplicationServices


def test_cmos_teaching_workflow_end_to_end(db_connection):
    connection = db_connection
    tenant_id = "tenant-cmos"

    connection.execute(
        "INSERT INTO tenants (tenant_id) VALUES (?)",
        (tenant_id,),
    )

    # Prerequisite institutional records.
    person = PersonRepository(connection).create(
        Person(id=None, name="CMOS Member")
    )

    anchor = ChurchAnchorRepository(connection).create(
        ChurchAnchor(
            id=None,
            tenant_id=tenant_id,
            name="CMOS Church",
            provenance_reference="test",
        )
    )

    factory = ApplicationServiceFactory(connection)
    services = ApplicationServices(factory)

    membership = services.membership(tenant_id).create(
        Membership(
            id=None,
            tenant_id=tenant_id,
            person_id=person.id,
            church_anchor_id=anchor.id,
            provenance_reference="test",
        )
    )

    # Application service surface.

    session = services.teaching_session(tenant_id).create(
        TeachingSession(
            id=None,
            tenant_id=tenant_id,
            name="Foundations of Faith",
            start_date="2026-09-19",
            end_date="2026-09-19",
        )
    )

    subject = services.teaching_subject(tenant_id).create(
        TeachingSubject(
            id=None,
            tenant_id=tenant_id,
            name="Faith",
        )
    )

    session_subject = services.teaching_session_subject(tenant_id).create(
        TeachingSessionSubject(
            id=None,
            tenant_id=tenant_id,
            teaching_session_id=session.id,
            teaching_subject_id=subject.id,
        )
    )

    series = services.teaching_series(tenant_id).create(
        TeachingSeries(
            id=None,
            tenant_id=tenant_id,
            teaching_session_id=session.id,
            name="Faith Foundations",
            start_date="2026-09-19",
            end_date="2026-09-19",
        )
    )

    focus = services.teaching_focus(tenant_id).create(
        TeachingFocus(
            id=None,
            tenant_id=tenant_id,
            teaching_series_id=series.id,
            name="Faith and Action",
            start_date="2026-09-19",
            end_date="2026-09-19",
        )
    )

    content = services.teaching_content(tenant_id).create(
        TeachingContent(
            id=None,
            tenant_id=tenant_id,
            teaching_focus_id=focus.id,
            name="Faith Demonstrated Through Action",
            description="Observable application of the teaching.",
            sequence=1,
        )
    )

    teacher_person = PersonRepository(connection).create(
        Person(id=None, name="CMOS Teacher")
    )

    teacher = TeacherPreacherRepository(connection).create(
        TeacherPreacher(
            id=None,
            tenant_id=tenant_id,
            person_id=teacher_person.id,
            role=TeacherPreacherRole.TEACHER,
        )
    )

    subject_assignment = services.teacher_preacher_subject_assignment(
        tenant_id
    ).create(
        TeacherPreacherSubjectAssignment(
            id=None,
            tenant_id=tenant_id,
            teacher_preacher_id=teacher.id,
            teaching_subject_id=subject.id,
        )
    )

    assert subject_assignment.tenant_id == tenant_id
    assert subject_assignment.teacher_preacher_id == teacher.id
    assert subject_assignment.teaching_subject_id == subject.id

    assignment = services.teaching_content_teacher_preacher_assignment(
        tenant_id
    ).create(
        TeachingContentTeacherPreacherAssignment(
            id=None,
            tenant_id=tenant_id,
            teaching_content_id=content.id,
            teacher_preacher_id=teacher.id,
        )
    )

    session_member = services.teaching_session_member(tenant_id).create(
        TeachingSessionMemberLink(
            tenant_id=tenant_id,
            teaching_session_id=session.id,
            membership_id=membership.id,
        )
    )

    attendance = services.teaching_session_attendance(tenant_id).record(
        TeachingSessionAttendance(
            id=None,
            tenant_id=tenant_id,
            teaching_session_id=session.id,
            membership_id=membership.id,
            attendance_date="2026-09-19",
            status="present",
        )
    )

    evidence = services.learning_evidence(tenant_id).record(
        LearningEvidence(
            id=None,
            tenant_id=tenant_id,
            membership_id=membership.id,
            teaching_content_id=content.id,
            evidence_date="2026-09-19",
            description="Member demonstrated the taught principle.",
        )
    )

    assessment = services.assessment(tenant_id).record(
        Assessment(
            id=None,
            tenant_id=tenant_id,
            teaching_content_id=content.id,
            name="Faith in Action Review",
            assessment_date="2026-09-19",
        )
    )

    grade = services.grade(tenant_id).record(
        Grade(
            id=None,
            tenant_id=tenant_id,
            name="A",
            minimum_score=80,
            maximum_score=100,
        )
    )

    score = AssessmentScore(
        id=None,
        tenant_id=tenant_id,
        assessment_id=assessment.id,
        membership_id=membership.id,
        score=88,
        scored_date="2026-09-19",
    )

    result = Result(
        id=None,
        tenant_id=tenant_id,
        assessment_id=assessment.id,
        membership_id=membership.id,
        grade_id=grade.id,
        result="completed",
        result_date="2026-09-19",
    )

    recorded_score, recorded_result = (
        services.cmos_assessment_outcome_workflow(tenant_id)
        .record_score_and_result(score, result)
    )

    progress = services.progress(tenant_id).record(
        Progress(
            id=None,
            tenant_id=tenant_id,
            membership_id=membership.id,
            teaching_content_id=content.id,
            progress_date="2026-09-19",
            description="Observable improvement in applying the teaching.",
        )
    )

    # Read-back verification through the application-service boundaries.
    assert services.membership(tenant_id).get(membership.id).tenant_id == tenant_id
    assert services.teaching_session(tenant_id).get(session.id).tenant_id == tenant_id
    assert services.teaching_subject(tenant_id).get(subject.id).tenant_id == tenant_id
    assert services.teaching_session_subject(tenant_id).get(session_subject.id).tenant_id == tenant_id
    assert services.teaching_series(tenant_id).get(series.id).tenant_id == tenant_id
    assert services.teaching_focus(tenant_id).get(focus.id).tenant_id == tenant_id
    assert services.teaching_content(tenant_id).get(content.id).tenant_id == tenant_id
    assert services.teaching_content_teacher_preacher_assignment(tenant_id).get(
        assignment.id
    ).tenant_id == tenant_id
    assert services.teaching_session_member(tenant_id).get(
        session.id, membership.id
    ).tenant_id == tenant_id
    assert services.teaching_session_attendance(tenant_id).get(
        attendance.id
    ).tenant_id == tenant_id
    assert services.learning_evidence(tenant_id).get(evidence.id).tenant_id == tenant_id
    assert services.assessment(tenant_id).get(assessment.id).tenant_id == tenant_id
    assert services.assessment_score(tenant_id).get(
        recorded_score.id
    ).tenant_id == tenant_id
    assert services.grade(tenant_id).get(grade.id).tenant_id == tenant_id
    assert services.result(tenant_id).get(recorded_result.id).tenant_id == tenant_id
    assert services.progress(tenant_id).get(progress.id).tenant_id == tenant_id

    # The complete scenario remains tenant/member/content coherent.
    assert session.id is not None
    assert session_subject.id is not None
    assert assignment.id is not None
    assert session_member.membership_id == membership.id
    assert attendance.membership_id == membership.id
    assert evidence.membership_id == membership.id
    assert evidence.teaching_content_id == content.id
    assert assessment.teaching_content_id == content.id
    assert recorded_score.assessment_id == assessment.id
    assert recorded_score.membership_id == membership.id
    assert recorded_result.assessment_id == assessment.id
    assert recorded_result.membership_id == membership.id
    assert recorded_result.grade_id == grade.id
    assert progress.membership_id == membership.id
    assert progress.teaching_content_id == content.id
