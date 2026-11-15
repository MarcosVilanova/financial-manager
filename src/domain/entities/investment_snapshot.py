from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4


@dataclass(frozen=True)
class InvestmentSnapshot:
    id: UUID
    investment_id: UUID
    snapshot_date: date
    total_value: Decimal
    contributions: Decimal

    @staticmethod
    def create(investment_id, snapshot_date, total_value, contributions=Decimal("0")):
        if total_value <= 0:
            raise ValueError("O valor total deve ser maior que zero.")
        if contributions < 0:
            raise ValueError("Os aportes não podem ser negativos.")
        return InvestmentSnapshot(
            id=uuid4(),
            investment_id=investment_id,
            snapshot_date=snapshot_date,
            total_value=total_value,
            contributions=contributions,
        )
