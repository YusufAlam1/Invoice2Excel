from pathlib import Path
import pandas as pd
from openpyxl import load_workbook
from core.models import InvoiceRow

def _ensure_workbook(path: Path):
    if not path.exists():
        with pd.ExcelWriter(path, engine="openpyxl") as w:
            pd.DataFrame(columns=[
                "Employee","Invoice #","Period","Hours","Rate",
                "Amount","HST","Total","Invoice Date","Due Date"
            ]).to_excel(w, sheet_name="Total Invoice Paid", index=False)
            pd.DataFrame(columns=["Year-Month","HST"]).to_excel(w, sheet_name="Total Tax", index=False)

def save_row(path: Path, row: InvoiceRow):
    _ensure_workbook(path)

    # Per-employee sheet (openpyxl for simple append)
    wb = load_workbook(path)
    if row.employee not in wb.sheetnames:
        ws = wb.create_sheet(row.employee)
        ws.append(["Invoice #","Week / Period","Worked","Rate","Amount","HST","Date & Time Paid","Notes"])
    ws = wb[row.employee]
    ws.append([row.invoice_no, row.period, row.hours, row.rate, row.amount, row.hst, "", ""])
    wb.save(path)

    # Global sheets with pandas
    df_total = pd.read_excel(path, sheet_name="Total Invoice Paid")
    df_total.loc[len(df_total)] = [
        row.employee, row.invoice_no, row.period, row.hours, row.rate,
        row.amount, row.hst, row.total, row.invoice_date, row.due_date
    ]

    # Monthly HST
    from dateutil import parser as dparser
    try:
        ym = dparser.parse(row.invoice_date, dayfirst=False).strftime("%Y-%m")
    except Exception:
        ym = "Unknown"
    df_tax = pd.read_excel(path, sheet_name="Total Tax")
    if (df_tax["Year-Month"] == ym).any():
        df_tax.loc[df_tax["Year-Month"] == ym, "HST"] += row.hst
    else:
        df_tax.loc[len(df_tax)] = [ym, row.hst]

    with pd.ExcelWriter(path, engine="openpyxl", mode="a", if_sheet_exists="replace") as w:
        df_total.to_excel(w, sheet_name="Total Invoice Paid", index=False)
        df_tax.to_excel(w, sheet_name="Total Tax", index=False)