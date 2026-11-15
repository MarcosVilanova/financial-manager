from src.infrastructure.repositories.investment_repository import InvestmentRepository


class ListInvestments:
    def __init__(self, repository: InvestmentRepository):
        self.repository = repository

    def execute(self):
        return self.repository.get_all()
