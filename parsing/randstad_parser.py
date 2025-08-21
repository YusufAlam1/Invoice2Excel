import io, re
import pdfplumber
from dateutil import parser as dparser
from core.models import InvoiceRow

HST_RATE = 0.13

# HEADER (TOP RIGHT)
INV_NO_RE   = re.compile(r"Invoice\s*#\s*(\d+)", re.I)
INV_DATE_RE = re.compile(r"Invoice Date\s*([0-9/]{8,10})", re.I)
DUE_RE      = re.compile(r"Payment Due Date\s*([0-9/]{8,10})", re.I)

# MIDDLE LINE
LINE_RE = re.compile(
    r"(?P<last>[A-Za-z'’-]+),\s*(?P<first>[A-Za-z'’-]+).*?"
    r"(?P<pstart>\d{2}/\d{2}/\d{2})-(?P<pend>\d{2}/\d{2}/\d{2}).*?"
    r"(?P<hours>\d+(?:\.\d+)?)\s+(?P<rate>\d+(?:\.\d+)?).*?\$?(?P<amount>\d{1,3}(?:,\d{3})*\.\d{2})",
    re.S
)

# TOTALS (BOTTOM RIGHT)
SUBTOTAL_RE = re.compile(r"Subtotal\s*\$?\s*([0-9,]+\.\d{2})", re.I)
HST_RE      = re.compile(r"(ON\s*HST|ONHST)\s*13%\s*\$?\s*([0-9,]+\.\d{2})", re.I)
TOTAL_RE    = re.compile(r"Total\s*\(CAD\)\s*\$?\s*([0-9,]+\.\d{2})", re.I)

def _pdf_text(pdf_bytes: bytes) -> str:
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)

def _norm_name(last: str, first: str) -> str:
    return f"{first.strip().title()} {last.strip().title()}"

def parse_invoice(pdf_bytes: bytes) -> InvoiceRow:
    text = _pdf_text(pdf_bytes)

    invoice_no = INV_NO_RE.search(text).group(1)
    invoice_date = INV_DATE_RE.search(text).group(1)
    due_date = DUE_RE.search(text).group(1)

    m = LINE_RE.search(text)
    if not m:
        raise ValueError("Couldn’t find candidate row.")
    employee = _norm_name(m["last"], m["first"])
    period = f"{m['pstart']} - {m['pend']}"
    hours  = float(m["hours"])
    rate   = float(m["rate"])
    amount = float(m["amount"].replace(",", ""))

    subtotal = float(SUBTOTAL_RE.search(text).group(1).replace(",", ""))
    hst_pdf  = float(HST_RE.search(text).group(2).replace(",", ""))
    total_pdf= float(TOTAL_RE.search(text).group(1).replace(",", ""))

    # Trust math more than OCR quirks
    hst_calc = round(subtotal * HST_RATE, 2)
    total_calc = round(subtotal + hst_calc, 2)
    amount = subtotal       # in these invoices Amount == Subtotal
    hst    = hst_calc       # prefer calculated
    total  = total_calc

    return InvoiceRow(
        invoice_no=invoice_no,
        invoice_date=invoice_date,
        due_date=due_date,
        employee=employee,
        period=period,
        hours=hours,
        rate=rate,
        amount=amount,
        hst=hst,
        total=total
    )
