from typing import Optional

from models.person import Person


class PersonRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(self, person: Person) -> Person:
        cursor = self.connection.execute(
            """
            INSERT INTO persons (
                name,
                status
            )
            VALUES (?, ?)
            """,
            (
                person.name,
                person.status,
            ),
        )
        self.connection.commit()

        return Person(
            id=cursor.lastrowid,
            name=person.name,
            status=person.status,
        )

    def get(self, person_id: int) -> Optional[Person]:
        row = self.connection.execute(
            """
            SELECT
                id,
                name,
                status
            FROM persons
            WHERE id = ?
            """,
            (person_id,),
        ).fetchone()

        if row is None:
            return None

        return self._to_model(row)

    def list(self) -> list[Person]:
        rows = self.connection.execute(
            """
            SELECT
                id,
                name,
                status
            FROM persons
            ORDER BY id
            """
        ).fetchall()

        return [self._to_model(row) for row in rows]

    @staticmethod
    def _to_model(row) -> Person:
        return Person(
            id=row["id"],
            name=row["name"],
            status=row["status"],
        )
