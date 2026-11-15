from datetime import date

from src.domain.entities.investment_snapshot import InvestmentSnapshot
from src.domain.entities.investment import Investment
from src.infrastructure.database.models import InvestmentModel
from src.infrastructure.database.models import InvestmentSnapshotModel


class InvestmentRepository:
    def __init__(self, session):
        self.session = session

    def create(self, investment):
        investment_model = InvestmentModel.from_entity(investment)
        self.session.add(investment_model)
        initial_snapshot = InvestmentSnapshot.create(
            investment.id, date.today(), investment.total_value
        )
        self.session.add(InvestmentSnapshotModel.from_entity(initial_snapshot))
        self.session.commit()
        return investment

    def get_all(self):
        investments = (
            self.session.query(InvestmentModel)
            .order_by(InvestmentModel.application_date.desc(), InvestmentModel.name)
            .all()
        )
        return [investment.to_entity() for investment in investments]

    def update(self, investment_id, bank_id, name, investment_type, application_date):
        row = self.session.get(InvestmentModel, str(investment_id))
        if row is None:
            raise ValueError("Investimento não encontrado.")
        validated = Investment.create(
            bank_id, name, investment_type, row.total_value, application_date
        )
        row.bank_id = str(bank_id)
        row.name = validated.name
        row.investment_type = validated.investment_type
        row.application_date = application_date
        self.session.commit()
        return row.to_entity()

    def delete(self, investment_id):
        row = self.session.get(InvestmentModel, str(investment_id))
        if row is None:
            raise ValueError("Investimento não encontrado.")
        self.session.query(InvestmentSnapshotModel).filter_by(
            investment_id=str(investment_id)
        ).delete(synchronize_session=False)
        self.session.delete(row)
        self.session.commit()

    def update_snapshot(self, snapshot_id, snapshot_date, total_value, contributions):
        row = self.session.get(InvestmentSnapshotModel, str(snapshot_id))
        if row is None:
            raise ValueError("Atualização do investimento não encontrada.")
        InvestmentSnapshot.create(row.investment_id, snapshot_date, total_value, contributions)
        duplicate = self.session.query(InvestmentSnapshotModel.id).filter(
            InvestmentSnapshotModel.investment_id == row.investment_id,
            InvestmentSnapshotModel.snapshot_date == snapshot_date,
            InvestmentSnapshotModel.id != row.id,
        ).first()
        if duplicate:
            raise ValueError("Já existe uma atualização desse investimento nessa data.")
        row.snapshot_date = snapshot_date
        row.total_value = total_value
        row.contributions = contributions
        self._sync_current_value(row.investment_id)
        self.session.commit()
        return row.to_entity()

    def delete_snapshot(self, snapshot_id):
        row = self.session.get(InvestmentSnapshotModel, str(snapshot_id))
        if row is None:
            raise ValueError("Atualização do investimento não encontrada.")
        investment_id = row.investment_id
        self.session.delete(row)
        self._sync_current_value(investment_id)
        self.session.commit()

    def _sync_current_value(self, investment_id):
        investment = self.session.get(InvestmentModel, str(investment_id))
        latest = (
            self.session.query(InvestmentSnapshotModel)
            .filter_by(investment_id=str(investment_id))
            .order_by(InvestmentSnapshotModel.snapshot_date.desc(), InvestmentSnapshotModel.id.desc())
            .first()
        )
        if investment is not None and latest is not None:
            investment.total_value = latest.total_value
