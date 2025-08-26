import io, re, pdfplumber
from core.models import InvoiceRow

from ._regex_rows import extract_row_from_text

try:
    from ._banner import extract_banner_row  
except Exception:
    extract_banner_row = None  

from ._text_utils import (
    num, to_first_last, norm_date, norm_period, find, collapse_spaces_keep_newlines
)

def parse_invoice(pdf_bytes: bytes) -> InvoiceRow:
    
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        page = pdf.pages[0]
        raw_text = page.extract_text() or ""

    text = collapse_spaces_keep_newlines(raw_text)
    
    rowdict = extract_row_from_text(text)

    if not rowdict and extract_banner_row is not None:
        rowdict = extract_banner_row(page)

    if not rowdict:
        raise ValueError(
            "Unable to locate the banner data row. "
            "Check that the header line ends with 'Amount' and the next line contains the row."
        )

    employee = to_first_last(rowdict.get("candidate", ""))
    period   = norm_period(rowdict.get("period", ""))
    hours    = num(rowdict.get("units"))
    rate     = num(rowdict.get("rate"))
    amount   = num(rowdict.get("amount"))
    
    invoice_no   = find(r"Invoice\s*#\s*([0-9]+)", text)
    invoice_date = norm_date(find(r"Invoice\s*Date[:\s]*([A-Za-z0-9,/\- ]+)", text))
    due_date     = norm_date(find(r"(?:Payment\s*Due\s*Date|Due\s*Date)[:\s]*([A-Za-z0-9,/\- ]+)", text))
    hst          = num(find(r"\bONHST\b[^\$]*\$?\s*([0-9,]+\.\d{2})", text))
    total        = num(
        find(r"Total\s*\(CAD\)\s*\$?\s*([0-9,]+\.\d{2})", text)
        or find(r"\bTotal\b[^\$]*\$?\s*([0-9,]+\.\d{2})", text)
    )

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
        total=total,
    )
