import streamlit as st

from src.infrastructure.database.connection import init_db
from src.UI.pages.banks import show_banks
from src.UI.pages.cards import show_cards
from src.UI.pages.dashboard import show_dashboard
from src.UI.pages.expenses import show_expenses
from src.UI.pages.investments import show_investments
from src.UI.pages.loans import show_loans
from src.UI.pages.reports import show_reports


st.set_page_config(page_title="Gestão Financeira", page_icon="💰", layout="wide")
init_db()

st.title("Gestão Financeira Pessoal")
page = st.sidebar.radio(
    "Navegação",
    [
        "Dashboard",
        "Investimentos",
        "Despesas",
        "Cartões de crédito",
        "Empréstimos",
        "Relatórios",
        "Instituições financeiras",
    ],
)

if page == "Dashboard":
    show_dashboard()
elif page == "Investimentos":
    show_investments()
elif page == "Despesas":
    show_expenses()
elif page == "Cartões de crédito":
    show_cards()
elif page == "Empréstimos":
    show_loans()
elif page == "Relatórios":
    show_reports()
else:
    show_banks()
