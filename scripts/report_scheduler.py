import calendar
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.application.services.reporting_service import ReportingService
from src.infrastructure.database.connection import SessionLocal, init_db
from src.infrastructure.repositories.finance_repository import FinanceRepository


TIMEZONE = ZoneInfo(os.getenv("APP_TIMEZONE", "America/Sao_Paulo"))


def generate_for_today(today):
    with SessionLocal() as session:
        return ReportingService(FinanceRepository(session)).ensure_monthly_report_for_today(today)


def main():
    init_db()
    # Catch up a missed month after a restart, then check the final day at 23:55.
    try:
        now = datetime.now(TIMEZONE)
        last_day = calendar.monthrange(now.year, now.month)[1]
        if now.day != last_day or (now.hour, now.minute) >= (23, 55):
            report = generate_for_today(now.date())
            if report:
                print(f"Relatório {report['month_key']} salvo.", flush=True)
    except Exception:
        traceback.print_exc()

    generated_month = None
    while True:
        now = datetime.now(TIMEZONE)
        last_day = calendar.monthrange(now.year, now.month)[1]
        month_key = now.strftime("%Y-%m")
        if now.day == last_day and (now.hour, now.minute) >= (23, 55) and generated_month != month_key:
            try:
                report = generate_for_today(now.date())
                if report:
                    print(f"Relatório {report['month_key']} salvo.", flush=True)
                generated_month = month_key
            except Exception:
                traceback.print_exc()
        time.sleep(30)


if __name__ == "__main__":
    main()
