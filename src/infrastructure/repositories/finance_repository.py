import json
from datetime import datetime
from uuid import uuid4

from sqlalchemy import and_

from src.infrastructure.database.models import (
    CreditCardModel,
    ExpenseModel,
    InvestmentModel,
    InvestmentSnapshotModel,
    LoanModel,
    MonthlyReportModel,
)


class FinanceRepository:
    """Persistence operations for finance records; business rules live in application services."""

    def __init__(self, session):
        self.session = session

    def create_card(self, card):
        model = CreditCardModel.from_entity(card)
        self.session.add(model)
        self.session.commit()
        return card

    def list_cards(self):
        return [row.to_entity() for row in self.session.query(CreditCardModel).order_by(CreditCardModel.name).all()]

    def get_card(self, card_id):
        row = self.session.get(CreditCardModel, str(card_id))
        return row.to_entity() if row else None

    def create_expense(self, expense):
        self.session.add(ExpenseModel.from_entity(expense))
        self.session.commit()
        return expense

    def list_expenses(self, start_date=None, end_date=None, category=None, payment_method=None):
        query = self.session.query(ExpenseModel)
        filters = []
        if start_date:
            filters.append(ExpenseModel.expense_date >= start_date)
        if end_date:
            filters.append(ExpenseModel.expense_date <= end_date)
        if category and category != "Todas":
            filters.append(ExpenseModel.category == category)
        if payment_method and payment_method != "Todas":
            filters.append(ExpenseModel.payment_method == payment_method)
        if filters:
            query = query.filter(and_(*filters))
        return [row.to_entity() for row in query.order_by(ExpenseModel.expense_date.desc()).all()]

    def create_loan(self, loan):
        self.session.add(LoanModel.from_entity(loan))
        self.session.commit()
        return loan

    def list_loans(self):
        rows = self.session.query(LoanModel).order_by(LoanModel.loan_date.desc()).all()
        return [row.to_entity() for row in rows]

    def mark_loan_returned(self, loan_id, returned_date):
        row = self.session.get(LoanModel, str(loan_id))
        if row is None:
            raise ValueError("Empréstimo não encontrado.")
        loan = row.to_entity().mark_returned(returned_date)
        row.status = loan.status
        row.returned_date = loan.returned_date
        self.session.commit()
        return loan

    def list_investments(self):
        rows = self.session.query(InvestmentModel).order_by(InvestmentModel.name).all()
        return [row.to_entity() for row in rows]

    def get_investment(self, investment_id):
        row = self.session.get(InvestmentModel, str(investment_id))
        return row

    def list_snapshots(self, investment_id=None):
        query = self.session.query(InvestmentSnapshotModel)
        if investment_id:
            query = query.filter(InvestmentSnapshotModel.investment_id == str(investment_id))
        rows = query.order_by(InvestmentSnapshotModel.snapshot_date, InvestmentSnapshotModel.id).all()
        return [row.to_entity() for row in rows]

    def latest_snapshot(self, investment_id):
        row = (
            self.session.query(InvestmentSnapshotModel)
            .filter(InvestmentSnapshotModel.investment_id == str(investment_id))
            .order_by(InvestmentSnapshotModel.snapshot_date.desc(), InvestmentSnapshotModel.id.desc())
            .first()
        )
        return row.to_entity() if row else None

    def create_snapshot(self, snapshot):
        investment_row = self.get_investment(snapshot.investment_id)
        if investment_row is None:
            raise ValueError("Investimento não encontrado.")
        self.session.add(InvestmentSnapshotModel.from_entity(snapshot))
        investment_row.total_value = snapshot.total_value
        self.session.commit()
        return snapshot

    def get_report(self, month_key):
        row = self.session.query(MonthlyReportModel).filter_by(month_key=month_key).first()
        return json.loads(row.content_json) if row else None

    def list_reports(self):
        rows = self.session.query(MonthlyReportModel).order_by(MonthlyReportModel.month_key.desc()).all()
        return [(row.month_key, row.generated_at, json.loads(row.content_json)) for row in rows]

    def save_report(self, month_key, content, replace=False):
        row = self.session.query(MonthlyReportModel).filter_by(month_key=month_key).first()
        if row is not None:
            if not replace:
                return json.loads(row.content_json)
            row.generated_at = datetime.now()
            row.content_json = json.dumps(content, ensure_ascii=False)
            self.session.commit()
            return content
        row = MonthlyReportModel(
            id=str(uuid4()), month_key=month_key,
            generated_at=datetime.now(), content_json=json.dumps(content, ensure_ascii=False),
        )
        self.session.add(row)
        self.session.commit()
        return content
