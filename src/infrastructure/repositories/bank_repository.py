from src.infrastructure.database.models import BankModel

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
