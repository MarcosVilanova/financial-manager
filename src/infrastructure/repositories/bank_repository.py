from src.domain.entities.bank import Bank
from src.infrastructure.database.models import BankModel, CreditCardModel, InvestmentModel

class BankRepository:

    def __init__(self, session):
        self.session = session

    def create(self, bank):
        bank_model = BankModel.from_entity(bank)

        self.session.add(bank_model)
        self.session.commit()

        return bank

    def get_all(self):
        banks = self.session.query(BankModel).all()

        return [bank.to_entity() for bank in banks]

    def update(self, bank_id, name):
        row = self.session.get(BankModel, str(bank_id))
        if row is None:
            raise ValueError("Instituição financeira não encontrada.")
        validated = Bank.create(name)
        row.name = validated.name
        self.session.commit()
        return row.to_entity()

    def delete(self, bank_id):
        row = self.session.get(BankModel, str(bank_id))
        if row is None:
            raise ValueError("Instituição financeira não encontrada.")
        has_investments = self.session.query(InvestmentModel.id).filter_by(bank_id=str(bank_id)).first()
        has_cards = self.session.query(CreditCardModel.id).filter_by(bank_id=str(bank_id)).first()
        if has_investments or has_cards:
            raise ValueError("Remova ou transfira os investimentos e cartões vinculados antes de excluir a instituição.")
        self.session.delete(row)
        self.session.commit()
