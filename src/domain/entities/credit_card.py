from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass(frozen=True)
class CreditCard:
    id: UUID
    bank_id: UUID
    name: str
    due_day: int
    closing_day: int

    @staticmethod
    def create(bank_id, name, due_day, closing_day):
        if not name or not name.strip():
            raise ValueError("A identificação do cartão é obrigatória.")
        if not 1 <= due_day <= 31:
            raise ValueError("O vencimento deve estar entre os dias 1 e 31.")
        if not 1 <= closing_day <= 31:
            raise ValueError("O fechamento deve estar entre os dias 1 e 31.")
        return CreditCard(uuid4(), bank_id, name.strip(), due_day, closing_day)
