import streamlit as st

from src.application.use_cases.create_bank import CreateBank
from src.application.use_cases.list_banks import ListBanks
from src.infrastructure.database.connection import SessionLocal
from src.infrastructure.repositories.bank_repository import BankRepository


def show_banks():
    st.header("Instituições financeiras")
    with st.form("create_bank_form"):
        bank_name = st.text_input("Nome da instituição")
        submitted = st.form_submit_button("Cadastrar instituição")
    if submitted:
        try:
            with SessionLocal() as session:
                CreateBank(BankRepository(session)).execute(bank_name)
            st.success("Instituição cadastrada.")
            st.rerun()
        except ValueError as error:
            st.error(str(error))

    with SessionLocal() as session:
        banks = ListBanks(BankRepository(session)).execute()
    if not banks:
        st.info("Nenhuma instituição cadastrada.")
        return

    st.subheader("Instituições cadastradas")
    for bank in banks:
        with st.expander(bank.name):
            with st.form(f"edit_bank_{bank.id}"):
                new_name = st.text_input("Nome", value=bank.name)
                update = st.form_submit_button("Salvar alterações")
            if update:
                try:
                    with SessionLocal() as session:
                        BankRepository(session).update(bank.id, new_name)
                    st.success("Instituição atualizada.")
                    st.rerun()
                except ValueError as error:
                    st.error(str(error))

            with st.form(f"delete_bank_{bank.id}"):
                confirmed = st.checkbox(
                    "Confirmo a exclusão desta instituição", key=f"confirm_delete_bank_{bank.id}"
                )
                delete = st.form_submit_button("Excluir instituição")
            if delete:
                if not confirmed:
                    st.warning("Marque a confirmação antes de excluir.")
                else:
                    try:
                        with SessionLocal() as session:
                            BankRepository(session).delete(bank.id)
                        st.success("Instituição excluída.")
                        st.rerun()
                    except ValueError as error:
                        st.error(str(error))
