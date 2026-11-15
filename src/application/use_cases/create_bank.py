from src.domain.entities.bank import Bank
from src.infrastructure.repositories.bank_repository import BankRepository

class CreateBank:

    def __init__(self, repository: BankRepository):
        self.repository = repository

    def execute(self, name: str):
        bank = Bank.create(name)

        return self.repository.create(bank)
