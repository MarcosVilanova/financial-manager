from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from src.application.services.reporting_service import ReportingService
from src.infrastructure.database.connection import SessionLocal
from src.infrastructure.repositories.finance_repository import FinanceRepository
from src.UI.formatting import brl


MONTHS = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]


def show_reports():
    st.header("Relatórios mensais")
    today = date.today()
    col1, col2 = st.columns(2)
    month_name = col1.selectbox("Mês", MONTHS, index=today.month - 1)
    year = col2.number_input("Ano", min_value=2000, max_value=2100, value=today.year, step=1)
    with SessionLocal() as session:
        service = ReportingService(FinanceRepository(session))
        existing = service.repository.get_report(f"{int(year):04d}-{MONTHS.index(month_name) + 1:02d}")
        if st.button("Gerar ou atualizar relatório", type="primary"):
            report = service.build_month_report(int(year), MONTHS.index(month_name) + 1, refresh=True)
            st.session_state["selected_financial_report"] = report
            st.success("Relatório salvo para consulta futura.")
        saved_reports = service.repository.list_reports()

    report = st.session_state.get("selected_financial_report") or existing
    if saved_reports:
        report_months = [item[0] for item in saved_reports]
        selected_saved_month = st.selectbox("Relatório salvo", report_months)
        if report is None or report.get("month_key") != selected_saved_month:
            report = next(item[2] for item in saved_reports if item[0] == selected_saved_month)
        with st.form(f"delete_report_{selected_saved_month}"):
            confirm_report_delete = st.checkbox(
                "Confirmo excluir este relatório salvo", key=f"confirm_delete_report_{selected_saved_month}"
            )
            delete_report = st.form_submit_button("Excluir relatório")
        if delete_report:
            if not confirm_report_delete:
                st.warning("Marque a confirmação antes de excluir.")
            else:
                with SessionLocal() as session:
                    FinanceRepository(session).delete_report(selected_saved_month)
                session_report = st.session_state.get("selected_financial_report") or {}
                if session_report.get("month_key") == selected_saved_month:
                    del st.session_state["selected_financial_report"]
                st.success("Relatório excluído.")
                st.rerun()
    if not report:
        st.info("Selecione um mês e gere o relatório. O relatório automático é produzido no último dia do mês pelo agendador.")
        return

    c1, c2, c3 = st.columns(3)
    c1.metric("Total de despesas", brl(report["total"]))
    c2.metric("PIX", brl(report["pix_total"]))
    c3.metric("Cartão de crédito", brl(report["card_total"]))
    pct = report["difference_percent"]
    st.write(
        f"**Comparação com o mês anterior:** {brl(report['previous_total'])} · "
        f"variação de {brl(report['difference'])}"
        + (f" ({pct:+.1f}%)." if pct is not None else " (não há base anterior).")
    )

    left, right = st.columns(2)
    with left:
        st.subheader("Distribuição por categoria")
        if report["categories"]:
            frame = pd.DataFrame(report["categories"])
            st.plotly_chart(px.pie(frame, names="category", values="total", hole=0.4), use_container_width=True)
            st.dataframe(frame.rename(columns={"category": "Categoria", "total": "Total"}), hide_index=True, use_container_width=True)
        else:
            st.info("Sem despesas registradas neste mês.")
    with right:
        st.subheader("Maiores variações por categoria")
        changes = report["category_changes"][:8]
        if changes:
            frame = pd.DataFrame(changes).rename(columns={
                "category": "Categoria", "current": "Mês selecionado",
                "previous": "Mês anterior", "difference": "Variação",
            })
            st.dataframe(frame, hide_index=True, use_container_width=True)
        else:
            st.info("Sem variações para comparar.")

    st.subheader("Evolução dos investimentos")
    if report["investment"]:
        st.dataframe(pd.DataFrame(report["investment"]), hide_index=True, use_container_width=True)
    else:
        st.info("Não há atualizações de investimento registradas neste período.")

    with SessionLocal() as session:
        pdf = ReportingService(FinanceRepository(session)).pdf_bytes(report)
    st.download_button(
        "Baixar relatório em PDF", data=pdf,
        file_name=f"relatorio-financeiro-{report['month_key']}.pdf",
        mime="application/pdf",
    )
