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
        banks = BankRepository(session).get_all()
        banks_by_id = {bank.id: bank.name for bank in banks}
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

    st.subheader("Editar ou excluir investimentos e atualizações")
    for investment in investments:
        with st.expander(f"Gerenciar: {investment.name}"):
            with st.form(f"edit_investment_{investment.id}"):
                bank = st.selectbox(
                    "Instituição financeira", banks,
                    index=next((i for i, item in enumerate(banks) if item.id == investment.bank_id), 0),
                    format_func=lambda item: item.name,
                )
                updated_name = st.text_input("Nome", value=investment.name)
                updated_type = st.selectbox(
                    "Tipo", INVESTMENT_TYPES,
                    index=INVESTMENT_TYPES.index(investment.investment_type)
                    if investment.investment_type in INVESTMENT_TYPES else len(INVESTMENT_TYPES) - 1,
                )
                updated_application_date = st.date_input(
                    "Data da aplicação", value=investment.application_date,
                    key=f"application_date_{investment.id}",
                )
                update_investment = st.form_submit_button("Salvar dados do investimento")
            if update_investment:
                try:
                    with SessionLocal() as session:
                        InvestmentRepository(session).update(
                            investment.id, bank.id, updated_name, updated_type, updated_application_date
                        )
                    st.success("Investimento atualizado.")
                    st.rerun()
                except ValueError as error:
                    st.error(str(error))

            with st.form(f"delete_investment_{investment.id}"):
                confirm_investment_delete = st.checkbox(
                    "Confirmo excluir o investimento e todo o seu histórico",
                    key=f"confirm_investment_{investment.id}",
                )
                delete_investment = st.form_submit_button("Excluir investimento")
            if delete_investment:
                if not confirm_investment_delete:
                    st.warning("Marque a confirmação antes de excluir.")
                else:
                    with SessionLocal() as session:
                        InvestmentRepository(session).delete(investment.id)
                    st.success("Investimento e histórico excluídos.")
                    st.rerun()

            with SessionLocal() as session:
                investment_history = FinanceService(FinanceRepository(session)).investment_history(investment.id)
            if investment_history:
                snapshot_options = [item["snapshot"] for item in investment_history]
                selected_snapshot = st.selectbox(
                    "Atualização do histórico", snapshot_options,
                    format_func=lambda item: f"{item.snapshot_date:%d/%m/%Y} — {brl(item.total_value)}",
                    key=f"snapshot_choice_{investment.id}",
                )
                with st.form(f"edit_snapshot_{investment.id}_{selected_snapshot.id}"):
                    updated_snapshot_date = st.date_input(
                        "Data da atualização", value=selected_snapshot.snapshot_date,
                        key=f"snapshot_date_{investment.id}_{selected_snapshot.id}",
                    )
                    updated_snapshot_total = st.text_input(
                        "Valor total (R$)", value=str(selected_snapshot.total_value).replace(".", ","),
                        key=f"snapshot_total_{investment.id}_{selected_snapshot.id}",
                    )
                    updated_snapshot_contributions = st.text_input(
                        "Aportes no período (R$)", value=str(selected_snapshot.contributions).replace(".", ","),
                        key=f"snapshot_contributions_{investment.id}_{selected_snapshot.id}",
                    )
                    update_snapshot = st.form_submit_button("Salvar atualização do histórico")
                if update_snapshot:
                    try:
                        with SessionLocal() as session:
                            FinanceService(FinanceRepository(session)).update_investment_snapshot(
                                selected_snapshot.id,
                                updated_snapshot_date,
                                _parse_money(updated_snapshot_total),
                                _parse_money(updated_snapshot_contributions),
                            )
                        st.success("Atualização do histórico salva; rendimentos foram recalculados.")
                        st.rerun()
                    except (InvalidOperation, ValueError) as error:
                        st.error("Informe valores válidos." if isinstance(error, InvalidOperation) else str(error))

                with st.form(f"delete_snapshot_{investment.id}_{selected_snapshot.id}"):
                    confirm_snapshot_delete = st.checkbox(
                        "Confirmo excluir esta atualização",
                        key=f"confirm_snapshot_{investment.id}_{selected_snapshot.id}",
                    )
                    delete_snapshot = st.form_submit_button("Excluir atualização")
                if delete_snapshot:
                    if not confirm_snapshot_delete:
                        st.warning("Marque a confirmação antes de excluir.")
                    else:
                        with SessionLocal() as session:
                            FinanceService(FinanceRepository(session)).delete_investment_snapshot(selected_snapshot.id)
                        st.success("Atualização excluída.")
                        st.rerun()

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
