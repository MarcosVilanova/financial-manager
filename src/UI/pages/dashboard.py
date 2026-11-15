from datetime import date
from decimal import Decimal

import pandas as pd
import plotly.express as px
import streamlit as st

from src.infrastructure.database.connection import SessionLocal
from src.infrastructure.repositories.finance_repository import FinanceRepository
from src.infrastructure.repositories.investment_repository import InvestmentRepository
from src.UI.formatting import brl


def _month_expenses(expenses, year, month):
    return [row for row in expenses if row.expense_date.year == year and row.expense_date.month == month]


def show_dashboard():
    st.header("Visão geral")
    today = date.today()
    previous_year, previous_month = (today.year - 1, 12) if today.month == 1 else (today.year, today.month - 1)
    with SessionLocal() as session:
        finance_repo = FinanceRepository(session)
        investments = InvestmentRepository(session).get_all()
        snapshots = finance_repo.list_snapshots()
        expenses = finance_repo.list_expenses()
        loans = finance_repo.list_loans()

    portfolio = sum((item.total_value for item in investments), Decimal("0"))
    current_spend = _month_expenses(expenses, today.year, today.month)
    previous_spend = _month_expenses(expenses, previous_year, previous_month)
    current_total = sum((item.amount for item in current_spend), Decimal("0"))
    previous_total = sum((item.amount for item in previous_spend), Decimal("0"))
    spending_delta = current_total - previous_total
    spending_pct = spending_delta / previous_total * Decimal("100") if previous_total else None
    pending_loans = sum((item.amount for item in loans if item.status == "Pendente"), Decimal("0"))

    investment_gain = Decimal("0")
    opening_value = Decimal("0")
    snapshots_by_investment = {}
    for row in snapshots:
        snapshots_by_investment.setdefault(row.investment_id, []).append(row)
    for series in snapshots_by_investment.values():
        series.sort(key=lambda item: item.snapshot_date)
        denominator_added = False
        for index, snapshot in enumerate(series):
            if snapshot.snapshot_date.year == today.year and snapshot.snapshot_date.month == today.month and index > 0:
                previous = series[index - 1]
                investment_gain += snapshot.total_value - previous.total_value - snapshot.contributions
                if not denominator_added:
                    opening_value += previous.total_value
                    denominator_added = True

    cols = st.columns(4)
    cols[0].metric("Patrimônio investido", brl(portfolio))
    cols[1].metric("Rendimento no mês", brl(investment_gain))
    cols[2].metric(
        "Despesas do mês", brl(current_total),
        delta=f"{brl(spending_delta)} ({spending_pct:+.1f}%)" if spending_pct is not None else brl(spending_delta),
        delta_color="inverse",
    )
    cols[3].metric("Empréstimos pendentes", brl(pending_loans))

    if previous_total:
        st.caption(f"Despesas no mês anterior: {brl(previous_total)} · variação de {spending_pct:+.1f}%")
    else:
        st.caption("Ainda não há despesas registradas no mês anterior para comparação.")
    if opening_value:
        st.caption(f"Rendimento acumulado entre atualizações do mês: {brl(investment_gain)} ({investment_gain / opening_value * 100:+.2f}%).")
    else:
        st.caption("Registre pelo menos duas atualizações de um investimento para acompanhar rendimento no mês.")

    chart_left, chart_right = st.columns(2)
    with chart_left:
        st.subheader("Evolução dos investimentos")
        if snapshots:
            investment_names = {item.id: item.name for item in investments}
            frame = pd.DataFrame([
                {"Data": item.snapshot_date, "Valor": float(item.total_value), "Investimento": investment_names.get(item.investment_id, "Investimento")}
                for item in snapshots
            ])
            st.plotly_chart(px.line(frame, x="Data", y="Valor", color="Investimento", markers=True), use_container_width=True)
        else:
            st.info("Ainda não há histórico de investimentos.")
    with chart_right:
        st.subheader("Despesas por categoria neste mês")
        if current_spend:
            frame = pd.DataFrame([{"Categoria": item.category, "Valor": float(item.amount)} for item in current_spend])
            grouped = frame.groupby("Categoria", as_index=False)["Valor"].sum()
            st.plotly_chart(px.pie(grouped, names="Categoria", values="Valor", hole=0.45), use_container_width=True)
        else:
            st.info("Ainda não há despesas neste mês.")
