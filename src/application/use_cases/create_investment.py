from datetime import date
from decimal import Decimal
from uuid import UUID

from src.domain.entities.investment import Investment
from src.infrastructure.repositories.investment_repository import InvestmentRepository


class CreateInvestment:
    def __init__(self, repository: InvestmentRepository):
        self.repository = repository

    def execute(
        self,
        bank_id: UUID,
        name: str,
        investment_type: str,
        total_value: Decimal,
        application_date: date,
    ) -> Investment:
        investment = Investment.create(
            bank_id=bank_id,
            name=name,
            investment_type=investment_type,
            total_value=total_value,
            application_date=application_date,
        )
        return self.repository.create(investment)
