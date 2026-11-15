import streamlit as st

from src.infrastructure.database.connection import SessionLocal
from src.infrastructure.repositories.bank_repository import BankRepository
from src.application.use_cases.create_bank import CreateBank
from src.application.use_cases.list_banks import ListBanks

def show_banks():

    st.title("Instituições financeiras")

    st.subheader("Cadastrar banco")

    bank_name = st.text_input("Nome do banco")

    if st.button("Cadastrar banco"):

        try:
            with SessionLocal() as session:
                repository = BankRepository(session)
                use_case = CreateBank(repository)

                use_case.execute(bank_name)

            st.success("Banco cadastrado com sucesso!")
            st.rerun()

        except ValueError as error:
            st.error(str(error))

    st.divider()

    st.subheader("Bancos cadastrados")

    with SessionLocal() as session:
        repository = BankRepository(session)
        use_case = ListBanks(repository)

        banks = use_case.execute()

    if banks:
        for bank in banks:
            st.write(f"**{bank.name}**")
    else:
        st.info("Nenhum banco cadastrado.")
