import calendar
from datetime import date
from decimal import Decimal

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from io import BytesIO
from xml.sax.saxutils import escape


def _month_bounds(year, month):
    last = calendar.monthrange(year, month)[1]
    return date(year, month, 1), date(year, month, last)


def _brl(value):
    return "R$ " + f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


class ReportingService:
    def __init__(self, repository):
        self.repository = repository

    def build_month_report(self, year, month, refresh=False):
        month_key = f"{year:04d}-{month:02d}"
        existing = self.repository.get_report(month_key)
        if existing and not refresh:
            return existing

        start, end = _month_bounds(year, month)
        all_expenses = self.repository.list_expenses()
        current = [item for item in all_expenses if start <= item.expense_date <= end]
        prev_year, prev_month = (year - 1, 12) if month == 1 else (year, month - 1)
        prev_start, prev_end = _month_bounds(prev_year, prev_month)
        previous = [item for item in all_expenses if prev_start <= item.expense_date <= prev_end]

        current_frame = self._expense_frame(current)
        previous_frame = self._expense_frame(previous)
        current_total = Decimal(str(current_frame["amount"].sum())) if not current_frame.empty else Decimal("0")
        previous_total = Decimal(str(previous_frame["amount"].sum())) if not previous_frame.empty else Decimal("0")
        difference = current_total - previous_total
        difference_pct = (difference / previous_total * Decimal("100")) if previous_total else None
        payment_totals = current_frame.groupby("payment_method")["amount"].sum().to_dict() if not current_frame.empty else {}
        pix_total = Decimal(str(payment_totals.get("PIX", 0)))
        card_total = Decimal(str(payment_totals.get("Cartão de crédito", 0)))
        by_category = {
            str(key): Decimal(str(value))
            for key, value in current_frame.groupby("category")["amount"].sum().items()
        } if not current_frame.empty else {}
        previous_categories = {
            str(key): Decimal(str(value))
            for key, value in previous_frame.groupby("category")["amount"].sum().items()
        } if not previous_frame.empty else {}
        category_deltas = []
        for category in sorted(set(by_category) | set(previous_categories)):
            now = by_category.get(category, Decimal("0"))
            before = previous_categories.get(category, Decimal("0"))
            category_deltas.append({
                "category": category,
                "current": float(now),
                "previous": float(before),
                "difference": float(now - before),
            })
        category_deltas.sort(key=lambda item: abs(item["difference"]), reverse=True)

        investment_summary = self._investment_period_summary(start, end)
        return self.repository.save_report(month_key, {
            "month_key": month_key,
            "generated_on": date.today().isoformat(),
            "expense_count": len(current),
            "total": float(current_total),
            "pix_total": float(pix_total),
            "card_total": float(card_total),
            "previous_total": float(previous_total),
            "difference": float(difference),
            "difference_percent": float(difference_pct) if difference_pct is not None else None,
            "categories": [
                {"category": key, "total": float(value)}
                for key, value in sorted(by_category.items(), key=lambda pair: pair[1], reverse=True)
            ],
            "category_changes": category_deltas,
            "investment": investment_summary,
        }, replace=refresh)

    @staticmethod
    def _expense_frame(expenses):
        return pd.DataFrame([
            {
                "amount": float(item.amount),
                "category": item.category,
                "payment_method": item.payment_method,
            }
            for item in expenses
        ], columns=["amount", "category", "payment_method"])

    def _investment_period_summary(self, start, end):
        investments = self.repository.list_investments()
        data = []
        for investment in investments:
            snapshots = self.repository.list_snapshots(investment.id)
            before = [row for row in snapshots if row.snapshot_date < start]
            during = [row for row in snapshots if start <= row.snapshot_date <= end]
            if not during:
                continue
            first = before[-1] if before else None
            last = during[-1]
            if first:
                contributions = sum((row.contributions for row in during), Decimal("0"))
                earnings = last.total_value - first.total_value - contributions
                percent = float(earnings / first.total_value * Decimal("100")) if first.total_value else None
                data.append({
                    "name": investment.name,
                    "start_value": float(first.total_value),
                    "end_value": float(last.total_value),
                    "contributions": float(contributions),
                    "earnings": float(earnings),
                    "percent": percent,
                })
            else:
                data.append({
                    "name": investment.name,
                    "start_value": None,
                    "end_value": float(last.total_value),
                    "contributions": float(sum((row.contributions for row in during), Decimal("0"))),
                    "earnings": None,
                    "percent": None,
                })
        return data

    def ensure_monthly_report_for_today(self, today=None):
        today = today or date.today()
        if today.day == calendar.monthrange(today.year, today.month)[1]:
            return self.build_month_report(today.year, today.month, refresh=True)
        previous_year, previous_month = (today.year - 1, 12) if today.month == 1 else (today.year, today.month - 1)
        previous_key = f"{previous_year:04d}-{previous_month:02d}"
        if self.repository.get_report(previous_key) is None:
            return self.build_month_report(previous_year, previous_month)
        return None

    def pdf_bytes(self, report):
        output = BytesIO()
        document = SimpleDocTemplate(output, pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm)
        styles = getSampleStyleSheet()
        story = [Paragraph(f"Relatório financeiro — {report['month_key']}", styles["Title"]), Spacer(1, 8 * mm)]
        story.append(Paragraph(f"Total de despesas: {_brl(report['total'])}", styles["Heading2"]))
        story.append(Paragraph(f"PIX: {_brl(report['pix_total'])} | Cartão: {_brl(report['card_total'])}", styles["BodyText"]))
        pct = "n/d" if report["difference_percent"] is None else f"{report['difference_percent']:+.1f}%"
        story.append(Paragraph(
            f"Mês anterior: {_brl(report['previous_total'])} | "
            f"Variação: {_brl(report['difference'])} ({pct})", styles["BodyText"]
        ))
        story.append(Spacer(1, 5 * mm))
        story.append(Paragraph("Despesas por categoria", styles["Heading2"]))
        rows = [["Categoria", "Total"]] + [[row["category"], _brl(row["total"])] for row in report["categories"]]
        if len(rows) == 1:
            rows.append(["Sem despesas", "R$ 0,00"])
        table = Table(rows, colWidths=[110 * mm, 45 * mm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#183B56")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(table)
        story.append(Spacer(1, 5 * mm))
        story.append(Paragraph("Principais variações por categoria", styles["Heading2"]))
        changes = report["category_changes"][:8]
        if changes:
            change_rows = [["Categoria", "Mês anterior", "Mês atual", "Variação"]]
            change_rows.extend([
                [row["category"], _brl(row["previous"]), _brl(row["current"]), _brl(row["difference"])]
                for row in changes
            ])
            change_table = Table(change_rows, colWidths=[55 * mm, 35 * mm, 35 * mm, 35 * mm])
            change_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#183B56")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(change_table)
        else:
            story.append(Paragraph("Sem variações para comparar.", styles["BodyText"]))
        story.append(Spacer(1, 5 * mm))
        story.append(Paragraph("Evolução dos investimentos", styles["Heading2"]))
        for item in report["investment"]:
            if item["earnings"] is None:
                text = f"{escape(item['name'])}: valor registrado de {_brl(item['end_value'])}; sem base anterior no período."
            else:
                text = f"{escape(item['name'])}: rendimento {_brl(item['earnings'])} ({item['percent']:+.2f}%)."
            story.append(Paragraph(text, styles["BodyText"]))
        document.build(story)
        return output.getvalue()
