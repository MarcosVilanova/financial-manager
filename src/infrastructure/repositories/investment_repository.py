from datetime import date

from src.domain.entities.investment_snapshot import InvestmentSnapshot
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
