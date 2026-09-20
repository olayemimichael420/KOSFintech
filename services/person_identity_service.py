from models.person import Person
from repositories.person_repository import PersonRepository


class PersonIdentityService:
    """
    KOSFintech-wide human identity service.

    Person identifies the human being. This service does not establish
    authentication, membership, capacity, recognition, assignment,
    participation, authorization, or institutional authority.
    """

    def __init__(self, repository: PersonRepository):
        self.repository = repository

    def create(self, person: Person) -> Person:
        return self.repository.create(person)

    def get(self, person_id: int):
        return self.repository.get(person_id)

    def list(self):
        return self.repository.list()
