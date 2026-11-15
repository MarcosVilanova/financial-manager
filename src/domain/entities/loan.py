from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4


@dataclass(frozen=True)
class Loan:
    id: UUID
    person_name: str
    amount: Decimal
    loan_date: date
    note: str
    status: str = "Pendente"
    returned_date: date | None = None

    @staticmethod
    def create(person_name, amount, loan_date, note=""):
        if not person_name or not person_name.strip():
            raise ValueError("O nome da pessoa é obrigatório.")
        if amount <= 0:
            raise ValueError("O valor emprestado deve ser maior que zero.")
        return Loan(uuid4(), person_name.strip(), amount, loan_date, note.strip())

    def mark_returned(self, returned_date):
        if self.status == "Devolvido":
            raise ValueError("Este empréstimo já foi marcado como devolvido.")
        if returned_date < self.loan_date:
            raise ValueError("A data de devolução não pode ser anterior à data do empréstimo.")
        return Loan(
            self.id, self.person_name, self.amount, self.loan_date,
            self.note, "Devolvido", returned_date
        )
