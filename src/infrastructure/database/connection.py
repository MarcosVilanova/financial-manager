import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date
from uuid import uuid4

from src.infrastructure.database.base import Base
from src.infrastructure.database.models import (
    BankModel,
    InvestmentModel,
    InvestmentSnapshotModel,
)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///financial_manager.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False, "timeout": 30}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def init_db():
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        investments = session.query(InvestmentModel).all()
        for investment in investments:
            has_snapshot = (
                session.query(InvestmentSnapshotModel.id)
                .filter(InvestmentSnapshotModel.investment_id == investment.id)
                .first()
            )
            if not has_snapshot:
                session.add(InvestmentSnapshotModel(
                    id=str(uuid4()),
                    investment_id=investment.id,
                    snapshot_date=date.today(),
                    total_value=investment.total_value,
                    contributions=0,
                ))
        session.commit()
