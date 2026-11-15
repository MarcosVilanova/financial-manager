from src.infrastructure.repositories.bank_repository import BankRepository

class ListBanks:

    def __init__(self, repository: BankRepository):
        self.repository = repository

    def execute(self):
        return self.repository.get_all()
