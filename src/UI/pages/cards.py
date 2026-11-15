import streamlit as st
import pandas as pd

from src.infrastructure.database.connection import SessionLocal
from src.infrastructure.repositories.bank_repository import BankRepository
from src.infrastructure.repositories.finance_repository import FinanceRepository
from src.application.services.finance_service import FinanceService
from src.UI.formatting import brl


def show_cards():
    st.header("Cartões de crédito")
    with SessionLocal() as session:
        banks = BankRepository(session).get_all()
        repository = FinanceRepository(session)
        cards = repository.list_cards()
        expenses = repository.list_expenses()

    with st.expander("Cadastrar cartão", expanded=not bool(cards)):
        if not banks:
            st.info("Cadastre uma instituição financeira antes de cadastrar cartões.")
        else:
            with st.form("credit_card_form"):
                bank = st.selectbox("Instituição financeira", banks, format_func=lambda item: item.name)
                name = st.text_input("Nome ou identificação")
                closing_day = st.number_input("Dia de fechamento da fatura", min_value=1, max_value=31, value=10)
                due_day = st.number_input("Dia de vencimento da fatura", min_value=1, max_value=31, value=20)
                submitted = st.form_submit_button("Cadastrar cartão")
            if submitted:
                try:
                    with SessionLocal() as session:
                        FinanceService(FinanceRepository(session)).create_card(
                            bank.id, name, int(due_day), int(closing_day)
                        )
                    st.success("Cartão cadastrado.")
                    st.rerun()
                except ValueError as error:
                    st.error(str(error))

    with SessionLocal() as session:
        cards = FinanceRepository(session).list_cards()
        banks_by_id = {bank.id: bank.name for bank in BankRepository(session).get_all()}
    if cards:
        st.dataframe([
            {
                "Cartão": card.name,
                "Instituição": banks_by_id.get(card.bank_id, "—"),
                "Fechamento": f"Dia {card.closing_day}",
                "Vencimento": f"Dia {card.due_day}",
            }
            for card in cards
        ], use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum cartão cadastrado.")

    card_names = {card.id: card.name for card in cards}
    invoice_expenses = [
        item for item in expenses
        if item.card_id in card_names and item.invoice_due_date is not None
    ]
    st.subheader("Despesas organizadas por fatura")
    if invoice_expenses:
        frame = pd.DataFrame([
            {
                "Vencimento": item.invoice_due_date,
                "Cartão": card_names[item.card_id],
                "Compra": item.expense_date.strftime("%d/%m/%Y"),
                "Descrição": item.description,
                "Categoria": item.category,
                "Valor": float(item.amount),
            }
            for item in invoice_expenses
        ])
        grouped = frame.groupby(["Vencimento", "Cartão"], as_index=False)["Valor"].sum()
        grouped["Total da fatura"] = grouped["Valor"].map(brl)
        st.dataframe(grouped[["Vencimento", "Cartão", "Total da fatura"]], hide_index=True, use_container_width=True)
        st.dataframe(frame.drop(columns=["Valor"]), hide_index=True, use_container_width=True)
    else:
        st.info("As despesas lançadas no cartão aparecerão aqui agrupadas pelo vencimento da fatura.")
