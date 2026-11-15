from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.entities.bank import Bank
from src.domain.entities.credit_card import CreditCard
from src.domain.entities.expense import Expense
from src.domain.entities.investment import Investment
from src.domain.entities.investment_snapshot import InvestmentSnapshot
from src.domain.entities.loan import Loan
from src.infrastructure.database.base import Base


class BankModel(Base):
    __tablename__ = "banks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    @staticmethod
    def from_entity(bank: Bank):
        return BankModel(id=str(bank.id), name=bank.name)

    def to_entity(self):
        return Bank(id=UUID(self.id), name=self.name)


class InvestmentModel(Base):
    __tablename__ = "investments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    bank_id: Mapped[str] = mapped_column(String(36), ForeignKey("banks.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    investment_type: Mapped[str] = mapped_column(String(50), nullable=False)
    total_value: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    application_date: Mapped[date] = mapped_column(Date, nullable=False)

    @staticmethod
    def from_entity(investment: Investment):
        return InvestmentModel(
            id=str(investment.id), bank_id=str(investment.bank_id), name=investment.name,
            investment_type=investment.investment_type, total_value=investment.total_value,
            application_date=investment.application_date,
        )

    def to_entity(self):
        return Investment(
            id=UUID(self.id), bank_id=UUID(self.bank_id), name=self.name,
            investment_type=self.investment_type, total_value=self.total_value,
            application_date=self.application_date,
        )


class InvestmentSnapshotModel(Base):
    __tablename__ = "investment_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    investment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("investments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    total_value: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    contributions: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0"))

    @staticmethod
    def from_entity(snapshot: InvestmentSnapshot):
        return InvestmentSnapshotModel(
            id=str(snapshot.id), investment_id=str(snapshot.investment_id),
            snapshot_date=snapshot.snapshot_date, total_value=snapshot.total_value,
            contributions=snapshot.contributions,
        )

    def to_entity(self):
        return InvestmentSnapshot(
            id=UUID(self.id), investment_id=UUID(self.investment_id),
            snapshot_date=self.snapshot_date, total_value=self.total_value,
            contributions=self.contributions,
        )


class CreditCardModel(Base):
    __tablename__ = "credit_cards"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    bank_id: Mapped[str] = mapped_column(String(36), ForeignKey("banks.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    due_day: Mapped[int] = mapped_column(Integer, nullable=False)
    closing_day: Mapped[int] = mapped_column(Integer, nullable=False)

    @staticmethod
    def from_entity(card: CreditCard):
        return CreditCardModel(
            id=str(card.id), bank_id=str(card.bank_id), name=card.name,
            due_day=card.due_day, closing_day=card.closing_day,
        )

    def to_entity(self):
        return CreditCard(
            UUID(self.id), UUID(self.bank_id), self.name, self.due_day, self.closing_day
        )


class ExpenseModel(Base):
    __tablename__ = "expenses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    expense_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    payment_method: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    card_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("credit_cards.id"), nullable=True)
    invoice_due_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)

    @staticmethod
    def from_entity(expense: Expense):
        return ExpenseModel(
            id=str(expense.id), description=expense.description, amount=expense.amount,
            expense_date=expense.expense_date, category=expense.category,
            payment_method=expense.payment_method,
            card_id=str(expense.card_id) if expense.card_id else None,
            invoice_due_date=expense.invoice_due_date,
        )

    def to_entity(self):
        return Expense(
            UUID(self.id), self.description, self.amount, self.expense_date, self.category,
            self.payment_method, UUID(self.card_id) if self.card_id else None,
            self.invoice_due_date,
        )


class LoanModel(Base):
    __tablename__ = "loans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    person_name: Mapped[str] = mapped_column(String(120), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    loan_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    note: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="Pendente", index=True)
    returned_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    @staticmethod
    def from_entity(loan: Loan):
        return LoanModel(
            id=str(loan.id), person_name=loan.person_name, amount=loan.amount,
            loan_date=loan.loan_date, note=loan.note, status=loan.status,
            returned_date=loan.returned_date,
        )

    def to_entity(self):
        return Loan(
            UUID(self.id), self.person_name, self.amount, self.loan_date,
            self.note, self.status, self.returned_date,
        )


class MonthlyReportModel(Base):
    __tablename__ = "monthly_reports"
    __table_args__ = (UniqueConstraint("month_key", name="uq_monthly_reports_month_key"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    month_key: Mapped[str] = mapped_column(String(7), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    content_json: Mapped[str] = mapped_column(Text, nullable=False)
