from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.application.services.reporting_service import ReportingService
from src.infrastructure.database.connection import SessionLocal, init_db
from src.infrastructure.repositories.finance_repository import FinanceRepository


def main():
    init_db()
    with SessionLocal() as session:
        report = ReportingService(FinanceRepository(session)).ensure_monthly_report_for_today()
    if report is None:
        print("Hoje não é o último dia do mês; nenhum relatório foi gerado.")
    else:
        print(f"Relatório {report['month_key']} gerado e salvo no banco de dados.")


if __name__ == "__main__":
    main()
