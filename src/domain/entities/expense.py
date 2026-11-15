from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4


@dataclass(frozen=True)
class Expense:
    id: UUID
    description: str
    amount: Decimal
    expense_date: date
    category: str
    payment_method: str
    card_id: UUID | None = None
    invoice_due_date: date | None = None

    @staticmethod
    def create(description, amount, expense_date, category, payment_method, card_id=None, invoice_due_date=None):
        if not description or not description.strip():
            raise ValueError("A descrição da despesa é obrigatória.")
        if amount <= 0:
            raise ValueError("O valor da despesa deve ser maior que zero.")
        if not category or not category.strip():
            raise ValueError("A categoria é obrigatória.")
        if payment_method not in {"PIX", "Cartão de crédito"}:
            raise ValueError("Forma de pagamento inválida.")
        if payment_method == "Cartão de crédito" and (card_id is None or invoice_due_date is None):
            raise ValueError("Selecione o cartão para calcular a fatura.")
        if payment_method == "PIX" and card_id is not None:
            raise ValueError("Despesas por PIX não podem estar associadas a um cartão.")
        return Expense(
            uuid4(), description.strip(), amount, expense_date, category.strip(),
            payment_method, card_id, invoice_due_date
        )
