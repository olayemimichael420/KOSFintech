import uuid

from database import get_connection, init_db
from models.academic_subject import AcademicSubject
from repositories.academic_subject_repository import AcademicSubjectRepository


def _school(connection, tenant_id):
    connection.execute(
        """
        INSERT INTO schools (
            tenant_id, name, school_type, country, currency
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (tenant_id, "Test School", "secondary", "NG", "NGN"),
    )
    connection.commit()


def test_create_and_get_subject():
    init_db()
    connection = get_connection()
    tenant_id = f"subject-{uuid.uuid4().hex}"

    try:
        _school(connection, tenant_id)
        repository = AcademicSubjectRepository(connection)

        subject = repository.create(
            AcademicSubject(
                id=None,
                tenant_id=tenant_id,
                name="Mathematics",
            )
        )

        loaded = repository.get(tenant_id, subject.id)

        assert loaded is not None
        assert loaded.name == "Mathematics"
    finally:
        connection.close()


def test_subject_names_are_vocabulary_neutral():
    init_db()
    connection = get_connection()
    tenant_id = f"subject-{uuid.uuid4().hex}"

    try:
        _school(connection, tenant_id)
        repository = AcademicSubjectRepository(connection)

        for name in (
            "Mathematics",
            "English Language",
            "Integrated Science",
            "Welding Technology",
            "Advanced Quantum Computing",
        ):
            repository.create(
                AcademicSubject(
                    id=None,
                    tenant_id=tenant_id,
                    name=name,
                )
            )

        assert len(repository.list(tenant_id)) == 5
    finally:
        connection.close()


def test_subject_get_is_tenant_scoped():
    init_db()
    connection = get_connection()
    suffix = uuid.uuid4().hex
    tenant_a = f"subject-a-{suffix}"
    tenant_b = f"subject-b-{suffix}"

    try:
        _school(connection, tenant_a)
        _school(connection, tenant_b)

        repository = AcademicSubjectRepository(connection)

        subject = repository.create(
            AcademicSubject(
                id=None,
                tenant_id=tenant_a,
                name="Physics",
            )
        )

        assert repository.get(tenant_a, subject.id) is not None
        assert repository.get(tenant_b, subject.id) is None
    finally:
        connection.close()


def test_subject_list_is_tenant_scoped():
    init_db()
    connection = get_connection()
    suffix = uuid.uuid4().hex
    tenant_a = f"subject-list-a-{suffix}"
    tenant_b = f"subject-list-b-{suffix}"

    try:
        _school(connection, tenant_a)
        _school(connection, tenant_b)

        repository = AcademicSubjectRepository(connection)

        repository.create(
            AcademicSubject(
                id=None,
                tenant_id=tenant_a,
                name="Chemistry",
            )
        )
        repository.create(
            AcademicSubject(
                id=None,
                tenant_id=tenant_b,
                name="History",
            )
        )

        subjects = repository.list(tenant_a)

        assert len(subjects) == 1
        assert subjects[0].name == "Chemistry"
    finally:
        connection.close()


def test_duplicate_subject_name_rejected_within_tenant():
    init_db()
    connection = get_connection()
    tenant_id = f"subject-duplicate-{uuid.uuid4().hex}"

    try:
        _school(connection, tenant_id)
        repository = AcademicSubjectRepository(connection)

        repository.create(
            AcademicSubject(
                id=None,
                tenant_id=tenant_id,
                name="Biology",
            )
        )

        try:
            repository.create(
                AcademicSubject(
                    id=None,
                    tenant_id=tenant_id,
                    name="Biology",
                )
            )
            assert False, "duplicate subject should be rejected"
        except Exception as exc:
            assert "UNIQUE" in str(exc).upper()
    finally:
        connection.close()
