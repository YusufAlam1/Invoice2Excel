from pydantic import BaseModel

class InvoiceRow(BaseModel):
    invoice_no: str
    invoice_date: str  # keep as str for now; we’ll parse to dates later
    due_date: str
    employee: str      # "First Last"
    period: str        # "MM/DD/YY - MM/DD/YY"
    hours: float
    rate: float
    amount: float      # subtotal
    hst: float
    total: float