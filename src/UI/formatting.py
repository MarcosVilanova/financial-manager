from decimal import Decimal


def brl(value):
    amount = Decimal(str(value or 0))
    formatted = f"{amount:,.2f}"
    return "R$ " + formatted.replace(",", "X").replace(".", ",").replace("X", ".")
