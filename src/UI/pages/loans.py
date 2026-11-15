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

    st.subheader("Editar ou excluir empréstimo")
    selected_loan = st.selectbox(
        "Empréstimo", loans,
        format_func=lambda item: f"{item.person_name} — {brl(item.amount)} — {item.status}",
        key="manage_loan",
    )
    statuses = ["Pendente", "Devolvido"]
    status = st.selectbox(
        "Status", statuses, index=statuses.index(selected_loan.status),
        key=f"loan_status_{selected_loan.id}",
    )
    returned_date = st.date_input(
        "Data de devolução", value=selected_loan.returned_date or date.today(),
        key=f"loan_return_date_{selected_loan.id}",
    )
    with st.form(f"edit_loan_{selected_loan.id}"):
        person = st.text_input("Pessoa", value=selected_loan.person_name)
        amount_text = st.text_input("Valor (R$)", value=str(selected_loan.amount).replace(".", ","))
        loan_date = st.date_input("Data do empréstimo", value=selected_loan.loan_date)
        note = st.text_area("Observação", value=selected_loan.note)
        update_loan = st.form_submit_button("Salvar empréstimo")
    if update_loan:
        try:
            with SessionLocal() as session:
                FinanceService(FinanceRepository(session)).update_loan(
                    selected_loan.id, person, _parse_money(amount_text), loan_date,
                    note, status, returned_date if status == "Devolvido" else None,
                )
            st.success("Empréstimo atualizado.")
            st.rerun()
        except (InvalidOperation, ValueError) as error:
            st.error("Informe um valor válido." if isinstance(error, InvalidOperation) else str(error))

    with st.form(f"delete_loan_{selected_loan.id}"):
        confirm_loan_delete = st.checkbox(
            "Confirmo excluir este empréstimo", key=f"confirm_delete_loan_{selected_loan.id}"
        )
        delete_loan = st.form_submit_button("Excluir empréstimo")
    if delete_loan:
        if not confirm_loan_delete:
            st.warning("Marque a confirmação antes de excluir.")
        else:
            with SessionLocal() as session:
                FinanceService(FinanceRepository(session)).delete_loan(selected_loan.id)
            st.success("Empréstimo excluído.")
            st.rerun()
