from datetime import date
from decimal import Decimal, InvalidOperation

import pandas as pd
import streamlit as st

from src.application.services.finance_service import FinanceService
from src.infrastructure.database.connection import SessionLocal
from src.infrastructure.repositories.finance_repository import FinanceRepository
from src.UI.formatting import brl


def _parse_money(value):
    normalized = value.strip().replace("R$", "").replace(" ", "")
    if "," in normalized:
        normalized = normalized.replace(".", "").replace(",", ".")
    return Decimal(normalized)


def show_loans():
    st.header("Empréstimos a terceiros")
    with st.expander("Registrar empréstimo", expanded=False):
        with st.form("loan_form"):
            person = st.text_input("Nome da pessoa")
            amount_text = st.text_input("Valor emprestado (R$)", placeholder="Ex.: 250,00")
            loan_date = st.date_input("Data do empréstimo", value=date.today())
            note = st.text_area("Descrição ou observação")
            submitted = st.form_submit_button("Registrar")
        if submitted:
            try:
                with SessionLocal() as session:
                    FinanceService(FinanceRepository(session)).create_loan(
                        person, _parse_money(amount_text), loan_date, note
                    )
                st.success("Empréstimo registrado.")
                st.rerun()
            except (InvalidOperation, ValueError) as error:
                st.error("Informe um valor válido." if isinstance(error, InvalidOperation) else str(error))

    with SessionLocal() as session:
        loans = FinanceRepository(session).list_loans()
    pending = [loan for loan in loans if loan.status == "Pendente"]
    st.metric("Total ainda não devolvido", brl(sum((loan.amount for loan in pending), Decimal("0"))))
    if not loans:
        st.info("Nenhum empréstimo registrado.")
        return

    st.dataframe(pd.DataFrame([
        {
            "Pessoa": loan.person_name,
            "Valor": brl(loan.amount),
            "Data": loan.loan_date.strftime("%d/%m/%Y"),
            "Observação": loan.note,
            "Status": loan.status,
            "Devolvido em": loan.returned_date.strftime("%d/%m/%Y") if loan.returned_date else "—",
        }
        for loan in loans
    ]), use_container_width=True, hide_index=True)

    for loan in pending:
        with st.expander(f"Marcar devolução — {loan.person_name} · {brl(loan.amount)}"):
            returned_date = st.date_input("Data de devolução", value=date.today(), key=f"returned_{loan.id}")
            if st.button("Confirmar devolução", key=f"return_{loan.id}"):
                with SessionLocal() as session:
                    FinanceService(FinanceRepository(session)).mark_loan_returned(loan.id, returned_date)
                st.success("Empréstimo marcado como devolvido.")
                st.rerun()
