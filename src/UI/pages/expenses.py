import calendar
from datetime import date
from decimal import Decimal, InvalidOperation

import pandas as pd
import streamlit as st

from src.application.services.finance_service import FinanceService
from src.infrastructure.database.connection import SessionLocal
from src.infrastructure.repositories.finance_repository import FinanceRepository
from src.UI.formatting import brl


CATEGORIES = ["Alimentação", "Transporte", "Lazer", "Saúde", "Moradia", "Compras", "Educação", "Contas", "Outros"]


def _parse_money(value):
    normalized = value.strip().replace("R$", "").replace(" ", "")
    if "," in normalized:
        normalized = normalized.replace(".", "").replace(",", ".")
    return Decimal(normalized)


def show_expenses():
    st.header("Despesas")
    with st.expander("Registrar despesa", expanded=False):
        with SessionLocal() as session:
            cards = FinanceRepository(session).list_cards()
        payment_method = st.selectbox(
            "Forma de pagamento", ["PIX", "Cartão de crédito"], key="expense_payment_method"
        )
        card = None
        if payment_method == "Cartão de crédito":
            if cards:
                card = st.selectbox("Cartão", cards, format_func=lambda item: item.name, key="expense_card")
            else:
                st.warning("Cadastre um cartão antes de lançar uma despesa no crédito.")
        with st.form("expense_form"):
            description = st.text_input("Descrição da compra")
            amount_text = st.text_input("Valor (R$)", placeholder="Ex.: 89,90")
            expense_date = st.date_input("Data da despesa", value=date.today())
            category = st.selectbox("Categoria", CATEGORIES)
            submitted = st.form_submit_button("Salvar despesa")
        if submitted:
            try:
                if payment_method == "Cartão de crédito" and card is None:
                    raise ValueError("Cadastre e selecione um cartão.")
                with SessionLocal() as session:
                    expense = FinanceService(FinanceRepository(session)).create_expense(
                        description, _parse_money(amount_text), expense_date,
                        category, payment_method, card.id if card else None,
                    )
                if expense.invoice_due_date:
                    st.success(f"Despesa registrada. Vencimento da fatura: {expense.invoice_due_date:%d/%m/%Y}.")
                else:
                    st.success("Despesa registrada.")
                st.rerun()
            except (InvalidOperation, ValueError) as error:
                st.error("Informe um valor válido." if isinstance(error, InvalidOperation) else str(error))

    today = date.today()
    first_of_month = date(today.year, today.month, 1)
    end_of_month = date(today.year, today.month, calendar.monthrange(today.year, today.month)[1])
    left, right = st.columns(2)
    start_date = left.date_input("De", value=first_of_month, key="expense_filter_start")
    end_date = right.date_input("Até", value=min(today, end_of_month), key="expense_filter_end")
    selected_category = st.selectbox("Categoria", ["Todas", *CATEGORIES], key="expense_filter_category")
    selected_method = st.selectbox("Pagamento", ["Todas", "PIX", "Cartão de crédito"], key="expense_filter_method")

    with SessionLocal() as session:
        repository = FinanceRepository(session)
        expenses = repository.list_expenses(start_date, end_date, selected_category, selected_method)
        cards_by_id = {card.id: card.name for card in repository.list_cards()}
    if not expenses:
        st.info("Nenhuma despesa encontrada para os filtros selecionados.")
        return

    total = sum((item.amount for item in expenses), Decimal("0"))
    st.metric("Total no período", brl(total))
    st.dataframe(pd.DataFrame([
        {
            "Data": item.expense_date.strftime("%d/%m/%Y"),
            "Descrição": item.description,
            "Categoria": item.category,
            "Pagamento": item.payment_method,
            "Cartão": cards_by_id.get(item.card_id, "—") if item.card_id else "—",
            "Vencimento da fatura": item.invoice_due_date.strftime("%d/%m/%Y") if item.invoice_due_date else "—",
            "Valor": brl(item.amount),
        }
        for item in expenses
    ]), use_container_width=True, hide_index=True)
