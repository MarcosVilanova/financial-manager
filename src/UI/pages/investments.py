from datetime import date
from decimal import Decimal, InvalidOperation

import pandas as pd
import plotly.express as px
import streamlit as st

from src.application.services.finance_service import FinanceService
from src.application.use_cases.create_investment import CreateInvestment
from src.application.use_cases.list_investments import ListInvestments
from src.infrastructure.database.connection import SessionLocal
from src.infrastructure.repositories.bank_repository import BankRepository
from src.infrastructure.repositories.finance_repository import FinanceRepository
from src.infrastructure.repositories.investment_repository import InvestmentRepository
from src.UI.formatting import brl


INVESTMENT_TYPES = ["CDB", "LCI", "LCA", "Tesouro Direto", "Ações", "Fundos", "Poupança", "Outro"]


def _parse_money(value):
    normalized = value.strip().replace("R$", "").replace(" ", "")
    if "," in normalized:
        normalized = normalized.replace(".", "").replace(",", ".")
    return Decimal(normalized)


def show_investments():
    st.header("Investimentos")
    with st.expander("Cadastrar investimento", expanded=False):
        with SessionLocal() as session:
            banks = BankRepository(session).get_all()
        if not banks:
            st.info("Cadastre uma instituição financeira antes dos investimentos.")
        else:
            with st.form("investment_form"):
                selected_bank = st.selectbox("Instituição financeira", banks, format_func=lambda item: item.name)
                name = st.text_input("Nome do investimento")
                investment_type = st.selectbox("Tipo", INVESTMENT_TYPES)
                amount_text = st.text_input("Valor total atual (R$)", placeholder="Ex.: 1.500,00")
                application_date = st.date_input("Data da aplicação", value=date.today())
                submitted = st.form_submit_button("Cadastrar")
            if submitted:
                try:
                    amount = _parse_money(amount_text)
                    with SessionLocal() as session:
                        CreateInvestment(InvestmentRepository(session)).execute(
                            selected_bank.id, name, investment_type, amount, application_date
                        )
                    st.success("Investimento cadastrado. O valor atual foi salvo como registro inicial.")
                    st.rerun()
                except (InvalidOperation, ValueError) as error:
                    st.error("Informe um valor válido e confira os campos obrigatórios." if isinstance(error, InvalidOperation) else str(error))

    with SessionLocal() as session:
        investments = ListInvestments(InvestmentRepository(session)).execute()
        banks_by_id = {bank.id: bank.name for bank in BankRepository(session).get_all()}
        repo = FinanceRepository(session)
        snapshots = repo.list_snapshots()
    if not investments:
        st.info("Nenhum investimento cadastrado.")
        return

    total = sum((investment.total_value for investment in investments), Decimal("0"))
    st.metric("Patrimônio investido", brl(total))

    with st.expander("Registrar atualização de valor", expanded=False):
        investment_options = {str(item.id): item for item in investments}
        with st.form("investment_snapshot_form"):
            selected_id = st.selectbox(
                "Investimento", list(investment_options),
                format_func=lambda key: investment_options[key].name,
            )
            snapshot_date = st.date_input("Data da atualização", value=date.today())
            total_text = st.text_input("Valor total atual (R$)", placeholder="Ex.: 1.650,00")
            contributions_text = st.text_input("Aportes desde a última atualização (R$)", value="0,00")
            submitted_snapshot = st.form_submit_button("Salvar atualização")
        if submitted_snapshot:
            try:
                with SessionLocal() as session:
                    service = FinanceService(FinanceRepository(session))
                    service.create_investment_snapshot(
                        investment_options[selected_id].id,
                        snapshot_date,
                        _parse_money(total_text),
                        _parse_money(contributions_text),
                    )
                st.success("Atualização registrada.")
                st.rerun()
            except (InvalidOperation, ValueError) as error:
                st.error("Informe valores válidos." if isinstance(error, InvalidOperation) else str(error))

    rows = []
    for investment in investments:
        rows.append({
            "Investimento": investment.name,
            "Instituição": banks_by_id.get(investment.bank_id, "—"),
            "Tipo": investment.investment_type,
            "Valor atual": brl(investment.total_value),
            "Data da aplicação": investment.application_date.strftime("%d/%m/%Y"),
        })
    st.subheader("Carteira")
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    if snapshots:
        history_rows = []
        for investment in investments:
            with SessionLocal() as session:
                history = FinanceService(FinanceRepository(session)).investment_history(investment.id)
            for item in history:
                snapshot = item["snapshot"]
                history_rows.append({
                    "Investimento": investment.name,
                    "Data": snapshot.snapshot_date,
                    "Valor total": float(snapshot.total_value),
                    "Aportes": float(snapshot.contributions),
                    "Rendimento": float(item["earnings"]) if item["earnings"] is not None else None,
                    "Rendimento %": float(item["percentage"]) if item["percentage"] is not None else None,
                })
        history_df = pd.DataFrame(history_rows)
        st.subheader("Histórico e rendimento entre atualizações")
        st.dataframe(history_df, use_container_width=True, hide_index=True)
        chart_df = history_df.dropna(subset=["Valor total"])
        if not chart_df.empty:
            figure = px.line(chart_df, x="Data", y="Valor total", color="Investimento", markers=True)
            st.plotly_chart(figure, use_container_width=True)
        if len(history_df) and history_df["Rendimento"].notna().sum() == 0:
            st.caption("O rendimento aparecerá após uma atualização posterior ao registro inicial.")
