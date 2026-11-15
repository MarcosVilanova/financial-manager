import calendar
from datetime import date
from decimal import Decimal

from src.domain.entities.credit_card import CreditCard
from src.domain.entities.expense import Expense
from src.domain.entities.investment_snapshot import InvestmentSnapshot
from src.domain.entities.loan import Loan


class FinanceService:
    def __init__(self, repository):
        self.repository = repository

    def create_card(self, bank_id, name, due_day, closing_day):
        card = CreditCard.create(bank_id, name, due_day, closing_day)
        return self.repository.create_card(card)

    def update_card(self, card_id, bank_id, name, due_day, closing_day):
        return self.repository.update_card(card_id, bank_id, name, due_day, closing_day)

    def delete_card(self, card_id):
        self.repository.delete_card(card_id)

    def create_expense(self, description, amount, expense_date, category, payment_method, card_id=None):
        invoice_due_date = None
        if payment_method == "Cartão de crédito":
            card = self.repository.get_card(card_id) if card_id else None
            if card is None:
                raise ValueError("Selecione um cartão cadastrado.")
            invoice_due_date = self._invoice_due_date(expense_date, card.closing_day, card.due_day)
        expense = Expense.create(
            description, amount, expense_date, category, payment_method, card_id, invoice_due_date
        )
        return self.repository.create_expense(expense)

    def update_expense(self, expense_id, description, amount, expense_date, category, payment_method, card_id=None):
        invoice_due_date = None
        if payment_method == "Cartão de crédito":
            card = self.repository.get_card(card_id) if card_id else None
            if card is None:
                raise ValueError("Selecione um cartão cadastrado.")
            invoice_due_date = self._invoice_due_date(expense_date, card.closing_day, card.due_day)
        expense = Expense.create(
            description, amount, expense_date, category, payment_method, card_id, invoice_due_date
        )
        return self.repository.update_expense(expense_id, expense)

    def delete_expense(self, expense_id):
        self.repository.delete_expense(expense_id)

    @staticmethod
    def _invoice_due_date(expense_date, closing_day, due_day):
        closing_month_last_day = calendar.monthrange(expense_date.year, expense_date.month)[1]
        closing_date = date(
            expense_date.year, expense_date.month, min(closing_day, closing_month_last_day)
        )
        if expense_date >= closing_date:
            if expense_date.month == 12:
                close_year, close_month = expense_date.year + 1, 1
            else:
                close_year, close_month = expense_date.year, expense_date.month + 1
        else:
            close_year, close_month = expense_date.year, expense_date.month

        due_month = close_month + 1 if due_day <= closing_day else close_month
        due_year = close_year
        if due_month == 13:
            due_year += 1
            due_month = 1
        due_last_day = calendar.monthrange(due_year, due_month)[1]
        return date(due_year, due_month, min(due_day, due_last_day))

    def create_loan(self, person_name, amount, loan_date, note=""):
        return self.repository.create_loan(Loan.create(person_name, amount, loan_date, note))

    def update_loan(self, loan_id, person_name, amount, loan_date, note, status, returned_date=None):
        loan = Loan.create(person_name, amount, loan_date, note)
        if status == "Devolvido":
            if returned_date is None:
                raise ValueError("Informe a data de devolução.")
            loan = loan.mark_returned(returned_date)
        elif status != "Pendente":
            raise ValueError("Status de empréstimo inválido.")
        return self.repository.update_loan(loan_id, loan)

    def delete_loan(self, loan_id):
        self.repository.delete_loan(loan_id)

    def mark_loan_returned(self, loan_id, returned_date):
        return self.repository.mark_loan_returned(loan_id, returned_date)

    def create_investment_snapshot(self, investment_id, snapshot_date, total_value, contributions):
        previous = self.repository.latest_snapshot(investment_id)
        if previous and snapshot_date <= previous.snapshot_date:
            raise ValueError("A data da atualização deve ser posterior ao último registro.")
        snapshot = InvestmentSnapshot.create(
            investment_id, snapshot_date, total_value, contributions
        )
        return self.repository.create_snapshot(snapshot)

    def update_investment_snapshot(self, snapshot_id, snapshot_date, total_value, contributions):
        return self.repository.update_snapshot(snapshot_id, snapshot_date, total_value, contributions)

    def delete_investment_snapshot(self, snapshot_id):
        self.repository.delete_snapshot(snapshot_id)

    def investment_history(self, investment_id):
        snapshots = self.repository.list_snapshots(investment_id)
        history = []
        previous = None
        for snapshot in snapshots:
            if previous:
                earnings = snapshot.total_value - previous.total_value - snapshot.contributions
                percentage = earnings / previous.total_value * Decimal("100")
            else:
                earnings = None
                percentage = None
            history.append({
                "snapshot": snapshot,
                "earnings": earnings,
                "percentage": percentage,
            })
            previous = snapshot
        return history

    @staticmethod
    def month_summary(expenses, year, month):
        return [expense for expense in expenses if expense.expense_date.year == year and expense.expense_date.month == month]
