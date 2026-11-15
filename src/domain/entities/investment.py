from dataclasses import dataclass
from decimal import Decimal
from datetime import date
from uuid import UUID, uuid4

@dataclass
class Investment:
    id: UUID
    bank_id: UUID
    name: str
    investment_type: str
    total_value: Decimal
    application_date: date

    @staticmethod
    def create(
        bank_id: UUID,
        name: str,
        investment_type: str,
        total_value: Decimal,
        application_date: date
    ):
        if not name or not name.strip():
            raise ValueError("O nome do investimento é obrigatório.")

        if not investment_type or not investment_type.strip():
            raise ValueError("O tipo de investimento é obrigatório.")

        if total_value <= 0:
            raise ValueError("O valor deve ser maior que zero.")

        return Investment(
            id=uuid4(),
            bank_id=bank_id,
            name=name.strip(),
            investment_type=investment_type.strip(),
            total_value=total_value,
            application_date=application_date
        )
